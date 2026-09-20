from typing import Any, Dict, List
from typesafe_sdk import Choice, Score

CASE_META = {
    "id": "citation",
    "title": "引用核查",
    "english_title": "Citation Check",
    "official_url": "https://docs.typesafe.ai/cookbooks/citation_check",
    "pattern": "事实比对",
    "badge": "官方案例",
    "summary": "针对知识库 RAG 问答，交叉核查引用依据与模型断言的真实语义关系。",
    "default_input_zh": {
        "source_context": "根据《企业职工带薪年休假实施办法》第三条：职工连续工作满12个月以上的，享受带薪年休假。职工在同一或者不同用人单位工作期间，以及依照法律、行政法规或者国务院规定视同工作期间，应当计为累计工作时间。",
        "claim": "员工只要累计工作时间连续满12个月以上就依法享有带薪年休假，且之前的用人单位工作时间同样计入累计工龄。"
    },
    "default_input_en": {
        "source_context": "RFC 7519 (Section 4.1.4): The 'exp' (expiration time) claim identifies the expiration time on or after which the JWT MUST NOT be accepted for processing. The processing of the 'exp' claim requires that the current date/time MUST be before the expiration date/time listed in the 'exp' claim. Implementers MAY provide for some small leeway, usually no more than a few minutes, to account for clock skew.",
        "claim": "Under RFC 7519 specifications, implementations must strictly reject tokens after 'exp' and are forbidden from allowing any leeway or tolerance for clock skew."
    },
    "presets_zh": [
        {
            "name": "真实支持",
            "data": {
                "source_context": "根据《企业职工带薪年休假实施办法》第三条：职工连续工作满12个月以上的，享受带薪年休假。职工在同一或者不同用人单位工作期间，以及依照法律、行政法规或者国务院规定视同工作期间，应当计为累计工作时间。",
                "claim": "员工只要累计工作时间连续满12个月以上就依法享有带薪年休假，且之前的用人单位工作时间同样计入累计工龄。"
            }
        },
        {
            "name": "概念矛盾",
            "data": {
                "source_context": "规范说明：处理 'exp' 声明需要当前日期时间必须早于 'exp' 声明中列出的到期时间。实现可能会提供小的宽限期（通常为几分钟）以解决时钟偏移问题。",
                "claim": "规范强制要求系统在超过 exp 时无条件立刻拒绝，严禁实现任何宽限期或时钟偏移容差。"
            }
        },
        {
            "name": "缺乏依据",
            "data": {
                "source_context": "生产集群数据库部署规范：核心交易数据库必须采用主从双机热备架构，开启二进制日志(binlog)，且每日凌晨2点自动执行全量冷备份并异地归档保存不少于180天。",
                "claim": "生产集群规范建议开发测试阶段为了节省成本，可以直接使用单机非备份数据库作为生产环境过渡。"
            }
        }
    ],
    "presets_en": [
        {
            "name": "Contradicted claim",
            "data": {
                "source_context": "RFC 7519 (Section 4.1.4): The 'exp' (expiration time) claim identifies the expiration time on or after which the JWT MUST NOT be accepted for processing. The processing of the 'exp' claim requires that the current date/time MUST be before the expiration date/time listed in the 'exp' claim. Implementers MAY provide for some small leeway, usually no more than a few minutes, to account for clock skew.",
                "claim": "Under RFC 7519 specifications, implementations must strictly reject tokens after 'exp' and are forbidden from allowing any leeway or tolerance for clock skew."
            }
        },
        {
            "name": "Verified claim",
            "data": {
                "source_context": "RFC 7519 (Section 4.1.4): The processing of the 'exp' claim requires that the current date/time MUST be before the expiration date/time listed in the 'exp' claim. Implementers MAY provide for some small leeway, usually no more than a few minutes, to account for clock skew.",
                "claim": "Implementers are permitted to provide a small leeway of a few minutes to account for clock skew when checking token expiration."
            }
        },
        {
            "name": "Unsupported citation",
            "data": {
                "source_context": "Production database standard: Core transaction databases must use primary-replica hot standby with binlog enabled, and perform full cold backups daily at 2 AM archived offsite for at least 180 days.",
                "claim": "The production database standard recommends transitioning directly with a single-instance non-backed-up database to save dev costs."
            }
        }
    ]
}

