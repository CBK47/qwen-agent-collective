# DGX verification handoff — Track-1 demo

The branch `port-brain-from-agents` is pushed. Everything except the Postgres-backed
demo has been verified on the Mac. Docker isn't running locally, so the Track-1 demo
needs to run on the DGX (where Docker is up).

## Task for the DGX agent

1. Clone/pull and check out the branch:
   ```bash
   git fetch origin
   git checkout port-brain-from-agents
   ```

2. Run the demo:
   ```bash
   cd brain/demo && bash run.sh
   ```

3. **Pass criteria** — `run.sh` exits 0 and the output shows all three beats:
   - `Beat 1 PASSED` — ACCUMULATE (governed review queue: 3 approved, 1 rejected, 1 pending)
   - `Beat 2 PASSED` — FORGET (prune_expired removes stale facts)
   - `Beat 3 PASSED` — RECALL (token-budget-gated, ordered by confidence)
   - final banner `ALL BEATS PASSED`

   Any `AssertionError` = fail; capture full output and report.

4. Tear down:
   ```bash
   docker compose -f docker-compose.demo.yml down -v
   ```

## Notes
- `run.sh` pulls `postgres:16`, installs `requirements.txt` (psycopg2), waits for the
  `brain_demo_postgres` healthcheck, then runs `track1_demo.py`. No model/n8n needed.
- The compose file has an obsolete `version:` key that prints a harmless warning.
- Schema lives in `brain/db/postgres-init.sql`; demo logic in `track1_demo.py` /
  `brain_client.py` / `seed_facts.py`.

## Reporting back
State pass/fail per beat and paste the final banner. If it fails, include the
failing assertion line and the surrounding output.
