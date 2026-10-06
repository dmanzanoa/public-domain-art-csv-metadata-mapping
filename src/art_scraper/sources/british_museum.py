from __future__ import annotations

from typing import Iterable

from art_scraper.models import Artwork
from art_scraper.sources.base import DiscoveryQuery, SourceNotSuitableError


class BritishMuseumAdapter:
    source_name = "british_museum"

    def discover(self, discovery_query: DiscoveryQuery) -> Iterable[Artwork]:
        raise SourceNotSuitableError(
            "British Museum is disabled until an official unrestricted commercial "
            "reuse API/dataset is identified."
        )
