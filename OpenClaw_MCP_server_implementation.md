# OpenClaw MCP Server Implementation

## Overview

This document describes the implementation strategy for deploying `Read_Medium_From_Gmail` as an MCP (Model Context Protocol) server for OpenClaw.

---

## 1. Existing MCP Server Implementations

The project has **two MCP server implementations** with different execution methods:

### 1.1 FastAPI HTTP Server (`fastapi_server.py`)

| Aspect | Details |
|--------|---------|
| File | `mcp_server/fastapi_server.py` |
| Transport | HTTP (port 8000) |
| Execution | Long-running server process |
| Endpoint | `POST /run`, `GET /status/{job_id}` |
| Usage | Trigger extraction via curl |
| Status | Local development only |

### 1.2 GitHub CLI Adapter (`github_mcp_adapter.py`)

| Aspect | Details |
|--------|---------|
| File | `mcp_server/github_mcp_adapter.py` |
| Transport | stdio (stdin/stdout) |
| Execution | One-shot CLI, reads JSON from stdin, runs, exits |
| Usage | `echo '{...}' \| python mcp_server/github_mcp_adapter.py` |
| Status | ✅ Tested with GitHub Actions + cron schedule |

---

## 2. OpenClaw Deployment Decision

### Chosen Approach: Stdio-Based MCP Server

For OpenClaw deployment, we use the **stdio transport** method, NOT FastAPI HTTP.

**Why stdio instead of HTTP:**
- OpenClaw supports stdio-based MCP servers natively via config
- No additional server/hosting required
- Simpler deployment (just a Python script)
- Already familiar pattern (GitHub Actions uses this)

### File Structure for OpenClaw

| File | Purpose | Keep Unchanged? |
|------|---------|-----------------|
| `github_mcp_adapter.py` | CLI one-shot runner for GitHub Actions | ✅ Yes |
| `stdio_mcp_server.py` | NEW - Full MCP protocol server for OpenClaw | ❌ New file |
| `_runner.py` | Core extraction logic | ✅ Yes - reused |

**Key decision:** Do NOT modify `github_mcp_adapter.py` - it's tested and working with GitHub cron. Create a new file for OpenClaw.

---

## 3. Implementation: stdio_mcp_server.py

### What It Does

The new MCP server implements the full MCP protocol (JSON-RPC over stdio):

1. **Stays running** - listens for JSON-RPC messages on stdin
2. **Advertises tools** - responds to `tools/list` with available capabilities
3. **Executes tools** - responds to `tools/call` when AI requests an action

### Tools to Expose

| Tool | Description |
|------|-------------|
| `run_extraction` | Trigger Gmail extraction (reads Medium emails) |
| `list_articles` | List available articles from JSON files |
| `get_article` | Retrieve specific article by ID or title |

### Reuse of _runner.py

The existing `_runner.py` provides the core extraction logic:
- Imports and runs `Read_Medium_From_Gmail.main()`
- Handles environment variables
- Captures logs

This is reused in both `github_mcp_adapter.py` and `stdio_mcp_server.py`.

---

## 4. Credential Management for OpenClaw

### Security Concern

**Plaintext credentials are dangerous:**
- OpenClaw stores API keys in plaintext in `~/.openclaw/openclaw.json` by default
- Any MCP server or tool with file access can read those credentials
- Environment variables can potentially be exposed via tool calls

### Recommended Solution: SecretRef Pattern

Use OpenClaw's `${VAR}` reference pattern:

```json
// In openclaw.json - credentials NOT embedded
{
  "mcpServers": {
    "read-medium-from-gmail": {
      "command": "python",
      "args": ["mcp_server/stdio_mcp_server.py"],
      "env": {
        "GMAIL_USERNAME": "${GMAIL_USERNAME}",
        "GMAIL_PASSWORD": "${GMAIL_PASSWORD}",
        "GMAIL_FOLDER": "${GMAIL_FOLDER}"
      }
    }
  }
}
```

### Setup Instructions

1. **Set credentials on the machine running OpenClaw:**
   ```bash
   # Option A: Environment variables (better)
   export GMAIL_USERNAME="your-email@gmail.com"
   export GMAIL_PASSWORD="app-specific-password"
   export GMAIL_FOLDER="[Gmail]/All Mail"  # optional
   ```

2. **Or use system keychain (most secure):**
   - macOS: Store in Keychain
   - Configure OpenClaw to read from keychain via SecretRef
   - Credentials never touch any config file

### Security Comparison

| Method | Security Level | Notes |
|--------|----------------|-------|
| Plaintext in MCP config | ❌ Dangerous | Avoid |
| `${VAR}` reference | ✅ Better | Credentials in machine env only |
| System keychain | ✅✅ Best | Credentials in OS keychain |

---

## 5. Pros/Cons Summary

### FastAPI HTTP Method (Rejected for OpenClaw)

| Pros | Cons |
|------|------|
| Async, scalable | Requires additional hosting |
| Built-in status tracking | Needs public HTTPS URL |
| Production-ready patterns | More complex deployment |
| Matches some MCP servers | Not needed for this use case |

### Stdio Method (Chosen for OpenClaw)

| Pros | Cons |
|------|------|
| No additional server needed | Basic protocol implementation required |
| Native OpenClaw support | Limited to local execution |
| Simple Python script | No real-time status from remote |
| Already tested (GitHub Actions) | Less suitable for multi-user scenarios |

