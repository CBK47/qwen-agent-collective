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

## Alibaba Cloud Deployment

1. **Configure Required Environment Variables**:  
   In the `agents/memory-echo` directory, update the `.env` file with your Alibaba Cloud credentials and DashScope API key:  
   ```env
   ALIBABA_CLOUD_ACCESS_KEY_ID=your_access_key_id
   ALIBABA_CLOUD_ACCESS_KEY_SECRET=your_access_key_secret
   ALIBABA_CLOUD_REGION=cn-hangzhou
   DASHSCOPE_API_KEY=your_api_key_here
   ```

2. **Deploy to Alibaba Cloud**:  
   Run the deployment script:  
   ```bash
   python deploy.py --cloud alibaba
   ```

3. **Verification**:  
   Access the WebUI at the public IP or domain provided by Alibaba Cloud (e.g., `http://<public-ip>:3000`). Test memory ingestion and retrieval to confirm successful deployment.

## WebUI Usage

After starting the brain stack, access the WebUI at `http://localhost:3000`. The interface includes:

- **Memory Input Form**: Enter raw text to store as a memory. The system automatically embeds and stores it in the `echo.private` namespace.

- **Search Interface**: Type queries to retrieve relevant memories. Results are ranked and summarized by the Qwen model before display.

- **Namespace Viewer**: Browse stored memories in `echo.private` and view read-only entries from `shared.*` namespaces.

- **Demo Mode**: A guided tour of features for new users, ideal for demo presentations.

The demo video demonstrates these interactive features with real-world examples.

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
