from pathlib import Path

root=Path(__file__).resolve().parents[1]
compose=(root/'compose.yaml').read_text()
server=(root/'services/media-worker/src/server.mjs').read_text()
env=(root/'.env.example').read_text()
assert 'PEXELS_API_KEY: ${PEXELS_API_KEY:-}' in compose
assert 'PIXABAY_API_KEY: ${PIXABAY_API_KEY:-}' in compose
assert 'SEARXNG_URL: ${SEARXNG_URL:-http://ai-short-form-v4-search:8080/search}' in compose
# Explicitly inspect the media-worker service before the top-level networks declaration.
worker=compose.split('  media-worker:',1)[1].split('\nnetworks:',1)[0]
assert '\n    networks:\n      default:\n      edge:' in worker
assert 'PEXELS_API_KEY=' in env and 'PIXABAY_API_KEY=' in env and 'SEARXNG_URL=' in env
assert 'process.env.SEARXNG_URL' in server
assert 'provider: "searxng"' in server
assert 'https://en.wikipedia.org/w/api.php' not in server
assert 'research_provider_unconfigured' in server
assert 'pexels: { configured:' in server and 'pixabay: { configured:' in server
print('PROVIDER_RUNTIME_WIRING_REGRESSION_PASS')
