/**
 * Jev Playground 国际化 (i18n) 字典与解析引擎
 * 严格遵循第一性原理：中英文模式下全界面彻底统一，除技术专有名词外杜绝混杂。
 */

export const TRANSLATIONS = {
  zh: {
    // 侧边栏 & 案例分类
    cases_title: "官方案例",
    experiment: "实验",
    custom_playground: "自定义",
    official_docs: "官方文档",
    author: "作者",

    // 头部 & 预设
    presets: "预设",
    lang_zh: "中",
    lang_en: "EN",

    // 选项卡
    tab_state: "State",
    tab_questions: "Questions",
    tab_results: "结果",

    // 工具栏操作
    undo: "撤销",
    reset: "重置",
    add_field: "+ 字段",
    add_item: "+ 子项",
    add_question: "+ 问题",
    add_option: "+ 选项",
    add_level: "+ 档位",
    delete: "删除",
    format: "格式化",
    chars: "字符",
    chars_count: "字符",
    view_block: "块",
    view_cards: "卡片",
    view_json: "JSON",

    // 编辑器空状态与提示
    no_fields: "暂无字段定义，请点击 \"+ 字段\" 添加",
    no_items: "暂无子项，可点击 \"+ 子项\" 添加",
    no_questions: "暂无问题定义，请点击 \"+ 问题\" 添加",
    placeholder_key: "键名",
    placeholder_text: "文本内容",
    placeholder_instructions: "指令文本",
    placeholder_option_key: "选项 Key",
    placeholder_option_desc: "选项说明",
    placeholder_level_desc: "档位说明",
    placeholder_true_cond: "True 判定条件",
    placeholder_false_cond: "False 判定条件",
    items_count: "项",
    instructions_label: "指令",
    options_label: "选项",
    levels_label: "档位",
    criteria_label: "判定条件",

    // 语法错误与字符溢出
    syntax_error: "语法错误",
    char_overflow: "超出字符上限",
    json_invalid_switch: "JSON 格式有误，无法切换：",
    json_must_be_array: "必须为合法 JSON 数组格式",
    questions_empty_err: "Questions 结构不能为空，请至少添加一个问题",
    case_not_found: "未找到当前案例",
    input_format_err: "输入格式错误，须为合法 JSON：",

    // 执行与归因底栏
    token_attribution: "Token 归因",
    execute: "执行",
    executing: "执行中...",
    waiting_execution: "等待执行",

    // 结果面板与动作流
    workflow_actions: "动作流",
    execution_completed: "执行完成",
    evaluated_primitives: "个原语已完成推理",
    latency_ms: "ms",
    tokens: "tokens",

    // Token 归因视图
    attribution_title: "Token 归因",
    output_label: "输出:",
    confidence_label: "置信度:",
    saliency_stream: "显著性",
    positive: "正向",
    neutral: "中立",
    negative: "负向",
    token_label: "Token:",
    contribution_label: "贡献:",
    ablation_label: "消融:",
    top_drivers: "Top 贡献:",
    balanced_distribution: "贡献分布均衡",
    attr_not_calculated: "未计算归因",
    calculate_attr: "计算 Token 归因",
    calculating_attr: "计算归因中...",
    analyzed_input_field: "输入文本",

    // 原语明细
    primitives_detail: "原语明细",
    score_label: "得分:",
    probability_label: "概率:",
    raw_json: "原始 JSON",
    expand: "展开",
    collapse: "收起",

    // API 设置模态框
    api_settings: "API 设置",
    api_key_label: "TypeSafe API Key",
    mock_mode: "离线模拟 (mock)",
    placeholder_api_key: "API Key 或填 mock",
    base_url_label: "服务地址 (Base URL)",
    placeholder_base_url: "https://api.typesafe.ai 或 Worker 代理地址",
    test_connection: "测试",
    testing_connection: "测试中...",
    connected_msg: "已连接",
    disconnected_msg: "未连接",
    cancel: "取消",
    save: "保存"
  },

  en: {
    // Sidebar & Cases
    cases_title: "Official Cases",
    experiment: "Experiment",
    custom_playground: "Custom",
    official_docs: "Documentation",
    author: "Author",

    // Header & Presets
    presets: "Presets",
    lang_zh: "中",
    lang_en: "EN",

    // Tabs
    tab_state: "State",
    tab_questions: "Questions",
    tab_results: "Results",

    // Toolbar actions
    undo: "Undo",
    reset: "Reset",
    add_field: "+ Field",
    add_item: "+ Item",
    add_question: "+ Question",
    add_option: "+ Option",
    add_level: "+ Level",
    delete: "Delete",
    format: "Format",
    chars: "Chars",
    chars_count: "Chars",
    view_block: "Block",
    view_cards: "Cards",
    view_json: "JSON",

    // Editor empty states & placeholders
    no_fields: "No fields defined. Click \"+ Field\" to add",
    no_items: "No items. Click \"+ Item\" to add",
    no_questions: "No questions defined. Click \"+ Question\" to add",
    placeholder_key: "Key",
    placeholder_text: "Text content",
    placeholder_instructions: "Instruction text",
    placeholder_option_key: "Option Key",
    placeholder_option_desc: "Option description",
    placeholder_level_desc: "Level description",
    placeholder_true_cond: "True criteria",
    placeholder_false_cond: "False criteria",
    items_count: "items",
    instructions_label: "Instructions",
    options_label: "Options",
    levels_label: "Levels",
    criteria_label: "Criteria",

    // Syntax errors & limits
    syntax_error: "Syntax Error",
    char_overflow: "Exceeds char limit",
    json_invalid_switch: "Invalid JSON syntax, cannot switch: ",
    json_must_be_array: "Must be a valid JSON array format",
    questions_empty_err: "Questions cannot be empty. Please add at least one question.",
    case_not_found: "Current case not found",
    input_format_err: "Invalid input format, must be valid JSON: ",

    // Execution bar
    token_attribution: "Token Attribution",
    execute: "Execute",
    executing: "Executing...",
    waiting_execution: "Awaiting execution",

    // Results & Workflow
    workflow_actions: "Workflow Actions",
    execution_completed: "Execution Completed",
    evaluated_primitives: "primitives evaluated",
    latency_ms: "ms",
    tokens: "tokens",

    // Token Attribution View
    attribution_title: "Token Attribution",
    output_label: "Output:",
    confidence_label: "Confidence:",
    saliency_stream: "Saliency",
    positive: "Positive",
    neutral: "Neutral",
    negative: "Negative",
    token_label: "Token:",
    contribution_label: "Contribution:",
    ablation_label: "Ablation:",
    top_drivers: "Top Drivers:",
    balanced_distribution: "Evenly distributed",
    attr_not_calculated: "Attribution not calculated",
    calculate_attr: "Calculate Token Attribution",
    calculating_attr: "Calculating...",
    analyzed_input_field: "Input Text",

    // Primitive Answers
    primitives_detail: "Primitive Answers",
    score_label: "Score:",
    probability_label: "Probability:",
    raw_json: "Raw JSON",
    expand: "Expand",
    collapse: "Collapse",

    // API Settings Modal
    api_settings: "API Settings",
    api_key_label: "TypeSafe API Key",
    mock_mode: "Offline Mock (mock)",
    placeholder_api_key: "API Key or type mock",
    base_url_label: "Service Endpoint (Base URL)",
    placeholder_base_url: "https://api.typesafe.ai or Worker URL",
    test_connection: "Test",
    testing_connection: "Testing...",
    connected_msg: "Connected",
    disconnected_msg: "Disconnected",
    cancel: "Cancel",
    save: "Save"
  }
};

/**
 * 翻译解析函数
 */
export function translate(key, lang = "zh") {
  const dict = TRANSLATIONS[lang] || TRANSLATIONS.zh;
  return dict[key] !== undefined ? dict[key] : key;
}
