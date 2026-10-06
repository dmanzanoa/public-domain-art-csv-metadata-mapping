from __future__ import annotations

from pathlib import Path

from PIL import Image

from art_scraper.models import ImageFile
from art_scraper.utils.hashing import sha256_file


def inspect_image(path: str | Path) -> ImageFile:
    image_path = Path(path)
    with Image.open(image_path) as image:
        image.verify()
    with Image.open(image_path) as image:
        width, height = image.size
        image_format = image.format or image_path.suffix.lstrip(".").upper()
    return ImageFile(
        path=image_path,
        width=width,
        height=height,
        image_format=image_format,
        file_size_bytes=image_path.stat().st_size,
        sha256=sha256_file(image_path),
    )


def passes_quality(
    image: ImageFile,
    min_long_edge: int = 2500,
    min_megapixels: float = 4.0,
) -> bool:
    return image.long_edge >= min_long_edge and image.megapixels >= min_megapixels
