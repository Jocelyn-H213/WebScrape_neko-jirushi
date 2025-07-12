#!/usr/bin/env python3
"""
Complete Cat Dataset Pipeline
Orchestrates the entire process: scraping -> YOLO detection -> optional reorganization
"""

import os
import sys
import json
import logging
import argparse
from pathlib import Path
from datetime import datetime
import subprocess

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('complete_pipeline.log'),
        logging.StreamHandler()
    ]
)

class CompletePipeline:
    def __init__(self):
        self.pipeline_stats = {
            'start_time': None,
            'end_time': None,
            'scraping_completed': False,
            'yolo_detection_completed': False,
            'reorganization_completed': False,
            'errors': []
        }
        
        # Pipeline configuration
        self.config = {
            'scraping_target': 100,  # Number of cats to scrape
            'yolo_confidence': 0.3,  # YOLO confidence threshold
            'reorganize': True,      # Whether to reorganize after YOLO detection
            'backup_enabled': True   # Whether to create backups
        }

    def run_command(self, command, description):
        """Run a command and handle errors"""
        logging.info(f"Running: {description}")
        logging.info(f"Command: {command}")
        
        try:
            result = subprocess.run(command, shell=True, check=True, 
                                  capture_output=True, text=True)
            logging.info(f"✅ {description} completed successfully")
            if result.stdout:
                logging.debug(f"Output: {result.stdout}")
            return True
        except subprocess.CalledProcessError as e:
            error_msg = f"❌ {description} failed: {e.stderr}"
            logging.error(error_msg)
            self.pipeline_stats['errors'].append(error_msg)
            return False

    def step_1_scraping(self):
        """Step 1: Run the comprehensive scraper"""
        logging.info("\n" + "="*60)
        logging.info("STEP 1: WEB SCRAPING")
        logging.info("="*60)
        
        command = f"python comprehensive_scraper.py --target {self.config['scraping_target']}"
        success = self.run_command(command, "Web scraping")
        
        if success:
            self.pipeline_stats['scraping_completed'] = True
            logging.info("✅ Scraping step completed")
        else:
            logging.error("❌ Scraping step failed")
            return False
        
        return True

    def step_2_yolo_detection(self):
        """Step 2: Run YOLO-based cat detection"""
        logging.info("\n" + "="*60)
        logging.info("STEP 2: YOLO CAT DETECTION")
        logging.info("="*60)
        
        # Check if scraped data exists
        if not Path("scraped_cats").exists():
            logging.error("❌ No scraped data found. Run scraping first.")
            return False
        
        command = f"python yolo_cat_detector.py --confidence {self.config['yolo_confidence']}"
        if not self.config['backup_enabled']:
            command += " --no-backup"
        
        success = self.run_command(command, "YOLO cat detection")
        
        if success:
            self.pipeline_stats['yolo_detection_completed'] = True
            logging.info("✅ YOLO detection step completed")
        else:
            logging.error("❌ YOLO detection step failed")
            return False
        
        return True

    def step_3_reorganization(self):
        """Step 3: Reorganize dataset for ML training"""
        if not self.config['reorganize']:
            logging.info("Skipping reorganization (disabled in config)")
            return True
        
        logging.info("\n" + "="*60)
        logging.info("STEP 3: DATASET REORGANIZATION")
        logging.info("="*60)
        
        # Check if YOLO-processed data exists
        if not Path("scraped_cats").exists():
            logging.error("❌ No YOLO-processed data found. Run YOLO detection first.")
            return False
        
        command = "python reorganize_dataset.py"
        success = self.run_command(command, "Dataset reorganization")
        
        if success:
            self.pipeline_stats['reorganization_completed'] = True
            logging.info("✅ Reorganization step completed")
        else:
            logging.error("❌ Reorganization step failed")
            return False
        
        return True

    def generate_final_report(self):
        """Generate final pipeline report"""
        logging.info("\n" + "="*60)
        logging.info("PIPELINE COMPLETION REPORT")
        logging.info("="*60)
        
        # Calculate statistics
        if Path("scraped_cats").exists():
            cat_dirs = [d for d in Path("scraped_cats").iterdir() if d.is_dir() and d.name.startswith('cat_')]
            total_cats = len(cat_dirs)
            
            total_images = 0
            for cat_dir in cat_dirs:
                for ext in ['.jpg', '.jpeg', '.png']:
                    total_images += len(list(cat_dir.glob(f"*{ext}")))
        else:
            total_cats = 0
            total_images = 0
        
        # Load YOLO detection report if available
        yolo_stats = {}
        if Path("yolo_detection_report.json").exists():
            try:
                with open("yolo_detection_report.json", 'r') as f:
                    yolo_data = json.load(f)
                    yolo_stats = yolo_data.get('statistics', {})
            except Exception as e:
                logging.warning(f"Could not load YOLO report: {e}")
        
        # Generate report
        report = {
            'pipeline_timestamp': datetime.now().isoformat(),
            'pipeline_stats': self.pipeline_stats,
            'configuration': self.config,
            'final_statistics': {
                'total_cats': total_cats,
                'total_images': total_images,
                'yolo_detection_stats': yolo_stats
            },
            'errors': self.pipeline_stats['errors']
        }
        
        # Save report
        report_path = Path("pipeline_completion_report.json")
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        # Print summary
        logging.info(f"📊 Final Statistics:")
        logging.info(f"   - Total cats: {total_cats}")
        logging.info(f"   - Total images: {total_images}")
        if yolo_stats:
            logging.info(f"   - Images with cats detected: {yolo_stats.get('images_with_cats', 'N/A')}")
            logging.info(f"   - Images removed: {yolo_stats.get('removed_images', 'N/A')}")
            logging.info(f"   - Average confidence: {yolo_stats.get('avg_confidence', 0):.3f}")
        
        logging.info(f"📋 Pipeline Status:")
        logging.info(f"   - Scraping: {'✅' if self.pipeline_stats['scraping_completed'] else '❌'}")
        logging.info(f"   - YOLO Detection: {'✅' if self.pipeline_stats['yolo_detection_completed'] else '❌'}")
        logging.info(f"   - Reorganization: {'✅' if self.pipeline_stats['reorganization_completed'] else '❌'}")
        
        if self.pipeline_stats['errors']:
            logging.warning(f"⚠️  {len(self.pipeline_stats['errors'])} errors encountered")
            for error in self.pipeline_stats['errors']:
                logging.warning(f"   - {error}")
        
        logging.info(f"📄 Detailed report saved to: {report_path}")
        
        return report

    def run_pipeline(self):
        """Run the complete pipeline"""
        self.pipeline_stats['start_time'] = datetime.now().isoformat()
        
        logging.info("🚀 Starting Complete Cat Dataset Pipeline")
        logging.info(f"Configuration: {self.config}")
        
        # Step 1: Scraping
        if not self.step_1_scraping():
            logging.error("Pipeline failed at scraping step")
            return False
        
        # Step 2: YOLO Detection
        if not self.step_2_yolo_detection():
            logging.error("Pipeline failed at YOLO detection step")
            return False
        
        # Step 3: Reorganization (optional)
        if not self.step_3_reorganization():
            logging.error("Pipeline failed at reorganization step")
            return False
        
        # Generate final report
        self.pipeline_stats['end_time'] = datetime.now().isoformat()
        self.generate_final_report()
        
        logging.info("\n🎉 Pipeline completed successfully!")
        return True

