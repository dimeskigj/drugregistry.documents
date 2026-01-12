import os
import logging
from pathlib import Path
from google import genai
from dotenv import load_dotenv

load_dotenv()

# Configuration
INPUT_DIR = Path("documents/parsed")
API_KEY = os.getenv("GEMINI_API_KEY")
MODEL_NAME = "gemini-2.5-flash"  # Use a standard model for counting

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

if not API_KEY:
    logger.error("GEMINI_API_KEY not found in .env file.")
    exit(1)

client = genai.Client(api_key=API_KEY)

def count_tokens():
    if not INPUT_DIR.exists():
        logger.error(f"Input directory does not exist: {INPUT_DIR}")
        return

    all_files = sorted(list(INPUT_DIR.glob("*.md")))
    if not all_files:
        logger.info("No markdown files found in the parsed directory.")
        return

    total_tokens = 0
    file_counts = []

    logger.info(f"Counting tokens for {len(all_files)} files...")

    for i, file_path in enumerate(all_files):
        if (i + 1) % 50 == 0:
            logger.info(f"Processed {i + 1}/{len(all_files)} files...")
        try:
            content = file_path.read_text(encoding="utf-8")
            response = client.models.count_tokens(
                model=MODEL_NAME,
                contents=content
            )
            tokens = response.total_tokens
            total_tokens += tokens
            file_counts.append((file_path.name, tokens))
        except Exception as e:
            logger.error(f"Error counting tokens for {file_path.name}: {e}")

    if not file_counts:
        return

    # Statistics
    avg_tokens = total_tokens / len(file_counts)
    max_file, max_tokens = max(file_counts, key=lambda x: x[1])
    min_file, min_tokens = min(file_counts, key=lambda x: x[1])

    print("\n" + "="*50)
    print("TOKEN COUNT SUMMARY")
    print("="*50)
    print(f"Total Files:          {len(all_files)}")
    print(f"Total Tokens:         {total_tokens:,}")
    print(f"Average per File:     {avg_tokens:,.2f}")
    print(f"Largest File:         {max_file} ({max_tokens:,} tokens)")
    print(f"Smallest File:        {min_file} ({min_tokens:,} tokens)")
    print("="*50)

if __name__ == "__main__":
    count_tokens()
