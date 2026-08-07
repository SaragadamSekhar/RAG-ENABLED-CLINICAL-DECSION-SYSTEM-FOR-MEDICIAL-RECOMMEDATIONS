"""
Custom CSS and small reusable HTML snippets for the Streamlit UI.
"""

CUSTOM_CSS = """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&display=swap');
        body {
            font-family: 'Roboto', sans-serif;
            background-color: #f8fafc;
        }
        .main .block-container {
            padding: 2rem 3rem;
            max-width: 1200px;
        }
        /* Avatars */
        .st-emotion-cache-1c7y2kd .st-emotion-cache-p5carg { /* User Avatar */
            background-image: url('https://raw.githubusercontent.com/g-emar/g-emar/main/assets/user.png');
            background-size: cover;
        }
        .st-emotion-cache-4kckof .st-emotion-cache-p5carg { /* Assistant Avatar */
            background-image: url('https://raw.githubusercontent.com/g-emar/g-emar/main/assets/chatbot.png');
            background-size: cover;
        }
         /* Chat bubble animations and styling */
        .stChatMessage {
            transition: all 0.3s ease-in-out;
            margin-bottom: 1rem;
        }
        .stChatMessage:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        }
        /* Sidebar */
        [data-testid="stSidebar"] {
            background-color: #ffffff;
            border-right: 1px solid #e2e8f0;
            padding: 2rem 1.5rem;
            box-shadow: 2px 0 8px rgba(0,0,0,0.06);
        }
        /* Title */
        h1 {
            color: #1e40af;
            font-weight: 700;
            font-size: 2.5rem;
            margin-bottom: 0.5rem;
        }
        .stCaption {
            color: #64748b;
            font-size: 1.2rem;
            border-left: 4px solid #3b82f6;
            padding-left: 15px;
            margin-bottom: 2rem;
        }
        /* Buttons */
        .stButton>button {
            border-radius: 12px;
            border: 2px solid #3b82f6;
            background-color: #ffffff;
            color: #3b82f6;
            font-weight: 500;
            transition: all 0.2s ease;
            padding: 0.5rem 1rem;
        }
        .stButton>button:hover {
             background-color: #3b82f6;
             color: white;
             border-color: #3b82f6;
             transform: translateY(-1px);
        }
        /* Inputs */
        .stTextInput > div > div > input, .stTextArea > div > textarea, .stSelectbox > div > div {
            background-color: #f1f5f9;
            border-radius: 10px;
            border: 1px solid #cbd5e1;
            font-size: 1rem;
        }
        .stTextInput > div > div > input:focus, .stTextArea > div > textarea:focus, .stSelectbox > div > div:focus {
            border-color: #3b82f6;
            box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2);
        }
        /* Follow-up questions styling */
        .followup-questions {
            background-color: #eff6ff;
            border-left: 4px solid #3b82f6;
            padding: 1rem;
            margin-top: 1rem;
            border-radius: 8px;
        }
        /* Chat input */
        .stChatInput {
            background-color: #ffffff;
            border-radius: 12px;
            border: 2px solid #e2e8f0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }
        /* Loading spinner */
        .stSpinner > div {
            color: #3b82f6;
            font-weight: 500;
        }
    </style>
"""

FOLLOWUP_BANNER_HTML = """
<div style="background-color: #f0f9ff; border-left: 4px solid #0ea5e9; padding: 12px; margin-top: 12px; border-radius: 8px;">
    <strong style="color: #0369a1;">💡 Follow-up questions:</strong>
</div>
"""

FOLLOWUP_INLINE_HTML = """
<div class="followup-questions">
    <strong>💡 Follow-up questions:</strong>
</div>
"""

ANSWERED_FOLLOWUPS_HTML_TEMPLATE = """
<div style="background-color: #dcfce7; border-left: 4px solid #22c55e; padding: 8px; margin-top: 8px; border-radius: 6px;">
    <strong style="color: #15803d;">✓ Answered:</strong> {answered_list}
</div>
"""
