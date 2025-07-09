"""
Configuration file for the Neko Jirushi Cat Scraper
Modify these settings to customize the scraper behavior
"""

# Base configuration
BASE_URL = "https://www.neko-jirushi.com"
DELAY_BETWEEN_REQUESTS = 2  # seconds
DELAY_BETWEEN_IMAGES = 1    # seconds

# Scraping limits
MAX_PAGES = 50              # Maximum number of listing pages to scrape
MAX_CATS_PER_PAGE = 20      # Maximum cats to process per page
MAX_RETRIES = 3             # Number of retries for failed requests

# Output settings
OUTPUT_DIR = "scraped_cats"
IMAGES_DIR = "images"
DATA_DIR = "data"

# File naming
SAFE_FILENAME_CHARS = r'[^\w\-_\.]'  # Characters to replace in filenames
REPLACEMENT_CHAR = '_'               # Character to replace unsafe chars with

# Image settings
SUPPORTED_FORMATS = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
DEFAULT_IMAGE_FORMAT = '.jpg'

# Logging
LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR
LOG_FILE = "scraper.log"

# HTTP settings
TIMEOUT = 30  # seconds
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"

# Headers for requests
HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}

# URL patterns to try for cat listings
LISTING_URL_PATTERNS = [
    "{base_url}/foster/cat/?p={page}",
    "{base_url}/foster/cat?p={page}",
    "{base_url}/cat/foster/?p={page}",
    "{base_url}/cat/foster?p={page}",
    "{base_url}/cats/?p={page}",
    "{base_url}/cats?p={page}",
    "{base_url}/cat/?p={page}",
    "{base_url}/cat?p={page}",
]

# CSS selectors for finding cat links
CAT_LINK_SELECTORS = [
    "a.catlist_tit",
    ".catlist a",
    ".cat-item a",
    ".cat-card a",
    "a[href*='/cat/']",
    ".listing a",
    "a[href*='cat']",
    "a[href*='neko']",
]

# CSS selectors for finding cat names
CAT_NAME_SELECTORS = [
    "h1",
    ".cat-name",
    ".cat-title",
    ".profile-title",
    "title",
    ".name",
    ".pet-name",
]

# CSS selectors for finding images
IMAGE_SELECTORS = [
    "img[src*='cat']",  # This is the main selector that works
    "img[src*='/img/foster/']",  # More specific to foster images
    "img[src*='detail']",  # Images in detail pages
    "div.catphoto img",
    ".cat-photos img",
    ".cat-images img",
    ".gallery img",
    ".photo-gallery img",
    "img[src*='photo']",
    "img[src*='image']",
    ".catphoto img",
    ".pet-photos img",
]

# CSS selectors for cat details
DETAIL_SELECTORS = {
    'age': ['.age', '.cat-age', '[class*="age"]', '.pet-age'],
    'gender': ['.gender', '.cat-gender', '[class*="gender"]', '.pet-gender'],
    'breed': ['.breed', '.cat-breed', '[class*="breed"]', '.pet-breed'],
    'description': ['.description', '.cat-description', '.profile-description', '.pet-description'],
    'weight': ['.weight', '.cat-weight', '[class*="weight"]', '.pet-weight'],
    'color': ['.color', '.cat-color', '[class*="color"]', '.pet-color'],
}

# Categories to scrape (if the website has different sections)
CATEGORIES = [
    "foster",
    "adopt",
    "cats",
    "neko",
]

# Content type to image extension mapping
CONTENT_TYPE_TO_EXTENSION = {
    'image/jpeg': '.jpg',
    'image/jpg': '.jpg',
    'image/png': '.png',
    'image/gif': '.gif',
    'image/webp': '.webp',
} 