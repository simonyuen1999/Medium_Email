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
4. Openlclaw calling `stdio_mcp_server.py'

* stdio_mcp_server.py
  * gets three enviroment variables from Openclaw environment setup (see below)
  * statement: from mcp.server.fastmcp import FastMCP
  * statement: mcp = FastMCP("Read.Medium.From.Gmail")
  * ... ***Waiting be called*** ...
  * statement: from `mcp_server._runner` import run_extraction as run_extractor.
* _runner.py gets env_vars and (this is hard coded the name)
* _runner.py statement: module = importlib.import_module("Read_Medium_From_Gmail.py")
* Then, spec.loader.exec_module(module)

---

# Add this MCP.server to Openclaw

Open `~/.openclaw/openclaw.json` file, find **mcpServers** section, and add the following into this section

```
"read-medium-from-gmail": {
  "command": "/Users/simon/.openclaw/mcp_servers/read-medium-from-gmail/.venv/bin/python"
  "args": ["stdio_mcp_server.py"],
  "env": {
     "NOT_IMPORTANT_VAR": "${GMAIL_FOLDER}"
  }
}
```

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

The development was based on Python 3.14, but Ubuntu only has Python 3.13.  So, we manually creates the MCP server .venv environment with Python 3.14.   In the manual setup testing, we already did the following for this .venv environment

1. sudo apt install python3-full

* Note: Ubuntu 24.04+ ships Python with PEP 668 protection, which prevents:
  * pip installing into system Python
  * pip installing into venvs created from system Python unless python3-full is installed

2. Prepare, install modules, testing

```
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