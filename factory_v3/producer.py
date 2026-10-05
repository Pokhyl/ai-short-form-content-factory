"""Trusted availability-first producer; server-owned budgets, no caller approvals."""
import itertools
import re
from uuid import UUID
from .catalog import prepare
from .preflight import digest, verify_before_voice
from .preparation import ResourceUnavailable
from .providers import PROVIDERS
from .worker_adapters import DENSITY


def preparation_budgets(seconds):
    count = DENSITY[seconds]
    return {"research_search": 1, "source_fetch": 6, "gemini": count * 3 + 3,
            "download": count * 3, "metadata": 1, **{"search:" + p: count * 3 for p in PROVIDERS}}


def tokens(text):
    return set(re.findall(r"[a-z0-9]+", str(text).lower())) - {"a", "an", "the", "with", "of", "on", "in"}


def select_previews(unit, pools):
    # Soft metadata ordering; only actual pixel review can approve a candidate.
    options = []
    concepts = tokens(" ".join(unit["contract"]["must_show"]))
    for pool in pools:
        query_words = tokens(pool["query"]["query"])
        ranked = []
        for asset in pool["result"]["candidates"]:
            text = tokens(asset.get("description", ""))
            score = len(concepts & text) * 3 + len(query_words & text)
            candidate = dict(asset)
            candidate["search_context"] = {"query": pool["query"], "query_index": pool["query_index"],
                "receipt_id": digest(pool["result"]["receipt"])}
            ranked.append({"asset": candidate, "provider": candidate["provider"],
                           "query_index": pool["query_index"], "score": score})
        options.extend(sorted(ranked, key=lambda x: (-x["score"], x["asset"]["id"]))[:3])
    distinct = len({o["asset"]["id"] for o in options})
    size = min(3, distinct)
    if not size:
        return []
    best, best_key = None, None
    for selected in itertools.combinations(options, size):
        if len({s["asset"]["id"] for s in selected}) != size:
            continue
        # Keep provider and detailed-query coverage within the three-image budget.
        priority = (len({s["provider"] for s in selected}), len({s["query_index"] for s in selected}),
                    sum(s["score"] for s in selected))
        tie = tuple(sorted(s["asset"]["id"] for s in selected))
        key = (priority, tuple(reversed(tie)))
        if best_key is None or key > best_key:
            best, best_key = selected, key
    return [s["asset"] for s in sorted(best, key=lambda s: (s["query_index"], s["provider"], s["asset"]["id"]))]


class Producer:
    def __init__(self, root, ledger, research, gemini, search, downloader, authorize=None):
        self.authorize = authorize
        self.root, self.ledger = root, ledger
        self.research, self.gemini = research, gemini
        self.search, self.downloader = search, downloader

    def create(self, request_id, topic, language, seconds):
        request_id = str(UUID(str(request_id)))
        if language not in {"pl", "en", "ru", "uk"} or seconds not in DENSITY:
            raise ValueError("unsupported request")
        if not isinstance(topic, str) or not 1 <= len(topic.strip()) <= 300:
            raise ValueError("bounded topic required")
        return self.ledger.create(request_id, {"topic": topic.strip(), "language": language, "seconds": seconds},
                                  preparation_budgets(seconds))

    def prepare(self, request_id):
        for component in (self.research, self.gemini, self.search, self.downloader):
            calls = getattr(component, "calls", None)
            if calls is not None and str(calls.request_id) != str(request_id):
                raise ValueError("producer component bound to another request")
        claim = self.ledger.claim_run(request_id)
        if claim["cached"]:
            verify_before_voice(self.root, claim["frozen"])
            return claim["frozen"]
        request = claim["request"]
        try:
            if self.authorize is not None:
                self.authorize()
            sources = self.research.fetch(request["topic"], request["language"])
            outline = self.gemini.outline({**request, "sources": sources})
            catalog = {"units": outline["units"], "assets": [], "reviews": []}
            assets = {}
            for unit in outline["units"]:
                pools = []
                for index, query in enumerate(unit["queries"]):
                    for provider in sorted(PROVIDERS):
                        result = self.search.search(provider, query["query"], query["orientation"])
                        pools.append({"query_index": index, "query": query, "result": result})
                for candidate in select_previews(unit, pools):
                    try:
                        asset = self.downloader.download(candidate)
                    except ResourceUnavailable:
                        continue  # The attempted slot remains spent; no fourth download.
                    assets[asset["id"]] = asset
                    catalog["reviews"].append(self.gemini.review_photo(
                        self.root, unit, asset, outline["evidence"]))
            catalog["assets"] = list(assets.values())
            frozen = prepare(self.root, request["topic"], request["language"], request["seconds"],
                outline["evidence"], catalog, outline["required_fact_ids"],
                self.gemini.compose, self.gemini.review_script)
            verify_before_voice(self.root, frozen)
            self.ledger.complete(request_id, frozen)
            return frozen
        except BaseException as error:
            try:
                self.ledger.reject(request_id, type(error).__name__)
            except Exception:
                pass  # Existing unknown/started/failed state is already an immutable stop.
            raise
