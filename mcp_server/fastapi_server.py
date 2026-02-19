"""FastAPI MCP-like server to trigger `Read_Medium_From_Gmail.py` runs.

Usage:
  pip install fastapi uvicorn

Run locally:
  uvicorn mcp_server.fastapi_server:app --host 0.0.0.0 --port 8000

Endpoints:
  POST /run   -> trigger extraction (accepts optional JSON: gmail_username, gmail_password, gmail_folder)
  GET  /status/{job_id} -> retrieve status and tail of log

This server imports and calls `Read_Medium_From_Gmail.main()` via the shared runner.
"""
from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel
import threading
import uuid
import json
import os
from pathlib import Path
from ._runner import run_extraction


APP_DIR = Path(__file__).resolve().parent
LOG_DIR = APP_DIR / "logs"
STATUS_FILE = APP_DIR / "status.json"
os.makedirs(LOG_DIR, exist_ok=True)

app = FastAPI(title="Medium Email MCP Server")


class RunRequest(BaseModel):
    gmail_username: str | None = None
    gmail_password: str | None = None
    gmail_folder: str | None = None


def save_status(status: dict):
    try:
        with open(STATUS_FILE, "w", encoding="utf-8") as f:
            json.dump(status, f, indent=2)
    except Exception:
        pass


def load_status():
    try:
        if STATUS_FILE.exists():
            return json.loads(STATUS_FILE.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {}


@app.post("/run")
def run_endpoint(req: RunRequest, background: BackgroundTasks):
    job_id = uuid.uuid4().hex[:12]
    log_path = str(LOG_DIR / f"run_{job_id}.log")

    env = {}
    if req.gmail_username:
        env["GMAIL_USERNAME"] = req.gmail_username
    if req.gmail_password:
        env["GMAIL_PASSWORD"] = req.gmail_password
    if req.gmail_folder:
        env["GMAIL_FOLDER"] = req.gmail_folder

    status = load_status()
    status[job_id] = {"status": "queued", "log": log_path, "started": None, "finished": None}
    save_status(status)

    def _background():
        status = load_status()
        status[job_id]["status"] = "running"
        status[job_id]["started"] = None
        save_status(status)

        # run and capture
        run_extraction(env, log_path)

        status = load_status()
        status[job_id]["status"] = "finished"
        status[job_id]["finished"] = None
        save_status(status)

    thread = threading.Thread(target=_background, daemon=True)
    thread.start()

    return {"job_id": job_id, "log": log_path}


@app.get("/status/{job_id}")
def get_status(job_id: str, tail: int = 2000):
    status = load_status()
    if job_id not in status:
        raise HTTPException(status_code=404, detail="job_id not found")

    entry = status[job_id]
    log_path = entry.get("log")
    log_text = ""
    if log_path and os.path.exists(log_path):
        try:
            with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
                f.seek(0, os.SEEK_END)
                size = f.tell()
                if size > tail:
                    f.seek(size - tail)
                log_text = f.read()
        except Exception as e:
            log_text = f"Error reading log: {e}"

    return {"job_id": job_id, "status": entry.get("status"), "log": log_text}
