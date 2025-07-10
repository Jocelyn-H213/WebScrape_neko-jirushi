#!/usr/bin/env python3
"""
Dataset Reorganization Script
Reorganizes scraped_cats into uniform structure for Siamese network training
"""

import os
import json
import shutil
from pathlib import Path
import logging
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('reorganization.log'),
        logging.StreamHandler()
    ]
)

class DatasetReorganizer:
    def __init__(self, scraped_dir="scraped_cats", output_dir="siamese_dataset"):
        self.scraped_dir = Path(scraped_dir)
        self.output_dir = Path(output_dir)
        self.cat_counter = 1
        
    def create_output_structure(self):
        """Create the output directory structure"""
        if self.output_dir.exists():
            shutil.rmtree(self.output_dir)
        self.output_dir.mkdir(exist_ok=True)
        logging.info(f"Created output directory: {self.output_dir}")
        
    def get_cat_name_from_info(self, info_file):
        """Extract cat name from info.json file"""
        try:
            with open(info_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Try different possible name fields
            name_fields = ['name', 'cat_name', 'title', 'catch_copy']
            for field in name_fields:
                if field in data and data[field]:
                    return str(data[field]).strip()
            
            # If no name found, use cat_id
            if 'cat_id' in data:
                return f"cat_{data['cat_id']}"
            
            return "unknown_cat"
            
        except Exception as e:
            logging.warning(f"Error reading info file {info_file}: {e}")
            return "unknown_cat"
    
    def clean_filename(self, name):
        """Clean filename for safe directory naming"""
        # Remove special characters and spaces
        cleaned = re.sub(r'[^\w\s-]', '', name)
        cleaned = re.sub(r'[-\s]+', '_', cleaned)
        cleaned = cleaned.strip('_')
        
        # Limit length
        if len(cleaned) > 50:
            cleaned = cleaned[:50]
            
        return cleaned or "unknown_cat"
    
    def process_cat_directory(self, cat_dir):
        """Process a single cat directory"""
        cat_dir = Path(cat_dir)
        
        # Find info.json file
        info_file = cat_dir / "info.json"
        if not info_file.exists():
            logging.warning(f"No info.json found in {cat_dir}")
            return None
            
        # Get cat name
        cat_name = self.get_cat_name_from_info(info_file)
        clean_name = self.clean_filename(cat_name)
        
        # Create new directory name
        new_dir_name = f"cat_{self.cat_counter:04d}_{clean_name}"
        new_dir_path = self.output_dir / new_dir_name
        
        # Create new directory
        new_dir_path.mkdir(exist_ok=True)
        
        # Copy info.json
        shutil.copy2(info_file, new_dir_path / "info.json")
        
        # Copy all image files
        image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
        images_copied = 0
        
        for file_path in cat_dir.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in image_extensions:
                # Rename image to consistent format
                new_image_name = f"image_{images_copied+1:03d}{file_path.suffix.lower()}"
                shutil.copy2(file_path, new_dir_path / new_image_name)
                images_copied += 1
        
        logging.info(f"Processed {cat_dir.name} -> {new_dir_name} ({images_copied} images)")
        self.cat_counter += 1
        
        return {
            'original_dir': str(cat_dir),
            'new_dir': str(new_dir_path),
            'cat_name': cat_name,
            'images_count': images_copied
        }
    
    def process_data_images_structure(self):
        """Process the data/ and images/ structure"""
        data_dir = self.scraped_dir / "data"
        images_dir = self.scraped_dir / "images"
        
        if not data_dir.exists() or not images_dir.exists():
            logging.info("No data/images structure found")
            return
            
        # Get all JSON files from data directory
        json_files = list(data_dir.glob("*.json"))
        logging.info(f"Found {len(json_files)} JSON files in data directory")
        
        for json_file in json_files:
            try:
                # Extract cat name from filename
                cat_name = json_file.stem
                clean_name = self.clean_filename(cat_name)
                
                # Create new directory name
                new_dir_name = f"cat_{self.cat_counter:04d}_{clean_name}"
                new_dir_path = self.output_dir / new_dir_name
                new_dir_path.mkdir(exist_ok=True)
                
                # Copy info.json
                shutil.copy2(json_file, new_dir_path / "info.json")
                
                # Find corresponding images directory
                images_subdir = images_dir / cat_name
                images_copied = 0
                
                if images_subdir.exists() and images_subdir.is_dir():
                    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
                    
                    for file_path in images_subdir.iterdir():
                        if file_path.is_file() and file_path.suffix.lower() in image_extensions:
                            new_image_name = f"image_{images_copied+1:03d}{file_path.suffix.lower()}"
                            shutil.copy2(file_path, new_dir_path / new_image_name)
                            images_copied += 1
                
                logging.info(f"Processed {cat_name} -> {new_dir_name} ({images_copied} images)")
                self.cat_counter += 1
                
            except Exception as e:
                logging.error(f"Error processing {json_file}: {e}")
                continue
    
    def reorganize(self):
        """Main reorganization function"""
        logging.info("Starting dataset reorganization...")
        
        # Create output structure
        self.create_output_structure()
        
        # Process cat_XXXXXX directories
        cat_dirs = [d for d in self.scraped_dir.iterdir() 
                   if d.is_dir() and d.name.startswith('cat_')]
        
        logging.info(f"Found {len(cat_dirs)} cat_XXXXXX directories")
        
        processed_cats = []
        for cat_dir in cat_dirs:
            result = self.process_cat_directory(cat_dir)
            if result:
                processed_cats.append(result)
        
        # Process data/images structure
        self.process_data_images_structure()
        
        # Create summary
        total_cats = len(list(self.output_dir.iterdir()))
        total_images = sum(len(list(d.glob("image_*"))) for d in self.output_dir.iterdir() if d.is_dir())
        
        logging.info(f"Reorganization complete!")
        logging.info(f"Total cats processed: {total_cats}")
        logging.info(f"Total images: {total_images}")
        
        # Save summary
        summary = {
            'total_cats': total_cats,
            'total_images': total_images,
            'processed_cats': processed_cats
        }
        
        with open(self.output_dir / "reorganization_summary.json", 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        return summary

if __name__ == "__main__":
    reorganizer = DatasetReorganizer()
    summary = reorganizer.reorganize()
    print(f"\n🎉 Reorganization complete!")
    print(f"📁 Output directory: siamese_dataset/")
    print(f"🐱 Total cats: {summary['total_cats']}")
    print(f"🖼️  Total images: {summary['total_images']}") 