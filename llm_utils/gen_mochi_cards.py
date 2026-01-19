import os
from base64 import b64encode

import requests

import torch
from mlx_lm import load, stream_generate


CARD_DELIMITER = "---"
MAX_TOKENS_IN_STREAM_GENERATE = 2048
HF_TOKEN = os.environ.get("HF_TOKEN")
CREATE_CARDS_URL = "https://app.mochi.cards/api/cards/"
MOCHI_API_KEY = os.environ.get("MOCHI_API_KEY")
ENCODED_CREDENTIALS = b64encode(bytes(f"{MOCHI_API_KEY}:", "utf-8")).decode("utf-8")
REQUEST_HEADERS = {
    "Authorization": f"Basic {ENCODED_CREDENTIALS}",
    "Content-Type": "application/json",
}


class QwenChatbot:
    def __init__(self, model_name: str, num_cards: int):
        self.num_cards = num_cards
        if torch.backends.mps.is_available():
            self.model_name = model_name
            self.model, self.tokenizer = load(model_name)
        else:
            raise Exception(
                "MPS backend not found; other backends not supported right now"
            )

    def _count_num_tokens(self, text: str) -> int:
        return len(self.tokenizer.encode(text))

    def _get_max_num_tokens_in_model(self) -> int:
        return self.tokenizer.model_max_length

    def _split_context_into_batches(self, context: str) -> list[str]:
        num_tokens_in_context = self._count_num_tokens(context)
        max_tokens_of_model = self._get_max_num_tokens_in_model()
        if num_tokens_in_context > max_tokens_of_model:
            # TODO: Split up the context into batches and create
            # (num_cards / n batches) cards for each batch instead
            # of throwing an exception
            raise Exception(
                (
                    f"Context is too long. Max tokens in model: {max_tokens_of_model}, "
                    f"num tokens in context: {num_tokens_in_context}\n"
                    "Splitting up the context into batches..."
                )
            )
            # return []

        return [context]

    def generate_spaced_rep_card_drafts(
        self,
        context: str,
        enable_thinking: bool = False,
    ) -> list[str]:
        """Generate spaced repetition cards for a given context."""
        context_batches = self._split_context_into_batches(context)
        all_spaced_rep_cards_output = []
        for context in context_batches:
            messages = [{"role": "user", "content": context}]
            prompt = self.tokenizer.apply_chat_template(
                messages,
                add_generation_prompt=True,
                enable_thinking=enable_thinking,
            )
            response = stream_generate(
                self.model,
                self.tokenizer,
                prompt=prompt,
                max_tokens=MAX_TOKENS_IN_STREAM_GENERATE,
            )
            spaced_rep_cards_output = ""
            print("Spaced repetition cards:")
            for chunk in response:
                spaced_rep_cards_output += chunk.text
                print(chunk.text, end="", flush=True)
            print()
            all_spaced_rep_cards_output.append(spaced_rep_cards_output)

        return all_spaced_rep_cards_output

    def generate_mochi_cards(
        self,
        url: str,
        context: str,
        deck_id: str,
        enable_thinking: bool = False,
    ) -> None:
        spaced_rep_card_drafts = self.generate_spaced_rep_card_drafts(
            context, enable_thinking=enable_thinking
        )
        for spaced_rep_card_output in spaced_rep_card_drafts:
            cards = spaced_rep_card_output.split(CARD_DELIMITER)
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
                print(f"Create card payload: {create_card_payload}")
                post_response = requests.post(
                    CREATE_CARDS_URL,
                    headers=REQUEST_HEADERS,
                    json=create_card_payload,
                )
                print(
                    f"Created card {card_num} with response: {post_response}"
                )
