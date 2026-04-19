import logging
logger = logging.getLogger(__name__)

import streamlit as st
import requests
import pandas as pd
from modules.nav import SideBarLinks
from modules.style import inject_custom_css, status_badge, API_BASE

st.set_page_config(layout="wide")
SideBarLinks()
inject_custom_css()

st.title("Users & Activity")

# ---------------------------------------------------------------------------
# Fetch users and roles
# ---------------------------------------------------------------------------
try:
    users_resp = requests.get(f"{API_BASE}/user/users")
    users_resp.raise_for_status()
    users = users_resp.json()
except requests.RequestException:
    st.error("Failed to load users from the server.")
    st.stop()

try:
    roles_resp = requests.get(f"{API_BASE}/user/roles")
    roles_resp.raise_for_status()
    roles = roles_resp.json()
except requests.RequestException:
    st.error("Failed to load roles from the server.")
    st.stop()

role_map = {r["role_id"]: r["role_name"] for r in roles}

# ---------------------------------------------------------------------------
# Section 1: User Accounts
# ---------------------------------------------------------------------------
st.subheader("User Accounts")

if not users:
    st.warning("No users found.")
else:
    header = (
        "<tr>"
        "<th style='text-align:left;padding:10px 12px;'>Name</th>"
        "<th style='text-align:left;padding:10px 12px;'>Role</th>"
        "<th style='text-align:center;padding:10px 12px;'>Status</th>"
        "</tr>"
    )

    rows_html = ""
    for u in users:
        full_name = u.get("name", f"{u.get('first_name', '')} {u.get('last_name', '')}".strip())
        role_name = role_map.get(u.get("role_id"), "Unknown")
        badge = status_badge("Active", "active")
        rows_html += (
            f"<tr>"
            f"<td style='padding:10px 12px;'>{full_name}</td>"
            f"<td style='padding:10px 12px;'>{role_name}</td>"
            f"<td style='padding:10px 12px;text-align:center;'>{badge}</td>"
            f"</tr>"
        )

    table_html = f"""
    <table style="width:100%;border-collapse:collapse;font-size:0.95em;">
        <thead style="background:#F0F0F0;font-weight:600;">
            {header}
        </thead>
        <tbody>
            {rows_html}
        </tbody>
    </table>
    """
    st.markdown(table_html, unsafe_allow_html=True)

st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Section 2: Recent Activity Log
# ---------------------------------------------------------------------------
st.subheader("Recent Activity Log")

try:
    log_resp = requests.get(f"{API_BASE}/user/activity_log")
    log_resp.raise_for_status()
    log_data = log_resp.json()
except requests.RequestException:
    st.error("Failed to load activity log from the server.")
    log_data = []

if not log_data:
    st.info("No recent activity.")
else:
    log_df = pd.DataFrame(log_data)
    log_df["action_time"] = pd.to_datetime(log_df["action_time"])
    log_df = log_df.sort_values("action_time", ascending=False).head(20)

    display_df = log_df[["action_time", "user_name", "action", "details"]].rename(
        columns={
            "action_time": "Timestamp",
            "user_name": "User",
            "action": "Action",
            "details": "Details",
        }
    )
    st.dataframe(display_df, use_container_width=True, hide_index=True)

st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Section 3: Modify User
# ---------------------------------------------------------------------------
with st.expander("Modify Users..."):
    st.subheader("Modify User")

    if not users:
        st.warning("No users available to modify.")
    else:
        user_options = {
            f"{u.get('name', u.get('first_name', ''))} (ID {u['user_id']})": u
            for u in users
        }
        selected_label = st.selectbox("Select User", options=list(user_options.keys()))
        selected_user = user_options[selected_label]

        # API may return 'name' (single field) or 'first_name'/'last_name'
        current_name = selected_user.get("name", f"{selected_user.get('first_name', '')} {selected_user.get('last_name', '')}".strip())
        name_parts = current_name.split(" ", 1)
        col1, col2 = st.columns(2)
        with col1:
            new_first = st.text_input("First Name", value=name_parts[0])
        with col2:
            new_last = st.text_input("Last Name", value=name_parts[1] if len(name_parts) > 1 else "")

        new_email = st.text_input("Email", value=selected_user.get("email", ""))

        role_options = [r["role_name"] for r in roles]
        current_role_name = role_map.get(selected_user.get("role_id"), role_options[0])
        current_idx = role_options.index(current_role_name) if current_role_name in role_options else 0
        new_role_name = st.selectbox("Role", options=role_options, index=current_idx)

        # Reverse lookup: role_name -> role_id
        role_name_to_id = {r["role_name"]: r["role_id"] for r in roles}
        new_role_id = role_name_to_id[new_role_name]

        btn_col1, btn_col2, _ = st.columns([1, 1, 3])
        with btn_col1:
            if st.button("Update User", type="primary"):
                payload = {
                    "first_name": new_first,
                    "last_name": new_last,
                    "email": new_email,
                    "role_id": new_role_id,
                }
                try:
                    resp = requests.put(
                        f"{API_BASE}/user/users/{selected_user['user_id']}",
                        json=payload,
                    )
                    resp.raise_for_status()
                    st.success("User updated successfully.")
                    st.rerun()
                except requests.RequestException as e:
                    st.error(f"Failed to update user: {e}")

        with btn_col2:
            if st.button("Delete User", type="secondary"):
                st.session_state["confirm_delete"] = True

            if st.session_state.get("confirm_delete"):
                st.warning(
                    f"Are you sure you want to delete "
                    f"**{selected_user.get('name', current_name)}**?"
                )
                c1, c2, _ = st.columns([1, 1, 3])
                with c1:
                    if st.button("Yes, delete"):
                        try:
                            resp = requests.delete(
                                f"{API_BASE}/user/users/{selected_user['user_id']}"
                            )
                            resp.raise_for_status()
                            st.success("User deleted.")
                            st.session_state.pop("confirm_delete", None)
                            st.rerun()
                        except requests.RequestException as e:
                            st.error(f"Failed to delete user: {e}")
                with c2:
                    if st.button("Cancel"):
                        st.session_state.pop("confirm_delete", None)
                        st.rerun()
