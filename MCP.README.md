# MCP Server README

## My original request

- Request VSC CHAT to create MCP.server to wrap around `Read_Medium_From_Gmail.py` program by import it.
  So, no need to modify and overwrite that program.
- Tell CHAT to create (both) two MCP.server with different techniques
  - **GitHub MCP server integration**
  - **Local HTTP microservice (FastAPI) that runs the script**

## What this is

- A lightweight MCP-style integration that lets you trigger the existing `Read_Medium_From_Gmail.py` workflow without modifying it.
- Implements two ways to run:
  - An HTTP endpoint (`FastAPI`) that triggers runs and returns a `job_id` for status/logs.
  - A small CLI adapter (`github_mcp_adapter.py`) that accepts a JSON payload on stdin and runs the extractor synchronously.

Files added

- `mcp_server/_runner.py` — imports and runs `Read_Medium_From_Gmail.main()` while capturing stdout/stderr to a log file.
- `mcp_server/fastapi_server.py` — FastAPI app with `POST /run` and `GET /status/{job_id}`.
- `mcp_server/github_mcp_adapter.py` — CLI adapter that reads JSON from stdin and runs extraction.

Quick prerequisites

- Run from the repository root `/Users/syuen/Medium_Email` (as project root).
- `uv` is initialized in this directory.
- `uvicorn` is installed as system command.
- Activate the virtualenv if desired:

  source ls/bin/activate

## FastAPI server (HTTP)

1. Install dependencies (only needed for the HTTP server):

`pip install fastapi uvicorn`

2. Start server:

`uvicorn mcp_server.fastapi_server:app --host 0.0.0.0 --port 8000`

3. Trigger a run with `curl` (example):

`curl -X POST http://localhost:8000/run -H "Content-Type: application/json" -d '{"gmail_username":"you@example.com","gmail_password":"app-pass"}'`

Response will include `job_id` and `log` path. Check status/tail:

`curl http://localhost:8000/status/job_id`

> My environment variables have both GMAIL_USERNAME and GMAIL_PASSWORD
>
> `echo '{"gmail_username":"'"$GMAIL_USERNAME"'","gmail_password":"'"$GMAIL_PASSWORD"'"}'`

My trigger `curl` command:

`curl -X POST http://localhost:8000/run -H "Content-Type: application/json" -d '{"gmail_username":"'"$GMAIL_USERNAME"'","gmail_password":"′"$GMAIL_PASSWORD"'"}'`

## Run adapter directly (no HTTP)

1. From repo root, run the adapter and pass JSON on stdin:

`echo '{"gmail_username":"you@example.com","gmail_password":"app-pass"}' | python mcp_server/github_mcp_adapter.py`

Since my env has these two variable, `python mcp_server/github_mcp_adapter.py` can be executed from the root directory.

2. The adapter writes logs to `mcp_server/logs/run_<id>.log` and prints the log path

Notes & troubleshooting

- The runner attempts to import `Read_Medium_From_Gmail` normally; if that fails it will load the `Read_Medium_From_Gmail.py` file by path. Run from repo root for best results.
- Logs are stored under `mcp_server/logs/`.
- The adapter and server do not modify `Read_Medium_From_Gmail.py` — they import and call its `main()` entrypoint.
- For non-interactive runs, ensure `GMAIL_USERNAME` and `GMAIL_PASSWORD` are provided via the JSON payload, environment, or `set_gmail_env.sh`.

Example curl and adapter commands (copyable):

# Start server (background)

uvicorn mcp_server.fastapi_server:app --host 0.0.0.0 --port 8000 &

# Trigger via curl

curl -X POST http://localhost:8000/run -H "Content-Type: application/json" -d '{"gmail_username":"you@example.com","gmail_password":"app-pass"}'

# Run adapter directly

echo '{"gmail_username":"you@example.com","gmail_password":"app-pass"}' | python mcp_server/github_mcp_adapter.py

If you want, I can also add a sample systemd/launchd unit or a GitHub Actions job that posts to `/run` and archives logs.<hr>

## GitHub Actions workflow (mcp_run.yml)

- Location: `.github/workflows/mcp_run.yml` in the repository root — open it in VS Code or on GitHub to view/modify.
- Who/what runs it: GitHub Actions runs the workflow on GitHub-hosted runners (for example `ubuntu-latest`) — GitHub provisions the VM that executes the job.
  Billing and runners: GitHub-hosted runners are provided by GitHub. Actions usage (minutes and artifact storage) is billed according to your GitHub plan for private repositories; public repositories have generous free usage. If you prefer no billed minutes, you can configure a self-hosted runner (your own machine) instead.

  * If you use GitHub-hosted runners, Actions usage (minutes + storage for artifacts) is billed to the repository/org according to your GitHub plan.
    * Public repos have free minutes
    * Private repos get a monthly included allotment and then pay per-minute if exceeded.
    * Artifact storage beyond free tier is also billable.
  * If you use a self-hosted runner (a machine you run), GitHub does not charge minutes for those runs, but you must supply/maintain the hardware and networking yourself.
  * Check billing and usage at: Repository Settings → Billing (or Organization Settings → Billing) → Actions usage.
- Where to add **repository** secrets: on GitHub.com go to **Settings → Secrets and variables → Actions → New repository secret**. Add `GMAIL_USERNAME`, `GMAIL_PASSWORD`, and optionally `GMAIL_FOLDER`.
- How secrets are used: when the workflow runs, GitHub injects the secret values into the runner environment as variables (via `${{ secrets.NAME }}` in the workflow). Those environment variables are available to child processes, so the adapter or extractor can read them from `os.environ`.

  - env:
    `GMAIL_USERNAME: ${{ secrets.GMAIL_USERNAME }}`
    `GMAIL_PASSWORD: ${{ secrets.GMAIL_PASSWORD }}`
- Manual dispatch: to run the workflow manually, open the repository on github.com → **Actions** tab → select **MCP Run** → click **Run workflow** (choose branch) → confirm. The workflow will run on GitHub infrastructure and produce logs/artifacts available in the run page.
- Automation vs manual: the workflow is configured to run on both manual dispatch (`workflow_dispatch`) and on a schedule (`cron`); it will run automatically on the schedule and can also be triggered manually. It is not triggered by local events unless configured (e.g., `push`, `pull_request`) — only manual dispatch or schedule run in the current config.
