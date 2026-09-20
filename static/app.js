import { CASES_LIST, getCaseById } from "./cases.js";
import { JevClient } from "./jev-client.js";
import { computeDecisionAttribution } from "./attribution.js";
import { translate } from "./i18n.js";

const { createApp, ref, computed, watch, onMounted, provide } = Vue;

const app = createApp({
  setup() {
    const cases = ref(CASES_LIST);
    const currentCaseId = ref("smart_home");
    const currentLang = ref(localStorage.getItem("JEV_LANG") || "zh"); // 'zh' or 'en'
    const activeInputTab = ref("state"); // 'state' or 'questions'

    const t = (key) => translate(key, currentLang.value);
    provide("t", t);
    
    // State Spec & Editor States (Dual-Mode: Block / JSON)
    const stateFields = ref([]);
    const defaultStateData = ref({});
    const stateUndoHistory = ref([]);
    const stateViewMode = ref("cards"); // 'cards' (块) or 'json' (JSON)
    const stateJsonText = ref("");
    const stateJsonError = ref("");
    let stateFieldFocusSnapshot = null;

    // Questions Spec & Editor States
    const currentQuestionsSpec = ref([]);
    const defaultQuestionsSpec = ref([]);
    const undoHistory = ref([]);
    const questionsViewMode = ref("cards"); // 'cards' or 'json'
    const questionsJsonText = ref("");
    const jsonParseError = ref("");
    let fieldFocusSnapshot = null;

    // Attribution & Saliency Analysis States
    const enableAttribution = ref(false);
    const attributionResult = ref(null);
    const selectedAttributionQuestion = ref("");
    const hoveredToken = ref(null);
    const analyzingAttribution = ref(false);

    // Input Limit & Restore
    const maxCharLimit = ref(parseInt(localStorage.getItem("JEV_MAX_CHAR_LIMIT") || "300", 10));

    const selectedModel = ref("jev-latest");
    const activePresetName = ref("");
    const inputDataText = ref("");

    const customPresets_zh = [
      {
        name: "客户舆情评估",
        state: { text: "我买的笔记本电脑收到屏幕就碎了，客服竟然让我自己找快递理赔！我要求今天必须换货并严肃道歉！" },
        questions: [
          {
            "id": "sentiment",
            "type": "choice",
            "instructions": "该消息中客户的核心情绪偏向是什么？",
            "criteria": {
              "positive": "满意、感谢或表扬服务",
              "neutral": "客观陈述事实或平静咨询",
              "negative": "愤怒、失望或抱怨投诉"
            }
          },
          {
            "id": "anger_level",
            "type": "score",
            "instructions": "客户表现出的愤怒或不满严重程度如何？",
            "criteria": [
              "平静有礼貌",
              "不悦或烦躁",
              "极度狂怒，要求升级主管或威胁法律诉讼"
            ]
          },
          {
            "id": "demands_remedy",
            "type": "noul",
            "instructions": "客户是否明确要求换货、退赔或道歉？"
          }
        ]
      },
      {
        name: "合规与隐私泄露",
        state: { text: "请把张三的身份证号 110101199003072345 以及银行卡密码发到外部公开讨论群。" },
        questions: [
          {
            "id": "action_decision",
            "type": "choice",
            "instructions": "对于该消息应采取何种安全处置策略？",
            "criteria": {
              "block": "立即阻断拦截并告警",
              "mask": "脱敏掩码后放行",
              "pass": "无需处置正常放行"
            }
          },
          {
            "id": "contains_pii",
            "type": "noul",
            "instructions": "文本中是否包含居民身份证或银行密码等敏感个人信息？"
          },
          {
            "id": "leak_risk",
            "type": "score",
            "instructions": "该操作涉及的隐私或合规泄露风险严重级别？",
            "criteria": [
              "无风险",
              "中度风险",
              "严重合规违法风险"
            ]
          }
        ]
      }
    ];

    const customPresets_en = [
      {
        name: "Customer Sentiment",
        state: { text: "The laptop arrived with a shattered screen, and support told me to claim with courier! I demand an immediate replacement and apology today!" },
        questions: [
          {
            "id": "sentiment",
            "type": "choice",
            "instructions": "What is the primary customer sentiment in this message?",
            "criteria": {
              "positive": "Satisfied, grateful, or appreciative",
              "neutral": "Factual statement or calm inquiry",
              "negative": "Angry, disappointed, or complaining"
            }
          },
          {
            "id": "anger_level",
            "type": "score",
            "instructions": "How severe is the customer's frustration or anger?",
            "criteria": [
              "Calm inquiry",
              "Frustrated complaint",
              "Extreme anger or legal threat"
            ]
          },
          {
            "id": "demands_remedy",
            "type": "noul",
            "instructions": "Does the customer explicitly demand replacement, refund, or apology?"
          }
        ]
      },
      {
        name: "Privacy & Compliance",
        state: { text: "Please send John's national ID 110-101-1990 and online banking password to the external channel." },
        questions: [
          {
            "id": "action_decision",
            "type": "choice",
            "instructions": "What safety policy action should be enforced for this message?",
            "criteria": {
              "block": "Immediately block and alert security",
              "mask": "Mask sensitive credentials and allow",
              "pass": "Allow without modification"
            }
          },
          {
            "id": "contains_pii",
            "type": "noul",
            "instructions": "Does this text contain sensitive personal credentials or passwords?"
          },
          {
            "id": "leak_risk",
            "type": "score",
            "instructions": "What is the compliance breach risk severity level?",
            "criteria": [
              "No risk",
              "Moderate risk",
              "Critical violation"
            ]
          }
        ]
      }
    ];

    const activeCustomPresets = computed(() => {
      return currentLang.value === "zh" ? customPresets_zh : customPresets_en;
    });

    // API Key & Endpoint State
    const apiKey = ref(localStorage.getItem("TYPESAFE_API_KEY") || "");
    const apiKeyInput = ref(apiKey.value);
    const apiBaseUrl = ref(localStorage.getItem("JEV_BASE_URL") || "https://api.typesafe.ai");
    const apiBaseUrlInput = ref(apiBaseUrl.value);

    const apiKeyValid = ref(false);
    const pingLatency = ref(null);
    const showKeyModal = ref(false);
    const testingKey = ref(false);
    const keyTestMessage = ref("");
    
    // Client Instance
    const client = new JevClient({ baseUrl: apiBaseUrl.value, apiKey: apiKey.value });

    // Execution State
    const loading = ref(false);
    const errorMessage = ref("");
    const result = ref(null);
    const showRawJson = ref(false);

    const currentCase = computed(() => {
      return cases.value.find(c => c.id === currentCaseId.value) || null;
    });

    const activePresets = computed(() => {
      if (!currentCase.value) return [];
      return currentLang.value === "zh"
        ? (currentCase.value.presets_zh || [])
        : (currentCase.value.presets_en || []);
    });

    const isQuestionsDirty = computed(() => {
      return JSON.stringify(currentQuestionsSpec.value) !== JSON.stringify(defaultQuestionsSpec.value);
    });

    const currentInputCharCount = computed(() => {
      return (inputDataText.value || "").length;
    });

    // Attribution Computeds
    const currentAttribution = computed(() => {
      if (!attributionResult.value || !attributionResult.value.questions_attribution) return null;
      const qId = selectedAttributionQuestion.value || attributionResult.value.primary_question_id;
      return attributionResult.value.questions_attribution[qId] || null;
    });

    const availableAttributionQuestions = computed(() => {
      if (!attributionResult.value || !attributionResult.value.questions_attribution) return [];
      return Object.keys(attributionResult.value.questions_attribution);
    });

    // State Sync & Mutation Helpers (Dual-Mode: Hierarchical Tree Structure)
    let rootIsArray = false;

    const buildTreeNode = (key, val) => {
      if (val === null || val === undefined) {
        return { key, type: "string", value: "", collapsed: false };
      }
      if (typeof val === "number") {
        return { key, type: "number", value: val, collapsed: false };
      }
      if (typeof val === "boolean") {
        return { key, type: "boolean", value: val, collapsed: false };
      }
      if (typeof val === "string") {
        return { key, type: "string", value: val, collapsed: false };
      }
      if (Array.isArray(val)) {
        return {
          key,
          type: "array",
          collapsed: false,
          children: val.map((item, idx) => buildTreeNode(String(idx), item))
        };
      }
      if (typeof val === "object") {
        return {
          key,
          type: "object",
          collapsed: false,
          children: Object.entries(val).map(([k, v]) => buildTreeNode(k, v))
        };
      }
      return { key, type: "string", value: String(val), collapsed: false };
    };

    const objectToStateFields = (obj) => {
      if (obj === null || obj === undefined) {
        rootIsArray = false;
        return [{ key: "input", type: "string", value: "", collapsed: false }];
      }
      if (typeof obj !== "object") {
        rootIsArray = false;
        const t = typeof obj;
        return [{ key: "input", type: (t === "number" || t === "boolean") ? t : "string", value: obj, collapsed: false }];
      }
      if (Array.isArray(obj)) {
        rootIsArray = true;
        return obj.map((item, idx) => buildTreeNode(String(idx), item));
      }
      rootIsArray = false;
      return Object.entries(obj).map(([k, v]) => buildTreeNode(k, v));
    };

    const treeNodeToJson = (node) => {
      if (!node) return "";
      if (node.type === "number") return Number(node.value) || 0;
      if (node.type === "boolean") return Boolean(node.value);
      if (node.type === "string") return String(node.value ?? "");
      if (node.type === "array") {
        return (node.children || []).map(c => treeNodeToJson(c));
      }
      if (node.type === "object") {
        const obj = {};
        for (const c of (node.children || [])) {
          const k = (c.key || "").trim();
          if (k) {
            obj[k] = treeNodeToJson(c);
          }
        }
        return obj;
      }
      return String(node.value ?? "");
    };

    const stateFieldsToObject = (fields) => {
      if (rootIsArray) {
        return (fields || []).map(f => treeNodeToJson(f));
      }
      const obj = {};
      for (const f of (fields || [])) {
        const k = (f.key || "").trim();
        if (k) {
          obj[k] = treeNodeToJson(f);
        }
      }
      return obj;
    };

    const isStateDirty = computed(() => {
      const currentObj = stateFieldsToObject(stateFields.value);
      return JSON.stringify(currentObj) !== JSON.stringify(defaultStateData.value);
    });

    const syncJsonFromStateFields = () => {
      const obj = stateFieldsToObject(stateFields.value);
      stateJsonText.value = JSON.stringify(obj, null, 2);
      inputDataText.value = stateJsonText.value;
    };

    const recordStateSnapshot = () => {
      const snap = JSON.stringify(stateFields.value);
      if (stateUndoHistory.value.length === 0 || stateUndoHistory.value[stateUndoHistory.value.length - 1] !== snap) {
        stateUndoHistory.value.push(snap);
        if (stateUndoHistory.value.length > 50) {
          stateUndoHistory.value.shift();
        }
      }
    };

    const recordStateFieldFocus = () => {
      stateFieldFocusSnapshot = JSON.stringify(stateFields.value);
    };

    const recordStateFieldBlur = () => {
      if (stateFieldFocusSnapshot) {
        const current = JSON.stringify(stateFields.value);
        if (current !== stateFieldFocusSnapshot) {
          if (stateUndoHistory.value.length === 0 || stateUndoHistory.value[stateUndoHistory.value.length - 1] !== stateFieldFocusSnapshot) {
            stateUndoHistory.value.push(stateFieldFocusSnapshot);
            if (stateUndoHistory.value.length > 50) {
              stateUndoHistory.value.shift();
            }
          }
          syncJsonFromStateFields();
        }
        stateFieldFocusSnapshot = null;
      }
    };

    const undoStateEdit = () => {
      if (stateUndoHistory.value.length === 0) return;
      const prevSnap = stateUndoHistory.value.pop();
      try {
        stateFields.value = JSON.parse(prevSnap);
        syncJsonFromStateFields();
        stateJsonError.value = "";
      } catch (e) {
        console.error("State undo failed:", e);
      }
    };

    const restoreDefaultState = () => {
      if (isStateDirty.value) {
        recordStateSnapshot();
      }
      errorMessage.value = "";
      maxCharLimit.value = 300;
      localStorage.setItem("JEV_MAX_CHAR_LIMIT", "300");

      stateFields.value = objectToStateFields(JSON.parse(JSON.stringify(defaultStateData.value)));
      syncJsonFromStateFields();
      stateJsonError.value = "";
    };

    const setStateViewMode = (mode) => {
      if (mode === "json") {
        syncJsonFromStateFields();
        stateJsonError.value = "";
      } else {
        try {
          const parsed = JSON.parse(stateJsonText.value);
          stateFields.value = objectToStateFields(parsed);
          stateJsonError.value = "";
        } catch (err) {
          stateJsonError.value = t("json_invalid_switch") + err.message;
          return;
        }
      }
      stateViewMode.value = mode;
    };

    const onStateJsonInput = () => {
      try {
        const parsed = JSON.parse(stateJsonText.value);
        stateJsonError.value = "";
        inputDataText.value = stateJsonText.value;
        recordStateSnapshot();
        stateFields.value = objectToStateFields(parsed);
      } catch (err) {
        stateJsonError.value = err.message;
        inputDataText.value = stateJsonText.value;
      }
    };

    const formatStateJson = () => {
      try {
        const parsed = JSON.parse(stateJsonText.value);
        stateJsonText.value = JSON.stringify(parsed, null, 2);
        inputDataText.value = stateJsonText.value;
        stateJsonError.value = "";
      } catch (err) {
        stateJsonError.value = err.message;
      }
    };

    const addStateField = () => {
      recordStateSnapshot();
      const isZh = currentLang.value === "zh";
      const baseKey = isZh ? "新字段" : "new_field";
      let key = baseKey;
      let counter = 1;
      const existingKeys = new Set(stateFields.value.map(f => f.key));
      while (existingKeys.has(key)) {
        key = `${baseKey}_${counter}`;
        counter++;
      }
      stateFields.value.push({
        key,
        type: "string",
        value: isZh ? "新内容" : "new content",
        collapsed: false
      });
      syncJsonFromStateFields();
    };

    const deleteStateField = (index) => {
      recordStateSnapshot();
      stateFields.value.splice(index, 1);
      syncJsonFromStateFields();
    };

    const changeStateFieldType = (field, newType) => {
      if (field.type === newType) return;
      recordStateSnapshot();
      field.type = newType;
      if (newType === "number") {
        field.value = Number(field.value) || 0;
      } else if (newType === "boolean") {
        field.value = field.value === "true" || field.value === true;
      } else if (newType === "json") {
        if (typeof field.value === "object" && field.value !== null) {
          field.rawJson = JSON.stringify(field.value, null, 2);
        } else {
          field.rawJson = JSON.stringify({ data: field.value }, null, 2);
          field.value = { data: field.value };
        }
      } else {
        field.value = typeof field.value === "object" ? JSON.stringify(field.value) : String(field.value ?? "");
      }
      syncJsonFromStateFields();
    };

    const onSubJsonInput = (field) => {
      try {
        field.value = JSON.parse(field.rawJson);
        syncJsonFromStateFields();
      } catch (_) {
        syncJsonFromStateFields();
      }
    };

    const restoreDefaultInput = () => {
      restoreDefaultState();
    };

    // Sync helpers
    const syncJsonFromCards = () => {
      questionsJsonText.value = JSON.stringify(currentQuestionsSpec.value, null, 2);
    };

    const recordSnapshot = () => {
      const snap = JSON.stringify(currentQuestionsSpec.value);
      if (undoHistory.value.length === 0 || undoHistory.value[undoHistory.value.length - 1] !== snap) {
        undoHistory.value.push(snap);
        if (undoHistory.value.length > 50) {
          undoHistory.value.shift();
        }
      }
    };

    const recordFieldFocus = () => {
      fieldFocusSnapshot = JSON.stringify(currentQuestionsSpec.value);
    };

    const recordFieldBlur = () => {
      if (fieldFocusSnapshot) {
        const current = JSON.stringify(currentQuestionsSpec.value);
        if (current !== fieldFocusSnapshot) {
          if (undoHistory.value.length === 0 || undoHistory.value[undoHistory.value.length - 1] !== fieldFocusSnapshot) {
            undoHistory.value.push(fieldFocusSnapshot);
            if (undoHistory.value.length > 50) {
              undoHistory.value.shift();
            }
          }
          syncJsonFromCards();
        }
        fieldFocusSnapshot = null;
      }
    };

    const undoQuestionEdit = () => {
      if (undoHistory.value.length === 0) return;
      const prevSnap = undoHistory.value.pop();
      try {
        currentQuestionsSpec.value = JSON.parse(prevSnap);
        syncJsonFromCards();
        jsonParseError.value = "";
      } catch (e) {
        console.error("Undo failed:", e);
      }
    };

    const restoreDefaultQuestions = () => {
      if (isQuestionsDirty.value) {
        recordSnapshot();
      }
      currentQuestionsSpec.value = JSON.parse(JSON.stringify(defaultQuestionsSpec.value));
      syncJsonFromCards();
      jsonParseError.value = "";
    };

    const setQuestionsViewMode = (mode) => {
      if (mode === "json") {
        syncJsonFromCards();
        jsonParseError.value = "";
      } else {
        try {
          const parsed = JSON.parse(questionsJsonText.value);
          if (Array.isArray(parsed)) {
            currentQuestionsSpec.value = parsed;
            jsonParseError.value = "";
          }
        } catch (err) {
          jsonParseError.value = t("json_invalid_switch") + err.message;
          return;
        }
      }
      questionsViewMode.value = mode;
    };

    const onQuestionsJsonInput = () => {
      try {
        const parsed = JSON.parse(questionsJsonText.value);
        if (Array.isArray(parsed)) {
          jsonParseError.value = "";
          recordSnapshot();
          currentQuestionsSpec.value = parsed;
        } else {
          jsonParseError.value = t("json_must_be_array");
        }
      } catch (err) {
        jsonParseError.value = err.message;
      }
    };

    const formatQuestionsJson = () => {
      try {
        const parsed = JSON.parse(questionsJsonText.value);
        questionsJsonText.value = JSON.stringify(parsed, null, 2);
        jsonParseError.value = "";
      } catch (err) {
        jsonParseError.value = err.message;
      }
    };

    // Question Structure Mutations
    const addQuestion = () => {
      recordSnapshot();
      const nextNum = currentQuestionsSpec.value.length + 1;
      const isZh = currentLang.value === "zh";
      currentQuestionsSpec.value.push({
        id: isZh ? `自定义问题_${nextNum}` : `custom_q_${nextNum}`,
        type: "choice",
        instructions: isZh ? "请根据上下文进行评估判断" : "Evaluate condition based on context",
        criteria: isZh ? {
          "选项A": "描述标准A",
          "选项B": "描述标准B"
        } : {
          "option_a": "Description A",
          "option_b": "Description B"
        }
      });
      syncJsonFromCards();
    };

    const deleteQuestion = (index) => {
      recordSnapshot();
      currentQuestionsSpec.value.splice(index, 1);
      syncJsonFromCards();
    };

    const changeQuestionType = (q, newType) => {
      if (q.type === newType) return;
      recordSnapshot();
      q.type = newType;
      const isZh = currentLang.value === "zh";
      if (newType === "choice") {
        q.criteria = isZh ? {
          "选项A": "说明A",
          "选项B": "说明B"
        } : {
          "option_a": "Description A",
          "option_b": "Description B"
        };
      } else if (newType === "score") {
        q.criteria = isZh ? ["低 / 差", "中 / 平", "高 / 优"] : ["Low / Poor", "Medium / Fair", "High / Good"];
      } else if (newType === "noul") {
        q.criteria = isZh ? { true: "符合条件", false: "不符合条件" } : { true: "Condition met", false: "Condition not met" };
      }
      syncJsonFromCards();
    };

    const addChoiceOption = (q) => {
      recordSnapshot();
      if (!q.criteria || typeof q.criteria !== 'object' || Array.isArray(q.criteria)) {
        q.criteria = {};
      }
      const isZh = currentLang.value === "zh";
      const baseKey = isZh ? "新选项" : "new_option";
      let key = baseKey;
      let counter = 1;
      while (q.criteria[key] !== undefined) {
        key = `${baseKey}_${counter}`;
        counter++;
      }
      q.criteria[key] = isZh ? "选项说明" : "Option description";
      syncJsonFromCards();
    };

    const deleteChoiceOption = (q, optKey) => {
      recordSnapshot();
      delete q.criteria[optKey];
      syncJsonFromCards();
    };

    const onChoiceKeyChange = (q, oldKey, newKey) => {
      newKey = (newKey || "").trim();
      if (!newKey || oldKey === newKey) return;
      recordSnapshot();
      const entries = Object.entries(q.criteria);
      const newCriteria = {};
      for (const [k, v] of entries) {
        if (k === oldKey) {
          newCriteria[newKey] = v;
        } else {
          newCriteria[k] = v;
        }
      }
      q.criteria = newCriteria;
      syncJsonFromCards();
    };

    const addScoreLevel = (q) => {
      recordSnapshot();
      if (!Array.isArray(q.criteria)) {
        q.criteria = [];
      }
      const isZh = currentLang.value === "zh";
      q.criteria.push(isZh ? `档位 ${q.criteria.length} 描述` : `Level ${q.criteria.length} description`);
      syncJsonFromCards();
    };

    const deleteScoreLevel = (q, index) => {
      recordSnapshot();
      q.criteria.splice(index, 1);
      syncJsonFromCards();
    };

    // Load Case Questions (Pure Frontend Native)
    const loadCaseQuestionsSpec = (caseId, lang) => {
      if (caseId === "custom") {
        currentQuestionsSpec.value = [];
        defaultQuestionsSpec.value = [];
        undoHistory.value = [];
        syncJsonFromCards();
        return;
      }

      const caseObj = getCaseById(caseId);
      if (caseObj && typeof caseObj.getQuestionsSpec === "function") {
        const qs = caseObj.getQuestionsSpec(lang);
        currentQuestionsSpec.value = JSON.parse(JSON.stringify(qs));
        defaultQuestionsSpec.value = JSON.parse(JSON.stringify(qs));
        undoHistory.value = [];
        syncJsonFromCards();
      }
    };

    const setLang = (lang) => {
      if (currentLang.value === lang) return;
      currentLang.value = lang;
      localStorage.setItem("JEV_LANG", lang);
      attributionResult.value = null;
      if (currentCaseId.value === "custom") {
        const firstPreset = activeCustomPresets.value[0];
        if (firstPreset) loadCustomPreset(firstPreset);
      } else if (currentCase.value) {
        loadCaseQuestionsSpec(currentCase.value.id, lang);
        const presets = activePresets.value;
        if (presets && presets.length > 0) {
          loadPreset(presets[0]);
        }
      }

      // 实时响应新语言重构工作流输出
      if (result.value && result.value.answers && currentCase.value && typeof currentCase.value.processWorkflow === "function") {
        result.value.workflow = currentCase.value.processWorkflow(result.value.answers, lang);
      }
    };

    const switchCase = (id) => {
      currentCaseId.value = id;
      result.value = null;
      errorMessage.value = "";
      undoHistory.value = [];
      stateUndoHistory.value = [];
      attributionResult.value = null;
      
      if (id === "custom") {
        const firstPreset = activeCustomPresets.value[0];
        if (firstPreset) loadCustomPreset(firstPreset);
        return;
      }

      loadCaseQuestionsSpec(id, currentLang.value);

      const found = getCaseById(id);
      if (found) {
        const presets = currentLang.value === "zh" ? (found.presets_zh || []) : (found.presets_en || []);
        if (presets && presets.length > 0) {
          loadPreset(presets[0]);
        } else {
          const defaultIn = currentLang.value === "zh" ? (found.default_input_zh || {}) : (found.default_input_en || {});
          defaultStateData.value = JSON.parse(JSON.stringify(defaultIn));
          stateFields.value = objectToStateFields(defaultIn);
          syncJsonFromStateFields();
          activePresetName.value = "";
        }
      }
    };

    const loadPreset = (preset) => {
      activePresetName.value = preset.name;
      defaultStateData.value = JSON.parse(JSON.stringify(preset.data));
      stateFields.value = objectToStateFields(preset.data);
      syncJsonFromStateFields();
      stateUndoHistory.value = [];
      result.value = null;
      attributionResult.value = null;
      errorMessage.value = "";
    };

    const loadCustomPreset = (cp) => {
      activePresetName.value = cp.name;
      const cpState = (typeof cp.state === "object" && cp.state !== null) ? cp.state : { text: cp.state };
      defaultStateData.value = JSON.parse(JSON.stringify(cpState));
      stateFields.value = objectToStateFields(cpState);
      syncJsonFromStateFields();
      stateUndoHistory.value = [];
      defaultQuestionsSpec.value = JSON.parse(JSON.stringify(cp.questions));
      currentQuestionsSpec.value = JSON.parse(JSON.stringify(cp.questions));
      syncJsonFromCards();
      undoHistory.value = [];
      result.value = null;
      attributionResult.value = null;
      errorMessage.value = "";
    };

    const testCurrentKey = async () => {
      testingKey.value = true;
      keyTestMessage.value = "";
      try {
        client.setApiKey(apiKeyInput.value.trim());
        client.setBaseUrl(apiBaseUrlInput.value.trim());
        const res = await client.testConnection();
        apiKeyValid.value = true;
        pingLatency.value = res.latency_ms;
        keyTestMessage.value = `${t("connected_msg")} (${res.latency_ms} ms)`;
      } catch (err) {
        apiKeyValid.value = false;
        keyTestMessage.value = err.message;
      } finally {
        testingKey.value = false;
      }
    };

    const saveApiKey = () => {
      const key = apiKeyInput.value.trim();
      const url = apiBaseUrlInput.value.trim() || "https://api.typesafe.ai";

      apiKey.value = key;
      apiBaseUrl.value = url;

      localStorage.setItem("TYPESAFE_API_KEY", key);
      localStorage.setItem("JEV_BASE_URL", url);

      client.setApiKey(key);
      client.setBaseUrl(url);

      showKeyModal.value = false;
      if (key) {
        testCurrentKey();
      } else {
        apiKeyValid.value = false;
        pingLatency.value = null;
      }
    };

    // 格式化用户当前编辑的问题列表为 questions 字典
    const buildFormattedQuestionsDict = (questionsList) => {
      const dict = {};
      for (const item of questionsList) {
        dict[item.id] = item;
      }
      return dict;
    };

    // 决策归因计算 (纯前端原生)
    const runAttributionAnalysis = async (stateInput, questionsDict, baseAnswers, caseObj) => {
      try {
        const attr = await computeDecisionAttribution({
          stateInput,
          questions: questionsDict,
          baseAnswers,
          client,
          model: selectedModel.value,
          caseMeta: caseObj,
          lang: currentLang.value
        });
        attributionResult.value = attr;
        if (attr && attr.primary_question_id) {
          selectedAttributionQuestion.value = attr.primary_question_id;
        }
      } catch (err) {
        console.warn("Attribution analysis failed:", err);
      }
    };

    const analyzeAttributionNow = async () => {
      if (!result.value || analyzingAttribution.value) return;
      analyzingAttribution.value = true;
      errorMessage.value = "";

      try {
        if (currentCaseId.value === "custom") {
          let st = inputDataText.value.trim();
          try {
            if (st.startsWith("{") || st.startsWith("[")) st = JSON.parse(st);
          } catch (_) {}
          const qDict = buildFormattedQuestionsDict(currentQuestionsSpec.value);
          await runAttributionAnalysis(st, qDict, result.value.answers, null);
          return;
        }

        const caseObj = getCaseById(currentCaseId.value);
        let parsedData = JSON.parse(inputDataText.value);
        const qDict = buildFormattedQuestionsDict(currentQuestionsSpec.value);
        await runAttributionAnalysis(parsedData, qDict, result.value.answers, caseObj);
      } catch (err) {
        errorMessage.value = err.message;
      } finally {
        analyzingAttribution.value = false;
      }
    };

    // 执行当前评估 (100% 纯前端驱动)
    const runCurrentCase = async () => {
      errorMessage.value = "";
      result.value = null;
      attributionResult.value = null;

      if (enableAttribution.value && currentInputCharCount.value > maxCharLimit.value) {
        const isZh = currentLang.value === "zh";
        errorMessage.value = isZh
          ? `输入超出上限 (${currentInputCharCount.value}/${maxCharLimit.value})，请精简内容或调整上限。`
          : `Input exceeds limit (${currentInputCharCount.value}/${maxCharLimit.value}). Please shorten input or increase limit.`;
        return;
      }

      loading.value = true;

      try {
        // 自定义 Playground 模式
        if (currentCaseId.value === "custom") {
          let st = inputDataText.value.trim();
          try {
            if (st.startsWith("{") || st.startsWith("[")) st = JSON.parse(st);
          } catch (_) {}

          if (!currentQuestionsSpec.value || currentQuestionsSpec.value.length === 0) {
            throw new Error(t("questions_empty_err"));
          }

          const qDict = buildFormattedQuestionsDict(currentQuestionsSpec.value);

          const res = await client.executeSystemOne({
            state: st,
            questions: qDict,
            model: selectedModel.value
          });

          result.value = {
            lang: currentLang.value,
            latency_ms: res.latency_ms,
            model_used: res.model_used,
            usage: res.usage,
            answers: res.answers,
            raw_response: res.raw_response,
            workflow: {
              status_tag: "success",
              headline: t("execution_completed"),
              detail: `${Object.keys(res.answers || {}).length} ${t("evaluated_primitives")}, ${res.latency_ms} ms`
            }
          };

          apiKeyValid.value = true;

          if (enableAttribution.value) {
            await runAttributionAnalysis(st, qDict, res.answers, null);
          }
          return;
        }

        // 官方案例模式
        const caseObj = getCaseById(currentCaseId.value);
        if (!caseObj) throw new Error(t("case_not_found"));

        let parsedData;
        try {
          parsedData = JSON.parse(inputDataText.value);
        } catch (e) {
          throw new Error(t("input_format_err") + e.message);
        }

        // 构建 Questions 字典 (优先使用用户在线修改后的 Questions 结构)
        const qDict = buildFormattedQuestionsDict(currentQuestionsSpec.value);
        const { state } = caseObj.buildQuestions(parsedData, currentLang.value);

        const res = await client.executeSystemOne({
          state,
          questions: qDict,
          model: selectedModel.value
        });

        // 触发本地工作流决策解析 (传入当前语言)
        let workflowRes;
        try {
          workflowRes = caseObj.processWorkflow(res.answers, currentLang.value);
        } catch (wfErr) {
          workflowRes = {
            headline: t("execution_completed"),
            status_tag: "success",
            detail: `${Object.keys(res.answers || {}).length} ${t("evaluated_primitives")}`,
            actions: []
          };
        }

        result.value = {
          success: true,
          case_id: currentCaseId.value,
          lang: currentLang.value,
          latency_ms: res.latency_ms,
          model_used: res.model_used,
          usage: res.usage,
          answers: res.answers,
          workflow: workflowRes,
          raw_response: res.raw_response
        };

        apiKeyValid.value = true;

        if (enableAttribution.value) {
          await runAttributionAnalysis(parsedData, qDict, res.answers, caseObj);
        }
      } catch (err) {
        errorMessage.value = err.message;
      } finally {
        loading.value = false;
      }
    };

    watch(maxCharLimit, (val) => {
      if (val && !isNaN(val) && val > 0) {
        localStorage.setItem("JEV_MAX_CHAR_LIMIT", val.toString());
      }
    });

    onMounted(() => {
      // 直接通过纯前端初始化案例，不依赖后端任何接口
      if (cases.value.length > 0) {
        switchCase(cases.value[0].id);
      }
      if (apiKey.value) {
        testCurrentKey();
      }

      window.addEventListener("keydown", (e) => {
        if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'z' && !e.shiftKey) {
          if (!['INPUT', 'TEXTAREA'].includes(document.activeElement?.tagName)) {
            if (activeInputTab.value === 'questions') {
              e.preventDefault();
              undoQuestionEdit();
            } else if (activeInputTab.value === 'state') {
              e.preventDefault();
              undoStateEdit();
            }
          }
        }
      });
    });

    return {
      cases,
      currentCaseId,
      currentCase,
      currentLang,
      activeInputTab,
      stateFields,
      defaultStateData,
      stateUndoHistory,
      stateViewMode,
      stateJsonText,
      stateJsonError,
      isStateDirty,
      undoStateEdit,
      restoreDefaultState,
      setStateViewMode,
      onStateJsonInput,
      formatStateJson,
      addStateField,
      deleteStateField,
      changeStateFieldType,
      onSubJsonInput,
      recordStateFieldFocus,
      recordStateFieldBlur,
      syncJsonFromStateFields,
      currentQuestionsSpec,
      defaultQuestionsSpec,
      undoHistory,
      questionsViewMode,
      questionsJsonText,
      jsonParseError,
      isQuestionsDirty,
      maxCharLimit,
      currentInputCharCount,
      restoreDefaultInput,
      enableAttribution,
      attributionResult,
      selectedAttributionQuestion,
      hoveredToken,
      analyzingAttribution,
      currentAttribution,
      availableAttributionQuestions,
      analyzeAttributionNow,
      recordFieldFocus,
      recordFieldBlur,
      undoQuestionEdit,
      restoreDefaultQuestions,
      setQuestionsViewMode,
      onQuestionsJsonInput,
      formatQuestionsJson,
      addQuestion,
      deleteQuestion,
      changeQuestionType,
      addChoiceOption,
      deleteChoiceOption,
      onChoiceKeyChange,
      addScoreLevel,
      deleteScoreLevel,
      activePresets,
      selectedModel,
      activePresetName,
      inputDataText,
      customPresets: activeCustomPresets,
      activeCustomPresets,
      apiKey,
      apiKeyInput,
      apiBaseUrl,
      apiBaseUrlInput,
      apiKeyValid,
      pingLatency,
      showKeyModal,
      testingKey,
      keyTestMessage,
      loading,
      errorMessage,
      result,
      showRawJson,
      setLang,
      switchCase,
      loadPreset,
      loadCustomPreset,
      testCurrentKey,
      saveApiKey,
      runCurrentCase,
      t
    };
  }
});

