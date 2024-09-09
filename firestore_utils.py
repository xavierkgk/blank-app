import streamlit as st
import json
import bcrypt
from google.oauth2 import service_account
from google.cloud import firestore

def initialize_firestore():
    """
    Initialize the Firestore client using credentials from Streamlit secrets.
    This function loads the Firestore JSON credentials and returns the Firestore client.
    """
    firestore_json = st.secrets["firebase"]["credentials"]
    key_dict = json.loads(firestore_json)
    
    # Create credentials and initialize Firestore client
    creds = service_account.Credentials.from_service_account_info(key_dict)
    db = firestore.Client(credentials=creds, project=key_dict["project_id"])
    return db

def get_database():
    """
    Get Firestore database client.
    This function ensures that the Firestore client is initialized once and reused.
    """
    if "db" not in st.session_state:
        st.session_state.db = initialize_firestore()
    return st.session_state.db

db = get_database()

def get_user_role(username):
    db = get_database()
    user_ref = db.collection('users').document(username)
    user = user_ref.get()
    if user.exists:
        return user.to_dict().get('role', 'user')
    else:
        return 'user'

def hash_password(password):
    """
    Hash a password using bcrypt.

    Args:
        password (str): Plain text password.

    Returns:
        str: Hashed password.
    """
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def get_users(current_user):
    """Retrieve users from Firestore based on current user's role."""
    users_ref = db.collection('users')
    docs = users_ref.stream()
    users = []
    for doc in docs:
        user_data = doc.to_dict()
        user_data['username'] = doc.id
        
        if current_user['role'] == 'super_admin':
            users.append(user_data)
        elif current_user['role'] == 'admin':
            if user_data['role'] != 'super_admin':
                users.append(user_data)
        elif current_user['role'] == 'user':
            if user_data['username'] == current_user['username']:
                users.append(user_data)
    
    return users

def update_user(username, name=None, email=None, password=None, role=None):
    """Update an existing user in Firestore."""
    user_ref = db.collection('users').document(username)
    updates = {}
    if name:
        updates['name'] = name
    if email:
        updates['email'] = email
    if password:
        updates['password'] = hash_password(password)  # Hash password if updating
    if role is not None:
        updates['role'] = role
    user_ref.update(updates)

def remove_user(username):
    """Remove a user from Firestore."""
    user_ref = db.collection('users').document(username)
    user_ref.delete()

def add_user(new_username, new_name, new_email, new_password, new_role):
    """Add a new user to Firestore."""
    user_ref = db.collection('users').document(new_username)
    user_ref.set({
        'name': new_name,
        'email': new_email,
        'password': hash_password(new_password),  # Hash the password before storing
        'role': new_role
    })


def get_device_configs():
    """Fetch device configurations from the 'device_config' collection."""
    db = get_database()
    device_configs_ref = db.collection('sensor_configurations')
    docs = device_configs_ref.stream()
    
    configs = {}
    for doc in docs:
        doc_id = doc.id  # The document ID is the sensor ID
        configs[doc_id] = doc.to_dict()  # Store the document data in the dictionary
    
    return configs


