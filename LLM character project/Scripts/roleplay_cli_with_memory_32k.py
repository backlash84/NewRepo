import os
import json
import requests
import time
from pathlib import Path

# === Configuration ===
CHARACTER_NAME = "Hermione Granger"
MODEL_ENDPOINT = "http://localhost:1234/v1/chat/completions"
MEMORY_FOLDER = "../Personal_Memories"
SESSION_FOLDER = "../Sessions"
CHARACTER_CONFIG_FILE = "../Character_Config/hermione_config.json"
MAX_HISTORY_TURNS = 20  # Number of recent exchanges to keep
MAX_MEMORY_CHUNKS = 50  # Number of memory chunks to inject
TIMEOUT_SECONDS = 300   # Allow up to 5 minutes for model response

# === Helper Functions ===

def load_character_config():
    with open(CHARACTER_CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def load_memory_chunks():
    files = sorted(Path(MEMORY_FOLDER).glob("*.json"), key=lambda f: int(f.stem.split("_")[-1]))
    memory_chunks = []
    for file in files[:MAX_MEMORY_CHUNKS]:
        with open(file, "r", encoding="utf-8") as f:
            chunk = json.load(f)
            memory_chunks.append(chunk["summary"])
    return memory_chunks

def build_prompt(system_message, memory, scenario, history):
    memory_text = "\n".join(f"- {m}" for m in memory)
    history_text = "\n".join(history[-MAX_HISTORY_TURNS:])
    return {
        "model": "default",
        "messages": [
            {"role": "system", "content": system_message},
            {"role": "user", "content": f"Character Memory:\n{memory_text}\n\nScenario:\n{scenario}\n\nConversation:\n{history_text}"}
        ],
        "temperature": 0.8,
        "top_p": 0.9
    }

def save_session(history, session_name="default_session.json"):
    os.makedirs(SESSION_FOLDER, exist_ok=True)
    with open(os.path.join(SESSION_FOLDER, session_name), "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2)

def load_session(session_name="default_session.json"):
    try:
        with open(os.path.join(SESSION_FOLDER, session_name), "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return []

# === Main Interaction Loop ===

def main():
    print(f"Enter a brief scenario (e.g., 'You and Hermione are researching in the Hogwarts library.')")
    scenario = input("Scenario: ").strip()
    print("\nSession started. Type your message. Type 'exit' to quit.\n")

    system_prompt = f"You are {CHARACTER_NAME}, as portrayed in the Harry Potter books. Stay in character. Maintain consistency with memories and prior exchanges. Speak in first person."
    character_config = load_character_config()
    memory = load_memory_chunks()
    history = load_session()

    while True:
        user_input = input("You: ")
        if user_input.lower() == "exit":
            break

        history.append(f"You: {user_input}")
        prompt = build_prompt(system_prompt, memory, scenario, history)

        try:
            response = requests.post(MODEL_ENDPOINT, json=prompt, timeout=TIMEOUT_SECONDS)
            response.raise_for_status()
            reply = response.json()["choices"][0]["message"]["content"]
            print(f"{CHARACTER_NAME}: {reply}")
            history.append(f"{CHARACTER_NAME}: {reply}")
        except requests.exceptions.RequestException as e:
            print(f"[Error from LLM: {e}]")
            history.append(f"{CHARACTER_NAME}: [Error generating response.]")

        save_session(history)

if __name__ == "__main__":
    main()
