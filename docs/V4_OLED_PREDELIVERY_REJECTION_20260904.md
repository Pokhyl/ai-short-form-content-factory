# V4 OLED pre-delivery rejection — 2026-09-04

## Artifact

Case: OLED vs LCD / English

Exact rendered artifact on VPS:

`/opt/ai-short-form-v4-runs/cross-topic-20260903/oled-en/render-bundle/out.mp4`

- duration: `32.427 s`;
- video: H.264, `1080x1920`;
- audio: AAC, 48 kHz stereo;
- size: `2,835,530` bytes;
- SHA256: `e779cac7db4fc38353a0b5ad8b0f1aa463cd6e766e76c1fc62461257ea451b61`.

The artifact was produced successfully by the unified `VerticalShort` renderer. This proves the renderer plumbing, not product quality.

## Pre-delivery rejection

The artifact is **not** a HUMAN PASS and is not being promoted as a review candidate.

Structural audit of the exact render manifest found six primary `motion_graphic` beats. Each compiled graphic is dominated by generic presentation primitives (`rect`, `text`, `line`) and 4-5 text labels. Example labels include `backlight`, `LCD panel`, `OLED pixel`, `self-emitted light`.

This repeats the already rejected product defect in a new form: text/cards/arrows replace the meaningful primary visual instead of annotating one.

## Root cause

The defect is architectural, not OLED-specific.

`graphic_spec.py` v1 only exposes entities as label + generic shape (`box`, `pill`, `circle`) plus relations. `graphic_compiler.py` v1 therefore necessarily compiles factual mechanisms into boxes, labels and arrows. A technically valid compiler cannot produce a rich factual visual from a contract that does not represent one.

Therefore the following are rejected as a primary factual visual:

- generic label boxes;
- text-card diagrams;
- arrow-only flow diagrams;
- changing text instead of changing/annotating meaningful imagery.

They remain allowed only as secondary annotation primitives.

## Systemic fix

Added `prototype/v4/visual_adequacy.py` and integrated it into `render_manifest.py`.

Primary motion graphics now require an explicit `visual_basis` from one of:

- `exact_media_annotation`;
- `pictorial_primitive`;
- `data_chart`;
- `map`;
- `screen_capture`.

Generic boxes/labels/arrows without such a basis fail before render-manifest generation.

Current cross-topic matrix result with the new guard:

- Eiffel / PL: rejects at `E2`;
- zipper / RU: rejects at `Z2`;
- OLED/LCD / EN: rejects at `O1`.

This is intentional: the previous compiler output is no longer allowed to reach the expensive renderer.

## Test proof

Focused V4 suite after the guard: `42/42 PASS`.

The suite includes positive pictorial-basis cases and a negative test that rejects a primary box/label/arrow diagram.

## Next architecture direction

Do not loosen the new guard to make old fixtures pass.

The next reusable visual layer is **annotated exact media / truthful pictorial basis**:

`resolved exact image/video/diagram -> optional crop/contain/zoom -> semantic motion overlays -> captions`

Motion graphics should normally explain or annotate a real subject, mechanism, diagram, map, chart or screen capture. They should not replace that subject with a presentation card.

This must be exercised across Eiffel, zipper and OLED/LCD before any n8n/DB integration.
