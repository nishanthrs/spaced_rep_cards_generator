#!/usr/bin/env python3
"""
Selenium-based Medium Scraper

This is an alternative scraper for Medium articles that uses Selenium
with a headless browser. This approach is more reliable for Medium
because it:
1. Executes JavaScript (Medium uses JS rendering)
2. Looks exactly like a real browser to Medium's anti-bot systems
3. Can handle Cloudflare and other protections

Use this when the regular scraper fails with 403 errors.

Requirements:
    pip install selenium webdriver-manager

Usage:
    python medium_selenium_scraper.py <medium_url>
"""

import json
import sys
import time
from pathlib import Path
from typing import Dict, List

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


class MediumSeleniumScraper:
    """
    Scraper for Medium articles using Selenium headless browser.

    This bypasses Medium's anti-bot protection by using a real browser.
    """

    def __init__(self, headless: bool = True):
        """
        Initialize the Selenium scraper.

        Args:
            headless: Run browser in headless mode (no GUI)
        """
        self.headless = headless
        self.driver = None

    def _setup_driver(self):
        """Set up the Chrome WebDriver with options to avoid detection."""
        chrome_options = Options()

        if self.headless:
            chrome_options.add_argument('--headless=new')

        # Options to avoid detection
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')

        # Realistic user agent
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

        # Exclude automation flags
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)

        # Set up the driver
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)

        # Execute script to remove webdriver property
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    def scrape(self, url: str) -> Dict:
        """
        Scrape a Medium article.

        Args:
            url: URL of the Medium article

        Returns:
            Dictionary containing article data
        """
        if not self.driver:
            self._setup_driver()

        print(f"Fetching Medium article with Selenium: {url}")

        try:
            # Load the page
            self.driver.get(url)

            # Wait for the article to load
            # Medium articles are in <article> tags
            wait = WebDriverWait(self.driver, 10)
            article = wait.until(
                EC.presence_of_element_located((By.TAG_NAME, "article"))
            )

            # Give it a bit more time for dynamic content
            time.sleep(2)

            # Extract data
            data = {
                'url': url,
                'scraper': 'MediumSeleniumScraper'
            }

            # Extract title (h1 in the article)
            try:
                title = self.driver.find_element(By.TAG_NAME, "h1")
                data['title'] = title.text
            except:
                data['title'] = 'Unknown'

            # Extract author
            try:
                # Medium puts author in meta tags
                author_meta = self.driver.find_element(By.CSS_SELECTOR, 'meta[name="author"]')
                data['author'] = author_meta.get_attribute('content')
            except:
                pass

            # Extract all paragraphs and headings from the article
            content_blocks = []

            # Find the article element
            article = self.driver.find_element(By.TAG_NAME, "article")

            # Get all text elements
            elements = article.find_elements(By.CSS_SELECTOR, "h1, h2, h3, h4, p, li, blockquote, pre")

            for elem in elements:
                text = elem.text.strip()
                if not text or len(text) < 10:
                    continue

                # Skip if it's the title
                if data.get('title') and text == data['title']:
                    continue

                tag_name = elem.tag_name
                content_blocks.append({
                    'type': tag_name,
                    'text': text
                })

            data['content'] = content_blocks

            # Extract images
            images = []
            img_elements = article.find_elements(By.TAG_NAME, "img")

            for idx, img in enumerate(img_elements, 1):
                img_url = img.get_attribute('src')
                if img_url:
                    # Skip tracking pixels and small images
                    if any(skip in img_url.lower() for skip in ['pixel', 'tracking', 'avatar']):
                        continue

                    images.append({
                        'url': img_url,
                        'alt': img.get_attribute('alt') or '',
                        'index': idx
                    })

            data['images'] = images

            print(f"✓ Successfully scraped: {data.get('title')}")
            print(f"  Content blocks: {len(content_blocks)}")
            print(f"  Images: {len(images)}")

            return data

        except Exception as e:
            print(f"Error scraping with Selenium: {e}")
            import traceback
            traceback.print_exc()
            return {'url': url, 'error': str(e)}

    def close(self):
        """Close the browser."""
        if self.driver:
            self.driver.quit()
            self.driver = None

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


def main():
    """Demo usage."""
    if len(sys.argv) < 2:
        print("Usage: python medium_selenium_scraper.py <medium_url>")
        print("\nExample:")
        print("  python medium_selenium_scraper.py https://medium.com/pinterest-engineering/web-performance-regression-detection-part-2-of-3-9e0b9d35a11f")
        sys.exit(1)

    url = sys.argv[1]

    # Use context manager to ensure browser is closed
    with MediumSeleniumScraper(headless=True) as scraper:
        data = scraper.scrape(url)

        # Save to file
        output_dir = Path("scraped_tech_blogs")
        output_dir.mkdir(exist_ok=True)

        if data.get('title'):
            import re
            filename = re.sub(r'[<>:"/\\|?*]', '', data['title'])
            filename = filename.replace(' ', '_')[:100]
        else:
            filename = 'medium_article'

        # Save JSON
        json_path = output_dir / f"{filename}.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"\nSaved to: {json_path}")

        # Save Markdown
        md_path = output_dir / f"{filename}.md"
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(f"# {data.get('title', 'Untitled')}\n\n")
            if data.get('author'):
                f.write(f"**Author:** {data['author']}\n\n")
            f.write(f"**Source:** {url}\n\n")
            f.write("---\n\n")

            if data.get('content'):
                for block in data['content']:
                    if block['type'].startswith('h'):
                        level = block['type'][1]
                        f.write(f"{'#' * int(level)} {block['text']}\n\n")
                    else:
                        f.write(f"{block['text']}\n\n")

        print(f"Saved to: {md_path}")


if __name__ == "__main__":
    main()
