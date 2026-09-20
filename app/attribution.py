import asyncio
import copy
import logging
import re
from typing import Any, Dict, List, Optional, Set, Tuple

import jieba
from app.jev_client import execute_system_one

logger = logging.getLogger(__name__)

# 预热 jieba 词典以避免首次调用延迟
jieba.initialize()

# 纯标点与无决策语义的极高频虚助词集合
# 当输入文本偏长时，跳过对这些纯语法连接词的单独消融，节约 API 资源，同时避免误伤实词
LIGHT_STOPWORDS: Set[str] = {
    "，", "。", "！", "？", "、", "；", "：", "“", "”", "‘", "’", "（", "）", "—", "…", "～",
    ",", ".", "!", "?", ";", ":", "\"", "'", "(", ")", "-", "_", "/", "\\",
    "的", "了", "在", "着", "过", "和", "跟", "同", "与", "以及", "并", "并且", "就", "也", "又",
    "啊", "吗", "呢", "吧", "呀", "啦"
}

def tokenize_text(text: str) -> List[str]:
    """
    对文本进行纯粹细粒度分词，严禁机械短句合并。
    保持自然分词单元（单个实词、单字、单词与标点）。
    """
    text = (text or "").strip()
    if not text:
        return []
    
    has_chinese = bool(re.search(r"[\u4e00-\u9fff]", text))
    if has_chinese:
        tokens = [t for t in jieba.cut(text) if t.strip()]
    else:
        tokens = [t for t in re.findall(r"\b\w+\b|[^\w\s]", text) if t.strip()]
    
    return tokens

def extract_primary_text_field(input_data: Any) -> Tuple[Optional[str], str]:
    """
    从输入数据中智能定位最主要且具有自然语言决策意义的文本字段与内容。
    返回: (field_key_or_path, text_content)
    """
    if isinstance(input_data, str):
        return None, input_data
    
    if not isinstance(input_data, dict):
        return None, str(input_data)
    
    # 优先寻找核心指令或长文本字段
    priority_keys = [
        "user_request", "message", "chief_complaint", "claim", 
        "text", "content", "query", "request", "state", "source_context"
    ]
    
    for pk in priority_keys:
        val = input_data.get(pk)
        if isinstance(val, str) and len(val.strip()) > 1:
            return pk, val.strip()
    
    # 兜底：挑选长度最长的字符串字段
    longest_key = None
    longest_val = ""
    for k, v in input_data.items():
        if isinstance(v, str) and len(v.strip()) > len(longest_val):
            longest_key = k
            longest_val = v.strip()
            
    return longest_key, longest_val

def replace_field_value(data: Any, field_key: Optional[str], new_val: str) -> Any:
    """
    将深拷贝的数据对象中指定字段的值替换为新值。
    """
    if field_key is None:
        return new_val
    if isinstance(data, dict):
        cloned = copy.deepcopy(data)
        cloned[field_key] = new_val
        return cloned
    return new_val

def build_fine_grained_ablations(
    text: str, 
    tokens: List[str], 
    max_ablate_count: int = 28
) -> Tuple[List[Tuple[int, str, str]], Set[int]]:
    """
    构建原子级单词消融变体。
    返回: ([(token_index, token_removed, ablated_text), ...], skipped_indices)
    """
    has_chinese = bool(re.search(r"[\u4e00-\u9fff]", text))
    sep = "" if has_chinese else " "
    
    # 识别无需消融的纯标点与虚词索引
    skipped_indices = set()
    candidate_indices = []
    
    for i, tok in enumerate(tokens):
        if tok in LIGHT_STOPWORDS:
            skipped_indices.add(i)
        else:
            candidate_indices.append(i)
    
    # 如果实词仍超过最大上限，优先保留较长且高信息密度的前 N 个实词做消融
    if len(candidate_indices) > max_ablate_count:
        # 按重要度排序截断（长词、非数字纯字母/汉字优先）
        candidate_indices = sorted(candidate_indices, key=lambda idx: len(tokens[idx]), reverse=True)[:max_ablate_count]
        candidate_indices.sort()  # 恢复文本序
        
        # 其余的记为跳过
        for i in range(len(tokens)):
            if i not in candidate_indices:
                skipped_indices.add(i)
                
    ablations = []
    for i in candidate_indices:
        tok = tokens[i]
        remaining = [tokens[j] for j in range(len(tokens)) if j != i]
        ablated = sep.join(remaining).strip()
        ablations.append((i, tok, ablated))
        
    return ablations, skipped_indices

