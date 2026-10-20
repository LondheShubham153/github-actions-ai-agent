"""Demo 4: tenant isolation. The namespace is the user id, so user B cannot see user A's memories.

The agent never lets the model pick a namespace and has no memory tool, so a prompt cannot cross the boundary.

Run (needs SUPERMEMORY_API_KEY):
    uv run --env-file .env python demos/04_tenant_isolation.py
"""
import asyncio
import uuid

from supermemory import AsyncSupermemory

SECRET = "teal-9137"


async def search(sm, namespace):
    try:
        return await sm.search(namespace, query="what is my favorite color?", search_mode="memories", limit=5)
    except Exception:
        return None  # not ready yet


async def main():
    sm = AsyncSupermemory()
    alice, bob = f"demo-alice-{uuid.uuid4().hex[:5]}", f"demo-bob-{uuid.uuid4().hex[:5]}"
    await sm.add(alice, content=f"User: my favorite color is {SECRET}.", id="t1", dreaming="instant")
    await sm.add(bob, content="User: I like hiking.", id="t1", dreaming="instant")
    print(f"added a private fact to {alice} and an unrelated one to {bob}; waiting for extraction ...")

    for _ in range(120):
        a, b = await search(sm, alice), await search(sm, bob)
        if a and a.results and b and b.results:
            break
        await asyncio.sleep(5)

    print(f"\n{alice} searches 'favorite color':", [r.memory for r in a.results][:2])
    print(f"{bob} searches 'favorite color':  ", [r.memory for r in b.results][:2])
    leaked = any(SECRET in (r.memory or "") for r in b.results)
    print("\nBob saw Alice's secret:", leaked, "(expected: False)")


if __name__ == "__main__":
    asyncio.run(main())
