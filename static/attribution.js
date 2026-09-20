/**
 * 纯前端决策字词归因与因果反事实消融分析引擎
 * 采用浏览器原生 Intl.Segmenter API，实现原子级分词与因果推动力定量计算。
 */

// 纯标点与无决策语义的极高频虚助词集合
const LIGHT_STOPWORDS = new Set([
  "，", "。", "！", "？", "、", "；", "：", "“", "”", "‘", "’", "（", "）", "—", "…", "～",
  ",", ".", "!", "?", ";", ":", "\"", "'", "(", ")", "-", "_", "/", "\\",
  "的", "了", "在", "着", "过", "和", "跟", "同", "与", "以及", "并", "并且", "就", "也", "又",
  "啊", "吗", "呢", "吧", "呀", "啦"
]);

/**
 * 原生高精度原子分词 (浏览器原生 Intl.Segmenter)
 */
export function tokenizeText(text) {
  text = (text || "").trim();
  if (!text) return [];

  // 若支持现代标准 Intl.Segmenter
  if (typeof Intl !== "undefined" && Intl.Segmenter) {
    try {
      const hasChinese = /[\u4e00-\u9fff]/.test(text);
      const segmenter = new Intl.Segmenter(hasChinese ? "zh-CN" : "en", { granularity: "word" });
      const segments = Array.from(segmenter.segment(text));
      return segments.filter(s => s.segment.trim().length > 0).map(s => s.segment);
    } catch (e) {
      // 回退
    }
  }

  // 回退分词器
  const matched = text.match(/[\u4e00-\u9fff]|[a-zA-Z0-9]+|[^\s\w]/g);
  return matched ? matched.filter(t => t.trim().length > 0) : [];
}

/**
 * 从输入对象中定位主要自然语言文本字段
 */
export function extractPrimaryTextField(inputData) {
  if (typeof inputData === "string") {
    return { fieldKey: null, textContent: inputData };
  }
  if (!inputData || typeof inputData !== "object") {
    return { fieldKey: null, textContent: String(inputData || "") };
  }

  const priorityKeys = [
    "user_request", "message", "chief_complaint", "claim", 
    "text", "content", "query", "request", "state", "source_context", "command"
  ];

  for (const pk of priorityKeys) {
    const val = inputData[pk];
    if (typeof val === "string" && val.trim().length > 1) {
      return { fieldKey: pk, textContent: val.trim() };
    }
  }

  // 挑选最长文本字段
  let longestKey = null;
  let longestVal = "";
  for (const [k, v] of Object.entries(inputData)) {
    if (typeof v === "string" && v.trim().length > longestVal.length) {
      longestKey = k;
      longestVal = v.trim();
    }
  }

  return { fieldKey: longestKey, textContent: longestVal };
}

/**
 * 替换输入对象中指定字段值
 */
export function replaceFieldValue(data, fieldKey, newVal) {
  if (fieldKey === null) {
    return newVal;
  }
  if (typeof data === "object" && data !== null) {
    const cloned = JSON.parse(JSON.stringify(data));
    cloned[fieldKey] = newVal;
    return cloned;
  }
  return newVal;
}

/**
 * 构建原子细粒度消融文本
 */
export function buildFineGrainedAblations(text, tokens, maxAblateCount = 25) {
  const hasChinese = /[\u4e00-\u9fff]/.test(text);
  const sep = hasChinese ? "" : " ";

  const skippedIndices = new Set();
  const candidateIndices = [];

  for (let i = 0; i < tokens.length; i++) {
    const tok = tokens[i];
    if (LIGHT_STOPWORDS.has(tok)) {
      skippedIndices.add(i);
    } else {
      candidateIndices.push(i);
    }
  }

  if (candidateIndices.length > maxAblateCount) {
    candidateIndices.sort((a, b) => tokens[b].length - tokens[a].length);
    const selected = new Set(candidateIndices.slice(0, maxAblateCount));
    for (let i = 0; i < tokens.length; i++) {
      if (!selected.has(i)) {
        skippedIndices.add(i);
      }
    }
    candidateIndices.length = 0;
    for (let i = 0; i < tokens.length; i++) {
      if (!skippedIndices.has(i)) candidateIndices.push(i);
    }
  }

  const ablations = [];
  for (const i of candidateIndices) {
    const tok = tokens[i];
    const remaining = tokens.filter((_, j) => j !== i);
    const ablated = remaining.join(sep).trim();
    ablations.push({ index: i, token: tok, ablatedText: ablated });
  }

  return { ablations, skippedIndices };
}

