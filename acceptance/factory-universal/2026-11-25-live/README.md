# Studio release d080b6a

Studio runs the image from commit `d080b6a` with the local translation models mounted read-only. The runtime, alignment and real FFmpeg suites passed. The eight live application files matched the release checkout. The proxy recovered after one 502 during the application container restart. A subsequent health check returned 200.

The public Chrome form submitted EN30 «How paper is made» without credentials. Job `8775435d-2e70-4dce-a324-b683fd55f51e` decoded and played at 1080×1920 with exactly 900 frames, 12 distinct photos, native Algenib and downloadable credits. The video endpoint returned the requested byte range. The midpoint review found images of forming, pressing and drying and complete captions. Some scenes use photos of equipment to illustrate operations. The opening changes images about once a second. Playback verification was muted and listening approval is pending.

The repair includes the earlier narration duration, photo metadata and source discovery changes. The Gdańsk yacht-production brief still lacks sufficient reusable source and media coverage in the current pipeline. The n8n brief can reach Ukrainian script planning, but the staged run lacked verified media.

PL15 «Warszawa» (`7ed12d9b-05c0-4242-b8dc-0c0544db0ea1`) decoded with 450 exact frames, six photographs and the selected Polish voice. The frame review rejected its second scene. Modern and twentieth-century street images accompanied a claim about 1427. The planner had omitted two common ways of expressing a source year. A follow-up runtime test and a new source plan caught both forms and allowed an overview about the city and its climate to be selected instead.

RU45 «Марс» (`d91826ec-a094-471c-a651-99df4e2eb857`) rendered 1,350 frames with eighteen photographs and the selected Russian voice. The frame review confirmed orbital images and surface photographs. Views of Mars illustrate the topic but do not directly demonstrate claims about apparent brightness, the length of the year or atmospheric pressure.

UK60 «Вулкан» (`aea4c046-f96d-46e7-a635-c35ae1cddcc1`) repeatedly found enough qualifying photos, then measured native recordings of 46.656 s, 51.936 s and 48.816 s against a 54–60 s window. No MP4 was produced. The initial Warsaw date-filter retest (`37f700f5-5685-4748-bcd9-d856b86f2721`) also stopped at narration with 12.456 s, 15.528 s and 15.528 s. A follow-up build adjusts the source search budget when media replanning and recalibration still leave a draft outside the intended voice window.

The adaptive follow-up `ed215c30-9588-4153-b0e7-db048f3e7976` rendered UK60 «Вулкан» after one unchanged 56.328 s Ukrainian Enceladus recording. The frame review inspected 24 shots. The photographs show volcanic landforms, active eruptions and ash plumes. Surface photographs give only general context for the part about underground channels and magma sources. The other adaptive follow-up, PL15 `2697bbef-d2d6-417c-9265-f86536841a50`, came within 36 ms of the lower voice boundary. The candidate permits a 50 ms margin there while keeping the exact video duration and unmodified voice.

The first attempt with the lower-bound margin reached the renderer and exposed a duplicate threshold. The final candidate shares one measured narration window between planning and every renderer gate. The FFmpeg regression used audio in the 50 ms margin and produced all 450 frames without changing the audio input.

The Warsaw follow-up `e4e6b0a0-e173-4954-ac76-18af1d1a40cb` completed with a cached 13.464 s Polish Enceladus recording and 450 frames. The six inspected photos show Warsaw with captions about the present-day city.

Studio then deployed `56280e8`. The built image passed all three suites, all eight live application files matched the checkout, and health recovered after restart. Chrome replayed all four completed MP4s after this deployment and verified exact durations, 1080×1920 playback, credit downloads and byte ranges. The result files record the native voice and frame count for each video. No listening approval was performed.

On `56280e8`, the public Chrome form created PL15 job `27b5b2bb-b651-42fa-8ada-b8bde19dcb42`. It completed with the same MP4 SHA-256 as the inspected staged Warsaw result, 450 frames and selected Polish Enceladus. The failed historical-scene jobs remain in the records.
