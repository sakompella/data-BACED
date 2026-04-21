import logging
import streamlit as st
import requests
from pathlib import Path
from modules.nav import SideBarLinks
from modules.style import API_BASE

logging.basicConfig(format='%(filename)s:%(lineno)s:%(levelname)s -- %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

st.set_page_config(layout='wide')


def preflight_pages_directory():
    pages_dir = Path(__file__).resolve().parent / "pages"
    if pages_dir.is_dir():
        return
    diagnostic = (
        f"Startup preflight failed: expected Streamlit pages directory at '{pages_dir}', "
        "but it does not exist."
    )
    logger.error(diagnostic)
    st.error(diagnostic)
    st.info("Restore or mount `app/src/pages` before starting the app.")
    st.stop()


preflight_pages_directory()

st.session_state['authenticated'] = False

SideBarLinks(show_home=True)

logger.info("Loading the Home page of the app")
st.title('Welcome to RestaurantBACED')
st.write('#### Your in-house restaurant order and inventory management system')
st.write('#### Choose a role, then select a user')

ROLE_CONFIG = {
    "chef": {
        "label": "Chef",
        "page": "pages/00_Chef_Home.py",
    },
    "waiter": {
        "label": "Waiter",
        "page": "pages/10_Waiter_Home.py",
    },
    "analyst": {
        "label": "Analyst",
        "page": "pages/20_Analyst_Home.py",
    },
    "administrator": {
        "label": "Administrator",
        "page": "pages/30_Admin_Home.py",
    },
}


def normalize_role_name(role_name: str) -> str | None:
    """Map backend role names to the app's navigation role keys."""
    key = (role_name or "").strip().lower()
    if key in {"chef", "head chef"}:
        return "chef"
    if key in {"waiter", "server"}:
        return "waiter"
    if key in {"analyst", "operations analyst"}:
        return "analyst"
    if key in {"administrator", "admin", "system administrator", "system admin"}:
        return "administrator"
    return None


def display_name(user: dict) -> str:
    name = (user.get("name") or "").strip()
    if name:
        return name
    first = (user.get("first_name") or "").strip()
    last = (user.get("last_name") or "").strip()
    full = f"{first} {last}".strip()
    return full or f"User {user.get('user_id', '?')}"


def first_name(user: dict) -> str:
    raw_first = (user.get("first_name") or "").strip()
    if raw_first:
        return raw_first
    return display_name(user).split(" ", 1)[0]


def build_role_user_map(users: list[dict], roles: list[dict]) -> dict[str, list[dict]]:
    role_ids_by_app_role = {name: set() for name in ROLE_CONFIG}
    for role in roles:
        app_role = normalize_role_name(role.get("role_name", ""))
        if app_role:
            role_ids_by_app_role[app_role].add(role.get("role_id"))

    users_by_role = {name: [] for name in ROLE_CONFIG}
    for user in users:
        user_role_id = user.get("role_id")
        for app_role, role_ids in role_ids_by_app_role.items():
            if user_role_id in role_ids:
                users_by_role[app_role].append(user)
                break
    return users_by_role


try:
    roles_resp = requests.get(f"{API_BASE}/roles", timeout=5)
    roles_resp.raise_for_status()
    roles = roles_resp.json()

    users_resp = requests.get(f"{API_BASE}/users", timeout=5)
    users_resp.raise_for_status()
    users = users_resp.json()
except requests.RequestException as exc:
    st.error(f"Unable to load users/roles from API: {exc}")
    st.stop()

users_by_role = build_role_user_map(users, roles)

for role_key, role_cfg in ROLE_CONFIG.items():
    role_users = users_by_role.get(role_key, [])
    st.markdown(f"##### {role_cfg['label']}")
    if not role_users:
        st.caption("No users available for this role.")
        continue

    options = {
        f"{display_name(user)} (ID {user.get('user_id')})": user
        for user in role_users
    }
    selected_label = st.selectbox(
        f"Select {role_cfg['label']} user",
        options=list(options.keys()),
        key=f"home_select_{role_key}",
    )

    if st.button(
        f"Log In as {role_cfg['label']}",
        key=f"home_login_{role_key}",
        type="primary",
        use_container_width=True,
    ):
        selected_user = options[selected_label]
        st.session_state["authenticated"] = True
        st.session_state["role"] = role_key
        st.session_state["first_name"] = first_name(selected_user)
        st.session_state["user_id"] = selected_user.get("user_id")
        logger.info(
            "Logging in as %s user_id=%s",
            role_key,
            selected_user.get("user_id"),
        )
        st.switch_page(role_cfg["page"])
