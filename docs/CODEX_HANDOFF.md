# Codex handoff — production video factory

Updated: 2026-09-20

## Goal

Finish and harden the existing production project Pokhyl/ai-short-form-content-factory.

This is a general-purpose n8n short-form video factory, not a one-video task.

Input contract:
- topic
- language
- duration in 15/30/45/60

Required output:
- automatic research -> script/storyboard -> one continuous TTS narration -> local alignment -> relevant visuals -> 1080x1920 render -> strict machine QA;
- free-only providers/services already used by the project;
- n8n remains the orchestrator;
- no Ollama/local LLM/model-worker;
- TikTok publishing, when used later, must be draft/inbox only.

## Production

Repo path on production VPS:
/opt/ai-short-form-content-factory

Production n8n:
https://publisher.hodor.com.pl

User Studio:
https://studio.hodor.com.pl/

Do not touch:
- https://n8n.hodor.com.pl
- protected MCP/ADMIN workflows
- unrelated containers/projects

Production workflow IDs:
- M3 VideoM3Intake001
- M4 VideoM4Research001
- M5 VideoM5Storyboard001
- M6 VideoM6Voiceover001
- M7 VideoM7Alignment001
- M8 VideoM8Visuals001
- M9 VideoM9RenderQa001
- self-test API VideoSelfTestApi001

Current production versions after the latest deploy:
- M5 versionCounter 81, versionId b548aee4-660f-4997-a17c-1d8fa24c38b3
- M8 versionCounter 41, versionId d889cb1d-c808-4e19-889e-35b06648da19

Current media-worker image:
sha256:5cf02e01d9cfb693d266bedc2f77b866fcee5960bb0a0654923b79be144e1874

At handoff:
- publisher HTTP 200
- Studio HTTP 200
- media-worker running/healthy, restart count 0

## Protected production facts

- publisher.hodor.com.pl is the single production n8n for this project plus existing MCP/ADMIN automation.
- Existing MCP/ADMIN workflows are protected.
- Existing credentials are protected.
- Project credential names referenced by exported workflows include Gemini Text and Video Factory Postgres; credentials themselves are not stored in this repository.
- Do not create a second production n8n or a new public n8n domain.
- Supporting Postgres/media-worker/SearXNG remain separate from the production n8n container.

## Important fixes already implemented

### M4 research
- systemic provider fallback and live-source handling;
- no topic lookup tables.

### M5 script/storyboard
- repair prompts now interpolate actual scene/shot counts instead of literal ctx.* text;
- JSON parser tolerates a narrow class of extra trailing JSON closers but rejects arbitrary trailing prose;
- semantic scene minimum accepts complete two-word scenes;
- pre-TTS word-count heuristics no longer override measured TTS;
- deterministic nearest-safe narration hybrid is allowed before another real TTS measurement;
- preview TTS uses real measured samples; median is the robust M5 estimate;
- M6 remains the authoritative strict final-audio duration gate;
- final near-miss stability rechecks preserve the original configured tolerance;
- generic/topic-independent validation only.

### M6 voiceover
- retries independent final TTS syntheses;
- only persists audio that passes the strict measured-duration gate;
- expression bug in TTS retry reservation fixed.

### M7 alignment
- numeric words are normalized to values, preserving non-equivalence: 30 != 40;
- Whisper token numeric sequences such as twenty + five normalize to 25;
- common apostrophe variants are punctuation-normalized consistently, fixing Ukrainian cases such as в'язкою;
- real UK Whisper regression reconstructs the normalized transcript exactly after the fix;
- existing global/scene lexical quality gates remain.

### M8 visuals
- provider degradation: a failed provider request is recorded honestly with its real HTTP status and zero candidates; remaining providers may satisfy the shot;
- failed provider responses are not written to the visual cache;
- strict per-shot relevant-asset requirement remains;
- Wikimedia request/download pacing added;
- Wikimedia candidate MIME allowlist matches media-worker supported formats;
- photo-first policy remains;
- generic semantic device/form descriptors are not treated as domain-specific subject words;
- compound primary-subject matching now requires a real distinctive subject term when such a term exists, plus query/intent context, instead of requiring nearly every compound word literally;
- known real regression candidates now pass while an unrelated negative-domain candidate still fails.

## Regression matrix

Use exactly these cases:

1. PL 15s — jak działa elektrownia wodna?
2. EN 30s — how do bees make honey?
3. RU 45s — как работает GPS?
4. UK 60s — як утворюються вулкани?

Run sequentially, not concurrently. The free Gemini tier exposed a 15 RPM rate limit during concurrent M5 tests, creating unrelated HTTP 429 failures.

### Last full runs before M8 v41

All below used M5 v81 and M8 v40.

PASS:
- PL15 c7d649af-f43d-41ed-a366-dd624a7d5ee3 -> machine_qa_passed
- EN30 96694991-1342-418f-a2eb-b7c727df0832 -> machine_qa_passed
- RU45 ae56e7ce-2028-4e2b-bf75-9256e5db346b -> machine_qa_passed

FAIL:
- UK60 df2de78d-2f99-47e0-94f6-a452e9494ce2
- reached M8 after M4/M5/M6/M7 all passed
- M8 failure: no compliant relevant visual candidate for shot S7-A
- shot: hidden/underground magma pool / rock cavity
- this exposed an overly literal compound primary-anchor rule

The S7-A scorer defect was then fixed systemically and deployed as M8 v41.

### M8 v41 scorer regression smoke

Passed real positive cases:
- UK magma pool candidate -> score 78, rejected=false
- RU navigation device candidate -> score 100, rejected=false
- PL turbine runner candidate -> score 80, rejected=false
- EN bee mouthparts candidate -> score 86, rejected=false

Negative control:
- unrelated swimming-pool portrait against a GPS navigation request -> score 46, rejected=true

## What remains

Do not call this finished yet.

1. Run a NEW sequential 4-case regression matrix on the currently deployed M5 v81 / M8 v41.
2. Every row must reach M3 -> M9 and machine_qa_passed.
3. Record for each row:
   - new job_id
   - M4/M5/M6/M7/M8/M9 statuses
   - final status
   - QA details
4. If a row fails:
   - inspect the exact production execution/data;
   - identify the systemic cause;
   - patch once;
   - validate;
   - deploy only affected component;
   - rerun a fresh job for that same row.
5. Do not lower visual relevance or audio timing thresholds simply to make a case pass.
6. After 4/4 machine PASS, inspect the exact four final MP4s manually:
   - strict vertical 1080x1920;
   - no text-description placeholders/cards;
   - no corrupt/unsupported assets;
   - no generic unrelated imagery;
   - enough visual changes;
   - visuals semantically tied to each narration scene/evidence;
   - continuous natural narration;
   - final duration within the existing strict gate.
7. Then update docs, run production/post-state checks, commit/push the final acceptance state.

## Operational discipline

- Do not reuse terminal failed jobs.
- Do not change topics/languages to make tests easier.
- No topic-specific lookup tables or manual asset bindings.
- If a command times out, inspect actual state before retrying.
- Never stack blind Docker restarts.
- Restart only the service that needs it.
- Do not reset existing intended repository changes.
- Preserve PostgreSQL as source of truth.
