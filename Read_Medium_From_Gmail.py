#!/usr/bin/env python3
"""
Comprehensive Medium Articles Extractor and Processor

This program combines Gmail extraction with complete processing pipeline:
1. Extract latest Medium articles from Gmail
2. Save to dated JSON file (medium_articles_YYYY_MM_DD.json)
3. Update master historical database (medium_articles_master.json)
4. Generate classified articles with automatic tagging
5. Create web browser interface

One command = Complete workflow!

Environment Variables (recommended for security):
  export GMAIL_USERNAME="your-email@gmail.com"
  export GMAIL_PASSWORD="your-app-password"
  export GMAIL_FOLDER="Medium"  # Optional, defaults to "Medium"

If not set, the script will prompt you to enter these values.
"""

import argparse
import email
import imaplib
import json
import os
import re
import sys
import tempfile
import time
from collections import defaultdict
from datetime import datetime
from email.header import decode_header
from typing import Dict, List, Set

from bs4 import BeautifulSoup


# Try to import Selenium for JavaScript rendering
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.support.ui import WebDriverWait

    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    print("⚠️  Selenium not available. Install with: pip install selenium")
    print("   Also install ChromeDriver for full JavaScript support")


def extract_reading_time(text):
    """Extract reading time from text like '5 min read', '10 min read'"""
    match = re.search(r"(\d+)\s*min\s*read", text, re.IGNORECASE)
    return match.group(1) if match else ""


def clean_text(text):
    """Clean text by removing extra whitespace and newlines"""
    if not text:
        return ""
    return " ".join(text.strip().split())


def fix_title(title):
    if not title:
        return title
    
    # Exceptions: words to preserve and not split internally, but allow splitting around them.
    exceptions = ["OpenAI", "MacBook", "GitHub", "SaaS", "JavaScript", "NotebookLM", "NoteBookLM", "LiteLLM"]
    placeholders = {}
    temp_title = title
    
    for i, word in enumerate(exceptions):
        # "Excepmask" + lowercase letter ensures it is treated as a simple Titlecase word (no internal caps)
        key = f"Excepmask{chr(97+i)}" 
        placeholders[key] = word
        temp_title = temp_title.replace(word, key)
    
    # Logic 1: CamelCase Split
    # Insert space between Lowercase and Uppercase (e.g., "WordWord" -> "Word Word")
    # Regex: Match [A-Z][a-z]+ followed by lookahead [A-Z]
    temp_title = re.sub(r'([A-Z][a-z]+)(?=[A-Z])', r'\1 ', temp_title)
    
    # Logic 2: Punctuation Split
    # Insert space after punctuation followed by Uppercase
    # Excluded punctuation: '(', '-', '&', '"', '`'
    # [^\w\s\(\-\&\"\`] matches anything that is NOT:
    # word char, whitespace, (, -, &, ", or `
    temp_title = re.sub(r'([^\w\s\(\-\&\"\`])(?=[A-Z])', r'\1 ', temp_title)
    
    # Logic 3: Digit Split
    # Insert space between Digit and Uppercase (e.g., "2026Feb" -> "2026 Feb")
    temp_title = re.sub(r'(\d)(?=[A-Z])', r'\1 ', temp_title)
    
    # Restore exceptions
    for key, word in placeholders.items():
        temp_title = temp_title.replace(key, word)
    
    return temp_title


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
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".html", delete=False
        ) as temp_file:
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
                    lambda driver: driver.execute_script("return document.readyState")
                    == "complete"
                )
            except:
                pass  # Continue even if waiting times out

            # Now simulate clicks on links to trigger onclick() events that generate URLs
            try:
                # Find article title links (more likely to be actual articles)
                article_elements = driver.find_elements(
                    By.CSS_SELECTOR, "a[href='#'], a[onclick], td a, p a"
                )

                generated_urls = []

                for i, element in enumerate(
                    article_elements[:10]
                ):  # Limit to first 10 to avoid overload
                    try:
                        # Check if this looks like an article link by its text content
                        element_text = element.text.strip()
                        if len(element_text) < 10 or element_text.lower() in [
                            "medium",
                            "unsubscribe",
                            "help",
                            "settings",
                        ]:
                            continue

                        # Get the current URL before click
                        original_url = driver.current_url

                        # Instead of actually clicking, try to extract the onclick handler
                        onclick_attr = element.get_attribute("onclick")
                        if onclick_attr and "medium.com" in onclick_attr:
                            # Extract URL from onclick JavaScript
                            url_match = re.search(
                                r'https?://[^"\']*medium\.com[^"\']*', onclick_attr
                            )
                            if url_match:
                                extracted_url = url_match.group(0)
                                if (
                                    extracted_url not in generated_urls
                                    and "@simonyuen" not in extracted_url
                                ):
                                    generated_urls.append(extracted_url)
                                    print(
                                        f"    📋 Extracted URL {i + 1}: {extracted_url[:80]}..."
                                    )
                        else:
                            # Try clicking if no onclick found but element looks promising
                            try:
                                driver.execute_script("arguments[0].click();", element)
                                time.sleep(0.3)

                                new_url = driver.current_url
                                if (
                                    new_url != original_url
                                    and "medium.com" in new_url
                                    and "@simonyuen" not in new_url
                                    and len(new_url) > 50
                                ):
                                    generated_urls.append(new_url)
                                    print(
                                        f"    📋 Generated URL {i + 1}: {new_url[:80]}..."
                                    )

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
    article_links = soup.find_all(
        "a", href=re.compile(r"medium\.com/.*?/.*?-[a-f0-9]+\?source=")
    )

    print(f"    🔗 Found {len(article_links)} potential article links")

    # Group links by URL - each URL may appear multiple times
    # We want to keep the occurrence with the longest/best title
    url_to_links = {}

    for link in article_links:
        href = link.get("href", "")

        # Skip if empty or unwanted
        if not href:
            continue

        # Skip unwanted URLs
        if any(
            skip in href.lower()
            for skip in ["unsubscribe", "help", "privacy", "settings"]
        ):
            continue

        # Extract title from the link text
        title = clean_text(link.get_text())

        # Store this link, preferring ones with longer titles
        if href not in url_to_links or len(title) > len(url_to_links[href]["title"]):
            url_to_links[href] = {"link": link, "title": title}

    # Now process each unique URL
    for href, data in url_to_links.items():
        link = data["link"]
        title = data["title"]

        # If title is still empty or too short, look for title in nearby elements
        if len(title) < 10:
            # Look for h2 or h3 elements that might contain the title
            parent_container = link
            for _ in range(3):  # Go up the DOM tree
                if parent_container.parent:
                    parent_container = parent_container.parent
                    title_elem = parent_container.find(["h2", "h3"])
                    if title_elem:
                        title = clean_text(title_elem.get_text())
                        break

        # Extract author information
        author = ""

        # Look for author information in the surrounding context
        # Medium emails typically have author info near the article link
        parent_container = link
        for _ in range(5):  # Check parent elements
            if parent_container.parent:
                parent_container = parent_container.parent
                container_text = clean_text(parent_container.get_text())

                # Look for author patterns - Medium often shows "Author Name in Publication"
                author_pattern = r"([A-Z][a-z]+ [A-Z][a-z]+)(?:\s+in\s+)"
                match = re.search(author_pattern, container_text)
                if match:
                    author = match.group(1)
                    break

        # Extract reading time
        reading_time = ""
        container_text = (
            clean_text(parent_container.get_text())
            if "parent_container" in locals()
            else ""
        )
        reading_time = extract_reading_time(container_text)

        # Clean up title
        if not title or len(title) < 5:
            # Extract title from URL as last resort
            url_parts = href.split("/")
            for part in url_parts:
                if len(part) > 20 and "-" in part and not part.startswith("source="):
                    title = part.split("?")[0].split("-")
                    title = (
                        " ".join(title[:-1]).replace("-", " ").title()
                    )  # Remove the hash at the end
                    break

        if not title:
            title = "Medium Article"

        # Skip 'Careers' entries
        if title.strip().lower() == "careers":
            continue

        # Clean up URL (remove source tracking for cleaner URLs)
        clean_url = href.split("?source=")[0] if "?source=" in href else href

        article = {"title": title, "url": clean_url, "email_date": email_date}

        articles.append(article)

        print(f"    📰 {title[:50]}{'...' if len(title) > 50 else ''}")
        if author:
            print(f"        👤 Author: {author}")
        if reading_time:
            print(f"        ⏱️  Reading time: {reading_time} min")

    return articles


