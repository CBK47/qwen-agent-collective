# git-committer — Retrieval Prompt

## Token Budget
Reserved for retrieved context: **600 tokens maximum**. Conventions are short facts; this budget is enough for ~15–20 rules.

## Query Formation
Before starting a review, form two retrieval queries:

1. **Convention query**: `code convention [language] [framework]`
   - Derive `language` and `framework` from the diff file extensions and imports.
   - Example: "code convention Python FastAPI"

2. **Verdict history query**: `pr verdict [repo-slug or topic]`
   - Use any repo name or topic visible in the diff context.
   - Example: "pr verdict auth-service"

Run both queries against the brain before the panel begins deliberating.

## Retrieval Order (Priority)

| Priority | Source | Reviewer Lane |
|----------|--------|---------------|
| 1 | `shared.code-conventions` (Qdrant: `shared_reference`) | rev-style, rev-test |
| 2 | `git-committer.private` (Postgres `fact_type = 'pr_verdict'`) | all (precedent check) |
| 3 | `shared.policies` (Qdrant: `shared_policies`) | rev-sec |

Stop adding results once the 600-token budget is reached.

## Ranking Within Each Source
```
score = (0.7 × vector_similarity) + (0.3 × recency_score)
```
- Drop results with `vector_similarity < 0.60`.
- For convention facts, recency matters less; boost any fact with `confidence >= 0.85` by +0.05.

## Using Retrieved Context
- Feed conventions to `rev-style` and `rev-test` at the top of their reasoning block.
- Feed security policies to `rev-sec`.
- Feed precedent verdicts to the panel as a whole to check for consistency ("we rejected this pattern in PR #47").
- Do not pad the review with retrieved context — cite only what is directly relevant to a finding.
- If no conventions are found for the given language/framework, say so in the `rev-style` block and apply general best practices explicitly.

## No-Result Handling
If retrieval returns nothing for conventions: `rev-style` notes "No stored conventions found; applying general principles." and proceeds. Do not block the review.
