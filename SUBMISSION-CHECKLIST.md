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
- [ ] Fresh-history public repo (his per-item approval at publish time)

## Judging alignment (100 pts)
- Impact 30 — pick a demo question with a real user and real stakes
- Technical 20 — multi-source pipeline, failure isolation, honest confidence
- Innovation 15 — the explanation layer (counterfactuals + trace) is the novelty
- Demo 15 — live question → full explanation in one screen recording
- Product & UX 10 — clean web UI over the markdown/JSON core
- Sponsor tech 10 — optional Zetaris backend spike (nice-to-have, not required)
