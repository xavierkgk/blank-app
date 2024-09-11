import streamlit as st
import pandas as pd
from firestore_utils import get_database

def fetch_all_sensors():
    """Fetch all sensor IDs and names from the 'sensor_configurations' collection."""
    db = get_database()
    docs = db.collection('sensor_configurations').get()

    sensors = []
    for doc in docs:
        sensor_id = doc.id
        sensor_name = doc.to_dict().get('name', f"Sensor {sensor_id}")
        sensors.append({'id': sensor_id, 'name': sensor_name})

    return sorted(sensors, key=lambda x: x['id'])

def fetch_sensor_configurations(sensor_ids):
    """Fetch the existing threshold configurations for given sensor IDs."""
    db = get_database()
    configs = {}

    for sensor_id in sensor_ids:
        doc = db.collection('sensor_configurations').document(sensor_id).get()
        if doc.exists:
            configs[sensor_id] = doc.to_dict()

    return configs

def save_thresholds(sensor_configs):
    """Save the threshold configurations and sensor information."""
    db = get_database()
    
    # Save the new thresholds and sensor details
    for sensor_id, config in sensor_configs.items():
        db.collection('sensor_configurations').document(sensor_id).set(config, merge=True)

def add_sensor(sensor_id, sensor_name):
    """Add a new sensor to the 'sensor_configurations' collection."""
    db = get_database()
    if db.collection('sensor_configurations').document(sensor_id).get().exists:
        st.error("Sensor ID already exists.")
        return

    db.collection('sensor_configurations').document(sensor_id).set({'name': sensor_name})
    st.success("Sensor added successfully!")

def delete_sensor(sensor_id):
    """Delete a sensor from the 'sensor_configurations' collection."""
    db = get_database()
    if db.collection('sensor_configurations').document(sensor_id).get().exists:
        db.collection('sensor_configurations').document(sensor_id).delete()
        st.success(f"Sensor {sensor_id} deleted successfully!")
    else:
        st.error("Sensor ID does not exist.")

def device_center():
    """Render the Device Center page for configuring device thresholds."""
    if st.session_state.get('user_role') not in ['super_admin', 'admin']:
        st.write("You have no access to the Device Center Page.")
        return

    st.title("Device Center")

    # Add sensor functionality
    st.subheader("Add New Sensor")
    new_sensor_id = st.text_input("Sensor ID", "")
    new_sensor_name = st.text_input("Sensor Name", "")
    
    if st.button("Add Sensor"):
        if new_sensor_id and new_sensor_name:
            add_sensor(new_sensor_id, new_sensor_name)
        else:
            st.error("Please provide both Sensor ID and Sensor Name.")

    # Delete sensor functionality
    st.subheader("Delete Sensor")
    delete_sensor_id = st.text_input("Sensor ID to Delete", "")
    
    if st.button("Delete Sensor"):
        if delete_sensor_id:
            delete_sensor(delete_sensor_id)
        else:
            st.error("Please provide a Sensor ID to delete.")

    # Fetch all sensors
    sensors = fetch_all_sensors()

    if sensors:
        st.subheader("Device Threshold Configuration")

        # Fetch existing configurations
        sensor_ids = [sensor['id'] for sensor in sensors]
        existing_configs = fetch_sensor_configurations(sensor_ids)

        # Prepare data for display
        data = []
        sensor_columns = ['Sensor ID', 'Sensor Name', 'Temp Min Threshold', 'Temp Max Threshold',
                          'Pressure Min Threshold', 'Pressure Max Threshold', 
                          'FlowRate Min Threshold', 'FlowRate Max Threshold']

        for sensor in sensors:
            sensor_id = sensor['id']
            sensor_name = sensor['name']
            sensor_config = existing_configs.get(sensor_id, {})
            data.append([
                sensor_id,
                sensor_name,
                sensor_config.get('Temp_min_threshold', 0),
                sensor_config.get('Temp_max_threshold', 100),
                sensor_config.get('Pressure_min_threshold', 0),
                sensor_config.get('Pressure_max_threshold', 100),
                sensor_config.get('FlowRate_min_threshold', 0),
                sensor_config.get('FlowRate_max_threshold', 100),
            ])

        df = pd.DataFrame(data, columns=sensor_columns)

        # Display instructions and the dataframe
        st.write("Update thresholds below:")
        st.data_editor(df, use_container_width=True, key="sensor_thresholds", hide_index=True)

        if st.button("Save Thresholds"):
            sensor_configs = {}
            for _, row in df.iterrows():
                sensor_id = row['Sensor ID']
                sensor_configs[sensor_id] = {
                    'name': row['Sensor Name'],
                    'Temp_min_threshold': row['Temp Min Threshold'],
                    'Temp_max_threshold': row['Temp Max Threshold'],
                    'Pressure_min_threshold': row['Pressure Min Threshold'],
                    'Pressure_max_threshold': row['Pressure Max Threshold'],
                    'FlowRate_min_threshold': row['FlowRate Min Threshold'],
                    'FlowRate_max_threshold': row['FlowRate Max Threshold'],
                }
            save_thresholds(sensor_configs)
            st.success("Thresholds and sensor names updated successfully!")
    else:
        st.write("No sensors found in the database.")