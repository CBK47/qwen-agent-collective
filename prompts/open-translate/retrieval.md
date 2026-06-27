# open-translate — Retrieval Prompt

## Token Budget
Reserved for retrieved context: **700 tokens maximum**. Glossary entries are compact; this fits ~40–60 term pairs. Prioritise glossary over segment history.

## Query Formation
Form two retrieval queries before translating:

1. **Glossary query**: `glossary [source_lang] [target_lang] [domain]`
   - Derive `domain` from content keywords (e.g., "legal", "medical", "UI", "marketing").
   - Example: "glossary EN ZH-CN UI software"

2. **Segment memory query**: top 3–5 noun phrases from the source text + `translation memory [target_lang]`
   - Example: "privacy policy data retention translation memory ZH-CN"

## Retrieval Order (Priority)

| Priority | Source | Use |
|----------|--------|-----|
| 1 | `shared.glossary` (Postgres `status = 'approved'`, Qdrant `shared_reference`) | Mandatory term lookup |
| 2 | `open-translate.private` — project glossary (`fact_type = 'glossary_term'`) | Project-specific overrides |
| 3 | `open-translate.private` — segment history (`fact_type = 'translation_segment'`) | Fuzzy segment reuse |
| 4 | `shared.*` (other) | Background context only; use only if budget allows |

Stop once the 700-token budget is reached.

## Ranking Within Each Source
```
score = (0.5 × term_similarity) + (0.3 × recency_score) + (0.2 × confidence)
```
- For glossary entries: exact string match on `subject` scores 1.0 term_similarity, overrides score formula.
- Drop results with `term_similarity < 0.50` for fuzzy segment matches.
- Glossary entries with `confidence >= 0.90` are treated as authoritative; do not override them.

## Applying Retrieved Context
- Authoritative glossary terms: apply verbatim; do not paraphrase.
- Fuzzy segment matches (similarity 0.80–0.99): use as a reference; note the match score internally and adjust confidence accordingly.
- Segment matches below 0.80: treat as hints only; do not inflate the translation confidence.
- Project glossary overrides `shared.glossary` when both have an entry for the same term — use the project-specific one and log the conflict.

## No-Result Handling
If `shared.glossary` returns nothing for a term that appears domain-specific, flag it as `[TERM:REVIEW]` in the output and add a candidate to `memory_review_queue`. Do not silently use a model-generated translation for flagged terms.
