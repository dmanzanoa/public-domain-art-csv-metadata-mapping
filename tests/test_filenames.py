from __future__ import annotations

from art_scraper.utils.filenames import deterministic_image_filename, shopify_handle, slugify


def test_slugify_handles_unicode_and_punctuation() -> None:
    assert slugify("Édouard Manet: Flowers / Study") == "edouard-manet-flowers-study"


def test_deterministic_filename_includes_source_id_artist_title(make_artwork) -> None:  # type: ignore[no-untyped-def]
    artwork = make_artwork(
        source="met",
        source_id="437853",
        artist="Vincent van Gogh",
        title="Wheat Field with Cypresses",
    )

    assert (
        deterministic_image_filename(artwork)
        == "met_437853_vincent-van-gogh_wheat-field-with-cypresses.jpg"
    )


def test_shopify_handle_is_stable(make_artwork) -> None:  # type: ignore[no-untyped-def]
    artwork = make_artwork()

    assert shopify_handle(artwork) == "vincent-van-gogh-wheat-field-with-cypresses-met-437853"
