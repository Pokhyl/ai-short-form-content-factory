# V4 Cross-Topic Timeline Contract — Implementation Proof

Date: 2026-09-03

## Why this was added

The 25-cut portrait-first OpenMontage artifact still received HUMAN FAIL. Two systemic defects were identified:

- standalone typography (`hero_title`, `text_card`, `callout`) replaced the primary visual track;
- generic cooking/electric-stove stock was accepted because it was vertical and visually plausible, even when it did not directly represent the factual narration.

The fix must not be induction-specific. A structural timeline contract was therefore added and exercised across materially different topic classes.

## Code

Remote files:

- `prototype/v4/timeline_contract.py`
- `prototype/v4/tests/test_timeline_contract.py`

Remote GitHub commits:

- implementation: `8aa5365c384a73d603a2cf072b65e51f1f5f66fb`
- matrix tests: `47089b7e626afd5bdfcdab23dcc46bc0f0403ed0`

Local VPS prototype commit:

`d3cfcdea7f4661bc65037aa31a0dd8001cf386a3`

## Contract scope

The validator is deliberately structural. It does not attempt to rebuild semantic understanding with thresholds.

It enforces:

- continuous beat coverage with no timeline gaps/overlaps;
- a `primary_visual` for every beat;
- text/card/title/callout cannot be the primary visual mode;
- `generic_stock` cannot be used as factual fallback;
- every primary visual declares a visible subject/visual obligation;
- contextual media requires an explicit context justification;
- constructed visuals must use diagram/motion-graphic/generated-image representation;
- landscape/square photo/video cannot be used as normal fullscreen media; use contain/PIP/collage instead;
- text remains an overlay/annotation layer.

The contract does NOT impose an arbitrary cut duration or semantic similarity score.

## Cross-topic test matrix

The same validator is exercised against four materially different fixture classes:

1. induction / Ukrainian — exact induction media + mechanism diagram/motion graphics;
2. Eiffel Tower construction / Polish — exact historical landscape evidence + portrait exact media;
3. zipper mechanism / Russian — exact macro media + original mechanism motion graphic;
4. OLED versus LCD / English — constructed side-by-side display mechanism graphics.

## Test proof

Command run on the VPS:

`PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest -v prototype.v4.tests.test_contract prototype.v4.tests.test_timeline_contract`

Result:

- 12 tests run;
- 12 passed;
- 0 failures;
- 0 errors.

Specific negative tests verify rejection of:

- text-only primary visual;
- generic factual fallback stock;
- landscape fullscreen photo;
- contextual media without explicit justification;
- uncovered timeline gap.

## Status

This is a contract-level technical PASS only.

It does not prove that the next generated videos are good. Human review remains authoritative, and no production/n8n rebuild is allowed yet.

The next direct-prototype stage must use this same contract across the cross-topic matrix rather than tuning one induction artifact again.