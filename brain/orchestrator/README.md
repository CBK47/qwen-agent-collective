# brain/orchestrator

n8n workflow definitions that wire agents to the shared brain.

## Responsibilities

- Route inter-agent events
- Trigger agents on schedule or external webhook
- Write shared brain updates atomically

## Files

n8n workflow JSON exports live here. Import via the n8n UI or the n8n CLI.

## Docker Compose Setup

Ensure Docker and Docker Compose are installed on your system.

1. Create a `.env` file in this directory with the required environment variables. Example:

```env
# Postgres configuration
POSTGRES_DB=brain
POSTGRES_USER=brain_user
POSTGRES_PASSWORD=brain_pass

# Qdrant configuration
QDRANT_API_KEY=your_api_key

# n8n configuration
N8N_BASIC_AUTH_USER=admin
N8N_BASIC_AUTH_PASSWORD=secret
```

2. Start the services with:

```bash
docker compose up -d
```

3. Verify all services are healthy by checking the status:

```bash
docker compose ps
```

Each service should show `healthy` in the status column.

4. To check logs for any issues:

```bash
docker compose logs
```
