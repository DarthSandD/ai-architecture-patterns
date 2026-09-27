"""
Pattern 03 — Multi-Agent
========================

Shows when splitting into multiple agents helps and when it just adds
coordination overhead. Compares a single agent against a coordinator +
specialists on the same task.

Stdlib only. Run:
    python demo.py
"""

from dataclasses import dataclass, field
from typing import Callable

# ---------------------------------------------------------------------------
# Simulated token accounting — the real cost of multi-agent
# ---------------------------------------------------------------------------

@dataclass
class Budget:
    """Tracks the hidden cost of coordination."""
    llm_calls: int = 0
    tokens: int = 0

    def spend(self, tokens: int):
        self.llm_calls += 1
        self.tokens += tokens


# ---------------------------------------------------------------------------
# SPECIALIST AGENTS  (each owns its own context)
# ---------------------------------------------------------------------------

def researcher_agent(query: str, budget: Budget) -> str:
    budget.spend(1200)  # 50k of search results, compressed
    return f"RESEARCH: found 3 sources about '{query}'."


def coder_agent(spec: str, budget: Budget) -> str:
    budget.spend(800)
    return f"CODE: implemented '{spec[:30]}'."


def reviewer_agent(code: str, budget: Budget) -> str:
    budget.spend(600)
    return f"REVIEW: {code[:20]}... looks correct."


# ---------------------------------------------------------------------------
# APPROACH A — ONE AGENT  (everything in one context)
# ---------------------------------------------------------------------------

def single_agent(task: str, budget: Budget) -> str:
    """
    One agent, one context. It does all three jobs in a single call.
    Cheaper and faster — but its context holds everything at once.
    """
    budget.spend(1800)  # one big call
    return f"[one agent] {task} → researched, coded, reviewed."


# ---------------------------------------------------------------------------
# APPROACH B — MULTI-AGENT  (coordinator + specialists)
# ---------------------------------------------------------------------------

def multi_agent(task: str, budget: Budget) -> str:
    """
    Coordinator routes to specialists. Each specialist has an isolated
    context — but every handoff costs a call.
    """
    # Coordinator decides the plan (call 1)
    budget.spend(300)
    plan = ["research", "code", "review"]

    # Coordinator dispatches each specialist (calls 2-4)
    budget.spend(200)  # routing overhead per handoff
    research = researcher_agent(task, budget)
    budget.spend(200)
    code = coder_agent(research, budget)
    budget.spend(200)
    review = reviewer_agent(code, budget)

    # Coordinator merges results (call 5)
    budget.spend(300)
    return f"[coordinator] merged → {review}"


# ---------------------------------------------------------------------------
# COMPARISON
# ---------------------------------------------------------------------------

def compare(task: str):
    print(f"TASK: {task}\n")

    b1 = Budget()
    r1 = single_agent(task, b1)
    print("─ Single agent ─")
    print(f"  result   : {r1}")
    print(f"  LLM calls: {b1.llm_calls}")
    print(f"  tokens   : {b1.tokens}\n")

    b2 = Budget()
    r2 = multi_agent(task, b2)
    print("─ Multi-agent (coordinator + 3 specialists) ─")
    print(f"  result   : {r2}")
    print(f"  LLM calls: {b2.llm_calls}")
    print(f"  tokens   : {b2.tokens}\n")

    print(f"  → multi-agent used {b2.llm_calls / b1.llm_calls:.1f}x the calls "
          f"and {b2.tokens / b1.tokens:.1f}x the tokens")
    print(f"  → for the SAME task, when the context fits in one window.\n")


def main():
    print("=" * 72)
    print("MULTI-AGENT: the coordination cost")
    print("=" * 72 + "\n")

    compare("Build a small REST endpoint")

    print("=" * 72)
    print("DECISION RULE")
    print("=" * 72)
    print("""
  Does one agent's context overflow?
  ├─ No  → Use ONE agent. (this demo: 1 call, 1800 tokens)
  └─ Yes → Does the task split into independent subtasks?
           ├─ No  → ONE agent + summarization.
           └─ Yes → Multi-agent is justified.

  Most teams jump to multi-agent at the top of that tree.
  Start at the top. Split only when context forces you to.
""")


if __name__ == "__main__":
    main()
