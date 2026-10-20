# Temporal concepts, taught with this repo

Every concept below points at the real code and, where there is one, a demo you can run. Read it alongside
[`workflow.py`](../workflow.py) and [`worker.py`](../worker.py), and keep the Temporal UI open at
http://localhost:8233 while you try things.

## 1. Why an agent needs durable execution

An agent run is a chain of slow, fallible steps: a model call that takes seconds, a GitHub call that can fail, a memory
write to a service that is sometimes slow. Without durability, a crash in step 6 loses steps 1 to 5 and you pay for
them again (more model calls, more API calls). Temporal records each finished step, so a crash costs you only the step
that was in flight.

## 2. Workflow vs activity

| | Workflow | Activity |
|---|---|---|
| Job | Decides what happens next | Does one thing that touches the outside world |
| May do I/O? | No | Yes |
| Re-executed on recovery? | Yes, by replay (cheap, no side effects) | Only if it did not finish |
| In this repo | `TriageWorkflow` ([`workflow.py:43`](../workflow.py)) | `recall`, `remember`, the three GitHub tools, `invoke_model` |

The rule of thumb: if it talks to a network, a file or a clock, it is an activity. The model call, every GitHub call
and every Supermemory call is an activity here, so the workflow itself is deterministic.

## 3. Determinism and the sandbox

Temporal rebuilds a workflow by **replaying** your code against its recorded history, so the code must make the same
decisions every time. The Python SDK runs workflow code in a sandbox that blocks nondeterministic things such as
`os.environ`, random numbers and wall-clock time.

**A real bug from this project.** The first version read the recall timeout with `os.environ.get(...)` inside the
workflow. The sandbox raised an error, a broad `except Exception` swallowed it, and memory was silently disabled: the
workflow had no `recall` activity at all and the agent answered "I don't know which repo you asked about". Two lessons:

- Read configuration outside workflow code. [`memory.py:11`](../memory.py) reads `RECALL_TIMEOUT_S` once at import time
  and the workflow imports the value through `workflow.unsafe.imports_passed_through()`
  ([`workflow.py:7`](../workflow.py)).
- Log the exception when you catch broadly ([`workflow.py:52`](../workflow.py)). The worker log showed the cause at
  once; without that line it would have taken far longer to find.

## 4. Timeouts and retries

Each activity call carries its own policy. These are the real values:

| Activity | Timeout (StartToClose) | Max attempts | On final failure |
|---|---|---|---|
| `recall` | `RECALL_TIMEOUT_S`, default 5s | 3 | Continue with empty memory |
| `invoke_model` | 2 minutes | 3 | Workflow fails |
| GitHub tools | 30 seconds | 3 | The tool error goes back to the model |
| `remember` | 30 seconds | 5 | Log it, still return the reply |

Two ideas to take from this:

- **Retries are for transient failures.** [`github_tools.py:22`](../github_tools.py) raises on a 5xx so Temporal
  retries, but returns a plain message for 401/403/404, because retrying a missing repo only wastes time.
- **A failure policy is a product decision.** Memory is optional (recall failure is swallowed), but a model failure is
  not (the workflow fails). Decide for each step what "give up" means.

## 5. Event history

Open any workflow in the UI and you see its **event history**: one row for every decision and every finished
activity. This is the whole trace; there is no separate tracing backend.

![A workflow's event history in the Temporal UI](../assets/screenshots/ui-durability-history.png)

Look for the pattern `invoke_model` -> `list_workflow_runs` -> `invoke_model` -> `get_run_jobs` ->
`invoke_model` -> ... -> `remember`. That alternation is the agent loop: the model asks for a tool, the tool runs as an
activity, and the result goes back to the model.

## 6. Crash recovery (demo 1)

[`demos/01_durability.py`](../demos/01_durability.py) starts a workflow, waits until a model call is running, kills the
worker with `SIGKILL`, starts a new worker, and prints each activity with its attempt number.

![Demo 1 output](../assets/screenshots/08-demo-durability.png)

Read the table at the end of the demo: activities that finished before the crash show attempt `1` and ran exactly
once; the interrupted model call shows attempt `2`. In the run above, recovery took **127 seconds**: when a worker
dies, Temporal learns about it when the activity's 2 minute StartToClose timeout expires, not instantly. A
**heartbeat** from long activities lets Temporal notice sooner, which is worth adding if your model calls are slow.

## 7. Replay and changing code (demo 2)

[`demos/02_replay.py`](../demos/02_replay.py) replays a finished history twice: against the current code (passes) and
against a changed workflow that does something different first (fails with a non-determinism error).

![Demo 2 output](../assets/screenshots/09-demo-replay.png)

This is also why changing workflow code is risky for **in-flight** runs: they replay your new code against an old
history. While building this repo, two old histories failed replay after we fixed the recall bug, for exactly that
reason. For production, use `workflow.patched(...)` to branch old and new behavior, and run the replayer on real
histories in CI before you deploy.

## 8. Workers and task queues

A **worker** is a process that polls a **task queue** and runs workflow and activity code. This repo uses the queue
`ci-triage` ([`worker.py:15`](../worker.py)); the evals use their own queue so they never compete with a running
worker. The client (`ask.py`) only names the queue; it never runs your code. Start two workers and either one can
take the work, which is how Temporal scales horizontally.

## 9. The ADK plugin

Google ADK builds the agent loop; Temporal's `GoogleAdkPlugin` makes each model call and tool call a Temporal
activity. Three pieces to know:

- **`TemporalModel("gemma4-ollama", ...)`** ([`workflow.py:29`](../workflow.py)) is a model *alias*. Inside the workflow
  it only records that a model call is needed; the real call happens in the `invoke_model` activity on the worker.
- **The registry.** Because the call happens on the worker, the alias must resolve there. `OllamaGemma`
  ([`worker.py:18`](../worker.py)) is a small `LiteLlm` subclass registered under `gemma4-ollama` before the worker
  starts. It also sets `llm_request.model = self.model`, because LiteLLM otherwise tries to use the alias as a real model
  name and fails with "LLM Provider NOT provided".
- **`activity_as_tool`** ([`workflow.py:38`](../workflow.py)) wraps a plain activity function as an ADK tool, keeping its
  signature so ADK can describe it to the model.

Pass `plugins=[GoogleAdkPlugin()]` to the `Client` (see [`ask.py`](../ask.py) and [`worker.py`](../worker.py)); a worker
built from that client inherits it.

## Exercises

1. Run demo 1, then open the workflow in the UI and find the attempt-2 model call.
2. Change `maximum_attempts=3` on `invoke_model` to `1`, run demo 1 again, and watch the workflow fail instead of recover.
3. Add `await asyncio.sleep(1)` inside the workflow loop in a scratch copy, then run demo 2 against an old history. Why
   is `asyncio.sleep` allowed in a workflow while `time.sleep` is not?
4. Move the `remember` call so it runs before the model loop. Predict what replay does with old histories, then check
   with demo 2.
5. Make `remember` fire-and-forget (a child workflow with `parent_close_policy=ABANDON`) so the user does not wait for
   Supermemory. See [results.md](results.md) for why this matters.
