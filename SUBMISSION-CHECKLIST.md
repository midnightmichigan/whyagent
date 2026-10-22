# WhyAgent — submission checklist (Open Agent Hackathon 2026, Track 02)

## His taps (need Dakota)
- [ ] Register on the GenAI.Works platform (free account) — registration
      closes Oct 22, 2026, 23:59 UTC (hard deadline). Event page:
      https://hackathon.genai.works/event/open-agent-hackathon-2026
      NOTE 2026-10-11: the organizer's own LinkedIn post says "Registration
      closes October 20" — 2 days earlier than the event page. Treat Oct 20
      as the conservative internal target until re-verified.
- [ ] Form/join team of 1–5 on the platform (solo = team of 1 is allowed)
- [ ] Submit before Oct 27, 2026, 23:45 UTC (hard deadline)
- [ ] Optional: Zetaris / Meterless / Bright Data free-tier accounts if we
      spike the sponsor-tech integration (only if no card required)

## Build-side (agent-owned)
- [x] Core pipeline: evidence → investigate → explain (test_flow.py passing)
- [x] Deterministic offline demo (stub fixtures, clearly labeled synthetic)
- [x] Live key-free backends (Wikipedia + arXiv) with degrade-to-[]
- [x] Demo web UI (single page: explanation + reasoning trace) — whyagent/webdemo.py (tests assert render + escaping)
- [x] Screen-capture demo video against live evidence — 2026-10-11: re-recorded
      a REAL `script` capture of `python3 -m whyagent.demo --live "Why do coral
      reefs bleach?"` (exit 0, 46 lines, live Wikipedia evidence) and rendered
      video-assets/terminal-demo-render.mp4 (31s, 1280x720@30, H.264):
      title card + paced replay at ~2 lines/s + 2s end hold; renderer is
      video-assets/render-terminal-demo.py (offline PIL + ffmpeg, word-boundary
      wrap). All frames inspected by the builder (title/mid/end): clean, no
      truncated text, no overlapping labels, words never split mid-word.
- [x] Public repo pushed 2026-10-22 (machine $0 publish): https://github.com/midnightmichigan/whyagent
      (pre-approved per 2026-10-21 standing rule; Qloo precedent 2026-10-22 ~07:40)

## PRIZE CORRECTION (2026-10-22 ~08:40 EDT, official event page read verbatim)
Pool is now shown as "up to $20,000": Track 01 $3,700 (1st $1,600 / 2nd $1,200 /
3rd $900), Track 02 $3,700 (same split), Track 03 $3,600 (1st $1,500 / 2nd $1,200 /
3rd $900), Wildcard $2,000 (1st $1,000 / 2nd $600 / 3rd $400) = $13,000 cash +
in-kind "Best use of NVIDIA Nemotron" NVIDIA DGX Spark AI Supercomputer
(Founder's Edition, listed $4,699). (Original Oct 11 read: $4,350/$4,350/$4,300/
$2,000 = $15k cash — organizers lowered the cash splits.)

## Judging alignment (100 pts)
- Impact 30 — pick a demo question with a real user and real stakes
- Technical 20 — multi-source pipeline, failure isolation, honest confidence
- Innovation 15 — the explanation layer (counterfactuals + trace) is the novelty
- Demo 15 — live question → full explanation in one screen recording
- Product & UX 10 — clean web UI over the markdown/JSON core
- Sponsor tech 10 — optional Zetaris backend spike (nice-to-have, not required)
