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

1. Copy the `.env.example` file to `.env`:

```bash
cp .env.example .env
```

2. Open the `.env` file and set the required environment variables, including `DASHSCOPE_API_KEY`. Example:

```env
# Postgres configuration
POSTGRES_DB=brain
POSTGRES_USER=brain_user
POSTGRES_PASSWORD=brain_pass

# Qdrant configuration
QDRANT_API_KEY=your_api_key

# DASHSCOPE configuration
DASHSCOPE_API_KEY=your_dashscope_api_key

# n8n configuration
N8N_BASIC_AUTH_USER=admin
N8N_BASIC_AUTH_PASSWORD=secret
```

**Note:** Replace all placeholder values (e.g., `your_api_key`, `your_dashscope_api_key`) with your actual credentials.

The services use the following ports:

- Postgres: 5432
- Qdrant: 6333
- n8n: 5678

3. Start the services with:

```bash
docker compose up -d
```

4. Verify all services are healthy by checking the status:

```bash
docker compose ps
```

Each service should show `healthy` in the status column.

5. To check logs for any issues:

```bash
docker compose logs
```
