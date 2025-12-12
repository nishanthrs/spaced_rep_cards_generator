#!/usr/bin/env python3
"""
Example usage of the Universal Tech Blog Scraper
"""

from generic_tech_blog_scraper import UniversalTechBlogScraper, BaseExtractor
from bs4 import BeautifulSoup
from typing import Dict

# Example 1: Basic usage - scrape multiple blogs
def basic_example():
    print("="*80)
    print("EXAMPLE 1: Basic Usage")
    print("="*80)

    scraper = UniversalTechBlogScraper(output_dir="my_scraped_articles")

    # Scrape a single article
    result = scraper.scrape("https://blog.janestreet.com/visualizing-piecewise-linear-neural-networks/")

    print(f"\nScraped article: {result.get('title')}")
    print(f"Content blocks: {len(result.get('content', []))}")


# Example 2: Scrape multiple URLs at once
def batch_scraping_example():
    print("\n" + "="*80)
    print("EXAMPLE 2: Batch Scraping")
    print("="*80)

    scraper = UniversalTechBlogScraper()

    urls = [
        "https://www.uber.com/blog/blazing-fast-olap-on-ubers-inventory-and-catalog-data-with-apache-pinot/",
        "https://blog.janestreet.com/visualizing-piecewise-linear-neural-networks/",
        "https://medium.com/pinterest-engineering/web-performance-regression-detection-part-2-of-3-9e0b9d35a11f",
    ]

    results = scraper.scrape_multiple(urls)

    print("\nScraped Articles:")
    for r in results:
        print(f"  - {r.get('title', 'Unknown')}")


# Example 3: Add a custom extractor for a new blog
def custom_extractor_example():
    print("\n" + "="*80)
    print("EXAMPLE 3: Adding Custom Extractor")
    print("="*80)

    # Define a custom extractor for Netflix Tech Blog
    class NetflixTechBlogExtractor(BaseExtractor):
        def can_handle(self, url: str) -> bool:
            return 'netflixtechblog.com' in url.lower()

        def extract(self, url: str, soup: BeautifulSoup, html: str) -> Dict:
            data = {
                'url': url,
                'domain': 'netflixtechblog.com',
                'extractor': 'NetflixTechBlogExtractor'
            }

            # Custom extraction logic for Netflix blog
            title_tag = soup.find('h1')
            if title_tag:
                data['title'] = title_tag.get_text(strip=True)

            # Extract article content
            article = soup.find('article')
            if article:
                content_blocks = []
                for elem in article.find_all(['h2', 'h3', 'p']):
                    text = elem.get_text(strip=True)
                    if text and len(text) > 10:
                        content_blocks.append({
                            'type': elem.name,
                            'text': text
                        })
                data['content'] = content_blocks

            return data

    # Initialize scraper and add custom extractor
    scraper = UniversalTechBlogScraper()
    scraper.add_extractor(NetflixTechBlogExtractor())

    print("Added NetflixTechBlogExtractor")
    print(f"Total extractors: {len(scraper.extractors)}")


# Example 4: Access extracted data programmatically
def data_access_example():
    print("\n" + "="*80)
    print("EXAMPLE 4: Accessing Extracted Data")
    print("="*80)

    scraper = UniversalTechBlogScraper()

    result = scraper.scrape("https://blog.janestreet.com/visualizing-piecewise-linear-neural-networks/")

    # Access different parts of the data
    print(f"\nTitle: {result.get('title')}")
    print(f"Author: {result.get('author', 'N/A')}")
    print(f"Date: {result.get('date', 'N/A')}")
    print(f"Extractor used: {result.get('extractor')}")

    # Access content blocks
    if result.get('content'):
        print(f"\nFirst 3 content blocks:")
        for i, block in enumerate(result['content'][:3], 1):
            print(f"  {i}. [{block['type']}] {block['text'][:80]}...")

    # Access images
    if result.get('images'):
        print(f"\nImages found: {len(result['images'])}")
        for i, img in enumerate(result['images'][:3], 1):
            print(f"  {i}. {img['url']}")


if __name__ == "__main__":
    # Run examples
    # Uncomment the example you want to run

    # basic_example()
    # batch_scraping_example()
    # custom_extractor_example()
    # data_access_example()

    print("\nUncomment the examples you want to run in example_usage.py")
