import logging
import requests
import streamlit as st
from modules.nav import SideBarLinks
from modules.style import inject_custom_css, API_BASE

logger = logging.getLogger(__name__)

st.set_page_config(layout="wide")
SideBarLinks()
inject_custom_css()

st.title(f"Welcome, {st.session_state['first_name']} — Waiter")
st.caption("Take orders, track tables, and keep guests happy.")

user_id = st.session_state.get("user_id")

try:
    orders = requests.get(f"{API_BASE}/kitchen_orders", timeout=5).json()
    active_orders = sum(
        1 for o in orders
        if o.get("waiter_id") == user_id and o.get("status") not in ("completed", "cancelled")
    )
except Exception:
    active_orders = "—"

try:
    notifications = requests.get(f"{API_BASE}/notifications/{user_id}", timeout=5).json()
    unread_alerts = sum(1 for n in notifications if not n.get("is_read"))
except Exception:
    unread_alerts = "—"

try:
    menu_items = requests.get(f"{API_BASE}/menu_items", timeout=5).json()
    available_items = sum(
        1 for m in menu_items
        if str(m.get("availability_status", "")).lower() == "available"
    )
except Exception:
    available_items = "—"

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("My Active Orders", active_orders)
with col2:
    st.metric("Unread Alerts", unread_alerts)
with col3:
    st.metric("Available Items", available_items)

st.divider()

st.subheader("Quick Actions")
col1, col2, col3 = st.columns(3)
with col1:
    if st.button("My Orders", use_container_width=True, type="primary"):
        st.switch_page("pages/11_Current_Orders.py")
with col2:
    if st.button("Create Order", use_container_width=True, type="primary"):
        st.switch_page("pages/12_Create_Order.py")
with col3:
    if st.button("Notifications", use_container_width=True, type="primary"):
        st.switch_page("pages/13_Notifications.py")
