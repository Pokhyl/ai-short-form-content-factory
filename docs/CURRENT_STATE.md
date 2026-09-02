# Current Project State — Rebuild

Last updated: 2026-09-02

This file is the authoritative source of truth for active branch `rebuild/simple-pipeline`. If chat memory, old branches, old workflow exports, or older docs conflict with this file, this file wins.

## Mandatory protocol

Before EVERY technical response, diagnosis, recommendation, code/config change, deployment, or test for this project:

1. Read `docs/PERMANENT_PROJECT_RULES.md` from GitHub.
2. Read this file from GitHub branch `rebuild/simple-pipeline`.
3. Architecture change: also read `docs/ARCHITECTURE.md`.
4. Milestone/acceptance/gate change: also read `docs/ROADMAP.md` and `docs/PROCESS_GATE.md`.
5. Upstream/provider change: also read `docs/UPSTREAM_DECISION.md`.

Repository state overrides chat memory. Unknown state must not be guessed.

## Product

Self-hosted AI Short-Form Content Factory:

`topic -> evidence -> final narration -> continuous natural voice -> timed beats -> truthful/relevant visuals -> render -> human review`

Publishing is outside the automatic generation chain.

## Runtime invariants

Exactly three persistent project services:

- `ai-short-form-content-factory-n8n-1`
- `ai-short-form-content-factory-postgres-1`
- `ai-short-form-content-factory-media-worker-1`

Per-video external API cost remains `0 PLN`.

Measured VPS class:

- 2 vCPU
- 3.7 GiB RAM
- 2.0 GiB swap
- no GPU
- constrained local disk

Do not add a fourth persistent service unless a separately measured blocker proves it necessary and the architecture decision is documented first.

## Voice — current production

WF03 is Edge-only continuous voice. Fixed voices:

- EN `en-US-AndrewNeural`
- PL `pl-PL-MarekNeural`
- RU `ru-RU-DmitryNeural`
- UK `uk-UA-OstapNeural`

Provider rate/pitch/volume remain default. No `atempo`, rate correction, pause rewrite, or silence-removal filter is allowed.

The destructive `silenceremove` stage was removed in implementation commit `146abeb`. Media-worker preserves provider timing and only normalizes format to 48 kHz stereo PCM WAV.

Production WF02 was recalibrated against untouched/default-rate Edge timing in implementation commit `097cdb7`, but its current monolithic generation architecture is now superseded by the staged redesign below.

## Visuals — current production

WF04 currently preserves canonical reference provenance plus structured `reference_media_kind = diagram | animation | photo` for technical-reference beats. The repair implementation is commit `7a302ce`.

The fresh zipper run after that repair proved reference-form selection, but also exposed a real stock semantic defect: a generic drysuit zipper photo was selected for a beat requesting continuous-coil detail. This remains an unresolved product issue and must be addressed by the redesigned visual-intent + stock eligibility boundary, not by a zipper-specific patch.

## Permanent provider rule

Production MUST NOT depend on request-count/rate/quota-limited hosted semantic AI as a required generation dependency.

Fresh production evidence:

- `gemini-3.6-flash` returned `429 RESOURCE_EXHAUSTED` for Free Tier request quota;
- `gemini-3.5-flash` simultaneously returned `503 UNAVAILABLE / high demand`;
- repeated fresh attempts also produced provider `503` failures.

Do not wait for quota reset and do not repair this with sleeps, retry loops, model hopping, extra keys/accounts/projects, paid fallback, or weakened acceptance.

## Rejected local-model experiment

Do not continue benchmarking local models against the old monolithic WF02 request.

The old zipper EN15 request was about 4.7k input tokens before generation and required one model response to contain exact narration tokens, claim/evidence links and six complete visual-scene objects. Qwen3 0.6B/1.7B fit the VPS individually but the old workload was too slow/brittle; complex JSON-schema/GBNF decoding also produced sampler/latency problems.

This is classified as an architecture-boundary failure, not a reason to keep model hopping.

