# Gmail Security Configuration Guide

## 🔐 Environment Variables for Security

The Gmail article extractor now uses environment variables to keep your credentials secure and out of the source code.

## 📋 Required Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GMAIL_USERNAME` | Your Gmail email address | ✅ Yes |
| `GMAIL_PASSWORD` | Your Gmail App Password | ✅ Yes |
| `GMAIL_FOLDER` | Gmail folder name | ❌ Optional (defaults to "Medium") |

## 🚀 Setup Methods

### Method 1: Use the Helper Script (Recommended)
```bash
# Run the interactive setup script
./set_gmail_env.sh
```

### Method 2: Manual Environment Variables
```bash
# Set for current session
export GMAIL_USERNAME="your-email@gmail.com"
export GMAIL_PASSWORD="your-app-password"
export GMAIL_FOLDER="Medium"

# Run the extractor
python Read_Gmail.py
```

### Method 3: Permanent Setup
Add to your `~/.zshrc` or `~/.bashrc`:
```bash
export GMAIL_USERNAME="your-email@gmail.com"
export GMAIL_PASSWORD="your-app-password" 
export GMAIL_FOLDER="Medium"
```

Then reload: `source ~/.zshrc`

## 🔑 Gmail App Password Setup

1. **Enable 2-Factor Authentication** on your Google account
2. **Generate App Password**:
   - Go to Google Account settings
   - Security → 2-Step Verification → App passwords
   - Select "Mail" and generate password
   - Use this 16-character password (not your regular Gmail password)

## 🛡️ Security Benefits

### ✅ Before (Insecure):
- Credentials hardcoded in source code
- Visible in version control
- Risk of accidental exposure

### ✅ After (Secure):
- Credentials in environment variables
- No sensitive data in source code
- Prompts user if not set
- Sets variables for current session

## 🎯 Script Behavior

### If Environment Variables Are Set:
- Script runs automatically with stored credentials
- No user promption needed

### If Environment Variables Are Missing:
1. **Username Missing**: Prompts for Gmail username
2. **Password Missing**: Prompts for app password (hidden input)
3. **Folder Missing**: Uses "Medium" as default, optionally prompts
4. **Missing Info**: Script exits with error message
5. **After Input**: Sets variables for current shell session

## 📝 Example Usage

### First Time Setup:
```bash
# No environment variables set
python Read_Gmail.py

# Output:
# 📧 Gmail username not found in environment variables.
# Enter your Gmail username: your-email@gmail.com
# ✅ GMAIL_USERNAME set for current session
# 🔐 Gmail password not found in environment variables.  
# Enter your Gmail app password (input will be hidden): ****************
# ✅ GMAIL_PASSWORD set for current session
# 📁 Gmail folder not specified, using default: 'Medium'
# Enter Gmail folder name (press Enter for 'Medium'): [Enter]
```

### With Environment Variables Set:
```bash
export GMAIL_USERNAME="your-email@gmail.com"
export GMAIL_PASSWORD="your-app-password"
python Read_Gmail.py

# Script runs immediately without prompts
```

## ⚠️ Important Notes

1. **Use App Passwords**: Never use your regular Gmail password
2. **Keep Secure**: Don't share or commit environment variables
3. **Session Scope**: Variables set by script only last for current terminal session
4. **Permanent Setup**: Add to shell config file for persistence

## 🔍 Troubleshooting

### Authentication Failed:
- Verify 2FA is enabled
- Generate new app password
- Check username format (full email address)

### Environment Variables Not Working:
```bash
# Check current variables
echo $GMAIL_USERNAME
echo $GMAIL_FOLDER

# Verify they're set
env | grep GMAIL
```

### Script Exits Early:
- Ensure you enter both username and password when prompted
- Check that inputs are not empty
- Verify Gmail folder exists in your account

This security enhancement protects your credentials while maintaining ease of use!