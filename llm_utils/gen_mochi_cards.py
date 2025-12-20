import os
from base64 import b64encode

import requests

import torch
from mlx_lm import generate, load, stream_generate
from transformers import AutoModelForCausalLM, AutoTokenizer, TextStreamer

CARD_DELIMITER = "---"
MAX_TOKENS = 2048
HF_TOKEN = os.environ.get("HF_TOKEN")
CREATE_CARDS_URL = "https://app.mochi.cards/api/cards/"
MOCHI_API_KEY = os.environ.get("MOCHI_API_KEY")
ENCODED_CREDENTIALS = b64encode(bytes(f"{MOCHI_API_KEY}:", "utf-8")).decode("utf-8")
REQUEST_HEADERS = {
    "Authorization": f"Basic {ENCODED_CREDENTIALS}",
    "Content-Type": "application/json",
}

class QwenChatbot:
    def __init__(self, model_name: str):
        if torch.backends.mps.is_available():
            self.model, self.tokenizer = load(model_name)
        else:
            raise Exception(
                "MPS backend not found; other backends not supported right now"
            )

    def _generate_response(self, context: str):
        messages = [{"role": "user", "content": context}]
        prompt = self.tokenizer.apply_chat_template(
            messages,
            add_generation_prompt=True,
            enable_thinking=False,
        )
        response = stream_generate(
            self.model,
            self.tokenizer,
            prompt=prompt,
            max_tokens=MAX_TOKENS,
        )
        total_response = ""
        print(f"Spaced repetition cards:")
        for chunk in response:
            total_response += chunk.text
            print(chunk.text, end="", flush=True)
        print()
        return total_response

    def generate_mochi_cards(self, url: str, context: str, deck_id: str) -> None:
        response = self._generate_response(context)
        cards = response.split(CARD_DELIMITER)
        for card_num, card in enumerate(cards):
            lines = card.split("\n")
            for line in lines:
                if line.startswith("Front: "):
                    question = line.split("Front: ")[1]
                elif line.startswith("Back: "):
                    answer = line.split("Back: ")[1]
            create_card_payload = {
                "content": f"{question}\n---\n{answer}\n---\n{url}\n",
                "deck-id": deck_id,
                "review-reverse?": False,
                "archived?": False,
            }
            post_response = requests.post(
                CREATE_CARDS_URL, headers=REQUEST_HEADERS, json=create_card_payload
            )
            print(
                f"Created card {card_num} with response: {post_response}"
            )
