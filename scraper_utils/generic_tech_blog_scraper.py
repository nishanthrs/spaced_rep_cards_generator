#!/usr/bin/env python3
"""
Generic Tech Blog Scraper with Domain-Specific Optimizations

This scraper uses a hybrid approach:
1. Generic content extraction using established libraries (trafilatura, newspaper3k)
2. Domain-specific configurations for known blogs
3. Fallback to heuristic-based extraction for unknown sites

This approach gives you the best of both worlds:
- Works on most sites out of the box
- More accurate on known domains
- Easy to add new domain configurations

Requirements:
    pip install trafilatura newspaper3k requests beautifulsoup4 lxml
"""

import argparse
import json
import re
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

# These libraries specialize in extracting main content from web pages
try:
    import trafilatura

    HAS_TRAFILATURA = True
except ImportError:
    HAS_TRAFILATURA = False
    print("Warning: trafilatura not installed. Install with: pip install trafilatura")

try:
    from newspaper import Article as NewspaperArticle

    HAS_NEWSPAPER = True
except ImportError:
    HAS_NEWSPAPER = False
    print("Warning: newspaper3k not installed. Install with: pip install newspaper3k")


class BaseExtractor(ABC):
    """
    Abstract base class for content extractors.

    Each domain-specific extractor inherits from this and implements
    custom logic for that particular site's HTML structure.
    """

    @abstractmethod
    def can_handle(self, url: str) -> bool:
        """Check if this extractor can handle the given URL."""
        pass

    @abstractmethod
    def extract(self, url: str, soup: BeautifulSoup, html: str) -> Dict:
        """Extract content from the page."""
        pass


class UberBlogExtractor(BaseExtractor):
    """
    Extractor specifically for Uber Engineering Blog.

    Uber's blog has a specific HTML structure we can target for
    more accurate extraction.

    Bugs:
    1. The title can contain weird chars like the TM symbol and null char, causing weird issues like value errors when creating and writing to files.
    This was fixed by adding the sanitize_text method to strip the null chars.
    """

    def can_handle(self, url: str) -> bool:
        """Check if URL is from Uber's blog."""
        return "uber.com/blog" in url.lower()

    def extract(self, url: str, soup: BeautifulSoup, html: str) -> Dict:
        """Extract content from Uber's blog."""
        data = {"url": url, "domain": "uber.com", "extractor": "UberBlogExtractor"}

        # Extract title - Uber uses h1 tags for titles
        title_tag = soup.find("h1")
        if title_tag:
            data["title"] = title_tag.get_text(strip=True)

        # Extract metadata from meta tags
        og_description = soup.find("meta", property="og:description")
        if og_description:
            data["description"] = og_description.get("content", "")

        # Uber blog typically has a main article container
        # We look for common article containers
        article = soup.find("article")
        if not article:
            # Fallback: look for main content div
            article = soup.find("main") or soup.find(
                "div", class_=re.compile("article|content|post")
            )

        if article:
            # Extract all text content blocks
            content_blocks = []

            for elem in article.find_all(
                ["h1", "h2", "h3", "h4", "h5", "h6", "p", "li", "blockquote", "pre"]
            ):
                text = elem.get_text(strip=True)
                if not text or len(text) < 10:  # Skip very short snippets
                    continue

                content_blocks.append({"type": elem.name, "text": text})

            data["content"] = content_blocks

            # Extract images from article
            images = []
            for img in article.find_all("img"):
                img_url = img.get("src") or img.get("data-src")
                if img_url:
                    images.append(
                        {
                            "url": img_url,
                            "alt": img.get("alt", ""),
                            "caption": img.get("title", ""),
                        }
                    )
            data["images"] = images

        return data


