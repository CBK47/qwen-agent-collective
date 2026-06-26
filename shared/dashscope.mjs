const DEFAULT_BASE_URL = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1";
const DEFAULT_CHAT_MODEL = "qwen-plus";

export class DashScopeNodeError extends Error {
  constructor(message, detail = {}) {
    super(message);
    this.name = "DashScopeNodeError";
    this.detail = detail;
  }
}

export function loadDashScopeConfig(env = process.env) {
  return {
    apiKey: env.DASHSCOPE_API_KEY,
    baseUrl: env.DASHSCOPE_BASE_URL || DEFAULT_BASE_URL,
    chatModel: env.QWEN_CHAT_MODEL || DEFAULT_CHAT_MODEL,
    timeoutMs: Number(env.QWEN_TIMEOUT_MS || "30000"),
  };
}

export function createDashScopeClient(config = loadDashScopeConfig()) {
  return {
    config,
    async chat({ messages, model = config.chatModel, metadata = {}, ...extra }) {
      if (!config.apiKey) {
        throw new DashScopeNodeError(
          "DASHSCOPE_API_KEY is not configured. Copy .env.example to .env and fill the key.",
          { metadata },
        );
      }
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), config.timeoutMs);
      const started = Date.now();
      try {
        const response = await fetch(`${config.baseUrl}/chat/completions`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${config.apiKey}`,
          },
          body: JSON.stringify({ model, messages, ...extra }),
          signal: controller.signal,
        });
        const data = await response.json();
        if (!response.ok) {
          throw new DashScopeNodeError(
            data.error?.message || data.message || `DashScope HTTP ${response.status}`,
            { status: response.status, metadata },
          );
        }
        console.info(JSON.stringify({
          event: "dashscope_node_request_ok",
          model,
          elapsed_ms: Date.now() - started,
          metadata,
        }));
        return data;
      } catch (error) {
        if (error.name === "AbortError") {
          throw new DashScopeNodeError(
            "DashScope request timed out. Increase QWEN_TIMEOUT_MS or retry later.",
            { metadata },
          );
        }
        if (error instanceof DashScopeNodeError) throw error;
        throw new DashScopeNodeError(error.message || "DashScope request failed", { metadata });
      } finally {
        clearTimeout(timeout);
      }
    },
  };
}
