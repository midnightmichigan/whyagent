"""WhyAgent — explanation stage.

This is the differentiator vs a plain research agent: it turns raw
claims into a structured, evidence-backed explanation with:
- a verdict (the direct answer to "why")
- ranked reasons, each with supporting sources and a confidence score
- alternatives that were considered and ranked lower (with why)
- counterfactuals: what evidence would change the answer
- explicit limitations (never hidden)
- a step-by-step reasoning trace (the "explain why" artifact)
Stdlib only.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .dispute import find_disputes
from .investigate import Investigation


def _confidence(n_sources: int, n_claims: int, live: bool) -> float:
    """Honest heuristic confidence in [0, 1].

    More independent sources + more claims = higher confidence.
    Fixture-only evidence is capped lower than live evidence.
    """
    base = min(0.95, 0.25 + 0.15 * n_sources + 0.08 * n_claims)
    if not live:
        base = min(base, 0.55)
    return round(base, 2)


@dataclass
class Reason:
    rank: int
    claim: str
    sources: list[dict]  # {title, url, source}
    confidence: float


@dataclass
class Explanation:
    question: str
    verdict: str
    reasons: list[Reason]
    alternatives: list[dict]  # lower-ranked claims + why ranked lower
    counterfactuals: list[str]
    limitations: list[str]
    overall_confidence: float
    trace: list[str] = field(default_factory=list)
    live_evidence: bool = False
    disputes: list[dict] = field(default_factory=list)  # cross-source disagreements

    def to_markdown(self) -> str:
        md = [f"# Why: {self.question}", ""]
        md.append(f"**Verdict:** {self.verdict}")
        md.append(f"**Overall confidence:** {self.overall_confidence:.0%} "
                  f"({'live' if self.live_evidence else 'fixture'} evidence)")
        md.append("")
        md.append("## Reasons (ranked)")
        for r in self.reasons:
            md.append(f"### {r.rank}. {r.claim}")
            md.append(f"Confidence: {r.confidence:.0%}")
            for s in r.sources:
                md.append(f"- [{s['title']}]({s['url']}) *({s['source']})*")
            md.append("")
        if self.alternatives:
            md.append("## Also considered (ranked lower)")
            for a in self.alternatives:
                md.append(f"- {a['claim']} — ranked lower because {a['why']}.")
            md.append("")
        if self.disputes:
            md.append("## Where sources disagree")
            for d in self.disputes:
                rf, op = d["refutes"], d["opposed"]
                md.append(f"- **{rf['text']}** ({rf['source']}) disputes "
                          f"**{op['text']}** ({op['source']}).")
            md.append("")
        md.append("## What would change this answer")
        for c in self.counterfactuals:
            md.append(f"- {c}")
        md.append("")
        md.append("## Limitations")
        for lim in self.limitations:
            md.append(f"- {lim}")
        md.append("")
        md.append("## Reasoning trace")
        for i, step in enumerate(self.trace, 1):
            md.append(f"{i}. {step}")
        return "\n".join(md)


def explain(inv: Investigation) -> Explanation:
    live = any(e.get("source") in ("wikipedia", "arxiv", "tavily")
               for e in inv.evidence)
    # Group claims: first 3 unique claims become ranked reasons; the rest
    # become alternatives (ranked lower for having single-source support).
    reasons: list[Reason] = []
    for i, claim in enumerate(inv.claims[:3], 1):
        srcs = [{"title": claim["title"], "url": claim["url"],
                 "source": claim["source"]}]
        reasons.append(Reason(
            rank=i, claim=claim["text"], sources=srcs,
            confidence=_confidence(len(srcs), 1, live)))
    alternatives = [
        {"claim": c["text"],
         "why": "it has single-source support in this evidence set"}
        for c in inv.claims[3:6]
    ]
    topic_words = inv.question.rstrip("?").lower()
    verdict = (
        f"The leading explanation is: {reasons[0].claim} "
        f"({len(inv.evidence)} evidence items reviewed, "
        f"{len(inv.claims)} unique claims extracted)."
        if reasons else
        "No evidence-backed explanation could be formed — the evidence "
        "set came back empty. See limitations."
    )
    counterfactuals = [
        "New peer-reviewed studies contradicting the top-ranked reason.",
        "First-party data (e.g. the asker's own analytics) disagreeing "
        "with the published evidence.",
        "A larger, more diverse evidence set shifting the ranking.",
    ]
    limitations = [
        "Evidence comes from public web sources, not first-party data.",
        "Confidence is a heuristic over source count and diversity, not "
        "a statistical guarantee.",
    ]
    disputes = find_disputes(inv.claims)
    if disputes:
        limitations.append(
            "Source disagreement is flagged by keyword heuristics, not "
            "human judgment — read the linked sources before trusting a "
            "dispute.")
    if not live:
        limitations.append(
            "SYNTHETIC FIXTURE EVIDENCE: this run used the offline demo "
            "corpus. Connect a live search backend for real answers.")
    if not inv.evidence:
        limitations.append(
            "The evidence set is empty (all backends degraded). "
            "No verdict should be trusted from this run.")
    trace = list(inv.trace)
    trace.append(f"Ranked {len(reasons)} reasons, "
                 f"{len(alternatives)} alternatives.")
    overall = _confidence(len({e.get("url") for e in inv.evidence}),
                          len(inv.claims), live)
    trace.append(f"Overall confidence {overall:.0%} "
                 f"({'live' if live else 'fixture'} evidence).")
    trace.append(f"Checked {len(inv.claims)} claims for cross-source "
                 f"disagreement: {len(disputes)} flagged.")
    return Explanation(
        question=inv.question,
        verdict=verdict,
        reasons=reasons,
        alternatives=alternatives,
        counterfactuals=counterfactuals,
        limitations=limitations,
        overall_confidence=overall,
        trace=trace,
        live_evidence=live,
        disputes=disputes,
    )
