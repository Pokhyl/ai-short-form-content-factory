# Codex task — rebuild visual resolver correctly

Work on the existing production project. Do not redesign the whole pipeline.

## Goal
Fix visual selection systemically so every semantic scene gets a relevant visual and wrong-topic media is rejected before render.

## Do not touch
- Gemini TTS model/voice: `gemini-3.1-flash-tts-preview` + `Enceladus`.
- One video = one TTS synthesis request.
- Do not speed/slow audio.
- Do not weaken duration/quality gates.
- Failed/rejected jobs are immutable.
- Do not redesign Studio UI.

## Current production behavior
The renderer already has semantic scenes and Whisper-derived real audio timings. The remaining blocker is visual relevance.

Bad finished job used eight scenes but many visuals were wrong/repeated. Examples:
- `Меркурій, Венера, Земля, Марс.` resolved to `Earth`.
- `Пояс астероїдів ...` has previously resolved to `Inner planet`.
- `За орбітою Нептуна розташовано транснептунові об'єкти ...` has previously resolved to `Neptune`.
- Fuzzy/history ranking has repeatedly produced visually related but semantically wrong entities.

The current source has already moved toward exact-only grounding in `engine-overlay/Pexels.js`, but this must be finished and tested, not patched scene-by-scene.

## Required architecture behavior
For each semantic scene:
1. Determine the main subject of the CURRENT scene.
2. Prefer an explicit alias/group in the current sentence (`звані також газовими гігантами`, etc.).
3. Otherwise prefer the main multi-word entity/topic in the current sentence.
4. A single named entity must not beat a more specific current multi-word subject merely because it appears earlier.
5. History may be used only to resolve explicit anaphora (`з них`, `ці`, `these`, etc.), and only from the immediately previous semantic scene.
6. Resolve the chosen local-language concept to its exact English Wikipedia/Wikidata concept.
7. Media may come from exact English Wikipedia page image or exact-subject Wikimedia Commons media.
8. No generic source-topic fallback such as random `Solar System` when the scene entity is different.
9. No partial/fuzzy substitute if exact grounding cannot be established. Fail preflight instead of rendering bad media.
10. Different semantic scenes should normally receive different media. Reuse is allowed only if the exact semantic entity is genuinely the same and no other exact media exists.

## Explicit acceptance cases
These must resolve as follows or to an equivalently correct exact group/entity:

- `Меркурій, Венера, Земля та Марс, звані також планетами земної групи...`
  -> terrestrial/inner planets group, NOT Mercury/Earth alone.

- `Юпітер, Сатурн, Уран та Нептун, звані також газовими гігантами...`
  -> Gas giant / giant planets group, NOT Inner planet.

- `У Сонячній системі є дві ділянки, заповнені малими тілами.`
  -> Small Solar System body or a correct small-body group.

- `Пояс астероїдів, що розташований між Марсом і Юпітером...`
  -> Asteroid belt, NOT Mars/Jupiter/Inner planet.

- `Найбільшими об'єктами поясу астероїдів є Церера, Паллада та Веста.`
  -> Asteroid belt OR an intentional multi-entity treatment; do not arbitrarily choose one object unless the scene itself is split.

- `За орбітою Нептуна розташовано транснептунові об'єкти...`
  -> Trans-Neptunian object, NOT Neptune.

- `Найбільшими з них є Плутон, Седна, Гаумеа, Макемаке та Ерида.` after a TNO scene
  -> Plutoid / dwarf-planet / TNO group as context warrants, not an unrelated prior entity.

- `Сонячний вітер ...`
  -> Solar wind / heliosphere as the current sentence warrants, never Mars/Solar corona because of media search noise.

## Tests required before production deploy
Add deterministic resolver tests covering the acceptance cases above and at least these failure modes:
- listed individual vs group entity
- early main subject vs later comparison phrase
- named entity vs multi-word subject
- anaphora using only previous scene
- ambiguous Commons co-subject filename rejection
- no generic topic fallback
- media dedup across adjacent scenes

Run the tests repeatedly; no topic-specific hardcoded exception for `Solar System` is allowed. The rules must generalize to UK/RU/PL/EN.

## Production validation
Only after tests pass:
1. Build renderer image from source.
2. Run resolver preflight for every scene BEFORE expensive TTS/render where practical.
3. Create a NEW normal job via the public intake endpoint.
4. Do not repair old failed jobs.
5. Verify audit JSON scene by scene: narration -> grounded entity -> selected media title/source.
6. Verify final MP4: 1080x1920, H264 video, AAC audio, correct duration, public HTTP 200.
7. Do not claim final success. User must watch the exact MP4 and explicitly give HUMAN PASS.

## Working rule
If a test exposes a wrong entity, fix the general resolver rule and add a regression test. Do not add a string-specific hack for the failing sentence/topic.
