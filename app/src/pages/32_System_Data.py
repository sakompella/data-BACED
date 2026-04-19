import logging
logger = logging.getLogger(__name__)

import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from modules.nav import SideBarLinks
from modules.style import inject_custom_css, status_badge, API_BASE

st.set_page_config(layout="wide")
SideBarLinks()
inject_custom_css()

st.title("System & Data")

# ---------------------------------------------------------------------------
# Helper: safe GET that returns (data, ok)
# ---------------------------------------------------------------------------
def safe_get(url):
    try:
        r = requests.get(url, timeout=5)
        r.raise_for_status()
        return r.json(), True
    except requests.RequestException:
        return [], False

# ---------------------------------------------------------------------------
# Two-column main layout
# ---------------------------------------------------------------------------
left_col, right_col = st.columns([2, 1])

# ========================== LEFT COLUMN ====================================
with left_col:

    # ---- Section 1: System Health -----------------------------------------
    st.subheader("System Health")

    # API Status
    try:
        r = requests.get(f"{API_BASE}/", timeout=5)
        api_online = r.status_code == 200
    except requests.RequestException:
        api_online = False

    users_data, _ = safe_get(f"{API_BASE}/user/users")
    orders_data, _ = safe_get(f"{API_BASE}/ord/kitchen_orders")
    menu_data, _ = safe_get(f"{API_BASE}/menu/menu_items")
    ingredients_data, _ = safe_get(f"{API_BASE}/inv/ingredients")

    health_rows = [
        ("API Status", "Online" if api_online else "Down",
         status_badge("Online", "green") if api_online else status_badge("Down", "red")),
        ("Total Users", str(len(users_data)),
         status_badge("OK", "green")),
        ("Total Orders", str(len(orders_data)),
         status_badge("OK", "green")),
        ("Menu Items", str(len(menu_data)),
         status_badge("OK", "green")),
        ("Ingredients", str(len(ingredients_data)),
         status_badge("OK", "green")),
    ]

    header = (
        "<tr>"
        "<th style='text-align:left;padding:10px 12px;'>Metric</th>"
        "<th style='text-align:right;padding:10px 12px;'>Value</th>"
        "<th style='text-align:center;padding:10px 12px;'>Status</th>"
        "</tr>"
    )
    rows_html = ""
    for metric, value, badge in health_rows:
        rows_html += (
            f"<tr>"
            f"<td style='padding:10px 12px;'>{metric}</td>"
            f"<td style='padding:10px 12px;text-align:right;'>{value}</td>"
            f"<td style='padding:10px 12px;text-align:center;'>{badge}</td>"
            f"</tr>"
        )

    st.markdown(f"""
    <table style="width:100%;border-collapse:collapse;font-size:0.95em;">
        <thead style="background:#F0F0F0;font-weight:600;">
            {header}
        </thead>
        <tbody>{rows_html}</tbody>
    </table>
    """, unsafe_allow_html=True)

    st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

    # ---- Section 2: Data Discrepancies ------------------------------------
    st.subheader("Potential Data Discrepancies")

    expected_data, exp_ok = safe_get(f"{API_BASE}/inv/expected_usage")

    discrepancies_df = pd.DataFrame()

    if exp_ok and expected_data and ingredients_data:
        exp_df = pd.DataFrame(expected_data)
        ing_df = pd.DataFrame(ingredients_data)

        # expected_usage already joins and returns ingredient_name,
        # expected_quantity, current_quantity
        if "ingredient_name" in exp_df.columns and "expected_quantity" in exp_df.columns:
            # Use the current_quantity from the expected_usage join if available,
            # otherwise fall back to joining with ingredients
            if "current_quantity" in exp_df.columns:
                exp_df["actual_qty"] = pd.to_numeric(exp_df["current_quantity"], errors="coerce")
            else:
                ing_qty = ing_df[["ingredient_name", "quantity"]].drop_duplicates("ingredient_name")
                exp_df = exp_df.merge(ing_qty, on="ingredient_name", how="left")
                exp_df["actual_qty"] = pd.to_numeric(exp_df["quantity"], errors="coerce")

            exp_df["expected_qty"] = pd.to_numeric(exp_df["expected_quantity"], errors="coerce")
            exp_df["variance"] = exp_df["actual_qty"] - exp_df["expected_qty"]

            # Only items where actual < expected (negative variance)
            neg = exp_df[exp_df["variance"] < 0].copy()

            if not neg.empty:
                discrepancies_df = neg[["ingredient_name", "expected_qty", "actual_qty", "variance"]].copy()
                discrepancies_df.columns = ["Item", "Expected", "Actual", "Variance"]
                discrepancies_df["Expected"] = discrepancies_df["Expected"].round(1)
                discrepancies_df["Actual"] = discrepancies_df["Actual"].round(1)
                discrepancies_df["Variance"] = discrepancies_df["Variance"].round(1)
                discrepancies_df = discrepancies_df.drop_duplicates(subset=["Item"]).reset_index(drop=True)

    if not discrepancies_df.empty:
        disc_header = (
            "<tr>"
            "<th style='text-align:left;padding:10px 12px;'>Item</th>"
            "<th style='text-align:right;padding:10px 12px;'>Expected</th>"
            "<th style='text-align:right;padding:10px 12px;'>Actual</th>"
            "<th style='text-align:right;padding:10px 12px;'>Variance</th>"
            "<th style='text-align:center;padding:10px 12px;'>Action</th>"
            "</tr>"
        )
        disc_rows = ""
        for _, row in discrepancies_df.iterrows():
            variance_badge = status_badge(f"{row['Variance']:.1f}", "red")
            disc_rows += (
                f"<tr>"
                f"<td style='padding:10px 12px;'>{row['Item']}</td>"
                f"<td style='padding:10px 12px;text-align:right;'>{row['Expected']}</td>"
                f"<td style='padding:10px 12px;text-align:right;'>{row['Actual']}</td>"
                f"<td style='padding:10px 12px;text-align:right;'>{variance_badge}</td>"
                f"<td style='padding:10px 12px;text-align:center;'>"
                f"<span style='color:#2E75ED;cursor:pointer;font-weight:600;'>Investigate</span>"
                f"</td>"
                f"</tr>"
            )

        st.markdown(f"""
        <table style="width:100%;border-collapse:collapse;font-size:0.95em;">
            <thead style="background:#F0F0F0;font-weight:600;">
                {disc_header}
            </thead>
            <tbody>{disc_rows}</tbody>
        </table>
        """, unsafe_allow_html=True)
    else:
        st.info("No data discrepancies detected.")

