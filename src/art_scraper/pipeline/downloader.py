from __future__ import annotations

import random
import time
from dataclasses import dataclass
from pathlib import Path

import requests

from art_scraper.models import Artwork, ImageFile, ManifestRecord, ManifestStatus, VALID_CATEGORIES
from art_scraper.pipeline.manifest import Manifest
from art_scraper.pipeline.metadata import append_metadata_row, metadata_row
from art_scraper.pipeline.validation import inspect_image, passes_quality
from art_scraper.utils.filenames import deterministic_image_filename


@dataclass(slots=True)
class DownloadResult:
    artwork: Artwork
    status: ManifestStatus
    image: ImageFile | None = None
    path: Path | None = None
    reason: str | None = None


class ImageDownloader:
    transient_statuses = {429, 500, 502, 503, 504}

    def __init__(
        self,
        output_dir: str | Path,
        manifest: Manifest,
        metadata_csv: str | Path,
        min_long_edge: int = 2500,
        min_megapixels: float = 4.0,
        max_retries: int = 5,
        timeout: int = 30,
        session: requests.Session | None = None,
    ) -> None:
        self.output_dir = Path(output_dir)
        self.manifest = manifest
        self.metadata_csv = Path(metadata_csv)
        self.min_long_edge = min_long_edge
        self.min_megapixels = min_megapixels
        self.max_retries = max_retries
        self.timeout = timeout
        self.session = session or requests.Session()
        self._ensure_output_structure()

    def download(self, artwork: Artwork) -> DownloadResult:
        latest = self.manifest.latest(artwork.source, artwork.source_id)
        if latest and latest.status == ManifestStatus.DOWNLOADED:
            return DownloadResult(
                artwork=artwork,
                status=ManifestStatus.DOWNLOADED,
                reason="already downloaded",
            )

        if not artwork.category:
            return self._reject(artwork, "unclassified artwork")

        artwork.local_filename = artwork.local_filename or deterministic_image_filename(artwork)
        category_dir = self.output_dir / artwork.category
        final_path = category_dir / artwork.local_filename

        self.manifest.append(
            ManifestRecord(artwork.source, artwork.source_id, ManifestStatus.QUEUED, filename=artwork.local_filename)
        )

        if final_path.exists():
            image = inspect_image(final_path)
            if not passes_quality(image, self.min_long_edge, self.min_megapixels):
                return self._reject(artwork, "existing file fails image quality", image=image)
            self._record_success(artwork, image, final_path, attempts=0)
            return DownloadResult(artwork=artwork, status=ManifestStatus.DOWNLOADED, image=image, path=final_path)

        category_dir.mkdir(parents=True, exist_ok=True)
        tmp_path = final_path.with_suffix(final_path.suffix + ".part")
        try:
            self._download_to_tmp(artwork.image_url, tmp_path)
            image = inspect_image(tmp_path)
            if not passes_quality(image, self.min_long_edge, self.min_megapixels):
                tmp_path.unlink(missing_ok=True)
                return self._reject(
                    artwork,
                    f"low resolution: {image.width}x{image.height}, {image.megapixels:.2f}MP",
                    image=image,
                )
            tmp_path.replace(final_path)
            image = inspect_image(final_path)
            self._record_success(artwork, image, final_path, attempts=1)
            return DownloadResult(artwork=artwork, status=ManifestStatus.DOWNLOADED, image=image, path=final_path)
        except Exception as exc:
            tmp_path.unlink(missing_ok=True)
            reason = str(exc)
            self.manifest.append(
                ManifestRecord(
                    artwork.source,
                    artwork.source_id,
                    ManifestStatus.FAILED,
                    filename=artwork.local_filename,
                    attempts=self.max_retries,
                    reason=reason,
                )
            )
            return DownloadResult(artwork=artwork, status=ManifestStatus.FAILED, reason=reason)

    def _download_to_tmp(self, url: str, tmp_path: Path) -> None:
        last_error: Exception | None = None
        for attempt in range(1, self.max_retries + 1):
            try:
                with self.session.get(url, stream=True, timeout=self.timeout) as response:
                    if response.status_code in self.transient_statuses:
                        raise requests.HTTPError(
                            f"transient HTTP {response.status_code}",
                            response=response,
                        )
                    response.raise_for_status()
                    with tmp_path.open("wb") as handle:
                        for chunk in response.iter_content(chunk_size=1024 * 1024):
                            if chunk:
                                handle.write(chunk)
                return
            except requests.RequestException as exc:
                last_error = exc
                if attempt >= self.max_retries:
                    break
                sleep_for = min(30.0, (2 ** (attempt - 1)) + random.uniform(0, 0.5))
                time.sleep(sleep_for)
        if last_error:
            raise last_error

    def _ensure_output_structure(self) -> None:
        for category in VALID_CATEGORIES:
            (self.output_dir / category).mkdir(parents=True, exist_ok=True)
        self.metadata_csv.parent.mkdir(parents=True, exist_ok=True)
        (self.output_dir / "shopify").mkdir(parents=True, exist_ok=True)
        (self.output_dir / "logs").mkdir(parents=True, exist_ok=True)

    def _record_success(
        self,
        artwork: Artwork,
        image: ImageFile,
        final_path: Path,
        attempts: int,
    ) -> None:
        row = metadata_row(artwork, image, final_path)
        append_metadata_row(self.metadata_csv, row)
        self.manifest.append(
            ManifestRecord(
                artwork.source,
                artwork.source_id,
                ManifestStatus.DOWNLOADED,
                filename=artwork.local_filename,
                sha256=image.sha256,
                attempts=attempts,
            )
        )

    def _reject(
        self,
        artwork: Artwork,
        reason: str,
        image: ImageFile | None = None,
    ) -> DownloadResult:
        self.manifest.append(
            ManifestRecord(
                artwork.source,
                artwork.source_id,
                ManifestStatus.REJECTED,
                filename=artwork.local_filename,
                sha256=image.sha256 if image else None,
                reason=reason,
            )
        )
        return DownloadResult(artwork=artwork, status=ManifestStatus.REJECTED, image=image, reason=reason)
