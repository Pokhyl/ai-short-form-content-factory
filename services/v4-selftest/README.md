# V4 self-test runtime

This directory is the Git-tracked source snapshot for the isolated Product-First V4 self-test runtime.

Runtime deployment:

- runner: `/opt/ai-short-form-v4-selftest/runner.py`
- service: `ai-short-form-v4-selftest.service`
- bind: `172.18.0.1:8094`
- Studio UI: `/opt/ai-short-form-content-factory/studio/index.html`
- public review media: `/opt/ai-short-form-content-factory/studio/v4-media/`
- Caddy API prefix: `/api/v4/*`

The V4 UI must not create jobs through legacy `/api/jobs` semantic-v3 endpoints.

The runner uses:

- self-hosted SearXNG for research;
- the internal model gateway for the semantic director;
- continuous Edge TTS;
- exact-audio Whisper word timestamps;
- duration-specific internal shots separate from semantic scenes;
- Wikimedia Commons exact media for factual/explain/proof shots;
- contextual Pexels only for hook/example/transition shots;
- the unified V4 render-manifest/bundle contracts and `VerticalShort` renderer.

No secret values or Basic Auth hashes are stored in this tracked fragment.
