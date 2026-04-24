import streamlit as st
import requests
import uuid
import os

st.set_page_config(
    page_title="Renewable Energy Myth Buster",
    page_icon="🌱",
    layout="centered",
)

API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost")
API_PORT = os.environ.get("API_PORT", "8001")

if "localhost" in API_BASE_URL or "127.0.0.1" in API_BASE_URL:
    API_URL = f"{API_BASE_URL}:8000/chat"
else:
    API_URL = f"{API_BASE_URL}:{API_PORT}/chat"

# Topic metadata for display
TOPIC_META = {
    "solar":   {"emoji": "☀️",  "label": "Solar Expert"},
    "wind":    {"emoji": "💨",  "label": "Wind Expert"},
    "storage": {"emoji": "🔋",  "label": "Storage Expert"},
    "grid":    {"emoji": "⚡",  "label": "Grid Expert"},
    "general": {"emoji": "🌱",  "label": "Renewables Expert"},
}

st.markdown(
    """
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display: none;}

    .chat-message {
        padding: 1.2rem 1.5rem;
        border-radius: 0.6rem;
        margin-bottom: 0.8rem;
    }
    .chat-message.user {
        background-color: #1e3a2f;
        color: #e6f4ea;
    }
    .chat-message.bot {
        background-color: #f0f7f0;
        color: #1a2e1a;
        border-left: 4px solid #4caf50;
    }
    .topic-badge {
        display: inline-block;
        padding: 0.2rem 0.7rem;
        border-radius: 999px;
        background-color: #4caf50;
        color: white;
        font-size: 0.8rem;
        font-weight: bold;
        margin-bottom: 0.5rem;
    }
    .myth-tip {
        font-size: 0.85rem;
        color: #555;
        font-style: italic;
    }
</style>
""",
    unsafe_allow_html=True,
)

# Session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "current_topic" not in st.session_state:
    st.session_state.current_topic = "general"
if "last_input" not in st.session_state:
    st.session_state.last_input = ""
if "input_key" not in st.session_state:
    st.session_state.input_key = 0
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

# Header
st.title("🌱 Renewable Energy Myth Buster")
st.markdown(
    "Challenge common misconceptions about solar, wind, batteries, and the grid. "
    "Our expert will correct the myths with real data!"
)

# Current expert badge
meta = TOPIC_META.get(st.session_state.current_topic, TOPIC_META["general"])
st.markdown(
    f'<div class="topic-badge">{meta["emoji"]} Currently talking to: {meta["label"]}</div>',
    unsafe_allow_html=True,
)

# Suggested starter myths
if not st.session_state.messages:
    st.markdown("**Try one of these common myths:**")
    starters = [
        "☀️ Solar panels produce more CO₂ to make than they ever save.",
        "💨 Wind turbines kill too many birds to be worth it.",
        "🔋 Batteries are too expensive and toxic to be a real solution.",
        "⚡ The grid can't be reliable if we use renewables.",
        "🌍 Renewables are still too expensive to replace fossil fuels.",
    ]
    for s in starters:
        st.markdown(f'<p class="myth-tip">{s}</p>', unsafe_allow_html=True)
    st.markdown("---")

# Chat history display
for message in st.session_state.messages:
    if message["role"] == "user":
        st.markdown(
            f'<div class="chat-message user">👤 <b>You:</b><br>{message["content"]}</div>',
            unsafe_allow_html=True,
        )
    else:
        topic = message.get("topic", "general")
        m = TOPIC_META.get(topic, TOPIC_META["general"])
        st.markdown(
            f'<div class="chat-message bot">{m["emoji"]} <b>{m["label"]}:</b><br>{message["content"]}</div>',
            unsafe_allow_html=True,
        )

# Input
with st.container():
    user_input = st.text_input(
        "Your myth or question:",
        placeholder="e.g. Solar panels don't work when it's cloudy...",
        key=f"user_input_{st.session_state.input_key}",
    )

if user_input and user_input != st.session_state.last_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    st.session_state.last_input = user_input

    with st.spinner("Consulting the expert..."):
        try:
            response = requests.post(
                API_URL,
                json={
                    "message": user_input,
                    "chat_history": [msg["content"] for msg in st.session_state.messages],
                    "session_id": st.session_state.session_id,
                },
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()

            st.session_state.messages.append(
                {
                    "role": "bot",
                    "content": data["response"],
                    "topic": data.get("topic", "general"),
                }
            )
            st.session_state.current_topic = data.get("topic", "general")
            st.session_state.input_key += 1
            st.experimental_rerun()

        except requests.exceptions.ConnectionError:
            st.error("❌ Could not connect to the API server. Is it running?")
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")

# Footer
st.markdown("---")
st.markdown(
    '<p class="myth-tip">Sources: IEA, IPCC, NREL, IRENA — facts updated as of 2024.</p>',
    unsafe_allow_html=True,
)
