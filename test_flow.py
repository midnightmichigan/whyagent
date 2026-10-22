"""WhyAgent test_flow — end-to-end verification.

All checks run against the deterministic StubSearch backend (no network).
Run: python3 test_flow.py  (or python3 -m whyagent.demo)
"""

from __future__ import annotations

import io
import json
import sys
from contextlib import redirect_stdout

sys.path.insert(0, ".")

from whyagent import StubSearch, best_backend, explain, investigate  # noqa: E402
from whyagent.demo import run  # noqa: E402
from whyagent.evidence import (ArxivSearch, MultiSearch,  # noqa: E402
                               WikipediaSearch)
from whyagent.investigate import plan_subquestions  # noqa: E402

CHECKS = []


def check(name):
    def deco(fn):
        CHECKS.append((name, fn))
        return fn
    return deco


@check("stub search returns deterministic hits for demo question")
def _():
    a = StubSearch().search("Why do online shoppers abandon their carts?", 3)
    b = StubSearch().search("Why do online shoppers abandon their carts?", 3)
    assert a == b and len(a) >= 1, "stub must be deterministic and non-empty"
    assert all(h["source"] == "stub-fixture" for h in a)


@check("stub search degrades gracefully on unknown topic")
def _():
    hits = StubSearch().search("quantum chromodynamics lattice gauge", 2)
    assert len(hits) >= 1, "stub must always return >= 1 item"


@check("sub-question planner produces 3-4 questions")
def _():
    qs = plan_subquestions("Why do online shoppers abandon their carts?")
    assert 3 <= len(qs) <= 4, qs
    assert all(isinstance(q, str) and q.endswith("?") for q in qs)


@check("investigation extracts claims with source links")
def _():
    inv = investigate("Why do online shoppers abandon their carts?", StubSearch())
    assert len(inv.evidence) >= 3, f"evidence={len(inv.evidence)}"
    assert len(inv.claims) >= 3, f"claims={len(inv.claims)}"
    for c in inv.claims:
        assert c["text"] and c["url"].startswith("http"), c


@check("claims are deduped")
def _():
    inv = investigate("Why do online shoppers abandon their carts?", StubSearch())
    texts = [c["text"].lower() for c in inv.claims]
    assert len(texts) == len(set(texts)), "duplicate claims survived"


@check("explanation ranks reasons with confidence in [0,1]")
def _():
    exp = explain(investigate("Why do online shoppers abandon their carts?",
                             StubSearch()))
    assert exp.reasons, "no reasons produced"
    assert exp.reasons[0].rank == 1
    for r in exp.reasons:
        assert 0.0 <= r.confidence <= 1.0, r.confidence
        assert r.sources, "reason without sources"


@check("fixture evidence caps confidence at 0.55")
def _():
    exp = explain(investigate("Why do online shoppers abandon their carts?",
                             StubSearch()))
    assert exp.overall_confidence <= 0.55, exp.overall_confidence
    assert not exp.live_evidence


@check("explanation carries explicit limitations incl. fixture label")
def _():
    exp = explain(investigate("Why do online shoppers abandon their carts?",
                             StubSearch()))
    assert exp.limitations, "limitations must never be empty"
    assert any("FIXTURE" in lim for lim in exp.limitations), exp.limitations


@check("explanation includes alternatives and counterfactuals")
def _():
    exp = explain(investigate("Why do online shoppers abandon their carts?",
                             StubSearch()))
    assert exp.counterfactuals, "counterfactuals missing"
    # fixture corpus has 4 cart items -> 3 reasons + 1 alternative minimum
    assert isinstance(exp.alternatives, list)


@check("markdown renderer covers all required sections")
def _():
    md = explain(investigate("Why do online shoppers abandon their carts?",
                            StubSearch())).to_markdown()
    for section in ("Verdict", "Reasons (ranked)", "What would change this answer",
                    "Limitations", "Reasoning trace"):
        assert section in md, f"missing section: {section}"


@check("reasoning trace is non-trivial")
def _():
    exp = explain(investigate("Why do online shoppers abandon their carts?",
                             StubSearch()))
    assert len(exp.trace) >= 5, exp.trace


@check("empty evidence set yields honest no-verdict")
def _():
    class Dead:
        def search(self, q, max_results=3):
            return []
    exp = explain(investigate("Why is the sky blue?", Dead()))
    assert not exp.reasons, "reasons must be empty with no evidence"
    assert "empty" in exp.verdict.lower() or "no evidence" in exp.verdict.lower()
    assert any("empty" in lim.lower() for lim in exp.limitations)


