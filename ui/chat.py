"""
Chat session state initialization and chat history rendering.
"""

import streamlit as st

from core.context import UserContext
from core.router import SafetyRouter
from ui.styles import ANSWERED_FOLLOWUPS_HTML_TEMPLATE, FOLLOWUP_INLINE_HTML


def init_session():
    if "messages" not in st.session_state:
        st.session_state.messages = []  # list of {role, content}
    if "ctx" not in st.session_state:
        st.session_state.ctx = UserContext()
    if "router" not in st.session_state:
        st.session_state.router = SafetyRouter()
    if "debug" not in st.session_state:
        st.session_state.debug = False
    if "last_rec_json" not in st.session_state:
        st.session_state.last_rec_json = None
    if "last_followups" not in st.session_state:
        st.session_state.last_followups = []


def render_chat():
    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            # Show timestamp if available
            if "timestamp" in m:
                st.markdown(f"<small style='color: #64748b;'>{m['timestamp']}</small>", unsafe_allow_html=True)

            # Show main content
            st.markdown(m["content"])

            # Show follow-up questions if they exist for this message
            if "followups" in m and m["followups"]:
                st.markdown(FOLLOWUP_INLINE_HTML, unsafe_allow_html=True)
                for fq in m["followups"]:
                    st.markdown(f"• {fq}")

            # Show if user answered previous follow-ups
            if "answered_followups" in m and m["answered_followups"]:
                st.markdown(
                    ANSWERED_FOLLOWUPS_HTML_TEMPLATE.format(
                        answered_list=", ".join(m["answered_followups"])
                    ),
                    unsafe_allow_html=True,
                )
