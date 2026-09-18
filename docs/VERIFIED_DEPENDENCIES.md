# Verified Dependencies

Last verified: 2026-09-18

Only official vendor documentation is accepted for provider/model eligibility.

## Google Gemini text

- Model: `gemini-3.5-flash-lite`
- Status: stable / GA
- Official models page lists the exact model ID.
- Official pricing page lists a Free Tier for Gemini 3.5 Flash-Lite.
- Source:
  - https://ai.google.dev/gemini-api/docs/models
  - https://ai.google.dev/gemini-api/docs/pricing

## Google Gemini TTS

- Model: `gemini-3.1-flash-tts-preview`
- Status: preview
- Official TTS documentation lists the exact model ID.
- Official pricing page lists input and output as free of charge on the Free Tier.
- Preview models can have more restrictive rate limits.
- Source:
  - https://ai.google.dev/gemini-api/docs/speech-generation
  - https://ai.google.dev/gemini-api/docs/pricing

## Current credential/runtime state

- The Gemini API secret remains only in the existing shared n8n credential store.
- The isolated `shorts-v2` stack does not contain or expose the Gemini API key.
- This project owns two private internal gateway workflows on the shared n8n runtime:
  - `ShortsV2GeminiTextGateway001`
  - `ShortsV2GeminiTtsGateway001`
- External access to those gateway webhook paths is blocked by Caddy; the isolated n8n reaches them only over the private Docker network.
- No unrelated shared workflow or credential is part of the production path.
- On 2026-09-18 the current Gemini TTS credential/model returned HTTP 429 with: `limit: 10 requests per day on Free Tier`. This is observed runtime evidence for the current credential/model, not a universal quota claim.
- There is no paid fallback. A TTS-quota failure marks the product job failed; the same job is not retried or resumed.

## Wikimedia Commons

- Visual source: Wikimedia Commons through the MediaWiki Action API.
- No paid API key is required for the read-only image search used by this project.
- Requests identify the client with a User-Agent.
- File-specific license and attribution metadata are retained per selected asset.
- Official references:
  - https://www.mediawiki.org/wiki/Wikimedia_APIs/Access_policy
  - https://www.mediawiki.org/wiki/API:Imageinfo

## FFmpeg

- Rendering runs locally with FFmpeg; there is no per-video API charge.
- FFmpeg is free/open-source software; licensing depends on the enabled build components.
- Official reference:
  - https://ffmpeg.org/legal.html
