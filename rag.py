import requests
import numpy as np
from pathlib import Path

OLLAMA = "http://localhost:11434"
EMBED_MODEL = "nomic-embed-text"
CHAT_MODEL = "qwen3.5:9b"

def embed(texts, kind):
    prefix = {"doc" : "search_document: ", "query": "search_query: "}[kind]
    r = requests.post(f"{OLLAMA}/api/embed", json ={"model": EMBED_MODEL, "input": [prefix + t for t in texts]})
    r.raise_for_status()
    return np.array(r.json()["embeddings"])

def ask_llm(prompt):
    r = requests.post(f"{OLLAMA}/api/chat", json ={
            "model": CHAT_MODEL, "stream": False,
            "messages": [{"role": "user", "content":prompt}]
            })
    return r.json()["message"]["content"]

#print(ask_llm("What model am I running right now?"))

chunks = []
for file in Path("docs").glob("*.md"):
    chunks += [p.strip() for p in file.read_text(encoding = "utf-8").split("\n\n") if p.split()]

chunk_vecotrs = embed(chunks, "doc")
print(f"indexed {len(chunks)} chunks\n")

def retrieve(question, k=3):
    q = embed([question], "query")[0]
    scores = chunk_vecotrs @ q / (np.linalg.norm(chunk_vecotrs, axis=1) * np.linalg.norm(q))
    return [chunks[i] for i in np.argsort(scores)[::-1][:k]]


while(True):
    ques = input("Ask: ")
    context = "\n\n".join(retrieve(ques))
    print(context)
    prompt = f"""Answer the question using ONLY the context below.
    If the answer isn't in the context, say  "I don't know, lol.".
    All answers should be direct and precise. 

    Context: {context}

    Question:{ques}"""

    print("\n" + ask_llm(prompt) + "\n")
