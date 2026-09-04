# V4 availability-blind visual planning failure — 2026-09-04

## Fresh cross-topic evidence

Replacement-architecture smoke topic:

`как работает автомобильный турбокомпрессор / ru / 15`

Job:

`815731bf-a953-4590-92f8-6bfb25165b38`

The multi-asset sequence experiment stopped using one still per visual unit, but the job failed during actual provider discovery:

`no provider media for V4: car engine explosion diagram`

The sequence planner had invented a desired exact-media query before it knew what the available free provider inventory actually contained.

## Root cause

Planning first and discovering media afterward is availability-blind. Even a semantically reasonable visual plan can be impossible to materialize from the free licensed provider set.

This failure is architectural, not turbocharger-specific. It can affect any person, mechanism, history or comparison topic.

## Decision

Do not repair this by changing the turbocharger query or adding a fallback search term.

The V4 sequence experiment is rejected. V5 changes the order more fundamentally: real visual inventory is discovered before the final story angle and script are frozen.

For V5 this means:

`topic -> research -> actual licensed visual inventory -> showable story angle -> final script -> voice/alignment -> concrete edit`

This is not a generic-stock fallback. If available inventory cannot support a truthful visual story, the story angle must change before script freeze or the job must fail closed.
