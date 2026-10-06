from __future__ import annotations

import argparse
import csv
from pathlib import Path

from art_scraper.classification import RuleBasedClassifier
from art_scraper.config import load_config
from art_scraper.exporters.shopify import SHOPIFY_COLUMNS, artwork_to_shopify_rows
from art_scraper.models import Artwork, ManifestStatus, VALID_CATEGORIES
from art_scraper.pipeline.downloader import ImageDownloader
from art_scraper.pipeline.manifest import Manifest
from art_scraper.pipeline.metadata import read_metadata_rows
from art_scraper.pipeline.validation import inspect_image, passes_quality
from art_scraper.sources.base import DiscoveryQuery
from art_scraper.sources.met import MetAdapter
from art_scraper.utils.filenames import deterministic_image_filename


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="art-scraper")
    parser.add_argument("--config", default="config.yaml")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("source-status")

    discover_parser = subparsers.add_parser("discover")
    discover_parser.add_argument("--source", default="met", choices=["met"])
    discover_parser.add_argument("--query", default="landscape")
    discover_parser.add_argument("--limit", type=int, default=10)

    download_parser = subparsers.add_parser("download")
    download_parser.add_argument("--source", default="met", choices=["met"])
    download_parser.add_argument("--query", default="landscape")
    download_parser.add_argument("--target", type=int, default=10)
    download_parser.add_argument("--candidate-limit", type=int, default=100)
    download_parser.add_argument("--category", choices=sorted(VALID_CATEGORIES))

    subparsers.add_parser("validate")

    validate_sample_parser = subparsers.add_parser("validate-sample")
    validate_sample_parser.add_argument("--directory", default="verification_sample")

    subparsers.add_parser("export-shopify")

    args = parser.parse_args(argv)
    config = load_config(args.config)

    if args.command == "source-status":
        print("met: available; official no-auth API; filters public-domain during normalization")
        print("british_museum: disabled; unrestricted commercial image reuse not confirmed")
        return 0

    if args.command == "discover":
        adapter = MetAdapter()
        classifier = RuleBasedClassifier.from_yaml()
        for artwork in adapter.discover(DiscoveryQuery(query=args.query, limit=args.limit)):
            classifier.apply(artwork)
            artwork.local_filename = deterministic_image_filename(artwork)
            category = artwork.category or "unclassified"
            print(f"{artwork.source}:{artwork.source_id}\t{category}\t{artwork.local_filename}\t{artwork.title}")
        return 0

    if args.command == "download":
        return _download(args, config)

    if args.command == "validate":
        output_dir = Path(config.get("output", {}).get("directory", "./output"))
        return _validate_output(output_dir, config)

    if args.command == "validate-sample":
        return _validate_sample(Path(args.directory), config)

    if args.command == "export-shopify":
        output_dir = Path(config.get("output", {}).get("directory", "./output"))
        return _export_shopify(output_dir, config)

    parser.error(f"Unknown command: {args.command}")
    return 2


def _download(args: argparse.Namespace, config: dict) -> int:
    output_dir = Path(config.get("output", {}).get("directory", "./output"))
    metadata_dir = output_dir / "metadata"
    manifest = Manifest(metadata_dir / "download_manifest.jsonl")
    downloader_config = config.get("downloader", {})
    quality_config = config.get("image_quality", {})
    downloader = ImageDownloader(
        output_dir=output_dir,
        manifest=manifest,
        metadata_csv=metadata_dir / "artworks.csv",
        min_long_edge=int(quality_config.get("min_long_edge", 2500)),
        min_megapixels=float(quality_config.get("min_megapixels", 4.0)),
        max_retries=int(downloader_config.get("max_retries", 5)),
        timeout=int(downloader_config.get("timeout_seconds", 30)),
    )
    adapter = MetAdapter(timeout=int(downloader_config.get("timeout_seconds", 30)))
    classifier = RuleBasedClassifier.from_yaml()
    downloaded = 0
    rejected = 0
    failed = 0
    skipped = 0

    for artwork in adapter.discover(DiscoveryQuery(query=args.query, limit=args.candidate_limit)):
        classifier.apply(artwork)
        if artwork.category is None:
            rejected += 1
            continue
        if args.category and artwork.category != args.category:
            rejected += 1
            continue
        artwork.local_filename = deterministic_image_filename(artwork)
        result = downloader.download(artwork)
        if result.status == ManifestStatus.DOWNLOADED:
            if result.reason == "already downloaded":
                skipped += 1
                continue
            downloaded += 1
            path_text = str(result.path or "")
            print(f"downloaded\t{artwork.source}:{artwork.source_id}\t{artwork.category}\t{path_text}")
            if downloaded >= args.target:
                break
        elif result.status == ManifestStatus.REJECTED:
            rejected += 1
            print(f"rejected\t{artwork.source}:{artwork.source_id}\t{result.reason}")
        elif result.status == ManifestStatus.FAILED:
            failed += 1
            print(f"failed\t{artwork.source}:{artwork.source_id}\t{result.reason}")

    print("========== DOWNLOAD SUMMARY ==========")
    print(f"Downloaded this run: {downloaded}")
    print(f"Skipped existing: {skipped}")
    print(f"Rejected this run: {rejected}")
    print(f"Failed this run: {failed}")
    print("Master metadata: " + str(metadata_dir / "artworks.csv"))
    print("Manifest: " + str(metadata_dir / "download_manifest.jsonl"))
    return 0 if downloaded else 1


