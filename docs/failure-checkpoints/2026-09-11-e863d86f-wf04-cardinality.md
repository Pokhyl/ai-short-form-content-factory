# V6 immutable failure checkpoint — 2026-09-11

Job: `e863d86f-faf8-43b3-aec8-7f688a4843ae`
Topic: `Почему небо голубое?`
Language: `ru`
Target duration: `15s`

The fresh V6 job passed WF02 and the corrected WF03 duration-rewrite path. WF03 persisted a natural voiceover duration of `16.270s`. Stage WF04 execution `18120` then failed closed with:

`Reserved visual persistence cardinality 1/4 [line 1]`

The job is terminal `failed|visuals` and is immutable. Do not resume or repair it. Inspect exact reserved-visual persistence state and WF04 persistence logic before changing code. Do not weaken the cardinality gate and do not manually supply/select assets.
