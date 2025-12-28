# AI Augmentation Prompt (Macedonian Drug Manuals)

**Task**: Process and refine drug manuals parsed by `docling`. The source text is in **Macedonian (Cyrillic)**.

**Input Path**: `documents/parsed/`
**Output Path**: `documents/augmented/`

**Instructions**:
For each Macedonian Markdown file, perform the following:

1. **OCR Artifact Repair (CRITICAL)**:
   - **DO NOT REWRITE OR SUMMARIZE THE TEXT.** Your goal is to restore the original text, not change it.
   - Fix OCR artifacts common in English and Macedonian Cyrillic (e.g., confusion between 'з' and '3', 'о' and '0', 'њ' and 'н', 'љ' and 'л', or Latin 'p' instead of Cyrillic 'р').
   - Repair broken words caused by bad scans or line breaks.
   - Correct obvious typos in medical terminology while preserving the original meaning.
   - Ensure consistent use of the Macedonian alphabet.

2. **Formatting & Structure**:
   - Standardize Markdown headers (`#`, `##`, `###`).
   - Repair broken tables, ensuring columns align and data is readable.
   - Fix list formatting (bullet points and numbered lists).

3. **Logical Reordering**:
   - Ensure the document flows logically according to standard drug manual structures (Indication, Dosage, Contraindications, etc.).
   - Remove or relocate misplaced text like page numbers or headers/footers.

4. **Add Disclaimer (In Macedonian)**:
   - Append a section at the end:
     ```markdown
     ## Изјава за дополнување со ВИ (AI Augmentation Disclaimer)
     Овој документ е дополнет со помош на вештачка интелигенција со цел да се подобри читливоста, форматирањето и структурната точност на оригиналниот изворен текст.
     ```

5. **Summary of Changes (In Macedonian)**:
   - Append a section:
     ```markdown
     ## Резиме на промени
     - [Краток опис на направените корекции, на пр. "Поправени табели во делот за дозирање", "Коригирани OCR грешки во текстот"]
     ```

**Constraints**:
- **STRICT NON-MODIFICATION**: Do not add, remove, or paraphrase any information. The output must be a verbatim restoration of the original document, minus the OCR errors.
- **DO NOT** alter medical facts, dosages, or clinical instructions.
- Maintain the formal tone of the original document.
- Ensure the output is valid Markdown.
