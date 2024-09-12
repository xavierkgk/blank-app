import streamlit as st
import pandas as pd
from firestore_utils import get_database

def fetch_all_devices():
    """Fetch all Device IDs and names from the 'sensor_configurations' collection."""
    db = get_database()
    docs = db.collection('sensor_configurations').get()

    devices = []
    for doc in docs:
        device_id = doc.id
        device_name = doc.to_dict().get('name', f"Device {device_id}")
        devices.append({'id': device_id, 'name': device_name})

    return sorted(devices, key=lambda x: x['id'])

def fetch_device_configurations(device_ids):
    """Fetch the existing threshold configurations for given device IDs."""
    db = get_database()
    configs = {}

    for device_id in device_ids:
        doc = db.collection('sensor_configurations').document(device_id).get()
        if doc.exists:
            configs[device_id] = doc.to_dict()

    return configs

def save_thresholds(device_configs):
    """Save the threshold configurations and device information."""
    db = get_database()
    
    # Save the new thresholds and device details
    for device_id, config in device_configs.items():
        try:
            db.collection('sensor_configurations').document(device_id).set(config, merge=True)
        except Exception as e:
            st.error(f"Failed to save configuration for device {device_id}: {e}")
            return

def add_device(device_id, device_name):
    """Add a new device to the 'sensor_configurations' collection."""
    db = get_database()
    if db.collection('sensor_configurations').document(device_id).get().exists:
        st.error("Device ID already exists.")
        return

    db.collection('sensor_configurations').document(device_id).set({'name': device_name})
    st.success("Device added successfully!")

def delete_device(device_id):
    """Delete a device from the 'sensor_configurations' collection."""
    db = get_database()
    if db.collection('sensor_configurations').document(device_id).get().exists:
        db.collection('sensor_configurations').document(device_id).delete()
        st.success(f"Device {device_id} deleted successfully!")
    else:
        st.error("Device ID does not exist.")

def device_center():
    """Render the Device Center page for configuring device thresholds."""
    if st.session_state.get('user_role') not in ['super_admin', 'admin']:
        st.write("You have no access to the Device Center Page.")
        return

    st.title("Device Center")

    # Add device functionality
    st.subheader("Add New Device")
    new_device_id = st.text_input("Device ID", "")
    new_device_name = st.text_input("Device Name", "")
    
    if st.button("Add Device"):
        if new_device_id and new_device_name:
            add_device(new_device_id, new_device_name)
        else:
            st.error("Please provide both Device ID and Device Name.")

    # Delete device functionality
    st.subheader("Delete Device")
    delete_device_id = st.text_input("Device ID to Delete", "")
    
    if st.button("Delete Device"):
        if delete_device_id:
            delete_device(delete_device_id)
        else:
            st.error("Please provide a Device ID to delete.")

    # Fetch all devices
    devices = fetch_all_devices()

    if devices:
        st.subheader("Device Threshold Configuration")

        # Fetch existing configurations
        device_ids = [device['id'] for device in devices]
        existing_configs = fetch_device_configurations(device_ids)

        # Prepare data for display
        data = []
        device_columns = ['Device ID', 'Device Name', 'Temp Min Threshold', 'Temp Max Threshold',
                          'Pressure Min Threshold', 'Pressure Max Threshold', 
                          'FlowRate Min Threshold', 'FlowRate Max Threshold']

        for device in devices:
            device_id = device['id']
            device_name = device['name']
            device_config = existing_configs.get(device_id, {})
            data.append([
                device_id,
                device_name,
                device_config.get('Temp_min_threshold', 0),
                device_config.get('Temp_max_threshold', 100),
                device_config.get('Pressure_min_threshold', 0),
                device_config.get('Pressure_max_threshold', 100),
                device_config.get('FlowRate_min_threshold', 0),
                device_config.get('FlowRate_max_threshold', 100),
            ])

        df = pd.DataFrame(data, columns=device_columns)

        # Display instructions and the dataframe
        st.write("Update thresholds below:")
        df = st.data_editor(df, use_container_width=True, key="device_thresholds", hide_index=True)

        if st.button("Save Thresholds"):
            device_configs = {}
            for _, row in df.iterrows():
                device_id = row['Device ID']
                device_configs[device_id] = {
                    'name': row['Device Name'],
                    'Temp_min_threshold': row['Temp Min Threshold'],
                    'Temp_max_threshold': row['Temp Max Threshold'],
                    'Pressure_min_threshold': row['Pressure Min Threshold'],
                    'Pressure_max_threshold': row['Pressure Max Threshold'],
                    'FlowRate_min_threshold': row['FlowRate Min Threshold'],
                    'FlowRate_max_threshold': row['FlowRate Max Threshold'],
                }

            try:
                save_thresholds(device_configs)
                st.success("Changes updated successfully!")
            except Exception as e:
                st.error(f"An error occurred: {e}")
    else:
        st.write("No devices found in the database.")