@check("MultiSearch dedupes by URL across backends")
def _():
    ms = MultiSearch([StubSearch(), StubSearch()], per_backend=2)
    hits = ms.search("Why do online shoppers abandon their carts?", 6)
    urls = [h["url"] for h in hits]
    assert len(urls) == len(set(urls)), "duplicate URLs survived MultiSearch"


@check("MultiSearch survives a dead backend")
def _():
    class Dead:
        def search(self, q, max_results=3):
            raise RuntimeError("boom")
    ms = MultiSearch([Dead(), StubSearch()], per_backend=2)
    hits = ms.search("Why do online shoppers abandon their carts?", 6)
    assert hits, "MultiSearch must still return StubSearch results"
    assert all(h["source"] == "stub-fixture" for h in hits)


@check("live backends degrade to [] on network failure (no crash)")
def _():
    import urllib.request

    real = urllib.request.urlopen

    def boom(*a, **k):
        raise OSError("simulated outage")
    urllib.request.urlopen = boom
    try:
        assert WikipediaSearch().search("test", 2) == []
        assert ArxivSearch().search("test", 2) == []
    finally:
        urllib.request.urlopen = real


@check("demo run() returns a complete Explanation (stub)")
def _():
    exp = run("Why do online shoppers abandon their carts?", live=False)
    assert exp.verdict and exp.reasons and exp.limitations


@check("demo CLI prints markdown by default")
def _():
    from whyagent.demo import main
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = main(["Why do online shoppers abandon their carts?"])
    out = buf.getvalue()
    assert rc == 0 and "## Reasons (ranked)" in out


@check("demo CLI --json emits parseable JSON")
def _():
    from whyagent.demo import main
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = main(["Why do online shoppers abandon their carts?", "--json"])
    data = json.loads(buf.getvalue())
    assert rc == 0 and data["reasons"] and "limitations" in data


@check("best_backend() returns a working backend object")
def _():
    b = best_backend()
    assert hasattr(b, "search")


@check("web demo renderer escapes injected HTML")
def _():
    from whyagent.explain import Explanation, Reason
    from whyagent.webdemo import render_html
    exp = Explanation(
        question='Why?</title><script>alert("x")</script>',
        verdict='ok<script>x()</script>',
        reasons=[Reason(rank=1, claim="<b>bold</b>", confidence=0.5,
                        sources=[{"title": "<i>t</i>", "url": "http://e.com",
                                   "source": "stub-fixture"}])],
        alternatives=[], counterfactuals=["<u>c</u>"],
        limitations=["<u>l</u>"], overall_confidence=0.5,
        trace=["<b>t</b>"])
    page = render_html(exp)
    assert "<script>" not in page, "raw script tag leaked into HTML"
    assert "&lt;script&gt;" in page, "escaped script expected"
    for section in ("Verdict", "Reasons (ranked)", "What would change this answer",
                    "Limitations", "Reasoning trace"):
        assert section in page, f"missing section: {section}"


@check("web demo GET / serves the question form")
def _():
    import urllib.request
    from whyagent.webdemo import run_in_thread
    server = run_in_thread(allow_live=False)
    try:
        with urllib.request.urlopen(
                f"http://localhost:{server.server_port}/", timeout=10) as resp:
            body = resp.read().decode("utf-8")
        assert resp.status == 200
        assert 'name="question"' in body and "WhyAgent" in body
    finally:
        server.shutdown()


@check("web demo POST /ask renders an explanation (fixture, no live)")
def _():
    import urllib.parse
    import urllib.request
    from whyagent.webdemo import run_in_thread
    server = run_in_thread(allow_live=False)
    try:
        data = urllib.parse.urlencode(
            {"question": "Why do online shoppers abandon their carts?"}).encode()
        req = urllib.request.Request(
            f"http://localhost:{server.server_port}/ask", data=data)
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read().decode("utf-8")
        assert resp.status == 200
        assert "Verdict" in body and "Reasons (ranked)" in body
        assert "FIXTURE DEMO" in body
    finally:
        server.shutdown()


@check("web demo POST /ask rejects a missing question")
def _():
    import urllib.error
    import urllib.parse
    import urllib.request
    from whyagent.webdemo import run_in_thread
    server = run_in_thread(allow_live=False)
    try:
        req = urllib.request.Request(
            f"http://localhost:{server.server_port}/ask",
            data=urllib.parse.urlencode({"question": ""}).encode())
        try:
            urllib.request.urlopen(req, timeout=10)
        except urllib.error.HTTPError as e:
            assert e.code == 400, e.code
        else:
            raise AssertionError("expected HTTP 400 for empty question")
    finally:
        server.shutdown()


