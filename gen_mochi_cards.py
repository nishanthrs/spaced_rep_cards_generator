import os
from base64 import b64encode

import requests

# Mochi API Docs: https://mochi.cards/docs/api/#api-reference

MOCHI_API_KEY = os.environ.get("MOCHI_API_KEY")

encoded_credentials = b64encode(bytes(f"{MOCHI_API_KEY}:", "utf-8")).decode("utf-8")
request_headers = {
    "Authorization": f"Basic {encoded_credentials}",
    "Content-Type": "application/json",
}

deck_url = "https://app.mochi.cards/api/decks/"
decks = requests.get(deck_url, headers=request_headers).json()["docs"]

cards_in_deck_url = "https://app.mochi.cards/api/cards/"
business_cards = requests.get(
    cards_in_deck_url, params={"deck-id": "fRaP9Q3j"}, headers=request_headers
).json()["docs"][0]
print(business_cards)

create_card_url = "https://app.mochi.cards/api/cards/"
question = "What is Mochi?"
answer = "Spaced repetition software"
test_card_payload = {
    "content": f"{question}\n---\n{answer}",
    "deck-id": "fRaP9Q3j",  # Business and Product Deck
    "template-id": "8BtaEAXe",
    "fields": {
        "name": {"id": "name", "value": "Hello,"},
        "JNEnw1e7": {"id": "JNEnw1e7", "value": "World!"},
    },
    "review-reverse?": False,
    "archived?": False,
    "pos": "6V",
    "manual-tags": ["philosophy", "philosophy/aristotle"],
}
requests.post(create_card_url, headers=request_headers, json=test_card_payload)
print("Successfully created a card")