def _validate_output(output_dir: Path, config: dict) -> int:
    metadata_path = output_dir / "metadata" / "artworks.csv"
    rows = read_metadata_rows(metadata_path)
    errors: list[str] = []
    seen_source_ids: set[tuple[str, str]] = set()
    seen_filenames: set[str] = set()
    seen_hashes: set[str] = set()
    quality_config = config.get("image_quality", {})
    min_long_edge = int(quality_config.get("min_long_edge", 2500))
    min_megapixels = float(quality_config.get("min_megapixels", 4.0))

    for category in sorted(VALID_CATEGORIES):
        category_dir = output_dir / category
        if not category_dir.exists():
            errors.append(f"missing category directory: {category_dir}")

    for index, row in enumerate(rows, start=2):
        source = row.get("source", "")
        source_id = row.get("source_id", "")
        category = row.get("category", "")
        filename = row.get("image_filename", "")
        image_path = Path(row.get("image_path", ""))
        sha256 = row.get("sha256", "")

        if not source or not source_id:
            errors.append(f"row {index}: missing source/source_id")
        key = (source, source_id)
        if key in seen_source_ids:
            errors.append(f"row {index}: duplicate source id {source}:{source_id}")
        seen_source_ids.add(key)

        if category not in VALID_CATEGORIES:
            errors.append(f"row {index}: invalid category {category!r}")
        if row.get("public_domain") != "true":
            errors.append(f"row {index}: public_domain must be true")
        if not row.get("license"):
            errors.append(f"row {index}: missing license")
        if not filename:
            errors.append(f"row {index}: missing image filename")
        if filename in seen_filenames:
            errors.append(f"row {index}: duplicate filename {filename}")
        seen_filenames.add(filename)
        if sha256 in seen_hashes:
            errors.append(f"row {index}: duplicate sha256 {sha256}")
        if sha256:
            seen_hashes.add(sha256)

        if not image_path.exists():
            errors.append(f"row {index}: missing image file {image_path}")
            continue
        try:
            image = inspect_image(image_path)
        except Exception as exc:
            errors.append(f"row {index}: unreadable image {image_path}: {exc}")
            continue
        if not passes_quality(image, min_long_edge, min_megapixels):
            errors.append(f"row {index}: image fails quality {image.width}x{image.height}")
        if sha256 and image.sha256 != sha256:
            errors.append(f"row {index}: sha256 mismatch for {image_path}")

    metadata_files = {Path(row.get("image_path", "")) for row in rows if row.get("image_path")}
    image_files = {
        path
        for category in VALID_CATEGORIES
        for path in (output_dir / category).glob("*")
        if path.is_file() and not path.name.endswith(".part")
    }
    for orphan in sorted(image_files - metadata_files):
        errors.append(f"orphan image file: {orphan}")

    print("========== VALIDATION SUMMARY ==========")
    print(f"Metadata rows: {len(rows)}")
    print(f"Image files: {len(image_files)}")
    print(f"Errors: {len(errors)}")
    for error in errors:
        print(f"ERROR: {error}")
    return 1 if errors else 0


