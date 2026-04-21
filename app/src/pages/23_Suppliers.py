import logging
import streamlit as st
import requests
import pandas as pd
from modules.nav import SideBarLinks
from modules.style import inject_custom_css, status_css, API_BASE

logger = logging.getLogger(__name__)
 
st.set_page_config(layout="wide")
SideBarLinks()
inject_custom_css()
 
st.title("Suppliers")
 
# ---------------------------------------------------------------------------
# Fetch data
# ---------------------------------------------------------------------------
try:
    suppliers_resp = requests.get(f"{API_BASE}/suppliers")
    suppliers_resp.raise_for_status()
    suppliers_data = suppliers_resp.json()
except requests.RequestException:
    st.error("Failed to load suppliers.")
    st.stop()
 
try:
    prices_resp = requests.get(f"{API_BASE}/supplier_prices")
    prices_resp.raise_for_status()
    prices_data = prices_resp.json()
except requests.RequestException:
    st.error("Failed to load supplier prices.")
    st.stop()
 
if not prices_data:
    st.warning("No supplier price data found.")
    st.stop()
 
prices_df = pd.DataFrame(prices_data)
prices_df["previous_price"] = pd.to_numeric(prices_df["previous_price"], errors="coerce")
prices_df["current_price"] = pd.to_numeric(prices_df["current_price"], errors="coerce")
 
# ---------------------------------------------------------------------------
# Section 1: Suppliers List
# ---------------------------------------------------------------------------
st.subheader("Suppliers")
 
if suppliers_data:
    suppliers_df = pd.DataFrame(suppliers_data)
    st.dataframe(suppliers_df, hide_index=True, use_container_width=True)
    st.download_button(
        label="Export Suppliers",
        data=suppliers_df.to_csv(index=False),
        file_name="suppliers.csv",
        mime="text/csv",
    )
else:
    st.info("No suppliers found.")
 
st.divider()
 
# ---------------------------------------------------------------------------
# Section 2: Supplier Prices Table
# ---------------------------------------------------------------------------
st.subheader("Supplier Prices")
 
def format_change(row):
    prev = row["previous_price"]
    current = row["current_price"]
    if prev and prev != 0:
        percent = (current - prev) / prev * 100
        sign = "+" if percent >= 0 else ""
        change_str = f"{sign}{percent:.0f}%"
        color_key = "red" if percent > 0 else "green" if percent < 0 else "gray"
    else:
        change_str = "N/A"
        color_key = "gray"
    return change_str, color_key

change_results = prices_df.apply(format_change, axis=1)
change_texts = [r[0] for r in change_results]
change_keys = [r[1] for r in change_results]

display_prices = pd.DataFrame({
    "Supplier": prices_df["supplier_name"],
    "Item": prices_df["ingredient_name"],
    "Prev. Price": prices_df["previous_price"],
    "Curr. Price": prices_df["current_price"],
    "Change": change_texts,
})

# Style the Change column using the per-row color keys computed above.
change_css_series = pd.Series(change_keys, index=display_prices.index).map(status_css)
styled = display_prices.style.apply(lambda _: change_css_series, subset=["Change"], axis=0)

st.dataframe(
    styled,
    column_config={
        "Prev. Price": st.column_config.NumberColumn("Prev. Price", format="$%.2f"),
        "Curr. Price": st.column_config.NumberColumn("Curr. Price", format="$%.2f"),
        "Change": st.column_config.TextColumn("Change"),
    },
    hide_index=True,
    use_container_width=True,
)
 
st.download_button(
    label="Export Supplier Prices",
    data=prices_df[["supplier_name", "ingredient_name", "previous_price", "current_price"]].to_csv(index=False),
    file_name="supplier_prices.csv",
    mime="text/csv",
)