"""Screenshot a web page (the Temporal UI) with headless Chrome.

    uv run python scripts/capture_ui.py --url http://localhost:8233/namespaces/default/workflows \
        --out assets/screenshots/ui-workflows.png [--size 1600x1000] [--wait 12000]
"""
import argparse
import subprocess
from pathlib import Path

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

ap = argparse.ArgumentParser()
ap.add_argument("--url", required=True)
ap.add_argument("--out", required=True)
ap.add_argument("--size", default="1600x1000")
ap.add_argument("--wait", type=int, default=12000, help="ms of virtual time to let the single-page app load")
a = ap.parse_args()

Path(a.out).parent.mkdir(parents=True, exist_ok=True)
subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--force-device-scale-factor=1",
                f"--window-size={a.size.replace('x', ',')}", f"--virtual-time-budget={a.wait}",
                f"--screenshot={a.out}", a.url], check=True, capture_output=True)
print("wrote", a.out)
