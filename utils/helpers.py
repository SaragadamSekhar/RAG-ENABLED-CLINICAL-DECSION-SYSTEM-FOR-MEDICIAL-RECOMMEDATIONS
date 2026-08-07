"""
Generic, model-agnostic helper functions.
"""

import json
import re
from typing import Any, Dict, Optional


def extract_json(text: str) -> Optional[Dict[str, Any]]:
    """Pull the first well-formed top-level JSON object out of raw model text.

    Tolerates trailing commas and surrounding chatter from the model.
    """
    text = text.strip()
    m = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not m:
        return None
    blob = m.group(0)

    brace_count = 0
    in_string = False
    start = -1
    end = -1

    for i, ch in enumerate(blob):
        if ch == '"' and (i == 0 or blob[i - 1] != "\\"):
            in_string = not in_string
        if in_string:
            continue
        if ch == "{":
            if brace_count == 0:
                start = i
            brace_count += 1
        elif ch == "}":
            brace_count -= 1
            if brace_count == 0 and start != -1:
                end = i + 1
                break

    if start != -1 and end != -1:
        clean = blob[start:end]
        try:
            return json.loads(clean)
        except json.JSONDecodeError:
            try:
                clean = re.sub(r",\s*}", "}", clean)
                clean = re.sub(r",\s*]", "]", clean)
                return json.loads(clean)
            except json.JSONDecodeError:
                return None
    return None


def clean_model_output(out: str) -> str:
    """Strip accidental chat-template / role-marker leakage from generations."""
    out = out.strip()
    out = re.sub(r"<\|system\|>.*", "", out, flags=re.DOTALL | re.IGNORECASE).strip()
    out = re.sub(r"<\|user\|>.*", "", out, flags=re.DOTALL | re.IGNORECASE).strip()
    out = re.sub(r"<\|assistant\|>.*", "", out, flags=re.DOTALL | re.IGNORECASE).strip()
    out = re.sub(r"\n{3,}", "\n\n", out).strip()
    return out
