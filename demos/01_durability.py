"""Demo 1: kill the worker in the middle of a model call and watch the workflow finish anyway.

Temporal stores every finished step in the workflow's event history. When a new worker starts, it replays the
history, skips the steps that already finished, and re-runs only the one that was interrupted.

Run (Ollama, `temporal server start-dev` and your .env must be ready; takes about 3 minutes):
    uv run --env-file .env python demos/01_durability.py
"""
import asyncio
import os
import subprocess
import sys
import time
import uuid

from _history import print_activity_table
from temporalio.client import Client
from temporalio.contrib.google_adk_agents import GoogleAdkPlugin

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from worker import TASK_QUEUE  # noqa: E402
from workflow import TriageWorkflow  # noqa: E402

REPO = os.environ.get("EVAL_REPO", "LondheShubham153/devboard-starter")


def start_worker():
    return subprocess.Popen([sys.executable, "worker.py"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


async def model_call_in_flight(handle):
    """True when a model activity is running and at least one tool call has already finished."""
    desc = await handle.describe()
    pending = [a.activity_type.name for a in desc.raw_description.pending_activities if a.state == 2]  # 2 = STARTED
    return "invoke_model" in pending and desc.history_length >= 20


async def main():
    client = await Client.connect("localhost:7233", plugins=[GoogleAdkPlugin()])
    worker = start_worker()
    turn_id = f"demo-durability-{uuid.uuid4().hex[:6]}"
    handle = await client.start_workflow(
        TriageWorkflow.run, id=turn_id, task_queue=TASK_QUEUE,
        args=["demo-user", turn_id, f"Why did the latest failed run on {REPO} fail? Check jobs and logs."])
    print(f"1. started workflow {turn_id} with worker pid {worker.pid}")

    while not await model_call_in_flight(handle):
        await asyncio.sleep(0.2)
    worker.kill()
    print(f"2. KILLED the worker (pid {worker.pid}) while a model call was running")

    await asyncio.sleep(2)
    worker = start_worker()
    began = time.time()
    print(f"3. started a new worker (pid {worker.pid}); Temporal notices the lost activity when its 2 minute "
          "StartToClose timeout expires, then retries it")
    print("\n4. result:", await handle.result())
    print(f"   finished {time.time() - began:.0f}s after the restart")
    await print_activity_table(handle)
    worker.kill()


if __name__ == "__main__":
    asyncio.run(main())
