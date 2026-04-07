#!/usr/bin/env bash
set -euo pipefail

# Usage: pdf2txt input.pdf output.txt

INPUT="${1:?ERROR: input PDF file required}"
OUTPUT="${2:?ERROR: output TXT file required}"

# Default to Portuguese + English, override with OCR_LANGS env var
LANGS="${OCR_LANGS:-por+eng}"

TMP_TXT="/tmp/direct_text.txt"
TMP_PDF="/tmp/ocr_output.pdf"

echo "Processing: $INPUT"

# First, try direct text extraction
pdftotext "$INPUT" "$TMP_TXT" 2>/dev/null || true

# Count non-whitespace characters
TEXT_LENGTH=$(tr -d '[:space:]' < "$TMP_TXT" | wc -c)

# If we got substantial text (>100 chars), use it directly
if [ "$TEXT_LENGTH" -gt 100 ]; then
    echo "✓ PDF has text layer, extracting directly"
    mv "$TMP_TXT" "$OUTPUT"
else
    echo "⚠ PDF needs OCR (text layer missing or minimal)"
    echo "Languages: $LANGS"
    
    # Run OCRmyPDF to add searchable text layer
    ocrmypdf \
      --force-ocr \
      --rotate-pages \
      --deskew \
      --clean \
      -l "$LANGS" \
      "$INPUT" "$TMP_PDF"
    
    # Extract text from the OCR'd PDF
    pdftotext "$TMP_PDF" "$OUTPUT"
    
    echo "✓ OCR complete"
fi

echo "Done! Text extracted to $OUTPUT"
