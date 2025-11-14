#!/bin/bash
# Cron-compatible Gmail extractor script
# This script ensures environment variables are loaded for cron execution

# Navigate to the script directory
cd "$(dirname "$0")"

# Method 1: Source environment file if it exists
# Create ~/.gmail_env with your credentials (see setup instructions below)
if [ -f "$HOME/.gmail_env" ]; then
    source "$HOME/.gmail_env"
fi

# Method 2: Load from shell profile (fallback)
if [ -f "$HOME/.zshrc" ]; then
    # Extract only Gmail environment variables from .zshrc to avoid other shell-specific code
    eval $(grep '^export GMAIL_' "$HOME/.zshrc" 2>/dev/null || true)
fi

# Verify required environment variables are set
if [ -z "$GMAIL_USERNAME" ] || [ -z "$GMAIL_PASSWORD" ]; then
    echo "❌ Error: Gmail credentials not found!"
    echo "Please set up environment variables using one of these methods:"
    echo ""
    echo "Method 1 - Create ~/.gmail_env file:"
    echo "  echo 'export GMAIL_USERNAME=\"your-email@gmail.com\"' > ~/.gmail_env"
    echo "  echo 'export GMAIL_PASSWORD=\"your-app-password\"' >> ~/.gmail_env"
    echo "  echo 'export GMAIL_FOLDER=\"Medium\"' >> ~/.gmail_env"
    echo "  chmod 600 ~/.gmail_env"
    echo ""
    echo "Method 2 - Add to your shell profile:"
    echo "  Add Gmail environment variables to ~/.zshrc"
    echo ""
    exit 1
fi

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
    echo "📚 Please install Python or set up a virtual environment"
    exit 1
fi

# Export the environment variables for the Python script
export GMAIL_USERNAME
export GMAIL_PASSWORD
export GMAIL_FOLDER

# Log execution for debugging cron issues
echo "$(date): Starting Gmail extraction with user: $GMAIL_USERNAME" >> gmail_extractor.log

# Run the unified workflow
$PYTHON_CMD Read_Medium_From_Gmail.py

# Check if successful and log result
if [ $? -eq 0 ]; then
    echo "$(date): Gmail extraction completed successfully" >> gmail_extractor.log
    echo "🎯 GMAIL EXTRACTION COMPLETE!"
else
    echo "$(date): Gmail extraction failed" >> gmail_extractor.log
    echo "❌ Workflow failed. Check gmail_extractor.log for details."
    exit 1
fi