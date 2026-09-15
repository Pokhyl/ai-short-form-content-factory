# Codex continuation checkpoint — Alpha Centauri / visual resolver

Work only on branch `codex/entity-beats-v5-20260914` and continue the existing PR #10. Do not restart architecture work.

## Current authoritative state

The branch has just been synchronized from the VPS with the latest resolver work in:
- `engine-overlay/Pexels.js`
- `engine-overlay/VisualSubject.js`
- `engine-overlay/VisualBeats.js`
- `tests/safety.test.cjs`
- `tests/visual-beats.test.cjs`

Do not revert these files to older PR versions.

Latest Alpha Centauri preflight on the VPS resolved the 8-scene extract as:
1. Proxima Centauri -> exact Wikidata P18 `New shot of Proxima Centauri, our nearest neighbour.jpg`
2. Alpha Centauri -> exact Wikidata P18 `Best image of Alpha Centauri A and B.jpg`
3. Alpha Centauri anaphora -> exact English/Wikidata system image
4. Proper motion -> exact Wikidata P18
5. Celestial sphere -> exact Wikidata P18
6. Edmond Halley -> exact P18/portrait
7. Thomas Henderson -> exact P18/portrait
8. Proper motion -> exact Wikidata P18

Systemic fixes already implemented and must be preserved:
- exact source-entity Wikidata local label/aliases are added to the source lexicon, so unlinked local names like `Альфа Центавра` can resolve to source page `Толіман` / Q12176;
- grammar roles are resolved before ambiguous-subject rejection for temporal subjects, reported-content clauses, predicate complements, anaphoric properties, attribution, and group possessors;
- neutral demonstrative anaphora (`це/это/to/this`) is immediate-previous-scene only;
- `Усі компоненти X ...` / `All components of X ...` resolves X as group possessor;
- reporting clauses like `Іннес дійшов висновку, що Проксима Центавра...` resolve the content-clause subject, not the reporter;
- literal `%` in Wikimedia filenames no longer crashes `decodeURIComponent`;
- exact Wikipedia article media is accepted only from filename/title identity, not from description text;
- sibling entities sharing one token are rejected (`Proxima Centauri` must not accept `Alpha Centauri A/B` merely because both contain `Centauri`);
- structured Wikidata P18 is ranked above ordinary article media;
- portraits/direct images outrank grave/memorial/plaque/book media;
- exact P373 category pagination + exact-title validation is retained;
- possession relation object handling (`have/мають/... -> Natural satellite`) and meta list-page suppression are retained;
- visual density remains fail-closed; do not weaken the 5s static-image gate.

## Tests / current blocker

Targeted safety + visual-beats tests are green: 63/63 on the latest VPS source.

The last full test run was 90/92 PASS. The only two failing tests were old offline replay fixtures:
- `tests/live-replay.test.cjs`: `real Wikimedia acceptance responses replay deterministically without network`
- `tests/live-replay.test.cjs`: `all seven previously rejected production narrations pass sequential exact-media replay`

Both fail only because the new source-entity alias enrichment adds this deterministic request which is not recorded in the fixture:
`https://uk.wikipedia.org/w/api.php?action=query&titles=Сонячна+система&redirects=1&prop=pageprops&ppprop=wikibase_item&format=json`

Do NOT remove the new identity request just to satisfy fixtures. Update the recorded replay fixtures deterministically for the new exact source-page -> wikibase_item lookup, then run the entire suite. Expected goal: full PASS with no gate weakening.

## Runtime facts outside GitHub branch

Production/VPS WF10 currently has a newer timing calibration that is not present in this GitHub branch tree:
- UK 60s `cleanWordsPerSecond = 1.78`
- `numericComplexitySeconds = -0.35`
- MediaWiki section headings are stripped before sentence selection.

That planner selected an Alpha Centauri candidate with 107 spoken words / numeric complexity 2 / estimated narration 59.412s. A previous shorter Alpha Centauri extract (97 spoken / 4 numeric) synthesized to 52.92s.

Do not modify TTS behavior:
- model: `gemini-3.1-flash-tts-preview`
- voice: `Enceladus`
- exactly one TTS synthesis request per video
- no speed-up/slow-down
- Whisper only for timing extraction.

Production has NOT yet been switched to the latest `alpha-93` resolver state because the full suite was still 90/92 due only to replay fixture drift.

## What to do now

1. Start from current branch state. Do not re-audit or redesign.
2. Update only the deterministic offline replay fixtures required by the new exact source-page Wikidata lookup.
3. Run the full native/Docker suite. Fix any real regression; do not weaken gates.
4. Verify Alpha Centauri preflight still maps Proxima vs Alpha correctly and historical persons to portraits/direct images.
5. Preserve all current hard rules and exact-media behavior.
6. Commit and push to the same branch / PR #10.
7. If you have access to the production VPS/runtime, deploy only after full PASS and create a NEW normal job. If you do not have VPS access, stop after commit/push/PR update and report the exact SHA and remaining deployment step.
8. Never claim HUMAN PASS. Only the user can do that after watching the exact MP4.

Return only: full test result, commit SHA, PR status, and the exact remaining blocker if any.
