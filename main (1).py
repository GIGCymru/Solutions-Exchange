import requests
import pandas as pd
import os

# Replace this with your actual GitHub personal access token
GITHUB_TOKEN = os.getenv('GH_SECRET')

# Set up the headers with the token
headers = {
    'Authorization': f'token {GITHUB_TOKEN}'
}

# List of organizations
organizations = [
    "Analytics-Learning-Programme", "Aneurin-Bevan-University-Health-Board",
    "Cardiff-Vale-University-Health-Board", "Cwm-Taf-Morgannwg-UHB",
    "DHCW-Digital-Health-and-Care-Wales", "GIGCymru",
    "HDUHB-Hywel-Dda-University-Health-Board", "National-Data-Resource-NDR",
    "NHS-Executive", "Powys-Teaching-Health-Board",
    "Swansea-Bay-University-Health-Board"
]

def get_repositories_for_org(organization):
    repos = []
    page = 1
    while True:
        # Construct the API URL for the organization
        api_url = f'https://api.github.com/orgs/{organization}/repos'
        
        # Fetch the repositories for the current page
        response = requests.get(api_url, headers=headers, params={'per_page': 100, 'page': page})
        if response.status_code != 200:
            raise Exception(f"Error fetching repositories for {organization}: {response.status_code}, {response.text}")
        
        # Parse the JSON response
        data = response.json()
        
        if not data:
            break  # No more data to fetch

        # Filter repositories by visibility: only "public" or "internal"
        filtered_repos = [repo for repo in data if repo['visibility'] in ['public', 'internal']]
        
        # Add the filtered repositories to the list
        repos.extend(filtered_repos)
        
        # Move to the next page
        page += 1
    
    return repos

def main():
    all_repositories = []

    # Loop over each organization and get their repositories
    for org in organizations:
        print(f"Fetching repositories for organization: {org}")
        repos = get_repositories_for_org(org)
        all_repositories.extend(repos)

    # Create a DataFrame from the repositories list
    df = pd.DataFrame(all_repositories)

    # Output the DataFrame to a JSON file
    df.to_json('repositories.json', orient='records', indent=4)
    df.to_csv('repo.csv')

    print(f"Total repositories: {len(all_repositories)}")
    print("Filtered data has been saved to 'repositories.json'.")

if __name__ == "__main__":
    main()
