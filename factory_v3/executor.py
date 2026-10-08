"""One bounded stage per invocation. Never retry a claimed external operation."""
from copy import deepcopy
from .preflight import verify_before_voice


NEXT = {"prepared": "voice", "voice_ready": "align", "align_ready": "render", "render_ready": "qa"}


class ReconciliationRequired(RuntimeError):
    pass


class Executor:
    def __init__(self, ledger, media_root, adapters, *, verifier=verify_before_voice):
        self.ledger = ledger
        self.media_root = media_root
        self.adapters = adapters
        self.verify = verifier

    def create(self, job_id, frozen):
        self.verify(self.media_root, frozen)
        return self.ledger.create(job_id, deepcopy(frozen))

    def run_next(self, job_id):
        snapshot = self.ledger.snapshot(job_id)
        status = snapshot["status"]
        if status == "qa_pass":
            return snapshot
        if status in {"failed", "unknown"} or status.endswith("_running"):
            raise ReconciliationRequired("terminal or claimed stage cannot be repeated: " + status)
        stage = NEXT.get(status)
        if stage is None:
            raise ValueError("unsupported job status")
        frozen = snapshot["frozen"]
        # Revalidate files/contracts before every step, including immediately before TTS.
        payload = self.verify(self.media_root, frozen)
        effective=snapshot['outputs'].get('voice',{}).get('effective_frozen')
        if effective is not None:
            from material_first.voice_correction import validate_revision
            validate_revision(payload,effective['payload'])
            payload=self.verify(self.media_root,effective)
        self.ledger.claim(job_id, stage, frozen["sha256"])
        try:
            if stage == "voice":
                accounted = False
                def before_send(attempt=None, revised=None):
                    nonlocal accounted
                    if attempt is not None:
                        from material_first.voice_correction import POLICY, validate_revision
                        if payload.get('voice_correction') != POLICY:
                            raise ValueError('voice correction not authorized by frozen plan')
                        validate_revision(payload,revised['payload'])
                        self.verify(self.media_root,revised)
                        self.ledger.account_voice_revision(job_id,attempt,revised)
                        accounted=True
                        return
                    if accounted:
                        raise ValueError("voice send already armed")
                    self.verify(self.media_root, frozen)
                    self.ledger.account_voice_attempt(job_id)
                    accounted = True
                output = self.adapters.voice(job_id, deepcopy(payload), deepcopy(snapshot["outputs"]), before_send)
                if not accounted:
                    raise ValueError("voice adapter bypassed send accounting")
            else:
                output = getattr(self.adapters, stage)(job_id, deepcopy(payload), deepcopy(snapshot["outputs"]))
            if not isinstance(output, dict) or output.get("status") != "ready":
                raise ValueError("adapter did not return verified ready output")
            self.ledger.finish(job_id, stage, output)
        except BaseException as error:
            # If persistence is unavailable, the durable 'started' claim still blocks a retry.
            try:
                self.ledger.fail(job_id, stage, type(error).__name__, True)
            except Exception:
                pass
            raise
        return self.ledger.snapshot(job_id)
