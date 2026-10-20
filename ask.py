"""Ask the agent one question: python ask.py <user_id> "<question>" """
import asyncio
import os
import sys
import uuid

from temporalio.client import Client
from temporalio.contrib.google_adk_agents import GoogleAdkPlugin

from worker import TASK_QUEUE
from workflow import TriageWorkflow


async def main():
    user_id, question = sys.argv[1], sys.argv[2]
    client = await Client.connect(os.environ.get("TEMPORAL_ADDRESS", "localhost:7233"),
                                  plugins=[GoogleAdkPlugin()])
    turn_id = f"turn-{uuid.uuid4().hex[:12]}"
    print(await client.execute_workflow(
        TriageWorkflow.run, args=[user_id, turn_id, question], id=turn_id, task_queue=TASK_QUEUE))


if __name__ == "__main__":
    asyncio.run(main())
