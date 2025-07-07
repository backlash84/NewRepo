# -*- coding: utf-8 -*-

import customtkinter as ctk
import os
import json
from tkinter import filedialog
import faiss
import numpy as np
import requests
import threading
import re
from sentence_transformers import SentenceTransformer
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS
from nltk.stem import WordNetLemmatizer
from tkinter import messagebox



ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# Contains def __init__, def show_frame
class RoleplayApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("AI Character Roleplay Simulator")
        self.geometry("900x800")

        # Default theme values to avoid missing attributes
        self.entry_bg_color = "#222222"
        self.accent_color = "#00ccff"
        self.text_color = "#ffffff"

        self.container = ctk.CTkFrame(self)
        self.container.pack(fill="both", expand=True)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        self.frames = {}
        for View in (StartMenu, ChatView, CharacterSettings, AdvancedSettings):
            frame = View(parent=self.container, controller=self)
            self.frames[View.__name__] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame("StartMenu")
        self.load_and_apply_settings()
        self.frames["ChatView"].apply_theme_colors()
        self.frames["CharacterSettings"].apply_theme_colors()
       
        # Load UI theme colors from saved settings and apply them
        try:
            os.makedirs("config", exist_ok=True)  # Ensure config directory exists
            try:
                with open("config/advanced_settings.json", "r", encoding="utf-8") as f:
                    settings = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError) as e:
                print(f"[Warning] Failed to load JSON from config/advanced_settings.json: {e}")
                settings = {}

            self.accent_color = settings.get("accent_color", "#00ccff")

            self.apply_ui_theme(
                bg_color=settings.get("theme_color", "#333333"),
                accent_color=self.accent_color,
                text_color=settings.get("text_color", "#ffffff"),
                entry_bg_color=settings.get("entry_color", "#222222")
            )
        except Exception as e:
            print(f"[Warning] Failed to load UI theme colors at startup: {e}")

        # Apply UI color from saved settings
        theme_color = self.frames["AdvancedSettings"].get_theme_color()
        self.apply_theme_color(theme_color)

    def apply_ui_theme(self, bg_color, accent_color, text_color, entry_bg_color="#222222"):
        def apply_recursive(widget):
            try:
                if isinstance(widget, ctk.CTkButton):
                    widget.configure(fg_color=accent_color, hover_color=accent_color, text_color=text_color)
                elif isinstance(widget, ctk.CTkSlider):
                    widget.configure(progress_color=accent_color, button_color=accent_color)
                elif isinstance(widget, ctk.CTkCheckBox):
                    widget.configure(border_color=accent_color, checkmark_color=accent_color, text_color=text_color)
                elif isinstance(widget, ctk.CTkLabel):
                    widget.configure(text_color=text_color)
                elif isinstance(widget, ctk.CTkEntry):
                    widget.configure(fg_color=entry_bg_color, text_color=text_color)
                elif isinstance(widget, ctk.CTkFrame):
                    widget.configure(fg_color=bg_color)
            except:
                pass

            for child in widget.winfo_children():
                apply_recursive(child)

        for frame in self.frames.values():
            apply_recursive(frame)

    def show_frame(self, name):
        self.frames[name].tkraise()

    def apply_theme_color(self, hex_color):
        for frame in self.frames.values():
            frame.configure(fg_color=hex_color)
            for child in frame.winfo_children():
                try:
                    child.configure(fg_color=hex_color)
                except:
                    pass  # some widgets may not support fg_color

    def load_and_apply_settings(self):
        try:
            os.makedirs("config", exist_ok=True)  # Ensure the config folder exists

            try:
                with open("config/advanced_settings.json", "r", encoding="utf-8") as f:
                    settings = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError) as e:
                print(f"[Warning] Failed to load JSON from config/advanced_settings.json: {e}")
                settings = {}

            self.entry_bg_color = settings.get("entry_color", "#222222")
            self.accent_color = settings.get("accent_color", "#00ccff")

            self.apply_ui_theme(
                bg_color=settings.get("theme_color", "#333333"),
                accent_color=self.accent_color,
                text_color=settings.get("text_color", "#ffffff"),
                entry_bg_color=self.entry_bg_color
            )

        except Exception as e:
            print(f"[Warning] Failed to load UI settings: {e}")
            self.entry_bg_color = "#222222"
            self.accent_color = "#00ccff"

class CenteredFrame(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)
        # configure 3x3 grid
        for i in range(3):
            self.grid_rowconfigure(i, weight=1)
            self.grid_columnconfigure(i, weight=1)

