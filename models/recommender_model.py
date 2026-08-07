"""
RecommenderModel: gemma-2-2b + LoRA adapter -> strict JSON triage output.
"""

import gc
from typing import Any, Dict

import streamlit as st

from core.context import UserContext
from utils.helpers import extract_json
from utils.prompts import build_recommender_prompt

ML_OK = True
ML_IMPORT_ERROR = None
try:
    import torch
    from transformers import AutoTokenizer, AutoModelForCausalLM
    from peft import PeftModel
except Exception as e:
    # Don't call st.error() here: this module can be imported before
    # st.set_page_config() runs in app.py, and Streamlit requires
    # set_page_config to be the first Streamlit command executed.
    # The failure is surfaced later via ML_OK / ML_IMPORT_ERROR instead.
    ML_OK = False
    ML_IMPORT_ERROR = str(e)


class RecommenderModel:
    def __init__(self, base_model: str, adapter: str):
        self.base_model = base_model
        self.adapter = adapter
        self.model = None
        self.tokenizer = None
        self.loaded = False

    def load(self) -> bool:
        if not ML_OK:
            return False
        try:
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

            self.tokenizer = AutoTokenizer.from_pretrained(self.base_model, trust_remote_code=True)
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token

            dtype = torch.float16 if torch.cuda.is_available() else torch.float32

            model = AutoModelForCausalLM.from_pretrained(
                self.base_model,
                torch_dtype=dtype,
                device_map="auto" if torch.cuda.is_available() else None,
                low_cpu_mem_usage=True,
                trust_remote_code=True,
            )
            model.eval()

            try:
                model = PeftModel.from_pretrained(model, self.adapter)
                model.eval()
            except Exception as e:
                # still usable as base, but recommender quality may drop
                st.warning(f"Recommender adapter load failed, using base model: {e}")

            self.model = model
            self.loaded = True
            return True

        except Exception as e:
            st.error(f"Recommender load failed: {e}")
            self.loaded = False
            return False

    def recommend_json(self, user_message: str, ctx: UserContext, intent: str) -> Dict[str, Any]:
        safe_fallback = {
            "intent": intent,
            "summary": "Unable to generate structured recommendation safely.",
            "likely_condition": None,
            "suggested_medicines": [],
            "home_care": [],
            "avoid": [],
            "red_flags": [],
            "followup_questions": [],
            "confidence": 0.0
        }

        if not self.loaded or self.model is None or self.tokenizer is None:
            return safe_fallback

        prompt = build_recommender_prompt(user_message, ctx)

        inputs = self.tokenizer(prompt, return_tensors="pt", truncation=True, max_length=900)
        device = next(self.model.parameters()).device
        inputs = {k: v.to(device) for k, v in inputs.items()}

        with torch.no_grad():
            out = self.model.generate(
                **inputs,
                max_new_tokens=260,
                do_sample=False,
                repetition_penalty=1.10,
                no_repeat_ngram_size=3,
                pad_token_id=self.tokenizer.eos_token_id,
                use_cache=True,
            )

        gen = out[0][inputs["input_ids"].shape[-1]:]
        text = self.tokenizer.decode(gen, skip_special_tokens=True).strip()
        parsed = extract_json(text)

        if isinstance(parsed, dict):
            for k in safe_fallback.keys():
                parsed.setdefault(k, safe_fallback[k])

            meds = parsed.get("suggested_medicines", [])
            if isinstance(meds, list):
                parsed["suggested_medicines"] = meds[:2]

            fqs = parsed.get("followup_questions", [])
            if isinstance(fqs, list):
                parsed["followup_questions"] = fqs[:2]

            try:
                c = float(parsed.get("confidence", 0.0))
                parsed["confidence"] = max(0.0, min(1.0, c))
            except Exception:
                parsed["confidence"] = 0.0

            return parsed

        return safe_fallback
