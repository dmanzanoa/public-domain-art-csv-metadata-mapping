# Public Domain Art CSV Metadata Mapping

A Python pipeline for collecting public-domain/open-access artwork metadata and images from museum sources, validating local image files, and exporting canonical metadata plus Shopify-compatible product CSV rows.

Milestone 1 is complete: the repository includes a validated 50-image verification sample in `verification_sample/`.

## What Is Included

- Official API-based Met source adapter.
- Strict public-domain/license filtering.
- Normalized artwork metadata model.
- YAML-backed deterministic category classifier.
- Resumable manifest-based image downloads.
- Pillow-based image validation and quality gates.
- Deterministic safe filenames.
- SHA256 duplicate checks.
- Canonical metadata CSV.
- Shopify product CSV with four size variants per artwork.
- Included 50-image verification sample.

## Verification Sample

```text
Total images: 50
Metadata rows: 50
Shopify variant rows: 200
Validation errors: 0
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

The sample package contains:

- `verification_sample/master_metadata.csv`
- `verification_sample/shopify_products.csv`
- `verification_sample/validation_report.json`
- six category folders containing the validated images

Shopify `Image Src` is intentionally blank because Shopify requires hosted image URLs. The pipeline does not fabricate public storage URLs.

## Setup

Python 3.11+ is recommended.

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e ".[dev]"
```

Dependency-only install, followed by editable package install:

```bash
pip install -r requirements-dev.txt
pip install -e .
```

## Verify The Repository

Run unit tests:

```bash
pytest -q
```

Validate the included 50-image sample:

```bash
python -m art_scraper validate-sample --directory verification_sample
```

Expected output:

```text
Metadata rows: 50
Image files: 50
Shopify rows: 200
Errors: 0
```

## CLI Examples

Inspect source status:

```bash
python -m art_scraper source-status
```

Discover Met records without downloading:

```bash
python -m art_scraper discover --source met --query landscape --limit 10
```

Download a small capped batch:

```bash
python -m art_scraper download --source met --query landscape --category landscape --target 2 --candidate-limit 20
```

Validate local generated output:

```bash
python -m art_scraper validate
```

Export Shopify rows from local generated output:

```bash
python -m art_scraper export-shopify
```

## Important Scope Notes

This repository completes the first 50-image verification milestone. It is not yet the full 3,000-4,000 image production pipeline. Remaining work includes adding the other museum adapters, source-specific rate-limit tuning, production-scale pagination, graceful shutdown handling, disk-space checks, richer rejected-record reporting, and hosted storage integration for Shopify image URLs.

See `docs/milestone_1_status.md` for the full status and remaining work.
