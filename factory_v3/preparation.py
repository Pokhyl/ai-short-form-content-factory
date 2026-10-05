"""Durable per-request budgets and exact request-identity replay for preparation."""
import json
from .preflight import digest, verify_before_voice


class ResourceUnavailable(ValueError):
    def __init__(self, receipt):
        self.receipt = receipt
        super().__init__("selected resource definitively unavailable")


class PreparationLedger:
    def __init__(self, postgres, revision):
        if not isinstance(revision, str) or not revision.strip():
            raise ValueError("source revision required")
        self.postgres = postgres
        self.revision = revision

    def create(self, request_id, request, budgets):
        return self.postgres._call(
            "SELECT factory_v3.create_preparation(%s::uuid,%s::jsonb,%s::jsonb,%s)",
            (request_id, json.dumps(request), json.dumps(budgets), self.revision))

    def claim_run(self, request_id):
        return self.postgres._call("SELECT factory_v3.claim_preparation_run(%s::uuid,%s)",
                                   (request_id, self.revision))

    def claim(self, request_id, key, kind, request_hash):
        return self.postgres._call(
            "SELECT factory_v3.claim_preparation_call(%s::uuid,%s,%s,%s,%s)",
            (request_id, key, kind, request_hash, self.revision))

    def finish(self, request_id, key, result):
        self.postgres._call(
            "SELECT factory_v3.finish_preparation_call(%s::uuid,%s,%s::jsonb)",
            (request_id, key, json.dumps(result, allow_nan=False)))

    def fail(self, request_id, key, code, receipt=None):
        self.postgres._call("SELECT factory_v3.fail_preparation_call(%s::uuid,%s,%s,%s::jsonb)",
                            (request_id, key, code, json.dumps(receipt)))

    def unavailable(self, request_id, key, receipt):
        self.postgres._call("SELECT factory_v3.unavailable_preparation_call(%s::uuid,%s,%s::jsonb)",
                            (request_id, key, json.dumps(receipt)))

    def reject(self, request_id, code):
        self.postgres._call("SELECT factory_v3.reject_preparation(%s::uuid,%s,%s)",
                            (request_id, code, self.revision))

    def complete(self, request_id, frozen):
        self.postgres._call(
            "SELECT factory_v3.complete_preparation(%s::uuid,%s::jsonb,%s)",
            (request_id, json.dumps(frozen), self.revision))


class BudgetedCalls:
    def __init__(self, ledger, request_id):
        self.ledger = ledger
        self.request_id = request_id

    def run(self, key, kind, public_request, invoke, *, allow_unavailable=False):
        # Include all identity-affecting settings, NEVER credentials.
        claim = self.ledger.claim(self.request_id, key, kind, digest(public_request))
        if claim.get("unavailable"):
            raise ResourceUnavailable(claim["response"])
        if claim["cached"]:
            return claim["response"]
        try:
            response = invoke()
            json.dumps(response, allow_nan=False)
            self.ledger.finish(self.request_id, key, response)
            return response
        except BaseException as error:
            receipt = getattr(error, "receipt", None)
            if allow_unavailable and isinstance(receipt, dict) and receipt.get("status") in {403, 404, 410}:
                self.ledger.unavailable(self.request_id, key, receipt)
                raise ResourceUnavailable(receipt) from None
            try:
                self.ledger.fail(self.request_id, key, type(error).__name__, getattr(error, "receipt", None))
            except Exception:
                pass  # The durable started claim still blocks another attempt.
            raise

    def complete(self, root, frozen):
        try:
            verify_before_voice(root, frozen)
        except Exception as error:
            self.ledger.reject(self.request_id, type(error).__name__)
            raise
        self.ledger.complete(self.request_id, frozen)
