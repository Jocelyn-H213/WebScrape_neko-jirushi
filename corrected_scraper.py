#!/usr/bin/env python3
"""
Corrected Neko Jirushi Cat Scraper
This version targets the actual individual cat profile URLs found in the deep exploration
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

# Set up logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('corrected_scraper.log'),
        logging.StreamHandler()
    ]
)

class CorrectedNekoJirushiScraper:
    def __init__(self, base_url=None, delay=None):
        self.base_url = base_url or config.BASE_URL
        self.delay = delay or config.DELAY_BETWEEN_REQUESTS
        self.session = requests.Session()
        self.session.headers.update(config.HEADERS)
        
        # Create directories
        self.output_dir = config.OUTPUT_DIR
        self.images_dir = os.path.join(self.output_dir, config.IMAGES_DIR)
        self.data_dir = os.path.join(self.output_dir, config.DATA_DIR)
        
        for directory in [self.output_dir, self.images_dir, self.data_dir]:
            os.makedirs(directory, exist_ok=True)
    
    def get_page(self, url, retries=None):
        """Get page content with retry logic"""
        retries = retries or config.MAX_RETRIES
        for attempt in range(retries):
            try:
                response = self.session.get(url, timeout=config.TIMEOUT)
                response.raise_for_status()
                return response
            except requests.RequestException as e:
                logging.warning(f"Attempt {attempt + 1} failed for {url}: {e}")
                if attempt == retries - 1:
                    logging.error(f"Failed to get {url} after {retries} attempts")
                    return None
                time.sleep(self.delay * (attempt + 1))
        return None
    
    def get_cat_profile_urls_from_listing(self, listing_url, page=1):
        """Get individual cat profile URLs from a listing page"""
        logging.info(f"Getting cat profiles from listing: {listing_url}")
        
        # Try different page patterns
        page_urls = [
            f"{listing_url}?p={page}",
            f"{listing_url}&p={page}",
            listing_url  # Try without page parameter
        ]
        
        for page_url in page_urls:
            response = self.get_page(page_url)
            if response:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Look for individual cat profile links
                # Based on the deep exploration, these are URLs like /foster/226656/
                cat_profile_urls = []
                
                # Find all links
                all_links = soup.find_all('a', href=True)
                
                for link in all_links:
                    href = link.get('href')
                    text = link.get_text().strip()
                    
                    # Look for individual cat profile patterns
                    # These should be URLs like /foster/226656/ or /foster/226655/
                    if href and '/foster/' in href:
                        # Check if it's a numeric ID (individual cat profile)
                        if re.search(r'/foster/\d+/?$', href):
                            full_url = urljoin(self.base_url, href)
                            if full_url not in cat_profile_urls:
                                cat_profile_urls.append(full_url)
                                logging.info(f"Found cat profile: {text} -> {full_url}")
                
                if cat_profile_urls:
                    logging.info(f"Found {len(cat_profile_urls)} individual cat profiles")
                    return cat_profile_urls
        
        logging.warning(f"No individual cat profiles found in listing: {listing_url}")
        return []
    
    def get_cat_profile_data(self, profile_url):
        """Extract cat information and images from individual cat profile page"""
        response = self.get_page(profile_url)
        if not response:
            return None
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract cat information
        cat_data = {
            'url': profile_url,
            'scraped_at': datetime.now().isoformat(),
            'name': 'Unknown',
            'images': [],
            'details': {}
        }
        
        # Try to get cat name from title or page content
        title = soup.title.string if soup.title else ''
        cat_data['name'] = title.replace(' - 猫好きのためのSNSコミュニティ', '').strip()
        
        # If no title, try to find cat name in page content
        if cat_data['name'] == 'Unknown' or not cat_data['name']:
            for selector in config.CAT_NAME_SELECTORS:
                element = soup.select_one(selector)
                if element:
                    cat_data['name'] = element.get_text().strip()
                    break
        
        # Clean the name for file naming
        safe_name = re.sub(config.SAFE_FILENAME_CHARS, config.REPLACEMENT_CHAR, cat_data['name'])
        cat_data['safe_name'] = safe_name
        
        # Extract images - focus on actual cat photos
        for selector in config.IMAGE_SELECTORS:
            images = soup.select(selector)
            if images:
                logging.info(f"Found {len(images)} images using selector: {selector}")
                for img in images:
                    src = img.get("src") or img.get("data-src")
                    if src:
                        full_url = urljoin(self.base_url, src)
                        # Filter out navigation and UI images
                        if not any(exclude in full_url.lower() for exclude in ['logo', 'icon', 'banner', 'header', 'nav']):
                            if full_url not in [img['url'] for img in cat_data['images']]:
                                cat_data['images'].append({
                                    'url': full_url,
                                    'alt': img.get('alt', ''),
                                    'title': img.get('title', '')
                                })
                break
        
        # Extract additional details
        for key, selectors in config.DETAIL_SELECTORS.items():
            for selector in selectors:
                element = soup.select_one(selector)
                if element:
                    cat_data['details'][key] = element.get_text().strip()
                    break
        
        return cat_data
    
    def download_image(self, image_url, cat_name, index):
        """Download a single image"""
        try:
            response = self.get_page(image_url)
            if not response:
                return None
            
            # Get file extension from URL or content-type
            parsed_url = urlparse(image_url)
            filename = os.path.basename(parsed_url.path)
            
            if not filename or '.' not in filename:
                content_type = response.headers.get('content-type', '')
                ext = config.CONTENT_TYPE_TO_EXTENSION.get(content_type, config.DEFAULT_IMAGE_FORMAT)
                filename = f"{cat_name}_{index}{ext}"
            else:
                # Clean filename
                name, ext = os.path.splitext(filename)
                filename = f"{cat_name}_{index}{ext}"
            
            # Create cat-specific directory
            cat_dir = os.path.join(self.images_dir, cat_name)
            os.makedirs(cat_dir, exist_ok=True)
            
            filepath = os.path.join(cat_dir, filename)
            
            if not os.path.exists(filepath):
                with open(filepath, 'wb') as f:
                    f.write(response.content)
                logging.info(f"Downloaded: {filename}")
                return filepath
            else:
                logging.info(f"File already exists: {filename}")
                return filepath
                
        except Exception as e:
            logging.error(f"Failed to download {image_url}: {e}")
            return None
    
    def scrape_cats_corrected(self, max_total_cats=100, max_total_images=1000):
        """Corrected scraping that targets actual individual cat profile URLs"""
        all_cats = []
        seen_urls = set()
        total_images = 0
        
        # List of listing pages to scrape from
        listing_pages = [
            "https://www.neko-jirushi.com/foster/cat/st-1/",
            "https://www.neko-jirushi.com/foster/cat/st-2/",
            "https://www.neko-jirushi.com/foster/cat/",
            "https://www.neko-jirushi.com/foster/cat/tokyo/st-1/",
            "https://www.neko-jirushi.com/foster/cat/hokkaido/st-1/",
            "https://www.neko-jirushi.com/foster/cat/kanagawa/st-1/",
            "https://www.neko-jirushi.com/foster/cat/saitama/st-1/",
            "https://www.neko-jirushi.com/foster/cat/chiba/st-1/"
        ]
        
        # Process each listing page
        for listing_idx, listing_url in enumerate(listing_pages):
            if len(all_cats) >= max_total_cats or total_images >= max_total_images:
                break
            
            logging.info(f"Processing listing {listing_idx + 1}/{len(listing_pages)}: {listing_url}")
            
            # Try multiple pages for each listing
            page = 1
            while page <= 3:  # Limit pages per listing
                cat_profile_urls = self.get_cat_profile_urls_from_listing(listing_url, page)
                
                if not cat_profile_urls:
                    logging.info(f"No more cat profiles found in listing {listing_url} on page {page}")
                    break
                
                # Filter out duplicates
                cat_profile_urls = [url for url in cat_profile_urls if url not in seen_urls]
                
                for cat_url in cat_profile_urls:
                    if len(all_cats) >= max_total_cats or total_images >= max_total_images:
                        break
                    
                    logging.info(f"[{len(all_cats)+1}/{max_total_cats}] Processing cat: {cat_url}")
                    seen_urls.add(cat_url)
                    
                    cat_data = self.get_cat_profile_data(cat_url)
                    if cat_data and cat_data['images']:
                        downloaded_images = []
                        for j, img_info in enumerate(cat_data['images']):
                            if total_images >= max_total_images:
                                break
                            filepath = self.download_image(img_info['url'], cat_data['safe_name'], j + 1)
                            if filepath:
                                img_info['local_path'] = filepath
                                downloaded_images.append(img_info)
                                total_images += 1
                            time.sleep(config.DELAY_BETWEEN_IMAGES)
                        
                        if downloaded_images:
                            cat_data['images'] = downloaded_images
                            all_cats.append(cat_data)
                            
                            # Save individual cat data
                            cat_file = os.path.join(self.data_dir, f"{cat_data['safe_name']}.json")
                            with open(cat_file, 'w', encoding='utf-8') as f:
                                json.dump(cat_data, f, ensure_ascii=False, indent=2)
                            
                            logging.info(f"Total cats so far: {len(all_cats)} | Total images: {total_images}")
                    
                    time.sleep(self.delay)
                
                page += 1
                time.sleep(self.delay)
        
        # Save summary
        summary = {
            'total_cats': len(all_cats),
            'total_images': total_images,
            'scraped_at': datetime.now().isoformat(),
            'cats': [{'name': c['name'], 'safe_name': c['safe_name'], 'image_count': len(c['images'])} for c in all_cats]
        }
        
        summary_file = os.path.join(self.output_dir, 'corrected_scraping_summary.json')
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        logging.info(f"Corrected scraping completed: {len(all_cats)} cats, {total_images} images.")
        return all_cats

def main():
    scraper = CorrectedNekoJirushiScraper()
    
    print("🐱 Corrected Neko Jirushi Cat Scraper")
    print("This version targets actual individual cat profile URLs")
    print("=" * 70)
    
    try:
        cats = scraper.scrape_cats_corrected(max_total_cats=100, max_total_images=1000)
        print(f"\n🎉 Corrected scraping completed successfully!")
        print(f"Total cats processed: {len(cats)}")
        total_images = sum(len(cat['images']) for cat in cats)
        print(f"Total images downloaded: {total_images}")
        print(f"Check the '{config.OUTPUT_DIR}' directory for results.")
        
    except KeyboardInterrupt:
        print("\n⚠️ Scraping interrupted by user.")
    except Exception as e:
        logging.error(f"Scraping failed: {e}")
        print(f"❌ Scraping failed: {e}")

if __name__ == "__main__":
    main() 