# Visual Segmentation Architecture

Last updated: 2026-09-03

This document defines the replacement for the rejected `one timed beat -> one independently sourced visual` model.

## Decision

`timed beats` and `visual scenes` are different product concepts and must remain different durable entities.

Timed beats exist to cover the accepted one-shot Edge voice track exactly and to drive subtitle timing. They are transport/timing units, not a requirement to perform an independent media search for every short phrase.

Visual sourcing operates on deterministic semantic `visual_segments` built from adjacent timed beats and their persisted evidence provenance.

The production path becomes:

`accepted voice -> timed beats -> deterministic semantic visual segments -> 1..N visual shots per segment -> truth eligibility -> local SigLIP ranking -> perceptual duplicate control -> render timeline -> post-render frame gate -> human review`

No generative model is added to visual planning.

## Why the previous model is rejected

Fresh production job `4372be34-c417-415f-92f6-63481b3b5686` produced 18 timed beats for a measured 57.216 second Ukrainian voice track and then failed WF04 with `perceptually unique truth-eligible assignment 11/12`.

The failure exposed an architectural mismatch: transport beats created for exact voice/subtitle timing were being treated as 18 independent semantic media-search obligations. Long videos therefore required many near-unique assets for micro-fragments of one continuous explanation.

This is not solved by weakening the existing diversity threshold. The source unit for media search is changed instead.

## Durable entities

### `scenes`

Existing `scenes` remain timed narration/subtitle beats.

They continue to own:

- sequential beat number;
- narration fragment;
- exact start/end/duration covering the accepted voice;
- narration/evidence provenance.

They no longer own the requirement that every beat have its own independently selected media asset.

### `visual_segments`

A visual segment is a contiguous semantic interval covering one or more adjacent timed beats.

Required durable fields:

- `job_id`;
- sequential `segment_number`;
- `start_seconds`, `end_seconds`, `duration_seconds`;
- first/last covered beat numbers;
- combined narration text;
- union of supporting evidence IDs;
- canonical subject / visual target;
- lane (`exact`, `reference`, `stock`);
- sourcing status and timestamps.

Visual segments must cover the entire accepted voice timeline without gaps or overlaps.

### `visual_shots`

A visual segment contains one or more ordered shots.

Each shot owns:

- exact segment-relative/global start/end;
- selected durable media-library asset;
- local rank / selection metadata;
- perceptual cluster identity;
- selected representation kind.

Shots, not timed beats, define the video image timeline consumed by render.

### `media_library_assets`

Downloaded and validated media are reusable durable library entries keyed by provider identity and perceptual hash.

The library stores provider/source/license metadata, media kind, local path, perceptual hash, and normalized metadata used for future eligibility/ranking. Reuse must still pass the current segment's truth-eligibility checks; cache presence is never evidence of relevance.

## Deterministic segmentation contract

Segmentation may use only persisted data already available after WF03:

- ordered timed beats;
- narration punctuation/text;
- narration support evidence IDs;
- evidence source/title/text metadata;
- canonical factual subject.

Boundaries are deterministic and topic-independent. They may be introduced by:

1. natural completed sentence/clause boundaries;
2. evidence/support-signature changes when the preceding interval is already editorially usable;
3. a maximum continuous visual interval so one static visual cannot dominate a long explanation.

Short adjacent fragments are merged rather than creating independent search requests merely because WF03 split the audio there.

There is no fixed rule such as `60 seconds = 8 visual segments`. Segment count is derived from the actual narration/evidence structure.

## Shot cadence

A segment may use one or more shots. A longer segment can be represented by multiple different truth-eligible assets without inventing additional semantic scenes.

Shot boundaries must remain deterministic and fill the segment exactly.

Quality is enforced at shot/timeline level rather than by demanding an almost-unique asset for every subtitle beat.

## Sourcing and ranking

For every visual segment:

1. derive bounded search intents from canonical subject + combined narration + supporting evidence;
2. query/reuse Wikimedia, Pixabay and optional Pexels candidates plus the local media library;
3. apply exact/reference/stock truth eligibility before ranking;
4. rank only eligible candidates using local SigLIP;
5. reject invalid/missing perceptual hashes fail-closed;
6. select shot assets with adjacent perceptual duplicate prevention and video-level repetition control.

SigLIP remains a relative ranking tool, never a truth oracle.

## Quality gate

The replacement gate must prove product-visible properties, not transport-beat cardinality:

- every visual segment is fully covered by selected shots;
- every selected shot was truth-eligible for its visual segment;
- no adjacent shots share the same perceptual cluster;
- no single shot may remain on screen beyond the validated editorial maximum;
- repeated visual clusters are bounded across the whole video;
- no one visual cluster may dominate total video duration;
- missing/NaN/non-finite timing, score or hash data fails closed;
- WF05 independently revalidates the durable shot timeline;
- post-render frame sampling independently verifies actual visual-state changes;
- human review remains mandatory for M8 acceptance.

Existing factual, one-Edge, duration, render-format and human-review gates are not weakened.

## Migration/compatibility

The change is additive first:

- keep legacy scene visual columns for historical jobs and rollback compatibility;
- add new visual-segment / shot / media-library tables;
- new jobs after deployment use the segment/shot timeline;
- WF05 supports the new timeline and must fail closed if a new-mode job has incomplete segment/shot coverage;
- old accepted jobs remain readable and are never rewritten merely to fit the new schema.

## Regression requirements before production

Before deployment, prove at minimum:

- 15/30/45/60 second fixtures create gapless visual segments from timed beats;
- segment count is content-derived, not fixed by duration;
- the 57.216 s failed UK induction fixture no longer creates 18 independent visual-search obligations;
- cross-topic EN/PL/RU/UK segmentation passes;
- all visual segments get truth-eligible candidate pools or fail closed;
- shot timeline is gapless and exactly equals accepted voice duration;
- no adjacent perceptual duplicates;
- video-level repetition limits pass without lowering existing factual gates;
- WF05 render + ffprobe + post-render visual-state tests pass;
- exactly three persistent services remain;
- no new hosted/quota/paid dependency is introduced.
