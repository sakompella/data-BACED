import logging
logger = logging.getLogger(__name__)

import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import time
from modules.nav import SideBarLinks
from modules.style import inject_custom_css, status_text, API_BASE

st.set_page_config(layout="wide")
SideBarLinks()
inject_custom_css()

st.title("System & Data Management")

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

    # Measure API response time
    start = time.time()
    try:
        r = requests.get(f"{API_BASE}/", timeout=5)
        api_online = r.status_code == 200
        response_ms = int((time.time() - start) * 1000)
    except requests.RequestException:
        api_online = False
        response_ms = 0

    users_data, _ = safe_get(f"{API_BASE}/users")
    orders_data, _ = safe_get(f"{API_BASE}/kitchen_orders")
    menu_data, _ = safe_get(f"{API_BASE}/menu_items")
    ingredients_data, _ = safe_get(f"{API_BASE}/ingredients")

    health_rows = [
        {"Metric": "API Status",
         "Value": "Online" if api_online else "Down",
         "Status": status_text("OK", "green") if api_online else status_text("Down", "red")},
        {"Metric": "Response Time",
         "Value": f"{response_ms}ms",
         "Status": status_text("OK", "green") if response_ms < 500 else status_text("Warning", "amber")},
        {"Metric": "Database",
         "Value": f"{len(users_data)} users, {len(orders_data)} orders",
         "Status": status_text("OK", "green")},
        {"Metric": "Menu Items",
         "Value": str(len(menu_data)),
         "Status": status_text("OK", "green")},
        {"Metric": "Ingredients",
         "Value": str(len(ingredients_data)),
         "Status": status_text("OK", "green")},
    ]
    health_df = pd.DataFrame(health_rows)

    st.dataframe(health_df, use_container_width=True, hide_index=True)

    # ---- Section 2: Data Discrepancies ------------------------------------
    st.subheader("Potential Data Discrepancies")

    expected_data, exp_ok = safe_get(f"{API_BASE}/expected_usage")

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
        display_df = discrepancies_df.copy()
        display_df["Variance"] = display_df["Variance"].apply(
            lambda v: status_text(f"{v:.1f}", "red")
        )
        st.dataframe(display_df, use_container_width=True, hide_index=True)
        st.caption("Items shown have actual stock below expected levels.")
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
