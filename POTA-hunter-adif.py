import streamlit as st
from datetime import datetime

# Parsing the ADIF file to extract necessary fields
def parse_adif_file(adif_content):
    existing_qsos = []
    adif_lines = adif_content.splitlines()
    current_qso = {}

    for line in adif_lines:
        if line.startswith('<eor>'):
            if current_qso:
                existing_qsos.append(current_qso)
                current_qso = {}
        elif line.startswith('<call:'):
            current_qso['CALL'] = line.split('>')[1].strip()
        elif line.startswith('<band:'):
            current_qso['BAND'] = line.split('>')[1].strip().lower()
        elif line.startswith('<qso_date:'):
            current_qso['QSO_DATE'] = line.split('>')[1].strip()
        elif line.startswith('<qso_date_off:'):
            current_qso['QSO_DATE_OFF'] = line.split('>')[1].strip()
        elif line.startswith('<time_on:'):
            current_qso['TIME_ON'] = line.split('>')[1].strip()
        elif line.startswith('<time_off:'):
            current_qso['TIME_OFF'] = line.split('>')[1].strip()

    return existing_qsos

# Check if a new QSO is a duplicate based on time, call, band, and mode
def is_duplicate(new_qso, existing_qsos):
    try:
        new_time_on = datetime.strptime(new_qso['QSO_DATE'] + new_qso['TIME_ON'], '%Y%m%d%H%M')
        new_time_off = datetime.strptime(new_qso['QSO_DATE_OFF'] + new_qso['TIME_OFF'], '%Y%m%d%H%M')
    except ValueError as e:
        st.error(f"Error parsing date and time for QSO: {new_qso['CALL']} - {e}")
        return False

    for qso in existing_qsos:
        if (qso['CALL'] == new_qso['CALL'] and 
            qso['BAND'] == new_qso['BAND']):
            try:
                existing_time_on = datetime.strptime(qso['QSO_DATE'] + qso['TIME_ON'], '%Y%m%d%H%M')
                existing_time_off = datetime.strptime(qso['QSO_DATE_OFF'] + qso['TIME_OFF'], '%Y%m%d%H%M')
                
                if (abs((new_time_on - existing_time_on).total_seconds()) <= 600 or
                    abs((new_time_off - existing_time_off).total_seconds()) <= 600):
                    return True
            except ValueError as e:
                st.error(f"Error parsing date and time for existing QSO: {qso['CALL']} - {e}")
                continue
    return False

# Filter out duplicates from the parsed data
def filter_duplicates(parsed_data, existing_qsos):
    unique_qsos = []
    for qso in parsed_data:
        if not is_duplicate(qso, existing_qsos):
            unique_qsos.append(qso)
    return unique_qsos

# Convert the parsed data to ADIF format
def convert_to_adif(parsed_data):
    adif_lines = []
    for qso in parsed_data:
        adif_lines.append(f"<call:{len(qso['CALL'])}>{qso['CALL']} <qso_date:{len(qso['QSO_DATE'])}>{qso['QSO_DATE']} <qso_date_off:{len(qso['QSO_DATE_OFF'])}>{qso['QSO_DATE_OFF']} <time_on:{len(qso['TIME_ON'])}>{qso['TIME_ON']} <time_off:{len(qso['TIME_OFF'])}>{qso['TIME_OFF']} <band:{len(qso['BAND'])}>{qso['BAND']} <eor>")
    return '\n'.join(adif_lines)

# Streamlit App Interface
st.title("POTA Hunter ADIF Converter with Duplicate Check")

uploaded_adif = st.file_uploader("Upload your existing ADIF log", type=["adi", "adif"])
new_hunter_log = st.text_area("Paste your POTA Hunter Log")

if st.button("Convert to ADIF"):
    if uploaded_adif is not None:
        adif_content = uploaded_adif.read().decode("utf-8")
        existing_qsos = parse_adif_file(adif_content)
        
        # Parsing the new Hunter Log
        hunter_log_lines = new_hunter_log.splitlines()
        parsed_data = []
        
        for line in hunter_log_lines:
            parts = line.split('\t')
            if len(parts) > 8:  # Ensure that the line has the necessary parts
                try:
                    datetime_str = parts[0].strip()
                    datetime_obj = datetime.strptime(datetime_str, '%Y-%m-%d %H:%M')
                    date = datetime_obj.strftime('%Y%m%d')
                    time = datetime_obj.strftime('%H%M')
                    
                    call = parts[2].strip()
                    station_callsign = parts[3].strip()
                    band = parts[4].strip().lower()
                    mode = parts[5].strip().split('(')[0].strip()
                    comment = ' '.join(parts[8:]).strip()
                    
                    qso_data = {
                        'CALL': call,
                        'QSO_DATE': date,
                        'QSO_DATE_OFF': date,  # Assuming the same date for off time
                        'TIME_ON': time,
                        'TIME_OFF': time,
                        'BAND': band,
                        'MODE': mode,
                        'STATION_CALLSIGN': station_callsign,
                        'COMMENT': comment
                    }
                    parsed_data.append(qso_data)
                except (IndexError, ValueError) as e:
                    st.error(f"Error parsing line: {line} - {e}")
                    continue
        
        unique_qsos = filter_duplicates(parsed_data, existing_qsos)
        
        if unique_qsos:
            adif_result = convert_to_adif(unique_qsos)
            st.download_button("Download ADIF", data=adif_result, file_name="pota_log.adif")
        else:
            st.write("No new QSOs found after filtering duplicates.")
    else:
        st.write("Please upload an existing ADIF log.")
