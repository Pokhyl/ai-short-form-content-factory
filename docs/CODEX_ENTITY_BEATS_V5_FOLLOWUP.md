# Codex follow-up: exact visual beats V5

## Scope
Continue the existing `Pokhyl/ai-short-form-content-factory` production project. Do **not** redesign the whole pipeline and do not repeat already completed resolver work.

Work only on branch:
`codex/entity-beats-v5-20260914`

The current production renderer on the VPS is based on local-only commit `262f25291ebb06dd3979b7f61098092f6d386f73` (`feat: render exact entity visual beats`). That commit is not present on GitHub, so do not assume this branch is byte-for-byte equal to production. Reconcile the existing branch implementation with the production facts below rather than overwriting good existing code.

## Do not touch
- Gemini narration model: `gemini-3.1-flash-tts-preview`
- voice: `Enceladus`
- one video = one TTS synthesis request
- no audio speed-up / slow-down
- Whisper remains only for timing extraction from the already-generated audio
- n8n remains the orchestrator
- failed/rejected jobs are immutable
- no generic-topic fallback and no quality-gate weakening
- no topic-specific Solar-System hacks

## Current production V5 result
Normal job:
`868dd3b2-9e9a-4ba8-90fc-edf5c748ff0b`

Video id:
`cmu1d55z9000001ombvb7g04a`

Exact public MP4:
`https://publisher.hodor.com.pl/webhook/jobs/video?job_id=868dd3b2-9e9a-4ba8-90fc-edf5c748ff0b`

Technical QA:
- ready
- 1080x1920
- H.264 + AAC
- 60.054 s
- Gemini TTS: 1 request
- narration length: 56.16 s
- target padding: 3.84 s
- 7 semantic scenes
- Whisper captions: 102
- alignment match ratio: 0.77
- renderer label: `semantic_scene_word_aligned_v5_entity_beats`

Resolver regression before deployment: 40/40 PASS across UK/RU/PL/EN.

## What V5 improved
The resolver no longer uses only one broad entity per semantic scene. It now resolves concrete visual beats such as:
- asteroid belt -> Mars -> Jupiter
- Ceres -> Pallas -> Vesta
- Neptune -> trans-Neptunian objects
- Pluto -> Sedna -> Haumea -> Makemake
- comet -> meteoroid -> cosmic dust
- dwarf planet -> natural satellite

This is directionally correct, but it is **not yet product quality**.

## Remaining systemic defects to fix

### 1. Hard cap of 4 visual beats drops explicit named entities
Current production `findVisualBeats()` clamps `maxVisuals` to 4. In the sentence:
`Найбільшими з них є Плутон, Седна, Гаумеа, Макемаке та Ерида.`
V5 selects Pluto, Sedna, Haumea, Makemake and silently drops Eris.

Required:
- for an explicit list of <= 6 concrete named entities, include all of them when scene duration can support a sane minimum hold;
- do not silently drop the last named object because of a global hard cap;
- for larger lists, use a deterministic group strategy rather than arbitrary truncation.

Add regression tests for 5 named entities in UK/RU/PL/EN.

### 2. Beat timing uses the wrong notion of token position
Production V5 stores `currentPosition` from `_rankSourceArticleLinks()`. That position is based on `tokens(sceneText)`, but `tokens()` removes stopwords and deduplicates with `Set`. It is **not a real word offset in the original sentence**.

Production then converts that value to caption timing using `currentPosition / sceneWordCount`. This can display a visual too early or too late.

Required:
- derive a real span from the original scene text: raw word index and preferably `startChar/endChar`;
- preserve repeated words; do not use deduplicated token order for timing;
- map the grounded concept span to the Whisper-aligned word/caption timeline;
- every visual beat must have deterministic real `startMs` and `endMs` (or equivalent `startSeconds/durationSeconds` if the existing branch already supports that correctly);
- beat boundaries must be monotonic and inside the semantic scene;
- no visual may be selected purely by equal-duration slicing when a textual span exists.

Add deterministic tests for span -> caption timing.

### 3. Audit does not expose visual beat timing
Production audit currently stores titles/sources but omits each beat's actual start/end time, making machine review impossible.

Required audit fields per beat:
- concept title / English concept
- resolution mode
- media title/source/identity key
- source width/height
- source text span (`startWord/endWord` and/or char span)
- `startMs`
- `endMs`
- hold duration

Add a machine gate that fails if beat timing is invalid or if a long scene effectively keeps one visual too long.

