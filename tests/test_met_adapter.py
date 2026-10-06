from __future__ import annotations

from art_scraper.sources.met import MetAdapter


def met_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "objectID": 437853,
        "isPublicDomain": True,
        "primaryImage": "https://images.metmuseum.org/CRDImages/ep/original/DT1567.jpg",
        "title": "Wheat Field with Cypresses",
        "artistDisplayName": "Vincent van Gogh",
        "artistDisplayBio": "Dutch, 1853-1890",
        "objectDate": "1889",
        "medium": "Oil on canvas",
        "dimensions": "28 7/8 x 36 3/4 in.",
        "department": "European Paintings",
        "classification": "Paintings",
        "objectName": "Painting",
        "objectURL": "https://www.metmuseum.org/art/collection/search/437853",
        "tags": [{"term": "Landscapes"}, {"term": "Trees"}],
    }
    payload.update(overrides)
    return payload


def test_normalize_public_domain_object() -> None:
    artwork = MetAdapter().normalize_object(met_payload())

    assert artwork is not None
    assert artwork.source == "met"
    assert artwork.source_id == "437853"
    assert artwork.artist == "Vincent van Gogh"
    assert artwork.public_domain is True
    assert artwork.license == "CC0 / public domain via The Met Open Access"
    assert artwork.tags == ["Landscapes", "Trees"]


def test_rejects_non_public_domain_object() -> None:
    artwork = MetAdapter().normalize_object(met_payload(isPublicDomain=False))

    assert artwork is None


def test_rejects_public_domain_object_without_primary_image() -> None:
    artwork = MetAdapter().normalize_object(met_payload(primaryImage=""))

    assert artwork is None
