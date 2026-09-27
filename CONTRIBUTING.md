# Pattern Template

Copy this folder to `patterns/NN-your-pattern/` and fill it in.

A pattern is only merged if it has **all four** elements. A pattern without a
"When NOT to use it" section is a sales pitch, not an architecture doc.

---

## Required structure

```
patterns/NN-your-pattern/
├── README.md     # the four elements below
└── demo.py       # runnable in under 5 minutes, minimal deps
```

## README.md must contain

### 1. What is it?
One diagram (ASCII is fine) + a two-line explanation. If it takes a paragraph
to say what it is, the pattern is too vague.

### 2. When do I use it?
A checklist of concrete conditions. Not "when you need scale" — name the signal.

### 3. When do I NOT use it?  ← mandatory
At least three real conditions where this pattern is the *wrong* choice.
Name the failure mode it causes.

### 4. The tradeoffs
A table: latency, cost, complexity, failure surface. Every pattern has a price.

## demo.py rules

- Runs with `python demo.py`
- Minimal dependencies (prefer stdlib)
- No API keys required to understand the shape
- Prints output that demonstrates the pattern's value
- Under ~150 lines

## Quality bar

- Diagram before code
- Name the failure mode, not just the happy path
- No hype words ("revolutionary", "blazing fast")
- If a claim can't be measured, don't make it
