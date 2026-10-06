# Cover Letter

Dear Hiring Team,

I am applying for the Python Data Engineer / Web Scraping Engineer role. I specialize in building reliable data acquisition pipelines that respect source terms, preserve provenance, and produce clean datasets that downstream teams can actually use.

As an initial work sample, I built a public-domain artwork acquisition pipeline for open-access museum collections. The project demonstrates the core workflow requested in the brief: official API usage, license gating, normalized metadata, deterministic categorization, image-quality validation, duplicate detection, resumable downloads, canonical CSV output, and Shopify-compatible variant export.

The included verification package contains exactly 50 validated public-domain images across six requested categories: abstract, botanical, landscape, photography, Australiana, and fashion. Each image has a matching metadata row, source object URL, original image URL, public-domain/license information, deterministic local filename, SHA256 hash, and Shopify export rows for four print-size variants. The validation report passes with zero orphan files, zero duplicate source IDs, zero duplicate filenames, and zero duplicate image hashes.

I treated licensing correctness as the first constraint. The current milestone uses The Metropolitan Museum of Art Open Access API because it provides explicit public-domain metadata and direct image URLs. I also documented other target sources and intentionally left British Museum automation disabled until an unrestricted commercial reuse path can be confirmed.

The project is not presented as the final 4,000-image production system. It is a completed first milestone that proves the workflow end to end and identifies the next engineering steps: adding the remaining museum adapters, strengthening source-specific rate limits and pagination, adding larger-scale job controls, and integrating hosted storage before Shopify image URLs are populated.

Thank you for reviewing my application. I would be glad to walk through the design decisions, the validation strategy, and how I would extend this into the full production-scale dataset.

Sincerely,

Miguel Zornoza
