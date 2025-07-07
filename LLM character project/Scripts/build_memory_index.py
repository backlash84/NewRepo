import os
import json
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

# === Paths ===
memory_folder = "../Character/Hermione Granger/Personal_Memories"
index_save_path = "../Character/Hermione Granger/memory_index.faiss"
mapping_save_path = "../Character/Hermione Granger/memory_mapping.json"

# === Load embedding model ===
model = SentenceTransformer('all-MiniLM-L6-v2')

# === Load and encode summaries ===
summaries = []
metadata_mapping = []

for filename in sorted(os.listdir(memory_folder)):
    if filename.endswith(".json"):
        filepath = os.path.join(memory_folder, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
            summary = data.get("summary", "").strip()
            if summary:
                summaries.append(summary)
                metadata_mapping.append(data)
# === Sanity check ===
if not summaries:
    raise ValueError("No valid summaries found. Check the memory folder path or file contents.")

# === Generate embeddings ===
embeddings = model.encode(summaries, show_progress_bar=True)
embeddings = np.array(embeddings).astype("float32")

# === Create FAISS index ===
index = faiss.IndexFlatL2(embeddings.shape[1])
index.add(embeddings)

# === Save index and mapping ===
faiss.write_index(index, index_save_path)
with open(mapping_save_path, "w", encoding="utf-8") as f:
    json.dump(metadata_mapping, f, indent=2)

print(f"Index built with {len(embeddings)} memory chunks.")