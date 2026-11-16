# Universal factory — active checkpoint

Read root AGENTS.md and factory_universal/README.md. The active app is factory_universal, deployed from /opt/factory-universal at https://studio.hodor.com.pl/ .

project_ready=false until the complete six-case MP4 matrix and actual output frames pass. Never infer completion from unit checks, preflights or a ready status alone.

## Access and providers

Studio is password-free. Actual unauthenticated page/API requests return 200 and MP4 ranges return 206. Invalid requests return 400 without creating jobs.

The owner restored the retained Google connection. Actual synthesis succeeds with the four fixed voices. Do not ask for another login while health passes; do not request new API keys. No Gemini, paid model API, audible eSpeak, voice substitution or speed/pitch change.

## Verified normal API outputs

- Photosynthesis EN15: 8cc37137-3cde-412b-9b77-f8d034c71eb5, 450 frames; actual frames reviewed.
- Mars RU45: 5e57a397-1ee2-41ff-889a-4cab8699d515, 1350 frames; actual frames reviewed. ESA Phobos-over-Mars photographs were checked against their source descriptions: these are real single shots, not staged astronaut stock.
- Bees UK60: 40afaf97-73c4-4ec1-ab41-d13ecbe7e870, ready; actual-frame review remains required.
- Named person UK30: c1ed6a0a-4a8d-433f-adfb-3e5ae30bf3eb, 900 frames; actual frames reviewed. Photographs illustrate the person and do not claim the exact narrated historical date.

Listening approval remains pending; assistant checks are never owner/HUMAN approval.

## Current acceptance work

The authoritative in-progress plan is /data/factory-universal/qa/factory-acceptance-20261115-v6.json. Its batch follows only existing IDs and never replays failed synthesis. PL30 replaces an image-review failure (a map among photographs). Manufacturing EN30 checks improved photographic production prompts while keeping .24 positive/.015 margin gates.

Retain all prior plans/failed IDs. The original failed Google test f632a0cf-b09b-4bd7-a553-d7c9e695900a, legacy-render failure db43f2c5-9c6f-480a-a97f-823b7da002f3 and later diagnosed cases remain historical evidence. Completed identical audio may be reused; uncertain sends must not repeat.

## Implementation

Primary-source identity binding and complete source spans drive native narration. Human identity uses Commons depicts/category metadata and a separate content gate. Named places require Commons category provenance; named details get distinct bounded queries. Named astronomical bodies require institutional provenance. Reject maps, diagrams, woodcuts, staged space imagery, downstream manufacturing uses and derivative duplicates.

All photographs are verified before narration. Use 6/12/18/24 distinct images, at least two per beat, whole aspect ratios, complete captions and provenance.

The project-owned FFmpeg renderer preserves input narration and writes exact requested frames. The shared media-worker remains unchanged and supplies ASR alignment. A known shared tokenizer error may recover from its already-produced Whisper JSON using project lexical normalization with the same 95% global and 85% per-scene coverage gates.

Cyrillic biological overviews prefer complete native source facts over Latin taxonomy. Natural duration corrections search different complete texts before any send. Three completed text attempts maximum; no uncertain retries.

## Storage and verification

One worker, a 900-second process-group deadline, a 2-GiB output cap including ASR and review artifacts, a 512-MiB audio/JSON cache cap, 30-day retention and a 2-GiB free-space reserve. Expired manifests are compacted; job/error IDs remain. Cleanup selects only exact factory SQLite-owned UUIDs. Never prune unrelated Docker/shared media or alter unrelated services.

Run checks.py, alignment_checks.py and renderer_checks.py inside the runtime. preflight_outputs.py creates bounded image-only tests without narration. acceptance_outputs.py submits each recorded case once; review_outputs.py collects actual frames and audits without creating jobs.

## Continuity

Delivery branch: codex/factory-universal-20261112. Published checkpoint before these pending refinements: 5fdf30bfe4a10af87b24a46bead9fe16740c0d28. Publish meaningful code and sanitized acceptance evidence, verify checkout and deployed source, and leave no false ready claim.

Use SentinelX host_58bbeb7da5059807, one short call at a time, and finite background work. Mac local execution was unavailable. No subagents. Keep the rejected Ходор to Hadar-star interpretation Q13175 in source_decisions; no new intended meaning has been supplied.
