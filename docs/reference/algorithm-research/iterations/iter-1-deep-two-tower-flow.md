# Deep Two-Tower for Mesh — data flow

## End-to-end (4 lines)

1. **Input**: user features `{frictions, capabilities, history, excluded_tools}` + tool features `{description, integrates_with, capabilities, cadence, pricing}` — embedded (text→vector) and concatenated with categoricals.
2. **Towers**: each side passes through a 3-layer MLP (e.g. 512→256→128) → produces `user_embed` and `tool_embed` (same dimension).
3. **Head**: `dot(user_embed, tool_embed)` → sigmoid → `P(adopt | user, tool)` ∈ [0,1]; trained on labeled `(user, tool, adopted=0/1)` pairs with BCE loss.
4. **Output**: at serve time, score user against all 300 tools, return top-K by P(adopt) → fed to iter-12 rerank.

## Diagram

```
user features ─▶ MLP(512→256→128) ─▶ user_embed ┐
                                                 ├─▶ dot ─▶ sigmoid ─▶ P(adopt)
tool features ─▶ MLP(512→256→128) ─▶ tool_embed ┘
```

## Mesh fit

- **Strength**: trainable end-to-end on adoption labels; ingests structured features (not just text); Mesh controls the schema at inception.
- **Limit**: needs ≥1k labeled `(user, tool, adopted)` pairs before the sigmoid head learns anything useful — bootstrap via LLM-judged synthetic labels, then transition to real adoption data from iter-10 logging.
- **Slot**: V1.5 trunk replacing/augmenting iter-5 retrieval once labels accumulate; iter-2 feeds user features, iter-12 reranks top-K.
