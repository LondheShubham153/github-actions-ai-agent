"""Demo 3: what Supermemory actually returns. Documents go in; memories and a profile come out.

You never write a memory. You `add` a document (here, a conversation turn) and Supermemory extracts facts from it
in the background. Then you can `search` those facts or read the maintained `profile`.

Run (needs SUPERMEMORY_API_KEY; extraction can take a minute or more):
    uv run --env-file .env python demos/03_memory_basics.py
"""
import asyncio
import time
import uuid

from supermemory import AsyncSupermemory


async def main():
    sm = AsyncSupermemory()
    namespace = f"demo-memory-{uuid.uuid4().hex[:6]}"  # a namespace is an isolation boundary: one per user
    print("namespace:", namespace)

    turn = "User: I mostly work on the devboard-starter repo.\nAssistant: Noted. I will check its runs first."
    first = await sm.add(namespace, content=turn, id="turn-1", dreaming="instant")
    again = await sm.add(namespace, content=turn, id="turn-1", dreaming="instant")  # a retry, same id
    print(f"add            -> id={first.id} status={first.status}")
    print(f"add (retry)    -> id={again.id} status={again.status}   (same id: Temporal retries are idempotent)")

    print("\nwaiting for extraction (dreaming='instant' still takes a while) ...")
    start = time.time()
    while True:
        try:
            found = await sm.search(namespace, query="which repo does the user work on?",
                                    search_mode="memories", limit=3)
            if found.results:
                break
        except Exception:
            pass  # a brand new namespace can answer 401 or empty until its first document is processed
        await asyncio.sleep(5)
    print(f"memories searchable after {time.time() - start:.0f}s\n")

    print("search(search_mode='memories'):")
    for r in found.results:
        print(f"  similarity={r.similarity:.2f}  memory={r.memory!r}")

    profile = (await sm.profile(namespace)).profile
    print("\nprofile.static  (durable facts):  ", [f.memory for f in profile.static])
    print("profile.dynamic (recent context): ", [f.memory for f in profile.dynamic])
    print("\nNote: profile entries are objects with .memory, not plain strings.")


if __name__ == "__main__":
    asyncio.run(main())
