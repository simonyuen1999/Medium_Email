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

# Run the unified workflow
$PYTHON_CMD Read_Medium_From_Gmail.py

# Check if successful
if [ $? -eq 0 ]; then
    echo ""
    echo "🎯 DAILY WORKFLOW COMPLETE!"
    echo ""
    echo "📄 Files ready:"
    echo "  🔒 medium_articles_master.json     (Permanent database)"
    echo "  📊 medium_articles_classified.json (Classified articles)"
    echo "  🌐 medium_article_browser.html     (Web interface)"
    echo ""
    echo "🎉 Open medium_article_browser.html in your browser!"
else
    echo ""
    echo "❌ Workflow failed. Please check the error messages above."
fi