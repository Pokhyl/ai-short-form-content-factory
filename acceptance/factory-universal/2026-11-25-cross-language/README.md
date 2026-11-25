# Local cross-language research

The optional images mount two checksum-pinned local translation models. Ukrainian briefs can be searched in English. An English Wikipedia article must cover the translated search terms at its pinned revision, and the resulting narration must cover the original brief. The translation links each retained passage to the original source span and revision. Model configuration, pinned downloads and runtime checks were verified on the staging host.

The first normal pipeline run used real source data. The checked-out app remained live on the preceding image.

| Request | Stage | Evidence |
| --- | --- | --- |
| Work in yacht manufacturing in Gdańsk, UK30 | Research stopped | `5eab1eed-86d5-42cb-b2bf-791a7ff2d34e`. The query translation retained Gdańsk. The research worker did not find an adequate article. No synthesis. |
| n8n business automation, UK45 | Visuals stopped | `f2fd1dda-ffa4-4fa2-a299-b32297e5518f`. Produced a Ukrainian draft from English revision 1387378004 and found too few suitable photographs. No synthesis. |
| Laser cutting of metal, UK15 | Voice stopped | `69f02768-8504-4e26-846b-9713a78b3dae`. The native source route found images. All three selected native recordings were outside the 13.5–15 second window. |
| How paper is made, EN30 | Rendered | `f333535b-3f96-49bb-9dad-13e071926843`. 900 exact frames, 12 images, complete decode and confirmed Algenib voice. The sampled frames show forming, pressing and drying. The opening cuts through four shots in 3.8 seconds. No listening approval. |

A separate source test retrieved exact English spans for the Ukrainian boat lamination and laser cutting briefs. The latter demonstrated that the script can use a supported metal-cutting fact in addition to the general lead.

The built image passed runtime checks with both translation models mounted. In normal job `4eafcf65-3efb-479f-abd8-77e7a1c873bd`, the composite-boat brief reached media selection. The article-title-based search returned one distinct candidate for twelve shots, so the job stopped before synthesis. The follow-up also uses the scope-preserving English query for Commons discovery.

The follow-up `7a8a99ef-fb01-43d3-b260-5549c5d28b56` also found one distinct candidate and stopped before synthesis. The relevant [Fiberglass molding collection](https://commons.wikimedia.org/wiki/Category:Fiberglass_molding) contains diagrams and an aircraft example. [Sunreef's Commons collection](https://commons.wikimedia.org/wiki/Category:Sunreef_Yachts) includes finished yachts, trade shows and the aftermath of a fire. Those files do not establish the production steps. No tests were promoted and the optional configuration was not deployed to Studio.
