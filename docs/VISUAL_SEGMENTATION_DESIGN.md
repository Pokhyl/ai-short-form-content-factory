# Visual Segmentation Architecture

Last updated: 2026-09-03

This document defines the replacement for the rejected `one timed beat -> one independently sourced visual` model.

## Decision

`timed beats` and `visual segments` are different product concepts and remain different durable entities.

Timed beats exist to cover the accepted one-shot Edge voice track exactly and drive subtitle timing. They are transport/timing units, not independent media-search obligations.

Visual sourcing operates on deterministic semantic `visual_segments` built from adjacent timed beats and their persisted evidence provenance.

The production path is:

`accepted voice -> timed beats -> deterministic semantic visual segments -> visual shots -> truth eligibility -> local SigLIP ranking -> perceptual duplicate control -> render timeline -> post-render frame gate -> human review`

No generative model is added to visual planning.

## Why the previous model is rejected

Fresh production job `4372be34-c417-415f-92f6-63481b3b5686` produced 18 timed beats for a measured `57.216 s` Ukrainian voice track and then failed old WF04 with `perceptually unique truth-eligible assignment 11/12`.

Transport beats created for exact voice/subtitle timing were being treated as independent semantic media-search obligations. Long videos therefore required many near-unique assets for micro-fragments of one continuous explanation.

This is not solved by weakening diversity gates. The media-search unit is changed instead.

## Durable entities

### `scenes`

Existing `scenes` remain timed narration/subtitle beats. They own sequential beat number, narration fragment, exact start/end/duration and narration/evidence provenance. They no longer require independently selected media per beat.

### `visual_segments`

A visual segment is a contiguous semantic interval covering one or more adjacent timed beats.

Required durable fields include `job_id`, sequential `segment_number`, start/end/duration, first/last covered beat, combined narration, support evidence IDs, canonical subject/visual target, lane, sourcing status and timestamps.

Visual segments must cover the full accepted voice timeline without gaps or overlaps.

### `visual_shots`

Shots define the video image timeline. Each shot owns exact timing, selected media-library asset, rank/selection metadata, perceptual cluster identity and representation kind.

The default contract is **one shot per semantic visual segment**. A second shot may be introduced only by a deterministic semantic or representation transition. Elapsed time alone must never multiply shot obligations.

### `media_library_assets`

Downloaded and validated media are reusable durable library entries keyed by provider identity with perceptual identity stored separately. Cache presence is never evidence of relevance: every use must still satisfy the current segment's truth-eligibility contract.

## Deterministic segmentation contract

Segmentation may use only persisted data available after WF03: ordered timed beats, narration punctuation/text, support evidence IDs, evidence metadata and canonical factual subject.

Boundaries are deterministic and topic-independent. They may be introduced by natural sentence/clause boundaries, evidence/support changes and the existing semantic editorial maximum.

There is no fixed mapping such as `60 seconds = 8 visual segments`.

### Quality-constrained semantic maximum

The unchanged video-level perceptual duration-share gate is `0.34`. Therefore a single one-shot semantic segment may not itself make that gate mathematically impossible.

For an accepted voice duration `T`, the segmenter uses:

`effective_max_segment_seconds = min(8.5, T * 0.34)`

The boundary is still chosen only on existing timed-beat boundaries; no timed beat is split merely to satisfy visual cadence. If one timed beat itself exceeds the effective cap, the visual stage fails closed rather than weakening `0.34`.

This is not the rejected `5 seconds = another asset` rule. For a `57.216 s` voice, `T * 0.34` is above `8.5`, so semantic structure remains the controlling limit. For the accepted `15.480 s` zipper voice, the quality cap is `5.2632 s`, preventing a single visual state from occupying more than the unchanged allowed share.

## Shot cadence

One semantic segment normally means one visual shot. Longer shots are allowed when the complete video still satisfies perceptual diversity. There is no hard 5-second shot-duration gate.

Asset-file uniqueness is also not a product-visible diversity gate. A non-adjacent asset may be reused when the current segment independently passes truth eligibility and the resulting video still passes perceptual-cluster occurrence, adjacency, duration-share and post-render state checks. Selection may penalize reuse, but file identity is not a substitute for perceptual identity.

## Sourcing and ranking

For every visual segment:

1. derive bounded search intents from canonical subject + combined narration + supporting evidence;
2. query/reuse Wikimedia, Pixabay and optional Pexels candidates plus the local media library;
3. apply exact/reference/stock truth eligibility before ranking;
4. rank only eligible candidates using local SigLIP;
5. reject invalid/missing perceptual hashes fail-closed;
6. select shots with video-level perceptual repetition control.

SigLIP remains a relative ranking tool, never a truth oracle.

## Quality gate

The gate proves product-visible properties rather than transport-beat or file cardinality:

- full gapless shot coverage of the accepted voice;
- every selected shot truth-eligible for its segment;
- no adjacent shots in the same perceptual cluster;
- a perceptual cluster may occur at most twice;
- one perceptual cluster may occupy at most `0.34` of total video duration;
- required unique perceptual state count is derived from the occurrence bound, not file IDs;
- missing/NaN/non-finite timing, score or hash data fails closed;
- WF05 independently revalidates the durable segment/shot timeline;
- post-render frame sampling independently verifies actual visual-state changes;
- human review remains mandatory for M8 acceptance.

Existing factual, one-Edge, duration and render-format gates are unchanged.

## Migration/compatibility

The change is additive:

- legacy scene visual columns remain for historical jobs and rollback compatibility;
- migration 015 adds `visual_segments`, `visual_shots` and `media_library_assets`;
- new jobs after deployment use segment/shot timeline;
- WF05 fails closed when new-mode segment/shot coverage is incomplete;
- historical accepted jobs are never rewritten merely to fit the new schema.

## Proven local evidence before production

The current local implementation has already proved:

- failed UK induction fixture: `57.216 s`, 18 timed beats -> 10 content-derived segments -> 10 shots; 9 perceptual clusters; adjacent 0; max occurrence 2; max share `0.245`; longest shot `7.278 s`;
- accepted zipper fixture: `15.480 s`, six timed beats -> five quality-constrained semantic segments; real-provider assignment gives five clusters, adjacent 0, max share `0.2958`;
- accepted EN induction fixture: `13.944 s`, six timed beats -> four segments/shots; four clusters, adjacent 0, max share `0.3374`;
- disposable `/render-v3` integration renders four `6 s` semantic shots successfully to H.264/yuv420p 1080x1920 + AAC 48 kHz stereo and independently observes four rendered states;
- focused/static WF04/WF05/media-worker regressions pass while exactly three production services remain running.

These are machine/dry-run proofs only. No semantic-v3 production migration/workflow publish/container replacement has occurred yet, and M8 remains `2/10` until a fresh deployed video is watched and accepted by the user.

## Regression requirements before production

Before deployment, additionally require:

- current implementation synchronized durably to GitHub;
- migration 015 validated and rollback snapshot captured;
- live WF04/WF05/media-worker equality after bounded deploy;
- fresh production RU-topic -> UK/60 job through `review_ready` with exactly one Edge synthesis;
- ffprobe + post-render perceptual gate;
- human-visible acceptance before M8 count changes.
