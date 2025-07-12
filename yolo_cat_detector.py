#!/usr/bin/env python3
"""
YOLO-based Cat Detection and Filtering Script
Uses YOLOv8 to detect cats in images and filters out non-cat images
"""

import os
import json
import shutil
import logging
from pathlib import Path
from PIL import Image
import cv2
import numpy as np
from ultralytics import YOLO
import argparse
from datetime import datetime
from collections import defaultdict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('yolo_cat_detection.log'),
        logging.StreamHandler()
    ]
)

class YOLOCatDetector:
    def __init__(self, dataset_path="scraped_cats", confidence_threshold=0.3):
        self.dataset_path = Path(dataset_path)
        self.backup_path = Path("scraped_cats_yolo_backup")
        self.confidence_threshold = confidence_threshold
        
        # Detection statistics
        self.detection_stats = {
            'total_cats': 0,
            'total_images_before': 0,
            'total_images_after': 0,
            'removed_images': 0,
            'cats_with_removals': 0,
            'cats_fully_removed': 0,
            'images_with_cats': 0,
            'images_without_cats': 0,
            'total_detections': 0,
            'avg_confidence': 0.0
        }
        
        # Cat class ID in COCO dataset (YOLO uses COCO classes)
        self.cat_class_id = 16  # Cat is class 16 in COCO
        
        # File extensions to process
        self.image_extensions = {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tiff'}
        
        # Initialize YOLO model
        self.model = None
        self.initialize_model()
    
    def initialize_model(self):
        """Initialize YOLO model for cat detection"""
        try:
            logging.info("Loading YOLOv8 model...")
            # Use YOLOv8n (nano) for faster processing, or YOLOv8s (small) for better accuracy
            self.model = YOLO('yolov8n.pt')  # or 'yolov8s.pt' for better accuracy
            logging.info("YOLO model loaded successfully")
        except Exception as e:
            logging.error(f"Failed to load YOLO model: {e}")
            logging.info("Attempting to download model...")
            try:
                self.model = YOLO('yolov8n.pt')
                logging.info("YOLO model downloaded and loaded successfully")
            except Exception as e2:
                logging.error(f"Failed to download YOLO model: {e2}")
                raise

    def create_backup(self):
        """Create a backup of the dataset before processing"""
        if self.backup_path.exists():
            logging.warning(f"Backup directory {self.backup_path} already exists")
            return
        
        logging.info(f"Creating backup at {self.backup_path}")
        shutil.copytree(self.dataset_path, self.backup_path)
        logging.info("Backup created successfully")

    def detect_cats_in_image(self, image_path):
        """Detect cats in a single image using YOLO"""
        try:
            # Run YOLO detection
            results = self.model(image_path, verbose=False)
            
            cat_detections = []
            total_confidence = 0.0
            detection_count = 0
            
            for result in results:
                if result.boxes is not None:
                    for box in result.boxes:
                        # Check if detected object is a cat (class 16)
                        if int(box.cls) == self.cat_class_id:
                            confidence = float(box.conf)
                            if confidence >= self.confidence_threshold:
                                cat_detections.append({
                                    'confidence': confidence,
                                    'bbox': box.xyxy[0].cpu().numpy().tolist()  # [x1, y1, x2, y2]
                                })
                                total_confidence += confidence
                                detection_count += 1
            
            avg_confidence = total_confidence / len(cat_detections) if cat_detections else 0.0
            
            return {
                'has_cat': len(cat_detections) > 0,
                'detections': cat_detections,
                'detection_count': len(cat_detections),
                'avg_confidence': avg_confidence,
                'total_confidence': total_confidence
            }
            
        except Exception as e:
            logging.error(f"Error detecting cats in {image_path}: {e}")
            return {
                'has_cat': False,
                'detections': [],
                'detection_count': 0,
                'avg_confidence': 0.0,
                'total_confidence': 0.0,
                'error': str(e)
            }

    def process_cat_directory(self, cat_dir):
        """Process a single cat directory with YOLO detection"""
        cat_id = cat_dir.name
        logging.info(f"Processing cat directory: {cat_id}")
        
        # Find all image files
        image_files = []
        for ext in self.image_extensions:
            image_files.extend(cat_dir.glob(f"*{ext}"))
            image_files.extend(cat_dir.glob(f"*{ext.upper()}"))
        
        images_before = len(image_files)
        self.detection_stats['total_images_before'] += images_before
        
        removed_images = []
        valid_images = []
        detection_results = []
        
        for image_path in image_files:
            detection_result = self.detect_cats_in_image(image_path)
            detection_results.append({
                'image_path': str(image_path),
                'detection_result': detection_result
            })
            
            if detection_result['has_cat']:
                valid_images.append(image_path)
                self.detection_stats['images_with_cats'] += 1
                self.detection_stats['total_detections'] += detection_result['detection_count']
                self.detection_stats['avg_confidence'] += detection_result['total_confidence']
            else:
                removed_images.append((image_path, detection_result))
                self.detection_stats['images_without_cats'] += 1
        
        # Remove images without cats
        for image_path, detection_result in removed_images:
            try:
                image_path.unlink()
                logging.debug(f"Removed {image_path.name}: No cat detected (confidence: {detection_result.get('avg_confidence', 0):.3f})")
            except Exception as e:
                logging.error(f"Failed to remove {image_path}: {e}")
        
        images_after = len(valid_images)
        self.detection_stats['total_images_after'] += images_after
        self.detection_stats['removed_images'] += len(removed_images)
        
        # Update statistics
        if removed_images:
            self.detection_stats['cats_with_removals'] += 1
        
        if images_after == 0:
            self.detection_stats['cats_fully_removed'] += 1
            logging.warning(f"All images removed from {cat_id} (no cats detected)")
        
        logging.info(f"{cat_id}: {images_before} -> {images_after} images ({len(removed_images)} removed)")
        
        return {
            'cat_id': cat_id,
            'images_before': images_before,
            'images_after': images_after,
            'removed_count': len(removed_images),
            'detection_results': detection_results
        }

    def process_dataset(self, create_backup=True):
        """Process the entire dataset with YOLO cat detection"""
        logging.info("Starting YOLO-based cat detection and filtering")
        
        if create_backup:
            self.create_backup()
        
        # Find all cat directories
        cat_dirs = [d for d in self.dataset_path.iterdir() if d.is_dir() and d.name.startswith('cat_')]
        self.detection_stats['total_cats'] = len(cat_dirs)
        
        logging.info(f"Found {len(cat_dirs)} cat directories to process")
        
        processing_results = []
        
        for cat_dir in cat_dirs:
            try:
                result = self.process_cat_directory(cat_dir)
                processing_results.append(result)
            except Exception as e:
                logging.error(f"Error processing {cat_dir}: {e}")
        
        # Calculate average confidence
        if self.detection_stats['total_detections'] > 0:
            self.detection_stats['avg_confidence'] /= self.detection_stats['total_detections']
        
        # Save detection report
        self.save_detection_report(processing_results)
        
        # Print final statistics
        self.print_detection_stats()
        
        return processing_results

    def save_detection_report(self, processing_results):
        """Save detailed detection report"""
        report = {
            'detection_timestamp': datetime.now().isoformat(),
            'dataset_path': str(self.dataset_path),
            'backup_path': str(self.backup_path),
            'statistics': self.detection_stats,
            'detection_settings': {
                'model': 'yolov8n.pt',
                'confidence_threshold': self.confidence_threshold,
                'cat_class_id': self.cat_class_id
            },
            'detailed_results': processing_results
        }
        
        report_path = Path("yolo_detection_report.json")
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logging.info(f"Detection report saved to {report_path}")

    def print_detection_stats(self):
        """Print detection statistics"""
        logging.info("\n" + "="*50)
        logging.info("YOLO CAT DETECTION COMPLETED")
        logging.info("="*50)
        logging.info(f"Total cats processed: {self.detection_stats['total_cats']}")
        logging.info(f"Total images before: {self.detection_stats['total_images_before']}")
        logging.info(f"Total images after: {self.detection_stats['total_images_after']}")
        logging.info(f"Total images removed: {self.detection_stats['removed_images']}")
        logging.info(f"Cats with removals: {self.detection_stats['cats_with_removals']}")
        logging.info(f"Cats fully removed: {self.detection_stats['cats_fully_removed']}")
        logging.info("")
        logging.info("Detection breakdown:")
        logging.info(f"  - Images with cats detected: {self.detection_stats['images_with_cats']}")
        logging.info(f"  - Images without cats: {self.detection_stats['images_without_cats']}")
        logging.info(f"  - Total cat detections: {self.detection_stats['total_detections']}")
        logging.info(f"  - Average confidence: {self.detection_stats['avg_confidence']:.3f}")
        
        if self.detection_stats['total_images_before'] > 0:
            removal_rate = (self.detection_stats['removed_images'] / self.detection_stats['total_images_before']) * 100
            logging.info(f"Removal rate: {removal_rate:.1f}%")

    def test_detection(self, test_image_path):
        """Test cat detection on a single image"""
        if not self.model:
            logging.error("YOLO model not initialized")
            return
        
        logging.info(f"Testing cat detection on: {test_image_path}")
        result = self.detect_cats_in_image(test_image_path)
        
        logging.info(f"Detection result: {result}")
        return result

def main():
    parser = argparse.ArgumentParser(description="YOLO-based cat detection and filtering")
    parser.add_argument("--dataset", default="scraped_cats", help="Path to dataset directory")
    parser.add_argument("--confidence", type=float, default=0.3, help="Confidence threshold for cat detection")
    parser.add_argument("--no-backup", action="store_true", help="Skip creating backup")
    parser.add_argument("--test", help="Test detection on a single image")
    
    args = parser.parse_args()
    
    detector = YOLOCatDetector(args.dataset, args.confidence)
    
    if args.test:
        detector.test_detection(args.test)
    else:
        detector.process_dataset(create_backup=not args.no_backup)

if __name__ == "__main__":
    main() 