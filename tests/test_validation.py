from __future__ import annotations

from PIL import Image

from art_scraper.pipeline.validation import inspect_image, passes_quality


def test_inspect_image_and_quality(tmp_path) -> None:  # type: ignore[no-untyped-def]
    path = tmp_path / "image.jpg"
    Image.new("RGB", (3000, 2000), "white").save(path, format="JPEG")

    image = inspect_image(path)

    assert image.width == 3000
    assert image.height == 2000
    assert image.image_format == "JPEG"
    assert passes_quality(image, min_long_edge=2500, min_megapixels=4.0)
    assert not passes_quality(image, min_long_edge=4000, min_megapixels=4.0)
