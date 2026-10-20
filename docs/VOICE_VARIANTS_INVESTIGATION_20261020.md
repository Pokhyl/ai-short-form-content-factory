# Voice correction investigation — 2026-10-20

Production SQL deferral fix remains deployed and verified. Studio runtime remains f98a351; no new application deployment, TTS or full production job in this session.

Candidate: whole-sentence alternatives, exact measured word/character window, bounded source-ID subsets with complete original fact-ID coverage, exact scene-bound reviewer quotations, reason-before-verdict review. It remains disabled (variant_correction is not enabled in wiring).

Evidence:
- whole-variants: rejected by exact quotation validation; original first two scenes each bind f1 and f2 despite narrating different portions.
- bound-variants: model approved insect protection as established fact despite source hypothesis. Human review REJECTED.
- fact-variants: model approved winter instead of preparation for winter. Human review REJECTED.
- review-controls: revised reviewer rejected both known bad drafts (2 calls).
- reasoned-variants: model approved 'plants slow chlorophyll' instead of its production, duplicated claim coverage and awkward narration. Human review REJECTED. Do not synthesize or deploy this result.

Tests: whole-variant/voice tests 30 passed; Gemini adapter tests 20 passed. Full Factory Next suite 173 passed before final prompt/schema refinement; focused tests rerun after refinement. Unit success does not establish semantic quality.

Remaining blocker: current generation and semantic reviewer can agree on incorrect shortened meaning. Further live prompt-only trials should stop. Next work should use saved replies for offline fact-to-scene allocation and a reusable semantic evaluation set, then compare an independently validated free-tier reviewer capability before another bounded provider test. Preserve the strict duration, source and native-language gates. No paid fallback, replay of failed job IDs, or altered voice speed.

No new MP4 was produced; the automatic factory is not declared fixed.
