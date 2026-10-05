"""Run V3 SQL against a disposable isolated PostgreSQL, never the production DB."""
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
image = subprocess.check_output(
    ["docker", "inspect", "-f", "{{.Config.Image}}", "shorts-v2-postgres-1"], text=True).strip()
script = """
set -eu
initdb -U shorts -A trust -D /tmp/v3-ledger-pg >/dev/null
pg_ctl -D /tmp/v3-ledger-pg -o "-k /tmp -c listen_addresses=''" -w -t 15 start >/dev/null
trap 'pg_ctl -D /tmp/v3-ledger-pg -m immediate stop >/dev/null' EXIT
createdb -h /tmp -U shorts shorts_factory
psql -X -h /tmp -U shorts -d shorts_factory -v ON_ERROR_STOP=1 -f /work/db/02-provider-budget.sql >/dev/null
psql -X -h /tmp -U shorts -d shorts_factory -v ON_ERROR_STOP=1 -f /work/factory_v3/ledger.sql >/dev/null
psql -X -h /tmp -U shorts -d shorts_factory -v ON_ERROR_STOP=1 -f /work/factory_v3/preparation.sql >/dev/null
psql -X -h /tmp -U shorts -d shorts_factory -v ON_ERROR_STOP=1 -f /work/factory_v3/provider_cache.sql >/dev/null
psql -X -h /tmp -U shorts -d shorts_factory -v ON_ERROR_STOP=1 -f /work/tests/factory_v3/ledger_assertions.sql
psql -X -h /tmp -U shorts -d shorts_factory -v ON_ERROR_STOP=1 -f /work/tests/factory_v3/preparation_assertions.sql
psql -X -h /tmp -U shorts -d shorts_factory -v ON_ERROR_STOP=1 -f /work/tests/factory_v3/provider_cache_assertions.sql
"""
result = subprocess.run(
    ["docker", "run", "--rm", "--network", "none", "--user", "postgres",
     "--entrypoint", "bash", "-v", str(ROOT)+":/work:ro", image, "-lc", script],
    capture_output=True, text=True, timeout=50)
print(result.stdout)
print(result.stderr)
raise SystemExit(result.returncode)