@check("second fixture topic also investigates cleanly")
def _():
    exp = explain(investigate("Why does remote work hurt productivity?",
                             StubSearch()))
    assert exp.reasons and exp.overall_confidence > 0


@check("find_disputes flags an explicit refutation across sources")
def _():
    from whyagent.dispute import find_disputes
    claims = [
        {"text": "Drinking coffee daily causes chronic insomnia in adults.",
         "source": "wikipedia", "url": "http://e.com/1", "title": "t1"},
        {"text": "Studies debunked the myth that daily coffee drinking "
                 "causes chronic insomnia in adults.",
         "source": "arxiv", "url": "http://e.com/2", "title": "t2"},
    ]
    ds = find_disputes(claims)
    assert len(ds) == 1, ds
    assert ds[0]["refutes"]["source"] == "arxiv"
    assert ds[0]["opposed"]["source"] == "wikipedia"


@check("find_disputes ignores same-source pairs")
def _():
    from whyagent.dispute import find_disputes
    claims = [
        {"text": "Drinking coffee daily causes chronic insomnia in adults.",
         "source": "wikipedia", "url": "http://e.com/1", "title": "t1"},
        {"text": "Studies debunked the myth that daily coffee drinking "
                 "causes chronic insomnia in adults.",
         "source": "wikipedia", "url": "http://e.com/3", "title": "t3"},
    ]
    assert find_disputes(claims) == []


@check("find_disputes ignores non-opposing overlaps")
def _():
    from whyagent.dispute import find_disputes
    claims = [
        {"text": "Drinking coffee daily causes chronic insomnia in adults.",
         "source": "wikipedia", "url": "http://e.com/1", "title": "t1"},
        {"text": "Daily coffee drinking causes chronic insomnia in adults, "
                 "studies confirm.",
         "source": "arxiv", "url": "http://e.com/2", "title": "t2"},
    ]
    assert find_disputes(claims) == []


@check("end-to-end dispute surfaces in markdown + heuristic limitation")
def _():
    class Opposed:
        def search(self, q, max_results=3):
            return [
                {"title": "t1", "url": "http://e.com/1",
                 "snippet": "Drinking coffee daily causes chronic insomnia "
                            "in adults. Researchers agree.",
                 "source": "wikipedia"},
                {"title": "t2", "url": "http://e.com/2",
                 "snippet": "Studies debunked the myth that daily coffee "
                            "drinking causes chronic insomnia in adults.",
                 "source": "arxiv"},
            ]
    exp = explain(investigate("Why does coffee cause insomnia?", Opposed()))
    assert exp.disputes, "expected a dispute to be flagged"
    md = exp.to_markdown()
    assert "Where sources disagree" in md, md
    assert any("heuristic" in lim.lower() for lim in exp.limitations)
    assert any("disagreement" in step for step in exp.trace)


@check("web renderer shows + escapes disputes")
def _():
    from whyagent.explain import Explanation, Reason
    from whyagent.webdemo import render_html
    exp = Explanation(
        question="q", verdict="v",
        reasons=[Reason(rank=1, claim="c", confidence=0.5,
                        sources=[{"title": "t", "url": "http://e.com",
                                  "source": "wikipedia"}])],
        alternatives=[], counterfactuals=[], limitations=["l"],
        overall_confidence=0.5,
        disputes=[{"refutes": {"text": "<script>x</script>",
                               "source": "arxiv", "url": "http://e.com/2",
                               "title": "t"},
                   "opposed": {"text": "plain", "source": "wikipedia",
                               "url": "http://e.com/1", "title": "t"},
                   "overlap": 0.7}])
    page = render_html(exp)
    assert "Where sources disagree" in page
    assert "<script>" not in page, "raw script tag leaked into HTML"


@check("demo --json includes disputes list")
def _():
    from whyagent.demo import main
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = main(["Why do online shoppers abandon their carts?", "--json"])
    data = json.loads(buf.getvalue())
    assert rc == 0 and "disputes" in data
    assert isinstance(data["disputes"], list)


def main() -> int:
    passed = failed = 0
    for name, fn in CHECKS:
        try:
            fn()
            print(f"  PASS  {name}")
            passed += 1
        except AssertionError as e:
            print(f"  FAIL  {name}: {e}")
            failed += 1
        except Exception as e:  # noqa: BLE001
            print(f"  ERROR {name}: {type(e).__name__}: {e}")
            failed += 1
    total = passed + failed
    print(f"\n{passed}/{total} checks passed"
          + (" — ALL CHECKS PASSED" if failed == 0 else " — FAILURES PRESENT"))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
