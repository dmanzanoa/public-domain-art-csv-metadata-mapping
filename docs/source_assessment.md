# Source Assessment

Assessment date: 2026-10-06

This document records the initial source investigation for a public-domain artwork acquisition pipeline. It intentionally favors official APIs, downloadable datasets, IIIF services, and institution-published open-access terms. Adapters should reject records unless the source metadata provides a confident public-domain, CC0, Public Domain Mark, or equivalent unrestricted-use signal.

## Summary

| Source | API / Data Access | Authentication | High-res Access | License Field / Signal | Suitable | Notes |
|---|---|---:|---|---|---:|---|
| Metropolitan Museum of Art | REST Collection API. Use `/public/collection/v1.1/search` for search and `/public/collection/v1/objects/{id}` for object records. | No | `primaryImage` / `primaryImageSmall` for public-domain objects | `isPublicDomain == true`; Open Access images and data are CC0 | Yes | Strong first adapter candidate: simple JSON, no key, direct image URLs, clear PD flag. `/v1/search` was retired on 2026-10-01. |
| Art Institute of Chicago | REST API plus IIIF Image API | No | IIIF URL from `config.iiif_url` + artwork `image_id` | `is_public_domain == true`; `copyright_notice`; `license_titles` / `license_codes` where present | Yes | Strong source. Must only build IIIF URLs for records with `is_public_domain=true` and usable `image_id`. |
| SMK Open / National Gallery of Denmark | SMK API with filters such as `has_image:true` and `public_domain:true`; IIIF image URLs in image fields | No for standard public API use | IIIF/image fields, including thumbnails and higher-res derivatives depending on record | `public_domain:true` and rights fields | Yes | Good candidate after Met/AIC. Need inspect response shapes before final normalization. |
| Rijksmuseum | Current Data Services: Search API, OAI-PMH, LDES, downloadable collection data, IIIF Image API | No API key for current documented Search/OAI services | IIIF Image API at `https://iiif.micr.io/{id}/...`; image metadata via `info.json` | OAI/EDM rights URIs such as CC0 or Public Domain Mark; policy distinguishes CC0/PDM from restricted records | Yes, with care | Use current `data.rijksmuseum.nl` docs, not undocumented legacy endpoints. Image service IDs may require parsing linked metadata. |
| National Gallery of Art | Open Data CSVs on GitHub; data dictionary documents `published_images.csv` with IIIF base URLs | No | IIIF base URL for published images; image files are not bundled in the dataset | Open data itself is CC0; image reuse must be based on published/open-access image records | Yes, with care | Suitable via CSV ingestion. Must join `objects.csv`, `published_images.csv`, and terms/people tables for metadata and categories. |
| British Museum | Collection Online search/download; no clearly documented public collection API found in official docs | No documented API key because no official public API confirmed | Website offers downloadable images, but commercial use can require a British Museum Images licence | Terms distinguish non-commercial downloads from commercial licensing | No for this commercial pipeline initially | Do not implement as an automated downloader until an official unrestricted commercial reuse path is identified. |

## Source Details

### Metropolitan Museum of Art

- Access mechanism: REST API.
- Authentication: none documented.
- Candidate discovery:
  - `GET /objects` for IDs.
  - `GET /public/collection/v1.1/search?hasImages=true&q=...` for keyword discovery.
  - `GET /objects/{objectID}` for full metadata.
- Licensing filter:
  - Accept only `isPublicDomain == true`.
  - Require a non-empty `primaryImage` for download.
  - Treat license as `CC0 / public domain via The Met Open Access`.
- Useful fields:
  - ID: `objectID`
  - title: `title`
  - artist: `artistDisplayName`, `artistDisplayBio`, `artistNationality`
  - date: `objectDate`, `objectBeginDate`, `objectEndDate`
  - medium: `medium`
  - dimensions: `dimensions`
  - department/category: `department`, `classification`, `objectName`
  - tags/keywords: `tags`
  - object URL: `objectURL`
  - image URL: `primaryImage`
  - public-domain flag: `isPublicDomain`
- Initial implementation recommendation: build this first because licensing and image URL handling are straightforward.

### Art Institute of Chicago

- Access mechanism: REST API plus IIIF Image API.
- Authentication: none documented.
- Candidate discovery:
  - Search endpoint with a public-domain term filter, e.g. `query[term][is_public_domain]=true`.
  - Request explicit fields to keep payloads small.
- Licensing filter:
  - Accept only records with `is_public_domain == true`.
  - Require `image_id`.
  - Preserve `copyright_notice`, `license_title`, `license_codes`, `term_titles`, and `api_link` where available.
- Useful fields:
  - ID: `id`
  - title: `title`
  - artist: `artist_title`, `artist_display`
  - date: `date_display`, `date_start`, `date_end`
  - medium: `medium_display`
  - dimensions: `dimensions`
  - department/category: `department_title`, `classification_title`, `artwork_type_title`, `category_titles`
  - tags/keywords: `term_titles`, `subject_titles`, `style_titles`
  - object URL: `https://www.artic.edu/artworks/{id}`
  - image URL: construct from `config.iiif_url` and `image_id`
  - public-domain flag: `is_public_domain`
