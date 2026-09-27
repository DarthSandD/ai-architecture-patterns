"""
Pattern 07 — Context Engineering
================================

A context budgeter that ranks, dedupes, compresses, and positions
sections under a token cap — and shows the effect of ordering.

Demonstrates the "lost in the middle" positioning rule.

Stdlib only. Run:
    python demo.py
"""

from dataclasses import dataclass
from typing import List
import re

# ---------------------------------------------------------------------------
# SECTION MODEL
# ---------------------------------------------------------------------------

@dataclass
class Section:
    kind: str          # system | tools | retrieved | history | ask
    text: str
    priority: int      # higher = keep first when over budget

    @property
    def tokens(self) -> int:
        """Rough token estimate: ~4 chars per token."""
        return max(1, len(self.text) // 4)


def estimate_tokens(text: str) -> int:
    return max(1, len(text) // 4)


# ---------------------------------------------------------------------------
# THE FOUR LEVERS  (pull in this order)
# ---------------------------------------------------------------------------

def dedupe(sections: List[Section]) -> List[Section]:
    """Lever 2: remove near-identical content."""
    seen = set()
    out = []
    for s in sections:
        key = frozenset(re.findall(r"[a-z0-9]+", s.text.lower()))
        if key and key not in seen:
            seen.add(key)
            out.append(s)
    return out


def rank(sections: List[Section]) -> List[Section]:
    """Lever 1: best content first."""
    return sorted(sections, key=lambda s: s.priority, reverse=True)


def compress(section: Section, max_tokens: int) -> Section:
    """Lever 3: summarize when a section is too big."""
    if section.tokens <= max_tokens:
        return section
    # Truncate at a word boundary, note the compression.
    char_cap = max_tokens * 4
    truncated = section.text[:char_cap].rsplit(" ", 1)[0]
    return Section(
        section.kind,
        f"{truncated}… [compressed from {section.tokens} tokens]",
        section.priority,
    )


def truncate(sections: List[Section], budget: int) -> List[Section]:
    """Lever 4: drop lowest-priority sections until under budget."""
    out = list(sections)
    while sum(s.tokens for s in out) > budget and len(out) > 1:
        out.pop()  # lowest priority is last after rank()
    return out


# ---------------------------------------------------------------------------
# ORDERING  (position matters — the lost-in-the-middle effect)
# ---------------------------------------------------------------------------

ORDER = {
    "system": 0,     # stable first → enables prompt caching
    "tools": 1,
    "retrieved": 2,  # reference material in the middle
    "history": 3,
    "ask": 4,        # current ask LAST → recency bias helps
}


def order_for_model(sections: List[Section]) -> List[Section]:
    return sorted(sections, key=lambda s: ORDER.get(s.kind, 99))


# ---------------------------------------------------------------------------
# ASSEMBLY
# ---------------------------------------------------------------------------

def build_context(sections: List[Section], budget: int) -> dict:
    before = sum(s.tokens for s in sections)

    working = dedupe(sections)
    working = rank(working)
    working = [compress(s, 60) for s in working]   # cap any single section
    working = truncate(working, budget)
    working = order_for_model(working)

    after = sum(s.tokens for s in working)
    return {
        "sections": working,
        "tokens_before": before,
        "tokens_after": after,
        "dropped": len(sections) - len(working),
    }


def render(result: dict) -> str:
    lines = []
    for s in result["sections"]:
        lines.append(f"  [{ORDER.get(s.kind, 9)}] {s.kind:<10} "
                     f"{s.tokens:>4} tok  {s.text[:52]}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# DEMO
# ---------------------------------------------------------------------------

def main():
    print("=" * 72)
    print("CONTEXT ENGINEERING: budget the window, don't fill it")
    print("=" * 72 + "\n")

    sections = [
        Section("system", "You are a helpful assistant. Always cite sources.",
                10),
        Section("tools", "get_weather(city), search(query), calculate(expr)",
                8),
        Section("retrieved", "The warranty covers defects for 12 months.",
                5),
        Section("retrieved", "The warranty covers defects for 12 months.",
                5),  # duplicate → deduped
        Section("retrieved", "Refunds take 5 business days. " * 30, 4),
        Section("history", "User asked about shipping earlier. " * 20, 3),
        Section("history", "User said thanks.", 2),
        Section("ask", "How long is the warranty?", 9),
    ]

    BUDGET = 200

    result = build_context(sections, BUDGET)

    print(f"Budget: {BUDGET} tokens\n")
    print("Final context (ordered for the model):")
    print(render(result))
    print()
    print(f"  tokens before : {result['tokens_before']}")
    print(f"  tokens after  : {result['tokens_after']}  "
          f"(under budget: {result['tokens_after'] <= BUDGET})")
    print(f"  sections dropped: {result['dropped']}")
    print()

    print("=" * 72)
    print("THE ORDERING RULES")
    print("=" * 72)
    print("""
  1. Stable content first    → enables prompt caching
  2. Reference in the middle → retrieved docs, examples
  3. Recent history near end → most relevant turns
  4. Current ask LAST        → recency bias works for you
  5. Critical constraints    → repeat at start AND end

  Models attend most to the BEGINNING and END of context, weakly to
  the MIDDLE ("lost in the middle"). Position is a design decision.
""")


if __name__ == "__main__":
    main()
