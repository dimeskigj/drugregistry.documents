import logging
import os
import re
import time
from pathlib import Path
from typing import Any, Dict
from urllib.parse import urljoin

import requests
from dotenv import load_dotenv

# Configuration
load_dotenv()

API_URL = os.getenv("API_URL")
PROJECT_ROOT = Path(__file__).parent.parent
OUTPUT_DIR = PROJECT_ROOT / "documents" / "original"
PAGE_SIZE = 20

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def normalize_filename(base_name: str, extension: str) -> str:
    """Normalizes a filename by removing non-alphanumeric characters and spaces."""
    clean_name = base_name.replace(" ", "_")
    normalized = re.sub(r"[^\w\-_]", "", clean_name)
    return f"{normalized}.{extension}"


def get_file_extension(url: str) -> str:
    """Extracts the file extension from a URL, defaulting to 'pdf'."""
    try:
        ext = url.split(".")[-1].split("?")[0].lower()
        return ext if 1 <= len(ext) <= 4 else "pdf"
    except (IndexError, AttributeError):
        return "pdf"


def download_file(session: requests.Session, url: str, drug_info: Dict[str, Any]) -> None:
    """Downloads a single manual and saves it with a normalized name."""
    try:
        decision_number = drug_info.get("decisionNumber")
        decision_date = drug_info.get("decisionDate")
        extension = get_file_extension(url)

        if isinstance(decision_date, str) and len(decision_date) > 10:
            decision_date = decision_date[:10]

        if decision_number and decision_date:
            base_name = f"{decision_number}_{decision_date}"
        elif decision_number:
            base_name = str(decision_number)
        else:
            base_name = url.split("/")[-1].split(".")[0] or f"manual_{int(time.time())}"

        filename = normalize_filename(base_name, extension)
        file_path = OUTPUT_DIR / filename

        if file_path.exists():
            logger.debug(f"Skipping {filename}, already exists.")
            return

        logger.info(f"Downloading: {filename}")
        with session.get(url, stream=True, timeout=30) as r:
            r.raise_for_status()
            with open(file_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)

    except Exception as e:
        logger.error(f"Failed to download {url}: {e}")


def fetch_and_download_all() -> None:
    """Iterates through API pages and downloads all available drug manuals."""
    if not API_URL:
        logger.error("API_URL environment variable is not set.")
        return

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    endpoint = urljoin(API_URL, "/api/drugs")
    
    session = requests.Session()
    page = 0

    while True:
        logger.info(f"Fetching page {page}...")
        try:
            url = f"{endpoint}?page={page}&size={PAGE_SIZE}"
            response = session.get(url, timeout=20)
            response.raise_for_status()
            
            result = response.json()
            items = result.get("data", [])
            
            if not items:
                logger.info("No more items found.")
                break

            for drug in items:
                manual_url = drug.get("manualUrl")
                if manual_url:
                    download_file(session, manual_url, drug)

            total_count = result.get("totalCount", 0)
            current_page = result.get("page", page)
            
            if (current_page + 1) * PAGE_SIZE >= total_count:
                logger.info("Reached the end of the results.")
                break
                
            page += 1
            
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            break


if __name__ == "__main__":
    try:
        fetch_and_download_all()
    except KeyboardInterrupt:
        logger.info("Process interrupted by user.")
