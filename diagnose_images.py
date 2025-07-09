#!/usr/bin/env python3
"""
Image Diagnosis Script
This script examines cat profile pages to see what images are actually available
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

class ImageDiagnostic:
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
    
    def diagnose_cat_profile(self, profile_url):
        """Diagnose what images are available on a cat profile page"""
        print(f"\n🔍 Diagnosing: {profile_url}")
        
        response = self.get_page(profile_url)
        if not response:
            print("❌ Failed to load page")
            return
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Get page title
        title = soup.title.string if soup.title else 'No title'
        print(f"📄 Page title: {title}")
        
        # Check all images on the page
        all_images = soup.find_all('img')
        print(f"📸 Total images found: {len(all_images)}")
        
        if all_images:
            print("\n🔍 All images on page:")
            for i, img in enumerate(all_images[:10]):  # Show first 10
                src = img.get('src') or img.get('data-src')
                alt = img.get('alt', 'No alt')
                title_attr = img.get('title', 'No title')
                classes = ' '.join(img.get('class', []))
                
                print(f"  {i+1}. src: {src}")
                print(f"     alt: {alt}")
                print(f"     title: {title_attr}")
                print(f"     classes: {classes}")
                print()
        
        # Test current selectors
        print("🧪 Testing current image selectors:")
        for selector in config.IMAGE_SELECTORS:
            images = soup.select(selector)
            print(f"  {selector}: {len(images)} images")
            if images:
                for img in images[:3]:  # Show first 3
                    src = img.get('src') or img.get('data-src')
                    print(f"    - {src}")
        
        # Look for common image patterns
        print("\n🔍 Looking for image patterns:")
        
        # Check for images in common containers
        containers = [
            '.gallery', '.photos', '.images', '.catphoto', '.cat-photos',
            '.pet-photos', '.profile-photos', '.main-content', '.content'
        ]
        
        for container in containers:
            elements = soup.select(container)
            if elements:
                print(f"  Found {len(elements)} elements with selector: {container}")
                for elem in elements[:2]:  # Show first 2
                    imgs = elem.find_all('img')
                    print(f"    Contains {len(imgs)} images")
                    for img in imgs[:2]:  # Show first 2
                        src = img.get('src') or img.get('data-src')
                        print(f"      - {src}")
        
        # Check for data attributes that might contain image URLs
        print("\n🔍 Checking for data attributes:")
        for img in all_images[:5]:  # Check first 5 images
            for attr in img.attrs:
                if 'data-' in attr and 'src' in attr.lower():
                    value = img.get(attr)
                    print(f"  {attr}: {value}")
        
        # Look for background images
        print("\n🔍 Checking for background images:")
        elements_with_bg = soup.find_all(style=re.compile(r'background.*url'))
        print(f"  Elements with background images: {len(elements_with_bg)}")
        
        # Check for any div with background-image
        for elem in soup.find_all('div', class_=True)[:10]:
            style = elem.get('style', '')
            if 'background' in style and 'url' in style:
                print(f"  Background image found: {style}")

def main():
    diagnostic = ImageDiagnostic()
    
    print("🔍 Neko Jirushi Image Diagnostic")
    print("This script examines cat profile pages to understand image structure")
    print("=" * 70)
    
    # Test with a few known cat profile URLs
    test_urls = [
        "https://www.neko-jirushi.com/foster/226656/",
        "https://www.neko-jirushi.com/foster/226676/",
        "https://www.neko-jirushi.com/foster/226677/"
    ]
    
    for url in test_urls:
        diagnostic.diagnose_cat_profile(url)
        time.sleep(config.DELAY_BETWEEN_REQUESTS)
        print("\n" + "="*50 + "\n")

if __name__ == "__main__":
    main() 