### 4. Entity extraction is still not the same as claim relevance
Example scene:
`Пояс астероїдів, що розташований між Марсом і Юпітером...`
V5 uses three beats: Asteroid belt -> Mars -> Jupiter.

Mars and Jupiter are named in the sentence, but isolated planet portraits are not necessarily the best illustration of the claim. The claim is **the asteroid belt between Mars and Jupiter**.

Required:
- visual beats should represent focal claims/objects, not mechanically every named token;
- distinguish focal list items from incidental relation endpoints, comparison objects, composition ingredients and subordinate-clause nouns;
- prefer an exact diagram/photo/render that illustrates the relation when one exact grounded visual exists;
- concrete named objects remain correct beats when the sentence is actually listing/describing those objects (Ceres/Pallas/Vesta; Pluto/Sedna/Haumea/Makemake/Eris).

Add negative regression tests: relation endpoints must not become standalone beats just because they are capitalized.

### 5. Low-resolution exact images are accepted and then enlarged to 1080x1920
Current production audit includes, for example:
- Pallas ~314x316
- Sedna ~320x320
- Haumea ~300x300

These are exact entities but visually poor after portrait rendering.

Required:
- prefer higher-resolution exact Commons/Wikidata alternatives for the same entity;
- establish a source-quality gate before render (choose a defensible threshold; do not hardcode one Solar-System exception);
- if the Wikipedia page image is low-resolution, continue searching exact-entity Commons/Wikidata instead of accepting it immediately;
- if no acceptable exact media exists, fail preflight rather than silently render a blurry asset.

Add tests for low-resolution page-image -> higher-resolution exact alternative.

### 6. Static-visual density must be measured, not guessed
User feedback on previous videos: too few images and visuals that are only generally on-topic.

Required:
- enforce a maximum static hold for long semantic scenes (approximately 4-5 seconds is a reasonable product target, but derive/encode it cleanly);
- do not create arbitrary 3-second semantic micro-scenes;
- visual beats live inside the semantic narration scene;
- short scenes may use one exact visual; long scenes need additional exact beats/alternatives when available;
- no duplicate underlying Commons file in adjacent beats/scenes.

Add audit/gate coverage for maximum hold and duplicate identity keys.

### 7. Avoid generic diagrams when a more direct exact visual exists
Current first scene resolves `Small Solar System body` to `Euler diagram of Solar System bodies.svg`. It is technically exact, but the product often feels like generic encyclopedia graphics.

Required:
- rank direct photographic/scientific rendered exact media above taxonomy/legend/logo/diagram assets when the narration does not specifically call for a diagram;
- diagrams remain allowed when they genuinely illustrate a spatial/relational claim better than an object portrait;
- do this via metadata/type/ranking rules, not topic-specific filenames.

## Current production scene audit summary
1. 0.00-4.16 — Small Solar System body — 1 visual
2. 4.16-16.60 — Asteroid belt / Mars / Jupiter — 3 visuals
3. 16.60-21.68 — Ceres / Pallas / Vesta — 3 visuals
4. 21.68-31.04 — Neptune / Trans-Neptunian object — 2 visuals
5. 31.04-36.68 — Pluto / Sedna / Haumea / Makemake — 4 visuals (Eris missing: defect)
6. 36.68-49.41 — Comet / Meteoroid / Cosmic dust — 3 visuals
7. 49.41-56.16 (+3.84 padding) — Dwarf planet / Natural satellite — 2 visuals

## Required validation
1. Preserve all existing resolver regressions; extend them for the defects above.
2. Tests must be deterministic and language-independent where applicable.
3. Build renderer locally.
4. Verify exact visual-beat plan before any expensive TTS.
5. Do not modify old jobs.
6. After systemic fixes, deploy and create a NEW normal job using the public intake path.
7. Audit exact narration -> claim/entity -> visual -> start/end timing.
8. Verify final MP4: 1080x1920, H.264, AAC, target duration, HTTP 200.
9. Extract representative frames/contact sheet from the **exact final MP4** and inspect for obvious topic mismatch, blurry low-res media, bad crop, and wrong beat timing.
10. Machine PASS is not final success. The user must watch the exact MP4 and explicitly give HUMAN PASS.

## Work rules
- Work autonomously to a finished code/test/deploy result.
- If a test or build fails, diagnose/fix/re-run; do not stop at the first error.
- No hacks, no weakened gates, no manual topic-specific selection.
- Do not touch TTS model/voice/timing architecture.
- Commit and push all changes to `codex/entity-beats-v5-20260914`.
- Open a PR when complete.
- At the end report only: tests, new job id, video id/URL, SHA and PR, plus any remaining blocker.