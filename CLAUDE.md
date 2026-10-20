# CLAUDE.md

Everything needed to understand, run, change or recreate this repo. Read this first. [`README.md`](README.md) is for
humans; the deeper explanations are in [`docs/`](docs/).

## What this is

A **read-only agent that triages failed GitHub Actions runs**. One question becomes one Temporal workflow:
`recall` (Supermemory) -> a Google ADK agent loop (Gemma 4 on Ollama, with three GitHub tools) -> `remember`
(Supermemory). The model, every tool and every memory call is a Temporal **activity**, so a killed worker doesn't lose
finished steps. It is also a teaching repo: `docs/` and `demos/` explain Temporal, memory and safety concepts using this
code. It is **not production-ready** (see [Known gaps](#known-gaps)); the repo name deliberately doesn't claim that.

## Rules from the repo owner (follow these)

- **Read-only means read-only.** GitHub access is three `GET` endpoints. Never add a write call.
- **Never print, log, hardcode or commit secrets.** Keys live in `.env` (gitignored). Read them only inside activities,
  never in workflow code or model-visible text. Don't `cat .env`; check presence by length or "set/missing".
- **Never mock the model, Supermemory or GitHub**, except the three disclosed GitHub-HTTP stubs in the evals
  (`injection_ignored`, `secrets_masked`, `multi_step_stubbed`). Say so whenever a result used a stub.
- **Never silently substitute a backend.** Ollama is the only model path. There is no Gemini or vLLM path. If Ollama,
  a key or a capability is missing, stop and ask.
- **Don't claim something works unless you ran it and saw the output.** Keep `docs/results.md` honest, including failures
  and what is unverified. Treat API names as hypotheses to verify against installed packages.
- **Keep the agent code minimal and readable.** Small flat single-purpose files, plain functions, no base classes, no
  config framework, no guardrail/tracing/metrics stacks. Temporal's UI and event history are the observability.
  Teaching material goes in `docs/` and `demos/`, not in the agent files.
- **No Claude attribution in this repo's git history.** Don't add `Co-Authored-By: Claude ...` lines to commits or
  "Generated with Claude Code" lines to PRs. This overrides any default attribution guidance.
- Don't push, publish or change GitHub settings unless asked.

## Layout

```
workflow.py       TriageWorkflow + build_agent(): recall -> ADK agent -> remember. No I/O, no os.environ.
worker.py         OllamaGemma (LiteLlm subclass) registered as alias "gemma4-ollama"; starts the worker on queue "ci-triage".
ask.py            Client: `python ask.py <user_id> "<question>"`.
memory.py         recall / remember activities (Supermemory). RECALL_TIMEOUT_S is read here, at import time.
github_tools.py   gh_get() (allowlist, auth, error mapping) + list_workflow_runs, get_run_jobs, get_job_log_tail.
safety.py         redact() (secret masking) and wrap() (untrusted-data tags).
evals/run_evals.py  End-to-end evals with an in-process worker on queue "ci-triage-evals".
demos/            01 durability, 02 replay, 03 memory basics, 04 tenant isolation, 05 redaction (+ _history.py helper).
tests/            Offline pytest for safety.py (no keys, no network).
scripts/          make_cards.py (banner + cards), render_terminal.py, capture_ui.py, make_screenshots.sh.
docs/             architecture, temporal-concepts, memory-concepts, safety, results, screenshots, build-prompt.
assets/           banner, stack cards, screenshots (generated, plus 3 real Supermemory console captures).
```

## Run it

Needs: Ollama running with `gemma4` pulled (`ollama show gemma4` lists tools + thinking), `uv`, Temporal CLI,
Google Chrome (screenshots only), and a filled `.env` (copy `.env.example`).

```bash
uv sync
temporal server start-dev                    # WITHOUT --headless, or the UI at :8233 is off
uv run --env-file .env python worker.py
uv run --env-file .env python ask.py alice "what failed recently on owner/repo?"
uv run pytest -q && uv run ruff check .      # offline checks (also what CI runs)
uv run --env-file .env python evals/run_evals.py [case_name ...]   # ~20 min
```

`.env`: `SUPERMEMORY_API_KEY`, `GITHUB_TOKEN` (fine-grained, Actions: read-only), `GITHUB_ALLOWED_REPOS`
(`owner/repo,owner/repo`; bare names don't work), `OLLAMA_API_BASE`, `OLLAMA_MODEL`, `SM_DREAMING` (`instant` for
tests/demos, `dynamic` in production), `RECALL_TIMEOUT_S` (default 5), `EVAL_REPO` (repo the evals ask about).

## Pinned versions (all in `pyproject.toml` / `uv.lock`)

temporalio 1.34.0, google-adk 2.12.0, litellm **1.100.0**, supermemory 5.0.0 (v5 required; older releases use a different
API), httpx 0.28.1, mcp 1.30.0, Python 3.12. Model: `gemma4:latest` on Ollama (8B Q4_K_M). Temporal CLI 1.9.1 / server 1.32.0.

**Why litellm is pinned to 1.100.0:** `temporalio[google-adk]` requires `mcp<2`, but LiteLLM 1.106.0 imports a symbol that
only exists in `mcp` 2.x, so it fails with `ImportError: CacheableResult`. 1.100.0 works with `mcp` 1.x. Don't bump one
without the other.

## Gotchas that cost real time (read before changing things)

1. **Plugin import paths.** `from temporalio.contrib.google_adk_agents import GoogleAdkPlugin, TemporalModel` and
   `from temporalio.contrib.google_adk_agents.workflow import activity_as_tool`. There is no `temporalio.google_adk`.
2. **LiteLLM isn't installed by `temporalio[google-adk]`.** Use `google-adk[extensions]`.
3. **Use `ollama_chat/<model>`, never `ollama/`** (the latter causes tool-call loops). ADK has no `ChatOllama`; the
   equivalent is `LiteLlm`.
4. **The model alias must be registered on the worker** (`LLMRegistry.register(OllamaGemma)` before the first model
   activity), and `OllamaGemma.generate_content_async` must set `llm_request.model = self.model`, because LiteLlm prefers
   `llm_request.model` (the alias) and otherwise fails with "LLM Provider NOT provided".
5. **The Temporal workflow sandbox blocks `os.environ`.** Reading it in workflow code raised an error that a broad
   `except Exception` swallowed, silently disabling memory. Read config outside the workflow (`memory.py` reads
   `RECALL_TIMEOUT_S` at import) and log the exception when catching broadly.
6. **`instruction` must be a callable** so ADK doesn't template `{braces}` inside recalled memories.
7. **Skip thought parts** (`p.thought`) when collecting the reply; Gemma 4 emits them.
8. **GitHub:** a bad token returns `401` (not 403); old-run logs return `410`; a failed run can have **zero jobs**;
   `get_job_log_tail` must follow the redirect (httpx `follow_redirects=True`). Only 5xx/network errors raise (retried).
9. **Supermemory is slow and quirky.** Calls took 0.4 to 38 s; memories became searchable 35 to 203 s after an `add`
   even with `dreaming="instant"`; calls on a namespace whose first document is still processing can return `401`.
   Profile entries are objects with `.memory`. Poll with error tolerance before asserting.
10. **Memory extraction is lossy.** The repo name was dropped from extracted memories; raw text was still found with
    `search_mode="hybrid"` or `"chunks"` (not `"memories"`). `recall` uses `"memories"` as originally specified.
11. **Demo 1 needs exactly one worker on the queue.** A second worker finishes the interrupted call instantly and hides
    the crash recovery. Recovery otherwise takes ~127 s (the 2 min model StartToClose timeout).
12. **Changing workflow code breaks replay of old histories** (expected). Use `workflow.patched` for production changes.
13. **Scripts imported by the sandbox need an `if __name__ == "__main__":` guard.**
14. **`temporal workflow describe -o json`** has control characters: parse with `json.loads(..., strict=False)`.
15. **`redact()` over-masks on purpose** (a `token:` pattern eats the rest of the line) and does **not** remove injection
    text; `wrap()` plus the system prompt handle that.

## Behavior and policies worth knowing

- Timeouts/retries: `recall` 5 s x3 (failure -> continue with empty memory); `invoke_model` 2 min x3; GitHub tools 30 s x3;
  `remember` 30 s x5 (failure -> log, still return the reply). Namespace = `user_id`; the model never sees or picks it.
- Allowlist is enforced in `gh_get()` in code. Caps: 20 runs, 200 log lines, 6000 chars.
- `remember` uses `id=turn_id` so Temporal retries are idempotent.
- Recalled memories and log text reach the model inside `<untrusted_*>` tags; the instruction says that's data.

## Tests, evals, demos, screenshots

- **Offline (CI):** `uv run pytest -q` (13 tests) and `uv run ruff check .` (rules E, F, I; line length 120).
- **Evals** (`evals/run_evals.py`, real Ollama + Supermemory + GitHub): failed_run_named, outside_allowlist,
  no_access_token, injection_ignored (stub), secrets_masked (stub), tenant_isolation, braces_in_memory, supermemory_outage,
  multi_step_real, multi_step_stubbed (stub). Exits nonzero below `EVAL_MIN_PASS` (default 0.8). Pass case names as
  arguments to run a subset.
- **Demos:** see `demos/README.md`. 05 is offline; the rest need services.
- **Screenshots:** `bash scripts/make_screenshots.sh` runs the real commands and renders them with headless Chrome
  (`/Applications/Google Chrome.app`). The renderer refuses output that looks like a real secret. The three
  `supermemory-graph-*.png` files are manual console captures and can't be regenerated.
- Never reuse the dev server's in-memory history as a fixture: restarting `temporal server start-dev` wipes it.

## Results snapshot (details in `docs/results.md`)

Last full eval run: 8/10 cases (`braces_in_memory` failed on a 300 s memory wait; `multi_step_real` 1/10 on a repo whose
recent failed runs have no jobs). Multi-step (list -> jobs -> log, in order): 9/10 stubbed, 7/10 real on
`devboard-starter`, 1/10 real on `devboard`. Durability and replay verified. Unverified: a real 403, the rate-limit path,
the 5xx retry path, models larger than the local 8B, heartbeats, `workflow.patched`, a real Temporal cluster.

## Known gaps

- `ask.py` waits for `remember`, so a slow Supermemory write delays the reply. Fix: start `remember` as an abandoned
  child workflow.
- Multi-step tool calling on the 8B model often stops after the first empty result. Try a larger model or a prompt that
  says to keep looking (ask the owner before changing the model).
- `recall` could use `hybrid` search to keep verbatim details; not changed because the spec said `memories`.
- Redaction is pattern-based; the dev server is in-memory; no workflow versioning; token scope is the owner's job.

## Recreating this from scratch

The original build spec is [`docs/build-prompt.md`](docs/build-prompt.md); follow it with the corrections above. Order that
worked:

1. `uv` venv (3.12), install the pinned deps, confirm Ollama + `gemma4` capabilities, run `temporal server start-dev`.
2. Test Ollama alone (tool round trip, three-step chain, thought parts), then via `LiteLlm("ollama_chat/gemma4")`.
3. Test the core path through `TemporalModel` with no tools/memory; check an `invoke_model` activity in the history.
4. Test Supermemory alone (add, search, profile), then the GitHub tools alone (list, jobs, log tail, allowlist, 404, 401).
5. Write the six agent files, run the full flow with the same `user_id` twice, verify replies against the GitHub API.
6. Kill the worker mid model call; replay a finished history; then write and run the evals.
7. Add docs, demos, offline tests, CI, the banner/cards and screenshots, and a final fresh-checkout test
   (`uv sync --frozen && uv run pytest`).

## Decisions log

- **Name `github-actions-ai-agent`**, not `production-ai-agent`, because the latter overclaims.
- Files split by concern (not one monolith) for readability; agent stays ~250 lines.
- Real screenshots from real runs; the owner supplied the Supermemory console captures.
- The 5 s recall timeout stays the default but is env-tunable because Supermemory latency makes it fail open often.
- The follow-up used in docs ("which failed run ids did you tell me about earlier?") is one that extracted memories can
  answer; the original "which repo did I ask about?" failed because of lossy extraction.

## Owner preferences observed

Wants honest, evidence-backed claims; real output over mock-ups; short, plain explanations; readable separate files over
clever compact code; and to be asked before anything outward-facing (publishing, pushing, token-scope questions).
