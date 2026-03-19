"""MCP Server for Read.Medium.From.Gmail service.

This implements a stdio-based MCP server that exposes tools for:
- run_extraction: Trigger Gmail extraction
- list_articles: List available articles from JSON files
- get_article: Retrieve a specific article
"""

import os
import sys
import json
import glob
from pathlib import Path
from typing import Any

# No need: Add parent directory to path so mcp_server package can be found when run as a script
# sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Read.Medium.From.Gmail")

# In the run-time, APP_DIR should be the directory containing this script
# e.g., /home/simon/.openclaw/mcp_servers/read-medium-from-gmail
APP_DIR = Path(__file__).resolve().parent
LOG_DIR = APP_DIR / "logs"

# Set process working directory to APP_DIR
# Need this to make sure all file operations are relative to the app directory where the JSON files are stored
# This is important when the server is run from a different directory,
# ensuring it can find the article JSON files and write logs correctly.
os.chdir(APP_DIR)

def get_article_files() -> list[str]:
    """Find all article JSON files in the app directory."""
    patterns = [
        APP_DIR / "medium_articles*.json",
        APP_DIR / "medium_articles_master*.json",
    ]
    files = []
    for pattern in patterns:
        files.extend(glob.glob(str(pattern)))
    return sorted(files, key=lambda x: os.path.getmtime(x), reverse=True)


def load_articles_from_file(filepath: str) -> list[dict]:
    """Load articles from a JSON file."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            elif isinstance(data, dict) and "articles" in data:
                return data["articles"]
            return []
    except (json.JSONDecodeError, FileNotFoundError):
        return []


def find_articles_by_title(search_term: str) -> list[dict]:
    """Find all articles matching the search term in title (case-insensitive, partial match)."""
    matches = []
    search_lower = search_term.lower()

    for filepath in get_article_files():
        articles = load_articles_from_file(filepath)
        for article in articles:
            title = article.get("title", "")
            if title and search_lower in title.lower():
                if article not in matches:
                    matches.append(article)

    return matches


@mcp.tool()
def run_extraction(gmail_folder: str = "Inbox") -> str:
    """Run the Medium email extraction from Gmail.

    This tool triggers the Read_Medium_From_Gmail.py script to fetch
    new Medium articles from your Gmail account.

    Args:
        gmail_folder: The Gmail folder to search (default: "Inbox")

    Returns:
        Status message with log file location
    """
    import uuid

    env = {}
    if os.environ.get("GMAIL_USERNAME"):
        env["GMAIL_USERNAME"] = os.environ["GMAIL_USERNAME"]
    if os.environ.get("GMAIL_PASSWORD"):
        env["GMAIL_PASSWORD"] = os.environ["GMAIL_PASSWORD"]
    if gmail_folder:
        env["GMAIL_FOLDER"] = gmail_folder

    if not env.get("GMAIL_USERNAME") or not env.get("GMAIL_PASSWORD"):
        return "Error: GMAIL_USERNAME and GMAIL_PASSWORD must be set in environment"

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    job_id = uuid.uuid4().hex[:12]
    log_path = str(LOG_DIR / f"openclaw_run_{job_id}.log")

    try:
        # Import _runner module directly by file path to avoid package issues
        import importlib.util
        runner_path = Path(__file__).resolve().parent / "_runner.py"
        spec = importlib.util.spec_from_file_location("_runner", runner_path)
        runner_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(runner_module)
        
        runner_module.run_extraction(env, log_path)
        return f"Extraction completed. Log file: {log_path}"
    except Exception as e:
        return f"Error during extraction: {str(e)}"


@mcp.tool()
def list_articles(limit: int = 20) -> str:
    """List available Medium articles from stored JSON files.

    This tool reads from the most recent article JSON files and returns
    a summary of available articles.

    Args:
        limit: Maximum number of articles to return (default: 20)

    Returns:
        JSON string with list of article summaries
    """
    files = get_article_files()
    if not files:
        return json.dumps({"error": "No article files found", "articles": []})

    all_articles = []
    for filepath in files[:3]:
        articles = load_articles_from_file(filepath)
        all_articles.extend(articles)

    unique_articles = {}
    for article in all_articles:
        article_id = article.get("id") or article.get("url", "")
        if article_id and article_id not in unique_articles:
            unique_articles[article_id] = article

    unique_list = list(unique_articles.values())[:limit]

    summaries = []
    for article in unique_list:
        summaries.append(
            {
                "id": article.get("id", ""),
                "title": article.get("title", "Untitled"),
                "url": article.get("url", ""),
                "author": article.get("author", "Unknown"),
                "published": article.get("published", ""),
                "tags": article.get("tags", [])[:3],
            }
        )

    return json.dumps(
        {
            "total": len(unique_articles),
            "showing": len(summaries),
            "articles": summaries,
        },
        indent=2,
    )


@mcp.tool()
def get_article(search_term: str) -> str:
    """Get detailed information about specific Medium articles by title search.

    Search for articles by title keyword (case-insensitive, partial match).
    Returns all matching articles.

    Args:
        search_term: The title keyword to search for

    Returns:
        JSON string with all matching articles or error message
    """
    if not search_term:
        return json.dumps({"error": "search_term is required"})

    articles = find_articles_by_title(search_term)

    if not articles:
        return json.dumps(
            {
                "error": f"No articles found matching: {search_term}",
                "hint": "Try using list_articles() to see available articles",
            }
        )

    return json.dumps(
        {
            "query": search_term,
            "total_matches": len(articles),
            "articles": articles,
        },
        indent=2,
        ensure_ascii=False,
    )


if __name__ == "__main__":
    mcp.run(transport="stdio")
