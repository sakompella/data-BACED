import logging
import streamlit as st
import requests
import pandas as pd
from datetime import datetime
from email.utils import parsedate_to_datetime
from modules.nav import SideBarLinks
from modules.style import inject_custom_css, status_badge, API_BASE

logger = logging.getLogger(__name__)

st.set_page_config(layout="wide")
SideBarLinks()
inject_custom_css()

st.title("My Orders")

waiter_id = st.session_state.get("user_id")
if waiter_id is None:
    st.error("No waiter session is active. Return to Home and choose a user.")
    st.stop()

STATUS_MAP = {
    "open": ("Queued", "gray"),
    "in_progress": ("Cooking", "amber"),
    "completed": ("Ready", "green"),
}


def time_ago(created_at) -> str:
    """Return a human-readable string like '8 minutes ago'."""
    if created_at is None:
        return ""
    if isinstance(created_at, str):
        try:
            created_at = parsedate_to_datetime(created_at)
        except (ValueError, TypeError):
            try:
                created_at = datetime.fromisoformat(created_at)
            except ValueError:
                return ""
    # Ensure both are naive for subtraction (API returns timezone-aware dates)
    if created_at.tzinfo is not None:
        created_at = created_at.replace(tzinfo=None)
    delta = datetime.now() - created_at
    total_seconds = int(delta.total_seconds())
    if total_seconds < 60:
        return f"{total_seconds} seconds ago"
    minutes = total_seconds // 60
    if minutes < 60:
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    hours = minutes // 60
    return f"{hours} hour{'s' if hours != 1 else ''} ago"


try:
    menu_resp = requests.get(f"{API_BASE}/menu_items")
    menu_resp.raise_for_status()
    menu_items = menu_resp.json()
except requests.exceptions.RequestException as e:
    st.error(f"Failed to load menu items: {e}")
    menu_items = []

tab_orders, tab_menu, tab_item_tools = st.tabs(["Current Orders", "Menu Items", "Order Item Tools"])

# -- Current Orders tab ------------------------------------------------------

with tab_orders:
    try:
        resp = requests.get(f"{API_BASE}/kitchen_orders")
        resp.raise_for_status()
        orders = resp.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to load orders: {e}")
        orders = []

    orders = [order for order in orders if order.get("waiter_id") == waiter_id]

    if not orders:
        st.info("No current orders.")
    else:
        for order in orders:
            order_id = order.get("order_id")
            table_id = order.get("table_id", "?")
            status_raw = order.get("status", "open")
            created_at = order.get("created_at")

            label, color_key = STATUS_MAP.get(status_raw, (status_raw, "gray"))

            with st.container(border=True):
                # Header: table number, status, time ago
                cols = st.columns([3, 2, 3])
                with cols[0]:
                    st.markdown(f"**Table {table_id}**")
                with cols[1]:
                    st.markdown(status_badge(label, color_key), unsafe_allow_html=True)
                with cols[2]:
                    st.caption(time_ago(created_at))

                st.divider()

                # Fetch items for this order
                try:
                    items_resp = requests.get(f"{API_BASE}/order_items/{order_id}")
                    items_resp.raise_for_status()
                    items = items_resp.json()
                except requests.exceptions.RequestException:
                    items = []

                if items:
                    # Group duplicate items to show quantity
                    item_counts: dict[str, int] = {}
                    for item in items:
                        name = item.get("item_name", "Unknown")
                        item_counts[name] = item_counts.get(name, 0) + 1

                    for name, qty in item_counts.items():
                        item_cols = st.columns([1, 5, 2])
                        with item_cols[0]:
                            st.markdown(f"**{qty}x**")
                        with item_cols[1]:
                            st.write(name)
                        with item_cols[2]:
                            st.markdown(status_badge(label, color_key), unsafe_allow_html=True)
                else:
                    st.caption("No items in this order.")

                num_items = len(items)
                st.caption(f"{num_items} item{'s' if num_items != 1 else ''}")

# -- Menu Items tab ----------------------------------------------------------

with tab_menu:
    if not menu_items:
        st.info("No menu items available.")
    else:
        df = pd.DataFrame(menu_items)
        display_cols = {
            "item_name": "Item Name",
            "price": "Price",
            "availability_status": "Availability",
        }
        # Keep only columns that exist in the response
        available = [c for c in display_cols if c in df.columns]
        df = df[available].rename(columns=display_cols)
        st.dataframe(df, use_container_width=True, hide_index=True)

# -- Order Item Tools tab ----------------------------------------------------

with tab_item_tools:
    st.subheader("Order Item Route Tools")
    st.caption("Use these controls to update or remove a specific order item by ID.")

    order_item_id = st.number_input(
        "Order Item ID",
        min_value=1,
        step=1,
        value=1,
        key="order_item_tool_id",
    )

    menu_options = {
        f"{item['item_name']} (ID {item['menu_item_id']})": item["menu_item_id"]
        for item in menu_items
    }

    if menu_options:
        selected_menu_label = st.selectbox(
            "Replacement Menu Item",
            options=list(menu_options.keys()),
            key="order_item_tool_menu",
        )
        selected_menu_item_id = int(menu_options[selected_menu_label])
    else:
        selected_menu_item_id = None
        st.info("Menu options unavailable; update can still change special notes.")

    special_notes = st.text_input(
        "Special Notes",
        key="order_item_tool_notes",
        placeholder="Optional notes for kitchen",
    )

    col_update, col_delete = st.columns(2)

    with col_update:
        if st.button("Update Order Item", type="primary", use_container_width=True):
            payload = {"special_notes": special_notes}
            if selected_menu_item_id is not None:
                payload["menu_item_id"] = selected_menu_item_id
            if waiter_id:
                payload["actor_id"] = waiter_id
            try:
                response = requests.put(
                    f"{API_BASE}/order_items/{int(order_item_id)}",
                    json=payload,
                )
                if response.status_code == 404:
                    st.warning("Order item not found.")
                else:
                    response.raise_for_status()
                    st.success(f"Order item #{int(order_item_id)} updated.")
            except requests.RequestException as exc:
                st.error(f"Failed to update order item: {exc}")

    with col_delete:
        if st.button("Delete Order Item", use_container_width=True):
            st.session_state["confirm_delete_order_item_id"] = int(order_item_id)

        if st.session_state.get("confirm_delete_order_item_id") == int(order_item_id):
            st.warning(f"Delete order item #{int(order_item_id)}?")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("Yes, delete order item", key="confirm_delete_order_item", use_container_width=True):
                    params = {"actor_id": waiter_id} if waiter_id else None
                    try:
                        response = requests.delete(
                            f"{API_BASE}/order_items/{int(order_item_id)}",
                            params=params,
                        )
                        if response.status_code == 404:
                            st.warning("Order item not found.")
                        else:
                            response.raise_for_status()
                            st.success(f"Order item #{int(order_item_id)} deleted.")
                        st.session_state.pop("confirm_delete_order_item_id", None)
                    except requests.RequestException as exc:
                        st.error(f"Failed to delete order item: {exc}")
            with c2:
                if st.button("Cancel", key="cancel_delete_order_item", use_container_width=True):
                    st.session_state.pop("confirm_delete_order_item_id", None)
