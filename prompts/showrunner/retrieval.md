# showrunner — Retrieval Prompt

## Token Budget
Reserved for retrieved context: **900 tokens maximum**. Episodes need enough raw material to be grounded; this budget supports ~6–8 event summaries plus light shared-memory context.

## Query Formation
showrunner uses two retrieval strategies:

1. **Event scan** (SQL, not vector): direct time-window query against `memory_events`.
   ```sql
   SELECT event_id, agent_id, event_type, title, event_text, event_time
   FROM memory_events
   WHERE event_time >= <window_start>
   ORDER BY event_time DESC
   LIMIT 30;
   ```
   This is the primary source. Run it first.

2. **Context enrichment query** (vector): for each selected story beat, form a query to pull background:
   - `<agent_name> <event_title keywords> context`
   - Example: "git-committer auth-service security block context"
   - Run against `shared_reference` (Qdrant) to surface any relevant shared facts that give the event meaning.

## Retrieval Order (Priority)

| Priority | Source | Use |
|----------|--------|-----|
| 1 | `memory_events` (Postgres, all agents) | Story beats — primary raw material |
| 2 | `shared.*` (Qdrant: `shared_reference`, `shared_policies`) | Context enrichment for selected beats |
| 3 | `showrunner.private` (Postgres `fact_type = 'episode'`) | Continuity check — what was covered in last episode |
| 4 | Agent-specific `memory_facts` (read-only) | Character detail for a specific agent's action |

Stop adding results once the 900-token budget is reached. Events take priority over context enrichment.

## Ranking and Selection

**For events (Step 1 results):**
Rank by narrative weight heuristic — not a formula, a checklist:
- Does it involve more than one agent? +2 points.
- Does it involve a conflict or refusal? +2 points.
- Does it close or open a significant project thread? +1 point.
- Is it the first or last occurrence of its `event_type` in the window? +1 point.

Select the top 3–6 events by this score.

**For context enrichment (Step 2 results):**
```
score = (0.6 × vector_similarity) + (0.4 × recency_score)
```
Drop results with `vector_similarity < 0.60`. Take at most 2 enrichment chunks per story beat.

**For continuity check (Step 3):**
Pull the most recent episode fact. Compare `source events` to avoid re-narrating the same events in consecutive episodes.

## Using Retrieved Context
- Ground every narrative claim in a real `event_id`. Do not invent or extrapolate events.
- Use context enrichment to explain *why* an event matters, not to add plot.
- If the last episode's event IDs overlap heavily with the current window: either extend the time window or flag that there is not enough new material for a fresh episode.
- Omit any `event_text` content that contains raw credentials, API keys, or personal identifiers — abstract to "[sensitive detail omitted]".

## No-Result Handling
If `memory_events` returns fewer than 3 events in the target window: "Not enough activity in the last [period] to produce a full episode. I can produce a short dispatch instead, or wait for more events." Do not generate a padded episode.
