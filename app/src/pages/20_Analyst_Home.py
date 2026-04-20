import streamlit as st
from modules.nav import SideBarLinks
from modules.style import inject_custom_css

st.set_page_config(layout='wide')
SideBarLinks()
inject_custom_css()

st.title(f"Welcome, {st.session_state['first_name']} — Analyst")
st.caption("Monitor inventory, suppliers, and usage forecasts across the operation.")

if st.button('Sales',
             type='primary',
             use_container_width=True):
    st.switch_page('pages/21_Sales.py')

if st.button('Ingredients',
             type='primary',
             use_container_width=True):
    st.switch_page('pages/22_Ingredients.py')

if st.button('Suppliers',
             type='primary',
             use_container_width=True):
    st.switch_page('pages/23_Suppliers.py')

if st.button('Demand Planning',
             type='primary',
             use_container_width=True):
    st.switch_page('pages/24_Demand_Planning.py')
