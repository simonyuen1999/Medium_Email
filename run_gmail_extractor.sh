#!/bin/bash
# run_gmail_extractor.sh - Wrapper script to run Gmail extractor with correct Python environment

echo "🚀 Medium Gmail Article Extractor"
echo "================================="

# Navigate to the script directory
cd "$(dirname "$0")"

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "💡 Please run: python -m venv .venv && .venv/bin/pip install beautifulsoup4 selenium"
    exit 1
fi

# Run the script with the virtual environment Python
echo "🔗 Using virtual environment Python..."
.venv/bin/python Read_Medium_From_Gmail.py

echo ""
echo "✅ Gmail extraction completed!"
echo "📄 Check medium_articles.json for results"