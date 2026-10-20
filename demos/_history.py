"""Tiny helper shared by the demos: print which activities ran, and on which attempt."""


async def print_activity_table(handle):
    history = await handle.fetch_history()
    names, rows = {}, []
    for event in history.events:
        if event.HasField("activity_task_scheduled_event_attributes"):
            names[event.event_id] = event.activity_task_scheduled_event_attributes.activity_type.name
        elif event.HasField("activity_task_started_event_attributes"):
            started = event.activity_task_started_event_attributes
            rows.append((names[started.scheduled_event_id], started.attempt))
    print(f"\n{'activity':22} attempt")
    for name, attempt in rows:
        print(f"{name:22} {attempt}" + ("   <-- retried after the crash" if attempt > 1 else ""))
