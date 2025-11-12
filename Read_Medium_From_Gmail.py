#!/usr/bin/env python3
"""
Extract Medium articles from Gmail to JSON format
Extracts: Title, URL, Email Date

Environment Variables (recommended for security):
  export GMAIL_USERNAME="your-email@gmail.com"
  export GMAIL_PASSWORD="your-app-password" 
  export GMAIL_FOLDER="Medium"  # Optional, defaults to "Medium"

If not set, the script will prompt you to enter these values.
"""

import imaplib
import email
from email.header import decode_header
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime
import os
import sys
import tempfile
import time

# Try to import Selenium for JavaScript rendering
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    print("⚠️  Selenium not available. Install with: pip install selenium")
    print("   Also install ChromeDriver for full JavaScript support")

def extract_reading_time(text):
    """Extract reading time from text like '5 min read', '10 min read'"""
    match = re.search(r'(\d+)\s*min\s*read', text, re.IGNORECASE)
    return match.group(1) if match else ''

def clean_text(text):
    """Clean text by removing extra whitespace and newlines"""
    if not text:
        return ''
    return ' '.join(text.strip().split())

def render_javascript_html(html_content):
    """Render HTML with JavaScript execution using Selenium"""
    if not SELENIUM_AVAILABLE:
        return html_content  # Fallback to original HTML
    
    try:
        # Set up Chrome options for headless mode
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-images")  # Don't load images for speed
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--allow-running-insecure-content")
        chrome_options.add_argument("--disable-features=VizDisplayCompositor")
        chrome_options.add_argument("--remote-debugging-port=9222")
        
        # Create temporary HTML file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as temp_file:
            # Add a base tag to handle relative URLs and improve rendering
            enhanced_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <base href="https://medium.com/">
                <meta charset="utf-8">
            </head>
            <body>
            {html_content}
            </body>
            </html>
            """
            temp_file.write(enhanced_html)
            temp_file_path = temp_file.name
        
        # Initialize webdriver
        driver = webdriver.Chrome(options=chrome_options)
        
        try:
            # Load the HTML file
            driver.get(f"file://{temp_file_path}")
            
            # Wait a bit for JavaScript to execute
            time.sleep(2)
            
            # Wait for any dynamic content to load (if any)
            try:
                WebDriverWait(driver, 10).until(
                    lambda driver: driver.execute_script("return document.readyState") == "complete"
                )
            except:
                pass  # Continue even if waiting times out
            
            # Now simulate clicks on links to trigger onclick() events that generate URLs
            try:
                # Find article title links (more likely to be actual articles)
                article_elements = driver.find_elements(By.CSS_SELECTOR, "a[href='#'], a[onclick], td a, p a")
                
                generated_urls = []
                
                for i, element in enumerate(article_elements[:10]):  # Limit to first 10 to avoid overload
                    try:
                        # Check if this looks like an article link by its text content
                        element_text = element.text.strip()
                        if len(element_text) < 10 or element_text.lower() in ['medium', 'unsubscribe', 'help', 'settings']:
                            continue
                        
                        # Get the current URL before click
                        original_url = driver.current_url
                        
                        # Instead of actually clicking, try to extract the onclick handler
                        onclick_attr = element.get_attribute('onclick')
                        if onclick_attr and 'medium.com' in onclick_attr:
                            # Extract URL from onclick JavaScript
                            url_match = re.search(r'https?://[^"\']*medium\.com[^"\']*', onclick_attr)
                            if url_match:
                                extracted_url = url_match.group(0)
                                if extracted_url not in generated_urls and '@simonyuen' not in extracted_url:
                                    generated_urls.append(extracted_url)
                                    print(f"    📋 Extracted URL {i+1}: {extracted_url[:80]}...")
                        else:
                            # Try clicking if no onclick found but element looks promising
                            try:
                                driver.execute_script("arguments[0].click();", element)
                                time.sleep(0.3)
                                
                                new_url = driver.current_url
                                if (new_url != original_url and 'medium.com' in new_url and 
                                    '@simonyuen' not in new_url and len(new_url) > 50):
                                    generated_urls.append(new_url)
                                    print(f"    📋 Generated URL {i+1}: {new_url[:80]}...")
                                    
                                # Navigate back if we moved
                                if new_url != original_url:
                                    driver.back()
                                    time.sleep(0.3)
                            except:
                                continue
                            
                    except Exception as e:
                        # Continue if individual processing fails
                        continue
                
                print(f"    🎯 Generated {len(generated_urls)} dynamic URLs")
                
                # Add generated URLs to the page as hidden elements for our parser to find
                for i, url in enumerate(generated_urls):
                    driver.execute_script(f"""
                        var hiddenDiv = document.createElement('div');
                        hiddenDiv.id = 'generated-url-{i}';
                        hiddenDiv.style.display = 'none';
                        hiddenDiv.setAttribute('data-generated-url', '{url}');
                        document.body.appendChild(hiddenDiv);
                    """)
                    
            except Exception as e:
                print(f"    ⚠️  Click simulation failed: {e}")
            
            # Get the rendered HTML with generated URLs
            rendered_html = driver.page_source
            
            return rendered_html
            
        finally:
            driver.quit()
            # Clean up temp file
            try:
                os.unlink(temp_file_path)
            except:
                pass
                
    except Exception as e:
        print(f"⚠️  JavaScript rendering failed: {e}")
        return html_content  # Fallback to original HTML

def extract_articles_from_email(html_content, email_date):
    """Extract Medium articles from email HTML content using improved parsing"""
    articles = []
    
    # Parse the HTML directly (no JavaScript rendering needed)
    soup = BeautifulSoup(html_content, "html.parser")
    
    # Find all Medium article links (these contain the actual article URLs)
    article_links = soup.find_all('a', href=re.compile(r'medium\.com/.*?/.*?-[a-f0-9]+\?source='))
    
    print(f"    🔗 Found {len(article_links)} potential article links")
    
    processed_urls = set()
    
    for link in article_links:
        href = link.get('href', '')
        
        # Skip if we've already processed this URL or if it's not an article
        if href in processed_urls or not href:
            continue
            
        # Skip unwanted URLs
        if any(skip in href.lower() for skip in ['unsubscribe', 'help', 'privacy', 'settings']):
            continue
        
        processed_urls.add(href)
        
        # Extract title from the link text or nearby elements
        title = clean_text(link.get_text())
        
        # If title is empty or too short, look for title in nearby elements
        if len(title) < 10:
            # Look for h2 or h3 elements that might contain the title
            parent_container = link
            for _ in range(3):  # Go up the DOM tree
                if parent_container.parent:
                    parent_container = parent_container.parent
                    title_elem = parent_container.find(['h2', 'h3'])
                    if title_elem:
                        title = clean_text(title_elem.get_text())
                        break
        
        # Extract author information
        author = ''
        
        # Look for author information in the surrounding context
        # Medium emails typically have author info near the article link
        parent_container = link
        for _ in range(5):  # Check parent elements
            if parent_container.parent:
                parent_container = parent_container.parent
                container_text = clean_text(parent_container.get_text())
                
                # Look for author patterns - Medium often shows "Author Name in Publication"
                author_pattern = r'([A-Z][a-z]+ [A-Z][a-z]+)(?:\s+in\s+)'
                match = re.search(author_pattern, container_text)
                if match:
                    author = match.group(1)
                    break
        
        # Extract reading time
        reading_time = ''
        container_text = clean_text(parent_container.get_text()) if 'parent_container' in locals() else ''
        reading_time = extract_reading_time(container_text)
        
        # Clean up title
        if not title or len(title) < 5:
            # Extract title from URL as last resort
            url_parts = href.split('/')
            for part in url_parts:
                if len(part) > 20 and '-' in part and not part.startswith('source='):
                    title = part.split('?')[0].split('-')
                    title = ' '.join(title[:-1]).replace('-', ' ').title()  # Remove the hash at the end
                    break
        
        if not title:
            title = "Medium Article"
        
        # Skip 'Careers' entries
        if title.strip().lower() == 'careers':
            continue
        
        # Clean up URL (remove source tracking for cleaner URLs)
        clean_url = href.split('?source=')[0] if '?source=' in href else href
        
        article = {
            'title': title,
            'url': clean_url,
            'email_date': email_date
        }
        
        articles.append(article)
        
        print(f"    📰 {title[:50]}{'...' if len(title) > 50 else ''}")
        if author:
            print(f"        👤 Author: {author}")
        if reading_time:
            print(f"        ⏱️  Reading time: {reading_time} min")
    
    return articles

def get_gmail_credentials():
    """Get Gmail credentials from environment variables or prompt user"""
    username = os.getenv('GMAIL_USERNAME')
    password = os.getenv('GMAIL_PASSWORD') 
    folder_name = os.getenv('GMAIL_FOLDER', 'Medium')  # Default to 'Medium' if not set
    
    # Check if username is missing
    if not username:
        print("📧 Gmail username not found in environment variables.")
        username = input("Enter your Gmail username: ").strip()
        if not username:
            print("❌ Gmail username is required. Exiting.")
            sys.exit(1)
        # Set environment variable for current shell session
        os.environ['GMAIL_USERNAME'] = username
        print(f"✅ GMAIL_USERNAME set for current session")
    
    # Check if password is missing
    if not password:
        print("🔐 Gmail password not found in environment variables.")
        import getpass
        password = getpass.getpass("Enter your Gmail app password (input will be hidden): ").strip()
        if not password:
            print("❌ Gmail password is required. Exiting.")
            sys.exit(1)
        # Set environment variable for current shell session
        os.environ['GMAIL_PASSWORD'] = password
        print(f"✅ GMAIL_PASSWORD set for current session")
    
    # Check if folder name is missing (though we have a default)
    if not os.getenv('GMAIL_FOLDER'):
        print(f"📁 Gmail folder not specified, using default: '{folder_name}'")
        folder_input = input(f"Enter Gmail folder name (press Enter for '{folder_name}'): ").strip()
        if folder_input:
            folder_name = folder_input
            os.environ['GMAIL_FOLDER'] = folder_name
            print(f"✅ GMAIL_FOLDER set to '{folder_name}' for current session")
    
    return username, password, folder_name

def main():
    """Main function to extract Medium articles and save to JSON"""
    
    # Get Gmail credentials
    username, password, folder_name = get_gmail_credentials()
    
    # Connect to Gmail
    print(f"🔗 Connecting to Gmail as {username}...")
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(username, password)
        print("✅ Login successful")
        
        # Select folder
        result, _ = mail.select(folder_name)
        if result != 'OK':
            print(f"❌ Failed to select folder '{folder_name}'. Please check if the folder exists.")
            sys.exit(1)
        print(f"✅ Selected folder: {folder_name}")
        
    except imaplib.IMAP4.error as e:
        print(f"❌ Gmail authentication failed: {e}")
        print("💡 Please check:")
        print("   • Username is correct (full email address)")  
        print("   • Password is an App Password (not regular password)")
        print("   • 2-Factor Authentication is enabled")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Connection error: {e}")
        sys.exit(1)
    
    # Search for Medium emails only
    status, messages = mail.search(None, 'FROM "noreply@medium.com"')
    email_ids = messages[0].split()
    
    print(f"Found {len(email_ids)} Medium emails from noreply@medium.com")
    
    all_articles = []
    
    # Process each email
    for i, eid in enumerate(email_ids, 1):
        print(f"Processing email {i}/{len(email_ids)}...")
        
        _, msg_data = mail.fetch(eid, "(RFC822)")
        msg = email.message_from_bytes(msg_data[0][1])
        
        # Get email subject and sender for debugging
        subject = decode_header(msg.get("Subject", ""))[0][0]
        if isinstance(subject, bytes):
            subject = subject.decode('utf-8', errors='ignore')
        sender = msg.get("From", "")
        
        if i <= 5 or i % 100 == 0:  # Show details for first 5 and every 100th email
            print(f"  Email {i}: From: {sender[:50]}... Subject: {subject[:60]}...")
        
        # Get email date
        email_date_raw = msg.get("Date", "")
        try:
            # Parse email date
            email_datetime = email.utils.parsedate_to_datetime(email_date_raw)
            email_date = email_datetime.strftime("%Y-%m-%d")
        except:
            email_date = datetime.now().strftime("%Y-%m-%d")
        
        # Extract HTML content
        html_content = ""
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/html":
                    html_content = part.get_payload(decode=True).decode('utf-8', errors ='ignore')
                    break
        else:
            if msg.get_content_type() == "text/html":
                html_content = msg.get_payload(decode=True).decode('utf-8', errors='ignore')
        
        if html_content:
            articles = extract_articles_from_email(html_content, email_date)
            all_articles.extend(articles)
    
    # Close Gmail connection
    mail.close()
    mail.logout()
    
    # Save all articles together
    current_date = datetime.now().strftime("%Y_%m_%d")
    filename = f'medium_articles_{current_date}.json'
    result = {
        'extraction_date': datetime.now().isoformat(),
        'total_emails_processed': len(email_ids),
        'total_articles_found': len(all_articles),
        'description': 'All Medium articles extracted from Gmail',
        'articles': all_articles
    }
    
    if all_articles:
        # Save all articles to single file
        with open(filename, 'w', encoding='utf-8') as jsonfile:
            json.dump(result, jsonfile, indent=2, ensure_ascii=False)
        
        print(f"\n✅ Extracted {len(all_articles)} total articles:")
        print(f"    Saved to: {filename}")
        
        # Show sample articles
        print(f"\n📋 Sample articles:")
        for i, article in enumerate(all_articles[:5]):
            print(f"{i+1}. {article['title'][:60]}{'...' if len(article['title']) > 60 else ''}")
            print(f"   🔗 URL: {article['url'][:80]}{'...' if len(article['url']) > 80 else ''}")
            print(f"   📅 Date: {article['email_date']}")
            print()
    else:
        print("❌ No articles found")

if __name__ == "__main__":
    main()
