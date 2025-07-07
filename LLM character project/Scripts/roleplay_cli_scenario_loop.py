
import os
import json
from datetime import datetime

# === Configurable paths ===
CHARACTER_NAME = "hermione"
BASE_DIR = os.path.join("sessions", CHARACTER_NAME)
SCENARIO_DIR = os.path.join("scenarios", CHARACTER_NAME)
os.makedirs(BASE_DIR, exist_ok=True)

# === Prompt user to enter or select a scenario ===
print("Welcome to the AI Character Roleplay Simulator!")
print("Enter a brief scenario to start the story (e.g., 'You and Hermione are traveling through the Alps on a mission for the Order.')")

scenario_text = input("Scenario: ").strip()
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
session_file = os.path.join(BASE_DIR, f"session_{timestamp}.json")

# === Create a new session file ===
session_data = {
    "character": CHARACTER_NAME,
    "scenario": scenario_text,
    "history": []
}
with open(session_file, "w", encoding="utf-8") as f:
    json.dump(session_data, f, indent=2)

print("\nSession started! Type your messages below. Type 'exit' to end.\n")

# === Main conversation loop ===
while True:
    user_input = input("You: ")
    if user_input.lower() == "exit":
        print("Session ended. Your conversation was saved.")
        break

    # Append to session history
    session_data["history"].append({
        "role": "user",
        "message": user_input
    })

    # Simulate a placeholder AI response (to be replaced later)
    ai_response = f"Hermione (placeholder): That's very interesting. Tell me more."

    print(ai_response)
    session_data["history"].append({
        "role": "hermione",
        "message": ai_response
    })

    # Save session after each exchange
    with open(session_file, "w", encoding="utf-8") as f:
        json.dump(session_data, f, indent=2)
