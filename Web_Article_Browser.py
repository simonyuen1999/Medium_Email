#!/usr/bin/env python3
"""
Web-based Medium Article Browser Generator
Creates an HTML page with the same functionality as the Tkinter application
"""

import json
import os
from datetime import datetime
from collections import defaultdict
import re

class WebMediumBrowser:
    def __init__(self):
        self.articles = []
        self.available_tags = set()
        
    def load_articles(self):
        """Load articles from medium_articles_classified.json or prompt for alternative"""
        # First, try to load the preferred default file
        default_file = "medium_articles_classified.json"
        
        if os.path.exists(default_file):
            json_file = default_file
            print(f"📁 Using default classified file: {json_file}")
        else:
            # Default file doesn't exist, look for alternatives
            json_files = [f for f in os.listdir('.') if f.startswith('medium_articles') and f.endswith('.json')]
            
            if not json_files:
                print(f"❌ Default file '{default_file}' not found and no other Medium articles JSON files found.")
                print("Please ensure medium_articles_classified.json exists or run the classification process.")
                return False
            
            print(f"⚠️ Default file '{default_file}' not found.")
            print("Available files:")
            for i, file in enumerate(json_files, 1):
                print(f"  {i}. {file}")
            
            try:
                choice = input(f"\nSelect a file (1-{len(json_files)}) or press Enter to exit: ").strip()
                if not choice:
                    return False
                
                index = int(choice) - 1
                if 0 <= index < len(json_files):
                    json_file = json_files[index]
                else:
                    print("Invalid selection.")
                    return False
            except (ValueError, KeyboardInterrupt):
                print("Operation cancelled.")
                return False
        
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.articles = data.get('articles', [])
            
            # Process articles and collect tags
            self.available_tags = set()
            for article in self.articles:
                # Add date object for JavaScript sorting
                try:
                    article['date_obj'] = datetime.strptime(article['email_date'], '%Y-%m-%d').isoformat()
                except:
                    article['date_obj'] = datetime.now().isoformat()
                
                # Collect tags
                tags = article.get('tags', [])
                self.available_tags.update(tags)
            
            print(f"✅ Loaded {len(self.articles)} articles with {len(self.available_tags)} unique tags")
            return True
            
        except Exception as e:
            print(f"❌ Error loading file: {str(e)}")
            return False
    
    def calculate_tag_stats(self):
        """Calculate tag statistics"""
        tag_counts = defaultdict(int)
        for article in self.articles:
            for tag in article.get('tags', []):
                tag_counts[tag] += 1
        
        return sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)
    
    def generate_html(self):
        """Generate the complete HTML page"""
        if not self.articles:
            print("❌ No articles to generate HTML for.")
            return
        
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
            height: calc(100vh - 80px);
        }}
        
        .sidebar {{
            width: 380px;
            background: white;
            border-radius: 12px;
            padding: 1.5rem;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
            overflow-y: auto;
            height: fit-content;
            max-height: 100%;
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
            max-height: 500px;
            overflow-y: auto;
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
            overflow-y: auto;
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
                max-height: 400px;
            }}
            
            .tag-filters {{
                max-height: 250px;
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
    </style>
</head>
<body>
    <div class="header">
        <h1>📚 Medium Article Browser - Web Edition</h1>
        <div class="stats">
            {len(self.articles)} articles • {len(self.available_tags)} categories • Generated on {datetime.now().strftime('%Y-%m-%d %H:%M')}
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
                            <a href="${{article.url}}" target="_blank" class="article-title">
                                ${{article.title}}
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
    </script>
</body>
</html>"""
        
        # Save HTML file
        html_filename = 'medium_article_browser.html'
        
        with open(html_filename, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"\n✅ Web browser generated: {html_filename}")
        print(f"🌐 Open in browser: file://{os.path.abspath(html_filename)}")
        
        return html_filename
    
    def generate_tag_checkboxes(self, tag_stats):
        """Generate HTML for tag checkboxes"""
        checkboxes = []
        for tag, count in tag_stats:
            safe_id = re.sub(r'[^a-zA-Z0-9]', '_', tag)
            checkboxes.append(f'''
                <div class="tag-item">
                    <input type="checkbox" id="tag_{safe_id}" value="{tag}">
                    <label for="tag_{safe_id}">{tag}</label>
                    <span class="tag-count">({count})</span>
                </div>''')
        return ''.join(checkboxes)

def main():
    """Main function to generate web browser"""
    print("🌐 Generating Web-based Medium Article Browser...")
    
    browser = WebMediumBrowser()
    
    if browser.load_articles():
        html_file = browser.generate_html()
        
        print(f"\n🎉 Web browser ready!")
        print(f"📁 File: {html_file}")
        print(f"🚀 Features:")
        print(f"   • Tag filtering with live counts")
        print(f"   • Advanced search with AND/OR operators")
        print(f"   • Responsive design for mobile/desktop")
        print(f"   • Export filtered results")
        print(f"   • Same functionality as Tkinter app")
        print(f"\n💡 Open the HTML file in any modern web browser!")
        
        # Optionally open in browser
        try:
            import webbrowser
            # Auto-open in browser for convenience
            webbrowser.open(f'file://{os.path.abspath(html_file)}')
            print(f"🌐 Opened in default browser!")
        except:
            print(f"💡 Manually open: {os.path.abspath(html_file)}")
    
    else:
        print("❌ Failed to load articles. Please check your JSON files.")

if __name__ == "__main__":
    main()