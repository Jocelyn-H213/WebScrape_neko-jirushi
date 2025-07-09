#!/usr/bin/env python3
"""
Test script for the Neko Jirushi Cat Scraper
This script tests the basic functionality without downloading images
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import logging

# Set up basic logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')

def test_website_access():
    """Test if we can access the website"""
    base_url = "https://www.neko-jirushi.com"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:
        print("Testing website access...")
        response = requests.get(base_url, headers=headers, timeout=10)
        response.raise_for_status()
        print(f"✓ Website accessible (Status: {response.status_code})")
        return True
    except Exception as e:
        print(f"✗ Website access failed: {e}")
        return False

def test_cat_listings():
    """Test if we can find cat listing pages"""
    base_url = "https://www.neko-jirushi.com"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    # Try different possible URL patterns
    possible_urls = [
        f"{base_url}/foster/cat/",
        f"{base_url}/foster/cat",
        f"{base_url}/cat/foster/",
        f"{base_url}/cat/foster",
        f"{base_url}/cats/",
        f"{base_url}/cats",
        f"{base_url}/",
    ]
    
    for url in possible_urls:
        try:
            print(f"Testing URL: {url}")
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for cat-related content
            cat_indicators = [
                "cat", "neko", "foster", "adopt", "pet", "animal"
            ]
            
            page_text = soup.get_text().lower()
            found_indicators = [indicator for indicator in cat_indicators if indicator in page_text]
            
            if found_indicators:
                print(f"✓ Found cat-related content: {found_indicators}")
                
                # Try to find cat links
                selectors = [
                    "a[href*='cat']",
                    "a[href*='neko']",
                    ".catlist a",
                    ".cat-item a",
                    ".listing a",
                    "a.catlist_tit"
                ]
                
                for selector in selectors:
                    links = soup.select(selector)
                    if links:
                        print(f"✓ Found {len(links)} potential cat links using selector: {selector}")
                        for i, link in enumerate(links[:3]):  # Show first 3
                            href = link.get('href')
                            text = link.get_text().strip()
                            print(f"  {i+1}. {text} -> {href}")
                        return True
                
                print("⚠ No specific cat links found, but page contains cat-related content")
                return True
            else:
                print("✗ No cat-related content found")
                
        except Exception as e:
            print(f"✗ Failed to access {url}: {e}")
    
    return False

def test_single_cat_page():
    """Test if we can access a single cat profile page"""
    base_url = "https://www.neko-jirushi.com"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    # Try to find a cat profile page
    try:
        # First get the main page
        response = requests.get(base_url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Look for any link that might lead to a cat profile
        cat_links = soup.find_all('a', href=True)
        cat_profile_url = None
        
        for link in cat_links:
            href = link.get('href')
            if href and ('cat' in href or 'neko' in href) and len(href) > 10:
                cat_profile_url = urljoin(base_url, href)
                break
        
        if cat_profile_url:
            print(f"Testing cat profile page: {cat_profile_url}")
            response = requests.get(cat_profile_url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for images
            images = soup.find_all('img')
            if images:
                print(f"✓ Found {len(images)} images on the page")
                for i, img in enumerate(images[:5]):  # Show first 5
                    src = img.get('src') or img.get('data-src')
                    alt = img.get('alt', 'No alt text')
                    print(f"  {i+1}. {alt} -> {src}")
                return True
            else:
                print("⚠ No images found on the page")
                return False
        else:
            print("⚠ Could not find a cat profile link to test")
            return False
            
    except Exception as e:
        print(f"✗ Failed to test cat profile page: {e}")
        return False

def main():
    print("Neko Jirushi Cat Scraper - Test Suite")
    print("=" * 50)
    
    tests = [
        ("Website Access", test_website_access),
        ("Cat Listings", test_cat_listings),
        ("Single Cat Page", test_single_cat_page),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        print("-" * 30)
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"✗ Test failed with exception: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 50)
    print("Test Results Summary:")
    print("-" * 30)
    
    passed = 0
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All tests passed! The scraper should work correctly.")
    elif passed > 0:
        print("⚠ Some tests passed. The scraper might work with modifications.")
    else:
        print("❌ No tests passed. The website structure may have changed significantly.")

if __name__ == "__main__":
    main() 