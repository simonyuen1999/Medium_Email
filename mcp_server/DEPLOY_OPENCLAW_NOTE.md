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
        requirements.txt          ← optional but recommended
           /workspace/
              config/
                 mcporter.json    ← this is the first priority (Openclaw setup)
or
~/.mcporter/mcporter.json         ← this is the second priority (system wide setup) 
```

## The MCP.server mcp.json file

**Is this true?** OpenClaw has a fixed, built‑in directory `mcp_servers` where it automatically looks for MCP servers:

``` XML
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

The following is my observation.  In the Appendix, it is official explaination.

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

This is **wrong** `.openclaw/config/mcporter.json` file, <span style='color: red;'>misleaded by LLM</span>.

``` XML
"read-medium-from-gmail": {
  "command": "/Users/simon/.openclaw/mcp_servers/read-medium-from-gmail/.venv/bin/python"
  "args": ["/home/simon/.openclaw/mcp_servers/read-medium-from-gmail/stdio_mcp_server.py"],
  "env": {
     "NOT_IMPORTANT_VAR": "${GMAIL_FOLDER}"
  }
}
```

**Note**: `cwd` is not used in this config `mcporter.json` file.

**TODO to find out**: During debugging, we confirm OpenClaw resolves args relative to its config directory (`/home/simon/.openclaw/config/`), not relative to the `cwd` setting.  **WHY**?

The flow is:

1. OpenClaw reads config from /home/simon/.openclaw/config/mcporter.json **Wrong, see Appendix below**
2. Set the relative paths to from /home/simon/.openclaw/config/ **Correct?**
3. **Reason**: we need the ***full path in args parameter***
4. Spawns process with the resolved script path
5. Sets process working directory to cwd (This is not correct, cwd does not work)
Solution: Keep args to **use absolute path**

In our testing, cwd has no effect.  We will skill / ignore the `cwd` parameter in the `mcporter.json` file.

## Openclaw 3.13 uses `mcporter` to manage MCP servers

**mcporter is not a subprocess.**  It can be executed when **openclaw gateway** is not running.

* mcporter config list
* mcporter config get \<name\> [--json]
* mcporter doctor
* mcporter add [option] \<name\> name [target]
* mcporter remove \<name\>

These daemon sub-commands do not make sense for come and go process

* mcporter daemon stop
* mcporter daemon start
* mcporter daemon status

The following mcporter is calling read medium from gmail entry point

* **mcporter call read-medium-from-gmail.list_articles**
* **mcporter call read-medium-from-gmail.run_extraction**

### My Observation

* When I execute `mcporter` command in `.openclaw` directory (only this dir), it uses `.openclaw/config/mcporter.json` file.
* When I execute `mcporter` elswhere, it uses `$HOME/.mcporter/mcporter.json` file.

Use this command to add our MCP server

``` shell
$ mcporter config add read-medium-from-gmail \
   --command "/home/simon/.openclaw/mcp_servers/read-medium-from-gmail/.venv/bin/python" \
   --arg "/home/simon/.openclaw/mcp_servers/read-medium-from-gmail/stdio_mcp_server.py" \
   --env "NOT_IMP_VAR=Testing only"
```

This command adds and modifies system wide `~/.mcporter/mcporter.json` file.

1. `mcporter config add` doesn't have a `--cwd` flag
2. cwd problem

* Openclaw set program cwd to  `/home/simon/.openclaw/config/` **Is it correct?**
* The paths in **args** are resolved from the config directory, not from cwd.
* Then: set process working directory to cwd.

## MCP worksflow

> **The following are not completely correct** since Openclaw switch to `mcporter`.
>
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
> Note: "**PYTHONPATH**": "/Users/simon/.openclaw/mcp_servers/read-medium-from-gmail" is not needed.

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

# Appendix: pip, uv, requirsments.txt, and mcporter

## pip and uv
First auto-generate from development environment

``` shell
pip install pipreqs
pipreqs . --force
```

However, the requirements.txt file has all system modules, pipreqs over-detects is the common issue.

uv keeps a clean dependency graph, but uv doesn't automatically export a minimal requirements.txt file.

``` shell
uv venv --python 3.14
source .venv/bin/activate
uv add beautifulsoup4 lxml python-dotenv FastMCP
uv pip list
uv remove <package>
uv export --format requirements-txt > requirements.txt
```

