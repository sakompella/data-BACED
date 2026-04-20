import logging
logger = logging.getLogger(__name__)

import streamlit as st
import requests
import pandas as pd
from datetime import datetime
from modules.nav import SideBarLinks
from modules.style import inject_custom_css, status_text, API_BASE

st.set_page_config(layout="wide")
SideBarLinks()
inject_custom_css()

st.title("Ingredients")

# ---------------------------------------------------------------------------
# Period selector (top-right)
# ---------------------------------------------------------------------------
_, period_col = st.columns([4, 1])
with period_col:
    period = st.selectbox("Period", ["Last 7 Days", "Last 30 Days"])

days = 7 if period == "Last 7 Days" else 30


# ---------------------------------------------------------------------------
# Ingredient Usage Table
# ---------------------------------------------------------------------------
st.subheader("Ingredient Usage")
 
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
 
FREQ_MULTIPLIERS = {
    "daily":    {"7": 7,   "30": 30},
    "weekly":   {"7": 1,   "30": 30 / 7},
    "biweekly": {"7": 0.5, "30": 30 / 14},
}
 
usage_df = pd.DataFrame(usage_data)
ingredients_df = pd.DataFrame(ingredients_data)
 
def compute_used(row):
    freq = row.get("time_period", row.get("usage_frequency", "daily")).lower()
    multipliers = FREQ_MULTIPLIERS.get(freq, FREQ_MULTIPLIERS["daily"])
    return float(row["expected_quantity"]) * multipliers[str(days)]
 
usage_df["used"] = usage_df.apply(compute_used, axis=1).astype(float)
usage_df["avg_per_day"] = usage_df["used"] / days
 
ingredients_df["quantity"] = pd.to_numeric(ingredients_df["quantity"], errors="coerce")
ingredients_df["reorder_count"] = pd.to_numeric(ingredients_df["reorder_count"], errors="coerce")
stock_lookup = ingredients_df.set_index("ingredient_name")[["quantity", "reorder_count", "unit"]].to_dict("index")
 
usage_df["in_stock"] = usage_df["ingredient_name"].map(
    lambda n: stock_lookup.get(n, {}).get("quantity", 0)
)
usage_df["reorder_count"] = usage_df["ingredient_name"].map(
    lambda n: stock_lookup.get(n, {}).get("reorder_count", 0)
)
usage_df["status"] = usage_df.apply(
    lambda r: "Low" if r["in_stock"] <= r["reorder_count"] else "OK", axis=1
)
 
ingredient_display = pd.DataFrame({
    "Ingredient": usage_df["ingredient_name"],
    f"Used ({period})": usage_df["used"],
    "Avg/Day": usage_df['avg_per_day'],
    "In Stock": usage_df['in_stock'],
    "Status": usage_df["status"].apply(lambda s: status_text(s, "red" if s == "Low" else "green")),
})
 
st.dataframe(
    ingredient_display,
    column_config={
        "Ingredient": st.column_config.TextColumn("Ingredient"),
        f"Used ({period})": st.column_config.NumberColumn(f"Used ({period})", format="%.1f"),
        "Avg/Day": st.column_config.NumberColumn("Avg / Day", format='%.1f'),
        "In Stock": st.column_config.NumberColumn("In Stock", format='%.1f'),
        "Status": st.column_config.TextColumn("Status"),
    },
    hide_index=True,
    use_container_width=True,
)
st.download_button(
    label='Export Ingredient Usage',
    data=ingredient_display.to_csv(index=False),
    file_name='ingredient_usage.csv',
    mime='text/csv'
)
 
st.divider()
 
# ---------------------------------------------------------------------------
# Ingredient vs Expected Usage
# ---------------------------------------------------------------------------
st.subheader("Inventory vs Expected Usage")

try:
    usage_resp = requests.get(f"{API_BASE}/inv/expected_usage")
    usage_resp.raise_for_status()
    usage_data = usage_resp.json()
except requests.RequestException:
    st.error("Failed to load expected usage data.")
    st.stop()

