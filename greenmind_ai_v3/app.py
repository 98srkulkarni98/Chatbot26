"""
app.py — GreenMind Streamlit Frontend v2.0
===========================================
Implements the full guided conversation flow:
  1. Welcome screen with starter buttons
  2. Onboarding (4 button-driven questions)
  3. Diagnosis + Eco Score reveal
  4. Prompt coaching (paste your prompt)
  5. What-if simulation
  6. Habit tracker activation
  7. Normal ongoing chat

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
    "prompt":   {"icon": "✏️",  "label": "Prompt Advisor",       "color": "#1565C0"},
    "educator": {"icon": "🌍",  "label": "Environmental Coach",  "color": "#2e7d32"},
    "habit":    {"icon": "♻️",  "label": "Habit Advisor",        "color": "#6a1b9a"},
    "none":     {"icon": "🤖",  "label": "GreenMind",            "color": "#37474f"},
}

STARTER_BUTTONS = [
    ("🕒", "I spend too much time on ChatGPT"),
    ("🔁", "I keep retrying answers"),
    ("💬", "My prompts don't work well"),
    ("💻", "I use AI all day for coding"),
    ("📊", "Check my AI habits"),
]

ECO_BANDS = [
    (80, "🌳", "Excellent",  "#2e7d32"),
    (60, "🌿", "Good",       "#558b2f"),
    (40, "🌱", "Fair",       "#f9a825"),
    (0,  "🍂", "Needs work", "#bf360c"),
]


def eco_band(score):
    for threshold, icon, label, color in ECO_BANDS:
        if score >= threshold:
            return icon, label, color
    return "🍂", "Needs work", "#bf360c"


# -----------------------------------------------------------------
# Page setup
# -----------------------------------------------------------------

st.set_page_config(
    page_title="GreenMind — Sustainable AI for Students",
    page_icon="🌿",
    layout="centered",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600&family=DM+Mono:wght@400;500&display=swap');

html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }

/* Quick-reply button row */
.stButton > button {
    border-radius: 20px !important;
    border: 1.5px solid #1565C0 !important;
    color: #1565C0 !important;
    background: #fff !important;
    font-size: 0.85rem !important;
    padding: 0.35rem 1rem !important;
    transition: all .15s !important;
    white-space: nowrap;
}
.stButton > button:hover {
    background: #E3F2FD !important;
    border-color: #0d47a1 !important;
}

/* Eco score card */
.eco-card {
    border-radius: 16px;
    padding: 1.5rem 2rem;
    margin: 1rem 0;
    text-align: center;
}
.eco-score-number {
    font-size: 4rem;
    font-weight: 600;
    line-height: 1;
}
.eco-band-label {
    font-size: 1rem;
    opacity: 0.8;
    margin-top: 4px;
}

/* Diagnosis check list */
.check-item {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 6px 0;
    font-size: 0.9rem;
    color: #37474f;
}

/* Mode badge */
.mode-badge {
    display: inline-block;
    padding: 2px 12px;
    border-radius: 20px;
    font-size: 0.72rem;
    font-weight: 600;
    color: white;
    margin-bottom: 5px;
}

/* Progress bar for onboarding */
.progress-label {
    font-size: 0.75rem;
    color: #78909c;
    margin-bottom: 4px;
}

/* What-if box */
.whatif-box {
    background: #E8F5E9;
    border-left: 4px solid #2e7d32;
    border-radius: 8px;
    padding: 1rem 1.2rem;
    margin: 0.8rem 0;
    font-size: 0.88rem;
}

/* Habit tracker card */
.habit-card {
    background: #F3E5F5;
    border-radius: 12px;
    padding: 1rem 1.2rem;
    margin: 0.8rem 0;
}
</style>
""", unsafe_allow_html=True)


# -----------------------------------------------------------------
# Session state init
# -----------------------------------------------------------------

def _init():
    defaults = {
        "session_id":         str(uuid.uuid4()),
        "messages":           [],
        "active_mode":        "none",
        "phase":              "welcome",       # welcome | onboarding | active
        "onboarding_step":    0,
        "onboarding_total":   4,
        "eco_score":          None,
        "diagnosis":          [],
        "profile":            {},
        "habit_activated":    False,
        "show_whatif":        False,
        "whatif_data":        None,
        "pending_message":    None,
        "pending_onboard_answer": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

_init()


# -----------------------------------------------------------------
# API helpers
# -----------------------------------------------------------------

def api_post(endpoint, payload, timeout=60):
    try:
        r = requests.post(f"{API_URL}{endpoint}", json=payload, timeout=timeout)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"API error ({endpoint}): {e}")
        return None


