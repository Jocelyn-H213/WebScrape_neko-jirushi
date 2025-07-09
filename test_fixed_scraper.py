#!/usr/bin/env python3
"""
Test Fixed Scraper
This script tests the fixed image selectors to verify they're working
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

class TestFixedScraper:
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
    
    def test_cat_profile(self, profile_url):
        """Test image extraction on a cat profile page"""
        print(f"\n🧪 Testing: {profile_url}")
        
        response = self.get_page(profile_url)
        if not response:
            print("❌ Failed to load page")
            return
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Get page title
        title = soup.title.string if soup.title else 'No title'
        print(f"📄 Page title: {title}")
        
        # Test the fixed image selectors
        print("\n🔍 Testing fixed image selectors:")
        total_images_found = 0
        
        for selector in config.IMAGE_SELECTORS:
            images = soup.select(selector)
            if images:
                print(f"  ✅ {selector}: {len(images)} images")
                
                # Filter and show the actual cat images
                cat_images = []
                for img in images:
                    src = img.get("src") or img.get("data-src")
                    if src:
                        full_url = urljoin(self.base_url, src)
                        # Use the same filtering logic as the main scraper
                        if not any(exclude in full_url.lower() for exclude in [
                            'logo', 'icon', 'banner', 'header', 'nav', 'gnav', 
                            'mucho-domingo', 'headerhealth', 'headermail', 'headernotice'
                        ]) and '/img/foster/' in full_url:
                            cat_images.append(full_url)
                
                if cat_images:
                    print(f"    🐱 Found {len(cat_images)} cat images:")
                    for img_url in cat_images:
                        print(f"      - {img_url}")
                    total_images_found += len(cat_images)
                else:
                    print(f"    ⚠️ No cat images found with this selector")
            else:
                print(f"  ❌ {selector}: 0 images")
        
        print(f"\n📊 Summary: {total_images_found} cat images found total")
        return total_images_found

def main():
    tester = TestFixedScraper()
    
    print("🧪 Testing Fixed Image Selectors")
    print("This script verifies that the fixed selectors find cat images")
    print("=" * 70)
    
    # Test with a few known cat profile URLs
    test_urls = [
        "https://www.neko-jirushi.com/foster/226656/",
        "https://www.neko-jirushi.com/foster/226676/",
        "https://www.neko-jirushi.com/foster/226677/"
    ]
    
    total_images = 0
    for url in test_urls:
        images_found = tester.test_cat_profile(url)
        total_images += images_found
        time.sleep(config.DELAY_BETWEEN_REQUESTS)
        print("\n" + "="*50 + "\n")
    
    print(f"🎉 Total cat images found across all test pages: {total_images}")
    
    if total_images > 0:
        print("✅ The fixed selectors are working! You should now get many more images.")
    else:
        print("❌ Still no images found. Need to investigate further.")

if __name__ == "__main__":
    main() 