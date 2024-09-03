import streamlit as st
from auth import login_user, logout_user
from firestore_utils import get_user_role
from streamlit_navigation_bar import st_navbar

# Importing page functions from pages folder
from pages.home import home
from pages.device_center import device_center
from pages.device_reading import device_reading  
from pages.user_management import user_management

# Initialize session state
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
    st.session_state['user_role'] = None
    st.session_state['current_user'] = {}
if 'current_page' not in st.session_state:
    st.session_state['current_page'] = 'Home'

# Role-based page navigation and access control
def handle_navigation():
    if st.session_state['current_page'] == 'Home':
        home()
    elif st.session_state['current_page'] == 'Device Center':
        device_center()
    elif st.session_state['current_page'] == 'Device Reading':  # Updated page name
        device_reading()
    elif st.session_state['current_page'] == 'User Management':
        user_management()
    elif st.session_state['current_page'] == 'Logout':
        logout_user()

# Render the UI
if st.session_state['logged_in']:
    # Create a navigation bar using the streamlit-navigation-bar library
    selected = st_navbar(
        pages=['Home', 'Device Center', 'Device Reading', 'User Management', 'Logout'],  # Added Device Reading
        key='navbar'
    )

    # Set the selected option as the current page
    st.session_state['current_page'] = selected

    # Handle navigation based on selected page
    handle_navigation()

else:
    st.title("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        user = login_user(username, password)
        if user:
            st.session_state['logged_in'] = True
            st.session_state['user_role'] = get_user_role(username)
            st.session_state['current_user'] = user  # Ensure the user data is set
            st.session_state['current_page'] = 'Home'
            st.rerun()
        else:
            st.error("Invalid login credentials.")
