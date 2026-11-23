# Sixty-second scene selection

The two earlier Ukrainian failures ended before speech synthesis. The image-only runs here tested the same requests with new job IDs, after changes to photo discovery, evidence matching and ranking. All image-only runs made zero voice calls.

The ranking stage scores each candidate once per scene and target, even when the same scene has several shots. Equivalent pixel verification inputs share an audit across replans. Distinct captions, identities and visual requirements keep the appropriate verification inputs. The worker still requires each selected image to pass the scene, photographic genre and duplicate checks.

For long concept videos, the worker adds photographs from the exact Wikipedia article revision used for the script. It retrieves every candidate's independent Commons license and provenance. Source images enter the same eligibility and verification path as search results.

The article-stage preflights produced 24 photographs for each of the volcano and bee requests. Manual review rejected topic-only photographs during named events and during scenes about specific ecological interactions. The next volcano pass discarded the historical story when it could not verify photos of the 1883 eruption. Its frame review still showed unrelated geographic examples for a regional claim. The normal worker stage uses the follow-up geographic, historical and interaction gates and checks the full MP4 flow.

The site release at the start of this work was `69d6213`.

The first normal worker run for «Вулкан» rendered 1,800 frames, 24 distinct images and 57.264 seconds of the selected native Ukrainian voice. Chrome played the 1080×1920 MP4 and served its byte ranges and credits. The frame review rejected shot 15, which used a labeled comparison photograph from Mars in an Earth-science scene. The follow-up metadata gates reject creator-declared overlays and off-planet imagery when the request concerns terrestrial volcanism.

The first normal worker run for «Бджоли» also rendered 1,800 frames and 24 distinct images with the selected voice. Frame review found general photographs of bees during honey-production and colony scenes and a queen-marking photograph during pollination. The next build recognizes both active and passive Ukrainian wording for honey production, ties collective organization to colony evidence, and rejects queen marking in a pollination scene.

The second volcano MP4 removed the Mars comparison and rendered the required 1,800 frames. Midpoint review also found photos of the wrong volcanoes during a comparison naming Vesuvius and Hawaii, as well as two close views of an isolated rock formation in the opening. A check against the original Wikipedia revision confirmed that the updated alias matcher attaches Mount Vesuvius and Hawaii to the inflected Ukrainian text. The release also distinguishes a landform overview from a material sample.

The second bee MP4 moved away from unsupported honey-making and colony imagery. Although it decoded correctly, frames 3–7 showed winged termites in a scene about bee anatomy, and the final scene used general bee photos for feeding young. The final identity gate requires a named insect subject independent of a shared trait such as wings. The brood matcher also recognizes Ukrainian wording for the young.

## Live Studio

Release `474a267` passed runtime, alignment and FFmpeg checks. Its eight live application hashes matched the checkout. In production, the previous five termite files all received a negative score for the bee-wing scene.

Chrome created UK60 «Вулкан» job `1db660ca-2a91-4020-94c4-e2f216ece2ca` through the public form. The file decoded and played at 1080×1920 with 1,800 frames, 24 distinct photographs and 56.208 seconds of native Enceladus speech. Chrome verified video ranges and credits. Frame inspection confirmed the Vulcano island scene and the removal of the isolated rock samples and the annotated Mars comparison. The last few shots give limited evidence for the plume-height claim. Listening approval is pending.

A read-only Chrome recheck on the live service replayed existing PL15 Warszawa, EN30 Barack Obama and RU45 Марс outputs. All three retained the expected frame count, selected voice, video ranges and credits. These were earlier renders, and the recheck made no synthesis requests.

The live form created UK60 «Бджоли» job `77465dea-64c1-47bc-9f7e-d5896d34556e`. The output passed full decode, Chrome playback, the byte-range and credits checks, and native voice verification. All 24 actual shot midpoints were inspected. The termite files from the earlier run are absent. The opening allocates nine shots to 3.4 seconds, and the seasonal beekeeper migration scene relies on generic pollination closeups. The QA review requested changes for those two findings. The three measured narration lengths and the shot allocation are recorded in the pacing receipt.
