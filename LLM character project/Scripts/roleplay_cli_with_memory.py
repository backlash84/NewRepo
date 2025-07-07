
import os
import json
import requests
from datetime import datetime

# === CONFIGURATION ===
CHARACTER_NAME = "hermione"
BASE_DIR = os.path.join("sessions", CHARACTER_NAME)
MEMORY_DIR = os.path.join("memory", CHARACTER_NAME)
API_URL = "http://localhost:1234/v1/chat/completions"
MODEL_NAME = "local-model"

# === SYSTEM PROMPT ===
SYSTEM_PROMPT = """You are Hermione Granger from the Harry Potter series, depicted as she is by the end of the 7th book. You are logical, detail-oriented, emotionally sincere, and brave. Your speech is fast, formal, and occasionally pedantic, but softens when speaking to someone you trust.

Your role is to engage in a realistic conversation with the player, staying true to your personality and knowledge as established in the books. You do not know you are fictional. You reference events only up to the final book, and your memory includes personal experiences, people, spells, and Hogwarts history.

Assume the scenario describes your current setting and relationship to the player. Always remain in-character, and respond as if the conversation is truly happening to you."""


# === SESSION SETUP ===
os.makedirs(BASE_DIR, exist_ok=True)
print("Enter a brief scenario (e.g., 'You and Hermione are researching in the Hogwarts library.')")
scenario_text = input("Scenario: ").strip()
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
session_file = os.path.join(BASE_DIR, f"session_{timestamp}.json")

session_data = {
    "character": CHARACTER_NAME,
    "scenario": scenario_text,
    "history": []
}
with open(session_file, "w", encoding="utf-8") as f:
    json.dump(session_data, f, indent=2)

# === MEMORY CHUNK LOADER ===
def load_relevant_memories(user_input, max_chunks=3):
    memories = []
    for filename in os.listdir(MEMORY_DIR):
        if not filename.endswith(".json"):
            continue
        with open(os.path.join(MEMORY_DIR, filename), "r", encoding="utf-8") as f:
            chunk = json.load(f)
            tags = chunk.get("tags", [])
            summary = chunk.get("summary", "")
            if any(tag in user_input.lower() for tag in tags) or any(word in summary.lower() for word in user_input.lower().split()):
                memories.append(summary)
                if len(memories) >= max_chunks:
                    break
    return memories

# === MAIN LOOP ===
print("\nSession started. Type your message. Type 'exit' to quit.\n")

while True:
    user_input = input("You: ")
    if user_input.lower() == "exit":
        print("Session ended. Conversation saved.")
        break

    session_data["history"].append({"role": "user", "message": user_input})

    # Rebuild prompt with memory injection
    memory_summaries = load_relevant_memories(user_input)
    memory_text = "\n".join(f"- {m}" for m in memory_summaries)

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.append({"role": "system", "content": f"Scenario: {scenario_text}"})
    if memory_text:
        messages.append({"role": "system", "content": f"Relevant memories:\n{memory_text}"})

    for entry in session_data["history"]:
        messages.append({"role": entry["role"], "content": entry["message"]})

    try:
        response = requests.post(API_URL, json={
            "model": MODEL_NAME,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 512
        })
        response.raise_for_status()
        reply = response.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        reply = f"[Error from LLM: {str(e)}]"

    print(f"Hermione: {reply}")
    session_data["history"].append({"role": "hermione", "message": reply})

    with open(session_file, "w", encoding="utf-8") as f:
        json.dump(session_data, f, indent=2)
