import streamlit as st
import datetime

# Utility function to parse ADIF content
def parse_adif_file(adif_content):
    qsos = []
    for line in adif_content.splitlines():
        qso = {}
        if '<call:' in line.lower():
            try:
                qso['CALL'] = line.split('<call:')[1].split('>')[1].strip().upper()
            except IndexError:
                qso['CALL'] = ''
            try:
                qso['BAND'] = line.split('<band:')[1].split('>')[1].strip().lower()
            except IndexError:
                qso['BAND'] = ''
            try:
                qso['QSO_DATE'] = line.split('<qso_date:')[1].split('>')[1].strip()
            except IndexError:
                qso['QSO_DATE'] = ''
            try:
                qso['TIME_ON'] = line.split('<time_on:')[1].split('>')[1].strip()
            except IndexError:
                qso['TIME_ON'] = ''
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

# Function to parse the log data
def parse_log_data(log_data):
    parsed_data = []
    for line in log_data.splitlines():
        if "Hunter" in line or "P2P" in line:
            continue
        parts = line.split()
        if len(parts) >= 8:
            qso = {
                'DATE': parts[0],
                'TIME': parts[1].replace(':', ''),
                'STATION': parts[2],
                'WORKED': parts[4],
                'BAND': parts[5].lower(),
                'MODE': parts[6].split('(')[0],
                'STATE': parts[7],
                'PARK': ' '.join(parts[8:])
            }
            parsed_data.append(qso)
    return parsed_data

# Function to convert parsed log data to ADIF format
def convert_to_adif(parsed_data):
    adif_lines = []
    for qso in parsed_data:
        adif_lines.append(f"<call:{len(qso['STATION'])}>{qso['STATION']} <qso_date:8>{qso['DATE'].replace('-','')} <time_on:4>{qso['TIME']} <band:{len(qso['BAND'])}>{qso['BAND']} <mode:2>{qso['MODE']} <station_callsign:{len(qso['WORKED'])}>{qso['WORKED']} <comment:{len(qso['PARK'])}>[POTA {qso['STATE']} {qso['PARK']}] <eor>")
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
        new_qsos = parse_log_data(log_data)
        
        if uploaded_file is not None:
            # Compare with existing log and filter duplicates
            filtered_qsos = filter_duplicates(new_qsos, existing_qsos)
        else:
            filtered_qsos = new_qsos
        
        if filtered_qsos:
            # Convert filtered QSOs to ADIF
            adif_output = convert_to_adif(filtered_qsos)
            st.download_button("Download ADIF", data=adif_output, file_name="pota_log.adi")
        else:
            st.write("No new QSOs found after filtering duplicates.")
    else:
        st.write("Please paste your log data before converting.")
