# Release coverage inventory

Source commit: `6e08b289bc0fd1a00540ae0a89e8d44df5995e86`. Generated with `python3 scripts/inventory_release_coverage.py --output-dir acceptance/release-coverage`.

Static literal-reference inventory and explicit JSON fields, with manually inspected boundary evidence limits. No source evaluation, provider calls, DB calls or production mutations. Missing literal references may be dynamic; language/topic absence means unknown, not unsupported.

## Verified checkpoint and scope

Node883/883 and SQL8/8 are stored, hash-verified offline results. They are not whole-product acceptance. Separate worker runners are not included in Node883. This inventory calls no models and changes no production state.

| Inventory | Count |
|---|---:|
| tracked_fixture_count | 41 |
| tracked_runner_count | 94 |
| node_suite_file_count | 81 |
| sql_runner_count | 8 |
| separate_runner_count | 5 |

Separate runners: 5/5 PASS on recorded worker/n8n image IDs, without network. Includes two real full-resolution FFmpeg renders using synthetic audio/images. Initial 45s harness timeout and successful bounded 110s retry are both retained. See `separate-checks.json`; this is not a real multilingual product acceptance.

Latest checks: Node886/886, SQL8/8 retained with unchanged SQL/workflow hashes, separate runners5/5, current native integrated9 unique selections. S4/S8 received two fresh provider responses; the other seven are saved responses with matching current sources and contracts. This is offline release evidence, not a new production acceptance.

## Stage boundaries

Every row below has partial evidence; none is marked as a current-release integrated acceptance pass.

| Boundary | Supporting checks | Evidence limit |
|---|---|---|
| M4 -> M5 | `tests/m4-research-relevance.test.cjs`, `tests/semantic-preservation.test.cjs` | Separate component tests; current failed production job passed both stages, but no portable replay of the combined boundary was identified. |
| M5 -> M6 | `tests/voiceover-candidate-reuse.test.cjs`, `tests/measured-draft-reuse.test.cjs` | Workflow contract tests include synthetic audio; do not infer a real media identity check from these alone. |
| M6 -> M7 | `tests/alignment-dtw-regression.py` | Saved ASR/DTW data and worker timing functions; a saved audio hash does not prove fresh decode/alignment of the exact MP3. |
| M5 -> M8 | `tests/m5-m8-12108-fastening-contract.test.cjs` | Partial native validator/request replay plus generic controls; an executable whole-stage handoff is not established by filename or fixture presence. |
| M8 retrieval -> SQL | `tests/m8-12108-semantic-nomination-ranking.py`, `tests/m8-component-owner-ranking.py`, `tests/m8-paired-objects-ranking.py` | Actual saved pools, baseline/current SQL and rollback; new S4 pixels/provider acceptance are still unresolved. |
| M8 previews -> vision -> selection | `tests/gemini-visual-validation.test.cjs`, `tests/m8-9229-replay.test.cjs`, `tests/m5-m8-12108-fastening-contract.test.cjs` | Parser/collector and historical saved reviews do not establish a new strict nine-scene provider pass after the S4 change. |
| M7/M8 -> M9 | `tests/render-target-duration-regression.py`, `tests/render-fit-regression.py`, `tests/voiceover-candidate-reuse.test.cjs` | Worker rendering and workflow contracts are separate checks; synthetic FFmpeg media is not the latest real full-product MP4. |
| M9 -> review/product acceptance | `scripts/audit_final_media.py` | Audit tool exists; latest failed job never reached M9. No current-release four-case media acceptance is recorded in this checkpoint. |

## Explicit fixture metadata

Metadata records source fields, not inferred language from prose or filenames. Multiple fields may come from synthetic controls. Fixture presence/reference is not a passing provider or product result.

