import logging
import os
import time
import re
from pathlib import Path
from typing import List, Dict

from google import genai
from dotenv import load_dotenv

load_dotenv()

# Configuration
INPUT_DIR = Path("documents/parsed")
OUTPUT_DIR = Path("documents/augmented")
PROMPT_FILE = Path("PROMPT_AUGMENTATION.md")
LOG_FILE = Path("augmentation.log")

# Gemini Configuration
API_KEY = os.getenv("GEMINI_API_KEY")
MODEL_NAME = "gemini-3-pro-preview" 
BATCH_SIZE = 5
RPM_LIMIT = 30
TPM_LIMIT = 60000
MAX_RETRIES = 5

# Pricing (per 1M tokens)
PRICE_PER_1M_INPUT = 0.50
PRICE_PER_1M_OUTPUT = 3.00

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Global usage tracking
usage_stats = {
    "prompt_tokens": 0,
    "candidate_tokens": 0,
    "total_files": 0,
    "start_time": time.time()
}

if not API_KEY:
    logger.error("GEMINI_API_KEY not found in .env file.")
    exit(1)

client = genai.Client(api_key=API_KEY)


def get_system_prompt() -> str:
    if not PROMPT_FILE.exists():
        logger.error(f"Prompt file not found: {PROMPT_FILE}")
        exit(1)
    return PROMPT_FILE.read_text(encoding="utf-8")


def process_batch(batch_files: List[Path], system_prompt: str) -> Dict[str, any]:
    """Sends a batch of documents to Gemini and returns a mapping of filename to augmented content and token usage."""
    
    batch_content = []
    batch_names = [f.name for f in batch_files]
    for file_path in batch_files:
        content = file_path.read_text(encoding="utf-8")
        batch_content.append(f'<manual filename="{file_path.name}">\n{content}\n</manual>')
    
    user_prompt = (
        f"SYSTEM INSTRUCTIONS:\n{system_prompt}\n\n"
        "I am providing multiple drug manuals in Macedonian. "
        "Process each one according to the system instructions. "
        "Return each refined manual wrapped in its original <manual filename=\"...\"> tag.\n\n"
        + "\n\n".join(batch_content)
    )

    # Proactive token counting
    try:
        token_count_resp = client.models.count_tokens(
            model=MODEL_NAME,
            contents=user_prompt
        )
        estimated_tokens = token_count_resp.total_tokens
        logger.info(f"Estimated request tokens: {estimated_tokens}")
        if estimated_tokens > TPM_LIMIT:
            logger.warning(f"Request tokens ({estimated_tokens}) exceed TPM limit ({TPM_LIMIT}). This might fail or be throttled.")
    except Exception as e:
        logger.warning(f"Token counting failed: {e}")
        estimated_tokens = 0

    for attempt in range(MAX_RETRIES):
        try:
            logger.info(f"Sending request to Gemini (Attempt {attempt + 1}/{MAX_RETRIES})...")
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=user_prompt
            )
            
            # Handle potential safety blocks or empty responses
            if not response.text:
                logger.warning(f"Empty response on attempt {attempt + 1}. Safety ratings: {response.candidates[0].safety_ratings if response.candidates else 'N/A'}")
                continue

            usage = response.usage_metadata
            results = {
                "_metadata": {
                    "prompt_tokens": usage.prompt_token_count if usage else estimated_tokens,
                    "candidate_tokens": usage.candidates_token_count if usage else 0,
                    "total_tokens": usage.total_token_count if usage else estimated_tokens
                }
            }
            
            pattern = r'<manual filename="([^"]+)">\s*(.*?)\s*</manual>'
            matches = re.findall(pattern, response.text, re.DOTALL)

            logger.info(f"Received response. Found {len(matches)} manuals in output.")

            for filename, content in matches:
                results[filename] = content.strip()

            if len(matches) < len(batch_files) and len(matches) > 0:
                missing = set(batch_names) - set([m[0] for m in matches])
                logger.warning(f"Partial results: Got {len(matches)}/{len(batch_files)} files. Missing: {', '.join(missing)}")

            if not matches and len(batch_files) > 0:
                logger.warning(f"No tags found in response on attempt {attempt + 1}. Response length: {len(response.text)}")
                continue

            return results

        except Exception as e:
            if "429" in str(e):
                wait = (2 ** attempt) + 5
                logger.warning(f"Rate limit hit (429). Waiting {wait}s before retry {attempt + 1}/{MAX_RETRIES}...")
                time.sleep(wait)
            else:
                logger.error(f"Error on attempt {attempt + 1}: {e}")
                time.sleep(2)
    
    return {}


