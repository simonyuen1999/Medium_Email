# Agents for Medium_Email

This document describes the project "agents" (scripts and scheduled jobs) used to fetch, process, and browse Medium emails/articles in this repository.

**Purpose**: Centralize instructions for running and maintaining the automated scripts (agents) and scheduled jobs in this repo.

**Common prerequisites**
- Python virtual environment: `ls/` (activate with `source ls/bin/activate`).
- Use the project's `pyproject.toml` for dependency information; install with `python -m pip install -e .` or `python -m pip install -r requirements.txt` if you maintain one.

**Agents**

- **Gmail extractor**
  - Purpose: read Medium-related emails from Gmail and extract article JSONs.
  - Entry point: `Read_Medium_From_Gmail.py`
  - Runner scripts: `run_gmail_extractor.sh`, `cron_run_gmail_extractor.sh`
  - Notes: ensure env is set (see `set_gmail_env.sh`) and venv activated before running.

- **Article merger**
  - Purpose: merge multiple article JSON files into the master store.
  - Entry point: `Merge_Medium_Articles.py`

- **Classifier**
  - Purpose: classify or tag articles.
  - Entry point: `Article_Classifier.py`

- **Browsers / UI**
  - `Medium_Article_Browser.py`, `Web_Article_Browser.py`, `Enhanced_Articles_Tk.py` — local tools to inspect and browse stored articles.

- **Helpers / Maintenance**
  - `fix_titles_v4.py`, `Manual_Edit_Master.py`, `main.py` and other utilities used for data cleanup and workflows.

**How to run locally**
1. Activate venv:

   source ls/bin/activate

2. Load environment variables for Gmail (if needed):

   source set_gmail_env.sh

3. Run an agent, for example:

   python Read_Medium_From_Gmail.py

Or use the provided shell runner:

   ./run_gmail_extractor.sh

**Cron / Production**
- Use `cron_run_gmail_extractor.sh` (or `cron_run_gmail_extractor.sh alias`) for scheduled extraction. Ensure the script activates the virtualenv and sources `set_gmail_env.sh` before invoking the Python script.

**Development notes**
- Virtualenv shipped at `ls/` targets Python 3.14 (see `ls/bin/python3.14`).
- Keep `pyproject.toml` updated when adding dependencies.
- If you add a new agent script, update this file with: name, purpose, entry point, and run instructions.

**Contact / Ownership**
- Primary maintainer: repository owner (see repo metadata). Open an issue or PR for changes to agent behavior or scheduling.

---
Revision: initial AGENTS.md added.
