"""Demo 2: replay a finished workflow's history against the current code, then against changed code.

Replay is how Temporal rebuilds a workflow after a crash: it re-runs your workflow function against the recorded
history and checks it makes the same decisions. If you change the code so it decides something different, replay
fails with a non-determinism error. That is also how you test a deploy before shipping it.

Run (needs at least one finished TriageWorkflow, e.g. after demo 1 or `ask.py`):
    uv run python demos/02_replay.py
"""
import asyncio
import os
import sys
from datetime import timedelta

from temporalio import workflow
from temporalio.client import Client
from temporalio.contrib.google_adk_agents import GoogleAdkPlugin
from temporalio.worker import Replayer

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from workflow import TriageWorkflow  # noqa: E402

with workflow.unsafe.imports_passed_through():
    from memory import remember  # noqa: E402


@workflow.defn(name="TriageWorkflow")  # same name as the real one: this is "the changed deploy"
class ChangedTriageWorkflow:
    @workflow.run
    async def run(self, user_id: str, turn_id: str, message: str) -> str:
        # The change: write to memory BEFORE doing anything else. The history says recall came first.
        await workflow.execute_activity(remember, args=[user_id, turn_id, message, ""],
                                        start_to_close_timeout=timedelta(seconds=30))
        return "changed"


async def replay(replayer, history, label):
    try:
        await replayer.replay_workflow(history)
        print(f"{label}: replay OK, the code makes the same decisions as the recorded history")
    except Exception as e:
        reason = str(e).split("Nondeterminism error:")[-1].split(", source")[0].strip(" \"")
        print(f"{label}: replay FAILED -> {type(e).__name__}: {reason}")


async def main():
    plugin = GoogleAdkPlugin()
    client = await Client.connect("localhost:7233", plugins=[plugin])
    query = "WorkflowType='TriageWorkflow' AND ExecutionStatus='Completed'"
    done = [w async for w in client.list_workflows(query, limit=1)]
    if not done:
        sys.exit("No finished TriageWorkflow found. Run demo 1 or ask.py first.")
    print("replaying history of", done[0].id)
    history = await client.get_workflow_handle(done[0].id).fetch_history()
    await replay(Replayer(workflows=[TriageWorkflow], plugins=[plugin]), history, "current code ")
    await replay(Replayer(workflows=[ChangedTriageWorkflow], plugins=[plugin]), history, "changed code ")


if __name__ == "__main__":
    asyncio.run(main())
