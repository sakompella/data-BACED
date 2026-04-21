import logging
import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from datetime import datetime
from modules.nav import SideBarLinks
from modules.style import inject_custom_css, status_css, API_BASE

logger = logging.getLogger(__name__)

st.set_page_config(layout="wide")
SideBarLinks()
inject_custom_css()

st.title("Demand Planning")
st.caption("Plan upcoming ingredient demand and spot likely shortages.")


def fetch_or_stop(url: str, error_text: str):
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.RequestException:
        st.error(error_text)
        st.stop()


usage_data = fetch_or_stop(f"{API_BASE}/expected_usage", "Failed to load expected usage data.")
ingredient_data = fetch_or_stop(f"{API_BASE}/ingredients", "Failed to load ingredient data.")

if not usage_data or not ingredient_data:
    st.warning("No data available for demand planning.")
    st.stop()

usage_df = pd.DataFrame(usage_data)
ingredients_df = pd.DataFrame(ingredient_data)

FREQ_MULTIPLIER_7D = {"daily": 7, "weekly": 1, "biweekly": 0.5}
usage_df["expected_quantity"] = pd.to_numeric(usage_df["expected_quantity"], errors="coerce").fillna(0.0)
usage_df["time_period"] = usage_df["time_period"].fillna("daily")
usage_df["expected_7d"] = usage_df.apply(
    lambda row: row["expected_quantity"] * FREQ_MULTIPLIER_7D.get(str(row["time_period"]).lower(), 7),
    axis=1,
)

ingredients_df["quantity"] = pd.to_numeric(ingredients_df["quantity"], errors="coerce").fillna(0.0)
stock_by_name = ingredients_df.set_index("ingredient_name")["quantity"].to_dict()
usage_df["current_stock"] = usage_df["ingredient_name"].map(lambda name: float(stock_by_name.get(name, 0.0)))
usage_df["projected_balance_7d"] = usage_df["current_stock"] - usage_df["expected_7d"]
usage_df["risk"] = usage_df["projected_balance_7d"].apply(
    lambda value: "High" if value < 0 else "Medium" if value < 5 else "Low"
)

metric_col1, metric_col2, metric_col3 = st.columns(3)
metric_col1.metric("Tracked Ingredients", f"{len(usage_df)}")
metric_col2.metric("Total Expected Usage (7d)", f"{usage_df['expected_7d'].sum():.1f}")
metric_col3.metric("High-Risk Items", f"{(usage_df['risk'] == 'High').sum()}")

table_df = pd.DataFrame({
    "Ingredient": usage_df["ingredient_name"],
    "Current Stock": usage_df["current_stock"],
    "Expected (7d)": usage_df["expected_7d"],
    "Projected Balance": usage_df["projected_balance_7d"],
    "Risk": usage_df["risk"],
}).sort_values("Projected Balance")

st.subheader("Projected Ingredient Position")
st.dataframe(
    table_df.style.map(status_css, subset=["Risk"]),
    column_config={
        "Current Stock": st.column_config.NumberColumn("Current Stock", format="%.1f"),
        "Expected (7d)": st.column_config.NumberColumn("Expected (7d)", format="%.1f"),
        "Projected Balance": st.column_config.NumberColumn("Projected Balance", format="%.1f"),
    },
    hide_index=True,
    use_container_width=True,
)

st.subheader("Top Expected Usage (7 Days)")
chart_source = usage_df.sort_values("expected_7d", ascending=False).head(10)
fig = px.bar(
    chart_source,
    x="ingredient_name",
    y="expected_7d",
    labels={"ingredient_name": "Ingredient", "expected_7d": "Expected Quantity"},
)
fig.update_layout(margin=dict(l=20, r=20, t=10, b=20), height=350)
st.plotly_chart(fig, use_container_width=True)

st.subheader("Planning Tools")

tool_lookup, tool_add_usage = st.columns(2)

with tool_lookup:
    with st.expander("Lookup Ingredient by ID", expanded=False):
        ingredient_id_lookup = st.number_input(
            "Ingredient ID",
            min_value=1,
            step=1,
            value=1,
            key="lookup_ingredient_id",
        )
        if st.button("Fetch Ingredient", key="btn_fetch_ingredient", use_container_width=True):
            try:
                response = requests.get(
                    f"{API_BASE}/ingredients/{int(ingredient_id_lookup)}",
                    timeout=5,
                )
                if response.status_code == 404:
                    st.warning("Ingredient not found.")
                else:
                    response.raise_for_status()
                    st.success("Ingredient loaded.")
                    st.json(response.json())
            except requests.RequestException as exc:
                st.error(f"Failed to fetch ingredient: {exc}")

with tool_add_usage:
    with st.expander("Add Expected Usage Entry", expanded=False):
        ingredient_choices = {
            f"{row['ingredient_name']} (ID {row['ingredient_id']})": row["ingredient_id"]
            for _, row in ingredients_df.sort_values("ingredient_name").iterrows()
        }
        selected_label = st.selectbox(
            "Ingredient",
            options=list(ingredient_choices.keys()),
            key="expected_usage_ing",
        )
        expected_qty = st.number_input(
            "Expected Quantity",
            min_value=0.1,
            step=0.5,
            value=1.0,
            key="expected_usage_qty",
        )
        time_period = st.selectbox(
            "Time Period",
            options=["daily", "weekly", "biweekly"],
            key="expected_usage_period",
        )
        start_date = st.date_input("Start Date", key="expected_usage_start_date")
        start_time = st.time_input("Start Time", value=datetime.now().time(), key="expected_usage_start_time")

        if st.button("Create Expected Usage", type="primary", key="btn_expected_usage", use_container_width=True):
            payload = {
                "ingredient_id": int(ingredient_choices[selected_label]),
                "expected_quantity": float(expected_qty),
                "time_period": time_period,
                "start_timestamp": datetime.combine(start_date, start_time).strftime("%Y-%m-%d %H:%M:%S"),
            }
            actor_id = st.session_state.get("user_id")
            if actor_id:
                payload["actor_id"] = actor_id
            try:
                response = requests.post(f"{API_BASE}/expected_usage", json=payload, timeout=5)
                response.raise_for_status()
                created = response.json()
                st.success(f"Created expected usage entry #{created.get('usage_id', 'new')}.")
            except requests.RequestException as exc:
                st.error(f"Failed to create expected usage entry: {exc}")
