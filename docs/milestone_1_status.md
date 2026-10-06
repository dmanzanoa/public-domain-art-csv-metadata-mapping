# Milestone 1 Status

## Completed

- Generated an exactly 50-image verification sample.
- Preserved source provenance, object URLs, original image URLs, licensing labels, and public-domain flags for every record.
- Validated all image files with Pillow.
- Applied configurable quality thresholds: minimum long edge and megapixels.
- Produced deterministic filenames and category folders.
- Generated canonical master metadata.
- Generated Shopify CSV output with four configured print-size variants per product.
- Verified duplicate source IDs, filenames, and SHA256 hashes are absent.
- Added manifest-based resume support for downloads.
- Added tests for classification, filename generation, hashing/deduplication, manifest behavior, Met normalization, image validation, downloader behavior, and Shopify export.

## Verification Sample Results

```text
Total images: 50
Metadata rows: 50
Shopify variant rows: 200
Validation errors: 0
Duplicate source IDs: 0
Duplicate filenames: 0
Duplicate image hashes: 0
```

Category distribution:

```text
Abstract:     8
Botanical:    8
Landscape:    9
Photography:  8
Australiana:  8
Fashion:      9
```

## Deliberate Scope Limits

This repository is a completed Milestone 1 verification sample, not the final 3,000-4,000 image production system. The following work remains before scaling:

- Add production adapters for Art Institute of Chicago, SMK, Rijksmuseum, and National Gallery of Art.
- Keep British Museum disabled unless an official unrestricted commercial reuse path is identified.
- Add source-specific rate-limit configuration and broader pagination controls.
- Add persistent rejected-record CSV output for full audit trails.
- Add disk-space checks and graceful shutdown handling for multi-thousand-image runs.
- Add hosted storage integration before populating Shopify `Image Src` values.
- Tune category rules against more sources and add manual review support for ambiguous records.

## How to Verify

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e ".[dev]"
pytest -q
python -m art_scraper validate-sample --directory verification_sample
```
