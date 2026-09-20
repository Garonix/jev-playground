import time
import logging
from typing import Any, Dict, Optional
from typesafe_sdk import (
    AsyncTypeSafeClient,
    TypeSafeAuthenticationError,
    TypeSafeRateLimitError,
    TypeSafeBadRequestError,
    TypeSafeAPIError,
    TypeSafeAPIConnectionError,
)
from app.config import DEFAULT_MODEL, DEFAULT_API_KEY, API_ENDPOINT

logger = logging.getLogger("jev_client")

async def test_api_key(api_key: Optional[str] = None) -> Dict[str, Any]:
    """Test whether the provided API Key is valid by calling the models API."""
    key = (api_key or "").strip() or DEFAULT_API_KEY
    if not key:
        return {
            "valid": False,
            "error": "未提供 API Key。请在页面右上角输入您的 TypeSafe API Key 或设置 TYPESAFE_API_KEY 环境变量。"
        }
    
    start_time = time.perf_counter()
    try:
        async with AsyncTypeSafeClient(api_key=key, base_url=API_ENDPOINT, timeout=15.0) as client:
            models_resp = await client.models.list()
            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 1)
            model_names = [m.name for m in models_resp.models] if hasattr(models_resp, "models") else []
            return {
                "valid": True,
                "latency_ms": elapsed_ms,
                "models": model_names,
                "message": f"连接成功！可用模型: {', '.join(model_names) or 'jev-latest'}"
            }
    except TypeSafeAuthenticationError:
        return {
            "valid": False,
            "error": "API Key 无效或未授权，请检查输入的 Key 是否正确 (Authentication Error)。"
        }
    except TypeSafeRateLimitError:
        return {
            "valid": False,
            "error": "请求过于频繁，触发了速率限制 (Rate Limit Exceeded)。"
        }
    except TypeSafeAPIConnectionError as e:
        return {
            "valid": False,
            "error": f"无法连接到 TypeSafe 服务器: {str(e)}"
        }
    except Exception as e:
        return {
            "valid": False,
            "error": f"测试失败: {str(e)}"
        }

async def execute_system_one(
    state: Any,
    questions: Dict[str, Any],
    api_key: Optional[str] = None,
    model: Optional[str] = None,
) -> Dict[str, Any]:
    """Execute a real system_one request to the Jev model and return detailed results."""
    key = (api_key or "").strip() or DEFAULT_API_KEY
    if not key:
        raise ValueError("请先在页面顶部配置 TypeSafe API Key 才能进行真实测试。")

    target_model = model or DEFAULT_MODEL
    start_time = time.perf_counter()

    try:
        async with AsyncTypeSafeClient(api_key=key, base_url=API_ENDPOINT, timeout=30.0) as client:
            response = await client.system_one(
                state=state,
                questions=questions,
                model=target_model,
            )
            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 1)

            # Format answers into friendly dictionary
            formatted_answers = {}
            for q_id, ans in response.answers.items():
                ans_dict = ans.model_dump()
                formatted_answers[q_id] = ans_dict

            usage_info = {
                "input_tokens": response.usage.input_tokens if response.usage else 0,
                "output_tokens": response.usage.output_tokens if response.usage else 0,
            }

            return {
                "success": True,
                "latency_ms": elapsed_ms,
                "model_used": response.model,
                "usage": usage_info,
                "answers": formatted_answers,
                "raw_response": response.model_dump(),
            }
    except TypeSafeAuthenticationError as e:
        logger.error("Auth error: %s", e)
        raise ValueError("API Key 认证失败：请核对您的 TypeSafe API Key 是否有效。") from e
    except TypeSafeRateLimitError as e:
        logger.error("Rate limit: %s", e)
        raise ValueError("达到 API 速率限制 (Rate Limit)，请稍后再试。") from e
    except TypeSafeBadRequestError as e:
        logger.error("Bad request: %s", e)
        raise ValueError(f"请求参数错误 (Bad Request): {str(e)}") from e
    except TypeSafeAPIConnectionError as e:
        logger.error("Connection error: %s", e)
        raise ValueError(f"连接 TypeSafe API 失败，请检查网络连接: {str(e)}") from e
    except Exception as e:
        logger.error("Unexpected error: %s", e)
        raise ValueError(f"Jev API 调用异常: {str(e)}") from e
