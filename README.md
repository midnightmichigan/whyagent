# WhyAgent — Open Agent Hackathon 2026 entry (Track 02)

**Track:** 02 — "The Agent That Can Explain Why"
**Event:** GenAI.Works Open Agent Hackathon 2026 — fully online, Oct 22–27, 2026
**Prize:** up to $20,000 pool ($13,000 cash — Track 02 pays 1st $1,600 / 2nd $1,200 / 3rd $900; corrected 2026-10-16 from $15,000 cash on the official page)
**Event page:** https://hackathon.genai.works/event/open-agent-hackathon-2026
**PRIZE CORRECTION 2026-10-16:** the official page now shows reduced cash
tiers vs the Oct 11 verification — Track 01 $3,700 / Track 02 $3,700 /
Track 03 $3,600 / Wildcard $2,000 (= $13,000 cash; was $15,000). Still GO:
12 cash places, small pool.

An explainable investigation agent: ask it a hard "why" question, and it
plans sub-questions, gathers evidence across multiple sources, extracts
source-linked claims, and produces a structured explanation — verdict,
ranked reasons with confidence, alternatives considered, counterfactuals
("what would change this answer"), explicit limitations, and a full
reasoning trace.

This is the differentiator vs a plain research agent: Track 02's brief is
"investigate complex questions across multiple data sources, connect
findings, and produce evidence-backed answers or recommendations" — the
explanation layer (ranked reasons + confidence + counterfactuals +
limitations + trace) is the whole product, not a citation list.

## Why this fits

- Agent-shaped brief, exactly an AI builder's strength; judging weights
  Impact 30 / Technical 20 / Innovation 15 / Demo 15 / Product&UX 10 /
  Sponsor tech 10.
- 12 cash places across 4 tracks (broader payout than winner-take-all);
  ~1,200 registrants published (submission rate unknown — treat odds as
  modest, not terrible).
- $0 entry, fully online, solo allowed (teams of 1–5), 16+, no ID/video/
  in-person gates at entry.
- Zero-key local build: stub fixtures for deterministic demos, key-free
  live backends (Wikipedia + arXiv) for real evidence. Sponsor-tech
  integration (Zetaris/Meterless) is an optional upgrade, not a blocker.

## Repo layout

- `whyagent/evidence.py` — SearchBackend interface: StubSearch (fixture),
  WikipediaSearch + ArxivSearch (live, key-free, degrade-to-[]),
  MultiSearch (merge + dedupe + per-backend failure isolation)
- `whyagent/investigate.py` — question → sub-question plan → evidence →
  source-linked claim extraction (deduped)
- `whyagent/explain.py` — verdict + ranked reasons + confidence +
  alternatives + counterfactuals + limitations + reasoning trace
- `whyagent/demo.py` — CLI: `python3 -m whyagent.demo "Why ...?" [--live] [--json]`
- `whyagent/webdemo.py` — web demo UI: `python3 -m whyagent.webdemo`
  (http://localhost:8123/; question form + full explanation page)
- `test_flow.py` — end-to-end verification (deterministic, offline)

## Quickstart

```bash
python3 test_flow.py                    # all checks, offline
python3 -m whyagent.demo                # fixture demo (cart abandonment)
python3 -m whyagent.demo --live "Why do coral reefs bleach?"   # live evidence
```

## Build plan (before the Oct 22 build window)

1. ~~Grow the demo UI: single-page web view rendering the explanation +
   trace (judging: Demo 15, Product&UX 10).~~ DONE 2026-10-11 ~05:40 EDT:
   `whyagent/webdemo.py` (stdlib-only http.server; verdict + ranked reasons
   + sources + alternatives + counterfactuals + limitations + trace; live
   checkbox; HTML-escaped; 4 new tests, 24/24 passing).
1b. ~~Source-disagreement detection (judging: Innovation 15 — an "explain
    why" agent must surface when sources contradict each other instead of
    averaging it away).~~ DONE 2026-10-11 ~06:35 EDT: `whyagent/dispute.py`
    (conservative heuristic: different sources + keyword-overlap >= 0.35 +
    explicit refutation marker on exactly one side; a claim used at most
    once); wired into `explain()` (new `disputes` field, "## Where sources
    disagree" markdown section, heuristic-caveat limitation, trace line),
    `webdemo.py` (escaped render), `demo.py` (`--json` includes disputes);
    6 new checks, test_flow.py 30/30 PASSING; verified no false flags on
    the fixture corpus (section correctly absent when empty).
2. Optional sponsor-tech spike: Zetaris (fragmented-data) as an extra
   SearchBackend — only if their free tier needs no card (his call).
3. ~~Record the screen-capture demo against live evidence.~~ DONE 2026-10-11
   ~09:50 EDT: `video-assets/terminal-demo.typescript` + `.timing`
   recorded (100x30 xterm-256color, `python3 -m whyagent.demo --live
   "Why do coral reefs bleach?"` — 12 evidence items, 16 claims, verdict
   95% confidence live; dispute-trace line shows "0 flagged" cleanly);
   replayable via `scriptreplay video-assets/terminal-demo.timing
   video-assets/terminal-demo.typescript` — backbone footage for the
   Demo-15 screen recording.
4. Registration + submission — his taps (see SUBMISSION-CHECKLIST.md).

## Dates (all UTC, from the official event page)

- Registration closes: **Oct 22, 2026, 23:59 UTC** (hard deadline)
- Build window: Oct 22–27, 2026
- Submissions close: **Oct 27, 2026, 23:45 UTC** (hard deadline)
- Results: Nov 6, 2026
