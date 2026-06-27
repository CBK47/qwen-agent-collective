
CREATE TABLE IF NOT EXISTS agents (
  agent_id TEXT PRIMARY KEY,
  agent_slug TEXT UNIQUE NOT NULL,
  display_name TEXT NOT NULL,
  description TEXT,
  system_prompt_path TEXT,
  retrieval_prompt_path TEXT,
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS users (
  user_id TEXT PRIMARY KEY,
  external_id TEXT,
  display_name TEXT NOT NULL,
  profile_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS sessions (
  session_id TEXT PRIMARY KEY,
  agent_id TEXT NOT NULL,
  user_id TEXT NOT NULL,
  channel TEXT,
  source_app TEXT,
  started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  ended_at TIMESTAMPTZ,
  title TEXT,
  summary_short TEXT,
  summary_long TEXT,
  tags_json JSONB NOT NULL DEFAULT '[]'::jsonb
);

CREATE TABLE IF NOT EXISTS messages (
  message_id BIGSERIAL PRIMARY KEY,
  session_id TEXT NOT NULL,
  role TEXT NOT NULL,
  content_text TEXT,
  content_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  token_count INTEGER,
  source_ref TEXT
);

CREATE TABLE IF NOT EXISTS memory_facts (
  fact_id BIGSERIAL PRIMARY KEY,
  agent_id TEXT NOT NULL,
  user_id TEXT,
  memory_namespace TEXT NOT NULL,
  fact_type TEXT NOT NULL,
  subject TEXT,
  predicate TEXT,
  object_text TEXT,
  confidence NUMERIC(4,3),
  source_session_id TEXT,
  source_note_path TEXT,
  status TEXT NOT NULL DEFAULT 'approved',
  expires_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS memory_events (
  event_id BIGSERIAL PRIMARY KEY,
  agent_id TEXT NOT NULL,
  user_id TEXT,
  event_type TEXT NOT NULL,
  title TEXT,
  event_text TEXT,
  event_time TIMESTAMPTZ,
  source_session_id TEXT,
  metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS memory_review_queue (
  candidate_id BIGSERIAL PRIMARY KEY,
  agent_id TEXT NOT NULL,
  session_id TEXT NOT NULL,
  candidate_type TEXT NOT NULL,
  payload_json JSONB NOT NULL,
  confidence NUMERIC(4,3),
  status TEXT NOT NULL DEFAULT 'pending',
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  reviewed_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS projects (
  project_id BIGSERIAL PRIMARY KEY,
  agent_scope TEXT,
  project_slug TEXT UNIQUE NOT NULL,
  title TEXT NOT NULL,
  description TEXT,
  metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS people (
  person_id BIGSERIAL PRIMARY KEY,
  agent_scope TEXT,
  display_name TEXT NOT NULL,
  role_title TEXT,
  metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS devices (
  device_id BIGSERIAL PRIMARY KEY,
  agent_scope TEXT NOT NULL DEFAULT 'skippy',
  device_slug TEXT UNIQUE NOT NULL,
  display_name TEXT NOT NULL,
  room_name TEXT,
  device_type TEXT,
  metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS source_registry (
  source_id BIGSERIAL PRIMARY KEY,
  source_type TEXT NOT NULL,
  source_path TEXT,
  checksum TEXT,
  last_ingested_at TIMESTAMPTZ,
  agent_scope TEXT,
  metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS retrieval_feedback (
  feedback_id BIGSERIAL PRIMARY KEY,
  agent_id TEXT NOT NULL,
  session_id TEXT,
  query_text TEXT,
  rating INTEGER,
  notes TEXT,
  metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_memory_facts_namespace_status_updated
  ON memory_facts (memory_namespace, status, updated_at DESC);

CREATE INDEX IF NOT EXISTS idx_sessions_agent_user_started
  ON sessions (agent_id, user_id, started_at DESC);

CREATE INDEX IF NOT EXISTS idx_review_queue_agent_status_created
  ON memory_review_queue (agent_id, status, created_at DESC);

-- ─────────────────────────────────────────────────────────────────────────────
-- MEMORY NAMESPACE CONVENTIONS
-- ─────────────────────────────────────────────────────────────────────────────
-- Private agent memory:  agent_id = 'echo'|'skippy',  memory_namespace = 'private'
-- Shared architecture:   agent_id = 'shared',         memory_namespace = 'architecture'
-- Shared project state:  agent_id = 'shared',         memory_namespace = 'projects'
-- Shared people/orgs:    agent_id = 'shared',         memory_namespace = 'people'
--
-- Rules:
--   - Only the owning agent writes to its 'private' namespace.
--   - All agents can READ any 'shared.*' namespace.
--   - All agents can WRITE to 'shared.*' namespaces (with review queue approval).
--   - Qdrant collections mirror this: echo_private, skippy_private, shared
-- ─────────────────────────────────────────────────────────────────────────────

INSERT INTO agents (agent_id, agent_slug, display_name, description, system_prompt_path, retrieval_prompt_path)
VALUES
  ('echo',   'echo',   'Echo',   'Primary collaboration agent',       'prompts/echo/system.md',   'prompts/echo/retrieval.md'),
  ('skippy', 'skippy', 'Skippy', 'Home-ops and banter agent',         'prompts/skippy/system.md', 'prompts/skippy/retrieval.md'),
  ('shared', 'shared', 'Shared', 'Cross-agent shared knowledge store', NULL, NULL)
ON CONFLICT (agent_id) DO NOTHING;

INSERT INTO users (user_id, external_id, display_name, profile_json)
VALUES ('connor', 'connor', 'Connor', '{"source":"seed"}'::jsonb)
ON CONFLICT (user_id) DO NOTHING;
