from __future__ import annotations

from art_scraper.models import Artwork
from art_scraper.utils.filenames import shopify_handle


SHOPIFY_COLUMNS = [
    "Handle",
    "Title",
    "Body (HTML)",
    "Vendor",
    "Product Category",
    "Type",
    "Tags",
    "Published",
    "Option1 Name",
    "Option1 Value",
    "Variant SKU",
    "Variant Price",
    "Image Src",
    "Image Position",
    "Image Alt Text",
    "Status",
]


def artwork_to_shopify_rows(
    artwork: Artwork,
    sizes: list[str],
    prices: dict[str, str | float | int | None] | None = None,
    vendor: str = "Public Domain Art",
    product_type: str = "Art Print",
    shopify_image_src: str = "",
) -> list[dict[str, str]]:
    if not artwork.category:
        raise ValueError("Artwork must be classified before Shopify export")
    prices = prices or {}
    handle = shopify_handle(artwork)
    title = f"{artwork.artist_name} - {artwork.title}"
    tags = ", ".join(
        item
        for item in [artwork.category, artwork.source, "public domain", artwork.artist_name]
        if item
    )
    rows: list[dict[str, str]] = []
    for position, size in enumerate(sizes, start=1):
        price = prices.get(size)
        rows.append(
            {
                "Handle": handle,
                "Title": title if position == 1 else "",
                "Body (HTML)": _body_html(artwork) if position == 1 else "",
                "Vendor": vendor if position == 1 else "",
                "Product Category": "" if position == 1 else "",
                "Type": product_type if position == 1 else "",
                "Tags": tags if position == 1 else "",
                "Published": "TRUE" if position == 1 else "",
                "Option1 Name": "Size",
                "Option1 Value": size,
                "Variant SKU": f"{handle}-{size.casefold()}",
                "Variant Price": "" if price is None else str(price),
                "Image Src": shopify_image_src if position == 1 else "",
                "Image Position": "1" if position == 1 and shopify_image_src else "",
                "Image Alt Text": f"{artwork.title} by {artwork.artist_name}" if position == 1 else "",
                "Status": "draft",
            }
        )
    return rows


def _body_html(artwork: Artwork) -> str:
    parts = [
        f"<p>{artwork.title}</p>",
        f"<p>Artist: {artwork.artist_name}</p>",
        f"<p>Source: {artwork.source} {artwork.source_id}</p>",
        f'<p>Object page: <a href="{artwork.object_url}">{artwork.object_url}</a></p>',
        f"<p>License: {artwork.license}</p>",
    ]
    return "".join(parts)
