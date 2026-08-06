import os
import json

import faiss
import numpy as np

from sentence_transformers import SentenceTransformer
CORPUS_DIR = CORPUS_DIR = os.path.join("retrieval", "corpus")

def load_documents():
    documents = []

    for filename in os.listdir(CORPUS_DIR):

        filepath = os.path.join(CORPUS_DIR, filename)

        if filename.endswith(".md") or filename.endswith(".txt"):

            with open(filepath, "r", encoding="utf-8") as file:

                text = file.read()

                documents.append(
                    {
                        "filename": filename,
                        "text": text
                    }
                )

    return documents

documents = load_documents()

# print(f"Loaded {len(documents)} documents.")


# print(documents[0]["filename"])
# print()
# print(documents[0]["text"][:500])

# print("Loading embedding model...")

model = SentenceTransformer("BAAI/bge-small-en-v1.5")

# print("Model loaded successfully!")

texts = [doc["text"] for doc in documents]

# print("Generating embeddings...")

embeddings = model.encode(
    texts,
    convert_to_numpy=True,
    show_progress_bar=True
)

# print("Embeddings generated!")

# print(type(embeddings))
# print(embeddings.shape)

# print(embeddings[0][:10])


print("Building FAISS index...")

dimension = embeddings.shape[1] 

index = faiss.IndexFlatL2(dimension) # creates empty vector database

index.add(embeddings)

print(f"FAISS index contains {index.ntotal} vectors.")

faiss.write_index(index, "index.faiss")
print("FAISS index saved!")

with open("chunks.json", "w", encoding="utf-8") as file:
    json.dump(documents, file, indent=4, ensure_ascii=False)

print("Chunk mapping saved!")


