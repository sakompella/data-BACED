import logging
logger = logging.getLogger(__name__)

import streamlit as st
import requests
from modules.nav import SideBarLinks
from modules.style import inject_custom_css, status_text, API_BASE

st.set_page_config(layout="wide")
SideBarLinks()
inject_custom_css()

st.title("Order Management")

# Display and clear any flash message set by a previous action
flash = st.session_state.pop("flash", None)
if flash:
    st.success(flash)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

STATUS_LABEL = {
    "open": "Queued",
    "in_progress": "Cooking",
    "completed": "Ready",
    "cancelled": "Cancelled",
}

STATUS_COLOR = {
    "open": "gray",
    "in_progress": "amber",
    "completed": "green",
    "cancelled": "red",
}


def fetch_json(url: str):
    """GET helper that returns parsed JSON or None on failure."""
    try:
        resp = requests.get(url)
        if resp.status_code == 200:
            return resp.json()
    except requests.RequestException as e:
        logger.error("Request failed: %s", e)
    return None


def update_order_status(order_id: int, new_status: str):
    """PUT new status for a kitchen order; returns True on success."""
    try:
        resp = requests.put(
            f"{API_BASE}/kitchen_orders/{order_id}",
            json={"status": new_status},
        )
        return resp.status_code == 200
    except requests.RequestException as e:
        logger.error("Failed to update order %s: %s", order_id, e)
        return False


# ---------------------------------------------------------------------------
# Section 1 - Kitchen Order Queue
# ---------------------------------------------------------------------------

st.subheader("Kitchen Order Queue")

orders = fetch_json(f"{API_BASE}/kitchen_orders")

if orders is None:
    st.error("Failed to load kitchen orders from the server.")
elif not orders:
    st.info("No orders in the queue right now.")
else:
    # Build a prep-summary across open/in_progress orders
    prep_counts: dict[str, int] = {}

    for order in orders:
        oid = order["order_id"]
        items = fetch_json(f"{API_BASE}/order_items/{oid}") or []
        order["_items"] = items

        if order["status"] in ("open", "in_progress"):
            for item in items:
                name = item.get("item_name", "Unknown")
                prep_counts[name] = prep_counts.get(name, 0) + 1

    # Prep Summary Banner
    if prep_counts:
        summary_parts = [f"**{name}** x{count}" for name, count in sorted(prep_counts.items())]
        st.info("Prep Summary:  " + "  |  ".join(summary_parts))

    # Render order table
    for order in orders:
        oid = order["order_id"]
        table_id = order.get("table_id", "—")
        status_key = order.get("status", "open")
        label = STATUS_LABEL.get(status_key, status_key)
        color = STATUS_COLOR.get(status_key, "gray")
        items = order["_items"]
        item_names = ", ".join(it.get("item_name", "?") for it in items) if items else "—"

        cols = st.columns([1, 1, 3, 2, 2])
        cols[0].markdown(f"**#{oid}**")
        cols[1].markdown(f"Table {table_id}")
        cols[2].markdown(item_names)
        cols[3].write(status_text(label, color))

        with cols[4]:
            if status_key == "open":
                if st.button("Claim", key=f"claim_{oid}"):
                    if update_order_status(oid, "in_progress"):
                        st.session_state["flash"] = f"Order #{oid} claimed — prep summary updated"
                        st.rerun()
                    else:
                        st.error("Failed to claim order.")
            elif status_key == "in_progress":
                if st.button("Mark Ready", key=f"ready_{oid}"):
                    if update_order_status(oid, "completed"):
                        st.session_state["flash"] = f"Order #{oid} marked ready — prep summary updated"
                        st.rerun()
                    else:
                        st.error("Failed to mark order ready.")

