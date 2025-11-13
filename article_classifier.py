#!/usr/bin/env python3
"""
Article Classification System
Automatically assigns multiple tags to Medium articles based on content analysis
"""

import json
import re
from collections import defaultdict
from datetime import datetime

class ArticleClassifier:
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
    
    def get_articles_by_category(self, articles, category):
        """Get all articles that belong to a specific category"""
        return [article for article in articles if category in article.get('tags', [])]
    
    def get_multi_category_articles(self, articles):
        """Get articles that belong to multiple categories"""
        return [article for article in articles if len(article.get('tags', [])) > 1]
    
    def print_classification_summary(self, category_stats, total_articles):
        """Print a summary of the classification results"""
        print(f"\n🏷️  Classification Summary ({total_articles} articles)")
        print("=" * 60)
        
        # Sort categories by count
        sorted_categories = sorted(category_stats.items(), key=lambda x: x[1], reverse=True)
        
        for category, count in sorted_categories:
            percentage = (count / total_articles) * 100
            print(f"{category:<20} {count:>4} articles ({percentage:5.1f}%)")
        
        print(f"\n📊 Total tagged articles: {sum(category_stats.values())} (some articles have multiple tags)")

def main():
    """Main function to classify existing articles"""
    
    # Load existing articles
    try:
        with open('medium_articles.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            articles = data.get('articles', [])
    except FileNotFoundError:
        print("❌ medium_articles.json not found. Please run the Gmail extractor first.")
        return
    
    print(f"🔍 Classifying {len(articles)} articles...")
    
    # Initialize classifier
    classifier = ArticleClassifier()
    
    # Classify all articles
    classified_articles, category_stats = classifier.classify_all_articles(articles)
    
    # Print summary
    classifier.print_classification_summary(category_stats, len(articles))
    
    # Save classified articles
    current_date = datetime.now().strftime("%Y_%m_%d")
    output_filename = f'medium_articles_classified_{current_date}.json'
    
    result = {
        'classification_date': datetime.now().isoformat(),
        'original_file': 'medium_articles.json',
        'total_articles': len(classified_articles),
        'category_statistics': category_stats,
        'articles': classified_articles
    }
    
    with open(output_filename, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Classified articles saved to: {output_filename}")
    
    # Show some examples
    print(f"\n📋 Sample classified articles:")
    multi_tag_articles = classifier.get_multi_category_articles(classified_articles)
    
    for i, article in enumerate(multi_tag_articles[:5]):
        print(f"\n{i+1}. {article['title'][:60]}...")
        print(f"   🏷️  Tags: {', '.join(article['tags'])}")
        if article.get('tag_scores'):
            scores = [f"{tag}({score})" for tag, score in article['tag_scores'].items()]
            print(f"   📊 Scores: {', '.join(scores)}")

if __name__ == "__main__":
    main()