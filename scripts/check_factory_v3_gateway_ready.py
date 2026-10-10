"""Run inside the app container: probe gateway authentication, never a provider.

An n8n healthz200 can precede webhook activation. Accept only authentication
rejection on the exact unauthenticated POST route. Never retry here.
"""
import urllib.request
import urllib.error


def check():
    request = urllib.request.Request(
        'http://ai-short-form-n8n:5678/webhook/factory-v3-internal-provider',
        data=b'{}', headers={'Content-Type': 'application/json'}, method='POST')
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            status = response.status
    except urllib.error.HTTPError as error:
        status = error.code
    if status not in (401, 403):
        raise RuntimeError('Gateway authentication route not ready: HTTP ' + str(status))
    return status


if __name__ == '__main__':
    print('Gateway authentication route ready: HTTP', check())
