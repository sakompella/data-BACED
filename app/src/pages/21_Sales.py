import logging
logger = logging.getLogger(__name__)

import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from modules.nav import SideBarLinks
from modules.style import inject_custom_css, API_BASE

st.set_page_config(layout="wide")
SideBarLinks()
inject_custom_css()

st.title("Sales")

# ---------------------------------------------------------------------------
# Period selector (top-right)
# ---------------------------------------------------------------------------
_, period_col = st.columns([4, 1])
with period_col:
    period = st.selectbox("Period", ["Last 7 Days", "Last 30 Days"])

days = 7 if period == "Last 7 Days" else 30



# ---------------------------------------------------------------------------
# Sales + Orders
# ---------------------------------------------------------------------------
col_sales, col_chart = st.columns(2)

# Fetch kitchen orders
try:
    orders_resp = requests.get(f"{API_BASE}/ord/kitchen_orders")
    orders_resp.raise_for_status()
    orders_data = orders_resp.json()
except requests.RequestException:
    orders_data = []

# Fetch menu items for average price calculation
try:
    menu_resp = requests.get(f"{API_BASE}/menu/menu_items")
    menu_resp.raise_for_status()
    menu_items_data = menu_resp.json()
except requests.RequestException:
    menu_items_data = []

avg_menu_price = 0.0
if menu_items_data:
    prices = [float(item["price"]) for item in menu_items_data if item.get("price")]
    avg_menu_price = sum(prices) / len(prices) if prices else 0.0

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

        daily["revenue"] = daily["orders"] * avg_menu_price
        daily["top_seller"] = "—"

        sales_display = pd.DataFrame({
            "Date": daily["date"].astype(str),
            "Orders": daily["orders"],
            "Est. Revenue": daily["revenue"],
            "Top Seller": daily["top_seller"],
        })

        st.dataframe(
            sales_display,
            column_config={
                "Date": st.column_config.TextColumn("Date"),
                "Orders": st.column_config.NumberColumn("Orders", format="%d"),
                "Est. Revenue": st.column_config.NumberColumn("Est. Revenue", format="$%.2f"),
                "Top Seller": st.column_config.TextColumn("Top Seller"),
            },
            hide_index=True,
            use_container_width=True,
        )
        st.caption("Revenue estimated using average menu item price.")
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
if orders_data:
    st.download_button(
    label="Export Data",
    data=sales_display.to_csv(index=False),
    file_name="sales.csv",
    mime="text/csv")
