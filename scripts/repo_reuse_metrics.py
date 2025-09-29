#!/usr/bin/env python3
"""
NHS Wales Solutions Exchange - Repo Reuse Metrics
Fetches forks, clones, and (if possible) downloads for all repos in data/repositories.json
Saves results to data/reuse_metrics.json
"""

import requests
import json
import os
import logging
from typing import Dict, Any, List

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_github_token():
    token = os.getenv('solutions_exchange_secret')
    if not token:
        logger.error("GitHub token not found. Set solutions_exchange_secret environment variable.")
        exit(1)
    return token

def load_repositories(path='data/repositories.json') -> List[Dict[str, Any]]:
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load repositories: {e}")
        return []

def fetch_repo_metrics(owner: str, repo: str, headers: Dict[str, str]) -> Dict[str, Any]:
    base_url = f"https://api.github.com/repos/{owner}/{repo}"
    metrics = {}
    # Forks
    r = requests.get(base_url, headers=headers)
    if r.status_code == 200:
        data = r.json()
        metrics['forks_count'] = data.get('forks_count', 0)
    else:
        metrics['forks_count'] = None
    # Clones (requires repo admin)
    r = requests.get(base_url + "/traffic/clones", headers=headers)
    if r.status_code == 200:
        data = r.json()
        metrics['clones_count'] = data.get('count', 0)
        metrics['clones_uniques'] = data.get('uniques', 0)
    else:
        metrics['clones_count'] = None
        metrics['clones_uniques'] = None
    # Downloads (GitHub API only supports releases)
    r = requests.get(base_url + "/releases", headers=headers)
    if r.status_code == 200:
        releases = r.json()
        total_downloads = 0
        for release in releases:
            for asset in release.get('assets', []):
                total_downloads += asset.get('download_count', 0)
        metrics['downloads_count'] = total_downloads
    else:
        metrics['downloads_count'] = None
    return metrics

def main():
    token = get_github_token()
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json',
        'User-Agent': 'NHS-Wales-Solutions-Exchange/metrics'
    }
    repos = load_repositories()
    results = []
    for repo in repos:
        owner = repo.get('owner', {}).get('login')
        name = repo.get('name')
        if not owner or not name:
            continue
        logger.info(f"Fetching metrics for {owner}/{name}")
        metrics = fetch_repo_metrics(owner, name, headers)
        results.append({
            'owner': owner,
            'name': name,
            **metrics
        })
    # Save results
    out_path = 'data/reuse_metrics.json'
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Saved metrics for {len(results)} repos to {out_path}")

if __name__ == "__main__":
    main()
