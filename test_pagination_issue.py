#!/usr/bin/env python3
"""
Test API pagination to understand why same cats are returned
"""

import requests
import json

def test_api_pagination():
    base_url = "https://neko-jirushi.com"
    api_url = base_url + "/foster/ajax/ajax_getFosterList.php"
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Accept-Language': 'en-US,en;q=0.5',
        'X-Requested-With': 'XMLHttpRequest',
        'Referer': 'https://neko-jirushi.com/foster/cat/contents/?p=1',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'
    })
    
    # Test different pages
    for page in [1, 2, 3, 10, 50, 100]:
        data = {
            'p': str(page),
            'limit': '22'
        }
        
        response = session.post(api_url, data=data)
        print(f"\n=== Page {page} ===")
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                result = response.json()
                cats = result.get('foster_list', [])
                page_info = result.get('page_info', {})
                
                print(f"Total cats on page: {len(cats)}")
                print(f"Page info: {page_info.get('now_page', 'N/A')}/{page_info.get('all_page', 'N/A')}")
                print(f"Total cats available: {page_info.get('rows', 'N/A')}")
                
                # Show first 3 cat IDs
                cat_ids = [cat.get('cat_id', 'N/A') for cat in cats[:3]]
                print(f"First 3 cat IDs: {cat_ids}")
                
                # Show last 3 cat IDs
                cat_ids = [cat.get('cat_id', 'N/A') for cat in cats[-3:]]
                print(f"Last 3 cat IDs: {cat_ids}")
                
            except json.JSONDecodeError:
                print("Failed to parse JSON response")
                print(f"Response: {response.text[:200]}...")
        else:
            print(f"Request failed: {response.status_code}")

if __name__ == "__main__":
    test_api_pagination() 