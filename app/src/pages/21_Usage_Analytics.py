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

st.title("Usage & Inventory Analytics")

# ---------------------------------------------------------------------------
# Period selector (top-right)
# ---------------------------------------------------------------------------
_, period_col = st.columns([4, 1])
with period_col:
    period = st.selectbox("Period", ["Last 7 Days", "Last 30 Days"])

days = 7 if period == "Last 7 Days" else 30

# ---------------------------------------------------------------------------
# Fetch data
# ---------------------------------------------------------------------------
try:
    usage_resp = requests.get(f"{API_BASE}/inv/expected_usage")
    usage_resp.raise_for_status()
    usage_data = usage_resp.json()
except requests.RequestException:
    st.error("Failed to load expected usage data from the server.")
    st.stop()

try:
    ingredients_resp = requests.get(f"{API_BASE}/inv/ingredients")
    ingredients_resp.raise_for_status()
    ingredients_data = ingredients_resp.json()
except requests.RequestException:
    st.error("Failed to load ingredient data from the server.")
    st.stop()

if not usage_data:
    st.warning("No usage data found.")
    st.stop()

# ---------------------------------------------------------------------------
# Section 1: Ingredient Usage Table
# ---------------------------------------------------------------------------
st.subheader("Ingredient Usage")

FREQ_MULTIPLIERS = {
    "daily":    {"7": 7,   "30": 30},
    "weekly":   {"7": 1,   "30": 30 / 7},
    "biweekly": {"7": 0.5, "30": 30 / 14},
}

usage_df = pd.DataFrame(usage_data)
ingredients_df = pd.DataFrame(ingredients_data)

# Compute period usage from expected_quantity and frequency
def compute_used(row):
    freq = row.get("usage_frequency", "daily").lower()
    multipliers = FREQ_MULTIPLIERS.get(freq, FREQ_MULTIPLIERS["daily"])
    return row["expected_quantity"] * multipliers[str(days)]

usage_df["used"] = usage_df.apply(compute_used, axis=1)
usage_df["avg_per_day"] = usage_df["used"] / days

# Join with ingredients for current stock and reorder threshold
stock_lookup = ingredients_df.set_index("ingredient_name")[["quantity", "reorder_count"]].to_dict("index")

usage_df["in_stock"] = usage_df["ingredient_name"].map(
    lambda n: stock_lookup.get(n, {}).get("quantity", 0)
)
usage_df["reorder_count"] = usage_df["ingredient_name"].map(
    lambda n: stock_lookup.get(n, {}).get("reorder_count", 0)
)
usage_df["status"] = usage_df.apply(
    lambda r: "Low" if r["in_stock"] <= r["reorder_count"] else "OK", axis=1
)

# Build HTML table
header = (
    "<tr>"
    "<th style='text-align:left;padding:10px 12px;'>Ingredient</th>"
    "<th style='text-align:right;padding:10px 12px;'>Used ({period})</th>"
    "<th style='text-align:right;padding:10px 12px;'>Avg/Day</th>"
    "<th style='text-align:right;padding:10px 12px;'>In Stock</th>"
    "<th style='text-align:center;padding:10px 12px;'>Status</th>"
    "</tr>"
).format(period=period)

rows_html = ""
for _, row in usage_df.iterrows():
    badge = status_badge(row["status"], row["status"].lower())
    rows_html += (
        f"<tr>"
        f"<td style='padding:10px 12px;'>{row['ingredient_name']}</td>"
        f"<td style='padding:10px 12px;text-align:right;'>{row['used']:.1f}</td>"
        f"<td style='padding:10px 12px;text-align:right;'>{row['avg_per_day']:.1f}</td>"
        f"<td style='padding:10px 12px;text-align:right;'>{row['in_stock']}</td>"
        f"<td style='padding:10px 12px;text-align:center;'>{badge}</td>"
        f"</tr>"
    )

table_html = f"""
<table style="width:100%;border-collapse:collapse;font-size:0.95em;">
    <thead style="background:#F0F0F0;font-weight:600;">
        {header}
    </thead>
    <tbody>
        {rows_html if rows_html else "<tr><td colspan='5' style='padding:20px;text-align:center;color:#999;'>No usage data.</td></tr>"}
    </tbody>
</table>
"""
st.markdown(table_html, unsafe_allow_html=True)
st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Section 2: Daily Sales Summary + Revenue Chart
# ---------------------------------------------------------------------------
col_sales, col_chart = st.columns(2)

# Fetch kitchen orders
try:
    orders_resp = requests.get(f"{API_BASE}/ord/kitchen_orders")
    orders_resp.raise_for_status()
    orders_data = orders_resp.json()
except requests.RequestException:
    orders_data = []

with col_sales:
    st.subheader("Daily Sales Summary")

    if orders_data:
        orders_df = pd.DataFrame(orders_data)
        orders_df["date"] = pd.to_datetime(orders_df["created_at"]).dt.date
        daily = (
            orders_df.groupby("date")
            .size()
            .reset_index(name="orders")
            .sort_values("date", ascending=False)
            .head(7)
            .sort_values("date")
        )

        sales_header = (
            "<tr>"
            "<th style='text-align:left;padding:10px 12px;'>Date</th>"
            "<th style='text-align:right;padding:10px 12px;'>Orders</th>"
            "</tr>"
        )
        sales_rows = ""
        for _, row in daily.iterrows():
            sales_rows += (
                f"<tr>"
                f"<td style='padding:10px 12px;'>{row['date']}</td>"
                f"<td style='padding:10px 12px;text-align:right;'>{row['orders']}</td>"
                f"</tr>"
            )

        sales_html = f"""
        <table style="width:100%;border-collapse:collapse;font-size:0.95em;">
            <thead style="background:#F0F0F0;font-weight:600;">
                {sales_header}
            </thead>
            <tbody>
                {sales_rows}
            </tbody>
        </table>
        """
        st.markdown(sales_html, unsafe_allow_html=True)
    else:
        st.info("No order data available.")

with col_chart:
    st.subheader("Orders Over Time")

    if orders_data:
        fig = px.line(
            daily,
            x="date",
            y="orders",
            labels={"date": "Date", "orders": "Order Count"},
            markers=True,
        )
        fig.update_layout(
            margin=dict(l=20, r=20, t=10, b=20),
            height=350,
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No order data available for chart.")

# ---------------------------------------------------------------------------
# Bottom: Export
# ---------------------------------------------------------------------------
st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

export_df = usage_df[["ingredient_name", "used", "avg_per_day", "in_stock", "status"]].copy()
export_df.columns = ["Ingredient", f"Used ({period})", "Avg/Day", "In Stock", "Status"]

st.download_button(
    label="Export Data",
    data=export_df.to_csv(index=False),
    file_name="ingredient_usage.csv",
    mime="text/csv",
)
