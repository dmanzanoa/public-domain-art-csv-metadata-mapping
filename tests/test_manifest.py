from __future__ import annotations

from art_scraper.models import ManifestRecord, ManifestStatus
from art_scraper.pipeline.manifest import Manifest


def test_manifest_loads_latest_record(tmp_path) -> None:  # type: ignore[no-untyped-def]
    path = tmp_path / "manifest.jsonl"
    manifest = Manifest(path)
    manifest.append(ManifestRecord("met", "1", ManifestStatus.DISCOVERED))
    manifest.append(
        ManifestRecord(
            "met",
            "1",
            ManifestStatus.DOWNLOADED,
            filename="met_1.jpg",
            sha256="abc",
            attempts=1,
        )
    )

    reloaded = Manifest(path)
    latest = reloaded.latest("met", "1")

    assert latest is not None
    assert latest.status == ManifestStatus.DOWNLOADED
    assert latest.filename == "met_1.jpg"
    assert latest.sha256 == "abc"
