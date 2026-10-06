# Architecture and Implementation Sequence

## Repository Status

The project directory was empty at the start of this work. There was no existing source code, configuration, tests, or documentation to preserve.

## Design Goals

- Make licensing correctness the first gate, before image download.
- Normalize every source into one internal `Artwork` model.
- Keep source acquisition, image downloading, validation, deduplication, and Shopify export separate.
- Make the 50-image verification workflow the first real milestone.
- Keep the architecture scalable to thousands of images through manifest-based resume, source/category quotas, rate limiting, and duplicate checks.

## Proposed Structure

```text
README.md
pyproject.toml
config.yaml
docs/
  source_assessment.md
  architecture.md
src/
  art_scraper/
    __init__.py
    cli.py
    config.py
    models.py
    sources/
      base.py
      met.py
      artic.py
      smk.py
      rijksmuseum.py
      nga.py
      british_museum.py
    classification/
      classifier.py
      rules.yaml
    pipeline/
      discovery.py
      downloader.py
      validation.py
      deduplication.py
      manifest.py
    exporters/
      shopify.py
    utils/
      filenames.py
      hashing.py
      logging.py
tests/
output/
```

## Core Components

### Source adapters

Each adapter implements a shared interface:

```python
class SourceAdapter(Protocol):
    source_name: str

    def discover(self, query: DiscoveryQuery) -> Iterable[Artwork]:
        ...
```

Adapters are responsible for:

- Calling official APIs/datasets only.
- Applying source-specific license checks.
- Mapping source metadata into `Artwork`.
- Preserving raw source metadata.

Adapters are not responsible for:

- Downloading image bytes.
- Writing Shopify rows.
- Making category decisions beyond preserving source metadata.

### Normalized model

Use Pydantic or dataclasses for `Artwork`, `ImageFile`, `ClassificationResult`, `ManifestRecord`, and `ValidationReport`. Pydantic gives stronger runtime validation, but dataclasses plus explicit validators are also acceptable. My recommendation is Pydantic because this pipeline is metadata-heavy.

### Classification

Use deterministic, editable YAML rules:

- weighted keyword matches across title, medium, department, classification, subject, tags, geography, and creator fields
- stronger rules for photography and australiana
- output category, reason, and score

Unknown or weak matches should be rejected or queued for review rather than forced into a category.

### Downloader

The downloader should:

- use `requests`/`httpx` with retries, backoff, jitter, and source-specific rate limits
- stream files to temporary paths, validate with Pillow, then atomically move into the category folder
- compute SHA256
- reject thumbnails and corrupt files
- update manifest records after each meaningful state transition

### Manifest and resume

Use JSONL for append-friendly state plus a loader that resolves the latest record per `source + source_id`.

Statuses:

```text
discovered
metadata_validated
queued
downloaded
rejected
failed
duplicate
```

This makes interruption safe and allows targeted retries.

### Validation

Validation should be a separate command that checks:

- every metadata row points to an existing image
- every category image has exactly one metadata row
- images open with Pillow
- image quality thresholds pass
- source IDs, filenames, and SHA256 hashes are unique
- public-domain/license fields are present
- Shopify export has exactly the configured variant count per product

### Shopify export

Shopify export reads only validated master metadata. It should never talk to museum APIs and should not fabricate image hosting URLs. `shopify_image_src` remains blank until storage/upload is implemented.

## Implementation Sequence

1. Scaffold project packaging, config, models, source base interface, and CLI shell.
2. Implement filename, hashing, manifest, and validation utilities with tests.
3. Implement classifier using `classification/rules.yaml` with tests.
4. Implement the Met adapter first and unit-test metadata normalization/license filtering with mocked API responses.
5. Run a tiny live discovery/download verification of 5-10 Met records, respecting rate limits.
6. Generate canonical metadata CSV and Shopify CSV for that mini-sample.
7. Add AIC, then SMK, then NGA/Rijksmuseum adapters.
8. Produce exactly 50 validated images if strict license and quality gates allow it; otherwise report category/source shortages.
9. Harden for 3,000-4,000 records: quotas, disk-space checks, graceful shutdown, source-specific throttling, and retry commands.

## First Adapter Recommendation

Start with The Met:

- no authentication
- explicit `isPublicDomain` flag
- direct `primaryImage` URL
- rich enough metadata for category tests
- easiest path to prove provenance, file naming, image validation, manifest resume, and Shopify export without solving IIIF first

## Initial Commands After Scaffolding

```bash
python -m art_scraper source-status
python -m art_scraper discover --source met --limit 25
python -m art_scraper download --source met --target 10
python -m art_scraper validate
python -m art_scraper export-shopify
pytest
```

## Assumptions

- Python 3.11+ is available.
- Network access will be needed for live API discovery/downloads, but tests should mock external calls.
- The first local output target will be `output/`, while the final 50-image handoff can be copied or generated into `verification_sample/`.
- Google Drive delivery is intentionally out of scope until local validation passes.