def api_get(endpoint, timeout=15):
    try:
        r = requests.get(f"{API_URL}{endpoint}", timeout=timeout)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"API error ({endpoint}): {e}")
        return None


def send_chat(text: str):
    return api_post("/chat", {
        "message":    text,
        "session_id": st.session_state.session_id,
    })


def start_onboarding():
    return api_post("/onboard/start", {
        "session_id": st.session_state.session_id,
    })


def send_onboard_answer(answer: str):
    return api_post("/onboard/answer", {
        "session_id": st.session_state.session_id,
        "answer":     answer,
    })


def reset_session():
    api_post("/reset", {"session_id": st.session_state.session_id})
    for k in list(st.session_state.keys()):
        del st.session_state[k]
    _init()


# -----------------------------------------------------------------
# Message helpers
# -----------------------------------------------------------------

def push_user(text):
    st.session_state.messages.append({"role": "user", "content": text})


def push_bot(text, mode="none", extra=None):
    st.session_state.messages.append({
        "role":    "assistant",
        "content": text,
        "mode":    mode,
        "extra":   extra,   # dict with eco_score / habit / whatif data
    })


# -----------------------------------------------------------------
# Sidebar
# -----------------------------------------------------------------

with st.sidebar:
    st.markdown("### 🌿 GreenMind")
    st.caption("Sustainable AI coach for students")
    st.divider()

    mode = st.session_state.active_mode
    meta = MODE_META.get(mode, MODE_META["none"])
    st.markdown("**Active mode**")
    st.markdown(
        f'<span class="mode-badge" style="background:{meta["color"]}">'
        f'{meta["icon"]} {meta["label"]}</span>',
        unsafe_allow_html=True,
    )
    st.divider()

    # Eco score in sidebar
    if st.session_state.eco_score:
        sc = st.session_state.eco_score["score"]
        icon, label, color = eco_band(sc)
        st.markdown("**Your Eco Score**")
        st.markdown(
            f'<div style="font-size:2.2rem;font-weight:600;color:{color}">'
            f'{icon} {sc}<span style="font-size:1rem;color:#90a4ae"> / 100</span></div>'
            f'<div style="font-size:0.8rem;color:{color};margin-bottom:8px">{label}</div>',
            unsafe_allow_html=True,
        )
        st.divider()

    # Habit tracker status
    if st.session_state.habit_activated:
        st.markdown("**🗓 Habit tracker**")
        st.markdown("✓ Independent thinking  \n✓ Retries  \n✓ Prompt quality")
        goal = st.session_state.get("habit_goal", "Reduce retries by 30%")
        st.caption(f"Week goal: {goal}")
        st.divider()

    # What-if toggle
    if st.session_state.whatif_data:
        wi = st.session_state.whatif_data
        if st.button("📈 Show what-if simulation"):
            st.session_state.show_whatif = not st.session_state.show_whatif

    if st.session_state.show_whatif and st.session_state.whatif_data:
        wi = st.session_state.whatif_data
        st.markdown(
            f'<div class="whatif-box">'
            f'<b>What if you: {wi["action"]}?</b><br><br>'
            f'✓ +{wi["points_gained"]} Eco points<br>'
            f'✓ Fewer AI queries<br>'
            f'✓ Faster task completion<br>'
            f'✓ Lower environmental footprint<br><br>'
            f'<b>New score: {wi["new_score"]} / 100</b>'
            f'</div>',
            unsafe_allow_html=True,
        )
        st.divider()

    if st.button("🔄 New conversation"):
        reset_session()
        st.rerun()

    st.caption(f"Session: `{st.session_state.session_id[:8]}…`")


# -----------------------------------------------------------------
# Main header
# -----------------------------------------------------------------

st.markdown("## 🌿 GreenMind")
st.markdown("*Your sustainable AI coach — helping students write better prompts, build greener habits, and understand AI's real cost.*")
st.divider()


