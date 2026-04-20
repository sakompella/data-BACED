import logging
logger = logging.getLogger(__name__)

import streamlit as st
from modules.nav import SideBarLinks

st.set_page_config(layout='wide')
SideBarLinks()

st.title(f"Welcome Chef, {st.session_state['first_name']}.")
st.write('### What would you like to do today?')

if st.button('View Inventory & Stock',
             type='primary',
             use_container_width=True):
    st.switch_page('pages/chef/01_Inventory.py')

if st.button('Manage Orders',
             type='primary',
             use_container_width=True):
    st.switch_page('pages/chef/02_Order_Management.py')
