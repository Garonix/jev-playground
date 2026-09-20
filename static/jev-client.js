/**
 * Jev System One Client (Pure Frontend ES Module)
 * 支持官方直连、本地/CF反向代理与离线模拟评测模式
 */
export class JevClient {
  constructor({ baseUrl = "https://api.typesafe.ai", apiKey = "" } = {}) {
    this.baseUrl = (baseUrl || "https://api.typesafe.ai").replace(/\/+$/, "");
    this.apiKey = (apiKey || "").trim();
  }

  setBaseUrl(url) {
    this.baseUrl = (url || "https://api.typesafe.ai").replace(/\/+$/, "");
  }

  setApiKey(key) {
    this.apiKey = (key || "").trim();
  }

  getHeaders() {
    const headers = {
      "Content-Type": "application/json"
    };
    if (this.apiKey) {
      headers["Authorization"] = `Bearer ${this.apiKey}`;
      headers["x-typesafe-api-key"] = this.apiKey;
    }
    return headers;
  }

  async testConnection() {
    if (!this.apiKey) {
      throw new Error("缺少 API Key");
    }

    if (this.apiKey.toLowerCase() === "mock") {
      return { valid: true, latency_ms: 12 };
    }

    const startTime = performance.now();
    const endpoint = `${this.baseUrl}/v1/models`;
    
    let resp;
    try {
      resp = await fetch(endpoint, {
        method: "GET",
        headers: this.getHeaders()
      });
    } catch (e) {
      throw new Error(`网络连接失败: ${e.message}。若在静态前端调用官方接口，请配置 CORS 代理 (如 Cloudflare Worker)；若离线体验，Key 可填入 mock。`);
    }

    const latency_ms = Math.round(performance.now() - startTime);

    if (resp.status === 401 || resp.status === 403) {
      throw new Error("API Key 无效或未授权");
    }
    if (!resp.ok) {
      throw new Error(`连接失败 (HTTP ${resp.status})`);
    }

    return { valid: true, latency_ms };
  }

  simulateSystemOne({ state, questions, model = "jev-mock" }) {
    const textState = typeof state === "string" ? state : JSON.stringify(state);
    const answers = {};

    for (const [qId, qDef] of Object.entries(questions)) {
      if (qDef.type === "choice") {
        const options = Object.keys(qDef.criteria || {});
        let selected = options[0] || "unknown";
        let bestScore = -1;

        for (const opt of options) {
          const desc = typeof qDef.criteria[opt] === "string"
            ? qDef.criteria[opt]
            : (qDef.criteria[opt]?.what || opt);
          let matchCount = 0;
          for (const char of opt + desc) {
            if (char.trim() && textState.includes(char)) matchCount++;
          }
          if (matchCount > bestScore) {
            bestScore = matchCount;
            selected = opt;
          }
        }

        const confidence = Number((0.85 + Math.random() * 0.12).toFixed(4));
        const probs = {};
        let remain = 1 - confidence;
        probs[selected] = confidence;
        const otherOpts = options.filter(o => o !== selected);
        otherOpts.forEach((o, idx) => {
          const p = idx === otherOpts.length - 1 ? remain : Number((remain * Math.random()).toFixed(4));
          probs[o] = p;
          remain = Math.max(0, remain - p);
        });

        answers[qId] = {
          type: "choice",
          choice: selected,
          confidence,
          probabilities: probs
        };
      } else if (qDef.type === "score") {
        const levels = Array.isArray(qDef.criteria) ? qDef.criteria : [];
        let scoreVal = 1.0;
        if (textState.includes("严重") || textState.includes("死") || textState.includes("退款") || textState.includes("怒") || textState.includes("投诉") || textState.includes("高")) {
          scoreVal = Math.min(2.0, (levels.length - 1) || 2.0);
        } else if (textState.includes("不悦") || textState.includes("咨询") || textState.includes("中")) {
          scoreVal = 1.0;
        } else {
          scoreVal = 0.0;
        }
        const score = Number((scoreVal + (Math.random() * 0.2 - 0.1)).toFixed(2));
        const probs = {};
        levels.forEach((lvl, idx) => {
          probs[lvl] = idx === Math.round(scoreVal) ? 0.78 : Number((0.22 / Math.max(1, levels.length - 1)).toFixed(4));
        });
        answers[qId] = {
          type: "score",
          score,
          probabilities: probs
        };
      } else if (qDef.type === "noul") {
        let prob = 0.15;
        const instructions = typeof qDef.instructions === "string" ? qDef.instructions : JSON.stringify(qDef.instructions || "");
        if (instructions.includes("复合") && (textState.includes("同时") || textState.includes("并且") || textState.includes("and"))) {
          prob = 0.88;
        } else if (instructions.includes("敏感") || instructions.includes("个人信息") || instructions.includes("pii")) {
          prob = textState.includes("身份证") || textState.includes("密码") ? 0.96 : 0.05;
        } else if (instructions.includes("退款") && (textState.includes("退款") || textState.includes("退钱") || textState.includes("理赔"))) {
          prob = 0.92;
        } else if (instructions.includes("越狱") || instructions.includes("覆盖")) {
          prob = textState.includes("忽略") || textState.includes("DAN") ? 0.94 : 0.08;
        } else if (instructions.includes("量") || instructions.includes("volume")) {
          prob = textState.includes("成交量") || textState.includes("volume") ? 0.91 : 0.12;
        } else {
          prob = Number((0.4 + Math.random() * 0.4).toFixed(4));
        }

        answers[qId] = {
          type: "noul",
          noul: prob,
          confidence: Number(Math.max(prob, 1 - prob).toFixed(4))
        };
      }
    }

    return {
      answers,
      latency_ms: Math.floor(80 + Math.random() * 40),
      model_used: "jev-mock",
      usage: { input_tokens: Math.floor(textState.length * 1.5) },
      raw_response: { mock: true, answers }
    };
  }