# -----------------------------------------------------------------
# PHASE: Welcome
# -----------------------------------------------------------------

def render_welcome():
    st.markdown(
        """
        **Hi, I'm GreenMind 🌱**

        I help students use AI smarter — save time, reduce retries,
        and build healthier AI habits.

        **What's happening with your AI usage today?**
        """
    )
    cols = st.columns(2)
    for i, (icon, label) in enumerate(STARTER_BUTTONS):
        if cols[i % 2].button(f"{icon} {label}", key=f"starter_{i}"):
            st.session_state.pending_message = label
            st.rerun()


# -----------------------------------------------------------------
# PHASE: Onboarding — render current question + buttons
# -----------------------------------------------------------------

def render_onboarding_question(question: str, buttons: list, step: int, total: int):
    pct = int((step / total) * 100)
    st.markdown(
        f'<div class="progress-label">Setting up your profile — question {step + 1} of {total}</div>',
        unsafe_allow_html=True,
    )
    st.progress(pct)
    st.markdown(f"**{question}**")
    cols = st.columns(min(len(buttons), 4))
    for i, btn in enumerate(buttons):
        if cols[i % len(cols)].button(btn, key=f"ob_{step}_{i}"):
            st.session_state.pending_onboard_answer = btn
            st.rerun()


# -----------------------------------------------------------------
# PHASE: Eco score reveal
# -----------------------------------------------------------------

