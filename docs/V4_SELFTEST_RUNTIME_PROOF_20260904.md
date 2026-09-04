# V4 self-test runtime proof — 2026-09-04

## Scope

This document records the isolated Product-First V4 self-test path exposed through `studio.hodor.com.pl`.

Semantic-v3 remains frozen. The V4 Studio UI uses only `/api/v4/*` and does not create new jobs through legacy `/api/jobs`.

## Runtime

- runtime root: `/opt/ai-short-form-v4-selftest`;
- runner: `/opt/ai-short-form-v4-selftest/runner.py`;
- systemd: `ai-short-form-v4-selftest.service`;
- bind: `172.18.0.1:8094`;
- Studio UI: `/opt/ai-short-form-content-factory/studio/index.html`;
- review media: `/opt/ai-short-form-content-factory/studio/v4-media/`;
- Caddy: `handle_path /api/v4/* -> 172.18.0.1:8094`.

Git-tracked runtime snapshot:

- `services/v4-selftest/runner.py`;
- `services/v4-selftest/studio-index.html`;
- `services/v4-selftest/ai-short-form-v4-selftest.service`;
- `services/v4-selftest/Caddyfile.fragment`;
- `services/v4-selftest/README.md`.

`/health` returns `{"ok": true, "service": "v4-selftest"}` after the latest restart.

## Research / director path

- research uses self-hosted SearXNG;
- semantic director uses the internal model gateway;
- no Wikipedia-only path;
- continuous Edge TTS remains separate from semantic scene structure;
- Whisper word timestamps from exact generated audio remain the timing authority.

## Self-test failure: editing layer collapsed toward semantic scenes

GPS job:

`dafae8be-67c7-4b7d-966a-7147dc678738`

The initial director returned only four shots for a fifteen-second job even though the prompt requested five to seven. Runtime validation only rejected fewer than four shots, so the invalid plan passed. The first two semantic scenes each contained one visual asset for the whole scene.

Independent cross-topic evidence came from the failed `Зеленский / ru / 30` self-test: six semantic scenes and six total shots, one shot per scene, while the thirty-second normal target is eight to ten.

Root cause: shot density existed only as prompt guidance; the runtime did not enforce a duration-specific editing-shot contract.

Systemic correction:

- new pure contract `prototype/v4/selftest_director_contract.py`;
- duration-specific minimum shot counts are enforced;
- `semantic scene == one editing shot` collapse is explicitly rejected;
- factual `stock` returned for explain/proof/close is normalized to `exact_media` before validation;
- placeholder `must_show` values such as `subject`/`object` are replaced with the concrete visual query before validation;
- one bounded shot-structure correction pass may repair only the editing layer while the semantic fingerprint remains frozen;
- no blind retry/sleep loop was added.

Proof tests: `prototype/v4/tests/test_selftest_director_contract.py`.

## Self-test failure: valid media selections were discarded

During GPS revalidation, the media selector returned all six valid choices as a direct JSON mapping:

`{"S1A":"...","S1B":"..."}`

The runner only read `payload["selections"]`, so every direct-mapping response became an empty selection map and the job falsely failed with `no truthful media selected for S1A`.

This was an output-contract mismatch, not a media-relevance failure.

Systemic correction:

- new strict parser `prototype/v4/selftest_media_contract.py`;
- accepts either the documented wrapper `{"selections": {...}}` or an equivalent direct mapping;
- requires the exact expected shot-id key set;
- rejects extra/missing keys and invalid values;
- `null` remains a real fail-closed media decision;
- the selector prompt now shows the exact wrapper schema;
- Commons candidates are filtered to image media before semantic selection, preventing PDF/book results from entering the visual candidate list.

Proof tests: `prototype/v4/tests/test_selftest_media_contract.py`.

## Corrected GPS six-shot render

The rejected GPS artifact was not regenerated from research or speech.

Reused unchanged:

- existing evidence/research;
- existing spoken script;
- existing exact `voice.mp3`;
- existing Whisper word timestamps.

Only editing-shot/media/timeline/render stages were corrected.

Final visual track has six distinct shots across three semantic scenes:

1. `S1A` — contextual portrait Pexels smartphone/city shot;
2. `S1B` — contextual portrait Pexels city intersection shot;
3. `S2A` — exact Commons `File:Benefon GPS Antenna.jpg`;
4. `S2B` — exact Commons `File:GPS Block IIIA.jpg`;
5. `S3A` — exact Commons `File:GPS trilateration fig1.jpg`;
6. `S3B` — exact Commons `File:Pin-location.png`.

Timing intervals from the exact-audio aligned render manifest:

- `S1A` 0.000–1.460 s;
- `S1B` 1.460–3.820 s;
- `S2A` 3.820–8.040 s;
- `S2B` 8.040–10.340 s;
- `S3A` 10.340–12.820 s;
- `S3B` 12.820–16.380 s.

Exact public MP4:

`/opt/ai-short-form-content-factory/studio/v4-media/dafae8be-67c7-4b7d-966a-7147dc678738.mp4`

Machine identity:

- SHA256 `1f3cdb5a71ebc4304d8b2a09195bcbd05bb97a6d1f4e7cdd464cfbc87cf998f9`;
- size `18,537,526` bytes;
- ffprobe duration `16.448 s`;
- H.264 `1080x1920`;
- AAC `48 kHz`, stereo.

The source render and the Studio public copy have the same SHA256.

Acceptance state: `machine_rendered`, not `human_approved`.

## Regression suite

After introducing the two self-test contracts and retaining all previous V4 tests:

`69/69 PASS`

No semantic-v3 code path was re-enabled.
