# AI Character Roleplay Simulator

A custom-built desktop app for roleplaying with AI-powered characters using local LLMs and persistent memory.

## 🎯 Features

- 🧠 **Rolling Memory**: Configurable memory of past messages for better contextual awareness.
- 📚 **RAG-Style Memory Retrieval**: Injects relevant knowledge chunks from character memory.
- 🎨 **Custom Character Configs**: Load character-specific instructions, scenarios, and dialogue color.
- ⚙️ **Advanced Settings Panel**: Fine-tune temperature, penalties, memory limits, font size, UI theme, and more.
- 🧾 **Session Save/Load**: Save full roleplay logs, including character and prompt setup.
- 🖥️ **Modern UI**: Built with `customtkinter` for a polished look and feel.

## 🛠️ Tech Stack

- Python 3.10+
- `customtkinter` for UI
- `sentence-transformers` + FAISS for semantic memory
- Local LLM endpoint (e.g. LM Studio or OpenRouter-compatible)

## 📂 Directory Structure

```
LLM character project/
├── Character/
│   └── [character folders + configs]
├── config/
│   └── advanced_settings.json
├── Sessions/
│   └── [saved chats]
├── start_ui.py
├── assets/
│   └── [optional images or UI assets]
└── models/
    └── [sentence-transformer files]
```

## 🚀 Getting Started

1. Install required Python libraries:
   ```
   pip install customtkinter sentence-transformers faiss-cpu
   ```

2. Run the app:
   ```
   python start_ui.py
   ```

3. Connect to your local LLM endpoint at the configured URL (default: `http://localhost:1234/v1/chat/completions`).

## 💾 Notes

- All configuration is saved in `config/advanced_settings.json`.
- Characters are loaded from the `Character/` directory.
- Make sure your LLM supports chat-style prompts.

---
