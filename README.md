# Spaced Repetition Card Auto-Generator

I consume so much valuable information daily, but I find it frustrating that I can never remember or recall any of it. For the most important content, I should build and use spaced repetition to actually retain it (see [here](https://gwern.net/spaced-repetition) and [here](https://www.dwarkesh.com/p/andy-matuschak) for reasons why). Who knows, I might do something with that information one day.

This CLI tool will allow me to automatically generate spaced repetition cards on the content I consume. Whether it's Semianalysis articles, tech blogs, WSJ videos, or books, it'll ingest the data from these sources and automatically generate cards for me to remember.

## References
[Guide to Effective Spaced Repetition](https://borretti.me/article/effective-spaced-repetition)
[Mochi API Client Wrapper](https://github.com/GSejas/mochi-api-client/tree/main) (not needed right now)

## TODO:
- [x] Write some scaffolding for the Mochi API so that it can read and generate new spaced repetition cards and put them in my account right away
- [ ] Write prompt to generate spaced repetition cards.
- [ ] Scrape data from website so that tool can read data from the sources.
  - [ ] Semianalysis articles
  - [ ] Random tech blogs
- [ ] Use LLM (Claude or Qwen3) to generate spaced repetition cards.
  - [ ] First have the tool generate the output.
  - [ ] After the data is verified, confirm that it can generate the spaced repetition cards in your Mochi account to the appropriate deck.
- [ ] Gradually expand sources of data to all your sources of consumption:
  - [ ] Books (epub downloads)
  - [ ] YT videos (yt-dlp)
