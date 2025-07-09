#!/usr/bin/env python3
"""
Cat Discovery Script
This script helps discover more cat profile URLs by exploring different patterns
"""

import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin
import json
import time
import logging
import config

# Set up logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class CatDiscovery:
    def __init__(self):
        self.base_url = config.BASE_URL
        self.session = requests.Session()
        self.session.headers.update(config.HEADERS)
        self.discovered_cats = set()
    
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
                    if full_url not in self.discovered_cats:
                        cat_urls.append(full_url)
                        self.discovered_cats.add(full_url)
        
        return cat_urls
    
    def discover_from_main_listing(self):
        """Discover cats from the main listing with pagination"""
        logging.info("Discovering cats from main listing...")
        
        base_url = "https://www.neko-jirushi.com/foster/cat/"
        all_cats = []
        
        # Try different page patterns
        for page in range(1, 21):  # Try up to 20 pages
            page_urls = [
                f"{base_url}?p={page}",
                f"{base_url}&p={page}",
                f"{base_url}page/{page}/",
            ]
            
            for page_url in page_urls:
                cats = self.find_cat_profiles_in_page(page_url)
                if cats:
                    all_cats.extend(cats)
                    logging.info(f"Found {len(cats)} cats on page {page}")
                    break
            else:
                logging.info(f"No cats found on page {page}, stopping pagination")
                break
            
            time.sleep(config.DELAY_BETWEEN_REQUESTS)
        
        return all_cats
    
    def discover_from_prefecture_listings(self):
        """Discover cats from prefecture-specific listings"""
        logging.info("Discovering cats from prefecture listings...")
        
        prefectures = [
            'tokyo', 'hokkaido', 'kanagawa', 'saitama', 'chiba', 'osaka', 'kyoto', 
            'hyogo', 'aichi', 'fukuoka', 'hiroshima', 'miyagi', 'shizuoka', 'ibaraki',
            'tochigi', 'gunma', 'niigata', 'nagano', 'gifu', 'mie', 'shiga', 'nara',
            'wakayama', 'tottori', 'shimane', 'okayama', 'yamaguchi', 'tokushima',
            'kagawa', 'ehime', 'kochi', 'fukushima', 'yamagata', 'akita', 'iwate',
            'aomori', 'yamanashi', 'nagasaki', 'kumamoto', 'oita', 'miyazaki',
            'kagoshima', 'okinawa'
        ]
        
        all_cats = []
        
        for prefecture in prefectures:
            logging.info(f"Checking prefecture: {prefecture}")
            
            # Try different URL patterns for each prefecture
            prefecture_urls = [
                f"https://www.neko-jirushi.com/foster/cat/{prefecture}/",
                f"https://www.neko-jirushi.com/foster/cat/{prefecture}/st-1/",
                f"https://www.neko-jirushi.com/foster/cat/{prefecture}/st-2/",
                f"https://www.neko-jirushi.com/foster/cat/{prefecture}/st-3/",
            ]
            
            for url in prefecture_urls:
                cats = self.find_cat_profiles_in_page(url)
                if cats:
                    all_cats.extend(cats)
                    logging.info(f"Found {len(cats)} cats in {prefecture}")
                    break
            
            time.sleep(config.DELAY_BETWEEN_REQUESTS)
        
        return all_cats
    
    def discover_from_search_results(self):
        """Discover cats by trying different search patterns"""
        logging.info("Discovering cats from search results...")
        
        # Try different search terms that might reveal more cats
        search_terms = [
            '子猫', '成猫', 'キジトラ', '三毛', '白猫', '黒猫', '茶トラ',
            'kitten', 'adult', 'male', 'female', 'young', 'senior'
        ]
        
        all_cats = []
        
        for term in search_terms:
            search_urls = [
                f"https://www.neko-jirushi.com/foster/cat/?search={term}",
                f"https://www.neko-jirushi.com/foster/?search={term}",
            ]
            
            for url in search_urls:
                cats = self.find_cat_profiles_in_page(url)
                if cats:
                    all_cats.extend(cats)
                    logging.info(f"Found {len(cats)} cats for search term: {term}")
                    break
            
            time.sleep(config.DELAY_BETWEEN_REQUESTS)
        
        return all_cats
    
    def discover_all_cats(self):
        """Discover cats using all methods"""
        logging.info("Starting comprehensive cat discovery...")
        
        all_cats = []
        
        # Method 1: Main listing with pagination
        cats1 = self.discover_from_main_listing()
        all_cats.extend(cats1)
        logging.info(f"Method 1 found {len(cats1)} cats")
        
        # Method 2: Prefecture listings
        cats2 = self.discover_from_prefecture_listings()
        all_cats.extend(cats2)
        logging.info(f"Method 2 found {len(cats2)} cats")
        
        # Method 3: Search results
        cats3 = self.discover_from_search_results()
        all_cats.extend(cats3)
        logging.info(f"Method 3 found {len(cats3)} cats")
        
        # Remove duplicates
        unique_cats = list(set(all_cats))
        
        logging.info(f"Total unique cats discovered: {len(unique_cats)}")
        
        # Save the discovered URLs
        with open('discovered_cat_urls.json', 'w', encoding='utf-8') as f:
            json.dump({
                'total_cats': len(unique_cats),
                'discovered_at': time.strftime('%Y-%m-%d %H:%M:%S'),
                'cat_urls': unique_cats
            }, f, ensure_ascii=False, indent=2)
        
        return unique_cats

def main():
    discovery = CatDiscovery()
    
    print("🔍 Cat Discovery Script")
    print("This script will find many more cat profile URLs")
    print("=" * 50)
    
    try:
        cat_urls = discovery.discover_all_cats()
        print(f"\n🎉 Discovery completed!")
        print(f"Total unique cat URLs found: {len(cat_urls)}")
        print("Results saved to 'discovered_cat_urls.json'")
        
        # Show first 10 URLs as examples
        print("\nFirst 10 discovered URLs:")
        for i, url in enumerate(cat_urls[:10]):
            print(f"{i+1}. {url}")
        
        if len(cat_urls) > 10:
            print(f"... and {len(cat_urls) - 10} more")
        
    except KeyboardInterrupt:
        print("\n⚠️ Discovery interrupted by user.")
    except Exception as e:
        logging.error(f"Discovery failed: {e}")
        print(f"❌ Discovery failed: {e}")

if __name__ == "__main__":
    main() 