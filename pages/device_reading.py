import streamlit as st
import pandas as pd
import altair as alt
from io import BytesIO
from firestore_utils import get_database
from fpdf import FPDF  # Import the FPDF library

def fetch_data(collection_name):
    """Fetches data from a Firestore collection.

    Args:
        collection_name (str): The name of the Firestore collection.

    Returns:
        pandas.DataFrame: A DataFrame containing the fetched data.
    """
    db = get_database()
    docs = db.collection(collection_name).get()
    data = [doc.to_dict() for doc in docs]
    return pd.DataFrame(data) if data else pd.DataFrame()

def to_csv(df):
    """Convert DataFrame to CSV format."""
    return df.to_csv(index=False).encode('utf-8')

def to_pdf(df):
    """Convert DataFrame to PDF format."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Filtered Data", ln=True, align='C')
    
    header = df.columns.tolist()
    for col in header:
        pdf.cell(40, 10, txt=col, border=1)
    pdf.ln()

    for index, row in df.iterrows():
        for value in row:
            pdf.cell(40, 10, txt=str(value), border=1)
        pdf.ln()

    return pdf.output(dest='S').encode('latin1')

def device_reading():
    """Render the Device Reading page for displaying and exporting device data."""
    st.title("📊 Regulator Dashboard")

    # Fetch data
    collection_name = "iot_gateway_reading"
    df = fetch_data(collection_name)

    # Process timestamps
    df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True)
    df['timestamp'] = df['timestamp'].dt.tz_convert('Asia/Singapore')
    df['formatted_timestamp'] = df['timestamp'].dt.strftime('%d/%m/%Y %H:%M')

    # Custom CSS for improved design and responsiveness
    st.markdown(
        """
        <style>
        /* Container styling */
        .main-container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        
        /* Metrics styling */
        .metric-container {
            display: flex;
            justify-content: space-between;
            flex-wrap: wrap;
            margin-bottom: 20px;
        }
        .metric-box {
            background-color: #f5f5f5;
            border-radius: 8px;
            padding: 15px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            margin-bottom: 10px;
            width: 23%;
            min-width: 140px;
            text-align: center;
        }
        .metric-box h3 {
            margin: 0;
            font-size: 16px;
            color: #333;
        }
        .metric-box p {
            margin: 5px 0 0;
            font-size: 24px;
            color: #007bff;
            font-weight: bold;
        }

        /* Responsive adjustments */
        @media (max-width: 1024px) {
            .metric-box {
                width: 45%;
            }
        }
        @media (max-width: 768px) {
            .metric-box {
                width: 100%;
            }
        }

        /* Button styling */
        .export-button {
            display: flex;
            gap: 10px;
            margin-top: 20px;
        }

        /* Adjust Altair chart container */
        .altair-chart-container {
            width: 100% !important;
            max-width: 100%;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    with st.container():
        st.markdown('<div class="main-container">', unsafe_allow_html=True)
        
        # Date Range Slicer with Date Selector
        st.header("📅 Filter by Date Range")
        
        # Create a date range selector similar to a slicer
        min_date = df['timestamp'].min().date()
        max_date = df['timestamp'].max().date()
        
        start_date, end_date = st.date_input(
            "Select date range",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date,
        )
        
        if isinstance(start_date, tuple):
            start_date, end_date = start_date
        else:
            start_date = min_date
            end_date = max_date
        
        # Convert to timezone-aware timestamps
        start_timestamp = pd.Timestamp(start_date).tz_localize('Asia/Singapore')
        end_timestamp = pd.Timestamp(end_date).tz_localize('Asia/Singapore') + pd.Timedelta(days=1)
        
        # Filter DataFrame based on date range
        filtered_df = df[(df['timestamp'] >= start_timestamp) & (df['timestamp'] < end_timestamp)]
        
        # Sensor ID Dropdown Filter with "All" option
        st.header("🔍 Select Sensor")
        sensor_ids = sorted(df['sensorID'].unique())
        sensor_ids_with_all = ["All"] + sensor_ids
        selected_sensor = st.selectbox("Select Sensor ID", options=sensor_ids_with_all)
        
        if selected_sensor != "All":
            filtered_df = filtered_df[filtered_df['sensorID'] == selected_sensor]
        
        if filtered_df.empty:
            st.warning("⚠️ No data available for the selected filters.")
        else:
            # Chart Section
            st.header(f"📈 Pressure Readings Over Time - {'All Sensors' if selected_sensor == 'All' else selected_sensor}")
            
            # Create a responsive Altair chart
            chart = alt.Chart(filtered_df).mark_line(point=True).encode(
                x=alt.X('timestamp:T', title='Timestamp', axis=alt.Axis(labelAngle=-45, labelFontSize=10)),
                y=alt.Y('pressure:Q', title='Pressure'),
                color=alt.Color('sensorID:N', title='Sensor ID'),
                tooltip=['formatted_timestamp', 'sensorID', 'pressure']
            ).interactive().properties(
                width='container',
                height=400,
                title='Pressure Readings Over Time'
            )
            
            st.altair_chart(chart, use_container_width=True)
            
            # Statistics Section (Moved Below the Chart)
            st.header("📊 Statistics")
            total_records = filtered_df.shape[0]
            mean_pressure = filtered_df['pressure'].mean()
            median_pressure = filtered_df['pressure'].median()
            std_pressure = filtered_df['pressure'].std()
            
            st.markdown(
                f"""
                <div class="metric-container">
                    <div class="metric-box">
                        <h3>Total Records</h3>
                        <p>{total_records}</p>
                    </div>
                    <div class="metric-box">
                        <h3>Mean Pressure</h3>
                        <p>{mean_pressure:.2f}</p>
                    </div>
                    <div class="metric-box">
                        <h3>Median Pressure</h3>
                        <p>{median_pressure:.2f}</p>
                    </div>
                    <div class="metric-box">
                        <h3>Std Deviation</h3>
                        <p>{std_pressure:.2f}</p>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
            
            # Export Data Section
            st.header("💾 Export Data")
            st.markdown('<div class="export-button">', unsafe_allow_html=True)
            
            # Export CSV Button
            csv = to_csv(filtered_df[['formatted_timestamp', 'sensorID', 'pressure']])
            st.download_button(
                label="📥 Download CSV",
                data=csv,
                file_name='filtered_data.csv',
                mime='text/csv',
                key='download-csv'
            )
            
            # Export PDF Button
            pdf = to_pdf(filtered_df[['formatted_timestamp', 'sensorID', 'pressure']])
            st.download_button(
                label="📄 Download PDF",
                data=pdf,
                file_name='filtered_data.pdf',
                mime='application/pdf',
                key='download-pdf'
            )
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
