# Architecture — Clean Rebuild

Last updated: 2026-09-02

`docs/CURRENT_STATE.md` is the operational source of truth. This file defines the intended production boundaries.

## Product

`topic -> evidence -> final narration -> natural voice -> timed beats -> visual intent + real media -> render -> human review`

Publishing remains outside the automatic generation chain.

## Persistent runtime

Exactly three persistent services remain:

1. `n8n`
2. `postgres`
3. `media-worker`

No fourth persistent service is introduced by local inference. A local semantic model, when used, runs as bounded compute inside `media-worker` and exits/releases memory after the request.

### n8n

Owns orchestration, public factual retrieval, deterministic evidence reduction, PostgreSQL transitions, validation boundaries, duration preflight, and stage hand-offs.

### PostgreSQL

Owns durable product state, selected evidence/provenance, final script, timed beats, visual intent, selected assets, render state and review state. The `n8n` schema remains private to n8n.

### media-worker

Owns bounded local compute and media operations:

- local semantic inference behind small internal endpoints;
- Edge voice synthesis/storage/format normalization;
- local visual ranking;
- image/video persistence;
- FFmpeg/ffprobe and render.

It never writes product state directly to PostgreSQL.

## Cost / provider boundary

Per-video external API cost remains `0 PLN`.

A request-count/rate/quota-limited hosted semantic AI may not be a REQUIRED production dependency. Gemini Free Tier is rejected from the critical path after repeated production `429 RESOURCE_EXHAUSTED` and `503 UNAVAILABLE` failures.

Hosted upstream services must not be used as search loops. Edge voice is therefore limited to exactly one automatic synthesis attempt per job. Duration fitting happens before TTS using local deterministic estimation and local text fitting.

Forbidden quota workarounds: sleeps, retry loops, quota-window waits, model hopping, extra keys/accounts/projects, paid semantic fallback, repeated TTS synthesis for fitting, or weaker acceptance.

Public zero-cost factual/media retrieval may remain external. The architecture must fail closed when evidence/media is insufficient instead of inventing content.

## Core correction: no monolithic semantic request

The previous WF02 contract was architecturally wrong for this VPS: one model request received a large evidence dump and simultaneously had to write narration, enforce duration shape, cite evidence, and plan every visual beat. That produced multi-thousand-token prompts/outputs and made local inference unnecessarily slow and brittle.

The replacement architecture separates deterministic work from narrow semantic work. No local model is asked to be researcher, duration controller, evidence database and visual planner at once.

## WF01 — intake

Unchanged responsibility:

- validate `topic`, `language`, `duration`;
- create exactly one durable job;
- invoke WF02.

## WF02 — research + narration only

WF02 no longer creates visual scenes.

### A. Retrieval

Retrieve bounded public factual sources for the requested topic. Source adapters are replaceable; Wikipedia/MediaWiki is one adapter, not the semantic engine. Exact identities/canonical titles may also use structured public sources such as Wikidata/Wikimedia where appropriate.

### B. Deterministic evidence packet

Source text is split into atomic evidence units. A deterministic reducer selects a small, diverse packet relevant to the immutable topic.

Target packet size is proportional to final sentence count rather than raw source size: normally at most two evidence units per requested narration sentence. For `15/30/45/60` seconds with `3/5/7/9` natural sentences, the normal maxima are `6/10/14/18` selected units.

Selection uses source/title/topic relevance and diversity; it is not performed by the generative model. Every selected unit keeps exact source provenance and is persisted durably.

### C. Narrow local narration call

The local semantic engine receives only:

- immutable topic;
- target language;
- duration/length guidance;
- the compact selected evidence packet.

It returns only the narration and sentence-to-evidence references. It does NOT return visual scenes.

Required narration invariants:

- EN/PL/RU/UK;
- one continuous natural narration;
- exactly `3/5/7/9` natural sentences for `15/30/45/60` seconds;
- every sentence cites only selected evidence units that directly support it;
- no new numeric/date/identity specificity unsupported by topic/evidence;
- no viewer-facing dependence on incidental source artifacts;
- deterministic validator fails closed before voice.

Clean-Edge calibration is used to plan text length before TTS. WF02 persists selected evidence plus the validated narration, then invokes WF03. No `scenes` rows are created yet.

## WF03 — one-shot natural voice + timed beats

WF03 owns the final narration/voice boundary.

### A. Local duration preflight before Edge

The project must not call hosted TTS repeatedly to discover the right text length.

Before any Edge request, a deterministic local duration estimator evaluates the narration using the fixed target voice/language calibration plus accumulated clean production measurements. This estimator is local and costs no provider request.

If the draft is predicted outside the target band, a bounded local TEXT-fit rewrite may occur before TTS. The rewrite must use the same persisted evidence packet and pass the same factual/language/sentence validator. No hosted TTS call is spent during this fitting stage.

The preflight is systemic per fixed voice/language, not topic-specific. Measured production durations continuously provide calibration data; no single-topic exception is allowed.

### B. Exactly one continuous Edge synthesis

Automatic production performs exactly one job-level Edge synthesis using fixed voices:

