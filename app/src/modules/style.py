import streamlit as st

API_BASE = "http://api:4000"

STATUS_COLORS = {
    "low":      ("#FDECEA", "#E53836"),
    "red":      ("#FDECEA", "#E53836"),
    "high":     ("#FDECEA", "#E53836"),
    "inactive": ("#FDECEA", "#E53836"),
    "ok":       ("#E8F5E9", "#2EB859"),
    "green":    ("#E8F5E9", "#2EB859"),
    "active":   ("#E8F5E9", "#2EB859"),
    "ready":    ("#E8F5E9", "#2EB859"),
    "completed":("#E8F5E9", "#2EB859"),
    "expiring": ("#FFF3E0", "#EDA321"),
    "amber":    ("#FFF3E0", "#EDA321"),
    "warning":  ("#FFF3E0", "#EDA321"),
    "cooking":  ("#FFF3E0", "#EDA321"),
    "in_progress": ("#FFF3E0", "#EDA321"),
    "medium":   ("#FFF3E0", "#EDA321"),
    "pending":  ("#FFF3E0", "#EDA321"),
    "queued":   ("#EDEDED", "#555555"),
    "gray":     ("#EDEDED", "#555555"),
    "open":     ("#EDEDED", "#555555"),
    "prepping": ("#E3F2FD", "#2E75ED"),
    "blue":     ("#E3F2FD", "#2E75ED"),
    "cancelled":("#FDECEA", "#E53836"),
}


def status_badge(text: str, color_key: str = "") -> str:
    """Return an HTML span styled as a status pill badge."""
    key = (color_key or text).lower().strip()
    bg, fg = STATUS_COLORS.get(key, ("#EDEDED", "#555555"))
    return (
        f'<span style="background:{bg};color:{fg};padding:2px 10px;'
        f'border-radius:12px;font-size:0.85em;font-weight:600;">'
        f'{text}</span>'
    )


def inject_custom_css():
    """Inject global custom CSS matching the Figma design system."""
    st.markdown("""
    <style>
    /* Table header styling */
    .stDataFrame thead th {
        background-color: #F0F0F0 !important;
        font-weight: 600;
    }
    /* Primary action button override */
    .stButton > button[kind="primary"] {
        background-color: #2E75ED;
        border-color: #2E75ED;
    }
    /* Card-like containers */
    div[data-testid="stExpander"] {
        border: 1px solid #E0E0E0;
        border-radius: 8px;
    }
    </style>
    """, unsafe_allow_html=True)
