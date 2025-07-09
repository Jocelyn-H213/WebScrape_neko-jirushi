#!/usr/bin/env python3
"""
Example usage of the Neko Jirushi Cat Scraper
This script demonstrates different ways to use the scraper
"""

from cat_scraper import NekoJirushiScraper
import config

def example_basic_usage():
    """Basic usage example"""
    print("=== Basic Usage Example ===")
    
    # Create scraper with default settings
    scraper = NekoJirushiScraper()
    
    # Scrape a few cats
    cats = scraper.scrape_cats(max_pages=1, max_cats_per_page=2)
    
    print(f"Found {len(cats)} cats")
    for cat in cats:
        print(f"- {cat['name']}: {len(cat['images'])} images")

def example_custom_settings():
    """Example with custom settings"""
    print("\n=== Custom Settings Example ===")
    
    # Create scraper with custom settings
    scraper = NekoJirushiScraper(
        base_url="https://www.neko-jirushi.com",
        delay=3  # 3 second delay between requests
    )
    
    # Scrape with custom limits
    cats = scraper.scrape_cats(max_pages=2, max_cats_per_page=3)
    
    print(f"Found {len(cats)} cats with custom settings")

def example_data_analysis():
    """Example of analyzing scraped data"""
    print("\n=== Data Analysis Example ===")
    
    scraper = NekoJirushiScraper()
    
    # Scrape some cats
    cats = scraper.scrape_cats(max_pages=1, max_cats_per_page=5)
    
    if cats:
        # Analyze the data
        total_images = sum(len(cat['images']) for cat in cats)
        avg_images_per_cat = total_images / len(cats)
        
        print(f"Total cats: {len(cats)}")
        print(f"Total images: {total_images}")
        print(f"Average images per cat: {avg_images_per_cat:.1f}")
        
        # Show details for each cat
        for cat in cats:
            print(f"\nCat: {cat['name']}")
            print(f"  Images: {len(cat['images'])}")
            if cat['details']:
                print(f"  Details: {cat['details']}")

def example_resume_scraping():
    """Example showing how the scraper skips already downloaded images"""
    print("\n=== Resume Scraping Example ===")
    
    scraper = NekoJirushiScraper()
    
    # First run
    print("First run:")
    cats1 = scraper.scrape_cats(max_pages=1, max_cats_per_page=2)
    
    # Second run (should skip already downloaded images)
    print("\nSecond run (should skip existing images):")
    cats2 = scraper.scrape_cats(max_pages=1, max_cats_per_page=2)
    
    print(f"First run: {len(cats1)} cats")
    print(f"Second run: {len(cats2)} cats")

def example_error_handling():
    """Example of error handling"""
    print("\n=== Error Handling Example ===")
    
    # Create scraper with very short timeout to trigger errors
    scraper = NekoJirushiScraper()
    
    try:
        # This might fail due to network issues
        cats = scraper.scrape_cats(max_pages=1, max_cats_per_page=1)
        print(f"Successfully scraped {len(cats)} cats")
    except Exception as e:
        print(f"Scraping failed: {e}")
        print("The scraper includes retry logic and error handling")

def main():
    """Run all examples"""
    print("Neko Jirushi Cat Scraper - Usage Examples")
    print("=" * 50)
    
    examples = [
        ("Basic Usage", example_basic_usage),
        ("Custom Settings", example_custom_settings),
        ("Data Analysis", example_data_analysis),
        ("Resume Scraping", example_resume_scraping),
        ("Error Handling", example_error_handling),
    ]
    
    for name, func in examples:
        try:
            func()
            print(f"\n✓ {name} completed successfully")
        except Exception as e:
            print(f"\n✗ {name} failed: {e}")
        
        print("-" * 50)
    
    print("\nAll examples completed!")
    print("Check the 'scraped_cats' directory for downloaded images and data.")

if __name__ == "__main__":
    main() 