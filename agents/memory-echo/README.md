# memory-echo

**Track:** Track 1 - MemoryAgent

## Purpose

Ingests, embeds, and retrieves personal memories. The reference agent for the shared brain - demonstrates read/write across both Qdrant (vector recall) and Postgres (structured facts).

## Setup Instructions

1. **Configure API Key**:  
   In the `agents/memory-echo` directory, create a `.env` file containing your DashScope API key:  
   ```env
   DASHSCOPE_API_KEY=your_api_key_here
   ```

2. **Initialize Brain Stack**:  
   Navigate to the `brain` directory and start the Docker services:  
   ```bash
   cd brain
   docker-compose up -d
   ```

## Signature Qwen Call

```
Model: text-embedding-v3 (QWEN_EMBED_MODEL)
Input: raw memory text
Output: vector written to Qdrant namespace echo.private
```

For retrieval, a follow-up call to `qwen-plus` ranks and summarises matched memories before returning them to the user.

## Brain Namespaces

| Namespace | Access | Contents |
|---|---|---|
| `echo.private` | read/write | Personal memories and embeddings |
| `shared.*` | read | Glossary, agent events, cross-agent facts |