def main():
    parser = argparse.ArgumentParser(description="Complete cat dataset pipeline")
    parser.add_argument("--target", type=int, default=100, help="Number of cats to scrape")
    parser.add_argument("--confidence", type=float, default=0.3, help="YOLO confidence threshold")
    parser.add_argument("--no-reorganize", action="store_true", help="Skip reorganization step")
    parser.add_argument("--no-backup", action="store_true", help="Skip creating backups")
    parser.add_argument("--config", help="Path to configuration JSON file")
    
    args = parser.parse_args()
    
    # Initialize pipeline
    pipeline = CompletePipeline()
    
    # Update configuration from arguments
    pipeline.config['scraping_target'] = args.target
    pipeline.config['yolo_confidence'] = args.confidence
    pipeline.config['reorganize'] = not args.no_reorganize
    pipeline.config['backup_enabled'] = not args.no_backup
    
    # Load configuration file if provided
    if args.config and Path(args.config).exists():
        try:
            with open(args.config, 'r') as f:
                file_config = json.load(f)
                pipeline.config.update(file_config)
                logging.info(f"Loaded configuration from {args.config}")
        except Exception as e:
            logging.error(f"Failed to load configuration file: {e}")
    
    # Run pipeline
    success = pipeline.run_pipeline()
    
    if not success:
        logging.error("Pipeline failed!")
        sys.exit(1)

if __name__ == "__main__":
    main() 