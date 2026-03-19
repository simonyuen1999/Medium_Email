# Deploy this MCP server to Openclaw

## Introduction of this program structure

This program was created in Mac environment.  After it was working on Mac CLI, I wrap around the program with MCP.server with Stdio integation method.

Since all the functions are integrated into one  `Read_Medium_From_Gmail.py` python code.  It only requires three environment variables to work:

* GMAIL_FOLDER=Inbox
* GMAIL_PASSWORD=xxxxxxxxxx
* GMAIL_USERNAME=simonyuen1999.hotmail@gmail.com

---

## How MCP.server works in Openclaw (Ubuntu)

At this moment, Openclaw cannot automatically install MCP.server from GitHub repo.   It is still a manual deployment process as follows,     Background:  Each MCP server gets its own folder, so we will

1. create `~/.openclaw/mcp_servers/read-medium-from-gmail/` directory
2. copy file from repo directory to above `read-medium-from-gmail` directory

* Read_Medium_From_Gmail.py
* mcp_server/stdio_mcp_server.py
* mcp_server/_runner.py

3. Prepare the following file in `read-medium-from-gmail` directory

* Python `requirements.txt` file
* Create `mcp.json` file
  This is folder structure

```
~/.openclaw/mcp_servers/
    read-medium-from-gmail/
        mcp.json
        stdio_mcp_server.py
        _runner.py
        Read_Medium_From_Gmail.py
        requirements.txt   ← optional but recommended
```

## The MCP.server mcp.json file

OpenClaw has a fixed, built‑in directory `mcp_servers` where it automatically looks for MCP servers:

```
{
  "name": "read-medium-from-gmail",
  "version": "1.0.0",
  "display_name": "Read.Medium.From.Gmail",
  "entry_point": "stdio_mcp_server.py",
  "language": "python",
  "commands": {
    "run_extraction": {
      "description": "Fetch Medium articles from Gmail"
    },
    "list_articles": {
      "description": "List stored Medium articles"
    },
    "get_article": {
      "description": "Search Medium articles by keyword",
      "arguments": [
        { "name": "query", "type": "string" }
      ]
    }
  }
}
```

## The MCP process starting and calling sequence

1. Openclaw starts a MCP server as external process
2. This process will not terminate as long as Openclaw process is running
3. It will execute pip to install the Python requirement
4. Openlclaw calling `stdio_mcp_server.py`

* **stdio_mcp_server.py**
  * gets three enviroment variables from Openclaw environment setup (see below)
  * statement: `from mcp.server.fastmcp import FastMCP`
  * statement: `mcp = FastMCP("Read.Medium.From.Gmail")`
  * ... ***Waiting be called*** ...
  * statement: `from mcp_server._runner import run_extraction as run_extractor.`
* **_runner.py** (Stdio method) gets env_vars and (this is hard coded the name)
* **_runner.py** statement:  `module = importlib.import_module("Read_Medium_From_Gmail.py")`
* Then calling `spec.loader.exec_module(module)`

---

# Add this MCP.server to Openclaw

This is .openclaw/config/mcporter.json file
```
"read-medium-from-gmail": {
  "command": "/Users/simon/.openclaw/mcp_servers/read-medium-from-gmail/.venv/bin/python"
  "args": ["/home/simon/.openclaw/mcp_servers/read-medium-from-gmail/stdio_mcp_server.py"],
  # "cwd": "/home/simon/.openclaw/mcp_servers/read-medium-from-gmail",
  "env": {
     "NOT_IMPORTANT_VAR": "${GMAIL_FOLDER}"
  }
}
```
We confirm OpenClaw resolves args relative to its config directory (`/home/simon/.openclaw/config/`), not relative to the `cwd` setting.

The flow is:

1. OpenClaw reads config from /home/simon/.openclaw/config/mcporter.json
2. Set the relative paths to from /home/simon/.openclaw/config/
3. Reason: we need the full path in args parameter
4. Spawns process with the resolved script path
5. Sets process working directory to cwd (This is not correct, cwd does not work)
Solution: Keep args to use absolute path

