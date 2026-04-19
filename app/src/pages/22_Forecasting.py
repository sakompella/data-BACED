import logging
logger = logging.getLogger(__name__)

import streamlit as st
import requests
import pandas as pd
from modules.nav import SideBarLinks
from modules.style import inject_custom_css, status_badge, API_BASE

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

    merged["risk"] = merged["variance"].apply(risk_level)

    RISK_COLOR = {"High": "red", "Medium": "amber", "Low": "green"}

    header = (
        "<tr>"
        "<th style='text-align:left;padding:10px 12px;'>Ingredient</th>"
        "<th style='text-align:right;padding:10px 12px;'>Expected (7d)</th>"
        "<th style='text-align:right;padding:10px 12px;'>Actual Stock</th>"
        "<th style='text-align:right;padding:10px 12px;'>Variance</th>"
        "<th style='text-align:center;padding:10px 12px;'>Risk</th>"
        "</tr>"
    )

    rows_html = ""
    for _, row in merged.iterrows():
        variance_str = f"+{row['variance']:.0f}" if row["variance"] >= 0 else f"{row['variance']:.0f}"
        badge = status_badge(row["risk"], RISK_COLOR[row["risk"]])
        rows_html += (
            f"<tr>"
            f"<td style='padding:10px 12px;'>{row['ingredient_name']}</td>"
            f"<td style='padding:10px 12px;text-align:right;'>{row['expected_7d']:.0f}</td>"
            f"<td style='padding:10px 12px;text-align:right;'>{row['quantity']}</td>"
            f"<td style='padding:10px 12px;text-align:right;'>{variance_str}</td>"
            f"<td style='padding:10px 12px;text-align:center;'>{badge}</td>"
            f"</tr>"
        )

    table_html = f"""
    <table style="width:100%;border-collapse:collapse;font-size:0.95em;">
        <thead style="background:#F0F0F0;font-weight:600;">
            {header}
        </thead>
        <tbody>
            {rows_html if rows_html else "<tr><td colspan='5' style='padding:20px;text-align:center;color:#999;'>No comparison data available.</td></tr>"}
        </tbody>
    </table>
    """
    st.markdown(table_html, unsafe_allow_html=True)

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
        header_prices = (
            "<tr>"
            "<th style='text-align:left;padding:10px 12px;'>Supplier</th>"
            "<th style='text-align:left;padding:10px 12px;'>Item</th>"
            "<th style='text-align:right;padding:10px 12px;'>Prev. Price</th>"
            "<th style='text-align:right;padding:10px 12px;'>Curr. Price</th>"
            "<th style='text-align:center;padding:10px 12px;'>Change</th>"
            "</tr>"
        )

        rows_prices = ""
        for item in prices_data:
            prev = float(item["previous_price"])
            curr = float(item["current_price"])
            if prev and prev != 0:
                pct = (curr - prev) / prev * 100
                sign = "+" if pct >= 0 else ""
                change_str = f"{sign}{pct:.0f}%"
                color_key = "red" if pct > 0 else "green" if pct < 0 else "gray"
            else:
                change_str = "N/A"
                color_key = "gray"

            badge = status_badge(change_str, color_key)
            rows_prices += (
                f"<tr>"
                f"<td style='padding:10px 12px;'>{item['supplier_name']}</td>"
                f"<td style='padding:10px 12px;'>{item['ingredient_name']}</td>"
                f"<td style='padding:10px 12px;text-align:right;'>${prev:.2f}</td>"
                f"<td style='padding:10px 12px;text-align:right;'>${curr:.2f}</td>"
                f"<td style='padding:10px 12px;text-align:center;'>{badge}</td>"
                f"</tr>"
            )

        table_prices_html = f"""
        <table style="width:100%;border-collapse:collapse;font-size:0.95em;">
            <thead style="background:#F0F0F0;font-weight:600;">
                {header_prices}
            </thead>
            <tbody>
                {rows_prices}
            </tbody>
        </table>
        """
        st.markdown(table_prices_html, unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Bottom actions
# ---------------------------------------------------------------------------
st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)
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
