#!/bin/bash
# setup_cron_env.sh - Interactive setup for cron-compatible Gmail environment

echo "🔐 Cron Environment Setup for Gmail Article Extractor"
echo "===================================================="
echo ""
echo "This script will create a secure environment file at ~/.gmail_env"
echo "that can be used by cron jobs without exposing passwords in crontab."
echo ""

# Check if file already exists
if [ -f "$HOME/.gmail_env" ]; then
    echo "⚠️  File ~/.gmail_env already exists."
    read -p "Do you want to overwrite it? (y/N): " overwrite
    if [[ ! $overwrite =~ ^[Yy]$ ]]; then
        echo "❌ Setup cancelled."
        exit 0
    fi
fi

# Get Gmail username
echo ""
read -p "📧 Enter your Gmail username: " gmail_username
if [ -z "$gmail_username" ]; then
    echo "❌ Gmail username is required"
    exit 1
fi

# Get Gmail password (hidden input)
echo ""
echo "🔑 Enter your Gmail App Password"
echo "   (Get this from: Google Account → Security → App passwords)"
read -s -p "   Password (input will be hidden): " gmail_password
echo ""
if [ -z "$gmail_password" ]; then
    echo "❌ Gmail app password is required"
    exit 1
fi

# Get Gmail folder (optional)
echo ""
read -p "📁 Enter Gmail folder name (default: Medium): " gmail_folder
gmail_folder=${gmail_folder:-Medium}

# Create the environment file
echo ""
echo "💾 Creating ~/.gmail_env..."

cat > "$HOME/.gmail_env" << EOF
# Gmail environment variables for cron-compatible execution
# Created on $(date)
export GMAIL_USERNAME="$gmail_username"
export GMAIL_PASSWORD="$gmail_password"
export GMAIL_FOLDER="$gmail_folder"
EOF

# Secure the file
chmod 600 "$HOME/.gmail_env"

echo "✅ Environment file created successfully!"
echo ""
echo "📋 Security check:"
ls -la "$HOME/.gmail_env"
echo ""
echo "🧪 Testing environment variables:"
source "$HOME/.gmail_env"
echo "   GMAIL_USERNAME: $GMAIL_USERNAME"
echo "   GMAIL_FOLDER: $GMAIL_FOLDER"
echo "   GMAIL_PASSWORD: [hidden for security]"
echo ""
echo "🎯 Next steps:"
echo "   1. Test the cron script: ./cron_run_gmail_extractor.sh"
echo "   2. Set up cron job: crontab -e"
echo "   3. Add line: 0 8 * * * $(pwd)/cron_run_gmail_extractor.sh"
echo ""
echo "📖 For detailed instructions, see: CRON_SETUP_GUIDE.md"