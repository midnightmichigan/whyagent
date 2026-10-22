# DEV POST DRAFT — MLH x DEV Writing Challenge ($100/month, next pick ~early Nov)

**Status:** REVIEW-READY — his tap to publish on his DEV account (midnightmichigan).
**Template note (VERIFIED 2026-10-12 ~00:45 EDT):** the official MLH x DEV submission
template page itself mis-resolves on fetch (redirects to dev.to/terms), so verification
was done against the WINNING post from month 1 instead. Evidence: devteam's winner
announcement "Congrats to Our First MLH x DEV Writing Challenge Winner" names
@pritam_patra_429a25dedae6's OmniML post; that post opens with
"*This is a submission for the [MLH x DEV Writing Challenge](https://dev.to/t/wlhchallenge)*"
(a link to the official tag page "World's Largest Hackathon Writing Challenge").
**Tags (verified — DEV allows max 4):** `devchallenge`, `wlhchallenge`, `ai`, `python`
**Opener line (required, verbatim):** `*This is a submission for the [MLH x DEV Writing Challenge](https://dev.to/t/wlhchallenge)*`
**Sections to keep:** What we built / How it works / Demo-ish walkthrough / What we learned / What's next + partner tech named (winners name their partner technologies).
**Publishing = his tap on midnightmichigan.** Publish any time before the early-November pick.

---

*This is a submission for the [MLH x DEV Writing Challenge](https://dev.to/t/wlhchallenge)*

---

# WhyAgent: an AI agent that explains *why* — with receipts

**Team:** Midnight Michigan (solo) — building for the GenAI.Works Open Agent Hackathon 2026, Track 02: "The Agent That Can Explain Why."

Most "AI research agents" hand you an answer and a pile of links. The answer might be right, but you have no idea *why* it's right — which reasons mattered most, what was ruled out, what would change the answer, or where the agent is guessing. That's the gap WhyAgent closes: every answer comes with an explanation layer — a verdict, ranked reasons with confidence, alternatives considered, counterfactuals, explicit limitations, and a full reasoning trace back to the exact sources.

## The problem

"Why do coral reefs bleach?" A chatbot gives you a paragraph. A research agent gives you ten links. Neither tells you which evidence carried the most weight, whether two sources disagree, or how confident the conclusion actually is. For decisions that matter, the explanation *is* the product — the answer alone isn't.

## What we built

WhyAgent runs a three-stage pipeline, stdlib-only Python, no API keys needed:

1. **Plan** — the question becomes a set of sub-questions (e.g. "what triggers bleaching" / "is bleaching reversible" / "what does the latest research say"), each routed to the right evidence source.
2. **Investigate** — evidence is gathered from multiple live, key-free backends (Wikipedia for encyclopedic context, arXiv for scholarly work) and merged with dedupe by URL. Every claim extracted is linked to its exact source. If a backend fails, it degrades to an empty set with an honest note — the run never crashes and never fabricates sources.
3. **Explain** — the explanation layer: a verdict, ranked reasons with per-reason confidence, alternatives that were considered and ruled out, counterfactuals ("what would change this answer"), an explicit limitations line, and a reasoning trace showing the full path from question to conclusion.

A fourth feature turned out to be the most important: **disagreement detection.** When claims come from *different* sources, overlap on the same keywords, and one explicitly refutes the other, WhyAgent flags the dispute and shows it in its own "Where sources disagree" section — with a caveat that the flagging is heuristic, not human judgment. Hedging words ("however") deliberately do *not* trigger it. Honest uncertainty beats confident fiction.

There's a live smoke-tested example: asking "Why do coral reefs bleach?" against real Wikipedia + arXiv evidence returned 16 source-linked claims, a verdict at 95% confidence, ranked reasons, and zero false dispute flags.

## How it works (for builders)

- `evidence.py` — a `SearchBackend` interface: `StubSearch` (deterministic fixtures for tests), `WikipediaSearch` + `ArxivSearch` (live, key-free, degrade-to-empty), `MultiSearch` (merge + dedupe + per-backend failure isolation, so one dead API can't poison the whole run).
- `investigate.py` — sub-question planning + claim extraction with source links, deduped.
- `explain.py` — the explanation layer (verdict, ranked reasons, confidence, alternatives, counterfactuals, limitations, trace) plus `dispute.py` for source-disagreement detection.
- `demo.py` (CLI) and `webdemo.py` (a stdlib-only web UI that renders the full explanation page — verdict, reasons with citations, alternatives, limitations, trace — plus a JSON API). The UI is the screen-recordable artifact for the hackathon demo video.
- 30/30 automated checks green, offline-deterministic: the test suite pins the stub backends so every run is reproducible.

## What we learned

- **Failure isolation is a product feature, not plumbing.** When the sandbox network dropped mid-build, every backend degraded to `[]` cleanly and the report said "0 sources" instead of crashing or hallucinating. That honesty survived into the shipped design.
- **Tuning sentence-pickers has traps.** In a sibling project, a same-family decoy penalty fixed one question but broke two pinned tests — identifier boosting and question-identifier preference are in genuine tension. The rule we kept: never re-tune without the full eval + unit suite green.
- **Judges reward transparency.** The first MLH x DEV winner picked was an "explains what's happening under the hood" tool — this whole project is that idea applied to answers. Documentation quality is what the challenge scores; the honesty features (disputes, limitations, trace) are the story.

## What's next

The agent ships to the Open Agent Hackathon build window (Oct 22–27, 2026). Before that: optional sponsor-tech spike (Zetaris data layer), the ≤3-minute screen-capture demo video, and a fresh-history public repo. Longer term, the disagreement detector could grow from keyword heuristics to citation-graph comparison — but only if the eval suite keeps it honest.

**Try it:** repo + terminal demo are local for now; the public repo goes live at submission time. The web UI runs at `localhost:8123` — ask it any "why" question and watch it show its work.

---

*Published by Midnight Michigan. AI-assisted build, disclosed per DEV guidelines. All demo outputs shown are real runs against live public APIs; fixture data is labeled synthetic everywhere it surfaces.*
