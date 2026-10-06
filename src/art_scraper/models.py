from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any


VALID_CATEGORIES = {
    "abstract",
    "botanical",
    "landscape",
    "photography",
    "australiana",
    "fashion",
}


class ManifestStatus(str, Enum):
    DISCOVERED = "discovered"
    METADATA_VALIDATED = "metadata_validated"
    QUEUED = "queued"
    DOWNLOADED = "downloaded"
    REJECTED = "rejected"
    FAILED = "failed"
    DUPLICATE = "duplicate"


@dataclass(slots=True)
class ClassificationResult:
    category: str
    reason: str
    score: float

    def __post_init__(self) -> None:
        if self.category not in VALID_CATEGORIES:
            raise ValueError(f"Unknown category: {self.category}")
        if not 0 <= self.score <= 1:
            raise ValueError("classification score must be between 0 and 1")


@dataclass(slots=True)
class Artwork:
    source: str
    source_id: str
    title: str
    artist: str | None
    artist_display: str | None
    date: str | None
    medium: str | None
    category: str | None
    public_domain: bool
    license: str | None
    object_url: str
    image_url: str
    image_width: int | None = None
    image_height: int | None = None
    local_filename: str | None = None
    classification_reason: str | None = None
    classification_score: float | None = None
    dimensions: str | None = None
    department: str | None = None
    classification: str | None = None
    object_type: str | None = None
    tags: list[str] = field(default_factory=list)
    source_metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.source:
            raise ValueError("source is required")
        if not self.source_id:
            raise ValueError("source_id is required")
        if not self.title:
            raise ValueError("title is required")
        if self.category is not None and self.category not in VALID_CATEGORIES:
            raise ValueError(f"Unknown category: {self.category}")
        if not self.public_domain:
            raise ValueError("Artwork must be public domain to enter the pipeline")
        if not self.license:
            raise ValueError("license is required for public-domain artworks")
        if not self.object_url:
            raise ValueError("object_url is required")
        if not self.image_url:
            raise ValueError("image_url is required")

    @property
    def artist_name(self) -> str:
        return self.artist or self.artist_display or "Unknown Artist"


@dataclass(slots=True)
class ImageFile:
    path: Path
    width: int
    height: int
    image_format: str
    file_size_bytes: int
    sha256: str

    @property
    def megapixels(self) -> float:
        return (self.width * self.height) / 1_000_000

    @property
    def long_edge(self) -> int:
        return max(self.width, self.height)


@dataclass(slots=True)
class ManifestRecord:
    source: str
    source_id: str
    status: ManifestStatus
    filename: str | None = None
    sha256: str | None = None
    attempts: int = 0
    reason: str | None = None
    updated_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    @property
    def key(self) -> tuple[str, str]:
        return (self.source, self.source_id)

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "source_id": self.source_id,
            "status": self.status.value,
            "filename": self.filename,
            "sha256": self.sha256,
            "attempts": self.attempts,
            "reason": self.reason,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_json_dict(cls, data: dict[str, Any]) -> "ManifestRecord":
        return cls(
            source=str(data["source"]),
            source_id=str(data["source_id"]),
            status=ManifestStatus(data["status"]),
            filename=data.get("filename"),
            sha256=data.get("sha256"),
            attempts=int(data.get("attempts", 0)),
            reason=data.get("reason"),
            updated_at=str(data.get("updated_at")),
        )
