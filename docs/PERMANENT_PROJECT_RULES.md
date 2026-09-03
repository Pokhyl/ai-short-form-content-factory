# Permanent Project Rules — Product-First V4

These rules are mandatory for all work on branch `rebuild/product-first-v4`.

## 1. Read GitHub first

Before technical work read fresh:

1. `docs/PERMANENT_PROJECT_RULES.md`;
2. `docs/CURRENT_STATE.md`;
3. `docs/PRODUCT_FIRST_V4.md`;
4. relevant history/reference docs.

Repository/runtime state overrides chat memory.

## 2. Product quality outranks internal elegance

A machine-valid video that sounds bad or shows irrelevant footage is a PRODUCT FAIL.

Do not certify quality from database state, diversity metrics, ffprobe, similarity scores or workflow success alone. Those are technical checks only.

Human review of the exact artifact remains authoritative during V4 bring-up.

## 3. No more bespoke semantic-threshold maze

Do not rebuild semantic understanding from topic-specific mappings, narration-fragment token overlap, arbitrary threshold tuning, special retries or other hand-built approximations.

Use the common architecture proven across mature open-source short-video projects: semantic script/storyboard first, actual-audio timing, scene-specific visuals, normal editing/rendering, preview/review.

## 4. Use mature upstream patterns before inventing

Before adding a new subsystem, check whether mature open-source projects already solve it.

Primary references include:

- `harry0703/MoneyPrinterTurbo`;
- `rayventura/shortgpt`;
- `AbdullahNaveed/ai-shorts-generator`;
- `gyoridavid/short-video-maker`;
- `het8802/OpenNolan`;
- `Cstrp/vml`;
- established Remotion/FFmpeg short-video patterns.

Prefer adapting proven components/contracts over writing a new replacement.

Respect upstream licenses and preserve attribution when code is reused.

## 5. Cost boundary

Do not make paid per-video APIs mandatory.

Free stock/media and local/open-source components remain preferred. A semantic model must be provider-pluggable. A capable local model may run on hardware suitable for it; do not force a weak general model onto the small VPS merely to maintain an old service-count rule.

Quota-limited hosted free tiers must not be the only required production path.

## 6. Speech contract

TTS receives speech-ready text, not raw source prose.

General multilingual text normalization must handle units, abbreviations, symbols, ranges, punctuation and markup before synthesis. No topic-specific pronunciation patches.

Captions/timing must come from the actual generated audio through Whisper/faster-whisper/whisper.cpp or equivalent forced alignment.

Do not fabricate caption timing from fixed beat counts.

## 7. Visual contract

Stock footage is not the default answer for every scene.

Every storyboard scene declares its representation mode, such as:

- exact media;
- stock;
- diagram/motion graphic;
- screen/text/card;
- optional generated image.

Factual/mechanism scenes must not silently degrade to generic lifestyle footage.

Provider metadata alone is never proof of visible relevance. CLIP/SigLIP may rerank but are not semantic directors.

If relevant footage is unavailable, change representation mode rather than insert unrelated stock.

## 8. Direct prototype before orchestration

Do not rebuild n8n/DB workflows first.

The direct V4 CLI must make a human-approved vertical video before database/orchestration integration resumes.

No production deployment until direct prototypes pass across multiple topics/languages.

## 9. No hacks

Permanent rule remains: no topic-specific hacks, acceptance bypasses, hidden retries, special-case blacklists, provider sleeps, threshold weakening or one-off patches that only make the current fixture pass.

## 10. Production freeze

The semantic-v3 production runtime is frozen as rollback/reference. Do not create new semantic-v3 jobs or consume additional Edge syntheses on it.

## 11. Durable history

Every meaningful failure, verified root cause, architectural decision, upstream adoption, prototype result and deployment/rollback must be recorded in GitHub before moving to the next independent stage.

Old chronology remains in `docs/ENGINEERING_HISTORY.md`. V4-specific chronology may also be recorded in `docs/ENGINEERING_HISTORY_V4.md`, but do not erase old history.

Do not rely on chat memory for project decisions. If an error, failed experiment, accepted rule or architectural conclusion can affect future work, persist it in the repository.

## 12. Cross-topic anti-overfit rule

Never validate or tune a general solution on one topic only.

Any new visual strategy, renderer behavior, pacing rule, media-selection rule, semantic-director contract or acceptance rule must be exercised on a materially diverse validation set before it is treated as architecture.

The validation set must vary the kind of visual problem, not just the wording. It should include materially different categories such as:

- a technical/mechanism explainer;
- a concrete person/place/object/history topic with exact-media needs;
- a process/list/comparison topic suited to cards, diagrams or mixed visuals;
- multiple languages across the V4 target set.

A change that only improves the current fixture is not accepted as a project solution.

When a current topic exposes a defect, extract the general defect, record it, then verify the fix on other topics before continuing production architecture work.

## 13. Acceptance vocabulary

Use these states clearly:

- `technical_pass` — code/render checks passed;
- `machine_rendered` — playable output exists;
- `human_approved` — user watched and accepted the exact artifact.

Never equate `technical_pass` or `machine_rendered` with product acceptance.