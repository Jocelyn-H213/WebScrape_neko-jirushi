#!/usr/bin/env python3
"""
Large Scale Cat Scraper for Neko Jirushi
Specialized script for scraping 100+ cats and 1000+ images
"""

import os
import json
import time
from datetime import datetime
from cat_scraper import NekoJirushiScraper
import config

class LargeScaleScraper:
    def __init__(self):
        self.scraper = NekoJirushiScraper()
        self.progress_file = os.path.join(config.OUTPUT_DIR, 'scraping_progress.json')
        self.load_progress()
    
    def load_progress(self):
        """Load previous scraping progress"""
        if os.path.exists(self.progress_file):
            try:
                with open(self.progress_file, 'r', encoding='utf-8') as f:
                    self.progress = json.load(f)
                print(f"Loaded previous progress: {self.progress['total_cats']} cats, {self.progress['total_images']} images")
            except Exception as e:
                print(f"Could not load progress file: {e}")
                self.progress = {'total_cats': 0, 'total_images': 0, 'seen_urls': []}
        else:
            self.progress = {'total_cats': 0, 'total_images': 0, 'seen_urls': []}
    
    def save_progress(self, cats, total_images, seen_urls):
        """Save current scraping progress"""
        self.progress = {
            'total_cats': len(cats),
            'total_images': total_images,
            'seen_urls': list(seen_urls),
            'last_updated': datetime.now().isoformat()
        }
        
        os.makedirs(os.path.dirname(self.progress_file), exist_ok=True)
        with open(self.progress_file, 'w', encoding='utf-8') as f:
            json.dump(self.progress, f, ensure_ascii=False, indent=2)
    
    def scrape_large_scale(self, target_cats=100, target_images=1000):
        """Large scale scraping with progress tracking"""
        print(f"Starting large scale scraping...")
        print(f"Target: {target_cats} cats, {target_images} images")
        print(f"Current progress: {self.progress['total_cats']} cats, {self.progress['total_images']} images")
        print("=" * 60)
        
        all_cats = []
        seen_urls = set(self.progress['seen_urls'])
        total_images = self.progress['total_images']
        page = 1
        
        # Load existing cat data
        if os.path.exists(self.scraper.data_dir):
            for filename in os.listdir(self.scraper.data_dir):
                if filename.endswith('.json'):
                    try:
                        with open(os.path.join(self.scraper.data_dir, filename), 'r', encoding='utf-8') as f:
                            cat_data = json.load(f)
                            all_cats.append(cat_data)
                    except Exception as e:
                        print(f"Error loading {filename}: {e}")
        
        print(f"Loaded {len(all_cats)} existing cats")
        
        start_time = time.time()
        
        while len(all_cats) < target_cats and total_images < target_images:
            print(f"\n--- Page {page} ---")
            print(f"Progress: {len(all_cats)}/{target_cats} cats, {total_images}/{target_images} images")
            
            cat_urls = self.scraper.get_cat_listing_urls(page)
            if not cat_urls:
                print(f"No cats found on page {page}, stopping.")
                break

            # Filter out duplicates
            cat_urls = [url for url in cat_urls if url not in seen_urls]
            cat_urls = cat_urls[:config.MAX_CATS_PER_PAGE]

            if not cat_urls:
                print(f"No new cats found on page {page}")
                page += 1
                continue

            for i, cat_url in enumerate(cat_urls):
                if len(all_cats) >= target_cats or total_images >= target_images:
                    break

                print(f"\n[{len(all_cats)+1}/{target_cats}] Processing cat: {cat_url}")
                seen_urls.add(cat_url)

                cat_data = self.scraper.get_cat_profile_data(cat_url)
                if cat_data and cat_data['images']:
                    downloaded_images = []
                    for j, img_info in enumerate(cat_data['images']):
                        if total_images >= target_images:
                            break
                        
                        print(f"  Downloading image {j+1}/{len(cat_data['images'])}...")
                        filepath = self.scraper.download_image(img_info['url'], cat_data['safe_name'], j + 1)
                        if filepath:
                            img_info['local_path'] = filepath
                            downloaded_images.append(img_info)
                            total_images += 1
                        time.sleep(config.DELAY_BETWEEN_IMAGES)

                    if downloaded_images:
                        cat_data['images'] = downloaded_images
                        all_cats.append(cat_data)

                        # Save individual cat data
                        cat_file = os.path.join(self.scraper.data_dir, f"{cat_data['safe_name']}.json")
                        with open(cat_file, 'w', encoding='utf-8') as f:
                            json.dump(cat_data, f, ensure_ascii=False, indent=2)

                        # Save progress every 5 cats
                        if len(all_cats) % 5 == 0:
                            self.save_progress(all_cats, total_images, seen_urls)
                            elapsed_time = time.time() - start_time
                            print(f"  Progress saved! Elapsed time: {elapsed_time/60:.1f} minutes")

                    print(f"  ✓ Cat completed: {len(downloaded_images)} images")
                else:
                    print(f"  ✗ No images found for this cat")
                
                time.sleep(self.scraper.delay)

            page += 1
            time.sleep(self.scraper.delay)

        # Final save
        self.save_progress(all_cats, total_images, seen_urls)
        
        # Save final summary
        summary = {
            'total_cats': len(all_cats),
            'total_images': total_images,
            'target_cats': target_cats,
            'target_images': target_images,
            'scraped_at': datetime.now().isoformat(),
            'elapsed_time_minutes': (time.time() - start_time) / 60,
            'cats': [{'name': c['name'], 'safe_name': c['safe_name'], 'image_count': len(c['images'])} for c in all_cats]
        }

        summary_file = os.path.join(self.scraper.output_dir, 'large_scale_summary.json')
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)

        elapsed_time = time.time() - start_time
        print(f"\n" + "=" * 60)
        print(f"LARGE SCALE SCRAPING COMPLETED!")
        print(f"Total cats: {len(all_cats)}")
        print(f"Total images: {total_images}")
        print(f"Elapsed time: {elapsed_time/60:.1f} minutes")
        print(f"Average time per cat: {elapsed_time/len(all_cats):.1f} seconds")
        print(f"Check '{config.OUTPUT_DIR}' for results")
        
        return all_cats

def main():
    """Run large scale scraping"""
    print("🐱 Neko Jirushi Large Scale Cat Scraper")
    print("=" * 60)
    
    scraper = LargeScaleScraper()
    
    try:
        cats = scraper.scrape_large_scale(target_cats=100, target_images=1000)
        
        print(f"\n🎉 Successfully scraped {len(cats)} cats!")
        total_images = sum(len(cat['images']) for cat in cats)
        print(f"📸 Total images downloaded: {total_images}")
        
    except KeyboardInterrupt:
        print("\n⚠️ Scraping interrupted by user. Progress has been saved.")
    except Exception as e:
        print(f"\n❌ Scraping failed: {e}")
        print("Progress has been saved. You can resume later.")

if __name__ == "__main__":
    main() 