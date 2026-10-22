"""WhyAgent — investigation stage.

Turns a "why" question into a plan of sub-questions, gathers evidence for
each from the search backend, and extracts source-linked claims.
Stdlib only.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from .evidence import SearchBackend

_STOP = frozenset(
    "a an the and or of to in on for with is are was were be by as at it its "
    "this that these those do does did why what how when where which who whom "
    "whose can could should would will shall may might must have has had not "
    "no yes if then than so such into out up down over under about from".split()
)


def _keywords(question: str) -> list[str]:
    words = re.findall(r"[a-z]{3,}", question.lower())
    seen, out = set(), []
    for w in words:
        if w not in _STOP and w not in seen:
            seen.add(w)
            out.append(w)
    return out


def plan_subquestions(question: str, max_q: int = 4) -> list[str]:
    """Heuristic decomposition of a why-question into investigable parts."""
    kws = _keywords(question)
    topic = " ".join(kws[:6]) or question.strip()
    qs = [
        f"What are the documented causes of {topic}?",
        f"How common or measurable is {topic}?",
        f"What evidence exists for the leading explanations of {topic}?",
    ]
    if len(kws) >= 2:
        qs.append(f"How do {' and '.join(kws[:2])} interact in {topic}?")
    return qs[:max_q]


_SENT_SPLIT = re.compile(r"(?<=[.!?])\s+")


def _claims_from_snippet(snippet: str) -> list[str]:
    claims = []
    for sent in _SENT_SPLIT.split(snippet.strip()):
        sent = sent.strip()
        if len(sent) >= 24 and re.search(r"[a-zA-Z]", sent):
            claims.append(sent[:280])
    return claims


@dataclass
class Investigation:
    question: str
    subquestions: list[str]
    evidence: list[dict] = field(default_factory=list)
    claims: list[dict] = field(default_factory=list)  # {text, source, url}
    trace: list[str] = field(default_factory=list)


def investigate(question: str, searcher: SearchBackend,
                per_q: int = 3) -> Investigation:
    """Run the full investigation pipeline for a why-question."""
    inv = Investigation(question=question, subquestions=[])
    inv.trace.append(f"Q: {question}")
    inv.subquestions = plan_subquestions(question)
    inv.trace.append(
        f"Planned {len(inv.subquestions)} sub-questions from "
        f"{len(_keywords(question))} topic keywords.")
    for sq in inv.subquestions:
        hits = searcher.search(sq, max_results=per_q)
        inv.trace.append(f"Sub-question '{sq[:60]}...' -> {len(hits)} evidence items.")
        for h in hits:
            inv.evidence.append({**h, "subquestion": sq})
            for claim in _claims_from_snippet(h.get("snippet", "")):
                inv.claims.append({
                    "text": claim,
                    "source": h.get("source", "unknown"),
                    "url": h.get("url", ""),
                    "title": h.get("title", ""),
                })
    # Dedupe claims by normalized text, keeping the first (best-ranked) source.
    seen, uniq = set(), []
    for c in inv.claims:
        key = re.sub(r"\W+", " ", c["text"].lower()).strip()
        if key and key not in seen:
            seen.add(key)
            uniq.append(c)
    inv.claims = uniq
    inv.trace.append(
        f"Extracted {len(inv.claims)} unique claims from "
        f"{len(inv.evidence)} evidence items.")
    return inv
