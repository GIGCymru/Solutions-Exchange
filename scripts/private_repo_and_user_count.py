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
        self.github_token = os.getenv('solutions_exchange_secret')
        
        if self.github_token:
            self.headers = {
                'Authorization': f'token {self.github_token}',
                'Accept': 'application/vnd.github.v3+json',
                'User-Agent': 'NHS-Wales-Solutions-Exchange/1.0'
            }
        else:
            logger.warning("GitHub token not found. Will use fallback method with repositories.json")
            self.headers = None
        
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
        """Get repository counts for a specific organization."""
        if not self.headers:
            return {"public_repos": 0, "private_repos": 0, "total_private_repos": 0}
            
        api_url = f'https://api.github.com/orgs/{organization}'
        
        try:
            response = requests.get(api_url, headers=self.headers, timeout=30)
            
            if response.status_code == 404:
                logger.warning(f"Organization {organization} not found or not accessible")
                return {"public_repos": 0, "private_repos": 0, "total_private_repos": 0}
            elif response.status_code != 200:
                logger.error(f"Error fetching organization {organization}: {response.status_code}")
                return {"public_repos": 0, "private_repos": 0, "total_private_repos": 0}
            
            data = response.json()
            
            # Get the counts from the organization data
            public_repos = data.get('public_repos', 0)
            total_private_repos = data.get('total_private_repos', 0)
            private_repos = data.get('private_repos', 0)
            
            logger.info(f"{organization}: public={public_repos}, private={total_private_repos}")
            
            return {
                "public_repos": public_repos,
                "private_repos": private_repos,
                "total_private_repos": total_private_repos
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed for {organization}: {e}")
            return {"public_repos": 0, "private_repos": 0, "total_private_repos": 0}
    
    def get_metrics_from_repos_file(self, repo_json_path: str) -> Dict[str, Any]:
        """Fallback method: Get metrics from existing repositories.json file."""
        try:
            with open(repo_json_path, 'r') as f:
                repos = json.load(f)
            
            private_count = sum(1 for repo in repos if repo.get('private'))
            public_count = sum(1 for repo in repos if not repo.get('private'))
            organizations = set(repo['owner']['login'] for repo in repos)
            organization_count = len(organizations)
            
            logger.info(f"From repositories.json: private={private_count}, public={public_count}, orgs={organization_count}")
            
            return {
                "private_repos": private_count,
                "public_repos": public_count,
                "organizations": organization_count,
                "accessible_organizations": list(organizations),
                "generated_at": datetime.now().isoformat(),
                "source": "repositories.json"
            }
            
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error(f"Failed to read repositories.json: {e}")
            return {
                "private_repos": 0,
                "public_repos": 0,
                "organizations": 0,
                "accessible_organizations": [],
                "generated_at": datetime.now().isoformat(),
                "source": "error"
            }
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """Get private repository counts and user counts from all NHS Wales organizations."""
        if not self.headers:
            # Fallback to repositories.json
            return self.get_metrics_from_repos_file("data/repositories.json")
        
        total_private_repos = 0
        total_public_repos = 0
        organization_count = 0
        accessible_orgs = []
        
        for org in self.organizations:
            try:
                counts = self.get_organization_repo_count(org)
                if counts["public_repos"] > 0 or counts["total_private_repos"] > 0:
                    total_public_repos += counts["public_repos"]
                    total_private_repos += counts["total_private_repos"]
                    organization_count += 1
                    accessible_orgs.append(org)
                    
            except Exception as e:
                logger.error(f"Failed to process organization {org}: {e}")
                continue
        
        metrics = {
            "private_repos": total_private_repos,
            "public_repos": total_public_repos,
            "organizations": organization_count,
            "accessible_organizations": accessible_orgs,
            "generated_at": datetime.now().isoformat(),
            "source": "github_api"
        }
        
        logger.info(f"Total metrics: private_repos={total_private_repos}, public_repos={total_public_repos}, organizations={organization_count}")
        
        return metrics

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