In our testing, cwd has no effect.  We will skill / ignore the `cwd` parameter in the mcporter.json file.


## Openclaw 3.13 uses `mcporter` to manage MCP servers

**mcporter is not a subprocess.**  It can be executed when **openclaw gateway** is not running.

* mcporter config list
* mcporter config get <name> [--json]
* mcporter doctor
* mcporter add [option] <name> name [target]
* mcporter remove name

These daemon sub-commands do not make sense for come and go process

* mcporter daemon stop
* mcporter daemon start
* mcporter daemon status

The following mcporter is calling read medium from gmail entry point

* **mcporter call read-medium-from-gmail.list_articles**
* **mcporter call read-medium-from-gmail.run_extraction**

Observation

* When I execute `mcporter` command in `.openclaw` directory (only this dir), it uses `.openclaw/config/mcporter.json` file.
* When I execute `mcporter` elswhere, it uses `$HOME/.mcporter/mcporter.json` file.

Use this command to add our MCP server

``` shell
$ mcporter config add read-medium-from-gmail \
   --command "/home/simon/.openclaw/mcp_servers/read-medium-from-gmail/.venv/bin/python" \
   --arg "/home/simon/.openclaw/mcp_servers/read-medium-from-gmail/stdio_mcp_server.py" \
   --env "NOT_IMP_VAR=Testing only"
```

1. `mcporter config add` doesn't have a `--cwd` flag
2. cwd problem

* Openclaw set program cwd to  `/home/simon/.openclaw/config/`
* The paths in **args** are resolved from the config directory, not from cwd.
* Then: set process working directory to cwd.

## MCP worksflow

> **The following are not completely correct** since Openclaw switch to `mcporter`.
> * Openclaw finds `mcp_servers/read-medium-from-gmail` setup
> * Load `mcp.json`
> * Launch the command in that directory
> * keep the MCP server running as a background process
>
> So the folder name is the link between:
>
> * the directory on disk
> * the entry in `openclaw.json`
> * the MCP server identity
>
> Note: "PYTHONPATH": "/Users/simon/.openclaw/mcp_servers/read-medium-from-gmail" is not needed.

## Python dependency and deploy to production (Openclaw system)

The development was based on Python 3.14, but Ubuntu only has Python 3.13.  So, we manually creates the MCP server .venv environment with Python 3.14.   In the manual setup testing, we already did the following for this .venv environment

1. sudo apt install python3-full

* Note: Ubuntu 24.04+ ships Python with PEP 668 protection, which prevents:
  * pip installing into system Python
  * pip installing into venvs created from system Python unless python3-full is installed

2. Prepare, install modules, testing

``` shell
cd ~/.openclaw/mcp_servers/read-medium-from-gmail
python3.14 -m venv .venv
source .venv/bin/activate
pip install beautifulsoup4 lxml python-dotenv FastMCP
pip list > requirements.txt
```

The `command` line in `openclaw.json` file is pointing to **already (modules) setup and tested** .venv environment, so the `requirements.txt` file is included in the MCP `~/.openclaw/mcp_servers/read-medium-from-gmail/` directory.

## Why GMAIL_xxx env var are not defined in `openclaw.json`?

We defined these three GMAIL values in Openclaw 3.13 as env variable.  Openclaw will protect any sensitive env var from normal chat.   When Openclaw starts MCP server, all its env var will be passed to MCP process.   Since `stdio_mcp_serer.py` will get env var, so no need to define them in `openclaw.json` file.

---

# Appendix: pip, uv, requirsments.txt

Auto-generate from repo

```
pip install pipreqs
pipreqs . --force
```

However, the requirements.txt file has all system modules, pipreqs over-detects is the common issue.

uv keeps a clean dependency graph, but uv doesn't automatically export a minimal requirements.txt file.

```
uv venv --python 3.14
source .venv/bin/activate
uv add beautifulsoup4 lxml python-dotenv FastMCP
uv pip list
uv remove <package>
uv export --format requirements-txt > requirements.txt
```
