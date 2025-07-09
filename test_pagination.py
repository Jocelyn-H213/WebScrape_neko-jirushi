#!/usr/bin/env python3
"""
Test Pagination Script
This script tests different pagination patterns to see which ones work
"""

import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin
import time
import logging
import config

# Set up logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class PaginationTester:
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
            except requests.RequestException as e:
                logging.warning(f"Attempt {attempt + 1} failed for {url}: {e}")
                if attempt == retries - 1:
                    return None
                time.sleep(config.DELAY_BETWEEN_REQUESTS * (attempt + 1))
        return None
    
    def find_cat_profiles_in_page(self, url):
        """Find all cat profile URLs in a given page"""
        response = self.get_page(url)
        if not response:
            return []
        
        soup = BeautifulSoup(response.text, 'html.parser')
        cat_urls = []
        
        # Find all links
        all_links = soup.find_all('a', href=True)
        
        for link in all_links:
            href = link.get('href')
            if href and '/foster/' in href:
                # Check if it's a numeric ID (individual cat profile)
                if re.search(r'/foster/\d+/?$', href):
                    full_url = urljoin(self.base_url, href)
                    cat_urls.append(full_url)
        
        return cat_urls
    
    def test_pagination_patterns(self):
        """Test different pagination patterns"""
        print("🔍 Testing Pagination Patterns")
        print("=" * 50)
        
        base_url = "https://www.neko-jirushi.com/foster/cat/"
        
        # Test different pagination patterns
        patterns = [
            ("?p={}", "Query parameter p"),
            ("&p={}", "Query parameter p (with &)"),
            ("page/{}/", "Path-based page"),
            ("?page={}", "Query parameter page"),
            ("?page={}&p={}", "Both page parameters"),
            ("?p={}&page={}", "Both page parameters (reversed)"),
        ]
        
        for pattern, description in patterns:
            print(f"\n📄 Testing: {description}")
            print(f"Pattern: {pattern}")
            
            # Test first 5 pages
            for page in range(1, 6):
                url = base_url + pattern.format(page, page)
                cats = self.find_cat_profiles_in_page(url)
                
                if cats:
                    print(f"  Page {page}: Found {len(cats)} cats")
                    # Show first few cat URLs as examples
                    for i, cat_url in enumerate(cats[:3]):
                        print(f"    {i+1}. {cat_url}")
                    if len(cats) > 3:
                        print(f"    ... and {len(cats) - 3} more")
                else:
                    print(f"  Page {page}: No cats found")
                
                time.sleep(config.DELAY_BETWEEN_REQUESTS)
        
        # Also test the base URL without pagination
        print(f"\n📄 Testing: Base URL (no pagination)")
        cats = self.find_cat_profiles_in_page(base_url)
        if cats:
            print(f"  Base URL: Found {len(cats)} cats")
            for i, cat_url in enumerate(cats[:3]):
                print(f"    {i+1}. {cat_url}")
            if len(cats) > 3:
                print(f"    ... and {len(cats) - 3} more")
        else:
            print(f"  Base URL: No cats found")

def main():
    tester = PaginationTester()
    
    try:
        tester.test_pagination_patterns()
        print(f"\n✅ Pagination testing completed!")
        
    except KeyboardInterrupt:
        print("\n⚠️ Testing interrupted by user.")
    except Exception as e:
        logging.error(f"Testing failed: {e}")
        print(f"❌ Testing failed: {e}")

if __name__ == "__main__":
    main() 