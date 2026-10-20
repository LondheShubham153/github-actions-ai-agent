# Screenshots

Most images in the README are **generated from real runs**: `bash scripts/make_screenshots.sh` runs the commands,
captures their output and renders it with headless Chrome. The Temporal UI images come from the same run.

The Supermemory images come from the Supermemory console, which only you can open. `supermemory-graph-memories.png` is
a real capture of the Memory Graph; the other two are still **placeholders**. To replace one, save your capture over the
file with the same name; no other change is needed.

| File | What to capture |
|---|---|
| `assets/screenshots/supermemory-graph-memories.png` | **Done.** The Memory Graph, with documents and the memories extracted from them. |
| `assets/screenshots/supermemory-graph-profile.png` | The profile view for that same namespace: the static and dynamic facts. |
| `assets/screenshots/supermemory-graph-isolation.png` | The two namespaces from `demos/04_tenant_isolation.py` side by side, showing no shared memories. Both namespace names are printed by the demo. |

## Tips

- Run the demo with `SM_DREAMING=instant` (the `.env.example` default) so the graph has memories within a minute or two.
- Crop to the graph, and check no API keys or account details are in frame.
- 1600x900 matches the placeholders, but any 16:9 size renders fine.

## Regenerating the rest

```bash
temporal server start-dev            # with the UI, not --headless
ollama serve                         # if it is not already running
bash scripts/make_screenshots.sh     # about 15 minutes; Supermemory is the slow part
```

Images are written to `assets/screenshots/`. The renderer refuses to draw output that looks like a real secret.
