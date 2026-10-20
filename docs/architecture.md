# Architecture

One question ("why did the latest run fail?") becomes one Temporal workflow. Everything that touches the outside
world (the model, Supermemory, GitHub) runs as an **activity**. The workflow only decides what happens next.

## The request, step by step

```mermaid
sequenceDiagram
    autonumber
    participant C as ask.py (client)
    participant T as Temporal server
    participant W as Worker (worker.py)
    participant S as Supermemory
    participant O as Ollama (Gemma 4)
    participant G as GitHub REST API

    C->>T: start TriageWorkflow(user_id, turn_id, message)
    T->>W: workflow task
    W->>S: recall activity: profile + search(user_id)
    S-->>W: facts about this user (or empty on timeout)
    loop until the model answers in text
        W->>O: invoke_model activity (instruction + memories + history)
        O-->>W: tool call, or final text
        W->>G: tool activity: list_workflow_runs / get_run_jobs / get_job_log_tail
        G-->>W: runs, jobs, or a redacted, wrapped log tail
    end
    W->>S: remember activity: add(user_id, redacted exchange, id=turn_id)
    W-->>C: reply
```

Every arrow that leaves the worker is an activity, so Temporal records it in the event history, retries it on
transient failure, and never re-runs it once it has completed.

## Where each concern lives

| Concern | File | What it does |
|---|---|---|
| Orchestration | [`workflow.py`](../workflow.py) | recall, then the ADK agent, then remember. Pure decisions, no I/O. |
| Model registration | [`worker.py`](../worker.py) | Registers Ollama under the alias `gemma4-ollama` and starts the worker. |
| Memory I/O | [`memory.py`](../memory.py) | `recall` and `remember` activities. The namespace is always `user_id`. |
| GitHub I/O | [`github_tools.py`](../github_tools.py) | Three read-only activities, the allowlist and the error mapping. |
| Safety helpers | [`safety.py`](../safety.py) | `redact` masks secrets, `wrap` labels text as untrusted data. |
| Client | [`ask.py`](../ask.py) | Starts a workflow and prints the reply. |

## The model path

ADK's `TemporalModel("gemma4-ollama")` turns each model call into an `invoke_model` activity. On the worker,
`OllamaGemma` (a small `LiteLlm` subclass) is registered under that alias and talks to Ollama through LiteLLM with the
`ollama_chat/` prefix. See [temporal-concepts.md](temporal-concepts.md#9-the-adk-plugin) for why the alias exists.

## Trust boundaries

```mermaid
flowchart LR
    U[User message] --> WF
    subgraph trusted[Trusted: your code]
        WF[Workflow] --> ACT[Activities]
    end
    ACT -->|redacted + wrapped| M[Model]
    GH[(GitHub logs)] -. untrusted .-> ACT
    SM[(Supermemory)] -. untrusted .-> ACT
    ENV[(.env secrets)] --> ACT
    ENV -. never .-> M
```

- The GitHub token and the Supermemory key are read only inside activities. They never appear in workflow code or in
  text the model sees.
- Log text and recalled memories are **untrusted data**: they are wrapped in `<untrusted_*>` tags before the model
  reads them. See [safety.md](safety.md).
- The allowlist and the read-only guarantee are enforced in code, not in the prompt.

## What is deliberately not here

No guardrail framework, no tracing backend, no metrics stack, no config system. Temporal's UI and event history are
the observability. This keeps the agent small enough to read in one sitting.
