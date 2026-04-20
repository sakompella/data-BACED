import logging
logger = logging.getLogger(__name__)

import streamlit as st
import requests
from modules.nav import SideBarLinks
from modules.style import inject_custom_css, status_text, API_BASE

st.set_page_config(layout="wide")
SideBarLinks()
inject_custom_css()

st.title("My Notifications")

waiter_id = st.session_state.get("user_id")
if waiter_id is None:
    st.error("No waiter session is active. Return to Home and choose a user.")
    st.stop()

# ---------------------------------------------------------------------------
# Fetch notifications for this user
# ---------------------------------------------------------------------------
try:
    resp = requests.get(f"{API_BASE}/notifications/{waiter_id}")
    resp.raise_for_status()
    notifications = resp.json()
except requests.RequestException:
    st.error("Failed to load notifications from the server.")
    notifications = []

# ---------------------------------------------------------------------------
# Filter tabs
# ---------------------------------------------------------------------------
tab_all, tab_unread, tab_read = st.tabs(["All", "Unread", "Read"])


def _mark_read(alert_id: int) -> bool:
    try:
        resp = requests.put(
            f"{API_BASE}/notifications/{alert_id}",
            json={"is_read": 1},
        )
        resp.raise_for_status()
        return True
    except requests.RequestException as e:
        st.error(f"Failed to mark as read: {e}")
        return False


def display_notifications(notif_list, key_prefix: str):
    if not notif_list:
        st.info("No notifications.")
        return

    for notif in notif_list:
        alert_id = notif.get("alert_id")
        message = notif.get("message", "")
        created_at = notif.get("created_at", "")
        is_read = notif.get("is_read", 0)

        with st.container(border=True):
            cols = st.columns([4, 1, 1])
            with cols[0]:
                st.markdown(f"**{message}**")
                st.caption(str(created_at))
            with cols[1]:
                if is_read:
                    st.markdown(status_text("Read", "green"))
                else:
                    st.markdown(status_text("Unread", "amber"))
            with cols[2]:
                if not is_read:
                    if st.button("Mark Read", key=f"mark_read_{key_prefix}_{alert_id}"):
                        if _mark_read(alert_id):
                            st.rerun()

with tab_all:
    display_notifications(notifications, "all")

with tab_unread:
    unread = [n for n in notifications if not n.get("is_read", 0)]
    display_notifications(unread, "unread")

with tab_read:
    read = [n for n in notifications if n.get("is_read", 0)]
    display_notifications(read, "read")

# ---------------------------------------------------------------------------
# Mark All as Read
# ---------------------------------------------------------------------------
unread_count = sum(1 for n in notifications if not n.get("is_read", 0))
if unread_count > 0:
    if st.button("Mark All as Read", type="primary"):
        success = all(
            _mark_read(n["alert_id"])
            for n in notifications
            if not n.get("is_read", 0)
        )
        if success:
            st.success("All notifications marked as read.")
            st.rerun()
        else:
            st.warning("Some notifications could not be updated.")