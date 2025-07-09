#!/usr/bin/env python3
"""
Improved Neko Jirushi Cat Scraper
This version properly navigates the website structure to find individual cat profiles
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
        logging.FileHandler('improved_scraper.log'),
        logging.StreamHandler()
    ]
)

class ImprovedNekoJirushiScraper:
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
    
    def get_category_pages(self):
        """Get all category pages from the main foster page"""
        logging.info("Getting category pages from main foster page...")
        
        # Start with the main foster page
        main_url = f"{self.base_url}/foster/"
        response = self.get_page(main_url)
        if not response:
            return []
        
        soup = BeautifulSoup(response.text, 'html.parser')
        category_urls = []
        
        # Look for links to different categories (prefectures, status, etc.)
        # Based on the website structure, we need to find links like:
        # /foster/cat/hokkaido/st-1/
        # /foster/cat/tokyo/st-1/
        # etc.
        
        # Find all links that contain foster/cat
        all_links = soup.find_all('a', href=True)
        for link in all_links:
            href = link.get('href')
            if href and '/foster/cat/' in href:
                full_url = urljoin(self.base_url, href)
                if full_url not in category_urls:
                    category_urls.append(full_url)
                    logging.info(f"Found category: {full_url}")
        
        return category_urls
    
    def get_cat_listing_urls_from_category(self, category_url, page=1):
        """Get individual cat profile URLs from a category page"""
        logging.info(f"Getting cat listings from category: {category_url}")
        
        # Try different page patterns
        page_urls = [
            f"{category_url}?p={page}",
            f"{category_url}&p={page}",
            category_url  # Try without page parameter
        ]
        
        for page_url in page_urls:
            response = self.get_page(page_url)
            if response:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Look for individual cat profile links
                # These should be links to actual cat profiles, not category pages
                cat_profile_urls = []
                
                # Try different selectors for individual cat links
                selectors = [
                    "a[href*='/foster/cat/detail/']",
                    "a[href*='/foster/cat/view/']",
                    "a[href*='/foster/cat/show/']",
                    ".cat-profile a",
                    ".cat-detail a",
                    "a[href*='detail']",
                    "a[href*='view']",
                    "a[href*='show']"
                ]
                
                for selector in selectors:
                    elements = soup.select(selector)
                    if elements:
                        logging.info(f"Found {len(elements)} potential cat profiles using selector: {selector}")
                        for element in elements:
                            href = element.get("href")
                            if href:
                                full_url = urljoin(self.base_url, href)
                                # Make sure it's not a category page
                                if ('detail' in full_url or 'view' in full_url or 'show' in full_url) and full_url not in cat_profile_urls:
                                    cat_profile_urls.append(full_url)
                        break
                
                if cat_profile_urls:
                    return cat_profile_urls
        
        logging.warning(f"No cat profile links found in category: {category_url}")
        return []
    
    def get_cat_profile_data(self, profile_url):
        """Extract cat information and images from profile page"""
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
        
        # Try to get cat name
        for selector in config.CAT_NAME_SELECTORS:
            element = soup.select_one(selector)
            if element:
                cat_data['name'] = element.get_text().strip()
                break
        
        # Clean the name for file naming
        safe_name = re.sub(config.SAFE_FILENAME_CHARS, config.REPLACEMENT_CHAR, cat_data['name'])
        cat_data['safe_name'] = safe_name
        
        # Extract images
        for selector in config.IMAGE_SELECTORS:
            images = soup.select(selector)
            if images:
                logging.info(f"Found {len(images)} images using selector: {selector}")
                for img in images:
                    src = img.get("src") or img.get("data-src")
                    if src:
                        full_url = urljoin(self.base_url, src)
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
    
    def scrape_cats_improved(self, max_total_cats=100, max_total_images=1000):
        """Improved scraping that properly navigates the website structure"""
        all_cats = []
        seen_urls = set()
        total_images = 0
        
        # Get all category pages first
        category_urls = self.get_category_pages()
        logging.info(f"Found {len(category_urls)} category pages")
        
        if not category_urls:
            logging.error("No category pages found. Trying fallback method...")
            # Fallback: try the original method
            return self.scrape_cats_fallback(max_total_cats, max_total_images)
        
        # Process each category
        for category_idx, category_url in enumerate(category_urls):
            if len(all_cats) >= max_total_cats or total_images >= max_total_images:
                break
            
            logging.info(f"Processing category {category_idx + 1}/{len(category_urls)}: {category_url}")
            
            # Try multiple pages for each category
            page = 1
            while page <= 5:  # Limit pages per category
                cat_profile_urls = self.get_cat_listing_urls_from_category(category_url, page)
                
                if not cat_profile_urls:
                    logging.info(f"No more cat profiles found in category {category_url} on page {page}")
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
        
        summary_file = os.path.join(self.output_dir, 'improved_scraping_summary.json')
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        logging.info(f"Improved scraping completed: {len(all_cats)} cats, {total_images} images.")
        return all_cats
    
    def scrape_cats_fallback(self, max_total_cats=100, max_total_images=1000):
        """Fallback method using the original approach"""
        logging.info("Using fallback scraping method...")
        
        all_cats = []
        seen_urls = set()
        total_images = 0
        page = 1
        
        while len(all_cats) < max_total_cats and total_images < max_total_images:
            logging.info(f"Scraping listing page {page}...")
            
            # Try different URL patterns
            possible_urls = [
                f"{self.base_url}/foster/cat/?p={page}",
                f"{self.base_url}/foster/cat?p={page}",
                f"{self.base_url}/foster/?p={page}",
            ]
            
            cat_urls = []
            for url in possible_urls:
                response = self.get_page(url)
                if response:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Look for any links that might lead to cat profiles
                    links = soup.find_all('a', href=True)
                    for link in links:
                        href = link.get('href')
                        if href and ('detail' in href or 'view' in href or 'show' in href):
                            full_url = urljoin(self.base_url, href)
                            if full_url not in cat_urls:
                                cat_urls.append(full_url)
                    
                    if cat_urls:
                        break
            
            if not cat_urls:
                logging.warning(f"No cat links found on page {page}, stopping.")
                break
            
            # Filter out duplicates
            cat_urls = [url for url in cat_urls if url not in seen_urls]
            cat_urls = cat_urls[:config.MAX_CATS_PER_PAGE]
            
            for cat_url in cat_urls:
                if len(all_cats) >= max_total_cats or total_images >= max_total_images:
                    break
                
                logging.info(f"[{len(all_cats)+1}] Processing cat: {cat_url}")
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
        
        return all_cats

def main():
    scraper = ImprovedNekoJirushiScraper()
    
    print("🐱 Improved Neko Jirushi Cat Scraper")
    print("This version properly navigates the website structure to find individual cat profiles")
    print("=" * 70)
    
    try:
        cats = scraper.scrape_cats_improved(max_total_cats=100, max_total_images=1000)
        print(f"\n🎉 Improved scraping completed successfully!")
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