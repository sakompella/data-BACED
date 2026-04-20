import logging
logger = logging.getLogger(__name__)

import streamlit as st
from modules.nav import SideBarLinks

st.set_page_config(layout='wide')
SideBarLinks()

st.title(f"Welcome, {st.session_state['first_name']}.")
st.write('### What would you like to do today?')

if st.button('Usage_Analytics',
             type='primary',
             use_container_width=True):
    st.switch_page('pages/21_Sales.py')

if st.button('Forecasting & Suppliers',
             type='primary',
             use_container_width=True):
    st.switch_page('pages/22_Ingredients.py')

if st.button('Suppliers',
             type='primary',
             use_container_width=True):
    st.switch_page('pages/23_Suppliers.py')