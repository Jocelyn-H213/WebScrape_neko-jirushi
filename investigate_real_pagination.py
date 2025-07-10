#!/usr/bin/env python3
"""
Investigate how the real website handles pagination
"""

import requests
from bs4 import BeautifulSoup
import re

def investigate_real_pagination():
    base_url = "https://neko-jirushi.com"
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    })
    
    # Test different page URLs
    for page in [1, 2, 3]:
        url = f"{base_url}/foster/cat/contents/?p={page}"
        print(f"\n=== Testing URL: {url} ===")
        
        response = session.get(url)
        print(f"Status: {response.status_code}")
        print(f"Content length: {len(response.content)}")
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for any JavaScript that might show the actual API call
            scripts = soup.find_all('script')
            for script in scripts:
                if script.string and 'ajax_getFosterList' in script.string:
                    print("Found ajax_getFosterList in script:")
                    print(script.string[:500] + "...")
                    break
            
            # Look for any form data or hidden inputs
            forms = soup.find_all('form')
            for form in forms:
                print(f"Form action: {form.get('action', 'N/A')}")
                inputs = form.find_all('input')
                for inp in inputs:
                    print(f"  Input: {inp.get('name', 'N/A')} = {inp.get('value', 'N/A')}")

if __name__ == "__main__":
    investigate_real_pagination() 