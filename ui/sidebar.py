"""
Sidebar UI: patient context editor, developer mode toggle, chat reset/export.
"""

import streamlit as st


def sidebar_context_editor():
    with st.sidebar:
        st.image("https://raw.githubusercontent.com/g-emar/g-emar/main/assets/g-emar-high-resolution-logo-transparent.png", width=150)
        st.header("Patient Context")
        st.caption("Manage patient details for tailored advice.")

        with st.expander("👤 Demographics", expanded=True):
            age = st.number_input("Age", min_value=0, max_value=120, value=st.session_state.ctx.age or 0, step=1, help="Patient's age in years.")
            gender_options = ["", "Male", "Female", "Other"]
            try:
                gender_index = [g.lower() for g in gender_options].index(st.session_state.ctx.gender)
            except (ValueError, AttributeError):
                gender_index = 0
            gender = st.selectbox("Gender", gender_options, index=gender_index, help="Patient's gender.")

        with st.expander("⚕️ Medical History", expanded=True):
            allergies = st.text_area("Allergies (one per line)", value="\n".join(st.session_state.ctx.allergies), height=100, help="List any known allergies.")
            meds = st.text_area("Current Meds (one per line)", value="\n".join(st.session_state.ctx.current_meds), height=100, help="List current medications.")
            conditions = st.text_area("Known Conditions (one per line)", value="\n".join(st.session_state.ctx.conditions), height=100, help="List pre-existing conditions.")

        st.session_state.ctx.age = int(age) if age > 0 else None
        st.session_state.ctx.gender = gender.lower() if gender else None
        st.session_state.ctx.allergies = [x.strip() for x in allergies.split("\n") if x.strip()]
        st.session_state.ctx.current_meds = [x.strip() for x in meds.split("\n") if x.strip()]
        st.session_state.ctx.conditions = [x.strip() for x in conditions.split("\n") if x.strip()]

        st.divider()

        st.header("⚙️ App Settings")
        st.session_state.debug = st.toggle("Developer Mode", value=st.session_state.debug, help="Show raw JSON output from the recommender model for debugging.")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("🗑️ Reset Chat", use_container_width=True, help="Clear the current conversation."):
                st.session_state.messages = []
                st.session_state.last_rec_json = None
                st.session_state.last_followups = []
                st.rerun()
        with col2:
            st.download_button(
                label="📥 Export Chat",
                data="\n\n".join([f"{m['role'].title()}:\n{m['content']}" for m in st.session_state.messages]),
                file_name="chat_history.txt",
                mime="text/plain",
                use_container_width=True,
                help="Download the chat history as a text file."
            )
