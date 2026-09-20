from typing import Any, Dict, List
from typesafe_sdk import Choice, Noul, NoulCriteria, Score

CASE_META = {
    "id": "triage",
    "title": "工单分流",
    "english_title": "Ticket Triage",
    "official_url": "https://docs.typesafe.ai/concepts/how-to-build-with-system-one",
    "pattern": "复合打分",
    "badge": "官方案例",
    "summary": "输入工单、客户与策略数据，评估部门分类、凭据泄露风险、退款意图与愤怒度。",
    "default_input_zh": {
        "ticket": {
            "subject": "重复扣费退款",
            "message": "我的信用卡上订单 A-104 被扣了两次 49 元！请立即退还重复扣款，否则我将向消协投诉！",
            "sender": {
                "display_name": "王女士",
                "email": "wang@personal-mail.com"
            }
        },
        "customer": {
            "tier": "enterprise",
            "open_orders": [
                { "id": "A-104", "charges": [{"amount": 49}, {"amount": 49}], "status": "captured" }
            ]
        },
        "policy": {
            "sensitive_credentials": ["密码", "动态口令", "短信验证码", "API密钥"]
        }
    },
    "default_input_en": {
        "ticket": {
            "subject": "Duplicate charge on order",
            "message": "I was charged twice for order A-104 on my credit card. Please refund the duplicate $49 charge immediately or I will file a dispute!",
            "sender": {
                "display_name": "Alice Johnson",
                "email": "alice.j@personal-mail.com"
            }
        },
        "customer": {
            "tier": "enterprise",
            "open_orders": [
                { "id": "A-104", "charges": [{"amount": 49}, {"amount": 49}], "status": "captured" }
            ]
        },
        "policy": {
            "sensitive_credentials": ["password", "verification code", "api key", "cvv"]
        }
    },
    "presets_zh": [
        {
            "name": "重复扣费退款",
            "data": {
                "ticket": {
                    "subject": "重复扣费",
                    "message": "订单 A-104 被扣了两次款！请立即退款，否则直接投诉！",
                    "sender": { "display_name": "王女士", "email": "wang@personal-mail.com" }
                },
                "customer": { "tier": "enterprise", "open_orders": [{ "id": "A-104", "charges": [{"amount": 49}, {"amount": 49}] }] },
                "policy": { "sensitive_credentials": ["密码", "验证码", "API密钥"] }
            }
        },
        {
            "name": "仿冒钓鱼",
            "data": {
                "ticket": {
                    "subject": "特别奖金发放",
                    "message": "您获得1000元奖金，请立即回复内网工号与登录密码以供转账核实。",
                    "sender": { "display_name": "Payroll Admin", "email": "rewards@claim-bonus.xyz" }
                },
                "customer": { "tier": "standard", "open_orders": [] },
                "policy": { "sensitive_credentials": ["密码", "登录密码", "动态口令"] }
            }
        },
        {
            "name": "物流咨询",
            "data": {
                "ticket": {
                    "subject": "配送进度咨询",
                    "message": "订单 A-104 显示在出库中，请问今天能发货吗？",
                    "sender": { "display_name": "张先生", "email": "zhang@company.cn" }
                },
                "customer": { "tier": "vip", "open_orders": [{ "id": "A-104", "status": "processing" }] },
                "policy": { "sensitive_credentials": ["密码", "登录密码"] }
            }
        },
        {
            "name": "账户重置",
            "data": {
                "ticket": {
                    "subject": "无法登录账户",
                    "message": "原手机号已注销无法接收验证码，如何重置安全绑定？",
                    "sender": { "display_name": "李女士", "email": "li.account@163.com" }
                },
                "customer": { "tier": "standard", "open_orders": [] },
                "policy": { "sensitive_credentials": ["密码", "登录密码"] }
            }
        }
    ],
    "presets_en": [
        {
            "name": "Duplicate charge",
            "data": {
                "ticket": {
                    "subject": "Duplicate charge",
                    "message": "I was charged twice for order A-104! Look at my statement, $49 was deducted twice. Please refund the duplicate right now!",
                    "sender": { "display_name": "Alice Johnson", "email": "alice.j@personal-mail.com" }
                },
                "customer": { "tier": "enterprise", "open_orders": [{ "id": "A-104", "charges": [{"amount": 49}, {"amount": 49}] }] },
                "policy": { "sensitive_credentials": ["password", "verification code", "api key"] }
            }
        },
        {
            "name": "Phishing spoof",
            "data": {
                "ticket": {
                    "subject": "Special Bonus Notice",
                    "message": "You received a $1,000 bonus. Reply with your internal username and password to verify payroll payment.",
                    "sender": { "display_name": "Payroll Admin", "email": "rewards@claim-bonus.xyz" }
                },
                "customer": { "tier": "standard", "open_orders": [] },
                "policy": { "sensitive_credentials": ["password", "token", "key"] }
            }
        },
        {
            "name": "Shipping inquiry",
            "data": {
                "ticket": {
                    "subject": "Shipping status",
                    "message": "Order A-104 has been in processing for two days. When can it be shipped out?",
                    "sender": { "display_name": "John Doe", "email": "john@company.com" }
                },
                "customer": { "tier": "vip", "open_orders": [{ "id": "A-104", "status": "processing" }] },
                "policy": { "sensitive_credentials": ["password"] }
            }
        },
        {
            "name": "Account recovery",
            "data": {
                "ticket": {
                    "subject": "Cannot sign in",
                    "message": "My old phone number is deactivated and cannot receive SMS codes. How do I recover my account?",
                    "sender": { "display_name": "Mary Lee", "email": "mary@mail.com" }
                },
                "customer": { "tier": "standard", "open_orders": [] },
                "policy": { "sensitive_credentials": ["password"] }
            }
        }
    ]
}