## mcporter of Architecture Overview

**McPorter** is a standalone MCP (Model Context Protocol) client CLI. **OpenClaw** integrates with it to expose MCP tools to agents. They communicate via McPorter's HTTP API (when running as a daemon) or CLI calls.

## The Full Sequence

``` diagram
┌─────────┐     ┌──────────┐     ┌──────────┐     ┌─────────────┐     ┌──────────┐
│  User   │────▶│ OpenClaw │────▶│ McPorter │────▶│ MCP Server  │────▶│ External │
│  Chat   │     │  Agent   │     │  Client  │     │ (stdio/sse) │     │  APIs    │
└─────────┘     └──────────┘     └──────────┘     └─────────────┘     └──────────┘
                      ▲                │                  │
                      │                ▼                  ▼
                      │         ┌──────────┐        ┌──────────┐
                      └─────────│  Result  │◀───────│  Gmail/  │
                                │          │        │  Medium  │
                                └──────────┘        └──────────┘
```

### Step-by-Step

1. **Chat Input** → OpenClaw receives your message via the gateway (webchat, Telegram, etc.)

2. **Agent Processing** → The LLM (Kimi in this case) receives the conversation context. If it decides an MCP tool is needed, it generates a tool call request.

3. **OpenClaw → McPorter** → OpenClaw calls McPorter via:
   - **HTTP API** (if `mcporter server` is running): `POST /call` with tool name + params
   - **CLI** (if no daemon): `mcporter call <server>.<tool> --json '{params}'`

4. **McPorter → MCP Server** → McPorter:
   - Looks up the server config from `mcporter.json`
   - Spawns the server process (stdio) or connects to SSE endpoint
   - Sends the JSON-RPC request: `tools/call` with the tool name and arguments

5. **MCP Server Execution** → The Python/Node server:
   - Receives the JSON-RPC call
   - Executes the actual logic (e.g., fetches Gmail, queries an API)
   - Returns result via stdout (stdio) or HTTP response (SSE)

6. **Result Propagation** → Result flows back:
   ```
   MCP Server → McPorter → OpenClaw → LLM → User
   ```

7. **LLM Formats Response** → The agent receives the tool result and incorporates it into its reply to you.

## How OpenClaw Discovers MCP Tools

When OpenClaw starts (or on config reload):

1. It reads `mcporter.json` from configured paths
2. Calls `mcporter list` or queries the daemon to get available tools
3. Converts each MCP tool definition into OpenClaw's internal tool format
4. Injects those tools into the agent's system prompt so the LLM knows they're available

## Key Files

| File | Purpose |
|------|---------|
| `workspace/config/mcporter.json` | MCP server definitions (command, args, env) |
| `~/.openclaw/mcp_servers/` | Where your actual server code lives |
| `mcporter` binary | The MCP client that manages connections |

mcporter system wide config file: ~/.mcporter/mcporter.json

## Is It Dynamic?

**Partially.** McPorter reads `mcporter.json` at startup. If you edit it:
- **If using daemon**: Restart `mcporter server` or send SIGHUP
- **If using CLI**: Each invocation reads fresh config

OpenClaw typically discovers tools at session start, so new servers added to `mcporter.json` may need an OpenClaw restart (or config reload) to appear in the agent's tool list.

---

The config resolution depends on whether you're using **McPorter CLI directly** vs **OpenClaw calling McPorter**.

## McPorter CLI Config Resolution

When you run `mcporter` commands in your terminal, it looks for config in this order:

1. **`--config /path/to/file`** — explicit flag (highest priority)
2. **`MCPorter_CONFIG` env var** — if set, uses that path
3. **`./mcporter.json`** — current working directory
4. **`~/.mcporter/mcporter.json`** — user home directory
5. **`/etc/mcporter/mcporter.json`** — system-wide (if exists)

So yes — **your cwd matters**. If you're in `~/projects/foo/` and run `mcporter list`, it looks for `./mcporter.json` first. If not found, it falls back to `~/.mcporter/`.

---

## OpenClaw's Behavior

OpenClaw doesn't just "run mcporter CLI from random cwd." It configures the config path explicitly:

