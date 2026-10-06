from __future__ import annotations

from importlib.resources import files
from pathlib import Path
from typing import Any

import yaml

from art_scraper.models import Artwork, ClassificationResult


class RuleBasedClassifier:
    def __init__(self, rules: dict[str, Any]) -> None:
        self.rules = rules

    @classmethod
    def from_yaml(cls, path: str | Path | None = None) -> "RuleBasedClassifier":
        if path is None:
            resource = files("art_scraper.classification").joinpath("rules.yaml")
            with resource.open("r", encoding="utf-8") as handle:
                rules = yaml.safe_load(handle) or {}
        else:
            with Path(path).open("r", encoding="utf-8") as handle:
                rules = yaml.safe_load(handle) or {}
        return cls(rules)

    def classify(self, artwork: Artwork) -> ClassificationResult | None:
        best: ClassificationResult | None = None
        categories = self.rules.get("categories", {})
        for category, config in categories.items():
            score, reason = self._score_category(artwork, config.get("terms", {}))
            threshold = float(config.get("threshold", 0.5))
            if score >= threshold and (best is None or score > best.score):
                best = ClassificationResult(category=category, reason=reason, score=min(score, 1.0))
        return best

    def apply(self, artwork: Artwork) -> Artwork:
        result = self.classify(artwork)
        if result is None:
            return artwork
        artwork.category = result.category
        artwork.classification_reason = result.reason
        artwork.classification_score = result.score
        return artwork

    def _score_category(
        self, artwork: Artwork, field_terms: dict[str, dict[str, float]]
    ) -> tuple[float, str]:
        score = 0.0
        reasons: list[str] = []
        fields = {
            "title": artwork.title,
            "artist": artwork.artist_name,
            "medium": artwork.medium,
            "department": artwork.department,
            "classification": artwork.classification,
            "object_type": artwork.object_type,
            "tags": " ".join(artwork.tags),
        }
        for field_name, terms in field_terms.items():
            haystack = str(fields.get(field_name) or "").casefold()
            if not haystack:
                continue
            for term, weight in terms.items():
                if str(term).casefold() in haystack:
                    score += float(weight)
                    reasons.append(f"{field_name} contains '{term}'")
        return min(score, 1.0), "; ".join(reasons) or "no rule matched"
