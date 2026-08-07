"""
Rule-based safety + intent router.

Classifies incoming user messages (greeting / emergency / symptom /
drug_info / unknown) and determines which follow-up questions are still
missing before a recommendation can be made safely.
"""

import re
from typing import List

from core.context import UserContext


class SafetyRouter:
    def __init__(self):
        self.greetings = {"hi", "hii", "hello", "hey", "good morning", "good evening", "good afternoon"}

        self.symptom_keywords = {
            "fever", "temperature", "cold", "cough", "sore throat", "throat",
            "headache", "body pain", "body ache", "pain", "stomach pain",
            "acidity", "gas", "heartburn", "vomit", "vomiting", "nausea",
            "diarrhea", "loose motion", "constipation", "allergy", "itching",
            "rash", "runny nose", "sneezing", "dizziness", "vertigo"
        }

        self.drug_info_triggers = {"what is", "about", "safe", "dose", "dosage", "side effect", "side effects", "overdose", "maximum"}
        self.drug_name_keywords = {
            "dolo", "crocin", "calpol", "brufen", "combiflam", "pantocid", "pan-d", "omez",
            "cetirizine", "allegra", "benadryl", "ascoril", "corex", "emeset",
            "ors", "electral", "imodium", "dulcoflex", "cremaffin", "stemetil",
            "paracetamol", "acetaminophen", "ibuprofen"
        }

        self.red_flags = {
            "chest pain", "difficulty breathing", "breathing difficulty", "shortness of breath",
            "fainting", "unconscious", "slurred speech", "one side weakness",
            "vomiting blood", "blood vomit", "black stool",
            "swelling of face", "swelling of lips", "swelling of tongue",
            "confusion", "seizure"
        }

    def _norm(self, s: str) -> str:
        return re.sub(r"\s+", " ", s.strip().lower())

    def _contains_any(self, text: str, phrases: set) -> bool:
        return any(p in text for p in phrases)

    def classify_intent(self, user_message: str) -> str:
        m = self._norm(user_message)
        if m in self.greetings:
            return "greeting"
        if self._contains_any(m, self.red_flags):
            return "emergency"
        if self._contains_any(m, self.drug_info_triggers) and self._contains_any(m, self.drug_name_keywords):
            return "drug_info"
        if self._contains_any(m, self.symptom_keywords):
            return "symptom"
        if self._contains_any(m, self.drug_name_keywords):
            return "drug_info"
        return "unknown"

    def missing_questions(self, user_message: str, intent: str, ctx: UserContext) -> List[str]:
        m = self._norm(user_message)
        qs = []

        if intent == "symptom" and ctx.age is None:
            qs.append("What is the patient age?")

        if intent == "symptom" and "fever" in m:
            if not re.search(r"\b(\d{1,2})\s*(day|days)\b", m):
                qs.append("How many days have you had fever?")
            if not re.search(r"\b(10[0-5]|9[5-9])\b", m) and "°c" not in m and "°f" not in m and "c" not in m and "f" not in m:
                qs.append("What is the highest temperature (°F or °C)?")

        if intent == "drug_info" and not self._contains_any(m, self.symptom_keywords):
            qs.append("Are you asking about it for fever, pain, cold, or something else?")

        return qs[:2]
