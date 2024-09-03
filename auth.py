import streamlit as st
from google.cloud import firestore
from firestore_utils import get_database
import bcrypt

def login_user(username, password):
    """
    Authenticate user with username and password.

    Args:
        username (str): Username provided by the user.
        password (str): Password provided by the user.

    Returns:
        dict or None: User data if authentication is successful, None otherwise.
    """
    db = get_database()
    user_ref = db.collection('users').document(username)
    user_doc = user_ref.get()
    
    if user_doc.exists:
        user_data = user_doc.to_dict()
        # Verify password using bcrypt
        if bcrypt.checkpw(password.encode('utf-8'), user_data['password'].encode('utf-8')):
            return user_data
    return None

def logout_user():
    # Clear session state
    st.session_state['logged_in'] = False
    st.session_state['user_role'] = None
    st.rerun()

def hash_password(password):
    """
    Hash a password using bcrypt.

    Args:
        password (str): Plain text password.

    Returns:
        str: Hashed password.
    """
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

