"""Read-only GitHub Actions activities. The token is read here and nowhere else."""
import os

import httpx
from temporalio import activity

from safety import redact, wrap


async def gh_get(repo: str, path: str):
    """GET a repo-scoped REST path. Returns (response, None) or (None, short message for the model)."""
    if repo not in [r.strip() for r in os.environ["GITHUB_ALLOWED_REPOS"].split(",")]:
        return None, f"Repo '{repo}' is not in the allowed list; I can't access it."
    headers = {"Authorization": f"Bearer {os.environ['GITHUB_TOKEN']}",
               "Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
    async with httpx.AsyncClient(follow_redirects=True, timeout=20) as c:  # logs redirect to a blob URL
        r = await c.get(f"https://api.github.com/repos/{repo}/{path}", headers=headers)
    if r.status_code in (403, 429) and r.headers.get("x-ratelimit-remaining") == "0":
        return None, "GitHub rate limit reached; try again later."
    if r.status_code in (401, 403, 404):
        return None, f"GitHub returned {r.status_code}: no access or not found for '{repo}'."
    r.raise_for_status()  # 5xx raises, so Temporal retries; 401/403/404 above never do
    return r, None


@activity.defn
async def list_workflow_runs(repo: str, status: str | None = None, limit: int = 10) -> str:
    """List recent GitHub Actions runs of owner/repo. status may be e.g. 'failure' or 'success'. limit max 20."""
    query = f"actions/runs?per_page={min(max(limit, 1), 20)}" + (f"&status={status}" if status else "")
    r, err = await gh_get(repo, query)
    if err:
        return err
    runs = [f"run_id={x['id']} workflow={x['name']} branch={x['head_branch']} "
            f"conclusion={x['conclusion'] or x['status']} created={x['created_at']}"
            for x in r.json()["workflow_runs"]]
    return "\n".join(runs) or "No runs found."


@activity.defn
async def get_run_jobs(repo: str, run_id: int) -> str:
    """Get the jobs of a run: job id, conclusion and names of failed steps."""
    r, err = await gh_get(repo, f"actions/runs/{int(run_id)}/jobs")
    if err:
        return err
    out = []
    for j in r.json()["jobs"]:
        failed = [s["name"] for s in j["steps"] if s["conclusion"] == "failure"]
        out.append(f"job_id={j['id']} name={j['name']} conclusion={j['conclusion']} failed_steps={failed}")
    return "\n".join(out) or "No jobs found."


@activity.defn
async def get_job_log_tail(repo: str, job_id: int, lines: int = 80) -> str:
    """Get the last N lines (max 200) of a job's log."""
    r, err = await gh_get(repo, f"actions/jobs/{int(job_id)}/logs")
    if err:
        return err
    tail = "\n".join(r.text.splitlines()[-min(max(lines, 1), 200):])[-6000:]
    return wrap("job_log", redact(tail))


GITHUB_ACTIVITIES = [list_workflow_runs, get_run_jobs, get_job_log_tail]
