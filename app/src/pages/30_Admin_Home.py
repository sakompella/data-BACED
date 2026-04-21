import logging
import requests
import streamlit as st
from modules.nav import SideBarLinks
from modules.style import inject_custom_css, API_BASE

logger = logging.getLogger(__name__)

st.set_page_config(layout='wide')
SideBarLinks()
inject_custom_css()

st.title(f"Welcome, {st.session_state['first_name']}, Administrator")
st.caption("Manage users, roles, menu configuration, and system activity.")

col1, col2, col3, col4 = st.columns(4)

with col1:
    try:
        data = requests.get(f"{API_BASE}/users").json()
        st.metric("Total Users", len(data))
    except Exception:
        st.metric("Total Users", "N/A")

with col2:
    try:
        data = requests.get(f"{API_BASE}/roles").json()
        st.metric("Roles Defined", len(data))
    except Exception:
        st.metric("Roles Defined", "N/A")

with col3:
    try:
        data = requests.get(f"{API_BASE}/menu_items").json()
        st.metric("Menu Items", len(data))
    except Exception:
        st.metric("Menu Items", "N/A")

with col4:
    try:
        data = requests.get(f"{API_BASE}/activity_log").json()
        st.metric("Activity Logs", len(data))
    except Exception:
        st.metric("Activity Logs", "N/A")

st.divider()
st.subheader("Quick Actions")

c1, c2, c3 = st.columns(3)

with c1:
    if st.button("Users & Activity", type='primary', use_container_width=True):
        st.switch_page('pages/31_Users_Activity.py')

with c2:
    if st.button("System & Data", type='primary', use_container_width=True):
        st.switch_page('pages/32_System_Data.py')

with c3:
    if st.button("Menu Config", type='primary', use_container_width=True):
        st.switch_page('pages/33_Menu_Configuration.py')
