#!/usr/bin/env bash
# Download all PDF files referenced in fontes.csv files

set -euo pipefail

YEAR="${1:-}"

if [ -z "$YEAR" ]; then
    echo "Usage: $0 <year>"
    echo "Example: $0 2024"
    exit 1
fi

DATA_DIR="data/$YEAR/raw"
FONTES_CSV="$DATA_DIR/fontes.csv"

if [ ! -f "$FONTES_CSV" ]; then
    echo "Error: $FONTES_CSV not found"
    exit 1
fi

echo "Downloading PDFs for year $YEAR..."
echo ""

DOWNLOADED=0
SKIPPED=0
FAILED=0

# Read CSV line by line, skip header
while IFS=, read -r empresa url; do
    # Convert company name to lowercase for filename
    filename=$(echo "$empresa" | tr '[:upper:]' '[:lower:]').pdf
    output_path="$DATA_DIR/$filename"
    
    # Skip if already exists
    if [ -f "$output_path" ]; then
        echo "⏭  Skipping $empresa (already exists)"
        ((SKIPPED++)) || true
        continue
    fi
    
    echo "⬇️  Downloading $empresa..."
    
    if curl -L -f -o "$output_path" "$url" --progress-bar; then
        echo "✅ Success: $output_path"
        ((DOWNLOADED++)) || true
    else
        echo "❌ Failed: $empresa"
        rm -f "$output_path"
        ((FAILED++)) || true
    fi
    echo ""
done < <(tail -n +2 "$FONTES_CSV")

echo "────────────────────────"
echo "Downloaded: $DOWNLOADED"
echo "Skipped: $SKIPPED"
echo "Failed: $FAILED"
