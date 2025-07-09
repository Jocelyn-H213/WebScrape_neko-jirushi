#!/usr/bin/env python3
"""
Comprehensive Site Explorer
Investigates all possible sections and endpoints for cat listings
"""

import requests
from bs4 import BeautifulSoup
import re
import time
import random
from urllib.parse import urljoin, urlparse
import json
import logging
import config

logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class SiteExplorer:
    def __init__(self):
        self.base_url = config.BASE_URL
        self.session = requests.Session()
        self.session.headers.update(config.HEADERS)
        self.delay_min = 1.0
        self.delay_max = 2.0
        self.discovered_urls = set()
        self.cat_listings = []
        
    def get_page(self, url, retries=3):
        for attempt in range(retries):
            try:
                response = self.session.get(url, timeout=config.TIMEOUT)
                response.raise_for_status()
                return response
            except Exception as e:
                logging.warning(f"Attempt {attempt + 1} failed for {url}: {e}")
                if attempt == retries - 1:
                    return None
                time.sleep(random.uniform(self.delay_min, self.delay_max))
        return None
    
    def find_cat_profiles(self, soup):
        """Find individual cat profile URLs from a page"""
        cat_links = soup.find_all('a', href=re.compile(r'/foster/\d+/'))
        cat_urls = []
        for link in cat_links:
            href = link.get('href', '')
            if href:
                full_url = urljoin(self.base_url, href)
                cat_urls.append(full_url)
        return list(set(cat_urls))  # Remove duplicates
    
    def explore_main_page(self):
        """Explore the main page to find navigation links"""
        logging.info("Exploring main page...")
        response = self.get_page(self.base_url)
        if not response:
            return []
        
        soup = BeautifulSoup(response.content, 'html.parser')
        links = soup.find_all('a', href=True)
        
        discovered_urls = []
        for link in links:
            href = link.get('href', '')
            if href:
                full_url = urljoin(self.base_url, href)
                if full_url.startswith(self.base_url):
                    discovered_urls.append(full_url)
        
        return list(set(discovered_urls))
    
    def explore_section(self, url, section_name):
        """Explore a specific section for cat listings"""
        logging.info(f"Exploring section: {section_name} - {url}")
        
        response = self.get_page(url)
        if not response:
            logging.warning(f"Failed to access {url}")
            return []
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find cat profiles on this page
        cat_urls = self.find_cat_profiles(soup)
        if cat_urls:
            logging.info(f"Found {len(cat_urls)} cat profiles in {section_name}")
            self.cat_listings.extend([(url, section_name, cat_url) for cat_url in cat_urls])
        
        # Find pagination links
        pagination_links = []
        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            if 'p=' in href or 'page=' in href:
                full_url = urljoin(self.base_url, href)
                if full_url.startswith(self.base_url):
                    pagination_links.append(full_url)
        
        # Find other potential listing links
        listing_links = []
        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            if any(keyword in href.lower() for keyword in ['foster', 'cat', 'adopt', 'list', 'search']):
                full_url = urljoin(self.base_url, href)
                if full_url.startswith(self.base_url):
                    listing_links.append(full_url)
        
        return {
            'section': section_name,
            'url': url,
            'cat_profiles': len(cat_urls),
            'pagination_links': list(set(pagination_links)),
            'listing_links': list(set(listing_links))
        }
    
    def test_url_patterns(self):
        """Test various URL patterns that might contain cat listings"""
        patterns_to_test = [
            # Foster variations
            "/foster/",
            "/foster/cat/",
            "/foster/cats/",
            "/foster/dog/",
            "/foster/other/",
            "/foster/adopt/",
            "/foster/adopted/",
            "/foster/alumni/",
            "/foster/history/",
            "/foster/archive/",
            
            # Adoption variations
            "/adopt/",
            "/adopt/cat/",
            "/adopt/cats/",
            "/adopted/",
            "/adopted/cat/",
            "/adopted/cats/",
            
            # General animal sections
            "/animals/",
            "/animals/cat/",
            "/animals/cats/",
            "/pets/",
            "/pets/cat/",
            "/pets/cats/",
            
            # Search and listing variations
            "/search/",
            "/search/cat/",
            "/list/",
            "/list/cat/",
            "/listing/",
            "/listing/cat/",
            
            # Archive and history
            "/archive/",
            "/archive/cat/",
            "/history/",
            "/history/cat/",
            "/past/",
            "/past/cat/",
            
            # Regional variations
            "/tokyo/",
            "/tokyo/cat/",
            "/osaka/",
            "/osaka/cat/",
            "/japan/",
            "/japan/cat/",
            
            # Status variations
            "/available/",
            "/available/cat/",
            "/waiting/",
            "/waiting/cat/",
            "/new/",
            "/new/cat/",
            "/recent/",
            "/recent/cat/",
            
            # AJAX endpoints
            "/foster/cat/contents/",
            "/foster/cat/ajax/",
            "/foster/cat/load/",
            "/api/foster/",
            "/api/cat/",
            
            # Pagination variations
            "/foster/cat/?p=1",
            "/foster/cat/?page=1",
            "/foster/cat/?offset=0",
            "/foster/cat/?start=0",
        ]
        
        results = []
        for pattern in patterns_to_test:
            url = self.base_url + pattern
            logging.info(f"Testing pattern: {pattern}")
            
            response = self.get_page(url)
            if response:
                soup = BeautifulSoup(response.content, 'html.parser')
                cat_urls = self.find_cat_profiles(soup)
                
                if cat_urls or 'foster' in pattern.lower() or 'cat' in pattern.lower():
                    results.append({
                        'pattern': pattern,
                        'url': url,
                        'status': 'success',
                        'cat_profiles': len(cat_urls),
                        'sample_cats': cat_urls[:5] if cat_urls else []
                    })
                    logging.info(f"✓ Pattern {pattern}: {len(cat_urls)} cats found")
                else:
                    results.append({
                        'pattern': pattern,
                        'url': url,
                        'status': 'no_cats',
                        'cat_profiles': 0
                    })
            else:
                results.append({
                    'pattern': pattern,
                    'url': url,
                    'status': 'failed',
                    'cat_profiles': 0
                })
                logging.warning(f"✗ Pattern {pattern}: Failed to access")
            
            time.sleep(random.uniform(self.delay_min, self.delay_max))
        
        return results
    
    def explore(self):
        """Main exploration method"""
        logging.info("Starting comprehensive site exploration...")
        
        # Step 1: Explore main page
        main_page_links = self.explore_main_page()
        logging.info(f"Found {len(main_page_links)} links on main page")
        
        # Step 2: Test URL patterns
        pattern_results = self.test_url_patterns()
        
        # Step 3: Explore sections that might have cats
        section_results = []
        sections_to_explore = [
            (self.base_url + "/foster/", "Foster Main"),
            (self.base_url + "/foster/cat/", "Foster Cats"),
            (self.base_url + "/", "Home Page"),
        ]
        
        for url, name in sections_to_explore:
            result = self.explore_section(url, name)
            section_results.append(result)
            time.sleep(random.uniform(self.delay_min, self.delay_max))
        
        # Compile results
        exploration_results = {
            'timestamp': time.time(),
            'main_page_links': main_page_links,
            'pattern_results': pattern_results,
            'section_results': section_results,
            'total_cat_listings_found': len(self.cat_listings),
            'unique_cat_urls': list(set([cat[2] for cat in self.cat_listings]))
        }
        
        # Save results
        with open('site_exploration_results.json', 'w', encoding='utf-8') as f:
            json.dump(exploration_results, f, indent=2, ensure_ascii=False)
        
        # Print summary
        print("\n" + "="*60)
        print("SITE EXPLORATION RESULTS")
        print("="*60)
        
        print(f"\n📊 Total cat listings found: {len(self.cat_listings)}")
        print(f"🐱 Unique cat URLs: {len(exploration_results['unique_cat_urls'])}")
        
        print(f"\n🔍 URL Patterns Tested: {len(pattern_results)}")
        successful_patterns = [p for p in pattern_results if p['status'] == 'success' and p['cat_profiles'] > 0]
        print(f"✅ Successful patterns with cats: {len(successful_patterns)}")
        
        if successful_patterns:
            print("\n🎯 Best patterns found:")
            for pattern in successful_patterns[:10]:  # Show top 10
                print(f"  • {pattern['pattern']}: {pattern['cat_profiles']} cats")
        
        print(f"\n📁 Sections explored: {len(section_results)}")
        for section in section_results:
            if section['cat_profiles'] > 0:
                print(f"  • {section['section']}: {section['cat_profiles']} cats")
        
        print(f"\n💾 Results saved to: site_exploration_results.json")
        print("="*60)
        
        return exploration_results

def main():
    explorer = SiteExplorer()
    explorer.explore()

if __name__ == "__main__":
    main() 