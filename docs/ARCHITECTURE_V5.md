# Architecture V5 — deployed reality and correction

Verified against GitHub `b909a25`, n8n PostgreSQL workflow definitions and the
running media-worker on 2026-09-06. See
[V5_SYSTEM_AUDIT_20260906.md](V5_SYSTEM_AUDIT_20260906.md) for evidence and unfinished work.

## Current inventory-first path (2026-09-07)

Production n8n is **2.37.10**. Do not downgrade based on the historical snapshot
below. WF01 accepts only topic/language/duration. WF02 resolves/researches the topic,
discovers and verifies licensed visual inventory before final narration, and
persists a story package binding claim, research evidence, narration unit and
reserved asset. WF03 produces one natural Edge voiceover and uses native word
boundaries; bounded text rewrites preserve the story assets and do not alter speech
rate. WF04 downloads and verifies the reserved assets without late discovery or
rebind. WF05 executes variable semantic units in a full-image 9:16 composition and
persists the final MP4 SHA256. The same existing workflows remain the product.

The next verified WF02 correction treats proposed claim/visual targets as research
hypotheses. Image review observes actual content and identifies a supported fact
from the supplied evidence before freezing the final claim/asset pair. Selection
checks evidence ID scope, metadata consistency and perceptual uniqueness. This
avoids treating imagined camera arrangements as immutable image requirements.
It does not authorize generic thematic images or facts about invisible mechanisms.
See CURRENT_STATE_V5.md for the exact deployment status, last job and next step.

These are implementation facts, not quality acceptance. No new successful MP4 has
yet been demonstrated in this continuation; final output still requires HUMAN PASS.

## Historical pre-inventory product path (superseded)

`topic + language + duration -> WF01 job intake -> WF02 research/script -> WF03
continuous TTS and bounded script-duration rewrites -> WF04 late visual discovery,
review and assignment -> WF05 FFmpeg render -> WF06 review API`

- n8n 2.33.3 orchestrates the path, and PostgreSQL persists product state.
- WF02 resolves topic candidates using SearXNG evidence, writes narration and
  fixed-count visual queries, then stores it before visual inventory is known.
- WF03 tries Gemini TTS and Edge fallback at natural rate. Total audio duration is
  measured, but internal beat boundaries are estimated from token weights.
- WF04 searches Wikimedia/Pexels Photos/Pixabay. Metadata gates, native preview
  hashes and hosted multimodal review feed bounded recovery and unique assignment.
- The model gateway tries hosted Kilo free vision/text then Gemini. There is no
  deployed local model worker in this path.
- WF05 calls media-worker's custom FFmpeg `/render-v3`, which makes static central
  crops for ordinary stills, separate subtitle beats, H.264/AAC 1080x1920 output,
  and technical/diversity checks.
- `review_ready` means machine completion only. Human acceptance is separate.

## Identified architecture defects

The current ordering commits to narration before checking what can truthfully be
shown. Fixed beat counts and synthetic timing create phrase fragments and excessive
visual obligations. Automatic evidence IDs and image-review booleans are not
proof of semantic support. Source-image approval does not verify the final crop.
These defects explain both false machine approvals and repeated fail-closed jobs.

## Historical correction plan (inventory-first is now deployed)

Retain existing orchestration, provider adapters, continuous natural voice,
persistence, encoding and human acceptance. Move discovery and verified unique
visual-story selection before script freeze. Author complete semantic units with
explicit claim/evidence/asset relationships. Derive editing boundaries from the
exact accepted voiceover; preserve asset support through bounded script rewrites.
Then execute and inspect the planned composition instead of searching for creative
rescues after voice freeze.

No arbitrary workflow/service count or new architecture version is prescribed.
No repeated visual, topic-specific recovery, manipulated speech rate, or machine
promotion to HUMAN PASS is permitted.

The additive Edge native word-timing capture is tested independently before WF03
adopts it. Until that adoption is complete, the deployed timing remains synthetic.

## Historical upstream proposal

The earlier version of this document proposed OpenNolan commit
`4457349c386ea1a89c01547f9a76fa650970c131`, faster-whisper and an asset-first editor.
That is historical design intent, not evidence of an active engine. The current
worker does not call those tools; the documented V5 Python environment is absent
on the VPS. Consult Git history for the original proposal. Choose further tooling
only after testing a concrete need; do not revive it merely because it was pinned.