| Fixture | Explicit language/locale | Explicit target seconds | Referencing runners |
|---|---|---|---:|
| `tests/fixtures/m5-10042-language-repair-context.json` | uk | 45 | 2 |
| `tests/fixtures/m5-10042-language-review.json` | en, pl, ru, uk | unknown | 1 |
| `tests/fixtures/m5-10042-natural-language-repair.json` | uk | unknown | 1 |
| `tests/fixtures/m5-11226-timing-boundary.json` | uk | 30 | 1 |
| `tests/fixtures/m5-11230-semantic-coverage.json` | uk | 30 | 1 |
| `tests/fixtures/m5-11234-compass-visual-anchors.json` | unknown | unknown | 1 |
| `tests/fixtures/m5-11350-visual-repair.json` | uk | 30 | 1 |
| `tests/fixtures/m5-11354-visual-anchor.json` | uk | 30 | 1 |
| `tests/fixtures/m5-12064-mislocalized-language.json` | pl | 30 | 1 |
| `tests/fixtures/m5-12075-clause-review.json` | pl, pl-PL | 30 | 1 |
| `tests/fixtures/m5-9221-final-retry.json` | pl | 15 | 1 |
| `tests/fixtures/m5-9516-final-measured.json` | pl | 15 | 1 |
| `tests/fixtures/m5-9537-scene-segments.json` | pl | 15 | 2 |
| `tests/fixtures/m5-9660-final-word-count-compliance.json` | pl | 15 | 1 |
| `tests/fixtures/m5-9672-precision-continuity.json` | pl | 15 | 1 |
| `tests/fixtures/m5-9910-storyboard-repair.json` | unknown | unknown | 1 |
| `tests/fixtures/m7-9802-alignment.json` | unknown | unknown | 1 |
| `tests/fixtures/m7-short-terminal-scene.json` | unknown | unknown | 1 |
| `tests/fixtures/m7-trailing-asr-hallucination.json` | pl | unknown | 1 |
| `tests/fixtures/m8-11978-primary-secondary-fallback.json` | unknown | unknown | 1 |
| `tests/fixtures/m8-11994-invented-pressing-hand.json` | unknown | unknown | 1 |
| `tests/fixtures/m8-12004-component-owner-pool.json` | unknown | unknown | 2 |
| `tests/fixtures/m8-12015-paired-objects.json` | unknown | unknown | 2 |
| `tests/fixtures/m8-12040-fastened-result.json` | unknown | unknown | 3 |
| `tests/fixtures/m8-12040-qualified-owner.json` | unknown | unknown | 2 |
| `tests/fixtures/m8-12040-surface-owner.json` | unknown | unknown | 2 |
| `tests/fixtures/m8-12093-paired-preview.json` | unknown | unknown | 2 |
| `tests/fixtures/m8-12108-fastening-contract.json` | pl | 30 | 3 |
| `tests/fixtures/m8-9229-live-overlay-provider-responses.json` | unknown | unknown | 2 |
| `tests/fixtures/m8-9229-s5-paired-current.json` | unknown | unknown | 1 |
| `tests/fixtures/m8-9229-saved-provider-responses.json` | unknown | unknown | 2 |
| `tests/fixtures/m8-9229-workflow-v53.json` | unknown | unknown | 1 |
| `tests/fixtures/m8-9809-pexels-context.json` | unknown | unknown | 1 |
| `tests/fixtures/m8-9948-pexels-responses.json` | unknown | unknown | 1 |
| `tests/fixtures/m8-9948-request-contracts.json` | unknown | unknown | 1 |
| `tests/fixtures/pl15-v51-s3-powerhouse.json` | unknown | unknown | 1 |
| `tests/fixtures/pl15-v52-nameplate.json` | unknown | unknown | 1 |
| `tests/fixtures/pl15-v94-selected-commons.json` | unknown | unknown | 2 |
| `tests/fixtures/pl15-v99-dam-reservoir.json` | unknown | unknown | 1 |
| `tests/fixtures/release-m8-12108-integrated.json` | unknown | unknown | 1 |
| `tests/fixtures/wikimedia-hydroelectric-penstock.json` | unknown | unknown | 1 |

## Release blockers

1. Add or establish executable connected stage-boundary replay where inventory shows only separate checks.
2. Deploy and verify exact changed components only after closure.
3. Complete representative current-release multilingual/duration final-media acceptance; no current-release four-case evidence established.

Machine-readable fixture hashes, schemas, provenance fields, runner references and boundaries are in `coverage.json`. Report generation itself is not a test run.
