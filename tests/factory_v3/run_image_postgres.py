"""Check packaged V3 against an isolated PostgreSQL; no provider or production calls."""
import argparse
from pathlib import Path
import subprocess
import uuid

root=Path(__file__).resolve().parents[2]
parser=argparse.ArgumentParser()
parser.add_argument("--image",required=True)
args=parser.parse_args()
pgimage=subprocess.check_output(
 ["docker","inspect","-f","{{.Config.Image}}","shorts-v2-postgres-1"],text=True).strip()
name="factory-v3-driver-test-"+uuid.uuid4().hex[:8]
try:
 subprocess.run(["docker","run","-d","--network","none","--name",name,"--user","postgres",
  "--entrypoint","sh",pgimage,"-c","exec tail -f /dev/null"],
  check=True,capture_output=True,text=True,timeout=10)
 setup="""
set -eu
initdb -U shorts -A trust -D /tmp/v3-pg >/dev/null
pg_ctl -D /tmp/v3-pg -o "-k /tmp -c listen_addresses='127.0.0.1'" -w -t 15 start >/dev/null
createdb -h /tmp -U shorts shorts_factory
"""
 subprocess.run(["docker","exec",name,"bash","-lc",setup],
  check=True,capture_output=True,text=True,timeout=20)
 result=subprocess.run(["docker","run","--rm","--network","container:"+name,
  "--entrypoint","python3","-e","PYTHONPATH=/app",
  "-e","V3_TEST_DATABASE_URL=postgresql://shorts@127.0.0.1:5432/shorts_factory",
  "-v",str(root/"tests/factory_v3/ledger_driver_check.py")+":/fixtures/driver.py:ro",
  "-v",str(root/"db/02-provider-budget.sql")+":/fixtures/budget.sql:ro",
  args.image,"/fixtures/driver.py"],capture_output=True,text=True,timeout=30)
 (root/"acceptance/factory-v3/image-postgres-driver.txt").write_text(result.stdout+result.stderr)
 print(result.stdout+result.stderr)
 if result.returncode:
  raise RuntimeError("isolated packaged PostgreSQL driver check failed")
finally:
 subprocess.run(["docker","rm","-f",name],capture_output=True,text=True,timeout=10)
print("ISOLATED_TEST_CONTAINER_REMOVED")
