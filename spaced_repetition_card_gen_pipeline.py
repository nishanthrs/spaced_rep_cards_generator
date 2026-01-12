import argparse
import os

from scraper_utils.generic_tech_blog_scraper import UniversalTechBlogScraper
from llm_utils.gen_mochi_cards import QwenChatbot
from video_transcription_utils.transcribe_video import VideoTranscriptionUtils

CONTENT_DIR = "tmp/scraped_content"
TECHNICAL_READINGS_DECKS = "eaUFr02Y"
CARD_DELIMITER = "---"


def gen_guidelines_on_card_gen(num_cards: int) -> str:
    # Inspired by https://andymatuschak.org/prompts/
    return f"""
        I want you to create a set of {num_cards} spaced repetition cards based on some article or text so that I can use these cards to retain
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
        6. ABOVE ALL, FOCUS ON GENERATING CARDS FOR REMEMBERING THE TECHNICAL DETAILS ON THE ARTICLE, SPECIFICALLY THE PROBLEM AND DETAILS OF HOW THAT PROBLEM IS SOLVED THROUGH TECHNICAL MEANS.
        FOCUS LESS ON SPECIFIC STATISTICS AND FIGURES AND MORE ON GENERAL CONCEPTS AND WHY THEY ARE IMPORTANT AND HOW THEY ARE USED TO SOLVE SPECIFIC PROBLEMS.
        NO QUESTIONS ABOUT THE AUTHORS, SOCIAL MEDIA, OR ANY OTHER IRRELEVANT CONTENT.

        You should only use the article text to come up with good retrieval practice prompts and answers to those prompts. I will then use these to study and remember and apply this valuable information from the articles.
        Here is the article in markdown or text format:
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
    parser.add_argument(
        "-u", "--url", type=str, help="URL to scrape", required=True
    )
    parser.add_argument(
        "-n",
        "--num-cards",
        type=int,
        help="Number of spaced repetition cards to generate for this URL",
        required=False,
        default=10,
    )
    parser.add_argument(
        "-nc",
        "--no-cards",
        action="store_true",
        help="Generate cards, but don't actually create them in Mochi.",
    )
    parser.add_argument(
        "-p",
        "--custom-additional-prompt",
        type=str,
        help="Custom additional prompt to control what kind of cards are generated",
    )
    parser.add_argument("-t", "--enable-thinking", action="store_true")
    args = parser.parse_args()
    url = args.url
    num_cards = args.num_cards

    if not os.path.exists(CONTENT_DIR):
        os.makedirs(CONTENT_DIR)

    if "youtube" in url:
        print("Youtube URL detected. Transcribing video...")
        video_transcription_utils = VideoTranscriptionUtils(
            whisper_model_name="mlx-community/whisper-large-v3-turbo"
        )
        audio_filepath, metadata_filepath = (
            video_transcription_utils.extract_audio_and_metadata_from_video(url)
        )
        # Transcribe audio from audio_filepath
        scraped_content_filepath = video_transcription_utils.transcribe_video_via_mlx_whisper(audio_filepath, CONTENT_DIR)
    else:
        # Scrape all URLs for content
        scraper = UniversalTechBlogScraper(output_dir=CONTENT_DIR)
        result = scraper.scrape(url)

        print("\n" + "=" * 80)
        print("SCRAPING SUMMARY")
        print("=" * 80)
        print(f"\nURL: {result.get('url')}")
        print(f"  Status: {'✓ Success' if not result.get('error') else '✗ Failed'}")
        if result.get("title"):
            print(f"  Title: {result['title']}")
        if result.get("extractor"):
            print(f"  Extractor: {result['extractor']}")
        if result.get("error"):
            print(f"  Error: {result['error']}")

        scraped_content_filepath = result["content_path"]

    # Use LLM to take text as context to generate spaced repetition cards
    pre_prompt = gen_guidelines_on_card_gen(num_cards)
    chatbot = QwenChatbot("mlx-community/Qwen3-30B-A3B-4bit")
    with open(scraped_content_filepath, "r") as f:
        article_content = f.read()
        if args.no_cards:
            chatbot.generate_response(
                pre_prompt + article_content, args.enable_thinking
            )
        else:
            chatbot.generate_mochi_cards(
                url,
                pre_prompt + article_content,
                TECHNICAL_READINGS_DECKS,
                args.enable_thinking,
            )

    os.remove(scraped_content_filepath)


if __name__ == "__main__":
    main()
