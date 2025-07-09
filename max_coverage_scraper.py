#!/usr/bin/env python3
"""
Max Coverage Neko Jirushi Cat Scraper
Uses AJAX endpoint to gather all foster cat profiles across all pages
"""

import requests
from bs4 import BeautifulSoup
import os
import time
import re
import random
from urllib.parse import urljoin, urlparse
import json
from datetime import datetime
import logging
import config

# Add the recommended selector if missing
if "img[data-src*='photo']" not in config.IMAGE_SELECTORS:
    config.IMAGE_SELECTORS.append("img[data-src*='photo']")

logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('max_coverage_scraper.log'),
        logging.StreamHandler()
    ]
)

class MaxCoverageScraper:
    def __init__(self):
        self.base_url = config.BASE_URL
        self.session = requests.Session()
        self.session.headers.update(config.HEADERS)
        self.delay_min = 1.5
        self.delay_max = 3.0
        self.output_dir = "scraped_cats"
        os.makedirs(self.output_dir, exist_ok=True)
        self.progress_file = "max_coverage_progress.json"
        self.seen_urls = set()
        self.downloaded_images = 0
        self.total_cats = 0
        self.load_progress()

    def load_progress(self):
        if os.path.exists(self.progress_file):
            try:
                with open(self.progress_file, 'r') as f:
                    data = json.load(f)
                    self.seen_urls = set(data.get('seen_urls', []))
                    self.downloaded_images = data.get('downloaded_images', 0)
                    self.total_cats = data.get('total_cats', 0)
                    logging.info(f"Loaded progress: {len(self.seen_urls)} cats, {self.downloaded_images} images")
            except Exception as e:
                logging.warning(f"Failed to load progress: {e}")

    def save_progress(self):
        try:
            data = {
                'seen_urls': list(self.seen_urls),
                'downloaded_images': self.downloaded_images,
                'total_cats': self.total_cats,
                'timestamp': datetime.now().isoformat()
            }
            with open(self.progress_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logging.warning(f"Failed to save progress: {e}")

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
        cat_links = soup.find_all('a', href=re.compile(r'/foster/\d+/'))
        cat_urls = []
        for link in cat_links:
            href = link.get('href', '')
            if href:
                full_url = urljoin(self.base_url, href)
                if full_url not in self.seen_urls:
                    cat_urls.append(full_url)
        return cat_urls

    def download_cat_images(self, cat_url):
        cat_id = re.search(r'/foster/(\d+)/', cat_url)
        if not cat_id:
            return 0
        cat_id = cat_id.group(1)
        if cat_url in self.seen_urls:
            logging.debug(f"Cat {cat_id} already processed, skipping")
            return 0
        logging.info(f"Processing cat {cat_id}: {cat_url}")
        response = self.get_page(cat_url)
        if not response:
            logging.warning(f"Failed to get cat page: {cat_url}")
            return 0
        soup = BeautifulSoup(response.content, 'html.parser')
        images = []
        for selector in config.IMAGE_SELECTORS:
            found_images = soup.select(selector)
            images.extend(found_images)
        unique_images = []
        seen_urls = set()
        for img in images:
            src = img.get('src') or img.get('data-src')
            if src:
                full_url = urljoin(self.base_url, src)
                if full_url not in seen_urls:
                    if not any(exclude in full_url.lower() for exclude in [
                        'logo', 'icon', 'banner', 'header', 'nav', 'gnav', 
                        'mucho-domingo', 'headerhealth', 'headermail', 'headernotice'
                    ]) and '/img/foster/' in full_url:
                        unique_images.append(full_url)
                        seen_urls.add(full_url)
        if not unique_images:
            logging.warning(f"No images found for cat {cat_id}")
            self.seen_urls.add(cat_url)
            return 0
        cat_dir = os.path.join(self.output_dir, f"cat_{cat_id}")
        os.makedirs(cat_dir, exist_ok=True)
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
            self.seen_urls.add(cat_url)
            self.total_cats += 1
            self.downloaded_images += downloaded
            logging.info(f"Downloaded {downloaded} images for cat {cat_id}")
        return downloaded

    def scrape(self):
        logging.info(f"Starting max coverage scraping using AJAX endpoint...")
        try:
            page = 1
            while True:
                ajax_url = f"{self.base_url}/foster/cat/contents/?p={page}"
                logging.info(f"Scraping AJAX listing page: {ajax_url}")
                response = self.get_page(ajax_url)
                if not response or not response.text.strip():
                    logging.info(f"No more content at page {page}. Stopping.")
                    break
                soup = BeautifulSoup(response.text, 'html.parser')
                cat_urls = self.find_cat_profiles(soup)
                if not cat_urls:
                    logging.info(f"No new cat profiles found at page {page}. Stopping.")
                    break
                logging.info(f"Found {len(cat_urls)} new cat profiles on page {page}")
                for cat_url in cat_urls:
                    self.download_cat_images(cat_url)
                    self.save_progress()
                    time.sleep(random.uniform(self.delay_min, self.delay_max))
                page += 1
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
            logging.info(f"Max coverage scraping completed: {self.total_cats} cats, {self.downloaded_images} images")
            print(f"\n🎉 Max coverage scraping completed!")
            print(f"Total cats processed: {self.total_cats}")
            print(f"Total images downloaded: {self.downloaded_images}")
            print(f"Check the '{self.output_dir}' directory for results.")

def main():
    scraper = MaxCoverageScraper()
    scraper.scrape()

if __name__ == "__main__":
    main() 