#!/usr/bin/env python3
"""
Investigate Pagination Script
This script investigates how the website actually handles pagination
"""

import requests
from bs4 import BeautifulSoup
import re
import json
import time
import logging
import config

# Set up logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class PaginationInvestigator:
    def __init__(self):
        self.base_url = config.BASE_URL
        self.session = requests.Session()
        self.session.headers.update(config.HEADERS)
    
    def get_page(self, url, retries=3):
        """Get page content with retry logic"""
        for attempt in range(retries):
            try:
                response = self.session.get(url, timeout=config.TIMEOUT)
                response.raise_for_status()
                return response
            except Exception as e:
                logging.warning(f"Attempt {attempt + 1} failed for {url}: {e}")
                if attempt == retries - 1:
                    return None
                time.sleep(config.DELAY_BETWEEN_REQUESTS)
        return None
    
    def investigate_pagination(self):
        """Investigate how pagination actually works"""
        print("🔍 Investigating Pagination Mechanism")
        print("=" * 50)
        
        # Get the main listing page
        url = f"{self.base_url}/foster/cat/"
        print(f"📄 Analyzing: {url}")
        
        response = self.get_page(url)
        if not response:
            print("❌ Failed to load page")
            return
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # 1. Look for forms that might handle pagination
        print("\n🔍 Looking for forms:")
        forms = soup.find_all('form')
        for i, form in enumerate(forms):
            action = form.get('action', 'No action')
            method = form.get('method', 'GET')
            print(f"  Form {i+1}: method={method}, action={action}")
            
            # Look for pagination-related inputs
            inputs = form.find_all('input')
            for inp in inputs:
                name = inp.get('name', '')
                value = inp.get('value', '')
                if any(term in name.lower() for term in ['page', 'pagination', 'offset', 'limit']):
                    print(f"    Input: {name} = {value}")
        
        # 2. Look for pagination links/buttons
        print("\n🔍 Looking for pagination elements:")
        
        # Check for pagination links
        pagination_links = soup.find_all('a', href=True)
        for link in pagination_links:
            href = link.get('href', '')
            text = link.get_text().strip()
            if any(term in text.lower() for term in ['next', 'prev', 'page', '次', '前', 'ページ']):
                print(f"  Pagination link: '{text}' -> {href}")
        
        # Check for pagination buttons
        buttons = soup.find_all(['button', 'input'], type=['button', 'submit'])
        for button in buttons:
            text = button.get_text().strip() or button.get('value', '')
            if any(term in text.lower() for term in ['next', 'prev', 'page', '次', '前', 'ページ']):
                print(f"  Pagination button: '{text}'")
        
        # 3. Look for JavaScript that handles pagination
        print("\n🔍 Looking for pagination JavaScript:")
        scripts = soup.find_all('script')
        for i, script in enumerate(scripts):
            if script.string:
                content = script.string.lower()
                if any(term in content for term in ['page', 'pagination', 'next', 'prev', 'offset', 'limit']):
                    print(f"  Script {i+1} contains pagination terms:")
                    # Extract relevant lines
                    lines = script.string.split('\n')
                    for line in lines:
                        if any(term in line.lower() for term in ['page', 'pagination', 'next', 'prev', 'offset', 'limit']):
                            print(f"    {line.strip()}")
        
        # 4. Look for AJAX endpoints or API calls
        print("\n🔍 Looking for AJAX/API endpoints:")
        for script in scripts:
            if script.string:
                # Look for URLs that might be AJAX endpoints
                urls = re.findall(r'["\']([^"\']*\.(?:php|asp|aspx|jsp|json|xml))[^"\']*["\']', script.string)
                for url in urls:
                    if 'page' in url or 'pagination' in url:
                        print(f"  Potential AJAX endpoint: {url}")
        
        # 5. Check for data attributes that might contain pagination info
        print("\n🔍 Looking for data attributes:")
        elements_with_data = soup.find_all(attrs=lambda x: any(attr.startswith('data-') for attr in x.keys() if attr))
        for elem in elements_with_data[:10]:  # Check first 10
            data_attrs = {k: v for k, v in elem.attrs.items() if k.startswith('data-')}
            if data_attrs:
                print(f"  Element with data attributes: {data_attrs}")
        
        # 6. Look for any hidden pagination state
        print("\n🔍 Looking for hidden pagination state:")
        hidden_inputs = soup.find_all('input', type='hidden')
        for inp in hidden_inputs:
            name = inp.get('name', '')
            value = inp.get('value', '')
            if any(term in name.lower() for term in ['page', 'pagination', 'offset', 'limit', 'start']):
                print(f"  Hidden input: {name} = {value}")
        
        # 7. Check if there's a "load more" or infinite scroll mechanism
        print("\n🔍 Looking for load more/infinite scroll:")
        load_more_elements = soup.find_all(string=re.compile(r'load|more|追加|読み込み|次|前', re.I))
        for elem in load_more_elements:
            print(f"  Load more text: {elem.strip()}")
        
        # 8. Check the actual URL structure when we visit the page
        print(f"\n🔍 Final URL after redirects: {response.url}")
        print(f"  Status code: {response.status_code}")
        print(f"  Content length: {len(response.content)} bytes")

def main():
    investigator = PaginationInvestigator()
    investigator.investigate_pagination()

if __name__ == "__main__":
    main() 