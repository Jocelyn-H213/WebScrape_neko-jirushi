#!/usr/bin/env python3
"""
Smart Neko Jirushi Cat Scraper
This version explores different URL patterns and search parameters to find many more cats
"""

import requests
from bs4 import BeautifulSoup
import os
import time
import re
from urllib.parse import urljoin, urlparse, urlencode
import json
from datetime import datetime
import logging
import config

# Set up logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('smart_scraper.log'),
        logging.StreamHandler()
    ]
)

class SmartNekoJirushiScraper:
    def __init__(self, base_url=None, delay=None):
        self.base_url = base_url or config.BASE_URL
        self.delay = delay or config.DELAY_BETWEEN_REQUESTS
        self.session = requests.Session()
        self.session.headers.update(config.HEADERS)
        self.processed_cats = set()
        self.downloaded_images = 0
        self.total_cats = 0
        
        # Create output directory
        self.output_dir = "scraped_cats"
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Load progress if exists
        self.progress_file = "smart_scraper_progress.json"
        self.load_progress()
    
    def load_progress(self):
        """Load progress from file"""
        if os.path.exists(self.progress_file):
            try:
                with open(self.progress_file, 'r') as f:
                    data = json.load(f)
                    self.processed_cats = set(data.get('processed_cats', []))
                    self.downloaded_images = data.get('downloaded_images', 0)
                    self.total_cats = data.get('total_cats', 0)
                    logging.info(f"Loaded progress: {len(self.processed_cats)} cats, {self.downloaded_images} images")
            except Exception as e:
                logging.warning(f"Failed to load progress: {e}")
    
    def save_progress(self):
        """Save progress to file"""
        try:
            data = {
                'processed_cats': list(self.processed_cats),
                'downloaded_images': self.downloaded_images,
                'total_cats': self.total_cats,
                'timestamp': datetime.now().isoformat()
            }
            with open(self.progress_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logging.warning(f"Failed to save progress: {e}")
    
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
                time.sleep(self.delay)
        return None
    
    def find_cat_profiles(self, url):
        """Find individual cat profile URLs from a listing page"""
        logging.info(f"Getting cat profiles from: {url}")
        
        response = self.get_page(url)
        if not response:
            logging.warning(f"Failed to get page: {url}")
            return []
        
        soup = BeautifulSoup(response.content, 'html.parser')
        cat_links = soup.find_all('a', href=re.compile(r'/foster/\d+/'))
        
        cat_urls = []
        for link in cat_links:
            href = link.get('href', '')
            if href:
                full_url = urljoin(self.base_url, href)
                cat_id = re.search(r'/foster/(\d+)/', href)
                if cat_id:
                    cat_urls.append(full_url)
        
        # Remove duplicates while preserving order
        unique_urls = []
        seen = set()
        for url in cat_urls:
            if url not in seen:
                unique_urls.append(url)
                seen.add(url)
        
        logging.info(f"Found {len(unique_urls)} individual cat profiles")
        return unique_urls
    
    def download_cat_images(self, cat_url):
        """Download images from a cat profile page"""
        cat_id = re.search(r'/foster/(\d+)/', cat_url)
        if not cat_id:
            return 0
        
        cat_id = cat_id.group(1)
        if cat_id in self.processed_cats:
            logging.debug(f"Cat {cat_id} already processed, skipping")
            return 0
        
        logging.info(f"Processing cat {cat_id}: {cat_url}")
        
        response = self.get_page(cat_url)
        if not response:
            logging.warning(f"Failed to get cat page: {cat_url}")
            return 0
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find images using the working selectors
        images = []
        for selector in config.IMAGE_SELECTORS:
            found_images = soup.select(selector)
            images.extend(found_images)
        
        # Remove duplicates
        unique_images = []
        seen_urls = set()
        for img in images:
            src = img.get('src', '')
            if src:
                full_url = urljoin(self.base_url, src)
                if full_url not in seen_urls:
                    # Filter out navigation and UI images - more comprehensive filtering
                    if not any(exclude in full_url.lower() for exclude in [
                        'logo', 'icon', 'banner', 'header', 'nav', 'gnav', 
                        'mucho-domingo', 'headerhealth', 'headermail', 'headernotice'
                    ]) and '/img/foster/' in full_url:
                        unique_images.append(full_url)
                        seen_urls.add(full_url)
        
        if not unique_images:
            logging.warning(f"No images found for cat {cat_id}")
            return 0
        
        # Create cat directory
        cat_dir = os.path.join(self.output_dir, f"cat_{cat_id}")
        os.makedirs(cat_dir, exist_ok=True)
        
        # Download images
        downloaded = 0
        for i, img_url in enumerate(unique_images):
            try:
                img_response = self.session.get(img_url, timeout=config.TIMEOUT)
                img_response.raise_for_status()
                
                # Extract file extension
                parsed_url = urlparse(img_url)
                path = parsed_url.path
                filename = f"cat_{cat_id}_{i+1}.jpg"
                
                filepath = os.path.join(cat_dir, filename)
                with open(filepath, 'wb') as f:
                    f.write(img_response.content)
                
                downloaded += 1
                logging.debug(f"Downloaded: {filename}")
                
            except Exception as e:
                logging.warning(f"Failed to download {img_url}: {e}")
        
        if downloaded > 0:
            self.processed_cats.add(cat_id)
            self.total_cats += 1
            self.downloaded_images += downloaded
            logging.info(f"Downloaded {downloaded} images for cat {cat_id}")
        
        return downloaded
    
    def explore_different_patterns(self):
        """Explore different URL patterns to find more cats"""
        patterns_to_try = [
            # Main listing
            "/foster/cat/",
            "/foster/",
            
            # Different search parameters
            "/foster/cat/?area=all",
            "/foster/cat/?age=all", 
            "/foster/cat/?sex=all",
            "/foster/cat/?pattern=all",
            
            # Different areas
            "/foster/cat/?area=13",  # Tokyo
            "/foster/cat/?area=27",  # Osaka
            "/foster/cat/?area=23",  # Aichi
            "/foster/cat/?area=14",  # Kanagawa
            "/foster/cat/?area=11",  # Saitama
            "/foster/cat/?area=12",  # Chiba
            "/foster/cat/?area=28",  # Hyogo
            "/foster/cat/?area=15",  # Niigata
            "/foster/cat/?area=16",  # Toyama
            "/foster/cat/?area=17",  # Ishikawa
            "/foster/cat/?area=18",  # Fukui
            "/foster/cat/?area=19",  # Yamanashi
            "/foster/cat/?area=20",  # Nagano
            "/foster/cat/?area=21",  # Gifu
            "/foster/cat/?area=22",  # Shizuoka
            "/foster/cat/?area=24",  # Mie
            "/foster/cat/?area=25",  # Shiga
            "/foster/cat/?area=26",  # Kyoto
            "/foster/cat/?area=29",  # Nara
            "/foster/cat/?area=30",  # Wakayama
            "/foster/cat/?area=31",  # Tottori
            "/foster/cat/?area=32",  # Shimane
            "/foster/cat/?area=33",  # Okayama
            "/foster/cat/?area=34",  # Hiroshima
            "/foster/cat/?area=35",  # Yamaguchi
            "/foster/cat/?area=36",  # Tokushima
            "/foster/cat/?area=37",  # Kagawa
            "/foster/cat/?area=38",  # Ehime
            "/foster/cat/?area=39",  # Kochi
            "/foster/cat/?area=40",  # Fukuoka
            "/foster/cat/?area=41",  # Saga
            "/foster/cat/?area=42",  # Nagasaki
            "/foster/cat/?area=43",  # Kumamoto
            "/foster/cat/?area=44",  # Oita
            "/foster/cat/?area=45",  # Miyazaki
            "/foster/cat/?area=46",  # Kagoshima
            "/foster/cat/?area=47",  # Okinawa
            
            # Different ages
            "/foster/cat/?age=1",  # 1-2 months
            "/foster/cat/?age=2",  # 3-4 months
            "/foster/cat/?age=3",  # 5-6 months
            "/foster/cat/?age=4",  # 7-12 months
            "/foster/cat/?age=5",  # 1-2 years
            "/foster/cat/?age=6",  # 3-5 years
            "/foster/cat/?age=7",  # 6-10 years
            "/foster/cat/?age=8",  # 11+ years
            
            # Different sexes
            "/foster/cat/?sex=1",  # Male
            "/foster/cat/?sex=2",  # Female
            
            # Different patterns
            "/foster/cat/?pattern=1",  # Tabby
            "/foster/cat/?pattern=2",  # Calico
            "/foster/cat/?pattern=3",  # Tortoiseshell
            "/foster/cat/?pattern=4",  # Solid
            "/foster/cat/?pattern=5",  # Bicolor
            "/foster/cat/?pattern=6",  # Tricolor
            "/foster/cat/?pattern=7",  # Pointed
            "/foster/cat/?pattern=8",  # Other
            
            # Combinations
            "/foster/cat/?area=13&age=1",  # Tokyo, 1-2 months
            "/foster/cat/?area=13&age=2",  # Tokyo, 3-4 months
            "/foster/cat/?area=27&age=1",  # Osaka, 1-2 months
            "/foster/cat/?area=27&age=2",  # Osaka, 3-4 months
            "/foster/cat/?sex=1&age=1",    # Male, 1-2 months
            "/foster/cat/?sex=2&age=1",    # Female, 1-2 months
        ]
        
        all_cat_urls = set()
        
        for pattern in patterns_to_try:
            url = self.base_url + pattern
            logging.info(f"Exploring pattern: {pattern}")
            
            cat_urls = self.find_cat_profiles(url)
            new_urls = [url for url in cat_urls if url not in all_cat_urls]
            all_cat_urls.update(cat_urls)
            
            logging.info(f"Found {len(new_urls)} new cats from {pattern}")
            
            # Process new cats
            for cat_url in new_urls:
                self.download_cat_images(cat_url)
                self.save_progress()
                
                # Check if we've reached our target
                if self.total_cats >= 1000:  # Target 1000 cats
                    logging.info(f"Reached target of {self.total_cats} cats")
                    return
            
            time.sleep(self.delay)
        
        logging.info(f"Exploration complete. Total unique cats found: {len(all_cat_urls)}")
    
    def scrape(self, target_cats=1000, target_images=5000):
        """Main scraping method"""
        logging.info(f"Starting smart scraping - Target: {target_cats} cats, {target_images} images")
        
        try:
            self.explore_different_patterns()
            
            logging.info(f"Smart scraping completed: {self.total_cats} cats, {self.downloaded_images} images")
            print(f"\n🎉 Smart scraping completed successfully!")
            print(f"Total cats processed: {self.total_cats}")
            print(f"Total images downloaded: {self.downloaded_images}")
            print(f"Check the '{self.output_dir}' directory for results.")
            
        except KeyboardInterrupt:
            logging.info("Scraping interrupted by user")
            print(f"\n⏸️  Scraping interrupted. Progress saved.")
            print(f"Total cats processed: {self.total_cats}")
            print(f"Total images downloaded: {self.downloaded_images}")
        except Exception as e:
            logging.error(f"Scraping failed: {e}")
            print(f"\n❌ Scraping failed: {e}")
        finally:
            self.save_progress()

def main():
    scraper = SmartNekoJirushiScraper()
    scraper.scrape()

if __name__ == "__main__":
    main() 