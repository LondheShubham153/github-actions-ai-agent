# Safety model

The agent is **read-only** and treats everything it reads as untrusted. Each control below is enforced in code, so a
clever prompt can't switch it off. The offline tests (`uv run pytest`) cover the redaction and wrapping helpers.

| Control | Where | What it guarantees |
|---|---|---|
| Read-only | [`github_tools.py`](../github_tools.py) | Only three `GET` endpoints exist. There is no write path to call. |
| Repo allowlist | [`github_tools.py:12`](../github_tools.py) | Every activity rejects repos outside `GITHUB_ALLOWED_REPOS` with a clear message. |
| Secrets stay in activities | `github_tools.py`, `memory.py` | The token and key are read only inside activities, never in workflow code or model text. |
| Redaction | [`safety.py:12`](../safety.py) | Masks tokens, keys, bearer tokens, password-style assignments and emails in logs and in stored memories. |
| Untrusted wrapping | [`safety.py:16`](../safety.py) | Logs and memories reach the model inside `<untrusted_*>` tags. |
| Caps | `github_tools.py` | At most 20 runs, 200 log lines and 6000 characters per call. |
| Clean errors | `github_tools.py` | `401/403/404` and rate limits return a short message; Temporal retries only transient failures. |

## Redaction in action

Run `uv run python demos/05_redaction.py` to see it. Two things worth knowing:

- **It over-masks, on purpose.** The pattern for `token=...` style assignments consumes the rest of the line, so
  `x-access-token:ghp_...@github.com/acme/app` becomes `x-access-[REDACTED]`. Losing a little context is the safe
  direction.
- **It does not remove prompt-injection text.** A log line that says "ignore all previous instructions" survives
  redaction. That is what the untrusted wrapper, and the instruction that text in those tags is data, are for. The eval
  `injection_ignored` stubs GitHub's HTTP response with such a payload and checks the answer doesn't change.

## Token scope

The prompt for this project asks for a fine-grained token with **Actions: read-only** on selected repositories. The
allowlist is the second line of defense: even a broader token can only reach the repos you list. Check a token's reach
without printing secrets:

```bash
curl -s -H "Authorization: Bearer $GITHUB_TOKEN" "https://api.github.com/user/repos?per_page=100" \
  | python3 -c "import sys,json; [print(r['full_name'], r['permissions']) for r in json.load(sys.stdin)]"
```

If it lists more repos than you intend, or shows write access, create a narrower token before using the agent on
anything important.

## Known gaps

- The allowlist is only as good as the token behind it (see above).
- Redaction is pattern-based. A secret in an unusual format will pass through.
- The model can still be wrong. The system prompt tells it to say when data is missing and not to state causes the
  logs don't support, but a small local model doesn't always follow that. See [results.md](results.md).
