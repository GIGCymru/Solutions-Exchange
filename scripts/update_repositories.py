#!/usr/bin/env python3
"""
NHS Wales Solutions Exchange - Repository Data Fetcher
Automated script to fetch and enhance repository data for GitHub Actions
"""

import requests
import json
import os
import sys
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import random

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('update.log', mode='a')
    ]
)
logger = logging.getLogger(__name__)

class NHSWalesRepositoryFetcher:
    """Fetches and enhances NHS Wales repository data for the Solutions Exchange."""
    
    def __init__(self):
        self.github_token = os.getenv('solutions_exchange_secret')
        if not self.github_token:
            logger.error("GitHub token not found. Set solutions_exchange_secret environment variable.")
            sys.exit(1)
        
        # Log token type for debugging
        token_type = "Unknown"
        if self.github_token.startswith('ghp_'):
            token_type = "Classic Personal Access Token (ghp_)"
        elif self.github_token.startswith('ghu_'):
            token_type = "Fine-grained Personal Access Token (ghu_)"
        elif self.github_token.startswith('github_pat_'):
            token_type = "Fine-grained Personal Access Token (github_pat_)"
        
        logger.info(f"Using token type: {token_type}")
            
        self.headers = {
            'Authorization': f'token {self.github_token}',
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'NHS-Wales-Solutions-Exchange/1.0'
        }
        
        # NHS Wales organizations - Updated to match working local script
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
            "NHS-Wales-Shared-Services-Partnership",
            "Public-Health-Wales",
            "Secure-Data-Environment-GIG-Cymru"
        ]
        
        self.output_file = 'data/repositories.json'

    
    def fetch_organization_repositories(self, organization: str) -> List[Dict[str, Any]]:
        """Fetch all repositories for a given organization."""
        repos = []
        page = 1
        
        logger.info(f"Fetching repositories for organization: {organization}")
        
        while True:
            api_url = f'https://api.github.com/orgs/{organization}/repos'
            params = {'per_page': 100, 'page': page, 'type': 'all'}
            
            try:
                response = requests.get(api_url, headers=self.headers, params=params, timeout=30)
                
                if response.status_code == 404:
                    logger.warning(f"Organization {organization} not found or not accessible")
                    break
                elif response.status_code != 200:
                    logger.error(f"Error fetching repositories for {organization}: {response.status_code}, {response.text}")
                    break
                
                data = response.json()
                
                if not data:
                    break  # No more data to fetch
                
                # Filter repositories by visibility: only "public" or "internal"
                filtered_repos = [repo for repo in data if repo.get('visibility') in ['public', 'internal']]
                repos.extend(filtered_repos)
                
                logger.debug(f"Page {page}: Found {len(filtered_repos)} public/internal repos out of {len(data)} total")
                page += 1
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Request failed for {organization}: {e}")
                break
        
        logger.info(f"Total repositories for {organization}: {len(repos)}")
        return repos
    
    def generate_ai_tags(self, repo: Dict[str, Any]) -> List[str]:
        """Generate AI-like tags based on repository characteristics."""
        name = repo.get('name', '').lower()
        description = (repo.get('description') or '').lower()
        language = repo.get('language', '').lower() if repo.get('language') else ''
        topics = repo.get('topics', [])
        
        # Healthcare-specific tags
        healthcare_keywords = {
            'clinical': ['clinical', 'patient-care', 'medical'],
            'emergency': ['emergency-department', 'urgent-care', 'triage'],
            'data': ['data-analytics', 'healthcare-insights', 'reporting'],
            'integration': ['system-integration', 'interoperability', 'api'],
            'pharmacy': ['pharmacy', 'prescriptions', 'medications'],
            'dental': ['dental-services', 'oral-health'],
            'mental': ['mental-health', 'wellbeing', 'psychology'],
            'forecast': ['predictive-analytics', 'forecasting', 'ml'],
            'dashboard': ['visualization', 'monitoring', 'dashboards'],
            'mobile': ['mobile-health', 'digital-health'],
            'security': ['information-governance', 'data-security']
        }
        
        # Technology tags based on language
        tech_tags = {
            'python': ['python', 'data-science', 'automation'],
            'javascript': ['javascript', 'web-development', 'frontend'],
            'typescript': ['typescript', 'modern-web', 'scalable'],
            'java': ['java', 'enterprise', 'backend'],
            'c#': ['csharp', 'dotnet', 'microsoft-stack'],
            'r': ['r', 'statistical-analysis', 'research'],
            'sql': ['database', 'data-management', 'analytics'],
            'html': ['web-interface', 'frontend', 'user-experience'],
            'css': ['styling', 'responsive-design', 'ui'],
            'shell': ['automation', 'scripting', 'devops'],
            'dockerfile': ['containerization', 'deployment', 'docker']
        }
        
        generated_tags = set()
        
        # Add existing topics
        generated_tags.update(topics)
        
        # Add healthcare tags based on content
        for keyword, tags in healthcare_keywords.items():
            if keyword in name or keyword in description:
                generated_tags.update(tags[:2])  # Add up to 2 related tags
        
        # Add technology tags
        if language in tech_tags:
            generated_tags.update(tech_tags[language])
        
        # Add general NHS tags
        generated_tags.update(['nhs-wales', 'healthcare'])
        
        # Add quality indicators based on repository characteristics
        if repo.get('stargazers_count', 0) > 0:
            generated_tags.add('community-validated')
        if repo.get('has_readme'):
            generated_tags.add('well-documented')
        if repo.get('size', 0) > 1000:
            generated_tags.add('comprehensive')
            
        return list(generated_tags)[:8]  # Limit to 8 tags
    
    def calculate_quality_score(self, repo: Dict[str, Any]) -> int:
        """Calculate a quality score based on repository metrics."""
        score = 50  # Base score
        
        # Community engagement (0-20 points)
        stars = repo.get('stargazers_count', 0)
        score += min(stars * 3, 20)
        
        # Recent activity (0-15 points)
        if repo.get('pushed_at'):
            try:
                last_push = datetime.fromisoformat(repo['pushed_at'].replace('Z', '+00:00'))
                days_since_update = (datetime.now().replace(tzinfo=last_push.tzinfo) - last_push).days
                if days_since_update < 30:
                    score += 15
                elif days_since_update < 90:
                    score += 10
                elif days_since_update < 365:
                    score += 5
            except (ValueError, TypeError):
                pass
        
        # Documentation quality (0-15 points)
        if repo.get('has_readme'):
            score += 5
        description_length = len(repo.get('description') or '')
        if description_length > 50:
            score += 10
        elif description_length > 20:
            score += 5
        
        # Technical implementation (0-10 points)
        if repo.get('language'):
            score += 5
        if repo.get('topics'):
            score += 5
        
        # Repository size and activity (0-10 points)
        size = repo.get('size', 0)
        if size > 1000:
            score += 10
        elif size > 100:
            score += 5
        
        # License and open source practices (0-5 points)
        if repo.get('license'):
            score += 5
        
        return min(max(score, 30), 100)  # Clamp between 30-100
    
    def determine_featured_status(self, repo: Dict[str, Any], quality_score: int) -> bool:
        """Determine if a repository should be featured."""
        # High quality automatic feature
        if quality_score >= 80:
            return True
        
        # Community engagement threshold
        if quality_score >= 70 and repo.get('stargazers_count', 0) > 0:
            return True
        
        # Recent activity and good quality
        if quality_score >= 65:
            try:
                last_push = datetime.fromisoformat(repo['pushed_at'].replace('Z', '+00:00'))
                days_since_update = (datetime.now().replace(tzinfo=last_push.tzinfo) - last_push).days
                if days_since_update < 60:  # Recent activity
                    return True
            except (ValueError, TypeError):
                pass
        
        return False
    
    def enhance_repository_data(self, repo: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance repository data with AI tags and quality metrics."""
        # Generate AI tags
        generated_tags = self.generate_ai_tags(repo)
        all_tags = list(set(repo.get('topics', []) + generated_tags))
        
        # Calculate quality score
        quality_score = self.calculate_quality_score(repo)
        
        # Determine featured status
        featured = self.determine_featured_status(repo, quality_score)
        
        # Determine visibility status
        visibility = "Internal" if repo.get('private', False) else "Public"
        
        # Add enhancement fields
        repo['generated_tags'] = generated_tags
        repo['all_tags'] = all_tags
        repo['quality_score'] = quality_score
        repo['featured'] = featured
        repo['visibility'] = visibility
        repo['last_updated'] = datetime.now().isoformat()
        
        return repo
    
    def fetch_all_repositories(self) -> List[Dict[str, Any]]:
        """Fetch repositories from all NHS Wales organizations."""
        all_repositories = []
        
        for org in self.organizations:
            try:
                repos = self.fetch_organization_repositories(org)
                for repo in repos:
                    enhanced_repo = self.enhance_repository_data(repo)
                    all_repositories.append(enhanced_repo)
            except Exception as e:
                logger.error(f"Failed to process organization {org}: {e}")
                continue
        
        # Sort by quality score and last updated
        all_repositories.sort(key=lambda x: (x.get('quality_score', 0), x.get('updated_at', '')), reverse=True)
        
        logger.info(f"Total repositories fetched and enhanced: {len(all_repositories)}")
        
        # Log statistics
        featured_count = sum(1 for repo in all_repositories if repo.get('featured'))
        avg_quality = sum(repo.get('quality_score', 0) for repo in all_repositories) / len(all_repositories) if all_repositories else 0
        
        logger.info(f"Featured repositories: {featured_count}")
        logger.info(f"Average quality score: {avg_quality:.1f}")
        
        return all_repositories
    
    def save_repositories(self, repositories: List[Dict[str, Any]]) -> None:
        """Save repositories to JSON file."""
        # Ensure data directory exists
        os.makedirs(os.path.dirname(self.output_file), exist_ok=True)
        
        # Save with pretty formatting
        with open(self.output_file, 'w', encoding='utf-8') as f:
            json.dump(repositories, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved {len(repositories)} repositories to {self.output_file}")
    
    def run(self) -> bool:
        """Main execution method."""
        try:
            logger.info("Starting NHS Wales Solutions Exchange data update")
            logger.info(f"Fetching from {len(self.organizations)} organizations")
            
            repositories = self.fetch_all_repositories()
            
            if not repositories:
                logger.warning("No repositories fetched!")
                return False
            
            self.save_repositories(repositories)
            logger.info("Data update completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Fatal error during data update: {e}")
            return False

def main():
    """Main entry point."""
    fetcher = NHSWalesRepositoryFetcher()
    success = fetcher.run()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
