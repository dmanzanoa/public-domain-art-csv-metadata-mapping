from __future__ import annotations

from typing import Any, Iterable

import requests
from requests import RequestException

from art_scraper.models import Artwork
from art_scraper.sources.base import DiscoveryQuery


class MetAdapter:
    source_name = "met"
    base_url = "https://collectionapi.metmuseum.org/public/collection"
    object_api_version = "v1"
    search_api_version = "v1.1"
    license_label = "CC0 / public domain via The Met Open Access"

    def __init__(self, session: requests.Session | None = None, timeout: int = 30) -> None:
        self.session = session or requests.Session()
        self.timeout = timeout

    def discover(self, discovery_query: DiscoveryQuery) -> Iterable[Artwork]:
        object_ids = self.search_object_ids(discovery_query.query)
        emitted = 0
        for object_id in object_ids:
            if emitted >= discovery_query.limit:
                break
            try:
                payload = self.get_object(object_id)
            except (RequestException, ValueError):
                continue
            artwork = self.normalize_object(payload)
            if artwork is None:
                continue
            emitted += 1
            yield artwork

    def search_object_ids(self, query: str) -> list[int]:
        response = self.session.get(
            f"{self.base_url}/{self.search_api_version}/search",
            params={"hasImages": "true", "q": query, "limit": 500, "offset": 0},
            timeout=self.timeout,
        )
        response.raise_for_status()
        payload = response.json()
        object_ids = payload.get("objectIDs") or []
        return [int(object_id) for object_id in object_ids]

    def get_object(self, object_id: int | str) -> dict[str, Any]:
        response = self.session.get(
            f"{self.base_url}/{self.object_api_version}/objects/{object_id}",
            timeout=self.timeout,
        )
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict):
            raise ValueError(f"Unexpected Met object payload for {object_id}")
        return payload

    def normalize_object(self, payload: dict[str, Any]) -> Artwork | None:
        if payload.get("isPublicDomain") is not True:
            return None
        image_url = str(payload.get("primaryImage") or "").strip()
        if not image_url:
            return None

        source_id = str(payload.get("objectID") or "").strip()
        title = str(payload.get("title") or "").strip()
        object_url = str(payload.get("objectURL") or "").strip()
        if not source_id or not title or not object_url:
            return None

        tags = self._extract_tags(payload)
        artist = str(payload.get("artistDisplayName") or "").strip() or None
        artist_display = str(payload.get("artistDisplayBio") or "").strip() or None

        return Artwork(
            source=self.source_name,
            source_id=source_id,
            title=title,
            artist=artist,
            artist_display=artist_display,
            date=str(payload.get("objectDate") or "").strip() or None,
            medium=str(payload.get("medium") or "").strip() or None,
            category=None,
            public_domain=True,
            license=self.license_label,
            object_url=object_url,
            image_url=image_url,
            dimensions=str(payload.get("dimensions") or "").strip() or None,
            department=str(payload.get("department") or "").strip() or None,
            classification=str(payload.get("classification") or "").strip() or None,
            object_type=str(payload.get("objectName") or "").strip() or None,
            tags=tags,
            source_metadata=payload,
        )

    @staticmethod
    def _extract_tags(payload: dict[str, Any]) -> list[str]:
        tags = payload.get("tags") or []
        values: list[str] = []
        if isinstance(tags, list):
            for tag in tags:
                if isinstance(tag, dict) and tag.get("term"):
                    values.append(str(tag["term"]))
                elif isinstance(tag, str):
                    values.append(tag)
        return values