class JaneStreetBlogExtractor(BaseExtractor):
    """
    Extractor for Jane Street's blog.

    Jane Street's blog has a clean structure that's relatively
    straightforward to parse.

    Bugs:
    1. Jane Street blogs have multiple <article> tags, but only one is the main article. The other articles are related articles.
    We need to extract the main article only.
    """

    def can_handle(self, url: str) -> bool:
        """Check if URL is from Jane Street's blog."""
        return "blog.janestreet.com" in url.lower()

    def extract(self, url: str, soup: BeautifulSoup, html: str) -> Dict:
        """Extract content from Jane Street's blog."""
        data = {
            "url": url,
            "domain": "blog.janestreet.com",
            "extractor": "JaneStreetBlogExtractor",
        }

        # Jane Street uses h1 for post titles
        title_tag = soup.find("h1", class_=re.compile("post-title|entry-title"))
        if not title_tag:
            title_tag = soup.find("h1")
        if title_tag:
            data["title"] = title_tag.get_text(strip=True)

        # Look for author and date
        author_tag = soup.find("a", rel="author") or soup.find(
            class_=re.compile("author")
        )
        if author_tag:
            data["author"] = author_tag.get_text(strip=True)

        time_tag = soup.find("time")
        if time_tag:
            data["date"] = time_tag.get("datetime", time_tag.get_text(strip=True))

        # CRITICAL FIX: Jane Street has multiple article tags on the page
        # We need to find the article that contains div with class "post-header"
        # This is the main article content, not sidebar or navigation
        article = None
        all_articles = soup.find_all("article")

        # Iterate through all article tags and find the one with post-header
        for article_tag in all_articles:
            # Check if this article contains a div with class "post-header"
            if article_tag.find("div", class_="post-header"):
                article = article_tag
                break

        # Fallback: if we didn't find the right article, use the first one
        # (though this is less reliable)
        if not article and all_articles:
            print("Warning: Could not find main article. Using first article.")
            article = all_articles[0]

        if article:
            content_blocks = []

            for elem in article.find_all(
                ["h2", "h3", "h4", "h5", "h6", "p", "li", "blockquote", "pre"]
            ):
                text = elem.get_text(strip=True)
                if not text or len(text) < 10:
                    continue

                content_blocks.append({"type": elem.name, "text": text})

            data["content"] = content_blocks

            # Extract images
            images = []
            for img in article.find_all("img"):
                img_url = img.get("src") or img.get("data-src")
                if img_url:
                    images.append(
                        {
                            "url": img_url,
                            "alt": img.get("alt", ""),
                        }
                    )
            data["images"] = images

        return data


class GenericExtractor(BaseExtractor):
    """
    Fallback extractor that uses heuristics and third-party libraries.

    This is used when we don't have a domain-specific extractor.
    It tries multiple approaches:
    1. Trafilatura (specialized content extraction library)
    2. Newspaper3k (article extraction library)
    3. Basic heuristics (find longest text blocks, article tags, etc.)
    """

    def can_handle(self, url: str) -> bool:
        """This is the fallback, so it can handle any URL."""
        return True

    def extract(self, url: str, soup: BeautifulSoup, html: str) -> Dict:
        """Extract content using generic methods."""
        data = {
            "url": url,
            "domain": urlparse(url).netloc,
            "extractor": "GenericExtractor",
        }

        # Try trafilatura first (most reliable generic extractor)
        if HAS_TRAFILATURA:
            extracted = trafilatura.extract(
                html, include_comments=False, include_tables=True, include_images=True
            )
            if extracted:
                data["content_raw"] = extracted

                # Try to get metadata
                metadata = trafilatura.extract_metadata(html)
                if metadata:
                    data["title"] = metadata.title
                    data["author"] = metadata.author
                    data["date"] = metadata.date
                    data["description"] = metadata.description

        # Try newspaper3k as alternative/supplement
        if HAS_NEWSPAPER:
            try:
                article = NewspaperArticle(url)
                article.download(input_html=html)
                article.parse()

                if not data.get("title"):
                    data["title"] = article.title
                if not data.get("author"):
                    data["authors"] = article.authors
                if not data.get("date"):
                    data["publish_date"] = (
                        str(article.publish_date) if article.publish_date else None
                    )

                # Get the main text
                if article.text and not data.get("content_raw"):
                    data["content_raw"] = article.text

                # Get images
                if article.images:
                    data["images"] = [{"url": img_url} for img_url in article.images]

                # Get top image
                if article.top_image:
                    data["top_image"] = article.top_image

            except Exception as e:
                print(f"Newspaper3k extraction failed: {e}")

        # Fallback: basic heuristic extraction using BeautifulSoup
        if not data.get("content_raw"):
            # Find title
            if not data.get("title"):
                title_tag = (
                    soup.find("h1")
                    or soup.find("meta", property="og:title")
                    or soup.find("title")
                )
                if title_tag:
                    data["title"] = (
                        title_tag.get("content", "")
                        if title_tag.name == "meta"
                        else title_tag.get_text(strip=True)
                    )

            # Find main content - try common article containers
            article = (
                soup.find("article")
                or soup.find("main")
                or soup.find(
                    "div", class_=re.compile("article|content|post|entry", re.I)
                )
                or soup.find("div", id=re.compile("article|content|post|entry", re.I))
            )

            if article:
                # Extract all paragraphs and headings
                content_blocks = []
                for elem in article.find_all(
                    ["h1", "h2", "h3", "h4", "h5", "h6", "p", "blockquote", "pre"]
                ):
                    text = elem.get_text(strip=True)
                    if text and len(text) > 20:  # Only include substantial text
                        content_blocks.append({"type": elem.name, "text": text})

                if content_blocks:
                    data["content"] = content_blocks

                # Extract images
                images = []
                for img in article.find_all("img"):
                    img_url = img.get("src") or img.get("data-src")
                    if img_url and not any(
                        skip in img_url.lower()
                        for skip in ["icon", "logo", "avatar", "pixel"]
                    ):
                        images.append(
                            {
                                "url": img_url,
                                "alt": img.get("alt", ""),
                            }
                        )
                if images:
                    data["images"] = images

        return data


