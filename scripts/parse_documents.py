import logging
import shutil
from pathlib import Path

import torch
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import (
    AcceleratorDevice,
    PdfPipelineOptions,
    TesseractCliOcrOptions,
)
from docling.document_converter import DocumentConverter, PdfFormatOption

# Configuration
PROJECT_ROOT = Path(__file__).parent.parent
INPUT_DIR = PROJECT_ROOT / "documents" / "original"
OUTPUT_DIR = PROJECT_ROOT / "documents" / "parsed"

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def parse_documents() -> None:
    """Parses all documents in the input directory and saves them as markdown."""
    if not INPUT_DIR.exists():
        logger.error(f"Input directory does not exist: {INPUT_DIR}. Did you download the documents?")
        return

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Configure pipeline options
    pipeline_options = PdfPipelineOptions()
    
    if torch.cuda.is_available():
        pipeline_options.accelerator_options.device = AcceleratorDevice.CUDA
        logger.info("Using CUDA acceleration.")
    else:
        pipeline_options.accelerator_options.device = AcceleratorDevice.CPU
        logger.info("CUDA not available, falling back to CPU.")

    if shutil.which("tesseract"):
        # Tesseract uses 3-letter ISO codes (mkd for Macedonian, eng for English)
        pipeline_options.ocr_options = TesseractCliOcrOptions(lang=["mkd", "eng"])
        logger.info("Using Tesseract CLI OCR (Macedonian + English).")
    else:
        # EasyOCR uses 2-letter ISO codes (mk for Macedonian, en for English)
        pipeline_options.ocr_options.lang = ["mk", "en"]
        logger.info("Tesseract not found, falling back to EasyOCR (Macedonian + English).")

    converter = DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
        }
    )

    # Supported extensions for docling
    supported_extensions = {".pdf", ".docx", ".pptx", ".xlsx", ".html"}
    
    files_to_parse = [
        f for f in INPUT_DIR.iterdir() 
        if f.suffix.lower() in supported_extensions and not (OUTPUT_DIR / f"{f.stem}.md").exists()
    ]

    if not files_to_parse:
        logger.info("No new documents to parse.")
        return

    total_files = len(files_to_parse)
    for i, file_path in enumerate(files_to_parse, 1):
        output_path = OUTPUT_DIR / f"{file_path.stem}.md"
        logger.info(f"[{i}/{total_files}] Parsing: {file_path.name}")

        try:
            result = converter.convert(file_path)
            markdown_content = result.document.export_to_markdown()

            with open(output_path, "w", encoding="utf-8") as f:
                f.write(markdown_content)

        except Exception as e:
            logger.error(f"Failed to parse {file_path.name}: {e}")


if __name__ == "__main__":
    try:
        parse_documents()
    except KeyboardInterrupt:
        logger.info("Process interrupted by user.")
