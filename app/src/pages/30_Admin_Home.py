import logging
logger = logging.getLogger(__name__)

import streamlit as st
from modules.nav import SideBarLinks

st.set_page_config(layout='wide')
SideBarLinks()

st.title(f"Welcome, {st.session_state['first_name']}.")
st.write('### What would you like to do today?')

if st.button('Users & Activity',
             type='primary',
             use_container_width=True):
    st.switch_page('pages/31_Users_Activity.py')

if st.button('System & Data',
             type='primary',
             use_container_width=True):
    st.switch_page('pages/32_System_Data.py')
    
if st.button('Menu & Inventory Config',
             type='primary',
             use_container_width=True):
    st.switch_page('pages/33_Menu_Configuration.py')
