# brain/db

Postgres and Qdrant definitions for the shared brain.

## Postgres

Stores structured data: agent facts, event log, inter-agent messages, and glossary entries.

Schema files go here (`.sql` migrations or an ORM equivalent).

## Qdrant

Vector store for semantic recall. Collections mirror the namespace contract defined in [../../shared/](../../shared/).

Connection vars: `POSTGRES_*` and `QDRANT_*` in `.env.example` at repo root.
