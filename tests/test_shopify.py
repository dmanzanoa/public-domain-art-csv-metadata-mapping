from __future__ import annotations

from art_scraper.exporters.shopify import artwork_to_shopify_rows


def test_shopify_generates_one_variant_per_size(make_artwork) -> None:  # type: ignore[no-untyped-def]
    artwork = make_artwork(category="landscape")

    rows = artwork_to_shopify_rows(
        artwork,
        sizes=["A4", "A3", "A2", "A1"],
        prices={"A4": None, "A3": "49.00", "A2": "79.00", "A1": "119.00"},
    )

    assert len(rows) == 4
    assert {row["Option1 Value"] for row in rows} == {"A4", "A3", "A2", "A1"}
    assert rows[0]["Title"] == "Vincent van Gogh - Wheat Field with Cypresses"
    assert rows[0]["Variant Price"] == ""
    assert rows[1]["Variant Price"] == "49.00"
    assert rows[0]["Image Src"] == ""
