
import os
import json
import requests
from datetime import datetime

CHARACTER_NAME = "hermione"
BASE_DIR = os.path.join("sessions", CHARACTER_NAME)
MEMORY_DIR = os.path.join("memory", CHARACTER_NAME)
API_URL = "http://localhost:1234/v1/chat/completions"
MODEL_NAME = "local-model"

SYSTEM_PROMPT = """You are Hermione Granger from the Harry Potter series, depicted as she is by the end of the 7th book. You are logical, detail-oriented, emotionally sincere, and brave. Your speech is fast, formal, and occasionally pedantic, but softens when speaking to someone you trust.

Your role is to engage in a realistic conversation with the player, staying true to your personality and knowledge as established in the books. You do not know you are fictional. You reference events only up to the final book, and your memory includes personal experiences, people, spells, and Hogwarts history.

Assume the scenario describes your current setting and relationship to the player. Always remain in-character, and respond as if the conversation is truly happening to you."""

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

def load_relevant_memory(user_input, max_length=300):
    best_match = None
    for filename in os.listdir(MEMORY_DIR):
        if not filename.endswith(".json"):
            continue
        with open(os.path.join(MEMORY_DIR, filename), "r", encoding="utf-8") as f:
            chunk = json.load(f)
            summary = chunk.get("summary", "")
            if any(word in summary.lower() for word in user_input.lower().split()):
                best_match = summary[:max_length]
                break
    return best_match

def build_messages(user_input, memory_summary):
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.append({"role": "system", "content": f"Scenario: {scenario_text}"})
    if memory_summary:
        messages.append({"role": "system", "content": f"Relevant memory:\n{memory_summary}"})

    last_turns = session_data["history"][-6:]  # 3 rounds (user, AI)
    for entry in last_turns:
        messages.append({"role": entry["role"], "content": entry["message"]})
    messages.append({"role": "user", "content": user_input})
    return messages

print("\nSession started. Type your message. Type 'exit' to quit.\n")

while True:
    user_input = input("You: ")
    if user_input.lower() == "exit":
        print("Session ended. Conversation saved.")
        break

    memory_summary = load_relevant_memory(user_input)

    messages = build_messages(user_input, memory_summary)

    try:
        response = requests.post(API_URL, json={
            "model": MODEL_NAME,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 512
        })
        response.raise_for_status()
        reply = response.json()["choices"][0]["message"]["content"].strip()
    except requests.exceptions.HTTPError as e:
        if response.status_code == 400:
            print("[Warning] Prompt too long. Retrying with no memory injection...")
            messages = build_messages(user_input, memory_summary=None)
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
                reply = f"[Final Error] Could not generate a response: {str(e)}"
        else:
            reply = f"[HTTP Error] {str(e)}"
    except Exception as e:
        reply = f"[General Error] {str(e)}"

    print(f"Hermione: {reply}")
    session_data["history"].append({"role": "user", "message": user_input})
    session_data["history"].append({"role": "hermione", "message": reply})

    with open(session_file, "w", encoding="utf-8") as f:
        json.dump(session_data, f, indent=2)
