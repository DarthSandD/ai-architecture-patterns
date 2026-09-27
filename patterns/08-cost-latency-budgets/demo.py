"""
Pattern 08 — Cost & Latency Budgets
===================================

A request pipeline that:
  · times each stage
  · enforces a per-request budget (latency + cost)
  · shows a cache eliminating the dominant cost

Stdlib only. Run:
    python demo.py
"""

import time
from dataclasses import dataclass, field
from typing import Callable, Dict, Optional

# ---------------------------------------------------------------------------
# BUDGET
# ---------------------------------------------------------------------------

@dataclass
class Budget:
    max_latency_ms: float = 2000.0
    max_cost_usd: float = 0.020

    latency_used: float = 0.0
    cost_used: float = 0.0
    stages: list = field(default_factory=list)

    def record(self, name: str, latency_ms: float, cost: float):
        self.latency_used += latency_ms
        self.cost_used += cost
        self.stages.append((name, latency_ms, cost))

    @property
    def within_budget(self) -> bool:
        return (self.latency_used <= self.max_latency_ms
                and self.cost_used <= self.max_cost_usd)


# ---------------------------------------------------------------------------
# PIPELINE STAGES  (latency in ms, cost in USD — realistic-ish)
# ---------------------------------------------------------------------------

def stage_cache(prompt: str, cache: Dict[str, str]) -> Optional[str]:
    time.sleep(0.005)
    return cache.get(prompt)


def stage_classify(prompt: str) -> str:
    """Cheap model decides: is this simple or hard?"""
    time.sleep(0.2)
    return "simple" if len(prompt) < 40 else "hard"


def stage_retrieve(prompt: str) -> str:
    time.sleep(0.15)
    return f"[3 docs about '{prompt[:20]}']"


def stage_generate(prompt: str, difficulty: str) -> str:
    """
    The dominant stage. 'simple' routes to a cheap fast model,
    'hard' to the big expensive one.
    """
    if difficulty == "simple":
        time.sleep(0.4)
        return "simple answer"
    time.sleep(1.4)
    return "detailed answer"


def stage_validate(text: str) -> str:
    time.sleep(0.01)
    return text


# ---------------------------------------------------------------------------
# THE PIPELINE
# ---------------------------------------------------------------------------

STAGE_COSTS = {
    "cache": 0.00000,
    "classify": 0.0002,
    "retrieve": 0.0001,
    "generate_simple": 0.002,
    "generate_hard": 0.018,
    "validate": 0.0000,
}


def run_pipeline(prompt: str, cache: Dict[str, str],
                 budget: Budget) -> dict:
    t0 = time.perf_counter()

    # Stage 1 — cache (cheapest possible: don't call the model)
    hit = stage_cache(prompt, cache)
    dt = (time.perf_counter() - t0) * 1000
    budget.record("cache", dt, STAGE_COSTS["cache"])
    if hit is not None:
        return {"result": hit, "cache": "HIT", "budget": budget}

    # Stage 2 — classify
    t = time.perf_counter()
    difficulty = stage_classify(prompt)
    dt = (time.perf_counter() - t) * 1000
    budget.record("classify", dt, STAGE_COSTS["classify"])

    # Stage 3 — retrieve
    t = time.perf_counter()
    context = stage_retrieve(prompt)
    dt = (time.perf_counter() - t) * 1000
    budget.record("retrieve", dt, STAGE_COSTS["retrieve"])

    # Stage 4 — generate (routed)
    t = time.perf_counter()
    answer = stage_generate(prompt, difficulty)
    dt = (time.perf_counter() - t) * 1000
    budget.record(f"generate_{difficulty}", dt,
                  STAGE_COSTS[f"generate_{difficulty}"])

    # Stage 5 — validate
    t = time.perf_counter()
    answer = stage_validate(answer)
    dt = (time.perf_counter() - t) * 1000
    budget.record("validate", dt, STAGE_COSTS["validate"])

    cache[prompt] = answer
    return {"result": answer, "cache": "MISS", "budget": budget}


# ---------------------------------------------------------------------------
# REPORTING
# ---------------------------------------------------------------------------

def show(label: str, out: dict):
    b: Budget = out["budget"]
    print(f"  {label}")
    print(f"    cache    : {out['cache']}")
    print(f"    result   : {out['result']}")
    print(f"    stages   :")
    for name, lat, cost in b.stages:
        bar = "█" * int(lat / 50)
        print(f"      {name:<16} {lat:7.1f} ms  ${cost:.4f}  {bar}")
    print(f"    ─────────────────────────────────────────")
    print(f"    TOTAL            {b.latency_used:7.1f} ms  "
          f"${b.cost_used:.4f}")
    print(f"    within budget    : "
          f"{'✅ yes' if b.within_budget else '❌ NO'}")
    print()


# ---------------------------------------------------------------------------
# DEMO
# ---------------------------------------------------------------------------

def main():
    print("=" * 72)
    print("COST & LATENCY BUDGETS: profile, then optimize the dominant stage")
    print("=" * 72 + "\n")

    cache: Dict[str, str] = {}

    print("Budget: ≤ 2000 ms  ·  ≤ $0.020 per request\n")
    print("-" * 72)

    print("1) A HARD request (long prompt):")
    b1 = Budget()
    out1 = run_pipeline("Explain how RAG retrieval scoring works in detail",
                        cache, b1)
    show("hard request", out1)

    print("-" * 72)
    print("2) The SAME request again (cache hit):")
    b2 = Budget()
    out2 = run_pipeline("Explain how RAG retrieval scoring works in detail",
                        cache, b2)
    show("cached repeat", out2)

    print("-" * 72)
    print("3) A SIMPLE request (routed to a cheap model):")
    b3 = Budget()
    out3 = run_pipeline("What's the weather?", cache, b3)
    show("simple request", out3)

    print("=" * 72)
    print("WHAT THE NUMBERS SHOW")
    print("=" * 72)
    gen_hard = [s for s in out1["budget"].stages if s[0] == "generate_hard"]
    gen_ms = gen_hard[0][1] if gen_hard else 0.0
    gen_cost = gen_hard[0][2] if gen_hard else 0.0
    print(f"""
  · generate_hard dominates: {gen_ms:.0f} ms, ${gen_cost:.4f} — the single
    biggest stage. That is where optimization effort belongs.
  · cache hit collapsed the whole request to {out2['budget'].latency_used:.0f} ms, ${out2['budget'].cost_used:.4f}
  · routing sent the simple case to a cheaper path

  OPTIMIZATION ORDER (never skip to the bottom):
    1. Cache        → eliminate the call
    2. Route        → cheap model for easy work
    3. Reduce       → trim context
    4. Parallelize  → independent calls together
    5. Downgrade    → smaller model (last resort)

  Most teams start at 5 and lose quality they didn't need to lose.
""")


if __name__ == "__main__":
    main()
