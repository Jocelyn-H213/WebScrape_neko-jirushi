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
        logging.FileHandler(config.LOG_FILE),
        logging.StreamHandler()
    ]
)

class NekoJirushiScraper:
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
    
    def get_cat_listing_urls(self, page=1, category="foster"):
        """Get cat profile URLs from listing pages"""
        # Try different possible URL patterns
        possible_urls = [
            pattern.format(base_url=self.base_url, page=page, category=category)
            for pattern in config.LISTING_URL_PATTERNS
        ]
        
        for url in possible_urls:
            logging.info(f"Trying to get cat listings from: {url}")
            response = self.get_page(url)
            if response:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Try different selectors for cat links
                links = []
                for selector in config.CAT_LINK_SELECTORS:
                    elements = soup.select(selector)
                    if elements:
                        logging.info(f"Found {len(elements)} links using selector: {selector}")
                        for element in elements:
                            href = element.get("href")
                            if href and ("/cat/" in href or "neko" in href):
                                full_url = urljoin(self.base_url, href)
                                if full_url not in links:
                                    links.append(full_url)
                        break
                
                if links:
                    return links
        
        logging.warning(f"No cat links found on page {page}")
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
    
    def scrape_cats(self, max_total_cats=100, max_total_images=1000):
        """Scrape until target number of cats and images reached"""
        all_cats = []
        seen_urls = set()
        total_images = 0
        page = 1

        while len(all_cats) < max_total_cats and total_images < max_total_images:
            logging.info(f"Scraping listing page {page}...")
            cat_urls = self.get_cat_listing_urls(page)
            if not cat_urls:
                logging.warning(f"No cats found on page {page}, stopping.")
                break

            # Filter out duplicates
            cat_urls = [url for url in cat_urls if url not in seen_urls]
            cat_urls = cat_urls[:config.MAX_CATS_PER_PAGE]

            for i, cat_url in enumerate(cat_urls):
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

        # Save summary
        summary = {
            'total_cats': len(all_cats),
            'total_images': total_images,
            'scraped_at': datetime.now().isoformat(),
            'cats': [{'name': c['name'], 'safe_name': c['safe_name'], 'image_count': len(c['images'])} for c in all_cats]
        }

        summary_file = os.path.join(self.output_dir, 'scraping_summary.json')
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)

        logging.info(f"Scraping completed: {len(all_cats)} cats, {total_images} images.")
        return all_cats

def main():
    scraper = NekoJirushiScraper()
    
    print("Starting Neko Jirushi Cat Scraper...")
    print("This will scrape cat profiles and download images from different angles.")
    print(f"Images will be saved in the '{config.OUTPUT_DIR}/{config.IMAGES_DIR}' directory.")
    print(f"Cat data will be saved in the '{config.OUTPUT_DIR}/{config.DATA_DIR}' directory.")
    print()
    
    try:
        cats = scraper.scrape_cats(max_total_cats=100, max_total_images=1000)
        print(f"\nScraping completed successfully!")
        print(f"Total cats processed: {len(cats)}")
        total_images = sum(len(cat['images']) for cat in cats)
        print(f"Total images downloaded: {total_images}")
        print(f"Check the '{config.OUTPUT_DIR}' directory for results.")
        
    except KeyboardInterrupt:
        print("\nScraping interrupted by user.")
    except Exception as e:
        logging.error(f"Scraping failed: {e}")
        print(f"Scraping failed: {e}")

if __name__ == "__main__":
    main() 