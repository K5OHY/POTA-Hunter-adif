import streamlit as st
import datetime
from dateutil import parser as date_parser

# Utility function to parse ADIF content
def parse_adif_file(adif_content):
    # Simple parser assuming each QSO is on a separate line
    qsos = []
    for line in adif_content.splitlines():
        if '<call:' in line.lower():
            qso = {}
            qso['CALL'] = line.split('<call:')[1].split('>')[1].strip()
            qso['BAND'] = line.split('<band:')[1].split('>')[1].strip()
            qso['QSO_DATE'] = line.split('<qso_date:')[1].split('>')[1].strip()
            qso['TIME_ON'] = line.split('<time_on:')[1].split('>')[1].strip()
            qsos.append(qso)
    return qsos

# Function to determine if a new QSO is a duplicate
def is_duplicate(new_qso, existing_qsos):
    for qso in existing_qsos:
        if (qso['CALL'] == new_qso['CALL'] and
            qso['BAND'] == new_qso['BAND'] and
            qso['QSO_DATE'] == new_qso['QSO_DATE']):
            
            # Check time difference
            new_time = datetime.datetime.strptime(new_qso['TIME_ON'], '%H%M')
            existing_time = datetime.datetime.strptime(qso['TIME_ON'], '%H%M')
            time_diff = abs((new_time - existing_time).total_seconds()) / 60
            
            if time_diff <= 10:
                return True
    return False

# Function to filter out duplicate QSOs
def filter_duplicates(new_log, existing_qsos):
    filtered_qsos = []
    for qso in new_log:
        if not is_duplicate(qso, existing_qsos):
            filtered_qsos.append(qso)
    return filtered_qsos

# Function to convert parsed log data to ADIF format
def convert_to_adif(parsed_data):
    adif_lines = []
    for qso in parsed_data:
        adif_lines.append(f"<call:{len(qso['CALL'])}>{qso['CALL']} <qso_date:8>{qso['QSO_DATE']} <time_on:4>{qso['TIME_ON']} <band:{len(qso['BAND'])}>{qso['BAND']} <mode:2>{qso['MODE']} <station_callsign:{len(qso['STATION_CALLSIGN'])}>{qso['STATION_CALLSIGN']} <comment:{len(qso['COMMENT'])}>{qso['COMMENT']} <eor>")
    return '\n'.join(adif_lines)

# Main application
st.title("POTA Hunter ADIF Converter with Duplicate Check")

# Step 1: Upload Existing Log (Optional)
st.header("Upload Existing ADIF Log")
uploaded_file = st.file_uploader("Choose an ADIF file", type="adi")
existing_qsos = []

if uploaded_file is not None:
    adif_content = uploaded_file.read().decode("utf-8")
    existing_qsos = parse_adif_file(adif_content)
    st.write(f"Uploaded ADIF log contains {len(existing_qsos)} QSOs.")

# Step 2: Input New Log Data
st.header("Paste New Log Data")
log_data = st.text_area("Paste your log data here")

# Process log data and filter duplicates
if st.button("Convert to ADIF"):
    if log_data.strip():
        # Parse and clean the log data
        new_qsos = []  # Implement the function to parse the new log data
        # Compare with existing log and filter duplicates
        filtered_qsos = filter_duplicates(new_qsos, existing_qsos)
        
        if filtered_qsos:
            # Convert filtered QSOs to ADIF
            adif_output = convert_to_adif(filtered_qsos)
            st.download_button("Download ADIF", data=adif_output, file_name="pota_log.adi")
        else:
            st.write("No new QSOs found after filtering duplicates.")
    else:
        st.write("Please paste your log data before converting.")