CHARACTER_DIR = "Character"
# Contains def __init__,  def on_character_change, 
# def start_fresh_chat, def load_session_from_start,
class StartMenu(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.controller.selected_character = None  # store active character name

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        outer = ctk.CTkFrame(self)
        outer.grid(row=0, column=0, sticky="nsew")

        outer.grid_rowconfigure(0, weight=1)
        outer.grid_columnconfigure(0, weight=1)

        inner = ctk.CTkFrame(outer)
        inner.grid(row=0, column=0)

        ctk.CTkLabel(inner, text="AI Roleplay Simulator", font=("Arial", 24)).pack(pady=20)
        ctk.CTkLabel(inner, text="Selected Character:", font=("Arial", 14)).pack(pady=(0, 5))

        self.character_names = [
            d for d in os.listdir(CHARACTER_DIR)
            if os.path.isdir(os.path.join(CHARACTER_DIR, d))
        ]
        self.character_var = ctk.StringVar()
        self.character_dropdown = ctk.CTkOptionMenu(
            inner,
            variable=self.character_var,
            values=self.character_names,
            fg_color=self.controller.accent_color,
            button_color=self.controller.accent_color,
            text_color=self.controller.text_color
        )
        self.character_dropdown.pack(pady=(0, 15))

        if self.character_names:
            self.character_var.set(self.character_names[0])
            self.controller.selected_character = self.character_names[0]

        # Update controller.selected_character whenever dropdown changes
        def on_character_change(value):
            self.controller.selected_character = value

        self.character_var.trace_add("write", lambda *args: on_character_change(self.character_var.get()))

        ctk.CTkButton(inner, text="Start Chat", width=200,
                      command=self.start_fresh_chat).pack(pady=10)

        ctk.CTkButton(inner, text="Load Previous Session", width=200,
                      command=self.load_session_from_start).pack(pady=10)

        ctk.CTkButton(inner, text="Character Settings", width=200,
                      command=lambda: controller.show_frame("CharacterSettings")).pack(pady=10)

        ctk.CTkButton(inner, text="Advanced Settings", width=200,
                      command=lambda: controller.show_frame("AdvancedSettings")).pack(pady=10)

    def apply_theme_colors(self):
        self.character_dropdown.configure(
            fg_color=self.controller.accent_color,
            button_color=self.controller.accent_color,
            text_color=self.controller.text_color,
            text_color_disabled=self.controller.text_color
        )

    def start_fresh_chat(self):
        chat_view = self.controller.frames["ChatView"]

        # Clear chat and entry box
        chat_view.chat_display.configure(state="normal")
        chat_view.chat_display.delete("1.0", "end")
        chat_view.chat_display.configure(state="disabled")
        chat_view.entry.delete("1.0", "end")

        # Mark as not initialized so it reloads
        chat_view.chat_initialized = False

        # Force reload from updated character_config.json
        chat_view.load_character_assets(force_reload=True)

        # Switch to chat view
        self.controller.show_frame("ChatView")

    def load_session_from_start(self):
        session_dir = "Sessions"
        os.makedirs(session_dir, exist_ok=True)

        file_path = filedialog.askopenfilename(
            initialdir=session_dir,
            filetypes=[("JSON Files", "*.json")],
            title="Load Previous Session"
        )
        if not file_path:
            return

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                session_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"[Warning] Failed to load JSON from {file_path}: {e}")
            session_data = {}

        # Set character in controller
        char_name = session_data.get("character")
        self.controller.selected_character = char_name

        # Forward session data to ChatView
        chat_view = self.controller.frames["ChatView"]
        # Overwrite the character_config.json file with session's prefix and scenario
        char_path = os.path.join("Character", char_name)
        config_path = os.path.join(char_path, "character_config.json")

        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError) as e:
                print(f"[Warning] Failed to load JSON from {config_path}: {e}")
                config = {}
        else:
            config = {}

        # Set scenario/prefix from session
        session_prefix = session_data.get("prefix", "")
        session_scenario = session_data.get("scenario", "")
        config["prefix_instructions"] = session_prefix
        config["scenario"] = session_scenario

        # Save updated config back to file
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)

        chat_content = session_data.get("chat", "")
        chat_view.insert_tagged_chat(chat_content)

        # Reload memory and config from character folder
        chat_view.load_character_assets(force_reload=True)

        # Show chat view
        self.controller.show_frame("ChatView")