| How OpenClaw Calls McPorter | Config Source |
|-----------------------------|---------------|
| Via `mcporter server` daemon | Daemon started with `--config` or env var pointing to your workspace file |
| Via direct CLI calls | OpenClaw sets `--config /path/to/workspace/config/mcporter.json` |

So **OpenClaw pins the config** — it doesn't wander based on where the gateway binary happens to be running.

---

## Your Situation

You have:
- `~/.mcporter/mcporter.json` (global/user default)
- `workspace/config/mcporter.json` (project-specific)

**In terminal:**
```bash
cd ~/.openclaw/workspace && mcporter list   # → reads workspace/config/mcporter.json
cd ~ && mcporter list                       # → reads ~/.mcporter/mcporter.json
mcporter --config workspace/config/mcporter.json list  # → explicit, cwd doesn't matter
```

**In OpenClaw:**
- Always uses `workspace/config/mcporter.json` (explicitly configured)
- Ignores `~/.mcporter/` even if it exists

---

## Pro Tip: Check Which Config is Loaded

```bash
# See which file mcporter is actually using
mcporter --config workspace/config/mcporter.json list --verbose
# or
MCPorter_CONFIG=workspace/config/mcporter.json mcporter list
```

If you want consistency between CLI and OpenClaw, set the env var in your shell:

```bash
export MCPorter_CONFIG=/home/simon/.openclaw/workspace/config/mcporter.json
```

Then `mcporter list` from any directory will use the workspace config.
---

> OpenClaw calls 'mcporter list' command or queries the daemon to get available tools. How I can find out OpenClaw is > calling CLI or daemon process? How to know McPorter is running on daemon mode, or not?
>
> Interesting finding — there's no explicit McPorter configuration in your openclaw.json. Let me check if OpenClaw > auto-detects McPorter and how it's actually integrated:

Let me check how OpenClaw is configured and whether a McPorter daemon is running.Interesting finding — **there's no explicit McPorter configuration in your `openclaw.json`**. Let me check if OpenClaw auto-detects McPorter and how it's actually integrated:Based on my investigation, here's what I found:

## Current State

**McPorter is NOT running as a daemon:**
```bash
ps aux | grep mcporter  # → No process found
```

**OpenClaw has NO explicit McPorter configuration** in your `~/.openclaw/openclaw.json`.

**How MCP tools are currently working:**
- OpenClaw uses the `mcporter` **CLI command** directly (spawning a new process each time)
- There is **no daemon mode** currently active

---

## How to Check Which Mode OpenClaw Uses

### 1. Check if McPorter daemon is running:
```bash
# Method 1: Process check
ps aux | grep mcporter | grep -v grep

# Method 2: Try to query the daemon HTTP API (default port 8080)
curl http://localhost:8080/list 2>/dev/null || echo "No daemon on port 8080"

# Method 3: Check with mcporter itself
mcporter server status  # (if this command exists in your version)
```

### 2. Check OpenClaw's logs for mcporter calls:
```bash
# Look at session logs to see how mcporter is invoked
cat /tmp/openclaw/openclaw-2026-03-19.log | grep -i mcporter
```

---

## How to Enable Daemon Mode (Optional)

If you want better performance (avoid spawning processes per call), you can start the McPorter daemon:

```bash
# Start daemon explicitly pointing to your config
mcporter server --config /home/simon/.openclaw/workspace/config/mcporter.json --port 8080

# Or use env var
export MCPorter_CONFIG=/home/simon/.openclaw/workspace/config/mcporter.json
mcporter server
```

Then configure OpenClaw to use it by adding to `~/.openclaw/openclaw.json`:
```json
{
  "mcporter": {
    "url": "http://localhost:8080"
  }
}
```

But looking at your setup — **OpenClaw is just shelling out to `mcporter call` CLI each time**. This is fine for occasional use, but daemon mode reduces latency for frequent calls.

---

## Summary

| Question | Answer |
|----------|--------|
| Is McPorter daemon running? | **No** |
| How does OpenClaw call McPorter? | **CLI command** (`mcporter call ...`) |
| Config being used? | `workspace/config/mcporter.json` (passed via `--config` or env) |
| Performance impact? | Slight cold-start per call (spawn process → exec → exit) |