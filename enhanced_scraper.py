#!/usr/bin/env python3
"""
Enhanced Neko Jirushi Cat Scraper
This version finds many more cats by exploring multiple pages and discovering more listing URLs
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
        logging.FileHandler('enhanced_scraper.log'),
        logging.StreamHandler()
    ]
)

class EnhancedNekoJirushiScraper:
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
    
    def discover_listing_urls(self):
        """Discover all possible listing URLs that might contain cat profiles"""
        logging.info("Discovering listing URLs...")
        
        discovered_urls = set()
        
        # Start with known listing pages
        base_listings = [
            "https://www.neko-jirushi.com/foster/cat/",
            "https://www.neko-jirushi.com/foster/cat/st-1/",
            "https://www.neko-jirushi.com/foster/cat/st-2/",
            "https://www.neko-jirushi.com/foster/cat/st-3/",
            "https://www.neko-jirushi.com/foster/cat/st-4/",
            "https://www.neko-jirushi.com/foster/cat/st-5/",
        ]
        
        # Add prefecture-specific listings
        prefectures = [
            'tokyo', 'hokkaido', 'kanagawa', 'saitama', 'chiba', 'osaka', 'kyoto', 
            'hyogo', 'aichi', 'fukuoka', 'hiroshima', 'miyagi', 'shizuoka', 'ibaraki',
            'tochigi', 'gunma', 'niigata', 'nagano', 'gifu', 'mie', 'shiga', 'nara',
            'wakayama', 'tottori', 'shimane', 'okayama', 'yamaguchi', 'tokushima',
            'kagawa', 'ehime', 'kochi', 'fukushima', 'yamagata', 'akita', 'iwate',
            'aomori', 'yamanashi', 'nagasaki', 'kumamoto', 'oita', 'miyazaki',
            'kagoshima', 'okinawa'
        ]
        
        for prefecture in prefectures:
            base_listings.extend([
                f"https://www.neko-jirushi.com/foster/cat/{prefecture}/",
                f"https://www.neko-jirushi.com/foster/cat/{prefecture}/st-1/",
                f"https://www.neko-jirushi.com/foster/cat/{prefecture}/st-2/",
                f"https://www.neko-jirushi.com/foster/cat/{prefecture}/st-3/",
            ])
        
        # Also try to discover more URLs from the main foster page
        main_foster_url = "https://www.neko-jirushi.com/foster/"
        response = self.get_page(main_foster_url)
        if response:
            soup = BeautifulSoup(response.text, 'html.parser')
            all_links = soup.find_all('a', href=True)
            
            for link in all_links:
                href = link.get('href')
                if href and '/foster/cat/' in href:
                    full_url = urljoin(self.base_url, href)
                    discovered_urls.add(full_url)
        
        # Add all discovered URLs
        for url in base_listings:
            discovered_urls.add(url)
        
        logging.info(f"Discovered {len(discovered_urls)} potential listing URLs")
        return list(discovered_urls)
    
    def get_cat_profile_urls_from_listing(self, listing_url, page=1):
        """Get individual cat profile URLs from a listing page"""
        logging.info(f"Getting cat profiles from listing: {listing_url} (page {page})")
        
        # Try different page patterns
        page_urls = [
            f"{listing_url}?p={page}",
            f"{listing_url}&p={page}",
            f"{listing_url}page/{page}/",
            listing_url  # Try without page parameter
        ]
        
        for page_url in page_urls:
            response = self.get_page(page_url)
            if response:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Look for individual cat profile links
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
                    logging.info(f"Found {len(cat_profile_urls)} individual cat profiles on page {page}")
                    return cat_profile_urls
        
        logging.warning(f"No individual cat profiles found in listing: {listing_url} on page {page}")
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
    
    def scrape_cats_enhanced(self, max_total_cats=500, max_total_images=2000):
        """Enhanced scraping that explores many more pages to find more cats"""
        all_cats = []
        seen_urls = set()
        total_images = 0
        
        # Discover all possible listing URLs
        listing_urls = self.discover_listing_urls()
        
        logging.info(f"Starting enhanced scraping with {len(listing_urls)} listing URLs")
        
        # Process each listing page
        for listing_idx, listing_url in enumerate(listing_urls):
            if len(all_cats) >= max_total_cats or total_images >= max_total_images:
                break
            
            logging.info(f"Processing listing {listing_idx + 1}/{len(listing_urls)}: {listing_url}")
            
            # Try multiple pages for each listing (up to 10 pages)
            page = 1
            consecutive_empty_pages = 0
            
            while page <= 10 and consecutive_empty_pages < 3:  # Stop after 3 consecutive empty pages
                cat_profile_urls = self.get_cat_profile_urls_from_listing(listing_url, page)
                
                if not cat_profile_urls:
                    consecutive_empty_pages += 1
                    logging.info(f"No cat profiles found on page {page} of {listing_url}")
                else:
                    consecutive_empty_pages = 0  # Reset counter
                    
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
        
        summary_file = os.path.join(self.output_dir, 'enhanced_scraping_summary.json')
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        logging.info(f"Enhanced scraping completed: {len(all_cats)} cats, {total_images} images.")
        return all_cats

def main():
    scraper = EnhancedNekoJirushiScraper()
    
    print("🐱 Enhanced Neko Jirushi Cat Scraper")
    print("This version explores many more pages to find hundreds of cats")
    print("=" * 70)
    
    try:
        cats = scraper.scrape_cats_enhanced(max_total_cats=500, max_total_images=2000)
        print(f"\n🎉 Enhanced scraping completed successfully!")
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