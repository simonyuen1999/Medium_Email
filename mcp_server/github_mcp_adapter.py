"""Simple MCP adapter CLI.

Reads a small JSON payload from stdin (or accepts env vars) and runs the extractor synchronously,
writing logs to `mcp_server/logs/run_<id>.log`.

Example usage:
  echo '{"gmail_username":"you@example.com","gmail_password":"app-pass"}' | python mcp_server/github_mcp_adapter.py

This file intentionally does not modify `Read_Medium_From_Gmail.py`.
"""
import sys
import json
import uuid
from pathlib import Path
try:
    # When run as a script from the repo root
    from mcp_server._runner import run_extraction
except Exception:
    # Fallback for package execution contexts
    from _runner import run_extraction


def main():
    payload = {}
    if not sys.stdin.isatty():
        try:
            data = sys.stdin.read()
            if data.strip():
                payload = json.loads(data)
        except Exception:
            pass

    # Allow quick CLI override via args as JSON string
    if len(sys.argv) > 1:
        try:
            payload = json.loads(sys.argv[1])
        except Exception:
            pass

    job_id = uuid.uuid4().hex[:12]
    app_dir = Path(__file__).resolve().parent
    log_dir = app_dir / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = str(log_dir / f"run_{job_id}.log")

    env = {}
    for k in ("gmail_username", "gmail_password", "gmail_folder"):
        if k in payload:
            env_key = "GMAIL_" + k.split("gmail_")[-1].upper()
            env[env_key] = payload[k]

    print(f"Starting extraction job {job_id}, logging to: {log_path}")
    run_extraction(env, log_path)
    print(f"Finished. See log: {log_path}")


if __name__ == "__main__":
    main()
