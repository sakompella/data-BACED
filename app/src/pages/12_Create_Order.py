import logging
import streamlit as st
import requests
from datetime import datetime
from modules.nav import SideBarLinks
from modules.style import inject_custom_css, status_badge, API_BASE

logger = logging.getLogger(__name__)

st.set_page_config(layout="wide")
SideBarLinks()
inject_custom_css()

st.title("Create New Order")

waiter_id = st.session_state.get("user_id")
if waiter_id is None:
    st.error("No waiter session is active. Return to Home and choose a user.")
    st.stop()

# ---------------------------------------------------------------------------
# Session state: cart
# ---------------------------------------------------------------------------
if "order_cart" not in st.session_state:
    st.session_state.order_cart = []

# ---------------------------------------------------------------------------
# Fetch menu items
# ---------------------------------------------------------------------------
try:
    response = requests.get(f"{API_BASE}/menu_items")
    response.raise_for_status()
    menu_items = response.json()
except requests.RequestException:
    st.error("Failed to load menu items from the server.")
    st.stop()

if not menu_items:
    st.warning("No menu items found.")
    st.stop()

# ---------------------------------------------------------------------------
# Layout: two columns
# ---------------------------------------------------------------------------
col_left, col_right = st.columns([2, 1])

# ---- Left column: Order Form ---------------------------------------------
with col_left:
    table_number = st.selectbox("Table Number", options=list(range(1, 31)))

    filter_choice = st.selectbox("Filter", ["All", "Available", "Unavailable"])

    # Apply filter
    if filter_choice == "Available":
        visible_items = [m for m in menu_items if m.get("availability_status") == "available"]
    elif filter_choice == "Unavailable":
        visible_items = [m for m in menu_items if m.get("availability_status") != "available"]
    else:
        visible_items = menu_items

    # Render menu item cards
    for item in visible_items:
        is_available = item.get("availability_status") == "available"
        with st.container(border=True):
            card_left, card_right = st.columns([3, 1])
            with card_left:
                st.markdown(f"**{item['item_name']}**")
                st.caption(item.get('description', ''))
                st.markdown(f"${float(item['price']):.2f}")
                badge_color = "green" if is_available else "amber"
                badge_label = "Available" if is_available else "Unavailable"
                st.markdown(status_badge(badge_label, badge_color), unsafe_allow_html=True)
            with card_right:
                st.write("")
                if st.button(
                    "ADD +",
                    key=f"add_{item['menu_item_id']}",
                    disabled=not is_available,
                ):
                    # Check if item already in cart; if so, increment quantity
                    found = False
                    for cart_item in st.session_state.order_cart:
                        if cart_item["menu_item_id"] == item["menu_item_id"]:
                            cart_item["quantity"] += 1
                            found = True
                            break
                    if not found:
                        st.session_state.order_cart.append({
                            "menu_item_id": item["menu_item_id"],
                            "item_name": item["item_name"],
                            "quantity": 1,
                        })
                    st.rerun()

# ---- Right column: Order Summary ------------------------------------------
with col_right:
    st.subheader("Order Summary")
    st.markdown(f"**Table:** {table_number}")
    st.divider()

    cart = st.session_state.order_cart
    if not cart:
        st.caption("No items added yet.")
    else:
        for cart_item in cart:
            st.markdown(f"{cart_item['item_name']}  x  **{cart_item['quantity']}**")
        st.divider()
        total_count = sum(ci["quantity"] for ci in cart)
        st.markdown(f"**Total items:** {total_count}")

    notes = st.text_area("Notes for Kitchen", placeholder="Special instructions...")

    btn_cancel, btn_submit = st.columns(2)
    with btn_cancel:
        if st.button("Cancel", use_container_width=True):
            st.session_state.order_cart = []
            st.rerun()
    with btn_submit:
        if st.button("Submit Order", type="primary", use_container_width=True, disabled=len(cart) == 0):
            new_order_id = None
            try:
                # Create the kitchen order header
                order_resp = requests.post(
                    f"{API_BASE}/kitchen_orders",
                    json={
                        "table_id": table_number,
                        "status": "open",
                        "waiter_id": waiter_id,
                        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "notes": notes if notes else None,
                    },
                )
                order_resp.raise_for_status()
                new_order_id = order_resp.json().get("order_id")

                # Add each cart item, rollback the order if any insert fails
                for cart_item in cart:
                    for _ in range(cart_item["quantity"]):
                        item_resp = requests.post(
                            f"{API_BASE}/order_items",
                            json={
                                "order_id": new_order_id,
                                "menu_item_id": cart_item["menu_item_id"],
                                "special_notes": "",
                            },
                        )
                        item_resp.raise_for_status()

                st.session_state.order_cart = []
                st.success(f"Order #{new_order_id} submitted successfully!")
            except requests.RequestException as e:
                logger.error(f"Failed to submit order: {e}")
                # Compensating delete: remove the partial order (cascades to items)
                if new_order_id is not None:
                    try:
                        requests.delete(f"{API_BASE}/kitchen_orders/{new_order_id}")
                    except requests.RequestException:
                        logger.error(f"Failed to rollback order #{new_order_id}")
                st.error("Failed to submit order. Cart preserved, please try again.")
