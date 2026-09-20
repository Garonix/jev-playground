from typing import Dict, Any
from app.cases import smart_home, guardrails, triage, function_call, citation

CASE_MODULES = {
    "smart_home": smart_home,
    "guardrails": guardrails,
    "triage": triage,
    "function_call": function_call,
    "citation": citation,
}

def get_all_cases() -> list[Dict[str, Any]]:
    return [mod.CASE_META for mod in CASE_MODULES.values()]

def get_case(case_id: str):
    return CASE_MODULES.get(case_id)
