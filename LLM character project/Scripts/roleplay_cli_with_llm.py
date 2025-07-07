
import os
import json
import requests
from datetime import datetime

# === CONFIGURATION ===
CHARACTER_NAME = "hermione"
BASE_DIR = os.path.join("sessions", CHARACTER_NAME)
API_URL = "http://localhost:1234/v1/chat/completions"  # LM Studio default endpoint
MODEL_NAME = "local-model"  # name can be anything, LM Studio doesn't use it

os.makedirs(BASE_DIR, exist_ok=True)

# === SCENARIO INPUT ===
print("Welcome to the AI Character Roleplay Simulator!")
print("Enter a brief scenario to start the story (e.g., 'You and Hermione are traveling through the Alps on a mission for the Order.')")

scenario_text = input("Scenario: ").strip()
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
session_file = os.path.join(BASE_DIR, f"session_{timestamp}.json")

# === INITIALIZE SESSION ===
session_data = {
    "character": CHARACTER_NAME,
    "scenario": scenario_text,
    "history": []
}
with open(session_file, "w", encoding="utf-8") as f:
    json.dump(session_data, f, indent=2)

print("\nSession started! Type your messages below. Type 'exit' to end.\n")

# === MAIN LOOP ===
while True:
    user_input = input("You: ")
    if user_input.lower() == "exit":
        print("Session ended. Your conversation was saved.")
        break

    session_data["history"].append({"role": "user", "message": user_input})

    # Build the prompt history for the model
    messages = [{"role": "system", "content": f"You are Hermione Granger. Scenario: {scenario_text}"}]
    for entry in session_data["history"]:
        messages.append({"role": entry["role"], "content": entry["message"]})

    # Send request to LM Studio API
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

    # Save updated session
    with open(session_file, "w", encoding="utf-8") as f:
        json.dump(session_data, f, indent=2)
