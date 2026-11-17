# Universal factory — active scene-grounding rework, 2026-11-17

Owner rejection: e4371771-bf21-4585-b195-fe7c77d23650 is a scene-irrelevant portrait slideshow and must not be accepted. General scene-to-media grounding is required; do not fix one video with handpicked assets.

Owner regression, 2026-11-16: Илон Маск / UK60 failed image selection at scene 24 (ae9b4750-4df5-4e1a-9ea0-7083625de950), with zero narration sends. Earlier six-case acceptance remains historical; general readiness is withdrawn until this regression and broader person selection are verified.

Read root AGENTS.md and factory_universal/README.md.

Current staged normal-pipeline test: `1674a10a-8e11-4cf3-989f-a727cceab68f` (paper / EN30), receipt `/data/factory-universal/qa/normal-stage-paper-20261117-v14.json`. This uses the normal quota/voice/alignment/render worker under its 900-second supervisor, while Studio remains on the previous release. Staged output is hidden from user/examples lists until actual frame review. Project readiness remains false. Latest code adds process-stage diversity, named model preservation, concrete-subject precedence and award-discipline checks. Do not replay existing receipts or submit another job while this test is active.

Latest WIP checkpoint: `acceptance/factory-universal/2026-11-17/scene-grounding-v12-checkpoint.json`. Runtime checks pass; image-only v12 is running. No new narration has been requested since the owner rejection, and Studio has not been redeployed. V10 produced 24 and 12 images but Musk failed assistant semantic review; the paper case hit its deadline. V11 was explicitly stopped after a diagnosed procedural-opening mismatch, then corrected and rechecked before v12. Do not describe these checkpoints as delivery.

2026-11-17 evidence: `acceptance/factory-universal/2026-11-17/scene-grounding-progress.json`. Image-only v8 passed counts for Curie and paper, but actual frame review rejected both; Musk exceeded its bounded image-only deadline. V9 adds organization/namesake discrimination, explicit paragraph-link precedence and procedural source preservation. Three previously wrong manufacturing images are rejected by the specific-operation pixel checks at the unchanged subject thresholds. New narration sends since the owner rejection: zero.

2026-11-17 work in progress: source-linked targets, award-object identity, photo genre screening, crop/resize deduplication and manufacturing stage matching are implemented. These are general rules, not handpicked topic assets. Runtime checks pass. Image-only v7 passed counts for Curie/paper but assistant review rejected unrelated award photos and manufacturing stages; these are not semantic acceptance. The v8 regression is image-only and does not send narration. Do not claim project readiness from these runs. Running Studio still uses the older release until a verified replacement is deployed.

Direct SSH alias `hodor-vps` works from the Mac. Always give local exec an existing working directory (for example `/`) and `/bin/sh`; the old supplied continuation workspace is absent. SentinelX availability is not a prerequisite for continuing server work. Do not expose SSH key contents or change shared services.

project_ready=false for the implemented automated source-grounded topic/language/duration-to-MP4 workflow. Six normal API outputs passed exact-frame/duration/hash checks, full decoding, fixed-voice validation and assistant inspection of every shot. This does not imply owner listening approval.

## Evidence

Authoritative receipt: acceptance/factory-universal/2026-11-16/acceptance.json . That receipt describes the previous six-case snapshot. The owner rejected e4371771-bf21-4585-b195-fe7c77d23650 despite its technical pass: identity-only photographs do not illustrate each scene. Source-linked general storyboard work is under verification and is not deployed. Studio is public at https://studio.hodor.com.pl/ ; actual unauthenticated checks returned page 200 and MP4 ranges 206.

| Topic | Language | Seconds | Frames | Job |
|---|---|---:|---:|---|
| Photosynthesis | en | 15 | 450 | 8cc37137-3cde-412b-9b77-f8d034c71eb5 |
| Warszawa | pl | 30 | 900 | 98d9b91e-7f56-4893-a181-f7e5c95a3232 |
| Марс | ru | 45 | 1350 | 5e57a397-1ee2-41ff-889a-4cab8699d515 |
| Бджоли | uk | 60 | 1800 | 40afaf97-73c4-4ec1-ab41-d13ecbe7e870 |
| How paper is made | en | 30 | 900 | 0165ea1e-96fd-45b0-b013-5b051ecaca88 |
| Зеленский | uk | 30 | 900 | c1ed6a0a-4a8d-433f-adfb-3e5ae30bf3eb |

## Provider and narration policy

Use exactly the four owner-selected voices in docs/PROVIDER_POLICY.md through the retained native Google gateway and PostgreSQL free-tier ledger. Google authorization was restored and actual synthesis passed. Do not ask the owner to reconnect again while health passes. Never expose or commit secrets. No Gemini, paid model API, audible eSpeak, voice substitution, tempo or pitch change.

Complete source sentences/blocks retain exact original spans. Native source facts replace unreadable Latin taxonomy in Cyrillic biological overviews. Duration correction keeps the preferred fact count stable and tries at most three distinct completed texts. Unknown provider outcomes stop without retries. A successful narration plan may reuse completed audio only while current entity, exact source spans, selected voice, duration and 24-hour cache remain valid; stale-source rejection was checked.

## Images and rendering

All 6/12/18/24 unique photos are checked before narration, at least two per beat. Preserve whole aspect ratios, full captions, author/license/source provenance and exact frames. Reject maps, SVG derivatives, diagrams, engravings, text documents, staged astronomical stock and downstream manufacturing uses. Named places require Commons category identity; proper-name details get their own bounded searches. License filters apply before the 50-result cap. Equal scene constraints share candidates; scarce images remain reserved for stricter future details.

The project-owned FFmpeg renderer preserves input voice audio and writes 1080x1920 H.264/AAC at 30 fps with exact requested duration. The shared media-worker remains unchanged and supplies ASR. Known tokenizer reconstruction errors can recover from existing Whisper JSON using the same 95% global / 85% scene coverage gates.

## Operation and bounds

Server checkout /opt/factory-universal; container factory-universal; branch codex/factory-universal-20261112. Use SentinelX host_58bbeb7da5059807, one short call at a time and finite background work. No subagents. Check active jobs before deployment or more operator tests.

One worker, 900-second process-group deadline, 2-GiB output cap including ASR/review artifacts, 512-MiB cache cap, 30-day retention, 2-GiB free-space reserve. Expired manifests are compacted; historical job/error IDs remain. Cleanup selects exact factory SQLite-owned UUIDs only. Never globally prune Docker/shared media or alter unrelated services.

Run checks.py, alignment_checks.py and renderer_checks.py inside the runtime. acceptance_outputs.py submits each recorded case once; review_outputs.py collects existing outputs and actual frames without sending narration. preflight_outputs.py is image-only and is never MP4 acceptance.

Inputs require an identifiable source and enough suitable licensed photos; clarify ambiguous topics instead of inventing facts or substituting unrelated media. Keep the owner-rejected Ходор-to-Hadar-star interpretation Q13175 in source_decisions until a different intended meaning is supplied.

## History

Earlier failed/rejected test IDs and plans remain under /data/factory-universal/qa/ and SQLite. Do not replay them or erase their failures. The dated 2026-11-15 checkpoint is historical; use the 2026-11-16 receipt above for delivery. Technical checks and assistant frame review never constitute owner/HUMAN listening approval.
