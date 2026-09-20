import os
import json
import logging
from typing import Any, Dict, Optional
from fastapi import FastAPI, Header, HTTPException, Query, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import httpx

from app.config import DEFAULT_MODEL, DEFAULT_API_KEY
from app.jev_client import test_api_key, execute_system_one
from app.cases import get_all_cases, get_case
from typesafe_sdk import Choice, Score, Noul, NoulCriteria

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("jev_app")

app = FastAPI(
    title="Jev Playground",
    description="TypeSafe Jev System One 决策模型现代化评测工作台",
    version="1.2.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.attribution import compute_decision_attribution

class RunCaseRequest(BaseModel):
    input_data: Dict[str, Any]
    model: Optional[str] = None
    lang: Optional[str] = "zh"
    custom_questions: Optional[list[Dict[str, Any]]] = None
    explain: Optional[bool] = False

class CustomQuestion(BaseModel):
    id: str
    type: str  # choice, score, noul
    instructions: Any
    criteria: Optional[Any] = None

class RunCustomRequest(BaseModel):
    state: Any
    questions: list[CustomQuestion]
    model: Optional[str] = None
    explain: Optional[bool] = False

class ExplainCaseRequest(BaseModel):
    input_data: Dict[str, Any]
    base_answers: Dict[str, Any]
    model: Optional[str] = None
    lang: Optional[str] = "zh"
    custom_questions: Optional[list[Dict[str, Any]]] = None

@app.get("/api/cases")
async def list_cases():
    return {
        "cases": get_all_cases(),
        "default_model": DEFAULT_MODEL,
        "has_server_api_key": bool(DEFAULT_API_KEY)
    }

@app.get("/api/case_questions/{case_id}")
async def get_case_questions(case_id: str, lang: str = Query("zh")):
    case_mod = get_case(case_id)
    if not case_mod:
        raise HTTPException(status_code=404, detail=f"未找到案例: {case_id}")
    
    if hasattr(case_mod, "get_questions_spec"):
        return {
            "case_id": case_id,
            "lang": lang,
            "questions": case_mod.get_questions_spec(lang)
        }
    return {"case_id": case_id, "lang": lang, "questions": []}

@app.get("/api/check_key")
async def check_key(x_typesafe_api_key: Optional[str] = Header(None)):
    return await test_api_key(x_typesafe_api_key)

@app.post("/api/run_case/{case_id}")
async def run_official_case(
    case_id: str,
    payload: RunCaseRequest,
    x_typesafe_api_key: Optional[str] = Header(None)
):
    case_mod = get_case(case_id)
    if not case_mod:
        raise HTTPException(status_code=404, detail=f"未找到案例: {case_id}")
    
    api_key = (x_typesafe_api_key or "").strip() or DEFAULT_API_KEY
    if not api_key:
        raise HTTPException(
            status_code=400,
            detail="缺少 API Key。请在页面右上角填入您的 TypeSafe API Key 或在服务器环境变量配置 TYPESAFE_API_KEY。"
        )

    try:
        lang = payload.lang or "zh"
        if payload.custom_questions:
            questions_dict = {}
            for item in payload.custom_questions:
                q_id = item["id"]
                q_type = item["type"]
                instr = item["instructions"]
                crit = item.get("criteria")
                if q_type == "choice":
                    questions_dict[q_id] = Choice(instructions=instr, criteria=crit if isinstance(crit, dict) else {})
                elif q_type == "score":
                    questions_dict[q_id] = Score(instructions=instr, criteria=crit if isinstance(crit, list) else [])
                elif q_type == "noul":
                    if crit and isinstance(crit, dict):
                        questions_dict[q_id] = Noul(instructions=instr, criteria=NoulCriteria(true=crit.get("true", ""), false=crit.get("false", "")))
                    else:
                        questions_dict[q_id] = Noul(instructions=instr)
            state, _ = case_mod.build_questions(payload.input_data, lang=lang)
            questions = questions_dict
        else:
            state, questions = case_mod.build_questions(payload.input_data, lang=lang)

        jev_result = await execute_system_one(
            state=state,
            questions=questions,
            api_key=api_key,
            model=payload.model or DEFAULT_MODEL
        )
        
        try:
            workflow_res = case_mod.process_workflow(jev_result["answers"])
        except Exception as wf_err:
            logger.warning("Workflow processing fallback for custom questions: %s", wf_err)
            workflow_res = {
                "headline": "自定义结构评估完成",
                "status_tag": "success",
                "detail": f"已完成 {len(jev_result['answers'])} 个原语的 Jev 推理评估。",
                "actions": []
            }
        
        attribution_res = None
        if payload.explain:
            try:
                attribution_res = await compute_decision_attribution(
                    state_input=payload.input_data,
                    questions=questions,
                    base_answers=jev_result["answers"],
                    api_key=api_key,
                    model=payload.model or DEFAULT_MODEL,
                    case_mod=case_mod,
                    lang=lang
                )
            except Exception as attr_err:
                logger.warning("Attribution calculation failed for case %s: %s", case_id, attr_err)

        return {
            "success": True,
            "case_id": case_id,
            "lang": lang,
            "latency_ms": jev_result["latency_ms"],
            "model_used": jev_result["model_used"],
            "usage": jev_result["usage"],
            "answers": jev_result["answers"],
            "workflow": workflow_res,
            "raw_response": jev_result["raw_response"],
            "attribution": attribution_res
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("Error executing case %s", case_id)
        raise HTTPException(status_code=500, detail=f"执行失败: {str(e)}")

@app.post("/api/explain_case/{case_id}")
async def explain_official_case(
    case_id: str,
    payload: ExplainCaseRequest,
    x_typesafe_api_key: Optional[str] = Header(None)
):
    case_mod = get_case(case_id)
    if not case_mod:
        raise HTTPException(status_code=404, detail=f"未找到案例: {case_id}")
    
    api_key = (x_typesafe_api_key or "").strip() or DEFAULT_API_KEY
    if not api_key:
        raise HTTPException(status_code=400, detail="缺少 API Key。")

    lang = payload.lang or "zh"
    if payload.custom_questions:
        questions_dict = {}
        for item in payload.custom_questions:
            q_id = item["id"]
            q_type = item["type"]
            instr = item["instructions"]
            crit = item.get("criteria")
            if q_type == "choice":
                questions_dict[q_id] = Choice(instructions=instr, criteria=crit if isinstance(crit, dict) else {})
            elif q_type == "score":
                questions_dict[q_id] = Score(instructions=instr, criteria=crit if isinstance(crit, list) else [])
            elif q_type == "noul":
                if crit and isinstance(crit, dict):
                    questions_dict[q_id] = Noul(instructions=instr, criteria=NoulCriteria(true=crit.get("true", ""), false=crit.get("false", "")))
                else:
                    questions_dict[q_id] = Noul(instructions=instr)
        questions = questions_dict
    else:
        _, questions = case_mod.build_questions(payload.input_data, lang=lang)

    try:
        attribution_res = await compute_decision_attribution(
            state_input=payload.input_data,
            questions=questions,
            base_answers=payload.base_answers,
            api_key=api_key,
            model=payload.model or DEFAULT_MODEL,
            case_mod=case_mod,
            lang=lang
        )
        return {"success": True, "attribution": attribution_res}
    except Exception as e:
        logger.exception("Error explaining case %s", case_id)
        raise HTTPException(status_code=500, detail=f"归因分析失败: {str(e)}")

@app.post("/api/run_custom")
async def run_custom(
    payload: RunCustomRequest,
    x_typesafe_api_key: Optional[str] = Header(None)
):
    api_key = (x_typesafe_api_key or "").strip() or DEFAULT_API_KEY
    if not api_key:
        raise HTTPException(status_code=400, detail="缺少 API Key，请在页面配置。")

    if not payload.questions:
        raise HTTPException(status_code=400, detail="至少需要提供一个问题 (Question)。")

    questions_dict = {}
    for q in payload.questions:
        if q.type == "choice":
            if not isinstance(q.criteria, dict):
                raise HTTPException(status_code=400, detail=f"问题 [{q.id}] 类型为 Choice，criteria 必须是字典。")
            questions_dict[q.id] = Choice(instructions=q.instructions, criteria=q.criteria)
        elif q.type == "score":
            if not isinstance(q.criteria, list):
                raise HTTPException(status_code=400, detail=f"问题 [{q.id}] 类型为 Score，criteria 必须是档位列表。")
            questions_dict[q.id] = Score(instructions=q.instructions, criteria=q.criteria)
        elif q.type == "noul":
            if q.criteria and isinstance(q.criteria, dict):
                questions_dict[q.id] = Noul(instructions=q.instructions, criteria=NoulCriteria(true=q.criteria.get("true", ""), false=q.criteria.get("false", "")))
            else:
                questions_dict[q.id] = Noul(instructions=q.instructions)
        else:
            raise HTTPException(status_code=400, detail=f"未知的问题类型: {q.type}")

    try:
        jev_result = await execute_system_one(
            state=payload.state,
            questions=questions_dict,
            api_key=api_key,
            model=payload.model or DEFAULT_MODEL
        )
        
        attribution_res = None
        if payload.explain:
            try:
                attribution_res = await compute_decision_attribution(
                    state_input=payload.state,
                    questions=questions_dict,
                    base_answers=jev_result["answers"],
                    api_key=api_key,
                    model=payload.model or DEFAULT_MODEL
                )
            except Exception as attr_err:
                logger.warning("Attribution calculation failed for custom run: %s", attr_err)

        return {
            **jev_result,
            "attribution": attribution_res
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("Custom run error")
        raise HTTPException(status_code=500, detail=f"自定义执行失败: {str(e)}")

async def _forward_proxy_request(path: str, request: Request):
    """
    局域网透明 CORS 反向代理实现：
    将浏览器发往后端的请求转发到 https://api.typesafe.ai/...
    自动附加 CORS 标头，解决浏览器直接调用官方接口的跨域问题。
    """
    if request.method == "OPTIONS":
        return Response(status_code=204, headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Headers": "*"
        })

    clean_path = path.lstrip("/")
    target_url = f"https://api.typesafe.ai/{clean_path}"
    if request.url.query:
        target_url = f"{target_url}?{request.url.query}"

    req_headers = dict(request.headers)
    req_headers.pop("host", None)
    req_headers.pop("content-length", None)

    body = await request.body() if request.method not in ("GET", "HEAD") else None

    async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
        try:
            resp = await client.request(
                method=request.method,
                url=target_url,
                headers=req_headers,
                content=body
            )
            resp_headers = dict(resp.headers)
            resp_headers.pop("content-encoding", None)
            resp_headers.pop("transfer-encoding", None)
            resp_headers.pop("content-length", None)
            resp_headers["Access-Control-Allow-Origin"] = "*"
            resp_headers["Access-Control-Allow-Methods"] = "*"
            resp_headers["Access-Control-Allow-Headers"] = "*"

            return Response(
                content=resp.content,
                status_code=resp.status_code,
                headers=resp_headers
            )
        except Exception as e:
            logger.warning("Local proxy error to %s: %s", target_url, e)
            return Response(
                content=json.dumps({"detail": f"本地代理转发异常: {str(e)}"}),
                status_code=502,
                media_type="application/json",
                headers={"Access-Control-Allow-Origin": "*"}
            )

@app.api_route("/api/proxy/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])
async def proxy_typesafe_api(path: str, request: Request):
    return await _forward_proxy_request(path, request)

@app.api_route("/v1/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])
async def proxy_v1_typesafe_api(path: str, request: Request):
    return await _forward_proxy_request(f"v1/{path}", request)

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_DIR = os.path.join(ROOT_DIR, "static")

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/")
async def serve_index():
    return FileResponse(os.path.join(ROOT_DIR, "index.html"))

