"""utils.py  –  Helper functions for the Streamlit travel app."""

import streamlit as st
from datetime import datetime


def init_session_state():
    """Initialise all required Streamlit session state keys."""
    defaults = {
        "messages": [],
        "agent": None,
        "evaluator": None,
        "quick_prompt": None,
        "booking_history": [],
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


def format_itinerary(messages: list) -> str:
    """Export the conversation as a Markdown document."""
    lines = [
        "# ✈️ Voyager AI – My Travel Plan",
        f"*Generated on {datetime.now().strftime('%B %d, %Y')}*",
        "",
        "---",
        "",
    ]
    for msg in messages:
        if msg["role"] == "user":
            lines.append(f"### 🙋 Me\n{msg['content']}\n")
        else:
            lines.append(f"### ✈️ Voyager AI\n{msg['content']}\n")
        lines.append("---\n")
    return "\n".join(lines)
