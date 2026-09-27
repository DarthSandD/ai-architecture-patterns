"""
Pattern 05 — Evals
==================

A tiny eval harness with three scorer types and a baseline gate.
Shows the point most demos miss: the value is the DIFF vs baseline,
not the raw score.

Stdlib only. Run:
    python demo.py
"""

from dataclasses import dataclass
from typing import Callable
import re

# ---------------------------------------------------------------------------
# TEST CASES  (inputs + expected)
# ---------------------------------------------------------------------------

@dataclass
class Case:
    input: str
    expected: str


TEST_SET = [
    Case("capital of France", "Paris"),
    Case("2 + 2", "4"),
    Case("color of sky", "blue"),
    Case("largest ocean", "Pacific"),
]


# ---------------------------------------------------------------------------
# SYSTEMS UNDER TEST  (a "good" one and a "regressed" one)
# ---------------------------------------------------------------------------

def system_good(prompt: str) -> str:
    answers = {
        "capital of France": "The capital of France is Paris.",
        "2 + 2": "The answer is 4.",
        "color of sky": "The sky is blue during the day.",
        "largest ocean": "The Pacific Ocean is the largest.",
    }
    return answers.get(prompt, "I don't know.")


def system_regressed(prompt: str) -> str:
    """A version where someone broke the math case."""
    answers = {
        "capital of France": "The capital of France is Paris.",
        "2 + 2": "The answer is 5.",          # ← regression
        "color of sky": "The sky is blue during the day.",
        "largest ocean": "The Pacific Ocean is the largest.",
    }
    return answers.get(prompt, "I don't know.")


# ---------------------------------------------------------------------------
# SCORERS  (cheapest first)
# ---------------------------------------------------------------------------

def exact_match(output: str, expected: str) -> bool:
    return output.strip().lower() == expected.strip().lower()


def contains(output: str, expected: str) -> bool:
    return expected.strip().lower() in output.strip().lower()


def rubric_word_count(output: str, expected: str) -> bool:
    """Example rubric: answer must be present AND under 12 words."""
    return contains(output, expected) and len(output.split()) <= 12


SCORERS = {
    "exact": exact_match,
    "contains": contains,
    "rubric": rubric_word_count,
}


# ---------------------------------------------------------------------------
# RUNNER
# ---------------------------------------------------------------------------

def run_eval(system: Callable[[str], str], scorer_name: str) -> float:
    scorer = SCORERS[scorer_name]
    passed = sum(1 for c in TEST_SET if scorer(system(c.input), c.expected))
    return passed / len(TEST_SET)


def report(label: str, score: float, baseline: float | None) -> str:
    line = f"  {label:<28} {score * 100:5.0f}%"
    if baseline is not None:
        diff = (score - baseline) * 100
        arrow = "→" if diff == 0 else ("▼" if diff < 0 else "▲")
        line += f"   {arrow} {diff:+.0f}pp vs baseline"
    return line


# ---------------------------------------------------------------------------
# DEMO
# ---------------------------------------------------------------------------

def main():
    print("=" * 72)
    print("EVALS: the score matters less than the diff")
    print("=" * 72 + "\n")

    print(f"Test set: {len(TEST_SET)} cases\n")

    # Establish the baseline
    print("Scorer: 'contains' (must include the expected answer)")
    baseline = run_eval(system_good, "contains")
    print(report("good version", baseline, None))
    print()

    # Compare a change against the baseline
    print("After a change (someone edited the math path):")
    regressed = run_eval(system_regressed, "contains")
    print(report("regressed version", regressed, baseline))
    print()

    if regressed < baseline:
        print("  ❌ REGRESSION DETECTED — this change would be blocked in CI.")
    else:
        print("  ✅ No regression — safe to merge.")
    print()

    # Show how scorer choice changes the picture
    print("-" * 72)
    print("Same system, different scorers:")
    for name in SCORERS:
        s = run_eval(system_good, name)
        print(f"  {name:<10} → {s * 100:.0f}%")
    print("\n  The scorer you pick IS the metric. Choose deliberately.")
    print()

    print("=" * 72)
    print("THE EVAL PYRAMID (run the bottom on every commit)")
    print("=" * 72)
    print("""
        ▲  Human review        (rare, high-stakes)
       ███  Model judge        (subjective quality)
      █████  Rubric/contains   (structure + facts)
     ███████  Exact/unit tests (cheap, always-on)

  Every production bug becomes a new eval case.
""")


if __name__ == "__main__":
    main()
