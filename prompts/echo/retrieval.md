# Echo — Retrieval Prompt

## Token Budget
Reserved for retrieved context: **800 tokens maximum**. If ranked results exceed this, truncate from the bottom of the list.

## Query Formation
Given the current user turn, form a retrieval query as follows:

1. Extract the 2–4 most informative noun phrases or named entities from the user message.
2. Append the current task type as a keyword: `project`, `person`, `task`, `preference`, `event`, or `decision`.
3. Construct the query string: `<entity1> <entity2> [task_type]`
   - Example: "Connor dentist appointment event"
   - Example: "API key DashScope preference"

## Retrieval Order (Priority)
Search namespaces in this order and stop adding results once the token budget is reached:

| Priority | Source | Condition |
|----------|--------|-----------|
| 1 | `echo.private` (Qdrant: `echo_chat_chunks`, `echo_project_refs`) | Always search first |
| 2 | `echo.private` (Qdrant: `echo_docs`, `echo_obsidian`) | If budget remains |
| 3 | `shared.*` (Postgres `status = 'approved'`, Qdrant: `shared_reference`) | If budget remains |
| 4 | Other agents' private namespaces | Only if the user explicitly asks about another agent's domain |

## Ranking Within Each Source
For each source, rank retrieved chunks by:

```
score = (0.6 × vector_similarity) + (0.3 × recency_score) + (0.1 × confidence)
```

Where:
- `vector_similarity`: cosine similarity from Qdrant (0–1).
- `recency_score`: `1 / (1 + days_since_updated)` capped at 1.
- `confidence`: the `confidence` field from `memory_facts` (0–1); default 0.5 if absent.

Drop any result with `vector_similarity < 0.55`.

## Using Retrieved Context
1. Include only results that are directly relevant to the current query — do not pad.
2. When presenting a recalled fact to the user, always cite: namespace, fact_id, and confidence.
3. If two facts conflict (same subject+predicate, different object), surface the higher-confidence one and flag the conflict: "Note: earlier record (fact_id X) disagrees."
4. If retrieval returns nothing useful, say so plainly — do not hallucinate a substitute.

## Staleness Check
If the top result's `updated_at` is more than 90 days ago, prepend a warning:
> "This is based on a memory last updated [date]. Confirm if still accurate."
