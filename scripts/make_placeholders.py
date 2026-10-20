"""Create the placeholder PNGs for the Supermemory graph screenshots.

Replace each PNG in assets/screenshots/ with your own capture (same file name) and nothing else needs to change.
    uv run python scripts/make_placeholders.py
"""
import subprocess
import tempfile
from pathlib import Path
from xml.sax.saxutils import escape

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
OUT = Path(__file__).resolve().parent.parent / "assets" / "screenshots"
FONT = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif"

SHOTS = [  # file, title, what to capture
    ("supermemory-graph-memories.png", "Supermemory memory graph",
     "The graph view for one user namespace after the demo, with memories linked to the documents they came from."),
    ("supermemory-graph-profile.png", "Supermemory user profile",
     "The profile view for the same namespace: static facts and dynamic, recent context."),
    ("supermemory-graph-isolation.png", "Two namespaces, no overlap",
     "Two users side by side (demo 4), showing that one user's memories never appear in the other's graph."),
]


def svg(title, hint, filename):
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="900" viewBox="0 0 1600 900">
<rect width="1600" height="900" fill="#0f172a"/>
<rect x="40" y="40" width="1520" height="820" rx="24" fill="none" stroke="#f472b6" stroke-width="4" stroke-dasharray="18 14"/>
<g fill="none" stroke="#f472b6" stroke-width="3" opacity="0.5"><circle cx="560" cy="420" r="26"/><circle cx="800" cy="330" r="34"/>
<circle cx="1040" cy="430" r="26"/><circle cx="700" cy="560" r="20"/><circle cx="930" cy="580" r="22"/>
<path d="M584 410 L768 340 M834 340 L1016 420 M572 440 L690 545 M720 555 L910 575 M1030 452 L945 565 M815 360 L710 545"/></g>
<text x="800" y="170" text-anchor="middle" font-family="{FONT}" font-size="30" font-weight="700" letter-spacing="4" fill="#f472b6">PLACEHOLDER</text>
<text x="800" y="250" text-anchor="middle" font-family="{FONT}" font-size="56" font-weight="800" fill="#f8fafc">{escape(title)}</text>
<text x="800" y="715" text-anchor="middle" font-family="{FONT}" font-size="26" fill="#cbd5e1">{escape(hint)}</text>
<text x="800" y="775" text-anchor="middle" font-family="ui-monospace, Menlo, monospace" font-size="24" fill="#94a3b8">replace with assets/screenshots/{escape(filename)}</text>
</svg>"""


for filename, title, hint in SHOTS:
    with tempfile.NamedTemporaryFile("w", suffix=".svg", delete=False) as f:
        f.write(svg(title, hint, filename))
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--window-size=1600,900",
                    f"--screenshot={OUT / filename}", f"file://{f.name}"], check=True, capture_output=True)
    print("wrote", OUT / filename)
