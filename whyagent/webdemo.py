"""WhyAgent — single-page web demo UI.

Stdlib-only (`http.server` + `html`). Serves a question form, runs the
full explain pipeline on submit, and renders the verdict + ranked reasons
+ sources + alternatives + counterfactuals + limitations + reasoning trace
as one page. Deterministic fixture mode by default; the live checkbox
switches to the key-free live backends.

Run: python3 -m whyagent.webdemo [--port 8123] [--no-live]
Then open http://localhost:8123/
"""

from __future__ import annotations

import argparse
import html
import threading
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer

from whyagent import best_backend, explain, investigate
from whyagent.evidence import StubSearch
from whyagent.explain import Explanation

PAGE_CSS = """
body{font-family:system-ui,-apple-system,sans-serif;max-width:860px;margin:2rem auto;
padding:0 1rem;color:#1a1a1a;background:#fafafa}
.card{background:#fff;border:1px solid #e2e2e2;border-radius:10px;padding:1.2rem;margin:1rem 0}
h1{font-size:1.6rem} h2{font-size:1.15rem;margin-top:1.4rem}
.verdict{background:#f0f6ff;border-left:4px solid #2563eb;padding:0.8rem 1rem;border-radius:0 8px 8px 0}
.conf{display:inline-block;font-size:0.85rem;background:#eef2ff;color:#3730a3;
border-radius:999px;padding:0.15rem 0.7rem;margin-left:0.5rem}
.reason{border-left:3px solid #10b981;padding-left:0.9rem;margin:0.9rem 0}
.src{font-size:0.85rem;color:#555}
.lim{background:#fffbeb;border:1px solid #fde68a;border-radius:8px;padding:0.6rem 1rem}
.trace{font-family:ui-monospace,monospace;font-size:0.82rem;background:#111827;color:#d1d5db;
border-radius:8px;padding:0.8rem 1rem;white-space:pre-wrap}
input[type=text]{width:75%;padding:0.55rem;font-size:1rem;border:1px solid #ccc;border-radius:6px}
button{padding:0.55rem 1.2rem;font-size:1rem;border:0;border-radius:6px;background:#2563eb;color:#fff}
label{font-size:0.9rem;margin-left:0.8rem}
.badge{font-size:0.75rem;padding:0.1rem 0.55rem;border-radius:999px}
.badge.live{background:#dcfce7;color:#166534}.badge.fixture{background:#fef3c7;color:#92400e}
"""

FORM_HTML = """
<div class="card">
<h1>WhyAgent &#128161; — the agent that explains why</h1>
<p>Ask a hard <em>why</em> question. It plans sub-questions, gathers evidence
across multiple sources, and returns an evidence-backed explanation with a
reasoning trace.</p>
<form method="post" action="/ask">
<input type="text" name="question" maxlength="400"
 placeholder="Why do online shoppers abandon their carts?" required>
<button type="submit">Explain</button>
<label><input type="checkbox" name="live" value="1"> live evidence
(Wikipedia + arXiv, no key needed)</label>
</form>
</div>
"""

_history: list[Explanation] = []


def esc(s: object) -> str:
    return html.escape(str(s), quote=True)


