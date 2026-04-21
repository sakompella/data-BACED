import logging
import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta
from modules.nav import SideBarLinks
from modules.style import inject_custom_css, status_css, API_BASE

logger = logging.getLogger(__name__)

st.set_page_config(layout="wide")
SideBarLinks()
inject_custom_css()

st.title("Inventory & Stock")

# ---------------------------------------------------------------------------
# Fetch ingredient data
# ---------------------------------------------------------------------------
try:
    response = requests.get(f"{API_BASE}/ingredients")
    response.raise_for_status()
    data = response.json()
except requests.RequestException:
    st.error("Failed to load ingredients from the server.")
    st.stop()

if not data:
    st.warning("No ingredients found.")
    st.stop()

df = pd.DataFrame(data)
df["expiration_date"] = pd.to_datetime(df["expiration_date"])
now = datetime.now()

# ---------------------------------------------------------------------------
# Derive status column
# ---------------------------------------------------------------------------
def compute_status(row):
    if row["quantity"] <= row["reorder_count"]:
        return "Low"
    if row["expiration_date"] <= now + timedelta(days=7):
        return "Expiring"
    return "OK"

df["status"] = df.apply(compute_status, axis=1)

# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------
tab_stock, tab_expiring = st.tabs(["Current Stock", "Expiring Soon"])

# ---- Current Stock --------------------------------------------------------
with tab_stock:
    col_search, col_filter = st.columns([3, 1])
    with col_search:
        search_query = st.text_input(
            "Search", placeholder="Search ingredients...", label_visibility="collapsed"
        )
    with col_filter:
        status_filter = st.selectbox(
            "Filter", ["All", "OK", "Low", "Expiring"], label_visibility="collapsed"
        )

    filtered = df.copy()
    if search_query:
        filtered = filtered[
            filtered["ingredient_name"].str.contains(search_query, case=False, na=False)
        ]
    if status_filter != "All":
        filtered = filtered[filtered["status"] == status_filter]

    display_df = filtered.copy()
    display_df["Status"] = display_df["status"]
    display_df["Expiration Date"] = display_df["expiration_date"].dt.strftime("%Y-%m-%d")
    display_df["Details"] = display_df.apply(
        lambda r: f"Reorder at {r['reorder_count']} | Supplier: {r['supplier_name']}",
        axis=1,
    )

    view = display_df[["ingredient_name", "quantity", "unit", "Expiration Date", "Status", "Details"]]
    styled = view.style.map(status_css, subset=["Status"])

    st.dataframe(
        styled,
        column_config={
            "ingredient_name": st.column_config.TextColumn("Ingredient"),
            "quantity": st.column_config.NumberColumn("Qty"),
            "unit": st.column_config.TextColumn("Unit"),
            "Expiration Date": st.column_config.TextColumn("Latest Exp. Date"),
            "Status": st.column_config.TextColumn("Status"),
            "Details": st.column_config.TextColumn("Details"),
        },
        hide_index=True,
        use_container_width=True,
    )

# ---- Expiring Soon --------------------------------------------------------
with tab_expiring:
    cutoff = now + timedelta(days=14)
    expiring_df = df[df["expiration_date"] <= cutoff].sort_values(
        "expiration_date", ascending=True
    )

    if expiring_df.empty:
        st.info("No ingredients expiring within the next 14 days.")
    else:
        exp_display = expiring_df.copy()
        exp_display["Status"] = exp_display["status"]
        exp_display["Expiration Date"] = exp_display["expiration_date"].dt.strftime("%Y-%m-%d")

        exp_view = exp_display[["ingredient_name", "quantity", "unit", "Expiration Date", "Status", "supplier_name"]]
        exp_styled = exp_view.style.map(status_css, subset=["Status"])

        st.dataframe(
            exp_styled,
            column_config={
                "ingredient_name": st.column_config.TextColumn("Ingredient"),
                "quantity": st.column_config.NumberColumn("Qty"),
                "unit": st.column_config.TextColumn("Unit"),
                "Expiration Date": st.column_config.TextColumn("Expiration Date"),
                "Status": st.column_config.TextColumn("Status"),
                "supplier_name": st.column_config.TextColumn("Supplier"),
            },
            hide_index=True,
            use_container_width=True,
        )

st.divider()
# -----------------------------------------------------------------------------
#Stock Requests
# -----------------------------------------------------------------------------

st.subheader("Request Extra Stock")

ingredient_map = {row['ingredient_name']: row for row in data}

with st.form('stock_request_form', clear_on_submit=True):
    col_ing, col_qty, col_btn = st.columns([3, 1, 1])
    with col_ing:
        selected_name = st.selectbox("Ingredient", options=sorted(ingredient_map.keys()), label_visibility='collapsed')
    selected_ing = ingredient_map.get(selected_name, {})
    unit = selected_ing.get('unit', "")
    with col_qty:
        request_qty = st.number_input(f"Qty ({unit})", min_value=1, step=1, label_visibility='collapsed')
    with col_btn:
        req_submitted = st.form_submit_button("Submit", type="primary",use_container_width=True)

if req_submitted:
    ing_id = selected_ing.get('ingredient_id')
    try:
        resp = requests.post(f"{API_BASE}/notifications", json={'user_id': st.session_state.get('user_id'),
                                                                     'message': f"Stock request: {request_qty} {unit} of {selected_name}",
                                                                     })
        if resp.status_code in (200, 201):
            st.success(f"Stock request for **{selected_name}** ({request_qty} {unit}) submitted.")
        else:
            st.error("Failed to submit request.")
    except requests.RequestException:
        st.error("Failed to submit request.")