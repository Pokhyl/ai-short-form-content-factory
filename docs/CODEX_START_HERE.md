# Universal factory — staged verification, 2026-11-18

Read root AGENTS.md and factory_universal/README.md. Active repo: /opt/factory-universal; branch codex/factory-universal-20261112. Public Studio https://studio.hodor.com.pl/ still runs the older release. project_ready=false until final normal outputs are reviewed and the replacement is deployed and checked. No subagents.

## Current verification

Normal matrix /data/factory-universal/qa/normal-stage-universal-20261118-v31.json is running. Never replay it or its immutable -plan.json. Paper EN30 job 15c51e44-8246-46a9-b160-cfb9675ce595 is technically ready and passes assistant review of all 12 actual MP4 shots: actual papermaking, mesh tools, presses and drying; no edible paper, scanned pages or unrelated factory images. Selected EN voice: 27,048 ms, two distinct completed texts, alignment .992084, exactly 900 frames. Review receipt: normal-stage-v31-paper-review.json. Other matrix cases are photosynthesis EN15, Curie PL30, Mars RU45, Musk UK60.

The v28 matrix completed four technical MP4 passes but failed paper duration after three texts. Actual v28 Curie and Mars frames now pass topic/context review. V26 photosynthesis frames pass (plants, algae, demonstrations; no diagrams). V28 Musk was rejected: a landing-leg display in headquarters appeared under rocket landing. The staged v32 fix rejects indoor component displays and headquarters for landing events; this needs a fresh normal Musk run after the current matrix ends. No listening or owner approval is implied by any assistant frame review.

## Latest source

V31 duration control compares complete source plans across fact counts, targets natural duration, calibrates once from this job's measured native recordings, prevents repeated physical stages hidden inside source blocks, and orders physical stages causally. Runtime checks pass. Do not change speed/pitch, append filler or repeat native synthesis after ambiguous outcomes. Maximum three distinct completed texts.

V32 also caches CLIP image vectors (256) and unchanged full text batches (128), bounded in memory. On six saved real images, cached scores exactly match full encoder execution (maximum error 0.0). The benchmark is /data/factory-universal/qa/visual-cache-equivalence-20261118-v32.json; runtime checks pass. New-image comparisons with cached descriptions took about .5-.9 seconds instead of about 4.5 seconds; repeated inputs about .03-.33 seconds. Pinned model and thresholds are unchanged. visual_cache_checks.py reproduces the equivalence check on local real images without provider calls.

Other general rules: source-linked objects for biographies, primary subject retention elsewhere, physical operation metadata, city exteriors rather than arbitrary city objects/interiors, actual award discipline, photographic genre checks and crop deduplication. No handpicked topic assets. NC/ND/unknown media remain excluded. Compatible Commons media, including BY-SA 3/4, retain author/source/license/change notices; output CC BY-SA 4.0 attribution is embedded in MP4 plus credits.txt/credits.json and a credits API. No paid model API or Gemini.

## Delivery steps still required

Follow v31 through completion and inspect actual final frames. After no active jobs, run the normal staged pipeline for Musk against v32 to verify the landing fix and cached verifier; do not reuse a failed ID. Keep staged_test outputs hidden until reviewed. Only after successful review recreate app with --no-deps. Verify public unauthenticated page/health, video Range 206, credits endpoint, actual image/implementation hashes and source tree. Publish source/evidence changes and align the delivery branch without force push. Unit checks alone are not delivery.

## Operation and bounds

Direct SSH alias hodor-vps works from the Mac; use local / and /bin/sh because the supplied Mac continuation path is absent. Long finite jobs run detached with logs so SSH resets do not interrupt them. Sentinel availability is not required. Never expose credentials or modify shared services.

Exact voices: en-US-Chirp3-HD-Algenib, pl-PL-Chirp3-HD-Enceladus, ru-RU-Wavenet-D, uk-UA-Chirp3-HD-Enceladus. Retained native Google gateway and PostgreSQL free-tier ledger only. No audible eSpeak, substituted voices, speed/pitch adjustments or blind provider resends. Respect 429. Image GET 503 allows only two delayed retries.

Preserve subject CLIP .24/.015, ASR .95 global/.85 per scene; 6/12/18/24 unique whole photos, minimum two per beat; 1080x1920 H.264/AAC, 30 fps and exact 450/900/1350/1800 frames, full decode. Inputs require an identifiable source and enough suitable licensed images. The owner-rejected Hodor-to-Hadar interpretation Q13175 stays blocked pending context.

One worker, 900-second deadline, 2-GiB outputs including ASR/reviews, 512-MiB cache, 30-day retention, 2-GiB disk reserve. Cleanup only exact SQLite-owned UUID directories. No global Docker prune or unrelated-file deletion. Retain historical failure IDs and evidence. Owner-rejected e4371771-bf21-4585-b195-fe7c77d23650 remains changes_requested. Older acceptance snapshots do not establish readiness.
