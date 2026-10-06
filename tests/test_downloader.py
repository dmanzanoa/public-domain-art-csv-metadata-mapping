from __future__ import annotations

from io import BytesIO

from PIL import Image

from art_scraper.models import ManifestStatus
from art_scraper.pipeline.downloader import ImageDownloader
from art_scraper.pipeline.manifest import Manifest
from art_scraper.pipeline.metadata import read_metadata_rows


class FakeResponse:
    status_code = 200

    def __init__(self, content: bytes) -> None:
        self.content = content

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def raise_for_status(self) -> None:
        return None

    def iter_content(self, chunk_size: int) -> list[bytes]:
        return [self.content]


class FakeSession:
    def __init__(self, content: bytes) -> None:
        self.content = content

    def get(self, url: str, stream: bool, timeout: int) -> FakeResponse:
        return FakeResponse(self.content)


def jpeg_bytes(width: int, height: int) -> bytes:
    handle = BytesIO()
    Image.new("RGB", (width, height), "white").save(handle, format="JPEG")
    return handle.getvalue()


def test_downloader_saves_valid_image_and_metadata(tmp_path, make_artwork) -> None:  # type: ignore[no-untyped-def]
    manifest = Manifest(tmp_path / "metadata" / "download_manifest.jsonl")
    metadata_csv = tmp_path / "metadata" / "artworks.csv"
    downloader = ImageDownloader(
        output_dir=tmp_path,
        manifest=manifest,
        metadata_csv=metadata_csv,
        min_long_edge=1000,
        min_megapixels=1,
        session=FakeSession(jpeg_bytes(1200, 1000)),
    )
    artwork = make_artwork(category="landscape", local_filename="test.jpg")

    result = downloader.download(artwork)

    assert result.status == ManifestStatus.DOWNLOADED
    assert result.path == tmp_path / "landscape" / "test.jpg"
    assert result.path.exists()
    rows = read_metadata_rows(metadata_csv)
    assert len(rows) == 1
    assert rows[0]["source_id"] == artwork.source_id
    assert rows[0]["image_filename"] == "test.jpg"


def test_downloader_rejects_low_resolution_image(tmp_path, make_artwork) -> None:  # type: ignore[no-untyped-def]
    manifest = Manifest(tmp_path / "metadata" / "download_manifest.jsonl")
    metadata_csv = tmp_path / "metadata" / "artworks.csv"
    downloader = ImageDownloader(
        output_dir=tmp_path,
        manifest=manifest,
        metadata_csv=metadata_csv,
        min_long_edge=2500,
        min_megapixels=4,
        session=FakeSession(jpeg_bytes(800, 600)),
    )
    artwork = make_artwork(category="landscape", local_filename="small.jpg")

    result = downloader.download(artwork)

    assert result.status == ManifestStatus.REJECTED
    assert "low resolution" in (result.reason or "")
    assert not (tmp_path / "landscape" / "small.jpg").exists()
    assert read_metadata_rows(metadata_csv) == []