/**
 * 并发控制池 (类似 Semaphore)
 */
async function asyncPool(limit, items, iteratorFn) {
  const ret = [];
  const executing = [];
  for (const item of items) {
    const p = Promise.resolve().then(() => iteratorFn(item));
    ret.push(p);
    if (limit <= items.length) {
      const e = p.then(() => executing.splice(executing.indexOf(e), 1));
      executing.push(e);
      if (executing.length >= limit) {
        await Promise.race(executing);
      }
    }
  }
  return Promise.all(ret);
}

/**
 * 纯前端计算决策字词因果归因
 */
export async function computeDecisionAttribution({
  stateInput,
  questions,
  baseAnswers,
  client,
  model = "jev-latest",
  lang = "zh",
  caseMeta = null,
  maxTokens = 25
}) {
  const { fieldKey, textContent } = extractPrimaryTextField(stateInput);
  if (!textContent) {
    return {
      field_analyzed: fieldKey || "state",
      text: "",
      tokens_count: 0,
      primary_question_id: "",
      questions_attribution: {}
    };
  }

  const tokens = tokenizeText(textContent);
  if (!tokens.length) {
    return {
      field_analyzed: fieldKey || "state",
      text: textContent,
      tokens_count: 0,
      primary_question_id: "",
      questions_attribution: {}
    };
  }

  const { ablations, skippedIndices } = buildFineGrainedAblations(textContent, tokens, maxTokens);

  // 构造并发消融推理任务
  const ablatedTasks = ablations.map(({ index, token, ablatedText }) => {
    const newStateInput = replaceFieldValue(stateInput, fieldKey, ablatedText);
    let st = newStateInput;
    if (caseMeta && typeof caseMeta.buildQuestions === "function") {
      const built = caseMeta.buildQuestions(newStateInput, lang);
      st = built.state;
    }
    return { index, token, state: st };
  });

  const resultsByIndex = {};

  // 使用并发控制池执行请求，防止并发数过多触发限制
  await asyncPool(8, ablatedTasks, async ({ index, token, state }) => {
    try {
      const res = await client.executeSystemOne({
        state,
        questions,
        model
      });
      resultsByIndex[index] = res.answers || {};
    } catch (err) {
      console.warn(`Ablation failed for token "${token}" (${index}):`, err);
      resultsByIndex[index] = null;
    }
  });

  // 分析每个原语在各个 token 移除后的概率/置信度变动
  const questionsAttribution = {};

  for (const [qId, baseAns] of Object.entries(baseAnswers)) {
    const qType = baseAns.type || "choice";
    const tokenStats = [];
    let winnerLabel = "";
    let baseMetric = 0.0;

    if (qType === "choice") {
      winnerLabel = baseAns.choice || "";
      const baseProbs = baseAns.probabilities || {};
      baseMetric = baseProbs[winnerLabel] !== undefined ? baseProbs[winnerLabel] : (baseAns.confidence || 0.5);

      for (let i = 0; i < tokens.length; i++) {
        const tok = tokens[i];
        if (skippedIndices.has(i)) {
          tokenStats.push({
            token: tok,
            delta: 0.0,
            base_val: Math.round(baseMetric * 10000) / 10000,
            ablated_val: Math.round(baseMetric * 10000) / 10000,
            weight: 0.0,
            type: "neutral"
          });
          continue;
        }

        const abAns = resultsByIndex[i];
        let delta = 0.0;
        let ablatedProb = baseMetric;

        if (abAns && abAns[qId]) {
          const abInfo = abAns[qId];
          const abProbs = abInfo.probabilities || {};
          if (abProbs[winnerLabel] !== undefined) {
            ablatedProb = abProbs[winnerLabel];
          } else {
            ablatedProb = (abInfo.choice === winnerLabel) ? (abInfo.confidence || 0.0) : 0.0;
          }
          delta = baseMetric - ablatedProb;
        }

        tokenStats.push({
          token: tok,
          delta: Math.round(delta * 10000) / 10000,
          base_val: Math.round(baseMetric * 10000) / 10000,
          ablated_val: Math.round(ablatedProb * 10000) / 10000
        });
      }
    } else if (qType === "score") {
      baseMetric = baseAns.score || 0.0;
      winnerLabel = baseMetric.toFixed(2);

      for (let i = 0; i < tokens.length; i++) {
        const tok = tokens[i];
        if (skippedIndices.has(i)) {
          tokenStats.push({
            token: tok,
            delta: 0.0,
            base_val: Math.round(baseMetric * 10000) / 10000,
            ablated_val: Math.round(baseMetric * 10000) / 10000,
            weight: 0.0,
            type: "neutral"
          });
          continue;
        }

        const abAns = resultsByIndex[i];
        let delta = 0.0;
        let ablatedScore = baseMetric;

        if (abAns && abAns[qId]) {
          ablatedScore = abAns[qId].score !== undefined ? abAns[qId].score : baseMetric;
          delta = baseMetric - ablatedScore;
        }

        tokenStats.push({
          token: tok,
          delta: Math.round(delta * 10000) / 10000,
          base_val: Math.round(baseMetric * 10000) / 10000,
          ablated_val: Math.round(ablatedScore * 10000) / 10000
        });
      }
    } else if (qType === "noul") {
      baseMetric = baseAns.noul || 0.0;
      winnerLabel = `${(baseMetric * 100).toFixed(1)}%`;

      for (let i = 0; i < tokens.length; i++) {
        const tok = tokens[i];
        if (skippedIndices.has(i)) {
          tokenStats.push({
            token: tok,
            delta: 0.0,
            base_val: Math.round(baseMetric * 10000) / 10000,
            ablated_val: Math.round(baseMetric * 10000) / 10000,
            weight: 0.0,
            type: "neutral"
          });
          continue;
        }

        const abAns = resultsByIndex[i];
        let delta = 0.0;
        let ablatedNoul = baseMetric;

        if (abAns && abAns[qId]) {
          ablatedNoul = abAns[qId].noul !== undefined ? abAns[qId].noul : baseMetric;
          delta = baseMetric - ablatedNoul;
        }

        tokenStats.push({
          token: tok,
          delta: Math.round(delta * 10000) / 10000,
          base_val: Math.round(baseMetric * 10000) / 10000,
          ablated_val: Math.round(ablatedNoul * 10000) / 10000
        });
      }
    } else {
      continue;
    }

    // 归一化权重与极性判断
    const posDeltas = tokenStats.filter(s => s.weight === undefined).map(s => Math.max(0.0, s.delta));
    const maxPos = posDeltas.length ? Math.max(...posDeltas) : 0.0;

    for (const s of tokenStats) {
      if (s.weight !== undefined) continue;
      const d = s.delta;
      if (maxPos > 0.001 && d > 0) {
        s.weight = Math.round((d / maxPos) * 1000) / 1000;
        s.type = "positive";
      } else if (d < -0.05) {
        s.weight = Math.round(Math.abs(d) * 1000) / 1000;
        s.type = "negative";
      } else {
        s.weight = 0.0;
        s.type = "neutral";
      }
    }

    // Top 3 核心驱动词
    const topDrivers = tokenStats
      .filter(s => s.delta > 0.01)
      .sort((a, b) => b.delta - a.delta)
      .slice(0, 3);

    questionsAttribution[qId] = {
      type: qType,
      winner: winnerLabel,
      base_val: baseMetric,
      tokens: tokenStats,
      top_drivers: topDrivers
    };
  }

  const primaryQId = Object.keys(questionsAttribution)[0] || "";

  return {
    field_analyzed: fieldKey || (lang === "zh" ? "输入文本" : "Input Text"),
    text: textContent,
    tokens_count: tokens.length,
    primary_question_id: primaryQId,
    questions_attribution: questionsAttribution
  };
}
