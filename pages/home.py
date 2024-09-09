import streamlit as st
import pandas as pd
from datetime import datetime, timezone
from firestore_utils import get_database, get_device_configs

def fetch_latest_readings(collection_name):
    """Fetch the latest reading for each sensor from Firestore and format the data."""
    db = get_database()
    docs = db.collection(collection_name).order_by('timestamp', direction='DESCENDING').get()

    data = []
    
    for doc in docs:
        record = doc.to_dict()
        timestamp = record.get('timestamp')

        # Loop over the fields to detect sensor readings
        for key, value in record.items():
            if key.startswith('Temp_') or key.startswith('Pressure_') or key.startswith('FlowRate_'):
                # Extract the sensor ID (01, 02, etc.)
                sensor_id = key.split('_')[1]
                reading_type = key.split('_')[0]  # Temp, Pressure, FlowRate, etc.
                data.append({
                    'sensorID': sensor_id,  # Only the numeric part (e.g., '01', '02')
                    'reading_type': reading_type,
                    'reading_value': value,
                    'timestamp': timestamp
                })

    # Create DataFrame and convert reading_value to numeric, coerce errors to NaN
    df = pd.DataFrame(data)
    if not df.empty:
        df['reading_value'] = pd.to_numeric(df['reading_value'], errors='coerce')

    return df if not df.empty else pd.DataFrame()

def home():
    """Render the main dashboard on the Home page."""
    st.title("IoT Dashboard Overview")

    # Fetch the device configurations and thresholds
    device_configs = get_device_configs()  # device_config collection
    collection_name = "iot_gateway_data"
    latest_df = fetch_latest_readings(collection_name)

    if not device_configs:
        st.write("No sensor configurations available.")
        return

    # Convert timestamps and format them
    if not latest_df.empty:
        latest_df['timestamp'] = pd.to_datetime(latest_df['timestamp'], utc=True)
        latest_df['timestamp'] = latest_df['timestamp'].dt.tz_convert('Asia/Singapore')
        latest_df['formatted_timestamp'] = latest_df['timestamp'].dt.strftime('%d/%m/%Y %H:%M')
        latest_df = latest_df.sort_values(by=['sensorID', 'reading_type'])

    st.header("Latest Sensor Readings")

    current_time = datetime.now(timezone.utc).astimezone()

    num_columns = 3  # Adjust based on screen width
    cols = st.columns(num_columns)

    for idx, (sensor_id, config) in enumerate(device_configs.items()):
        col = cols[idx % num_columns]  # Distribute sensors across columns
        
        name = config.get('name', f'Sensor {sensor_id}')
        temp_max_threshold = config.get('Temp_max_threshold')
        temp_min_threshold = config.get('Temp_min_threshold')
        pressure_max_threshold = config.get('Pressure_max_threshold')
        pressure_min_threshold = config.get('Pressure_min_threshold')
        flowrate_max_threshold = config.get('FlowRate_max_threshold')
        flowrate_min_threshold = config.get('FlowRate_min_threshold')
        
        device_df = latest_df[latest_df['sensorID'] == sensor_id]
        
        # Determine if the sensor should be grey (no readings)
        if device_df.empty:
            card_bg_color = '#E0E0E0'  # Grey color for no readings
            card_border_color = '#B0B0B0'
            card_shadow_color = '#A0A0A0'
        else:
            latest_timestamp = pd.to_datetime(device_df["timestamp"].max(), utc=True)
            outdated_class = (current_time - latest_timestamp).total_seconds() > 600

            card_bg_color = '#FFFFFF' if not outdated_class else '#F2F2F2'
            card_border_color = '#E0E0E0'
            card_shadow_color = '#B0B0B0'

        with col:
            st.markdown(f"""
                <div style="
                    border: 1px solid {card_border_color};
                    border-radius: 10px;
                    padding: 20px;
                    background-color: {card_bg_color};
                    box-shadow: 0 4px 6px {card_shadow_color};
                    margin: 10px;
                    overflow: hidden;
                    transition: background-color 0.3s, box-shadow 0.3s;
                ">
                    <div style="
                        text-align: center;
                        margin-bottom: 15px;
                        border-bottom: 1px solid {card_border_color};
                        padding-bottom: 10px;
                        font-size: 1.25em;
                        color: #333;
                        font-weight: bold;
                        text-transform: uppercase;
                    ">
                        {name}
                        <p style="font-size: 0.85em; color: #888;"><strong>Last Update:</strong> {device_df['formatted_timestamp'].max() if not device_df.empty else 'No data'}</p>
                    </div>
                    <div style="
                        display: flex;
                        flex-direction: column;
                        gap: 12px;
                        flex-grow: 1;
                    ">
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
                    elif reading_type == 'FlowRate':
                        threshold_max = flowrate_max_threshold
                        threshold_min = flowrate_min_threshold

                    is_alert_max = threshold_max is not None and reading_value > threshold_max
                    is_alert_min = threshold_min is not None and reading_value < threshold_min
                    alert_color = '#FFEBEE' if is_alert_max else '#E0F7FA' if is_alert_min else '#F5F5F5'
                    alert_text = 'Alert! Exceeds threshold.' if is_alert_max else 'Warning! Below threshold.' if is_alert_min else ''
                    alert_icon = '🔔' if alert_text else ''

                    st.markdown(f"""
                        <div style="
                            background-color: {alert_color};
                            border-radius: 8px;
                            padding: 12px;
                            text-align: center;
                            transition: background-color 0.3s;
                            border: 1px solid {card_border_color};
                            font-size: 1em;
                            display: flex;
                            justify-content: space-between;
                            align-items: center;
                            box-shadow: 0 2px 4px {card_shadow_color};
                        ">
                            <p style="margin: 0; font-weight: bold;">{reading_type}:</p>
                            <p style="margin: 0;">{reading_value}</p>
                            <div style="
                                position: relative;
                                display: inline-block;
                            ">
                                <span style="
                                    font-size: 1.2em;
                                    cursor: pointer;
                                ">{alert_icon}</span>
                                <div style="
                                    visibility: hidden;
                                    width: 200px;
                                    background-color: #333;
                                    color: #fff;
                                    text-align: center;
                                    border-radius: 6px;
                                    padding: 5px 0;
                                    position: absolute;
                                    z-index: 1;
                                    bottom: 125%;
                                    left: 50%;
                                    margin-left: -100px;
                                    opacity: 0;
                                    transition: opacity 0.3s;
                                    white-space: nowrap;
                                ">
                                    {alert_text}
                                </div>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
                else:
                    # Display placeholder for missing readings
                    st.markdown(f"""
                        <div style="
                            background-color: #F5F5F5;
                            border-radius: 8px;
                            padding: 12px;
                            text-align: center;
                            border: 1px solid {card_border_color};
                            font-size: 1em;
                            display: flex;
                            justify-content: space-between;
                            align-items: center;
                            box-shadow: 0 2px 4px {card_shadow_color};
                        ">
                            <p style="margin: 0; font-weight: bold;">{reading_type}:</p>
                            <p style="margin: 0;">No data available</p>
                        </div>
                    """, unsafe_allow_html=True)
            
            st.markdown("""
                <style>
                    .tooltip:hover .tooltiptext {{
                        visibility: visible;
                        opacity: 1;
                    }}
                </style>
            """, unsafe_allow_html=True)
            
            st.markdown("</div></div>", unsafe_allow_html=True)


