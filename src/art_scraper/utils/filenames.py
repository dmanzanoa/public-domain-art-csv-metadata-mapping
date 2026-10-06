from __future__ import annotations

import re
import unicodedata

from art_scraper.models import Artwork


MAX_FILENAME_STEM_LENGTH = 150


def slugify(value: str, fallback: str = "unknown") -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", ascii_value.casefold()).strip("-")
    slug = re.sub(r"-{2,}", "-", slug)
    return slug or fallback


def deterministic_image_filename(artwork: Artwork, extension: str = "jpg") -> str:
    artist_slug = slugify(artwork.artist_name)
    title_slug = slugify(artwork.title, fallback="untitled")
    source_slug = slugify(artwork.source)
    id_slug = slugify(artwork.source_id)
    stem = f"{source_slug}_{id_slug}_{artist_slug}_{title_slug}"
    if len(stem) > MAX_FILENAME_STEM_LENGTH:
        stem = stem[:MAX_FILENAME_STEM_LENGTH].rstrip("-_")
    clean_ext = slugify(extension.lstrip("."), fallback="jpg")
    return f"{stem}.{clean_ext}"


def shopify_handle(artwork: Artwork) -> str:
    artist_slug = slugify(artwork.artist_name)
    title_slug = slugify(artwork.title, fallback="untitled")
    source_slug = slugify(artwork.source)
    id_slug = slugify(artwork.source_id)
    return f"{artist_slug}-{title_slug}-{source_slug}-{id_slug}"
