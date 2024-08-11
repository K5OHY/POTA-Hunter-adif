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

# Function to check if a QSO is a duplicate
def is_duplicate_qso(new_qso, existing_qsos):
    try:
        new_time = datetime.datetime.strptime(f"{new_qso['qso_date']} {new_qso['time_on']}", "%Y%m%d %H%M")
    except ValueError as e:
        st.write(f"Error parsing new QSO time: {e}")
        return False

    for existing_qso in existing_qsos:
        try:
            existing_time = datetime.datetime.strptime(f"{existing_qso['qso_date']} {existing_qso['time_on']}", "%Y%m%d %H%M")
        except ValueError as e:
            st.write(f"Error parsing existing QSO time: {e}")
            continue

        if (
            new_qso['call'] == existing_qso['call'] and
            new_qso['band'] == existing_qso['band'] and
            new_qso['mode'] == existing_qso['mode']
        ):
            time_difference = abs((new_time - existing_time).total_seconds())
            if time_difference <= 1200:  # within 20 minutes
                st.write(f"Duplicate found: {new_qso}")
                return True

    return False

# Function to convert the parsed data into ADIF format
def convert_to_adif(parsed_data):
    adif_records = []
    for entry in parsed_data:
        record = (
            f"<CALL:{len(entry['call'])}>{entry['call']}"
            f"<QSO_DATE:{len(entry['qso_date'])}>{entry['qso_date']}"
            f"<TIME_ON:{len(entry['time_on'])}>{entry['time_on']}"
            f"<BAND:{len(entry['band'])}>{entry['band']}"
            f"<MODE:{len(entry['mode'])}>{entry['mode']}"
            f"<STATION_CALLSIGN:{len(entry['station_callsign'])}>{entry['station_callsign']}"
        )
        record += "<EOR>\n"
        adif_records.append(record)
    return "\n".join(adif_records)

# Streamlit app interface
st.title("POTA Log to ADIF Converter with Duplicate Removal")

st.write("Paste your POTA hunters log data below:")

log_data = st.text_area("Hunters Log Data", height=300)

uploaded_adif = st.file_uploader("Upload your existing QRZ ADIF file", type="adi")

if st.button("Generate ADIF"):
    if log_data:
        parsed_data = clean_and_parse_log_data(log_data)

        existing_qsos = []
        if uploaded_adif:
            try:
                adif_content = StringIO(uploaded_adif.getvalue().decode("utf-8", errors='replace')).read()
                existing_qsos = parse_adif(adif_content)
            except UnicodeDecodeError:
                st.error("There was an issue decoding the ADIF file. Please ensure it is encoded in UTF-8.")
                st.stop()
        
        # Filter out duplicates
        filtered_data = [
            qso for qso in parsed_data if not is_duplicate_qso(qso, existing_qsos)
        ]
        
        if filtered_data:  # Check if any data was parsed successfully
            adif_data = convert_to_adif(filtered_data)
            st.text_area("ADIF Output", adif_data, height=300)

            st.download_button(
                label="Download ADIF",
                data=adif_data,
                file_name="pota_log_filtered.adi",
                mime="text/plain",
            )
        else:
            st.warning("No valid log data was found or all were duplicates.")
    else:
        st.warning("Please paste the log data before generating the ADIF file.")
