#!/usr/bin/env python3
"""
Deep Explorer Neko Jirushi Cat Scraper
This version systematically explores the website to find additional cat listings
"""

import requests
from bs4 import BeautifulSoup
import os
import time
import re
from urllib.parse import urljoin, urlparse
import json
from datetime import datetime
import logging
import config
from collections import deque

# Set up logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('deep_explorer_scraper.log'),
        logging.StreamHandler()
    ]
)

class DeepExplorerScraper:
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
        self.progress_file = "deep_explorer_progress.json"
        self.load_progress()
        
        # URLs to explore
        self.urls_to_explore = deque()
        self.explored_urls = set()
        
        # Initialize with main pages
        self.urls_to_explore.extend([
            self.base_url + "/foster/",
            self.base_url + "/foster/cat/",
            self.base_url + "/foster/dog/",
            self.base_url + "/foster/other/",
            self.base_url + "/",
            self.base_url + "/about/",
            self.base_url + "/contact/",
            self.base_url + "/search/",
            self.base_url + "/map/",
            self.base_url + "/guide/",
            self.base_url + "/help/",
            self.base_url + "/faq/",
            self.base_url + "/terms/",
            self.base_url + "/privacy/",
        ])
    
    def load_progress(self):
        """Load progress from file"""
        if os.path.exists(self.progress_file):
            try:
                with open(self.progress_file, 'r') as f:
                    data = json.load(f)
                    self.processed_cats = set(data.get('processed_cats', []))
                    self.downloaded_images = data.get('downloaded_images', 0)
                    self.total_cats = data.get('total_cats', 0)
                    self.explored_urls = set(data.get('explored_urls', []))
                    logging.info(f"Loaded progress: {len(self.processed_cats)} cats, {self.downloaded_images} images, {len(self.explored_urls)} explored URLs")
            except Exception as e:
                logging.warning(f"Failed to load progress: {e}")
    
    def save_progress(self):
        """Save progress to file"""
        try:
            data = {
                'processed_cats': list(self.processed_cats),
                'downloaded_images': self.downloaded_images,
                'total_cats': self.total_cats,
                'explored_urls': list(self.explored_urls),
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
                    # Filter out navigation and UI images
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
    
    def discover_new_urls(self, url):
        """Discover new URLs to explore from a page"""
        response = self.get_page(url)
        if not response:
            return []
        
        soup = BeautifulSoup(response.content, 'html.parser')
        new_urls = []
        
        # Find all links
        links = soup.find_all('a', href=True)
        for link in links:
            href = link.get('href', '')
            if href:
                full_url = urljoin(self.base_url, href)
                
                # Only explore URLs from the same domain
                if full_url.startswith(self.base_url):
                    # Skip already explored URLs and external links
                    if full_url not in self.explored_urls and full_url not in self.urls_to_explore:
                        # Focus on foster-related URLs
                        if any(keyword in full_url.lower() for keyword in [
                            'foster', 'cat', 'dog', 'pet', 'animal', 'adopt', 'search', 'list'
                        ]):
                            new_urls.append(full_url)
        
        return new_urls
    
    def explore_website(self):
        """Systematically explore the website to find cat listings"""
        logging.info("Starting deep website exploration...")
        
        all_cat_urls = set()
        max_exploration = 100  # Limit exploration to avoid infinite loops
        exploration_count = 0
        
        while self.urls_to_explore and exploration_count < max_exploration:
            url = self.urls_to_explore.popleft()
            
            if url in self.explored_urls:
                continue
            
            logging.info(f"Exploring URL {exploration_count + 1}/{max_exploration}: {url}")
            self.explored_urls.add(url)
            exploration_count += 1
            
            # Find cat profiles on this page
            cat_urls = self.find_cat_profiles(url)
            new_cat_urls = [cat_url for cat_url in cat_urls if cat_url not in all_cat_urls]
            all_cat_urls.update(cat_urls)
            
            logging.info(f"Found {len(new_cat_urls)} new cats from {url}")
            
            # Process new cats
            for cat_url in new_cat_urls:
                self.download_cat_images(cat_url)
                self.save_progress()
                
                # Check if we've reached our target
                if self.total_cats >= 500:  # Target 500 cats
                    logging.info(f"Reached target of {self.total_cats} cats")
                    return
            
            # Discover new URLs to explore
            new_urls = self.discover_new_urls(url)
            for new_url in new_urls:
                if new_url not in self.explored_urls and new_url not in self.urls_to_explore:
                    self.urls_to_explore.append(new_url)
            
            logging.info(f"Discovered {len(new_urls)} new URLs to explore. Queue size: {len(self.urls_to_explore)}")
            
            time.sleep(self.delay)
        
        logging.info(f"Exploration complete. Total unique cats found: {len(all_cat_urls)}")
    
    def scrape(self, target_cats=500, target_images=2000):
        """Main scraping method"""
        logging.info(f"Starting deep explorer scraping - Target: {target_cats} cats, {target_images} images")
        
        try:
            self.explore_website()
            
            logging.info(f"Deep explorer scraping completed: {self.total_cats} cats, {self.downloaded_images} images")
            print(f"\n🎉 Deep explorer scraping completed successfully!")
            print(f"Total cats processed: {self.total_cats}")
            print(f"Total images downloaded: {self.downloaded_images}")
            print(f"URLs explored: {len(self.explored_urls)}")
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
    scraper = DeepExplorerScraper()
    scraper.scrape()

if __name__ == "__main__":
    main() 