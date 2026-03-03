import json
import os
from typing import Any, Dict, Optional

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

ALLOWED_CATEGORIES = {"mobile", "laptop", "tv", "tablet"}
ALLOWED_BRANDS = {"Samsung", "Apple", "Lenovo", "Sony"}


def _get_api_key() -> Optional[str]:
    return os.getenv("OPENAI_API_KEY") or os.getenv("OPEN_AI_API")


def _safe_get_str(d: Dict[str, Any], key: str) -> Optional[str]:
    v = d.get(key)
    if isinstance(v, str) and v.strip():
        return v.strip()
    return None


def _normalize(s: str) -> str:
    return "".join(ch.lower() if ch.isalnum() or ch.isspace() else " " for ch in s).strip()


def _basic_normalized_text(product: str) -> str:
    t = _normalize(product)
    t = t.replace("samsng", "samsung")
    t = t.replace("samnsung", "samsung")
    t = t.replace("aplle", "apple")
    t = t.replace("aple", "apple")
    t = " ".join(t.split())
    return t


def _infer_from_text(product: str) -> Dict[str, Any]:
    t = _basic_normalized_text(product)

    brand: Optional[str] = None
    if "samsung" in t:
        brand = "Samsung"
    elif any(k in t for k in ["apple", "iphone", "ipad", "macbook"]):
        brand = "Apple"
    elif any(k in t for k in ["lenovo", "thinkpad"]):
        brand = "Lenovo"
    elif any(k in t for k in ["sony", "bravia"]):
        brand = "Sony"

    category: Optional[str] = None
    if any(k in t for k in ["phone", "mobile", "cell", "smartphone", "iphone", "galaxy"]):
        category = "mobile"
    elif any(k in t for k in ["laptop", "notebook", "pc", "macbook", "thinkpad"]):
        category = "laptop"
    elif any(k in t for k in ["tv", "television", "bravia"]):
        category = "tv"
    elif any(k in t for k in ["tablet", "ipad", "tab"]):
        category = "tablet"

    if brand and not category:
        category = "mobile"

    subcategory: Optional[str] = None
    if "iphone" in t:
        subcategory = "iphone"
    elif "galaxy" in t:
        subcategory = "galaxy"
    elif "thinkpad" in t:
        subcategory = "thinkpad"
    elif "bravia" in t:
        subcategory = "bravia"
    elif "ipad" in t:
        subcategory = "ipad"
    elif "macbook" in t:
        subcategory = "macbook"

    confidence = 0.3
    if category and brand:
        confidence = 0.85
    elif category or brand:
        confidence = 0.6

    return {
        "normalized_text": t,
        "taxonomy": {"category": category, "subcategory": subcategory, "brand": brand},
        "attributes": {},
        "confidence": confidence,
    }


def _get_client() -> OpenAI:
    api_key = _get_api_key()
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY (or OPEN_AI_API) is not set")
    return OpenAI(api_key=api_key)


def tag_product(product: str) -> Dict[str, Any]:
    client = _get_client()

    system_prompt = (
        "You are a product tagging AI.\n\n"
        "Return output as JSON only in this exact shape:\n"
        "{\n"
        '  "normalized_text": "",\n'
        '  "taxonomy": {\n'
        '    "category": "",\n'
        '    "subcategory": "",\n'
        '    "brand": ""\n'
        "  },\n"
        '  "attributes": {},\n'
        '  "confidence": 0.0\n'
        "}\n\n"
        "Rules:\n"
        '- taxonomy.category must be one of: mobile, laptop, tv, tablet\n'
        '- taxonomy.brand must be one of: Samsung, Apple, Lenovo, Sony, or null\n'
        "- taxonomy.subcategory is a short string or null\n"
        "- normalized_text is corrected/normalized input\n"
        "- attributes is an object\n"
        "- confidence is a number from 0.0 to 1.0\n"
        'If a brand is identified but category is ambiguous, default "category" to "mobile".\n'
        "Map synonyms as: phone/mobile/cell/smartphone -> mobile; notebook/pc/macbook -> laptop; television/bravia -> tv; ipad/tab -> tablet.\n"
    )

    create_kwargs: Dict[str, Any] = {
        "model": "gpt-4.1-mini",
        "temperature": 0,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": product},
        ],
        "tools": [
            {
                "type": "function",
                "function": {
                    "name": "set_tagging_result",
                    "parameters": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                            "normalized_text": {"type": "string"},
                            "taxonomy": {
                                "type": "object",
                                "additionalProperties": False,
                                "properties": {
                                    "category": {
                                        "type": "string",
                                        "enum": ["mobile", "laptop", "tv", "tablet"],
                                    },
                                    "subcategory": {
                                        "anyOf": [{"type": "string"}, {"type": "null"}]
                                    },
                                    "brand": {
                                        "anyOf": [
                                            {
                                                "type": "string",
                                                "enum": ["Samsung", "Apple", "Lenovo", "Sony"],
                                            },
                                            {"type": "null"},
                                        ]
                                    },
                                },
                                "required": ["category", "subcategory", "brand"],
                            },
                            "attributes": {"type": "object"},
                            "confidence": {
                                "type": "number",
                                "minimum": 0.0,
                                "maximum": 1.0,
                            },
                        },
                        "required": ["normalized_text", "taxonomy", "attributes", "confidence"],
                    },
                },
            }
        ],
        "tool_choice": {
            "type": "function",
            "function": {"name": "set_tagging_result"},
        },
    }

    response = client.chat.completions.create(**create_kwargs)

    data: Dict[str, Any] = {}
    try:
        msg = response.choices[0].message
        tool_calls = getattr(msg, "tool_calls", None) or []
        if tool_calls:
            args = tool_calls[0].function.arguments
            data = json.loads(args) if isinstance(args, str) else dict(args)
        else:
            raw = (msg.content or "").strip()
            data = json.loads(raw) if raw else {}
    except Exception:
        raise RuntimeError("OpenAI returned an invalid JSON response")

    if not isinstance(data, dict):
        raise RuntimeError("OpenAI returned a non-object JSON response")

    normalized_text = _safe_get_str(data, "normalized_text") or _basic_normalized_text(product)

    taxonomy = data.get("taxonomy") if isinstance(data.get("taxonomy"), dict) else {}
    category = _safe_get_str(taxonomy, "category")
    brand = _safe_get_str(taxonomy, "brand")
    subcategory = _safe_get_str(taxonomy, "subcategory")

    if category not in ALLOWED_CATEGORIES:
        raise RuntimeError("OpenAI returned an invalid category")
    if brand is not None and brand not in ALLOWED_BRANDS:
        raise RuntimeError("OpenAI returned an invalid brand")

    attributes = data.get("attributes") if isinstance(data.get("attributes"), dict) else {}

    confidence_val = data.get("confidence")
    confidence = float(confidence_val) if isinstance(confidence_val, (int, float)) else 0.5
    confidence = max(0.0, min(1.0, confidence))

    return {
        "normalized_text": normalized_text,
        "taxonomy": {"category": category, "subcategory": subcategory, "brand": brand},
        "attributes": attributes,
        "confidence": confidence,
    }

