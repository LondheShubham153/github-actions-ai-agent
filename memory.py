"""Supermemory activities. The namespace is always user_id; the model never sees or picks it."""
import asyncio
import os

from supermemory import AsyncSupermemory
from temporalio import activity

from safety import redact

# Spec default is 5s. Read here (not in workflow code) so the workflow stays deterministic.
RECALL_TIMEOUT_S = int(os.environ.get("RECALL_TIMEOUT_S", 5))


@activity.defn
async def recall(user_id: str, query: str) -> str:
    sm = AsyncSupermemory()
    prof, found = await asyncio.gather(
        sm.profile(user_id), sm.search(user_id, query=query, search_mode="memories", limit=5))
    facts = [f.memory for f in prof.profile.static + prof.profile.dynamic]
    facts += [r.memory for r in found.results if r.memory]
    return "\n".join(f"- {f}" for f in dict.fromkeys(facts))


@activity.defn
async def remember(user_id: str, turn_id: str, user_msg: str, reply: str) -> None:
    # id=turn_id makes Temporal retries idempotent
    await AsyncSupermemory().add(
        user_id, content=redact(f"User: {user_msg}\nAssistant: {reply}"), id=turn_id,
        dreaming=os.environ.get("SM_DREAMING", "dynamic"))
