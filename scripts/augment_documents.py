import logging
import os
from pathlib import Path

from anthropic import Anthropic

# Configuration
PROJECT_ROOT = Path(__file__).parent.parent
INPUT_DIR = PROJECT_ROOT / "documents" / "parsed"
OUTPUT_DIR = PROJECT_ROOT / "documents" / "augmented"

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# System prompt for Claude to augment Macedonian drug manuals
AUGMENTATION_PROMPT = """You are an expert in Macedonian language (Cyrillic script) and pharmaceutical document processing. Your task is to refine and repair OCR-parsed drug manuals while strictly preserving the original content.

**CRITICAL RULES:**
1. **DO NOT REWRITE OR SUMMARIZE** - Your goal is to restore the original text, not change it
2. **DO NOT ALTER** medical facts, dosages, or clinical instructions
3. **PRESERVE** all information verbatim, only fixing OCR errors and formatting

**Your Tasks:**

1. **OCR Artifact Repair:**
   - Fix common OCR errors in Macedonian Cyrillic (e.g., '3' → 'з', '0' → 'о', 'н' → 'њ', 'л' → 'љ', Latin 'p' → Cyrillic 'р')
   - Repair broken words from bad scans or line breaks
   - Fix obvious typos in medical terminology while preserving meaning
   - Ensure consistent Macedonian alphabet usage

2. **Formatting & Structure:**
   - Standardize Markdown headers (#, ##, ###)
   - Repair broken tables (align columns, make data readable)
   - Fix list formatting (bullets and numbers)
   - Remove HTML comments like <!-- image -->

3. **Logical Reordering:**
   - Ensure logical flow per standard drug manual structure (Indication, Dosage, Contraindications, etc.)
   - Remove/relocate misplaced page numbers or headers/footers

4. **Add Disclaimer (at the end):**
```markdown
## Изјава за дополнување со ВИ (AI Augmentation Disclaimer)
Овој документ е дополнет со помош на вештачка интелигенција со цел да се подобри читливоста, форматирањето и структурната точност на оригиналниот изворен текст.
```

5. **Add Summary of Changes (at the end):**
```markdown
## Резиме на промени
- [List specific corrections made, e.g., "Поправени табели во делот за дозирање", "Коригирани OCR грешки во текстот"]
```

**Output:** Return ONLY the corrected Markdown document with no additional commentary."""


def augment_document(content: str, api_key: str) -> str:
    """Augments a single document using Claude API."""
    client = Anthropic(api_key=api_key)
    
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=16000,
        temperature=0,
        system=AUGMENTATION_PROMPT,
        messages=[
            {
                "role": "user",
                "content": f"Please augment this Macedonian drug manual:\n\n{content}"
            }
        ]
    )
    
    return message.content[0].text


def augment_documents() -> None:
    """Processes all parsed documents and saves augmented versions."""
    # Check for API key
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        logger.error("ANTHROPIC_API_KEY environment variable not set.")
        logger.error("Please set it in your .env file or environment.")
        return

    if not INPUT_DIR.exists():
        logger.error(f"Input directory does not exist: {INPUT_DIR}")
        return

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Get all markdown files that haven't been processed yet
    files_to_process = [
        f for f in INPUT_DIR.glob("*.md")
        if not (OUTPUT_DIR / f.name).exists()
    ]

    if not files_to_process:
        logger.info("No new documents to augment.")
        return

    total_files = len(files_to_process)
    for i, file_path in enumerate(files_to_process, 1):
        output_path = OUTPUT_DIR / file_path.name
        logger.info(f"[{i}/{total_files}] Augmenting: {file_path.name}")

        try:
            # Read the parsed document
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Augment using Claude API
            augmented_content = augment_document(content, api_key)

            # Save the augmented document
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(augmented_content)

            logger.info(f"✓ Successfully augmented: {file_path.name}")

        except Exception as e:
            logger.error(f"✗ Failed to augment {file_path.name}: {e}")


if __name__ == "__main__":
    try:
        augment_documents()
    except KeyboardInterrupt:
        logger.info("Process interrupted by user.")
