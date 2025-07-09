#!/usr/bin/env python3
"""
Pagination Tester
Thoroughly tests pagination to find additional pages and cats
"""

import requests
from bs4 import BeautifulSoup
import re
import time
import random
from urllib.parse import urljoin
import json
import logging
import config

logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class PaginationTester:
    def __init__(self):
        self.base_url = config.BASE_URL
        self.session = requests.Session()
        self.session.headers.update(config.HEADERS)
        self.delay_min = 1.0
        self.delay_max = 2.0
        self.all_cat_urls = set()
        
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
        return list(set(cat_urls))
    
    def test_pagination_patterns(self):
        """Test various pagination patterns"""
        patterns = [
            # Standard pagination
            "/foster/cat/?p={}",
            "/foster/cat/?page={}",
            "/foster/cat/?offset={}",
            "/foster/cat/?start={}",
            "/foster/cat/?limit=30&offset={}",
            "/foster/cat/?per_page=30&page={}",
            
            # AJAX pagination
            "/foster/cat/contents/?p={}",
            "/foster/cat/ajax/?p={}",
            "/foster/cat/load/?p={}",
            
            # Alternative patterns
            "/foster/?p={}",
            "/foster/?page={}",
            "/foster/?offset={}",
            
            # With different parameters
            "/foster/cat/?p={}&sort=newest",
            "/foster/cat/?p={}&sort=oldest",
            "/foster/cat/?p={}&area=all",
            "/foster/cat/?p={}&age=all",
            "/foster/cat/?p={}&sex=all",
        ]
        
        results = []
        max_pages_to_test = 20  # Test up to 20 pages
        
        for pattern in patterns:
            logging.info(f"Testing pagination pattern: {pattern}")
            pattern_results = []
            
            for page in range(1, max_pages_to_test + 1):
                url = self.base_url + pattern.format(page)
                logging.info(f"  Testing page {page}: {url}")
                
                response = self.get_page(url)
                if not response:
                    logging.warning(f"    Failed to access page {page}")
                    break
                
                soup = BeautifulSoup(response.content, 'html.parser')
                cat_urls = self.find_cat_profiles(soup)
                
                if cat_urls:
                    logging.info(f"    ✓ Page {page}: {len(cat_urls)} cats found")
                    pattern_results.append({
                        'page': page,
                        'url': url,
                        'cat_count': len(cat_urls),
                        'cat_urls': cat_urls
                    })
                    self.all_cat_urls.update(cat_urls)
                else:
                    logging.info(f"    ✗ Page {page}: No cats found")
                    # If no cats found, this might be the end
                    if page > 1:  # Don't break on page 1, might be empty
                        break
                
                time.sleep(random.uniform(self.delay_min, self.delay_max))
            
            if pattern_results:
                results.append({
                    'pattern': pattern,
                    'pages_found': len(pattern_results),
                    'total_cats': sum(r['cat_count'] for r in pattern_results),
                    'pages': pattern_results
                })
                logging.info(f"  Pattern {pattern}: {len(pattern_results)} pages, {sum(r['cat_count'] for r in pattern_results)} total cats")
            else:
                logging.info(f"  Pattern {pattern}: No pages with cats found")
        
        return results
    
    def test_date_based_pagination(self):
        """Test if there are date-based or time-based listings"""
        logging.info("Testing date-based pagination...")
        
        # Test different date ranges
        date_patterns = [
            "/foster/cat/?date=2024",
            "/foster/cat/?date=2023", 
            "/foster/cat/?date=2022",
            "/foster/cat/?year=2024",
            "/foster/cat/?year=2023",
            "/foster/cat/?year=2022",
            "/foster/cat/?month=01",
            "/foster/cat/?month=02",
            "/foster/cat/?month=03",
        ]
        
        results = []
        for pattern in date_patterns:
            url = self.base_url + pattern
            logging.info(f"Testing date pattern: {pattern}")
            
            response = self.get_page(url)
            if response:
                soup = BeautifulSoup(response.content, 'html.parser')
                cat_urls = self.find_cat_profiles(soup)
                
                if cat_urls:
                    logging.info(f"✓ Date pattern {pattern}: {len(cat_urls)} cats found")
                    results.append({
                        'pattern': pattern,
                        'url': url,
                        'cat_count': len(cat_urls),
                        'cat_urls': cat_urls
                    })
                    self.all_cat_urls.update(cat_urls)
                else:
                    logging.info(f"✗ Date pattern {pattern}: No cats found")
            else:
                logging.warning(f"✗ Date pattern {pattern}: Failed to access")
            
            time.sleep(random.uniform(self.delay_min, self.delay_max))
        
        return results
    
    def test_search_parameters(self):
        """Test various search parameters that might reveal more cats"""
        logging.info("Testing search parameters...")
        
        # Test different search combinations
        search_params = [
            "?status=available",
            "?status=waiting", 
            "?status=adopted",
            "?type=cat",
            "?type=all",
            "?area=all",
            "?age=all",
            "?sex=all",
            "?pattern=all",
            "?sort=newest",
            "?sort=oldest",
            "?sort=name",
            "?view=all",
            "?show=all",
            "?filter=all",
        ]
        
        results = []
        for param in search_params:
            url = self.base_url + "/foster/cat/" + param
            logging.info(f"Testing search parameter: {param}")
            
            response = self.get_page(url)
            if response:
                soup = BeautifulSoup(response.content, 'html.parser')
                cat_urls = self.find_cat_profiles(soup)
                
                if cat_urls:
                    logging.info(f"✓ Search param {param}: {len(cat_urls)} cats found")
                    results.append({
                        'param': param,
                        'url': url,
                        'cat_count': len(cat_urls),
                        'cat_urls': cat_urls
                    })
                    self.all_cat_urls.update(cat_urls)
                else:
                    logging.info(f"✗ Search param {param}: No cats found")
            else:
                logging.warning(f"✗ Search param {param}: Failed to access")
            
            time.sleep(random.uniform(self.delay_min, self.delay_max))
        
        return results
    
    def run_tests(self):
        """Run all pagination tests"""
        logging.info("Starting comprehensive pagination testing...")
        
        # Test pagination patterns
        pagination_results = self.test_pagination_patterns()
        
        # Test date-based patterns
        date_results = self.test_date_based_pagination()
        
        # Test search parameters
        search_results = self.test_search_parameters()
        
        # Compile results
        all_results = {
            'pagination_results': pagination_results,
            'date_results': date_results,
            'search_results': search_results,
            'total_unique_cats': len(self.all_cat_urls),
            'all_cat_urls': list(self.all_cat_urls)
        }
        
        # Save results
        with open('pagination_test_results.json', 'w', encoding='utf-8') as f:
            json.dump(all_results, f, indent=2, ensure_ascii=False)
        
        # Print summary
        print("\n" + "="*60)
        print("PAGINATION TEST RESULTS")
        print("="*60)
        
        print(f"\n🐱 Total unique cats found: {len(self.all_cat_urls)}")
        
        print(f"\n📄 Pagination patterns tested: {len(pagination_results)}")
        for result in pagination_results:
            print(f"  • {result['pattern']}: {result['pages_found']} pages, {result['total_cats']} cats")
        
        print(f"\n📅 Date patterns tested: {len(date_results)}")
        for result in date_results:
            print(f"  • {result['pattern']}: {result['cat_count']} cats")
        
        print(f"\n🔍 Search parameters tested: {len(search_results)}")
        for result in search_results:
            print(f"  • {result['param']}: {result['cat_count']} cats")
        
        print(f"\n💾 Results saved to: pagination_test_results.json")
        print("="*60)
        
        return all_results

def main():
    tester = PaginationTester()
    tester.run_tests()

if __name__ == "__main__":
    main() 