def _validate_sample(sample_dir: Path, config: dict) -> int:
    metadata_path = sample_dir / "master_metadata.csv"
    shopify_path = sample_dir / "shopify_products.csv"
    rows = read_metadata_rows(metadata_path)
    errors: list[str] = []
    seen_source_ids: set[tuple[str, str]] = set()
    seen_filenames: set[str] = set()
    seen_hashes: set[str] = set()
    quality_config = config.get("image_quality", {})
    min_long_edge = int(quality_config.get("min_long_edge", 2500))
    min_megapixels = float(quality_config.get("min_megapixels", 4.0))

    if not metadata_path.exists():
        errors.append(f"missing master metadata: {metadata_path}")
    if not shopify_path.exists():
        errors.append(f"missing Shopify CSV: {shopify_path}")

    for category in sorted(VALID_CATEGORIES):
        category_dir = sample_dir / category
        if not category_dir.exists():
            errors.append(f"missing category directory: {category_dir}")

    for index, row in enumerate(rows, start=2):
        source = row.get("source", "")
        source_id = row.get("source_id", "")
        category = row.get("category", "")
        filename = row.get("image_filename", "")
        sha256 = row.get("sha256", "")

        if not source or not source_id:
            errors.append(f"row {index}: missing source/source_id")
        key = (source, source_id)
        if key in seen_source_ids:
            errors.append(f"row {index}: duplicate source id {source}:{source_id}")
        seen_source_ids.add(key)

        if category not in VALID_CATEGORIES:
            errors.append(f"row {index}: invalid category {category!r}")
        if row.get("public_domain") != "true":
            errors.append(f"row {index}: public_domain must be true")
        if not row.get("license"):
            errors.append(f"row {index}: missing license")
        if not filename:
            errors.append(f"row {index}: missing image filename")
        if filename in seen_filenames:
            errors.append(f"row {index}: duplicate filename {filename}")
        seen_filenames.add(filename)
        if sha256 in seen_hashes:
            errors.append(f"row {index}: duplicate sha256 {sha256}")
        if sha256:
            seen_hashes.add(sha256)

        image_path = sample_dir / category / filename
        if not image_path.exists():
            errors.append(f"row {index}: missing image file {image_path}")
            continue
        try:
            image = inspect_image(image_path)
        except Exception as exc:
            errors.append(f"row {index}: unreadable image {image_path}: {exc}")
            continue
        if not passes_quality(image, min_long_edge, min_megapixels):
            errors.append(f"row {index}: image fails quality {image.width}x{image.height}")
        if sha256 and image.sha256 != sha256:
            errors.append(f"row {index}: sha256 mismatch for {image_path}")

    metadata_files = {
        sample_dir / row.get("category", "") / row.get("image_filename", "")
        for row in rows
        if row.get("category") and row.get("image_filename")
    }
    image_files = {
        path
        for category in VALID_CATEGORIES
        for path in (sample_dir / category).glob("*")
        if path.is_file() and not path.name.endswith(".part")
    }
    for orphan in sorted(image_files - metadata_files):
        errors.append(f"orphan image file: {orphan}")

    shopify_rows = []
    if shopify_path.exists():
        with shopify_path.open("r", encoding="utf-8", newline="") as handle:
            shopify_rows = list(csv.DictReader(handle))
    expected_variants = len(rows) * len(config.get("shopify", {}).get("sizes", ["A4", "A3", "A2", "A1"]))
    if shopify_rows and len(shopify_rows) != expected_variants:
        errors.append(f"expected {expected_variants} Shopify rows, found {len(shopify_rows)}")

    print("========== SAMPLE VALIDATION SUMMARY ==========")
    print(f"Sample directory: {sample_dir}")
    print(f"Metadata rows: {len(rows)}")
    print(f"Image files: {len(image_files)}")
    print(f"Shopify rows: {len(shopify_rows)}")
    print(f"Errors: {len(errors)}")
    for error in errors:
        print(f"ERROR: {error}")
    return 1 if errors else 0


def _export_shopify(output_dir: Path, config: dict) -> int:
    rows = read_metadata_rows(output_dir / "metadata" / "artworks.csv")
    shopify_dir = output_dir / "shopify"
    shopify_dir.mkdir(parents=True, exist_ok=True)
    shopify_path = shopify_dir / "shopify_products.csv"
    shopify_config = config.get("shopify", {})
    sizes = list(shopify_config.get("sizes", ["A4", "A3", "A2", "A1"]))
    prices = dict(shopify_config.get("prices", {}))
    with shopify_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=SHOPIFY_COLUMNS)
        writer.writeheader()
        for row in rows:
            artwork = _artwork_from_metadata_row(row)
            for shopify_row in artwork_to_shopify_rows(
                artwork,
                sizes=sizes,
                prices=prices,
                vendor=str(shopify_config.get("vendor", "Public Domain Art")),
                product_type=str(shopify_config.get("product_type", "Art Print")),
                shopify_image_src="",
            ):
                writer.writerow(shopify_row)
    print(f"Exported {len(rows) * len(sizes)} Shopify variant rows to {shopify_path}")
    return 0


def _artwork_from_metadata_row(row: dict[str, str]) -> Artwork:
    return Artwork(
        source=row["source"],
        source_id=row["source_id"],
        title=row["artwork_title"],
        artist=row.get("artist_name") or None,
        artist_display=None,
        date=row.get("artwork_date") or None,
        medium=row.get("medium") or None,
        category=row["category"],
        public_domain=row.get("public_domain") == "true",
        license=row.get("license") or None,
        object_url=row["object_page_url"],
        image_url=row["original_image_url"],
        image_width=int(row["image_width"]) if row.get("image_width") else None,
        image_height=int(row["image_height"]) if row.get("image_height") else None,
        local_filename=row.get("image_filename") or None,
        classification_reason=row.get("classification_reason") or None,
        classification_score=float(row["classification_score"]) if row.get("classification_score") else None,
    )


if __name__ == "__main__":
    raise SystemExit(main())
