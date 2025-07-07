import json
import os
import requests
import tiktoken
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

# Configuration
LLM_ENDPOINT = "http://localhost:1234/v1/chat/completions"
MODEL_NAME = "local-llm"
MAX_TOKENS = 16000
RESPONSE_TOKENS = 400
INPUT_BUDGET = MAX_TOKENS - RESPONSE_TOKENS

# Load RAG memory index and mapping
rag_model = SentenceTransformer("all-MiniLM-L6-v2")
character_folder = "../Character/Hermione" #Replace with variable later. 
index = faiss.read_index(os.path.join(character_folder, "memory_index.faiss"))
with open(os.path.join(character_folder, "memory_mapping.json"), "r", encoding="utf-8") as f:
    memory_mapping = json.load(f)

def get_relevant_memories(user_input, top_k=10):
    embedding = rag_model.encode([user_input])
    embedding = np.array(embedding).astype("float32")
    distances, indices = index.search(embedding, top_k)
    return [memory_mapping[i] for i in indices[0] if i < len(memory_mapping)]

# Load character config
with open(os.path.join(character_folder, "character_config.json"), "r", encoding="utf-8") as f:
    character_config = json.load(f)

# Token encoder
encoder = tiktoken.get_encoding("cl100k_base")

def count_tokens(text):
    return len(encoder.encode(text))

def build_prompt(scenario, history):
    prompt_sections = []
    prefix_instruction = "\n".join([
        "You are Hermione Granger from the Harry Potter universe.",
        "You are an eighteen year old witch attending Hogwarts School of Witchcraft and Wizardry, known for your intelligence, rule-following nature, and fierce loyalty to your friends.",
        "You are intelligent, curious, and highly logical. You quote books and professors often and expect others to keep up with your pace.",
        "You are passionate about learning and tend to over-prepare. Though you care deeply about others, you rarely show vulnerability and may hide it behind a brisk or overly formal tone.",
        "You dislike being underestimated, especially for being female or not a pure-blooded witch.",
        "You write in third person limited perspective, focused only on Hermione Granger.",
        "Write as if continuing a novel. The user controls the character Greg. You describe only Hermione's thoughts, dialogue, and actions in response.",
        "Never control the user's character. Do not write Greg's thoughts, feelings, or dialogue.",
        "Always stay in-character. Hermione's words, thoughts, and actions should match her canon personality and emotional development.",
        "Always continue directly from the user's message as if it were the previous paragraph in a novel.",
        "Write in present tense. Show only what Hermione perceives and chooses to express in the moment.",
        "Do not summarize, reflect, or explain unless Hermione is consciously thinking about it.",
        "Describe Hermione's physical reactions, tone, internal thoughts, and spoken words in vivid detail.",
        "Do not repeat past events unless Hermione would actively recall them. Refer to memories only when they naturally come to mind.",
        "Let emotional openness develop slowly. At first, Hermione may be reserved or guarded. Warmth should grow over time in response to intelligence, respect, or kindness.",
        "Always speak in the third person. Your tone is thoughtful, often formal, with occasional exasperation when others cannot keep up.",
        "Never use slang unless it is canon-consistent for Hermione."
    ])
    prompt_sections.append(prefix_instruction)

    # Character identity
    if "personality" in character_config:
        prompt_sections.append(f"Character Personality: {character_config['personality']}")
    if "speech_style" in character_config:
        prompt_sections.append(f"Speech Style: {character_config['speech_style']}")

    # Scenario
    prompt_sections.append(f"Scenario: {scenario}")

    # Use the last user message for semantic memory search
    recent_user_input = history[-1]['user'] if history else scenario
    relevant_memories = get_relevant_memories(recent_user_input)

    # Insert relevant memory summaries
    used_tokens = sum(count_tokens(p) for p in prompt_sections)
    for mem in relevant_memories:
        mem_text = f"[Memory] {mem['summary']}"
        mem_tokens = count_tokens(mem_text)
        if used_tokens + mem_tokens > INPUT_BUDGET:
            break
        prompt_sections.append(mem_text)
        used_tokens += mem_tokens

    # Add conversation history
    history_text = ""
    for exchange in reversed(history):
        line = f"You: {exchange['user']}\nCharacter: {exchange['bot']}"
        if used_tokens + count_tokens(line) > INPUT_BUDGET:
            break
        history_text = line + history_text
        used_tokens += count_tokens(line)

    prompt_sections.append(history_text)
    return "\n\n".join(prompt_sections)

def main():
    print("Enter a brief scenario (e.g., 'You and Hermione are researching in the Hogwarts library.')")
    scenario = input("Scenario: ")

    history = []
    print("\nSession started. Type your message. Type 'exit' to quit.\n")
    while True:
        user_input = input("You: ")
        if user_input.lower() == "exit":
            break

        history.append({"user": user_input, "bot": ""})  # pre-fill to access in build_prompt
        prompt = build_prompt(scenario, history)
        headers = {"Content-Type": "application/json"}
        payload = {
            "model": MODEL_NAME,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "max_tokens": RESPONSE_TOKENS,
            "stop": None
        }

        try:
            response = requests.post(LLM_ENDPOINT, headers=headers, json=payload)
            response.raise_for_status()
            result = response.json()
            bot_reply = result["choices"][0]["message"]["content"]
        except Exception as e:
            bot_reply = f"[Error from LLM: {str(e)}]"

        print(f"Character: {bot_reply}\n")
        history[-1]["bot"] = bot_reply

if __name__ == "__main__":
    main()