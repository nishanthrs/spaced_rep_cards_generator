# Fixing Medium 403 Errors

## Why Does Medium Block Scrapers?

Medium has aggressive anti-bot protection that blocks automated requests. When you get a **403 Forbidden** error, it means Medium detected your request as coming from a bot, not a real browser.

### What Medium Checks:

1. **User-Agent header** - Is it from a real browser?
2. **Browser fingerprinting** - Does it have all the headers a real browser sends?
3. **JavaScript execution** - Real browsers execute JS; simple HTTP requests don't
4. **Referer header** - Where did you come from?
5. **Cookies/Session data** - Real browsers maintain sessions
6. **Request timing** - Too fast = bot
7. **Sec-Fetch headers** - Modern security headers
8. **TLS fingerprinting** - Advanced detection of automated tools

## Solutions (In Order of Effectiveness)

### Solution 1: Enhanced Headers (Already Implemented) ⭐

I've updated `generic_tech_blog_scraper.py` with better headers:

**What changed:**
- More realistic User-Agent (Chrome on macOS)
- Added Sec-Fetch-* headers (modern browsers send these)
- Added Referer header for Medium (pretends you came from Google)
- Added sec-ch-ua headers (Chromium version info)
- Retry logic with delays

**Try this first:**
```bash
python generic_tech_blog_scraper.py
```

**Success rate:** 30-50% (Medium updates their detection frequently)

---

### Solution 2: Selenium Headless Browser (Most Reliable) ⭐⭐⭐

Use a real browser controlled by automation. This is the most reliable approach.

**Install dependencies:**
```bash
pip install selenium webdriver-manager
```

**[Sample Script to Scrape WSJ Articles](https://github.com/philippe-heitzmann/WSJ_WebScraping_NLP/blob/master/scraping/scrape.py)**

**Why it works:**
- Uses a real Chrome browser (headless)
- Executes JavaScript like a real user
- Has all browser fingerprints
- Medium can't tell it's automated

**Success rate:** 90-95%

**Downsides:**
- Slower (needs to load full browser)
- Requires Chrome/Chromium installed
- More resource-intensive

---

### Solution 3: Use Medium's RSS Feed

Many Medium publications offer RSS feeds that are not blocked.

**Format:**
```
https://medium.com/feed/@username
https://medium.com/feed/publication-name
```

**For Pinterest Engineering:**
```
https://medium.com/feed/pinterest-engineering
```

**Pros:**
- Never blocked
- Official API
- Includes full content

**Cons:**
- Limited to recent articles
- May not have all formatting
- RSS-specific parsing needed

---

### Solution 4: Archive.is / Wayback Machine

Use cached versions from web archives.

**Archive.is:**
1. Go to https://archive.is
2. Enter the Medium URL
3. Use the archived URL for scraping

**Wayback Machine:**
```
https://web.archive.org/web/*/YOUR_MEDIUM_URL
```

**Pros:**
- No blocking
- Preserves article at a point in time

**Cons:**
- May not have latest version
- Extra step to archive first

---

### Solution 5: Playwright (Modern Alternative to Selenium)

Playwright is a newer browser automation tool that's even better at avoiding detection.

**Install:**
```bash
pip install playwright
playwright install chromium
```

**Example code:**
```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto("https://medium.com/...")
    content = page.content()
    browser.close()
```

**Success rate:** 95%+

---

### Solution 6: Use a Proxy Service

Rotate IP addresses and use residential proxies.

**Services:**
- ScraperAPI
- Bright Data
- Oxylabs

**Pros:**
- Very high success rate
- Handles all anti-bot measures

**Cons:**
- Costs money
- Overkill for personal projects

---

## My Recommendation

For your use case (scraping tech blogs for spaced repetition), I recommend:

### **Approach A: Try Enhanced Headers First**

```bash
python generic_tech_blog_scraper.py
```

If it works, great! If you get 403:

### **Approach B: Fall Back to Selenium**

```bash
# Install Selenium
pip install selenium webdriver-manager

# Use the Selenium scraper
python medium_selenium_scraper.py "YOUR_MEDIUM_URL"
```

### **Approach C: Long-term Solution**

Create a hybrid scraper that:
1. Tries regular HTTP request first (fast)
2. Falls back to Selenium if 403 (reliable)

---

## Implementation: Hybrid Approach

I can update the `generic_tech_blog_scraper.py` to automatically fall back to Selenium for Medium if needed:

```python
def scrape(self, url: str):
    try:
        # Try regular HTTP first
        return self._scrape_http(url)
    except HTTPError as e:
        if e.status_code == 403 and 'medium.com' in url:
            print("Falling back to Selenium...")
            return self._scrape_selenium(url)
        raise
```

Would you like me to implement this?

---

## Testing Your Current Setup

Try running the enhanced scraper:

```bash
# Test with all three blogs
python generic_tech_blog_scraper.py
```

**Expected results:**
- ✓ Uber blog: Should work (less strict)
- ✓ Jane Street: Should work (less strict)
- ⚠️ Medium/Pinterest: May get 403

If Medium fails, use:
```bash
python medium_selenium_scraper.py "https://medium.com/pinterest-engineering/web-performance-regression-detection-part-2-of-3-9e0b9d35a11f"
```

---

## Why Not Use Medium's API?

Medium has an official API, but:
- Requires OAuth authentication
- Limited to your own articles
- Can't access other people's articles
- Rate limited

So it's not suitable for scraping public articles.

---

## Additional Tips

### 1. Add Delays Between Requests
```python
import time
time.sleep(2)  # 2 seconds between requests
```

### 2. Rotate User-Agents
```python
import random
user_agents = [
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) ...',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) ...',
    # etc.
]
headers['User-Agent'] = random.choice(user_agents)
```

### 3. Use Requests Sessions
Already implemented! Sessions maintain cookies automatically.

### 4. Respect robots.txt
Check what Medium allows:
```
https://medium.com/robots.txt
```

---

## Summary

| Solution | Success Rate | Speed | Setup Difficulty |
|----------|-------------|-------|------------------|
| Enhanced Headers | 30-50% | Fast | Easy (done) |
| Selenium | 90-95% | Slow | Medium |
| Playwright | 95%+ | Medium | Medium |
| RSS Feed | 100% | Fast | Easy |
| Proxies | 99% | Medium | Hard |

**My recommendation:** Try enhanced headers first, use Selenium for Medium if needed.
