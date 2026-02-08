#!/usr/bin/env python3
"""
Simple GUI editor for medium_articles_master.json
- Add title, url, email_date
- Filter by keywords
- Remove selected articles
"""

import json
import os
import re
import subprocess
import sys
import tkinter as tk
from datetime import datetime
from tkinter import messagebox, ttk

MASTER_FILE = "medium_articles_master.json"


def load_master():
    if not os.path.exists(MASTER_FILE):
        return {
            "created_date": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "total_unique_articles": 0,
            "update_history": [],
            "description": "Master historical database of all Medium articles",
            "articles": [],
        }
    with open(MASTER_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_master(data):
    data["last_updated"] = datetime.now().isoformat()
    data["total_unique_articles"] = len(data.get("articles", []))
    with open(MASTER_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def normalize_date(date_str):
    date_str = date_str.strip()
    if not date_str:
        return ""
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y_%m_%d"):
        try:
            return datetime.strptime(date_str, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return ""


class MasterEditor(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Medium Master Editor")
        self.geometry("1000x700")

        self.data = load_master()
        self.articles = self.data.get("articles", [])
        self.filtered_articles = []

        self._build_ui()
        self.apply_filter()

    def _build_ui(self):
        main = ttk.Frame(self, padding=12)
        main.pack(fill=tk.BOTH, expand=True)

        form = ttk.LabelFrame(main, text="Add Article", padding=10)
        form.pack(fill=tk.X)

        ttk.Label(form, text="Title").grid(row=0, column=0, sticky=tk.W)
        ttk.Label(form, text="URL").grid(row=1, column=0, sticky=tk.W)
        ttk.Label(form, text="Email Date (YYYY-MM-DD)").grid(
            row=2, column=0, sticky=tk.W
        )

        self.title_var = tk.StringVar()
        self.url_var = tk.StringVar()
        self.date_var = tk.StringVar()

        ttk.Entry(form, textvariable=self.title_var, width=80).grid(
            row=0, column=1, sticky=tk.W, padx=8, pady=2
        )
        ttk.Entry(form, textvariable=self.url_var, width=80).grid(
            row=1, column=1, sticky=tk.W, padx=8, pady=2
        )
        ttk.Entry(form, textvariable=self.date_var, width=20).grid(
            row=2, column=1, sticky=tk.W, padx=8, pady=2
        )

        add_btn = ttk.Button(form, text="Add Article", command=self.add_article)
        add_btn.grid(row=0, column=2, rowspan=3, padx=10, pady=2)

        filter_frame = ttk.LabelFrame(main, text="Filter / Remove", padding=10)
        filter_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Label(filter_frame, text="Keywords (space or comma separated)").grid(
            row=0, column=0, sticky=tk.W
        )
        self.filter_var = tk.StringVar()
        ttk.Entry(filter_frame, textvariable=self.filter_var, width=80).grid(
            row=0, column=1, sticky=tk.W, padx=8
        )
        ttk.Button(filter_frame, text="Apply Filter", command=self.apply_filter).grid(
            row=0, column=2, padx=6
        )
        ttk.Button(filter_frame, text="Clear Filter", command=self.clear_filter).grid(
            row=0, column=3, padx=6
        )

        list_frame = ttk.Frame(main)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

        self.listbox = tk.Listbox(list_frame, selectmode=tk.EXTENDED)
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(
            list_frame, orient=tk.VERTICAL, command=self.listbox.yview
        )
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.listbox.config(yscrollcommand=scrollbar.set)

        buttons = ttk.Frame(main)
        buttons.pack(fill=tk.X, pady=10)

        ttk.Button(buttons, text="Remove Selected", command=self.remove_selected).pack(
            side=tk.LEFT
        )
        ttk.Button(buttons, text="Save", command=self.save).pack(side=tk.LEFT, padx=8)
        ttk.Button(buttons, text="Reload", command=self.reload).pack(side=tk.LEFT)

        self.status_var = tk.StringVar(value="Loaded 0 articles")
        ttk.Label(main, textvariable=self.status_var).pack(anchor=tk.W)

    def apply_filter(self):
        query = self.filter_var.get().strip().lower()
        if not query:
            self.filtered_articles = list(self.articles)
        else:
            parts = [p for p in re.split(r"[\s,]+", query) if p]

            def matches(article):
                text = f"{article.get('title', '')} {article.get('url', '')}".lower()
                return all(p in text for p in parts)

            self.filtered_articles = [a for a in self.articles if matches(a)]

        self.refresh_listbox()

    def clear_filter(self):
        self.filter_var.set("")
        self.apply_filter()

    def refresh_listbox(self):
        self.listbox.delete(0, tk.END)
        for article in self.filtered_articles:
            title = article.get("title", "")
            url = article.get("url", "")
            date = article.get("email_date", "")
            self.listbox.insert(tk.END, f"[{date}] {title} | {url}")
        self.status_var.set(
            f"Showing {len(self.filtered_articles)} of {len(self.articles)} articles"
        )

    def add_article(self):
        title = self.title_var.get().strip()
        url = self.url_var.get().strip()
        date = normalize_date(self.date_var.get())

        if not title or not url:
            messagebox.showerror("Missing Fields", "Title and URL are required.")
            return
        if not date:
            messagebox.showerror(
                "Invalid Date", "Email date must be in YYYY-MM-DD format."
            )
            return

        if any(a.get("url") == url for a in self.articles):
            messagebox.showwarning(
                "Duplicate", "An article with this URL already exists."
            )
            return

        self.articles.append({"title": title, "url": url, "email_date": date})
        self.title_var.set("")
        self.url_var.set("")
        self.date_var.set("")
        self.apply_filter()

    def remove_selected(self):
        selections = list(self.listbox.curselection())
        if not selections:
            return

        to_remove = [self.filtered_articles[i] for i in selections]
        if not messagebox.askyesno(
            "Confirm", f"Remove {len(to_remove)} selected article(s)?"
        ):
            return

        remove_urls = {a.get("url") for a in to_remove}
        self.articles = [a for a in self.articles if a.get("url") not in remove_urls]
        self.data["articles"] = self.articles
        self.apply_filter()

    def save(self):
        self.data["articles"] = self.articles
        save_master(self.data)
        messagebox.showinfo(
            "Saved", f"Saved {len(self.articles)} articles to {MASTER_FILE}."
        )

        if messagebox.askyesno(
            "Regenerate HTML",
            "Regenerate medium_article_browser.html from master database now?",
        ):
            script_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), "Read_Medium_From_Gmail.py"
            )
            try:
                subprocess.run(
                    [sys.executable, script_path, "--regen-html"],
                    check=True,
                )
            except subprocess.CalledProcessError:
                messagebox.showerror(
                    "Error", "Failed to regenerate HTML. Check console for details."
                )

    def reload(self):
        self.data = load_master()
        self.articles = self.data.get("articles", [])
        self.apply_filter()


if __name__ == "__main__":
    app = MasterEditor()
    app.mainloop()
