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
Status: PENDING LIVE PROOF THROUGH PRODUCTION N8N

Production provider calls must run through `publisher.hodor.com.pl`.

Required proof:
- current approved free-tier model call through `publisher.hodor.com.pl`;
- structured JSON response;
- no paid fallback.

### Google Cloud Text-to-Speech
Status: PENDING OAUTH RECONNECT + LIVE PROOF THROUGH PRODUCTION N8N

Required proof:
- reconnect the restored Google OAuth credential in `publisher.hodor.com.pl`;
- real OAuth authentication through `publisher.hodor.com.pl`;
- one MP3 synthesis for each locked voice:
  - `en-US-Chirp3-HD-Algenib`;
  - `pl-PL-Chirp3-HD-Enceladus`;
  - `ru-RU-Wavenet-D`;
  - `uk-UA-Chirp3-HD-Enceladus`;
- real returned audio inspected;
- no Gemini TTS substitution.

### Pixabay
Status: PENDING API KEY

Official API requires an API key.

Required proof:
- image search;
- video search;
- download of one result;
- source/author/license metadata capture;
- rate-limit headers captured.

### Unsplash
Status: PENDING API KEY + COMPLIANCE PROOF

Required before enabling:
- API call with project credential;
- hotlinked URL behavior verified;
- required download-location tracking verified;
- attribution metadata retained;
- confirm local render workflow complies with current Unsplash API terms.

### Local speech alignment
Status: PARTIAL — runtime/timestamps verified; production-audio quality pending

Selected CPU-compatible dependency:
- official `ggml-org/whisper.cpp` CPU image;
- pinned image digest: `sha256:9cfbaf11ef5bec57ec9cade6af7ed991ab5e32b01a6e40db3380a12363336e11`;
- multilingual `ggml-base.bin`;
- model SHA256: `60ed5bc3dd14eea856493d334349b405782ddcaf0028d4b5df4088345fba2efe`.

Observed:
- CPU binary starts correctly on the VPS;
- en/pl/ru/uk fixtures all produce JSON transcription;
- token timestamps are present;
- synthetic eSpeak fixtures are not accurate enough, especially RU/UK, to use as a production-quality acceptance test.

Decision:
- implementation mechanism is viable;
- final alignment quality gate remains pending until the exact Google Cloud TTS voices are available;
- production acceptance must use the exact final TTS audio, not synthetic test speech.

## Gate

M3 must not start until the mandatory M2 production dependencies are verified.

Mandatory to unblock M3:
1. Gemini text;
2. Google Cloud TTS with all four locked voices;
3. at least two independent production-ready visual sources;
4. local four-language speech alignment.

Wikimedia currently counts as one visual source. Pixabay is the intended second source once its API key is connected.


## Recovery findings — 2026-09-19

Historical Google Cloud TTS proof:
- the August backup contains a real Google OAuth credential named Google account;
- WF03 called the Google Cloud text:synthesize endpoint;
- all four selected voices were present;
- August execution history contains repeated successful executions.

Current status differs:
- the restored OAuth credential can be read by n8n;
- a current live call reaches Google but reports that the credential needs reconnect;
- production status therefore remains PENDING until OAuth is reconnected and all four voices pass again.

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

This closes model-selection uncertainty only. It does NOT close the M2 live-provider gate.

The live structured-output call remains PENDING until it succeeds through the production n8n at `publisher.hodor.com.pl`. The bootstrap `shorts-v2` n8n has been removed.


## Free-only TTS budget guard — 2026-09-19

Status: PASS for local budget-control infrastructure.

Implemented:
- db/02-provider-budget.sql;
- factory.provider_budget_limits;
- factory.provider_usage_ledger;
- factory.provider_budget_status;
- atomic reserve_provider_usage();
- idempotent commit_provider_usage();
- idempotent release_provider_usage().

Verified on shorts-v2 PostgreSQL:
- Chirp 3 HD provider free limit seeded as 1,000,000 characters/month;
- WaveNet provider free limit seeded as 4,000,000 characters/month;
- internal production limits are intentionally NULL and disabled by default;
- reservation fails closed while internal limit is unset/disabled;
- same idempotency key returns the same reservation;
- concurrent-style allocation cannot exceed the configured internal limit;
- committed/reserved amounts calculate correctly;
- test transaction rolled back with zero test ledger rows remaining.

This closes the application-level free-only budget-control mechanism. It does not close the live Google Cloud TTS credential/voice gate.
