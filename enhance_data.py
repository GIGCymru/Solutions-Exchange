#!/usr/bin/env python3
"""
Quick script to enhance the existing repository data with sample AI tags and featured assessments
for demonstration purposes.
"""

import json
import random
from datetime import datetime, timedelta

def generate_sample_tags(repo_name, description, language):
    """Generate sample AI tags based on repository characteristics."""
    tags = []
    
    # Healthcare keywords
    healthcare_terms = ['clinical', 'patient', 'medical', 'healthcare', 'hospital', 'emergency', 'pharmacy', 'dental']
    technical_terms = ['api', 'integration', 'data', 'analytics', 'automation', 'dashboard', 'monitoring']
    department_terms = ['emergency department', 'radiology', 'pathology', 'dental services', 'referrals']
    
    name_lower = repo_name.lower()
    desc_lower = (description or '').lower()
    
    # Add healthcare tags
    for term in healthcare_terms:
        if term in name_lower or term in desc_lower:
            tags.append(term.title())
    
    # Add technical tags
    for term in technical_terms:
        if term in name_lower or term in desc_lower:
            tags.append(term.title())
    
    # Add department tags
    for term in department_terms:
        if any(word in name_lower or word in desc_lower for word in term.split()):
            tags.append(term.title())
    
    # Add language-based tags
    if language:
        tags.append(f"{language} Development")
    
    # Remove duplicates and limit to 5 tags
    tags = list(set(tags))[:5]
    
    # If no tags generated, add some generic ones
    if not tags:
        if 'integration' in name_lower or 'hub' in name_lower:
            tags = ['Integration', 'Healthcare Systems']
        elif 'ui' in name_lower or 'mock' in name_lower:
            tags = ['User Interface', 'Testing']
        elif language:
            tags = [f"{language} Application"]
        else:
            tags = ['Healthcare Solution']
    
    return tags

def assess_quality(repo):
    """Assess repository quality for featured eligibility."""
    score = 0
    criteria_met = []
    missing_criteria = []
    
    # Required fields (20 points each)
    if repo.get('name'):
        score += 20
        criteria_met.append('name')
    else:
        missing_criteria.append('name')
    
    if repo.get('owner', {}).get('login'):
        score += 20
        criteria_met.append('owner')
    else:
        missing_criteria.append('owner')
    
    if repo.get('language'):
        score += 20
        criteria_met.append('language')
    else:
        missing_criteria.append('language')
    
    # Description (15 points)
    if repo.get('description') and len(repo['description'].strip()) > 10:
        score += 15
        criteria_met.append('description')
    else:
        missing_criteria.append('description')
    
    # Tags (15 points)
    total_tags = len(repo.get('topics', [])) + len(repo.get('generated_tags', []))
    if total_tags >= 2:
        score += 15
        criteria_met.append('tags')
    else:
        missing_criteria.append('tags')
    
    # Recent activity (15 points)
    if repo.get('updated_at'):
        try:
            updated_date = datetime.fromisoformat(repo['updated_at'].replace('Z', '+00:00'))
            six_months_ago = datetime.now().replace(tzinfo=updated_date.tzinfo) - timedelta(days=180)
            if updated_date > six_months_ago:
                score += 15
                criteria_met.append('recent_activity')
            else:
                missing_criteria.append('recent_activity')
        except:
            missing_criteria.append('recent_activity')
    else:
        missing_criteria.append('recent_activity')
    
    # License (5 points bonus)
    if repo.get('license'):
        score += 5
        criteria_met.append('license')
    
    # Determine eligibility
    required_criteria = ['name', 'owner', 'language']
    has_required = all(criterion in criteria_met for criterion in required_criteria)
    eligible = score >= 80 and has_required
    
    return {
        'eligible': eligible,
        'score': score,
        'criteria_met': criteria_met,
        'missing_criteria': missing_criteria
    }

def enhance_repositories():
    """Enhance the existing repository data."""
    print("🤖 Enhancing repository data with AI tags and quality assessments...")
    
    # Load existing data
    with open('/workspaces/Solutions-Exchange/data/repositories.json', 'r') as f:
        repositories = json.load(f)
    
    print(f"📊 Processing {len(repositories)} repositories...")
    
    enhanced_count = 0
    featured_eligible = 0
    
    for repo in repositories:
        # Generate AI tags if none exist
        if not repo.get('generated_tags'):
            generated_tags = generate_sample_tags(
                repo['name'], 
                repo.get('description'), 
                repo.get('language')
            )
            repo['generated_tags'] = generated_tags
            
            # Update all_tags
            all_tags = list(set(repo.get('topics', []) + generated_tags))
            repo['all_tags'] = all_tags
            
            enhanced_count += 1
        
        # Assess quality for featuring
        if not repo.get('featured'):
            assessment = assess_quality(repo)
            repo['featured'] = assessment
            
            if assessment['eligible']:
                featured_eligible += 1
    
    # Save enhanced data
    with open('/workspaces/Solutions-Exchange/data/repositories.json', 'w') as f:
        json.dump(repositories, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Enhanced {enhanced_count} repositories with AI tags")
    print(f"⭐ {featured_eligible} repositories qualify for featuring")
    print(f"📈 Quality assessment completed for all {len(repositories)} repositories")
    
    # Show some stats
    languages = {}
    organizations = {}
    
    for repo in repositories:
        # Count languages
        lang = repo.get('language') or 'Unknown'
        languages[lang] = languages.get(lang, 0) + 1
        
        # Count organizations
        org = repo.get('owner', {}).get('login', 'Unknown')
        organizations[org] = organizations.get(org, 0) + 1
    
    print(f"\n📊 Repository Statistics:")
    print(f"  • Languages: {len(languages)} different languages")
    print(f"  • Organizations: {len(organizations)} organizations")
    print(f"  • Featured eligible: {featured_eligible}/{len(repositories)} ({(featured_eligible/len(repositories)*100):.1f}%)")
    
    # Show top featured candidates
    featured_repos = [r for r in repositories if r.get('featured', {}).get('eligible')]
    if featured_repos:
        top_featured = sorted(featured_repos, key=lambda x: x['featured']['score'], reverse=True)[:5]
        print(f"\n⭐ Top Featured Candidates:")
        for repo in top_featured:
            print(f"  • {repo['name']} ({repo['featured']['score']}/100) - {repo['owner']['login']}")

if __name__ == "__main__":
    enhance_repositories()
