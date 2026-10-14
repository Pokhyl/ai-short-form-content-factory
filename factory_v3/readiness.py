"""Check the credential route without credentials or a provider request."""
from .credential_http import GATEWAY
from .http import HTTPFailure, JSONHTTP


class GatewayUnavailable(RuntimeError):
    """Admission failed; no preparation or provider claim has been created."""


def check_gateway(http=None):
    try:
        (http or JSONHTTP()).request("POST", GATEWAY, {}, {}, timeout=5)
    except HTTPFailure as error:
        if error.receipt["status"] in (401, 403):
            return error.receipt["status"]
        raise GatewayUnavailable("credential route is not ready") from None
    except Exception:
        raise GatewayUnavailable("credential route is not ready") from None
    raise GatewayUnavailable("credential route did not require authentication")