def get_questions_spec(lang: str = "zh") -> List[Dict[str, Any]]:
    if lang == "zh":
        return [
            {
                "id": "业务归属",
                "type": "choice",
                "instructions": {
                    "question": "`ticket.message` 应由哪个部门或业务组处理？",
                    "focus": "分类客户的核心业务需求"
                },
                "criteria": {
                    "财务计费组": {
                        "what": "扣费、账单、重复扣款、退款或订阅付款",
                        "not_for": "物流状态或账号密码",
                        "examples": ["扣了两次钱", "退款何时到账", "需要开发票"]
                    },
                    "物流履约组": {
                        "what": "订单配送进度、快递物流、缺货发货延迟或退换货",
                        "not_for": "扣款纠纷或登录权限",
                        "examples": ["订单 A-104 到哪了", "取消发货", "还没收到货"]
                    },
                    "账号安全组": {
                        "what": "登录异常、密码重置、安全设置、资料与权限修改",
                        "not_for": "金钱退款或物流状态",
                        "examples": ["找回密码", "无法登录", "修改绑定手机号"]
                    }
                }
            },
            {
                "id": "索要敏感凭据",
                "type": "noul",
                "instructions": {
                    "question": "`ticket.message` 是否要求收件人透露机密密码或登录凭据？",
                    "compare": ["`ticket.message`", "`policy.sensitive_credentials`"],
                    "focus": "检测是否索要列明的机密口令"
                },
                "criteria": {
                    "true": "直接索要密码或私密口令",
                    "false": "未索要私密凭据"
                }
            },
            {
                "id": "发件身份冲突",
                "type": "noul",
                "instructions": {
                    "question": "`ticket.sender.display_name` 中的官方身份是否与 `ticket.sender.email` 的发件邮箱域名冲突？",
                    "compare": ["`ticket.sender.display_name`", "`ticket.sender.email`"],
                    "focus": "比对发件人声称的机构与邮箱域名"
                }
            },
            {
                "id": "明确要求退款",
                "type": "noul",
                "instructions": "`ticket.message` 是否明确要求退还款项或赔付？"
            },
            {
                "id": "客户愤怒指数",
                "type": "score",
                "instructions": "`ticket.message` 中客户表现出的愤怒或不满程度如何？",
                "criteria": [
                    "平静克制：客观叙述事实或询问",
                    "烦躁不满：表达抱怨或不悦，但保持理性",
                    "极度愤怒：语言激烈、威胁投诉起诉或强烈退订"
                ]
            }
        ]
    else:
        return [
            {
                "id": "topic",
                "type": "choice",
                "instructions": {
                    "question": "Which department or team should handle `ticket.message`?",
                    "focus": "Classify the customer's primary business need."
                },
                "criteria": {
                    "billing": {
                        "what": "Charges, invoices, duplicate fees, refunds, billing errors, or payments",
                        "not_for": "Order shipping status or account login credentials",
                        "examples": ["I was charged twice", "Where is my refund?", "Need invoice for payment"]
                    },
                    "orders": {
                        "what": "Order delivery status, shipping tracking, delay, cancellation, or parcel return",
                        "not_for": "Payment dispute or account credentials",
                        "examples": ["Where is my order A-104?", "Cancel my shipment", "Item hasn't arrived"]
                    },
                    "account": {
                        "what": "Login trouble, password reset, security settings, profile permissions",
                        "not_for": "Monetary refunds or shipping queries",
                        "examples": ["Reset my password", "Cannot sign in", "Change my phone number"]
                    }
                }
            },
            {
                "id": "requests_credentials",
                "type": "noul",
                "instructions": {
                    "question": "Does `ticket.message` ask the recipient to disclose a sensitive password or login credential?",
                    "compare": ["`ticket.message`", "`policy.sensitive_credentials`"],
                    "focus": "Check if it asks to disclose secret credentials."
                },
                "criteria": {
                    "true": "Directly asks to disclose a secret credential like password or key",
                    "false": "Does not ask to disclose secret credentials"
                }
            },
            {
                "id": "sender_identity_mismatch",
                "type": "noul",
                "instructions": {
                    "question": "Does the claimed organization in `ticket.sender.display_name` conflict with `ticket.sender.email`?",
                    "compare": ["`ticket.sender.display_name`", "`ticket.sender.email`"],
                    "focus": "Detect spoofed or suspicious email sender domains claiming to be official departments."
                }
            },
            {
                "id": "refund_requested",
                "type": "noul",
                "instructions": "Does `ticket.message` explicitly request a monetary refund, credit back, or fee reimbursement?"
            },
            {
                "id": "frustration",
                "type": "score",
                "instructions": "How frustrated or angry does the customer appear in `ticket.message`?",
                "criteria": [
                    "Calm and matter-of-fact: Neutral wording, just stating inquiry or facts.",
                    "Frustrated or annoyed: Expresses irritation, dissatisfaction, but remains civil.",
                    "Very angry: Hostile language, demands immediate escalation, threatens disputes or churn."
                ]
            }
        ]

