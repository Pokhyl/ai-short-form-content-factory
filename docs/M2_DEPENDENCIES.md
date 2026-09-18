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
- image metadata endpoint is reachable from the isolated runtime.

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
Status: PENDING CREDENTIAL IN ISOLATED RUNTIME

Current isolated n8n has no Gemini credential.

Shared n8n contains Gemini credentials, but the clean-rebuild isolation rule forbids copying secrets out of another runtime or creating a hidden shared-runtime dependency.

Required proof:
- current approved free-tier model call from isolated runtime;
- structured JSON response;
- no paid fallback.

### Google Cloud Text-to-Speech
Status: PENDING OAUTH CREDENTIAL IN ISOLATED RUNTIME

Required proof:
- real OAuth authentication from isolated runtime;
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
Status: PENDING

Required proof:
- selected local aligner pinned;
- en/pl/ru/uk audio tests;
- actual word/token timestamps;
- script coverage thresholds validated.

## Gate

M3 must not start until the mandatory M2 production dependencies are verified.

Mandatory to unblock M3:
1. Gemini text;
2. Google Cloud TTS with all four locked voices;
3. at least two independent production-ready visual sources;
4. local four-language speech alignment.

Wikimedia currently counts as one visual source. Pixabay is the intended second source once its API key is connected.
