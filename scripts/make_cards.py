"""Generate assets/banner.svg and assets/cards/*.svg. Run: uv run python scripts/make_cards.py"""
from pathlib import Path
from xml.sax.saxutils import escape

ASSETS = Path(__file__).resolve().parent.parent / "assets"
FONT = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif"
MONO = "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"

CARDS = [  # file, role, title, line1, line2, accent
    ("gemma-ollama", "THE BRAIN", "Gemma 4 on Ollama", "Local 8B model with native tool", "calling and thinking. No API key.", "#38bdf8"),
    ("google-adk", "THE AGENT LOOP", "Google ADK", "Tools, sessions and the model loop.", "Each call becomes a Temporal activity.", "#34d399"),
    ("temporal", "THE DURABILITY", "Temporal", "Retries, timeouts, event history, replay.", "Kill the worker; the run resumes.", "#a78bfa"),
    ("supermemory", "THE MEMORY", "Supermemory", "One namespace per user, extracted", "memories and a maintained profile.", "#f472b6"),
    ("github-actions", "THE DATA", "GitHub Actions API", "Read-only: runs, jobs, log tails.", "Repo allowlist enforced in code.", "#fbbf24"),
    ("uv-python", "THE TOOLCHAIN", "uv and Python 3.12", "One `uv sync`, pinned versions,", "offline tests that need no keys.", "#fb923c"),
]


def card(role, title, l1, l2, accent):
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="400" height="160" viewBox="0 0 400 160" role="img" aria-label="{escape(title)}: {escape(role.lower())}">
  <rect x="1" y="1" width="398" height="158" rx="14" fill="#0f172a" stroke="#1e293b" stroke-width="2"/>
  <rect x="1" y="1" width="8" height="158" rx="4" fill="{accent}"/>
  <text x="28" y="38" font-family="{FONT}" font-size="12" font-weight="700" letter-spacing="2" fill="{accent}">{escape(role)}</text>
  <text x="28" y="76" font-family="{FONT}" font-size="26" font-weight="700" fill="#f8fafc">{escape(title)}</text>
  <text x="28" y="108" font-family="{FONT}" font-size="14" fill="#cbd5e1">{escape(l1)}</text>
  <text x="28" y="130" font-family="{FONT}" font-size="14" fill="#cbd5e1">{escape(l2)}</text>
</svg>
"""


def banner():
    boxes = [("GitHub Actions", "failed run", "#fbbf24"), ("Agent", "Gemma 4 + ADK", "#34d399"),
             ("Temporal", "durable steps", "#a78bfa"), ("Memory", "Supermemory", "#f472b6")]
    parts = []
    for i, (name, sub, color) in enumerate(boxes):
        x = 90 + i * 280
        parts.append(f'<rect x="{x}" y="430" width="220" height="100" rx="16" fill="#0f172a" stroke="{color}" stroke-width="2.5"/>'
                     f'<text x="{x + 110}" y="473" text-anchor="middle" font-family="{FONT}" font-size="24" font-weight="700" fill="#f8fafc">{name}</text>'
                     f'<text x="{x + 110}" y="503" text-anchor="middle" font-family="{FONT}" font-size="16" fill="{color}">{sub}</text>')
        if i < len(boxes) - 1:
            parts.append(f'<path d="M{x + 226} 480 H{x + 274}" stroke="#64748b" stroke-width="3" marker-end="url(#arrow)"/>')
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="640" viewBox="0 0 1280 640" role="img" aria-label="github-actions-ai-agent banner">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#0b1020"/><stop offset="1" stop-color="#1e1b4b"/></linearGradient>
    <linearGradient id="title" x1="0" x2="1"><stop offset="0" stop-color="#38bdf8"/><stop offset="0.5" stop-color="#a78bfa"/><stop offset="1" stop-color="#f472b6"/></linearGradient>
    <marker id="arrow" markerWidth="10" markerHeight="10" refX="8" refY="5" orient="auto"><path d="M0 0 L10 5 L0 10 z" fill="#64748b"/></marker>
  </defs>
  <rect width="1280" height="640" fill="url(#bg)"/>
  <circle cx="1120" cy="90" r="220" fill="#7c3aed" opacity="0.12"/><circle cx="140" cy="600" r="260" fill="#0ea5e9" opacity="0.10"/>
  <text x="90" y="150" font-family="{MONO}" font-size="20" fill="#94a3b8" letter-spacing="3">DURABLE  /  MEMORY-EQUIPPED  /  READ-ONLY</text>
  <text x="90" y="235" font-family="{FONT}" font-size="84" font-weight="800" fill="url(#title)">github-actions-ai-agent</text>
  <text x="90" y="300" font-family="{FONT}" font-size="30" fill="#e2e8f0">An agent that triages failed GitHub Actions runs,</text>
  <text x="90" y="342" font-family="{FONT}" font-size="30" fill="#e2e8f0">remembers you, and survives a crashed worker.</text>
  <text x="90" y="395" font-family="{FONT}" font-size="18" fill="#94a3b8">Gemma 4 on Ollama  ·  Google ADK  ·  Temporal  ·  Supermemory</text>
  {''.join(parts)}
</svg>
"""


if __name__ == "__main__":
    (ASSETS / "cards").mkdir(parents=True, exist_ok=True)
    (ASSETS / "banner.svg").write_text(banner())
    for name, role, title, l1, l2, accent in CARDS:
        (ASSETS / "cards" / f"{name}.svg").write_text(card(role, title, l1, l2, accent))
    print("wrote banner.svg and", len(CARDS), "cards")
