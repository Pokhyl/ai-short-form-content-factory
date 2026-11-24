# Native narration duration and frame review

The public request «нейтронная звезда», Ukrainian, 45 seconds, reached the voice stage in job `1ada4823-bb86-4a56-93f0-767e97e3d81a`. The three native measurements were 47.616 s, 39.864 s and 35.256 s. All were outside the 40.5–45 s speech window. The original job remains unchanged.

The planner now compares distinct source-grounded scripts around the speech budget and ranks them against the original requested duration. An early return requires an estimate close to the center of the speech window. The selected Google voice, measured duration gate and three-attempt limit remain in effect. The regression check exercises the candidate ranking for all 16 language and duration combinations.

Normal staged job `7798c4d8-5df0-4939-9fc8-09b2d40ce571` used a single Ukrainian Enceladus synthesis of 43.344 s at native tempo and rendered 1,350 frames in 45 s. Full decode, source attribution and the automated renderer checks passed.

Midpoint review of all 18 frames rejected the staged video. Frames 5–6 and 10–11 included generated illustrations or simulation stills. The final narration about the interior of the star used unrelated external views. Multiple images came from the same narrow set of releases. Frames 2 and 14 also embedded annotation or labeling in the source image. This staged output was not promoted.

The follow-up metadata checks cover declared simulation stills, planetarium imagery, image creation software, labeled views and infographics. Known observatory image variants in the same release now compete for one slot.

With those screens enabled, fresh job `9f14a8d0-e99f-4b48-8acc-eb2ba483dc93` stopped before synthesis. The scene planner could not verify enough distinct photographs for the opening. Its trace also exposed a bypass: an opening definition excluded after a photo rejection could still be inserted before ordinary sentence filtering. The follow-up applies the same exclusions to that opening. A runtime regression checks that the planner moves on to a different grounded sentence.

## Additional topics

- EN30 «How paper is made» (`dfd5370a-b7e6-477c-a43c-8a6f2b9705f1`) rendered 900 frames with a single Algenib recording. The 12 sampled frames showed papermaking, moulds, pressing and drying. The opening cuts through five photos in 4.2 seconds, and the wide factory shot gives limited evidence for pressing.
- PL15 «Łódź» (`224bc833-9928-48be-8e36-34398a212676`) rendered 450 frames with the selected Polish Enceladus voice. Frame review rejected it. The same sculpture appears from several angles and some shots under the caption about the diocese show unrelated public art.
- RU60 «Паровоз» (`30e8957d-9b7a-4205-b608-bc5b9ab162e6`) rendered 1,800 frames. A single Wavenet-D recording ran 57.216 s. Frame review rejected it. Shot 8 shows a firebox during a claim about locomotives without one. Shots under the caption about diesel and electric replacements show steam locomotives. Shot 15 is an engraving, and shots near the end show locomotive exteriors while the script describes the boiler and drive.

The last build retried the Ukrainian request as job `48951407-3c5d-4275-b7fe-aea5b4e53fcf`. The worker tried all 20 bounded source alternatives and found too few verified photographs. It stopped before making any synthesis request. Different source sentences appear in the rejection trace. The remaining gaps concern reliable evidence for each scene and showing distinct subjects where the script calls for them.

The final image passed the runtime, alignment and FFmpeg suites. The four-case live-data run took place in staging. Full scene acceptance is incomplete. Studio continued running the preceding image, and no test output was promoted. There was no listening approval.