# Contains def toggle_debug_mode, def __init__,
#def insert_tagged_chat,
class ChatView(ctk.CTkFrame):
    def toggle_debug_mode(self):
        self.debug_mode = self.debug_toggle_var.get()

    def __init__(self, parent, controller):
        self.editing_reply = False
        self.debug_toggle_var = ctk.BooleanVar(value=False)
        self.debug_mode = self.debug_toggle_var.get()  # Sync immediately

        super().__init__(parent)
        self.controller = controller

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        outer = ctk.CTkFrame(self)
        outer.grid(row=0, column=0, sticky="nsew")

        outer.grid_rowconfigure(0, weight=1)
        outer.grid_columnconfigure(0, weight=1)

        inner = ctk.CTkFrame(outer)
        inner.grid(row=0, column=0)

        # Top row for right-aligned retry button
        top_button_row = ctk.CTkFrame(inner)
        top_button_row.pack(fill="x", pady=(5, 0))

        ctk.CTkButton(top_button_row, text="Try Again", width=100, command=self.retry_last_response).pack(side="right", padx=10)
        self.edit_button = ctk.CTkButton(top_button_row, text="Edit Reply", width=100, command=self.toggle_edit_last_reply)
        self.edit_button.pack(side="right", padx=10)
        ctk.CTkButton(top_button_row, text="Back", width=100, command=self.confirm_back_to_main).pack(side="left", padx=10)

        ctk.CTkLabel(inner, text="Chat", font=("Arial", 20)).pack(pady=(10, 5))

        # Theme colors
        entry_bg_color = controller.entry_bg_color
        accent_color = controller.accent_color
        text_color = controller.text_color  # fallback

        print("[DEBUG] Entry BG Color:", entry_bg_color)  # TEMPORARY

        # Load user/debug colors from settings
        try:
            os.makedirs("config", exist_ok=True)
            try:
                with open("config/advanced_settings.json", "r", encoding="utf-8") as f:
                    settings = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError) as e:
                print(f"[Warning] Failed to load JSON from config/advanced_settings.json: {e}")
                settings = {}

            user_color = settings.get("user_color", "#00ccff")
            debug_color = settings.get("debug_color", "#ff0f0f")
            text_color = settings.get("text_color", text_color)
        except Exception as e:
            print(f"[Warning] Failed to apply text colors: {e}")
            user_color = "#00ccff"
            debug_color = "#ff0f0f"

        self.chat_display = ctk.CTkTextbox(inner, height=0, width=0, wrap="word",
                                           fg_color=entry_bg_color, text_color=text_color,
                                           border_color=accent_color, border_width=2)
        self.chat_display.pack(pady=10, fill="both", expand=True)
        self.chat_display.configure(state="disabled")

        self.entry = ctk.CTkTextbox(inner, width=0, height=0, wrap="word",
                                    fg_color=entry_bg_color, text_color=text_color,
                                    border_color=accent_color, border_width=2)
        self.entry.pack(pady=(0, 10), fill="x", expand=True)

        # Optional: keep bot color as default
        self.bot_color = "#ffeb0f"

        # Apply tag styles
        self.chat_display.tag_config("user", foreground=user_color)
        self.chat_display.tag_config("bot", foreground=self.bot_color)
        self.chat_display.tag_config("debug", foreground=debug_color)

        # Create a horizontal row of buttons
        button_row = ctk.CTkFrame(inner)
        button_row.pack(pady=(0, 10))

        ctk.CTkButton(button_row, text="Send", width=100, command=self.send_message).pack(side="left", padx=5)
        ctk.CTkButton(button_row, text="Save", width=100, command=self.save_session).pack(side="left", padx=5)
        ctk.CTkButton(button_row, text="Load", width=100, command=self.load_session).pack(side="left", padx=5)

        # Memory debug toggle
        self.debug_toggle_var = ctk.BooleanVar(value=False)
        self.debug_toggle = ctk.CTkCheckBox(
            inner,
            text="Show memory debug",
            variable=self.debug_toggle_var,
            command=self.toggle_debug_mode
        )
        self.debug_toggle.pack(pady=(5, 10))

        # Initialize conversation state
        self.chat_initialized = False
        self.prefix = ""
        self.scenario = ""
        self.memory_index = None
        self.memory_mapping = []

        # Load embedding and lemmatization tools
        self.embedder = SentenceTransformer("all-MiniLM-L6-v2")
        self.lemmatizer = WordNetLemmatizer()

        # Prep for last prompt tracking
        self.last_prompt = ""

    def print_memory_debug(self):
        payload = getattr(self, "last_payload_used", {})
        top_k = payload.get("top_k", "???")
        similarity_threshold = payload.get("similarity_threshold", "???")

        debug_lines = ["\n=== Retrieved Memory Debug ===\n"]
        debug_lines.append(f"Top K (Memory Chunks): {top_k}")
        debug_lines.append(f"Similarity Threshold: {similarity_threshold}")
        debug_lines.append("")
        debug_lines.append("--- LLM Settings Used ---")
        debug_lines.append(f"Model: {payload.get('model', '???')}")
        debug_lines.append(f"Temperature: {payload.get('temperature', '???')}")
        max_tokens = payload.get("max_tokens")
        debug_lines.append(f"Max Tokens: {max_tokens if max_tokens is not None else 'No Limit'}")
        debug_lines.append(f"Frequency Penalty: {payload.get('frequency_penalty', '???')}")
        debug_lines.append(f"Presence Penalty: {payload.get('presence_penalty', '???')}")
        debug_lines.append("")

        debug_text = "\n".join(debug_lines)
        print(debug_text)

        if self.debug_mode:
            self.chat_display.configure(state="normal")
            self.chat_display.insert("end", debug_text + "\n", "debug")
            self.chat_display.configure(state="disabled")

    def retry_last_response(self):
        if not self.last_prompt:
            return  # Nothing to retry

        self.chat_display.configure(state="normal")
        content = self.chat_display.get("1.0", "end")

        # Attempt to remove the last AI reply block
        lines = content.strip().split("\n")
        char_label = f"{self.controller.selected_character}:"

        for i in range(len(lines) - 1, -1, -1):
            if lines[i].startswith(char_label):
                lines = lines[:i]
                break

        updated_content = "\n".join(lines).strip() + "\n\n"
        self.chat_display.delete("1.0", "end")
        self.chat_display.insert("1.0", updated_content)
        self.chat_display.configure(state="disabled")

        # Regenerate the reply using the last prompt
        self.after(100, lambda: self.fetch_and_display_reply(self.last_prompt))

    def toggle_edit_last_reply(self):
        self.chat_display.configure(state="normal")
        content = self.chat_display.get("1.0", "end").strip().split("\n")

        char_label = f"{self.controller.selected_character}:"

        if not self.editing_reply:
            # Enter editing mode: find and highlight last AI line
            for i in range(len(content) - 1, -1, -1):
                if content[i].startswith(char_label):
                    self.last_ai_line_index = i
                    break
            else:
                self.chat_display.configure(state="disabled")
                from tkinter import messagebox
                messagebox.showinfo("No AI Reply Found", "There is no previous AI message to edit.")
                return

            # Put entire content back in editable state
            self.chat_display.configure(state="normal")
            self.editing_reply = True
            self.edit_button.configure(text="Save Edit")
            return

        else:
            # Save edits: update the internal chat with new AI reply
            full_text = self.chat_display.get("1.0", "end").strip().split("\n")
            updated_text = "\n".join(full_text)
            self.chat_display.delete("1.0", "end")
            self.chat_display.insert("1.0", updated_text + "\n\n")

            self.editing_reply = False
            self.chat_display.configure(state="disabled")
            self.edit_button.configure(text="Edit Reply")

    def apply_theme_colors(self):
        entry_bg_color = self.controller.entry_bg_color
        text_color = self.controller.text_color
        accent_color = self.controller.accent_color

        self.chat_display.configure(fg_color=entry_bg_color, text_color=text_color, border_color=accent_color)
        self.entry.configure(fg_color=entry_bg_color, text_color=text_color, border_color=accent_color)

    def save_session(self):
        session_dir = "Sessions"
        os.makedirs(session_dir, exist_ok=True)

        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            initialdir=session_dir,
            filetypes=[("JSON Files", "*.json")],
            title="Save Session"
        )
        if not file_path:
            return

        session_data = {
            "character": self.controller.selected_character,
            "chat": self.chat_display.get("1.0", "end").strip(),
            "scenario": self.scenario,
            "prefix": self.prefix
}

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(session_data, f, indent=2)

    def load_session(self):
        session_dir = "Sessions"
        os.makedirs(session_dir, exist_ok=True)

        file_path = filedialog.askopenfilename(
            initialdir=session_dir,
            filetypes=[("JSON Files", "*.json")],
            title="Load Session"
        )
        if not file_path:
            return

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                session_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"[Warning] Failed to load JSON from {file_path}: {e}")
            session_data = {}

        # Apply character selection from session
        char_name = session_data.get("character")
        self.controller.selected_character = char_name

        # Load character config (if needed for memory)
        char_path = os.path.join("Character", char_name)
        config_path = os.path.join(char_path, "character_config.json")
        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError) as e:
                print(f"[Warning] Failed to load JSON from {config_path}: {e}")
                config = {}
        else:
            config = {}

        # Load session prefix/scenario in memory only — do not overwrite config file
        self.prefix = session_data.get("prefix", "")
        self.scenario = session_data.get("scenario", "")

        # Reload character assets and restore chat content
        self.load_character_assets(force_reload=True)
        chat_content = session_data.get("chat", "")
        self.insert_tagged_chat(chat_content)

    def confirm_back_to_main(self):
        if messagebox.askyesno("Return to Main Menu", "Are you sure you want to return to the main menu? Unsaved progress will be lost."):
            self.controller.show_frame("StartMenu")

    def send_message(self):
        user_message = self.entry.get("1.0", "end").strip()
        if not user_message:
            return

        self.entry.delete("1.0", "end")
        self.entry.focus_set()

        self.chat_display.configure(state="normal")
        self.chat_display.insert("end", f"You: {user_message}\n", "user")
        self.chat_display.see("end")
        self.chat_display.configure(state="disabled")

        memory_text = self.retrieve_relevant_memories(user_message)
        prompt = "\n".join([
            self.prefix.strip(),
            f"Scenario: {self.scenario.strip()}",
            memory_text,
            f"User: {user_message}",
            f"{self.controller.selected_character}:"
        ])

        self.last_prompt = prompt

        self.chat_display.configure(state="normal")
        self.chat_display.insert("end", "\n(Thinking...)\n\n")
        self.chat_display.configure(state="disabled")
        self.chat_display.see("end")

        self.after(100, lambda: self.fetch_and_display_reply(prompt))

    def fetch_and_display_reply(self, prompt):
        reply = self.call_llm_api(prompt)
        self.print_memory_debug()

        # Remove (Thinking...) from display directly
        self.chat_display.configure(state="normal")
        index = self.chat_display.search("(Thinking...)", "1.0", "end")
        if index:
            line_end = f"{index} lineend+1c"
            self.chat_display.delete(index, line_end)

        # Insert bot reply with proper tag
        self.chat_display.insert("end", f"{self.controller.selected_character}: ", "bot")
        self.chat_display.insert("end", reply.strip() + "\n\n", "bot")
        self.chat_display.configure(state="disabled")
        self.chat_display.see("end")

    def insert_tagged_chat(self, chat_text):
        self.chat_display.configure(state="normal")
        self.chat_display.delete("1.0", "end")

        for line in chat_text.strip().split("\n"):
            tag = None
            if line.startswith("You:"):
                tag = "user"
            elif line.startswith(f"{self.controller.selected_character}:"):
                tag = "bot"
            elif line.startswith("===") or line.startswith("  ") or line.startswith("> "):
                tag = "debug"

            self.chat_display.insert("end", line + "\n", tag if tag else "")
    
        self.chat_display.configure(state="disabled")

    def call_llm_api(self, prompt):
        assert "AdvancedSettings" in self.controller.frames, "AdvancedSettings view not initialized!"
        settings = self.controller.frames["AdvancedSettings"]

        url = settings.get_llm_url()
        headers = {"Content-Type": "application/json"}

        payload = {
            "model": settings.get_model_name(),
            "messages": [{"role": "user", "content": prompt}],
            "temperature": settings.get_temperature(),
            "frequency_penalty": settings.get_frequency_penalty(),
            "presence_penalty": settings.get_presence_penalty()
        }

        max_tokens = settings.get_max_tokens()
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens

        # Store the final payload (after optional fields added)
        # Combine LLM settings with memory settings for debug tracking
        self.last_payload_used = {
            "model": payload.get("model"),
            "temperature": payload.get("temperature"),
            "max_tokens": max_tokens,
            "frequency_penalty": payload.get("frequency_penalty"),
            "presence_penalty": payload.get("presence_penalty"),
        }

        # Merge in top_k and similarity_threshold if available
        if hasattr(self, "memory_settings"):
            self.last_payload_used.update(self.memory_settings)
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        else:
            # Optionally omit from payload if None
            pass

        # Always track what was set, even if it's None
        self.last_payload_used["max_tokens"] = max_tokens

        if settings.get_prompt_preview():
            print("\n=== Final API Payload ===")
            print(json.dumps(payload, indent=2))
            print("=== End Payload ===\n")

        try:
            response = requests.post(url, headers=headers, json=payload)
            if response.status_code == 200:
                return response.json()["choices"][0]["message"]["content"]
            else:
                return f"[Error {response.status_code}] {response.text}"
        except Exception as e:
            return f"[Connection Error] {e}"

    def retrieve_relevant_memories(self, user_message, similarity_threshold=None):
        settings = self.controller.frames["AdvancedSettings"]
        if similarity_threshold is None:
            similarity_threshold = settings.get_similarity_threshold()
        top_k = settings.get_memory_chunk_limit()
        # Ensure top_k is an integer
        try:
            top_k = int(top_k)
        except (ValueError, TypeError):
            top_k = 5  # fallback default
        # Store memory values temporarily
        self.memory_settings = {
            "top_k": top_k,
            "similarity_threshold": similarity_threshold
        }

        if not self.memory_index or not self.memory_mapping:
            return ""

        query_embedding = self.embedder.encode([user_message]).astype("float32")
        D, I = self.memory_index.search(query_embedding, top_k)

        lemmatized_keywords = set(
            self.lemmatizer.lemmatize(w) for w in re.findall(r'\b\w+\b', user_message.lower())
            if w not in ENGLISH_STOP_WORDS
        )

        payload = getattr(self, "last_payload_used", {})
        top_k_debug = payload.get("top_k", "???")
        similarity_threshold_debug = payload.get("similarity_threshold", "???")

        debug_lines = ["\n=== Retrieved Memory Debug ===\n"]

        debug_lines.append(f"Top K (Memory Chunks): {top_k_debug}")
        debug_lines.append(f"Similarity Threshold: {similarity_threshold_debug}")
        debug_lines.append("")

        debug_lines.append("--- LLM Settings Used ---")
        debug_lines.append(f"Model: {payload.get('model', '???')}")

        temperature_val = payload.get("temperature")
        debug_lines.append(f"Temperature: {temperature_val if temperature_val is not None else '???'}")

        max_tokens_val = payload.get("max_tokens")
        debug_lines.append(f"Max Tokens: {max_tokens_val if max_tokens_val is not None else 'No Limit'}")

        frequency_val = payload.get("frequency_penalty")
        debug_lines.append(f"Frequency Penalty: {frequency_val if frequency_val is not None else '???'}")

        presence_val = payload.get("presence_penalty")
        debug_lines.append(f"Presence Penalty: {presence_val if presence_val is not None else '???'}")

        debug_lines.append("")
        results = []

        for dist, idx in zip(D[0], I[0]):
            if idx >= len(self.memory_mapping):
                continue

            memory = self.memory_mapping[idx]
            summary = memory.get("summary", "")
            tags = set(t.lower() for t in memory.get("tags", []))

            # Lemmatize all tag words
            lemmatized_tag_words = set()
            tag_to_words = {}
            for tag in tags:
                tag_words = re.findall(r'\b\w+\b', tag)
                tag_to_words[tag] = tag_words
                for word in tag_words:
                    lemmatized_tag_words.add(self.lemmatizer.lemmatize(word))

            matched = lemmatized_keywords & lemmatized_tag_words
            boost = 0.5 * len(matched)
            score = dist + boost

            results.append((score, summary, matched, dist, boost, tag_to_words))

        results.sort(reverse=True, key=lambda x: x[0])
        selected = []

        for score, summary, matched_tags, base_score, boost, tag_to_words in results[:top_k]:
            if score > similarity_threshold:
                debug_lines.append(f"> Memory: {summary.strip()[:100]}...")
                debug_lines.append(f"  Base: {base_score:.4f}")
                debug_lines.append(f"  Boost: {boost:.4f}")
                debug_lines.append(f"  Total: {score:.4f}")
                if matched_tags:
                    debug_lines.append(f"  Matched words: {', '.join(sorted(matched_tags))}")
                else:
                    debug_lines.append("  Matched words: (none)")
                debug_lines.append("")

                selected.append(f"[Memory] {summary}")

        debug_lines.append("=== End ===\n")
        debug_text = "\n".join(debug_lines)

        # Print to console for dev
        #print(debug_text)

        # Optionally show in chat window
        #if self.debug_mode:  
            #self.chat_display.configure(state="normal")
            #self.chat_display.insert("end", debug_text + "\n", "debug")
            #self.chat_display.configure(state="disabled")

        return "\n".join(selected)

    def tkraise(self, aboveThis=None):
        super().tkraise(aboveThis)
        self.debug_mode = self.debug_toggle_var.get()
        if not self.chat_initialized:
            self.load_character_assets()
            self.chat_initialized = True

    def load_character_assets(self, force_reload=False):
        if self.chat_initialized and not force_reload:
            return

        char_name = self.controller.selected_character
        if not char_name:
            return

        path = os.path.join("Character", char_name)
        config_path = os.path.join(path, "character_config.json")
        index_path = os.path.join(path, "memory_index.faiss")
        mapping_path = os.path.join(path, "memory_mapping.json")

        # Load character config
        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError) as e:
                print(f"[Warning] Failed to load JSON from {config_path}: {e}")
                config = {}
        
            self.character_color = config.get("text_color", self.bot_color)
            self.chat_display.tag_config("bot", foreground=self.character_color)

            if force_reload or not self.prefix:
                self.prefix = config.get("prefix_instructions", "")
            if force_reload or not self.scenario:
                self.scenario = config.get("scenario", "")

        # Load memory index + mapping
        if os.path.exists(index_path) and os.path.exists(mapping_path):
            self.memory_index = faiss.read_index(index_path)
            try:
                with open(mapping_path, "r", encoding="utf-8") as f:
                    self.memory_mapping = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError) as e:
                print(f"[Warning] Failed to load JSON from {mapping_path}: {e}")
                self.memory_mapping = []

        # Output intro message if chat display is still empty
        if not self.chat_display.get("1.0", "end").strip():
            self.chat_display.configure(state="normal")
            self.chat_display.insert("end", f"--- {char_name} loaded ---\nScenario: {self.scenario}\n\n")
            self.chat_display.configure(state="disabled")

