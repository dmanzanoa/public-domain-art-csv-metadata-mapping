from __future__ import annotations

from art_scraper.classification import RuleBasedClassifier


def test_classifies_landscape(make_artwork) -> None:  # type: ignore[no-untyped-def]
    artwork = make_artwork(title="Mountain Landscape", tags=["Mountains", "Rivers"])
    result = RuleBasedClassifier.from_yaml().classify(artwork)

    assert result is not None
    assert result.category == "landscape"
    assert "title contains 'landscape'" in result.reason


def test_photography_relies_on_medium_or_classification(make_artwork) -> None:  # type: ignore[no-untyped-def]
    artwork = make_artwork(
        title="Portrait of a Woman",
        medium="Gelatin silver print",
        classification="Photographs",
        object_type="Photograph",
    )
    result = RuleBasedClassifier.from_yaml().classify(artwork)

    assert result is not None
    assert result.category == "photography"
    assert result.score >= 0.65


def test_weak_australia_artist_signal_does_not_classify_alone(make_artwork) -> None:  # type: ignore[no-untyped-def]
    artwork = make_artwork(
        title="Untitled Study",
        artist="Australian Artist",
        tags=[],
        department="Drawings",
        classification="Drawings",
    )
    result = RuleBasedClassifier.from_yaml().classify(artwork)

    assert result is None
