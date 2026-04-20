import logging
logger = logging.getLogger(__name__)

import streamlit as st
import requests
from modules.nav import SideBarLinks
from modules.style import inject_custom_css, status_text, API_BASE

st.set_page_config(layout="wide")
SideBarLinks()
inject_custom_css()

st.title("Menu Management")

# -----------------------------------------------
# Helpers
# -----------------------------------------------

def fetch_json(url):
    try:
        resp = requests.get(url)
        if resp.status_code == 200:
            return resp.json()
    except requests.RequestException as e:
        logger.error("Request failed: %s", e)
    return None

def save_menu_item(payload, menu_item_id=None):
    try:
        if menu_item_id:
            resp = requests.put(f"{API_BASE}/menu/menu_items/{menu_item_id}", json=payload)
        else:
            resp = requests.post(f"{API_BASE}/menu/menu_items", json=payload)
        return resp.status_code in (200,201)
    except requests.RequestException as e:
        logger.error("Failed to save menu item: %s", e)
        return False
    

# ---------------------------------------------
# Menu Items Table
# ---------------------------------------------
st.subheader("Menu Items")

menu_items = fetch_json(f"{API_BASE}/menu/menu_items")
if menu_items is None:
    st.error("Failed to load menu items from server")
elif not menu_items:
    st.info("No menu items found")
else:
    hcols = st.columns([3, 4, 1.5, 2])
    for col, label in zip(hcols, ["Item", "Description", "Price", "Status"]):
        col.markdown(f"**{label}**")
    nonarchived_items = []
    for item in menu_items:
        if item.get('availability_status') != 'archived':
            nonarchived_items.append(item)
    for item in nonarchived_items:
        avail = item.get("availability_status", "unavailable")
        if avail == "available":
            color = "green"
        elif avail == 'unavailable':
            color = 'red'
        else:
            color = 'gray'
        cols = st.columns([3,4,1.5,2])
        cols[0].write(item.get('item_name', "-"))
        cols[1].write(item.get('description',"-"))
        cols[2].write(f"${float(item.get('price', 0)):.2f}")
        cols[3].write(status_text(avail.capitalize(), color))

st.divider()

# ----------------------------------------------
# Edit Menu
# ----------------------------------------------
st.subheader("Edit Menu")
tab_add, tab_edit, tab_delete = st.tabs(["New Item", "Edit Item", "Archive Item"])

# Add item
with tab_add:
    with st.form("add_form", clear_on_submit=True):
        new_name = st.text_input("Item Name")
        new_desc = st.text_area("Description", height=80)
        new_price = st.number_input("Price ($)", min_value=0.0, step=0.01, format="%.2f")
        new_avail = st.selectbox("Availability", ['available', 'unavailable'])
        saved = st.form_submit_button('Save Item', type="primary")
    if saved:
        if not new_name.strip():
            st.warning("Need item name")
        else:
            if save_menu_item({'item_name': new_name.strip(), 'description': new_desc.strip(),
                            'price': new_price, 'availability_status': new_avail}):
                st.success(f"{new_name} added to menu")
                st.rerun()
            else:
                st.error("Failed to create new item")

#Edit item
with tab_edit:
    if not menu_items:
        st.info("No menu items found")
    else:
        item_map = {}
        for i in menu_items:
            if i.get('availability_status') != 'archived':
                item_map[i['item_name']] = i
        selected_name = st.selectbox("Select item", options=["select item"] + list(item_map.keys()), 
                                     label_visibility="collapsed", key='edit')
        if selected_name != "select item":
            item = item_map[selected_name]
            item_id = item["menu_item_id"]
            with st.form("edit_form"):
                edit_name = st.text_input('Item Name', value=item.get('item_name', ""))
                edit_desc = st.text_area('Description', value=item.get('description', ""), height=80)
                edit_price = st.number_input('Price ($)', value=float(item.get('price', 0)), min_value=0.0,
                                             step=0.01, format="%.2f")
                if item.get('availability_status') == 'available':
                    avail_index = 0
                else:
                    avail_index = 1
                edit_avail = st.selectbox("Availability", ['available', 'unavailable'], index=avail_index)
                save_clicked = st.form_submit_button("Save Changes", type='primary')
            if save_clicked:
                stripped_name = edit_name.strip()
                if not stripped_name:
                    st.warning('Item name is blank')
                elif save_menu_item({'item_name': stripped_name, 'description': edit_desc.strip(),
                            'price': edit_price, 'availability_status': edit_avail}, menu_item_id=item_id):
                    if edit_avail == "unavailable" and item.get("availability_status") == "available":
                        try:
                            users_resp = requests.get(f"{API_BASE}/user/users", params={"role_id": 1})
                            if users_resp.status_code == 200:
                                for user in users_resp.json():
                                    try:
                                        requests.post(
                                            f"{API_BASE}/menu/notifications",
                                            json={
                                                "user_id": user["user_id"],
                                                "message": f"{stripped_name} is now unavailable",
                                            },
                                        )
                                    except requests.RequestException:
                                        logger.warning("Failed to notify user %s", user.get("user_id"))
                        except requests.RequestException:
                            logger.error("Failed to fetch users for notification")
                    st.success("Menu item updated")
                    st.rerun()
                else:
                    st.error("Failed to update item")
#Delete item
with tab_delete:
    if not menu_items:
        st.info('No menu items found')
    else:
        item_map = {}
        for i in menu_items:
            if i.get('availability_status') != 'archived':
                item_map[i['item_name']] = i
        selected_name = st.selectbox("Select item", options=["select item"] + list(item_map.keys()), 
                                     label_visibility="collapsed", key='delete')
        if selected_name != "select item":
            item = item_map[selected_name]
            item_id = item['menu_item_id']
            if st.session_state.get('confirm_del_id') == item_id:
                st.warning(f'Archive {selected_name}?')
                c1, c2 = st.columns([1, 1,])
                if c1.button("Confirm", type='primary'):
                    try:
                        resp = requests.put(f"{API_BASE}/menu/menu_items/{item_id}",
                                            json={'availability_status': 'archived'})
                        if resp.status_code == 200:
                            st.success("Menu item archived")
                            st.session_state.confirm_del_id = None
                            st.rerun()
                    except requests.RequestException as e:
                        st.error(f"Request failed: {e}")
                if c2.button("Cancel"):
                    st.session_state.confirm_del_id = None
                    st.rerun()
            else:
                if st.button("Archive Item", type='primary'):
                    st.session_state.confirm_del_id = item_id
                    st.rerun()
        