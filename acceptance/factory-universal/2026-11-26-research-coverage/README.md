# Research coverage candidate

The candidate preserves explicit manufacturing terms while translating the object and its qualifiers for research. A runtime translation probe reproduced the old «Work on yachting» query for «работа на производстве яхт». The new query retained the manufacturing subject. It also uses the existing SearXNG service to discover English Wikipedia candidates when direct Wikipedia discovery cannot produce a verified translated plan. Search snippets do not enter the script. English source excerpts must come from a pinned revision and cover the requested scope.

In a Ukrainian glass-manufacturing probe the old native resolver picked Berdychiv, a city, and planned three beats. The follow-up rejects an unrelated place as the primary manufacturing source. Runtime fixtures cover that input class, a municipal qualifier with different spelling in English, and the selection and provenance of supplementary Commons files.

The candidate also checks files from the source revision and the Wikidata-linked Commons category when the initial photo pool cannot cover a storyboard. A live category probe found 45 files that passed the provider and licensing metadata filter in the Boat-building category. That count makes no claim about the files passing scene or image checks.

| Staged case | Observed result |
| --- | --- |
| «работа на производстве яхт», UK45, `c244b52c-83de-4ee0-9a29-63de2ece897a` | Stopped at source research. Zero synthesis attempts. |
| «n8n автоматизация для фирм», UK45, `b36a1302-3360-4cf6-9a1b-70ef6e31a461` | Exhausted scripts with licensed scene-matched imagery. Zero synthesis attempts. |
| «Warszawa», PL15, `e69a981c-8d21-4322-8a60-b8464818ad7a` | Ready with 450 frames and six distinct city photographs. |
| «How paper is made», EN30, `e8fc0ba7-41ad-49fb-b62e-86fc8495d2f5` | Alignment timed out during high host memory pressure. |
| «Марс», RU45, `322d3801-6d32-465f-a3c9-c673fdbdfb5f` | Ready with 1,350 frames and eighteen distinct photographs. |
| «Вулкан», UK60, `86114253-b976-42dc-9bb0-e0361c9d4ebb` | Ready with 1,800 frames and twenty-four distinct photographs. |
| «How paper is made», EN30, `90c75d0b-990f-4eed-b90b-202ff3c75406` | Fresh retry on the final candidate reached ready with 900 frames and twelve distinct photographs. |
| «Виробництво скла», UK30, `78708b48-be42-4e46-9df5-3b43fcb363fd` | Final candidate rejected the unrelated place and stopped at research. Zero synthesis attempts. |

During the alignment timeout, SSH and Studio stopped answering. Sentinel reported high system load and sustained memory pressure. Studio recovered and the concurrent research-only probe was stopped. The final app releases the CLIP session after the photos and narration are settled, before the separate speech alignment worker loads its model. In the runtime memory probe, resident memory was 60,756 KiB before loading CLIP, 291,220 KiB after loading, and 76,896 KiB after release. The retry verifies the complete pipeline with the memory change. The concurrent probe was also absent during the retry.

All 60 shot midpoints and their captions were inspected on review sheets. The paper scenes show machinery, screens, presses and drying, with some equipment shown at rest. Mars brightness, year length and pressure are illustrated by contextual planet views. The volcano shots show volcanic landforms and eruptions. Several surface views give limited evidence for the specific underground structures described, and two views show a similar setting. Technical checks and midpoint review leave owner listening approval pending.

Studio deployed `9e74418` after the queue was empty. Runtime, alignment and real FFmpeg suites passed in the built image. Eight application file hashes matched the server checkout. A transient 502 during the app restart cleared and the public health check returned 200.

Chrome replayed the four staged MP4s through the public service after deployment. It checked portrait playback, exact durations, byte ranges, author credits and the configured native voices in the manifests. The playback recordings were muted.

The public Chrome form then submitted a fresh PL15 «Warszawa» as job `c8691ed0-746e-4b35-a57c-d9e966d2315e`. It reached ready and the browser played it at 1080 × 1920 for exactly 15 seconds. Its 450-frame MP4 has the same SHA-256 as the inspected staged Warsaw file.
