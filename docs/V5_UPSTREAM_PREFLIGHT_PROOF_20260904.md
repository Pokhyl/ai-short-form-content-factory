# V5 upstream-native preflight proof — 2026-09-04

## Scope

This proof belongs only to the clean `rebuild/agentic-editor-v5` branch. It is not a V4 continuation and is not a product/HUMAN PASS.

## Pinned upstream

OpenNolan checkout:

`/opt/ai-short-form-v5-upstreams/OpenNolan`

Exact commit:

`4457349c386ea1a89c01547f9a76fa650970c131` (`v1.0.2`, AGPL-3.0).

The V5 preflight verifies the checkout SHA before importing upstream tooling.

## Runtime proof

Fresh `v5/preflight.py` reported:

- Python `3.12.3`;
- `/usr/bin/ffmpeg` and `/usr/bin/ffprobe` available;
- `faster-whisper 1.2.1`;
- `edge-tts 7.2.8`;
- OpenNolan `DirectClipSearch`: AVAILABLE;
- OpenNolan `VideoCompose`: AVAILABLE;
- OpenNolan `Transcriber`: AVAILABLE.

The existing provider credentials are read from the already protected production environment at runtime; V5 does not copy secrets into Git or a new plaintext config.

With those existing free-provider credentials loaded, OpenNolan reported Pexels and Pixabay Video in addition to no-key sources such as Wikimedia and Archive.org.

## Active provider evidence

Static provider status was deliberately not treated as enough. Fresh active searches were run on three unrelated visual classes:

- mechanism: `turbocharger engine`;
- history: `Eiffel Tower construction`;
- comparison: `OLED screen display`.

Pexels, Pixabay Video, Wikimedia and Archive.org returned real candidates. Raw inventories remain runtime evidence rather than tracked source files.

The probe also found a real upstream health discrepancy: OpenNolan's Coverr adapter reported itself available but active API searches returned HTTP `401`. V5 therefore uses active search success as provider-health evidence rather than trusting `is_available()` alone. Coverr is not in V5's default inventory source set.

The returned inventories also demonstrate why asset-first planning is required: some providers return adjacent or irrelevant material even when the query is reasonable. Candidate availability is evidence for what can be made, not automatic proof of relevance.

## Disk/runtime cleanup

The frozen V4 Remotion Docker image, old OpenMontage V4 checkout and obsolete V4 Python tools environment were removed after their failure history had been committed. The V4 self-test service remains stopped.

This reclaimed enough disk space for the new isolated V5 runtime while preserving repository history and proof documents.

## Acceptance state

`technical_foundation_only`

No V5 artifact has been offered for human review yet.
