#!/usr/bin/env python3
"""
Merge Medium Articles JSON Files

This script reads all medium_articles_YYYY_MM_DD.json and medium_articles_classified_YYYY_MM_DD.json 
files in the current directory and merges them into consolidated files.

Output files:
- medium_articles.json: Merged articles from all dated files
- medium_articles_classified.json: Merged classified articles from all dated files
"""

import json
import os
import re
from datetime import datetime
from typing import Dict, List, Set
from collections import defaultdict


def find_dated_files(pattern: str) -> List[str]:
    """Find all files matching the given pattern with YYYY_MM_DD date format."""
    files = []
    date_pattern = re.compile(pattern.replace('YYYY_MM_DD', r'(\d{4}_\d{2}_\d{2})'))
    
    for filename in os.listdir('.'):
        if date_pattern.match(filename):
            files.append(filename)
    
    # Sort by date (newest first)
    files.sort(reverse=True)
    return files


def load_json_file(filepath: str) -> Dict:
    """Load JSON file and return the data."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {filepath}: {e}")
        return {}


def merge_regular_articles():
    """Merge all medium_articles_YYYY_MM_DD.json files."""
    print("🔍 Finding regular Medium articles files...")
    files = find_dated_files('medium_articles_YYYY_MM_DD.json')
    
    if not files:
        print("❌ No dated medium_articles files found.")
        return
    
    print(f"📁 Found {len(files)} files: {files}")
    
    # Use the newest file as the base
    newest_file = files[0]
    print(f"📊 Using {newest_file} as base file...")
    
    base_data = load_json_file(newest_file)
    if not base_data:
        return
    
    # Collect unique articles using URL as key
    unique_articles = {}
    all_articles_count = 0
    
    # Process all files (including the base)
    for filename in files:
        print(f"📖 Processing {filename}...")
        data = load_json_file(filename)
        
        if not data or 'articles' not in data:
            print(f"⚠️  Skipping {filename} - invalid format")
            continue
        
        articles = data.get('articles', [])
        file_article_count = len(articles)
        all_articles_count += file_article_count
        
        # Add articles to unique collection (URL is the key)
        for article in articles:
            url = article.get('url', '')
            if url and url not in unique_articles:
                unique_articles[url] = article
        
        print(f"   📈 {file_article_count} articles in this file")
    
    # Create merged data
    merged_data = {
        'extraction_date': datetime.now().isoformat(),
        'merged_from_files': files,
        'total_source_files': len(files),
        'total_articles_across_files': all_articles_count,
        'total_unique_articles': len(unique_articles),
        'description': f'Merged Medium articles from {len(files)} dated files',
        'articles': list(unique_articles.values())
    }
    
    # Sort articles by email_date (newest first)
    merged_data['articles'].sort(
        key=lambda x: x.get('email_date', ''), 
        reverse=True
    )
    
    # Save merged file
    output_file = 'medium_articles.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(merged_data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Merged {len(unique_articles)} unique articles into {output_file}")
    print(f"   📊 Total articles across all files: {all_articles_count}")
    print(f"   🔗 Unique articles (deduplicated): {len(unique_articles)}")


def merge_classified_articles():
    """Merge all medium_articles_classified_YYYY_MM_DD.json files."""
    print("\n🔍 Finding classified Medium articles files...")
    files = find_dated_files('medium_articles_classified_YYYY_MM_DD.json')
    
    if not files:
        print("❌ No dated classified medium_articles files found.")
        return
    
    print(f"📁 Found {len(files)} files: {files}")
    
    # Use the newest file as the base
    newest_file = files[0]
    print(f"📊 Using {newest_file} as base file...")
    
    base_data = load_json_file(newest_file)
    if not base_data:
        return
    
    # Collect unique articles using URL as key
    unique_articles = {}
    all_categories = defaultdict(int)
    all_articles_count = 0
    
    # Process all files
    for filename in files:
        print(f"📖 Processing {filename}...")
        data = load_json_file(filename)
        
        if not data or 'articles' not in data:
            print(f"⚠️  Skipping {filename} - invalid format")
            continue
        
        articles = data.get('articles', [])
        file_article_count = len(articles)
        all_articles_count += file_article_count
        
        # Add articles to unique collection and count categories
        for article in articles:
            url = article.get('url', '')
            if url and url not in unique_articles:
                unique_articles[url] = article
                # Count categories from tags
                tags = article.get('tags', [])
                for tag in tags:
                    all_categories[tag] += 1
        
        print(f"   📈 {file_article_count} classified articles in this file")
    
    # Create merged data
    merged_data = {
        'classification_date': datetime.now().isoformat(),
        'merged_from_files': files,
        'total_source_files': len(files),
        'total_articles_across_files': all_articles_count,
        'total_unique_articles': len(unique_articles),
        'description': f'Merged classified Medium articles from {len(files)} dated files',
        'category_statistics': dict(sorted(all_categories.items(), key=lambda x: x[1], reverse=True)),
        'articles': list(unique_articles.values())
    }
    
    # Sort articles by email_date (newest first)
    merged_data['articles'].sort(
        key=lambda x: x.get('email_date', ''), 
        reverse=True
    )
    
    # Save merged file
    output_file = 'medium_articles_classified.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(merged_data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Merged {len(unique_articles)} unique classified articles into {output_file}")
    print(f"   📊 Total articles across all files: {all_articles_count}")
    print(f"   🔗 Unique articles (deduplicated): {len(unique_articles)}")
    print(f"   📂 Categories found: {len(all_categories)}")
    
    # Show top categories
    print("   🏷️  Top categories:")
    for category, count in sorted(all_categories.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"      • {category}: {count} articles")





def main():
    """Main function to merge all Medium articles files."""
    print("🚀 Starting Medium Articles Merge Process")
    print("=" * 50)
    
    # Change to the script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    print(f"📂 Working directory: {script_dir}")
    
    # Check for existing files
    existing_files = []
    for filename in ['medium_articles.json', 'medium_articles_classified.json']:
        if os.path.exists(filename):
            existing_files.append(filename)
    
    if existing_files:
        print(f"📄 Will overwrite existing files: {', '.join(existing_files)}")
    
    # Merge regular articles
    merge_regular_articles()
    
    # Merge classified articles
    merge_classified_articles()
    
    print("\n" + "=" * 50)
    print("🎉 Merge process completed!")
    
    # Show final summary
    if os.path.exists('medium_articles.json'):
        with open('medium_articles.json', 'r') as f:
            data = json.load(f)
            print(f"📄 medium_articles.json: {data.get('total_unique_articles', 0)} unique articles")
    
    if os.path.exists('medium_articles_classified.json'):
        with open('medium_articles_classified.json', 'r') as f:
            data = json.load(f)
            print(f"📄 medium_articles_classified.json: {data.get('total_unique_articles', 0)} unique classified articles")


if __name__ == "__main__":
    main()