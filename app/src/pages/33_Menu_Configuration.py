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

st.title("Menu & Inventory Configuration")

# ---------------------------------------------------------------------------
# Tabs: Menu Items | Ingredients
# ---------------------------------------------------------------------------
tab_menu, tab_ingredients = st.tabs(["Menu Items", "Ingredients"])

# ========================== MENU ITEMS TAB =================================
with tab_menu:

    # ---- Fetch menu items -------------------------------------------------
    try:
        menu_resp = requests.get(f"{API_BASE}/menu/menu_items")
        menu_resp.raise_for_status()
        menu_items = menu_resp.json()
    except requests.RequestException:
        st.error("Failed to load menu items from the server.")
        menu_items = []

    # ---- Display existing menu items --------------------------------------
    st.subheader("Current Menu Items")

    if menu_items:
        menu_df = pd.DataFrame(menu_items)
        display_df = pd.DataFrame({
            "ID": menu_df["menu_item_id"],
            "Name": menu_df["item_name"],
            "Description": menu_df.get("description", ""),
            "Price": menu_df["price"],
            "Status": menu_df["availability_status"].apply(
                lambda s: status_text("Available", "green") if s == "available"
                else status_text("Unavailable", "red")
            ),
        })
        st.dataframe(display_df, use_container_width=True, hide_index=True)
    else:
        st.info("No menu items found.")

    # ---- Add New Menu Item ------------------------------------------------
    with st.expander("Add New Menu Item..."):
        st.subheader("Add Menu Item")

        col1, col2 = st.columns(2)
        with col1:
            new_item_name = st.text_input("Item Name", key="new_menu_name")
            new_item_price = st.number_input(
                "Price ($)", min_value=0.00, step=0.50, format="%.2f", key="new_menu_price"
            )
        with col2:
            new_item_desc = st.text_area("Description", key="new_menu_desc")
            new_item_status = st.selectbox(
                "Availability", ["available", "unavailable"], key="new_menu_status"
            )

        if st.button("Add Menu Item", type="primary", key="btn_add_menu"):
            if not new_item_name.strip():
                st.error("Item name cannot be blank.")
            else:
                payload = {
                    "item_name": new_item_name.strip(),
                    "price": new_item_price,
                    "description": new_item_desc.strip(),
                    "availability_status": new_item_status,
                }
                try:
                    resp = requests.post(f"{API_BASE}/menu/menu_items", json=payload)
                    resp.raise_for_status()
                    st.success(f"Menu item '{new_item_name}' added successfully.")
                    st.rerun()
                except requests.RequestException as e:
                    st.error(f"Failed to add menu item: {e}")

    # ---- Edit / Delete Menu Item ------------------------------------------
    with st.expander("Edit or Delete Menu Item..."):
        st.subheader("Edit Menu Item")

        if not menu_items:
            st.warning("No menu items available to edit.")
        else:
            menu_options = {
                f"{m['item_name']} (ID {m['menu_item_id']})": m for m in menu_items
            }
            selected_menu_label = st.selectbox(
                "Select Menu Item", options=list(menu_options.keys()), key="sel_menu_edit"
            )
            selected_menu = menu_options[selected_menu_label]

            col1, col2 = st.columns(2)
            with col1:
                edit_name = st.text_input(
                    "Item Name", value=selected_menu.get("item_name", ""), key="edit_menu_name"
                )
                edit_price = st.number_input(
                    "Price ($)",
                    min_value=0.00,
                    step=0.50,
                    format="%.2f",
                    value=float(selected_menu.get("price", 0)),
                    key="edit_menu_price",
                )
            with col2:
                edit_desc = st.text_area(
                    "Description",
                    value=selected_menu.get("description", ""),
                    key="edit_menu_desc",
                )
                status_options = ["available", "unavailable"]
                current_status = selected_menu.get("availability_status", "available")
                edit_status = st.selectbox(
                    "Availability",
                    status_options,
                    index=status_options.index(current_status) if current_status in status_options else 0,
                    key="edit_menu_status",
                )

            btn_update, btn_delete, _ = st.columns([1, 1, 3])
            with btn_update:
                if st.button("Update Menu Item", type="primary", key="btn_update_menu"):
                    if not edit_name.strip():
                        st.error("Item name cannot be blank.")
                    else:
                        payload = {
                            "item_name": edit_name.strip(),
                            "price": edit_price,
                            "description": edit_desc.strip(),
                            "availability_status": edit_status,
                        }
                        try:
                            resp = requests.put(
                                f"{API_BASE}/menu/menu_items/{selected_menu['menu_item_id']}",
                                json=payload,
                            )
                            resp.raise_for_status()
                            st.success("Menu item updated successfully.")
                            st.rerun()
                        except requests.RequestException as e:
                            st.error(f"Failed to update menu item: {e}")

            with btn_delete:
                if st.button("Delete Menu Item", type="secondary", key="btn_del_menu"):
                    st.session_state["confirm_delete_menu_id"] = selected_menu["menu_item_id"]

                if st.session_state.get("confirm_delete_menu_id") == selected_menu["menu_item_id"]:
                    st.warning(
                        f"Are you sure you want to delete **{selected_menu['item_name']}**?"
                    )
                    c1, c2 = st.columns(2)
                    with c1:
                        if st.button("Yes, delete", key="confirm_del_menu"):
                            try:
                                resp = requests.delete(
                                    f"{API_BASE}/menu/menu_items/{selected_menu['menu_item_id']}"
                                )
                                resp.raise_for_status()
                                st.success("Menu item deleted.")
                                st.session_state.pop("confirm_delete_menu_id", None)
                                st.rerun()
                            except requests.RequestException as e:
                                st.error(f"Failed to delete menu item: {e}")
                    with c2:
                        if st.button("Cancel", key="cancel_del_menu"):
                            st.session_state.pop("confirm_delete_menu_id", None)
                            st.rerun()