- Image note: the common IIIF example uses a resized derivative. For print-quality validation, the adapter/downloader should request an appropriate IIIF size and then validate actual pixels with Pillow.

### SMK Open / National Gallery of Denmark

- Access mechanism: SMK API and IIIF-backed image fields.
- Authentication: none for standard API use.
- Candidate discovery:
  - Use filters such as `has_image:true` and `public_domain:true`.
  - Query by category-oriented keywords for the 50-image verification run.
- Licensing filter:
  - Accept only records with `public_domain == true` or an explicit public-domain/CC0 rights URI.
  - Require a usable image URL or IIIF service.
- Useful fields to verify against live responses:
  - ID/accession: object number / persistent identifier fields
  - title: `titles`
  - artist/creator: production/creator fields
  - date: production date fields
  - medium/dimensions: material and measurement fields
  - categories/tags: object names, techniques, subjects
  - image: `image_thumbnail` and image/IIIF-related fields
  - public-domain flag: `public_domain`
- Implementation note: inspect several live records before freezing normalization, because SMK records can contain nested multilingual fields.

### Rijksmuseum

- Access mechanism: documented Data Services, including Search API, OAI-PMH, LDES, downloads, and IIIF.
- Authentication: no API key needed for current documented Search and OAI-PMH services.
- Candidate discovery:
  - Prefer the current Search API/OAI-PMH or bulk downloads from `data.rijksmuseum.nl`.
  - Do not use undocumented legacy endpoints.
- Licensing filter:
  - Accept only rights URIs that are CC0 or Public Domain Mark.
  - Reject records with copyright-holder notices or rights that are not unrestricted.
- Useful fields:
  - ID: persistent Rijksmuseum object URI or record ID
  - title: `dc:title` / JSON-LD title fields
  - artist: creator/contributor linked fields
  - date: date/created fields
  - medium/dimensions: descriptive metadata fields
  - object URL: resolver/canonical collection URL
  - image URL: IIIF Image API URL derived from the linked digital object service
  - license: `edm:rights` or equivalent rights URI
- Image note: IIIF `info.json` provides `width`, `height`, formats, qualities, and max request area. The downloader should use those values to request a validated derivative that meets configured quality thresholds.

### National Gallery of Art

- Access mechanism: Open Data CSVs on GitHub.
- Authentication: none.
- Candidate discovery:
  - Ingest CSVs locally instead of calling a per-object API.
  - Join `objects.csv`, `published_images.csv`, people/constituents, and terms tables as needed.
- Licensing filter:
  - The dataset is CC0, but images are not included in the dataset itself.
  - Accept only records from published/open-access image rows that indicate public-domain/open-access image availability.
- Useful fields:
  - ID: object ID / accession fields from `objects.csv`
  - title: object title
  - artist: linked constituent/attribution fields
  - date: display date / begin/end date fields
  - medium/dimensions: object fields
  - department/category: classification and terms tables
  - tags/keywords: `objects_terms.csv`
  - image URL: IIIF base URL in `published_images.csv`
  - license: open-access/public-domain indicators in image rows plus NGA open-access policy
- Implementation note: good for scale once CSV ingestion exists, but less ideal than Met for the first end-to-end adapter because it requires multi-file joins.

### British Museum

- Access mechanism: Collection Online UI and search-result spreadsheet downloads. No official, documented public collection API was confirmed during this assessment.
- Authentication: not applicable.
- Licensing issue:
  - Official image guidance states direct downloads are available for limited-size images and free image service is for non-commercial use.
  - Commercial use may require a British Museum Images licence.
- Suitability:
  - Marked unsuitable for the initial unrestricted commercial-reuse pipeline.
  - Revisit only if the museum publishes an official API/dataset with explicit public-domain/CC0 or unrestricted commercial image rights.

## Recommended Adapter Order

1. `met.py` - simplest rights and image handling, best first end-to-end verification adapter.
2. `artic.py` - strong API/IIIF support and clear public-domain field.
3. `smk.py` - public-domain filter and IIIF, but needs nested metadata normalization.
4. `nga.py` - CSV ingestion and IIIF; useful for scale after local dataset plumbing exists.
5. `rijksmuseum.py` - suitable but should use current Data Services/IIIF carefully.
6. `british_museum.py` - stub only, disabled by default, with a clear "not suitable for commercial unrestricted download" reason.

## Open Questions

- Shopify product taxonomy, prices, vendor name, and final hosted image URL strategy are not yet specified.
- Exact print-quality thresholds should be validated against real museum image sizes; the current proposed defaults should be treated as conservative starting values.
- Category quotas may need adjustment after the first 5-10 verified images reveal which categories are abundant under strict license and resolution rules.
- Google Drive delivery should remain a later storage backend, separate from acquisition and validation.