def get_questions_spec(lang: str = "zh") -> List[Dict[str, Any]]:
    if lang == "zh":
        return [
            {
                "id": "引用事实关系",
                "type": "choice",
                "instructions": {
                    "question": "`source_context` 与 `claim` 中断言的事实关系如何？",
                    "focus": "评估原文依据是否真实确凿地支撑该断言"
                },
                "criteria": {
                    "证实支持": {
                        "what": "原文依据直接且准确地支持、证实或推导出该断言",
                        "not_for": "与原文矛盾或原文未提及的断言"
                    },
                    "事实矛盾": {
                        "what": "原文依据直接矛盾、反驳或推翻该断言",
                        "not_for": "仅讨论不同主题但无矛盾的断言"
                    },
                    "缺乏依据": {
                        "what": "原文依据不足以证明该断言，或原文对该特定断言保持沉默",
                        "not_for": "直接支持或直接矛盾的断言"
                    }
                }
            },
            {
                "id": "主题相关程度",
                "type": "score",
                "instructions": "`source_context` 与 `claim` 讨论主题的相关度如何？",
                "criteria": [
                    "完全无关：讨论完全不同的领域或概念",
                    "部分相关：涉及相关概念但关注面不同",
                    "高度相关：直接针对断言所讨论的核心议题"
                ]
            }
        ]
    else:
        return [
            {
                "id": "citation_verdict",
                "type": "choice",
                "instructions": {
                    "question": "How does `source_context` relate to the claim stated in `claim`?",
                    "focus": "Evaluate whether the source passage accurately and factually supports the claim."
                },
                "criteria": {
                    "verified": {
                        "what": "The source context directly and accurately supports, confirms, or proves the claim.",
                        "not_for": "Claims that contradict the context or claim things not mentioned in the context."
                    },
                    "contradicted": {
                        "what": "The source context directly contradicts, refutes, or says the opposite of the claim.",
                        "not_for": "Passages that merely discuss an unrelated topic without contradiction."
                    },
                    "unsupported": {
                        "what": "The source context does not provide sufficient evidence to substantiate the claim, or is silent on the specific assertion.",
                        "not_for": "Direct confirmations or direct contradictions."
                    }
                }
            },
            {
                "id": "relevance",
                "type": "score",
                "instructions": "How relevant is `source_context` to the topic discussed in `claim`?",
                "criteria": [
                    "Completely unrelated: Discusses entirely different concepts or domains.",
                    "Partially related: Touches on related themes but focuses on different aspects.",
                    "Highly relevant: Directly addresses the exact subject matter of the claim."
                ]
            }
        ]

def build_questions(input_data: Dict[str, Any], lang: str = "zh") -> tuple[Any, Dict[str, Any]]:
    state = {
        "source_context": input_data.get("source_context", ""),
        "claim": input_data.get("claim", "")
    }
    spec = get_questions_spec(lang)
    questions = {}
    for item in spec:
        q_id = item["id"]
        q_type = item["type"]
        if q_type == "choice":
            questions[q_id] = Choice(instructions=item["instructions"], criteria=item["criteria"])
        elif q_type == "score":
            questions[q_id] = Score(instructions=item["instructions"], criteria=item["criteria"])
            
    return state, questions

def process_workflow(answers: Dict[str, Any]) -> Dict[str, Any]:
    verdict_ans = answers.get("引用事实关系") or answers.get("citation_verdict") or {}
    verdict = verdict_ans.get("choice", "unsupported")
    conf = verdict_ans.get("confidence", 0.0)
    
    rel_ans = answers.get("主题相关程度") or answers.get("relevance") or {}
    rel_score = rel_ans.get("score", 0.0)
    
    actions = []
    
    if verdict in ["事实矛盾", "contradicted"]:
        status_tag = "danger"
        headline = "事实矛盾"
        detail = f"断言与依据存在事实冲突 (置信度 {conf:.1%})。"
        actions.append({"action": "拦截回答", "reason": "发现幻觉"})
    elif verdict in ["缺乏依据", "unsupported"]:
        status_tag = "warning"
        headline = "证据不足"
        detail = f"依据未提及断言断定的内容 (置信度 {conf:.1%})。"
        actions.append({"action": "提示引用缺失", "flag": "unsupported"})
    elif verdict in ["证实支持", "verified"]:
        if conf >= 0.80:
            status_tag = "success"
            headline = "核实通过"
            detail = f"依据充分支撑断言 (置信度 {conf:.1%}，相关度 {rel_score:.2f})。"
            actions.append({"action": "放行回答", "badge": "verified"})
        else:
            status_tag = "warning"
            headline = "置信度偏低"
            detail = f"判定为支持，但置信度 {conf:.1%} 未达自动放行线 (0.80)。"
            actions.append({"action": "转人工复验", "priority": "low"})
    else:
        status_tag = "info"
        headline = f"判定: {verdict}"
        detail = f"置信度 {conf:.1%}"

    return {
        "headline": headline,
        "status_tag": status_tag,
        "detail": detail,
        "actions": actions
    }
