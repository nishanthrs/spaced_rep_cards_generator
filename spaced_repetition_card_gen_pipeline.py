import argparse
from os import listdir

from scraper_utils.generic_tech_blog_scraper import UniversalTechBlogScraper
from llm_utils.gen_mochi_cards import QwenChatbot


SCRAPED_CONTENT_DIR = "scraper_utils/scraped_content"
TECHNICAL_READINGS_DECKS = "eaUFr02Y"
CARD_DELIMITER = "---"
# Inspired by https://andymatuschak.org/prompts/
PRE_PROMPT = f"""
    I want you to create a set of 10 spaced repetition cards based on some article or text so that I can use these cards to retain
    and remember important things from the article for longer.
    These cards have two sides: a front and a back. The front is a retrieval practice prompt and the back is the answer to that prompt.
    Each card should be structured as: line 1 = ### Card <X>, line 2 = Front: <Prompt>, line 3 = Back: <Answer>
    Make sure to include a delimiter like {CARD_DELIMITER} after each card.

    Here are a few guidelines to writing good retrieval practice prompt:
    1. Retrieval practice prompts should be focused. A question or answer involving too much detail will dull your concentration and stimulate incomplete retrievals, leaving some bulbs unlit. Unfocused questions also make it harder to check whether you remembered all parts of the answer and to note places where you differed. It’s usually best to focus on one detail at a time.
    2. Retrieval practice prompts should be precise about what they’re asking for. Vague questions will elicit vague answers, which won’t reliably light the bulbs you’re targeting.
    3. Retrieval practice prompts should produce consistent answers, lighting the same bulbs each time you perform the task. Otherwise, you may run afoul of an interference phenomenon called “retrieval-induced forgetting”This effect has been produced in many experiments but is not yet well understood. For an overview, see Murayama et al, Forgetting as a consequence of retrieval: a meta-analytic review of retrieval-induced forgetting (2014).: what you remember during practice is reinforced, but other related knowledge which you didn’t recall is actually inhibited. Now, there is a useful type of prompt which involves generating new answers with each repetition, but such prompts leverage a different theory of change. We’ll discuss them briefly later in this guide.
    4. SuperMemo’s algorithms (also used by most other major systems) are tuned for 90% accuracy. Each review would likely have a larger impact on your memory if you targeted much lower accuracy numbers—see e.g. Carpenter et al, Using Spacing to Enhance Diverse Forms of Learning (2012). Higher accuracy targets trade efficiency for reliability.Retrieval practice prompts should be tractable. To avoid interference-driven churn and recurring annoyance in your review sessions, you should strive to write prompts which you can almost always answer correctly. This often means breaking the task down, or adding cues.
    5. Retrieval practice prompts should be effortful. It’s important that the prompt actually involves retrieving the answer from memory. You shouldn’t be able to trivially infer the answer. Cues are helpful, as we’ll discuss later—just don’t “give the answer away.” In fact, effort appears to be an important factor in the effects of retrieval practice.For more on the notion that difficult retrievals have a greater impact than easier retrievals, see the discussion in Bjork and Bjork, A New Theory of Disuse and an Old Theory of Stimulus Fluctuation (1992). Pyc and Rawson, Testing the retrieval effort hypothesis: Does greater difficulty correctly recalling information lead to higher levels of memory? (2009) offers some focused experimental tests of this theory, which they coin the “retrieval effort hypothesis.”
    That’s one motivation for spacing reviews out over time: if it’s too easy to recall the answer, retrieval practice has little effect.
    6. ABOVE ALL, FOCUS ON GENERATING CARDS FOR REMEMBERING THE TECHNICAL DETAILS ON THE ARTICLE. NO QUESTIONS ABOUT THE AUTHORS, SOCIAL MEDIA, OR ANY OTHER IRRELEVANT CONTENT.

    You should only use the article text to come up with good retrieval practice prompts and answers to those prompts. I will then use these to study and remember and apply this valuable information from the articles.
    Here is the article in markdown format:
"""

def main():
    """
    Model names:
    1. Qwen/Qwen3-30B-A3B
    2. Qwen/Qwen3-8B
    3. MLX model names here: https://huggingface.co/collections/mlx-community/qwen3
    """
    # Setup CLI
    parser = argparse.ArgumentParser()
    parser.add_argument("-u", "--urls", nargs="+", help="URLs to scrape")
    args = parser.parse_args()
    urls = args.urls

    # Initialize scraper
    scraper = UniversalTechBlogScraper(output_dir=SCRAPED_CONTENT_DIR)
    # Scrape all URLs
    results = scraper.scrape_multiple(urls)

    # Scraper logs
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

    # Init LLM (on Mac for now), ingest scraped content from files, and generate Mochi cards
    # TODO: For further customization and better generation of cards, add a power user arg that takes
    # in further instructions to focus on specific sections of the article to generate cards for
    chatbot = QwenChatbot("mlx-community/Qwen3-30B-A3B-4bit")
    scraped_content_files = listdir(SCRAPED_CONTENT_DIR)
    url_delimiter = "**Source:** "
    for f in scraped_content_files:
        user_input = PRE_PROMPT
        with open(f"{SCRAPED_CONTENT_DIR}/{f}", "r") as f:
            url = ""
            for line in f:
                if url_delimiter in line:
                    url = line.split(url_delimiter)[1]
                    break

            article_content = f.read()
            chatbot.generate_mochi_cards(
                url,
                PRE_PROMPT + article_content,
                TECHNICAL_READINGS_DECKS
            )

if __name__ == "__main__":
    main()