def augment_documents() -> None:
    if not INPUT_DIR.exists():
        logger.error(f"Input directory does not exist: {INPUT_DIR}")
        return

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    system_prompt = get_system_prompt()

    # Get list of files not yet processed
    all_files = sorted(list(INPUT_DIR.glob("*.md")))
    files_to_process = [
        f for f in all_files if not (OUTPUT_DIR / f.name).exists()
    ]

    if not files_to_process:
        logger.info("No new documents to process.")
        return

    total_files = len(files_to_process)
    logger.info(f"Starting augmentation for {total_files} files in batches of {BATCH_SIZE}...")

    for i in range(0, total_files, BATCH_SIZE):
        batch = files_to_process[i : i + BATCH_SIZE]
        batch_names = [f.name for f in batch]
        
        logger.info(f"--- Batch {i//BATCH_SIZE + 1} ---")
        logger.info(f"Progress: {i+len(batch)}/{total_files} files")
        logger.info(f"Processing: {', '.join(batch_names)}")
        
        start_time = time.time()
        results = process_batch(batch, system_prompt)
        
        if not results:
            logger.warning(f"Batch {i//BATCH_SIZE + 1} returned no results. Skipping.")
            tokens_used = 0
        else:
            metadata = results.pop("_metadata", {})
            prompt_tokens = metadata.get("prompt_tokens", 0)
            candidate_tokens = metadata.get("candidate_tokens", 0)
            tokens_used = metadata.get("total_tokens", 0)
            
            usage_stats["prompt_tokens"] += prompt_tokens
            usage_stats["candidate_tokens"] += candidate_tokens
            
            batch_cost = (prompt_tokens / 1_000_000 * PRICE_PER_1M_INPUT) + \
                         (candidate_tokens / 1_000_000 * PRICE_PER_1M_OUTPUT)
            
            for filename, content in results.items():
                output_path = OUTPUT_DIR / filename
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(content)
                usage_stats["total_files"] += 1
                logger.info(f"Saved: {filename}")

            logger.info(f"Batch usage: {tokens_used} tokens (In: {prompt_tokens}, Out: {candidate_tokens})")
            logger.info(f"Batch cost: ${batch_cost:.6f}")

        # Rate limiting: 
        rpm_wait = 60 / RPM_LIMIT
        tpm_wait = tokens_used / (TPM_LIMIT / 60)
        
        wait_time = max(rpm_wait, tpm_wait)
        elapsed = time.time() - start_time
        actual_wait = max(wait_time - elapsed, 0)
        
        if i + BATCH_SIZE < total_files:
            if actual_wait > 0:
                logger.info(f"Waiting {actual_wait:.2f}s to respect rate limits...")
                time.sleep(actual_wait)

    # Final summary
    total_duration = time.time() - usage_stats["start_time"]
    total_cost = (usage_stats["prompt_tokens"] / 1_000_000 * PRICE_PER_1M_INPUT) + \
                 (usage_stats["candidate_tokens"] / 1_000_000 * PRICE_PER_1M_OUTPUT)
    
    logger.info("=" * 50)
    logger.info("AUGMENTATION COMPLETED")
    logger.info(f"Total files processed: {usage_stats['total_files']}")
    logger.info(f"Total prompt tokens: {usage_stats['prompt_tokens']}")
    logger.info(f"Total candidate tokens: {usage_stats['candidate_tokens']}")
    logger.info(f"Total cost: ${total_cost:.4f}")
    logger.info(f"Total duration: {total_duration:.2f}s")
    logger.info(f"Logs saved to: {LOG_FILE}")
    logger.info("=" * 50)


if __name__ == "__main__":
    try:
        augment_documents()
    except KeyboardInterrupt:
        logger.info("Process interrupted by user.")
