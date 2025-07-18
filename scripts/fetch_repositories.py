<<<<<<< HEAD
=======
import requests
import pandas as pd
import json
import os
import re
from datetime import datetime, timedelta
from collections import Counter
import nltk
from textblob import TextBlob

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

try:
    nltk.data.find('taggers/averaged_perceptron_tagger')
except LookupError:
    nltk.download('averaged_perceptron_tagger')

from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize


from dotenv import load_dotenv

load_dotenv()  # This loads variables from .env into environment
# Replace this with your actual GitHub personal access token
GITHUB_TOKEN = os.getenv('GH_SECRET')

# Set up the headers with the token
headers = {
    'Authorization': f'token {GITHUB_TOKEN}',
    'Accept': 'application/vnd.github.v3+json'
}

# List of organizations for NHS Wales Solutions Exchange
organizations = [
    "Analytics-Learning-Programme", 
    "Aneurin-Bevan-University-Health-Board",
    "Cardiff-Vale-University-Health-Board", 
    "Cwm-Taf-Morgannwg-UHB",
    "DHCW-Digital-Health-and-Care-Wales", 
    "GIGCymru",
    "HDUHB-Hywel-Dda-University-Health-Board", 
    "National-Data-Resource-NDR",
    "NHS-Executive", 
    "Powys-Teaching-Health-Board",
    "Swansea-Bay-University-Health-Board"
]

def get_repositories_for_org(organization):
    """Fetch all repositories for a given organization."""
    repos = []
    page = 1
    
    print(f"Fetching repositories for organization: {organization}")
    
    while True:
        # Construct the API URL for the organization
        api_url = f'https://api.github.com/orgs/{organization}/repos'
        
        # Fetch the repositories for the current page
        response = requests.get(api_url, headers=headers, params={
            'per_page': 100, 
            'page': page,
            'type': 'all',  # Include all types of repositories
            'sort': 'updated',
            'direction': 'desc'
        })
        
        if response.status_code == 404:
            print(f"Organization {organization} not found or no access")
            break
        elif response.status_code != 200:
            print(f"Error fetching repositories for {organization}: {response.status_code}")
            print(f"Response: {response.text}")
            break
        
        # Parse the JSON response
        data = response.json()
        
        if not data:
            break  # No more data to fetch

        # Filter repositories by visibility: only "public" or "internal"
        # Also exclude archived repositories unless specifically wanted
        filtered_repos = [
            repo for repo in data 
            if repo['visibility'] in ['public', 'internal'] and not repo.get('archived', False)
        ]
        
        # Add the filtered repositories to the list
        repos.extend(filtered_repos)
        print(f"  Page {page}: Found {len(filtered_repos)} repositories")
        
        # Move to the next page
        page += 1
        
        # GitHub API pagination limit check
        if len(data) < 100:
            break
    
    print(f"  Total repositories for {organization}: {len(repos)}")
    return repos

