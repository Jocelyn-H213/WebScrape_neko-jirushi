#!/usr/bin/env python3
"""
Data Management Script for Neko Jirushi Cat Scraper
Helps organize, compress, and backup scraped data
"""

import os
import json
import shutil
import zipfile
import tarfile
from datetime import datetime
import argparse
from pathlib import Path
import config

class DataManager:
    def __init__(self):
        self.data_dir = config.OUTPUT_DIR
        self.backup_dir = "backups"
        self.archive_dir = "archives"
        
        # Create directories
        for directory in [self.backup_dir, self.archive_dir]:
            os.makedirs(directory, exist_ok=True)
    
    def get_data_stats(self):
        """Get statistics about the scraped data"""
        if not os.path.exists(self.data_dir):
            return {"error": "Data directory not found"}
        
        stats = {
            "total_cats": 0,
            "total_images": 0,
            "total_size_mb": 0,
            "cat_details": []
        }
        
        images_dir = os.path.join(self.data_dir, config.IMAGES_DIR)
        data_dir = os.path.join(self.data_dir, config.DATA_DIR)
        
        # Count cats and images
        if os.path.exists(images_dir):
            for cat_folder in os.listdir(images_dir):
                cat_path = os.path.join(images_dir, cat_folder)
                if os.path.isdir(cat_path):
                    images = [f for f in os.listdir(cat_path) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp'))]
                    stats["total_cats"] += 1
                    stats["total_images"] += len(images)
                    
                    # Calculate folder size
                    folder_size = sum(os.path.getsize(os.path.join(cat_path, f)) for f in images)
                    stats["total_size_mb"] += folder_size / (1024 * 1024)
                    
                    stats["cat_details"].append({
                        "name": cat_folder,
                        "images": len(images),
                        "size_mb": folder_size / (1024 * 1024)
                    })
        
        return stats
    
    def create_backup(self, backup_name=None):
        """Create a backup of the scraped data"""
        if not backup_name:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"cat_data_backup_{timestamp}"
        
        backup_path = os.path.join(self.backup_dir, backup_name)
        
        if os.path.exists(self.data_dir):
            print(f"Creating backup: {backup_path}")
            shutil.copytree(self.data_dir, backup_path)
            print(f"✓ Backup created successfully")
            return backup_path
        else:
            print("✗ No data directory found to backup")
            return None
    
    def create_archive(self, archive_name=None, format="zip"):
        """Create a compressed archive of the scraped data"""
        if not archive_name:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            archive_name = f"cat_data_archive_{timestamp}"
        
        if format == "zip":
            archive_path = os.path.join(self.archive_dir, f"{archive_name}.zip")
            print(f"Creating ZIP archive: {archive_path}")
            
            with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(self.data_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, self.data_dir)
                        zipf.write(file_path, arcname)
        
        elif format == "tar":
            archive_path = os.path.join(self.archive_dir, f"{archive_name}.tar.gz")
            print(f"Creating TAR archive: {archive_path}")
            
            with tarfile.open(archive_path, 'w:gz') as tar:
                tar.add(self.data_dir, arcname=os.path.basename(self.data_dir))
        
        archive_size = os.path.getsize(archive_path) / (1024 * 1024)
        print(f"✓ Archive created: {archive_size:.1f} MB")
        return archive_path
    
    def cleanup_old_data(self, days_old=30):
        """Remove old backup files"""
        cutoff_time = datetime.now().timestamp() - (days_old * 24 * 60 * 60)
        
        for directory in [self.backup_dir, self.archive_dir]:
            if os.path.exists(directory):
                for filename in os.listdir(directory):
                    file_path = os.path.join(directory, filename)
                    if os.path.getctime(file_path) < cutoff_time:
                        if os.path.isdir(file_path):
                            shutil.rmtree(file_path)
                        else:
                            os.remove(file_path)
                        print(f"Removed old file: {filename}")
    
    def export_summary(self, output_file="data_summary.json"):
        """Export a summary of the scraped data"""
        stats = self.get_data_stats()
        
        if "error" not in stats:
            summary = {
                "exported_at": datetime.now().isoformat(),
                "data_directory": self.data_dir,
                "statistics": stats,
                "config": {
                    "output_dir": config.OUTPUT_DIR,
                    "images_dir": config.IMAGES_DIR,
                    "data_dir": config.DATA_DIR
                }
            }
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(summary, f, ensure_ascii=False, indent=2)
            
            print(f"✓ Summary exported to: {output_file}")
            return output_file
        else:
            print(f"✗ Could not export summary: {stats['error']}")
            return None
    
    def list_backups(self):
        """List all available backups"""
        if not os.path.exists(self.backup_dir):
            print("No backup directory found")
            return
        
        backups = []
        for item in os.listdir(self.backup_dir):
            item_path = os.path.join(self.backup_dir, item)
            if os.path.isdir(item_path):
                size = sum(os.path.getsize(os.path.join(dirpath, filename))
                          for dirpath, dirnames, filenames in os.walk(item_path)
                          for filename in filenames)
                backups.append({
                    "name": item,
                    "size_mb": size / (1024 * 1024),
                    "created": datetime.fromtimestamp(os.path.getctime(item_path))
                })
        
        if backups:
            print("Available backups:")
            for backup in sorted(backups, key=lambda x: x["created"], reverse=True):
                print(f"  {backup['name']} - {backup['size_mb']:.1f} MB - {backup['created'].strftime('%Y-%m-%d %H:%M')}")
        else:
            print("No backups found")

def main():
    parser = argparse.ArgumentParser(description="Data Manager for Neko Jirushi Cat Scraper")
    parser.add_argument("action", choices=["stats", "backup", "archive", "cleanup", "summary", "list"], 
                       help="Action to perform")
    parser.add_argument("--name", help="Name for backup/archive")
    parser.add_argument("--format", choices=["zip", "tar"], default="zip", help="Archive format")
    parser.add_argument("--days", type=int, default=30, help="Days old for cleanup")
    parser.add_argument("--output", default="data_summary.json", help="Output file for summary")
    
    args = parser.parse_args()
    
    manager = DataManager()
    
    if args.action == "stats":
        stats = manager.get_data_stats()
        if "error" not in stats:
            print(f"Data Statistics:")
            print(f"  Total cats: {stats['total_cats']}")
            print(f"  Total images: {stats['total_images']}")
            print(f"  Total size: {stats['total_size_mb']:.1f} MB")
            if stats['cat_details']:
                print(f"  Average images per cat: {stats['total_images']/stats['total_cats']:.1f}")
        else:
            print(f"Error: {stats['error']}")
    
    elif args.action == "backup":
        manager.create_backup(args.name)
    
    elif args.action == "archive":
        manager.create_archive(args.name, args.format)
    
    elif args.action == "cleanup":
        manager.cleanup_old_data(args.days)
    
    elif args.action == "summary":
        manager.export_summary(args.output)
    
    elif args.action == "list":
        manager.list_backups()

if __name__ == "__main__":
    main() 