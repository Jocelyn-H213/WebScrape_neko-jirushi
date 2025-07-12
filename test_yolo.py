#!/usr/bin/env python3
"""
Test script to verify YOLO cat detection works
"""

import sys
from pathlib import Path
from yolo_cat_detector import YOLOCatDetector

def test_yolo_detection():
    """Test YOLO detection on a sample image"""
    print("Testing YOLO cat detection...")
    
    # Initialize detector
    detector = YOLOCatDetector()
    
    # Check if we have any scraped images
    scraped_dir = Path("scraped_cats")
    if not scraped_dir.exists():
        print("No scraped data found. Please run scraping first.")
        return
    
    # Find a sample image
    sample_image = None
    for cat_dir in scraped_dir.iterdir():
        if cat_dir.is_dir() and cat_dir.name.startswith('cat_'):
            for ext in ['.jpg', '.jpeg', '.png']:
                images = list(cat_dir.glob(f"*{ext}"))
                if images:
                    sample_image = images[0]
                    break
            if sample_image:
                break
    
    if not sample_image:
        print("No images found in scraped data.")
        return
    
    print(f"Testing on: {sample_image}")
    
    # Test detection
    result = detector.detect_cats_in_image(sample_image)
    
    print(f"Detection result: {result}")
    
    if result['has_cat']:
        print("✅ Cat detected successfully!")
        print(f"   - Number of detections: {result['detection_count']}")
        print(f"   - Average confidence: {result['avg_confidence']:.3f}")
    else:
        print("❌ No cat detected")
        if 'error' in result:
            print(f"   - Error: {result['error']}")

if __name__ == "__main__":
    test_yolo_detection() 