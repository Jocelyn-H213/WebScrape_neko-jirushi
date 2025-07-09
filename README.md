# Neko Jirushi Cat Scraper

A comprehensive web scraper for collecting cat pictures from different angles from the [Neko Jirushi](https://www.neko-jirushi.com) website.

## Features

- **Multi-angle image collection**: Downloads all available images of each cat from different angles
- **Robust error handling**: Retry logic and graceful error handling
- **Rate limiting**: Polite scraping with configurable delays
- **Organized output**: Images and data are saved in structured directories
- **Comprehensive logging**: Detailed logs for debugging and monitoring
- **Metadata extraction**: Captures cat information along with images
- **Resume capability**: Skips already downloaded images

## Installation

1. Clone or download this repository
2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

Run the scraper with default settings:

```bash
python cat_scraper.py
```

### Custom Configuration

You can modify the scraper behavior by editing the parameters in the `main()` function:

```python
# In cat_scraper.py, modify these parameters:
cats = scraper.scrape_cats(
    max_pages=3,        # Number of listing pages to scrape
    max_cats_per_page=5 # Maximum cats to process per page
)
```

### Advanced Usage

You can also use the scraper programmatically:

```python
from cat_scraper import NekoJirushiScraper

# Create scraper instance
scraper = NekoJirushiScraper(delay=2)  # 2 second delay between requests

# Scrape cats
cats = scraper.scrape_cats(max_pages=5, max_cats_per_page=10)

# Access results
for cat in cats:
    print(f"Cat: {cat['name']}")
    print(f"Images: {len(cat['images'])}")
    print(f"Details: {cat['details']}")
```

## Output Structure

The scraper creates the following directory structure:

```
scraped_cats/
├── images/
│   ├── Cat_Name_1/
│   │   ├── Cat_Name_1_1.jpg
│   │   ├── Cat_Name_1_2.jpg
│   │   └── ...
│   ├── Cat_Name_2/
│   │   ├── Cat_Name_2_1.jpg
│   │   └── ...
│   └── ...
├── data/
│   ├── Cat_Name_1.json
│   ├── Cat_Name_2.json
│   └── ...
├── scraping_summary.json
└── scraper.log
```

### File Descriptions

- **`images/`**: Contains subdirectories for each cat with their downloaded images
- **`data/`**: JSON files containing metadata for each cat (name, details, image URLs, etc.)
- **`scraping_summary.json`**: Overview of the scraping session
- **`scraper.log`**: Detailed logs of the scraping process

## Configuration Options

### Scraper Parameters

- **`delay`**: Time to wait between requests (default: 2 seconds)
- **`max_pages`**: Maximum number of listing pages to scrape
- **`max_cats_per_page`**: Maximum number of cats to process per page

### Headers and Session

The scraper uses realistic browser headers to avoid being blocked:

```python
headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36...",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    # ... more headers
}
```

## Error Handling

The scraper includes comprehensive error handling:

- **Network errors**: Automatic retry with exponential backoff
- **Missing images**: Graceful handling of broken image links
- **Rate limiting**: Configurable delays to be respectful to the server
- **File system errors**: Proper directory creation and file handling

## Logging

The scraper provides detailed logging:

- **Console output**: Real-time progress updates
- **Log file**: Detailed logs saved to `scraper.log`
- **Log levels**: INFO, WARNING, ERROR for different types of messages

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

## Legal Notice

Please ensure you have permission to scrape the target website and comply with their terms of service. This tool is for educational purposes only.

## Contributing

Feel free to submit issues and enhancement requests!

## License

This project is open source and available under the MIT License. 