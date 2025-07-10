#!/usr/bin/env python3
"""
Dataset Cleanup Script
Removes non-cat images while preserving all cat images regardless of quality
"""

import os
import json
import shutil
from pathlib import Path
import logging
from PIL import Image
import requests
from urllib.parse import urlparse
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('dataset_cleanup.log'),
        logging.StreamHandler()
    ]
)

class DatasetCleanup:
    def __init__(self, scraped_dir="scraped_cats"):
        self.scraped_dir = Path(scraped_dir)
        self.backup_dir = Path("scraped_cats_backup")
        self.cleaned_dir = Path("scraped_cats_cleaned")
        
        # Create directories
        self.backup_dir.mkdir(exist_ok=True)
        self.cleaned_dir.mkdir(exist_ok=True)
        
        # Statistics
        self.stats = {
            'total_cats': 0,
            'total_images': 0,
            'removed_images': 0,
            'kept_images': 0,
            'failed_cats': 0
        }
    
    def backup_dataset(self):
        """Create a backup of the original dataset"""
        logging.info("Creating backup of original dataset...")
        
        if self.scraped_dir.exists():
            # Copy all files to backup
            for item in self.scraped_dir.rglob('*'):
                if item.is_file():
                    relative_path = item.relative_to(self.scraped_dir)
                    backup_path = self.backup_dir / relative_path
                    backup_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(item, backup_path)
            
            logging.info(f"Backup created at: {self.backup_dir}")
        else:
            logging.error(f"Scraped directory {self.scraped_dir} not found!")
            return False
        
        return True
    
    def is_valid_image_file(self, file_path):
        """Check if file is a valid image"""
        try:
            with Image.open(file_path) as img:
                img.verify()
            return True
        except Exception:
            return False
    
    def analyze_image_content(self, image_path):
        """Analyze image to determine if it's likely a cat"""
        try:
            with Image.open(image_path) as img:
                # Convert to RGB if necessary
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Get image properties
                width, height = img.size
                aspect_ratio = width / height if height > 0 else 0
                
                # Basic heuristics for cat detection
                cat_indicators = 0
                
                # Check image dimensions (cats are usually not extremely wide or tall)
                if 0.5 <= aspect_ratio <= 2.0:
                    cat_indicators += 1
                
                # Check if image is not too small (likely not a cat if tiny)
                if width >= 100 and height >= 100:
                    cat_indicators += 1
                
                # Check if image is not too large (likely not a cat if massive)
                if width <= 5000 and height <= 5000:
                    cat_indicators += 1
                
                # Get dominant colors (cats often have warm colors)
                try:
                    # Resize for faster processing
                    small_img = img.resize((50, 50))
                    colors = small_img.getcolors(maxcolors=1000)
                    if colors:
                        # Check for warm colors (browns, oranges, etc.)
                        warm_colors = 0
                        total_pixels = sum(count for count, _ in colors)
                        
                        for count, color in colors:
                            r, g, b = color
                            # Check for warm colors (more red/orange than blue)
                            if r > g and r > b and r > 100:
                                warm_colors += count
                        
                        warm_ratio = warm_colors / total_pixels if total_pixels > 0 else 0
                        if warm_ratio > 0.1:  # At least 10% warm colors
                            cat_indicators += 1
                except Exception:
                    pass
                
                # Return confidence score (0-4, higher = more likely to be cat)
                return cat_indicators
                
        except Exception as e:
            logging.error(f"Error analyzing {image_path}: {e}")
            return 0
    
    def check_filename_patterns(self, filename):
        """Check filename for patterns that suggest non-cat content"""
        filename_lower = filename.lower()
        
        # Patterns that suggest non-cat content
        non_cat_patterns = [
            'ad', 'advertisement', 'banner', 'logo', 'icon', 'button',
            'thumb', 'thumbnail', 'preview', 'placeholder', 'dummy',
            'loading', 'error', '404', 'noimage', 'default',
            'illustration', 'drawing', 'cartoon', 'anime', 'manga',
            'graphic', 'design', 'art', 'painting'
        ]
        
        for pattern in non_cat_patterns:
            if pattern in filename_lower:
                return False
        
        # Patterns that suggest cat content
        cat_patterns = [
            'cat', 'foster', 'pet', 'animal', 'kitten', 'kitty'
        ]
        
        for pattern in cat_patterns:
            if pattern in filename_lower:
                return True
        
        return None  # No clear indication
    
    def should_keep_image(self, image_path):
        """Determine if an image should be kept based on multiple criteria"""
        filename = image_path.name
        
        # Check if it's a valid image file
        if not self.is_valid_image_file(image_path):
            logging.info(f"Removing invalid image: {filename}")
            return False
        
        # Check filename patterns first
        filename_result = self.check_filename_patterns(filename)
        if filename_result is False:
            logging.info(f"Removing non-cat image (filename): {filename}")
            return False
        elif filename_result is True:
            logging.info(f"Keeping cat image (filename): {filename}")
            return True
        
        # Analyze image content
        cat_score = self.analyze_image_content(image_path)
        
        # Decision logic
        if cat_score >= 3:
            logging.info(f"Keeping likely cat image (score {cat_score}): {filename}")
            return True
        elif cat_score <= 1:
            logging.info(f"Removing unlikely cat image (score {cat_score}): {filename}")
            return False
        else:
            # Borderline case - keep it to be safe
            logging.info(f"Keeping borderline image (score {cat_score}): {filename}")
            return True
    
    def cleanup_cat_directory(self, cat_dir):
        """Clean up a single cat directory"""
        cat_id = cat_dir.name
        logging.info(f"Cleaning up cat directory: {cat_id}")
        
        # Create cleaned directory
        cleaned_cat_dir = self.cleaned_dir / cat_id
        cleaned_cat_dir.mkdir(exist_ok=True)
        
        # Copy info.json if it exists
        info_file = cat_dir / 'info.json'
        if info_file.exists():
            shutil.copy2(info_file, cleaned_cat_dir / 'info.json')
        
        # Process images
        images_kept = 0
        images_removed = 0
        
        for image_file in cat_dir.glob('*'):
            if image_file.is_file() and image_file.suffix.lower() in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
                self.stats['total_images'] += 1
                
                if self.should_keep_image(image_file):
                    # Keep the image
                    shutil.copy2(image_file, cleaned_cat_dir / image_file.name)
                    images_kept += 1
                    self.stats['kept_images'] += 1
                else:
                    # Remove the image
                    images_removed += 1
                    self.stats['removed_images'] += 1
        
        if images_kept == 0:
            logging.warning(f"No images kept for cat {cat_id}")
            self.stats['failed_cats'] += 1
        else:
            logging.info(f"Cat {cat_id}: {images_kept} kept, {images_removed} removed")
        
        return images_kept > 0
    
    def run_cleanup(self):
        """Run the complete dataset cleanup"""
        logging.info("Starting dataset cleanup...")
        
        # Create backup
        if not self.backup_dataset():
            return False
        
        # Process each cat directory
        cat_dirs = [d for d in self.scraped_dir.iterdir() if d.is_dir() and d.name.startswith('cat_')]
        
        logging.info(f"Found {len(cat_dirs)} cat directories to process")
        
        for cat_dir in cat_dirs:
            try:
                if self.cleanup_cat_directory(cat_dir):
                    self.stats['total_cats'] += 1
            except Exception as e:
                logging.error(f"Error processing {cat_dir}: {e}")
                self.stats['failed_cats'] += 1
        
        # Print final statistics
        self.print_statistics()
        
        return True
    
    def print_statistics(self):
        """Print cleanup statistics"""
        logging.info("\n" + "="*50)
        logging.info("DATASET CLEANUP COMPLETE")
        logging.info("="*50)
        logging.info(f"Total cats processed: {self.stats['total_cats']}")
        logging.info(f"Total images processed: {self.stats['total_images']}")
        logging.info(f"Images kept: {self.stats['kept_images']}")
        logging.info(f"Images removed: {self.stats['removed_images']}")
        logging.info(f"Failed cats: {self.stats['failed_cats']}")
        
        if self.stats['total_images'] > 0:
            keep_percentage = (self.stats['kept_images'] / self.stats['total_images']) * 100
            logging.info(f"Keep rate: {keep_percentage:.1f}%")
        
        logging.info(f"Cleaned dataset saved to: {self.cleaned_dir}")
        logging.info(f"Original backup saved to: {self.backup_dir}")

def main():
    cleanup = DatasetCleanup()
    cleanup.run_cleanup()

if __name__ == "__main__":
    main() 