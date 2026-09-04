# V4 annotated exact media + Commons discovery proof — 2026-09-04

## Purpose

Replace the rejected `text/box/arrow as primary visual` path with a reusable factual-media path:

`discovery -> free-license candidate -> materialize without re-query -> hash-verified exact asset -> optional transparent motion annotation -> vertical renderer`

This is a cross-topic architecture change. It is not an induction-specific fix.

## Annotated exact media path

Implemented across:

- `prototype/v4/asset_resolver.py` — new `annotated_exact` source class; exact asset keeps the same SHA/license/dimensions checks as `exact`;
- `prototype/v4/graphic_compiler.py` — annotations compile as a transparent layer and declare `visual_basis=exact_media_annotation`;
- `prototype/v4/render_manifest.py` — emits `annotated_media` with both verified asset and compiled overlay;
- `prototype/v4/render_bundle.py` — stages the verified asset while preserving annotation props;
- `prototype/v4/remotion/VerticalShort.tsx` — renders exact media first and transparent motion annotation above it.

Generic box/label graphics remain rejected as standalone primary visuals. This path does not weaken `visual_adequacy.py`.

## Commons discovery

Implemented:

- `parse_commons_search_response()` filters invalid and non-free candidates;
- `search_commons_candidates()` supports deterministic on-disk cache keyed by normalized query + limit + requested width;
- cached results avoid repeated provider calls;
- HTTP `429` raises explicit `CommonsRateLimitError`; there is intentionally no blind retry or arbitrary sleep;
- `materialize_commons_candidate()` downloads a previously discovered candidate directly from its preserved download URL, rechecks free-license metadata/dimensions, writes bytes + SHA256 + provenance JSON and does not repeat the search API call.

## Real provider failure recorded

A rapid multi-query discovery run was rate-limited by Wikimedia Commons with HTTP `429 Too Many Requests` after several distinct sequential searches.

Decision:

- do not add arbitrary `sleep`;
- do not add blind retry loops;
- cache successful discovery results;
- materialize selected candidates without re-query;
- keep discovery request count low by using one high-quality semantic query per visual obligation and reuse cached results.

## Saved multi-query findings

Existing query results were inspected offline after the rate limit.

### Eiffel Tower construction / PL

Useful exact candidates include:

- `File:Eiffel Tower under construction (cropped), 1888-11-14.jpg` — portrait, Public domain;
- `File:Paris Eiffel Tower Caissons for foundations.jpg` — portrait, Public domain;
- `File:Pierre Petit Eiffel Tower under construction.jpg` — portrait, Public domain;
- multiple 1888 construction photographs from Paris collections under CC0/Public domain.

### Zipper mechanism / RU

Useful exact candidates include:

- `File:Reissverschluss Teile (fcm).jpg` — portrait, CC BY-SA 4.0, explicit zipper-component diagram;
- `File:Reissverschluss Teile 2 (fcm).jpg` — portrait, CC BY-SA 2.5;
- `File:Zipper by David Ring.jpg` — portrait, CC0;
- existing exact local `File:Metalzipper.jpg` — portrait, Public domain.

### OLED vs LCD / EN

Useful exact candidates include:

- `File:OLED spin statistics.png` — portrait, CC BY-SA 4.0, schematic/simplified OLED structure;
- `File:OLED-Pixel.2T1C (P-TFT).svg` — portrait, Public domain;
- `File:OLED diagram.jpg` — portrait, CC BY-SA 4.0;
- `File:OLED-Schema vector.svg` — landscape, CC BY-SA 2.5; valid only with contain/diagram treatment, never stretched to fullscreen.

## Materialized cross-topic assets

Three candidates were materialized from already-saved discovery results without another Commons search request:

### Eiffel foundations

`File:Paris Eiffel Tower Caissons for foundations.jpg`

- selected dimensions: `1440x2168` portrait;
- Public domain;
- local SHA256: `cfabc89f226ba84dc7bc0ffce4337b39d89fd05bc14b52890531204585a7d24f`.

### Zipper components

`File:Reissverschluss Teile (fcm).jpg`

- selected dimensions: `1440x2567` portrait;
- CC BY-SA 4.0;
- local SHA256: `38c8ba35f83c2c68562968d4ecb74b96af6492bb88c08b83165d2284fa6649cf`.

### OLED structure

`File:OLED-Schema vector.svg`

- selected raster representation: `1440x1407` landscape;
- CC BY-SA 2.5;
- local SHA256: `55473616849f0ba2cf46e986df1faff0f4f1211e87ed81b4f4de90c1453523fb`;
- must use contain/diagram treatment.

## Test proof

Authoritative GitHub branch was checked from a clean detached worktree after the connector writes:

- remote HEAD: `20a3c7a9bff8d0c8f635ce3e5354c75a48820b7f`;
- focused V4 suite: `47/47 PASS`.

## Next action

Do not render the old E2/Z2/O1 card-graphic fixtures.

Convert the cross-topic matrix to truthful exact/annotated media obligations using the discovered assets, keep constructed graphics only where they have a real pictorial basis, then build fresh render manifests and inspect complete videos before user review.
