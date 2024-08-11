import streamlit as st
import datetime
from io import StringIO

# Function to parse the QRZ ADIF file and generate a list of QSOs with relevant data
def parse_adif(adif_data):
    existing_qsos = []
    lines = adif_data.strip().splitlines()
    current_qso = {}

    for line in lines:
        if line.startswith('<EOR>'):
            if 'CALL' in current_qso and 'QSO_DATE' in current_qso and 'TIME_ON' in current_qso:
                qso_entry = {
                    'call': current_qso.get('CALL', '').strip().lower(),
                    'qso_date': current_qso.get('QSO_DATE', '').strip(),
                    'time_on': current_qso.get('TIME_ON', '').strip(),
                    'band': current_qso.get('BAND', '').strip().lower(),
                    'mode': current_qso.get('MODE', '').strip().lower()
                }
                existing_qsos.append(qso_entry)
            current_qso = {}
        else:
            parts = line.split('<')
            for part in parts:
                if ':' in part:
                    key_value = part.split('>', 1)
                    if len(key_value) == 2:
                        key, value = key_value
                        key = key.split(':')[0].strip().upper()
                        current_qso[key] = value.strip().lower()

    return existing_qsos

# Function to parse the log data and generate a list of QSOs with relevant data
def clean_and_parse_log_data(log_data):
    lines = log_data.strip().split("\n")
    parsed_data = []

    i = 0
    while i < len(lines):
        if len(lines[i].strip().split()) == 2 and "-" in lines[i] and ":" in lines[i]:
            try:
                date_time = lines[i].strip().split()
                qso_date = date_time[0].replace("-", "").strip()
                time_on = date_time[1].replace(":", "").strip()
                call = lines[i + 1].strip().lower()
                details = lines[i + 3].strip().split()

                station_callsign = details[0].strip().lower()
                band = details[1].strip().lower()
                mode = details[2].strip().replace("(", "").replace(")", "").lower()

                qso_entry = {
                    'call': call,
                    'qso_date': qso_date,
                    'time_on': time_on,
                    'band': band,
                    'mode': mode,
                    'station_callsign': station_callsign
                }

                parsed_data.append(qso_entry)
                i += 4
            except IndexError:
                st.warning(f"Skipping entry due to unexpected format: {lines[i:i+4]}")
                i += 1
                continue
        else:
            i += 1
    
    return parsed_data

# Streamlit app interface for testing the parsing
st.title("POTA Log to ADIF Converter - Parsing Test")

st.write("Paste your POTA hunters log data below:")

log_data = st.text_area("Hunters Log Data", height=300)

uploaded_adif = st.file_uploader("Upload your existing QRZ ADIF file", type="adi")

if st.button("Parse Data"):
    if log_data:
        parsed_data = clean_and_parse_log_data(log_data)
        st.write("Parsed Log Data:", parsed_data)  # Display parsed log data

        if uploaded_adif:
            try:
                adif_content = StringIO(uploaded_adif.getvalue().decode("utf-8", errors='replace')).read()
                existing_qsos = parse_adif(adif_content)
                st.write("Parsed ADIF Data:", existing_qsos)  # Display parsed ADIF data
            except UnicodeDecodeError:
                st.error("There was an issue decoding the ADIF file. Please ensure it is encoded in UTF-8.")
