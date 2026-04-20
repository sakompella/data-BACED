import logging
logger = logging.getLogger(__name__)

import streamlit as st
from modules.nav import SideBarLinks

st.set_page_config(layout='wide')
SideBarLinks()

st.title(f"Welcome, {st.session_state['first_name']}.")
st.write('### What would you like to do today?')

if st.button('Usage & Inventory Analytics',
             type='primary',
             use_container_width=True):
    st.switch_page('pages/21_Usage_Analytics.py')

if st.button('Forecasting & Suppliers',
             type='primary',
             use_container_width=True):
    st.switch_page('pages/22_Forecasting.py')
