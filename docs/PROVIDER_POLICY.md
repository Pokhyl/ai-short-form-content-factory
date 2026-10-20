## Wikimedia retrieval compatibility — 2026-10-07
Current official metadata/thumbnail docs checked: CommonsMetadata explicitly describes Copyrighted=False public-domain metadata and its default public-domain schema license link as https://commons.wikimedia.org/wiki/Help:Public_domain (https://www.mediawiki.org/wiki/Extension:CommonsMetadata). MissingLicenseUrl may use that link only with explicit normalizedPublic Domain + Copyrighted=False and NonFree!=True; actual per-file source URL, original metadata and attribution remain. Missing licensed/copyrighted/unknown links still rejected. Explicit unsafe license URLs still rejected. Thumbnail API now returns thumb.wikimedia.org (https://phabricator.wikimedia.org/T439443); exact host added beside upload.wikimedia.org, no arbitrary hosts or constructed thumbnail URLs. Actual saved API corpus reproduces both admission bugs; no new provider calls in replay. Picture type/relevance still needs independent inspection; PD is not a real-photo declaration.

# Provider Policy

Updated: 2026-10-13 (selected free-tier model availability recovery)

## Gemini Developer API
Selected text model: gemini-3.1-flash-lite. Google documents this stable model with structured outputs and free standard-tier text/image input and text output.

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
- use a current Gemini authorization key, not a historical standard API key;
- Google AI Studio has created new keys as authorization keys since 2026-05-28;
- current Google documentation rejects unrestricted standard keys; explicitly restricted standard keys continue to work (https://ai.google.dev/gemini-api/docs/api-key, updated2026-09-25);
- fail closed if free-tier access is unavailable.

## Factory Next narrative model — 2026-10-20 candidate

An additional fixed model, `gemini-3.8-flash`, is implemented for Factory Next narration composition, independent script review and measured-duration rewrites. Primary research/photo model remains `gemini-3.1-flash-lite`. This is an explicit private configuration, never an automatic paid fallback or public model selector.

Google's current official pricing lists standard text input/output free of charge; the model supports structured outputs and thinking low/medium/high:
- https://ai.google.dev/gemini-api/docs/pricing#gemini-3.8-flash
- https://ai.google.dev/gemini-api/docs/models/gemini-3.8-flash

Actual credential-backed capability evaluation `cda47247-d7b4-4292-beb7-396faed4e8dd`: project billingInfo false, same selected Gemini credential, one separately metered standard-tier request, modelVersion gemini-3.8-flash, 1117 input / 412 output / 3952 thinking tokens. It rejected all three saved human-rejected scripts and accepted all three exact fact-statement controls. This supports the tested semantic boundary, not universal accuracy or MP4 acceptance.

Opt-in requires `factory_next_narrative_proof` bound to the same project and credential hash, exact model, billing false, standard free-tier true and actual verification ID. The native gateway's `gemini_narrative` role has a fixed model URL and the same existing body/tool/token limits. Per-job call ceilings, monthly voice quotas and immutable uncertain calls remain unchanged. Voice corrections do not retry unavailable or ambiguous sends.

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
- Legacy plans: one TTS synthesis only. Owner-authorized measured-text-correction-v1 plans: maximum three separately accounted sends; correction only after a completed measured duration mismatch, never after an ambiguous response. Existing monthly ceilings and free-only policy remain enforced.

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