# ========================== RIGHT COLUMN ===================================
with right_col:

    # ---- Order Volume Chart -----------------------------------------------
    st.subheader("Order Volume")

    if orders_data:
        orders_df = pd.DataFrame(orders_data)
        if "created_at" in orders_df.columns:
            orders_df["date"] = pd.to_datetime(orders_df["created_at"]).dt.date
            daily_counts = (
                orders_df.groupby("date")
                .size()
                .reset_index(name="order_count")
            )
            daily_counts["date"] = pd.to_datetime(daily_counts["date"])

            fig = px.line(
                daily_counts,
                x="date",
                y="order_count",
                labels={"date": "Date", "order_count": "Orders"},
            )
            fig.update_layout(
                margin=dict(l=0, r=0, t=10, b=0),
                height=300,
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Order data missing 'created_at' field.")
    else:
        st.warning("No order data available.")

# ---------------------------------------------------------------------------
# Bottom buttons
# ---------------------------------------------------------------------------
st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
btn_export, btn_refresh, _ = st.columns([1, 1, 3])

with btn_export:
    if not discrepancies_df.empty:
        csv = discrepancies_df.to_csv(index=False)
        st.download_button(
            "Export Report",
            data=csv,
            file_name="data_discrepancies.csv",
            mime="text/csv",
        )
    else:
        st.download_button(
            "Export Report",
            data="No discrepancies found.",
            file_name="data_discrepancies.csv",
            mime="text/csv",
        )

with btn_refresh:
    if st.button("Refresh", type="primary"):
        st.rerun()
