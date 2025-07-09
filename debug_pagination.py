#!/usr/bin/env python3
"""
Debug Pagination Script
This script investigates why pagination is not working correctly
"""

import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin, urlparse
import time
import logging
import config

# Set up logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class PaginationDebugger:
    def __init__(self):
        self.base_url = config.BASE_URL
        self.session = requests.Session()
        self.session.headers.update(config.HEADERS)
    
    def get_page(self, url, retries=3):
        """Get page content with retry logic"""
        for attempt in range(retries):
            try:
                response = self.session.get(url, timeout=config.TIMEOUT)
                response.raise_for_status()
                return response
            except Exception as e:
                logging.warning(f"Attempt {attempt + 1} failed for {url}: {e}")
                if attempt == retries - 1:
                    return None
                time.sleep(config.DELAY_BETWEEN_REQUESTS)
        return None
    
    def debug_pagination(self):
        """Debug pagination by testing different URL patterns"""
        print("🔍 Debugging Pagination Issues")
        print("=" * 50)
        
        # Test different pagination patterns
        pagination_patterns = [
            "/foster/cat/?p={}",
            "/foster/cat?p={}",
            "/foster/?p={}",
            "/foster?p={}",
            "/cat/foster/?p={}",
            "/cat/foster?p={}",
            "/cats/?p={}",
            "/cats?p={}",
            "/cat/?p={}",
            "/cat?p={}",
            "/foster/cat/?page={}",
            "/foster/cat?page={}",
            "/foster/?page={}",
            "/foster?page={}",
        ]
        
        for pattern in pagination_patterns:
            print(f"\n🧪 Testing pattern: {pattern}")
            
            # Test pages 1 and 2
            for page in [1, 2]:
                url = self.base_url + pattern.format(page)
                print(f"  Testing: {url}")
                
                response = self.get_page(url)
                if not response:
                    print(f"    ❌ Failed to load")
                    continue
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Check if page actually changed
                title = soup.title.string if soup.title else 'No title'
                print(f"    📄 Title: {title[:50]}...")
                
                # Look for pagination indicators
                pagination_elements = soup.find_all(['a', 'span', 'div'], 
                    string=re.compile(r'page|pagination|next|prev|前|次|ページ', re.I))
                
                if pagination_elements:
                    print(f"    🔗 Found {len(pagination_elements)} pagination elements:")
                    for elem in pagination_elements[:3]:
                        print(f"      - {elem.get_text().strip()}")
                
                # Check for cat links
                cat_links = soup.find_all('a', href=re.compile(r'/foster/\d+/'))
                if cat_links:
                    cat_ids = []
                    for link in cat_links[:5]:  # Show first 5
                        href = link.get('href', '')
                        match = re.search(r'/foster/(\d+)/', href)
                        if match:
                            cat_ids.append(match.group(1))
                    
                    print(f"    🐱 Found {len(cat_links)} cat links, first 5 IDs: {cat_ids}")
                else:
                    print(f"    ❌ No cat links found")
                
                time.sleep(1)  # Be nice to the server
        
        # Test the actual main listing URL
        print(f"\n🔍 Testing main listing URL: {self.base_url}/foster/cat/")
        response = self.get_page(f"{self.base_url}/foster/cat/")
        if response:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for any pagination links
            all_links = soup.find_all('a', href=True)
            pagination_links = []
            
            for link in all_links:
                href = link.get('href', '')
                if any(param in href for param in ['p=', 'page=', '?p=', '?page=']):
                    pagination_links.append({
                        'text': link.get_text().strip(),
                        'href': href
                    })
            
            if pagination_links:
                print(f"  🔗 Found {len(pagination_links)} pagination links:")
                for link in pagination_links[:10]:
                    print(f"    - {link['text']} -> {link['href']}")
            else:
                print(f"  ❌ No pagination links found")
            
            # Check for any JavaScript that might handle pagination
            scripts = soup.find_all('script')
            pagination_js = []
            for script in scripts:
                if script.string and any(term in script.string.lower() for term in ['page', 'pagination', 'next', 'prev']):
                    pagination_js.append(script.string[:100] + "...")
            
            if pagination_js:
                print(f"  📜 Found {len(pagination_js)} scripts with pagination terms:")
                for js in pagination_js[:3]:
                    print(f"    - {js}")

def main():
    debugger = PaginationDebugger()
    debugger.debug_pagination()

if __name__ == "__main__":
    main() 