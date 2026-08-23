"""Streamlit chat UI for the RecruitAI proof of concept."""

import sys
from datetime import date
from pathlib import Path
from uuid import uuid4

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.modules.agents.orchestrator import handle_turn, reset_session
from streamlit_app.utils import OPENING_MESSAGE, parse_simulated_date, registration_message


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
    if result["action"] == "end":
        st.session_state.conversation_ended = True


st.set_page_config(page_title="RecruitAI", page_icon="💬")
st.title("RecruitAI")
st.caption("Python Developer recruiting assistant")

init_state()

with st.sidebar:
    st.header("Session")
    simulated = st.date_input(
        "Conversation date",
        value=date.today(),
    )
    name = st.text_input("Your name (optional)")
    note = st.text_area("Registration note (optional)")
    if st.button("Start with registration"):
        text = registration_message(name, note)
        if text:
            with st.spinner("Thinking..."):
                run_turn(text, parse_simulated_date(simulated))
            st.rerun()
    if st.button("Reset conversation"):
        st.session_state.session_id = str(uuid4())
        history = reset_session(st.session_state.session_id)
        history.add_ai_message(OPENING_MESSAGE)
        st.session_state.messages = [
            {"role": "assistant", "content": OPENING_MESSAGE, "action": "continue"}
        ]
        st.session_state.conversation_ended = False
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
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            run_turn(user_text, parse_simulated_date(simulated))
    st.rerun()