# ========================== INGREDIENTS TAB =================================
with tab_ingredients:

    # ---- Fetch ingredients ------------------------------------------------
    try:
        ing_resp = requests.get(f"{API_BASE}/inv/ingredients")
        ing_resp.raise_for_status()
        ingredients = ing_resp.json()
    except requests.RequestException:
        st.error("Failed to load ingredients from the server.")
        ingredients = []

    # ---- Fetch suppliers (for dropdown) -----------------------------------
    try:
        sup_resp = requests.get(f"{API_BASE}/inv/suppliers")
        sup_resp.raise_for_status()
        suppliers = sup_resp.json()
    except requests.RequestException:
        suppliers = []

    supplier_map = {s["supplier_id"]: s["supplier_name"] for s in suppliers}
    supplier_name_to_id = {s["supplier_name"]: s["supplier_id"] for s in suppliers}

    # ---- Display existing ingredients -------------------------------------
    st.subheader("Current Ingredients")

    if ingredients:
        ing_df = pd.DataFrame(ingredients)
        display_ing = pd.DataFrame({
            "ID": ing_df["ingredient_id"],
            "Name": ing_df["ingredient_name"],
            "Qty": ing_df["quantity"],
            "Unit": ing_df["unit"],
            "Cost/Unit": ing_df["cost_per_unit"],
            "Reorder At": ing_df["reorder_count"],
            "Expiration": pd.to_datetime(ing_df["expiration_date"]).dt.strftime("%Y-%m-%d"),
            "Supplier": ing_df["supplier_name"],
        })
        st.dataframe(display_ing, use_container_width=True, hide_index=True)
    else:
        st.info("No ingredients found.")

    # ---- Add New Ingredient -----------------------------------------------
    with st.expander("Add New Ingredient..."):
        st.subheader("Add Ingredient")

        col1, col2 = st.columns(2)
        with col1:
            new_ing_name = st.text_input("Ingredient Name", key="new_ing_name")
            new_ing_unit = st.text_input("Unit (e.g., lbs, oz, each)", key="new_ing_unit")
            new_ing_cost = st.number_input(
                "Cost per Unit ($)", min_value=0.00, step=0.10, format="%.2f", key="new_ing_cost"
            )
            new_ing_qty = st.number_input(
                "Initial Quantity", min_value=0.0, step=1.0, format="%.1f", key="new_ing_qty"
            )
        with col2:
            new_ing_reorder = st.number_input(
                "Reorder Threshold", min_value=0.0, step=1.0, format="%.1f", key="new_ing_reorder"
            )
            new_ing_exp = st.date_input("Expiration Date", key="new_ing_exp")
            if suppliers:
                new_ing_supplier = st.selectbox(
                    "Supplier",
                    options=list(supplier_name_to_id.keys()),
                    key="new_ing_supplier",
                )
            else:
                st.warning("No suppliers available.")
                new_ing_supplier = None

        if st.button("Add Ingredient", type="primary", key="btn_add_ing"):
            if not new_ing_name.strip():
                st.error("Ingredient name cannot be blank.")
            elif not new_ing_supplier:
                st.error("Please select a supplier.")
            else:
                payload = {
                    "ingredient_name": new_ing_name.strip(),
                    "supplier_id": supplier_name_to_id[new_ing_supplier],
                    "unit": new_ing_unit.strip(),
                    "cost_per_unit": new_ing_cost,
                    "quantity": new_ing_qty,
                    "reorder_count": new_ing_reorder,
                    "expiration_date": new_ing_exp.strftime("%Y-%m-%d"),
                }
                try:
                    resp = requests.post(f"{API_BASE}/inv/ingredients", json=payload)
                    resp.raise_for_status()
                    st.success(f"Ingredient '{new_ing_name}' added successfully.")
                    st.rerun()
                except requests.RequestException as e:
                    st.error(f"Failed to add ingredient: {e}")

    # ---- Edit / Delete Ingredient -----------------------------------------
    with st.expander("Edit or Delete Ingredient..."):
        st.subheader("Edit Ingredient")

        if not ingredients:
            st.warning("No ingredients available to edit.")
        else:
            ing_options = {
                f"{i['ingredient_name']} (ID {i['ingredient_id']})": i for i in ingredients
            }
            selected_ing_label = st.selectbox(
                "Select Ingredient", options=list(ing_options.keys()), key="sel_ing_edit"
            )
            selected_ing = ing_options[selected_ing_label]

            col1, col2 = st.columns(2)
            with col1:
                edit_ing_name = st.text_input(
                    "Ingredient Name",
                    value=selected_ing.get("ingredient_name", ""),
                    key="edit_ing_name",
                )
                edit_ing_unit = st.text_input(
                    "Unit", value=selected_ing.get("unit", ""), key="edit_ing_unit"
                )
                edit_ing_cost = st.number_input(
                    "Cost per Unit ($)",
                    min_value=0.00,
                    step=0.10,
                    format="%.2f",
                    value=float(selected_ing.get("cost_per_unit", 0)),
                    key="edit_ing_cost",
                )
                edit_ing_qty = st.number_input(
                    "Quantity",
                    min_value=0.0,
                    step=1.0,
                    format="%.1f",
                    value=float(selected_ing.get("quantity", 0)),
                    key="edit_ing_qty",
                )
            with col2:
                edit_ing_reorder = st.number_input(
                    "Reorder Threshold",
                    min_value=0.0,
                    step=1.0,
                    format="%.1f",
                    value=float(selected_ing.get("reorder_count", 0)),
                    key="edit_ing_reorder",
                )
                edit_ing_exp = st.date_input(
                    "Expiration Date",
                    value=pd.to_datetime(selected_ing.get("expiration_date")).date()
                    if selected_ing.get("expiration_date")
                    else None,
                    key="edit_ing_exp",
                )
                if suppliers:
                    current_supplier = selected_ing.get("supplier_name", "")
                    sup_names = list(supplier_name_to_id.keys())
                    sup_idx = sup_names.index(current_supplier) if current_supplier in sup_names else 0
                    edit_ing_supplier = st.selectbox(
                        "Supplier", options=sup_names, index=sup_idx, key="edit_ing_supplier"
                    )
                else:
                    edit_ing_supplier = None

            btn_update, btn_delete, _ = st.columns([1, 1, 3])
            with btn_update:
                if st.button("Update Ingredient", type="primary", key="btn_update_ing"):
                    if not edit_ing_name.strip():
                        st.error("Ingredient name cannot be blank.")
                    else:
                        payload = {
                            "ingredient_name": edit_ing_name.strip(),
                            "unit": edit_ing_unit.strip(),
                            "cost_per_unit": edit_ing_cost,
                            "quantity": edit_ing_qty,
                            "reorder_count": edit_ing_reorder,
                            "expiration_date": edit_ing_exp.strftime("%Y-%m-%d"),
                        }
                        if edit_ing_supplier:
                            payload["supplier_id"] = supplier_name_to_id[edit_ing_supplier]
                        try:
                            resp = requests.put(
                                f"{API_BASE}/inv/ingredients/{selected_ing['ingredient_id']}",
                                json=payload,
                            )
                            resp.raise_for_status()
                            st.success("Ingredient updated successfully.")
                            st.rerun()
                        except requests.RequestException as e:
                            st.error(f"Failed to update ingredient: {e}")

            with btn_delete:
                if st.button("Delete Ingredient", type="secondary", key="btn_del_ing"):
                    st.session_state["confirm_delete_ing_id"] = selected_ing["ingredient_id"]

                if st.session_state.get("confirm_delete_ing_id") == selected_ing["ingredient_id"]:
                    st.warning(
                        f"Are you sure you want to delete "
                        f"**{selected_ing['ingredient_name']}**?"
                    )
                    c1, c2, _ = st.columns([1, 1, 3])
                    with c1:
                        if st.button("Yes, delete", key="confirm_del_ing"):
                            try:
                                resp = requests.delete(
                                    f"{API_BASE}/inv/ingredients/{selected_ing['ingredient_id']}"
                                )
                                resp.raise_for_status()
                                st.success("Ingredient deleted.")
                                st.session_state.pop("confirm_delete_ing_id", None)
                                st.rerun()
                            except requests.RequestException as e:
                                st.error(f"Failed to delete ingredient: {e}")
                    with c2:
                        if st.button("Cancel", key="cancel_del_ing"):
                            st.session_state.pop("confirm_delete_ing_id", None)
                            st.rerun()