#!/usr/bin/env python3
"""
Enhanced Medium Article Browser with Tagging System
Supports multi-category classification and advanced filtering
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import json
import webbrowser
from datetime import datetime
import re
import os
from collections import defaultdict

class EnhancedMediumBrowser:
    def __init__(self, root):
        self.root = root
        self.root.title("Enhanced Medium Article Browser with Tags")
        self.root.geometry("1500x950")
        
        # Data
        self.articles = []
        self.filtered_articles = []
        self.available_tags = set()
        self.selected_tags = set()
        
        # GUI variables
        self.search_var = tk.StringVar()
        self.reverse_var = tk.BooleanVar(value=True)
        self.tag_filter_mode = tk.StringVar(value="ANY")  # ANY or ALL
        
        # Load articles
        self.load_articles()
        
        # Setup GUI
        self.setup_gui()
        
        # Initial display
        self.update_display()
    
    def load_articles(self):
        """Load articles with automatic file selection, defaulting to medium_articles_classified.json"""
        # First, try to load the preferred default file
        default_file = "medium_articles_classified.json"
        
        if os.path.exists(default_file):
            json_file = default_file
            print(f"📁 Using default classified file: {json_file}")
        else:
            # Default file doesn't exist, prompt user to select
            messagebox.showinfo("Default File Not Found", 
                              f"Default file '{default_file}' not found.\nPlease select a Medium articles JSON file.")
            json_file = filedialog.askopenfilename(
                title="Select Medium Articles JSON File",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            if not json_file:
                self.articles = []
                return
        
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.articles = data.get('articles', [])
            
            # Convert dates and collect tags
            self.available_tags = set()
            for article in self.articles:
                # Date conversion
                try:
                    article['date_obj'] = datetime.strptime(article['email_date'], '%Y-%m-%d')
                except:
                    article['date_obj'] = datetime.now()
                
                # Collect tags
                tags = article.get('tags', [])
                self.available_tags.update(tags)
            
            print(f"✅ Loaded {len(self.articles)} articles with {len(self.available_tags)} unique tags")
            
            # Update window title
            filename = os.path.basename(json_file)
            self.root.title(f"Enhanced Medium Browser - {filename}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error loading file: {str(e)}")
            self.articles = []
    
    def setup_gui(self):
        """Setup the enhanced GUI with tag filtering"""
        
        # Create menu
        self.create_menu()
        
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        # Left sidebar for tag filtering
        self.setup_tag_sidebar(main_frame)
        
        # Right panel for articles
        self.setup_article_panel(main_frame)
    
    def create_menu(self):
        """Create menu bar"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open...", command=self.open_file, accelerator="Cmd+O")
        file_menu.add_command(label="Classify Articles", command=self.classify_articles)
        file_menu.add_separator()
        file_menu.add_command(label="Export Filtered Results", command=self.export_results)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit, accelerator="Cmd+Q")
        
        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Show Tag Statistics", command=self.show_tag_stats)
        view_menu.add_command(label="Clear All Filters", command=self.clear_all_filters)
        
        # Bind keyboard shortcuts
        self.root.bind('<Command-o>', lambda e: self.open_file())
        self.root.bind('<Command-q>', lambda e: self.root.quit())
    
    def setup_tag_sidebar(self, parent):
        """Setup the left sidebar for tag filtering"""
        sidebar_frame = ttk.Frame(parent, width=380)
        sidebar_frame.grid(row=0, column=0, rowspan=3, sticky=(tk.W, tk.N, tk.S), padx=(0, 10))
        sidebar_frame.grid_propagate(False)  # Keep fixed width
        
        # Title
        ttk.Label(sidebar_frame, text="Tag Filters", font=('Arial', 14, 'bold')).grid(row=0, column=0, sticky=tk.W, pady=(0, 10))
        
        # Filter mode selection
        mode_frame = ttk.Frame(sidebar_frame)
        mode_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(mode_frame, text="Match:").grid(row=0, column=0, sticky=tk.W)
        ttk.Radiobutton(mode_frame, text="Any tag", variable=self.tag_filter_mode, 
                       value="ANY", command=self.update_display).grid(row=1, column=0, sticky=tk.W)
        ttk.Radiobutton(mode_frame, text="All tags", variable=self.tag_filter_mode, 
                       value="ALL", command=self.update_display).grid(row=2, column=0, sticky=tk.W)
        
        # Tag selection area
        ttk.Label(sidebar_frame, text="Select Categories:", font=('Arial', 11, 'bold')).grid(row=2, column=0, sticky=tk.W, pady=(10, 5))
        
        # Scrollable tag list
        tag_frame = ttk.Frame(sidebar_frame)
        tag_frame.grid(row=3, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        tag_frame.columnconfigure(0, weight=1)
        tag_frame.rowconfigure(0, weight=1)
        
        # Canvas and scrollbar for tags
        canvas = tk.Canvas(tag_frame, height=450, bg='white')
        scrollbar = ttk.Scrollbar(tag_frame, orient="vertical", command=canvas.yview)
        self.scrollable_tag_frame = ttk.Frame(canvas)
        
        self.scrollable_tag_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.scrollable_tag_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # Populate tag checkboxes
        self.tag_vars = {}
        self.populate_tag_filters()
        
        # Clear filters button
        ttk.Button(sidebar_frame, text="Clear All Filters", 
                  command=self.clear_all_filters).grid(row=4, column=0, sticky=(tk.W, tk.E), pady=(5, 0))
        
        # Statistics label
        self.stats_label = ttk.Label(sidebar_frame, text="", font=('Arial', 9))
        self.stats_label.grid(row=5, column=0, sticky=tk.W, pady=(10, 0))
    
    def populate_tag_filters(self):
        """Populate the tag filter checkboxes"""
        # Clear existing
        for widget in self.scrollable_tag_frame.winfo_children():
            widget.destroy()
        
        self.tag_vars = {}
        
        # Sort tags by frequency
        tag_counts = defaultdict(int)
        for article in self.articles:
            for tag in article.get('tags', []):
                tag_counts[tag] += 1
        
        sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)
        
        for i, (tag, count) in enumerate(sorted_tags):
            var = tk.BooleanVar()
            self.tag_vars[tag] = var
            
            cb = ttk.Checkbutton(
                self.scrollable_tag_frame,
                text=f"{tag} ({count})",
                variable=var,
                command=self.on_tag_filter_change
            )
            cb.grid(row=i, column=0, sticky=tk.W, pady=1)
    
    def setup_article_panel(self, parent):
        """Setup the right panel for article display"""
        article_frame = ttk.Frame(parent)
        article_frame.grid(row=0, column=1, rowspan=3, sticky=(tk.W, tk.E, tk.N, tk.S))
        article_frame.columnconfigure(0, weight=1)
        article_frame.rowconfigure(2, weight=1)
        
        # Search and controls
        controls_frame = ttk.Frame(article_frame)
        controls_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        controls_frame.columnconfigure(1, weight=1)
        
        # Sort control
        ttk.Checkbutton(
            controls_frame,
            text="Reverse sort (oldest first)",
            variable=self.reverse_var,
            command=self.update_display
        ).grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        
        # Search
        search_frame = ttk.Frame(controls_frame)
        search_frame.grid(row=0, column=1, sticky=(tk.W, tk.E))
        search_frame.columnconfigure(1, weight=1)
        
        ttk.Label(search_frame, text="Search:").grid(row=0, column=0, padx=(0, 5))
        
        self.search_var.trace_add('write', lambda *args: self.update_display())
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, font=('Arial', 12))
        search_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10))
        
        # Results info
        self.results_label = ttk.Label(article_frame, text="", font=('Arial', 10))
        self.results_label.grid(row=1, column=0, sticky=tk.W, pady=(0, 5))
        
        # Article list with tags
        self.setup_article_tree(article_frame)
    
    def setup_article_tree(self, parent):
        """Setup the treeview for articles"""
        # Tree with scrollbars
        tree_frame = ttk.Frame(parent)
        tree_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)
        
        # Define columns
        columns = ('index', 'date', 'title', 'tags')
        self.tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=20)
        
        # Configure columns
        self.tree.heading('index', text='#')
        self.tree.heading('date', text='Date')
        self.tree.heading('title', text='Title')
        self.tree.heading('tags', text='Tags')
        
        self.tree.column('index', width=40, minwidth=30)
        self.tree.column('date', width=85, minwidth=75)
        self.tree.column('title', width=550, minwidth=350)
        self.tree.column('tags', width=280, minwidth=220)
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        h_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        
        self.tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Grid placement
        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        v_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        h_scrollbar.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        # Bind double-click
        self.tree.bind('<Double-1>', self.on_article_double_click)
        
        # Configure alternating row colors
        self.tree.tag_configure('oddrow', background='#f0f8f0')
        self.tree.tag_configure('evenrow', background='white')
    
    def on_tag_filter_change(self):
        """Handle tag filter checkbox changes"""
        self.selected_tags = {tag for tag, var in self.tag_vars.items() if var.get()}
        self.update_display()
    
    def apply_filters(self):
        """Apply search and tag filters to articles"""
        filtered = self.articles.copy()
        
        # Apply search filter
        search_text = self.search_var.get().strip().lower()
        if search_text:
            search_conditions = self.parse_search_query(search_text)
            filtered = [article for article in filtered 
                       if self.evaluate_search_conditions(article.get('title', '').lower(), search_conditions)]
        
        # Apply tag filters
        if self.selected_tags:
            if self.tag_filter_mode.get() == "ANY":
                # Article must have at least one selected tag
                filtered = [article for article in filtered 
                           if any(tag in article.get('tags', []) for tag in self.selected_tags)]
            else:  # ALL
                # Article must have all selected tags
                filtered = [article for article in filtered 
                           if all(tag in article.get('tags', []) for tag in self.selected_tags)]
        
        return filtered
    
    def parse_search_query(self, query):
        """Parse search query with boolean operators"""
        # Simple implementation - can be enhanced
        query = query.strip()
        if not query:
            return []
        
        # Split by AND/OR (case insensitive)
        conditions = []
        current_term = ""
        
        tokens = re.split(r'\s+(and|or)\s+', query, flags=re.IGNORECASE)
        
        for i, token in enumerate(tokens):
            if i % 2 == 0:  # Term
                conditions.append(('term', token.strip()))
            else:  # Operator
                conditions.append(('op', token.lower()))
        
        return conditions
    
    def evaluate_search_conditions(self, text, conditions):
        """Evaluate search conditions against text"""
        if not conditions:
            return True
        
        result = None
        current_op = 'and'
        
        for condition_type, value in conditions:
            if condition_type == 'term':
                term_match = value.lower() in text.lower()
                
                if result is None:
                    result = term_match
                elif current_op == 'and':
                    result = result and term_match
                elif current_op == 'or':
                    result = result or term_match
            
            elif condition_type == 'op':
                current_op = value
        
        return result or False
    
    def update_display(self):
        """Update the article display with current filters"""
        # Apply filters
        self.filtered_articles = self.apply_filters()
        
        # Sort articles
        reverse_sort = self.reverse_var.get()
        self.filtered_articles.sort(key=lambda x: x.get('date_obj', datetime.now()), reverse=not reverse_sort)
        
        # Update tree
        self.tree.delete(*self.tree.get_children())
        
        for i, article in enumerate(self.filtered_articles, 1):
            tags_text = ', '.join(article.get('tags', []))
            row_tag = 'evenrow' if i % 2 == 0 else 'oddrow'
            
            self.tree.insert('', 'end', values=(
                i,
                article['email_date'],
                article['title'],
                tags_text
            ), tags=(row_tag,))
        
        # Update statistics
        total = len(self.articles)
        filtered = len(self.filtered_articles)
        selected_tags_text = ', '.join(sorted(self.selected_tags)) if self.selected_tags else "None"
        
        self.results_label.config(text=f"Showing {filtered} of {total} articles")
        
        if self.selected_tags:
            self.stats_label.config(text=f"Active filters: {selected_tags_text}")
        else:
            self.stats_label.config(text="No tag filters active")
    
    def on_article_double_click(self, event):
        """Handle double-click on article"""
        selection = self.tree.selection()
        if selection:
            item = self.tree.item(selection[0])
            index = int(item['values'][0]) - 1
            
            if 0 <= index < len(self.filtered_articles):
                article = self.filtered_articles[index]
                webbrowser.open(article['url'])
    
    def clear_all_filters(self):
        """Clear all filters"""
        # Clear tag selections
        for var in self.tag_vars.values():
            var.set(False)
        self.selected_tags.clear()
        
        # Clear search
        self.search_var.set('')
        
        # Update display
        self.update_display()
    
    def classify_articles(self):
        """Run classification on current articles"""
        try:
            from article_classifier import ArticleClassifier
            
            if not self.articles:
                messagebox.showwarning("No Articles", "No articles loaded to classify.")
                return
            
            classifier = ArticleClassifier()
            classified_articles, category_stats = classifier.classify_all_articles(self.articles)
            
            # Save classified version
            current_date = datetime.now().strftime("%Y_%m_%d")
            output_filename = f'medium_articles_classified_{current_date}.json'
            
            result = {
                'classification_date': datetime.now().isoformat(),
                'total_articles': len(classified_articles),
                'category_statistics': category_stats,
                'articles': classified_articles
            }
            
            with open(output_filename, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            
            messagebox.showinfo("Classification Complete", 
                              f"Articles classified and saved to:\n{output_filename}\n\nRestart the browser to load the classified version.")
            
        except ImportError:
            messagebox.showerror("Classification Error", 
                               "article_classifier.py not found.\nPlease ensure the classifier module is available.")
        except Exception as e:
            messagebox.showerror("Classification Error", f"Error during classification: {str(e)}")
    
    def show_tag_stats(self):
        """Show tag statistics window"""
        if not self.articles:
            messagebox.showinfo("No Data", "No articles loaded.")
            return
        
        # Calculate statistics
        tag_counts = defaultdict(int)
        multi_tag_articles = 0
        
        for article in self.articles:
            tags = article.get('tags', [])
            if len(tags) > 1:
                multi_tag_articles += 1
            for tag in tags:
                tag_counts[tag] += 1
        
        # Create statistics window
        stats_window = tk.Toplevel(self.root)
        stats_window.title("Tag Statistics")
        stats_window.geometry("500x400")
        
        # Scrolled text widget
        text_widget = scrolledtext.ScrolledText(stats_window, wrap=tk.WORD, font=('Courier', 11))
        text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Generate statistics text
        stats_text = f"📊 Tag Statistics\n"
        stats_text += f"{'='*50}\n\n"
        stats_text += f"Total articles: {len(self.articles)}\n"
        stats_text += f"Articles with multiple tags: {multi_tag_articles}\n"
        stats_text += f"Unique tags: {len(tag_counts)}\n\n"
        stats_text += f"Tag Distribution:\n"
        stats_text += f"{'-'*30}\n"
        
        sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)
        for tag, count in sorted_tags:
            percentage = (count / len(self.articles)) * 100
            stats_text += f"{tag:<20} {count:>4} ({percentage:5.1f}%)\n"
        
        text_widget.insert(tk.END, stats_text)
        text_widget.config(state=tk.DISABLED)
    
    def export_results(self):
        """Export filtered results"""
        if not self.filtered_articles:
            messagebox.showwarning("No Results", "No articles to export.")
            return
        
        filename = filedialog.asksaveasfilename(
            title="Export Filtered Results",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                export_data = {
                    'export_date': datetime.now().isoformat(),
                    'filters_applied': {
                        'search_query': self.search_var.get(),
                        'selected_tags': list(self.selected_tags),
                        'tag_filter_mode': self.tag_filter_mode.get()
                    },
                    'total_articles': len(self.filtered_articles),
                    'articles': self.filtered_articles
                }
                
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(export_data, f, indent=2, ensure_ascii=False)
                
                messagebox.showinfo("Export Complete", f"Exported {len(self.filtered_articles)} articles to:\n{filename}")
                
            except Exception as e:
                messagebox.showerror("Export Error", f"Error exporting results: {str(e)}")
    
    def open_file(self):
        """Open a different JSON file"""
        filename = filedialog.askopenfilename(
            title="Open Medium Articles File",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.articles = data.get('articles', [])
                
                # Process articles
                self.available_tags = set()
                for article in self.articles:
                    try:
                        article['date_obj'] = datetime.strptime(article['email_date'], '%Y-%m-%d')
                    except:
                        article['date_obj'] = datetime.now()
                    
                    tags = article.get('tags', [])
                    self.available_tags.update(tags)
                
                # Update GUI
                self.populate_tag_filters()
                self.clear_all_filters()
                
                # Update title
                basename = os.path.basename(filename)
                self.root.title(f"Enhanced Medium Browser - {basename}")
                
            except Exception as e:
                messagebox.showerror("Error", f"Error loading file: {str(e)}")

def main():
    """Main function"""
    root = tk.Tk()
    app = EnhancedMediumBrowser(root)
    root.mainloop()

if __name__ == "__main__":
    main()