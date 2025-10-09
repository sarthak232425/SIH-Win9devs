# hf_inference.py
import os
import time
import logging
from functools import wraps

from flask import Blueprint, request, jsonify, current_app
import requests
from cachetools import TTLCache, cached
from dotenv import load_dotenv

load_dotenv()

bp = Blueprint("hf_ai", __name__, url_prefix="/api/ai")

HF_API_TOKEN = os.getenv("HF_API_TOKEN")
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "SaranDharshan/Ayumaton")
HF_TIMEOUT = int(os.getenv("HF_TIMEOUT_SECONDS", "25"))
CACHE_TTL = int(os.getenv("CACHE_TTL_SECONDS", "300"))

# Simple in-memory cache for identical prompts (good for demos)
_cache = TTLCache(maxsize=1024, ttl=CACHE_TTL)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def require_json(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not request.is_json:
            return jsonify({"error": "Request must be application/json"}), 400
        return f(*args, **kwargs)
    return wrapper


def hf_call(model_id: str, prompt: str, max_tokens: int = 256, temperature: float = 0.2):
    """
    Make a single synchronous call to Hugging Face Inference API (text generation).
    Returns dict (parsed JSON) or raises requests.HTTPError on unrecoverable error.
    """
    url = f"https://api-inference.huggingface.co/models/{model_id}"
    headers = {"Authorization": f"Bearer {HF_API_TOKEN}"}
    payload = {
        "inputs": prompt,
        "parameters": {"max_new_tokens": max_tokens, "temperature": temperature},
    }
    resp = requests.post(url, headers=headers, json=payload, timeout=HF_TIMEOUT)
    # Raise on HTTP 4xx/5xx
    resp.raise_for_status()
    return resp.json()


@cached(_cache)
def cached_hf_call(model_id: str, prompt: str, max_tokens: int, temperature: float):
    # wrapper so identical queries get cached
    return hf_call(model_id, prompt, max_tokens, temperature)


@bp.route("/generate", methods=["POST"])
@require_json
def generate():
    """
    POST /api/ai/generate
    Body JSON: { "prompt": "...", "model_id": "...", "max_tokens": 200, "temperature": 0.2 }
    Response JSON: { "success": true, "model": "<id>", "output": "<generated text>", "meta": {...} }
    """
    body = request.get_json()
    prompt = body.get("prompt", "").strip()
    if not prompt:
        return jsonify({"error": "prompt is required"}), 400

    # Protect from extremely long prompts
    if len(prompt) > 2000:
        return jsonify({"error": "prompt length too long (max 2000 chars)"}), 400

    model_id = body.get("model_id", DEFAULT_MODEL)
    max_tokens = int(body.get("max_tokens", 256))
    temperature = float(body.get("temperature", 0.2))
    use_cache = bool(body.get("use_cache", True))

    # Minimal content safety: block obviously harmful keywords (not a full safety system)
    prohibited = ["suicide", "self-harm", "bomb", "poison"]  # example
    for p in prohibited:
        if p in prompt.lower():
            return jsonify({"error": "Prompt contains disallowed content"}), 400

    start = time.time()
    try:
        if use_cache:
            resp_json = cached_hf_call(model_id, prompt, max_tokens, temperature)
        else:
            resp_json = hf_call(model_id, prompt, max_tokens, temperature)
    except requests.HTTPError as e:
        # Log and return a clean error
        logger.exception("HF API error")
        code = getattr(e.response, "status_code", 502)
        return jsonify({"error": "upstream_model_error", "status_code": code, "detail": str(e)}), 502
    except requests.Timeout:
        logger.exception("HF API timed out")
        return jsonify({"error": "upstream_timeout"}), 504
    except Exception:
        logger.exception("Unexpected error contacting HF")
        return jsonify({"error": "upstream_unknown"}), 502

    elapsed = time.time() - start

    # Hugging Face returns different shapes depending on model; common structure for text-gen:
    # e.g. [{"generated_text": "..." }]  or {"error": "..."}  or other shapes
    output_text = None
    if isinstance(resp_json, dict) and resp_json.get("error"):
        # upstream model returned an error field
        return jsonify({"error": "upstream_model", "detail": resp_json.get("error")}), 502
    elif isinstance(resp_json, list) and len(resp_json) > 0 and "generated_text" in resp_json[0]:
        output_text = resp_json[0]["generated_text"]
    elif isinstance(resp_json, str):
        # Some endpoints return plain text (rare)
        output_text = resp_json
    else:
        # try to stringify whatever we got
        output_text = str(resp_json)

    # Add a short safety/confidence disclaimer for medical domain
    disclaimer = (
        "This response is for informational purposes only and is not medical advice. "
        "Consult a qualified Ayurvedic practitioner before acting on health recommendations."
    )

    return jsonify({
        "success": True,
        "model": model_id,
        "output": output_text,
        "disclaimer": disclaimer,
        "meta": {
            "upstream_elapsed_s": round(elapsed, 3),
            "cached": use_cache,
        }
    }), 200
