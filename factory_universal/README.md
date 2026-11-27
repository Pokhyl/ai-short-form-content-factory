# Universal Video Factory

Topic and language → source-grounded vertical MP4 with the selected native voice, distinct photographs, aligned captions and cited sources.

Studio: https://studio.hodor.com.pl/ — no password.

## Delivery

The public form creates a 60-second Ukrainian MP4 on the updated scene-selection pipeline. The volcano acceptance checked browser playback, the selected native voice, 1,800 frames, 24 photographs and credits. See [the long-scene release evidence](../acceptance/factory-universal/2026-11-23-long-scenes/README.md) for the named-location and insect-identity checks and the remaining quality limits.

The worker skips scripts with a verified out-of-window recording and uses the available synthesis attempts for new scripts. An earlier public 30-second paper-manufacturing test passed Chrome playback and frame inspection, with 12 distinct photographs, the selected English voice, synchronized captions and credits. See [the narration and pressing checks](../acceptance/factory-universal/2026-11-23-timing-and-scene-matching/README.md) and the [four-language duration matrix](../acceptance/factory-universal/2026-11-23-matrix-after-reconnect/README.md).

Earlier releases resolved verified split-title spellings and added scene checks for named historical dates and catalog identifiers. The unauthenticated browser request «супер нова» completed a 45-second Ukrainian MP4. Frame and caption review accepted astronomy and English plant biology. The Polish microscope result requires stronger visual grounding for named historical facts. See acceptance/factory-universal/2026-11-22-source-resolution/.

Owner listening approval remains pending. Inputs require an identifiable source and enough suitable licensed photos. A single exact alphanumeric identifier anywhere in a brief can resolve its subject through another Wikipedia edition and follow a published link to the selected language. Studio reports when source coverage is insufficient for the requested focus.

Local translation can use a verified English article for an identifier with no Ukrainian or Russian edition. It can also search English Wikipedia with a locally translated Ukrainian brief. The article revision must cover the translated search terms and the script must cover the original scope. A translated beat carries both the original sentence and its translated text, plus the article revision. The normal image, voice and render gates apply.

The search keeps explicit manufacturing intent when translating a brief. If Wikipedia search cannot produce a suitable translated plan, the existing SearXNG service can find up to six other English Wikipedia article titles. The worker reads those articles directly through Wikipedia and verifies the pinned revision before planning. Search snippets do not enter the narration.

Install the pinned translation files with `python3 factory_universal/setup_models.py --translation` and include `factory_universal/compose.translation.yaml` after the base Compose file to enable the local models. Set `FACTORY_TRANSLATION_HOST_DIR` when using a custom installation directory. Studio runs both models locally from a read-only mount.

## Pipeline

1. Resolve a primary native-language Wikipedia article and Wikidata identity; preserve exact source spans and revision provenance.
2. Plan complete facts with source-linked biography objects, primary-topic context for other subjects and physical manufacturing stages. Compare feasible fact counts against completed native measurements, combining character counts with silent pronunciation estimates; keep production stages in causal order.
3. Search bounded Commons pools across the entire job: three broad queries, eight for long overviews or qualified natural and place scenes, twelve process queries or forty-eight source-linked queries, at most fifty candidates each. Long overviews also consider independently licensed files from the cited article revision. Cache source and search results for 24 hours.
4. Prefer 6/12/18/24 unique images before synthesis. If ordinary discovery cannot cover a scene, also check licensed files from the cited revision and the subject's Wikidata-linked Commons category, where available. When the verified pool cannot support the preferred layout, allow a lower shot count with at least two photos per beat and at least one shot per five seconds on average. Reuse scores and pixel audits when their verification inputs match. Require metadata context, pinned local CLIP subject and genre screening, and crop and resize deduplication. Preserve the complete photograph on a solid matte.
5. Synthesize with the exact selected Google voice through the retained native credential gateway and PostgreSQL free-tier ledger. Exclude verified cached recordings outside the requested speech window before photo preparation. Try at most three distinct complete source-backed texts, stop on an ambiguous send, and preserve the selected recording's voice, pitch and speed.
6. Align the unchanged native recording using the existing media worker; render 1080×1920 H.264/AAC at 30 fps with exactly 450/900/1350/1800 frames, then fully decode and verify the result.

Manufacturing scenes can query a tool explicitly linked in the narrated source paragraph. Tool metadata can support a scene when it identifies the tool in use and its documented function matches the operation. Kiln firing and decoration have separate media queries and image checks. Natural speech can fall up to 200 ms below the 90% coverage target, with exact video duration and the selected recording's playback speed preserved.

No Gemini or paid model APIs. eSpeak is an internal duration estimate only and is never audible output.

| Language | Owner-selected voice |
|---|---|
| EN | en-US-Chirp3-HD-Algenib |
| PL | pl-PL-Chirp3-HD-Enceladus |
| RU | ru-RU-Wavenet-D |
| UK | uk-UA-Chirp3-HD-Enceladus |

Subject CLIP gates remain .24 positive/.015 margin; ASR .95 global/.85 per scene. Bounded CLIP caches retain 256 image vectors and 128 complete text batches. Real-image verification found zero score difference versus full encoder execution; repeated inputs avoid inference. See visual_cache_checks.py and the dated evidence.

## Licenses and review

New adaptations use CC BY-SA 4.0. Compatible Commons media, including CC BY-SA 3.0/4.0, retain their original author/source/license/change notices. NC/ND/unknown media are rejected. MP4 tags embed full attribution; credits.txt and credits.json accompany the output, with /api/jobs/{id}/credits available in Studio. The manifest records sources, licenses, hashes, voice receipts, alignment and renderer gates.

The current Examples view contains the five reviewed outputs. Old tests and failures remain in history. Assistant frame inspection and automated checks do not constitute owner listening approval.

## Operation

Active server checkout: /opt/factory-universal. Docker Compose: factory_universal/compose.yaml, app service only. Delivery branch: codex/factory-universal-20261112. Read docs/CODEX_START_HERE.md and root AGENTS.md before work. Existing server credentials/settings remain retained; never print or commit them or modify shared services.

One worker, 900-second deadline, 2-GiB owned output limit including ASR/reviews, 512-MiB cache, 30-day retention and a 2-GiB free-disk reserve. Cleanup selects exact factory SQLite-owned UUID directories. No global Docker prune or unrelated-file removal. Image GET 503 permits two delayed retries; 429 and ambiguous native sends are never blindly replayed.

Run runtime checks with:

```sh
docker compose -f factory_universal/compose.yaml run --rm --no-deps -T app python3 - <factory_universal/checks.py
```

Run alignment_checks.py and renderer_checks.py when relevant. visual_cache_checks.py accepts --images and --receipt for local real-image encoder-equivalence checks. stage_outputs.py exercises the normal worker from a staged image; its receipt is immutable and never replayed. preflight_outputs.py is image-only. review_outputs.py collects existing outputs and actual midpoint frames without creating jobs or synthesis.

Before deployment verify no active jobs, publish source/evidence and recreate only app with --no-deps. Verify the running image, implementation hashes, public routes and a normal public create-to-ready flow. Preserve the owner-rejected historical IDs and their review decisions.

Browser QA uses the existing Chrome installation in an isolated headless context, without credentials. Install the optional pinned requirements in a project-local environment and run browser_regression.py --receipt /absolute/path/result.json. Its default is read-only; --submit-topic explicitly creates one recorded job with --language and --duration. Existing receipts are never replayed. The check covers default/user and example views, continuous video playback across refresh, mobile overflow, JavaScript errors and retained form selections.
