import logging
logger = logging.getLogger(__name__)

import streamlit as st
import requests
import pandas as pd
from modules.nav import SideBarLinks

st.set_page_config(layout='wide')
SideBarLinks()

st.title("🍳 Inventory & Stock")

# Fetch ingredients from API
response = requests.get("http://api:4000/inv/ingredients")

if response.status_code == 200:
    data = response.json()

    if data:
        df = pd.DataFrame(data)

        # Add stock status based on quantity vs reorder_count
        def get_status(row):
            if row["quantity"] <= row["reorder_count"]:
                return "Low"
            else:
                return "OK"

        df["status"] = df.apply(get_status, axis=1)

        # Tabs for different views (stories 1 and 4)
        tab1, tab2 = st.tabs(["Current Stock", "Expiring Soon"])

        with tab1:
            st.subheader("All Ingredients")

            # Filter by status
            status_filter = st.selectbox("Filter by status", ["All", "OK", "Low"])
            if status_filter != "All":
                filtered_df = df[df["status"] == status_filter]
            else:
                filtered_df = df

            st.dataframe(
                filtered_df[["ingredient_name", "quantity", "unit",
                             "cost_per_unit", "reorder_count", "supplier_name", "status"]],
                use_container_width=True
            )

        with tab2:
            st.subheader("Ingredients Expiring Soon")

            # Convert expiration_date to datetime for sorting
            df["expiration_date"] = pd.to_datetime(df["expiration_date"])
            expiring_df = df.sort_values("expiration_date", ascending=True)

            st.dataframe(
                expiring_df[["ingredient_name", "quantity", "unit",
                             "expiration_date", "supplier_name", "status"]],
                use_container_width=True
            )
    else:
        st.warning("No ingredients found.")
else:
    st.error("Failed to load ingredients from the server.")
