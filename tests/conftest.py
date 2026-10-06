from __future__ import annotations

from collections.abc import Callable

import pytest

from art_scraper.models import Artwork


@pytest.fixture
def make_artwork() -> Callable[..., Artwork]:
    def _make_artwork(**overrides: object) -> Artwork:
        data = {
            "source": "met",
            "source_id": "437853",
            "title": "Wheat Field with Cypresses",
            "artist": "Vincent van Gogh",
            "artist_display": "Dutch, 1853-1890",
            "date": "1889",
            "medium": "Oil on canvas",
            "category": "landscape",
            "public_domain": True,
            "license": "CC0 / public domain via The Met Open Access",
            "object_url": "https://www.metmuseum.org/art/collection/search/437853",
            "image_url": "https://images.metmuseum.org/CRDImages/ep/original/DT1567.jpg",
            "department": "European Paintings",
            "classification": "Paintings",
            "object_type": "Painting",
            "tags": ["Landscapes"],
            "source_metadata": {},
        }
        data.update(overrides)
        return Artwork(**data)

    return _make_artwork
