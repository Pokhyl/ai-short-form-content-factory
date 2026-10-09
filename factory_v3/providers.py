"""Official bounded photo search; actual media review is a later independent gate."""
import html
import json
import re
from urllib.parse import urlencode, urlsplit, quote
from .preflight import digest


PROVIDERS = {"pixabay", "pexels", "wikimedia"}
MEDIA_HOSTS = {"pixabay": {"pixabay.com", "cdn.pixabay.com"},
               "pexels": {"images.pexels.com"},
               "wikimedia": {"upload.wikimedia.org", "thumb.wikimedia.org"}}


def safe_url(url, hosts):
    parsed = urlsplit(url)
    if parsed.scheme != "https" or parsed.hostname not in hosts or parsed.username or parsed.password or parsed.port not in (None, 443):
        raise ValueError("unexpected provider URL")
    return url


def media_url(provider, url):
    return safe_url(url, MEDIA_HOSTS[provider])


def clean_text(value):
    return html.unescape(re.sub(r"<[^>]*>", " ", str(value or ""))).strip()


def commons_license(name):
    value = clean_text(name)
    normalized = value.upper().replace("_", " ").replace("-", " ")
    if normalized in {"PUBLIC DOMAIN", "PDM", "PUBLIC DOMAIN MARK"}:
        return "Public Domain"
    if re.fullmatch(r"CC0(?: 1\.0)?", normalized):
        return "CC0"
    if re.fullmatch(r"CC BY SA(?: [1-4]\.0)?", normalized):
        return "CC BY-SA"
    if re.fullmatch(r"CC BY(?: [1-4]\.0)?", normalized):
        return "CC BY"
    raise ValueError("unsupported Wikimedia license")


def commons_license_url(metadata, license_name):
    value = metadata.get("LicenseUrl", {}).get("value")
    if value:
        return safe_url(value, {"creativecommons.org", "www.creativecommons.org", "commons.wikimedia.org"})
    # Commons' public-domain records often have no LicenseUrl. Use the
    # extension's documented default only with an explicit PD declaration.
    # Missing links on a copyrighted/unknown record are still ineligible.
    if (license_name == "Public Domain"
            and metadata.get("Copyrighted", {}).get("value") == "False"
            and metadata.get("NonFree", {}).get("value") != "True"):
        return "https://commons.wikimedia.org/wiki/Help:Public_domain"
    raise ValueError("missing Wikimedia license URL")


class ProviderQueryUnavailable(RuntimeError):
    def __init__(self, state, receipt):
        self.state, self.receipt = state, receipt
        super().__init__('saved provider query is pending or ambiguous; no repeat')


class ProviderCache:
    def __init__(self, postgres):
        self.postgres = postgres

    def run(self, identity, provider, send):
        key = digest(identity)
        try:
            claim = self.postgres._call("SELECT factory_v3.claim_provider_cache(%s,%s)", (key, provider))
        except Exception as error:
            # Only the cache's explicit no-repeat refusal is optional. Database
            # outages, identity mismatches and budget failures remain errors.
            if (getattr(error,'sqlstate',None) == 'P0001' and
                getattr(getattr(error,'diag',None),'message_primary',None) == 'provider query pending or ambiguous'):
                saved=self.postgres._call("SELECT jsonb_build_object('provider',provider,'state',state,'receipt',receipt) FROM factory_v3.provider_cache WHERE identity_hash=%s",(key,))
                if saved and saved['provider']==provider and saved['state'] in {'started','unknown'}:
                    raise ProviderQueryUnavailable(saved['state'],saved['receipt']) from None
            raise
        if claim["cached"]:
            return claim["receipt"]
        try:
            receipt = send()
            self.postgres._call("SELECT factory_v3.finish_provider_cache(%s,%s::jsonb)",
                                (key, json.dumps(receipt, allow_nan=False)))
            return receipt
        except BaseException as error:
            try:
                self.postgres._call("SELECT factory_v3.fail_provider_cache(%s,%s::jsonb)",
                                    (key, json.dumps(getattr(error, "receipt", None))))
            except Exception:
                pass
            raise