def generate_tags_from_description(description, existing_topics=None):
    """Generate tags from repository description using NLP."""
    if not description or description.strip() == "":
        return []
    
    # Healthcare and NHS-specific keywords to prioritize
    healthcare_keywords = {
        'clinical', 'patient', 'hospital', 'medical', 'health', 'healthcare', 'nhs', 'emergency',
        'diagnosis', 'treatment', 'nursing', 'doctor', 'physician', 'therapy', 'medication',
        'surgery', 'radiology', 'pathology', 'laboratory', 'cardiology', 'oncology',
        'mental health', 'primary care', 'secondary care', 'tertiary care', 'outpatient',
        'inpatient', 'discharge', 'admission', 'referral', 'prescription', 'pharmacy',
        'epidemiology', 'public health', 'preventive', 'screening', 'vaccination',
        'electronic health record', 'ehr', 'clinical decision support', 'telemedicine',
        'digital health', 'health informatics', 'medical imaging', 'genomics'
    }
    
    # Technical keywords
    technical_keywords = {
        'analytics', 'machine learning', 'ai', 'artificial intelligence', 'data science',
        'visualization', 'dashboard', 'reporting', 'forecast', 'prediction', 'model',
        'algorithm', 'neural network', 'deep learning', 'nlp', 'natural language processing',
        'api', 'database', 'sql', 'nosql', 'etl', 'pipeline', 'automation', 'deployment',
        'docker', 'kubernetes', 'cloud', 'aws', 'azure', 'monitoring', 'logging',
        'security', 'authentication', 'encryption', 'backup', 'disaster recovery'
    }
    
    # Department/specialty keywords  
    department_keywords = {
        'emergency department', 'ed', 'accident and emergency', 'a&e', 'intensive care',
        'icu', 'operating theatre', 'maternity', 'pediatrics', 'geriatrics', 'psychiatry',
        'radiology', 'pathology', 'pharmacy', 'physiotherapy', 'occupational therapy',
        'social services', 'district nursing', 'community care', 'mental health services',
        'ambulance service', 'blood transfusion', 'laboratory services', 'imaging',
        'surgical services', 'medical services', 'nursing services', 'allied health'
    }
    
    # Combine all keyword sets
    all_keywords = healthcare_keywords | technical_keywords | department_keywords
    
    # Clean and normalize description
    description_lower = description.lower()
    
    # Extract existing topics to avoid duplication
    existing_topics = existing_topics or []
    existing_lower = [topic.lower() for topic in existing_topics]
    
    # Find matching keywords
    found_tags = []
    
    # Direct keyword matching
    for keyword in all_keywords:
        if keyword in description_lower and keyword not in existing_lower:
            # Capitalize properly
            tag = ' '.join(word.capitalize() for word in keyword.split())
            if tag not in found_tags and len(tag) > 2:
                found_tags.append(tag)
    
    # Use TextBlob for noun phrase extraction
    try:
        blob = TextBlob(description)
        noun_phrases = blob.noun_phrases
        
        for phrase in noun_phrases:
            # Clean and filter noun phrases
            phrase_clean = phrase.strip().lower()
            if (len(phrase_clean.split()) <= 3 and  # Max 3 words
                len(phrase_clean) > 3 and  # Min 4 characters
                phrase_clean not in existing_lower and
                not any(stop_word in phrase_clean for stop_word in ['the', 'this', 'that', 'and', 'or']) and
                phrase_clean not in [tag.lower() for tag in found_tags]):
                
                # Capitalize properly
                tag = ' '.join(word.capitalize() for word in phrase_clean.split())
                found_tags.append(tag)
                
                if len(found_tags) >= 5:  # Limit to 5 generated tags
                    break
                    
    except Exception as e:
        print(f"Warning: Error in NLP processing: {e}")
    
    # Return up to 5 most relevant tags
    return found_tags[:5]

def check_readme_exists(owner_login, repo_name, headers):
    """Check if repository has a README file."""
    readme_urls = [
        f'https://api.github.com/repos/{owner_login}/{repo_name}/readme',
        f'https://api.github.com/repos/{owner_login}/{repo_name}/contents/README.md',
        f'https://api.github.com/repos/{owner_login}/{repo_name}/contents/readme.md',
        f'https://api.github.com/repos/{owner_login}/{repo_name}/contents/README.txt'
    ]
    
    for url in readme_urls:
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                return True
        except:
            continue
    return False

def calculate_featured_score(repo, readme_exists=False):
    """Calculate a score for featuring eligibility based on the checklist."""
    score = 0
    criteria_met = {}
    
    # Required fields (each worth 20 points)
    if repo.get('name'):
        score += 20
        criteria_met['name'] = True
    
    if repo.get('owner', {}).get('login'):
        score += 20  
        criteria_met['owner'] = True
    
    # Language (20 points)
    if repo.get('language'):
        score += 20
        criteria_met['language'] = True
    
    # Description (15 points)
    if repo.get('description') and len(repo['description'].strip()) > 10:
        score += 15
        criteria_met['description'] = True
    
    # Tags - at least 2 (combining topics and generated tags, 15 points)
    total_tags = len(repo.get('topics', [])) + len(repo.get('generated_tags', []))
    if total_tags >= 2:
        score += 15
        criteria_met['tags'] = True
    
    # README file (10 points)
    if readme_exists:
        score += 10
        criteria_met['readme'] = True
    
    # Last updated within 6 months (15 points)
    if repo.get('updated_at'):
        try:
            updated_date = datetime.fromisoformat(repo['updated_at'].replace('Z', '+00:00'))
            six_months_ago = datetime.now().replace(tzinfo=updated_date.tzinfo) - timedelta(days=180)
            if updated_date > six_months_ago:
                score += 15
                criteria_met['recent_activity'] = True
        except:
            pass
    
    # License (5 points bonus)
    if repo.get('license') and repo['license'].get('name'):
        score += 5
        criteria_met['license'] = True
    
    return score, criteria_met

