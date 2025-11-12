#!/bin/bash
# set_gmail_env.sh - Helper script to set Gmail environment variables

echo "🔐 Gmail Environment Variables Setup"
echo "=================================="
echo ""
echo "This script helps you set environment variables for the Gmail article extractor."
echo "These variables will be available for the current terminal session."
echo ""

# Get Gmail username
if [ -z "$GMAIL_USERNAME" ]; then
    read -p "Enter your Gmail username: " gmail_username
    if [ -n "$gmail_username" ]; then
        export GMAIL_USERNAME="$gmail_username"
        echo "✅ GMAIL_USERNAME set"
    else
        echo "❌ Gmail username is required"
        exit 1
    fi
else
    echo "✅ GMAIL_USERNAME already set: $GMAIL_USERNAME"
fi

# Get Gmail password (hidden input)
if [ -z "$GMAIL_PASSWORD" ]; then
    read -s -p "Enter your Gmail app password (input will be hidden): " gmail_password
    echo ""
    if [ -n "$gmail_password" ]; then
        export GMAIL_PASSWORD="$gmail_password"
        echo "✅ GMAIL_PASSWORD set"
    else
        echo "❌ Gmail password is required"
        exit 1
    fi
else
    echo "✅ GMAIL_PASSWORD already set (hidden)"
fi

# Get Gmail folder (optional)
if [ -z "$GMAIL_FOLDER" ]; then
    read -p "Enter Gmail folder name (default: Medium): " gmail_folder
    gmail_folder=${gmail_folder:-Medium}
    export GMAIL_FOLDER="$gmail_folder"
    echo "✅ GMAIL_FOLDER set to: $gmail_folder"
else
    echo "✅ GMAIL_FOLDER already set: $GMAIL_FOLDER"
fi

echo ""
echo "🎉 Environment variables are now set for this terminal session!"
echo ""
echo "To make these permanent, add these lines to your ~/.zshrc or ~/.bashrc:"
echo "  export GMAIL_USERNAME=\"$GMAIL_USERNAME\""
echo "  export GMAIL_PASSWORD=\"your-app-password\""
echo "  export GMAIL_FOLDER=\"$GMAIL_FOLDER\""
echo ""
echo "You can now run: python Read_Gmail.py"