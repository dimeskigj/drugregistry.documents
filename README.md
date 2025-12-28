# Drug Registry Documents Processing

This project provides a pipeline for downloading and parsing drug manuals from the Macedonian Drug Registry.

## Document Processing Pipeline

To process the documents, follow these steps in order:

1. **Download**: Fetch original PDFs from the API.
   ```bash
   python scripts/download_manuals.py
   ```
2. **Parse**: Convert PDFs to Markdown using OCR (GPU-accelerated).
   ```bash
   python scripts/parse_documents.py
   ```
3. **Cleanup**: Remove documents that contain no text (only image tags).
   ```bash
   python scripts/cleanup_empty_docs.py
   ```
4. **Augment**: Refine and repair OCR artifacts in Macedonian drug manuals using AI.
   ```bash
   python scripts/augment_documents.py
   ```

## Naming Convention

All documents follow a standardized naming convention:

`{DecisionNumber}_{DecisionDate}.pdf` (or `.md`)

- **DecisionNumber**: The unique identifier from the registry (e.g., `11-10042`).
- **DecisionDate**: The date of the decision in `YYYY-MM-DD` format.
- **Example**: `11-10042_2021-03-03.pdf`

## Prerequisites

- Python 3.12 or higher
- [uv](https://github.com/astral-sh/uv) for dependency management
- [Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki) (with Macedonian language data)

## Setup

1. **Install dependencies**:
   ```bash
   uv sync
   ```
   *Note: The project uses CUDA-enabled PyTorch by default for GPU acceleration.*

2. **Configure environment**:
   Copy `.env.example` to `.env` and set the required API keys:
   ```dotenv
   API_URL=https://your-api-endpoint.com
   ANTHROPIC_API_KEY=your_anthropic_api_key_here
   ```

## Project Structure

- `scripts/download_manuals.py`: Downloads manuals from the API.
- `scripts/parse_documents.py`: Parses PDFs to Markdown using GPU/Tesseract.
- `scripts/cleanup_empty_docs.py`: Deletes Markdown files that only contain image tags.
- `scripts/augment_documents.py`: Augments parsed documents using AI to repair OCR artifacts and improve formatting.
- `documents/original/`: Directory for downloaded PDFs.
- `documents/parsed/`: Directory for parsed Markdown files.
- `documents/augmented/`: Directory for AI-augmented Markdown files.
- `pyproject.toml`: Dependency definitions.
