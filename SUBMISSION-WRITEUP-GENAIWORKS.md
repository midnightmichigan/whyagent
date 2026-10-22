# WhyAgent — GenAI.Works platform submission writeup (draft, ready to paste)
**Track:** 02 — The Agent That Can Explain Why
**Team:** Midnight Michigan (solo)
**Repo:** https://github.com/midnightmichigan/whyagent
**Demo video:** video-assets/terminal-demo-render.mp4 (upload to the platform or link)

## One-liner
WhyAgent is an AI agent that explains *why* — every answer ships with a verdict, ranked evidence-backed reasons, alternatives considered, counterfactuals, and a full reasoning trace back to the exact sources.

## The problem
"Why do coral reefs bleach?" A chatbot gives you a paragraph. A research agent gives you ten links. Neither tells you which evidence carried the most weight, whether two sources disagree, or how confident the conclusion actually is. For decisions that matter — medical, financial, operational — the explanation *is* the product. The answer alone isn't.

## What we built
WhyAgent runs a three-stage pipeline in stdlib-only Python, with zero API keys required:

1. **Plan** — the question becomes a set of sub-questions ("what triggers bleaching" / "is bleaching reversible" / "what does the latest research say"), each routed to the right evidence source.
2. **Investigate** — evidence is gathered from multiple live, key-free backends (Wikipedia for encyclopedic context, arXiv for scholarly work), merged with dedupe by URL. Every claim extracted is linked to its exact source. If a backend fails, it degrades to an empty set with an honest note — the run never crashes and never fabricates sources.
3. **Explain** — the explanation layer: a verdict, ranked reasons with per-reason confidence, alternatives considered and ruled out, counterfactuals ("what would change this answer"), an explicit limitations line, and a reasoning trace showing the full path from question to conclusion.

The most important feature is **source-disagreement detection**: when claims come from *different* sources, overlap on the same keywords, and one explicitly refutes the other, WhyAgent flags the dispute in its own "Where sources disagree" section — with a caveat that the flagging is heuristic, not human judgment. Hedging words like "however" deliberately do *not* trigger it. Honest uncertainty beats confident fiction.

A clean web UI (single page: explanation + reasoning trace) sits on top of the markdown/JSON core, so a non-technical user gets the full explanation in one screen.

## How we built it
- Pure Python standard library — no dependencies, no API keys, no cloud services.
- Live evidence from public APIs: Wikipedia (api.php) and the arXiv Atom API, each wrapped in the same degrade-to-empty contract with failure isolation per backend.
- Deterministic offline demo path: stub fixtures, clearly labeled synthetic everywhere they surface, pinned by 30 automated checks (`python3 test_flow.py` — 30/30 passing).
- Demo video rendered offline from a real `script` terminal capture of a live run, word-boundary wrapped, frames inspected for clean text.

## Challenges
- **Honest confidence**: most agents report 99% on everything. We calibrate per-reason confidence from claim multiplicity across independent sources, cap the range, and print the limitations line on every run.
- **Disagreement without noise**: keyword overlap alone produces false flags. The detector requires three conditions at once (different sources + keyword overlap ≥ 0.35 + an explicit refutation marker) and each claim is used at most once — zero false flags on the fixture corpus.
- **Failure honesty**: every backend can vanish (rate limits, outages). The degrade-to-[] contract means the output says what it could not verify instead of inventing sources.

## Accomplishments
- End-to-end live run on "Why do coral reefs bleach?": 16 claims from real Wikipedia + arXiv evidence, 95% verdict confidence, zero fabricated sources.
- 30/30 automated checks passing, including XSS-escaping tests on the web UI and network-failure degradation tests.
- Full demo: CLI (markdown/JSON) + web UI + rendered screen-capture video, all reproducible from the repo in seconds.

## What we learned
The explanation layer is where agents earn trust: users don't need *more* sources, they need to know which reasons mattered, what was ruled out, and where the agent is guessing. And the hardest engineering problem wasn't retrieval — it was saying "I don't know" correctly.

## What's next
- Dispute detector: move from keyword heuristics to claim-level entailment.
- Sponsor-tech backends (Zetaris / Meterless) behind the same backend interface.
- Per-domain calibration: confidence weights tuned per evidence type (encyclopedic vs scholarly vs practitioner).
