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
from typing import Dict, List, Set
from collections import defaultdict

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


# ===== COMPREHENSIVE PROCESSING CLASSES =====

class ArticleClassifier:
    """Article classification system for automatic tagging"""
    
    def __init__(self):
        # Define classification rules with keywords for each category
        self.classification_rules = {
            'Python': {
                'keywords': ['python', 'django', 'flask', 'pandas', 'numpy', 'fastapi', 'pytest', 'pip', 'conda', 'jupyter'],
                'patterns': [r'\bpy\b', r'python\s*\d', r'\.py\b']
            },
            'JavaScript/Node': {
                'keywords': ['javascript', 'node', 'nodejs', 'npm', 'yarn', 'express', 'nest', 'typescript', 'js'],
                'patterns': [r'\bjs\b', r'node\.js', r'\.js\b']
            },
            'AI/ML': {
                'keywords': ['artificial intelligence', 'machine learning', 'deep learning', 'neural network', 
                            'tensorflow', 'pytorch', 'scikit-learn', 'keras', 'opencv', 'nlp', 'computer vision'],
                'patterns': [r'\bai\b', r'\bml\b', r'neural\s+network']
            },
            'LLM/GPT': {
                'keywords': ['llm', 'gpt', 'chatgpt', 'openai', 'claude', 'transformer', 'bert', 'large language model',
                            'prompt engineering', 'fine-tuning', 'embedding'],
                'patterns': [r'gpt-?\d', r'\bllm\b']
            },
            'AWS/Cloud': {
                'keywords': ['aws', 'amazon web services', 'ec2', 's3', 'lambda', 'cloudformation', 'terraform',
                            'azure', 'gcp', 'google cloud', 'kubernetes', 'docker', 'serverless'],
                'patterns': [r'\baws\b', r'\bgcp\b', r'\bk8s\b']
            },
            'Linux/DevOps': {
                'keywords': ['linux', 'ubuntu', 'centos', 'bash', 'shell', 'devops', 'ci/cd', 'jenkins', 
                            'gitlab', 'github actions', 'ansible', 'puppet', 'chef'],
                'patterns': [r'ci/cd', r'\.sh\b']
            },
            'React/Frontend': {
                'keywords': ['react', 'reactjs', 'jsx', 'redux', 'next.js', 'gatsby', 'hooks', 'component'],
                'patterns': [r'react\.js', r'next\.js']
            },
            'Angular': {
                'keywords': ['angular', 'angularjs', 'typescript', 'rxjs', 'ngrx', 'ionic'],
                'patterns': [r'angular\s*\d+']
            },
            'HTML/CSS/Browser': {
                'keywords': ['html', 'css', 'sass', 'scss', 'bootstrap', 'tailwind', 'responsive', 'frontend',
                            'browser', 'dom', 'web development', 'css3', 'html5'],
                'patterns': [r'\bdom\b', r'css\d?', r'html\d?']
            },
            'Database': {
                'keywords': ['database', 'sql', 'mysql', 'postgresql', 'mongodb', 'redis', 'elasticsearch',
                            'nosql', 'orm', 'prisma', 'sequelize'],
                'patterns': [r'\bsql\b', r'\bdb\b']
            },
            'Mobile': {
                'keywords': ['mobile', 'ios', 'android', 'flutter', 'react native', 'swift', 'kotlin', 'xamarin'],
                'patterns': [r'react\s+native', r'\bios\b']
            },
            'Security': {
                'keywords': ['security', 'authentication', 'authorization', 'oauth', 'jwt', 'encryption',
                            'cybersecurity', 'vulnerability', 'penetration testing'],
                'patterns': [r'\bauth\b', r'\bjwt\b']
            },
            'Social/Career': {
                'keywords': ['career', 'interview', 'job', 'hiring', 'remote work', 'freelance', 'startup',
                            'leadership', 'management', 'team', 'culture', 'diversity', 'inclusion'],
                'patterns': [r'remote\s+work']
            },
            'Tutorial/Learning': {
                'keywords': ['tutorial', 'guide', 'beginner', 'learn', 'course', 'education', 'teaching',
                            'how to', 'step by step', 'getting started'],
                'patterns': [r'how\s+to', r'step\s+by\s+step']
            },
            'Performance': {
                'keywords': ['performance', 'optimization', 'speed', 'benchmark', 'profiling', 'caching',
                            'memory', 'cpu', 'latency', 'scaling'],
                'patterns': [r'performance', r'optimization']
            }
        }
    
    def classify_article(self, article):
        """Classify a single article and return list of matching categories"""
        title = article.get('title', '').lower()
        url = article.get('url', '').lower()
        
        # Combine title and URL for analysis
        content = f"{title} {url}"
        
        matched_categories = []
        category_scores = {}
        
        for category, rules in self.classification_rules.items():
            score = 0
            
            # Check keywords
            for keyword in rules['keywords']:
                if keyword.lower() in content:
                    score += 1
            
            # Check patterns
            for pattern in rules.get('patterns', []):
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
            classified_article['tags'] = categories
            classified_article['tag_scores'] = scores
            
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
                article['date_obj'] = datetime.strptime(article['email_date'], '%Y-%m-%d').isoformat()
            except:
                article['date_obj'] = datetime.now().isoformat()
            
            # Collect tags
            tags = article.get('tags', [])
            self.available_tags.update(tags)
    
    def calculate_tag_stats(self):
        """Calculate tag statistics"""
        tag_counts = defaultdict(int)
        for article in self.articles:
            for tag in article.get('tags', []):
                tag_counts[tag] += 1
        
        return sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)
    
    def generate_html(self, output_file='medium_article_browser.html'):
        """Generate the complete HTML page"""
        if not self.articles:
            print("❌ No articles to generate HTML for.")
            return False
        
        tag_stats = self.calculate_tag_stats()
        
        # Create a simplified version of the HTML for space
        html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Medium Article Browser</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #f8f9fa; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 1rem; }}
        .container {{ display: flex; padding: 1rem; gap: 1rem; }}
        .sidebar {{ width: 300px; background: white; border-radius: 8px; padding: 1rem; }}
        .main-content {{ flex: 1; background: white; border-radius: 8px; padding: 1rem; }}
        .article-card {{ border: 1px solid #eee; border-radius: 6px; padding: 1rem; margin-bottom: 1rem; }}
        .article-title {{ font-weight: 600; margin-bottom: 0.5rem; }}
        .article-title a {{ color: #2c3e50; text-decoration: none; }}
        .article-meta {{ color: #666; font-size: 0.9rem; margin-bottom: 0.5rem; }}
        .tag {{ background: #667eea; color: white; padding: 0.2rem 0.5rem; border-radius: 12px; font-size: 0.75rem; margin-right: 0.3rem; }}
        .search-input {{ width: 100%; padding: 0.5rem; border: 1px solid #ddd; border-radius: 4px; margin-bottom: 1rem; }}
        .tag-filter {{ margin: 0.3rem 0; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📚 Medium Article Browser</h1>
        <p>{len(self.articles)} articles • {len(self.available_tags)} tags</p>
    </div>
    
    <div class="container">
        <div class="sidebar">
            <input type="text" id="searchInput" class="search-input" placeholder="Search articles...">
            <h3>Filter by Tags</h3>
            {"".join([f'<div class="tag-filter"><label><input type="checkbox" value="{tag}" class="tag-checkbox"> {tag} ({count})</label></div>' for tag, count in tag_stats])}
        </div>
        
        <div class="main-content">
            <div id="articlesContainer">
                {"".join([f'''<div class="article-card">
                    <div class="article-title"><a href="{article['url']}" target="_blank">{article['title']}</a></div>
                    <div class="article-meta">📅 {article['email_date']}</div>
                    <div>{"".join([f'<span class="tag">{tag}</span>' for tag in article.get('tags', [])])}</div>
                </div>''' for article in self.articles])}
            </div>
        </div>
    </div>
    
    <script>
        const articles = {json.dumps(self.articles)};
        let filteredArticles = [...articles];
        
        function filterArticles() {{
            const searchTerm = document.getElementById('searchInput').value.toLowerCase();
            const selectedTags = Array.from(document.querySelectorAll('.tag-checkbox:checked')).map(cb => cb.value);
            
            filteredArticles = articles.filter(article => {{
                const matchesSearch = !searchTerm || 
                    article.title.toLowerCase().includes(searchTerm) || 
                    article.url.toLowerCase().includes(searchTerm);
                
                const matchesTags = selectedTags.length === 0 || 
                    selectedTags.some(tag => (article.tags || []).includes(tag));
                
                return matchesSearch && matchesTags;
            }});
            
            renderArticles();
        }}
        
        function renderArticles() {{
            const container = document.getElementById('articlesContainer');
            container.innerHTML = filteredArticles.map(article => `
                <div class="article-card">
                    <div class="article-title"><a href="${{article.url}}" target="_blank">${{article.title}}</a></div>
                    <div class="article-meta">📅 ${{article.email_date}}</div>
                    <div>${{(article.tags || []).map(tag => `<span class="tag">${{tag}}</span>`).join('')}}</div>
                </div>
            `).join('');
        }}
        
        document.getElementById('searchInput').addEventListener('input', filterArticles);
        document.querySelectorAll('.tag-checkbox').forEach(cb => cb.addEventListener('change', filterArticles));
    </script>
</body>
</html>'''
        
        # Write HTML file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return True


class ComprehensiveProcessor:
    """Manages the complete processing pipeline"""
    
    def __init__(self):
        self.classifier = ArticleClassifier()
    
    def find_dated_files(self, pattern: str) -> List[str]:
        """Find all files matching the given pattern with YYYY_MM_DD date format."""
        files = []
        date_pattern = re.compile(pattern.replace('YYYY_MM_DD', r'(\d{4}_\d{2}_\d{2})'))
        
        for filename in os.listdir('.'):
            if date_pattern.match(filename):
                files.append(filename)
        
        # Sort by date (newest first)
        files.sort(reverse=True)
        return files

    def load_json_file(self, filepath: str) -> Dict:
        """Load JSON file and return the data."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading {filepath}: {e}")
            return {}

    def load_master_database(self) -> Dict:
        """Load or create the master historical database"""
        master_file = 'medium_articles_master.json'
        
        if os.path.exists(master_file):
            print(f"📚 Loading existing master database: {master_file}")
            return self.load_json_file(master_file)
        else:
            print(f"📚 Creating new master database: {master_file}")
            return {
                'created_date': datetime.now().isoformat(),
                'last_updated': datetime.now().isoformat(),
                'total_unique_articles': 0,
                'update_history': [],
                'description': 'Master historical database of all Medium articles',
                'articles': []
            }

    def update_master_database(self, new_articles: List[Dict]) -> Dict:
        """Update the master database with new articles"""
        print("🔄 Updating master historical database...")
        
        # Load existing master database
        master_data = self.load_master_database()
        
        # Create URL index for existing articles
        existing_urls = {article['url']: article for article in master_data.get('articles', [])}
        
        # Track statistics
        added_count = 0
        updated_count = 0
        
        # Process new articles
        for article in new_articles:
            url = article.get('url', '')
            if not url:
                continue
                
            if url in existing_urls:
                # Article exists, update if newer or has more data
                existing = existing_urls[url]
                if len(str(article)) > len(str(existing)):  # Simple heuristic for "more data"
                    existing_urls[url] = article
                    updated_count += 1
            else:
                # New article
                existing_urls[url] = article
                added_count += 1
        
        # Update master data
        master_data['articles'] = list(existing_urls.values())
        master_data['total_unique_articles'] = len(master_data['articles'])
        master_data['last_updated'] = datetime.now().isoformat()
        
        # Add update history entry
        update_entry = {
            'date': datetime.now().isoformat(),
            'articles_added': added_count,
            'articles_updated': updated_count,
            'total_articles': len(master_data['articles'])
        }
        
        if 'update_history' not in master_data:
            master_data['update_history'] = []
        master_data['update_history'].append(update_entry)
        
        # Keep only last 50 updates in history
        if len(master_data['update_history']) > 50:
            master_data['update_history'] = master_data['update_history'][-50:]
        
        # Sort articles by email_date (newest first)
        master_data['articles'].sort(
            key=lambda x: x.get('email_date', ''), 
            reverse=True
        )
        
        # Save updated master database
        master_file = 'medium_articles_master.json'
        with open(master_file, 'w', encoding='utf-8') as f:
            json.dump(master_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Master database updated:")
        print(f"   📈 Articles added: {added_count}")
        print(f"   🔄 Articles updated: {updated_count}")  
        print(f"   📊 Total articles: {len(master_data['articles'])}")
        
        return master_data

    def merge_and_process_all(self):
        """Merge all dated files and process through complete pipeline"""
        print("\n" + "="*60)
        print("🚀 COMPREHENSIVE PROCESSING PIPELINE")
        print("="*60)
        
        # Step 1: Find and merge all dated files
        print("📋 Step 1: Merging all dated files...")
        regular_files = self.find_dated_files('medium_articles_YYYY_MM_DD.json')
        
        if not regular_files:
            print("❌ No dated files found for merging")
            return False
            
        print(f"📁 Found {len(regular_files)} dated files: {regular_files}")
        
        # Collect all articles from dated files
        all_articles = []
        for filename in regular_files:
            data = self.load_json_file(filename)
            if data and 'articles' in data:
                all_articles.extend(data['articles'])
        
        # Remove duplicates by URL
        unique_articles = {}
        for article in all_articles:
            url = article.get('url', '')
            if url:
                unique_articles[url] = article
        
        merged_articles = list(unique_articles.values())
        print(f"✅ Merged {len(merged_articles)} unique articles from {len(regular_files)} files")
        
        # Step 2: Update master database
        print("\n📋 Step 2: Updating master database...")
        master_data = self.update_master_database(merged_articles)
        
        # Step 3: Create current files
        print("\n📋 Step 3: Creating current merged files...")
        self._save_current_files(merged_articles)
        
        # Step 4: Classify articles
        print("\n📋 Step 4: Classifying articles...")
        classified_articles, category_stats = self.classifier.classify_all_articles(merged_articles)
        
        # Print classification summary
        print(f"\n🏷️  Classification Summary ({len(classified_articles)} articles)")
        sorted_categories = sorted(category_stats.items(), key=lambda x: x[1], reverse=True)
        for category, count in sorted_categories[:10]:  # Show top 10
            percentage = (count / len(classified_articles)) * 100
            print(f"  {category:<20} {count:>4} articles ({percentage:5.1f}%)")
        
        # Save classified articles
        classified_data = {
            'classification_date': datetime.now().isoformat(),
            'total_articles': len(classified_articles),
            'category_statistics': category_stats,
            'articles': classified_articles
        }
        
        with open('medium_articles_classified.json', 'w', encoding='utf-8') as f:
            json.dump(classified_data, f, indent=2, ensure_ascii=False)
        print(f"✅ Classified articles saved: medium_articles_classified.json")
        
        # Step 5: Generate web browser
        print("\n📋 Step 5: Generating web browser...")
        web_generator = WebBrowserGenerator(classified_articles)
        success = web_generator.generate_html('medium_article_browser.html')
        
        if success:
            print(f"✅ Web browser generated: medium_article_browser.html")
        
        # Final summary
        print("\n" + "="*60)
        print("🎉 COMPREHENSIVE PROCESSING COMPLETE!")
        print("="*60)
        
        output_files = [
            'medium_articles_master.json',
            'medium_articles.json', 
            'medium_articles_classified.json',
            'medium_article_browser.html'
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
    
    def _save_current_files(self, articles):
        """Save current merged files for compatibility"""
        merged_data = {
            'extraction_date': datetime.now().isoformat(),
            'total_unique_articles': len(articles),
            'description': f'Current merged Medium articles ({len(articles)} articles)',
            'articles': articles
        }
        
        # Sort articles by email_date (newest first)
        merged_data['articles'].sort(
            key=lambda x: x.get('email_date', ''), 
            reverse=True
        )
        
        with open('medium_articles.json', 'w', encoding='utf-8') as f:
            json.dump(merged_data, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Saved current articles: medium_articles.json")


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
        for i, article in enumerate(all_articles[:3]):
            print(f"{i+1}. {article['title'][:60]}{'...' if len(article['title']) > 60 else ''}")
            print(f"   🔗 URL: {article['url'][:80]}{'...' if len(article['url']) > 80 else ''}")
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
