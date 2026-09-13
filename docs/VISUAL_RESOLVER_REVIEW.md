# Visual resolver review — Issue #8

No production deployment or production job was performed. Human review of a production MP4 remains outstanding.

## Implementation

The resolver uses the current narration and source-linked aliases. UK/RU/EN dictionary lookups and PL morphological dictionary analyses normalize complete, ordered phrases; unknown words are never guessed by prefix, edit distance or suffix. Explicit aliases take priority. Comparison clauses, locative context and unrelated incoming `mediaContext` cannot override the current subject. Unsupported or ambiguous constructions fail closed.

Preflight owns the ordered scene list. Anaphora can use only the immediately preceding resolved semantic scene in the same source/language. Incoming free-text history is ignored. Sentence segmentation runs before the existing one-shot narration synthesis, preserving the narration text.

Localized Wikipedia concepts are grounded through Wikidata IDs. English section redirects never authorize the containing article's image. Listed groups render every explicitly named member as a montage. Commons candidates require an unambiguous whole-subject filename and structured depicts evidence; multi-object media require every depicted item to be an instance/subclass of the selected group. Search rank is not evidence. SVG raster thumbnails and GIF images are supported.

File identity drives deduplication. Same-entity reuse is recorded only when no unused exact alternative exists. Long scenes alternate available exact assets in shots of at most eight seconds. If no exact alternative exists, the audit records `same_entity_no_alternative`. Different entities cannot share the same file as a fallback.

## Validation commands

```sh
python3 -m venv .venv
.venv/bin/pip install -r engine-overlay/visual-requirements.txt
VISUAL_PYTHON="$PWD/.venv/bin/python" npm test
VISUAL_PYTHON="$PWD/.venv/bin/python" npm run test:mapping
docker build --platform linux/amd64 -t visual-resolver:review-20260913 engine-overlay
docker run --rm --network none --platform linux/amd64 --entrypoint node \
  -v "$PWD:/verify:ro" -w /verify visual-resolver:review-20260913 --test tests/*.test.cjs
```

Tests cover 32 narrated acceptance cases across UK/RU/PL/EN, negative subject/media cases, previous-scene isolation, media reuse, timing/shot planning, and preflight-before-TTS/render ordering. The original duration tolerances remain unchanged. `tests/fixtures/wikimedia-uk.json` replays the successful live Ukrainian acceptance run offline, including the real section redirect, all eight listed planet images, rasterized SVG, group Commons image and GIF. Synthetic API contract fixtures are explicitly distinguished from that live recording.

`scripts/resolver-mapping.cjs --live --uk-only` performs a read-only live resolver check; it never synthesizes, renders, writes jobs or deploys. Add `--record <path>` only when intentionally refreshing the API fixture.

## Production source synchronization

Commit `e9463e3` copies the existing production `ShortCreator.js`, `PortraitVideo.js`, `Whisper.js`, `Kokoro.js` and Dockerfile into the stale repository baseline, byte-for-byte. This prerequisite makes the actual renderer integration reviewable. Subsequent resolver changes do not modify `Kokoro.js` or `Whisper.js`. The production Gemini gateway, `gemini-3.1-flash-tts-preview`, `Enceladus`, one synthesis request, audio timing implementation, workflows, job records and Studio UI were not changed.

The repository's compose/workflow files still represent its older baseline; use the existing reviewed production configuration when deployment is eventually authorized. Do not replace live configuration wholesale with these older files.

## Data and dependencies

- Simplemma 1.1.2: dictionary lookup only, MIT; https://github.com/adbar/simplemma
- Morfeusz2 1.99.15: Polish dictionary analyses, BSD-2-Clause; https://morfeusz.sgjp.pl/doc/license/en
- Wikimedia fixtures were captured read-only on 2026-09-13. Each response retains its exact API URL. The source article fixture stores linked title/surface pairs rather than article prose. Wikipedia/Wikimedia text and media retain their respective source licenses; Wikidata structured data is CC0. Media URLs and exact filenames in the mapping identify the source file description pages and license records.

## Remaining review boundary

Passing resolver tests is not HUMAN PASS. No new production video was created. The next production deployment/render requires review of this PR and then visual review of the exact new MP4. Old failed/rejected jobs remain untouched.