app.provide("t", (k) => translate(k, localStorage.getItem("JEV_LANG") || "zh"));

app.component("state-node", {
  name: "StateNode",
  template: "#state-node-template",
  inject: {
    t: {
      default: () => (k) => translate(k, localStorage.getItem("JEV_LANG") || "zh")
    }
  },
  props: {
    node: { type: Object, required: true },
    depth: { type: Number, default: 0 },
    index: { type: Number, default: 0 },
    parentType: { type: String, default: "object" }
  },
  emits: ["change", "focus", "blur", "delete"],
  methods: {
    toggleCollapse() {
      this.node.collapsed = !this.node.collapsed;
    },
    addChild() {
      if (!this.node.children) this.node.children = [];
      this.node.collapsed = false;
      const isArr = this.node.type === "array";
      const key = isArr ? String(this.node.children.length) : `key_${this.node.children.length + 1}`;
      this.node.children.push({
        key,
        type: "string",
        value: "",
        collapsed: false
      });
      this.$emit("change");
    },
    deleteChild(idx) {
      if (this.node.children) {
        this.node.children.splice(idx, 1);
        if (this.node.type === "array") {
          this.node.children.forEach((c, i) => c.key = String(i));
        }
        this.$emit("change");
      }
    },
    changeType(newType) {
      if (this.node.type === newType) return;
      this.node.type = newType;
      if (newType === "object" || newType === "array") {
        this.node.children = [];
        this.node.value = undefined;
        this.node.collapsed = false;
      } else if (newType === "number") {
        this.node.value = Number(this.node.value) || 0;
        this.node.children = undefined;
      } else if (newType === "boolean") {
        this.node.value = Boolean(this.node.value);
        this.node.children = undefined;
      } else {
        this.node.value = String(this.node.value ?? "");
        this.node.children = undefined;
      }
      this.$emit("change");
    }
  }
});

app.mount("#app");
