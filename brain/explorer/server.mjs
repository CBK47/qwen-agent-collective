import express from "express";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { execSync } from "node:child_process";
import fs from "node:fs";
import dotenv from "dotenv";
import { createDashScopeClient } from "../../shared/dashscope.mjs";
import { createQdrantClient } from "../../shared/qdrant.mjs";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
dotenv.config({ path: path.resolve(__dirname, "../../.env") });

const PORT = 3456;
const qwen = createDashScopeClient();

const qdrant = createQdrantClient();
try {
  await qdrant.createCollection('brain', {
    vectors: {
      size: 1024,
      distance: 'Cosine'
    }
  });
} catch (e) {
  if (e.message.includes('already exists')) {
    console.log('Qdrant collection "brain" already exists');
  } else {
    console.error('Error creating Qdrant collection:', e);
  }
}

const app = express();
app.use(express.json());
app.use(express.static(__dirname));

app.post("/api/search", async (req, res) => {
  try {
    const { query, agent, context } = req.body;
    if (!query) return res.status(400).json({ error: "Query is required" });
    const systemInstruction = `You are ${agent.name}, a cognitive agent with the role: ${agent.role}.
Bio: ${agent.bio}.

You have access to the following local agent memory records (context) from namespaces [${agent.namespaces.join(", ")}]:
${JSON.stringify(context, null, 2)}

Guidelines:
1. Answer the query by combining your local agent memory records with real-time web search.
2. If the query needs up-to-date facts, device specs, release dates, or external knowledge, ground your answer using web search.
3. Synthesize beautifully in your professional persona. Keep it focused and concise.
4. Do not dump raw markdown URLs in the body; keep it clean.`;

    const data = await qwen.chat({
      messages: [
        { role: "system", content: systemInstruction },
        { role: "user", content: query },
      ],
      enable_search: true,
      search_options: { enable_source: true, enable_citation: true },
      metadata: { surface: "brain-explorer", agent: agent.name },
    });

    const text = data.choices?.[0]?.message?.content || "";
    const results = data.choices?.[0]?.message?.search_results
      || data.search_info?.search_results || [];
    const chunks = results.map(s => ({ web: { uri: s.url || s.uri, title: s.title } }));
    const searchQueries = (data.search_info?.search_queries || []).map(q => q.text || q);

    res.json({ text, chunks, searchQueries });
  } catch (err) {
    console.error("Qwen search error:", err);
    res.status(500).json({ error: err.message || "Internal server error" });
  }
});

app.get("/api/git-log", (_req, res) => {
  try {
    const raw = execSync(
      'git log --pretty=format:"%H|%h|%ar|%s|%an" -30',
      { cwd: REPO }
    ).toString().trim();
    const commits = raw.split("\n").filter(Boolean).map(l => {
      const [hash, shortHash, when, ...rest] = l.split("|");
      const author = rest.pop() || "";
      const message = rest.join("|");
      return { hash, shortHash, when, message, author };
    });
    res.json({ commits });
  } catch (e) {
    res.json({ commits: [], error: e.message });
  }
});

app.get("/api/latest-report", (_req, res) => {
  try {
    const raw = execSync(
      'find reports/qwen-worker reports/local-worker -name "*.md" 2>/dev/null | sort | tail -1',
      { cwd: REPO }
    ).toString().trim();
    if (!raw) return res.json({ content: "", path: "" });
    const content = fs.readFileSync(path.join(REPO, raw), "utf8");
    res.json({ content, path: raw });
  } catch (e) {
    res.json({ content: "", path: "", error: e.message });
  }
});

app.listen(PORT, "0.0.0.0", () => console.log(`Brain Explorer on http://localhost:${PORT}`));
