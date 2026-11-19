# Current regression — 2026-11-19

project_ready=false pending correction of failed user job acfbd2ea-ee67-4115-9ed1-05e6624c7bb2 (Владимир зеленский / UK45). Its planning trace misclassified Ukrainian office appointment «посаду» as vehicle landing; public roles, elections and entertainment organizations also lacked appropriate event contexts. Typed person/event verification is staged, not deployed. Preserve the failed ID. Verify the actual normal pipeline and frames before claiming readiness. The 2026-11-18 evidence below is historical and does not establish general readiness.

Normal stage v2: 9914a9b0-5b2a-4649-9b90-1148c2980188 failed before synthesis (0 native attempts); db684e42-ce42-4bad-8742-7098326956a1 assembled EN30 with 900 frames and the selected voice, but assistant review rejected unrelated anthropology-museum shots. Do not promote it. Real image controls identified and repaired missing civic photo/human descriptions without lowering thresholds; all four negative controls remain rejected. Runtime checks pass, and cached/full scores are exactly equivalent on four new images. Stage v5 was stopped before synthesis (0 native attempts) after exposing an encoder batch overflow when adding a sourced human description. Person and genre comparisons now preserve all positive/negative descriptions in bounded batches; regression tests cover this case. Stage v7 is running the actual UK45 request (d845a00c-9a99-494e-80ea-077f0d0a513a) and an EN30 biography (89c38472-7992-466f-8229-240b8ec8c928), with abstract fields excluded as physical scene subjects. These changes remain staged, not deployed. Evidence is under acceptance/factory-universal/2026-11-19/.

# Historical release evidence — 2026-11-18

The previous release is deployed at https://studio.hodor.com.pl/ without a password. Its successful examples are historical evidence, not a current general readiness claim. Read root AGENTS.md and factory_universal/README.md. No subagents.

Authoritative evidence: acceptance/factory-universal/2026-11-18/acceptance.json. Five normal pipeline outputs passed exact frame/duration checks, full decoding, selected native voice validation, source/media provenance and assistant review of every shot (72 photographs):

| Topic | Language | Seconds | Frames | Job |
|---|---|---:|---:|---|
| Paper manufacturing | EN | 30 | 900 | 15c51e44-8246-46a9-b160-cfb9675ce595 |
| Photosynthesis | EN | 15 | 450 | 3223bb8a-434c-418c-8c94-18b367008fbd |
| Maria Skłodowska-Curie | PL | 30 | 900 | 607c6d93-e831-4f09-b6cc-75f14523bf70 |
| Mars | RU | 45 | 1350 | 18df5cd7-279f-4fb2-ab57-44b65940e62e |
| Musk | UK | 60 | 1800 | 1df244b9-31a1-4bfe-8cfd-afa66e3d8afa |

A further real public POST /api/jobs returned 202 and completed as ready: 7eae7dea-a01c-41de-9851-c5063acd3628. Its entire MP4 is bit-identical to the reviewed final Musk output. Unauthenticated page/health returned 200, five example videos returned Range 206, and all credits downloads returned 200. The deployed image implementation hashes match the staged release. Owner listening/approval remains pending; technical and assistant visual review do not represent it.

## Active implementation

Server checkout /opt/factory-universal, service/container factory-universal, delivery branch codex/factory-universal-20261112. Implementation commit 1649388963962a85f91ba259525cc914f4176829; later delivery commits update documentation/evidence only. Use direct SSH alias hodor-vps; Sentinel availability is not required. Long finite checks should run detached with durable logs because SSH can reset. Leave unrelated services, workflows, files and credentials unchanged.

Source-linked biography objects, primary-topic context elsewhere, manufacturing operation metadata, city exteriors, award discipline, photographic genre screening and crop deduplication apply generally; there are no handpicked topic assets. Natural duration planning compares complete fact counts, calibrates once from completed native measurements, prevents repeated physical stages and preserves causal production order. Every image is checked before synthesis. Unsupported or ambiguous inputs request context rather than inventing facts or substituting unrelated assets. Preserve the owner-rejected Hodor-to-Hadar interpretation Q13175 until different context is supplied.

The pinned CLIP model uses bounded caches of 256 image vectors and 128 unchanged complete text batches. Six real-image tests found exactly identical scores versus full encoder execution. Evidence: visual-cache-equivalence.json beside acceptance.json. New-image comparisons with cached descriptions took roughly .5-.9 seconds versus about 4.5 seconds; repeated inputs .03-.33 seconds. Model checksum and quality thresholds are unchanged.

## Provider, output and storage bounds

Use retained Google native credentials and PostgreSQL free-tier ledger. Exactly: en-US-Chirp3-HD-Algenib, pl-PL-Chirp3-HD-Enceladus, ru-RU-Wavenet-D, uk-UA-Chirp3-HD-Enceladus. No Gemini, paid model API, audible eSpeak, voice substitution, speed/pitch change, filler or blind synthesis resend. Maximum three distinct completed narration texts. Respect 429; image GET 503 allows only two delayed retries.

Preserve subject CLIP .24/.015, ASR .95 global/.85 per scene; 6/12/18/24 unique whole photographs, at least two per beat; 1080x1920 H.264/AAC, 30 fps, exact 450/900/1350/1800 frames and full decode. Compatible Commons images retain authorship, original license and change notices. New adaptations use CC BY-SA 4.0 with attribution embedded in MP4, credits.txt/credits.json and the credits API. NC/ND/unknown licenses remain excluded.

One worker, 900-second process-group deadline; 2-GiB owned outputs including ASR/reviews, 512-MiB cache, 30-day retention and 2-GiB free-space reserve. Verified storage: about 223 MB outputs, 31 MB cache and 5.87 GB free. Cleanup selects exact SQLite-owned UUID directories only. No global Docker prune or unrelated-file deletion. A bounded 174-KB rollback source archive is retained under /data/factory-universal/rollback-app-20261118.tar because the old container's base image metadata/content had previously been removed.

## Maintaining the release

Run checks.py in the runtime for relevant changes; alignment_checks.py/renderer_checks.py when their behavior changes. visual_cache_checks.py verifies cached/full encoder equivalence on supplied local real images. stage_outputs.py runs the normal worker under its existing deadline while keeping outputs hidden; preflight_outputs.py is image-only and is not MP4 acceptance. Never replay receipts or failed job IDs. Check live jobs before creating more work or recreating app. review_outputs.py collects existing MP4 midpoint frames without synthesis; inspect actual frames before promoting examples.

Only the five reviewed examples were promoted. Historical tests are retained outside the current Examples view. Keep owner-rejected e4371771-bf21-4585-b195-fe7c77d23650 changes_requested. Previous acceptance snapshots and failed iterations are historical evidence, not the current release. Do not auto-approve owner listening or reuse old rejected outputs as successes.

Publish meaningful source/evidence changes, verify the checkout against the delivery branch, and deploy only app with --no-deps. After deployment check image/implementation hashes, unauthenticated public routes, credits and an actual public create-to-ready flow. Credentials remain on the retained server; never print or commit them.
