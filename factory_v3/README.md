# Video factory runtime

The deployed Studio is at https://studio.hodor.com.pl/factory-v3/. The `/factory-v3` path is the application route on the Studio host, not a separate publisher deployment. Public access is configured by the private runtime settings.

The complete request path is implemented and wired in `runtime.py`:

1. Studio accepts topic, PL/EN/RU/UK, and 15/30/45/60 seconds. A new request is admitted only after the credential route is available.
2. `material_first` researches sources, retrieves candidate photographs, inspects exact downloaded images, selects relevant distinct materials, and composes and reviews narration.
3. The credential gateway handles provider credentials. Gemini requires an unbilled project; Google TTS has durable monthly character ceilings. Credentials are never supplied by public callers. New preparation calls can make at most three separately budgeted attempts after an explicit gateway-confirmed Gemini 503/UNAVAILABLE, with bounded backoff. Transport ambiguity, voice-stage correction and TTS do not retry.
4. The worker synthesizes natural-speed speech, aligns it, renders whole photographs into a vertical video, and audits the resulting media. Measured-text-correction plans allow at most three separately accounted voice sends; ambiguous calls are not repeated.
5. Studio exposes the script, sources, photo attribution, completed MP4, explicit owner review, and scoped media deletion. Machine QA does not imply owner acceptance.

Implementation and deployment do not establish product reliability. **The project is not accepted as ready.** See `docs/RELEASE_GATE.md` and `acceptance/factory-v3/current-release-verification-20261014.json` for the current evidence and bounded verification plan. Historical missing-adapter lists in earlier versions of this README described initial scaffolding and are no longer accurate.

## Runtime and persistence

`server.py` provides the UI/API and a bounded single worker. `cli.py` provides operator commands. PostgreSQL stores preparation calls, budgets, immutable request identities, execution stages and reviews. `material_first` owns current production planning and media behavior; the older `Producer` in this package is not the current runtime entrypoint.

The application container shares the media volume with the media worker. `deploy/factory-v3/compose.yaml` describes the service; an explicitly recorded override selects the deployed image. Private settings live outside the repository. Build from committed source and verify the exact image before rollout. Do not pull into the dirty production checkout or replay a failed job ID.

## Local verification

```sh
python3 -m unittest discover -s tests/factory_v3
python3 -m unittest discover -s tests/material_first
```

For package tests, mount fixtures at `/app/tests` and `/app/acceptance`, read-only, with networking disabled. Keep the runtime modules from the image; mounting source over them would test different code. Provider-backed media and owner acceptance require separate evidence.

Apply `model_unavailable.sql` after `preparation.sql` before deploying the bounded model-overload handler. It adds one function and does not rewrite historical jobs.
