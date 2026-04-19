import logging
logger = logging.getLogger(__name__)

import streamlit as st
import requests
import pandas as pd
from datetime import datetime
from email.utils import parsedate_to_datetime
from modules.nav import SideBarLinks
from modules.style import inject_custom_css, status_badge, API_BASE

st.set_page_config(layout="wide")
SideBarLinks()
inject_custom_css()

st.title("My Orders")

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


tab_orders, tab_menu = st.tabs(["Current Orders", "Menu Items"])

# ── Current Orders tab ──────────────────────────────────────────────────────

with tab_orders:
    try:
        resp = requests.get(f"{API_BASE}/ord/kitchen_orders")
        resp.raise_for_status()
        orders = resp.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to load orders: {e}")
        orders = []

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
                # Header: table number, status badge, time ago
                cols = st.columns([3, 2, 3])
                with cols[0]:
                    st.markdown(f"**Table {table_id}**")
                with cols[1]:
                    st.markdown(status_badge(label, color_key), unsafe_allow_html=True)
                with cols[2]:
                    st.markdown(
                        f"<span style='color:#888;font-size:0.9em'>{time_ago(created_at)}</span>",
                        unsafe_allow_html=True,
                    )

                st.divider()

                # Fetch items for this order
                try:
                    items_resp = requests.get(f"{API_BASE}/ord/order_items/{order_id}")
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
                            # Per-item status mirrors the order status (DB has no per-item status)
                            st.markdown(
                                status_badge(label, color_key),
                                unsafe_allow_html=True,
                            )
                else:
                    st.caption("No items in this order.")

                # Footer placeholder
                num_items = len(items)
                st.caption(f"Guests: 1 \u2022 Course 1 of 1 \u2022 {num_items} item{'s' if num_items != 1 else ''}")

# ── Menu Items tab ──────────────────────────────────────────────────────────

with tab_menu:
    try:
        resp = requests.get(f"{API_BASE}/menu/menu_items")
        resp.raise_for_status()
        menu_items = resp.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to load menu items: {e}")
        menu_items = []

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
