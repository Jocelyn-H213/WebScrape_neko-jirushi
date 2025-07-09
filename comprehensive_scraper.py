#!/usr/bin/env python3
"""
Comprehensive Cat Scraper for neko-jirushi.com
Uses the discovered API endpoint to scrape all available cats
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
        logging.FileHandler('comprehensive_scraper.log'),
        logging.StreamHandler()
    ]
)

class ComprehensiveCatScraper:
    def __init__(self, base_url="https://neko-jirushi.com"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'X-Requested-With': 'XMLHttpRequest',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Referer': 'https://neko-jirushi.com/foster/cat/contents/?p=1'
        })
        
        # Create directories
        self.data_dir = Path("scraped_cats")
        self.data_dir.mkdir(exist_ok=True)
        
        # Progress tracking
        self.progress_file = "comprehensive_scraper_progress.json"
        self.discovered_cats_file = "comprehensive_discovered_cats.json"
        self.load_progress()
        
        # Statistics
        self.stats = {
            'total_cats_found': 0,
            'total_images_downloaded': 0,
            'pages_scraped': 0,
            'errors': 0,
            'start_time': datetime.now().isoformat()
        }

    def load_progress(self):
        """Load progress from file"""
        if os.path.exists(self.progress_file):
            with open(self.progress_file, 'r', encoding='utf-8') as f:
                loaded_progress = json.load(f)
            # Convert lists back to sets
            self.progress = {
                'last_page': loaded_progress.get('last_page', 0),
                'scraped_cats': set(loaded_progress.get('scraped_cats', [])),
                'failed_pages': set(loaded_progress.get('failed_pages', []))
            }
            logging.info(f"Loaded progress: {self.progress}")
        else:
            self.progress = {
                'last_page': 0,
                'scraped_cats': set(),
                'failed_pages': set()
            }
            logging.info("Starting fresh scraping session")

    def save_progress(self):
        """Save progress to file"""
        # Convert sets to lists for JSON serialization
        progress_to_save = {
            'last_page': self.progress['last_page'],
            'scraped_cats': list(self.progress['scraped_cats']),
            'failed_pages': list(self.progress['failed_pages'])
        }
        
        with open(self.progress_file, 'w', encoding='utf-8') as f:
            json.dump(progress_to_save, f, indent=2, ensure_ascii=False)
        
        # Save discovered cats
        with open(self.discovered_cats_file, 'w', encoding='utf-8') as f:
            json.dump(self.discovered_cats, f, indent=2, ensure_ascii=False)

    def get_api_page(self, page_num, retries=3):
        """Get cat data from API endpoint"""
        api_url = f"{self.base_url}/foster/ajax/ajax_getFosterList.php"
        
        # Prepare the search condition
        search_cond = {
            'params': 'contents/',
            'p': str(page_num),
            'page': page_num - 1,  # API uses 0-based indexing
            'target_pref_id': '',
            'age_limit': '',
            'sex': '',
            'vaccine': '',
            'spay_and_neuter': '',
            'pattern_no': '',
            'status_id': '',
            'city_id': '',
            'city_name': '',
            'keyword': '',
            'user_id': '',
            'recruiter_pref': 0
        }
        
        data = {
            'search_cond': json.dumps(search_cond),
            'spMode': 0
        }
        
        for attempt in range(retries):
            try:
                response = self.session.post(api_url, data=data, timeout=30)
                response.raise_for_status()
                return response.json()
            except requests.RequestException as e:
                logging.warning(f"Attempt {attempt + 1} failed for page {page_num}: {e}")
                if attempt < retries - 1:
                    time.sleep(random.uniform(2, 5))
                else:
                    logging.error(f"Failed to get page {page_num} after {retries} attempts")
                    return None
            except json.JSONDecodeError as e:
                logging.error(f"JSON decode error for page {page_num}: {e}")
                return None

    def scrape_cat_profile(self, cat_info):
        """Scrape individual cat profile for images"""
        if str(cat_info['cat_id']) in self.progress['scraped_cats']:
            logging.info(f"Cat {cat_info['cat_id']} already scraped, skipping")
            return
        
        logging.info(f"Scraping cat profile: {cat_info['catch_copy']} ({cat_info['cat_id']})")
        
        # Construct the cat URL
        cat_url = urljoin(self.base_url, cat_info['url'])
        
        response = self.session.get(cat_url, timeout=30)
        if not response:
            return
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find all images on the page
        images = []
        
        # Look for images in various containers
        image_selectors = [
            'img[src*="cat"]',
            'img[src*="foster"]',
            '.cat-image img',
            '.profile-image img',
            '.gallery img',
            '.photo img',
            'img[src*=".jpg"]',
            'img[src*=".jpeg"]',
            'img[src*=".png"]',
            'img[src*=".webp"]'
        ]
        
        for selector in image_selectors:
            found_images = soup.select(selector)
            for img in found_images:
                src = img.get('src') or img.get('data-src')
                if src:
                    if not src.startswith('http'):
                        src = urljoin(self.base_url, src)
                    
                    # Filter out small images, icons, and non-cat images
                    if (src not in [img['url'] for img in images] and
                        ('cat' in src.lower() or 'foster' in src.lower() or
                         any(ext in src.lower() for ext in ['.jpg', '.jpeg', '.png', '.webp']))):
                        
                        images.append({
                            'url': src,
                            'alt': img.get('alt', ''),
                            'title': img.get('title', '')
                        })
        
        # Also add the main image from the API response
        if cat_info.get('image_1'):
            main_image_url = urljoin(self.base_url, cat_info['image_1'])
            if main_image_url not in [img['url'] for img in images]:
                images.insert(0, {
                    'url': main_image_url,
                    'alt': cat_info.get('catch_copy', ''),
                    'title': cat_info.get('catch_copy', '')
                })
        
        if images:
            # Create cat directory
            cat_dir = self.data_dir / f"cat_{cat_info['cat_id']}"
            cat_dir.mkdir(exist_ok=True)
            
            # Save cat info
            cat_data = {
                'id': cat_info['cat_id'],
                'name': cat_info.get('cat_name', ''),
                'catch_copy': cat_info.get('catch_copy', ''),
                'url': cat_url,
                'api_data': cat_info,
                'images': images,
                'scraped_at': datetime.now().isoformat()
            }
            
            with open(cat_dir / 'info.json', 'w', encoding='utf-8') as f:
                json.dump(cat_data, f, indent=2, ensure_ascii=False)
            
            # Download images
            downloaded_count = 0
            for i, img in enumerate(images):
                try:
                    img_response = self.session.get(img['url'], timeout=30)
                    img_response.raise_for_status()
                    
                    # Determine file extension
                    content_type = img_response.headers.get('content-type', '')
                    if 'jpeg' in content_type or 'jpg' in content_type:
                        ext = '.jpg'
                    elif 'png' in content_type:
                        ext = '.png'
                    elif 'webp' in content_type:
                        ext = '.webp'
                    else:
                        ext = '.jpg'  # default
                    
                    img_filename = f"image_{i+1}{ext}"
                    img_path = cat_dir / img_filename
                    
                    with open(img_path, 'wb') as f:
                        f.write(img_response.content)
                    
                    downloaded_count += 1
                    self.stats['total_images_downloaded'] += 1
                    
                    # Random delay between image downloads
                    time.sleep(random.uniform(0.5, 1.5))
                    
                except Exception as e:
                    logging.error(f"Failed to download image {img['url']}: {e}")
            
            logging.info(f"Downloaded {downloaded_count} images for cat {cat_info['cat_id']}")
            self.progress['scraped_cats'].add(str(cat_info['cat_id']))
            self.stats['total_cats_found'] += 1
            
        else:
            logging.warning(f"No images found for cat {cat_info['cat_id']}")

    def scrape_api_page(self, page_num):
        """Scrape a single API page"""
        logging.info(f"Scraping API page {page_num}")
        
        data = self.get_api_page(page_num)
        if not data:
            self.progress['failed_pages'].add(page_num)
            self.stats['errors'] += 1
            return []
        
        foster_list = data.get('foster_list', [])
        page_info = data.get('page', {})
        
        logging.info(f"Found {len(foster_list)} cats on page {page_num}")
        logging.info(f"Page info: {page_info.get('now', 'N/A')}/{page_info.get('all_page', 'N/A')} (Total: {page_info.get('rows', 'N/A')} cats)")
        
        self.stats['pages_scraped'] += 1
        
        return foster_list

    def run_comprehensive_scrape(self, max_pages=None, target_cats=1000):
        """Run comprehensive scraping of all available cats"""
        logging.info(f"Starting comprehensive scraping - targeting {target_cats} cats")
        
        # Initialize discovered cats
        if os.path.exists(self.discovered_cats_file):
            with open(self.discovered_cats_file, 'r', encoding='utf-8') as f:
                self.discovered_cats = json.load(f)
        else:
            self.discovered_cats = {}
        
        start_page = self.progress['last_page'] + 1
        
        # If no max_pages specified, start with a reasonable number
        if max_pages is None:
            max_pages = min(1000, (target_cats // 22) + 10)  # 22 cats per page
        
        for page_num in range(start_page, start_page + max_pages):
            try:
                cats_on_page = self.scrape_api_page(page_num)
                
                if not cats_on_page:
                    logging.warning(f"No cats found on page {page_num}, stopping")
                    break
                
                # Scrape each cat's profile
                for cat_info in cats_on_page:
                    try:
                        self.scrape_cat_profile(cat_info)
                    except Exception as e:
                        logging.error(f"Error scraping cat {cat_info.get('cat_id', 'unknown')}: {e}")
                        continue
                    
                    # Save progress periodically
                    if len(self.progress['scraped_cats']) % 10 == 0:
                        self.save_progress()
                        self.print_stats()
                
                # Save progress after each page
                self.save_progress()
                
                self.progress['last_page'] = page_num
                self.save_progress()
                
                # Random delay between pages
                delay = random.uniform(3, 7)
                logging.info(f"Waiting {delay:.1f} seconds before next page...")
                time.sleep(delay)
                
                # Check if we've reached our target
                if self.stats['total_cats_found'] >= target_cats:
                    logging.info(f"Reached target of {target_cats} cats, stopping")
                    break
                
            except KeyboardInterrupt:
                logging.info("Scraping interrupted by user")
                break
            except Exception as e:
                logging.error(f"Error on page {page_num}: {e}")
                self.stats['errors'] += 1
                continue
        
        self.save_progress()
        self.print_final_stats()

    def print_stats(self):
        """Print current statistics"""
        logging.info(f"=== Current Stats ===")
        logging.info(f"Total cats found: {self.stats['total_cats_found']}")
        logging.info(f"Total images downloaded: {self.stats['total_images_downloaded']}")
        logging.info(f"Pages scraped: {self.stats['pages_scraped']}")
        logging.info(f"Errors: {self.stats['errors']}")
        logging.info(f"Scraped cats: {len(self.progress['scraped_cats'])}")
        logging.info(f"Discovered cats: {len(self.discovered_cats)}")

    def print_final_stats(self):
        """Print final statistics"""
        end_time = datetime.now()
        start_time = datetime.fromisoformat(self.stats['start_time'])
        duration = end_time - start_time
        
        logging.info(f"\n=== FINAL STATISTICS ===")
        logging.info(f"Scraping completed in: {duration}")
        logging.info(f"Total cats found: {self.stats['total_cats_found']}")
        logging.info(f"Total images downloaded: {self.stats['total_images_downloaded']}")
        logging.info(f"Pages scraped: {self.stats['pages_scraped']}")
        logging.info(f"Errors encountered: {self.stats['errors']}")
        logging.info(f"Unique cats discovered: {len(self.discovered_cats)}")
        logging.info(f"Successfully scraped cats: {len(self.progress['scraped_cats'])}")
        logging.info(f"Failed pages: {len(self.progress['failed_pages'])}")

def main():
    scraper = ComprehensiveCatScraper()
    
    try:
        # Start with a reasonable target - we can always increase it
        scraper.run_comprehensive_scrape(target_cats=1000, max_pages=50)
    except KeyboardInterrupt:
        logging.info("Scraping interrupted by user")
        scraper.save_progress()
        scraper.print_final_stats()
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        scraper.save_progress()

if __name__ == "__main__":
    main() 