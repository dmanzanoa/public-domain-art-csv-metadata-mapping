from __future__ import annotations

import csv
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from art_scraper.models import Artwork, ImageFile


MASTER_METADATA_COLUMNS = [
    "source",
    "source_id",
    "category",
    "artist_name",
    "artwork_title",
    "artwork_date",
    "medium",
    "original_image_url",
    "object_page_url",
    "license",
    "public_domain",
    "image_filename",
    "image_path",
    "image_width",
    "image_height",
    "image_format",
    "file_size_bytes",
    "sha256",
    "classification_reason",
    "classification_score",
    "download_status",
    "download_timestamp",
]


def metadata_row(
    artwork: Artwork,
    image: ImageFile,
    image_path: Path,
    status: str = "downloaded",
) -> dict[str, Any]:
    return {
        "source": artwork.source,
        "source_id": artwork.source_id,
        "category": artwork.category or "",
        "artist_name": artwork.artist_name,
        "artwork_title": artwork.title,
        "artwork_date": artwork.date or "",
        "medium": artwork.medium or "",
        "original_image_url": artwork.image_url,
        "object_page_url": artwork.object_url,
        "license": artwork.license or "",
        "public_domain": str(artwork.public_domain).lower(),
        "image_filename": artwork.local_filename or image_path.name,
        "image_path": str(image_path),
        "image_width": image.width,
        "image_height": image.height,
        "image_format": image.image_format,
        "file_size_bytes": image.file_size_bytes,
        "sha256": image.sha256,
        "classification_reason": artwork.classification_reason or "",
        "classification_score": "" if artwork.classification_score is None else artwork.classification_score,
        "download_status": status,
        "download_timestamp": datetime.now(timezone.utc).isoformat(),
    }


def append_metadata_row(path: str | Path, row: dict[str, Any]) -> None:
    csv_path = Path(path)
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    write_header = not csv_path.exists() or csv_path.stat().st_size == 0
    with csv_path.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=MASTER_METADATA_COLUMNS)
        if write_header:
            writer.writeheader()
        writer.writerow(row)


def read_metadata_rows(path: str | Path) -> list[dict[str, str]]:
    csv_path = Path(path)
    if not csv_path.exists():
        return []
    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))
