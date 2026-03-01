# Read.Medium.From.Gmail MCP Server

An MCP (Model Context Protocol) server that provides tools to:
- Extract Medium articles from Gmail
- List available articles from stored JSON files
- Search articles by title

## Installation

### 1. Clone this repository

Git repo name is simonyuen1999/Medim_Emai.git

```bash
git clone https://github.com/simonyuen1999/Medium_Email.git
cd Medium_Email
```

### 2. Install dependencies

```bash
pip install -e .
# OR
uv pip install -e .
```

### 3. Set Gmail credentials

Push your GMAIL ID and Password in the environment variables.

```bash
export GMAIL_USERNAME="your-email@gmail.com"
export GMAIL_PASSWORD="your-app-specific-password"
export GMAIL_FOLDER="[Gmail]/Inbox"  # optional
```

### 4. Configure OpenClaw

Add to your `openclaw.json`:

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

## Available Tools

Once installed, you can ask OpenClaw to:

| Tool | Usage |
|------|-------|
| `run_extraction` | "Run the Medium extraction to fetch new articles from Gmail" |
| `list_articles` | "Show me the latest Medium articles" |
| `get_article` | "Find articles about Python automation" |

### Examples

**Extract new articles:**
```
User: Run the Medium email extraction
OpenClaw: [calls run_extraction tool]
```

**Search articles:**
```
User: Find articles about Python
OpenClaw: [calls get_article with "Python" search term]
```

**List articles:**
```
User: Show me the recent articles
OpenClaw: [calls list_articles]
```

## MCP Server Name

- **Display name:** Read.Medium.From.Gmail
- **Config key:** read-medium-from-gmail

## Troubleshooting

### Tool not found
Ensure the MCP server is configured in `openclaw.json` and OpenClaw has been restarted.

### Credentials error
Make sure `GMAIL_USERNAME` and `GMAIL_PASSWORD` environment variables are set on the machine running OpenClaw.
