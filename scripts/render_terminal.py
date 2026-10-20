"""Render real command output as a terminal-window PNG (headless Chrome, no extra dependencies).

    uv run python scripts/render_terminal.py --cmd "uv run python demos/05_redaction.py" \
        --in transcript.txt --out assets/screenshots/redaction.png [--max-lines 40]

Refuses to render text that looks like a real secret, so screenshots are safe to commit.
"""
import argparse
import html
import math
import re
import subprocess
import sys
import tempfile
from pathlib import Path

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
REAL_SECRET = re.compile(r"github_pat_[A-Za-z0-9_]{30,}|gh[pos]_[A-Za-z0-9]{36}|sm_[A-Za-z0-9]{30,}|AKIA[0-9A-Z]{16}")
FAKE_OK = ("AKIAIOSFODNN7EXAMPLE", "ghp_abcdefghijklmnopqrstuvwxyz0123456789")  # documented demo values
WIDTH, COLS, LINE_PX = 1040, 112, 21

PAGE = """<html><body style="margin:0;background:#0b1020">
<div style="width:{w}px;box-sizing:border-box;padding:24px;background:linear-gradient(135deg,#1e1b4b,#0b1020)">
<div style="background:#0f172a;border:1px solid #334155;border-radius:12px;overflow:hidden;box-shadow:0 10px 40px #0008">
<div style="background:#1e293b;padding:10px 14px;display:flex;gap:8px;align-items:center">
<span style="width:12px;height:12px;border-radius:6px;background:#ef4444"></span>
<span style="width:12px;height:12px;border-radius:6px;background:#f59e0b"></span>
<span style="width:12px;height:12px;border-radius:6px;background:#22c55e"></span>
<span style="margin-left:12px;color:#94a3b8;font:13px -apple-system,Helvetica,sans-serif">
{title}</span></div>
<pre style="margin:0;padding:16px 18px;color:#e2e8f0;font:14px/{lh}px ui-monospace,Menlo,monospace;\
white-space:pre-wrap;word-break:break-word"><span style="color:#22c55e">$</span> <span style="color:#f8fafc">{cmd}</span>
{body}</pre></div></div></body></html>"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cmd", required=True)
    ap.add_argument("--in", dest="src", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--max-lines", type=int, default=45)
    ap.add_argument("--title", default="zsh")
    a = ap.parse_args()

    text = Path(a.src).read_text().rstrip("\n")
    for fake in FAKE_OK:
        text = text.replace(fake, "X" * len(fake))  # check the rest, and never print the demo values as real
    if REAL_SECRET.search(text) or REAL_SECRET.search(a.cmd):
        sys.exit("refusing to render: output looks like it contains a real secret")
    text = Path(a.src).read_text().rstrip("\n")
    lines = text.splitlines()
    if len(lines) > a.max_lines:
        lines = lines[: a.max_lines - 1] + ["..."]
    shown = sum(max(1, math.ceil(len(line) / COLS)) for line in lines) + 1
    height = 48 + 38 + 32 + shown * LINE_PX + 2

    page = PAGE.format(w=WIDTH, title=html.escape(a.title), cmd=html.escape(a.cmd), lh=LINE_PX,
                       body=html.escape("\n".join(lines)))
    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False) as f:
        f.write(page)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--force-device-scale-factor=2",
                    f"--window-size={WIDTH},{height}", f"--screenshot={a.out}", f"file://{f.name}"],
                   check=True, capture_output=True)
    print("wrote", a.out)


if __name__ == "__main__":
    main()
