from __future__ import annotations

from art_scraper.models import Artwork, ImageFile


def duplicate_source_ids(artworks: list[Artwork]) -> set[tuple[str, str]]:
    seen: set[tuple[str, str]] = set()
    duplicates: set[tuple[str, str]] = set()
    for artwork in artworks:
        key = (artwork.source, artwork.source_id)
        if key in seen:
            duplicates.add(key)
        seen.add(key)
    return duplicates


def duplicate_filenames(artworks: list[Artwork]) -> set[str]:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for artwork in artworks:
        if not artwork.local_filename:
            continue
        if artwork.local_filename in seen:
            duplicates.add(artwork.local_filename)
        seen.add(artwork.local_filename)
    return duplicates


def duplicate_hashes(images: list[ImageFile]) -> set[str]:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for image in images:
        if image.sha256 in seen:
            duplicates.add(image.sha256)
        seen.add(image.sha256)
    return duplicates
