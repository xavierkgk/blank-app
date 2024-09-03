import streamlit as st
import pandas as pd
from firestore_utils import get_database

def fetch_all_sensors():
    """Fetch all sensor IDs from the 'device' collection."""
    db = get_database()
    docs = db.collection('device').get()
    
    sensors = []
    for doc in docs:
        sensor_id = doc.id
        sensors.append(sensor_id)
    
    return sorted(sensors)

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
    """Save the threshold configurations for multiple sensors."""
    db = get_database()
    for sensor_id, config in sensor_configs.items():
        db.collection('sensor_configurations').document(sensor_id).set(config, merge=True)

def device_center():
    """Render the Device Center page for configuring device thresholds."""
    # Check user role
    if st.session_state.get('user_role') not in ['super_admin', 'admin']:
        st.write("You have no access to the Device Center Page.")
        return

    st.title("Device Center")
    sensors = fetch_all_sensors()
    if sensors:
        st.subheader("Device Threshold Configuration")

        # Fetch existing configurations
        existing_configs = fetch_sensor_configurations(sensors)

        # Prepare data for display
        data = []
        for sensor_id in sensors:
            min_threshold = existing_configs.get(sensor_id, {}).get('min_threshold', 0)
            max_threshold = existing_configs.get(sensor_id, {}).get('max_threshold', 100)

            data.append([sensor_id, min_threshold, max_threshold])

        df = pd.DataFrame(data, columns=['Sensor ID', 'Min Threshold', 'Max Threshold'])

        # Hide the index
        st.write("Update thresholds below:")
        st.markdown(
            """
            <style>
            .dataframe {
                border-collapse: collapse;
                width: 100%;
            }
            .dataframe th, .dataframe td {
                border: 1px solid #ddd;
                padding: 8px;
                text-align: left;
            }
            .dataframe th {
                background-color: #f4f4f4;
                color: #333;
                font-weight: bold;
            }
            .dataframe tr:nth-child(even) {
                background-color: #f9f9f9;
            }
            .dataframe tr:hover {
                background-color: #e2e2e2;
            }
            .dataframe td {
                font-size: 14px;
            }
            </style>
            """,
            unsafe_allow_html=True
        )

        updated_df = st.data_editor(df, use_container_width=True, key="sensor_thresholds")

        if st.button("Save Thresholds"):
            # Prepare data for saving
            sensor_configs = {}
            for index, row in updated_df.iterrows():
                sensor_id = row['Sensor ID']
                sensor_configs[sensor_id] = {
                    'min_threshold': row['Min Threshold'],
                    'max_threshold': row['Max Threshold']
                }
            save_thresholds(sensor_configs)
            st.success("Thresholds updated successfully!")
    else:
        st.write("No sensors found in the database.")
