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

# Run E2E script to scrape content, feed it to LLM, log spaced repetition card output to terminal, and create spaced repetition cards in Mochi
python3 spaced_repetition_card_gen_pipeline.py -u "<url>"
# Run E2E script without creating spaced repetition cards in Mochi
python3 spaced_repetition_card_gen_pipeline.py -u "<url>" -nc
# Add custom prompting to steer spaced repetition card generation (focus on only specific sections in article, generate card with code examples, etc)
python3 spaced_repetition_card_gen_pipeline.py -u "<url>" -p "<custom_additional_prompt>"
# Enable thinking mode (for potentially better cards, but cards seem to be of similar quality with non-thinking mode)
python3 spaced_repetition_card_gen_pipeline.py -u "<url>" -t
```

## References
* [Guide to Effective Spaced Repetition](https://borretti.me/article/effective-spaced-repetition)
* [Mochi API Client Wrapper](https://github.com/GSejas/mochi-api-client/tree/main) (not needed right now)
* [Sample Script to Scrape WSJ Articles](https://github.com/philippe-heitzmann/WSJ_WebScraping_NLP/blob/master/scraping/scrape.py)
*

## TODO:
- [x] [P0] Write some scaffolding for the Mochi API so that it can read and generate new spaced repetition cards and put them in my account right away
- [x] [P0] Write prompt to generate spaced repetition cards.
- [x] [P0] Scrape data from website so that tool can read data from the sources.
  - [x] Semianalysis articles (semianalysis_scraper.py)
  - [x] Random tech blogs (generic_tech_blog_scraper.py - hybrid approach with domain-specific extractors)
- [x] Use LLM (Claude or Qwen3) to generate spaced repetition cards.
  - [x] [P0] First have the tool generate the output.
  - [x] [P0] Optimize LLM inference on Mac M4 (takes way too long right now; one run at ~20 mins; impossible to test)
  - [x] [P0] After the data is verified, confirm that it can generate the spaced repetition cards in your Mochi account to the appropriate deck
- [x] [P0] Build E2E script so that it can be executed in one CLI cmd
- [x] [P0] Verify that the spaced repetition cards are actually useful and testing you on knowledge that you want to retain!
- [ ] Gradually expand sources of data to all your sources of consumption:
  - [ ] [P0] YT videos (yt-dlp)
  - [ ] [P0] News articles with required auth / strong bot protections (e.g. Medium, WSJ, Financial Times, )
    - **[Sample Script to Scrape WSJ Articles](https://github.com/philippe-heitzmann/WSJ_WebScraping_NLP/blob/master/scraping/scrape.py)**
    - Also explore options by scraping articles from WaybackMachine, archive.is, archive.ph, etc
  - [ ] [P1] Books (EPUB downloads)
    - This one might be a big harder to scrape. See if Anna's Archive or Libgen has an API or if we can use selenium to download EPUB files.
- [ ] [P1] Productize this tool to see if anyone would use it
  - [ ] Deploy on web server as API
  - [ ] Build a web app interface (Next.JS with Tailwind)
  - [ ] Build a chrome/firefox extension
  - [ ] Look into increasing performance of tool (latency first, then throughput)
    - [ ] Run load tests
    - [ ] Write web server logic in Rust or Go
    - [ ] Deploy card generation on vLLM or SGLang or llama.cpp servers to increase throughput (and possibly latency) of service
      - [ ] Deploy on GPU workers for faster token generation
    *NOTE: Not expecting this tool to achieve significant scale or anything like that; this is purely out of curiosity and fun*
- [ ] [P2] See if multimodal support can be added so that we can create richer cards that ask and answer questions about image data as well
- [ ] [P2] Extend this tool to support content Q&A (talk-to-article) with citations
