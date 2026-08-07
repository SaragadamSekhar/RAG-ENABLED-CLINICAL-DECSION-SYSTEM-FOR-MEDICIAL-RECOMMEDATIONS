# GenAI Clinical Drug Recommendation

A Streamlit chat assistant that pipelines two Gemma-2-2B models:

1. **RecommenderModel** (`google/gemma-2-2b` + LoRA adapter) — turns the
   conversation into strict, schema-constrained JSON (likely condition,
   suggested OTC medicines, home care, red flags, follow-up questions).
2. **ChatModel** (`google/gemma-2-2b-it`) — turns that JSON into a
   natural-language reply for the user, following hard safety rules
   (no antibiotics without a doctor diagnosis, always show warnings and
   "when to see a doctor", pediatric dosing caveats, etc.).

A rule-based `SafetyRouter` sits in front of both models to classify
intent (`greeting` / `emergency` / `symptom` / `drug_info` / `unknown`),
bypass the models entirely on red-flag emergency phrases, and decide
which follow-up questions (age, fever duration/temperature, etc.) are
still missing.

> ⚠️ Educational/demo project only — not a substitute for professional
> medical advice.

## Project layout

```
GenAI-Clinical-Drug-Recommendation/
│
├── app.py                     # Streamlit entrypoint: page setup + chat loop
├── requirements.txt
├── README.md
├── .gitignore
│
├── models/
│   ├── chat_model.py          # ChatModel (gemma-2-2b-it)
│   ├── recommender_model.py   # RecommenderModel (gemma-2-2b + LoRA)
│   └── __init__.py
│
├── core/
│   ├── assistant.py           # HybridMedicalAssistant orchestrator
│   ├── router.py              # SafetyRouter (intent + missing-question logic)
│   ├── context.py             # UserContext dataclass
│   └── __init__.py
│
├── ui/
│   ├── sidebar.py              # Patient-context editor, settings, reset/export
│   ├── chat.py                 # Session-state init + chat history rendering
│   ├── styles.py                # CSS + reusable HTML snippets
│   └── __init__.py
│
├── utils/
│   ├── helpers.py               # extract_json(), clean_model_output()
│   ├── prompts.py                # Prompt templates + JSON schema
│   └── __init__.py
│
├── assets/
│   ├── chatbot.png              # (add your own assets)
│   ├── user.png
│   └── logo.png
│
└── docs/
    ├── architecture.png
    └── screenshots/
```

## How the pieces fit together

- `app.py` calls `ui.chat.init_session()` and `ui.sidebar.sidebar_context_editor()`,
  loads both models once via `@st.cache_resource`, builds a
  `core.assistant.HybridMedicalAssistant`, and drives the `st.chat_input` loop.
- `core.assistant.HybridMedicalAssistant.answer()` is the single entrypoint
  used per turn: it updates `core.context.UserContext` from free text,
  classifies intent with `core.router.SafetyRouter`, calls
  `models.recommender_model.RecommenderModel.recommend_json()`, then
  `models.chat_model.ChatModel.generate()`, and cleans the output with
  `utils.helpers.clean_model_output()`.
- `utils/prompts.py` centralizes every prompt string and the JSON schema
  so both models stay in sync without duplicating text across files.

## Setup

```bash
pip install -r requirements.txt
export HF_TOKEN=your_huggingface_token
streamlit run app.py
```

## Notes on this split

- Behavior is unchanged from the original single-file `app.py` — this is
  a structural refactor only, no logic was altered.
- One small bug fix: the "✓ Answered" banner in the original used an
  f-string expression inside a non-f-string, so it never actually
  interpolated. `ui/styles.py` now exposes it as a `.format()` template
  used correctly in `ui/chat.py`.
- `assets/` and `docs/` are placeholders — add your own images there.
