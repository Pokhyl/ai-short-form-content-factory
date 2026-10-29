"""Durable per-request budgets and exact request-identity replay for preparation."""
import json
from .preflight import digest, verify_before_voice


class ResourceUnavailable(ValueError):
    def __init__(self, receipt):
        self.receipt = receipt
        super().__init__("selected resource definitively unavailable")


def model_unavailable_receipt(receipt):
    return (isinstance(receipt, dict) and receipt.get('status') == 503
            and receipt.get('error_status') == 'UNAVAILABLE'
            and isinstance(receipt.get('gateway_execution_id'), str)
            and receipt['gateway_execution_id'].isdigit())


class ModelUnavailable(RuntimeError):
    def __init__(self, receipt):
        self.receipt = receipt
        super().__init__('model temporarily unavailable after explicit provider rejection')


class SavedRequestMismatch(ValueError):
    def __init__(self, expected, observed):
        self.expected = expected
        self.observed = observed
        super().__init__("saved provider request identity does not match replay")


class PreparationDeferred(RuntimeError):
    def __init__(self, retry_at):
        self.retry_at = retry_at
        super().__init__('preparation waiting for scheduled provider retry')


class PreparationBusy(RuntimeError):
    pass


def verify_saved_request(request, expected_hash):
    """Require an exact identity match before returning a saved provider response."""
    observed = digest(request)
    if not isinstance(expected_hash, str) or observed != expected_hash:
        raise SavedRequestMismatch(expected_hash, observed)
    return observed


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

    def snapshot(self, request_id):
        result = self.postgres._call("SELECT jsonb_build_object('id',id,'request',request,'status',status,'source_revision',source_revision,'error_code',error_code) FROM factory_v3.preparations WHERE id=%s::uuid", (request_id,))
        if result is None:
            raise KeyError("preparation not found")
        return result

    def claim_run(self, request_id):
        result = self.postgres._call("SELECT factory_v3.claim_preparation_run(%s::uuid,%s)",
                                    (request_id, self.revision))
        if result and result.get('busy'):
            raise PreparationBusy('preparation already claimed or not due')
        return result

    def defer(self, request_id, failed_key, next_key, delay):
        return self.postgres._call('SELECT factory_v3.defer_preparation_call(%s::uuid,%s,%s,%s,%s)',
                                  (request_id, failed_key, next_key, delay, self.revision))

    def waiting(self, request_id):
        return self.postgres._call("SELECT jsonb_build_object('retry_at',d.retry_at) "
            "FROM factory_v3.preparation_deferrals d JOIN factory_v3.preparations p ON p.id=d.preparation_id "
            "WHERE p.id=%s::uuid AND p.status='preparing' AND d.state='waiting'", (request_id,))

    def ready(self):
        return self.postgres._call("SELECT coalesce(jsonb_agg(id),'[]'::jsonb) FROM ("
            "SELECT p.id FROM factory_v3.preparation_deferrals d JOIN factory_v3.preparations p ON p.id=d.preparation_id "
            "WHERE p.status='preparing' AND p.source_revision=%s AND d.state='waiting' AND d.retry_at<=now() "
            "ORDER BY d.retry_at LIMIT 5) due", (self.revision,))

    def claim(self, request_id, key, kind, request_hash):
        return self.postgres._call(
            "SELECT factory_v3.claim_preparation_call(%s::uuid,%s,%s,%s,%s)",
            (request_id, key, kind, request_hash, self.revision))

    def finish(self, request_id, key, result):
        self.postgres._call(
            "SELECT factory_v3.finish_preparation_call(%s::uuid,%s,%s::jsonb)",
            (request_id, key, json.dumps(result, allow_nan=False)))

    def claim_model_retry(self, request_id, key, request_hash, prior_key):
        return self.postgres._call(
            'SELECT factory_v3.claim_model_retry(%s::uuid,%s,%s,%s,%s)',
            (request_id, key, request_hash, self.revision, prior_key))

    def fail(self, request_id, key, code, receipt=None):
        self.postgres._call("SELECT factory_v3.fail_preparation_call(%s::uuid,%s,%s,%s::jsonb)",
                            (request_id, key, code, json.dumps(receipt)))

    def unavailable(self, request_id, key, receipt):
        self.postgres._call("SELECT factory_v3.unavailable_preparation_call(%s::uuid,%s,%s::jsonb)",
                            (request_id, key, json.dumps(receipt)))

    def model_unavailable(self, request_id, key, receipt):
        self.postgres._call('SELECT factory_v3.model_unavailable_preparation_call(%s::uuid,%s,%s::jsonb)',
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

    def defer_unavailable(self, failed_key, next_key, delay):
        result = self.ledger.defer(self.request_id, failed_key, next_key, delay)
        if result['deferred']:
            raise PreparationDeferred(result['retry_at'])

    def run(self, key, kind, public_request, invoke, *, allow_unavailable=False, allow_model_unavailable=False, retry_of=None):
        # Include all identity-affecting settings, NEVER credentials.
        if retry_of is not None:
            if not allow_model_unavailable or kind!='gemini':raise ValueError('retry requires explicit model policy')
            claim=self.ledger.claim_model_retry(self.request_id,key,digest(public_request),retry_of)
        else:
            claim = self.ledger.claim(self.request_id, key, kind, digest(public_request))
        if claim.get("unavailable"):
            if allow_model_unavailable and kind == 'gemini' and model_unavailable_receipt(claim['response']):
                raise ModelUnavailable(claim['response'])
            raise ResourceUnavailable(claim["response"])
        if claim["cached"]:
            return claim["response"]
        try:
            if retry_of is not None:
                import time
                delay=claim.get('retry_delay_seconds')
                if delay not in (60,180):raise ValueError('invalid durable retry delay')
                time.sleep(delay)
            response = invoke()
            json.dumps(response, allow_nan=False)
            self.ledger.finish(self.request_id, key, response)
            return response
        except BaseException as error:
            receipt = getattr(error, "receipt", None)
            from .http import HTTPFailure
            if (allow_model_unavailable and kind == 'gemini' and isinstance(error, HTTPFailure)
                    and model_unavailable_receipt(receipt)):
                # A lost ledger write still blocks another send via its started claim.
                self.ledger.model_unavailable(self.request_id, key, receipt)
                raise ModelUnavailable(receipt) from None
            if allow_unavailable and isinstance(receipt, dict) and (receipt.get("status") in {403, 404, 410} or
                    (kind == "download" and receipt.get("status") == 429)):
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
