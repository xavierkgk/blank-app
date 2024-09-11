import streamlit as st
import pandas as pd
import plotly.express as px
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from io import BytesIO
from datetime import datetime
from firestore_utils import get_database

# Function to fetch historical readings from Firestore
def fetch_historical_readings(collection_name, sensor_id=None, start_date=None, end_date=None):
    db = get_database()
    docs = db.collection(collection_name).get()
    
    data = []
    for doc in docs:
        record = doc.to_dict()
        timestamp = record.get('timestamp')
        
        for key, value in record.items():
            if key.startswith(('Temp_', 'Pressure_', 'FlowRate_')):
                reading_type = key.split('_')[0]
                sensor_id_from_key = key.split('_')[1]
                
                if sensor_id and sensor_id != sensor_id_from_key:
                    continue
                
                data.append({
                    'sensorID': sensor_id_from_key,
                    'reading_type': reading_type,
                    'reading_value': value,
                    'timestamp': timestamp
                })

    df = pd.DataFrame(data)
    if not df.empty:
        df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True).dt.tz_convert('Asia/Kuala_Lumpur')
        
        if start_date and end_date:
            start_datetime = pd.to_datetime(start_date).tz_localize('Asia/Kuala_Lumpur')
            end_datetime = pd.to_datetime(end_date).tz_localize('Asia/Kuala_Lumpur')
            df = df[(df['timestamp'] >= start_datetime) & (df['timestamp'] <= end_datetime)]
            
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
    # Convert timezone-aware datetime to timezone-unaware datetime
    if df['timestamp'].dt.tz is not None:
        df['timestamp'] = df['timestamp'].dt.tz_localize(None)
    
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='Readings', index=False)
        writer.close()  # Use close() instead of save()
    return output

# Function to export data to PDF
def export_to_pdf(df):
    output = BytesIO()
    pdf = SimpleDocTemplate(output, pagesize=letter)

    # Prepare data for the table
    data = [['Timestamp', 'Sensor ID', 'Reading Type', 'Reading Value']]  # Table header
    for index, row in df.iterrows():
        data.append([
            str(row['timestamp']),
            str(row['sensorID']),
            str(row['reading_type']),
            str(row['reading_value'])
        ])

    # Create a table with data
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))

    # Build the PDF
    pdf.build([table])
    output.seek(0)  # Reset the BytesIO object to the beginning
    
    return output

# Function to plot time series data
def plot_time_series(df):
    # Ensure the timestamp column is datetime
    df['timestamp'] = pd.to_datetime(df['timestamp'])

    for reading_type in df['reading_type'].unique():
        filtered_df = df[df['reading_type'] == reading_type]

        # Sort the DataFrame by timestamp
        filtered_df = filtered_df.sort_values(by='timestamp')
        
        # Create the time series plot
        fig = px.line(
            filtered_df,
            x='timestamp',
            y='reading_value',
            color='sensorID',
            title=f'{reading_type} Readings Over Time',
            labels={'timestamp': 'Time', 'reading_value': reading_type}
        )
        
        # Customize the x-axis to ensure it's treated as a time series
        fig.update_xaxes(
            title_text='Time',
            dtick='M1',  # Display every month
            tickformat='%Y-%m-%d %H:%M:%S',  # Format date and time
            ticklabelmode='period'
        )
        
        # Customize the y-axis
        fig.update_yaxes(title_text=reading_type)

        # Update layout for better visualization
        fig.update_layout(
            xaxis_title='Time',
            yaxis_title=reading_type,
            legend_title='Sensor ID',
            title_font_size=18,
            xaxis_title_font_size=14,
            yaxis_title_font_size=14
        )
        
        # Display the plot
        st.plotly_chart(fig, use_container_width=True)
# Streamlit app
def device_reading():
    st.title("Historical Sensor Readings")
    
    # Fetch device configurations
    device_configs = get_device_configs()
    
    # Filter by Sensor ID
    sensor_ids = ['All'] + list(device_configs.keys())
    sensor_id = st.sidebar.selectbox('Select Sensor ID', sensor_ids)
    
    # Date range filter
    st.sidebar.header("Date Range Filter")
    start_date = st.sidebar.date_input('Start Date', datetime.now().date())
    end_date = st.sidebar.date_input('End Date', datetime.now().date())
    
    if start_date > end_date:
        st.sidebar.error("Error: End date must be after start date.")
        return
    
    # Fetch data
    collection_name = 'iot_gateway_data'  
    df = fetch_historical_readings(collection_name, sensor_id if sensor_id != 'All' else None, start_date, end_date)
    
    if df.empty:
        st.write("No data available.")
        return
    
    # Display time series chart
    st.header("Sensor Readings Over Time")
    plot_time_series(df)
    
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