## Selected staged architecture — NOT YET IMPLEMENTED

The new source-of-truth architecture is defined in `docs/ARCHITECTURE.md` and `docs/UPSTREAM_DECISION.md`.

### WF02 becomes research + narration only

1. Retrieve bounded factual sources.
2. Split source text into deterministic evidence units.
3. Select a compact diverse evidence packet before local inference: normally at most two evidence units per final sentence (`6/10/14/18` max selected units for `15/30/45/60` seconds).
4. Persist selected evidence/provenance durably in PostgreSQL.
5. Call a local semantic engine with only topic + target language + duration guidance + selected evidence.
6. Return/persist narration + sentence evidence references only.
7. Do NOT create scenes and do NOT generate visual intent in WF02.

### WF03 becomes final voice + timed beat creator

1. Synthesize one continuous default-rate Edge voice.
2. Measured duration remains the hard gate.
3. If the first synthesis misses the unchanged duration gate, allow at most one bounded TEXT-fit rewrite against the same persisted evidence; revalidate and synthesize once more. Never modify audio speed/pauses.
4. If final voice still misses, fail closed.
5. Only after final script + voice pass, deterministically create `6/10/14/18` timed beats/scenes.
6. Visual-specific scene fields remain unset at this stage.

### WF04 becomes visual intent + sourcing

1. Generate compact local visual intent only from final timed beats + relevant evidence/canonical entity context.
2. Persist visual-support provenance for fact-critical specificity.
3. Enforce eligibility before ranking:
   - exact identity match;
   - canonical reference provenance + requested representation form;
   - metadata-supported `concrete_subject` for truth-critical stock;
   - contextual stock only when substitution remains truthful.
4. Only eligible candidates reach local SigLIP relative ranking.
5. Empty eligible lanes fail closed.

### WF05/WF06

Render/review boundaries remain conceptually unchanged and consume only final accepted voice, timed beats and visuals.

## Required database changes

Before production implementation:

- add durable job evidence/provenance storage (`job_evidence` or equivalent);
- allow scene rows to exist in a pre-visual `timed` state with narration/timing present and visual fields null;
- require complete/consistent visual fields before a scene can advance to visual-ready state;
- persist evidence references that justify fact-critical visual intent.

No migration has been applied yet for this redesign.

## Heavy-compute invariant

`media-worker` must have one global heavyweight-compute boundary. Local semantic inference and SigLIP must not run concurrently or remain simultaneously resident when that exceeds measured memory.

Semantic inference must release model memory after the request. SigLIP lifetime must be explicitly controlled. Concurrent-job testing must prove no RAM/swap exhaustion before production acceptance.

## Local model selection — next phase only

Do not select/deploy a model using the old giant WF02 prompt.

First implement a local evaluation harness for the new compact contracts. Then evaluate feasible multilingual local candidates on materially different topics and all four languages. A weak model is rejected; Gemini is not restored as fallback.

## Frozen product acceptance

CASE 1 remains:

`How does a zipper work? / en / 15`

No later matrix case may be accepted before CASE 1 passes on one unchanged redesigned runtime:

- selected evidence is relevant and persisted;
- narration facts/coherence pass;
- natural clean Edge measured duration passes;
- timed beats exactly reconstruct the final narration/voice timeline;
- every visual intent is evidence-consistent;
- every selected asset/provenance/content check passes;
- final ffprobe passes;
- human-visible voice/render quality passes.

First real product failure stops progression and is repaired systemically, never with a topic-specific patch.

## Immediate next action

Implement the redesign in a disposable/local branch surface before production mutation, in this order:

1. schema/migration for durable evidence + timed pre-visual scenes;
2. deterministic evidence reducer and compact narration contract/harness;
3. evaluate local narration candidate(s) against that compact contract;
4. voice/text-fit boundary + timed scene creation;
5. compact visual-intent contract + stock/reference/exact eligibility changes;
6. full local regression;
7. document exact implementation proof;
8. bounded deploy with rollback evidence;
9. completely fresh CASE 1.