#!/usr/bin/env python3
"""
Aggressive Dataset Cleaning Script
Uses very strict criteria to ensure only actual cat photos remain:
1. Much higher minimum dimensions (300x300)
2. Duplicate image detection and removal
3. Image content analysis
4. Aspect ratio validation
5. File size validation
"""

import os
import json
import shutil
import logging
from pathlib import Path
from PIL import Image
import hashlib
from collections import defaultdict
import argparse
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('aggressive_cleaning.log'),
        logging.StreamHandler()
    ]
)

class AggressiveDatasetCleaner:
    def __init__(self, dataset_path="scraped_cats_cleaned"):
        self.dataset_path = Path(dataset_path)
        self.backup_path = Path("scraped_cats_cleaned_aggressive_backup")
        self.cleaning_stats = {
            'total_cats': 0,
            'total_images_before': 0,
            'total_images_after': 0,
            'removed_images': 0,
            'cats_with_removals': 0,
            'cats_fully_removed': 0,
            'dimension_removals': 0,
            'duplicate_removals': 0,
            'file_size_removals': 0,
            'aspect_ratio_removals': 0,
            'content_removals': 0
        }
        
        # Much stricter file size thresholds
        self.min_file_size = 10000  # 10KB minimum (was 5KB)
        self.max_file_size = 20 * 1024 * 1024  # 20MB maximum (was 50MB)
        
        # Much stricter image dimension thresholds
        self.min_width = 300  # Was 100
        self.min_height = 300  # Was 100
        self.max_width = 8000  # Was 10000
        self.max_height = 8000  # Was 10000
        
        # Stricter aspect ratio limits
        self.min_aspect_ratio = 0.3  # Was 0.1 (allow less extreme ratios)
        self.max_aspect_ratio = 3.0  # Was 10.0 (allow less extreme ratios)
        
        # Known problematic file sizes (logos, icons)
        self.problematic_sizes = [5276, 6490, 5871, 4058, 4560, 3480, 1964, 4634, 2713, 883, 1505, 1320, 2326, 4356]
        
        # File extensions to process
        self.image_extensions = {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tiff'}
        
        # Track duplicate images across cats
        self.duplicate_hashes = defaultdict(list)

    def create_backup(self):
        """Create a backup of the dataset before cleaning"""
        if self.backup_path.exists():
            logging.warning(f"Backup directory {self.backup_path} already exists")
            return
        
        logging.info(f"Creating backup at {self.backup_path}")
        shutil.copytree(self.dataset_path, self.backup_path)
        logging.info("Backup created successfully")

    def calculate_image_hash(self, image_path):
        """Calculate hash of image content to detect duplicates"""
        try:
            with open(image_path, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except Exception as e:
            logging.error(f"Error calculating hash for {image_path}: {e}")
            return None

    def analyze_image_content(self, image_path):
        """Analyze image content to detect if it's likely a cat photo"""
        try:
            with Image.open(image_path) as img:
                width, height = img.size
                
                # Check if image is too small (likely a logo/icon)
                if width < self.min_width or height < self.min_height:
                    return False, f"Too small: {width}x{height} (min: {self.min_width}x{self.min_height})"
                
                # Check if image is too large (likely an error)
                if width > self.max_width or height > self.max_height:
                    return False, f"Too large: {width}x{height}"
                
                # Check aspect ratio
                aspect_ratio = width / height
                if aspect_ratio < self.min_aspect_ratio or aspect_ratio > self.max_aspect_ratio:
                    return False, f"Bad aspect ratio: {aspect_ratio:.2f}"
                
                # Check if image is mostly transparent or has unusual characteristics
                if img.mode in ['RGBA', 'LA']:
                    if img.mode == 'RGBA':
                        alpha = img.split()[-1]
                        if alpha.getextrema()[1] < 50:  # Mostly transparent
                            return False, "Mostly transparent"
                
                # Check if image is mostly one color (likely a logo/icon)
                if img.mode in ['RGB', 'RGBA']:
                    # Convert to RGB if needed
                    if img.mode == 'RGBA':
                        rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                        rgb_img.paste(img, mask=img.split()[-1])
                    else:
                        rgb_img = img
                    
                    # Get color statistics
                    colors = rgb_img.getcolors(maxcolors=10000)
                    if colors:
                        total_pixels = sum(count for count, _ in colors)
                        if total_pixels > 0:
                            # Check if more than 80% of pixels are the same color
                            max_color_count = max(count for count, _ in colors)
                            if max_color_count / total_pixels > 0.8:
                                return False, "Too uniform (likely logo/icon)"
                
                return True, f"Valid cat image: {width}x{height}"
                
        except Exception as e:
            return False, f"Error analyzing image: {str(e)}"

    def should_remove_image(self, image_path):
        """Determine if an image should be removed based on strict criteria"""
        file_size = image_path.stat().st_size
        filename = image_path.name.lower()
        
        # Check file size
        if file_size < self.min_file_size:
            self.cleaning_stats['file_size_removals'] += 1
            return True, f"File too small: {file_size} bytes (min: {self.min_file_size})"
        
        if file_size > self.max_file_size:
            self.cleaning_stats['file_size_removals'] += 1
            return True, f"File too large: {file_size} bytes (max: {self.max_file_size})"
        
        # Check for known problematic sizes
        if file_size in self.problematic_sizes:
            self.cleaning_stats['file_size_removals'] += 1
            return True, f"Known problematic size: {file_size} bytes"
        
        # Check image content and dimensions
        is_valid, reason = self.analyze_image_content(image_path)
        if not is_valid:
            self.cleaning_stats['content_removals'] += 1
            return True, reason
        
        return False, "Valid cat image"

    def find_and_remove_duplicates(self):
        """Find and remove duplicate images across all cats"""
        logging.info("Scanning for duplicate images...")
        
        # First pass: calculate hashes for all images
        all_images = []
        for cat_dir in self.dataset_path.iterdir():
            if cat_dir.is_dir() and cat_dir.name.startswith('cat_'):
                for ext in self.image_extensions:
                    for image_path in cat_dir.glob(f"*{ext}"):
                        image_hash = self.calculate_image_hash(image_path)
                        if image_hash:
                            all_images.append((image_path, image_hash))
                            self.duplicate_hashes[image_hash].append(image_path)
        
        # Find duplicates
        duplicates_removed = 0
        for image_hash, image_paths in self.duplicate_hashes.items():
            if len(image_paths) > 1:
                # Keep the first one, remove the rest
                for image_path in image_paths[1:]:
                    try:
                        image_path.unlink()
                        duplicates_removed += 1
                        self.cleaning_stats['duplicate_removals'] += 1
                        logging.debug(f"Removed duplicate: {image_path}")
                    except Exception as e:
                        logging.error(f"Failed to remove duplicate {image_path}: {e}")
        
        logging.info(f"Removed {duplicates_removed} duplicate images")
        return duplicates_removed

    def clean_cat_directory(self, cat_dir):
        """Clean a single cat directory with aggressive criteria"""
        cat_id = cat_dir.name
        logging.info(f"Cleaning cat directory: {cat_id}")
        
        # Find all image files
        image_files = []
        for ext in self.image_extensions:
            image_files.extend(cat_dir.glob(f"*{ext}"))
            image_files.extend(cat_dir.glob(f"*{ext.upper()}"))
        
        images_before = len(image_files)
        self.cleaning_stats['total_images_before'] += images_before
        
        removed_images = []
        valid_images = []
        
        for image_path in image_files:
            should_remove, reason = self.should_remove_image(image_path)
            
            if should_remove:
                removed_images.append((image_path, reason))
                self.cleaning_stats['removed_images'] += 1
            else:
                valid_images.append(image_path)
        
        # Remove suspicious images
        for image_path, reason in removed_images:
            try:
                image_path.unlink()
                logging.debug(f"Removed {image_path.name}: {reason}")
            except Exception as e:
                logging.error(f"Failed to remove {image_path}: {e}")
        
        images_after = len(valid_images)
        self.cleaning_stats['total_images_after'] += images_after
        
        # Update statistics
        if removed_images:
            self.cleaning_stats['cats_with_removals'] += 1
        
        if images_after == 0:
            self.cleaning_stats['cats_fully_removed'] += 1
            logging.warning(f"All images removed from {cat_id}")
        
        logging.info(f"{cat_id}: {images_before} -> {images_after} images ({len(removed_images)} removed)")
        
        return {
            'cat_id': cat_id,
            'images_before': images_before,
            'images_after': images_after,
            'removed_count': len(removed_images),
            'removed_reasons': [reason for _, reason in removed_images]
        }

    def clean_dataset(self, create_backup=True):
        """Clean the entire dataset with aggressive criteria"""
        logging.info("Starting aggressive dataset cleaning")
        
        if create_backup:
            self.create_backup()
        
        # Find all cat directories
        cat_dirs = [d for d in self.dataset_path.iterdir() if d.is_dir() and d.name.startswith('cat_')]
        self.cleaning_stats['total_cats'] = len(cat_dirs)
        
        logging.info(f"Found {len(cat_dirs)} cat directories to clean")
        
        # First, remove duplicates across all cats
        self.find_and_remove_duplicates()
        
        # Then clean individual cat directories
        cleaning_results = []
        
        for cat_dir in cat_dirs:
            try:
                result = self.clean_cat_directory(cat_dir)
                cleaning_results.append(result)
            except Exception as e:
                logging.error(f"Error cleaning {cat_dir}: {e}")
        
        # Save cleaning report
        self.save_cleaning_report(cleaning_results)
        
        # Print final statistics
        self.print_cleaning_stats()
        
        return cleaning_results

    def save_cleaning_report(self, cleaning_results):
        """Save detailed cleaning report"""
        report = {
            'cleaning_timestamp': datetime.now().isoformat(),
            'dataset_path': str(self.dataset_path),
            'backup_path': str(self.backup_path),
            'statistics': self.cleaning_stats,
            'detailed_results': cleaning_results,
            'removal_criteria': {
                'min_file_size': self.min_file_size,
                'max_file_size': self.max_file_size,
                'min_dimensions': f"{self.min_width}x{self.min_height}",
                'max_dimensions': f"{self.max_width}x{self.max_height}",
                'aspect_ratio_limits': f"{self.min_aspect_ratio}-{self.max_aspect_ratio}",
                'problematic_sizes': self.problematic_sizes
            }
        }
        
        report_path = Path("aggressive_cleaning_report.json")
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logging.info(f"Cleaning report saved to {report_path}")

    def print_cleaning_stats(self):
        """Print cleaning statistics"""
        logging.info("\n" + "="*50)
        logging.info("AGGRESSIVE CLEANING COMPLETED")
        logging.info("="*50)
        logging.info(f"Total cats processed: {self.cleaning_stats['total_cats']}")
        logging.info(f"Total images before: {self.cleaning_stats['total_images_before']}")
        logging.info(f"Total images after: {self.cleaning_stats['total_images_after']}")
        logging.info(f"Total images removed: {self.cleaning_stats['removed_images']}")
        logging.info(f"Cats with removals: {self.cleaning_stats['cats_with_removals']}")
        logging.info(f"Cats fully removed: {self.cleaning_stats['cats_fully_removed']}")
        logging.info("")
        logging.info("Removal breakdown:")
        logging.info(f"  - Content removals: {self.cleaning_stats['content_removals']}")
        logging.info(f"  - Duplicate removals: {self.cleaning_stats['duplicate_removals']}")
        logging.info(f"  - File size removals: {self.cleaning_stats['file_size_removals']}")
        
        if self.cleaning_stats['total_images_before'] > 0:
            removal_rate = (self.cleaning_stats['removed_images'] / self.cleaning_stats['total_images_before']) * 100
            logging.info(f"Removal rate: {removal_rate:.1f}%")

def main():
    parser = argparse.ArgumentParser(description="Aggressive dataset cleaning for cat images")
    parser.add_argument("--dataset", default="scraped_cats_cleaned", help="Path to dataset directory")
    parser.add_argument("--no-backup", action="store_true", help="Skip creating backup")
    
    args = parser.parse_args()
    
    cleaner = AggressiveDatasetCleaner(args.dataset)
    cleaner.clean_dataset(create_backup=not args.no_backup)

if __name__ == "__main__":
    main() 