- EN `en-US-AndrewNeural`
- PL `pl-PL-MarekNeural`
- RU `ru-RU-DmitryNeural`
- UK `uk-UA-OstapNeural`

Provider rate/pitch/volume remain default. No `atempo`, time-stretch, speed correction, pause rewrite, silence removal, padding, or scene-by-scene TTS.

There is no second automatic Edge synthesis for duration fitting and no hidden retry loop around provider limits.

### C. Measured duration acceptance

The single clean Edge output is measured once. That measured duration is authoritative.

If it passes the target-relative quality gate, continue. If it misses, the job fails closed. The pipeline does not automatically rewrite and call Edge again.

The failed measured sample may be retained as calibration evidence for future jobs so the local pre-TTS estimator improves across topics for that fixed voice/language.

### D. Timed beat creation

Only after the single final script + measured voice are accepted, WF03 deterministically splits the final narration into `6/10/14/18` transport beats and computes beat timings that exactly cover the accepted voice duration.

WF03 inserts `scenes` rows containing narration + timing only. Visual-specific fields remain unset until WF04. This prevents visual plans from becoming stale and keeps TTS provider usage to one request per job.

## WF04 — visual intent + sourcing

WF04 receives final timed beats, not a draft script.

### A. Narrow visual-intent call

A separate compact local semantic call receives:

- topic;
- final beat narrations;
- only the evidence references relevant to those beats;
- canonical source/entity context.

It returns compact visual intent only:

- `visual_mode = stock | reference | exact`;
- `visual_query`;
- `visual_brief`;
- `reference_query` + `reference_media_kind` when reference is required;
- `concrete_subject` for truth-critical stock;
- exact identity fields when substitution would be misleading;
- supporting evidence IDs for fact-critical visual specificity.

It may not invent new named identities, materials, dates, measurements or technical specificity absent from topic/narration/evidence.

### B. Deterministic visual eligibility before ranking

The model never chooses the final asset.

- exact lane: candidate must match the required canonical identity;
- reference lane: candidate must come from the canonical reference provenance and match requested `diagram | animation | photo` representation form;
- truth-critical stock lane: candidate metadata must substantively support `concrete_subject` before relative image ranking;
- contextual stock lane: replacement is allowed only when it stays truthful to the beat.

Only eligible candidates reach local visual ranking. Relative SigLIP ranking chooses among eligible candidates; it is not an absolute truth gate.

Selected asset provenance and the reason it was eligible are persisted. Empty eligible lanes fail closed.

## WF05 — render

Consumes only final accepted artifacts:

- one continuous accepted voice track;
- final timed beats;
- one accepted visual per beat.

Output remains 1080x1920 H.264/yuv420p 30fps + AAC 48 kHz stereo. Subtitles are derived from final persisted narration. ffprobe validates the final file before `review_ready`.

## WF06 — human review

Generation stops at `review_ready`. Human review remains a separate boundary; publishing is not automatic.

## Durable data changes

The redesigned pipeline requires explicit evidence provenance rather than keeping the evidence packet only inside n8n execution data.

Add a durable evidence relation (for example `job_evidence`) containing at minimum:

- `job_id`;
- deterministic `evidence_id`;
- source ID/title/URL/language;
- passage/section locator;
- exact evidence text;
- deterministic selection score/rank;
- created timestamp.

`scenes` must support a pre-visual `timed` state where narration/timing are present but visual-intent fields are still null. Database constraints must require complete/consistent visual fields before a scene can advance to visual planning/sourcing completion.

## Heavy-compute memory boundary

The VPS has 2 vCPU / 3.7 GiB RAM / 2 GiB swap and no GPU. Therefore `media-worker` must have one global heavyweight-compute gate.

A local semantic model and SigLIP may not execute concurrently or remain simultaneously resident when that exceeds the measured memory budget. Semantic inference is a bounded subprocess/request and releases its model memory when complete. SigLIP lifetime must also be explicitly controlled rather than assumed harmless because it is cached.

No production deployment is accepted until concurrent-job tests prove that heavyweight model overlap cannot exhaust RAM/swap.

## Local semantic engine selection

Model selection happens only AFTER the compact evidence/narration and visual-intent contracts above exist in a test harness. Benchmarking a small model against the old multi-thousand-token monolithic WF02 request is no longer an architecture decision criterion.

A candidate local model must pass materially different science/history/entity topics across EN/PL/RU/UK using the compact contracts and the unchanged final validators. Weak candidates are rejected; no Gemini fallback is restored.

## Production acceptance

After implementation and full local regression, start a completely fresh frozen CASE 1:

`How does a zipper work? / en / 15`

CASE 1 passes only when all are true on one unchanged runtime:

- evidence is relevant and persisted;
- narration is factual/coherent;
- local duration preflight passes before TTS;
- exactly one clean Edge synthesis is performed;
- measured clean Edge duration passes;
- timed beats reconstruct the final narration;
- every visual intent is evidence-consistent;
- every selected asset/provenance/content check passes;
- final ffprobe passes;
- human-visible voice/render quality is acceptable.

The first real product failure stops progression and is repaired systemically before later matrix cases.