import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO
from datetime import datetime
from firestore_utils import get_database

# Function to fetch historical readings from Firestore
def fetch_historical_readings(collection_name, sensor_id=None):
    db = get_database()
    docs = db.collection(collection_name).get()
    
    data = []
    for doc in docs:
        record = doc.to_dict()
        timestamp = record.get('timestamp')
        if sensor_id:
            # Filter by sensor_id
            filtered = {k: v for k, v in record.items() if k.endswith(f'_{sensor_id}')}
            for key, value in filtered.items():
                reading_type = key.split('_')[0]
                data.append({
                    'sensorID': sensor_id,
                    'reading_type': reading_type,
                    'reading_value': value,
                    'timestamp': timestamp
                })
        else:
            for key, value in record.items():
                if key.startswith(('Temp_', 'Pressure_', 'FlowRate_')):
                    sensor_id = key.split('_')[1]
                    reading_type = key.split('_')[0]
                    data.append({
                        'sensorID': sensor_id,
                        'reading_type': reading_type,
                        'reading_value': value,
                        'timestamp': timestamp
                    })

    df = pd.DataFrame(data)
    if not df.empty:
        df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True).dt.tz_localize(None)
    return df

# Function to fetch device configurations from Firestore
def get_device_configs():
    db = get_database()
    docs = db.collection('sensor_configurations').get()
    
    configs = {}
    for doc in docs:
        config = doc.to_dict()
        sensor_id = doc.id
        configs[sensor_id] = config
    return configs

# Function to export data to Excel
def export_to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='Readings', index=False)
        writer.save()
    return output

# Function to export data to PDF
def export_to_pdf(df):
    from fpdf import FPDF
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    pdf.cell(200, 10, txt="Sensor Readings", ln=True, align='C')

    for index, row in df.iterrows():
        pdf.cell(200, 10, txt=f"{row['timestamp']} | Sensor {row['sensorID']} | {row['reading_type']}: {row['reading_value']}", ln=True)
    
    output = BytesIO()
    pdf.output(output)
    return output

# Streamlit app
def device_reading():
    st.title("Historical Sensor Readings")
    
    # Fetch device configurations
    device_configs = get_device_configs()
    
    # Filter by Sensor ID
    sensor_ids = ['All'] + list(device_configs.keys())
    sensor_id = st.sidebar.selectbox('Select Sensor ID', sensor_ids)
    
    # Fetch data
    collection_name = 'iot_gateway_data'  
    df = fetch_historical_readings(collection_name, sensor_id if sensor_id != 'All' else None)
    
    if df.empty:
        st.write("No data available.")
        return
    
    # Display a chart
    st.header("Sensor Readings Over Time")
    
    for reading_type in df['reading_type'].unique():
        filtered_df = df[df['reading_type'] == reading_type]
        fig = px.line(filtered_df, x='timestamp', y='reading_value', color='sensorID', title=f'{reading_type} Readings')
        st.plotly_chart(fig, use_container_width=True)
    
    # Export functionality
    st.header("Export Data")
    
    if st.button('Export to Excel'):
        excel_file = export_to_excel(df)
        st.download_button('Download Excel File', excel_file.getvalue(), file_name='sensor_readings.xlsx', mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    
    if st.button('Export to PDF'):
        pdf_file = export_to_pdf(df)
        st.download_button('Download PDF File', pdf_file.getvalue(), file_name='sensor_readings.pdf', mime='application/pdf')

if __name__ == "__main__":
    device_reading()
