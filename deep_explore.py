#!/usr/bin/env python3
"""
Deep Explorer for Neko Jirushi
This script explores listing pages to find actual individual cat profile links
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import config
import re

def explore_listing_page(listing_url):
    """Deeply explore a listing page to find individual cat profile links"""
    print(f"🔍 Deep exploring listing page: {listing_url}")
    
    headers = config.HEADERS
    
    try:
        response = requests.get(listing_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        print(f"✓ Successfully loaded listing page")
        print(f"Page title: {soup.title.string if soup.title else 'No title'}")
        
        # Find all links
        all_links = soup.find_all('a', href=True)
        print(f"📊 Found {len(all_links)} total links")
        
        # Look for patterns that might indicate individual cat profiles
        potential_profiles = []
        
        for link in all_links:
            href = link.get('href')
            text = link.get_text().strip()
            
            # Skip empty or very short text
            if not text or len(text) < 2:
                continue
            
            # Look for patterns that suggest individual cat profiles
            # These might be cat names, IDs, or specific profile patterns
            if any(pattern in href.lower() for pattern in ['detail', 'view', 'show', 'profile', 'cat']):
                if not any(exclude in href.lower() for exclude in ['list', 'category', 'page', 'st-']):
                    potential_profiles.append((href, text))
            # Also look for links that might contain cat IDs or names
            elif re.search(r'/\d+/?$', href) or re.search(r'/[a-zA-Z0-9_-]+/?$', href):
                if len(text) > 2 and len(text) < 50:  # Reasonable name length
                    potential_profiles.append((href, text))
        
        print(f"\n🐱 Potential individual cat profiles ({len(potential_profiles)}):")
        for href, text in potential_profiles[:20]:  # Show first 20
            full_url = urljoin(config.BASE_URL, href)
            print(f"  {text} -> {full_url}")
        
        return potential_profiles
        
    except Exception as e:
        print(f"❌ Error exploring listing page: {e}")
        return []

def explore_potential_cat_profile(profile_url):
    """Explore a potential individual cat profile to confirm it's a real cat profile"""
    print(f"\n🔍 Exploring potential cat profile: {profile_url}")
    
    headers = config.HEADERS
    
    try:
        response = requests.get(profile_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        print(f"✓ Successfully loaded potential profile")
        print(f"Page title: {soup.title.string if soup.title else 'No title'}")
        
        # Check page content
        page_text = soup.get_text().lower()
        
        # Look for indicators that this is an individual cat profile
        indicators = {
            'has_cat_name': any(word in page_text for word in ['name', '名前', 'cat', 'neko', '猫']),
            'has_images': len(soup.find_all('img')) > 3,
            'has_details': any(word in page_text for word in ['age', 'gender', 'breed', '年齢', '性別', '種類']),
            'has_description': any(word in page_text for word in ['description', '説明', 'detail', '詳細']),
            'not_listing': not any(word in page_text for word in ['list', 'category', 'page', '一覧', 'st-']),
            'has_contact': any(word in page_text for word in ['contact', '連絡', 'phone', '電話', 'email', 'メール'])
        }
        
        print(f"\n📊 Profile indicators:")
        for indicator, value in indicators.items():
            print(f"  {indicator}: {'✓' if value else '✗'}")
        
        # Look for images
        images = soup.find_all('img')
        cat_images = []
        
        for img in images:
            src = img.get('src') or img.get('data-src')
            alt = img.get('alt', 'No alt')
            if src and not any(exclude in src.lower() for exclude in ['logo', 'icon', 'banner', 'header']):
                cat_images.append((src, alt))
        
        print(f"\n🖼️ Found {len(cat_images)} potential cat images")
        
        # Show first few cat images
        for i, (src, alt) in enumerate(cat_images[:5]):
            print(f"  {i+1}. {alt} -> {src}")
        
        # Determine if this is likely an individual cat profile
        score = sum(indicators.values())
        is_profile = score >= 4 and len(cat_images) > 2
        
        print(f"\n🎯 Profile score: {score}/6")
        print(f"🎯 Likely individual cat profile: {'✓' if is_profile else '✗'}")
        
        return is_profile, cat_images, indicators
        
    except Exception as e:
        print(f"❌ Error exploring potential profile: {e}")
        return False, [], {}

def main():
    print("🔍 Deep Neko Jirushi Explorer")
    print("=" * 60)
    
    # Explore the main listing pages
    listing_pages = [
        "https://www.neko-jirushi.com/foster/cat/st-1/",
        "https://www.neko-jirushi.com/foster/cat/st-2/",
        "https://www.neko-jirushi.com/foster/cat/",
        "https://www.neko-jirushi.com/foster/cat/tokyo/st-1/",
        "https://www.neko-jirushi.com/foster/cat/hokkaido/st-1/"
    ]
    
    all_potential_profiles = []
    
    for listing_url in listing_pages:
        print(f"\n{'='*60}")
        potential_profiles = explore_listing_page(listing_url)
        all_potential_profiles.extend(potential_profiles)
        
        # Test first few potential profiles from this listing
        for href, text in potential_profiles[:3]:
            full_url = urljoin(config.BASE_URL, href)
            is_profile, images, indicators = explore_potential_cat_profile(full_url)
            
            if is_profile:
                print(f"\n✅ FOUND REAL CAT PROFILE: {text}")
                print(f"   URL: {full_url}")
                print(f"   Images: {len(images)}")
                break
    
    # Summary
    print(f"\n{'='*60}")
    print("📋 DEEP EXPLORATION SUMMARY")
    print("=" * 60)
    print(f"Total potential profiles found: {len(all_potential_profiles)}")
    
    # Show unique patterns
    unique_patterns = set()
    for href, text in all_potential_profiles:
        if href:
            # Extract the last part of the URL
            parts = href.split('/')
            if len(parts) > 1:
                unique_patterns.add(parts[-2] if parts[-1] == '' else parts[-1])
    
    print(f"\n🔍 UNIQUE URL PATTERNS FOUND:")
    for pattern in sorted(unique_patterns)[:20]:
        print(f"  - {pattern}")
    
    print(f"\n💡 RECOMMENDATIONS:")
    print(f"  - Look for URLs ending with: {', '.join(list(unique_patterns)[:5])}")
    print(f"  - Focus on links with cat names or IDs")
    print(f"  - Avoid links containing 'st-', 'list', 'category'")

if __name__ == "__main__":
    main() 