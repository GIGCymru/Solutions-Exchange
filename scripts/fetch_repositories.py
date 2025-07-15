import requests
import pandas as pd
import json
import os

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

def clean_repository_data(repo):
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

    # Loop over each organization and get their repositories
    for org in organizations:
        try:
            repos = get_repositories_for_org(org)
            # Clean the repository data
            cleaned_repos = [clean_repository_data(repo) for repo in repos]
            all_repositories.extend(cleaned_repos)
        except Exception as e:
            print(f"Error processing organization {org}: {str(e)}")
            continue

    # Sort repositories by update date (most recent first)
    all_repositories.sort(key=lambda x: x['updated_at'], reverse=True)

    # Create output files
    try:
        # Save as JSON for the web application
        with open('data/repositories.json', 'w', encoding='utf-8') as f:
            json.dump(all_repositories, f, indent=2, ensure_ascii=False)
        
        # Save as CSV for analysis
        df = pd.DataFrame(all_repositories)
        df.to_csv('data/repositories.csv', index=False)
        
        print(f"\n✅ Successfully processed {len(all_repositories)} repositories")
        print(f"📊 Data saved to 'data/repositories.json' and 'data/repositories.csv'")
        
        # Print summary statistics
        print("\n📈 Summary Statistics:")
        print(f"  - Total repositories: {len(all_repositories)}")
        print(f"  - Public repositories: {len([r for r in all_repositories if r['visibility'] == 'public'])}")
        print(f"  - Internal repositories: {len([r for r in all_repositories if r['visibility'] == 'internal'])}")
        
        # Count by organization
        org_counts = {}
        for repo in all_repositories:
            org = repo['owner']['login']
            org_counts[org] = org_counts.get(org, 0) + 1
        
        print(f"  - Organizations with repositories: {len(org_counts)}")
        for org, count in sorted(org_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"    * {org}: {count} repositories")
            
    except Exception as e:
        print(f"❌ Error saving data: {str(e)}")

if __name__ == "__main__":
    main()
