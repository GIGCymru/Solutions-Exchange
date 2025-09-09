#!/usr/bin/env python3
"""
NHS Wales Solutions Exchange - Private Repository and User Counter
Fetches private repository counts and user counts from NHS Wales organizations
Falls back to repositories.json if GitHub token is not available
"""

import requests
import json
import os
import sys
import logging
from datetime import datetime
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class NHSWalesPrivateMetricsFetcher:
    """Fetches private repository counts and user counts from NHS Wales organizations."""
    
    def __init__(self):
        """Initialize the fetcher with organizations list and GitHub token."""
        self.github_token = os.getenv('solutions_exchange_secret')
        if not self.github_token:
            logger.error("GitHub token not found. Set solutions_exchange_secret environment variable.")
            sys.exit(1)
        
        self.headers = {
            'Authorization': f'token {self.github_token}',
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'NHS-Wales-Solutions-Exchange/1.0'
        }
        logger.info("GitHub token found. Using API calls to fetch private repository data.")
        
        # Same organizations as update_repositories.py
        self.organizations = [
            "Analytics-Learning-Programme", 
            "Aneurin-Bevan-University-Health-Board",
            "Cardiff-Vale-University-Health-Board", 
            "Cwm-Taf-Morgannwg-UHB",
            "DHCW-Digital-Health-and-Care-Wales", 
            "GIGCymru",
            "HDUHB-Hywel-Dda-University-Health-Board",
            "NHS-Executive", 
            "Powys-Teaching-Health-Board",
            "Swansea-Bay-University-Health-Board",
            "Advanced-Analytics-NHS-Wales",
            "Betsi-Cadwaladr-University-Health-Board",
            "Genomics-Partnership-Wales",
            "National-Data-Resource",
            "Velindre-University-NHS-Trust",
            "Welsh-Ambulance-Services-NHS-Trust",
            "NDR-National-Data-Analytics-Platform",
            "CI-ARM",
            "NHS-Wales-Shared-Services-Partnership"
        ]
    
    def get_organization_repo_count(self, organization: str) -> Dict[str, int]:
        """Get repository counts for a specific organization by fetching ALL repositories."""
        repos = []
        page = 1
        
        logger.info(f"Fetching ALL repositories for organization: {organization}")
        
        while True:
            api_url = f'https://api.github.com/orgs/{organization}/repos'
            params = {'per_page': 100, 'page': page, 'type': 'all'}  # 'all' includes private repos
            
            try:
                response = requests.get(api_url, headers=self.headers, params=params, timeout=30)
                
                if response.status_code == 404:
                    logger.warning(f"Organization {organization} not found or not accessible")
                    break
                elif response.status_code != 200:
                    logger.error(f"Error fetching repositories for {organization}: {response.status_code}")
                    break
                
                data = response.json()
                
                if not data:
                    break  # No more data to fetch
                
                repos.extend(data)
                logger.debug(f"Page {page}: Found {len(data)} repos for {organization}")
                page += 1
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Request failed for {organization}: {e}")
                break
        
        # Count private and public repos
        private_count = sum(1 for repo in repos if repo.get('private', False))
        public_count = sum(1 for repo in repos if not repo.get('private', False))
        
        logger.info(f"{organization}: total={len(repos)}, public={public_count}, private={private_count}")
        
        return {
            "public_repos": public_count,
            "private_repos": private_count,
            "total_repos": len(repos)
        }
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """Get private repository counts and user counts from all NHS Wales organizations."""
        total_private_repos = 0
        total_public_repos = 0
        organization_count = 0
        accessible_orgs = []
        
        for org in self.organizations:
            try:
                logger.info(f"Processing organization: {org}")
                repo_counts = self.get_organization_repo_count(org)
                
                total_private_repos += repo_counts["private_repos"]
                total_public_repos += repo_counts["public_repos"]
                
                # Count organization if it has any repos
                if repo_counts["total_repos"] > 0:
                    organization_count += 1
                    accessible_orgs.append(org)
                    
            except Exception as e:
                logger.error(f"Failed to process organization {org}: {e}")
                continue
        
        logger.info(f"FINAL TOTALS: private={total_private_repos}, public={total_public_repos}, orgs={organization_count}")
        
        return {
            "private_repos": total_private_repos,
            "public_repos": total_public_repos,
            "organizations": organization_count,
            "accessible_organizations": accessible_orgs,
            "generated_at": datetime.now().isoformat(),
            "source": "github_api"
        }

def save_metrics_to_file(metrics: Dict[str, Any], output_path: str) -> None:
    """Save the metrics to a JSON file for use by the web pages"""
    # Ensure the directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(metrics, f, indent=2)

def main():
    """Main entry point."""
    output_path = "data/private_metrics.json"
    
    try:
        fetcher = NHSWalesPrivateMetricsFetcher()
        metrics = fetcher.get_all_metrics()
        
        # Save to file for web pages to use
        save_metrics_to_file(metrics, output_path)
        
        # Also print to stdout for direct use
        print(json.dumps({
            "private_repos": metrics["private_repos"],
            "organizations": metrics["organizations"],
            "source": metrics.get("source", "unknown")
        }))
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to fetch private metrics: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
