# Spaced Repetition Card Generator

I consume so much valuable information daily, but I find it frustrating that I can never remember or recall any of it. For the most important content, I should build and use spaced repetition to actually retain it (see [here](https://gwern.net/spaced-repetition) and [here](https://www.dwarkesh.com/p/andy-matuschak) for reasons why). Who knows, I might do something with that information one day.

**This CLI tool will allow me to automatically generate spaced repetition cards on the content I consume.** Whether it's Semianalysis articles, tech blogs, WSJ videos, or books, it'll ingest the data from these sources and automatically generate cards for me to remember.


## Web Scrapers

Two scraping approaches are available:

1. **`semianalysis_scraper.py`** - Substack-specific scraper optimized for SemiAnalysis articles
2. **`generic_tech_blog_scraper.py`** - Universal scraper with domain-specific extractors + generic fallback (RECOMMENDED)

See `SCRAPER_COMPARISON.md` for detailed comparison.

### Quick Start

```bash
# Create and activate virtual environment (better in isolating dependencies from rest of system)
python3 -m venv .venv
source .venv/bin/activate
# Install dependencies
pip install -r requirements.txt
# Make sure env vars are set up
source ~/.bashrc
# ALSO MAKE SURE TO INSTALL FFMPEG AND FFPROBE FOR VIDEO TRANSCRIPTION SUPPORT (yt_dlp)!
# Mac: downloaded homebrew via `/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"`, additional instructions from https://stackoverflow.com/questions/65619529/fixing-zsh-command-not-found-brew-installing-homebrew, `source ~/.bashrc`
# Then I was finally able to run `brew install ffmpeg` successfully

# Run E2E script to scrape content, feed it to LLM, log spaced repetition card output to terminal, and create spaced repetition cards in Mochi
python3 spaced_repetition_card_gen_pipeline.py -u "<url>"
# Run E2E script without creating spaced repetition cards in Mochi
python3 spaced_repetition_card_gen_pipeline.py -u "<url>" -nc
# Add custom prompting to steer spaced repetition card generation (focus on only specific sections in article, generate card with code examples, etc)
python3 spaced_repetition_card_gen_pipeline.py -u "<url>" -p "<custom_additional_prompt>"
# Enable thinking mode (for potentially better cards, but cards seem to be of similar quality with non-thinking mode)
python3 spaced_repetition_card_gen_pipeline.py -u "<url>" -t

NOTE: Models are stored ~/.cache/huggingface/hub
```

## References
### Virtues of Spaced Repetition
* [Guide to Effective Spaced Repetition](https://borretti.me/article/effective-spaced-repetition)
* [Spaced Repetition for Efficient Learning](https://gwern.net/spaced-repetition)
* [Andy Matuschak: The Reason Most Learning Tools Fail](https://www.dwarkesh.com/p/andy-matuschak)

### Useful Projects
* [Mochi API Client Wrapper](https://github.com/GSejas/mochi-api-client/tree/main) (wrapper not needed; can call API directly)
* [Sample Script to Scrape WSJ Articles](https://github.com/philippe-heitzmann/WSJ_WebScraping_NLP/blob/master/scraping/scrape.py)
