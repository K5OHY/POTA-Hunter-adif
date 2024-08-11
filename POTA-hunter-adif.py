import streamlit as st
import datetime
from io import StringIO

def parse_adif(adif_data):
    existing_qsos = []
    lines = adif_data.strip().splitlines()
    current_qso = {}

    for line in lines:
        if line.startswith('<EOR>'):
            if 'CALL' in current_qso and 'QSO_DATE' in current_qso and 'TIME_ON' in current_qso:
                existing_qsos.append(current_qso)
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

                if len(details) < 5:
                    st.warning(f"Skipping entry due to incomplete details: {lines[i:i+4]}")
                    i += 4
                    continue
                
                station_callsign = details[0].strip().lower()
                band = details[1].strip().lower()
                mode = details[2].strip().replace("(", "").replace(")", "").lower()

                entry = {
                    "qso_date": qso_date,
                    "time_on": time_on,
                    "call": call,
                    "station_callsign": station_callsign,
                    "band": band,
                    "mode": mode,
                }
                parsed_data.append(entry)
                i += 4
            except IndexError:
                st.warning(f"Skipping entry due to unexpected format: {lines[i:i+4]}")
                i += 1
                continue
        else:
            i += 1
    
    return parsed_data

def is_duplicate_qso(new_qso, existing_qsos):
    new_time = datetime.datetime.strptime(f"{new_qso['qso_date']} {new_qso['time_on']}", "%Y%m%d %H%M")
    
    for existing_qso in existing_qsos:
        # Print out the field values with lengths and repr to detect subtle issues
        st.write(f"Comparing new QSO:")
        st.write(f"CALL: '{new_qso['call']}' (len: {len(new_qso['call'])}) vs '{existing_qso.get('CALL')}' (len: {len(existing_qso.get('CALL'))})")
        st.write(f"QSO_DATE: '{new_qso['qso_date']}' (len: {len(new_qso['qso_date'])}) vs '{existing_qso.get('QSO_DATE')}' (len: {len(existing_qso.get('QSO_DATE'))})")
        st.write(f"BAND: '{new_qso['band']}' (len: {len(new_qso['band'])}) vs '{existing_qso.get('BAND')}' (len: {len(existing_qso.get('BAND'))})")
        st.write(f"MODE: '{new_qso['mode']}' (len: {len(new_qso['mode'])}) vs '{existing_qso.get('MODE')}' (len: {len(existing_qso.get('MODE'))})")
        st.write(f"STATION_CALLSIGN: '{new_qso['station_callsign']}' (len: {len(new_qso['station_callsign'])}) vs '{existing_qso.get('STATION_CALLSIGN')}' (len: {len(existing_qso.get('STATION_CALLSIGN'))})")
        st.write(f"TIME_ON: '{new_qso['time_on']}' (len: {len(new_qso['time_on'])}) vs '{existing_qso.get('TIME_ON')}' (len: {len(existing_qso.get('TIME_ON'))})")

        if (new_qso['call'] == existing_qso.get('CALL') and
            new_qso['qso_date'] == existing_qso.get('QSO_DATE') and
            new_qso['band'] == existing_qso.get('BAND') and
            new_qso['mode'] == existing_qso.get('MODE') and
            new_qso['station_callsign'] == existing_qso.get('STATION_CALLSIGN')):
            
            existing_time = datetime.datetime.strptime(f"{existing_qso['QSO_DATE']} {existing_qso['TIME_ON']}", "%Y%m%d %H%M")
            time_difference = abs((new_time - existing_time).total_seconds())
            
            st.write(f"Time difference: {time_difference} seconds")

            if time_difference <= 1200:  # within 20 minutes
                st.write(f"Duplicate found: {new_qso} is a duplicate of {existing_qso}")
                return True

    st.write(f"No duplicate found for: {new_qso}")
    return False

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