  async executeSystemOne({ state, questions, model = "jev-latest" }) {
    if (!this.apiKey) {
      throw new Error("缺少 API Key，请点击右上角进行配置。");
    }

    if (this.apiKey.toLowerCase() === "mock") {
      await new Promise(r => setTimeout(r, 60 + Math.random() * 50));
      return this.simulateSystemOne({ state, questions, model });
    }

    // 格式化 questions 字典
    const formattedQuestions = {};
    for (const [qId, qDef] of Object.entries(questions)) {
      if (qDef.type === "choice") {
        formattedQuestions[qId] = {
          type: "choice",
          instructions: qDef.instructions,
          criteria: qDef.criteria || {}
        };
      } else if (qDef.type === "score") {
        formattedQuestions[qId] = {
          type: "score",
          instructions: qDef.instructions,
          criteria: Array.isArray(qDef.criteria) ? qDef.criteria : []
        };
      } else if (qDef.type === "noul") {
        const item = {
          type: "noul",
          instructions: qDef.instructions
        };
        if (qDef.criteria && (qDef.criteria.true || qDef.criteria.false)) {
          item.criteria = {
            true: qDef.criteria.true || "",
            false: qDef.criteria.false || ""
          };
        }
        formattedQuestions[qId] = item;
      }
    }

    const startTime = performance.now();
    const endpoint = `${this.baseUrl}/v1/systemone`;

    let resp;
    try {
      resp = await fetch(endpoint, {
        method: "POST",
        headers: this.getHeaders(),
        body: JSON.stringify({
          state,
          questions: formattedQuestions,
          model
        })
      });
    } catch (e) {
      throw new Error(`API 请求网络异常: ${e.message}。若在静态前端调用官方接口，请配置 CORS 代理 (如 Cloudflare Worker)；若离线体验，Key 可填入 mock。`);
    }

    const latency_ms = Math.round(performance.now() - startTime);

    if (!resp.ok) {
      let detail = `请求失败 (HTTP ${resp.status})`;
      try {
        const errJson = await resp.json();
        detail = errJson.detail || errJson.message || errJson.error || JSON.stringify(errJson);
      } catch (_) {}
      throw new Error(detail);
    }

    const data = await resp.json();
    return {
      answers: data.answers || {},
      usage: data.usage || {},
      model_used: data.model || model,
      latency_ms,
      raw_response: data
    };
  }
}
