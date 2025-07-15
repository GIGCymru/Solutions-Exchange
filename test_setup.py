#!/usr/bin/env python3
"""
Simple test script to validate the Solutions Exchange setup
"""

import json
import os
import sys

def test_json_file():
    """Test that repositories.json exists and is valid JSON"""
    try:
        with open('repositories.json', 'r') as f:
            data = json.load(f)
        
        print(f"✅ repositories.json is valid JSON with {len(data)} repositories")
        
        # Check structure of first repository
        if data and len(data) > 0:
            repo = data[0]
            required_fields = ['name', 'description', 'html_url', 'owner', 'visibility']
            missing_fields = [field for field in required_fields if field not in repo]
            
            if missing_fields:
                print(f"⚠️  Missing fields in repository data: {missing_fields}")
            else:
                print("✅ Repository data structure is correct")
        
        return True
    except FileNotFoundError:
        print("❌ repositories.json not found")
        return False
    except json.JSONDecodeError as e:
        print(f"❌ repositories.json is not valid JSON: {e}")
        return False

def test_html_file():
    """Test that index.html exists and has required elements"""
    try:
        with open('index.html', 'r') as f:
            content = f.read()
        
        required_elements = [
            'NHS Wales Solutions Exchange',
            'repositories.json',
            'filterProjects',
            'jsonData'
        ]
        
        missing_elements = [element for element in required_elements if element not in content]
        
        if missing_elements:
            print(f"⚠️  Missing elements in index.html: {missing_elements}")
            return False
        else:
            print("✅ index.html contains required elements")
            return True
            
    except FileNotFoundError:
        print("❌ index.html not found")
        return False

def test_css_file():
    """Test that CSS file exists"""
    if os.path.exists('css/style.css'):
        print("✅ CSS file exists")
        return True
    else:
        print("❌ css/style.css not found")
        return False

def test_python_script():
    """Test that Python script exists and has required imports"""
    try:
        with open('fetch_repositories.py', 'r') as f:
            content = f.read()
        
        required_imports = ['requests', 'pandas', 'json']
        missing_imports = [imp for imp in required_imports if f"import {imp}" not in content]
        
        if missing_imports:
            print(f"⚠️  Missing imports in fetch_repositories.py: {missing_imports}")
            return False
        else:
            print("✅ Python script has required imports")
            return True
            
    except FileNotFoundError:
        print("❌ fetch_repositories.py not found")
        return False

def main():
    """Run all tests"""
    print("🧪 Testing NHS Wales Solutions Exchange Setup\n")
    
    tests = [
        ("JSON Data File", test_json_file),
        ("HTML File", test_html_file),
        ("CSS File", test_css_file),
        ("Python Script", test_python_script)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"Testing {test_name}...")
        result = test_func()
        results.append(result)
        print()
    
    passed = sum(results)
    total = len(results)
    
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The Solutions Exchange is ready to deploy.")
        print("\nNext steps:")
        print("1. Commit your changes to GitHub")
        print("2. Set up the GITHUB_TOKEN secret")
        print("3. Enable GitHub Pages")
        print("4. The workflow will run automatically daily at 6 AM UTC")
    else:
        print("⚠️  Some tests failed. Please check the issues above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
