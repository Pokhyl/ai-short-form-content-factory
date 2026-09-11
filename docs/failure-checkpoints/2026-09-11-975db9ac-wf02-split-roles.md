# V6 WF02 split-role boundary failure — 2026-09-11

Fresh immutable stage job `975db9ac-f6ce-4733-a248-5727f78c0cfa` (`Почему небо голубое?`, `ru`, `15`) completed WF01 and all three WF02 model-gateway calls, then failed in WF02 validation with `diagram shot S2A split roles are invalid [line 7]`. The previously fixed `purpose` and `flows -> flow` boundary defects did not recur. The job is immutable and must not be resumed or repaired in place.

This is another model-boundary structural variation in diagram output. Do not add a topic-specific exception or weaken the diagram gate. Inspect the exact S2A diagram output and existing canonicalization/diagram compiler rules, then make one general, fail-closed diagram canonicalization correction with regression coverage before creating a new job.
