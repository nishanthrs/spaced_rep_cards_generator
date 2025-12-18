from transformers import AutoModelForCausalLM, AutoTokenizer, TextStreamer

PRE_PROMPT = """
    I want you to create a set of 10 spaced repetition cards based on some article or text so that I can use these cards to retain
    and remember important things from the article for longer.
    These cards have two sides: a front and a back. The front is a retrieval practice prompt and the back is the answer to that prompt.
    Here are a few guidelines to writing good retrieval practice prompt:
    1. Retrieval practice prompts should be focused. A question or answer involving too much detail will dull your concentration and stimulate incomplete retrievals, leaving some bulbs unlit. Unfocused questions also make it harder to check whether you remembered all parts of the answer and to note places where you differed. It’s usually best to focus on one detail at a time.
    2. Retrieval practice prompts should be precise about what they’re asking for. Vague questions will elicit vague answers, which won’t reliably light the bulbs you’re targeting.
    3. Retrieval practice prompts should produce consistent answers, lighting the same bulbs each time you perform the task. Otherwise, you may run afoul of an interference phenomenon called “retrieval-induced forgetting”This effect has been produced in many experiments but is not yet well understood. For an overview, see Murayama et al, Forgetting as a consequence of retrieval: a meta-analytic review of retrieval-induced forgetting (2014).: what you remember during practice is reinforced, but other related knowledge which you didn’t recall is actually inhibited. Now, there is a useful type of prompt which involves generating new answers with each repetition, but such prompts leverage a different theory of change. We’ll discuss them briefly later in this guide.
    4. SuperMemo’s algorithms (also used by most other major systems) are tuned for 90% accuracy. Each review would likely have a larger impact on your memory if you targeted much lower accuracy numbers—see e.g. Carpenter et al, Using Spacing to Enhance Diverse Forms of Learning (2012). Higher accuracy targets trade efficiency for reliability.Retrieval practice prompts should be tractable. To avoid interference-driven churn and recurring annoyance in your review sessions, you should strive to write prompts which you can almost always answer correctly. This often means breaking the task down, or adding cues.
    5. Retrieval practice prompts should be effortful. It’s important that the prompt actually involves retrieving the answer from memory. You shouldn’t be able to trivially infer the answer. Cues are helpful, as we’ll discuss later—just don’t “give the answer away.” In fact, effort appears to be an important factor in the effects of retrieval practice.For more on the notion that difficult retrievals have a greater impact than easier retrievals, see the discussion in Bjork and Bjork, A New Theory of Disuse and an Old Theory of Stimulus Fluctuation (1992). Pyc and Rawson, Testing the retrieval effort hypothesis: Does greater difficulty correctly recalling information lead to higher levels of memory? (2009) offers some focused experimental tests of this theory, which they coin the “retrieval effort hypothesis.”
    That’s one motivation for spacing reviews out over time: if it’s too easy to recall the answer, retrieval practice has little effect.

    You should only use the article text to come up with good retrieval practice prompts and answers to those prompts. I will then use these to study and remember and apply this valuable information from the articles.
    Here is the article in markdown format:
"""

class QwenChatbot:
    def __init__(self, model_name="Qwen/Qwen3-30B-A3B"):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForCausalLM.from_pretrained(model_name)
        self.history = []

    def generate_response(self, user_input):
        messages = self.history + [{"role": "user", "content": user_input}]

        text = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
            enable_thinking=False,
        )

        inputs = self.tokenizer(text, return_tensors="pt")
        streamer = TextStreamer(self.tokenizer, skip_prompt=True)
        response_ids = self.model.generate(**inputs, streamer=streamer, max_new_tokens=32768)[0][len(inputs.input_ids[0]):].tolist()
        response = self.tokenizer.decode(response_ids, skip_special_tokens=True)

        # Update history
        self.history.append({"role": "user", "content": user_input})
        self.history.append({"role": "assistant", "content": response})

        return response

    def generate_mochi_cards(self, article_text: str) -> None:
        pass

# Example Usage
if __name__ == "__main__":
    chatbot = QwenChatbot("Qwen/Qwen3-8B")
    # user_input_1 = "what are the best web scraping libraries out there?"
    # print(f"User: {user_input_1}")
    user_input = PRE_PROMPT
    with open("scraped_semianalysis_articles/text/The_Memory_Wall_Past,_Present,_and_Future_of_DRAM.md") as f:
        semianalysis_content = f.read()
        user_input += semianalysis_content
    print(f"User: {user_input}")
    response_1 = chatbot.generate_response(user_input)
    print(f"Bot: {response_1}")
