"""
Floating MP Groundwater Intelligence chatbot.
Call render_floating_chatbot() once from dashboard/app.py after rendering the page.
"""

import re

import streamlit as st

from dashboard.utils import chatbot_service
from dashboard.views.chatbot import extract_location, geocode_location


GROUNDWATER_TERMS = (
    "groundwater",
    "ground water",
    "ground-water",
    "water level",
    "water table",
)


def _is_groundwater_question(question: str) -> bool:
    text = question.lower()
    return any(term in text for term in GROUNDWATER_TERMS)


def _extract_year(question: str):
    match = re.search(r"\b(202[1-6])\b", question)
    return int(match.group(1)) if match else None


def _answer_question(question: str) -> str:
    """Route groundwater questions through retrieval; general questions to Ollama."""
    if not _is_groundwater_question(question):
        return chatbot_service.generate_answer(question)

    location = extract_location(question)
    if not location:
        return (
            "Please include a locality, village, or city in Madhya Pradesh. "
            "For example: 'What is the groundwater level in Bhopal in 2025?'"
        )

    coordinates = geocode_location(location)
    if coordinates is None:
        return (
            f"I couldn't verify **{location}** as a location in Madhya Pradesh, India. "
            "Please try a nearby town, district, or a more specific locality."
        )

    latitude, longitude = coordinates
    year = _extract_year(question)

    context = chatbot_service.location_year_answer(
        latitude=latitude,
        longitude=longitude,
        year=year,
    )

    return chatbot_service.generate_answer(question, context)


def _inject_floating_chat_css():
    st.markdown(
        """
        <style>
        /* Keep the popover launcher visible at the lower-right of the viewport. */
        div[data-testid="stPopover"] {
            position: fixed !important;
            right: 26px !important;
            bottom: 24px !important;
            z-index: 99999 !important;
            width: auto !important;
        }

        div[data-testid="stPopover"] > button {
            min-height: 54px !important;
            min-width: 54px !important;
            border-radius: 999px !important;
            border: 1px solid #22d3ee !important;
            background: linear-gradient(135deg, #0891b2, #06b6d4) !important;
            color: #ffffff !important;
            font-size: 1.05rem !important;
            font-weight: 700 !important;
            box-shadow: 0 8px 28px rgba(6, 182, 212, .35) !important;
            padding: 0.65rem 1rem !important;
        }

        div[data-testid="stPopover"] > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 32px rgba(6, 182, 212, .48) !important;
        }

        div[data-testid="stPopoverBody"] {
            width: min(390px, calc(100vw - 32px)) !important;
            max-height: 72vh !important;
            overflow-y: auto !important;
            background: #ffffff !important;
            border: 1px solid #d9e5ef !important;
            border-radius: 16px !important;
            box-shadow: 0 16px 50px rgba(0, 0, 0, .45) !important;
        }

        div[data-testid="stPopoverBody"] [data-testid="stChatMessage"] {
            background: #f3f8fc;
            border: 1px solid #d9e5ef;
            border-radius: 12px;
            padding: .65rem;
        }

        div[data-testid="stPopoverBody"] .stTextInput input {
            background: #ffffff !important;
            color: #183247 !important;
            border: 1px solid #cbd9e6 !important;
        }

        @media (max-width: 640px) {
            div[data-testid="stPopover"] {
                right: 14px !important;
                bottom: 14px !important;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_floating_chatbot():
    """Render a persistent, floating chatbot launcher and conversation panel."""
    _inject_floating_chat_css()

    if "floating_chat_messages" not in st.session_state:
        st.session_state.floating_chat_messages = [
            {
                "role": "assistant",
                "content": (
                    "Hello! I'm the MP Groundwater AI Assistant. "
                    "Ask me about groundwater monitoring, historical readings, "
                    "or a location in Madhya Pradesh."
                ),
            }
        ]

    with st.popover("💧 Ask AI", help="Open MP Groundwater AI Assistant"):
        st.markdown("### 💧 Groundwater AI Assistant")
        st.caption("Ask about groundwater data or the project.")

        clear_col, status_col = st.columns([1, 2])
        with clear_col:
            if st.button(
                "Clear chat",
                key="floating_chat_clear",
                use_container_width=True,
            ):
                st.session_state.floating_chat_messages = []
                st.rerun()
        with status_col:
            st.caption("Powered by your existing Ollama + CGWB data pipeline")

        for message in st.session_state.floating_chat_messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        with st.form("floating_chat_form", clear_on_submit=True):
            question = st.text_input(
                "Your question",
                placeholder="e.g. Groundwater level in Bhopal in 2025",
                label_visibility="collapsed",
            )
            submitted = st.form_submit_button(
                "Send",
                type="primary",
                use_container_width=True,
            )

        if submitted and question.strip():
            question = question.strip()
            st.session_state.floating_chat_messages.append(
                {"role": "user", "content": question}
            )

            with st.spinner("Thinking..."):
                try:
                    answer = _answer_question(question)
                except Exception as exc:
                    answer = (
                        "Sorry, I couldn't process that question. "
                        "Please try again. If the problem continues, check that "
                        "the local Ollama service and project data files are available."
                    )

            st.session_state.floating_chat_messages.append(
                {"role": "assistant", "content": answer}
            )
            st.rerun()
