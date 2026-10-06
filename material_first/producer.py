"""Durable single-run preparation wrapper for the replacement pipeline."""
from .engine import Producer, verify


class DurableProducer:
    def __init__(self, root, ledger, operations, authorize=None):
        self.root, self.ledger, self.operations, self.authorize = root, ledger, operations, authorize

    def prepare(self, request_id):
        for component in (self.operations.source, self.operations.gemini,
                          self.operations.search, self.operations.downloader):
            calls = getattr(component, 'calls', None)
            if calls is not None and str(calls.request_id) != str(request_id):
                raise ValueError('preparation component bound to another request')
        claim = self.ledger.claim_run(request_id)
        if claim['cached']:
            verify(self.root, claim['frozen'])
            return claim['frozen']
        try:
            if self.authorize is not None:
                self.authorize()
            request = claim['request']
            mode = request.get('visual_validation_mode', 'gemini')
            if mode not in {'metadata', 'gemini'}:
                raise ValueError('unsupported visual validation mode')
            self.operations.visual_validation_mode = mode
            frozen = Producer(self.root, self.operations).prepare(
                request['topic'], request['language'], request['seconds'])
            self.ledger.complete(request_id, frozen)
            return frozen
        except BaseException as error:
            try:
                self.ledger.reject(request_id, type(error).__name__)
            except Exception:
                pass
            raise
