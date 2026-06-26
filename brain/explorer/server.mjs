// Brain Explorer server: static UI + one grounded-recall endpoint backed by
// the Qwen/DashScope spine (OpenAI-compatible, so a plain fetch — no SDK).
import express from "express";
import path from "node:path";
import { fileURLToPath } from "node:url";
import dotenv from "dotenv";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
// Key/models live in the repo-root .env (shared with the Python spine).
dotenv.config({ path: path.resolve(__dirname, "../../.env") });

const PORT = 3000;
const BASE_URL = process.env.DASHSCOPE_BASE_URL
  || "https://dashscope-intl.aliyuncs.com/compatible-mode/v1";
const MODEL = process.env.QWEN_CHAT_MODEL || "qwen-plus";

const app = express();
app.use(express.json());
app.use(express.static(__dirname));

app.post("/api/search", async (req, res) => {
  try {
    const { query, agent, context } = req.body;
    if (!query) return res.status(400).json({ error: "Query is required" });
    const apiKey = process.env.DASHSCOPE_API_KEY;
    if (!apiKey) return res.status(500).json({ error: "DASHSCOPE_API_KEY is not configured in the server .env." });

    const systemInstruction = `You are ${agent.name}, a cognitive agent with the role: ${agent.role}.
Bio: ${agent.bio}.

You have access to the following local agent memory records (context) from namespaces [${agent.namespaces.join(", ")}]:
${JSON.stringify(context, null, 2)}

Guidelines:
1. Answer the query by combining your local agent memory records with real-time web search.
2. If the query needs up-to-date facts, device specs, release dates, or external knowledge, ground your answer using web search.
3. Synthesize beautifully in your professional persona. Keep it focused and concise.
4. Do not dump raw markdown URLs in the body; keep it clean.`;

    // DashScope OpenAI-compatible endpoint. enable_search = Qwen's web grounding.
    const r = await fetch(`${BASE_URL}/chat/completions`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${apiKey}` },
      body: JSON.stringify({
        model: MODEL,
        messages: [
          { role: "system", content: systemInstruction },
          { role: "user", content: query },
        ],
        enable_search: true,
        search_options: { enable_source: true, enable_citation: true },
      }),
    });

    const data = await r.json();
    if (!r.ok) throw new Error(data.error?.message || data.message || `DashScope HTTP ${r.status}`);

    const text = data.choices?.[0]?.message?.content || "";
    // ponytail: this compatible endpoint doesn't return citation chunks; map
    // them if a future endpoint/model does, else the UI hides the source cards.
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

app.listen(PORT, "0.0.0.0", () => console.log(`Brain Explorer on http://localhost:${PORT}`));
