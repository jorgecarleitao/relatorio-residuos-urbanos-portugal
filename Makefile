# Makefile for Waste Management Report

# Variables
# Use Docker if asciidoctor is not installed locally
DOCKER_IMAGE = asciidoctor/docker-asciidoctor:latest
DOCKER_RUN = docker run --rm -v $(PWD):/documents $(DOCKER_IMAGE)

# Try local first, fall back to Docker
ADOC := $(shell command -v asciidoctor 2> /dev/null)
ADOC_PDF_BIN := $(shell command -v asciidoctor-pdf 2> /dev/null)
ifndef ADOC
    ADOC = $(DOCKER_RUN) asciidoctor
    ADOC_PDF = $(DOCKER_RUN) asciidoctor-pdf
else
    ADOC = asciidoctor
    ifndef ADOC_PDF_BIN
        ADOC_PDF = $(DOCKER_RUN) asciidoctor-pdf
    else
        ADOC_PDF = asciidoctor-pdf
    endif
endif

# Build directory
BUILD_DIR = build
FIGURES_DIR = $(BUILD_DIR)/figures
DIAGRAMS_DIR = $(BUILD_DIR)/diagrams
TABLES_DIR = $(BUILD_DIR)/tables

# Python environment
VENV = venv
PYTHON = $(VENV)/bin/python
PIP = $(VENV)/bin/pip

# Git version: tag name if on a tag, short commit hash otherwise
GIT_VERSION := $(shell git describe --exact-match --tags 2>/dev/null || git rev-parse --short HEAD 2>/dev/null || echo unknown)

# Source file
REPORT = index.adoc

# Output files
REPORT_HTML = $(BUILD_DIR)/index.html
REPORT_PDF = $(BUILD_DIR)/relatorio.pdf

# OCR configuration
OCR_IMAGE = residuos-ocr:latest
OCR_DOCKERFILE = ocr/Dockerfile.ocr
OCR_DIR = ocr

# Targets
.PHONY: all html pdf clean help setup generate diagrams check-spelling lint ocr-build ocr download-2024 download-2025 download-all

all: html

help:
	@echo "Waste Management Report Build System"
	@echo ""
	@echo "Available targets:"
	@echo "  make html       - Generate HTML report (default)"
	@echo "  make pdf        - Generate PDF report"
	@echo "  make all        - Generate HTML report"
	@echo "  make setup      - Setup Python environment"
	@echo "  make generate   - Generate all figures and tables"
	@echo "  make diagrams   - Copy diagrams to build"
	@echo "  make check-spelling - Check grammar and spelling (Portuguese)"
	@echo "  make lint       - Alias for check-spelling"
	@echo "  make download-2024  - Download PDFs from fontes.csv (2024)"
	@echo "  make download-2025  - Download PDFs from fontes.csv (2025)"
	@echo "  make download-all   - Download PDFs for all years"
	@echo "  make ocr-build  - Build OCR Docker image"
	@echo "  make ocr  - Process all PDFs in data/ with OCR"
	@echo "  make clean      - Remove generated files"
	@echo "  make help       - Show this help message"

setup: $(VENV)

generate: $(VENV)
	@$(PYTHON) src/generate.py

diagrams: | $(BUILD_DIR)
	@echo "Copying diagrams..."
	@mkdir -p $(DIAGRAMS_DIR)
	@cp -r src/diagrams/*.svg $(DIAGRAMS_DIR)/ 2>/dev/null || true
	@echo "✓ Diagrams copied"

check-spelling: $(VENV)
	@echo "Checking grammar and spelling..."
	@$(PYTHON) src/check_spelling.py

lint: check-spelling

html: generate diagrams $(REPORT_HTML)
	@echo "✓ HTML report generated successfully"

pdf: generate diagrams $(REPORT_PDF)
	@echo "✓ PDF report generated successfully"

# Python virtual environment setup
$(VENV):
	@echo "Setting up Python virtual environment..."
	@python3 -m venv $(VENV)
	@$(PIP) install --upgrade pip -q
	@$(PIP) install -r src/requirements.txt -q
	@echo "✓ Virtual environment ready"

# HTML generation
$(REPORT_HTML): $(REPORT) | $(BUILD_DIR)
	@echo "Building $@..."
	$(ADOC) -a lang=pt -a revnumber=$(GIT_VERSION) -o $@ $(REPORT)

# PDF generation
$(REPORT_PDF): $(REPORT) | $(BUILD_DIR)
	@echo "Building $@..."
	$(ADOC_PDF) -a lang=pt -a revnumber=$(GIT_VERSION) -a imagesdir=$(BUILD_DIR) -o $@ $(REPORT)

# Create build directory
$(BUILD_DIR):
	@mkdir -p $(BUILD_DIR)

# Download targets
download-2024:
	@chmod +x download_pdfs.sh
	@./download_pdfs.sh 2024

download-2025:
	@chmod +x download_pdfs.sh
	@./download_pdfs.sh 2025

download-all: download-2024 download-2025
	@echo "✓ All PDFs downloaded"

# OCR targets
.ocr-built: $(OCR_DOCKERFILE) $(OCR_DIR)/pdf2txt.sh $(OCR_DIR)/batch_ocr.sh
	@echo "Building OCR Docker image..."
	docker build -f $(OCR_DOCKERFILE) -t $(OCR_IMAGE) .
	@touch .ocr-built
	@echo "✓ OCR image built: $(OCR_IMAGE)"

ocr-build: .ocr-built

ocr: .ocr-built download-all
	@echo "Processing all PDFs with OCR..."
	@chmod +x $(OCR_DIR)/batch_ocr.sh
	@./$(OCR_DIR)/batch_ocr.sh

# Clean generated files
clean:
	@echo "Cleaning generated files..."
	rm -rf $(BUILD_DIR) $(VENV) .ocr-built
	@echo "✓ Clean complete"
