#!/usr/bin/env python3
"""
Website Structure Explorer for Neko Jirushi
This script helps understand the website structure and find individual cat profile URLs
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import config

def explore_main_foster_page():
    """Explore the main foster page to understand the structure"""
    print("🔍 Exploring main foster page...")
    
    url = "https://www.neko-jirushi.com/foster/"
    headers = config.HEADERS
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        print(f"✓ Successfully loaded: {url}")
        print(f"Page title: {soup.title.string if soup.title else 'No title'}")
        
        # Find all links
        all_links = soup.find_all('a', href=True)
        print(f"\n📊 Found {len(all_links)} total links")
        
        # Categorize links
        foster_links = []
        cat_links = []
        other_links = []
        
        for link in all_links:
            href = link.get('href')
            text = link.get_text().strip()
            
            if '/foster/' in href:
                foster_links.append((href, text))
            elif '/cat/' in href or 'cat' in href.lower():
                cat_links.append((href, text))
            else:
                other_links.append((href, text))
        
        print(f"\n🐱 Foster-related links ({len(foster_links)}):")
        for href, text in foster_links[:10]:  # Show first 10
            print(f"  {text} -> {href}")
        
        print(f"\n🐈 Cat-related links ({len(cat_links)}):")
        for href, text in cat_links[:10]:  # Show first 10
            print(f"  {text} -> {href}")
        
        return foster_links, cat_links
        
    except Exception as e:
        print(f"❌ Error exploring main page: {e}")
        return [], []

def explore_category_page(category_url):
    """Explore a specific category page to find individual cat profiles"""
    print(f"\n🔍 Exploring category page: {category_url}")
    
    headers = config.HEADERS
    
    try:
        response = requests.get(category_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        print(f"✓ Successfully loaded category page")
        print(f"Page title: {soup.title.string if soup.title else 'No title'}")
        
        # Look for individual cat profile links
        all_links = soup.find_all('a', href=True)
        
        # Look for links that might be individual cat profiles
        potential_profiles = []
        
        for link in all_links:
            href = link.get('href')
            text = link.get_text().strip()
            
            # Look for patterns that suggest individual cat profiles
            if any(keyword in href.lower() for keyword in ['detail', 'view', 'show', 'profile', 'cat']):
                if not any(exclude in href.lower() for exclude in ['list', 'category', 'page']):
                    potential_profiles.append((href, text))
        
        print(f"\n🐱 Potential individual cat profiles ({len(potential_profiles)}):")
        for href, text in potential_profiles[:15]:  # Show first 15
            full_url = urljoin(config.BASE_URL, href)
            print(f"  {text} -> {full_url}")
        
        return potential_profiles
        
    except Exception as e:
        print(f"❌ Error exploring category page: {e}")
        return []

def explore_potential_profile(profile_url):
    """Explore a potential individual cat profile page"""
    print(f"\n🔍 Exploring potential profile: {profile_url}")
    
    headers = config.HEADERS
    
    try:
        response = requests.get(profile_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        print(f"✓ Successfully loaded profile page")
        print(f"Page title: {soup.title.string if soup.title else 'No title'}")
        
        # Check if this looks like an individual cat profile
        page_text = soup.get_text().lower()
        
        # Look for indicators that this is an individual cat profile
        indicators = {
            'has_cat_name': any(word in page_text for word in ['name', '名前', 'cat', 'neko']),
            'has_images': len(soup.find_all('img')) > 5,
            'has_details': any(word in page_text for word in ['age', 'gender', 'breed', '年齢', '性別']),
            'not_listing': not any(word in page_text for word in ['list', 'category', 'page', '一覧'])
        }
        
        print(f"\n📊 Profile indicators:")
        for indicator, value in indicators.items():
            print(f"  {indicator}: {'✓' if value else '✗'}")
        
        # Look for images
        images = soup.find_all('img')
        print(f"\n🖼️ Found {len(images)} images")
        
        # Show first few image sources
        for i, img in enumerate(images[:5]):
            src = img.get('src') or img.get('data-src')
            alt = img.get('alt', 'No alt')
            print(f"  {i+1}. {alt} -> {src}")
        
        # Determine if this is likely an individual cat profile
        is_profile = sum(indicators.values()) >= 3
        print(f"\n🎯 Likely individual cat profile: {'✓' if is_profile else '✗'}")
        
        return is_profile, images
        
    except Exception as e:
        print(f"❌ Error exploring profile page: {e}")
        return False, []

def main():
    print("🌐 Neko Jirushi Website Structure Explorer")
    print("=" * 60)
    
    # Step 1: Explore main foster page
    foster_links, cat_links = explore_main_foster_page()
    
    if not foster_links and not cat_links:
        print("❌ No useful links found on main page")
        return
    
    # Step 2: Explore first few category pages
    category_urls = []
    for href, text in foster_links[:3]:  # Try first 3 foster links
        full_url = urljoin(config.BASE_URL, href)
        category_urls.append(full_url)
    
    for href, text in cat_links[:3]:  # Try first 3 cat links
        full_url = urljoin(config.BASE_URL, href)
        if full_url not in category_urls:
            category_urls.append(full_url)
    
    print(f"\n🔍 Will explore {len(category_urls)} category pages...")
    
    # Step 3: Explore each category page
    all_potential_profiles = []
    for category_url in category_urls:
        potential_profiles = explore_category_page(category_url)
        all_potential_profiles.extend(potential_profiles)
    
    if not all_potential_profiles:
        print("❌ No potential individual cat profiles found")
        return
    
    # Step 4: Explore first few potential profiles
    print(f"\n🔍 Will explore first 3 potential profiles...")
    
    confirmed_profiles = []
    for href, text in all_potential_profiles[:3]:
        full_url = urljoin(config.BASE_URL, href)
        is_profile, images = explore_potential_profile(full_url)
        
        if is_profile:
            confirmed_profiles.append((full_url, text, len(images)))
    
    # Summary
    print(f"\n" + "=" * 60)
    print("📋 EXPLORATION SUMMARY")
    print("=" * 60)
    print(f"Total foster links found: {len(foster_links)}")
    print(f"Total cat links found: {len(cat_links)}")
    print(f"Total potential profiles found: {len(all_potential_profiles)}")
    print(f"Confirmed individual profiles: {len(confirmed_profiles)}")
    
    if confirmed_profiles:
        print(f"\n✅ CONFIRMED INDIVIDUAL CAT PROFILES:")
        for url, text, image_count in confirmed_profiles:
            print(f"  {text} ({image_count} images) -> {url}")
        
        print(f"\n💡 RECOMMENDATIONS:")
        print(f"  - Use URLs containing: {', '.join(set([url.split('/')[-2] for url, _, _ in confirmed_profiles]))}")
        print(f"  - Look for patterns in: {', '.join([url.split('/')[-1] for url, _, _ in confirmed_profiles])}")
    else:
        print(f"\n⚠️ No confirmed individual cat profiles found")
        print(f"  - The website structure might be different than expected")
        print(f"  - Consider exploring more pages or different URL patterns")

if __name__ == "__main__":
    main() 