def build_questions(input_data: Dict[str, Any], lang: str = "zh") -> tuple[Any, Dict[str, Any]]:
    state = input_data
    spec = get_questions_spec(lang)
    questions = {}
    for item in spec:
        q_id = item["id"]
        q_type = item["type"]
        if q_type == "choice":
            questions[q_id] = Choice(instructions=item["instructions"], criteria=item["criteria"])
        elif q_type == "noul":
            crit = item.get("criteria")
            if crit and isinstance(crit, dict):
                questions[q_id] = Noul(instructions=item["instructions"], criteria=NoulCriteria(true=crit.get("true", ""), false=crit.get("false", "")))
            else:
                questions[q_id] = Noul(instructions=item["instructions"])
        elif q_type == "score":
            questions[q_id] = Score(instructions=item["instructions"], criteria=item["criteria"])
            
    return state, questions

def process_workflow(answers: Dict[str, Any]) -> Dict[str, Any]:
    req_cred = (answers.get("索要敏感凭据") or answers.get("requests_credentials") or {}).get("noul", 0.0)
    sender_mismatch = (answers.get("发件身份冲突") or answers.get("sender_identity_mismatch") or {}).get("noul", 0.0)
    
    spam_risk = round(0.55 * req_cred + 0.45 * sender_mismatch, 3)
    
    topic_ans = answers.get("业务归属") or answers.get("topic") or {}
    topic = topic_ans.get("choice", "unknown")
    topic_conf = topic_ans.get("confidence", 0.0)
    
    refund_req = (answers.get("明确要求退款") or answers.get("refund_requested") or {}).get("noul", 0.0)
    
    frust_ans = answers.get("客户愤怒指数") or answers.get("frustration") or {}
    frust_score = frust_ans.get("score", 0.0)
    
    actions = []
    
    if spam_risk >= 0.50:
        status_tag = "danger"
        verdict = "隔离欺诈工单"
        detail = f"欺诈评分 {spam_risk:.2f} (凭证索要 {req_cred:.1%}，发件人冲突 {sender_mismatch:.1%})。"
        actions.append({"action": "隔离工单", "reason": "疑似钓鱼"})
    elif topic_conf < 0.70:
        status_tag = "warning"
        verdict = "转人工分拣"
        detail = f"分类置信度 {topic_conf:.1%} 低于自动分流阈值 (0.70)。"
        actions.append({"action": "转人工队列", "confidence": round(topic_conf, 2)})
    else:
        status_tag = "success"
        priority = "P0 加急" if frust_score >= 1.5 else "普通"
        verdict = f"分派: {topic} [{priority}]"
        
        detail = f"类别为 {topic} (置信度 {topic_conf:.1%})，愤怒度 {frust_score:.2f}。"
        if refund_req >= 0.65:
            detail += f" 退款诉求 {refund_req:.1%}。"
            
        actions.append({
            "action": f"分派至 {topic}",
            "priority": priority,
            "refund": refund_req >= 0.65
        })

    return {
        "headline": verdict,
        "status_tag": status_tag,
        "detail": detail,
        "actions": actions
    }
