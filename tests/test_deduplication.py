from __future__ import annotations

from art_scraper.models import ImageFile
from art_scraper.pipeline.deduplication import (
    duplicate_filenames,
    duplicate_hashes,
    duplicate_source_ids,
)


def test_duplicate_source_ids(make_artwork) -> None:  # type: ignore[no-untyped-def]
    artworks = [make_artwork(), make_artwork(title="Duplicate")]

    assert duplicate_source_ids(artworks) == {("met", "437853")}


def test_duplicate_filenames(make_artwork) -> None:  # type: ignore[no-untyped-def]
    artworks = [
        make_artwork(local_filename="one.jpg"),
        make_artwork(source_id="2", local_filename="one.jpg"),
    ]

    assert duplicate_filenames(artworks) == {"one.jpg"}


def test_duplicate_hashes(tmp_path) -> None:  # type: ignore[no-untyped-def]
    images = [
        ImageFile(tmp_path / "a.jpg", 10, 10, "JPEG", 100, "abc"),
        ImageFile(tmp_path / "b.jpg", 10, 10, "JPEG", 100, "abc"),
    ]

    assert duplicate_hashes(images) == {"abc"}
