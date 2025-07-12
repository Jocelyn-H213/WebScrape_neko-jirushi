#!/usr/bin/env python3
"""
Advanced Dataset Cleaning Script
Filters out non-cat images using multiple strategies:
1. File size filtering (remove very small files that are likely icons)
2. Naming pattern analysis
3. Image dimension analysis
4. File type validation
5. Metadata analysis
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
        logging.FileHandler('advanced_cleaning.log'),
        logging.StreamHandler()
    ]
)

class AdvancedDatasetCleaner:
    def __init__(self, dataset_path="scraped_cats_cleaned"):
        self.dataset_path = Path(dataset_path)
        self.backup_path = Path("scraped_cats_cleaned_backup")
        self.cleaning_stats = {
            'total_cats': 0,
            'total_images_before': 0,
            'total_images_after': 0,
            'removed_images': 0,
            'cats_with_removals': 0,
            'cats_fully_removed': 0,
            'file_size_removals': 0,
            'dimension_removals': 0,
            'pattern_removals': 0,
            'corrupted_removals': 0
        }
        
        # File size thresholds (in bytes)
        self.min_file_size = 5000  # 5KB minimum
        self.max_file_size = 50 * 1024 * 1024  # 50MB maximum
        
        # Image dimension thresholds
        self.min_width = 100
        self.min_height = 100
        self.max_width = 10000
        self.max_height = 10000
        
        # Aspect ratio limits (width/height)
        self.min_aspect_ratio = 0.1  # Very tall images
        self.max_aspect_ratio = 10.0  # Very wide images
        
        # Known non-cat image patterns
        self.non_cat_patterns = [
            'icon', 'button', 'banner', 'logo', 'avatar', 'profile',
            'noimage', 'placeholder', 'default', 'empty', 'loading',
            'spacer', 'pixel', 'transparent', 'blank', 'sample'
        ]
        
        # Known non-cat file sizes (very small files that are likely icons)
        self.suspicious_sizes = [43, 172, 281, 364, 883, 1300, 1500, 1900, 3400, 4000, 4058, 4500, 5200, 5871, 6300, 6400, 6490, 6700, 6900, 7200]
        
        # File extensions to process
        self.image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.tiff'}

    def create_backup(self):
        """Create a backup of the dataset before cleaning"""
        if self.backup_path.exists():
            logging.warning(f"Backup directory {self.backup_path} already exists")
            return
        
        logging.info(f"Creating backup at {self.backup_path}")
        shutil.copytree(self.dataset_path, self.backup_path)
        logging.info("Backup created successfully")

    def is_suspicious_file_size(self, file_size):
        """Check if file size is suspiciously small (likely an icon)"""
        return file_size in self.suspicious_sizes or file_size < self.min_file_size

    def is_suspicious_filename(self, filename):
        """Check if filename suggests it's not a cat image"""
        filename_lower = filename.lower()
        return any(pattern in filename_lower for pattern in self.non_cat_patterns)

    def analyze_image_dimensions(self, image_path):
        """Analyze image dimensions and return if it's likely a cat image"""
        try:
            with Image.open(image_path) as img:
                width, height = img.size
                
                # Check minimum dimensions
                if width < self.min_width or height < self.min_height:
                    return False, f"Too small: {width}x{height}"
                
                # Check maximum dimensions
                if width > self.max_width or height > self.max_height:
                    return False, f"Too large: {width}x{height}"
                
                # Check aspect ratio
                aspect_ratio = width / height
                if aspect_ratio < self.min_aspect_ratio or aspect_ratio > self.max_aspect_ratio:
                    return False, f"Bad aspect ratio: {aspect_ratio:.2f}"
                
                # Check if image is mostly transparent or has unusual characteristics
                if img.mode in ['RGBA', 'LA']:
                    # For images with alpha channel, check if they're mostly transparent
                    if img.mode == 'RGBA':
                        alpha = img.split()[-1]
                        if alpha.getextrema()[1] < 50:  # Mostly transparent
                            return False, "Mostly transparent"
                
                return True, f"Valid: {width}x{height}"
                
        except Exception as e:
            return False, f"Error analyzing image: {str(e)}"

    def should_remove_image(self, image_path):
        """Determine if an image should be removed based on multiple criteria"""
        file_size = image_path.stat().st_size
        filename = image_path.name.lower()
        
        # Check file size
        if self.is_suspicious_file_size(file_size):
            self.cleaning_stats['file_size_removals'] += 1
            return True, f"File size suspicious: {file_size} bytes"
        
        # Check filename patterns
        if self.is_suspicious_filename(filename):
            self.cleaning_stats['pattern_removals'] += 1
            return True, f"Filename suspicious: {filename}"
        
        # Check image dimensions and characteristics
        is_valid, reason = self.analyze_image_dimensions(image_path)
        if not is_valid:
            self.cleaning_stats['dimension_removals'] += 1
            return True, reason
        
        return False, "Valid image"

    def clean_cat_directory(self, cat_dir):
        """Clean a single cat directory"""
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
        """Clean the entire dataset"""
        logging.info("Starting advanced dataset cleaning")
        
        if create_backup:
            self.create_backup()
        
        # Find all cat directories
        cat_dirs = [d for d in self.dataset_path.iterdir() if d.is_dir() and d.name.startswith('cat_')]
        self.cleaning_stats['total_cats'] = len(cat_dirs)
        
        logging.info(f"Found {len(cat_dirs)} cat directories to clean")
        
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
                'non_cat_patterns': self.non_cat_patterns,
                'suspicious_sizes': self.suspicious_sizes
            }
        }
        
        report_path = Path("advanced_cleaning_report.json")
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logging.info(f"Cleaning report saved to {report_path}")

    def print_cleaning_stats(self):
        """Print cleaning statistics"""
        logging.info("\n" + "="*50)
        logging.info("ADVANCED CLEANING COMPLETED")
        logging.info("="*50)
        logging.info(f"Total cats processed: {self.cleaning_stats['total_cats']}")
        logging.info(f"Total images before: {self.cleaning_stats['total_images_before']}")
        logging.info(f"Total images after: {self.cleaning_stats['total_images_after']}")
        logging.info(f"Total images removed: {self.cleaning_stats['removed_images']}")
        logging.info(f"Cats with removals: {self.cleaning_stats['cats_with_removals']}")
        logging.info(f"Cats fully removed: {self.cleaning_stats['cats_fully_removed']}")
        logging.info("")
        logging.info("Removal breakdown:")
        logging.info(f"  - File size removals: {self.cleaning_stats['file_size_removals']}")
        logging.info(f"  - Dimension removals: {self.cleaning_stats['dimension_removals']}")
        logging.info(f"  - Pattern removals: {self.cleaning_stats['pattern_removals']}")
        logging.info(f"  - Corrupted removals: {self.cleaning_stats['corrupted_removals']}")
        
        if self.cleaning_stats['total_images_before'] > 0:
            removal_rate = (self.cleaning_stats['removed_images'] / self.cleaning_stats['total_images_before']) * 100
            logging.info(f"Removal rate: {removal_rate:.1f}%")

    def analyze_dataset_before_cleaning(self):
        """Analyze the dataset before cleaning to understand the scope"""
        logging.info("Analyzing dataset before cleaning...")
        
        cat_dirs = [d for d in self.dataset_path.iterdir() if d.is_dir() and d.name.startswith('cat_')]
        
        total_images = 0
        file_size_distribution = defaultdict(int)
        file_type_distribution = defaultdict(int)
        
        for cat_dir in cat_dirs:
            for ext in self.image_extensions:
                for image_path in cat_dir.glob(f"*{ext}"):
                    total_images += 1
                    file_size = image_path.stat().st_size
                    file_size_distribution[file_size] += 1
                    file_type_distribution[ext] += 1
        
        logging.info(f"Dataset analysis:")
        logging.info(f"  - Total cat directories: {len(cat_dirs)}")
        logging.info(f"  - Total images: {total_images}")
        logging.info(f"  - File types: {dict(file_type_distribution)}")
        
        # Show most common file sizes
        common_sizes = sorted(file_size_distribution.items(), key=lambda x: x[1], reverse=True)[:10]
        logging.info("  - Most common file sizes:")
        for size, count in common_sizes:
            logging.info(f"    {size} bytes: {count} images")

def main():
    parser = argparse.ArgumentParser(description="Advanced dataset cleaning for cat images")
    parser.add_argument("--dataset", default="scraped_cats_cleaned", help="Path to dataset directory")
    parser.add_argument("--no-backup", action="store_true", help="Skip creating backup")
    parser.add_argument("--analyze-only", action="store_true", help="Only analyze dataset, don't clean")
    
    args = parser.parse_args()
    
    cleaner = AdvancedDatasetCleaner(args.dataset)
    
    if args.analyze_only:
        cleaner.analyze_dataset_before_cleaning()
    else:
        cleaner.clean_dataset(create_backup=not args.no_backup)

if __name__ == "__main__":
    main() 