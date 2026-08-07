"""
ChatModel: gemma-2-2b-it -> final, user-facing natural language response.
"""

import gc

import streamlit as st

ML_OK = True
ML_IMPORT_ERROR = None
try:
    import torch
    from transformers import AutoTokenizer, AutoModelForCausalLM
except Exception as e:
    # Don't call st.error() here: this module can be imported before
    # st.set_page_config() runs in app.py, and Streamlit requires
    # set_page_config to be the first Streamlit command executed.
    # The failure is surfaced later via ML_OK / ML_IMPORT_ERROR instead.
    ML_OK = False
    ML_IMPORT_ERROR = str(e)


class ChatModel:
    def __init__(self, model_name: str):
        self.model_name = model_name
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

            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            dtype = torch.float16 if torch.cuda.is_available() else torch.float32

            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                torch_dtype=dtype,
                device_map="auto" if torch.cuda.is_available() else None,
                low_cpu_mem_usage=True,
            )
            self.model.eval()
            self.loaded = True
            return True
        except Exception as e:
            st.error(f"ChatModel load failed: {e}")
            self.loaded = False
            return False

    def generate(self, system_text: str, user_text: str, max_new_tokens: int = 260) -> str:
        if not self.loaded or self.model is None or self.tokenizer is None:
            return "Model not loaded."

        # Gemma-IT works best with everything in the user message
        full_user_prompt = system_text + "\n\n" + user_text
        messages = [{"role": "user", "content": full_user_prompt}]

        prompt = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )

        inputs = self.tokenizer(prompt, return_tensors="pt", truncation=True, max_length=1600)
        device = next(self.model.parameters()).device
        inputs = {k: v.to(device) for k, v in inputs.items()}

        with torch.no_grad():
            out = self.model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                do_sample=False,
                repetition_penalty=1.12,
                no_repeat_ngram_size=3,
                pad_token_id=self.tokenizer.eos_token_id,
                use_cache=True,
            )

        gen = out[0][inputs["input_ids"].shape[-1]:]
        text = self.tokenizer.decode(gen, skip_special_tokens=True).strip()
        return text
