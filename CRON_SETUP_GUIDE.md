# Cron Setup Guide for Gmail Article Extractor

## 🚨 Problem
When cron executes scripts, it doesn't load shell rc files (`.zshrc`, `.bashrc`), so Gmail environment variables aren't available, causing the script to prompt for user input and fail.

## ✅ Solution
Use the new cron-compatible script: `cron_run_gmail_extractor.sh`

## 🔧 Setup Instructions

### Step 1: Set Up Environment Variables (Choose One Method)

#### Method A: Dedicated Environment File (Recommended for Cron)
Create a dedicated file for Gmail credentials:

```bash
# Create the environment file
echo 'export GMAIL_USERNAME="your-email@gmail.com"' > ~/.gmail_env
echo 'export GMAIL_PASSWORD="your-app-password"' >> ~/.gmail_env
echo 'export GMAIL_FOLDER="Medium"' >> ~/.gmail_env

# Secure the file (only you can read/write)
chmod 600 ~/.gmail_env
```

#### Method B: Shell Profile Method
Add to your `~/.zshrc`:

```bash
# Add these lines to ~/.zshrc
export GMAIL_USERNAME="your-email@gmail.com"
export GMAIL_PASSWORD="your-app-password"
export GMAIL_FOLDER="Medium"
```

### Step 2: Test the Cron Script
Before setting up cron, test the script manually:

```bash
cd /Users/syuen/Medium_Email
./cron_run_gmail_extractor.sh
```

### Step 3: Set Up Cron Job

#### Add Cron Entry
```bash
# Edit crontab
crontab -e

# Add one of these lines:

# Run daily at 8:00 AM
0 8 * * * /Users/syuen/Medium_Email/cron_run_gmail_extractor.sh

# Run every 6 hours
0 */6 * * * /Users/syuen/Medium_Email/cron_run_gmail_extractor.sh

# Run Monday to Friday at 9:00 AM
0 9 * * 1-5 /Users/syuen/Medium_Email/cron_run_gmail_extractor.sh
```

### Step 4: Monitor Execution
The script creates a log file for debugging:

```bash
# View recent log entries
tail -f /Users/syuen/Medium_Email/gmail_extractor.log

# Check if cron job ran
grep "Gmail extraction" /Users/syuen/Medium_Email/gmail_extractor.log
```

## 🔐 Security Best Practices

1. **Use App Passwords**: Never use your actual Gmail password
2. **Secure Permissions**: Make sure credential files have restricted permissions (`chmod 600`)
3. **Avoid Hardcoding**: Don't put passwords directly in scripts or crontab
4. **Monitor Logs**: Regularly check execution logs for issues

## 🐛 Troubleshooting

### Cron Job Not Running
```bash
# Check if cron service is running
sudo launchctl list | grep cron

# Check cron logs (macOS)
log show --predicate 'process == "cron"' --last 1h
```

### Environment Variables Not Found
```bash
# Test environment loading
source ~/.gmail_env && echo "Gmail user: $GMAIL_USERNAME"

# Verify file permissions
ls -la ~/.gmail_env
```

### Python Issues in Cron
The script automatically detects Python installation, but you can force a specific version by modifying the `PYTHON_CMD` variable in the script.

## 📝 Example Complete Setup

```bash
# 1. Create credentials file
echo 'export GMAIL_USERNAME="john@gmail.com"' > ~/.gmail_env
echo 'export GMAIL_PASSWORD="abcd efgh ijkl mnop"' >> ~/.gmail_env
echo 'export GMAIL_FOLDER="Medium"' >> ~/.gmail_env
chmod 600 ~/.gmail_env

# 2. Test the script
cd /Users/syuen/Medium_Email
./cron_run_gmail_extractor.sh

# 3. Set up daily execution
(crontab -l 2>/dev/null; echo "0 8 * * * /Users/syuen/Medium_Email/cron_run_gmail_extractor.sh") | crontab -

# 4. Verify cron job was added
crontab -l
```

## ⚡ Key Differences from Original Script

| Original Script | Cron-Compatible Script |
|----------------|----------------------|
| Relies on shell rc files | Explicitly loads environment variables |
| Interactive prompts | Fails gracefully with helpful error messages |
| No logging | Creates execution log for debugging |
| Manual execution only | Designed for automated/cron execution |

The new script ensures reliable unattended execution while maintaining security best practices.