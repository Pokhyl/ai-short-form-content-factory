# Provider Policy

Updated: 2026-09-19

## Gemini Developer API
Selected text model: gemini-3.5-flash-lite.

Verified from official Google documentation:
- stable GA model;
- text output supported;
- structured outputs supported;
- standard Developer API Free Tier lists text input/output as free of charge;
- active rate limits are project-specific.

Rules:
- Gemini is for evidence-grounded text/script/storyboard only;
- no Gemini TTS in production;
- no Google Search grounding inside Gemini; research comes from SearXNG plus fetched evidence;
- fail closed if free-tier access is unavailable.

## Google Cloud Text-to-Speech
Selected voices:
- en-US-Chirp3-HD-Algenib
- pl-PL-Chirp3-HD-Enceladus
- ru-RU-Wavenet-D
- uk-UA-Chirp3-HD-Enceladus

Verified from official Google Cloud documentation:
- Chirp 3 HD supports English US, Polish, Russian and Ukrainian;
- Chirp 3 HD free usage limit is 1,000,000 characters/month;
- WaveNet free usage limit is 4,000,000 characters/month;
- billing must be enabled;
- usage above free limits is automatically billable.

Free-only enforcement:
- use a dedicated Google Cloud project for this pipeline;
- record every TTS operation and exact input character count in PostgreSQL;
- keep separate monthly counters for Chirp 3 HD and WaveNet;
- production internal ceiling is 900,000 characters/month for Chirp 3 HD;
- production internal ceiling is 3,600,000 characters/month for WaveNet;
- these 90% ceilings are project engineering safety settings, not Google recommendations;
- fail closed when the internal ceiling is reached;
- no paid fallback;
- one final TTS synthesis per job only.

## Pixabay
Live production credential verification — 2026-09-19:
- image search HTTP 200;
- video search HTTP 200;
- current key exposed rate-limit headers: limit 100, remaining 99, reset 60 seconds;
- response cache policy exposed `max-age=86400`;
- one returned JPEG downloaded successfully through media-worker and passed ffprobe.

Verified from official API documentation:
- image and video search supported;
- default limit 100 requests per 60 seconds per API key;
- rate-limit headers expose limit/remaining/reset;
- API responses must be cached for 24 hours;
- systematic mass downloads are not allowed;
- permanent image hotlinking is not allowed;
- selected assets should be downloaded to our server.

Adapter requirements:
- persist source URL, provider asset ID, author/user metadata, media URL, dimensions and media type;
- download selected assets to durable local storage;
- cache query responses for at least 24 hours;
- persist rate-limit headers;
- never work around limits.

## Pexels
Live production credential verification — 2026-09-19:
- photo search HTTP 200;
- video search HTTP 200;
- current key exposed rate-limit headers: limit 25000, remaining 24248 after smoke tests;
- one returned JPEG downloaded successfully through media-worker and passed ffprobe.

Verified from official API documentation:
- photo and video APIs available;
- documented default limits may differ from the live account-specific headers;
- successful responses expose limit/remaining/reset headers;
- API use requires a prominent link to Pexels;
- photographer credit is requested when possible;
- rate-limit bypass is prohibited.

Adapter requirements:
- persist source URL, photographer, photographer URL, provider asset ID, dimensions, media type and attribution metadata;
- preserve attribution metadata through render/publish metadata;
- persist rate-limit headers;
- never work around limits.

## Wikimedia Commons
Status: live API PASS.

Rules:
- accepted licenses only: Public Domain/PDM, CC0, CC BY, CC BY-SA;
- persist source URL, author, exact license, license URL, dimensions and media type;
- never treat Wikimedia as the only or automatic first-choice provider.

## Openverse
Status: disabled while the official API returns a Cloudflare challenge from this VPS.

Rules:
- no bypass;
- no website scraping substitute;
- re-test only via the official API path.

## Unsplash
Not enabled.

Before enabling:
- verify current API key;
- verify hotlink requirements;
- verify download tracking;
- preserve attribution metadata;
- verify local rendering/downloading compliance.

## Production-ready gate
A provider is production-ready only after:
1. current official documentation is verified;
2. a live credential call succeeds through the production n8n at `publisher.hodor.com.pl`;
3. compliance metadata is captured;
4. rate-limit behavior is captured;
5. a real output is stored and inspected where applicable.