def get_gmail_credentials():
    """Get Gmail credentials from environment variables or prompt user"""
    username = os.getenv("GMAIL_USERNAME")
    password = os.getenv("GMAIL_PASSWORD")
    folder_name = os.getenv("GMAIL_FOLDER", "Medium")  # Default to 'Medium' if not set

    # Check if username is missing
    if not username:
        print("📧 Gmail username not found in environment variables.")
        username = input("Enter your Gmail username: ").strip()
        if not username:
            print("❌ Gmail username is required. Exiting.")
            sys.exit(1)
        # Set environment variable for current shell session
        os.environ["GMAIL_USERNAME"] = username
        print(f"✅ GMAIL_USERNAME set for current session")

    # Check if password is missing
    if not password:
        print("🔐 Gmail password not found in environment variables.")
        import getpass

        password = getpass.getpass(
            "Enter your Gmail app password (input will be hidden): "
        ).strip()
        if not password:
            print("❌ Gmail password is required. Exiting.")
            sys.exit(1)
        # Set environment variable for current shell session
        os.environ["GMAIL_PASSWORD"] = password
        print(f"✅ GMAIL_PASSWORD set for current session")

    # Check if folder name is missing (though we have a default)
    if not os.getenv("GMAIL_FOLDER"):
        print(f"📁 Gmail folder not specified, using default: '{folder_name}'")
        folder_input = input(
            f"Enter Gmail folder name (press Enter for '{folder_name}'): "
        ).strip()
        if folder_input:
            folder_name = folder_input
            os.environ["GMAIL_FOLDER"] = folder_name
            print(f"✅ GMAIL_FOLDER set to '{folder_name}' for current session")

    return username, password, folder_name


# ===== COMPREHENSIVE PROCESSING CLASSES =====


