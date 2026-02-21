#!/usr/bin/env python3
"""
Process Medium Article Browser HTML for email.
- Removes sidebar and search functionality
- Generates static table instead of dynamic JavaScript
- Sends via email with unique Message-ID
"""

import argparse
import os
import json
import re
import smtplib
import uuid
from datetime import datetime, timezone, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from html import escape


def get_current_timestamp():
    """Get current timestamp in EST timezone.
    
    If running in GitHub Actions (Ubuntu), convert UTC to EST.
    If running locally, use local time as-is.
    """
    # Check if running in GitHub Actions (GITHUB_ACTIONS env var is set)
    is_github_actions = os.getenv('GITHUB_ACTIONS') == 'true'
    
    if is_github_actions:
        # GitHub Actions runs in UTC, convert to EST (UTC-5)
        utc_now = datetime.now(timezone.utc)
        est_offset = timedelta(hours=-5)
        est_now = utc_now + est_offset
        timestamp_str = est_now.strftime('%Y-%m-%d %I:%M:%S %p')
        print(f"[GitHub Actions] UTC time: {utc_now.strftime('%Y-%m-%d %I:%M:%S %p')}")
        print(f"[GitHub Actions] EST time: {timestamp_str}")
    else:
        # Local execution, use local timezone
        timestamp_str = datetime.now().strftime('%Y-%m-%d %I:%M:%S %p')
        print(f"[Local execution] Local time: {timestamp_str}")
    
    return timestamp_str


def extract_articles_from_html(html_content):
    """Extract the allArticles JSON array from the HTML."""
    # Find the allArticles array in the JavaScript
    pattern = r'const\s+allArticles\s*=\s*(\[[\s\S]*?\]);'
    match = re.search(pattern, html_content)
    
    if not match:
        raise ValueError("Could not find allArticles array in HTML")
    
    articles_json = match.group(1)
    articles = json.loads(articles_json)
    
    return articles


def generate_table_rows(articles):
    """Generate static HTML table rows from articles data.
    
    Uses direct links to URLs instead of JavaScript onclick for email client compatibility.
    """
    rows = []
    
    for index, article in enumerate(articles):
        row_class = 'even' if index % 2 == 1 else ''
        
        # Escape title for display
        title = escape(article['title'])
        url = article['url']
        email_date = article['email_date']
        
        # Use direct link instead of JavaScript onclick for email client compatibility
        row = f'''                        <tr class="article-row {row_class}">
                            <td class="col-index">{index + 1}</td>
                            <td class="col-date">{email_date}</td>
                            <td class="col-title">
                                <a href="{url}" target="_blank" class="article-title">
                                    {title}
                                </a>
                            </td>
                        </tr>'''
        
        rows.append(row)
    
    return '\n'.join(rows)


def process_html_for_email(html_content, articles):
    """Process HTML: remove sidebar, search, JS data; add static table."""
    
    # Generate static table rows
    table_rows = generate_table_rows(articles)
    
    # Remove the sidebar div (from <div class="sidebar"> to its closing </div>)
    html_content = re.sub(
        r'<div class="sidebar">.*?</div>\s*</div>\s*<div class="main-content">',
        '<div class="main-content">',
        html_content,
        flags=re.DOTALL
    )
    
    # Update container to remove flex layout (sidebar gone)
    html_content = html_content.replace(
        'display: flex;',
        'display: block;',
        1  # Only first occurrence in .container
    )
    
    # Remove sidebar width constraint
    html_content = re.sub(
        r'\.sidebar\s*\{[^}]*\}',
        '',
        html_content
    )
    
    # Remove the search controls section
    html_content = re.sub(
        r'<div class="controls">.*?</div>\s*<div class="article-list">',
        '<div class="article-list" style="margin-top: 0;">',
        html_content,
        flags=re.DOTALL
    )
    
    # Replace the tbody placeholder with static content
    html_content = re.sub(
        r'<tbody id="articleTableBody">\s*<!-- Articles will be populated by JavaScript -->\s*</tbody>',
        f'<tbody id="articleTableBody">\n{table_rows}\n                    </tbody>',
        html_content
    )
    
    # Remove the Tags column header
    html_content = re.sub(
        r'<th class="col-tags">Tags</th>',
        '',
        html_content
    )
    
    # Remove col-tags CSS rules
    html_content = re.sub(
        r'\.col-tags \{[^}]*\}',
        '',
        html_content
    )
    
    # Update col-title width to use full remaining space
    html_content = re.sub(
        r'\.col-title \{[^}]*width:[^;]*;[^}]*\}',
        '.col-title { width: calc(100% - 125px); min-width: 300px; }',
        html_content
    )
    
    # Remove the allArticles JavaScript data
    html_content = re.sub(
        r'// Article data\s*const allArticles = \[[\s\S]*?\];',
        '// Article data removed - using static HTML table',
        html_content
    )
    
    # Remove filter-related JavaScript functions more thoroughly
    # Remove entire script section with filters and rebuild with just modal functions
    html_content = re.sub(
        r'<script>\s*// Article data.*?(?=// Modal functionality|function openOptions)',
        '<script>\n        // Article data removed - using static HTML table\n        \n        ',
        html_content,
        flags=re.DOTALL
    )
    
    # Remove the "no results" div
    html_content = re.sub(
        r'<div id="noResults"[^>]*>.*?</div>',
        '',
        html_content,
        flags=re.DOTALL
    )
    
    # Remove the modal overlay (not needed for direct links in email)
    html_content = re.sub(
        r'<div id="optionModal"[^>]*>.*?</div>\s*</div>\s*</div>',
        '',
        html_content,
        flags=re.DOTALL
    )
    
    # Remove openOptions() and closeModal() functions (not needed for direct links)
    html_content = re.sub(
        r'function openOptions\([^)]*\)\s*\{[^}]*\}',
        '',
        html_content,
        flags=re.DOTALL
    )
    
    html_content = re.sub(
        r'function closeModal\([^)]*\)\s*\{[^}]*\}',
        '',
        html_content,
        flags=re.DOTALL
    )
    
    # Remove modal event listener
    html_content = re.sub(
        r"document\.getElementById\('optionModal'\)\.addEventListener\([^)]*\)\s*\{[^}]*\}\);",
        '',
        html_content,
        flags=re.DOTALL
    )
    
    # Remove entire <script> block (not needed for email - most clients strip JavaScript anyway)
    html_content = re.sub(
        r'<script>.*?</script>',
        '',
        html_content,
        flags=re.DOTALL
    )
    
    # Update stats in header - remove time container
    article_count = len(articles)
    timestamp_str = get_current_timestamp()
    # First remove the time container span
    html_content = re.sub(
        r'<span id="timeContainer">.*?</span>',
        '',
        html_content,
        flags=re.DOTALL
    )
    # Then update the stats with simpler format
    html_content = re.sub(
        r'(<div class="stats">).*?(</div>)',
        rf'\g<1>{article_count} articles • Generated on {timestamp_str}\g<2>',
        html_content,
        count=1,
        flags=re.DOTALL
    )
    
    return html_content


