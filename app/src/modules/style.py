import streamlit as st

API_BASE = "http://api:4000"

STATUS_COLORS: dict[str, str] = {
    "low":          "background-color: #E53836; color: white",
    "red":          "background-color: #E53836; color: white",
    "high":         "background-color: #E53836; color: white",
    "inactive":     "background-color: #E53836; color: white",
    "cancelled":    "background-color: #E53836; color: white",
    "unavailable":  "background-color: #E53836; color: white",
    "ok":           "background-color: #4CAF50; color: white",
    "green":        "background-color: #4CAF50; color: white",
    "active":       "background-color: #4CAF50; color: white",
    "ready":        "background-color: #4CAF50; color: white",
    "completed":    "background-color: #4CAF50; color: white",
    "available":    "background-color: #4CAF50; color: white",
    "expiring":     "background-color: #FFD600; color: black",
    "amber":        "background-color: #FFD600; color: black",
    "warning":      "background-color: #FFD600; color: black",
    "in_progress":  "background-color: #FFD600; color: black",
    "medium":       "background-color: #FFD600; color: black",
    "pending":      "background-color: #FFD600; color: black",
    "cooking":      "background-color: #FFD600; color: black",
    "open":         "background-color: #E0E0E0; color: black",
    "queued":       "background-color: #E0E0E0; color: black",
    "gray":         "background-color: #E0E0E0; color: black",
}


def status_css(key: str) -> str:
    """Return a CSS string for use with df.style.map()."""
    return STATUS_COLORS.get(key.lower().strip(), "")


def status_badge(text: str, color_key: str = "") -> str:
    """Return an HTML badge string for use with st.markdown(unsafe_allow_html=True)."""
    key = (color_key or text).lower().strip()
    css = STATUS_COLORS.get(key, "background-color: #E0E0E0; color: black")
    return f'<span style="{css}; padding: 2px 8px; border-radius: 4px; font-size: 0.85em;">{text}</span>'


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
    div[data-testid="stMetric"] {
        margin-bottom: 8px;
    }
    </style>
    """, unsafe_allow_html=True)
