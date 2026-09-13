# Visual resolver handoff

> Current authorization update (2026-09-13): the user explicitly lifted the production deployment restriction and asked work to continue. Deploying the tested renderer and creating a NEW normal validation job are now authorized. Do not ask for deployment permission again. TTS/settings and old jobs must remain unchanged. Production validation is in progress; HUMAN PASS still requires the user to watch the resulting MP4.


Branch: `codex/visual-resolver-rework-20260913`.
Issue: https://github.com/Pokhyl/ai-short-form-content-factory/issues/8

## Required reading

1. Issue #8 and `docs/CODEX_VISUAL_RESOLVER_TASK.md`.
2. `docs/VISUAL_RESOLVER_REVIEW.md` for implementation and production-baseline details.
3. `docs/VISUAL_RESOLVER_MAPPING.md` for every acceptance narration → entity → media.

## Completed

- Replaced fuzzy/prefix subject selection with source aliases, dictionary-normalized complete phrases, conservative subject rules, and exact Wikipedia/Wikidata identity.
- Isolated anaphora to the previous resolved semantic scene; removed incoming history/topic fallback paths.
- Added all-member montage treatment for explicit lists; Commons depicts verification; file dedup; timed exact-image alternatives; preflight before TTS/render.
- Preserved the existing TTS adapter and Whisper implementation byte-for-byte after synchronizing the actual production baseline in commit `e9463e3`.
- 37/37 tests pass natively and in the built Linux amd64 renderer with network disabled. This includes 32 acceptance narrations across four languages and real Wikimedia replay for all eight UK scenes.
- Read-only live UK resolver check passes all eight scenes. Exact responses are committed as a replay fixture.
- Local Docker build succeeds. No production deployment or new production job was performed. No old job was modified.

## Resume safely

Work only on this branch. Read the PR and `git log` for final SHAs. The repository contains all implementation, tests, pinned NLP dependencies, replay data, mapping and build instructions; no previous agent memory is required.

The PR has been created and the additional resolver review regressions pass. Deployment is authorized. Do not replace production compose/workflows with the repository's older baseline configuration. Do not change Gemini TTS (`gemini-3.1-flash-tts-preview`, Enceladus, one synthesis per video), Studio UI, audio timing, or duration/quality gates. Failed/rejected jobs remain immutable.

There is no production MP4 and no HUMAN PASS. Next: deploy the reviewed image, create a NEW normal job via public intake, inspect audit and MP4, and request the user's visual verdict. Do not resume or repair old failed jobs.

Unsupported/ambiguous grammatical constructions and unavailable exact media fail preflight. Dictionary/source data are finite; passing the recorded scenarios is not a claim of unrestricted semantic understanding. Live source content can change; keep frozen tests deterministic and review any fixture update.
