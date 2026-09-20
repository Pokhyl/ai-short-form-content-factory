# M2 Dependency Verification

Date: 2026-09-18

This file records real dependency tests for the clean rebuild. A provider is not considered production-ready until the test actually passes from the isolated `shorts-v2` runtime.

## PASS

### SearXNG general web search
Status: PASS

Runtime call:

```text
GET http://searxng:8080/search?...&format=json
```

Observed:
- HTTP 200;
- 37 results for a Rayleigh-scattering research query;
- results came from multiple engines, including Google CSE, DuckDuckGo and Brave;
- results included Wikipedia, Reddit, Met Office and independent web pages.

Conclusion:
- research is not limited to Wikipedia;
- SearXNG is usable as the general-web discovery layer.

### Direct source-page fetch
Status: PASS

Observed:
- HTTP 200 from a selected public research page;
- HTML body retrieved successfully inside the isolated n8n container;
- source text contained the expected subject.

Conclusion:
- search results can be followed by direct source retrieval for evidence extraction.

### Wikimedia Commons API
Status: PASS

Observed:
- HTTP 200;
- 5 image candidates returned for a Rayleigh-scattering query;
- image metadata endpoint is reachable from the project server runtime.

Conclusion:
- Wikimedia adapter can proceed to implementation.

### Local render
Status: PASS

Observed synthetic render:
- 1080×1920;
- H.264 / AVC;
- AAC;
- 30 fps;
- 2.000 s container duration;
- valid MP4.

Conclusion:
- FFmpeg rendering works in the pinned media-worker runtime.

## BLOCKED / PENDING

### Openverse
Status: BLOCKED FROM CURRENT VPS

Observed:
- `https://api.openverse.org/v1/images/` returns HTTP 403;
- response is a Cloudflare browser challenge, not API JSON;
- same result from the n8n container and directly from the host.

Decision:
- Openverse is not enabled in production while this remains true;
- do not bypass Cloudflare or scrape the website.

### Gemini text
Status: PASS — live production-n8n proof completed 2026-09-19.

Verified:
- credential `Gemini Text` exists in `publisher.hodor.com.pl` as `googlePalmApi`;
- n8n credential connection test succeeds;
- model: `gemini-3.5-flash-lite`;
- a real text request executed through the production n8n;
- structured JSON mode succeeded;
- returned values matched `status=ok`, `language=en`, `purpose=script`;
- n8n reported 19 input tokens and 27 output tokens;
- no Google Search grounding or Gemini TTS was used;
- the first smoke request failed only because `thinkingBudget=0` was sent; removing that unsupported request parameter produced a successful call;
- temporary M2 workflow was deleted after proof.

### Google Cloud Text-to-Speech
Status: PASS — live OAuth + four-voice proof completed 2026-09-19.

Verified after reconnecting the existing `Google account` credential:
- endpoint: `https://texttospeech.googleapis.com/v1/text:synthesize`;
- the same restored credential ID `8KbFC6GBZOd18bzG` was reused; no replacement credential was created;
- one real MP3 was returned for every locked voice:
  - EN `en-US-Chirp3-HD-Algenib`: 9,696 bytes, 2.424 s, SHA256 `121d1a7ae38c7ee5797d1c5b1f659443172d4380dccc1b1c4124ba71ff63c3cf`;
  - PL `pl-PL-Chirp3-HD-Enceladus`: 13,536 bytes, 3.384 s, SHA256 `aef1cf5874e15f54d1fc20e6ee913968d53af0c443c86945e337aaa5a34a0499`;
  - RU `ru-RU-Wavenet-D`: 20,352 bytes, 2.544 s, SHA256 `b226835db6798969519418c6daa80cf888199bed2903b39808c847c80c866dde`;
  - UK `uk-UA-Chirp3-HD-Enceladus`: 11,712 bytes, 2.928 s, SHA256 `57a503f03b41c36ec9c8c9c589fe24104168c07002836bd1717170e4fb16b2a6`;
- MP3 streams are mono 24 kHz and were inspected with ffprobe;
- no Gemini TTS substitution was used;
- exact successful character counts were committed to the provider usage ledger;
- the earlier failed-auth test reservations remain released;
- temporary TTS M2 workflow was deleted after proof.

### Pixabay
Status: PASS — live credential verified through `publisher.hodor.com.pl` on 2026-09-19.

Observed:
- image search HTTP 200;
- video search HTTP 200;
- image result metadata included provider asset ID, source page URL, user/author metadata, dimensions and media URLs;
- video search returned real video candidates;
- rate-limit headers observed: limit 100, remaining 99, reset 60 seconds;
- response cache policy exposed `max-age=86400`;
- one returned JPEG was downloaded by media-worker and verified by ffprobe;
- downloaded Pixabay test image: JPEG/MJPEG, 640×427.

Conclusion:
- Pixabay is production-ready as an independent visual discovery source subject to the provider/license policy in `docs/PROVIDER_POLICY.md`.

### Pexels
Status: PASS — live credential verified through `publisher.hodor.com.pl` on 2026-09-19.

