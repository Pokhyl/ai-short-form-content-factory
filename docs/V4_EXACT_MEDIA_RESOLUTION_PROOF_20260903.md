# V4 Exact-Media Resolution Proof — 2026-09-03

## Purpose

Advance the V4 automation from semantic visual obligations to reproducible exact-media resolution. This stage must prevent a future renderer from silently binding an arbitrary local file or generic stock result to an `exact_media` beat.

Production semantic-v3 remained frozen.

## Wikimedia Commons acquisition adapter

New module:

`prototype/v4/commons_media.py`

CLI command:

`fetch-commons`

The adapter:

- resolves a canonical Commons `File:` title through the MediaWiki API;
- requests a bounded-width derivative rather than always downloading the original full-resolution file;
- records canonical file title, Commons page URL, download/original URLs, MIME type, original and selected dimensions, orientation, license, license URL, artist, credit and description;
- downloads the exact bytes to the run directory;
- records byte size and SHA256;
- writes sidecar JSON provenance;
- rejects unknown/non-free licensing rather than allowing the asset to proceed silently.

Remote commits:

- adapter: `2996b3807331737fe1e70a6cf641323782a0a796`;
- tests: `fe8d0397b60936c33658fe08dfe1e9c39f246a34`;
- CLI integration: `c8656b2cf576547ffbb2759ef58f73d1f2038146`.

## Beat-level asset resolver

New module:

`prototype/v4/asset_resolver.py`

CLI command:

`resolve-assets`

For every `source_class=exact` beat, the resolver:

1. requires an explicit asset-map entry;
2. requires the local file to exist;
3. recomputes the file SHA256 and compares it with acquisition metadata;
4. verifies the expected Commons identity when `expected_file_title` is declared;
5. verifies actual dimensions/orientation against the declared layout contract;
6. attaches license/attribution/source metadata to the resolved timeline.

Constructed beats are explicitly marked `construction_required=true`. Contextual beats are intentionally rejected until a separate contextual-media resolver exists; they are not silently routed to generic stock.

Remote commits:

- resolver: `ea2e35265dd9e850d38d35b9ce0b97c4bd83a00b`;
- tests: `12372ee66094584089e1759e832943f8f5dfcd24`;
- CLI integration: `1d60ce70aaa01edd97c70aa46dba8e7a11d3dc9c`.

Local VPS commit containing the Commons + resolver stage:

`2e9375393e85e4509f3e287251d224cd867744f9`

Focused V4 suite after this stage: `22/22 PASS`.

## Real exact-media proof across different topic classes

### Eiffel E1 — historical construction

Commons identity:

`File:Louis-Emile Durandelle, The Eiffel Tower - State of the Construction, 1888.jpg`

Resolved derivative:

- dimensions: `1440x1832`;
- license: `Public domain`;
- SHA256: `9c67de360bab67bc5de849d7846bf1f2972ca0722b6152c48ef753fa309bc784`.

### Eiffel E5 — completed construction state

Commons identity:

`File:Achèvement de la Tour Eiffel, 1889.jpg`

Resolved derivative:

- dimensions: `1440x1956`;
- license: `Public domain`;
- SHA256: `45ddfb7b051fe4d3e5dbb522ba9fdf96f0701cc9480fab0b9cb999105d2594ac`.

### Zipper Z1 — exact macro object

Commons identity:

`File:Metalzipper.jpg`

Resolved derivative:

- dimensions: `1440x2166`;
- license: `Public domain`;
- SHA256: `2b9f1c974e60ef7a22e55c4771126175654f75e7aa08d26240ede7cd82f18501`.

## Cross-topic resolution results

The three active non-induction timelines were recompiled from current actual audio and then resolved through the same asset layer:

- Eiffel / Polish: `2 exact + 3 constructed`, all exact SHA verified;
- Zipper / Russian: `1 exact + 7 constructed`, all exact SHA verified;
- OLED/LCD / English: `0 exact + 6 constructed`, therefore no fake/random device media was introduced.

This is intentionally different from the failed approach `find some portrait stock for every beat`.

## Architectural decision

Exact-media acquisition is now a provenance-bearing automation layer. A renderer must consume the resolved timeline; it must not independently search for replacement media.

For constructed beats, the next layer must also be structured and reusable. Raw topic-specific SVG coordinates are not an acceptable semantic-director contract. The existing low-level Remotion `MotionDiagram` primitive may remain a rendering backend, but a higher-level generic graphic specification and layout compiler must sit above it.

## Immediate next action

1. define a high-level constructed-graphic schema using reusable visual grammar rather than topic-specific coordinate dumps;
2. validate the same schema family on Eiffel, zipper and OLED/LCD;
3. compile high-level specs deterministically into renderer geometry;
4. bind compiled graphic assets to the provenance-resolved timeline;
5. only then produce multi-topic renderer inputs and review complete videos.

No n8n/DB production rebuild. M8 remains `2/10`.
