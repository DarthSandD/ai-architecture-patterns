# AI Architecture Patterns

**A visual design library for AI systems — diagrams, tradeoffs, and the part everyone skips.**

Most AI repos show you *how to code it*. Almost none show you *how to design it* — or when not to.

This is that library. One folder per pattern. Each one gives you:

| Element | What you get |
|---------|-------------|
| **Diagram** | The system shape, at a glance |
| **Tradeoffs** | Latency vs accuracy vs cost vs complexity |
| **Runnable demo** | Under 100 lines, runs in under 5 minutes |
| **When NOT to use it** | The failure modes nobody documents |

---

## Patterns

| # | Pattern | The confusion it solves |
|---|---------|------------------------|
| 01 | [RAG](./patterns/01-rag/) | "When do I need retrieval, and when is it just a prompt?" |
| 02 | [Tool Use](./patterns/02-tool-use/) | "How do I let a model take actions safely?" |
| 03 | [Multi-Agent](./patterns/03-multi-agent/) | "Do I actually need multiple agents, or one good loop?" |
| 04 | [Memory](./patterns/04-memory/) | "Where does state live across turns?" |
| 05 | [Evals](./patterns/05-evals/) | "How do I know it got worse?" |
| 06 | [Guardrails](./patterns/06-guardrails/) | "How do I stop bad outputs before they ship?" |
| 07 | [Context Engineering](./patterns/07-context-engineering/) | "Why does it forget the middle of my prompt?" |
| 08 | [Cost & Latency Budgets](./patterns/08-cost-latency-budgets/) | "Why is this slow and expensive?" |

---

## How to read this

Each pattern answers three questions in order:

1. **What is it?** — the shape, in one diagram
2. **When do I use it?** — the conditions that make it right
3. **When do I NOT?** — the conditions that make it wrong

If a pattern doesn't clearly earn its place, it's not in here.

---

## Who this is for

- Engineers moving from "I called an LLM" to "I designed a system"
- Architects who need to explain *why* a design was chosen
- Anyone who has shipped an AI feature and watched it fail in production

---

## Principles

**1. Design before code.** A diagram catches a bad idea faster than 500 lines of Python.

**2. Every pattern has a cost.** There is no free abstraction. Each pattern page names the price.

**3. Complexity must earn itself.** Start with the simplest thing that works. Add a pattern only when you can name the failure it fixes.

**4. "When not to use" is mandatory.** A pattern without documented failure modes is a sales pitch, not an architecture.

---

## Contributing

Adding a pattern? It must include all four elements (diagram, tradeoffs, runnable demo, when-not-to-use). A pattern without a "when not to use" section will not be merged.

---

## License

MIT — use it, fork it, teach with it.
