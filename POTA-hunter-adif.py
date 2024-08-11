import streamlit as st
import datetime
from io import StringIO

# Step 1: Parse the QRZ ADIF file and generate keys
def parse_adif(adif_data):
    existing_qsos = []
    lines = adif_data.strip().splitlines()
    current_qso = {}

    for line in lines:
        if line.startswith('<EOR>'):
            if 'CALL' in current_qso and 'QSO_DATE' in current_qso and 'TIME_ON' in current_qso:
                # Generate a unique key for each QSO
                qso_key = (
                    current_qso.get('CALL', ''),
                    current_qso.get('QSO_DATE', ''),
                    current_qso.get('TIME_ON', ''),
                    current_qso.get('BAND', ''),
                    current_qso.get('MODE', ''),
                    current_qso.get('STATION_CALLSIGN', '')
                )
                existing_qsos.append(qso_key)
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

# Step 2: Parse the log data and generate keys
def clean_and_parse_log_data(log_data):
    lines = log_data.strip().split("\n")
    parsed_data = []
    
    i = 0
    while i < len(lines):
        if len(lines[i].strip().split()) == 2 and "-" in lines[i] and ":" in lines[i]:
            try:
                date_time = lines[i].strip().split()
                qso_date = date_time[0].replace("-", "")
                time_on = date_time[1].replace(":", "")
                call = lines[i + 1].strip().lower()
                details = lines[i + 3].strip().split()

                station_callsign = details[0].strip().lower()
                band = details[1].strip().lower()
                mode = details[2].strip().replace("(", "").replace(")", "").lower()

                # Generate a unique key for each QSO
                qso_key = (
                    call,
                    qso_date,
                    time_on,
                    band,
                    mode,
                    station_callsign
                )

                parsed_data.append(qso_key)
                i += 4
            except IndexError:
                st.warning(f"Skipping entry due to unexpected format: {lines[i:i+4]}")
                i += 1
                continue
        else:
            i += 1
    
    return parsed_data

# Step 3: Check for duplicates using keys
def is_duplicate_qso(new_qso_key, existing_qsos):
    for existing_qso_key in existing_qsos:
        if new_qso_key == existing_qso_key:
            st.write(f"Duplicate found: {new_qso_key} is a duplicate of {existing_qso_key}")
            return True
    st.write(f"No duplicate found for: {new_qso_key}")
    return False

# Step 4: Simplify the ADIF conversion
def convert_to_adif(parsed_data):
    adif_records = []
    for entry in parsed_data:
        record = (
            f"<CALL:{len(entry[0])}>{entry[0]}"
            f"<QSO_DATE:{len(entry[1])}>{entry[1]}"
            f"<TIME_ON:{len(entry[2])}>{entry[2]}"
            f"<BAND:{len(entry[3])}>{entry[3]}"
            f"<MODE:{len(entry[4])}>{entry[4]}"
            f"<STATION_CALLSIGN:{len(entry[5])}>{entry[5]}"
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
        st.write("Parsed Log Data:", parsed_data)  # Verify parsing

        existing_qsos = []
        if uploaded_adif:
            try:
                adif_content = StringIO(uploaded_adif.getvalue().decode("utf-8", errors='replace')).read()
                existing_qsos = parse_adif(adif_content)
                st.write("Parsed ADIF Data:", existing_qsos)  # Verify parsing
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
