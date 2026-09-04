# V5 evidence-grounded topic resolution — 2026-09-04

## Production failure

Fresh autonomous job `16c23aed-4370-46a4-b135-63f8b6af47c6` received `Ходор / ru / 30` and reached machine `review_ready`, but resolved the subject as `Mikhail Khodorkovsky`. This is HUMAN FAIL.

Persisted production evidence proves the failure was upstream of research: every selected SearXNG result already concerned Khodorkovsky, and the grounded writer faithfully narrated that wrong subject.

## General root cause

WF02 previously asked one model call to emit one canonical subject before any search. It generated neither competing interpretations nor evidence for the decision. Research then used only that unverified guess, creating a self-confirming loop. The node name `semantic intent` did not match its actual contract.

## Systemic correction

WF02 now performs the following n8n-orchestrated sequence before factual research:

`raw topic -> 1-5 distinct interpretations -> per-candidate SearXNG discovery -> evidence comparison -> structured resolved topic -> factual research for resolved subject`

The durable `jobs.topic_resolution` JSON records raw topic, candidate inventory, discovery evidence, selected and runner-up candidate IDs, resolved subject/type/context, confidence, score margin, reasoning evidence IDs, and resolution reason. Migration `018_evidence_grounded_topic_resolution.sql` enforces the core stored contract.

No topic-specific alias, blacklist, query, threshold, or retry was added. Output language remains independent of topic language. WF03 continuous TTS and measured-duration rewrite, WF04 photo-first sourcing, and WF05 render/QA are unchanged.

## Regression contract

`tests/wf02_topic_resolution_regression.mjs` checks the workflow topology, absence of topic-specific production literals, structured persistence, Code-node compilation, and seven unrelated resolution classes:

- ambiguous fictional/person name;
- cross-language scientific question;
- cross-language technical question;
- cross-language factual question;
- ambiguous short word;
- ordinary medical question;
- known company/object ambiguity.

Machine regression success is not HUMAN PASS. A fresh deployed n8n job and exact MP4 review remain required.

The first post-deploy job stopped safely before TTS because the new per-candidate HTTP node still referenced the old final-research field name (`search_query_en`) instead of `discovery_query`; SearXNG returned `400 No query`. The same execution exposed an older failure-recording mismatch (`error_message` was produced while SQL read `last_error`). Both are general wiring-contract defects. They were corrected and covered by regression assertions; the consumed failed job is not retried.
