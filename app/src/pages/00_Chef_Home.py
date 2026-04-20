import logging
import requests
import streamlit as st
from modules.nav import SideBarLinks
from modules.style import inject_custom_css, API_BASE

logger = logging.getLogger(__name__)

st.set_page_config(layout="wide")
SideBarLinks()
inject_custom_css()

st.title(f"Welcome, {st.session_state['first_name']} — Chef")
st.caption("Manage kitchen operations, monitor inventory, and keep the menu fresh.")

try:
    orders = requests.get(f"{API_BASE}/kitchen_orders", timeout=5).json()
    pending_orders = sum(1 for o in orders if o.get("status") not in ("completed", "cancelled"))
except Exception:
    pending_orders = "—"

try:
    ingredients = requests.get(f"{API_BASE}/ingredients", timeout=5).json()
    low_stock = sum(1 for i in ingredients if i.get("quantity", 0) <= i.get("reorder_count", 0))
except Exception:
    low_stock = "—"

try:
    menu_items = requests.get(f"{API_BASE}/menu_items", timeout=5).json()
    total_menu = len(menu_items)
except Exception:
    total_menu = "—"

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Pending Orders", pending_orders)
with col2:
    st.metric("Low Stock Items", low_stock)
with col3:
    st.metric("Menu Items", total_menu)

st.divider()

st.subheader("Quick Actions")
col1, col2, col3 = st.columns(3)
with col1:
    if st.button("Inventory & Stock", use_container_width=True, type="primary"):
        st.switch_page("pages/01_Inventory.py")
with col2:
    if st.button("Order Management", use_container_width=True, type="primary"):
        st.switch_page("pages/02_Order_Management.py")
with col3:
    if st.button("Menu Management", use_container_width=True, type="primary"):
        st.switch_page("pages/03_Menu_Management.py")