class ArticleClassifier:
    """Article classification system for automatic tagging"""

    def __init__(self):
        # Define classification rules with keywords for each category
        self.classification_rules = {
            "Python": {
                "keywords": [
                    "python",
                    "django",
                    "flask",
                    "pandas",
                    "numpy",
                    "fastapi",
                    "pytest",
                    "pip",
                    "conda",
                    "jupyter",
                ],
                "patterns": [r"\bpy\b", r"python\s*\d", r"\.py\b"],
            },
            "JavaScript/Node": {
                "keywords": [
                    "javascript",
                    "node",
                    "nodejs",
                    "npm",
                    "yarn",
                    "express",
                    "nest",
                    "typescript",
                    "js",
                ],
                "patterns": [r"\bjs\b", r"node\.js", r"\.js\b"],
            },
            "AI/ML": {
                "keywords": [
                    "artificial intelligence",
                    "machine learning",
                    "deep learning",
                    "neural network",
                    "tensorflow",
                    "pytorch",
                    "scikit-learn",
                    "keras",
                    "opencv",
                    "nlp",
                    "computer vision",
                ],
                "patterns": [r"\bai\b", r"\bml\b", r"neural\s+network"],
            },
            "LLM/GPT": {
                "keywords": [
                    "llm",
                    "gpt",
                    "chatgpt",
                    "openai",
                    "claude",
                    "transformer",
                    "bert",
                    "large language model",
                    "prompt engineering",
                    "fine-tuning",
                    "embedding",
                ],
                "patterns": [r"gpt-?\d", r"\bllm\b"],
            },
            "AI Agent": {
                "keywords": [
                    "ai agent",
                    "agent",
                    "agents",
                    "agentic",
                    "autonomous agent",
                    "multi-agent",
                    "tool calling",
                    "function calling",
                    "orchestration",
                    "planner",
                    "assistant",
                    "copilot",
                    "ai toolkit",
                    "vs code ai toolkit",
                    "google antigravity",
                    "antigravity",
                    "autogen",
                    "crew ai",
                    "langgraph",
                    "langchain",
                ],
                "patterns": [
                    r"\bai\s+agent\b",
                    r"\bagentic\b",
                    r"\bmulti-?agent\b",
                    r"\btool\s+calling\b",
                    r"\bfunction\s+calling\b",
                    r"vs\s*code\s*ai\s*toolkit",
                    r"\bautogen\b",
                    r"\bcrewai\b",
                    r"\blanggraph\b",
                ],
            },
            "AWS/Cloud": {
                "keywords": [
                    "aws",
                    "amazon web services",
                    "ec2",
                    "s3",
                    "lambda",
                    "cloudformation",
                    "terraform",
                    "azure",
                    "gcp",
                    "google cloud",
                    "kubernetes",
                    "docker",
                    "serverless",
                ],
                "patterns": [r"\baws\b", r"\bgcp\b", r"\bk8s\b"],
            },
            "Linux/DevOps": {
                "keywords": [
                    "linux",
                    "ubuntu",
                    "centos",
                    "bash",
                    "shell",
                    "devops",
                    "ci/cd",
                    "jenkins",
                    "gitlab",
                    "github actions",
                    "ansible",
                    "puppet",
                    "chef",
                ],
                "patterns": [r"ci/cd", r"\.sh\b"],
            },
            "React/Frontend": {
                "keywords": [
                    "react",
                    "reactjs",
                    "jsx",
                    "redux",
                    "next.js",
                    "gatsby",
                    "hooks",
                    "component",
                ],
                "patterns": [r"react\.js", r"next\.js"],
            },
            "Angular": {
                "keywords": [
                    "angular",
                    "angularjs",
                    "typescript",
                    "rxjs",
                    "ngrx",
                    "ionic",
                ],
                "patterns": [r"angular\s*\d+"],
            },
            "HTML/CSS/Browser": {
                "keywords": [
                    "html",
                    "css",
                    "sass",
                    "scss",
                    "bootstrap",
                    "tailwind",
                    "responsive",
                    "frontend",
                    "browser",
                    "dom",
                    "web development",
                    "css3",
                    "html5",
                ],
                "patterns": [r"\bdom\b", r"css\d?", r"html\d?"],
            },
            "Database": {
                "keywords": [
                    "database",
                    "sql",
                    "mysql",
                    "postgresql",
                    "mongodb",
                    "redis",
                    "elasticsearch",
                    "nosql",
                    "orm",
                    "prisma",
                    "sequelize",
                ],
                "patterns": [r"\bsql\b", r"\bdb\b"],
            },
            "Mobile": {
                "keywords": [
                    "mobile",
                    "ios",
                    "android",
                    "flutter",
                    "react native",
                    "swift",
                    "kotlin",
                    "xamarin",
                ],
                "patterns": [r"react\s+native", r"\bios\b"],
            },
            "Security": {
                "keywords": [
                    "security",
                    "authentication",
                    "authorization",
                    "oauth",
                    "jwt",
                    "encryption",
                    "cybersecurity",
                    "vulnerability",
                    "penetration testing",
                ],
                "patterns": [r"\bauth\b", r"\bjwt\b"],
            },
            "Social/Career": {
                "keywords": [
                    "career",
                    "interview",
                    "job",
                    "hiring",
                    "remote work",
                    "freelance",
                    "startup",
                    "leadership",
                    "management",
                    "team",
                    "culture",
                    "diversity",
                    "inclusion",
                ],
                "patterns": [r"remote\s+work"],
            },
            "Tutorial/Learning": {
                "keywords": [
                    "tutorial",
                    "guide",
                    "beginner",
                    "learn",
                    "course",
                    "education",
                    "teaching",
                    "how to",
                    "step by step",
                    "getting started",
                ],
                "patterns": [r"how\s+to", r"step\s+by\s+step"],
            },
            "Performance": {
                "keywords": [
                    "performance",
                    "optimization",
                    "speed",
                    "benchmark",
                    "profiling",
                    "caching",
                    "memory",
                    "cpu",
                    "latency",
                    "scaling",
                ],
                "patterns": [r"performance", r"optimization"],
            },
        }

    def classify_article(self, article):
        """Classify a single article and return list of matching categories"""
        title = article.get("title", "").lower()
        url = article.get("url", "").lower()

        # Combine title and URL for analysis
        content = f"{title} {url}"

        matched_categories = []
        category_scores = {}

        for category, rules in self.classification_rules.items():
            score = 0

            # Check keywords
            for keyword in rules["keywords"]:
                if keyword.lower() in content:
                    score += 1

            # Check patterns
            for pattern in rules.get("patterns", []):
                if re.search(pattern, content, re.IGNORECASE):
                    score += 2  # Patterns get higher weight

            if score > 0:
                category_scores[category] = score
                matched_categories.append(category)

        return matched_categories, category_scores

    def classify_all_articles(self, articles):
        """Classify all articles and add tags"""
        classified_articles = []
        category_stats = defaultdict(int)

        for article in articles:
            # Create a copy of the article
            classified_article = article.copy()

            # Get classifications
            categories, scores = self.classify_article(article)

            # Add tags to article
            classified_article["tags"] = categories
            classified_article["tag_scores"] = scores

            # Update statistics
            for category in categories:
                category_stats[category] += 1

            classified_articles.append(classified_article)

        return classified_articles, dict(category_stats)


