#!/usr/bin/env python3
"""
Test different API parameters to find working pagination
"""

import requests
import json

def test_different_params():
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
    
    # Test different parameter combinations
    test_cases = [
        {'page': '2', 'limit': '22'},
        {'page_num': '2', 'limit': '22'},
        {'offset': '22', 'limit': '22'},
        {'start': '22', 'limit': '22'},
        {'p': '2', 'limit': '22', 'sort': 'newest'},
        {'p': '2', 'limit': '22', 'order': 'desc'},
        {'p': '2', 'limit': '22', 'category': 'all'},
        {'p': '2', 'limit': '22', 'status': 'active'},
    ]
    
    for i, params in enumerate(test_cases):
        print(f"\n=== Test Case {i+1}: {params} ===")
        
        response = session.post(api_url, data=params)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                result = response.json()
                cats = result.get('foster_list', [])
                page_info = result.get('page_info', {})
                
                print(f"Total cats on page: {len(cats)}")
                print(f"Page info: {page_info}")
                
                # Show first 3 cat IDs
                cat_ids = [cat.get('cat_id', 'N/A') for cat in cats[:3]]
                print(f"First 3 cat IDs: {cat_ids}")
                
                # Show last 3 cat IDs
                cat_ids = [cat.get('cat_id', 'N/A') for cat in cats[-3:]]
                print(f"Last 3 cat IDs: {cat_ids}")
                
            except json.JSONDecodeError:
                print("Failed to parse JSON response")
        else:
            print(f"Request failed: {response.status_code}")

if __name__ == "__main__":
    test_different_params() 