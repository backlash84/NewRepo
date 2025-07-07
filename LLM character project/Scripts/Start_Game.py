import tkinter as tk
from tkinter import messagebox

def start_new_chat():
    messagebox.showinfo("New Chat", "Starting a new chat... (placeholder)")

def load_chat():
    messagebox.showinfo("Load Chat", "Loading previous chat... (placeholder)")

def open_character_settings():
    messagebox.showinfo("Character Settings", "Opening character settings... (placeholder)")

def open_help():
    help_text = (
        "Welcome to the AI Character Roleplay Tool!\n\n"
        "New: Start a fresh roleplay session with the selected character.\n"
        "Load: Continue your last saved roleplay session.\n"
        "Character Settings: Choose a character, edit their behavior, or update the starting scenario.\n"
        "Help: View this guide.\n\n"
        "All sessions are offline and use your locally running LLM model. Make sure it is active before starting."
    )
    messagebox.showinfo("Help", help_text)

# Create the main window
root = tk.Tk()
root.title("AI Character Roleplay")
root.geometry("300x250")

# Create and place buttons
tk.Button(root, text="New", width=20, command=start_new_chat).pack(pady=10)
tk.Button(root, text="Load", width=20, command=load_chat).pack(pady=10)
tk.Button(root, text="Character Settings", width=20, command=open_character_settings).pack(pady=10)
tk.Button(root, text="Help", width=20, command=open_help).pack(pady=10)

# Run the main loop
root.mainloop()