class WebBrowserGenerator:
    """Generates HTML web interface for browsing articles"""

    def __init__(self, articles):
        self.articles = articles
        self.available_tags = set()

        # Process articles and collect tags
        for article in self.articles:
            # Add date object for JavaScript sorting
            try:
                article["date_obj"] = datetime.strptime(
                    article["email_date"], "%Y-%m-%d"
                ).isoformat()
            except:
                article["date_obj"] = datetime.now().isoformat()

            # Collect tags
            tags = article.get("tags", [])
            self.available_tags.update(tags)

    def calculate_tag_stats(self):
        """Calculate tag statistics"""
        tag_counts = defaultdict(int)
        for article in self.articles:
            for tag in article.get("tags", []):
                tag_counts[tag] += 1

        return sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)

    def generate_tag_checkboxes(self, tag_stats):
        """Generate HTML for tag checkboxes"""
        checkboxes = []
        for tag, count in tag_stats:
            safe_id = re.sub(r"[^a-zA-Z0-9]", "_", tag)
            checkboxes.append(f'''
                <div class="tag-item">
                    <input type="checkbox" id="tag_{safe_id}" value="{tag}">
                    <label for="tag_{safe_id}">{tag}</label>
                    <span class="tag-count">({count})</span>
                </div>''')
        return "".join(checkboxes)

    def generate_html(self, output_file="medium_article_browser.html"):
        """Generate the complete HTML page"""
        if not self.articles:
            print("❌ No articles to generate HTML for.")
            return False

        tag_stats = self.calculate_tag_stats()

        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Medium Article Browser - Web Edition</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f8f9fa;
            color: #333;
            width: 100%;
            overflow-x: auto;
        }}
        
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 1rem;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            width: 100%;
        }}
        
        .header h1 {{
            font-size: 1.8rem;
            font-weight: 600;
        }}
        
        .stats {{
            font-size: 0.9rem;
            opacity: 0.9;
            margin-top: 0.5rem;
        }}
        
        .container {{
            display: flex;
            width: 100%;
            margin: 0;
            padding: 1rem;
            gap: 1rem;
            min-height: calc(100vh - 80px);
            align-items: flex-start;
        }}
        
        .sidebar {{
            width: 380px;
            background: white;
            border-radius: 12px;
            padding: 1.5rem;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
            height: fit-content;
        }}
        
        .sidebar h2 {{
            color: #2c3e50;
            font-size: 1.3rem;
            margin-bottom: 1rem;
            border-bottom: 2px solid #eee;
            padding-bottom: 0.5rem;
        }}
        
        .filter-mode {{
            margin-bottom: 1.5rem;
            padding: 1rem;
            background: #f8f9fa;
            border-radius: 8px;
        }}
        
        .filter-mode label {{
            display: block;
            font-weight: 600;
            margin-bottom: 0.5rem;
            color: #495057;
        }}
        
        .radio-group {{
            display: flex;
            gap: 1rem;
        }}
        
        .radio-group label {{
            font-weight: normal;
            display: flex;
            align-items: center;
            gap: 0.3rem;
        }}
        
        .tag-filters {{
            border: 1px solid #e9ecef;
            border-radius: 8px;
            padding: 1rem;
            background: #fdfdfd;
        }}
        
        .tag-item {{
            display: flex;
            align-items: center;
            padding: 0.4rem 0;
            border-bottom: 1px solid #f1f3f4;
        }}
        
        .tag-item:last-child {{
            border-bottom: none;
        }}
        
        .tag-item input {{
            margin-right: 0.7rem;
            transform: scale(1.1);
        }}
        
        .tag-item label {{
            flex: 1;
            cursor: pointer;
            font-size: 0.9rem;
            color: #495057;
        }}
        
        .tag-count {{
            color: #6c757d;
            font-size: 0.8rem;
            font-weight: 600;
        }}
        
        .clear-filters {{
            width: 100%;
            margin-top: 1rem;
            padding: 0.7rem;
            background: #e74c3c;
            color: white;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-weight: 600;
            transition: background 0.2s;
        }}
        
        .clear-filters:hover {{
            background: #c0392b;
        }}
        
        .main-content {{
            flex: 1;
            background: white;
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
            display: flex;
            flex-direction: column;
        }}
        
        .controls {{
            padding: 1.5rem;
            border-bottom: 1px solid #eee;
            background: #f8f9fa;
            border-radius: 12px 12px 0 0;
        }}
        
        .search-row {{
            display: flex;
            align-items: center;
            gap: 1rem;
            margin-bottom: 1rem;
        }}
        
        .search-input {{
            flex: 1;
            padding: 0.7rem 1rem;
            border: 2px solid #e9ecef;
            border-radius: 8px;
            font-size: 1rem;
            transition: border-color 0.2s;
        }}
        
        .search-input:focus {{
            outline: none;
            border-color: #667eea;
        }}
        
        .sort-control {{
            display: flex;
            align-items: center;
            gap: 0.5rem;
            font-size: 0.9rem;
        }}
        
        .results-info {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 0.9rem;
            color: #6c757d;
        }}
        
        .active-filters {{
            font-style: italic;
        }}
        
        .article-list {{
            flex: 1;
        }}
        
        .article-table {{
            width: 100%;
            border-collapse: collapse;
            table-layout: fixed;
        }}
        
        .article-table th {{
            background: #f1f3f4;
            padding: 1rem;
            text-align: left;
            font-weight: 600;
            border-bottom: 2px solid #dee2e6;
            position: sticky;
            top: 0;
            z-index: 10;
        }}
        
        .article-table td {{
            padding: 0.6rem 0.8rem;
            border-bottom: 1px solid #f1f3f4;
            vertical-align: top;
        }}
        
        .article-row:hover {{
            background: #f8f9fa;
        }}
        
        .article-row.even {{
            background: #fdffe6;
        }}
        
        .article-row.even:hover {{
            background: #f0f8e6;
        }}
        
        .col-index {{
            width: 40px;
            text-align: center;
            font-weight: 600;
            color: #6c757d;
        }}
        
        .col-date {{
            width: 85px;
            font-size: 0.85rem;
            color: #495057;
            white-space: nowrap;
        }}
        
        .col-title {{
            width: calc(100% - 375px); /* Total width minus index(40) + date(85) + tags(250) */
            min-width: 300px;
        }}
        
        .col-tags {{
            width: 250px;
            max-width: 250px;
            overflow: hidden;
            word-wrap: break-word;
        }}
        
        .article-title {{
            color: #2c3e50;
            text-decoration: none;
            font-weight: 500;
            line-height: 1.4;
            transition: color 0.2s;
        }}
        
        .article-title:hover {{
            color: #667eea;
        }}
        
        .tag-list {{
            display: flex;
            flex-wrap: wrap;
            gap: 0.3rem;
        }}
        
        .tag {{
            background: linear-gradient(45deg, #667eea, #764ba2);
            color: white;
            padding: 0.2rem 0.5rem;
            border-radius: 12px;
            font-size: 0.7rem;
            font-weight: 500;
        }}
        
        .no-results {{
            text-align: center;
            padding: 3rem;
            color: #6c757d;
        }}
        
        .export-btn {{
            background: #28a745;
            color: white;
            border: none;
            padding: 0.5rem 1rem;
            border-radius: 6px;
            cursor: pointer;
            font-size: 0.9rem;
            transition: background 0.2s;
        }}
        
        .export-btn:hover {{
            background: #218838;
        }}
        
        @media (max-width: 1200px) {{
            .container {{
                flex-direction: column;
                height: auto;
            }}
            
            .sidebar {{
                width: 100%;
            }}
        }}
        
        @media (max-width: 768px) {{
            .container {{
                padding: 1rem;
            }}
            
            .search-row {{
                flex-direction: column;
                align-items: stretch;
            }}
            
            .col-tags {{
                width: auto;
            }}
        }}
        
        /* Modal Styles */
        .modal-overlay {{
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.5);
            z-index: 1000;
            justify-content: center;
            align-items: center;
        }}
        
        .modal {{
            background: white;
            padding: 2rem;
            border-radius: 12px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.2);
            width: 90%;
            max-width: 500px;
            text-align: center;
            position: relative;
        }}
        
        .modal h3 {{
            margin-bottom: 1.5rem;
            color: #2c3e50;
        }}
        
        .modal-actions {{
            display: flex;
            gap: 1rem;
            justify-content: center;
            flex-wrap: wrap;
        }}
        
        .modal-btn {{
            padding: 0.8rem 1.5rem;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-size: 1rem;
            font-weight: 500;
            transition: transform 0.1s, box-shadow 0.1s;
            text-decoration: none;
            display: inline-block;
        }}
        
        .modal-btn:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 10px rgba(0,0,0,0.1);
        }}
        
        .btn-primary {{
            background: #667eea;
            color: white;
        }}
        
        .btn-secondary {{
            background: #28a745;
            color: white;
        }}
        
        .btn-close {{
            position: absolute;
            top: 10px;
            right: 15px;
            background: none;
            border: none;
            font-size: 1.5rem;
            cursor: pointer;
            color: #999;
        }}
        
        .btn-close:hover {{
            color: #333;
        }}
    </style>
