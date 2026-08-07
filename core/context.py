"""
Session/user context model.

Holds the lightweight patient context (age, gender, allergies, meds,
conditions) that is collected across a chat session and fed into both
the recommender and chat models as grounding context.
"""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class UserContext:
    age: Optional[int] = None
    gender: Optional[str] = None
    allergies: List[str] = field(default_factory=list)
    current_meds: List[str] = field(default_factory=list)
    conditions: List[str] = field(default_factory=list)

    def to_compact_text(self) -> str:
        parts = []
        if self.age is not None:
            parts.append(f"Age: {self.age}")
        if self.gender:
            parts.append(f"Gender: {self.gender}")
        if self.conditions:
            parts.append("Known conditions: " + ", ".join(self.conditions))
        if self.current_meds:
            parts.append("Current meds: " + ", ".join(self.current_meds))
        if self.allergies:
            parts.append("Allergies: " + ", ".join(self.allergies))
        return " | ".join(parts) if parts else "No extra user context available."
