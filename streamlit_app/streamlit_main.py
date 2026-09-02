"""Streamlit chat UI for the RecruitAI proof of concept."""
# Help: Lesson 17 - ML Eval & vsCode & Modules & Git (Streamlit listed as a deploy option)

import sys
from datetime import date
from pathlib import Path
from uuid import uuid4

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.modules.agents.orchestrator import handle_turn, reset_session
from streamlit_app.utils import (
    LOGO_PATH,
    OPENING_MESSAGE,
    load_css,
    parse_simulated_date,
    registration_message,
)


def init_state():
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid4())
        history = reset_session(st.session_state.session_id)
        history.add_ai_message(OPENING_MESSAGE)
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": OPENING_MESSAGE, "action": "continue"}
        ]
    if "conversation_ended" not in st.session_state:
        st.session_state.conversation_ended = False
    if "conversation_started" not in st.session_state:
        st.session_state.conversation_started = False


def add_message(role, content, action=None):
    st.session_state.messages.append(
        {"role": role, "content": content, "action": action}
    )


def run_turn(text, conversation_dt):
    result = handle_turn(
        text,
        session_id=st.session_state.session_id,
        conversation_dt=conversation_dt,
    )
    add_message("user", text)
    add_message("assistant", result["message"], result["action"])
    st.session_state.conversation_started = True
    if result["action"] == "end":
        st.session_state.conversation_ended = True


st.set_page_config(
    page_title="RecruitAI",
    page_icon=str(LOGO_PATH) if LOGO_PATH.exists() else "💬",
    layout="centered",
)
st.markdown(load_css(), unsafe_allow_html=True)

# Branding header (presentation only — same title/caption as before).
header_logo, header_text = st.columns([1, 4])
with header_logo:
    if LOGO_PATH.exists():
        st.image(str(LOGO_PATH), width=108)
with header_text:
    st.markdown(
        """
        <div class="recruit-hero">
          <div class="recruit-title">RecruitAI</div>
          <div class="recruit-subtitle">Python Developer recruiting assistant</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

init_state()

with st.sidebar:
    if LOGO_PATH.exists():
        st.image(str(LOGO_PATH), width=150)
    st.markdown(
        '<div class="sidebar-brand-title">RecruitAI</div>'
        '<div class="sidebar-brand-sub">AI Recruiting Assistant</div>',
        unsafe_allow_html=True,
    )
    st.header("Session")
    simulated = st.date_input(
        "Conversation date",
        value=date.today(),
    )
    registration_locked = st.session_state.conversation_started
    name = st.text_input("Your name (optional)", disabled=registration_locked)
    note = st.text_area("Registration note (optional)", disabled=registration_locked)
    if st.button("Start with registration", disabled=registration_locked):
        text = registration_message(name, note)
        if text:
            with st.spinner("Thinking..."):
                run_turn(text, parse_simulated_date(simulated))
            st.rerun()
    if registration_locked:
        st.caption("Registration is locked once the conversation starts.")
    if st.button("Reset conversation"):
        st.session_state.session_id = str(uuid4())
        history = reset_session(st.session_state.session_id)
        history.add_ai_message(OPENING_MESSAGE)
        st.session_state.messages = [
            {"role": "assistant", "content": OPENING_MESSAGE, "action": "continue"}
        ]
        st.session_state.conversation_ended = False
        st.session_state.conversation_started = False
        st.rerun()

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])
        if message.get("action"):
            st.caption(f"action: {message['action']}")

if st.session_state.conversation_ended:
    st.info("This conversation has ended.")

# Keep the chat input rendered so the page layout does not shift when the chat ends.
user_text = st.chat_input(
    "Write a message",
    disabled=st.session_state.conversation_ended,
)
if user_text:
    with st.chat_message("user"):
        st.write(user_text)
    with st.chat_message("assistant"), st.spinner("Thinking..."):
        run_turn(user_text, parse_simulated_date(simulated))
    st.rerun()
