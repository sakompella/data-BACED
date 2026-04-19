import logging
logger = logging.getLogger(__name__)

import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta
from modules.nav import SideBarLinks
from modules.style import inject_custom_css, status_badge, API_BASE

st.set_page_config(layout="wide")
SideBarLinks()
inject_custom_css()

st.title("Inventory & Stock")

# ---------------------------------------------------------------------------
# Fetch ingredient data
# ---------------------------------------------------------------------------
try:
    response = requests.get(f"{API_BASE}/inv/ingredients")
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

    # Build HTML table
    header = (
        "<tr>"
        "<th style='text-align:left;padding:10px 12px;'>Ingredient</th>"
        "<th style='text-align:right;padding:10px 12px;'>Qty</th>"
        "<th style='text-align:left;padding:10px 12px;'>Unit</th>"
        "<th style='text-align:left;padding:10px 12px;'>Latest Exp. Date</th>"
        "<th style='text-align:center;padding:10px 12px;'>Status</th>"
        "<th style='text-align:left;padding:10px 12px;'>Details</th>"
        "</tr>"
    )

    rows_html = ""
    for _, row in filtered.iterrows():
        color_key = row["status"].lower()
        badge = status_badge(row["status"], color_key)
        exp_str = row["expiration_date"].strftime("%Y-%m-%d")
        detail = f"Reorder at {row['reorder_count']} · Supplier: {row['supplier_name']}"
        rows_html += (
            f"<tr>"
            f"<td style='padding:10px 12px;'>{row['ingredient_name']}</td>"
            f"<td style='padding:10px 12px;text-align:right;'>{row['quantity']}</td>"
            f"<td style='padding:10px 12px;'>{row['unit']}</td>"
            f"<td style='padding:10px 12px;'>{exp_str}</td>"
            f"<td style='padding:10px 12px;text-align:center;'>{badge}</td>"
            f"<td style='padding:10px 12px;font-size:0.85em;color:#666;'>{detail}</td>"
            f"</tr>"
        )

    table_html = f"""
    <table style="width:100%;border-collapse:collapse;font-size:0.95em;">
        <thead style="background:#F0F0F0;font-weight:600;">
            {header}
        </thead>
        <tbody>
            {rows_html if rows_html else "<tr><td colspan='6' style='padding:20px;text-align:center;color:#999;'>No matching ingredients.</td></tr>"}
        </tbody>
    </table>
    """
    st.markdown(table_html, unsafe_allow_html=True)

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
    btn_col1, btn_col2, _ = st.columns([1, 1, 3])
    with btn_col1:
        st.button("Request Extra Stock", type="primary")
    with btn_col2:
        st.button("Confirm Delivery")

# ---- Expiring Soon --------------------------------------------------------
with tab_expiring:
    cutoff = now + timedelta(days=14)
    expiring_df = df[df["expiration_date"] <= cutoff].sort_values(
        "expiration_date", ascending=True
    )

    if expiring_df.empty:
        st.info("No ingredients expiring within the next 14 days.")
    else:
        header_exp = (
            "<tr>"
            "<th style='text-align:left;padding:10px 12px;'>Ingredient</th>"
            "<th style='text-align:right;padding:10px 12px;'>Qty</th>"
            "<th style='text-align:left;padding:10px 12px;'>Unit</th>"
            "<th style='text-align:left;padding:10px 12px;'>Expiration Date</th>"
            "<th style='text-align:center;padding:10px 12px;'>Status</th>"
            "<th style='text-align:left;padding:10px 12px;'>Supplier</th>"
            "</tr>"
        )

        rows_exp = ""
        for _, row in expiring_df.iterrows():
            color_key = row["status"].lower()
            badge = status_badge(row["status"], color_key)
            exp_str = row["expiration_date"].strftime("%Y-%m-%d")
            rows_exp += (
                f"<tr>"
                f"<td style='padding:10px 12px;'>{row['ingredient_name']}</td>"
                f"<td style='padding:10px 12px;text-align:right;'>{row['quantity']}</td>"
                f"<td style='padding:10px 12px;'>{row['unit']}</td>"
                f"<td style='padding:10px 12px;'>{exp_str}</td>"
                f"<td style='padding:10px 12px;text-align:center;'>{badge}</td>"
                f"<td style='padding:10px 12px;'>{row['supplier_name']}</td>"
                f"</tr>"
            )

        table_exp_html = f"""
        <table style="width:100%;border-collapse:collapse;font-size:0.95em;">
            <thead style="background:#F0F0F0;font-weight:600;">
                {header_exp}
            </thead>
            <tbody>
                {rows_exp}
            </tbody>
        </table>
        """
        st.markdown(table_exp_html, unsafe_allow_html=True)