def send_email(html_content, recipient='simonyuen1999@hotmail.com'):
    """Send the processed HTML via email with unique Message-ID."""
    
    # Get credentials from environment variables
    gmail_user = os.getenv('GMAIL_USERNAME')
    gmail_password = os.getenv('GMAIL_PASSWORD')
    
    if not gmail_user or not gmail_password:
        raise ValueError(
            "Missing required environment variables: GMAIL_USERNAME and/or GMAIL_PASSWORD\n"
            "Please set them before running this script."
        )
    
    # Generate unique Message-ID to prevent duplicate filtering
    unique_id = str(uuid.uuid4())
    domain = gmail_user.split('@')[1] if '@' in gmail_user else 'gmail.com'
    message_id = f"<{unique_id}@{domain}>"
    
    # Get subject with timestamp (EST if in GitHub Actions, local time otherwise)
    timestamp_str = get_current_timestamp()
    subject = f'Medium Article ({timestamp_str})'
    
    # Create message
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = gmail_user
    msg['To'] = recipient
    msg['Message-ID'] = message_id  # Unique ID for each email
    
    # Add plain text version as fallback
    text_part = MIMEText(
        "This email contains an HTML version of the Medium Article Browser. "
        "Please view this email in an HTML-capable email client.",
        'plain'
    )
    msg.attach(text_part)
    
    # Add HTML version
    html_part = MIMEText(html_content, 'html')
    msg.attach(html_part)
    
    # Send email via Gmail SMTP
    print("\nConnecting to Gmail SMTP server...")
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            print(f"Logging in as {gmail_user}...")
            server.login(gmail_user, gmail_password)
            
            print(f"Sending email to {recipient}...")
            server.send_message(msg)
            
        print("✓ Email sent successfully!")
        print(f"  From: {gmail_user}")
        print(f"  To: {recipient}")
        print(f"  Subject: {subject}")
        print(f"  Message-ID: {message_id}")
        
    except smtplib.SMTPAuthenticationError:
        print("✗ Authentication failed!")
        print("  Make sure GMAIL_PASSWORD is set correctly.")
        print("  You may need to use an App Password instead of your regular password.")
        print("  See: https://support.google.com/accounts/answer/185833")
        raise
    except Exception as e:
        print(f"✗ Error sending email: {e}")
        raise


def process_and_save(debug=False):
    """Main function to process HTML and save to file.
    
    Args:
        debug: If True, skip sending email (default: False)
    """
    
    # Read the HTML file
    html_file = Path(__file__).parent / 'medium_article_browser.html'
    
    if not html_file.exists():
        raise FileNotFoundError(f"HTML file not found: {html_file}")
    
    print(f"Reading HTML file: {html_file}")
    with open(html_file, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    print(f"Original HTML size: {len(html_content):,} characters")
    
    # Extract articles data
    print("Extracting articles data...")
    all_articles = extract_articles_from_html(html_content)
    print(f"Found {len(all_articles)} articles")
    
    # Limit to first 50 articles for daily email summary
    max_articles = 50
    articles = all_articles[:max_articles]
    print(f"Using first {len(articles)} articles for email")
    
    # Process HTML
    print("Processing HTML...")
    processed_html = process_html_for_email(html_content, articles)
    print(f"Processed HTML size: {len(processed_html):,} characters")
    
    # Save to output file
    output_file = Path(__file__).parent / 'email_output.html'
    print(f"Saving to: {output_file}")
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(processed_html)
    
    print("✓ Output saved successfully!")
    print(f"  File: {output_file}")
    print(f"  Articles: {len(articles)}")
    
    # Send email (unless debug mode is enabled)
    if debug:
        print("\n⚠ Debug mode enabled - skipping email sending")
        print(f"  You can review the file at: {output_file}")
    else:
        try:
            send_email(processed_html)
        except Exception as e:
            print("\n⚠ Email sending failed, but file was saved successfully.")
            print(f"  You can review the file at: {output_file}")
            raise


if __name__ == '__main__':
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description='Process Medium Article Browser HTML and send via email'
    )
    parser.add_argument(
        '-d', '--debug',
        action='store_true',
        help='Debug mode: generate HTML file but do not send email (default: False)'
    )
    args = parser.parse_args()
    
    try:
        process_and_save(debug=args.debug)
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
