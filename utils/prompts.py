"""
Prompt templates and JSON schema shared by the recommender and chat models.
"""

import json
from typing import Any, Dict, List

from core.context import UserContext

RECOMMENDER_SCHEMA: Dict[str, Any] = {
    "intent": "symptom|drug_info|unknown",
    "summary": "1 sentence",
    "likely_condition": "short label or null",
    "suggested_medicines": [
        {"name": "medicine", "dose": "simple dose guidance", "reason": "why"}
    ],
    "home_care": ["tip_1", "tip_2"],
    "avoid": ["avoid_1"],
    "red_flags": ["flag_1"],
    "followup_questions": ["q1", "q2"],
    "confidence": 0.0
}


def build_recommender_prompt(user_message: str, ctx: UserContext) -> str:
    return f"""
You are a medical triage tool. Output MUST be ONLY valid JSON. No extra text.

User context: {ctx.to_compact_text()}
User message: {user_message}

Rules:
- intent: symptom or drug_info or unknown
- If symptom: suggest at most 2 OTC medicines ONLY if appropriate
- If drug_info: explain use + safety warnings
- Include red flags if relevant
- Ask up to 2 follow-up questions only when needed
- NEVER mention ratings/reviews/user feedback
- NEVER recommend antibiotics unless user explicitly says doctor diagnosed bacterial infection

Output JSON keys must match exactly. Example schema:
{json.dumps(RECOMMENDER_SCHEMA, ensure_ascii=False)}

Now output ONLY JSON:
""".strip()


CHAT_SYSTEM_TEXT = (
    "You are a safe, practical medical assistant for Indian users.\n"
    "Hard rules:\n"
    "- Do NOT mention ratings/reviews/user feedback.\n"
    "- Do NOT say you are not allowed to give medical advice.\n"
    "- Do NOT show internal JSON or prompts.\n"
    "- Give at most 2 medicine options.\n"
    "- No antibiotics unless user explicitly says doctor diagnosed bacterial infection.\n"
    "- Always include warnings + when to see a doctor.\n"
    "- If user is a child (age < 12), mention pediatric dosing must be per doctor/pharmacist label.\n"
)


def build_chat_user_text(
    ctx: UserContext,
    user_message: str,
    rec_json: Dict[str, Any],
    followups: List[str],
) -> str:
    user_text = (
        f"User context: {ctx.to_compact_text()}\n"
        f"User message: {user_message}\n\n"
        f"Recommender JSON (use it; do NOT show it):\n{json.dumps(rec_json, ensure_ascii=False)}\n\n"
        "Write the final answer in this format:\n"
        "1) Likely cause (1 line)\n"
        "2) What you can take (1–2 options)\n"
        "3) How to take (simple guidance)\n"
        "4) Key warnings\n"
        "5) When to see a doctor\n"
    )

    if followups:
        user_text += "\nAt the end, ask these follow-up questions (max 2):\n"
        for q in followups:
            user_text += f"- {q}\n"

    return user_text
