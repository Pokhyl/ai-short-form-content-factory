# Personal subject continuation — 2026-09-15

Branch: `codex/entity-beats-v5-20260914`; PR #10.
Read together with `CODEX_ALPHA_CENTAURI_CONTINUE.md`; do not revert its resolver changes.

## Confirmed runtime evidence

New normal job `f8c5a105-8afd-44c3-8a2a-aed34fb9f5d1`, video `cmu1pxjon000001l0husk971o`, failed preflight before TTS/render. Its **first** input scene starts `Однак він приховав свої результати...`; `mediaHistory` is empty. There is no preceding semantic scene containing Henderson. Later Bessel / 61 Cygni mentions are subordinate context, not authorization to infer an absent subject. This failed job stays immutable.

The earlier `ambiguous_subject` diagnostic obscured the missing antecedent. Leading personal subject pronouns now use only the immediately previous scene, after more specific claim roles. Without that scene, they fail with `missing_antecedent`. UK/RU/PL/EN coverage includes subordinate named people and chemicals, orphan pronouns, the exact production sentence, reporting/property precedence, and non-leading pronouns. No topic-specific identity rules were added.

## Validation and next boundary

Native full suite: 97/97 PASS, zero skips. Linux amd64 renderer image built successfully; full offline container suite: 97/97 PASS, zero skips. The original source Wikidata fixtures and resolver mechanisms remain intact. TTS, timing gates, n8n, and existing jobs were not edited.

This change does not make the invalid opening narration renderable. Do not attach an antecedent from the source article or manufacture history to force a pass. A future normal input must begin with a self-contained semantic scene. Live planner calibration resides outside GitHub; do not overwrite it with the older repository workflow. No deployment or new job was performed for this diagnostic correction. Production remains on `bb562e1371d8522914bafcce5504cdb24397877f` from the preceding validation.
