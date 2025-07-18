#!/usr/bin/env python3
"""
Demo script to enhance existing repository data with AI-generated tags and quality assessments
"""

import json
import random

def generate_demo_tags(repo):
    """Generate demo AI tags based on repository information"""
    language = repo.get('language', '').lower() if repo.get('language') else ''
    name = repo.get('name', '').lower()
    description = repo.get('description', '') or ''
    
    # Common NHS/healthcare tags
    healthcare_tags = ['healthcare', 'nhs', 'patient-care', 'clinical', 'medical', 'digital-health']
    
    # Technology tags based on language
    tech_tags = {
        'python': ['python', 'data-science', 'automation', 'api'],
        'javascript': ['javascript', 'web-app', 'frontend', 'interactive'],
        'java': ['java', 'enterprise', 'backend', 'scalable'],
        'c#': ['csharp', 'dotnet', 'enterprise', 'windows'],
        'typescript': ['typescript', 'web-app', 'frontend', 'modern'],
        'r': ['r', 'statistics', 'data-analysis', 'research'],
        'sql': ['sql', 'database', 'analytics', 'reporting']
    }
    
    # Purpose tags based on name patterns
    purpose_tags = []
    if any(word in name for word in ['api', 'service', 'backend']):
        purpose_tags.extend(['api', 'service', 'integration'])
    if any(word in name for word in ['web', 'app', 'frontend', 'ui']):
        purpose_tags.extend(['web-application', 'user-interface'])
    if any(word in name for word in ['data', 'analytics', 'report']):
        purpose_tags.extend(['data-analytics', 'reporting', 'insights'])
    if any(word in name for word in ['mobile', 'ios', 'android']):
        purpose_tags.extend(['mobile', 'cross-platform'])
    if any(word in name for word in ['test', 'quality', 'automation']):
        purpose_tags.extend(['testing', 'quality-assurance', 'automation'])
    
    # Combine tags
    tags = []
    tags.extend(random.sample(healthcare_tags, min(2, len(healthcare_tags))))
    
    if language and language in tech_tags:
        tags.extend(tech_tags[language])
    
    tags.extend(purpose_tags[:3])
    
    # Add some random quality tags
    quality_tags = ['innovative', 'scalable', 'secure', 'user-friendly', 'efficient', 'robust']
    tags.extend(random.sample(quality_tags, min(2, len(quality_tags))))
    
    return list(set(tags))[:6]  # Limit to 6 unique tags

def calculate_quality_score(repo):
    """Calculate a demo quality score based on repository metrics"""
    score = 50  # Base score
    
    # Adjust based on stars
    stars = repo.get('stargazers_count', 0)
    score += min(stars * 5, 20)
    
    # Adjust based on recent activity
    if repo.get('pushed_at'):
        score += 10
    
    # Adjust based on description
    if repo.get('description') and len(repo.get('description', '')) > 20:
        score += 15
    
    # Adjust based on language
    if repo.get('language'):
        score += 10
    
    # Adjust based on size (activity indicator)
    size = repo.get('size', 0)
    if size > 100:
        score += 10
    elif size > 1000:
        score += 15
    
    # Add some randomness for demo
    score += random.randint(-5, 10)
    
    return min(max(score, 30), 95)  # Clamp between 30-95

def assess_featured_status(repo, quality_score):
    """Determine if repository should be featured"""
    # Feature repositories with high quality scores and recent activity
    if quality_score >= 75:
        return True
    elif quality_score >= 65 and repo.get('stargazers_count', 0) > 0:
        return True
    elif repo.get('language') and quality_score >= 60:
        return True
    else:
        return False

def enhance_repositories():
    """Enhance repository data with AI tags and assessments"""
    print("Loading repository data...")
    
    with open('data/repositories.json', 'r') as f:
        repositories = json.load(f)
    
    print(f"Enhancing {len(repositories)} repositories...")
    
    featured_count = 0
    for repo in repositories:
        # Generate AI tags
        generated_tags = generate_demo_tags(repo)
        repo['generated_tags'] = generated_tags
        
        # Combine with existing topics
        all_tags = list(set(repo.get('topics', []) + generated_tags))
        repo['all_tags'] = all_tags
        
        # Calculate quality score
        quality_score = calculate_quality_score(repo)
        repo['quality_score'] = quality_score
        
        # Assess featured status
        featured = assess_featured_status(repo, quality_score)
        repo['featured'] = featured
        
        if featured:
            featured_count += 1
        
        print(f"Enhanced {repo['name']}: {len(generated_tags)} tags, quality: {quality_score}, featured: {featured}")
    
    print(f"\nEnhancement complete!")
    print(f"- Total repositories: {len(repositories)}")
    print(f"- Featured repositories: {featured_count}")
    print(f"- Coverage: {featured_count/len(repositories)*100:.1f}%")
    
    # Save enhanced data
    print("\nSaving enhanced data...")
    with open('data/repositories.json', 'w') as f:
        json.dump(repositories, f, indent=2)
    
    print("✅ Repository data enhanced and saved!")
    
    # Show some examples
    print("\nFeatured repositories preview:")
    featured_repos = [r for r in repositories if r.get('featured')][:5]
    for repo in featured_repos:
        print(f"- {repo['name']}: {repo['quality_score']} pts, tags: {repo['generated_tags'][:3]}")

if __name__ == "__main__":
    enhance_repositories()
