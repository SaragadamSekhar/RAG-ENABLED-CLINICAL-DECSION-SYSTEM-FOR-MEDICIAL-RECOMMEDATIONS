#!/usr/bin/env python3
"""
STREAMLIT HYBRID MEDICAL ASSISTANT (2-MODEL PIPELINE)
----------------------------------------------------
RecommenderModel (gemma-2-2b + LoRA) -> STRICT JSON
ChatModel (gemma-2-2b-it)            -> final user response

Features:
- Streamlit UI with chat
- Strong session memory (chat + extracted context)
- Follow-up questions only when needed
- Emergency bypass
- Debug mode to view recommender JSON (optional)

This file is the thin entrypoint: it wires together core/, models/,
ui/ and utils/ and owns only Streamlit page setup + the chat loop.
"""

import json
import os
import warnings
from datetime import datetime
from typing import Tuple

import streamlit as st
from huggingface_hub import login

from core.assistant import HybridMedicalAssistant
from models.chat_model import ML_IMPORT_ERROR, ChatModel
from models.recommender_model import ML_OK, RecommenderModel
from ui.chat import init_session, render_chat
from ui.sidebar import sidebar_context_editor
from ui.styles import CUSTOM_CSS, FOLLOWUP_BANNER_HTML

warnings.filterwarnings("ignore")


def _hf_login():
    """Log in to Hugging Face Hub if a token is configured.

    Gemma is a gated model, so a token IS required to download it — but
    the app should show a clear error instead of crashing at import time
    when the env var is missing or invalid.
    """
    token = os.getenv("HF_TOKEN")
    if not token:
        st.error(
            "HF_TOKEN environment variable is not set. Gemma is a gated "
            "model on Hugging Face — set HF_TOKEN to a token for an "
            "account that has accepted the Gemma license before the "
            "models can be downloaded."
        )
        st.stop()
    try:
        login(token)
    except Exception as e:
        st.error(f"Hugging Face login failed: {e}")
        st.stop()


# ==============================
# Streamlit Cached Loaders
# ==============================
@st.cache_resource(show_spinner=True)
def load_models() -> Tuple[ChatModel, RecommenderModel]:
    if not ML_OK:
        raise RuntimeError(f"ML libraries are not available: {ML_IMPORT_ERROR}")

    chat = ChatModel("google/gemma-2-2b-it")
    rec = RecommenderModel(
        base_model="google/gemma-2-2b",
        adapter="coderop12/gemma-2b-medical-qlora"
    )

    with st.spinner("Loading ChatModel (gemma-2-2b-it)..."):
        ok_chat = chat.load()
    if not ok_chat:
        raise RuntimeError("Chat model failed to load.")

    with st.spinner("Loading Recommender (gemma-2-2b + LoRA)..."):
        rec.load()  # if adapter fails, it falls back to base recommender

    return chat, rec


def main():
    st.set_page_config(page_title="RAG ENABLED CLINICAL DECISION SYSTEM FOR MEDICAL RECOMMENDATIONS", page_icon="🩺", layout="wide")

    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

    _hf_login()

    init_session()
    sidebar_context_editor()

    st.title("🩺 RAG ENABLED CLINICAL DECISION SYSTEM FOR MEDICAL RECOMMENDATIONS")
    st.caption("An intelligent assistant for medical information. Not a substitute for professional medical advice.")

    # Load models (cached)
    try:
        chat_model, rec_model = load_models()
    except Exception as e:
        st.error(str(e))
        st.stop()

    assistant = HybridMedicalAssistant(
        ctx=st.session_state.ctx,
        router=st.session_state.router,
        recommender=rec_model,
        chat=chat_model
    )

    # First assistant greeting if chat is empty
    if not st.session_state.messages:
        st.session_state.messages.append({
            "role": "assistant",
            "content": "Hello! I am an AI medical assistant. How can I help you today?\n\nPlease describe your symptoms or ask about a medication. For example: *'I have a fever and a headache'* or *'What is paracetamol used for?'*",
            "followups": []
        })

    render_chat()

    # Enhanced chat input with context-aware placeholder
    placeholder_text = "Type your symptom or medicine question…"
    if st.session_state.last_followups:
        # If there are pending follow-ups, suggest answering them
        placeholder_text = f"Answer: {st.session_state.last_followups[0]}"

    user_text = st.chat_input(placeholder_text)
    if user_text:
        # Check if user is answering previous follow-ups
        answered_followups = []
        if st.session_state.last_followups and len(st.session_state.messages) > 0:
            # Check the last assistant message for follow-ups
            last_assistant_msg = None
            for msg in reversed(st.session_state.messages):
                if msg["role"] == "assistant":
                    last_assistant_msg = msg
                    break

            if last_assistant_msg and "followups" in last_assistant_msg:
                answered_followups = assistant.check_followup_answered(user_text, last_assistant_msg["followups"])

        # Store user message with context
        user_message_data = {
            "role": "user",
            "content": user_text,
            "followups": [],
            "timestamp": datetime.now().strftime("%H:%M")
        }

        if answered_followups:
            user_message_data["answered_followups"] = answered_followups

        st.session_state.messages.append(user_message_data)

        with st.chat_message("assistant", avatar="https://raw.githubusercontent.com/g-emar/g-emar/main/assets/chatbot.png"):
            message_placeholder = st.empty()
            with st.spinner("Analyzing..."):
                reply, rec_json, followups = assistant.answer(user_text)
                message_placeholder.markdown(reply)

                # Display follow-up questions immediately below the response with enhanced styling
                if followups:
                    st.markdown(FOLLOWUP_BANNER_HTML, unsafe_allow_html=True)
                    for fq in followups:
                        st.markdown(f"• {fq}")

            st.session_state.last_rec_json = rec_json
            st.session_state.last_followups = followups

            if st.session_state.debug:
                with st.expander("🕵️ Developer Info"):
                    st.caption("Recommender Model Output (JSON)")
                    st.code(json.dumps(rec_json, indent=2, ensure_ascii=False), language="json")
                    st.caption("Current Session Context")
                    st.code(st.session_state.ctx.to_compact_text())

        # Store assistant reply with follow-ups and timestamp
        assistant_message_data = {
            "role": "assistant",
            "content": reply,
            "followups": followups,
            "timestamp": datetime.now().strftime("%H:%M")
        }

        st.session_state.messages.append(assistant_message_data)


if __name__ == "__main__":
    main()