def candidates(provider, body):
    found = []
    if provider == "pixabay":
        entries = body.get("hits", [])[:8]
    elif provider == "pexels":
        entries = body.get("photos", [])[:8]
    else:
        entries = sorted(body.get("query", {}).get("pages", {}).values(),
                         key=lambda entry: entry.get("index", 100000))[:20]
    for entry in entries:
        try:
            if provider == "pixabay":
                if entry.get("type") != "photo":
                    continue
                author = str(entry["user"])
                asset = {"id": "pixabay:" + str(entry["id"]), "provider": provider,
                    "provider_asset_id": str(entry["id"]), "source_url": safe_url(entry["pageURL"], {"pixabay.com"}),
                    "author": author, "author_url": "https://pixabay.com/users/" + quote(author, safe="") + "-" + str(entry["user_id"]) + "/",
                    "license": "Pixabay Content License", "license_original": "Pixabay Content License",
                    "license_url": "https://pixabay.com/service/license-summary/",
                    "media_url": entry.get("fullHDURL") or entry["largeImageURL"],
                    "width": entry["imageWidth"], "height": entry["imageHeight"],
                    "description": entry.get("tags", ""), "attribution": "Photo by " + author + " on Pixabay"}
            elif provider == "pexels":
                author = str(entry["photographer"])
                asset = {"id": "pexels:" + str(entry["id"]), "provider": provider,
                    "provider_asset_id": str(entry["id"]), "source_url": safe_url(entry["url"], {"www.pexels.com", "pexels.com"}),
                    "author": author, "author_url": safe_url(entry["photographer_url"], {"www.pexels.com", "pexels.com"}),
                    "license": "Pexels License", "license_original": "Pexels License",
                    "license_url": "https://www.pexels.com/license/",
                    "media_url": entry["src"]["large2x"], "width": entry["width"], "height": entry["height"],
                    "description": entry.get("alt", ""), "attribution": "Photo by " + author + " on Pexels",
                    "provider_link": "https://www.pexels.com"}
            else:
                info = entry["imageinfo"][0]
                if info.get("mime") not in {"image/jpeg", "image/png", "image/webp"}:
                    continue
                metadata = info["extmetadata"]
                raw_license = metadata["LicenseShortName"]["value"]
                license_name = commons_license(raw_license)
                author = clean_text(metadata["Artist"]["value"])
                asset = {"id": "wikimedia:" + str(entry["pageid"]), "provider": provider,
                    "provider_asset_id": str(entry["pageid"]),
                    "source_url": safe_url(info["descriptionurl"], {"commons.wikimedia.org"}),
                    "author": author, "license": license_name, "license_original": clean_text(raw_license),
                    "license_url": commons_license_url(metadata, license_name),
                    "media_url": info.get("thumburl") or info["url"],
                    "width": info.get("thumbwidth", info["width"]), "height": info.get("thumbheight", info["height"]),
                    "description": clean_text(metadata.get("ImageDescription", {}).get("value", entry.get("title", ""))),
                    "attribution": author + " / Wikimedia Commons / " + clean_text(raw_license)}
            media_url(provider, asset["media_url"])
            if not asset["author"].strip() or int(asset["width"]) <= 0 or int(asset["height"]) <= 0:
                continue
            asset["media_type"] = "photo"
            asset["source_metadata"] = entry
            found.append(asset)
        except (KeyError, IndexError, TypeError, ValueError):
            continue  # Ineligible metadata never becomes an approved photograph.
    return found


class PhotoSearch:
    def __init__(self, calls, cache, http, credentials, credential_scope):
        if not credential_scope:
            raise ValueError("non-secret provider credential scope required")
        self.calls, self.cache, self.http = calls, cache, http
        self.credentials, self.scope = credentials, credential_scope

    def search(self, provider, query, orientation="portrait"):
        if provider not in PROVIDERS or orientation not in {"portrait", "landscape", "all"}:
            raise ValueError("unsupported provider or orientation")
        if not isinstance(query, str) or not 1 <= len(query.strip()) <= 100:
            raise ValueError("bounded nonempty photo query required")
        query = query.strip()
        if provider == "pixabay":
            url = "https://pixabay.com/api/"
            params = {"q": query, "per_page": 8, "safesearch": "true", "image_type": "photo",
                      "orientation": {"portrait": "vertical", "landscape": "horizontal", "all": "all"}[orientation], "lang": "en"}
        elif provider == "pexels":
            url = "https://api.pexels.com/v1/search"
            params = {"query": query, "per_page": 8}
            if orientation != "all":
                params["orientation"] = orientation
        else:
            url = "https://commons.wikimedia.org/w/api.php"
            params = {"action": "query", "generator": "search", "gsrsearch": query + " filetype:bitmap",
                "gsrnamespace": 6, "gsrlimit": 20, "prop": "imageinfo",
                "iiprop": "url|size|mime|extmetadata", "iiurlwidth": 1600, "format": "json"}
        identity = {"provider": provider, "endpoint": url, "params": params, "credential_scope": self.scope}
        def send():
            request_params = dict(params)
            headers = {}
            if provider == "pixabay":
                request_params["key"] = self.credentials(provider)
            elif provider == "pexels":
                headers["Authorization"] = self.credentials(provider)
            if provider != "wikimedia" and not (request_params.get("key") or headers.get("Authorization")):
                raise ValueError("provider credential unavailable")
            return self.http.request_receipt("GET", url + "?" + urlencode(request_params),
                                             headers=headers, timeout=30)
        def fetch():
            from .http import InvalidHTTPJSON
            try:
                return self.cache.run(identity, provider, send)
            except ProviderQueryUnavailable as error:
                return {'adapter_status':'unavailable','cache_state':error.state,'failure_receipt':error.receipt}
            except InvalidHTTPJSON as error:
                # A completed empty search response contributes no candidates.
                # Preserve the actual failure, do not cache it or retry the read.
                if error.receipt.get('status') == 200 and error.receipt.get('body_bytes') == 0:
                    return {'adapter_status':'unavailable','failure_receipt':error.receipt}
                raise
        receipt = self.calls.run("search:" + digest(identity), "search:" + provider, identity, fetch)
        if receipt.get('adapter_status') == 'unavailable':
            return {"identity":identity,"receipt":receipt,"candidates":[]}
        return {"identity": identity, "receipt": receipt, "candidates": candidates(provider, receipt["body"])}
