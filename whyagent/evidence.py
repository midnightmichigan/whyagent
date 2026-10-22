"""WhyAgent — evidence stage.

SearchBackend interface + four implementations:
- StubSearch: deterministic local fixture corpus (offline demo / tests).
- WikipediaSearch: live key-free search via the public Wikipedia API
  (no signup, no key). Gracefully degrades to [] on network errors.
- ArxivSearch: live key-free paper search via the arXiv Atom API
  (no signup, no key). Gracefully degrades to [] on network errors.
- MultiSearch: merges evidence from several backends, dedupes by URL.
Stdlib only. Pattern proven on the Nebius DeepDive build (29/29 tests).
"""

from __future__ import annotations

import json
import re
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

# Synthetic fixture corpus for the offline demo. Clearly labeled wherever
# it surfaces in output.
_FIXTURES = {
    "cart abandonment": [
        {"title": "Unexpected shipping costs at checkout (fixture)",
         "url": "https://example.com/fixtures/shipping-costs",
         "snippet": "Shoppers report abandoning carts when shipping, taxes, "
                    "or fees added at the final step push the total well above "
                    "the advertised price. Extra-cost surprise is the most "
                    "cited reason in checkout surveys."},
        {"title": "Forced account creation (fixture)",
         "url": "https://example.com/fixtures/account-creation",
         "snippet": "Requiring shoppers to create an account before paying "
                    "adds friction. Guest-checkout options consistently show "
                    "lower abandonment in A/B tests."},
        {"title": "Long or confusing checkout forms (fixture)",
         "url": "https://example.com/fixtures/checkout-friction",
         "snippet": "Every additional form field increases drop-off. "
                    "Single-page checkouts with autofill and digital wallets "
                    "convert better than multi-step forms."},
        {"title": "Trust and security concerns (fixture)",
         "url": "https://example.com/fixtures/trust-signals",
         "snippet": "Missing trust badges, unclear return policies, and "
                    "unfamiliar payment pages make shoppers hesitate at the "
                    "payment step, especially first-time buyers."},
    ],
    "remote work productivity": [
        {"title": "Async communication norms (fixture)",
         "url": "https://example.com/fixtures/async-norms",
         "snippet": "Teams that default to written async updates report "
                    "fewer interruptions and deeper focus blocks than "
                    "meeting-heavy teams."},
        {"title": "Home office setup quality (fixture)",
         "url": "https://example.com/fixtures/home-office",
         "snippet": "Ergonomic setup and a dedicated workspace correlate "
                    "with self-reported productivity in remote surveys."},
    ],
}


def _overlap(query: str, text: str) -> int:
    qtokens = set(re.findall(r"[a-z]{3,}", query.lower()))
    ttokens = set(re.findall(r"[a-z]{3,}", text.lower()))
    return len(qtokens & ttokens)


class SearchBackend:
    def search(self, query: str, max_results: int = 3) -> list[dict]:
        raise NotImplementedError


class StubSearch(SearchBackend):
    """Deterministic fixture search. Always returns >= 1 item."""

    def search(self, query: str, max_results: int = 3) -> list[dict]:
        scored = []
        for topic, items in _FIXTURES.items():
            for item in items:
                s = _overlap(query, topic + " " + item["title"] + " " + item["snippet"])
                scored.append((s, item))
        scored.sort(key=lambda p: p[0], reverse=True)
        hits = [dict(item, source="stub-fixture") for _, item in scored[:max_results]]
        if not hits or scored[0][0] == 0:
            hits = [{"title": f"No fixture match for: {query[:60]} (fixture)",
                     "url": "https://example.com/fixtures/no-match",
                     "snippet": "No fixture covers this query; connect a live "
                                "search backend for real results.",
                     "source": "stub-fixture"}]
        return hits


