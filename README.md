<p align="center">
  <img src="assets/banner.png" alt="github-actions-ai-agent: an agent that triages failed GitHub Actions runs, remembers you, and survives a crashed worker" width="100%">
</p>

<p align="center">
  <img alt="Python 3.12" src="https://img.shields.io/badge/python-3.12-3776ab?logo=python&logoColor=white">
  <img alt="Temporal SDK 1.34" src="https://img.shields.io/badge/temporalio-1.34.0-7c3aed">
  <img alt="Google ADK 2.12" src="https://img.shields.io/badge/google--adk-2.12.0-34a853">
  <img alt="Supermemory 5" src="https://img.shields.io/badge/supermemory-5.0.0-ec4899">
  <img alt="Gemma 4 on Ollama" src="https://img.shields.io/badge/model-gemma4%20on%20Ollama-0ea5e9">
  <img alt="License MIT" src="https://img.shields.io/badge/license-MIT-lightgrey">
</p>

# github-actions-ai-agent

**A durable, memory-equipped agent that triages failed GitHub Actions runs.** Ask it "what failed recently on my repo?"
and it lists the runs, opens the failed jobs, reads the log tails and tells you what the logs support. It remembers who
you are between questions, and if its worker process is killed mid-answer, the answer still finishes.

It is also a **teaching repo**. The agent is about 250 lines, and every moving part is explained, with a runnable demo:
how Temporal makes an agent crash-safe, how memory works, and how to keep an agent read-only and safe with untrusted
input. Start with [Learn the concepts](#learn-the-concepts).

## The stack

<table>
  <tr>
    <td><a href="docs/architecture.md#the-model-path"><img src="assets/cards/gemma-ollama.svg" alt="Gemma 4 on Ollama"></a></td>
    <td><a href="docs/temporal-concepts.md#9-the-adk-plugin"><img src="assets/cards/google-adk.svg" alt="Google ADK"></a></td>
  </tr>
  <tr>
    <td><a href="docs/temporal-concepts.md"><img src="assets/cards/temporal.svg" alt="Temporal"></a></td>
    <td><a href="docs/memory-concepts.md"><img src="assets/cards/supermemory.svg" alt="Supermemory"></a></td>
  </tr>
  <tr>
    <td><a href="docs/safety.md"><img src="assets/cards/github-actions.svg" alt="GitHub Actions API"></a></td>
    <td><a href="pyproject.toml"><img src="assets/cards/uv-python.svg" alt="uv and Python 3.12"></a></td>
  </tr>
</table>

## See it work

Ask about a repo. The agent calls GitHub, and the answer matches the real runs:

<img src="assets/screenshots/04-ask.png" alt="Asking the agent what failed recently on a repo" width="100%">

Ask a follow-up later, even from a fresh process. It recalls what it told you from memory:

<img src="assets/screenshots/05-ask-memory.png" alt="A follow-up question answered from memory" width="100%">

Every step of that is recorded by Temporal. This is the workflow's history in the Temporal UI, from the crash demo below.
The red bar is a model call that was interrupted and retried:

<img src="assets/screenshots/ui-durability-history.png" alt="Temporal UI timeline showing recall, model calls, tool calls, a retried model call and remember" width="100%">

## Quickstart

You need [uv](https://docs.astral.sh/uv/), the [Temporal CLI](https://docs.temporal.io/cli), [Ollama](https://ollama.com),
Google Chrome (only for regenerating screenshots), a [Supermemory](https://supermemory.ai) API key, and a GitHub token
with **Actions: read-only**.

```bash
# 1. Install
uv sync
ollama pull gemma4
ollama show gemma4                  # Capabilities must list "tools" and "thinking"

# 2. Configure (never commit .env)
cp .env.example .env                # then fill in SUPERMEMORY_API_KEY, GITHUB_TOKEN, GITHUB_ALLOWED_REPOS

# 3. Run, in separate terminals
ollama serve                                         # skip if Ollama is already running
temporal server start-dev                            # UI at http://localhost:8233
uv run --env-file .env python worker.py
uv run --env-file .env python ask.py alice "what failed recently on owner/repo?"
uv run --env-file .env python ask.py alice "which failed run ids did you tell me about earlier?"
```

`GITHUB_ALLOWED_REPOS` is a comma-separated list of `owner/repo`; the agent refuses anything else, in code. Use the
same user id (`alice` above) to share memory between questions. Memory takes a minute or more to become searchable, so
wait a bit before the follow-up ([why](docs/memory-concepts.md#timing-why-recall-sometimes-comes-back-empty)).

<img src="assets/screenshots/01-ollama-show.png" alt="ollama show gemma4 listing tools and thinking capabilities" width="70%">

## Learn the concepts

| I want to understand... | Read | Then run |
|---|---|---|
| The whole picture | [docs/architecture.md](docs/architecture.md) | |
| Workflows, activities, retries, replay | [docs/temporal-concepts.md](docs/temporal-concepts.md) | [demo 1](demos/01_durability.py), [demo 2](demos/02_replay.py) |
| Memory, profiles, namespaces | [docs/memory-concepts.md](docs/memory-concepts.md) | [demo 3](demos/03_memory_basics.py), [demo 4](demos/04_tenant_isolation.py) |
| Keeping an agent read-only and safe | [docs/safety.md](docs/safety.md) | [demo 5](demos/05_redaction.py) |
| What was tested, and the honest numbers | [docs/results.md](docs/results.md) | `uv run --env-file .env python evals/run_evals.py` |

### Kill the worker, keep the answer

[Demo 1](demos/01_durability.py) kills the worker while a model call is running. A new worker picks up the same
workflow. The table at the bottom shows which steps ran once and which was retried:

<img src="assets/screenshots/08-demo-durability.png" alt="Durability demo: worker killed mid model call, workflow still completes, one model call retried" width="100%">

### What memory really returns

[Demo 3](demos/03_memory_basics.py) adds a document and prints what comes back: extracted memories, a similarity score,
and a profile. [Demo 4](demos/04_tenant_isolation.py) shows that one user's memory never leaks to another.

<img src="assets/screenshots/06-demo-memory.png" alt="Memory demo output" width="100%">
<img src="assets/screenshots/07-demo-isolation.png" alt="Tenant isolation demo output" width="100%">

Supermemory's own view of the same data, the memory graph in its console:

<img src="assets/screenshots/supermemory-graph-memories.png" alt="Supermemory memory graph showing documents linked to extracted memories" width="100%">

<p>
  <img src="assets/screenshots/supermemory-graph-profile.png" alt="Placeholder: Supermemory user profile" width="49%">
  <img src="assets/screenshots/supermemory-graph-isolation.png" alt="Placeholder: two Supermemory namespaces with no overlap" width="49%">
</p>

### Replay, and why changing workflow code is risky

<img src="assets/screenshots/09-demo-replay.png" alt="Replay demo: current code replays fine, changed code raises a non-determinism error" width="100%">

### Secrets and prompt injection

<img src="assets/screenshots/03-redaction-demo.png" alt="Redaction demo: secrets masked, injection text wrapped as untrusted data" width="100%">

## How it works

```mermaid
flowchart LR
    Q[Your question] --> W[TriageWorkflow]
    W -->|activity| R[recall: Supermemory]
    W -->|activity, loop| M[invoke_model: Gemma 4 on Ollama]
    M -->|tool call| G[GitHub: runs, jobs, log tails]
    G --> M
    W -->|activity| S[remember: Supermemory]
    W --> A[Answer]
```

Everything that touches the outside world is a Temporal activity, so it is retried on transient failure and never
re-run once it has finished. The workflow only decides what happens next. Full detail, with a sequence diagram, is in
[docs/architecture.md](docs/architecture.md).

<img src="assets/screenshots/ui-workflows.png" alt="Temporal UI workflow list" width="100%">

## Is it production-ready?

No, and the name doesn't pretend otherwise. It shows the patterns a production agent needs, built on a small local model.

| Solid | Not yet |
|---|---|
| Crash recovery and per-step retries and timeouts | Multi-step tool calling with the local 8B model: 7/10 on a repo whose failed runs have jobs, 1/10 when recent failures have none ([numbers](docs/results.md)) |
| Replay-tested workflow | Runs on Temporal's in-memory dev server, with no workflow versioning (`workflow.patched`) |
| Read-only, repo allowlist enforced in code | Token scope is your responsibility: a broad token is limited only by the allowlist |
| Secret redaction and untrusted-data wrapping | Redaction is pattern-based; unusual secret formats pass through |
| Per-user memory with tested tenant isolation | Supermemory latency (1 to 40 s observed) and lossy extraction make recall unreliable at short timeouts |
| 13 offline tests, lint and CI that need no keys | The user waits for the memory write before getting the reply (a known design gap, see results) |

## Configuration

All settings live in `.env` (see [`.env.example`](.env.example)).

| Variable | Default | Meaning |
|---|---|---|
| `SUPERMEMORY_API_KEY` | required | Supermemory key |
| `GITHUB_TOKEN` | required | Fine-grained token, Actions: read-only |
| `GITHUB_ALLOWED_REPOS` | required | Comma-separated `owner/repo` the agent may read |
| `OLLAMA_API_BASE` | `http://localhost:11434` | Where Ollama is |
| `OLLAMA_MODEL` | `gemma4` | Which Ollama model to use |
| `SM_DREAMING` | `dynamic` in code, `instant` in `.env.example` | Memory extraction mode |
| `RECALL_TIMEOUT_S` | `5` | Seconds before recall gives up and continues without memory |
| `EVAL_REPO` | first allowed repo | Repo the evals ask about |

## Repo map

```
workflow.py  worker.py  ask.py       the agent: workflow, worker, client
memory.py  github_tools.py  safety.py   activities and helpers
docs/        concepts, architecture, safety, results, screenshot checklist
demos/       five runnable lessons
tests/       offline tests (no keys)
evals/       end-to-end evals against the dev server
scripts/     screenshot, banner and card generators
assets/      banner, stack cards, screenshots
```

## Tests and evals

```bash
uv run pytest -q                                        # offline, instant
uv run --env-file .env python evals/run_evals.py        # ~20 min, needs Ollama, Temporal, both keys
uv run --env-file .env python evals/run_evals.py multi_step_real   # one case
```

<img src="assets/screenshots/02-offline-tests.png" alt="Offline tests passing" width="70%">

## Troubleshooting

| Symptom | Cause and fix |
|---|---|
| Agent says it has no memory of you | Recall timed out or the memory isn't searchable yet. Wait, and raise `RECALL_TIMEOUT_S`. Check the worker log for `recall failed`. |
| Follow-up can't name the repo | Memory extraction can drop details (it kept run ids but not the repo name in our run). See [results.md](docs/results.md). |
| `LLM Provider NOT provided` | The model alias isn't registered on the worker; see [temporal-concepts.md](docs/temporal-concepts.md#9-the-adk-plugin). |
| `ImportError: CacheableResult` from LiteLLM | Wrong LiteLLM and `mcp` pair. Use the pinned versions in `pyproject.toml` (`uv sync`). |
| Demo 1 shows no retry | A second worker is running on the same queue and finished the call. Stop it first. |
| Temporal UI doesn't load | You started the server with `--headless`. Run `temporal server start-dev` without it. |

## License

[MIT](LICENSE)