</head>
<body>
    <div id="optionModal" class="modal-overlay">
        <div class="modal">
            <button class="btn-close" onclick="closeModal()">&times;</button>
            <h3>Choose an Action</h3>
            <div class="modal-actions">
                <a id="btnGoToUrl" href="#" target="_blank" class="modal-btn btn-primary" onclick="closeModal()">
                    🌐 Go to URL
                </a>
                <a id="btnDownloadPdf" href="#" target="_blank" class="modal-btn btn-secondary" onclick="closeModal()">
                    📄 PDF / Read
                </a>
            </div>
        </div>
    </div>

    <div class="header">
        <h1>📚 Medium Article Browser - Web Edition</h1>
        <div class="stats">
            {len(self.articles)} articles • {len(self.available_tags)} categories • Generated on {datetime.now().strftime("%Y-%b-%d %I:%M %p")} <span id="timeContainer">&nbsp; | &nbsp; Current Time: <span id="time"></span></span>
        </div>
    </div>
    
    <div class="container">
        <div class="sidebar">
            <h2>🏷️ Tag Filters</h2>
            
            <div class="filter-mode">
                <label>Match Mode:</label>
                <div class="radio-group">
                    <label><input type="radio" name="filterMode" value="ANY" checked> Any tag</label>
                    <label><input type="radio" name="filterMode" value="ALL"> All tags</label>
                </div>
            </div>
            
            <div class="tag-filters">
                {self.generate_tag_checkboxes(tag_stats)}
            </div>
            
            <button class="clear-filters" onclick="clearAllFilters()">Clear All Filters</button>
            
            <div id="filterStats" style="margin-top: 1rem; font-size: 0.8rem; color: #6c757d;"></div>
        </div>
        
        <div class="main-content">
            <div class="controls">
                <div class="search-row">
                    <input type="text" id="searchInput" class="search-input" 
                           placeholder="Search articles... (supports AND/OR operators)" 
                           onkeyup="filterArticles()">
                    <button class="export-btn" onclick="exportResults()">📥 Export</button>
                </div>
                
                <div class="results-info">
                    <div>
                        <label class="sort-control">
                            <input type="checkbox" id="reverseSort" onchange="filterArticles()"> 
                            Reverse sort (oldest first)
                        </label>
                    </div>
                    <div id="resultsCount">Showing {len(self.articles)} of {len(self.articles)} articles</div>
                </div>
                <div id="activeFilters" class="active-filters"></div>
            </div>
            
            <div class="article-list">
                <table class="article-table">
                    <thead>
                        <tr>
                            <th class="col-index">#</th>
                            <th class="col-date">Date</th>
                            <th class="col-title">Title</th>
                            <th class="col-tags">Tags</th>
                        </tr>
                    </thead>
                    <tbody id="articleTableBody">
                        <!-- Articles will be populated by JavaScript -->
                    </tbody>
                </table>
                
                <div id="noResults" class="no-results" style="display: none;">
                    <h3>🔍 No articles found</h3>
                    <p>Try adjusting your search criteria or clearing some filters.</p>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        // Article data
        const allArticles = {json.dumps(self.articles, indent=8)};
        const availableTags = {json.dumps(sorted(list(self.available_tags)))};
        
        let filteredArticles = [...allArticles];
        
        // Initialize
        document.addEventListener('DOMContentLoaded', function() {{
            updateFilterStats();
            filterArticles();
        }});
        
        function filterArticles() {{
            const searchTerm = document.getElementById('searchInput').value.toLowerCase().trim();
            const selectedTags = getSelectedTags();
            const filterMode = document.querySelector('input[name="filterMode"]:checked').value;
            const reverseSort = document.getElementById('reverseSort').checked;
            
            // Start with all articles
            filteredArticles = allArticles.filter(article => {{
                // Apply search filter
                if (searchTerm) {{
                    const title = article.title.toLowerCase();
                    if (!evaluateSearchQuery(title, searchTerm)) {{
                        return false;
                    }}
                }}
                
                // Apply tag filter
                if (selectedTags.length > 0) {{
                    const articleTags = article.tags || [];
                    if (filterMode === 'ANY') {{
                        return selectedTags.some(tag => articleTags.includes(tag));
                    }} else {{ // ALL
                        return selectedTags.every(tag => articleTags.includes(tag));
                    }}
                }}
                
                return true;
            }});
            
            // Sort articles
            filteredArticles.sort((a, b) => {{
                const dateA = new Date(a.date_obj);
                const dateB = new Date(b.date_obj);
                return reverseSort ? dateA - dateB : dateB - dateA;
            }});
            
            displayArticles();
            updateResultsCount();
            updateActiveFilters();
        }}
        
        function evaluateSearchQuery(text, query) {{
            // Simple search implementation with AND/OR
            if (!query) return true;
            
            // Split by AND/OR operators
            const terms = query.split(/\\s+(and|or)\\s+/i);
            let result = null;
            let operator = 'and';
            
            for (let i = 0; i < terms.length; i++) {{
                if (i % 2 === 0) {{ // Term
                    const termMatch = text.includes(terms[i].trim());
                    if (result === null) {{
                        result = termMatch;
                    }} else if (operator === 'and') {{
                        result = result && termMatch;
                    }} else if (operator === 'or') {{
                        result = result || termMatch;
                    }}
                }} else {{ // Operator
                    operator = terms[i].toLowerCase();
                }}
            }}
            
            return result !== null ? result : false;
        }}
        
        function getSelectedTags() {{
            const checkboxes = document.querySelectorAll('.tag-filters input[type="checkbox"]:checked');
            return Array.from(checkboxes).map(cb => cb.value);
        }}
        
        function displayArticles() {{
            const tbody = document.getElementById('articleTableBody');
            const noResults = document.getElementById('noResults');
            
            if (filteredArticles.length === 0) {{
                tbody.innerHTML = '';
                noResults.style.display = 'block';
                return;
            }}
            
            noResults.style.display = 'none';
            
            tbody.innerHTML = filteredArticles.map((article, index) => {{
                const rowClass = index % 2 === 1 ? 'even' : '';
                const tags = (article.tags || []).map(tag => 
                    `<span class="tag">${{tag}}</span>`
                ).join('');
                
                return `
                    <tr class="article-row ${{rowClass}}">
                        <td class="col-index">${{index + 1}}</td>
                        <td class="col-date">${{article.email_date}}</td>
                        <td class="col-title">
                            <a href="javascript:void(0)" onclick="openOptions('${{article.url}}')" class="article-title">
                                ${{article.title.replace(/</g, "&lt;").replace(/>/g, "&gt;")}}
                            </a>
                        </td>
                        <td class="col-tags">
                            <div class="tag-list">${{tags}}</div>
                        </td>
                    </tr>
                `;
            }}).join('');
        }}
        
        function updateResultsCount() {{
            const resultsCount = document.getElementById('resultsCount');
            resultsCount.textContent = `Showing ${{filteredArticles.length}} of ${{allArticles.length}} articles`;
        }}
        
        function updateActiveFilters() {{
            const selectedTags = getSelectedTags();
            const searchTerm = document.getElementById('searchInput').value.trim();
            const activeFilters = document.getElementById('activeFilters');
            
            const filters = [];
            if (searchTerm) filters.push(`Search: "${{searchTerm}}"`);
            if (selectedTags.length > 0) filters.push(`Tags: ${{selectedTags.join(', ')}}`);
            
            activeFilters.textContent = filters.length > 0 ? 
                `Active filters: ${{filters.join(' • ')}}` : 
                'No active filters';
        }}
        
        function updateFilterStats() {{
            const selectedTags = getSelectedTags();
            const filterStats = document.getElementById('filterStats');
            filterStats.textContent = selectedTags.length > 0 ? 
                `${{selectedTags.length}} tags selected` : 
                'No tags selected';
        }}
        
        function clearAllFilters() {{
            // Clear search
            document.getElementById('searchInput').value = '';
            
            // Clear tag checkboxes
            document.querySelectorAll('.tag-filters input[type="checkbox"]').forEach(cb => {{
                cb.checked = false;
            }});
            
            // Reset filter mode
            document.querySelector('input[name="filterMode"][value="ANY"]').checked = true;
            
            updateFilterStats();
            filterArticles();
        }}
        
        function exportResults() {{
            const exportData = {{
                export_date: new Date().toISOString(),
                filters_applied: {{
                    search_query: document.getElementById('searchInput').value,
                    selected_tags: getSelectedTags(),
                    filter_mode: document.querySelector('input[name="filterMode"]:checked').value
                }},
                total_articles: filteredArticles.length,
                articles: filteredArticles
            }};
            
            const dataStr = JSON.stringify(exportData, null, 2);
            const dataBlob = new Blob([dataStr], {{type: 'application/json'}});
            
            const link = document.createElement('a');
            link.href = URL.createObjectURL(dataBlob);
            link.download = `medium_articles_filtered_${{new Date().toISOString().split('T')[0]}}.json`;
            link.click();
        }}
        
        // Add event listeners for tag checkboxes
        document.addEventListener('change', function(e) {{
            if (e.target.matches('.tag-filters input[type="checkbox"]')) {{
                updateFilterStats();
                filterArticles();
            }}
            
            if (e.target.matches('input[name="filterMode"]')) {{
                filterArticles();
            }}
        }});
        
        // Time update functionality (updates live every minute)
        function updateCurrentTime() {{
            // Check if running from local file system
            if (window.location.protocol === 'file:') {{
                const timeContainer = document.getElementById("timeContainer");
                if (timeContainer) {{
                    timeContainer.style.display = 'none';
                }}
                return; // Disable clock and auto-refresh for local files
            }}

            const now = new Date();
            const year = now.getFullYear();
            const monthNames = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];
            const month = monthNames[now.getMonth()];
            const day = now.getDate().toString().padStart(2, '0');

            let hours = now.getHours();
            const minutes = now.getMinutes().toString().padStart(2, '0');
            const ampm = hours >= 12 ? 'PM' : 'AM';
            let hours12 = hours % 12;
            hours12 = hours12 === 0 ? 12 : hours12;
            const hoursStr = hours12.toString().padStart(2, '0');

            // Auto-Refresh Logic (Target: 8:10 AM)
            const refreshTime = new Date();
            refreshTime.setHours(8, 10, 0, 0);

            let loadTime;
            try {{
                loadTime = new Date(performance.timeOrigin);
            }} catch(e) {{
                loadTime = new Date(); // Fallback
            }}

            // If now is past today's 8:10 AM
            if (now > refreshTime) {{
                // If loaded before today's 8:10 AM, we need to refresh
                if (loadTime < refreshTime) {{
                    console.log("Auto-refreshing daily content...");
                    location.reload();
                    return;
                }}
                // Assume next refresh is tomorrow
                refreshTime.setDate(refreshTime.getDate() + 1);
            }}

            // Calculate countdown
            const diffMs = refreshTime - now;
            const diffHrs = Math.floor(diffMs / (1000 * 60 * 60));
            const diffMins = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60));
            const diffStr = `${{diffHrs.toString().padStart(2, '0')}} hour ${{diffMins.toString().padStart(2, '0')}} min`;

            // Format Refresh Time Target
            const rYear = refreshTime.getFullYear();
            const rMonth = monthNames[refreshTime.getMonth()];
            const rDay = refreshTime.getDate().toString().padStart(2, '0');
            const rHours = refreshTime.getHours().toString().padStart(2, '0');
            const rMinutes = refreshTime.getMinutes().toString().padStart(2, '0');
            const refreshTimeStr = `${{rYear}}-${{rMonth}}-${{rDay}} ${{rHours}}:${{rMinutes}}`;

            // Display current time in YYYY-MMM-DD hh:mm AM/PM format
            const timeElement = document.getElementById("time");
            if (timeElement) {{
                timeElement.textContent = `${{year}}-${{month}}-${{day}} ${{hoursStr}}:${{minutes}} ${{ampm}}  |  Next Refresh cycle in ${{diffStr}} at ${{refreshTimeStr}}`;
            }}
        }}

        // Check every minute
        setInterval(updateCurrentTime, 60000);
        updateCurrentTime(); // run immediately on load
        
        // Modal functionality
        function openOptions(url) {{
            const modal = document.getElementById('optionModal');
            const btnGoToUrl = document.getElementById('btnGoToUrl');
            const btnDownloadPdf = document.getElementById('btnDownloadPdf');
            
            // Set URLs
            btnGoToUrl.href = url;
            // Use r.jina.ai for clean reader view/PDF readiness or similar service
            // Alternatively use printfriendly: `https://www.printfriendly.com/print?url=${{encodeURIComponent(url)}}`
            // For now, using jina.ai as it is popular for "content from URL"
            btnDownloadPdf.href = `https://www.printfriendly.com/print?url=${{encodeURIComponent(url)}}`;
            
            modal.style.display = 'flex';
        }}
        
        function closeModal() {{
            document.getElementById('optionModal').style.display = 'none';
        }}
        
        // Close modal when clicking outside
        document.getElementById('optionModal').addEventListener('click', function(e) {{
            if (e.target === this) {{
                closeModal();
            }}
        }});
    </script>
