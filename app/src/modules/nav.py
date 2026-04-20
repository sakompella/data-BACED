import streamlit as st


# ---- General ----------------------------------------------------------------

def home_nav():
    st.sidebar.page_link("Home.py", label="Home", icon="🏠")


def about_page_nav():
    st.sidebar.page_link("pages/40_About.py", label="About", icon="🧠")


# ---- Role: Chef (Armando) ---------------------------------------------------

def chef_home_nav():
    st.sidebar.page_link("pages/00_Chef_Home.py", label="Chef Home", icon="👨‍🍳")

def inventory_nav():
    st.sidebar.page_link("pages/01_Inventory.py", label="Inventory & Stock", icon="📦")

def order_management_nav():
    st.sidebar.page_link("pages/02_Order_Management.py", label="Orders", icon="📋")

def menu_management_nav():
    st.sidebar.page_link('page/03_Menu_Management.py', label="Menu Items", icon="")


# ---- Role: Waiter (Maya) ----------------------------------------------------

def waiter_home_nav():
    st.sidebar.page_link("pages/10_Waiter_Home.py", label="Waiter Home", icon="🍽️")

def current_orders_nav():
    st.sidebar.page_link("pages/11_Current_Orders.py", label="My Orders", icon="🧾")

def create_order_nav():
    st.sidebar.page_link("pages/12_Create_Order.py", label="Create Order", icon="➕")


# ---- Role: Analyst (Charles) ------------------------------------------------

def analyst_home_nav():
    st.sidebar.page_link("pages/20_Analyst_Home.py", label="Analyst Home", icon="📊")

def usage_analytics_nav():
    st.sidebar.page_link("pages/21_Usage_Analytics.py", label="Analytics", icon="📈")

def forecasting_nav():
    st.sidebar.page_link("pages/22_Forecasting.py", label="Forecasting & Suppliers", icon="🔮")


# ---- Role: Administrator (Priya) --------------------------------------------

def admin_home_nav():
    st.sidebar.page_link("pages/30_Admin_Home.py", label="Admin Home", icon="🖥️")

def users_activity_nav():
    st.sidebar.page_link("pages/31_Users_Activity.py", label="Users & Activity", icon="👥")

def system_data_nav():
    st.sidebar.page_link("pages/32_System_Data.py", label="System & Data", icon="⚙️")


# ---- Sidebar assembly -------------------------------------------------------

def SideBarLinks(show_home=False):
    """
    Renders sidebar navigation links based on the logged-in user's role.
    """
    st.sidebar.image("assets/logo.png", width=150)

    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
        st.switch_page("Home.py")

    if show_home:
        home_nav()

    if st.session_state["authenticated"]:

        if st.session_state["role"] == "chef":
            chef_home_nav()
            inventory_nav()
            order_management_nav()

        if st.session_state["role"] == "waiter":
            waiter_home_nav()
            current_orders_nav()
            create_order_nav()

        if st.session_state["role"] == "analyst":
            analyst_home_nav()
            usage_analytics_nav()
            forecasting_nav()

        if st.session_state["role"] == "administrator":
            admin_home_nav()
            users_activity_nav()
            system_data_nav()

    about_page_nav()

    if st.session_state["authenticated"]:
        if st.sidebar.button("Logout"):
            for key in ("role", "authenticated", "first_name", "user_id", "order_cart"):
                st.session_state.pop(key, None)
            st.switch_page("Home.py")
