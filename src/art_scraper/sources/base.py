from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Protocol

from art_scraper.models import Artwork


@dataclass(frozen=True, slots=True)
class DiscoveryQuery:
    query: str
    limit: int = 25


class SourceAdapter(Protocol):
    source_name: str

    def discover(self, discovery_query: DiscoveryQuery) -> Iterable[Artwork]:
        ...


class SourceNotSuitableError(RuntimeError):
    """Raised when a source is intentionally disabled for licensing/API reasons."""