</body>
</html>"""

        # Write HTML file
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(html_content)

        return True


class ComprehensiveProcessor:
    """Manages the complete processing pipeline"""

    def __init__(self):
        self.classifier = ArticleClassifier()

    def find_dated_files(self, pattern: str) -> List[str]:
        """Find all files matching the given pattern with YYYY_MM_DD date format."""
        files = []
        date_pattern = re.compile(pattern.replace("YYYY_MM_DD", r"(\d{4}_\d{2}_\d{2})"))

        for filename in os.listdir("."):
            if date_pattern.match(filename):
                files.append(filename)

        # Sort by date (newest first)
        files.sort(reverse=True)
        return files

    def load_json_file(self, filepath: str) -> Dict:
        """Load JSON file and return the data."""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading {filepath}: {e}")
            return {}

    def load_master_database(self) -> Dict:
        """Load or create the master historical database"""
        master_file = "medium_articles_master.json"

        if os.path.exists(master_file):
            print(f"📚 Loading existing master database: {master_file}")
            return self.load_json_file(master_file)
        else:
            print(f"📚 Creating new master database: {master_file}")
            return {
                "created_date": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat(),
                "total_unique_articles": 0,
                "update_history": [],
                "description": "Master historical database of all Medium articles",
                "articles": [],
            }

    def update_master_database(self, new_articles: List[Dict]) -> Dict:
        """Update the master database with new articles"""
        print("🔄 Updating master historical database...")

        # Load existing master database
        master_data = self.load_master_database()

        # Create URL index for existing articles
        existing_urls = {
            article["url"]: article for article in master_data.get("articles", [])
        }

        # Track statistics
        added_count = 0
        updated_count = 0

        # Process new articles
        for article in new_articles:
            url = article.get("url", "")
            if not url:
                continue

            # Fix title before saving to master
            if "title" in article:
                article["title"] = fix_title(article["title"])

            if url in existing_urls:
                # Article exists, update if newer or has more data
                existing = existing_urls[url]
                if len(str(article)) > len(
                    str(existing)
                ):  # Simple heuristic for "more data"
                    existing_urls[url] = article
                    updated_count += 1
            else:
                # New article
                existing_urls[url] = article
                added_count += 1

        # Update master data
        master_data["articles"] = list(existing_urls.values())
        master_data["total_unique_articles"] = len(master_data["articles"])
        master_data["last_updated"] = datetime.now().isoformat()

        # Add update history entry
        update_entry = {
            "date": datetime.now().isoformat(),
            "articles_added": added_count,
            "articles_updated": updated_count,
            "total_articles": len(master_data["articles"]),
        }

        if "update_history" not in master_data:
            master_data["update_history"] = []
        master_data["update_history"].append(update_entry)

        # Keep only last 50 updates in history
        if len(master_data["update_history"]) > 50:
            master_data["update_history"] = master_data["update_history"][-50:]

        # Sort articles by email_date (newest first)
        master_data["articles"].sort(
            key=lambda x: x.get("email_date", ""), reverse=True
        )

        # Save updated master database
        master_file = "medium_articles_master.json"
        with open(master_file, "w", encoding="utf-8") as f:
            json.dump(master_data, f, indent=2, ensure_ascii=False)

        print(f"✅ Master database updated:")
        print(f"   📈 Articles added: {added_count}")
        print(f"   🔄 Articles updated: {updated_count}")
        print(f"   📊 Total articles: {len(master_data['articles'])}")

        return master_data

    def merge_and_process_all(self):
        """Merge all dated files and process through complete pipeline"""
        print("\n" + "=" * 60)
        print("🚀 COMPREHENSIVE PROCESSING PIPELINE")
        print("=" * 60)

        # Step 1: Find and merge all dated files
        print("📋 Step 1: Merging all dated files...")
        regular_files = self.find_dated_files("medium_articles_YYYY_MM_DD.json")

        if not regular_files:
            print("❌ No dated files found for merging")
            return False

        print(f"📁 Found {len(regular_files)} dated files: {regular_files}")

        # Collect all articles from dated files
        all_articles = []
        for filename in regular_files:
            data = self.load_json_file(filename)
            if data and "articles" in data:
                all_articles.extend(data["articles"])

        # Remove duplicates by URL
        unique_articles = {}
        for article in all_articles:
            url = article.get("url", "")
            if url:
                unique_articles[url] = article

        merged_articles = list(unique_articles.values())
        print(
            f"✅ Merged {len(merged_articles)} unique articles from {len(regular_files)} files"
        )

        # Step 2: Update master database
        print("\n📋 Step 2: Updating master database...")
        master_data = self.update_master_database(merged_articles)
        master_articles = master_data.get("articles", [])

        # Step 3: Create current files
        print("\n📋 Step 3: Creating current merged files...")
        self._save_current_files(merged_articles)

        # Step 4: Classify articles (use master database articles)
        print("\n📋 Step 4: Classifying articles...")
        classified_articles, category_stats = self.classifier.classify_all_articles(
            master_articles
        )

        # Print classification summary
        print(f"\n🏷️  Classification Summary ({len(classified_articles)} articles)")
        sorted_categories = sorted(
            category_stats.items(), key=lambda x: x[1], reverse=True
        )
        for category, count in sorted_categories[:10]:  # Show top 10
            percentage = (count / len(classified_articles)) * 100
            print(f"  {category:<20} {count:>4} articles ({percentage:5.1f}%)")

        # Save classified articles
        classified_data = {
            "classification_date": datetime.now().isoformat(),
            "total_articles": len(classified_articles),
            "category_statistics": category_stats,
            "articles": classified_articles,
        }

        with open("medium_articles_classified.json", "w", encoding="utf-8") as f:
            json.dump(classified_data, f, indent=2, ensure_ascii=False)
        print(f"✅ Classified articles saved: medium_articles_classified.json")

        # Step 5: Generate web browser
        print("\n📋 Step 5: Generating web browser...")
        web_generator = WebBrowserGenerator(classified_articles)
        success = web_generator.generate_html("medium_article_browser.html")

        if success:
            print(f"✅ Web browser generated: medium_article_browser.html")

        # Final summary
        print("\n" + "=" * 60)
        print("🎉 COMPREHENSIVE PROCESSING COMPLETE!")
        print("=" * 60)

        output_files = [
            "medium_articles_master.json",
            "medium_articles.json",
            "medium_articles_classified.json",
            "medium_article_browser.html",
        ]

        print("📄 Output files generated:")
        for filename in output_files:
            if os.path.exists(filename):
                size = os.path.getsize(filename)
                print(f"   ✅ {filename:<35} ({size:,} bytes)")

        print(f"\n📊 Final statistics:")
        print(f"   📚 Total articles in master DB: {len(master_data['articles'])}")
        print(f"   🏷️  Categories identified: {len(category_stats)}")
        print(f"   🌐 Web interface ready: medium_article_browser.html")

        return True

    def regenerate_html_from_master(self):
        """Regenerate classified data and HTML from master database"""
        print("\n" + "=" * 60)
        print("🔄 REGENERATING HTML FROM MASTER DATABASE")
        print("=" * 60)

        master_data = self.load_master_database()
        master_articles = master_data.get("articles", [])

        if not master_articles:
            print("❌ No articles found in master database")
            return False

        print(f"📚 Master database contains {len(master_articles)} articles")

        # Classify articles
        classified_articles, category_stats = self.classifier.classify_all_articles(
            master_articles
        )

        # Save classified articles
        classified_data = {
            "classification_date": datetime.now().isoformat(),
            "total_articles": len(classified_articles),
            "category_statistics": category_stats,
            "articles": classified_articles,
        }

        with open("medium_articles_classified.json", "w", encoding="utf-8") as f:
            json.dump(classified_data, f, indent=2, ensure_ascii=False)
        print("✅ Classified articles saved: medium_articles_classified.json")

        # Generate HTML
        web_generator = WebBrowserGenerator(classified_articles)
        success = web_generator.generate_html("medium_article_browser.html")

        if success:
            print("✅ Web browser regenerated: medium_article_browser.html")

        return success

    def _save_current_files(self, articles):
        """Save current merged files for compatibility"""
        merged_data = {
            "extraction_date": datetime.now().isoformat(),
            "total_unique_articles": len(articles),
            "description": f"Current merged Medium articles ({len(articles)} articles)",
            "articles": articles,
        }

        # Sort articles by email_date (newest first)
        merged_data["articles"].sort(
            key=lambda x: x.get("email_date", ""), reverse=True
        )

        with open("medium_articles.json", "w", encoding="utf-8") as f:
            json.dump(merged_data, f, indent=2, ensure_ascii=False)

        print(f"💾 Saved current articles: medium_articles.json")


def main():
    """Main function to extract Medium articles and save to JSON"""

    parser = argparse.ArgumentParser(
        description="Extract Medium articles or regenerate HTML from master database."
    )
    parser.add_argument(
        "--regen-html",
        action="store_true",
        help="Skip Gmail and regenerate HTML from medium_articles_master.json",
    )
    args = parser.parse_args()

    if args.regen_html:
        processor = ComprehensiveProcessor()
        success = processor.regenerate_html_from_master()
        sys.exit(0 if success else 1)

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
        if result != "OK":
            print(
                f"❌ Failed to select folder '{folder_name}'. Please check if the folder exists."
            )
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
            subject = subject.decode("utf-8", errors="ignore")
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
                    html_content = part.get_payload(decode=True).decode(
                        "utf-8", errors="ignore"
                    )
                    break
        else:
            if msg.get_content_type() == "text/html":
                html_content = msg.get_payload(decode=True).decode(
                    "utf-8", errors="ignore"
                )

        if html_content:
            articles = extract_articles_from_email(html_content, email_date)
            all_articles.extend(articles)

    # Close Gmail connection
    mail.close()
    mail.logout()

    # Save all articles together
    current_date = datetime.now().strftime("%Y_%m_%d")
    filename = f"medium_articles_{current_date}.json"
    result = {
        "extraction_date": datetime.now().isoformat(),
        "total_emails_processed": len(email_ids),
        "total_articles_found": len(all_articles),
        "description": "All Medium articles extracted from Gmail",
        "articles": all_articles,
    }

    if all_articles:
        # Save all articles to single file
        with open(filename, "w", encoding="utf-8") as jsonfile:
            json.dump(result, jsonfile, indent=2, ensure_ascii=False)

        print(f"\n✅ Extracted {len(all_articles)} total articles:")
        print(f"    Saved to: {filename}")

        # Show sample articles
        print(f"\n📋 Sample articles:")
        for i, article in enumerate(all_articles[:3]):
            print(
                f"{i + 1}. {article['title'][:60]}{'...' if len(article['title']) > 60 else ''}"
            )
            print(
                f"   🔗 URL: {article['url'][:80]}{'...' if len(article['url']) > 80 else ''}"
            )
            print(f"   📅 Date: {article['email_date']}")

        # ===== COMPREHENSIVE PROCESSING PIPELINE =====
        print(f"\n🚀 Starting comprehensive processing pipeline...")
        processor = ComprehensiveProcessor()

        try:
            success = processor.merge_and_process_all()

            if success:
                print(f"\n🎯 DAILY WORKFLOW COMPLETE!")
                print(f"📝 All data preserved in master database")
                print(f"🏷️  Articles classified and tagged")
                print(f"🌐 Web interface ready: medium_article_browser.html")
                print(f"\n💡 Next steps:")
                print(f"   • Open medium_article_browser.html in your browser")
                print(f"   • Run: python Enhanced_Articles_Tk.py for GUI")
                print(f"   • Your data is safely stored in medium_articles_master.json")
            else:
                print(f"\n⚠️  Gmail extraction completed but processing pipeline failed")
                print(f"   Your articles are saved in: {filename}")

        except Exception as e:
            print(f"\n❌ Processing pipeline error: {str(e)}")
            print(f"   Gmail extraction completed successfully: {filename}")
            print(f"   You can run comprehensive processing separately if needed")

    else:
        print("❌ No articles found")


if __name__ == "__main__":
    main()