Observed:
- photo search HTTP 200;
- video search HTTP 200;
- photo result metadata included source page URL, photographer, photographer URL, dimensions and multiple media URLs;
- video search returned a real video candidate;
- live account rate-limit headers observed: limit 25000, remaining 24248 after the video smoke test;
- one returned JPEG was downloaded by media-worker and verified by ffprobe;
- downloaded Pexels test image: JPEG/MJPEG, 5472×3648.

Conclusion:
- Pexels is production-ready as an independent visual discovery source subject to the provider/attribution policy in `docs/PROVIDER_POLICY.md`.

### Unsplash
Status: PENDING API KEY + COMPLIANCE PROOF

Required before enabling:
- API call with project credential;
- hotlinked URL behavior verified;
- required download-location tracking verified;
- attribution metadata retained;
- confirm local render workflow complies with current Unsplash API terms.

### Local speech alignment
Status: PASS — exact production-audio proof completed 2026-09-19.

Selected CPU-compatible dependency:
- official `ggml-org/whisper.cpp` CPU image;
- pinned image digest: `sha256:9cfbaf11ef5bec57ec9cade6af7ed991ab5e32b01a6e40db3380a12363336e11`;
- multilingual `ggml-base.bin`;
- model SHA256: `1be3a9b2063867b937e64e2ec7483364a79917e157fa98c5d94b5c1fffea987b`.

Observed on the exact Cloud TTS MP3s:
- EN transcript exact after normalization; lexical timestamps end at 2360 ms within 2424 ms audio;
- PL transcript exact after normalization; lexical timestamps end at 2960 ms within 3384 ms audio;
- RU transcript exact after normalization; lexical timestamps end at 1930 ms within 2544 ms audio;
- UK transcript exact after normalization; lexical timestamps end at 2640 ms within 2928 ms audio;
- token timestamps are present in whisper.cpp full JSON for every language;
- special `[_TT_*]` control tokens are excluded from lexical timing checks.

Decision:
- the local multilingual aligner is accepted for the production pipeline;
- production must continue using the exact final Google TTS audio as alignment input;
- no proportional timing fallback is permitted.

## Gate

M2 mandatory gate: PASS.

Verified:
1. Gemini text;
2. Google Cloud TTS with all four locked voices;
3. at least two independent production-ready visual sources;
4. local four-language speech alignment.

Visual-source gate is PASS: Wikimedia Commons, Pixabay and Pexels are independently verified. Openverse remains disabled; Unsplash is optional and not required to unblock M3.

M3 is unblocked.


## Recovery findings — 2026-09-19

Historical Google Cloud TTS proof:
- the August backup contains a real Google OAuth credential named Google account;
- WF03 called the Google Cloud text:synthesize endpoint;
- all four selected voices were present;
- August execution history contains repeated successful executions.

Current status:
- the restored OAuth credential was reconnected in-place on 2026-09-19;
- live synthesis now succeeds through the same credential;
- all four locked voices passed and produced inspected MP3 output.

Recovered visual credentials:
- historical Pexels and Pixabay credentials exist in the restored publisher database;
- credential presence is not a current live validity proof;
- do not mark either provider production-ready until a current API call succeeds and metadata/license handling is verified.

Production credential boundary:
- production credentials stay in `publisher.hodor.com.pl`;
- the bootstrap `shorts-v2` n8n container was removed on 2026-09-19;
- supporting Postgres/media-worker/SearXNG remain isolated without moving production n8n credentials.


## Gemini model verification — 2026-09-19

Official Google documentation verified:
- stable production model: gemini-3.5-flash-lite;
- status: GA;
- text output supported;
- structured outputs supported;
- standard Developer API Free Tier lists text input and output as free of charge;
- active rate limits are project-specific and must be checked in AI Studio for the connected project.

Model selection and live-provider proof are both closed.

The live structured-output call succeeded through the production n8n at `publisher.hodor.com.pl` using the `Gemini Text` credential. The bootstrap `shorts-v2` n8n remains removed.


## Free-only TTS budget guard — 2026-09-19

Status: PASS for local budget-control infrastructure and enabled production safety policy.

Implemented:
- db/02-provider-budget.sql;
- db/03-provider-budget-policy.sql;
- factory.provider_budget_limits;
- factory.provider_usage_ledger;
- factory.provider_budget_status;
- atomic reserve_provider_usage();
- idempotent commit_provider_usage();
- idempotent release_provider_usage().

Verified on shorts-v2 PostgreSQL:
- Chirp 3 HD provider free limit: 1,000,000 characters/month;
- WaveNet provider free limit: 4,000,000 characters/month;
- internal Chirp 3 HD ceiling enabled at 900,000 characters/month;
- internal WaveNet ceiling enabled at 3,600,000 characters/month;
- the 90% ceilings are project engineering safety settings, not Google recommendations;
- reservation fails closed while a budget is unset/disabled;
- enabled in-limit reservation succeeds;
- a 900,001-character Chirp reservation is rejected against the 900,000 internal ceiling;
- same idempotency key returns the same reservation;
- concurrent-style allocation cannot exceed the configured internal limit;
- committed/reserved amounts calculate correctly;
- smoke transactions rolled back with zero test ledger rows remaining.

Rollback snapshot:
- .backups/provider-budget-before-enable-20260919.sql

This closes the application-level free-only budget-control mechanism. It does not close the live Google Cloud TTS credential/voice gate.
