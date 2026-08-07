"""
HybridMedicalAssistant: orchestrates the router, recommender and chat
models into a single turn-taking `answer()` call, plus light-weight
context extraction from free text.
"""

import re
from typing import Any, Dict, List, Tuple

from core.context import UserContext
from core.router import SafetyRouter
from models.chat_model import ChatModel
from models.recommender_model import RecommenderModel
from utils.helpers import clean_model_output
from utils.prompts import CHAT_SYSTEM_TEXT, build_chat_user_text


class HybridMedicalAssistant:
    def __init__(self, ctx: UserContext, router: SafetyRouter, recommender: RecommenderModel, chat: ChatModel):
        self.ctx = ctx
        self.router = router
        self.recommender = recommender
        self.chat = chat

    def update_context_from_text(self, user_message: str):
        m = user_message.lower()

        # age: "age 6" OR "6 years"
        m_age = re.search(r"\bage\s*[:=]?\s*(\d{1,3})\b", m)
        if m_age:
            self.ctx.age = int(m_age.group(1))
        else:
            m_age2 = re.search(r"\b(\d{1,2})\s*(year|years|yrs)\b", m)
            if m_age2:
                self.ctx.age = int(m_age2.group(1))

        if "male" in m:
            self.ctx.gender = "male"
        elif "female" in m:
            self.ctx.gender = "female"

        ma = re.search(r"allergy to ([a-z0-9_\-\s]+)", m)
        if ma:
            item = re.sub(r"[^a-z0-9\s\-]", "", ma.group(1).strip())
            if item and item not in self.ctx.allergies:
                self.ctx.allergies.append(item)

        mm = re.search(r"current meds[:=]?\s*([a-z0-9,\-\s]+)", m)
        if mm:
            meds = [x.strip() for x in mm.group(1).split(",") if x.strip()]
            for med in meds:
                if med not in self.ctx.current_meds:
                    self.ctx.current_meds.append(med)

    def check_followup_answered(self, user_message: str, previous_followups: List[str]) -> List[str]:
        """Check if user message answers any of the previous follow-up questions"""
        if not previous_followups:
            return []

        answered = []
        message_lower = user_message.lower()

        for followup in previous_followups:
            followup_lower = followup.lower()
            # Check for age-related answers
            if "age" in followup_lower and (re.search(r"\b\d{1,3}\b", message_lower) or re.search(r"\b\d{1,2}\s+(year|years|yrs)", message_lower)):
                answered.append(followup)
            # Check for duration-related answers
            elif ("days" in followup_lower or "long" in followup_lower) and re.search(r"\b\d+\s*(day|days|week|weeks|month|months)", message_lower):
                answered.append(followup)
            # Check for temperature-related answers
            elif ("temperature" in followup_lower or "fever" in followup_lower) and ("°c" in message_lower or "°f" in message_lower or re.search(r"\b(10[0-5]|9[5-9])\b", message_lower)):
                answered.append(followup)

        return answered

    def answer(self, user_message: str) -> Tuple[str, Dict[str, Any], List[str]]:
        self.update_context_from_text(user_message)

        intent = self.router.classify_intent(user_message)
        if intent == "emergency":
            return (
                "⚠️ This may be serious.\n\n"
                "Please seek urgent medical care now (ER / 108 in India).\n"
                "If possible, share age and what started it after getting help.",
                {"intent": "emergency"},
                []
            )

        if intent == "greeting":
            return ("Hi! Tell me your symptom (fever, cough, headache, stomach pain, acidity).", {"intent": "greeting"}, [])

        followups = self.router.missing_questions(user_message, intent, self.ctx)

        rec_json = self.recommender.recommend_json(user_message, self.ctx, intent)

        # If recommender asked followups, merge (but keep max 2)
        rec_fq = rec_json.get("followup_questions", [])
        if isinstance(rec_fq, list):
            for q in rec_fq:
                if q and q not in followups:
                    followups.append(q)
        followups = followups[:2]

        user_text = build_chat_user_text(self.ctx, user_message, rec_json, followups)

        out = self.chat.generate(CHAT_SYSTEM_TEXT, user_text, max_new_tokens=260)
        out = clean_model_output(out)

        return out, rec_json, followups