def render_html(exp: Explanation) -> str:
    badge = ('<span class="badge live">LIVE EVIDENCE</span>' if exp.live_evidence
             else '<span class="badge fixture">FIXTURE DEMO</span>')
    parts = [
        "<!doctype html><html><head><meta charset='utf-8'>",
        f"<title>WhyAgent: {esc(exp.question)}</title>",
        f"<style>{PAGE_CSS}</style></head><body>",
        FORM_HTML,
        "<div class='card'>",
        f"<h2>Question</h2><p>{esc(exp.question)} {badge}",
        f"<span class='conf'>confidence {exp.overall_confidence:.0%}</span></p>",
        "<h2>Verdict</h2>",
        f"<div class='verdict'>{esc(exp.verdict)}</div>",
        "<h2>Reasons (ranked)</h2>",
    ]
    for r in exp.reasons:
        parts.append(
            f"<div class='reason'><b>{r.rank}. {esc(r.claim)}</b>"
            f"<span class='conf'>{r.confidence:.0%}</span><br>")
        for s in r.sources:
            parts.append(
                f"<span class='src'>&bull; <a href='{esc(s['url'])}' target='_blank'>"
                f"{esc(s['title'])}</a> ({esc(s['source'])})</span><br>")
        parts.append("</div>")
    if exp.alternatives:
        parts.append("<h2>Also considered (ranked lower)</h2><ul>")
        parts.extend(f"<li>{esc(a['claim'])} &mdash; ranked lower because "
                     f"{esc(a['why'])}.</li>" for a in exp.alternatives)
        parts.append("</ul>")
    if exp.disputes:
        parts.append("<h2>Where sources disagree</h2><ul>")
        for d in exp.disputes:
            rf, op = d["refutes"], d["opposed"]
            parts.append(f"<li><b>{esc(rf['text'])}</b> "
                         f"({esc(rf['source'])}) disputes "
                         f"<b>{esc(op['text'])}</b> "
                         f"({esc(op['source'])}).</li>")
        parts.append("</ul>")
    parts.append("<h2>What would change this answer</h2><ul>")
    parts.extend(f"<li>{esc(c)}</li>" for c in exp.counterfactuals)
    parts.append("</ul>")
    parts.append("<h2>Limitations</h2><div class='lim'><ul>")
    parts.extend(f"<li>{esc(l)}</li>" for l in exp.limitations)
    parts.append("</ul></div>")
    parts.append("<h2>Reasoning trace</h2><div class='trace'>")
    parts.extend(esc(f"{i}. {step}") for i, step in enumerate(exp.trace, 1))
    parts.append("</div></div>")
    if _history:
        parts.append("<div class='card'><h2>This session's investigations</h2><ul>")
        for h in reversed(_history[-10:]):
            parts.append(f"<li>{esc(h.question)} "
                         f"<span class='conf'>{h.overall_confidence:.0%}</span></li>")
        parts.append("</ul></div>")
    parts.append("</body></html>")
    return "\n".join(parts)


class Handler(BaseHTTPRequestHandler):
    allow_live = True

    def _send(self, body: str, code: int = 200) -> None:
        data = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self) -> None:  # noqa: N802
        self._send(f"<!doctype html><html><head><meta charset='utf-8'>"
                   f"<style>{PAGE_CSS}</style></head><body>{FORM_HTML}"
                   f"</body></html>")

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/ask":
            self._send("Not found", 404)
            return
        try:
            length = int(self.headers.get("Content-Length", 0))
        except ValueError:
            length = 0
        fields = urllib.parse.parse_qs(
            self.rfile.read(min(length, 65536)).decode("utf-8", "replace"))
        question = fields.get("question", [""])[0].strip()[:400]
        if not question:
            self._send("Missing question", 400)
            return
        want_live = self.allow_live and fields.get("live") == ["1"]
        searcher = best_backend() if want_live else StubSearch()
        exp = explain(investigate(question, searcher))
        _history.append(exp)
        if len(_history) > 20:
            del _history[:-20]
        self._send(render_html(exp))

    def log_message(self, *args) -> None:  # noqa: ANN002
        pass  # keep demo output clean


def serve(port: int = 8123, allow_live: bool = True) -> HTTPServer:
    Handler.allow_live = allow_live
    server = HTTPServer(("127.0.0.1", port), Handler)
    print(f"WhyAgent demo at http://localhost:{server.server_port}/ "
          f"(live={'on' if allow_live else 'off'}) — Ctrl-C to stop")
    server.serve_forever()
    return server


def run_in_thread(port: int = 0, allow_live: bool = False) -> HTTPServer:
    """For tests: start the server on an ephemeral port in a thread."""
    Handler.allow_live = allow_live
    server = HTTPServer(("127.0.0.1", port), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="WhyAgent web demo")
    ap.add_argument("--port", type=int, default=8123)
    ap.add_argument("--no-live", action="store_true",
                    help="disable the live-evidence checkbox (fixture only)")
    args = ap.parse_args(argv)
    try:
        serve(args.port, allow_live=not args.no_live)
    except KeyboardInterrupt:
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
