#!/usr/bin/env python3
"""
Debug script to test GitHub token permissions and API access
"""

import requests
import os

def test_github_token():
    token = os.getenv('GH_SECRET') or os.getenv('GITHUB_TOKEN')
    if not token:
        print("❌ No GitHub token found!")
        return
    
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    print(f"🔑 Testing token: {token[:8]}...{token[-4:]}")
    
    # Test 1: Check token permissions
    print("\n1. Testing token permissions...")
    response = requests.get('https://api.github.com/user', headers=headers)
    if response.status_code == 200:
        user_data = response.json()
        print(f"✅ Token valid for user: {user_data.get('login')}")
        print(f"   User type: {user_data.get('type')}")
    else:
        print(f"❌ Token validation failed: {response.status_code}")
        return
    
    # Test 2: Check rate limits
    print("\n2. Checking rate limits...")
    rate_limit = response.headers.get('X-RateLimit-Remaining', 'Unknown')
    rate_reset = response.headers.get('X-RateLimit-Reset', 'Unknown')
    print(f"   Remaining requests: {rate_limit}")
    
    # Test 3: Test organization access (try one org with different approaches)
    test_org = "DHCW-Digital-Health-and-Care-Wales"
    print(f"\n3. Testing organization access for: {test_org}")
    
    # Try different API endpoints
    endpoints = [
        f'https://api.github.com/orgs/{test_org}/repos',
        f'https://api.github.com/orgs/{test_org}/repos?type=all',
        f'https://api.github.com/orgs/{test_org}/repos?type=public',
        f'https://api.github.com/orgs/{test_org}/repos?type=private'
    ]
    
    for endpoint in endpoints:
        print(f"\n   Testing: {endpoint}")
        response = requests.get(endpoint, headers=headers, params={'per_page': 5})
        if response.status_code == 200:
            repos = response.json()
            print(f"   ✅ Found {len(repos)} repositories")
            if repos:
                for repo in repos[:2]:  # Show first 2
                    visibility = repo.get('visibility', 'unknown')
                    private = repo.get('private', 'unknown')
                    print(f"      - {repo['name']}: visibility={visibility}, private={private}")
        else:
            print(f"   ❌ Failed: {response.status_code} - {response.text[:100]}")

if __name__ == "__main__":
    test_github_token()