def determine_featured_eligibility(repo, readme_exists=False):
    """Determine if repository qualifies for featured section."""
    score, criteria_met = calculate_featured_score(repo, readme_exists)
    
    # Must score at least 80/100 to be eligible for featuring
    # Must have all required fields (name, owner, language)
    required_criteria = ['name', 'owner', 'language']
    has_required = all(criteria_met.get(criterion, False) for criterion in required_criteria)
    
    eligible = score >= 80 and has_required
    
def clean_repository_data(repo, headers):
    """Clean and standardize repository data with enhanced features."""
    
    # Generate tags from description
    generated_tags = generate_tags_from_description(
        repo.get('description', ''), 
        repo.get('topics', [])
    )
    
    # Check for README
    readme_exists = check_readme_exists(repo['owner']['login'], repo['name'], headers)
    
    # Create enhanced repository data
    cleaned_repo = {
        'id': repo['id'],
        'name': repo['name'],
        'full_name': repo['full_name'],
        'description': repo.get('description', ''),
        'html_url': repo['html_url'],
        'language': repo.get('language'),
        'topics': repo.get('topics', []),
        'generated_tags': generated_tags,  # New: AI-generated tags
        'all_tags': repo.get('topics', []) + generated_tags,  # Combined tags
        'visibility': repo['visibility'],
        'created_at': repo['created_at'],
        'updated_at': repo['updated_at'],
        'pushed_at': repo.get('pushed_at'),
        'size': repo['size'],
        'stargazers_count': repo['stargazers_count'],
        'watchers_count': repo['watchers_count'],
        'forks_count': repo['forks_count'],
        'open_issues_count': repo['open_issues_count'],
        'archived': repo.get('archived', False),
        'disabled': repo.get('disabled', False),
        'private': repo['private'],
        'license': repo.get('license'),
        'has_readme': readme_exists,  # New: README check
        'owner': {
            'login': repo['owner']['login'],
            'id': repo['owner']['id'],
            'html_url': repo['owner']['html_url'],
            'type': repo['owner']['type']
        }
    }
    
    # Add feature flag assessment
    feature_assessment = determine_featured_eligibility(cleaned_repo, readme_exists)
    cleaned_repo['featured'] = feature_assessment
    
    return cleaned_repo
    """Clean and standardize repository data."""
    return {
        'id': repo['id'],
        'name': repo['name'],
        'full_name': repo['full_name'],
        'description': repo.get('description', ''),
        'html_url': repo['html_url'],
        'language': repo.get('language'),
        'topics': repo.get('topics', []),
        'visibility': repo['visibility'],
        'created_at': repo['created_at'],
        'updated_at': repo['updated_at'],
        'pushed_at': repo.get('pushed_at'),
        'size': repo['size'],
        'stargazers_count': repo['stargazers_count'],
        'watchers_count': repo['watchers_count'],
        'forks_count': repo['forks_count'],
        'open_issues_count': repo['open_issues_count'],
        'archived': repo.get('archived', False),
        'disabled': repo.get('disabled', False),
        'private': repo['private'],
        'owner': {
            'login': repo['owner']['login'],
            'id': repo['owner']['id'],
            'html_url': repo['owner']['html_url'],
            'type': repo['owner']['type']
        }
    }

