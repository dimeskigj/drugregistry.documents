import logging
from pathlib import Path

# Configuration
PROJECT_ROOT = Path(__file__).parent.parent
PARSED_DIR = PROJECT_ROOT / "documents" / "parsed"

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def cleanup_empty_documents() -> None:
    """Deletes markdown files that only contain '<!-- image -->' tags and no actual text."""
    if not PARSED_DIR.exists():
        logger.error(f"Parsed directory does not exist: {PARSED_DIR}")
        return

    files = list(PARSED_DIR.glob("*.md"))
    if not files:
        logger.info("No parsed documents found.")
        return

    deleted_count = 0
    total_files = len(files)

    for file_path in files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Remove all image tags and whitespace to see if any text remains
            cleaned_content = content.replace("<!-- image -->", "").strip()

            if not cleaned_content:
                logger.info(f"Deleting empty document: {file_path.name}")
                file_path.unlink()
                deleted_count += 1
        except Exception as e:
            logger.error(f"Failed to process {file_path.name}: {e}")

    logger.info(f"Cleanup complete. Deleted {deleted_count} empty documents out of {total_files} total.")


if __name__ == "__main__":
    try:
        cleanup_empty_documents()
    except KeyboardInterrupt:
        logger.info("Process interrupted by user.")