class UniversalTechBlogScraper:
    """
    Main scraper class that orchestrates domain-specific and generic extractors.

    This uses a chain-of-responsibility pattern:
    1. Try domain-specific extractors first
    2. Fall back to generic extractor if no match

    This gives you:
    - High accuracy on known domains
    - Reasonable accuracy on unknown domains
    - Easy to add new domain-specific extractors
    """

    def __init__(self, output_dir: str = "scraped_content"):
        """Initialize the scraper with all available extractors."""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        # Register all extractors
        # Order matters: more specific extractors should come first
        self.extractors = [
            UberBlogExtractor(),
            JaneStreetBlogExtractor(),
            GenericExtractor(),  # Always last (fallback)
        ]

        # Set up HTTP session with browser-like headers
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
            }
        )

    def _get_extractor(self, url: str) -> BaseExtractor:
        """
        Find the appropriate extractor for a given URL.

        Iterates through registered extractors and returns the first
        one that can handle the URL.
        """
        for extractor in self.extractors:
            if extractor.can_handle(url):
                print(f"Using extractor: {extractor.__class__.__name__} for {url}")
                return extractor

        # Should never reach here since GenericExtractor handles everything
        return self.extractors[-1]

    def _fetch_page(self, url: str) -> Tuple[str, BeautifulSoup]:
        """
        Fetch a webpage and return both raw HTML and parsed soup.

        Returns:
            Tuple of (html_string, BeautifulSoup_object)
        """
        print(f"Fetching: {url}")
        response = self.session.get(url, timeout=30)
        response.raise_for_status()

        html = response.text
        soup = BeautifulSoup(html, "html.parser")

        return html, soup

    def sanitize_text(self, text: str) -> str:
        """
        Sanitize text to prevent file-reading and writing issues:
        1. Unexpected null bytes
        2. Weird special characters
        """
        return text.replace("\x00", "")  # Remove null bytes

    def scrape(self, url: str) -> Dict:
        """
        Main scraping method.

        Args:
            url: URL of the article to scrape

        Returns:
            Dictionary containing extracted article data
        """
        print(f"\n{'='*80}")
        print(f"Scraping: {url}")
        print(f"{'='*80}\n")

        # Fetch the page
        try:
            html, soup = self._fetch_page(url)
        except Exception as e:
            print(f"Error fetching page: {e}")
            return {"url": url, "error": str(e)}

        # Select appropriate extractor
        extractor = self._get_extractor(url)
        print(f"Using extractor: {extractor.__class__.__name__}")

        # Extract content
        try:
            data = extractor.extract(url, soup, html)
            data["scrape_timestamp"] = time.strftime("%Y-%m-%d %H:%M:%S")

            # Save the results
            self._save_data(data)

            # Print summary
            print(f"\n{'='*80}")
            print(f"Extraction complete!")
            print(f"  Title: {data.get('title', 'N/A')}")
            print(f"  Extractor: {data.get('extractor', 'N/A')}")
            print(f"  Content blocks: {len(data.get('content', []))}")
            print(f"  Images: {len(data.get('images', []))}")
            print(f"{'='*80}\n")

            return data

        except Exception as e:
            print(f"Error extracting content: {e}")
            import traceback

            traceback.print_exc()
            return {"url": url, "error": str(e)}

    def _save_data(self, data: Dict):
        """Save extracted data to JSON and Markdown files."""
        # Create safe filename from title or URL
        if data.get("title"):
            filename_base = re.sub(r'[<>:"/\\|?*]', "", data["title"])
            filename_base = filename_base.replace(" ", "_")[:100]
            filename_base = self.sanitize_text(filename_base)
        else:
            # Use domain and timestamp as filename
            parsed = urlparse(data["url"])
            filename_base = f"{parsed.netloc}_{int(time.time())}"

        # Save Markdown
        md_path = f"{self.output_dir}/{filename_base}.md"
        with open(md_path, "w", encoding="utf-8") as f:
            title = self.sanitize_text(data.get("title", "Untitled"))
            f.write(f"# {title}\n\n")

            if data.get("author"):
                f.write(f"**Author:** {data['author']}\n\n")

            if data.get("date"):
                f.write(f"**Date:** {data['date']}\n\n")

            f.write(f"**Source:** {data['url']}\n\n")
            f.write(f"**Extracted by:** {data.get('extractor', 'Unknown')}\n\n")
            f.write("---\n\n")

            # Write content
            if data.get("content"):
                for block in data["content"]:
                    if block["type"].startswith("h"):
                        level = block["type"][1] if len(block["type"]) > 1 else "2"
                        f.write(f"{'#' * int(level)} {block['text']}\n\n")
                    elif block["type"] == "p":
                        f.write(f"{block['text']}\n\n")
                    elif block["type"] == "blockquote":
                        f.write(f"> {block['text']}\n\n")
                    elif block["type"] in ["pre", "code"]:
                        f.write(f"```\n{block['text']}\n```\n\n")
                    else:
                        f.write(f"{block['text']}\n\n")

            elif data.get("content_raw"):
                f.write(data["content_raw"])

            # Write images
            if data.get("images"):
                f.write("\n---\n\n## Images\n\n")
                for idx, img in enumerate(data["images"], 1):
                    f.write(f"{idx}. {img['url']}\n")
                    if img.get("caption"):
                        f.write(f"   Caption: {img['caption']}\n")
                    f.write("\n")

        print(f"Saved Markdown: {md_path}")

    def scrape_multiple(self, urls: List[str]) -> List[Dict]:
        """
        Scrape multiple URLs.

        Args:
            urls: List of URLs to scrape

        Returns:
            List of extracted data dictionaries
        """
        results = []

        for url in urls:
            try:
                data = self.scrape(url)
                results.append(data)

                # Be respectful: add delay between requests
                time.sleep(2)

            except Exception as e:
                print(f"Failed to scrape {url}: {e}")
                results.append({"url": url, "error": str(e)})

        return results

    def add_extractor(self, extractor: BaseExtractor, priority: int = -1):
        """
        Add a custom extractor to the scraper.

        Args:
            extractor: An instance of a BaseExtractor subclass
            priority: Position in the extractor list (lower = higher priority)
                     -1 means insert before GenericExtractor
        """
        if priority == -1:
            # Insert before the last extractor (GenericExtractor)
            self.extractors.insert(-1, extractor)
        else:
            self.extractors.insert(priority, extractor)


def main():
    """
    Demonstration of the universal scraper.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("-u", "--urls", nargs="+", help="URLs to scrape")
    args = parser.parse_args()
    urls = args.urls

    # Initialize scraper
    scraper = UniversalTechBlogScraper(output_dir="scraped_content")
    # Scrape all URLs
    results = scraper.scrape_multiple(urls)

    # Print summary
    print("\n" + "=" * 80)
    print("SCRAPING SUMMARY")
    print("=" * 80)
    for result in results:
        print(f"\nURL: {result.get('url')}")
        print(f"  Status: {'✓ Success' if not result.get('error') else '✗ Failed'}")
        if result.get("title"):
            print(f"  Title: {result['title']}")
        if result.get("extractor"):
            print(f"  Extractor: {result['extractor']}")
        if result.get("error"):
            print(f"  Error: {result['error']}")


if __name__ == "__main__":
    main()
