"""
app.py — GreenMind Streamlit Frontend
=======================================
Run:
  streamlit run app.py
"""

import streamlit as st
import requests
import uuid

# -----------------------------------------------------------------
# Config
# -----------------------------------------------------------------

API_URL = "http://localhost:8000"

MODE_META = {
    "educator":   {"icon": "🌍", "label": "Environmental Educator", "color": "#2e7d32"},
    "calculator": {"icon": "🧮", "label": "Footprint Calculator",  "color": "#1565c0"},
    "habit":      {"icon": "♻️", "label": "Habit Advisor",         "color": "#6a1b9a"},
    "unknown":    {"icon": "🤖", "label": "GreenMind",             "color": "#37474f"},
}

STARTER_PROMPTS = [
    "How much energy does a ChatGPT query use?",
    "I use AI 2 hours a day — what's my carbon footprint?",
    "How can I use AI more sustainably?",
]

# -----------------------------------------------------------------
# Page setup
# -----------------------------------------------------------------

st.set_page_config(
    page_title="GreenMind — Sustainable AI",
    page_icon="🌿",
    layout="centered",
)

st.markdown("""
<style>
.chat-message { padding: 0.75rem 1rem; border-radius: 12px; margin-bottom: 0.5rem; }
.user-msg     { background: #e8f5e9; text-align: right; }
.bot-msg      { background: #f1f8e9; text-align: left; }
.mode-badge   { display: inline-block; padding: 2px 10px; border-radius: 20px;
                font-size: 0.75rem; font-weight: 600; color: white; margin-bottom: 6px; }
div.stButton > button { width: 100%; text-align: left; font-size: 0.85rem; }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------
# Session state
# -----------------------------------------------------------------

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "messages" not in st.session_state:
    st.session_state.messages = []

if "active_mode" not in st.session_state:
    st.session_state.active_mode = "educator"

# -----------------------------------------------------------------
# API helpers
# -----------------------------------------------------------------

def send_message(user_text: str):
    try:
        r = requests.post(
            f"{API_URL}/chat",
            json={
                "message": user_text,
                "session_id": st.session_state.session_id
            },
            timeout=60,
        )
        r.raise_for_status()
        return r.json()
    except requests.exceptions.ConnectionError:
        st.error("Cannot reach API. Run: uvicorn api:app --reload")
    except Exception as e:
        st.error(f"API error: {e}")
    return None


def reset_session():
    try:
        requests.post(
            f"{API_URL}/reset",
            json={"session_id": st.session_state.session_id},
            timeout=10,
        )
    except Exception:
        pass

    st.session_state.messages = []
    st.session_state.session_id = str(uuid.uuid4())
    st.session_state.active_mode = "educator"

# -----------------------------------------------------------------
# Sidebar
# -----------------------------------------------------------------

with st.sidebar:
    st.image("https://em-content.zobj.net/source/twitter/376/seedling_1f331.png", width=60)
    st.title("GreenMind")
    st.caption("Sustainable AI Assistant")

    st.divider()

    mode = st.session_state.active_mode
    meta = MODE_META.get(mode, MODE_META["unknown"])

    st.markdown("**Active Mode**")
    st.markdown(
        f'<span class="mode-badge" style="background:{meta["color"]}">'
        f'{meta["icon"]} {meta["label"]}</span>',
        unsafe_allow_html=True,
    )

    st.divider()

    st.markdown("**What I can do:**")
    for m in ["educator", "calculator", "habit"]:
        info = MODE_META[m]
        st.markdown(f"{info['icon']} **{info['label']}**")

    st.divider()

    if st.button("🔄 New Conversation"):
        reset_session()
        st.rerun()

    st.caption(f"Session: `{st.session_state.session_id[:8]}…`")

# -----------------------------------------------------------------
# Main UI
# -----------------------------------------------------------------

st.markdown("## 🌿 GreenMind — Sustainable AI Assistant")
st.markdown(
    "Ask about AI's **environmental impact**, your **carbon footprint**, "
    "or **sustainable usage habits**."
)

# Starter prompts
if not st.session_state.messages:
    st.markdown("**Try asking:**")
    cols = st.columns(2)
    for i, prompt in enumerate(STARTER_PROMPTS):
        if cols[i % 2].button(prompt, key=f"starter_{i}"):
            st.session_state._pending = prompt
            st.rerun()

st.divider()

# -----------------------------------------------------------------
# Chat display
# -----------------------------------------------------------------

for msg in st.session_state.messages:
    if msg["role"] == "user":
        with st.chat_message("user"):
            st.markdown(msg["content"])
    else:
        mode = msg.get("mode", "educator")
        meta = MODE_META.get(mode, MODE_META["unknown"])

        with st.chat_message("assistant", avatar=meta["icon"]):
            st.markdown(
                f'<span class="mode-badge" style="background:{meta["color"]}">'
                f'{meta["icon"]} {meta["label"]}</span>',
                unsafe_allow_html=True,
            )
            st.markdown(msg["content"])

# -----------------------------------------------------------------
# Starter execution
# -----------------------------------------------------------------

if hasattr(st.session_state, "_pending"):
    prompt = st.session_state._pending
    del st.session_state._pending

    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.spinner("GreenMind is thinking…"):
        result = send_message(prompt)

    if result:
        st.session_state.active_mode = result.get("active_mode", "educator")
        st.session_state.messages.append({
            "role": "assistant",
            "content": result.get("response", "Error"),
            "mode": result.get("active_mode", "educator"),
        })

    st.rerun()

# -----------------------------------------------------------------
# Chat input
# -----------------------------------------------------------------

user_input = st.chat_input("Ask about AI & sustainability…")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.spinner("GreenMind is thinking…"):
        result = send_message(user_input)

    if result:
        st.session_state.active_mode = result.get("active_mode", "educator")
        st.session_state.messages.append({
            "role": "assistant",
            "content": result.get("response", "Error"),
            "mode": result.get("active_mode", "educator"),
        })
        print("MODE_DEBUG:", result.get("active_mode", "educator"))
    st.rerun()