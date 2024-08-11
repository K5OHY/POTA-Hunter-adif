import streamlit as st
from datetime import datetime

# Parsing the ADIF file to extract necessary fields
def parse_adif_file(adif_content):
    existing_qsos = []
    adif_lines = adif_content.splitlines()
    current_qso = {}

    for line in adif_lines:
        if line.startswith('<eor>'):
            if current_qso and all(k in current_qso for k in ['CALL', 'BAND', 'QSO_DATE', 'TIME_ON']):
                existing_qsos.append(current_qso)
            current_qso = {}
        elif line.startswith('<call:'):
            current_qso['CALL'] = line.split('>')[1].strip()
        elif line.startswith('<band:'):
            current_qso['BAND'] = line.split('>')[1].strip().lower()
        elif line.startswith('<qso_date:'):
            current_qso['QSO_DATE'] = line.split('>')[1].strip()
        elif line.startswith('<time_on:'):
            current_qso['TIME_ON'] = line.split('>')[1].strip()

    if current_qso and all(k in current_qso for k in ['CALL', 'BAND', 'QSO_DATE', 'TIME_ON']):
        existing_qsos.append(current_qso)  # Add the last QSO if not followed by <eor>

    st.write(f"Parsed {len(existing_qsos)} QSOs from the ADIF file.")
    return existing_qsos

# Convert the Hunter Log into ADIF format
def convert_hunter_log_to_adif(hunter_log_lines):
    adif_data = []
    for line in hunter_log_lines:
        # Split by tabs or multiple spaces
        parts = [p for p in line.split() if p.strip()]
        if len(parts) >= 8:
            try:
                # Parse Date/Time
                datetime_str = parts[0] + ' ' + parts[1]
                datetime_obj = datetime.strptime(datetime_str, '%Y-%m-%d %H:%M')
                date = datetime_obj.strftime('%Y%m%d')
                time = datetime_obj.strftime('%H%M')

                # Extract necessary fields
                worked_call = parts[3].strip()  # Worked call sign
                band = parts[4].strip().lower()  # Band

                # Create ADIF QSO entry
                adif_qso = (
                    f"<call:{len(worked_call)}>{worked_call} "
                    f"<qso_date:{len(date)}>{date} "
                    f"<time_on:{len(time)}>{time} "
                    f"<band:{len(band)}>{band} <eor>"
                )
                adif_data.append(adif_qso)
            except (IndexError, ValueError) as e:
                st.error(f"Error parsing line: {line} - {e}")
                continue

    st.write(f"Converted {len(adif_data)} QSOs to ADIF format.")
    return adif_data

# Filter out duplicates from the parsed data
def filter_duplicates(parsed_data, existing_qsos):
    unique_qsos = []
    for qso in parsed_data:
        if not is_duplicate(qso, existing_qsos):
            unique_qsos.append(qso)
    st.write(f"Filtered out {len(parsed_data) - len(unique_qsos)} duplicates.")
    return unique_qsos

# Check if a new QSO is a duplicate based on time, call, and band
def is_duplicate(new_qso, existing_qsos):
    try:
        new_time_on = datetime.strptime(new_qso['QSO_DATE'] + new_qso['TIME_ON'], '%Y%m%d%H%M')
    except ValueError as e:
        st.error(f"Error parsing date and time for QSO: {new_qso['CALL']} - {e}")
        return False

    for qso in existing_qsos:
        if (qso['CALL'] == new_qso['CALL'] and 
            qso['BAND'] == new_qso['BAND'] and
            qso['QSO_DATE'] == new_qso['QSO_DATE']):
            try:
                existing_time_on = datetime.strptime(qso['QSO_DATE'] + qso['TIME_ON'], '%Y%m%d%H%M')
                time_diff = abs((new_time_on - existing_time_on).total_seconds())
                if time_diff <= 600:
                    st.write(f"Duplicate found: {new_qso['CALL']} on {new_qso['BAND']} at {new_qso['QSO_DATE']} {new_qso['TIME_ON']}")
                    return True
            except ValueError as e:
                st.error(f"Error parsing date and time for existing QSO: {qso['CALL']} - {e}")
                continue
    return False

# Convert the parsed data to ADIF format
def convert_to_adif(parsed_data):
    adif_lines = []
    for qso in parsed_data:
        adif_lines.append(f"<call:{len(qso['CALL'])}>{qso['CALL']} <qso_date:{len(qso['QSO_DATE'])}>{qso['QSO_DATE']} <time_on:{len(qso['TIME_ON'])}>{qso['TIME_ON']} <band:{len(qso['BAND'])}>{qso['BAND']} <eor>")
    return '\n'.join(adif_lines)

# Streamlit App Interface
st.title("POTA Hunter ADIF Converter with Duplicate Check")

uploaded_adif = st.file_uploader("Upload your existing ADIF log", type=["adi", "adif"])
new_hunter_log = st.text_area("Paste your POTA Hunter Log")

if st.button("Convert to ADIF"):
    if uploaded_adif is not None:
        adif_content = uploaded_adif.read().decode("utf-8")
        existing_qsos = parse_adif_file(adif_content)
        
        # Clean and filter out unnecessary text from the Hunter Log
        hunter_log_lines = [line for line in new_hunter_log.splitlines() if '\t' in line]  # Only keep lines with tabs, which are QSOs
        
        # Convert Hunter Log to ADIF format
        hunter_adif_data = convert_hunter_log_to_adif(hunter_log_lines)
        
        # Parse the newly converted Hunter Log ADIF data
        parsed_data = parse_adif_file('\n'.join(hunter_adif_data))
        
        unique_qsos = filter_duplicates(parsed_data, existing_qsos)
        
        if unique_qsos:
            adif_result = convert_to_adif(unique_qsos)
            st.download_button("Download ADIF", data=adif_result, file_name="pota_log.adif")
        else:
            st.write("No new QSOs found after filtering duplicates.")
    else:
        st.write("Please upload an existing ADIF log.")
