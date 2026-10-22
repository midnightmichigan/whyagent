"""WhyAgent — end-to-end demo.

Runs the full pipeline on a question and prints the explanation as
markdown (+ JSON with --json). Defaults to the stub backend for a
deterministic offline demo; use --live for the key-free live backends.
Stdlib only.
"""

from __future__ import annotations

import argparse
import json
import sys

from whyagent import best_backend, explain, investigate
from whyagent.evidence import StubSearch

DEFAULT_QUESTION = "Why do online shoppers abandon their carts?"


def run(question: str, live: bool = False):
    searcher = best_backend() if live else StubSearch()
    inv = investigate(question, searcher)
    return explain(inv)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="WhyAgent explainable-investigation demo")
    ap.add_argument("question", nargs="?", default=DEFAULT_QUESTION)
    ap.add_argument("--live", action="store_true",
                    help="use live key-free backends (Wikipedia + arXiv)")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of markdown")
    args = ap.parse_args(argv)

    exp = run(args.question, live=args.live)
    if args.json:
        print(json.dumps({
            "question": exp.question,
            "verdict": exp.verdict,
            "overall_confidence": exp.overall_confidence,
            "live_evidence": exp.live_evidence,
            "reasons": [
                {"rank": r.rank, "claim": r.claim,
                 "confidence": r.confidence, "sources": r.sources}
                for r in exp.reasons],
            "alternatives": exp.alternatives,
            "counterfactuals": exp.counterfactuals,
            "disputes": [
                {"refutes": {"claim": d["refutes"]["text"],
                             "source": d["refutes"]["source"],
                             "url": d["refutes"]["url"],
                             "title": d["refutes"]["title"]},
                 "opposed": {"claim": d["opposed"]["text"],
                             "source": d["opposed"]["source"],
                             "url": d["opposed"]["url"],
                             "title": d["opposed"]["title"]},
                 "overlap": d["overlap"]}
                for d in exp.disputes],
            "limitations": exp.limitations,
            "trace": exp.trace,
        }, indent=2))
    else:
        print(exp.to_markdown())
    return 0


if __name__ == "__main__":
    sys.exit(main())
