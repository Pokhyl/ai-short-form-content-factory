# V6 immutable failure — 2026-09-11

Job `557b2a2a-c382-4cfb-ab68-cfc259dafd67` (`Почему небо голубое?`, `ru`, `15s`) passed WF02 completely after the compound-purpose and `flows -> flow` storyboard boundary corrections. It persisted `storyboard-first-v1` and entered stage WF03 execution `18154`.

WF03 performed its single bounded duration-story rewrite through gateway execution `18156`, then failed closed with exact durable error `Voiceover duration 17.558s is still outside target after 1 bounded story rewrite [line 2]`. No WF04/WF05 render or MP4 exists for this job. The job is immutable and must not be resumed or repaired.

Before any next product job, inspect the exact initial/rewrite word budgets and measured natural-rate TTS durations from execution `18154`. Do not add retries, sleeps, timeout inflation, speech-rate manipulation, or arbitrary gate relaxation. Correct only a demonstrated duration-controller/model-contract defect, then use a completely new job.
