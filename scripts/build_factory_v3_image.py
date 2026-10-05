"""Secret-free bounded image build from committed runtime source."""
import argparse,json,shutil,subprocess,tempfile
from pathlib import Path
root=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument("--tag",required=True);args=parser.parse_args()
head=subprocess.check_output(["git","rev-parse","HEAD"],cwd=root,text=True).strip()
if subprocess.check_output(["git","status","--porcelain","--","factory_v3","material_first","scripts/audit_final_media.py"],cwd=root,text=True).strip():
    raise ValueError("commit runtime source before building")
with tempfile.TemporaryDirectory(prefix="factory-v3-build-") as tmp:
    context=Path(tmp)
    shutil.copytree(root/"factory_v3",context/"factory_v3",ignore=shutil.ignore_patterns("__pycache__","*.pyc"))
    shutil.copytree(root/"material_first",context/"material_first",ignore=shutil.ignore_patterns("__pycache__","*.pyc"))
    (context/"scripts").mkdir();shutil.copy2(root/"scripts/audit_final_media.py",context/"scripts/audit_final_media.py")
    result=subprocess.run(["docker","build","--build-arg","SOURCE_REVISION="+head,"--label","org.opencontainers.image.revision="+head,
      "-f",str(context/"factory_v3/Dockerfile"),"-t",args.tag,str(context)],capture_output=True,text=True,timeout=110)
    (root/"acceptance/factory-v3/image-build-current.txt").write_text(result.stdout+result.stderr)
    print((result.stdout+result.stderr)[-1200:])
    if result.returncode:raise RuntimeError("image build failed; inspect actual effects")
identifier=subprocess.check_output(["docker","image","inspect","-f","{{.Id}}",args.tag],text=True).strip()
manifest={"tag":args.tag,"image_id":identifier,"source_commit":head,"deployed":False}
(root/"acceptance/factory-v3/image-current.json").write_text(json.dumps(manifest,indent=2)+"\n")
print(json.dumps(manifest))
