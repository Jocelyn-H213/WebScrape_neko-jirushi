#!/usr/bin/env python3
"""
Smart Cat Discovery Scraper
Finds new cats by exploring individual cat profile pages and related links
"""

import os
import json
import time
import random
import requests
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import logging
from datetime import datetime
import re
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('smart_discovery.log'),
        logging.StreamHandler()
    ]
)

class SmartCatDiscovery:
    def __init__(self, base_url="https://neko-jirushi.com", target_cats=100):
        self.base_url = base_url
        self.target_cats = target_cats
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        
        # Progress tracking
        self.progress_file = 'smart_discovery_progress.json'
        self.scraped_cats = set()
        self.discovered_urls = set()
        self.failed_urls = set()
        
        # Create directories
        self.output_dir = Path('scraped_cats')
        self.output_dir.mkdir(exist_ok=True)
        
        self.load_progress()
    
    def load_progress(self):
        """Load progress from file"""
        if os.path.exists(self.progress_file):
            with open(self.progress_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.scraped_cats = set(data.get('scraped_cats', []))
            self.discovered_urls = set(data.get('discovered_urls', []))
            self.failed_urls = set(data.get('failed_urls', []))
            logging.info(f"Loaded progress: {len(self.scraped_cats)} cats scraped, {len(self.discovered_urls)} URLs discovered")
        else:
            logging.info("Starting fresh discovery session")
    
    def save_progress(self):
        """Save progress to file"""
        data = {
            'scraped_cats': list(self.scraped_cats),
            'discovered_urls': list(self.discovered_urls),
            'failed_urls': list(self.failed_urls),
            'timestamp': datetime.now().isoformat()
        }
        with open(self.progress_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def get_existing_cat_ids(self):
        """Get list of already scraped cat IDs"""
        existing_ids = set()
        if self.output_dir.exists():
            for cat_dir in self.output_dir.iterdir():
                if cat_dir.is_dir() and cat_dir.name.startswith('cat_'):
                    cat_id = cat_dir.name.replace('cat_', '')
                    existing_ids.add(cat_id)
        return existing_ids
    
    def discover_new_cats(self):
        """Discover new cats using various methods"""
        logging.info("Starting smart cat discovery...")
        
        # Method 1: Use the API to get the first batch of cats
        api_cats = self.get_api_cats()
        for cat_info in api_cats:
            cat_id = str(cat_info.get('cat_id'))
            if cat_id not in self.scraped_cats:
                self.discovered_urls.add(f"/foster/{cat_id}/")
        
        # Method 2: Explore existing cat pages for related cats
        existing_ids = self.get_existing_cat_ids()
        for cat_id in list(existing_ids)[:10]:  # Check first 10 existing cats
            self.explore_cat_page_for_links(cat_id)
        
        # Method 3: Try different cat ID ranges
        self.try_cat_id_ranges()
        
        logging.info(f"Discovery complete. Found {len(self.discovered_urls)} potential cat URLs")
    
    def get_api_cats(self):
        """Get cats from the API (even if pagination is broken)"""
        api_url = self.base_url + "/foster/ajax/ajax_getFosterList.php"
        
        headers = {
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Language': 'en-US,en;q=0.5',
            'X-Requested-With': 'XMLHttpRequest',
            'Referer': 'https://neko-jirushi.com/foster/cat/contents/?p=1',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'
        }
        
        data = {'p': '1', 'limit': '22'}
        
        try:
            response = self.session.post(api_url, data=data, headers=headers)
            if response.status_code == 200:
                result = response.json()
                return result.get('foster_list', [])
        except Exception as e:
            logging.error(f"Error getting API cats: {e}")
        
        return []
    
    def explore_cat_page_for_links(self, cat_id):
        """Explore a cat page to find links to other cats"""
        url = f"{self.base_url}/foster/{cat_id}/"
        
        try:
            response = self.session.get(url, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Look for links to other foster pages
                links = soup.find_all('a', href=re.compile(r'/foster/\d+/'))
                for link in links:
                    href = link.get('href')
                    if href and href not in self.discovered_urls:
                        self.discovered_urls.add(href)
                        logging.info(f"Found new cat link: {href}")
                
                # Look for "related cats" or "similar cats" sections
                related_sections = soup.find_all(['div', 'section'], class_=re.compile(r'related|similar|recommend'))
                for section in related_sections:
                    links = section.find_all('a', href=re.compile(r'/foster/\d+/'))
                    for link in links:
                        href = link.get('href')
                        if href and href not in self.discovered_urls:
                            self.discovered_urls.add(href)
                            logging.info(f"Found related cat: {href}")
        
        except Exception as e:
            logging.error(f"Error exploring cat {cat_id}: {e}")
    
    def try_cat_id_ranges(self):
        """Try different cat ID ranges to find new cats"""
        # Try some common ID ranges
        ranges_to_try = [
            (226600, 226700),  # Around our existing cats
            (226500, 226600),  # Lower range
            (226700, 226800),  # Higher range
            (226400, 226500),  # Even lower
            (226800, 226900),  # Even higher
        ]
        
        for start_id, end_id in ranges_to_try:
            for cat_id in range(start_id, end_id, 5):  # Skip every 5 to be efficient
                url = f"{self.base_url}/foster/{cat_id}/"
                if url not in self.discovered_urls and url not in self.failed_urls:
                    self.discovered_urls.add(url)
    
    def scrape_cat_profile(self, url):
        """Scrape a single cat profile"""
        try:
            response = self.session.get(url, timeout=10)
            if response.status_code != 200:
                self.failed_urls.add(url)
                return False
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract cat ID from URL
            cat_id_match = re.search(r'/foster/(\d+)/', url)
            if not cat_id_match:
                self.failed_urls.add(url)
                return False
            
            cat_id = cat_id_match.group(1)
            
            if cat_id in self.scraped_cats:
                return False
            
            # Extract cat information
            cat_info = self.extract_cat_info(soup, cat_id)
            if not cat_info:
                self.failed_urls.add(url)
                return False
            
            # Download images
            images_downloaded = self.download_cat_images(cat_info, cat_id)
            
            # Save cat info
            self.save_cat_info(cat_info, cat_id)
            
            self.scraped_cats.add(cat_id)
            logging.info(f"Successfully scraped cat {cat_id} with {images_downloaded} images")
            
            return True
            
        except Exception as e:
            logging.error(f"Error scraping {url}: {e}")
            self.failed_urls.add(url)
            return False
    
    def extract_cat_info(self, soup, cat_id):
        """Extract cat information from the page"""
        try:
            cat_info = {
                'cat_id': cat_id,
                'url': f"{self.base_url}/foster/{cat_id}/",
                'scraped_at': datetime.now().isoformat()
            }
            
            # Extract name
            name_elem = soup.find(['h1', 'h2', 'h3'], class_=re.compile(r'title|name'))
            if name_elem:
                cat_info['name'] = name_elem.get_text(strip=True)
            
            # Extract description
            desc_elem = soup.find(['div', 'p'], class_=re.compile(r'description|desc|content'))
            if desc_elem:
                cat_info['description'] = desc_elem.get_text(strip=True)
            
            # Extract other details
            details = soup.find_all(['div', 'span'], class_=re.compile(r'detail|info|attribute'))
            for detail in details:
                text = detail.get_text(strip=True)
                if ':' in text:
                    key, value = text.split(':', 1)
                    cat_info[key.strip().lower()] = value.strip()
            
            return cat_info
            
        except Exception as e:
            logging.error(f"Error extracting cat info: {e}")
            return None
    
    def download_cat_images(self, cat_info, cat_id):
        """Download images for a cat"""
        cat_dir = self.output_dir / f"cat_{cat_id}"
        cat_dir.mkdir(exist_ok=True)
        
        images_downloaded = 0
        
        # Find all images on the page
        soup = BeautifulSoup(requests.get(cat_info['url']).content, 'html.parser')
        images = soup.find_all('img', src=re.compile(r'\.(jpg|jpeg|png|gif)'))
        
        for i, img in enumerate(images):
            src = img.get('src')
            if src:
                if not src.startswith('http'):
                    src = urljoin(self.base_url, src)
                
                try:
                    response = self.session.get(src, timeout=10)
                    if response.status_code == 200:
                        ext = src.split('.')[-1].lower()
                        if ext not in ['jpg', 'jpeg', 'png', 'gif']:
                            ext = 'jpg'
                        
                        filename = f"image_{i+1:03d}.{ext}"
                        filepath = cat_dir / filename
                        
                        with open(filepath, 'wb') as f:
                            f.write(response.content)
                        
                        images_downloaded += 1
                
                except Exception as e:
                    logging.error(f"Error downloading image {src}: {e}")
        
        return images_downloaded
    
    def save_cat_info(self, cat_info, cat_id):
        """Save cat information to JSON file"""
        cat_dir = self.output_dir / f"cat_{cat_id}"
        cat_dir.mkdir(exist_ok=True)
        
        info_file = cat_dir / 'info.json'
        with open(info_file, 'w', encoding='utf-8') as f:
            json.dump(cat_info, f, indent=2, ensure_ascii=False)
    
    def run(self):
        """Main execution method"""
        logging.info(f"Starting smart cat discovery. Target: {self.target_cats} cats")
        
        # Discover new cats
        self.discover_new_cats()
        
        # Scrape discovered cats
        for url in list(self.discovered_urls):
            if len(self.scraped_cats) >= self.target_cats:
                break
            
            if url not in self.failed_urls:
                success = self.scrape_cat_profile(url)
                if success:
                    self.save_progress()
                    
                    # Random delay
                    time.sleep(random.uniform(1, 3))
        
        # Final statistics
        logging.info(f"\n=== DISCOVERY COMPLETE ===")
        logging.info(f"Total cats scraped: {len(self.scraped_cats)}")
        logging.info(f"Total URLs discovered: {len(self.discovered_urls)}")
        logging.info(f"Failed URLs: {len(self.failed_urls)}")
        
        if len(self.scraped_cats) >= self.target_cats:
            logging.info(f"Target of {self.target_cats} cats reached!")
        else:
            logging.info(f"Target not reached. Need {self.target_cats - len(self.scraped_cats)} more cats.")

if __name__ == "__main__":
    discovery = SmartCatDiscovery(target_cats=100)
    discovery.run() 