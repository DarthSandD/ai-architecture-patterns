"""
Pattern 01 — RAG (Retrieval-Augmented Generation)
=================================================

A minimal, dependency-light RAG to show the *shape* of the pattern.
Uses a tiny in-memory store and a keyword-overlap "embedding" so it
runs anywhere with zero API keys. Swap in real embeddings + a vector DB
for production.

Run:
    python demo.py
"""

from dataclasses import dataclass
from typing import List
import math
import re

# ---------------------------------------------------------------------------
# 1. INDEX PHASE  (runs once, offline)
# ---------------------------------------------------------------------------

# A tiny "corpus" — imagine these are your docs, tickets, or policy pages.
DOCUMENTS = [
    "The warranty covers manufacturing defects for 12 months from purchase.",
    "Refunds are processed within 5 business days to the original payment method.",
    "Shipping to remote islands may take 7-14 days due to logistics.",
    "Bulk orders over 100 units qualify for a 15% discount.",
    "Returns require the original packaging and a receipt.",
    "The warranty does NOT cover water damage or accidental drops.",
]


def tokenize(text: str) -> List[str]:
    """Lowercase word tokens — the simplest possible 'embedding'."""
    return re.findall(r"[a-z0-9]+", text.lower())


def embed(text: str) -> dict:
    """
    Bag-of-words vector as a dict {token: count}.
    Stands in for a real embedding model.
    """
    vector = {}
    for token in tokenize(text):
        vector[token] = vector.get(token, 0) + 1
    return vector


def cosine(a: dict, b: dict) -> float:
    """Cosine similarity between two sparse vectors."""
    shared = set(a) & set(b)
    dot = sum(a[t] * b[t] for t in shared)
    mag_a = math.sqrt(sum(v * v for v in a.values()))
    mag_b = math.sqrt(sum(v * v for v in b.values()))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)


@dataclass
class Chunk:
    text: str
    vector: dict


class Index:
    """In-memory vector store. Swap for Pinecone/Weaviate/pgvector in prod."""

    def __init__(self, documents: List[str]):
        self.chunks = [Chunk(text=d, vector=embed(d)) for d in documents]

    def search(self, query: str, top_k: int = 3) -> List[tuple]:
        """Return [(score, chunk_text)] sorted by relevance."""
        q_vec = embed(query)
        scored = [(cosine(q_vec, c.vector), c.text) for c in self.chunks]
        scored.sort(key=lambda x: x[0], reverse=True)
        return scored[:top_k]


# ---------------------------------------------------------------------------
# 2. QUERY PHASE  (runs per request)
# ---------------------------------------------------------------------------

MIN_SCORE = 0.15  # The guardrail: below this, we have no real match.


def build_prompt(question: str, retrieved: List[tuple]) -> str:
    """Inject retrieved context into the prompt."""
    context = "\n".join(f"- {text}" for _, text in retrieved)
    return (
        "Answer the question using ONLY the context below.\n"
        "If the context does not contain the answer, say "
        "'I don't have that information.'\n\n"
        f"Context:\n{context}\n\n"
        f"Question: {question}\n"
        "Answer:"
    )


def fake_llm(prompt: str) -> str:
    """
    Stand-in for the model call.
    A real version sends `prompt` to your LLM provider.
    """
    if "I don't have that information" in prompt:
        pass  # keep the instruction visible for the demo
    context = prompt.split("Context:\n")[1].split("\n\nQuestion:")[0]
    return f"[model would answer from]:\n{context}"


def rag(question: str, index: Index, top_k: int = 3) -> dict:
    """Full RAG pipeline with a retrieval-miss guardrail."""
    retrieved = index.search(question, top_k=top_k)
    best_score = retrieved[0][0] if retrieved else 0.0

    # GUARDRAIL: don't feed the model weak context.
    if best_score < MIN_SCORE:
        return {
            "answer": "I don't have that information.",
            "retrieved": retrieved,
            "best_score": best_score,
            "miss": True,
        }

    prompt = build_prompt(question, retrieved)
    return {
        "answer": fake_llm(prompt),
        "retrieved": retrieved,
        "best_score": best_score,
        "miss": False,
    }


# ---------------------------------------------------------------------------
# 3. DEMO
# ---------------------------------------------------------------------------

def main():
    index = Index(DOCUMENTS)
    print(f"Indexed {len(index.chunks)} chunks.\n")

    questions = [
        "How long is the warranty?",          # should hit
        "How fast are refunds?",              # should hit
        "Do you cover water damage?",         # should hit (negative answer)
        "What is the capital of France?",     # should MISS
    ]

    for q in questions:
        result = rag(q, index)
        flag = "MISS" if result["miss"] else "HIT "
        print(f"[{flag}] Q: {q}")
        print(f"        best_score = {result['best_score']:.2f}")
        for score, text in result["retrieved"]:
            print(f"          {score:.2f}  {text[:60]}...")
        print()

    print("-" * 70)
    print("Notice: the off-topic question triggers the guardrail instead of")
    print("inventing an answer. That guardrail is the difference between a")
    print("demo and a system you can ship.")


if __name__ == "__main__":
    main()
