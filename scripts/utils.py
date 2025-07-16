#!/usr/bin/env python3
"""
NHS Wales Solutions Exchange - Utilities
Common functions and utilities for data processing
"""

import json
import os
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

def load_repositories(file_path: str = 'data/repositories.json') -> List[Dict[str, Any]]:
    """Load repository data from JSON file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning(f"Repository file not found: {file_path}")
        return []
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in {file_path}: {e}")
        return []

def save_repositories(repositories: List[Dict[str, Any]], file_path: str = 'data/repositories.json') -> bool:
    """Save repository data to JSON file."""
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(repositories, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved {len(repositories)} repositories to {file_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to save repositories: {e}")
        return False

def get_repository_stats(repositories: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate statistics about the repository collection."""
    if not repositories:
        return {}
    
    total_repos = len(repositories)
    featured_repos = sum(1 for repo in repositories if repo.get('featured'))
    
    # Language distribution
    languages = {}
    for repo in repositories:
        lang = repo.get('language')
        if lang:
            languages[lang] = languages.get(lang, 0) + 1
    
    # Organization distribution
    organizations = {}
    for repo in repositories:
        org = repo.get('owner', {}).get('login')
        if org:
            organizations[org] = organizations.get(org, 0) + 1
    
    # Quality score distribution
    quality_scores = [repo.get('quality_score', 0) for repo in repositories]
    avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0
    
    # Recent activity (last 30 days)
    recent_cutoff = datetime.now().replace(tzinfo=None)
    recent_repos = 0
    for repo in repositories:
        try:
            last_push = datetime.fromisoformat(repo.get('pushed_at', '').replace('Z', ''))
            if (recent_cutoff - last_push).days <= 30:
                recent_repos += 1
        except (ValueError, TypeError):
            pass
    
    return {
        'total_repositories': total_repos,
        'featured_repositories': featured_repos,
        'featured_percentage': round((featured_repos / total_repos) * 100, 1) if total_repos > 0 else 0,
        'average_quality_score': round(avg_quality, 1),
        'recently_active': recent_repos,
        'languages': dict(sorted(languages.items(), key=lambda x: x[1], reverse=True)),
        'organizations': dict(sorted(organizations.items(), key=lambda x: x[1], reverse=True))
    }

def validate_repository_data(repositories: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Validate repository data structure and content."""
    validation_results = {
        'valid': True,
        'errors': [],
        'warnings': [],
        'statistics': {}
    }
    
    required_fields = ['id', 'name', 'full_name', 'html_url', 'owner']
    enhanced_fields = ['generated_tags', 'all_tags', 'quality_score', 'featured']
    
    for i, repo in enumerate(repositories):
        repo_name = repo.get('name', f'Repository {i}')
        
        # Check required fields
        for field in required_fields:
            if field not in repo:
                validation_results['errors'].append(f"{repo_name}: Missing required field '{field}'")
                validation_results['valid'] = False
        
        # Check enhanced fields
        for field in enhanced_fields:
            if field not in repo:
                validation_results['warnings'].append(f"{repo_name}: Missing enhanced field '{field}'")
        
        # Validate quality score
        quality_score = repo.get('quality_score')
        if quality_score is not None:
            if not isinstance(quality_score, (int, float)) or not (0 <= quality_score <= 100):
                validation_results['errors'].append(f"{repo_name}: Invalid quality_score '{quality_score}'")
                validation_results['valid'] = False
        
        # Validate featured status
        featured = repo.get('featured')
        if featured is not None and not isinstance(featured, bool):
            validation_results['errors'].append(f"{repo_name}: Invalid featured status '{featured}'")
            validation_results['valid'] = False
    
    validation_results['statistics'] = get_repository_stats(repositories)
    
    return validation_results

def map_organization_name(org_login: str) -> str:
    """Map GitHub organization login to full display name."""
    org_mapping = {
        'NHS-Executive': 'NHS Executive',
        'DHCW-Digital-Health-and-Care-Wales': 'Digital Health and Care Wales',
        'GIGCymru': 'GitHub GIG Cymru',
        'NHS-Wales': 'NHS Wales',
        'Betsi-Cadwaladr-UHB': 'Betsi Cadwaladr UHB',
        'Cardiff-and-Vale-UHB': 'Cardiff and Vale UHB',
        'Cardiff-Vale-University-Health-Board': 'Cardiff and Vale UHB',
        'Cwm-Taf-Morgannwg-UHB': 'Cwm Taf Morgannwg UHB',
        'TBUHB-Cwm-Taf-Morgannwg-University-Health-Board': 'Cwm Taf Morgannwg UHB',
        'Hywel-Dda-UHB': 'Hywel Dda UHB',
        'HDUHB-Hywel-Dda-University-Health-Board': 'Hywel Dda UHB',
        'Swansea-Bay-UHB': 'Swansea Bay UHB',
        'Swansea-Bay-University-Health-Board': 'Swansea Bay UHB',
        'Aneurin-Bevan-UHB': 'Aneurin Bevan UHB',
        'Aneurin-Bevan-University-Health-Board': 'Aneurin Bevan UHB',
        'Powys-Teaching-HB': 'Powys Teaching Health Board',
        'Powys-Teaching-Health-Board': 'Powys Teaching Health Board',
        'National-Data-Resource-NDR': 'National Data Resource',
        'Analytics-Learning-Programme': 'Analytics Learning Programme'
    }
    return org_mapping.get(org_login, org_login.replace('-', ' '))

def export_summary_report(repositories: List[Dict[str, Any]], output_file: str = 'data/summary_report.json') -> bool:
    """Export a summary report of the repository data."""
    try:
        stats = get_repository_stats(repositories)
        validation = validate_repository_data(repositories)
        
        summary = {
            'generated_at': datetime.now().isoformat(),
            'statistics': stats,
            'validation': validation,
            'featured_repositories': [
                {
                    'name': repo['name'],
                    'organization': map_organization_name(repo.get('owner', {}).get('login', '')),
                    'quality_score': repo.get('quality_score', 0),
                    'url': repo.get('html_url', ''),
                    'tags': repo.get('all_tags', [])[:5]  # First 5 tags
                }
                for repo in repositories if repo.get('featured')
            ][:10]  # Top 10 featured
        }
        
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Summary report exported to {output_file}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to export summary report: {e}")
        return False