async def compute_decision_attribution(
    state_input: Any,
    questions: Dict[str, Any],
    base_answers: Dict[str, Any],
    api_key: str,
    model: str,
    case_mod: Optional[Any] = None,
    lang: str = "zh",
    max_tokens: int = 30
) -> Dict[str, Any]:
    """
    通过因果反事实消融计算各单字/单词对模型决策的推动贡献度。
    严格维持真实原子级粒度，杜绝粗暴拼装短句导致的共线性污染与语法破碎畸变。
    """
    field_key, text_content = extract_primary_text_field(state_input)
    if not text_content:
        return {
            "field_analyzed": field_key or "state",
            "text": "",
            "tokens": [],
            "questions_attribution": {}
        }
    
    # 1. 纯粹原子级分词
    tokens = tokenize_text(text_content)
    if not tokens:
        return {
            "field_analyzed": field_key or "state",
            "text": text_content,
            "tokens": [],
            "questions_attribution": {}
        }
    
    # 2. 生成细粒度消融文本
    ablations, skipped_indices = build_fine_grained_ablations(text_content, tokens, max_ablate_count=max_tokens)
    
    # 3. 构造消融后的 state 变体
    ablated_states = []
    for idx, tok, ablated_text in ablations:
        new_state_input = replace_field_value(state_input, field_key, ablated_text)
        if case_mod and hasattr(case_mod, "build_questions"):
            st, _ = case_mod.build_questions(new_state_input, lang=lang)
        else:
            st = new_state_input
        ablated_states.append((idx, tok, st))
    
    # 4. 并发限流执行消融推理（使用 Semaphore 保证吞吐与安全）
    sem = asyncio.Semaphore(12)
    
    async def run_ablate_task(idx: int, tok: str, st: Any):
        async with sem:
            try:
                res = await execute_system_one(
                    state=st,
                    questions=questions,
                    api_key=api_key,
                    model=model
                )
                return idx, tok, res.get("answers", {})
            except Exception as ex:
                logger.warning("Ablation request for token '%s' (idx=%d) failed: %s", tok, idx, ex)
                return idx, tok, None

    tasks = [run_ablate_task(idx, tok, st) for idx, tok, st in ablated_states]
    results = await asyncio.gather(*tasks)
    
    # 5. 将消融结果按原始 token 索引映射
    results_by_index: Dict[int, Optional[Dict[str, Any]]] = {}
    for idx, tok, answers in results:
        results_by_index[idx] = answers
        
    # 6. 计算每个原语下每个原子 Token 的决策因果边际贡献
    questions_attribution = {}
    
    for q_id, base_ans in base_answers.items():
        q_type = base_ans.get("type", "choice")
        
        token_stats = []
        winner_label = ""
        base_metric = 0.0
        
        if q_type == "choice":
            winner_label = base_ans.get("choice", "")
            base_probs = base_ans.get("probabilities") or {}
            base_metric = base_probs.get(winner_label)
            if base_metric is None:
                base_metric = base_ans.get("confidence", 0.5)
            
            for i, tok in enumerate(tokens):
                if i in skipped_indices:
                    # 标点与天然虚词，因果作用视为中立 0
                    token_stats.append({
                        "token": tok,
                        "delta": 0.0,
                        "base_val": round(base_metric, 4),
                        "ablated_val": round(base_metric, 4),
                        "weight": 0.0,
                        "type": "neutral"
                    })
                    continue
                
                ab_ans = results_by_index.get(i)
                if not ab_ans or q_id not in ab_ans:
                    delta = 0.0
                    ablated_prob = base_metric
                else:
                    ab_info = ab_ans[q_id]
                    ab_probs = ab_info.get("probabilities") or {}
                    ablated_prob = ab_probs.get(winner_label)
                    if ablated_prob is None:
                        ablated_prob = ab_info.get("confidence", 0.0) if ab_info.get("choice") == winner_label else 0.0
                    delta = base_metric - ablated_prob
                
                token_stats.append({
                    "token": tok,
                    "delta": round(delta, 4),
                    "base_val": round(base_metric, 4),
                    "ablated_val": round(ablated_prob, 4),
                })
                
        elif q_type == "score":
            base_metric = base_ans.get("score", 0.0)
            winner_label = f"{base_metric:.2f}"
            for i, tok in enumerate(tokens):
                if i in skipped_indices:
                    token_stats.append({
                        "token": tok,
                        "delta": 0.0,
                        "base_val": round(base_metric, 4),
                        "ablated_val": round(base_metric, 4),
                        "weight": 0.0,
                        "type": "neutral"
                    })
                    continue
                
                ab_ans = results_by_index.get(i)
                if not ab_ans or q_id not in ab_ans:
                    delta = 0.0
                    ablated_score = base_metric
                else:
                    ab_info = ab_ans[q_id]
                    ablated_score = ab_info.get("score", base_metric)
                    delta = base_metric - ablated_score
                
                token_stats.append({
                    "token": tok,
                    "delta": round(delta, 4),
                    "base_val": round(base_metric, 4),
                    "ablated_val": round(ablated_score, 4),
                })
                
        elif q_type == "noul":
            base_metric = base_ans.get("noul", 0.0)
            winner_label = f"{base_metric:.1%}"
            for i, tok in enumerate(tokens):
                if i in skipped_indices:
                    token_stats.append({
                        "token": tok,
                        "delta": 0.0,
                        "base_val": round(base_metric, 4),
                        "ablated_val": round(base_metric, 4),
                        "weight": 0.0,
                        "type": "neutral"
                    })
                    continue
                
                ab_ans = results_by_index.get(i)
                if not ab_ans or q_id not in ab_ans:
                    delta = 0.0
                    ablated_noul = base_metric
                else:
                    ab_info = ab_ans[q_id]
                    ablated_noul = ab_info.get("noul", base_metric)
                    delta = base_metric - ablated_noul
                
                token_stats.append({
                    "token": tok,
                    "delta": round(delta, 4),
                    "base_val": round(base_metric, 4),
                    "ablated_val": round(ablated_noul, 4),
                })
        else:
            continue
        
        # 7. 计算归一化相对权重
        pos_deltas = [max(0.0, s["delta"]) for s in token_stats if "weight" not in s]
        max_pos = max(pos_deltas) if pos_deltas else 0.0
        
        for s in token_stats:
            if "weight" in s:
                continue
            d = s["delta"]
            if max_pos > 0.001 and d > 0:
                s["weight"] = round(d / max_pos, 3)
                s["type"] = "positive"
            elif d < -0.05:
                s["weight"] = round(abs(d), 3)
                s["type"] = "negative"
            else:
                s["weight"] = 0.0
                s["type"] = "neutral"
        
        # 提取推动贡献前 3 的核心词
        top_drivers = sorted(
            [s for s in token_stats if s["delta"] > 0.01], 
            key=lambda x: x["delta"], 
            reverse=True
        )[:3]
        
        questions_attribution[q_id] = {
            "type": q_type,
            "winner": winner_label,
            "base_val": base_metric,
            "tokens": token_stats,
            "top_drivers": top_drivers
        }
    
    primary_q_id = list(questions_attribution.keys())[0] if questions_attribution else ""
    
    return {
        "field_analyzed": field_key or "输入文本",
        "text": text_content,
        "tokens_count": len(tokens),
        "primary_question_id": primary_q_id,
        "questions_attribution": questions_attribution
    }
