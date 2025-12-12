#!/usr/bin/env python3
"""
SemiAnalysis Article Scraper

This script scrapes text and image data from SemiAnalysis newsletter articles.
SemiAnalysis is hosted on Substack, so this scraper is designed to work with
Substack's HTML structure.

Usage:
    python semianalysis_scraper.py

Requirements:
    pip install requests beautifulsoup4 pillow
"""

import json
import os
import re
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup


class SemiAnalysisScraper:
    """
    A web scraper specifically designed for SemiAnalysis newsletter articles.

    This scraper extracts:
    - Article title
    - Article subtitle/description
    - Publication date
    - Author information
    - All text content (paragraphs, headings, lists)
    - All images with their captions
    - Article metadata
    """

    def __init__(self, output_dir: str = "scraped_articles"):
        """
        Initialize the scraper.

        Args:
            output_dir: Directory where scraped content will be saved
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        # Create subdirectories for organized storage
        self.text_dir = self.output_dir / "text"
        self.images_dir = self.output_dir / "images"
        self.text_dir.mkdir(exist_ok=True)
        self.images_dir.mkdir(exist_ok=True)

        # Set up a session with headers to mimic a real browser
        # This helps avoid being blocked by the server
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
            }
        )

    def _sanitize_filename(self, text: str) -> str:
        """
        Convert text to a safe filename by removing special characters.

        Args:
            text: The text to sanitize

        Returns:
            A safe filename string
        """
        # Remove or replace characters that are invalid in filenames
        text = re.sub(r'[<>:"/\\|?*]', "", text)
        # Replace spaces with underscores
        text = text.replace(" ", "_")
        # Limit length to avoid filesystem issues
        return text[:200]

    def _fetch_page(self, url: str) -> BeautifulSoup:
        """
        Fetch a webpage and return a BeautifulSoup object.

        Args:
            url: The URL to fetch

        Returns:
            BeautifulSoup object containing the parsed HTML

        Raises:
            requests.RequestException: If the request fails
        """
        try:
            print(f"Fetching: {url}")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()  # Raise an exception for bad status codes

            # Parse with html.parser (built-in) or lxml (faster, requires installation)
            return BeautifulSoup(response.content, "html.parser")

        except requests.RequestException as e:
            print(f"Error fetching page: {e}")
            raise

    def _extract_metadata(self, soup: BeautifulSoup) -> Dict[str, str]:
        """
        Extract article metadata (title, subtitle, author, date, etc.).

        Substack stores metadata in various places:
        - Open Graph meta tags (og:title, og:description, etc.)
        - JSON-LD structured data
        - HTML elements with specific classes

        Args:
            soup: BeautifulSoup object of the page

        Returns:
            Dictionary containing metadata
        """
        metadata = {}

        # Try to extract title from multiple sources for robustness
        # 1. Open Graph meta tag
        og_title = soup.find("meta", property="og:title")
        if og_title:
            metadata["title"] = og_title.get("content", "")

        # 2. Standard title tag as fallback
        if "title" not in metadata or not metadata["title"]:
            title_tag = soup.find("title")
            if title_tag:
                metadata["title"] = title_tag.string.strip()

        # 3. Article h1 heading as last resort
        if "title" not in metadata or not metadata["title"]:
            h1 = soup.find("h1", class_="post-title")
            if h1:
                metadata["title"] = h1.get_text(strip=True)

        # Extract description/subtitle
        og_description = soup.find("meta", property="og:description")
        if og_description:
            metadata["description"] = og_description.get("content", "")

        # Extract author
        # Substack typically has author info in meta tags
        author_tag = soup.find("meta", attrs={"name": "author"})
        if author_tag:
            metadata["author"] = author_tag.get("content", "")

        # Alternative: look for author in article-meta div
        if "author" not in metadata or not metadata["author"]:
            author_elem = soup.find(
                "a",
                class_="frontend-pencraft-Text-module__decoration-hover-underline--BEYAn",
            )
            if author_elem:
                metadata["author"] = author_elem.get_text(strip=True)

        # Extract publication date
        # Look for time element with datetime attribute
        time_elem = soup.find("time")
        if time_elem:
            metadata["publication_date"] = time_elem.get(
                "datetime", time_elem.get_text(strip=True)
            )

        # Extract article URL
        og_url = soup.find("meta", property="og:url")
        if og_url:
            metadata["url"] = og_url.get("content", "")

        # Extract any JSON-LD structured data
        # This often contains rich metadata in Substack articles
        json_ld = soup.find("script", type="application/ld+json")
        if json_ld:
            try:
                structured_data = json.loads(json_ld.string)
                metadata["structured_data"] = structured_data
            except json.JSONDecodeError:
                pass

        return metadata

    def _extract_text_content(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """
        Extract all text content from the article in structured format.

        Substack articles are typically contained in divs with class 'body' or 'post-content'.
        This method preserves the structure (headings, paragraphs, lists, etc.)

        Args:
            soup: BeautifulSoup object of the page

        Returns:
            List of dictionaries, each containing 'type' and 'content'
        """
        content_blocks = []

        # Find the main article container
        # Substack uses various classes, so we try multiple selectors
        article_container = (
            soup.find("div", class_="available-content")
            or soup.find("div", class_="body")
            or soup.find("article")
            or soup.find("div", class_="post-content")
        )

        if not article_container:
            print("Warning: Could not find main article container")
            return content_blocks

        # Iterate through all elements in the article
        # We look for headings, paragraphs, lists, blockquotes, etc.
        for element in article_container.find_all(
            ["h1", "h2", "h3", "h4", "h5", "h6", "p", "ul", "ol", "blockquote", "pre"]
        ):
            # Skip empty elements
            text = element.get_text(strip=True)
            if not text:
                continue

            # Determine the type of content
            tag_name = element.name

            if tag_name.startswith("h"):
                # Heading
                content_blocks.append(
                    {
                        "type": f"heading_{tag_name[1]}",  # h1 -> heading_1, h2 -> heading_2, etc.
                        "content": text,
                    }
                )

            elif tag_name == "p":
                # Paragraph
                content_blocks.append({"type": "paragraph", "content": text})

            elif tag_name in ["ul", "ol"]:
                # List - extract each list item
                list_type = "unordered_list" if tag_name == "ul" else "ordered_list"
                list_items = [
                    li.get_text(strip=True)
                    for li in element.find_all("li", recursive=False)
                ]
                content_blocks.append({"type": list_type, "content": list_items})

            elif tag_name == "blockquote":
                # Quote
                content_blocks.append({"type": "quote", "content": text})

            elif tag_name == "pre":
                # Code block
                content_blocks.append({"type": "code", "content": text})

        return content_blocks

    def _extract_images(
        self, soup: BeautifulSoup, article_title: str
    ) -> List[Dict[str, str]]:
        """
        Extract all images from the article and download them.

        Args:
            soup: BeautifulSoup object of the page
            article_title: Title of the article (used for organizing image files)

        Returns:
            List of dictionaries containing image metadata and local paths
        """
        images = []

        # Find the main article container to avoid header/footer images
        article_container = (
            soup.find("div", class_="available-content")
            or soup.find("div", class_="body")
            or soup.find("article")
            or soup.find("div", class_="post-content")
        )

        if not article_container:
            # Fallback to searching the entire page
            article_container = soup

        # Find all image tags
        img_tags = article_container.find_all("img")

        # Create a subdirectory for this article's images
        article_slug = self._sanitize_filename(article_title)
        article_image_dir = self.images_dir / article_slug
        article_image_dir.mkdir(exist_ok=True)

        for idx, img in enumerate(img_tags, 1):
            # Extract image URL
            # Substack uses 'src' for direct images and sometimes 'data-src' for lazy-loaded images
            img_url = img.get("src") or img.get("data-src")

            if not img_url:
                continue

            # Skip placeholder images, tracking pixels, and tiny images
            if any(
                skip in img_url.lower() for skip in ["placeholder", "tracking", "pixel"]
            ):
                continue

            # Convert relative URLs to absolute URLs
            if img_url.startswith("//"):
                img_url = "https:" + img_url
            elif img_url.startswith("/"):
                img_url = urljoin("https://newsletter.semianalysis.com", img_url)

            # Extract image caption
            # Captions in Substack are often in figcaption tags or in the alt attribute
            caption = ""

            # Check for figcaption (most common in Substack)
            figure = img.find_parent("figure")
            if figure:
                figcaption = figure.find("figcaption")
                if figcaption:
                    caption = figcaption.get_text(strip=True)

            # Fallback to alt text if no caption found
            if not caption:
                caption = img.get("alt", "")

            # Download the image
            try:
                local_path = self._download_image(img_url, article_image_dir, idx)

                images.append(
                    {
                        "url": img_url,
                        "caption": caption,
                        "alt_text": img.get("alt", ""),
                        "local_path": str(local_path),
                        "index": idx,
                    }
                )

                print(f"  Downloaded image {idx}: {img_url}")

            except Exception as e:
                print(f"  Failed to download image {idx} ({img_url}): {e}")
                # Still record the image metadata even if download fails
                images.append(
                    {
                        "url": img_url,
                        "caption": caption,
                        "alt_text": img.get("alt", ""),
                        "local_path": None,
                        "index": idx,
                        "error": str(e),
                    }
                )

        return images

    def _download_image(self, url: str, save_dir: Path, index: int) -> Path:
        """
        Download an image from a URL and save it locally.

        Args:
            url: URL of the image
            save_dir: Directory to save the image
            index: Index number for the filename

        Returns:
            Path to the saved image

        Raises:
            requests.RequestException: If download fails
        """
        # Extract file extension from URL
        parsed_url = urlparse(url)
        path = parsed_url.path
        ext = os.path.splitext(path)[1]

        # Default to .jpg if no extension found
        if not ext or len(ext) > 5:
            ext = ".jpg"

        # Create filename
        filename = f"image_{index:03d}{ext}"
        filepath = save_dir / filename

        # Download the image
        response = self.session.get(url, timeout=30, stream=True)
        response.raise_for_status()

        # Save to file
        with open(filepath, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        # Small delay to be respectful to the server
        time.sleep(0.5)

        return filepath

    def scrape_article(self, url: str) -> Dict:
        """
        Main method to scrape a complete article.

        Args:
            url: URL of the SemiAnalysis article

        Returns:
            Dictionary containing all scraped data
        """
        print(f"\n{'='*80}")
        print(f"Scraping article: {url}")
        print(f"{'='*80}\n")

        # Fetch and parse the page
        soup = self._fetch_page(url)

        # Extract all components
        print("Extracting metadata...")
        metadata = self._extract_metadata(soup)

        print("Extracting text content...")
        text_content = self._extract_text_content(soup)

        print("Extracting and downloading images...")
        images = self._extract_images(soup, metadata.get("title", "untitled"))

        # Combine all data
        article_data = {
            "url": url,
            "metadata": metadata,
            "text_content": text_content,
            "images": images,
            "scrape_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        }

        # Save the data
        self._save_article_data(article_data, metadata.get("title", "untitled"))

        print(f"\n{'='*80}")
        print(f"Scraping complete!")
        print(f"  - Title: {metadata.get('title', 'N/A')}")
        print(f"  - Text blocks: {len(text_content)}")
        print(f"  - Images: {len(images)}")
        print(f"{'='*80}\n")

        return article_data

    def _save_article_data(self, article_data: Dict, title: str):
        """
        Save the scraped article data to disk in multiple formats.

        Args:
            article_data: The complete article data dictionary
            title: Title of the article
        """
        # Create a safe filename from the title
        safe_title = self._sanitize_filename(title)

        # Save as JSON for programmatic access
        json_path = self.text_dir / f"{safe_title}.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(article_data, f, indent=2, ensure_ascii=False)
        print(f"\nSaved JSON: {json_path}")

        # Save as Markdown for human readability
        md_path = self.text_dir / f"{safe_title}.md"
        with open(md_path, "w", encoding="utf-8") as f:
            # Write metadata
            f.write(f"# {article_data['metadata'].get('title', 'Untitled')}\n\n")

            if article_data["metadata"].get("author"):
                f.write(f"**Author:** {article_data['metadata']['author']}\n\n")

            if article_data["metadata"].get("publication_date"):
                f.write(
                    f"**Published:** {article_data['metadata']['publication_date']}\n\n"
                )

            if article_data["metadata"].get("description"):
                f.write(f"*{article_data['metadata']['description']}*\n\n")

            f.write(f"**Source:** {article_data['url']}\n\n")
            f.write("---\n\n")

            # Write content
            for block in article_data["text_content"]:
                block_type = block["type"]
                content = block["content"]

                if block_type.startswith("heading_"):
                    level = int(block_type.split("_")[1])
                    f.write(f"{'#' * level} {content}\n\n")

                elif block_type == "paragraph":
                    f.write(f"{content}\n\n")

                elif block_type in ["unordered_list", "ordered_list"]:
                    prefix = "-" if block_type == "unordered_list" else "1."
                    for item in content:
                        f.write(f"{prefix} {item}\n")
                    f.write("\n")

                elif block_type == "quote":
                    f.write(f"> {content}\n\n")

                elif block_type == "code":
                    f.write(f"```\n{content}\n```\n\n")

            # Write image references
            if article_data["images"]:
                f.write("\n---\n\n## Images\n\n")
                for img in article_data["images"]:
                    f.write(f"### Image {img['index']}\n\n")
                    if img.get("caption"):
                        f.write(f"**Caption:** {img['caption']}\n\n")
                    f.write(f"**URL:** {img['url']}\n\n")
                    if img.get("local_path"):
                        f.write(f"**Local file:** {img['local_path']}\n\n")
                    f.write("\n")

        print(f"Saved Markdown: {md_path}")


def main():
    """
    Main function to demonstrate usage of the scraper.
    """
    # Initialize the scraper
    scraper = SemiAnalysisScraper(output_dir="scraped_semianalysis_articles")

    # The article URL to scrape
    article_urls = [
        "https://newsletter.semianalysis.com/p/scaling-the-memory-wall-the-rise-and-roadmap-of-hbm",
        "https://newsletter.semianalysis.com/p/the-memory-wall",
        "https://newsletter.semianalysis.com/p/google-we-have-no-moat-and-neither",
    ]

    for article_url in article_urls:
        """
        TODO: Very low-pri task but for large batch jobs (many articles), we can use a ThreadPoolExecutor to speed up the scraping process,
        similar to https://github.com/karpathy/hn-time-capsule/blob/master/pipeline.py#L642
        """

        # Scrape the article
        try:
            article_data = scraper.scrape_article(article_url)

            # You can now work with the article_data dictionary
            # For example, print the title and first few text blocks
            print("\n" + "=" * 80)
            print("ARTICLE PREVIEW")
            print("=" * 80)
            print(f"\nTitle: {article_data['metadata'].get('title')}")
            print(f"\nFirst 3 content blocks:")
            for i, block in enumerate(article_data["text_content"][:3], 1):
                print(f"\n{i}. [{block['type']}]")
                content = block["content"]
                if isinstance(content, list):
                    content = ", ".join(
                        content[:2]
                    )  # Just show first 2 items if it's a list
                print(f"   {content[:200]}...")  # Show first 200 characters

        except Exception as e:
            print(f"\nError scraping article: {e}")
            import traceback

            traceback.print_exc()


if __name__ == "__main__":
    main()
