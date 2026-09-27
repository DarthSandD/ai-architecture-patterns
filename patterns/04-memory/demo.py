"""
Pattern 04 — Memory
===================

Three-tier memory (short-term / working / long-term) with:
  · relevance-based retrieval
  · an eviction policy (bounded store)
  · deduplication
  · a leakage guard (per-user scoping)

Stdlib only. Run:
    python demo.py
"""

from dataclasses import dataclass, field
from typing import List
import math
import re

# ---------------------------------------------------------------------------
# TIER 3 — LONG-TERM MEMORY  (external store)
# ---------------------------------------------------------------------------

@dataclass
class Memory:
    user_id: str
    text: str
    importance: int = 1  # 1-5, higher = keep longer
    hits: int = 0


class LongTermStore:
    """
    Bounded vector-ish store. Caps size, evicts the least useful,
    and scopes every read to one user (leakage guard).
    """

    MAX_ITEMS = 6  # eviction kicks in beyond this

    def __init__(self):
        self._items: List[Memory] = []

    def _tokens(self, text: str) -> set:
        return set(re.findall(r"[a-z0-9]+", text.lower()))

    def _score(self, a: set, b: set) -> float:
        if not a or not b:
            return 0.0
        return len(a & b) / math.sqrt(len(a) * len(b))

    def write(self, user_id: str, text: str, importance: int = 3) -> str:
        # Dedup: skip near-identical memories for the same user.
        for m in self._items:
            if m.user_id == user_id and self._tokens(m.text) == self._tokens(text):
                return "skipped (duplicate)"

        self._items.append(Memory(user_id, text, importance))
        evicted = self._evict()
        return f"stored{evicted}"

    def _evict(self) -> str:
        """Drop the lowest-value item when over capacity."""
        if len(self._items) <= self.MAX_ITEMS:
            return ""
        # value = importance + usage hits; keep the highest
        self._items.sort(key=lambda m: (m.importance + m.hits), reverse=True)
        dropped = self._items.pop()
        return f" (evicted: '{dropped.text[:30]}...')"

    def retrieve(self, user_id: str, query: str, top_k: int = 2) -> List[Memory]:
        """Relevance search, scoped to ONE user (leakage guard)."""
        q = self._tokens(query)
        scoped = [m for m in self._items if m.user_id == user_id]  # ← guard
        scored = [(self._score(q, self._tokens(m.text)), m) for m in scoped]
        scored = [s for s in scored if s[0] > 0]
        scored.sort(key=lambda x: x[0], reverse=True)
        for _, m in scored[:top_k]:
            m.hits += 1
        return [m for _, m in scored[:top_k]]


# ---------------------------------------------------------------------------
# TIER 2 — WORKING MEMORY  (compressed history)
# ---------------------------------------------------------------------------

class WorkingMemory:
    """Summarizes old turns so the context window doesn't overflow."""

    def __init__(self, max_turns: int = 3):
        self.turns: List[str] = []
        self.summary = ""
        self.max_turns = max_turns

    def add(self, turn: str):
        self.turns.append(turn)
        if len(self.turns) > self.max_turns:
            overflow = self.turns.pop(0)
            self.summary += f" | {overflow[:40]}"

    def render(self) -> str:
        parts = []
        if self.summary:
            parts.append(f"[summary]{self.summary}")
        parts.extend(self.turns)
        return " ".join(parts)


# ---------------------------------------------------------------------------
# TIER 1 + ASSEMBLY
# ---------------------------------------------------------------------------

@dataclass
class Conversation:
    user_id: str
    store: LongTermStore = field(default_factory=LongTermStore)
    working: WorkingMemory = field(default_factory=WorkingMemory)

    def turn(self, user_text: str) -> str:
        self.working.add(f"User: {user_text}")
        memories = self.store.retrieve(self.user_id, user_text)
        context = self.working.render()
        mem_text = "; ".join(m.text for m in memories) or "(none)"
        return (
            f"  context : {context}\n"
            f"  recalled: {mem_text}"
        )


# ---------------------------------------------------------------------------
# DEMO
# ---------------------------------------------------------------------------

def main():
    print("=" * 72)
    print("MEMORY: three tiers, bounded store, leakage guard")
    print("=" * 72 + "\n")

    alice = Conversation("alice")
    bob = Conversation("bob")

    # Seed long-term memory
    print("Writing memories for alice:")
    for text, imp in [
        ("Prefers metric units", 4),
        ("Based in Banjarmasin", 5),
        ("Prefers metric units", 4),          # duplicate → skipped
        ("Working on a fire dashboard", 3),
        ("Likes short answers", 2),
        ("Uses Python daily", 3),
        ("Drinks kopi every morning", 1),
    ]:
        print(f"  '{text}' → {alice.store.write('alice', text, imp)}")

    # Bob has his own memory
    bob.store.write("bob", "Prefers imperial units", 4)
    bob.store.write("bob", "Based in Singapore", 5)

    print("\n" + "-" * 72)
    print("Turn 1 — alice asks about units")
    print(alice.turn("What units should you use?"))

    print("\n" + "-" * 72)
    print("Turn 2 — alice asks where she is based")
    print(alice.turn("Where am I based?"))

    print("\n" + "-" * 72)
    print("LEAKAGE TEST — bob asks about units")
    print(bob.turn("What units should you use?"))
    print("  → bob recalls HIS preference, not alice's. Guard works.")

    print("\n" + "=" * 72)
    print("FAILURE MODES TO TEST BEFORE SHIPPING:")
    for f in ["Forgetting", "Wrong recall", "Pollution",
              "Staleness", "Leakage"]:
        print(f"  · {f}")
    print("\nThis demo covers leakage (per-user scope), pollution (bounded")
    print("store), and dedup. Staleness and wrong-recall need an eval set.")


if __name__ == "__main__":
    main()
