import logging
logger = logging.getLogger(__name__)

import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from modules.nav import SideBarLinks
from modules.style import inject_custom_css, status_text, API_BASE

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
    freq = row.get("time_period", row.get("usage_frequency", "daily")).lower()
    multipliers = FREQ_MULTIPLIERS.get(freq, FREQ_MULTIPLIERS["daily"])
    return float(row["expected_quantity"]) * multipliers[str(days)]

usage_df["used"] = usage_df.apply(compute_used, axis=1).astype(float)
usage_df["avg_per_day"] = usage_df["used"] / days

# Join with ingredients for current stock and reorder threshold
ingredients_df["quantity"] = pd.to_numeric(ingredients_df["quantity"], errors="coerce")
ingredients_df["reorder_count"] = pd.to_numeric(ingredients_df["reorder_count"], errors="coerce")
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

# Build dataframe for display
ingredient_display = pd.DataFrame({
    "Ingredient": usage_df["ingredient_name"],
    f"Used ({period})": usage_df["used"],
    "Avg/Day": usage_df["avg_per_day"],
    "In Stock": usage_df["in_stock"],
    "Status": usage_df["status"].apply(lambda s: status_text(s, s.lower())),
})

st.dataframe(
    ingredient_display,
    column_config={
        "Ingredient": st.column_config.TextColumn("Ingredient"),
        f"Used ({period})": st.column_config.NumberColumn(f"Used ({period})", format="%.1f"),
        "Avg/Day": st.column_config.NumberColumn("Avg/Day", format="%.1f"),
        "In Stock": st.column_config.NumberColumn("In Stock", format="%d"),
        "Status": st.column_config.TextColumn("Status"),
    },
    hide_index=True,
    use_container_width=True,
)

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
export_df = usage_df[["ingredient_name", "used", "avg_per_day", "in_stock", "status"]].copy()
export_df.columns = ["Ingredient", f"Used ({period})", "Avg/Day", "In Stock", "Status"]

st.download_button(
    label="Export Data",
    data=export_df.to_csv(index=False),
    file_name="ingredient_usage.csv",
    mime="text/csv",
)
