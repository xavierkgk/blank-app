import streamlit as st
import pandas as pd
from datetime import datetime, timezone
from firestore_utils import get_database  # Ensure you have a function to get the Firestore database connection

def fetch_latest_readings(collection_name):
    """Fetch the latest reading for each sensor from Firestore."""
    db = get_database()
    docs = db.collection(collection_name).order_by('timestamp', direction='DESCENDING').get()
    
    data = []
    seen_sensors = set()

    for doc in docs:
        record = doc.to_dict()
        sensor_id = record.get('sensorID')
        if sensor_id not in seen_sensors:
            data.append(record)
            seen_sensors.add(sensor_id)

    return pd.DataFrame(data) if data else pd.DataFrame()

def home():
    """Render the main dashboard on the Home page."""
    st.title("IoT Dashboard Overview")

    collection_name = "iot_gateway_reading"
    latest_df = fetch_latest_readings(collection_name)

    if not latest_df.empty:
        latest_df['timestamp'] = pd.to_datetime(latest_df['timestamp'], utc=True)
        latest_df['timestamp'] = latest_df['timestamp'].dt.tz_convert('Asia/Singapore')
        latest_df['formatted_timestamp'] = latest_df['timestamp'].dt.strftime('%d/%m/%Y %H:%M')
        latest_df = latest_df.sort_values(by='sensorID')

        st.header("Latest Sensor/Regulator Readings")

        st.markdown(
            """
            <style>
            @keyframes flash {
                0% { background-color: #f1948a; }
                50% { background-color: #f5b7b1; }
                100% { background-color: #f1948a; }
            }
            .flash-red {
                animation: flash 1s infinite;
            }
            .sensor-container {
                border: 1px solid #ddd;
                border-radius: 10px;
                padding: 15px;
                background-color: #f5f5f5;
                box-shadow: 0 4px 8px rgba(0,0,0,0.1);
                width: calc(50% - 20px); /* Adjust width for 2 containers per row */
                min-height: 200px;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: space-between;
                transition: transform 0.2s;
                margin: 10px;
            }
            .sensor-container:hover {
                transform: scale(1.05);
            }
            .sensor-grid {
                display: flex;
                flex-wrap: wrap;
                justify-content: space-between;
                gap: 20px; /* Adjust gap between items */
            }
            .sensor-info, .sensor-reading {
                text-align: center;
                margin-bottom: 10px;
            }
            .sensor-reading {
                background-color: #abebc6;
                padding: 10px;
                border-radius: 5px;
                width: 100%;
            }
            @media (max-width: 768px) {
                .sensor-container {
                    width: 100%; /* Full width on smaller screens */
                }
            }
            </style>
            """,
            unsafe_allow_html=True
        )

        # Display sensor data in a grid layout
        st.markdown('<div class="sensor-grid">', unsafe_allow_html=True)
        for sensor_id, group in latest_df.groupby('sensorID'):
            for _, row in group.iterrows():
                time_diff = datetime.now(timezone.utc) - row['timestamp']
                is_outdated = time_diff.total_seconds() > 5 * 60  # 5 minutes threshold
                container_bg_color = "#f1948a" if is_outdated else "#85c1e9"
                flash_class = "flash-red" if is_outdated else ""

                st.markdown(
                    f"""
                    <div class="sensor-container {flash_class}" style="background-color: {container_bg_color};">
                        <div class="sensor-info">
                            <h3>{sensor_id}</h3>
                            <p><strong>Timestamp:</strong> {row["formatted_timestamp"]}</p>
                        </div>
                        <div class="sensor-reading">
                            <p><strong>Pressure:</strong> {row["pressure"]}</p>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.write("No data available.")
