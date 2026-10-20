# Screenshots

Most images in the README are **generated from real runs**: `bash scripts/make_screenshots.sh` runs the commands,
captures their output and renders it with headless Chrome. The Temporal UI images come from the same run.

The three Supermemory images are real captures of the Memory Graph in the Supermemory console, which only the repo
owner can open, so the script can't regenerate them:

| File | What it shows |
|---|---|
| `assets/screenshots/supermemory-graph-memories.png` | A document selected, with the memories extracted from it. |
| `assets/screenshots/supermemory-graph-overview.png` | The whole workspace zoomed out: documents and their memories. |
| `assets/screenshots/supermemory-graph-memory-versions.png` | One memory selected, with its version history and links to source documents. |

They show the whole workspace ("All Namespaces"), so they include memories from other projects too. To capture a graph
for just the demo users, pick that namespace in the console first; the demos print their namespace names
(`demo-memory-...`, `demo-alice-...`).

## Tips

- Run the demo with `SM_DREAMING=instant` (the `.env.example` default) so the graph has memories within a minute or two.
- Crop to the graph, and check no API keys or account details are in frame.
- Crop out the sidebar if it shows more than you want to publish (workspace and account names are visible in it).

## Regenerating the rest

```bash
temporal server start-dev            # with the UI, not --headless
ollama serve                         # if it is not already running
bash scripts/make_screenshots.sh     # about 15 minutes; Supermemory is the slow part
```

Images are written to `assets/screenshots/`. The renderer refuses to draw output that looks like a real secret.
