import streamlit as st
from datetime import datetime, timedelta

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
            current_qso['BAND'] = line.split('>')[1].strip()
        elif line.startswith('<mode:'):
            current_qso['MODE'] = line.split('>')[1].strip()
        elif line.startswith('<qso_date:'):
            current_qso['QSO_DATE'] = line.split('>')[1].strip()
        elif line.startswith('<time_on:'):
            current_qso['TIME_ON'] = line.split('>')[1].strip()

    return existing_qsos

def is_duplicate(new_qso, existing_qsos):
    try:
        new_time = datetime.strptime(new_qso['QSO_DATE'] + new_qso['TIME_ON'], '%Y%m%d%H%M')
    except ValueError as e:
        st.error(f"Error parsing date and time for QSO: {new_qso['CALL']} - {e}")
        return False

    for qso in existing_qsos:
        if (qso['CALL'] == new_qso['CALL'] and 
            qso['BAND'] == new_qso['BAND'] and 
            qso['MODE'] == new_qso['MODE']):
            try:
                existing_time = datetime.strptime(qso['QSO_DATE'] + qso['TIME_ON'], '%Y%m%d%H%M')
                time_diff = abs((new_time - existing_time).total_seconds())
                if time_diff <= 600:  # 10 minutes
                    return True
            except ValueError as e:
                st.error(f"Error parsing date and time for existing QSO: {qso['CALL']} - {e}")
                continue
    return False

def filter_duplicates(parsed_data, existing_qsos):
    unique_qsos = [qso for qso in parsed_data if not is_duplicate(qso, existing_qsos)]
    return unique_qsos

def convert_to_adif(parsed_data):
    adif_lines = []
    for qso in parsed_data:
        adif_lines.append(f"<call:{len(qso['CALL'])}>{qso['CALL']} <qso_date:{len(qso['QSO_DATE'])}>{qso['QSO_DATE']} <time_on:{len(qso['TIME_ON'])}>{qso['TIME_ON']} <band:{len(qso['BAND'])}>{qso['BAND']} <mode:{len(qso['MODE'])}>{qso['MODE']} <station_callsign:{len(qso['STATION_CALLSIGN'])}>{qso['STATION_CALLSIGN']} <comment:{len(qso['COMMENT'])}>{qso['COMMENT']} <eor>")
    return '\n'.join(adif_lines)

# Streamlit App
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
            parts = line.split()
            if len(parts) > 8:  # Ensure that the line has the necessary parts
                try:
                    date = parts[0]
                    time = parts[1]
                    call = parts[2]
                    station_callsign = parts[4]
                    band = parts[5]
                    mode = parts[6].split('(')[0].strip()
                    location = parts[7]
                    park = parts[8]
                    comment = ' '.join(parts[9:])
                    
                    qso_data = {
                        'CALL': call,
                        'QSO_DATE': date.replace('-', ''),
                        'TIME_ON': time.replace(':', ''),
                        'BAND': band.lower(),
                        'MODE': mode,
                        'STATION_CALLSIGN': station_callsign,
                        'COMMENT': f"[POTA {park} {location}] {comment}"
                    }
                    parsed_data.append(qso_data)
                except IndexError as e:
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
