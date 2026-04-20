import logging
logger = logging.getLogger(__name__)

import streamlit as st
import requests
import pandas as pd
from modules.nav import SideBarLinks
from modules.style import inject_custom_css, status_text, API_BASE

st.set_page_config(layout="wide")
SideBarLinks()
inject_custom_css()

st.title("Forecasting & Suppliers")

tab_comparison, tab_prices = st.tabs(["Inventory Comparison", "Supplier Prices"])

# ---------------------------------------------------------------------------
# Inventory Comparison
# ---------------------------------------------------------------------------
with tab_comparison:
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

# ---------------------------------------------------------------------------
# Supplier Prices
# ---------------------------------------------------------------------------
with tab_prices:
    st.subheader("Supplier Prices")

    try:
        prices_resp = requests.get(f"{API_BASE}/inv/supplier_prices")
        prices_resp.raise_for_status()
        prices_data = prices_resp.json()
    except requests.RequestException:
        st.error("Failed to load supplier prices.")
        st.stop()

    if not prices_data:
        st.warning("No supplier price data found.")
    else:
        prices_df = pd.DataFrame(prices_data)
        prices_df["previous_price"] = pd.to_numeric(prices_df["previous_price"], errors="coerce")
        prices_df["current_price"] = pd.to_numeric(prices_df["current_price"], errors="coerce")

        def format_change(row):
            prev = row["previous_price"]
            curr = row["current_price"]
            if prev and prev != 0:
                pct = (curr - prev) / prev * 100
                sign = "+" if pct >= 0 else ""
                change_str = f"{sign}{pct:.0f}%"
                color_key = "red" if pct > 0 else "green" if pct < 0 else "gray"
            else:
                change_str = "N/A"
                color_key = "gray"
            return status_text(change_str, color_key)

        display_prices = pd.DataFrame({
            "Supplier": prices_df["supplier_name"],
            "Item": prices_df["ingredient_name"],
            "Prev. Price": prices_df["previous_price"],
            "Curr. Price": prices_df["current_price"],
            "Change": prices_df.apply(format_change, axis=1),
        })

        st.dataframe(
            display_prices,
            column_config={
                "Prev. Price": st.column_config.NumberColumn("Prev. Price", format="$%.2f"),
                "Curr. Price": st.column_config.NumberColumn("Curr. Price", format="$%.2f"),
                "Change": st.column_config.TextColumn("Change"),
            },
            hide_index=True,
            use_container_width=True,
        )

# ---------------------------------------------------------------------------
# Bottom actions
# ---------------------------------------------------------------------------
btn_col1, btn_col2, _ = st.columns([1, 1, 3])

with btn_col1:
    if st.button("Generate Forecast", type="primary"):
        st.info("Forecast generation coming soon")

with btn_col2:
    # Build CSV from whichever data is available
    export_rows = []
    if "merged" in dir() and not merged.empty:
        for _, row in merged.iterrows():
            export_rows.append({
                "Ingredient": row["ingredient_name"],
                "Expected (7d)": row["expected_7d"],
                "Actual Stock": row["quantity"],
                "Variance": row["variance"],
                "Risk": row["risk"],
            })
    export_df = pd.DataFrame(export_rows) if export_rows else pd.DataFrame()
    st.download_button(
        "Export Report",
        data=export_df.to_csv(index=False) if not export_df.empty else "No data",
        file_name="forecasting_report.csv",
        mime="text/csv",
    )
