import streamlit as st

API_BASE = "http://api:4000"

STATUS_EMOJI = {
    "low":       "🔴", "red":       "🔴", "high":      "🔴",
    "inactive":  "🔴", "cancelled": "🔴",
    "ok":        "🟢", "green":     "🟢", "active":    "🟢",
    "ready":     "🟢", "completed": "🟢",
    "expiring":  "🟡", "amber":     "🟡", "warning":   "🟡",
    "cooking":   "🟡", "in_progress": "🟡", "medium":  "🟡",
    "pending":   "🟡",
    "queued":    "⚪", "gray":      "⚪", "open":      "⚪",
    "prepping":  "🔵", "blue":      "🔵",
}


def status_text(text: str, color_key: str = "") -> str:
    """Return an emoji-prefixed status string for native Streamlit display."""
    key = (color_key or text).lower().strip()
    emoji = STATUS_EMOJI.get(key, "⚪")
    return f"{emoji} {text}"


def inject_custom_css():
    """Inject minimal global CSS for design system consistency."""
    st.markdown("""
    <style>
    .stButton > button[kind="primary"] {
        background-color: #2E75ED;
        border-color: #2E75ED;
    }
    div[data-testid="stExpander"] {
        border: 1px solid #E0E0E0;
        border-radius: 8px;
    }
    </style>
    """, unsafe_allow_html=True)