class WikipediaSearch(SearchBackend):
    """Live key-free search via the public Wikipedia API."""

    API = "https://en.wikipedia.org/w/api.php"
    UA = "WhyAgent/0.1 (hackathon explainable-agent demo; stdlib urllib)"

    def _get(self, params: dict) -> dict:
        qs = urllib.parse.urlencode(params)
        req = urllib.request.Request(
            f"{self.API}?{qs}",
            headers={"User-Agent": self.UA, "Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=20) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def search(self, query: str, max_results: int = 3) -> list[dict]:
        try:
            found = self._get({
                "action": "query", "format": "json", "list": "search",
                "srsearch": query, "srlimit": max_results,
                "srnamespace": 0, "srwhat": "text"})
            titles = [h["title"]
                      for h in found.get("query", {}).get("search", [])]
            if not titles:
                return []
            pages = self._get({
                "action": "query", "format": "json", "prop": "extracts",
                "exsentences": 2, "explaintext": 1, "exintro": 1,
                "titles": "|".join(titles)})
            by_title = {p.get("title"): p
                        for p in pages.get("query", {}).get("pages", {}).values()}
            out = []
            for t in titles:
                p = by_title.get(t)
                if not p or "missing" in p:
                    continue
                out.append({
                    "title": p["title"],
                    "url": ("https://en.wikipedia.org/wiki/"
                            + p["title"].replace(" ", "_")),
                    "snippet": p.get("extract", "")[:400],
                    "source": "wikipedia"})
            return out[:max_results]
        except Exception as e:
            print(f"[wikipedia] live search failed ({type(e).__name__}); "
                  f"degrading to []", file=sys.stderr)
            return []


class ArxivSearch(SearchBackend):
    """Live key-free paper search via the public arXiv Atom API."""

    API = "https://export.arxiv.org/api/query"
    UA = "WhyAgent/0.1 (hackathon explainable-agent demo; stdlib urllib)"
    NS = "{http://www.w3.org/2005/Atom}"

    def _fetch(self, query: str, max_results: int) -> bytes:
        params = {"search_query": f"all:{query}",
                  "start": "0", "max_results": str(max_results),
                  "sortBy": "relevance", "sortOrder": "descending"}
        req = urllib.request.Request(
            f"{self.API}?{urllib.parse.urlencode(params)}",
            headers={"User-Agent": self.UA, "Accept": "application/atom+xml"})
        with urllib.request.urlopen(req, timeout=20) as resp:
            return resp.read()

    def search(self, query: str, max_results: int = 3) -> list[dict]:
        try:
            root = ET.fromstring(self._fetch(query, max_results))
            out = []
            for entry in root.findall(f"{self.NS}entry"):
                title = (entry.findtext(f"{self.NS}title") or "").strip()
                link = (entry.findtext(f"{self.NS}id") or "").strip()
                summary = (entry.findtext(f"{self.NS}summary") or "").strip()
                if not title or not link:
                    continue
                out.append({"title": re.sub(r"\s+", " ", title),
                            "url": link.replace("http://", "https://", 1),
                            "snippet": re.sub(r"\s+", " ", summary)[:400],
                            "source": "arxiv"})
                if len(out) >= max_results:
                    break
            return out
        except Exception as e:
            print(f"[arxiv] live search failed ({type(e).__name__}); "
                  f"degrading to []", file=sys.stderr)
            return []


class MultiSearch(SearchBackend):
    """Merges evidence from several backends, in order.

    Each backend gets up to `per_backend` results; duplicates by URL are
    dropped. If one backend fails/degrades, the others still contribute.
    """

    def __init__(self, backends: list[SearchBackend], per_backend: int = 2):
        self.backends = backends
        self.per_backend = per_backend

    def search(self, query: str, max_results: int = 6) -> list[dict]:
        out, seen = [], set()
        for backend in self.backends:
            try:
                hits = backend.search(query, max_results=self.per_backend)
            except Exception as e:  # noqa: BLE001
                print(f"[multisearch] backend {type(backend).__name__} failed "
                      f"({type(e).__name__}); skipping", file=sys.stderr)
                continue
            for hit in hits:
                url = hit.get("url", "")
                if url and url in seen:
                    continue
                seen.add(url)
                out.append(hit)
                if len(out) >= max_results:
                    return out
        return out


def best_backend() -> SearchBackend:
    """Preference order: Wikipedia (live, key-free) + arXiv > Stub."""
    return MultiSearch([WikipediaSearch(), ArxivSearch()], per_backend=2)
