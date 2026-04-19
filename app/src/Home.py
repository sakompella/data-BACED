##################################################
# This is the main/entry-point file for the
# sample application for your project
##################################################

# Set up basic logging infrastructure
import logging
logging.basicConfig(format='%(filename)s:%(lineno)s:%(levelname)s -- %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# import the main streamlit library as well
# as SideBarLinks function from src/modules folder
import streamlit as st
from modules.nav import SideBarLinks

# streamlit supports regular and wide layout (how the controls
# are organized/displayed on the screen).
st.set_page_config(layout='wide')

# If a user is at this page, we assume they are not
# authenticated.  So we change the 'authenticated' value
# in the streamlit session_state to false.
st.session_state['authenticated'] = False

# Use the SideBarLinks function from src/modules/nav.py to control
# the links displayed on the left-side panel.
# IMPORTANT: ensure src/.streamlit/config.toml sets
# showSidebarNavigation = false in the [client] section
SideBarLinks(show_home=True)

# ***************************************************
#    The major content of this page
# ***************************************************

logger.info("Loading the Home page of the app")
st.title('Welcome to RestaurantBACED')
st.write('#### Your in-house restaurant order and inventory management system')
st.write('#### Which user would you like to log in as?')

if st.button("Act as Armando, Head Chef",
             type='primary',
             use_container_width=True):
    st.session_state['authenticated'] = True
    st.session_state['role'] = 'chef'
    st.session_state['first_name'] = 'Armando'
    logger.info("Logging in as Chef Persona")
    st.switch_page('pages/00_Chef_Home.py')

if st.button('Act as Maya, Waiter',
             type='primary',
             use_container_width=True):
    st.session_state['authenticated'] = True
    st.session_state['role'] = 'waiter'
    st.session_state['first_name'] = 'Maya'
    logger.info("Logging in as Waiter Persona")
    st.switch_page('pages/10_Waiter_Home.py')

if st.button('Act as Charles, Operations Analyst',
             type='primary',
             use_container_width=True):
    st.session_state['authenticated'] = True
    st.session_state['role'] = 'analyst'
    st.session_state['first_name'] = 'Charles'
    logger.info("Logging in as Analyst Persona")
    st.switch_page('pages/20_Analyst_Home.py')

if st.button('Act as Priya, System Administrator',
             type='primary',
             use_container_width=True):
    st.session_state['authenticated'] = True
    st.session_state['role'] = 'administrator'
    st.session_state['first_name'] = 'Priya'
    logger.info("Logging in as Admin Persona")
    st.switch_page('pages/30_Admin_Home.py')
