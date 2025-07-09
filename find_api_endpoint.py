#!/usr/bin/env python3
"""
Script to find the AJAX endpoint that loads cat data
"""

import requests
import json
import re

def find_api_endpoint():
    base_url = "https://neko-jirushi.com"
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Accept-Language': 'en-US,en;q=0.5',
        'X-Requested-With': 'XMLHttpRequest',
        'Referer': 'https://neko-jirushi.com/foster/cat/contents/?p=1'
    })
    
    # Try common API endpoints
    api_endpoints = [
        "/foster/api/cats",
        "/foster/api/list",
        "/foster/api/search",
        "/foster/cat/api/list",
        "/foster/cat/api/search",
        "/api/foster/cats",
        "/api/foster/list",
        "/foster/ajax/list",
        "/foster/ajax/cats",
        "/foster/cat/ajax/list",
        "/foster/cat/ajax/cats"
    ]
    
    print("Trying common API endpoints...")
    for endpoint in api_endpoints:
        try:
            url = base_url + endpoint
            response = session.get(url, timeout=10)
            print(f"{endpoint}: {response.status_code} - {len(response.content)} bytes")
            if response.status_code == 200 and len(response.content) > 100:
                try:
                    data = response.json()
                    print(f"  JSON response: {str(data)[:200]}...")
                except:
                    print(f"  Not JSON: {response.text[:200]}...")
        except Exception as e:
            print(f"{endpoint}: Error - {e}")
    
    # Try with query parameters
    print("\nTrying with query parameters...")
    query_endpoints = [
        "/foster/cat/contents/",
        "/foster/search_result.php",
        "/foster/api/search.php"
    ]
    
    for endpoint in query_endpoints:
        try:
            url = base_url + endpoint + "?p=1&format=json"
            response = session.get(url, timeout=10)
            print(f"{endpoint}?p=1&format=json: {response.status_code} - {len(response.content)} bytes")
            if response.status_code == 200 and len(response.content) > 100:
                try:
                    data = response.json()
                    print(f"  JSON response: {str(data)[:200]}...")
                except:
                    print(f"  Not JSON: {response.text[:200]}...")
        except Exception as e:
            print(f"{endpoint}: Error - {e}")
    
    # Try to get the JavaScript file to understand the API
    print("\nTrying to get the JavaScript file...")
    try:
        js_url = base_url + "/foster/inc/js/foster_search.js?date=20250526"
        response = session.get(js_url, timeout=10)
        if response.status_code == 200:
            js_content = response.text
            print(f"JavaScript file size: {len(js_content)} bytes")
            
            # Look for API URLs in the JavaScript
            api_patterns = [
                r'["\']([^"\']*api[^"\']*)["\']',
                r'["\']([^"\']*ajax[^"\']*)["\']',
                r'["\']([^"\']*search[^"\']*)["\']',
                r'url\s*[:=]\s*["\']([^"\']*)["\']',
                r'\.get\(["\']([^"\']*)["\']',
                r'\.post\(["\']([^"\']*)["\']'
            ]
            
            for pattern in api_patterns:
                matches = re.findall(pattern, js_content, re.IGNORECASE)
                for match in matches:
                    if any(keyword in match.lower() for keyword in ['api', 'ajax', 'search', 'list', 'cat', 'foster']):
                        print(f"  Found potential API: {match}")
        else:
            print(f"Failed to get JavaScript file: {response.status_code}")
    except Exception as e:
        print(f"Error getting JavaScript: {e}")

if __name__ == "__main__":
    find_api_endpoint() 