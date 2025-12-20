# SemiAnalysis Article Scraper

A Python web scraper designed to extract text and image data from SemiAnalysis newsletter articles.

## Features

- **Text Extraction**: Captures all text content including headings, paragraphs, lists, quotes, and code blocks
- **Image Downloading**: Downloads all images with their captions and alt text
- **Metadata Extraction**: Extracts article title, author, publication date, and description
- **Multiple Output Formats**: Saves data as JSON, Markdown, and plain text
- **Robust Error Handling**: Gracefully handles missing elements and download failures
- **Organized Storage**: Creates structured directories for text and images

## Installation

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

Run the scraper with the default article URL:
```bash
python semianalysis_scraper.py
```

### Custom Usage

To scrape a different article, modify the `article_url` variable in the `main()` function:

```python
def main():
    scraper = SemiAnalysisScraper(output_dir="scraped_articles")
    article_url = "https://newsletter.semianalysis.com/p/your-article-slug"
    article_data = scraper.scrape_article(article_url)
```

### Using as a Module

You can also import and use the scraper in your own code:

```python
from semianalysis_scraper import SemiAnalysisScraper

# Initialize scraper
scraper = SemiAnalysisScraper(output_dir="my_articles")

# Scrape an article
article_data = scraper.scrape_article("https://newsletter.semianalysis.com/p/the-memory-wall")

# Access the data
print(f"Title: {article_data['metadata']['title']}")
print(f"Number of images: {len(article_data['images'])}")

# Iterate through text content
for block in article_data['text_content']:
    print(f"{block['type']}: {block['content']}")
```

## Output Structure

The scraper creates the following directory structure:

```
scraped_articles/
├── text/
│   ├── Article_Title.json          # Full article data in JSON format
│   ├── Article_Title.md            # Formatted Markdown version
│   └── Article_Title.txt           # Plain text version
└── images/
    └── Article_Title/
        ├── image_001.jpg
        ├── image_002.png
        └── ...
```

### JSON Output

The JSON file contains:
- `url`: Original article URL
- `metadata`: Title, author, date, description, etc.
- `text_content`: Array of content blocks with type and content
- `images`: Array of image metadata including URLs, captions, and local paths
- `scrape_timestamp`: When the article was scraped

### Content Block Types

The scraper recognizes these content types:
- `heading_1` through `heading_6`: Article headings
- `paragraph`: Regular paragraphs
- `unordered_list` / `ordered_list`: Bulleted and numbered lists
- `quote`: Blockquotes
- `code`: Code blocks

## How It Works

### 1. Page Fetching
- Uses a session with browser-like headers to avoid blocks
- Implements timeout and error handling

### 2. Metadata Extraction
- Searches multiple sources: Open Graph tags, JSON-LD, meta tags
- Falls back to alternative selectors if primary ones fail

### 3. Text Content Extraction
- Finds the main article container using multiple CSS selectors
- Preserves content structure (headings, paragraphs, lists)
- Filters out empty or irrelevant content

### 4. Image Extraction
- Identifies images within the article container
- Handles both direct `src` and lazy-loaded `data-src` attributes
- Extracts captions from `<figcaption>` tags or `alt` attributes
- Downloads images with proper error handling
- Skips placeholder and tracking images

### 5. Data Storage
- Saves in three formats for different use cases:
  - JSON: For programmatic access
  - Markdown: For human-readable formatted text
  - Plain text: For simple reading

## Edge Cases Handled

1. **Missing Elements**: Uses fallback selectors and graceful degradation
2. **Failed Image Downloads**: Records metadata even if download fails
3. **Invalid Filenames**: Sanitizes titles to create safe filenames
4. **Relative URLs**: Converts to absolute URLs before downloading
5. **Rate Limiting**: Adds delays between image downloads
6. **Empty Content**: Skips empty paragraphs and elements
7. **Special Characters**: Handles Unicode properly in all output formats

## Limitations

- Designed specifically for Substack-hosted articles (SemiAnalysis uses Substack)
- May need adjustments if Substack changes their HTML structure
- Respects server load with delays between requests
- Does not handle paywalled content (requires authentication)

## Troubleshooting

**Images not downloading?**
- Check your internet connection
- Verify the image URLs are accessible
- Check if the site requires authentication

**Missing content?**
- The article might use different HTML classes
- Check the HTML structure and update selectors if needed

**Import errors?**
- Make sure all dependencies are installed: `pip install -r requirements.txt`

## License

This scraper is for educational purposes. Respect SemiAnalysis's terms of service and copyright.