---

## 6. Files to Create/Modify

### New Files

1. **`mcp_server/stdio_mcp_server.py`** - MCP protocol server
   - Implements JSON-RPC over stdio
   - Exposes 3 tools: run_extraction, list_articles, get_article
   - Reuses `_runner.py` for extraction

2. **`OPENCLAW_DEPLOYMENT.md`** - Setup documentation
   - OpenClaw config snippet
   - Environment variable setup
   - Available tools reference

### Existing Files (Unchanged)

| File | Reason |
|------|--------|
| `github_mcp_adapter.py` | Working with GitHub Actions cron |
| `_runner.py` | Core logic - reuse, don't duplicate |
| `Read_Medium_From_Gmail.py` | Never modify - keep original |

---

## 7. Deployment Workflow

### Important: How OpenClaw Installs MCP Servers

**OpenClaw does NOT automatically install MCP servers from GitHub.** There are two options:

#### Option A: OpenClaw Launch (Managed)
- Publish to ClawHub marketplace
- Users click to install from OpenClaw's web interface
- Requires marketplace submission

#### Option B: Self-Hosted (Manual Setup)
1. **Clone this repository** to the machine running OpenClaw
2. **Install dependencies** (`pip install -e .` or `uv pip install -e .`)
3. **Set environment variables** for Gmail credentials
4. **Configure** `openclaw.json` with the MCP server path
5. **Restart OpenClaw** to load the new MCP server

### Steps for Self-Hosted Deployment

```bash
# 1. Clone repo to the OpenClaw machine
git clone https://github.com/YOUR_USERNAME/Medium_Email.git
cd Medium_Email

# 2. Install dependencies
pip install -e .

# 3. Set Gmail credentials (in shell profile)
export GMAIL_USERNAME="your-email@gmail.com"
export GMAIL_PASSWORD="app-password"

# 4. Add to openclaw.json (see Section 10)

# 5. Restart OpenClaw
```

### After Installation

Once configured, users just **ask OpenClaw naturally**:
- "Extract my Medium articles from Gmail" → calls `run_extraction`
- "Show me articles about Python" → calls `get_article("Python")`
- "List recent articles" → calls `list_articles()`

The AI decides which tool to call based on the user's request.

---

## 8. Service Name

**Service Name:** `Read.Medium.From.Gmail`

This name will be used in:
- MCP server identification in OpenClaw config
- Documentation and tooling
- GitHub repository references

---

## 9. Available MCP Tools

### run_extraction

Trigger the Gmail extraction to fetch new Medium articles.

**Parameters:**
- `gmail_folder` (optional, string): Gmail folder to search. Default: "[Gmail]/All Mail"

**Returns:** Status message with log file location

**Example:**
```
Run the extraction to fetch Medium articles from Gmail
```

### list_articles

List available Medium articles from stored JSON files.

**Parameters:**
- `limit` (optional, integer): Maximum number of articles to return. Default: 20

**Returns:** JSON with article summaries (id, title, url, author, published, tags)

**Example:**
```
List the latest Medium articles
```

### get_article

Search for articles by title keyword (case-insensitive, returns all matches).

**Parameters:**
- `search_term` (required, string): Title keyword to search for

**Returns:** JSON with all matching articles

**Natural language usage:**
- "Find articles about Python"
- "Search for automation articles"
- "Show me articles matching 'machine learning'"

---

## 10. OpenClaw Configuration

### Prerequisite: Install Dependencies

The MCP server requires Python 3.12+ with the `mcp` package:

```bash
# Using uv (recommended)
uv pip install "mcp>=1.0.0"

# Or using pip
pip install "mcp>=1.0.0"
```

### Environment Setup

Before configuring OpenClaw, set the Gmail credentials as environment variables on the machine running OpenClaw:

```bash
# Add to your shell profile (.bashrc, .zshrc, etc.)
export GMAIL_USERNAME="your-email@gmail.com"
export GMAIL_PASSWORD="your-app-specific-password"
export GMAIL_FOLDER="[Gmail]/All Mail"  # optional
```

### OpenClaw Config

Add this to your `openclaw.json` or via the OpenClaw web interface:

```json
{
  "mcpServers": {
    "read-medium-from-gmail": {
      "command": "python",
      "args": ["mcp_server/stdio_mcp_server.py"],
      "env": {
        "GMAIL_USERNAME": "${GMAIL_USERNAME}",
        "GMAIL_PASSWORD": "${GMAIL_PASSWORD}",
        "GMAIL_FOLDER": "${GMAIL_FOLDER}"
      }
    }
  }
}
```

### Testing the MCP Server

Test locally before deploying to OpenClaw:

```bash
# List available tools
cd /Users/syuen/Medium_Email
python -c "from mcp_server.stdio_mcp_server import list_articles; print(list_articles(limit=5))"
```

---

## 11. Implementation Status

| Component | Status | Notes |
|-----------|--------|-------|
| `mcp_server/stdio_mcp_server.py` | ✅ Complete | Full MCP protocol implementation |
| `list_articles` tool | ✅ Working | Tested locally |
| `get_article` tool | ✅ Working | Tested locally |
| `run_extraction` tool | ✅ Implemented | Uses _runner.py |
| OpenClaw config | ✅ Documented | Ready for use |
| pyproject.toml | ✅ Updated | Added mcp dependency |