CHARACTER_DIR = "Character"
# Contains def load_character, def save_character, 
# def load_scenario_from_file, def save_scenario_to_file,
# def load_prefix_from_file, def save_prefix_to_file, 
class CharacterSettings(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        outer = ctk.CTkFrame(self)
        outer.grid(row=0, column=0, sticky="nsew")

        outer.grid_rowconfigure(0, weight=1)
        outer.grid_columnconfigure(0, weight=1)

        inner = ctk.CTkFrame(outer)
        inner.grid(row=0, column=0)

        self.character_folder_map = {}
        self.selected_character = ctk.StringVar()
        self.selected_character.trace("w", self.load_character)

        ctk.CTkLabel(inner, text="Select Character:").pack(pady=(10, 0))

        character_display_names = []

        os.makedirs(CHARACTER_DIR, exist_ok=True)
        for folder_name in os.listdir(CHARACTER_DIR):
            folder_path = os.path.join(CHARACTER_DIR, folder_name)
            config_path = os.path.join(folder_path, "character_config.json")
            if os.path.isdir(folder_path) and os.path.exists(config_path):
                try:
                    with open(config_path, "r", encoding="utf-8") as f:
                        config = json.load(f)
                except (FileNotFoundError, json.JSONDecodeError) as e:
                    print(f"[Warning] Failed to load JSON from {config_path}: {e}")
                    config = {}

                display_name = config.get("name", folder_name)
                character_display_names.append(display_name)
                self.character_folder_map[display_name] = folder_name

        self.character_dropdown = ctk.CTkOptionMenu(inner, variable=self.selected_character, values=character_display_names)
        self.character_dropdown.pack(pady=(0, 10))

        ctk.CTkLabel(inner, text="Scenario:").pack()
        self.scenario_box = ctk.CTkTextbox(inner, height=100, width=0)
        self.scenario_box.pack(pady=(0, 10))

        ctk.CTkButton(inner, text="Load Scenario from File", command=self.load_scenario_from_file).pack(pady=(0, 5))
        ctk.CTkButton(inner, text="Save Scenario to File", command=self.save_scenario_to_file).pack(pady=(0, 10))

        ctk.CTkLabel(inner, text="Prefix Instructions:").pack()
        self.prefix_box = ctk.CTkTextbox(inner, height=180, width=0)
        self.prefix_box.pack(pady=(0, 10))

        ctk.CTkButton(inner, text="Load Prefix from File", command=self.load_prefix_from_file).pack(pady=(0, 5))
        ctk.CTkButton(inner, text="Save Prefix to File", command=self.save_prefix_to_file).pack(pady=(0, 10))

        ctk.CTkLabel(inner, text="Text Color (hex):").pack()
        self.color_entry = ctk.CTkEntry(inner, width=150)
        self.color_entry.pack(pady=(0, 10))

        ctk.CTkButton(inner, text="Save All Settings", command=self.save_character).pack(pady=10)
        ctk.CTkButton(inner, text="Back to Menu", command=lambda: controller.show_frame("StartMenu")).pack(pady=20)

        if character_display_names:
            self.selected_character.set(character_display_names[0])
            self.load_character()  # Safe to call once initially

    def is_valid_hex_color(self, color):
        if isinstance(color, str) and len(color) == 7 and color.startswith("#"):
            try:
                int(color[1:], 16)
                return True
            except ValueError:
                return False
        return False

    def apply_theme_colors(self):
        entry_bg_color = self.controller.entry_bg_color
        text_color = self.controller.text_color
        accent_color = self.controller.accent_color

        self.scenario_box.configure(fg_color=entry_bg_color, text_color=text_color, border_color=accent_color)
        self.prefix_box.configure(fg_color=entry_bg_color, text_color=text_color, border_color=accent_color)

    def load_character(self, *args):
        display_name = self.selected_character.get()
        name = self.character_folder_map.get(display_name, display_name)
        path = os.path.join(CHARACTER_DIR, name, "character_config.json")

        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError) as e:
                print(f"[Warning] Failed to load JSON from {path}: {e}")
                data = {}

            self.scenario_box.delete("1.0", "end")
            self.scenario_box.insert("end", data.get("scenario", ""))

            self.prefix_box.delete("1.0", "end")
            self.prefix_box.insert("end", data.get("prefix_instructions", ""))

            self.color_entry.delete(0, "end")
            self.color_entry.insert(0, data.get("text_color", ""))

    def save_character(self):
        # Validate hex input for character text color
        color = self.color_entry.get().strip()
        if not is_valid_hex_color(color):
            print("[Warning] Invalid character text color hex value.")
            messagebox.showerror("Invalid Color", "Text color must be a valid hex code like #ffaa00.")
            return  # abort save

        display_name = self.selected_character.get()
        name = self.character_folder_map.get(display_name, display_name)
        path = os.path.join(CHARACTER_DIR, name)
        os.makedirs(path, exist_ok=True)

        config_path = os.path.join(path, "character_config.json")
        config = {}

        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError) as e:
                print(f"[Warning] Failed to load JSON from {config_path}: {e}")
                config = {}

        config["scenario"] = self.scenario_box.get("1.0", "end").strip()
        config["prefix_instructions"] = self.prefix_box.get("1.0", "end").strip()
        config["text_color"] = color.upper()

        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)

        # Update ChatView if this character is currently active
        current_char = self.controller.selected_character
        if current_char == name:
            chat_view = self.controller.frames.get("ChatView")
            if chat_view:
                chat_view.load_character_assets(force_reload=True)

    def load_scenario_from_file(self):
        name = self.selected_character.get()
        scenario_dir = os.path.join(CHARACTER_DIR, self.character_folder_map[name], "Scenarios")
        os.makedirs(scenario_dir, exist_ok=True)
        file_path = filedialog.askopenfilename(initialdir=scenario_dir, title="Select Scenario File", filetypes=[("Text Files", "*.txt")])
        if file_path:
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()
                self.scenario_box.delete("1.0", "end")
                self.scenario_box.insert("end", text)

    def save_scenario_to_file(self):
        name = self.selected_character.get()
        scenario_dir = os.path.join(CHARACTER_DIR, self.character_folder_map[name], "Scenarios")
        os.makedirs(scenario_dir, exist_ok=True)
        file_path = filedialog.asksaveasfilename(defaultextension=".txt", initialdir=scenario_dir, filetypes=[("Text Files", "*.txt")])
        if file_path:
            text = self.scenario_box.get("1.0", "end").strip()
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(text)

    def load_prefix_from_file(self):
        name = self.selected_character.get()
        prefix_dir = os.path.join(CHARACTER_DIR, self.character_folder_map[name], "Prefix")
        os.makedirs(prefix_dir, exist_ok=True)
        file_path = filedialog.askopenfilename(initialdir=prefix_dir, title="Select Prefix File", filetypes=[("Text Files", "*.txt")])
        if file_path:
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()
                self.prefix_box.delete("1.0", "end")
                self.prefix_box.insert("end", text)

    def save_prefix_to_file(self):
        name = self.selected_character.get()
        prefix_dir = os.path.join(CHARACTER_DIR, self.character_folder_map[name], "Prefix")
        os.makedirs(prefix_dir, exist_ok=True)
        file_path = filedialog.asksaveasfilename(defaultextension=".txt", initialdir=prefix_dir, filetypes=[("Text Files", "*.txt")])
        if file_path:
            text = self.prefix_box.get("1.0", "end").strip()
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(text)

