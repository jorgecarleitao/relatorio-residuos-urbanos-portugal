#!/usr/bin/env bash
# Batch OCR processor for all PDFs in data directories

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_DIR"

IMAGE_NAME="residuos-ocr:latest"

# Find all PDFs
PDFS=$(find data -type f -name "*.pdf" 2>/dev/null || true)

if [ -z "$PDFS" ]; then
    echo "No PDF files found in data directory"
    exit 0
fi

COUNT=$(echo "$PDFS" | wc -l)
echo "Found $COUNT PDF file(s) to process"
echo ""

PROCESSED=0
FAILED=0

while IFS= read -r pdf_path; do
    # Generate output path: replace .pdf with .txt
    txt_path="${pdf_path%.pdf}_ocr.txt"
    
    # Skip if already processed
    if [ -f "$txt_path" ]; then
        echo "⏭  Skipping $pdf_path (already processed)"
        continue
    fi
    
    echo "🔄 Processing: $pdf_path"
    
    if docker run --rm \
        -v "$PWD:/work" \
        -w /work \
        -e OCR_LANGS=por+eng \
        "$IMAGE_NAME" "$pdf_path" "$txt_path"; then
        echo "✅ Success: $txt_path"
        PROCESSED=$((PROCESSED + 1))
    else
        echo "❌ Failed: $pdf_path"
        FAILED=$((FAILED + 1))
    fi
    echo ""
done < <(echo "$PDFS")

echo "────────────────────────"
echo "Processed: $PROCESSED"
echo "Failed: $FAILED"
echo "Total: $COUNT"
