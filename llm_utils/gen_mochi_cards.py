import os
from base64 import b64encode

import requests

import torch
from mlx_lm import load, stream_generate

BUFFER_NUM_TOKENS = 1024
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
        """Split the context into batches of size max_tokens_of_model
        NOTE: We might be able to achieve better performance by splitting
        the context by chapters/sections rather than fixed lengths, but this
        is a good start"""
        num_tokens_in_context = self._count_num_tokens(context)
        print(f"Number of tokens in context: {num_tokens_in_context}")
        max_tokens_of_model = self._get_max_num_tokens_in_model()
        print(f"Max number of tokens in model: {max_tokens_of_model}")
        if num_tokens_in_context <= max_tokens_of_model:
            return [context]

        batches = []

        tokens = self.tokenizer.encode(context)
        # Divide max context size by 4 since LLM response quality and
        # performance degrades rapidly with larger context sizes
        num_tokens_in_batch = int(max_tokens_of_model / 4)
        for i in range(0, len(tokens), num_tokens_in_batch):
            chunk_tokens = tokens[i:i+num_tokens_in_batch]
            chunk_text = self.tokenizer.decode(chunk_tokens)
            batches.append(chunk_text.strip())

        return batches

    def generate_spaced_rep_card_drafts(
        self,
        instructions: str,
        context: str,
        enable_thinking: bool = False,
    ) -> list[str]:
        """Generate spaced repetition cards for a given context."""
        context_batches = self._split_context_into_batches(context)
        all_spaced_rep_cards_output = []
        # TODO: Look into parallelizing this with concurrent reqs to vLLM/SGLang servers in the future
        for i, context_batch in enumerate(context_batches):
            messages = [{"role": "user", "content": instructions + context_batch}]
            prompt = self.tokenizer.apply_chat_template(
                messages,
                add_generation_prompt=True,
                enable_thinking=enable_thinking,
            )
            print(f"Spaced repetition cards for batch {i}:")
            response = stream_generate(
                self.model,
                self.tokenizer,
                prompt=prompt,
                max_tokens=MAX_TOKENS_IN_STREAM_GENERATE,
            )
            spaced_rep_cards_output = ""
            for chunk in response:
                spaced_rep_cards_output += chunk.text
                print(chunk.text, end="", flush=True)
            print()
            all_spaced_rep_cards_output.append(spaced_rep_cards_output)

        return all_spaced_rep_cards_output

    def generate_mochi_cards(
        self,
        url: str,
        instructions: str,
        context: str,
        deck_id: str,
        enable_thinking: bool = False,
    ) -> None:
        spaced_rep_card_drafts = self.generate_spaced_rep_card_drafts(
            instructions, context, enable_thinking=enable_thinking
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
                print(f"Question: {question}")
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
