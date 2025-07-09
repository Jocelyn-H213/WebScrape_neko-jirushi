#!/usr/bin/env python3
"""
Test the discovered API endpoint
"""

import requests
import json

def test_api_endpoint():
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
    
    # Test with different parameters
    test_params = [
        {
            'search_cond': json.dumps({
                'params': 'contents/',
                'p': '1',
                'page': 0,
                'target_pref_id': '',
                'age_limit': '',
                'sex': '',
                'vaccine': '',
                'spay_and_neuter': '',
                'pattern_no': '',
                'status_id': '',
                'city_id': '',
                'city_name': '',
                'keyword': '',
                'user_id': '',
                'recruiter_pref': 0
            }),
            'spMode': 0
        },
        {
            'search_cond': json.dumps({
                'params': 'contents/',
                'p': '1'
            }),
            'spMode': 0
        },
        {
            'p': '1',
            'spMode': 0
        }
    ]
    
    for i, params in enumerate(test_params):
        print(f"\nTest {i+1}:")
        print(f"Parameters: {params}")
        
        try:
            response = session.post(api_url, data=params, timeout=30)
            print(f"Status: {response.status_code}")
            print(f"Content length: {len(response.content)} bytes")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"JSON response keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
                    
                    if isinstance(data, dict):
                        if 'foster_list' in data:
                            foster_list = data['foster_list']
                            print(f"Found {len(foster_list)} cats in foster_list")
                            if foster_list:
                                print(f"First cat: {foster_list[0]}")
                        
                        if 'page' in data:
                            page_info = data['page']
                            print(f"Page info: {page_info}")
                    
                    # Save response for inspection
                    with open(f'api_response_{i+1}.json', 'w', encoding='utf-8') as f:
                        json.dump(data, f, indent=2, ensure_ascii=False)
                    print(f"Saved response to api_response_{i+1}.json")
                    
                except json.JSONDecodeError:
                    print(f"Not JSON: {response.text[:500]}...")
                    with open(f'api_response_{i+1}.txt', 'w', encoding='utf-8') as f:
                        f.write(response.text)
                    print(f"Saved response to api_response_{i+1}.txt")
            else:
                print(f"Error response: {response.text[:200]}...")
                
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    test_api_endpoint() 