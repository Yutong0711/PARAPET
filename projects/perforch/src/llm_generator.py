import threading
import time
from typing import Any, Dict, Optional

from openai import APITimeoutError, OpenAI

from config.api_config import API_CONFIG

import logging

# The OpenAI python SDK uses httpx/httpcore; these can log request lines.
for _name in ("httpx", "httpcore", "openai"):
    logging.getLogger(_name).disabled = True

_client_cache: dict[str, OpenAI] = {}
_client_lock = threading.Lock()
_rpm_last_call: dict[str, float] = {}
_rpm_lock = threading.Lock()


def _get_client(product_name: str, timeout: Optional[float] = None) -> OpenAI:
    """Return a cached OpenAI client for the given product."""
    cache_key = f"{product_name}:{timeout}"
    cached = _client_cache.get(cache_key)
    if cached is not None:
        return cached
    with _client_lock:
        cached = _client_cache.get(cache_key)
        if cached is not None:
            return cached
        model_data = API_CONFIG[product_name]
        client = OpenAI(
            api_key=model_data["api_key"],
            base_url=model_data["base_url"],
            timeout=timeout,
        )
        _client_cache[cache_key] = client
        return client


def _generate_with_openai_sdk(input_string: str, product_name: str, timeout: Optional[float] = None, temperature: Optional[float] = None, top_p: Optional[float] = None) -> str:
    """Call an OpenAI-compatible Chat Completions endpoint and return plain text."""
    model_data = API_CONFIG[product_name]
    client = _get_client(product_name, timeout)

    kwargs: Dict[str, Any] = {
        "model": model_data["model"],
        "messages": [{"role": "user", "content": input_string}],
    }
    if temperature is not None:
        kwargs["temperature"] = temperature
    if top_p is not None:
        kwargs["top_p"] = top_p

    completion = client.chat.completions.create(**kwargs)
    return completion.choices[0].message.content or ""

def generate_text(input_string: str, product_name: str, timeout: int = 600, max_retries: int = 3, temperature: Optional[float] = None, top_p: Optional[float] = None) -> Dict[str, Any]:
    """Generate text with a configured model, retrying only on request timeout.

    Returns a dict with keys: status ("success"|"error"), text, error.
    """
    config = API_CONFIG.get(product_name)
    if not config:
        return {"status": "error", "text": None, "error": f"Unknown model: {product_name}"}
    if config.get("type") != "openai-sdk":
        return {"status": "error", "text": None, "error": f"Unsupported model type: {config.get('type')}"}

    rpm = config.get("RPM")
    for attempt in range(max_retries):
        try:
            if rpm:
                min_interval = 60.0 / rpm
                with _rpm_lock:
                    now = time.monotonic()
                    last = _rpm_last_call.get(product_name, 0.0)
                    wait = min_interval - (now - last)
                    if wait > 0:
                        time.sleep(wait)
                    _rpm_last_call[product_name] = time.monotonic()
            text = _generate_with_openai_sdk(input_string, product_name, timeout=timeout, temperature=temperature, top_p=top_p)
            if text:
                return {"status": "success", "text": text, "error": None}
            return {"status": "error", "text": None, "error": f"Model {product_name} returned empty response"}
        except APITimeoutError:
            if attempt >= max_retries - 1:
                return {"status": "error", "text": None, "error": f"Request timed out after {timeout} seconds"}
        except Exception as e:
            # Fail fast on non-timeout errors to avoid hiding config/auth problems.
            return {
                "status": "error",
                "text": None,
                "error": f"API Error: {e.__class__.__name__}: {str(e)}",
            }

        # Timeout retry only.
        print(f"Attempt {attempt + 1} timed out. Retrying...")
        time.sleep(1)
    
    return {"status": "error", "text": None, "error": "Unknown error occurred"}

def test_llms(models: Optional[list] = None, timeout: int = 60, prompt: str = "") -> Dict[str, Any]:
    """Lightweight smoke test for one or more configured models."""
    test_prompt = prompt or "Write a simple Python function that adds two numbers."
    model_list = models or list(API_CONFIG.keys())

    results: Dict[str, Any] = {
        "total_tested": 0,
        "successful": 0,
        "failed": 0,
        "details": {},
    }

    for product_name in model_list:
        results["total_tested"] += 1

        try:
            res = generate_text(test_prompt, product_name, timeout=timeout, max_retries=1)
        except Exception as e:
            res = {"status": "error", "text": None, "error": f"Exception: {e.__class__.__name__}: {str(e)}"}

        if res.get("status") == "success":
            results["successful"] += 1
            text = res.get("text") or ""
            results["details"][product_name] = {
                "status": "success",
                "response_length": len(text),
            }
        else:
            results["failed"] += 1
            results["details"][product_name] = {
                "status": "failed",
                "error": res.get("error"),
            }

    return results

if __name__ == "__main__":
    test_llms()
