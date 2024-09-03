import streamlit as st
from firestore_utils import get_database, update_user, remove_user, add_user

# Initialize Firestore client
db = get_database()

def get_users(current_user):
    """Retrieve users from Firestore based on the current user's role."""
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

def user_management():
    """Render the User Management page."""
    current_role = st.session_state.get('user_role', 'user')
    
    if current_role in ['admin', 'super_admin']:
        st.title("User Management")

        if current_role == 'super_admin':
            # Add User button visible only to super_admin
            if st.button("Add User"):
                st.session_state['show_add_user'] = not st.session_state.get('show_add_user', False)

            if st.session_state.get('show_add_user', False):
                st.subheader("Add New User")
                with st.form("add_user_form"):
                    new_username = st.text_input("Username")
                    new_name = st.text_input("Name")
                    new_email = st.text_input("Email")
                    new_password = st.text_input("Password", type="password")
                    new_role = st.selectbox("Role", ["admin", "user"])
                    submit_button = st.form_submit_button("Add User")
                    if submit_button:
                        add_user(new_username, new_name, new_email, new_password, new_role)
                        st.success(f"User {new_username} added successfully!")
                        st.session_state['show_add_user'] = False
                        st.rerun()  # Refresh the UI

        # Fetch and display users
        current_user = {'role': current_role}  # This should be your logged-in user's data
        users = get_users(current_user)

        # Filter out super_admin users
        filtered_users = [user for user in users if user['role'] != 'super_admin']
        
        if filtered_users:
            st.subheader("User List")
            st.write("Below is the list of users. Use the actions to edit or delete users.")

            # Table header
            col1, col2, col3, col4, col5 = st.columns([3, 2, 3, 2, 1])
            col1.write("**Name**")
            col2.write("**Username**")
            col3.write("**Email**")
            col4.write("**Role**")
            col5.write("**Actions**")

            for user in filtered_users:
                col1, col2, col3, col4, col5 = st.columns([3, 2, 3, 2, 1])
                col1.write(user['name'])
                col2.write(user['username'])
                col3.write(user['email'])
                col4.write(user['role'])

                # Add action buttons with popovers
                with col5:
                    if current_role in ['admin', 'super_admin']:
                        # Edit button
                        with st.popover("✏️", use_container_width=True):
                            st.write(f"**Edit User: {user['username']}**")
                            with st.form(f"update_user_form_{user['username']}"):
                                new_name = st.text_input("New Name", value=user['name'])
                                new_email = st.text_input("New Email", value=user['email'])
                                new_password = st.text_input("New Password", type="password")
                                new_role = st.selectbox("New Role", ["admin", "user"], index=["admin", "user"].index(user['role']))
                                submit_button = st.form_submit_button("Update User")
                                if submit_button:
                                    update_user(user['username'], new_name, new_email, new_password, new_role)
                                    st.success(f"User {user['username']} updated successfully!")
                                    st.rerun()  # Refresh the UI

                    if current_role == 'super_admin':
                        # Delete button
                        with st.popover("🗑️", use_container_width=True):
                            st.write(f"**Delete User: {user['username']}**")
                            st.write("Are you sure you want to delete this user?")
                            confirm_delete = st.checkbox(f"Confirm delete {user['username']}")
                            if confirm_delete and st.button("Delete User", key=f"delete_{user['username']}"):
                                remove_user(user['username'])
                                st.success(f"User {user['username']} removed successfully!")
                                st.rerun()  # Refresh the UI
        else:
            st.write("No users found.")
    else:
        st.write("You have no access to User Management Page.")