def main():
    """Main function to fetch all repositories and save to JSON."""
    all_repositories = []

    # Check if GitHub token is available
    if not GITHUB_TOKEN:
        print("ERROR: GitHub token not found. Please set the GH_SECRET environment variable.")
        return

    print("🔍 Initializing enhanced repository fetcher with AI tag generation...")
    print("📋 Feature criteria checklist:")
    print("   ✓ Repository name")
    print("   ✓ Owner/Organization") 
    print("   ✓ Language specified")
    print("   ✓ Description (>10 chars)")
    print("   ✓ At least 2 tags (user + AI generated)")
    print("   ✓ README file exists")
    print("   ✓ Updated within 6 months")
    print("   ✓ License specified (bonus)")
    print()

    # Loop over each organization and get their repositories
    for org in organizations:
        try:
            repos = get_repositories_for_org(org)
            print(f"🤖 Generating AI tags for {len(repos)} repositories from {org}...")
            
            # Clean the repository data with enhanced features
            cleaned_repos = [clean_repository_data(repo, headers) for repo in repos]
            all_repositories.extend(cleaned_repos)
            
            # Show feature eligibility stats for this org
            eligible_count = len([r for r in cleaned_repos if r['featured']['eligible']])
            print(f"   ⭐ {eligible_count}/{len(cleaned_repos)} repositories qualify for featuring")
            
        except Exception as e:
            print(f"❌ Error processing organization {org}: {str(e)}")
            continue

    # Sort repositories by update date (most recent first)
    all_repositories.sort(key=lambda x: x['updated_at'], reverse=True)

    # Create output files
    try:
        # Save as JSON for the web application
        with open('data/repositories.json', 'w', encoding='utf-8') as f:
            json.dump(all_repositories, f, indent=2, ensure_ascii=False)
        
        # Save as CSV for analysis (flattened for CSV compatibility)
        csv_data = []
        for repo in all_repositories:
            csv_row = repo.copy()
            csv_row['topics'] = '; '.join(repo['topics'])
            csv_row['generated_tags'] = '; '.join(repo['generated_tags']) 
            csv_row['all_tags'] = '; '.join(repo['all_tags'])
            csv_row['featured_eligible'] = repo['featured']['eligible']
            csv_row['featured_score'] = repo['featured']['score']
            csv_row['missing_criteria'] = '; '.join(repo['featured']['missing_criteria'])
            # Remove nested objects for CSV
            del csv_row['owner']
            del csv_row['featured']
            del csv_row['license']
            csv_data.append(csv_row)
            
        df = pd.DataFrame(csv_data)
        df.to_csv('data/repositories.csv', index=False)
        
        print(f"\n✅ Successfully processed {len(all_repositories)} repositories")
        print(f"📊 Data saved to 'data/repositories.json' and 'data/repositories.csv'")
        
        # Print enhanced summary statistics
        print("\n📈 Enhanced Summary Statistics:")
        print(f"  - Total repositories: {len(all_repositories)}")
        print(f"  - Public repositories: {len([r for r in all_repositories if r['visibility'] == 'public'])}")
        print(f"  - Internal repositories: {len([r for r in all_repositories if r['visibility'] == 'internal'])}")
        
        # Feature eligibility stats
        featured_eligible = [r for r in all_repositories if r['featured']['eligible']]
        print(f"\n⭐ Featured Solutions Eligibility:")
        print(f"  - Repositories qualifying for featuring: {len(featured_eligible)}")
        print(f"  - Average feature score: {sum(r['featured']['score'] for r in all_repositories) / len(all_repositories):.1f}/100")
        
        # Show top featured candidates
        if featured_eligible:
            top_featured = sorted(featured_eligible, key=lambda x: x['featured']['score'], reverse=True)[:5]
            print(f"  - Top featured candidates:")
            for repo in top_featured:
                print(f"    * {repo['name']} ({repo['featured']['score']}/100) - {repo['owner']['login']}")
        
        # AI tag generation stats
        total_generated_tags = sum(len(r['generated_tags']) for r in all_repositories)
        repos_with_generated_tags = len([r for r in all_repositories if r['generated_tags']])
        print(f"\n🤖 AI Tag Generation Stats:")
        print(f"  - Total AI-generated tags: {total_generated_tags}")
        print(f"  - Repositories with AI tags: {repos_with_generated_tags}")
        if repos_with_generated_tags > 0:
            print(f"  - Average AI tags per repo: {total_generated_tags / repos_with_generated_tags:.1f}")
        
        # Count by organization
        org_counts = {}
        for repo in all_repositories:
            org = repo['owner']['login']
            org_counts[org] = org_counts.get(org, 0) + 1
        
        print(f"\n🏥 Organizations with repositories: {len(org_counts)}")
        for org, count in sorted(org_counts.items(), key=lambda x: x[1], reverse=True):
            org_featured = len([r for r in all_repositories if r['owner']['login'] == org and r['featured']['eligible']])
            print(f"    * {org}: {count} repositories ({org_featured} featured-eligible)")
            
    except Exception as e:
        print(f"❌ Error saving data: {str(e)}")

if __name__ == "__main__":
    main()
>>>>>>> da3d0780438625098785d3b610a27b3e2ceb928b
