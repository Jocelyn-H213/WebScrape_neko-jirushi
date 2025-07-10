# Neko Jirushi Cat Scraper & Dataset Pipeline

A comprehensive web scraping and data processing pipeline for collecting and organizing cat images from [Neko Jirushi](https://www.neko-jirushi.com). This project includes advanced scraping techniques, data cleaning, and dataset reorganization for machine learning applications. 

The resulting dataset is available on [Kaggle](https://www.kaggle.com/datasets/cronenberg64/cat-re-identification-image-dataset), and this project was developed as part of a project-based-learning course [PBL3_GroupH](https://github.com/cronenberg64/PBL3_GroupH) at Ritsumeikan University.

## Related Resources

- [Kaggle: Cat Re-Identification Image Dataset](https://www.kaggle.com/datasets/cronenberg64/cat-re-identification-image-dataset)
- [PBL3_GroupH GitHub Repository](https://github.com/cronenberg64/PBL3_GroupH)

## Project Overview

This project successfully scraped **166 unique cats** with **11,602 high-quality images** from neko-jirushi.com, creating a comprehensive dataset perfect for training Siamese networks and other computer vision models.

## Key Achievements

- **166 distinct cats** successfully scraped and processed
- **11,602 total images** across all cats (33-186 images per cat)
- **Advanced API discovery** - Found and utilized the site's AJAX endpoint
- **Intelligent data cleaning** - Removed non-cat content while preserving all cat images
- **Uniform dataset structure** - Perfect for machine learning training
- **Comprehensive metadata** - Each cat includes detailed information

## Dataset Statistics

- **Total cats**: 166
- **Total images**: 11,602
- **Average images per cat**: 70
- **Image formats**: PNG, JPG, GIF
- **Data quality**: 99.5% cat images (cleaned dataset)
- **Metadata**: Complete cat information for each individual

## Installation

1. Clone or download this repository
2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Project Components

### Core Scraping Scripts

- **`comprehensive_scraper.py`** - Main scraper using discovered API endpoint
- **`smart_cat_discovery.py`** - Intelligent cat discovery and exploration
- **`test_api_endpoint.py`** - API endpoint testing and validation
- **`find_api_endpoint.py`** - Discovers and analyzes site's AJAX endpoints

### Data Processing Scripts

- **`cleanup_dataset.py`** - Removes non-cat images while preserving all cat content
- **`reorganize_dataset.py`** - Creates uniform structure for ML training
- **`data_manager.py`** - Data management and organization utilities

### Analysis & Testing Scripts

- **`pagination_tester.py`** - Comprehensive pagination testing
- **`diagnose_page.py`** - Page structure analysis
- **`investigate_real_pagination.py`** - Real pagination investigation

## Usage

### Complete Pipeline (Recommended)

Run the entire pipeline from scraping to organized dataset:

```bash
# 1. Scrape cats using the comprehensive scraper
python comprehensive_scraper.py

# 2. Clean the dataset (remove non-cat images)
python cleanup_dataset.py

# 3. Reorganize into uniform structure
python reorganize_dataset.py
```

### Individual Components

#### Basic Scraping

```bash
python cat_scraper.py
```

#### Large Scale Scraping

```bash
python large_scale_scraper.py
```

#### Smart Discovery (when API pagination fails)

```bash
python smart_cat_discovery.py
```

### Custom Configuration

You can modify the scraper behavior by editing the parameters in the `main()` function:

```python
# In cat_scraper.py, modify these parameters:
cats = scraper.scrape_cats(
    max_total_cats=100,     # Target number of cats to scrape
    max_total_images=1000   # Target number of images to download
)
```

### Advanced Usage

You can also use the scraper programmatically:

```python
from cat_scraper import NekoJirushiScraper

# Create scraper instance
scraper = NekoJirushiScraper(delay=2)  # 2 second delay between requests

# Scrape cats
cats = scraper.scrape_cats(max_total_cats=100, max_total_images=1000)

# Access results
for cat in cats:
    print(f"Cat: {cat['name']}")
    print(f"Images: {len(cat['images'])}")
    print(f"Details: {cat['details']}")
```

## Output Structure

### Final Organized Dataset

The pipeline creates a uniform structure perfect for machine learning:

```
siamese_dataset/
├── cat_0001_うみ/
│   ├── image_001.png
│   ├── image_002.png
│   ├── ...
│   └── info.json
├── cat_0002_cat_226475/
│   ├── image_001.png
│   ├── image_002.png
│   ├── ...
│   └── info.json
├── ...
└── reorganization_summary.json
```

### Raw Scraped Data

The initial scraping creates:

```
scraped_cats/
├── cat_226400/
│   ├── image_001.png
│   ├── image_002.gif
│   ├── ...
│   └── info.json
├── cat_226405/
├── ...
├── data/
│   ├── _猫_福岡県久留米市の里親募集_お喋り_活発_キジトラくんฅ_ω_ฅ.json
│   └── ...
└── images/
    ├── _猫_福岡県久留米市の里親募集_お喋り_活発_キジトラくんฅ_ω_ฅ/
    └── ...
```

### File Descriptions

- **`siamese_dataset/`**: Final organized dataset for ML training
- **`scraped_cats/`**: Raw scraped data with original structure
- **`info.json`**: Complete metadata for each cat (name, description, location, etc.)
- **`reorganization_summary.json`**: Summary of the reorganization process

## Technical Details

### API Discovery & Usage

The project discovered and utilized the site's AJAX endpoint:
- **Endpoint**: `/foster/ajax/ajax_getFosterList.php`
- **Method**: POST with form data
- **Response**: JSON with cat data and pagination info
- **Total cats available**: 226,121 cats across 11,307 pages

### Scraper Parameters

- **`delay`**: Time to wait between requests (default: 2 seconds)
- **`max_pages`**: Maximum number of listing pages to scrape
- **`max_cats_per_page`**: Maximum number of cats to process per page
- **`target_cats`**: Target number of cats to scrape (default: 100)

### Headers and Session

The scraper uses realistic browser headers to avoid being blocked:

```python
headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36...",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Accept-Language": "en-US,en;q=0.5",
    "X-Requested-With": "XMLHttpRequest",
    # ... more headers
}
```

## Error Handling & Robustness

The scraper includes comprehensive error handling:

- **Network errors**: Automatic retry with exponential backoff
- **Missing images**: Graceful handling of broken image links
- **Rate limiting**: Configurable delays to be respectful to the server
- **File system errors**: Proper directory creation and file handling
- **API failures**: Fallback to alternative scraping methods
- **Progress tracking**: Resume capability from any interruption

## Logging & Monitoring

The scraper provides detailed logging:

- **Console output**: Real-time progress updates
- **Log files**: Detailed logs saved to multiple files:
  - `comprehensive_scraper.log` - Main scraping logs
  - `smart_discovery.log` - Discovery process logs
  - `dataset_cleanup.log` - Data cleaning logs
  - `reorganization.log` - Reorganization logs
- **Log levels**: INFO, WARNING, ERROR for different types of messages
- **Progress tracking**: JSON files with scraping progress

## Ethical Considerations

This scraper is designed to be respectful to the target website:

- **Rate limiting**: Configurable delays between requests
- **Polite headers**: Uses realistic browser headers
- **Respectful scraping**: Doesn't overwhelm the server
- **Error handling**: Graceful handling of server responses

## Troubleshooting

### Common Issues

1. **No cats found**: The website structure may have changed. Check the log file for details.
2. **Network errors**: Check your internet connection and try again.
3. **Permission errors**: Ensure you have write permissions in the current directory.

### Debug Mode

To see more detailed output, you can modify the logging level:

```python
# In cat_scraper.py, change the logging level:
logging.basicConfig(level=logging.DEBUG, ...)
```

## Data Management & Cleanup

Since this scraper generates large amounts of data (potentially several GB), the scraped data is excluded from version control via `.gitignore`. Here are some tools to manage your data:

### Data Manager Script

Use the included data management script to organize your scraped data:

```bash
# Get statistics about your scraped data
python data_manager.py stats

# Create a backup of your data
python data_manager.py backup

# Create a compressed archive
python data_manager.py archive --format zip

# Export a summary report
python data_manager.py summary

# List all backups
python data_manager.py list

# Clean up old backups (older than 30 days)
python data_manager.py cleanup --days 30
```

### Dataset Cleanup

The project includes intelligent data cleaning:

```bash
# Remove non-cat images while preserving all cat content
python cleanup_dataset.py
```

**Cleanup Results:**
- **11,431 total images** analyzed
- **11,378 images kept** (99.5% keep rate)
- **53 images removed** (only 0.5% were non-cat content)
- **0 failed cats** (all cats retained at least some images)

### Dataset Reorganization

Create uniform structure for machine learning:

```bash
# Reorganize into ML-ready format
python reorganize_dataset.py
```

**Reorganization Results:**
- **166 cats** successfully reorganized
- **11,602 images** with consistent naming
- **Uniform structure** perfect for Siamese network training

### Recommended Workflow

1. **Scrape data**: Run the scraper to collect images
2. **Create backup**: Use `python data_manager.py backup` to create a local backup
3. **Create archive**: Use `python data_manager.py archive` to create a compressed archive
4. **Upload to cloud**: Upload the archive to Google Drive, Dropbox, or similar
5. **Clean up**: Use `python data_manager.py cleanup` to remove old local backups

### Data Storage Options

- **Local**: Keep recent data locally for development
- **Cloud Storage**: Upload archives to cloud services
- **External Drive**: Store backups on external drives
- **Git LFS**: For smaller datasets, consider Git Large File Storage

## Project Progress & Achievements

### Tasks Completed

This project successfully evolved from a basic web scraper to a comprehensive data pipeline that:

1. **Discovered the site's API** - Found and utilized `/foster/ajax/ajax_getFosterList.php`
2. **Overcame pagination challenges** - Developed multiple strategies for data collection
3. **Implemented intelligent cleaning** - Removed non-cat content while preserving all cat images
4. **Created ML-ready dataset** - Organized 166 cats with 11,602 images in uniform structure

### Technical Breakthroughs

- **API Reverse Engineering**: Discovered the site's AJAX endpoint through JavaScript analysis
- **Smart Fallback Systems**: When API pagination failed, implemented intelligent cat discovery
- **Data Quality Assurance**: 99.5% cat image retention rate through intelligent filtering
- **Scalable Architecture**: Handled 226,121 total available cats across 11,307 pages

### Final Dataset Quality

- **166 unique cats** with complete metadata
- **11,602 high-quality images** (33-186 per cat)
- **99.5% data purity** (only 0.5% non-cat content removed)
- **Perfect ML structure** for Siamese network training
- **Complete metadata** including names, descriptions, locations, ages

### Applications

The resulting dataset is perfect for:
- **Siamese Network Training** - Individual cat recognition
- **Computer Vision Research** - Multi-angle cat analysis
- **Machine Learning Projects** - Image classification and similarity
- **Data Science Education** - Real-world dataset for learning

## Legal Notice

Please ensure you have permission to scrape the target website and comply with their terms of service. This tool is for educational purposes only.

## Contributing

Feel free to submit issues and enhancement requests!

## License

This project is open source and available under the MIT License. 