try:
    ing_resp = requests.get(f"{API_BASE}/inv/ingredients")
    ing_resp.raise_for_status()
    ing_data = ing_resp.json()
except requests.RequestException:
    st.error("Failed to load ingredients data.")
    st.stop()

if not usage_data or not ing_data:
    st.warning("No data available for comparison.")
    st.stop()

FREQ_MULTIPLIERS = {
    "daily": 7,
    "weekly": 1,
    "biweekly": 0.5,
}

usage_df = pd.DataFrame(usage_data)
ing_df = pd.DataFrame(ing_data)

# Adjust expected quantity by frequency for a 7-day window
usage_df["expected_quantity"] = pd.to_numeric(usage_df["expected_quantity"], errors="coerce")
usage_df["expected_7d"] = usage_df.apply(
    lambda r: float(r["expected_quantity"]) * FREQ_MULTIPLIERS.get(
        str(r.get("time_period", r.get("frequency", "daily"))).lower(), 1
    ),
    axis=1,
)

ing_df["quantity"] = pd.to_numeric(ing_df["quantity"], errors="coerce")
merged = usage_df.merge(ing_df, on="ingredient_name", how="inner", suffixes=("_usage", "_inv"))
merged["variance"] = merged["quantity"].astype(float) - merged["expected_7d"].astype(float)

def risk_level(variance):
    if variance < 0:
        return "High"
    if variance < 5:
        return "Medium"
    return "Low"

RISK_COLOR = {"High": "red", "Medium": "amber", "Low": "green"}
merged["risk"] = merged["variance"].apply(risk_level)

display_df = pd.DataFrame({
    "Ingredient": merged["ingredient_name"],
    "Expected (7d)": merged["expected_7d"],
    "Actual Stock": merged["quantity"],
    "Variance": merged["variance"].apply(
        lambda v: f"+{v:.0f}" if v >= 0 else f"{v:.0f}"
    ),
    "Risk": merged["risk"].apply(
        lambda r: status_text(r, RISK_COLOR[r])
    ),
})

if display_df.empty:
    st.info("No comparison data available.")
else:
    st.dataframe(
        display_df,
        column_config={
            "Expected (7d)": st.column_config.NumberColumn("Expected (7d)"),
            "Actual Stock": st.column_config.NumberColumn("Actual Stock"),
            "Variance": st.column_config.TextColumn("Variance"),
            "Risk": st.column_config.TextColumn("Risk"),
        },
        hide_index=True,
            use_container_width=True,
    )
    st.download_button(
        label="Export Inventory vs Expected",
        data=merged[['ingredient_name','expected_7d','quantity','variance','risk']].to_csv(index=False),
        file_name='inventory_vs_expected.csv',
        mime='text/csv'
    )

st.divider()
# ---------------------------------------------------------------------------
# Demand Prediction
# ---------------------------------------------------------------------------
st.subheader("Add Demand Prediction")
 
ing_options = {i["ingredient_name"]: i["ingredient_id"] for i in ing_data}
 
with st.form("demand_form", clear_on_submit=True):
    selected_ing = st.selectbox("Ingredient", options=list(ing_options.keys()))
    expected_qty = st.number_input("Expected Quantity", min_value=0.1, step=0.1, format="%.1f")
    time_period = st.selectbox("Frequency", ["daily", "weekly", "biweekly"])
    start_date = st.date_input("Start Date", value=datetime.today())
    submitted = st.form_submit_button("Add Prediction", type="primary")
 
if submitted:
    ing_id = ing_options.get(selected_ing)
    try:
        resp = requests.post(f"{API_BASE}/inv/expected_usage", json={
            "ingredient_id": ing_id,
            "expected_quantity": expected_qty,
            "time_period": time_period,
            "start_timestamp": start_date.strftime("%Y-%m-%d %H:%M:%S"),
        })
        if resp.status_code in (200, 201):
            st.success(f"Demand prediction added for {selected_ing}.")
            st.rerun()
        else:
            st.error("Failed to add prediction.")
    except requests.RequestException:
        st.error("Failed to add prediction.")
 
st.divider()