def render_eco_score(eco: dict, diagnosis: list):
    sc               = eco["score"]
    icon, label, col = eco_band(sc)

    st.markdown(
        f'<div class="eco-card" style="background:{col}18;border:2px solid {col}40">'
        f'<div style="font-size:1.1rem;font-weight:500;color:{col};margin-bottom:8px">Your Green Score</div>'
        f'<div class="eco-score-number" style="color:{col}">{icon} {sc}</div>'
        f'<div class="eco-band-label" style="color:{col}">/ 100 — {label}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    if diagnosis:
        st.markdown("**What we detected:**")
        for d in diagnosis:
            st.markdown(
                f'<div class="check-item">✓ {d}</div>',
                unsafe_allow_html=True,
            )

    if eco.get("loss_factors"):
        st.markdown("**Main factors:**")
        for f in eco["loss_factors"]:
            st.markdown(f"− {f}")

    # Store what-if for sidebar
    if eco.get("what_if"):
        st.session_state.whatif_data = eco["what_if"]


# -----------------------------------------------------------------
# Habit tracker reveal
# -----------------------------------------------------------------

def render_habit_activated(tracking: dict):
    goal = tracking.get("week_goal", "Reduce retries by 30%")
    st.session_state.habit_activated = True
    st.session_state.habit_goal      = goal
    st.markdown(
        f'<div class="habit-card">'
        f'<b>🗓 Habit tracking activated!</b><br><br>'
        f'Tomorrow I\'ll track:<br>'
        f'✓ Independent thinking (try before asking AI)<br>'
        f'✓ Retries<br>'
        f'✓ Prompt quality<br><br>'
        f'<b>Your goal this week:</b> {goal}'
        f'</div>',
        unsafe_allow_html=True,
    )


# -----------------------------------------------------------------
# Chat history renderer
# -----------------------------------------------------------------

def render_history():
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            with st.chat_message("user"):
                st.markdown(msg["content"])
        else:
            mode = msg.get("mode", "none")
            meta = MODE_META.get(mode, MODE_META["none"])
            with st.chat_message("assistant", avatar=meta["icon"]):
                st.markdown(
                    f'<span class="mode-badge" style="background:{meta["color"]}">'
                    f'{meta["icon"]} {meta["label"]}</span>',
                    unsafe_allow_html=True,
                )
                st.markdown(msg["content"])

                # Render extras embedded in the message
                extra = msg.get("extra") or {}
                if extra.get("type") == "onboarding_complete":
                    render_eco_score(extra["eco_score"], extra.get("diagnosis", []))
                if extra.get("type") == "habit_activated":
                    render_habit_activated(extra.get("tracking", {}))


# -----------------------------------------------------------------
# ── MAIN RENDER LOOP ─────────────────────────────────────────────
# -----------------------------------------------------------------

# ── 1. Process pending starter button click ──────────────────────

if st.session_state.pending_message and st.session_state.phase == "welcome":
    text = st.session_state.pending_message
    st.session_state.pending_message = None

    push_user(text)
    push_bot(
        "I can help with that! Let me ask you a few quick questions to understand your AI habits.",
        mode="none",
    )

    with st.spinner("Setting up your profile…"):
        result = start_onboarding()

    if result:
        st.session_state.phase = "onboarding"
        st.session_state["_ob_question"] = result["message"]
        st.session_state["_ob_buttons"]  = result.get("buttons", [])
        st.session_state["_ob_step"]     = result.get("step", 0)
        st.session_state["_ob_total"]    = result.get("total", 4)

    st.rerun()


# ── 2. Process pending onboarding answer ────────────────────────

if st.session_state.pending_onboard_answer and st.session_state.phase == "onboarding":
    answer = st.session_state.pending_onboard_answer
    st.session_state.pending_onboard_answer = None

    push_user(answer)

    with st.spinner("Got it…"):
        result = send_onboard_answer(answer)

    if result:
        if result["type"] == "onboarding":
            # Next question
            st.session_state["_ob_question"] = result["message"]
            st.session_state["_ob_buttons"]  = result.get("buttons", [])
            st.session_state["_ob_step"]     = result.get("step", 0)
            st.session_state["_ob_total"]    = result.get("total", 4)
        else:
            # Onboarding complete
            st.session_state.phase     = "active"
            st.session_state.eco_score = result.get("eco_score")

            push_bot(
                result["message"],
                mode  = "prompt",
                extra = {
                    "type":      "onboarding_complete",
                    "eco_score": result.get("eco_score", {}),
                    "diagnosis": result.get("diagnosis", []),
                },
            )
            st.session_state.active_mode = "prompt"

    st.rerun()


# ── 3. Render welcome or history ─────────────────────────────────

render_history()

if st.session_state.phase == "welcome" and not st.session_state.messages:
    render_welcome()

if st.session_state.phase == "onboarding":
    render_onboarding_question(
        st.session_state.get("_ob_question", ""),
        st.session_state.get("_ob_buttons",  []),
        st.session_state.get("_ob_step",     0),
        st.session_state.get("_ob_total",    4),
    )


# ── 4. Normal chat input (active phase) ──────────────────────────

if st.session_state.phase == "active":

    # Quick-reply buttons after eco score is shown (habit question)
    if (
        st.session_state.eco_score
        and not st.session_state.habit_activated
        and len(st.session_state.messages) > 0
    ):
        last = st.session_state.messages[-1]
        if last.get("role") == "assistant" and "habit" in last.get("content", "").lower():
            c1, c2 = st.columns(2)
            if c1.button("✅ Yes, track my habits"):
                st.session_state.pending_message = "Yes"
                st.rerun()
            if c2.button("⏩ Maybe later"):
                st.session_state.pending_message = "Maybe later"
                st.rerun()

    user_input = st.chat_input("Paste a prompt or ask about your AI habits…")

    if user_input:
        push_user(user_input)

        with st.spinner("GreenMind is thinking…"):
            result = send_chat(user_input)

        if result:
            mode = result.get("active_mode", "none")
            if mode not in MODE_META:
                mode = "none"
            st.session_state.active_mode = mode

            structured = result.get("structured")

            # Handle habit activation structured response
            if structured and structured.get("type") == "habit_activated":
                push_bot(
                    result["response"],
                    mode  = "habit",
                    extra = structured,
                )
            else:
                push_bot(result.get("response", ""), mode=mode)

        st.rerun()

    # Handle pending "Yes" / "Maybe later" for habit from sidebar quick reply
    if st.session_state.pending_message and st.session_state.phase == "active":
        text = st.session_state.pending_message
        st.session_state.pending_message = None
        push_user(text)

        with st.spinner("GreenMind is thinking…"):
            result = send_chat(text)

        if result:
            structured = result.get("structured")
            mode       = result.get("active_mode", "none")
            if mode not in MODE_META:
                mode = "none"
            st.session_state.active_mode = mode

            if structured and structured.get("type") == "habit_activated":
                push_bot(result["response"], mode="habit", extra=structured)
            else:
                push_bot(result.get("response", ""), mode=mode)

        st.rerun()
