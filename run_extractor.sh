#!/bin/bash
# Ultimate Medium Articles Daily Workflow
# Complete end-to-end pipeline: Gmail extraction + Processing + Classification + Web generation

echo "⚡ Medium Articles - Ultimate Daily Workflow"
echo "=============================================="
echo "🔄 This will:"
echo "  📧 Extract latest articles from Gmail"
echo "  📚 Update master historical database" 
echo "  🏷️  Classify articles with intelligent tags"
echo "  🌐 Generate web browser interface"
echo "  💾 Create all output files"
echo ""

# Navigate to the script directory
cd "$(dirname "$0")"

# Load Gmail environment variables for non-interactive launchers (cron/launchctl).
if [ -f "$HOME/.gmail_env" ]; then
    # shellcheck disable=SC1090
    source "$HOME/.gmail_env"
fi

# Optional repo-local env file for automation contexts.
if [ -f "./.gmail_env" ]; then
    # shellcheck disable=SC1091
    source "./.gmail_env"
fi

# Fallback: import only GMAIL_ exports from zsh profile.
if [ -f "$HOME/.zshrc" ]; then
    eval "$(grep '^export GMAIL_' "$HOME/.zshrc" 2>/dev/null || true)"
fi

# If still missing creds: prompt only in interactive shells.
if [ -z "${GMAIL_USERNAME:-}" ] || [ -z "${GMAIL_PASSWORD:-}" ]; then
    if [ -t 0 ]; then
        # shellcheck disable=SC1091
        source "./set_gmail_env.sh"
    else
        echo "❌ Gmail credentials not found in non-interactive mode."
        echo "   Create ~/.gmail_env (recommended for launchctl/cron)."
        echo "$(date): Gmail extraction failed - missing environment variables" >> gmail_extractor.log
        exit 1
    fi
fi

export GMAIL_USERNAME
export GMAIL_PASSWORD
export GMAIL_FOLDER="${GMAIL_FOLDER:-Medium}"

# Determine Python command to use
if [ -d ".venv" ]; then
    echo "🔗 Using virtual environment Python..."
    PYTHON_CMD=".venv/bin/python"
elif command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo "❌ Python not found!"
    echo "� Please install Python or set up a virtual environment"
    exit 1
fi

# Log execution status for troubleshooting
echo "$(date): Starting Gmail extraction" >> gmail_extractor.log

# Run the unified workflow
$PYTHON_CMD Read_Medium_From_Gmail.py

# Where wiki is my internal MediaWiki Apache web server
SCP_CMD="/usr/bin/scp"

# Check if successful and append status to log
if [ $? -eq 0 ]; then
    echo "$(date): Gmail extraction completed successfully" >> gmail_extractor.log
    echo ""
    echo "🎯 DAILY WORKFLOW COMPLETE!"
    echo ""
    echo "📄 Files ready:"
    echo "  🔒 medium_articles_master.json     (Permanent database)"
    echo "  📊 medium_articles_classified.json (Classified articles)"
    echo "  🌐 medium_article_browser.html     (Web interface)"
    echo ""
    echo "🎉 Open medium_article_browser.html in your browser!"
    $SCP_CMD medium_article_browser.html  wiki:/var/www/html/Medium.html
else
    echo "$(date): Gmail extraction failed" >> gmail_extractor.log
    echo ""
    echo "❌ Workflow failed. Check gmail_extractor.log for details."
    exit 1
fi