class AdvancedSettings(CenteredFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        # Load saved settings inor use defaults
        self.settings_path = "config/advanced_settings.json"
        self.settings = self.load_settings()

        container = ctk.CTkFrame(self)
        container.grid(row=1, column=1)
        container.grid_columnconfigure((0, 1, 2), weight=1)

        ctk.CTkLabel(container, text="Advanced Settings", font=("Arial", 18)).grid(row=0, column=0, columnspan=3, pady=20)

        col1 = ctk.CTkFrame(container)
        col2 = ctk.CTkFrame(container)
        col3 = ctk.CTkFrame(container)
        col1.grid(row=1, column=0, padx=10, sticky="n")
        col2.grid(row=1, column=1, padx=10, sticky="n")
        col3.grid(row=1, column=2, padx=10, sticky="n")

        def add_labeled_entry(parent, label, default):
            ctk.CTkLabel(parent, text=label).pack()
            entry = ctk.CTkEntry(parent, width=180)
            entry.insert(0, str(default))
            entry.pack(pady=(0, 10))
            return entry

        def add_slider_with_entry(parent, label, from_, to_, default, steps=100):
            ctk.CTkLabel(parent, text=label).pack()
            frame = ctk.CTkFrame(parent, fg_color="transparent")
            frame.pack(pady=(0, 10))

            slider = ctk.CTkSlider(frame, from_=from_, to=to_, number_of_steps=steps)
            slider.pack(side="left", expand=True, fill="x", padx=(0, 5))

            entry = ctk.CTkEntry(frame, width=50)
            entry.pack(side="right")
            entry.insert(0, str(default))

            def slider_changed(val):
                entry.delete(0, "end")
                entry.insert(0, f"{float(val):.2f}")

            def entry_changed(_):
                try:
                    value = float(entry.get())
                    value = max(min(value, to_), from_)
                    slider.set(value)
                except ValueError:
                    # Invalid input  restore to slider's current value
                    entry.delete(0, "end")
                    entry.insert(0, f"{slider.get():.2f}")

            slider.configure(command=slider_changed)
            entry.bind("<Return>", entry_changed)
            entry.bind("<FocusOut>", entry_changed)
            slider.set(default)
            return slider, entry

        def add_labeled_checkbox(parent, label, default):
            var = ctk.BooleanVar(value=default)
            chk = ctk.CTkCheckBox(parent, text=label, variable=var)
            chk.pack(pady=(0, 10))
            return var

        # Column 1: Model + Memory
        self.max_tokens_entry = add_labeled_entry(col1, "Max Tokens", self.settings.get("max_tokens", 2048))
        self.no_token_limit_var = add_labeled_checkbox(col1, "No Token Limit", self.settings.get("no_token_limit", False))
        self.chunk_entry = add_labeled_entry(col1, "Memory Chunks (Top K)", self.settings.get("top_k", 10))
        self.temp_slider, self.temp_entry = add_slider_with_entry(col1, "Temperature", 0.0, 1.5, self.settings.get("temperature", 0.7), 15)
        self.sim_thresh_slider, self.sim_thresh_entry = add_slider_with_entry(col1, "Similarity Threshold", 0.0, 1.0, self.settings.get("similarity_threshold", 0.7), 100)
        self.boost_slider, self.boost_entry = add_slider_with_entry(col1, "Memory Boost", 0.0, 3.0, self.settings.get("memory_boost", 0.5), 30)
        self.freq_penalty_slider, self.freq_penalty_entry = add_slider_with_entry(col1, "Frequency Penalty", 0.0, 2.0, self.settings.get("frequency_penalty", 0.0), 20)
        self.pres_penalty_slider, self.pres_penalty_entry = add_slider_with_entry(col1, "Presence Penalty", 0.0, 2.0, self.settings.get("presence_penalty", 0.0), 20)

        # Column 2: Display + Theme
        self.ui_theme_color_entry = add_labeled_entry(col2, "UI Theme Color (hex)", self.settings.get("theme_color", "#333333"))
        self.accent_color_entry = add_labeled_entry(col2, "Accent Color (hex)", self.settings.get("accent_color", "#00ccff"))
        self.entry_color_entry = add_labeled_entry(col2, "Entry BG Color (hex)", self.settings.get("entry_color", "#222222"))
        self.text_color_entry = add_labeled_entry(col2, "Text Color (hex)", self.settings.get("text_color", "#ffffff"))
        self.user_color_entry = add_labeled_entry(col2, "User Text Color (hex)", self.settings.get("user_color", "#00ccff"))
        self.debug_color_entry = add_labeled_entry(col2, "Debug Text Color (hex)", self.settings.get("debug_color", "#ff0f0f"))
        self.text_size_entry = add_labeled_entry(col2, "Text Size", self.settings.get("text_size", 14))
        self.auto_scroll_var = add_labeled_checkbox(col2, "Auto-Scroll", self.settings.get("auto_scroll", True))
        self.prompt_preview_var = add_labeled_checkbox(col2, "Prompt Preview", self.settings.get("prompt_preview", False))

        # Column 3: API + Paths
        self.llm_url_entry = add_labeled_entry(col3, "LLM URL", self.settings.get("llm_url", "http://localhost:1234/v1/chat/completions"))
        self.model_entry = add_labeled_entry(col3, "Model Name", self.settings.get("model", "neural-chat-7b-v3.1"))
        self.save_path_entry = add_labeled_entry(col3, "Save Path Override", self.settings.get("save_path", ""))

        ctk.CTkButton(col3, text="Save Settings", command=self.save_settings_as).pack(pady=(0, 5))
        ctk.CTkButton(col3, text="Load Settings", command=self.load_settings_from_file).pack(pady=(0, 5))
        ctk.CTkButton(col3, text="Show Current Values (Debug)", command=self.print_current_values).pack(pady=(0, 5))
        ctk.CTkButton(col3, text="Back to Menu", command=lambda: controller.show_frame("StartMenu")).pack(pady=(0, 20))

    def get_temperature(self): return round(float(self.temp_entry.get()), 2)
    def get_memory_chunk_limit(self):
        return max(1, int(self.chunk_entry.get()))
    def get_similarity_threshold(self): return round(float(self.sim_thresh_entry.get()), 2)
    def get_memory_boost(self): return round(float(self.boost_entry.get()), 2)
    def get_text_size(self): return int(self.text_size_entry.get())
    def get_debug_color(self): return self.debug_color_entry.get().strip()
    def get_user_color(self): return self.user_color_entry.get().strip()
    def get_theme_color(self): return self.ui_theme_color_entry.get().strip()
    def get_llm_url(self): return self.llm_url_entry.get().strip()
    def get_model_name(self): return self.model_entry.get().strip()
    def get_max_tokens(self):
        if self.get_no_token_limit():
            return None  # tells the API to use the full available context
        return int(self.max_tokens_entry.get())
    def get_no_token_limit(self): return self.no_token_limit_var.get()
    def get_frequency_penalty(self): return round(float(self.freq_penalty_entry.get()), 2)
    def get_presence_penalty(self): return round(float(self.pres_penalty_entry.get()), 2)
    def get_auto_scroll(self): return self.auto_scroll_var.get()
    def get_prompt_preview(self): return self.prompt_preview_var.get()
    def get_save_path(self): return self.save_path_entry.get().strip()
    def get_accent_color(self): return self.accent_color_entry.get().strip()
    def get_text_color(self): return self.text_color_entry.get().strip()

    def save_settings_as(self):
        profile_dir = "config/settings_profiles"
        os.makedirs(profile_dir, exist_ok=True)

        file_path = filedialog.asksaveasfilename(
            initialdir=profile_dir,
            defaultextension=".json",
            filetypes=[("JSON Files", "*.json")],
            title="Save Settings Profile"
        )
        if not file_path:
            return

        settings = self.get_all_settings()

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(self.get_all_settings(), f, indent=2)

        # Also save to default so it's applied next launch
        os.makedirs("config", exist_ok=True)
    with open("config/advanced_settings.json", "w", encoding="utf-8") as f:
            json.dump(self.get_all_settings(), f, indent=2)

    def load_settings(self):
        if os.path.exists(self.settings_path):
            try:
                with open(self.settings_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (FileNotFoundError, json.JSONDecodeError) as e:
                print(f"[Warning] Failed to load JSON from {self.settings_path}: {e}")
        return {}

    def load_settings_from_file(self):
        profile_dir = "config/settings_profiles"
        os.makedirs(profile_dir, exist_ok=True)

        file_path = filedialog.askopenfilename(
            initialdir=profile_dir,
            filetypes=[("JSON Files", "*.json")],
            title="Load Settings Profile"
        )
        if not file_path:
            return

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                settings = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"[Warning] Failed to load JSON from {file_path}: {e}")
            return

        self.apply_settings(settings)

        # Save this as the new default for next launch
        os.makedirs("config", exist_ok=True)
        with open("config/advanced_settings.json", "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2)

    def get_all_settings(self):
        max_tokens = self.get_max_tokens()
        return {
            "no_token_limit": self.get_no_token_limit(),
            "temperature": self.get_temperature(),
            "top_k": self.get_memory_chunk_limit(),
            "similarity_threshold": self.get_similarity_threshold(),
            "memory_boost": self.get_memory_boost(),
            "text_size": self.get_text_size(),
            "debug_color": self.get_debug_color(),
            "user_color": self.get_user_color(),
            "theme_color": self.get_theme_color(),
            "accent_color": self.get_accent_color(),
            "entry_color": self.entry_color_entry.get().strip(),
            "text_color": self.get_text_color(),
            "llm_url": self.get_llm_url(),
            "model": self.get_model_name(),
            "max_tokens": max_tokens if max_tokens is not None else 2048,
            "frequency_penalty": self.get_frequency_penalty(),
            "presence_penalty": self.get_presence_penalty(),
            "auto_scroll": self.get_auto_scroll(),
            "prompt_preview": self.get_prompt_preview(),
            "save_path": self.get_save_path()
        }

    def set_slider_and_entry(self, slider, entry, value):
        try:
            num = float(value)
        except (ValueError, TypeError):
            num = 0.0
        slider.set(num)
        entry.delete(0, "end")
        entry.insert(0, f"{num:.2f}")

    def apply_settings(self, data):
        try:
            max_tokens = data.get("max_tokens") or 2048
            self.max_tokens_entry.delete(0, "end")
            self.max_tokens_entry.insert(0, str(max_tokens))

            self.chunk_entry.delete(0, "end")
            self.chunk_entry.insert(0, data.get("top_k", 10))

            self.set_slider_and_entry(self.temp_slider, self.temp_entry, data.get("temperature", 0.7))
            self.set_slider_and_entry(self.sim_thresh_slider, self.sim_thresh_entry, data.get("similarity_threshold", 0.7))
            self.set_slider_and_entry(self.boost_slider, self.boost_entry, data.get("memory_boost", 0.5))
            self.set_slider_and_entry(self.freq_penalty_slider, self.freq_penalty_entry, data.get("frequency_penalty", 0.0))
            self.set_slider_and_entry(self.pres_penalty_slider, self.pres_penalty_entry, data.get("presence_penalty", 0.0))

            start_menu = self.controller.frames.get("StartMenu")
            if start_menu and hasattr(start_menu, "apply_theme_colors"):
                start_menu.apply_theme_colors()

            self.text_size_entry.delete(0, "end")
            self.text_size_entry.insert(0, data.get("text_size", 14))

            self.ui_theme_color_entry.delete(0, "end")
            self.ui_theme_color_entry.insert(0, data.get("theme_color", "#333333"))

            self.accent_color_entry.delete(0, "end")
            self.accent_color_entry.insert(0, data.get("accent_color", "#00ccff"))

            self.entry_color_entry.delete(0, "end")
            self.entry_color_entry.insert(0, data.get("entry_color", "#222222"))

            self.text_color_entry.delete(0, "end")
            self.text_color_entry.insert(0, data.get("text_color", "#ffffff"))

            self.user_color_entry.delete(0, "end")
            self.user_color_entry.insert(0, data.get("user_color", "#00ccff"))

            self.debug_color_entry.delete(0, "end")
            self.debug_color_entry.insert(0, data.get("debug_color", "#ff0f0f"))

            self.llm_url_entry.delete(0, "end")
            self.llm_url_entry.insert(0, data.get("llm_url", "http://localhost:1234/v1/chat/completions"))

            self.model_entry.delete(0, "end")
            self.model_entry.insert(0, data.get("model", "neural-chat-7b-v3.1"))

            self.save_path_entry.delete(0, "end")
            self.save_path_entry.insert(0, data.get("save_path", ""))

            self.no_token_limit_var.set(data.get("no_token_limit", False))
            self.auto_scroll_var.set(data.get("auto_scroll", True))
            self.prompt_preview_var.set(data.get("prompt_preview", False))
            theme = data.get("theme_color", "#333333")
            self.controller.apply_theme_color(theme)

            # Update controller theme values FIRST
            self.controller.entry_bg_color = data.get("entry_color", "#222222")
            self.controller.accent_color = data.get("accent_color", "#00ccff")
            self.controller.text_color = data.get("text_color", "#ffffff")

            # Apply UI theme
            self.controller.apply_ui_theme(
                bg_color=data.get("theme_color", "#333333"),
                accent_color=self.controller.accent_color,
                text_color=self.controller.text_color,
                entry_bg_color=self.controller.entry_bg_color
            )

            # Update chat colors
            view = self.controller.frames.get("ChatView")
            if view:
                view.chat_display.tag_config("user", foreground=self.get_user_color())
                view.chat_display.tag_config("debug", foreground=self.get_debug_color())
                view.apply_theme_colors()

            char_view = self.controller.frames.get("CharacterSettings")
            if char_view and hasattr(char_view, "apply_theme_colors"):
                char_view.apply_theme_colors()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to apply settings:\n{e}")

    def print_current_values(self):
        print("\n=== Current Advanced Settings ===")
        for key in [
            "temperature", "memory_chunk_limit", "no_token_limit", "similarity_threshold", "memory_boost", "text_size",
            "debug_color", "user_color", "theme_color", "llm_url", "model_name",
            "max_tokens", "frequency_penalty", "presence_penalty",
            "auto_scroll", "prompt_preview", "save_path"
        ]:
            print(f"{key}:", getattr(self, f"get_{key}")())
        print("=== End ===\n")

if __name__ == "__main__":
    app = RoleplayApp()
    app.mainloop()
