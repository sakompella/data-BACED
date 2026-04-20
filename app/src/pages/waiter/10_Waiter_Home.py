import logging
logger = logging.getLogger(__name__)

import streamlit as st
from modules.nav import SideBarLinks

st.set_page_config(layout='wide')
SideBarLinks()

st.title(f"Welcome, {st.session_state['first_name']}.")
st.write('### What would you like to do today?')

if st.button('View My Orders',
             type='primary',
             use_container_width=True):
    st.switch_page('pages/waiter/11_Current_Orders.py')

if st.button('Create New Order',
             type='primary',
             use_container_width=True):
    st.switch_page('pages/waiter/12_Create_Order.py')
