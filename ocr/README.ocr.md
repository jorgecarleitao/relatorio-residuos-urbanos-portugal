# OCR PDF to Text Extraction

Robust OCR pipeline using OCRmyPDF + Tesseract for extracting text from scanned/image-based PDFs.

## Quick Start

### Build the image

```bash
docker build -f Dockerfile.ocr -t residuos-ocr .
```

### Process a single PDF

```bash
docker run --rm \
  -v "$PWD:/work" \
  -w /work \
  -e OCR_LANGS=por+eng \
  residuos-ocr input.pdf output.txt
```

### Batch processing

Process all PDFs in a directory:

```bash
for pdf in data/*/raw/*.pdf; do
  txt="${pdf%.pdf}.txt"
  docker run --rm \
    -v "$PWD:/work" \
    -w /work \
    residuos-ocr "$pdf" "$txt"
done
```

## Supported Languages

By default, Portuguese and English are enabled (`por+eng`).

To change languages, set the `OCR_LANGS` environment variable:

```bash
docker run --rm \
  -v "$PWD:/work" \
  -e OCR_LANGS=por+eng+fra+spa \
  residuos-ocr input.pdf output.txt
```

Common language codes:
- `por` - Portuguese
- `eng` - English
- `spa` - Spanish
- `fra` - French
- `deu` - German

## How It Works

1. **OCRmyPDF** processes the input PDF:
   - Rotates pages to correct orientation
   - Deskews tilted scans
   - Runs Tesseract OCR to add a searchable text layer
   - Outputs a new PDF with embedded text

2. **pdftotext** extracts the text layer to a plain `.txt` file

## Performance Notes

- First run will download the Docker image (~500MB)
- OCR processing time depends on page count and image quality
- Typical speed: 1-3 pages per second
- Multi-core processing is enabled by default

## Troubleshooting

### Poor OCR quality

Try adjusting OCR parameters by modifying `pdf2txt.sh`:

```bash
ocrmypdf \
  --rotate-pages \
  --deskew \
  --clean \
  --optimize 0 \
  -l "$LANGS" \
  "$INPUT" "$TMP_PDF"
```

### Language not supported

Check available languages in the container:

```bash
docker run --rm --entrypoint tesseract residuos-ocr --list-langs
```

### PDF already has text

Remove `--skip-text` flag in `pdf2txt.sh` to re-OCR pages with existing text.
