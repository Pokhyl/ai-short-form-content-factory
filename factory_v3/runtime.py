"""Production wiring; public inputs cannot provide credentials, budgets or approvals."""
import json
import re
from pathlib import Path
from uuid import UUID
from .credential_http import CredentialHTTP, MODEL
from .download import PhotoDownload
from .executor import Executor
from .gemini import Gemini
from .http import JSONHTTP
from .ledger import PostgresLedger
from .preparation import PreparationLedger, BudgetedCalls
from material_first.operations import Operations, preparation_budgets
from material_first.producer import DurableProducer
from material_first.portrait import PortraitDownload
from material_first.worker import PhotoWorker, executor as material_executor
from .providers import PhotoSearch, ProviderCache
from .research import Research
from .worker_adapters import WorkerAdapters, GoogleVoice
from scripts.audit_final_media import audit


def load_settings(file):
    path = Path(file)
    if not path.is_file() or path.stat().st_mode & 0o077:
        raise ValueError("private runtime settings file required")
    return json.loads(path.read_text())


class Runtime:
    def __init__(self, settings, root, revision, *, ledger=None, http=None):
        if not re.fullmatch(r"[0-9a-f]{40}", revision or ""):
            raise ValueError("exact built source revision required")
        self.settings, self.root, self.revision = settings, Path(root), revision
        self.ledger = ledger or PostgresLedger(settings["database_url"])
        self.direct = http or JSONHTTP()
        self.gateway = CredentialHTTP(settings["broker_token"], self.direct)
        self.preparations = PreparationLedger(self.ledger, revision)

    def create(self, request_id, topic, language, seconds, *, visual_validation_mode=None):
        request_id = str(UUID(str(request_id)))
        if language not in {"pl","en","ru","uk"} or seconds not in {15,30,45,60}:
            raise ValueError("unsupported language/duration")
        if not isinstance(topic,str) or not 1 <= len(topic.strip()) <= 300:
            raise ValueError("bounded topic required")
        try:
            old = self.preparations.snapshot(request_id)
        except KeyError:
            old = None
        request = {"topic":topic.strip(),"language":language,"seconds":seconds}
        if visual_validation_mode is not None:
            if visual_validation_mode not in {"metadata", "gemini"}:
                raise ValueError("unsupported visual validation mode")
            request["visual_validation_mode"] = visual_validation_mode
        if old is not None:
            if old["request"] != request or old["source_revision"] != self.revision:
                raise ValueError("existing request identity changed")
            return {"id":request_id,"created":False,"status":old["status"]}
        if any((self.root / directory / request_id).exists()
               for directory in ("voiceovers","visuals","renders")):
            raise ValueError("existing media job ID must not be reused")
        self.preparations.create(request_id, request, preparation_budgets(seconds))
        return {"id":request_id,"created":True,"status":"preparing"}

    def producer(self, request_id):
        proof = self.settings.get("free_tier_proof", {})
        if (self.settings.get("gemini_free_tier_confirmed") is not True or
            proof.get("billing_enabled") is not False or proof.get("model") != MODEL or
            not isinstance(proof.get("project_id"), str) or not proof.get("credential_sha256")):
            raise ValueError("verified free-only Gemini configuration required")
        calls = BudgetedCalls(self.preparations,request_id)
        def authorize():
            receipt = calls.run("gemini-billing-check", "metadata",
                {"project_id":proof["project_id"],"credential_scope":self.settings["credential_scope"]},
                lambda:self.gateway.metadata("billing",{"project_id":proof["project_id"]}))
            body = receipt["body"]
            if body.get("projectId") != proof["project_id"] or body.get("billingEnabled") is not False:
                raise ValueError("Gemini project is not confirmed unbilled")
        gemini = Gemini(calls, lambda:"gateway-managed", self.gateway, model=MODEL,
                        free_tier_confirmed=True)
        search = PhotoSearch(calls,ProviderCache(self.ledger),self.gateway,
                             lambda provider:"gateway-managed",self.settings["credential_scope"])
        return DurableProducer(self.root, self.preparations,
            Operations(self.root, Research(calls,self.direct), gemini, search,
                       PortraitDownload(self.root, PhotoDownload(self.root,request_id,calls,self.direct))), authorize=authorize)

    def executor(self):
        adapters = PhotoWorker(self.root,GoogleVoice(lambda:"gateway-managed",self.gateway),
                                   "http://shorts-v2-media-worker-1:3001",audit,http=self.direct)
        return material_executor(self.ledger,self.root,adapters)

    def run(self, request_id):
        self.producer(request_id).prepare(request_id)
        executor = self.executor()
        for _ in range(4):
            state = executor.run_next(request_id)
            if state["status"] == "qa_pass":
                return {"id":request_id,"status":"qa_pass","machine_pass":True,"human_pass":False}
        raise ValueError("bounded execution did not reach machine QA")

    def status(self, request_id):
        prep = self.preparations.snapshot(request_id)
        result = {"id":request_id,"request":prep["request"],"status":prep["status"],
                  "source_revision":prep["source_revision"],"error_code":prep["error_code"],
                  "machine_pass":False,"human_pass":False}
        try:
            state = self.ledger.snapshot(request_id)
            result.update({"status":state["status"],"completed":list(state["outputs"]),
                           "machine_pass":state["status"]=="qa_pass"})
        except KeyError:
            pass
        return result
