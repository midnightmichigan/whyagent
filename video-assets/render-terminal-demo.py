#!/usr/bin/env python3
"""Render the WhyAgent typescript recording to a paced terminal-demo MP4.

Offline, stdlib + PIL + ffmpeg only. The raw replay is ~18s of bursty
output (unwatchable); this renderer replays the same bytes with readable
pacing (~2 lines/s). Adapted from the PipelineSurgeon renderer.
"""
import re, subprocess, sys
from PIL import Image, ImageDraw, ImageFont

TS = "/home/hatch/workspace/bounty-hunts/open-agent-hackathon-2026/video-assets/terminal-demo.typescript"
OUT = "/home/hatch/workspace/bounty-hunts/open-agent-hackathon-2026/video-assets/terminal-demo-render.mp4"
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"

W, H = 1280, 720
COLS, ROWS = 100, 30
FPS = 30
BG = (13, 17, 23)
FG = (201, 209, 217)
GREEN = (63, 185, 80)
DIM = (139, 148, 158)

def load_text(path):
    raw = open(path, "rb").read()
    # strip ANSI CSI sequences (defensive; recording is mostly plain)
    raw = re.sub(rb"\x1b\[[0-9;?]*[a-zA-Z]", b"", raw)
    raw = re.sub(rb"\x1b[()][0-9A-B]", b"", raw)
    text = raw.decode("utf-8", "replace")
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    # drop the "Script started/done" wrappers and trailing empties
    lines = [l for l in lines if not l.startswith("Script started")]
    lines = [l for l in lines if not l.startswith("Script done")]
    while lines and not lines[-1].strip():
        lines.pop()
    return "\n".join(lines)

def wrap(text, cols):
    """Word-boundary wrap so words are never split mid-word on screen."""
    out = []
    for ln in text.split("\n"):
        while len(ln) > cols:
            cut = ln.rfind(" ", 0, cols)
            if cut <= 0:
                cut = cols  # no space: hard break (e.g. long URL)
            out.append(ln[:cut].rstrip())
            ln = ln[cut:].lstrip()
        out.append(ln)
    return out

text = load_text(TS)
lines = wrap(text, COLS)

font = ImageFont.truetype(FONT, 15)
cw, ch = font.getbbox("M")[2], font.getbbox("M")[3] + 6
PAD_X, PAD_Y = (W - COLS * cw) // 2, (H - ROWS * ch) // 2 + 20
print("char cell", cw, ch, "grid px", COLS * cw, ROWS * ch, "pad", PAD_X, PAD_Y, file=sys.stderr)
print("wrapped lines:", len(lines), file=sys.stderr)

def draw_frame(visible_lines):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    # header bar
    d.rectangle([0, 0, W, 34], fill=(22, 27, 34))
    d.text((20, 8), "WhyAgent — explainable investigation  (live evidence, replayed)", font=font, fill=DIM)
    y = PAD_Y
    for ln in visible_lines[-(ROWS):]:
        color = GREEN if ln.startswith("#") or ln.startswith("**") else FG
        d.text((PAD_X, y), ln[:COLS], font=font, fill=color)
        y += ch
    # footer hint
    d.text((20, H - 26), 'python3 -m whyagent.demo --live "Why do coral reefs bleach?"', font=font, fill=DIM)
    return img

def draw_title(title, sub):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    big = ImageFont.truetype(FONT, 54)
    mid = ImageFont.truetype(FONT, 22)
    d.text((W // 2 - 240, H // 2 - 80), title, font=big, fill=GREEN)
    d.text((W // 2 - 240, H // 2 + 10), sub, font=mid, fill=DIM)
    return img

# pacing: reveal ~2 lines per second (1 line per 0.5s ~ readable)
frames = []
title = draw_title("WhyAgent", "Open Agent Hackathon 2026 — explainable-investigation agent")
frames += [title] * (2 * FPS)

revealed = 0
frames_per_line = 15
while revealed < len(lines):
    revealed += 1
    vis = lines[:revealed]
    frames += [draw_frame(vis)] * frames_per_line
    if revealed == len(lines):
        break
# hold final frame 2s
frames += [frames[-1]] * (2 * FPS)

print("frames:", len(frames), "duration: %.1fs" % (len(frames) / FPS), file=sys.stderr)

proc = subprocess.Popen(
    ["ffmpeg", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
     "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
     "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20",
     "-movflags", "+faststart", OUT],
    stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)
for f in frames:
    proc.stdin.write(f.tobytes())
proc.stdin.close()
proc.wait()
print("wrote", OUT)
