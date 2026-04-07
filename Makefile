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
REPORT_PDF = $(BUILD_DIR)/index.pdf

# Targets
.PHONY: all html pdf clean help setup figures diagrams tables

all: html

help:
	@echo "Waste Management Report Build System"
	@echo ""
	@echo "Available targets:"
	@echo "  make html       - Generate HTML report (default)"
	@echo "  make pdf        - Generate PDF report"
	@echo "  make all        - Generate HTML report"
	@echo "  make setup      - Setup Python environment"
	@echo "  make figures    - Generate all figures"
	@echo "  make diagrams   - Copy diagrams to build"
	@echo "  make tables     - Generate tables from CSV data"
	@echo "  make clean      - Remove generated files"
	@echo "  make help       - Show this help message"

setup: $(VENV)

figures: $(VENV)
	@echo "Generating figures..."
	@$(PYTHON) src/figures.py

tables: $(VENV)
	@echo "Generating tables..."
	@$(PYTHON) src/tables.py

diagrams: | $(BUILD_DIR)
	@echo "Copying diagrams..."
	@mkdir -p $(DIAGRAMS_DIR)
	@cp -r src/diagrams/*.svg $(DIAGRAMS_DIR)/ 2>/dev/null || true
	@echo "✓ Diagrams copied"

html: figures tables diagrams $(REPORT_HTML)
	@echo "✓ HTML report generated successfully"

pdf: figures tables diagrams $(REPORT_PDF)
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
	$(ADOC) -a revnumber=$(GIT_VERSION) -o $@ $(REPORT)

# PDF generation
$(REPORT_PDF): $(REPORT) | $(BUILD_DIR)
	@echo "Building $@..."
	$(ADOC_PDF) -a revnumber=$(GIT_VERSION) -a imagesdir=$(BUILD_DIR) -o $@ $(REPORT)

# Create build directory
$(BUILD_DIR):
	@mkdir -p $(BUILD_DIR)

# Clean generated files
clean:
	@echo "Cleaning generated files..."
	rm -rf $(BUILD_DIR) $(VENV)
	@echo "✓ Clean complete"
