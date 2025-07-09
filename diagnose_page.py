#!/usr/bin/env python3
"""
Diagnostic script to examine page structure
"""

import requests
from bs4 import BeautifulSoup
import re

def diagnose_page():
    url = "https://neko-jirushi.com/foster/cat/contents/?p=1"
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    })
    
    response = session.get(url)
    print(f"Status: {response.status_code}")
    print(f"Content length: {len(response.content)}")
    
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Look for any links to foster pages
    foster_links = soup.find_all('a', href=re.compile(r'/foster/\d+/'))
    print(f"\nFound {len(foster_links)} foster links:")
    for link in foster_links[:5]:  # Show first 5
        print(f"  {link['href']} - {link.get_text(strip=True)[:50]}")
    
    # Look for any divs or articles
    divs = soup.find_all('div')
    print(f"\nFound {len(divs)} divs")
    
    # Look for elements with 'cat' or 'foster' in class names
    cat_elements = soup.find_all(['div', 'article'], class_=re.compile(r'cat|foster|item'))
    print(f"\nFound {len(cat_elements)} elements with cat/foster/item classes")
    
    # Look for any images
    images = soup.find_all('img')
    print(f"\nFound {len(images)} images")
    for img in images[:3]:
        src = img.get('src') or img.get('data-src')
        print(f"  {src}")
    
    # Save the HTML for inspection
    with open('page_diagnosis.html', 'w', encoding='utf-8') as f:
        f.write(str(soup))
    print(f"\nSaved page HTML to page_diagnosis.html")

if __name__ == "__main__":
    diagnose_page() 