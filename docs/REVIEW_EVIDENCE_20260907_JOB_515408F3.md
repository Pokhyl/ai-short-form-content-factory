# Review Evidence — 2026-09-07 — job 515408f3-0f17-4ce4-aaf5-63d709998ee9

Source product checkpoint: `c8d4da01d725821055467245cfa9dbfb7da54064` with only docs-only deployment evidence commit `94c4a554418350ce15bd9f42f84fe1cec0448fc5` added afterward. Product workflow blobs were unchanged by the docs commit.

Input submitted exactly once through normal WF01 intake:
`{"topic":"How the Panama Canal locks work","language":"ru","duration":15}`

Job: `515408f3-0f17-4ce4-aaf5-63d709998ee9`.

Execution chain:
- WF01 `16438` success
- WF02 `16439` success
- model gateways `16440–16444` success
- WF03 `16445` success
- duration-rewrite gateways `16446–16448` success
- WF04 `16449` success
- WF05/render `16450` success

Final persisted state: `review_ready/review`; no `last_error`.
Accepted continuous Edge voiceover duration: `16.420s`.

Exact artifact:
- DB path: `jobs/515408f3-0f17-4ce4-aaf5-63d709998ee9/render/final.mp4`
- container path: `/data/jobs/515408f3-0f17-4ce4-aaf5-63d709998ee9/render/final.mp4`
- host path: `/var/lib/docker/volumes/ai-short-form-content-factory_media_data/_data/jobs/515408f3-0f17-4ce4-aaf5-63d709998ee9/render/final.mp4`
- DB SHA256 = file SHA256: `0f765192024fb2f3cbc241b3eeac3d41509cd54fe7fd6a3745235be7ec66dae6`
- size: `1551163` bytes
- ffprobe: H.264 video, AAC audio, 1080x1920, 30 fps, 48 kHz stereo, container duration `16.434s`
- direct media-worker review endpoint HEAD: HTTP 200, `video/mp4`, content-length `1551163`, byte ranges enabled, no-store.

Story units/timing:
1. `0.000–4.688` — Панамский канал использует шлюзы для подъёма и спуска крупных судов.
2. `4.688–10.606` — Система поднимает суда на 26 метров до уровня канала, потом опускает обратно.
3. `10.606–16.420` — Ворота шлюзов работают как двойные двери, полая конструкция облегчает движение в воде.

Visual inventory/render proof:
- 3 visual segments, all `ready`
- 3 visual shots
- 3 unique media-library assets
- 3 unique perceptual clusters
- asset reuse `0`
- adjacent perceptual duplicates `0`
- each reserved shot persisted with preview-to-stored perceptual identity distance 1–2
- renderer `visual_quality.pass=true`, version `inventory-first-render-v1`
- `reserved_before_script=true`
- `post_freeze_search_used=false`
- composition quality `full-image-preserve-v1`, pass=true
- still policy `fit-preserve-with-blurred-fill`
- destructive still crop count `0`

The diagnostic `max_visual_cluster_duration_share=0.3604` exceeds the retained informational field `max_allowed_visual_cluster_duration_share=0.34`, but current source pass logic intentionally does not use duration share when every asset/cluster is unique. The active pass contract requires all source assets unique, sufficient unique clusters, no adjacent cluster duplicate and max cluster occurrence exactly 1; this job satisfies those conditions.

Studio review route is the existing authenticated path `/media/515408f3-0f17-4ce4-aaf5-63d709998ee9`, which Caddy maps directly to media-worker `/review/video/<job_id>`. It serves the exact artifact above; no copy or transcode was made.

Acceptance state: MACHINE `review_ready` only. HUMAN PASS/FAIL is intentionally unset until the user watches this exact MP4.
