# Demos

Five short scripts, each teaching one idea. Read the docstring at the top of each; it says what to look for.
All commands run from the repo root.

| Demo | Teaches | Needs | Takes |
|---|---|---|---|
| [`05_redaction.py`](05_redaction.py) | Redaction and untrusted-data wrapping ([safety.md](../docs/safety.md)) | nothing | instant |
| [`03_memory_basics.py`](03_memory_basics.py) | What Supermemory returns: documents in, memories and a profile out ([memory-concepts.md](../docs/memory-concepts.md)) | Supermemory key | 1 to 4 min |
| [`04_tenant_isolation.py`](04_tenant_isolation.py) | One namespace per user; B never sees A | Supermemory key | 1 to 4 min |
| [`01_durability.py`](01_durability.py) | Kill the worker mid model call; the workflow still finishes ([temporal-concepts.md](../docs/temporal-concepts.md#6-crash-recovery-demo-1)) | Ollama, Temporal, both keys | about 3 min |
| [`02_replay.py`](02_replay.py) | Replay a history; see a non-determinism error from a changed workflow | Temporal, a finished workflow | seconds |

```bash
uv run python demos/05_redaction.py                       # offline
uv run --env-file .env python demos/03_memory_basics.py
uv run --env-file .env python demos/04_tenant_isolation.py
uv run --env-file .env python demos/01_durability.py      # needs Ollama and `temporal server start-dev`
uv run python demos/02_replay.py                          # after demo 1 or ask.py has produced a finished workflow
```

Stop any `worker.py` you started yourself before demo 1. The demo starts and kills its own worker, and a second worker
on the same queue would finish the interrupted call immediately, so you would not see the crash recovery.
