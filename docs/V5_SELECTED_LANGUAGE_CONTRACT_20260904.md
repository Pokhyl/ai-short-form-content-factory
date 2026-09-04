# V5 Selected Output Language Contract — 2026-09-04

## Required behavior

The language selected in the product input is authoritative for the final spoken/text output.

`topic` may be written in any supported input language. The topic language must **not** determine the narration language.

For every job:

- `language=en` -> final script/narration is English;
- `language=pl` -> final script/narration is Polish;
- `language=ru` -> final script/narration is Russian;
- `language=uk` -> final script/narration is Ukrainian.

Research may use other languages when useful, but WF02 must resolve factual evidence into the selected output language before the script is persisted. It must never silently fall back to writing the final script in the source/topic language.

## Systemic correction

WF02 now prioritizes factual candidates that are directly in the selected language or have a verified language-link equivalent in the selected language. A missing language link on the highest-scoring source no longer forces the whole job to fail if another target-language equivalent is available.

WF04 also now accepts valid three-letter canonical subject tokens (for example `Sun`) instead of rejecting them because of the previous `>=4` token-length filter.

## Cross-language proof

Input supplied only through the n8n product path:

- topic: `почему солнце светит` (Russian text);
- selected language: `uk`;
- requested duration: `30 s`.

Resulting job:

- job: `bbd79a96-48ab-4f47-ae4c-340ce6789cc5`;
- status: `review_ready`;
- factual source language: `uk`;
- canonical title: `Сонце`;
- generated script language: Ukrainian;
- measured voiceover duration: `32.112 s`;
- final path: `jobs/bbd79a96-48ab-4f47-ae4c-340ce6789cc5/render/final.mp4`.

This proves that topic-input language and selected output language are now decoupled for the current n8n path.

Acceptance state remains `machine_rendered / review_ready`; no HUMAN PASS has been claimed.
