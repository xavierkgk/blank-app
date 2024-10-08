import streamlit as st
import pandas as pd
from datetime import datetime, timezone
from firestore_utils import get_database, get_device_configs
from streamlit_autorefresh import st_autorefresh

def fetch_latest_readings(collection_name):
    """Fetch the latest reading for each sensor from Firestore."""
    db = get_database()
    doc = db.collection(collection_name).document('current_reading').get()

    if doc.exists:
        record = doc.to_dict()
        timestamp = record.get('Timestamp')

        data = []
        for key, value in record.items():
            if key.startswith('Temp_') or key.startswith('Pressure_') or key.startswith('FlowRate_'):
                sensor_id = key.split('_')[1]
                reading_type = key.split('_')[0]
                data.append({
                    'sensorID': sensor_id,
                    'reading_type': reading_type,
                    'reading_value': float(value),  # Convert string to float
                    'timestamp': timestamp
                })

        df = pd.DataFrame(data)
        if not df.empty:
            # Correct format to match Firestore timestamp format
            df['timestamp'] = pd.to_datetime(df['timestamp'], format='%Y-%m-%d %H:%M')

        return df
    else:
        return pd.DataFrame()


def display_sensor_readings(latest_df, device_configs):
    """Render the sensor readings inside a container."""
    current_time = datetime.now(timezone.utc).astimezone()  # Ensure timezone-aware current time
    
    # Define CSS for flashing animations
    st.write("""
        <style>
            .flash-red { animation: flash-red 1s infinite; }
            @keyframes flash-red {
                0% { background-color: #FFCCCC; }
                50% { background-color: #FF0000; }
                100% { background-color: #FFCCCC; }
            }
            .flash-yellow { animation: flash-yellow 1s infinite; }
            @keyframes flash-yellow {
                0% { background-color: #FFFFCC; }
                50% { background-color: #FFFF00; }
                100% { background-color: #FFFFCC; }
            }
            .reading-box { padding: 12px; }
        </style>
    """, unsafe_allow_html=True)

    cols = st.columns(5)  # Adjust the number of columns if needed
    
    for i, (sensor_id, config) in enumerate(device_configs.items()):
        name = config.get('name', f'Sensor {sensor_id}')
        temp_max_threshold = config.get('Temp_max_threshold')
        temp_min_threshold = config.get('Temp_min_threshold')
        pressure_max_threshold = config.get('Pressure_max_threshold')
        pressure_min_threshold = config.get('Pressure_min_threshold')
        
        device_df = latest_df[latest_df['sensorID'] == sensor_id]

        if device_df.empty:
            card_class = ''
            last_update = 'No data'
        else:
            latest_timestamp = device_df["timestamp"].max()

            # Ensure that latest_timestamp is timezone-aware
            if pd.isna(latest_timestamp):
                last_update = 'No data'
            else:
                if latest_timestamp.tzinfo is None:
                    latest_timestamp = latest_timestamp.tz_localize('UTC')  # Localize to UTC if naive

                last_update = latest_timestamp.strftime('%d/%m/%Y %H:%M')

                # Calculate time difference in minutes
                time_diff = current_time - latest_timestamp
                minutes_diff = time_diff.total_seconds() / 60

                # Apply the flash-red class if time difference is more than 10 minutes
                if minutes_diff > 10:
                    card_class = 'flash-red'
                else:
                    card_class = ''

        col = cols[i % 5]

        with col:
            st.markdown(f"""
                <div style="border: 1px solid #E0E0E0; box-shadow: 0 4px 6px #B0B0B0; border-radius: 10px; padding: 10px; margin-bottom: 10px;" class="{card_class}">
                    <div style="text-align: center; margin-bottom: 15px; border-bottom: 1px solid #E0E0E0; padding-bottom: 10px; font-size: 1.25em; color: #333; font-weight: bold;">
                        {name}
                        <p style="font-size: 0.85em; color: #888;"><strong>Last Update:</strong> {last_update}</p>
                    </div>
                    <div style="display: flex; flex-wrap: wrap; gap: 10px;">
            """, unsafe_allow_html=True)

            for reading_type in ['Temp', 'Pressure', 'FlowRate']:
                reading_row = device_df[device_df['reading_type'] == reading_type]
                if not reading_row.empty:
                    reading_value = reading_row['reading_value'].values[0]
                    if reading_type == 'Temp':
                        threshold_max = temp_max_threshold
                        threshold_min = temp_min_threshold
                    elif reading_type == 'Pressure':
                        threshold_max = pressure_max_threshold
                        threshold_min = pressure_min_threshold

                    is_alert_max = threshold_max and reading_value > threshold_max
                    is_alert_min = threshold_min and reading_value < threshold_min
                    alert_class = 'flash-yellow' if is_alert_max or is_alert_min else ''

                    st.markdown(f"""
                        <div style="background-color: #F5F5F5; border-radius: 8px; padding: 12px; text-align: center;" class="{alert_class}">
                            <p style="margin: 0; font-weight: bold;">{reading_type}:</p>
                            <p style="margin: 0;">{reading_value}</p>
                        </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                        <div style="background-color: #F5F5F5; border-radius: 8px; padding: 12px; text-align: center;">
                            <p style="margin: 0; font-weight: bold;">{reading_type}:</p>
                            <p style="margin: 0; color: #888;">No data available</p>
                        </div>
                    """, unsafe_allow_html=True)

            st.markdown("</div></div>", unsafe_allow_html=True)


def home():
    """Render the main dashboard on the Home page."""
    st.title("IoT Dashboard Overview")

    # Fetch the device configurations and thresholds
    device_configs = get_device_configs()
    collection_name = "iot_gateway_data"

    # Auto-refresh with 30 seconds interval
    st_autorefresh(interval=30000, key="data_refresh")

    # Fetch latest readings
    latest_df = fetch_latest_readings(collection_name)
    if latest_df.empty:
        st.write("No data available.")
    else:
        latest_df['formatted_timestamp'] = latest_df['timestamp'].dt.strftime('%d/%m/%Y %H:%M:%S')

        # Display sensor readings
        display_sensor_readings(latest_df, device_configs)

