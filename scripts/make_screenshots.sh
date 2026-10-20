#!/usr/bin/env bash
# Regenerate the README screenshots from REAL runs. Needs: Ollama running with gemma4, `temporal server start-dev`
# (with the UI, i.e. not --headless), a filled .env, and Google Chrome. Takes about 15 minutes (Supermemory is slow).
#   bash scripts/make_screenshots.sh
set -uo pipefail
cd "$(dirname "$0")/.."
OUT=assets/screenshots
TMP=$(mktemp -d)
REPO=${EVAL_REPO:-LondheShubham153/devboard-starter}
USER_ID="demo-$(date +%H%M%S)"
RUN="uv run --env-file .env"
mkdir -p "$OUT"

# shot <file-name> <command shown in the window> <max-lines> <actual command...>
shot() {
  local name=$1 shown=$2 max=$3; shift 3
  echo ">> $shown"
  "$@" > "$TMP/$name.txt" 2>&1
  grep -v -E "WARN|UserWarning|warnings.warn|_get_declaration|check_feature_enabled|^\s*$" "$TMP/$name.txt" > "$TMP/$name.clean" || true
  uv run python scripts/render_terminal.py --cmd "$shown" --in "$TMP/$name.clean" --out "$OUT/$name.png" --max-lines "$max"
}
ui() { uv run python scripts/capture_ui.py --url "$2" --out "$OUT/$1.png" "${@:3}"; }

shot 01-ollama-show        "ollama show gemma4" 25 ollama show gemma4
shot 02-offline-tests      "uv run pytest -q" 20 uv run pytest -q
shot 03-redaction-demo     "uv run python demos/05_redaction.py" 40 uv run python demos/05_redaction.py

$RUN python worker.py > "$TMP/worker.log" 2>&1 &
WORKER=$!
sleep 8
shot 04-ask                "uv run --env-file .env python ask.py $USER_ID \"what failed recently on $REPO?\"" 30 \
  $RUN python ask.py "$USER_ID" "what failed recently on $REPO?"

echo ">> waiting for the memory to become searchable ..."
$RUN python - "$USER_ID" <<'PY'
import asyncio, sys, time
from supermemory import AsyncSupermemory
async def main():
    sm, start = AsyncSupermemory(), time.time()
    while time.time() - start < 480:
        try:
            if (await sm.search(sys.argv[1], query="repo", search_mode="memories", limit=3)).results:
                return print(f"ready after {time.time() - start:.0f}s")
        except Exception:
            pass
        await asyncio.sleep(10)
    print("memory never became searchable")
asyncio.run(main())
PY
shot 05-ask-memory         "uv run --env-file .env python ask.py $USER_ID \"which failed run ids did you tell me about earlier?\"" 20 \
  $RUN python ask.py "$USER_ID" "which failed run ids did you tell me about earlier?"
kill $WORKER 2>/dev/null; wait $WORKER 2>/dev/null

shot 06-demo-memory        "uv run --env-file .env python demos/03_memory_basics.py" 30 $RUN python demos/03_memory_basics.py
shot 07-demo-isolation     "uv run --env-file .env python demos/04_tenant_isolation.py" 20 $RUN python demos/04_tenant_isolation.py
shot 08-demo-durability    "uv run --env-file .env python demos/01_durability.py" 40 $RUN python demos/01_durability.py
shot 09-demo-replay        "uv run python demos/02_replay.py" 20 uv run python demos/02_replay.py

# Temporal UI (the durability workflow shows the retried model call)
DUR=$(ls -t "$TMP"/08-demo-durability.txt >/dev/null 2>&1 && grep -o "demo-durability-[a-z0-9]*" "$TMP/08-demo-durability.txt" | head -1)
ui ui-workflows "http://localhost:8233/namespaces/default/workflows?query=ExecutionStatus%3D%22Completed%22" --size 1600x800
[ -n "$DUR" ] && ui ui-durability-history "http://localhost:8233/namespaces/default/workflows/$DUR" --size 1600x1300
echo "done. screenshots in $OUT"
