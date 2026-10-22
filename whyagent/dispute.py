"""WhyAgent — source-disagreement detection.

Track 02's brief is "evidence-backed answers": when two sources make
opposing claims about the same topic, an honest explanation surfaces the
disagreement instead of averaging it away.

A pair of claims is flagged as a dispute when ALL of these hold:
- the claims come from DIFFERENT sources, and
- they are about the same topic (keyword Jaccard overlap >= threshold), and
- exactly one of them carries an EXPLICIT refutation marker
  ("debunked", "refuted", "myth", "no evidence that", ...).

Deliberately conservative: hedges like "however" or "some argue" are NOT
markers, and every surface that shows a dispute carries the caveat that
the detection is a keyword heuristic, not human judgment.
Stdlib only.
"""

from __future__ import annotations

import re

from .investigate import _keywords

# Explicit refutation language only — strong, unambiguous phrases.
_REFUTE_MARKERS = (
    "debunked",
    "debunking",
    "refuted",
    "refutes",
    "refutation",
    "myth",
    "no evidence",
    "contradicts",
    "contradicted",
    "contradiction",
    "fails to show",
    "not supported",
    "overstated",
    "exaggerated",
    "disproven",
    "disproves",
)

_OVERLAP_MIN = 0.35


def _has_refutation(text: str) -> bool:
    low = text.lower()
    return any(re.search(r"\b" + re.escape(m) + r"\b", low)
               for m in _REFUTE_MARKERS)


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def find_disputes(claims: list[dict],
                  overlap_min: float = _OVERLAP_MIN) -> list[dict]:
    """Flag opposing claim pairs across different sources.

    Each dispute is {"refutes": claim, "opposed": claim, "overlap": float}.
    A claim is used in at most one dispute (highest overlap wins) so the
    output stays readable.
    """
    keyed = [(c, set(_keywords(c.get("text", ""))),
              _has_refutation(c.get("text", "")))
             for c in claims]
    pairs = []
    for i in range(len(keyed)):
        for j in range(i + 1, len(keyed)):
            (ci, ki, ri), (cj, kj, rj) = keyed[i], keyed[j]
            if ri == rj:
                continue  # need exactly one refuting side
            if ci.get("source") == cj.get("source"):
                continue
            overlap = _jaccard(ki, kj)
            if overlap < overlap_min:
                continue
            refuting, opposed = (ci, cj) if ri else (cj, ci)
            pairs.append((overlap, i, j, refuting, opposed))
    pairs.sort(key=lambda p: p[0], reverse=True)
    used: set[int] = set()
    disputes = []
    for overlap, i, j, refuting, opposed in pairs:
        if i in used or j in used:
            continue
        used.add(i)
        used.add(j)
        disputes.append({"refutes": refuting, "opposed": opposed,
                         "overlap": round(overlap, 2)})
    return disputes
