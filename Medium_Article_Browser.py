#!/usr/bin/env python3
"""
Medium Article Browser
A Tkinter GUI application to browse and search Medium articles from JSON file
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import json
import webbrowser
from datetime import datetime
import re

class MediumArticleBrowser:
    def __init__(self, root):
        self.root = root
        self.root.title("Medium Article Browser")
        self.root.geometry("1200x800")
        
        # Predefined keywords for highlighting
        self.highlight_keywords = [
            'python', 'javascript', 'react', 'angular', 'vue', 'node', 'ai', 'machine learning',
            'data science', 'docker', 'kubernetes', 'aws', 'git', 'github', 'api', 'fastapi',
            'django', 'flask', 'web development', 'frontend', 'backend', 'database', 'sql',
            'mongodb', 'postgresql', 'mysql', 'redis', 'microservices', 'devops', 'cicd',
            'testing', 'debugging', 'performance', 'security', 'authentication', 'jwt',
            'rest', 'graphql', 'typescript', 'java', 'spring', 'rust', 'go', 'c++', 'c#',
            'dotnet', 'mobile', 'ios', 'android', 'flutter', 'blockchain', 'cryptocurrency',
            'machine learning', 'deep learning', 'neural networks', 'nlp', 'opencv', 'tensorflow',
            'pytorch', 'pandas', 'numpy', 'matplotlib', 'seaborn', 'plotly', 'jupyter',
            'vs code', 'vscode', 'ide', 'editor', 'linux', 'ubuntu', 'macos', 'windows'
        ]
        
        # Current search keywords for highlighting
        self.current_search_keywords = []
        
        # Load articles data
        self.articles = []
        self.filtered_articles = []
        self.sorted_articles = []
        self.load_articles()
        
        # Create GUI
        self.setup_gui()
        
        # Initial display
        self.update_article_list()
    
    def load_articles(self):
        """Load articles from JSON file"""
        json_file = 'medium_articles.json'
        
        # Check if default file exists, if not, prompt for file selection
        import os
        if not os.path.exists(json_file):
            from tkinter import filedialog
            messagebox.showinfo("File Not Found", 
                              f"Default file '{json_file}' not found.\nPlease select a JSON file containing Medium articles.")
            
            json_file = filedialog.askopenfilename(
                title="Select Medium Articles JSON File",
                filetypes=[
                    ("JSON files", "*.json"),
                    ("All files", "*.*")
                ],
                initialdir=os.getcwd()
            )
            
            if not json_file:  # User cancelled file selection
                messagebox.showwarning("No File Selected", "No file selected. The application will start with no articles.")
                self.articles = []
                return
        
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.articles = data.get('articles', [])
                
            # Convert email_date to datetime for sorting
            for article in self.articles:
                try:
                    article['date_obj'] = datetime.strptime(article['email_date'], '%Y-%m-%d')
                except:
                    article['date_obj'] = datetime.now()
                    
            print(f"Loaded {len(self.articles)} articles from {json_file}")
            
            # Update window title to show loaded file
            if json_file != 'medium_articles.json':
                filename = os.path.basename(json_file)
                self.root.title(f"Medium Article Browser - {filename}")
            
        except FileNotFoundError:
            messagebox.showerror("Error", f"Selected file '{json_file}' not found!")
            self.articles = []
        except json.JSONDecodeError:
            messagebox.showerror("Error", f"Invalid JSON format in '{json_file}'!\nPlease select a valid Medium articles JSON file.")
            self.articles = []
        except Exception as e:
            messagebox.showerror("Error", f"Error loading file '{json_file}': {str(e)}")
            self.articles = []
    
    def setup_gui(self):
        """Setup the GUI layout"""
        
        # Create menu bar
        self.create_menu()
        
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        # Top controls frame
        controls_frame = ttk.Frame(main_frame)
        controls_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        controls_frame.columnconfigure(1, weight=1)
        
        # Reverse sort checkbox (default to newest first)
        self.reverse_var = tk.BooleanVar(value=True)  # Default to True for newest first
        reverse_check = ttk.Checkbutton(
            controls_frame, 
            text="Reverse sort (oldest first)", 
            variable=self.reverse_var,
            command=self.update_article_list
        )
        reverse_check.grid(row=0, column=0, padx=(0, 10), sticky=tk.W)
        
        # Search frame
        search_frame = ttk.Frame(controls_frame)
        search_frame.grid(row=0, column=1, sticky=(tk.W, tk.E))
        search_frame.columnconfigure(1, weight=1)
        
        # Search label
        search_label = ttk.Label(search_frame, text="Search:")
        search_label.grid(row=0, column=0, padx=(0, 5))
        
        # Search entry
        self.search_var = tk.StringVar()
        self.search_var.trace_add('write', self.on_search_change)
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, font=('Arial', 12))
        search_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10))
        
        # Add tooltip for search help
        self.create_tooltip(search_entry, 
            "Search with 'and'/'or' operators:\n" +
            "• python and machine learning\n" +
            "• react or angular\n" +
            "• python and (developer or 2025)\n" +
            "• (python or javascript) and api")
        
        # Clear button
        clear_btn = ttk.Button(search_frame, text="Clear", command=self.clear_search)
        clear_btn.grid(row=0, column=2)
        
        # Stats label
        self.stats_label = ttk.Label(main_frame, text="", font=('Arial', 10))
        self.stats_label.grid(row=1, column=0, sticky=tk.W, pady=(0, 5))
        
        # Articles list frame
        list_frame = ttk.Frame(main_frame)
        list_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        
        # Create Treeview for articles list
        columns = ('Index', 'Date', 'Title')
        self.tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=25)
        
        # Define headings
        self.tree.heading('Index', text='#')
        self.tree.heading('Date', text='Date')
        self.tree.heading('Title', text='Title')
        
        # Configure columns
        self.tree.column('Index', width=60, minwidth=50)
        self.tree.column('Date', width=100, minwidth=80)
        self.tree.column('Title', width=940, minwidth=400)
        
        # Configure tags for alternating row colors
        self.tree.tag_configure('even_row', background='#f0fff0', foreground='#000000')  # Light green bg, black text
        self.tree.tag_configure('odd_row', background='#ffffff', foreground='#000000')   # White bg, black text
        
        # Configure selection colors using ttk.Style
        style = ttk.Style()
        style.map('Treeview', 
                 background=[('selected', '#316AC5')],  # Blue background for selected
                 foreground=[('selected', '#ffffff')])  # White text for selected
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Grid the treeview and scrollbar
        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # Bind double-click event
        self.tree.bind('<Double-1>', self.on_article_click)
        self.tree.bind('<Return>', self.on_article_click)
        
        # Status bar
        status_frame = ttk.Frame(main_frame)
        status_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(10, 0))
        
        self.status_label = ttk.Label(
            status_frame, 
            text="Double-click an article to open in browser", 
            font=('Arial', 9),
            foreground='gray'
        )
        self.status_label.grid(row=0, column=0, sticky=tk.W)
        
        # Focus on search entry
        search_entry.focus()
    
    def create_menu(self):
        """Create menu bar"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open JSON File...", command=self.open_json_file, accelerator="Ctrl+O")
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit, accelerator="Ctrl+Q")
        
        # Bind keyboard shortcuts
        self.root.bind('<Control-o>', lambda e: self.open_json_file())
        self.root.bind('<Control-q>', lambda e: self.root.quit())
    
    def open_json_file(self):
        """Open a different JSON file"""
        from tkinter import filedialog
        import os
        
        json_file = filedialog.askopenfilename(
            title="Select Medium Articles JSON File",
            filetypes=[
                ("JSON files", "*.json"),
                ("All files", "*.*")
            ],
            initialdir=os.getcwd()
        )
        
        if json_file:  # User selected a file
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    articles = data.get('articles', [])
                
                # Convert email_date to datetime for sorting
                for article in articles:
                    try:
                        article['date_obj'] = datetime.strptime(article['email_date'], '%Y-%m-%d')
                    except:
                        article['date_obj'] = datetime.now()
                
                # Update articles and refresh display
                self.articles = articles
                self.update_article_list()
                
                # Update window title
                filename = os.path.basename(json_file)
                self.root.title(f"Medium Article Browser - {filename}")
                
                print(f"Loaded {len(self.articles)} articles from {json_file}")
                messagebox.showinfo("Success", f"Successfully loaded {len(self.articles)} articles from {filename}")
                
            except json.JSONDecodeError:
                messagebox.showerror("Error", f"Invalid JSON format in '{json_file}'!\nPlease select a valid Medium articles JSON file.")
            except Exception as e:
                messagebox.showerror("Error", f"Error loading file '{json_file}': {str(e)}")
    
    def on_search_change(self, *args):
        """Handle search text changes"""
        self.update_article_list()
    
    def clear_search(self):
        """Clear the search field"""
        self.search_var.set("")
    
    def parse_search_query(self, query):
        """Parse search query with 'and'/'or' operators and parentheses support"""
        query = query.lower().strip()
        if not query:
            return []
        
        try:
            # Handle parentheses first by expanding them
            expanded = self.expand_parentheses(query)
            return self.parse_or_groups(expanded)
        except:
            # Fallback to simple parsing if complex parsing fails
            return self.simple_parse(query)
    
    def expand_parentheses(self, query):
        """Expand parentheses using distribution logic"""
        # Example: "python and (developer or 2025)" becomes:
        # "python and developer or python and 2025"
        
        # Remove extra spaces and normalize
        query = re.sub(r'\s+', ' ', query).strip()
        
        # Find parentheses groups
        while '(' in query and ')' in query:
            # Find the first complete parentheses group
            start = query.find('(')
            count = 0
            end = start
            
            for i in range(start, len(query)):
                if query[i] == '(':
                    count += 1
                elif query[i] == ')':
                    count -= 1
                    if count == 0:
                        end = i
                        break
            
            if count != 0:  # Unmatched parentheses
                break
                
            # Extract the parts
            before = query[:start].strip()
            inside = query[start+1:end].strip()
            after = query[end+1:].strip()
            
            # Check if there's an 'and' before the parentheses
            if before.endswith(' and'):
                # Distribution: "A and (B or C)" -> "A and B or A and C"
                prefix = before[:-4].strip()  # Remove ' and'
                or_parts = re.split(r'\s+or\s+', inside)
                expanded_parts = []
                for part in or_parts:
                    if prefix:
                        expanded_parts.append(f"{prefix} and {part.strip()}")
                    else:
                        expanded_parts.append(part.strip())
                
                replacement = ' or '.join(expanded_parts)
                
                # Rebuild the query  
                if after:
                    query = replacement + ' ' + after
                else:
                    query = replacement
            else:
                # No distribution needed, just remove parentheses
                parts = []
                if before:
                    parts.append(before)
                parts.append(inside)
                if after:
                    parts.append(after)
                query = ' '.join(parts)
        
        return query
    
    def parse_or_groups(self, query):
        """Parse OR groups from expanded query"""
        # Split by 'or' (lowest precedence)
        or_groups = re.split(r'\s+or\s+', query)
        
        parsed_groups = []
        for group in or_groups:
            # Split by 'and' (higher precedence)  
            and_terms = re.split(r'\s+and\s+', group.strip())
            # Clean up terms
            and_terms = [term.strip() for term in and_terms if term.strip()]
            if and_terms:
                parsed_groups.append(and_terms)
        
        return parsed_groups
    
    def simple_parse(self, query):
        """Fallback simple parsing without parentheses"""
        # Remove parentheses and parse simply
        query = re.sub(r'[()]', '', query)
        
        # Split by 'or' first (lower precedence)
        or_groups = re.split(r'\s+or\s+', query)
        
        parsed_groups = []
        for group in or_groups:
            # Split by 'and' (higher precedence)
            and_terms = re.split(r'\s+and\s+', group.strip())
            # Clean up terms
            and_terms = [term.strip() for term in and_terms if term.strip()]
            if and_terms:
                parsed_groups.append(and_terms)
        
        return parsed_groups

    def evaluate_search_conditions(self, text, conditions):
        """Evaluate search conditions against text"""
        text = text.lower()
        
        # Reset sub-expressions for next search
        if hasattr(self, '_subexpressions'):
            delattr(self, '_subexpressions')
        
        # OR groups: at least one group must be satisfied
        for and_group in conditions:
            # AND terms: all terms in this group must be present
            if all(term in text for term in and_group):
                return True
        
        return False

    def extract_search_keywords(self, query):
        """Extract individual keywords from search query for highlighting"""
        # Remove 'and'/'or' operators and extract individual terms
        cleaned = re.sub(r'\s+(and|or)\s+', ' ', query.lower())
        keywords = [term.strip() for term in cleaned.split() if term.strip()]
        return keywords

    def filter_articles(self):
        """Filter articles based on search term with 'and'/'or' support"""
        search_term = self.search_var.get().strip()
        
        if not search_term:
            self.current_search_keywords = []
            return self.articles
        
        # Parse search query into conditions
        search_conditions = self.parse_search_query(search_term)
        if not search_conditions:
            self.current_search_keywords = []
            return self.articles
        
        # Extract keywords for highlighting
        self.current_search_keywords = self.extract_search_keywords(search_term)
        
        filtered = []
        for article in self.articles:
            title = article.get('title', '').lower()
            
            # If no 'and'/'or' operators, use simple search
            if len(search_conditions) == 1 and len(search_conditions[0]) == 1:
                if search_conditions[0][0] in title:
                    filtered.append(article)
            else:
                # Use advanced search with conditions
                if self.evaluate_search_conditions(title, search_conditions):
                    filtered.append(article)
        
        return filtered

    def update_article_list(self):
        """Update the articles list display"""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Filter articles
        self.filtered_articles = self.filter_articles()
        
        # Sort articles by date
        reverse_sort = self.reverse_var.get()
        sorted_articles = sorted(
            self.filtered_articles, 
            key=lambda x: x['date_obj'], 
            reverse=reverse_sort
        )
        
        # Store sorted articles for click handling
        self.sorted_articles = sorted_articles
        
        # Add articles to tree
        for i, article in enumerate(sorted_articles):
            title = article.get('title', 'No Title')
            date = article.get('email_date', 'No Date')
            index_num = i + 1  # 1-based index for display
            
            # Truncate very long titles
            if len(title) > 100:
                display_title = title[:97] + "..."
            else:
                display_title = title
            
            # Determine row color (alternating)
            row_tag = 'even_row' if i % 2 == 0 else 'odd_row'
            
            # Insert into tree with row coloring and index for click handling
            tags = [str(i), row_tag]  # Keep index tag for click handling + row color
            
            item_id = self.tree.insert('', 'end', values=(index_num, date, display_title), tags=tuple(tags))
        
        # Update stats
        total_articles = len(self.articles)
        filtered_count = len(self.filtered_articles)
        search_term = self.search_var.get().strip()
        
        if search_term:
            stats_text = f"Showing {filtered_count} of {total_articles} articles (filtered by '{search_term}')"
        else:
            stats_text = f"Showing all {total_articles} articles"
        
        self.stats_label.config(text=stats_text)
        
        # Update status
        sort_order = "oldest first" if self.reverse_var.get() else "newest first"
        status_text = f"Double-click to open • {sort_order} • Green rows for better readability"
        self.status_label.config(text=status_text)
    
    def on_article_click(self, event):
        """Handle article click to open in browser"""
        selection = self.tree.selection()
        if not selection:
            return
        
        item = selection[0]
        try:
            # Get the article index from tags
            tags = self.tree.item(item, 'tags')
            if tags:
                article_index = int(tags[0])
                article = self.sorted_articles[article_index]
                url = article.get('url', '')
                
                if url:
                    print(f"Opening URL: {url}")
                    webbrowser.open(url)
                    self.status_label.config(text=f"Opened: {article.get('title', 'Article')[:50]}...")
                else:
                    messagebox.showwarning("Warning", "No URL available for this article")
            else:
                messagebox.showerror("Error", "Could not identify article")
                
        except (ValueError, IndexError) as e:
            print(f"Error opening article: {e}")
            messagebox.showerror("Error", "Could not open article")

    def create_tooltip(self, widget, text):
        """Create a tooltip for a widget"""
        def on_enter(event):
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{event.x_root + 10}+{event.y_root + 10}")
            
            label = tk.Label(tooltip, text=text, 
                           background='#ffffe0', 
                           relief='solid', 
                           borderwidth=1,
                           font=('Arial', 9),
                           justify='left')
            label.pack()
            
            # Store tooltip reference
            widget.tooltip = tooltip
        
        def on_leave(event):
            if hasattr(widget, 'tooltip'):
                widget.tooltip.destroy()
                del widget.tooltip
        
        widget.bind('<Enter>', on_enter)
        widget.bind('<Leave>', on_leave)

def main():
    """Main function to run the application"""
    root = tk.Tk()
    app = MediumArticleBrowser(root)
    
    try:
        root.mainloop()
    except KeyboardInterrupt:
        print("\nApplication closed by user")

if __name__ == "__main__":
    main()