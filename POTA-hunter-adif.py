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
                location = details[3].strip().upper()
                pota_ref = details[4].strip()
                park_name = " ".join(details[5:])
                state = location.split("-")[-1] if location.startswith("US-") else ""

                entry = {
                    "qso_date": qso_date,
                    "time_on": time_on,
                    "call": call,
                    "station_callsign": station_callsign,
                    "band": band,
                    "mode": mode,
                    "state": state,
                    "comment": f"[POTA {pota_ref} {park_name}]",
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
        if (new_qso['call'] == existing_qso.get('CALL') and
            new_qso['qso_date'] == existing_qso.get('QSO_DATE') and
            new_qso['band'] == existing_qso.get('BAND') and
            new_qso['mode'] == existing_qso.get('MODE')):
            
            existing_time = datetime.datetime.strptime(f"{existing_qso['QSO_DATE']} {existing_qso['TIME_ON']}", "%Y%m%d %H%M")
            time_difference = abs((new_time - existing_time).total_seconds())
            
            st.write(f"Comparing with: {existing_qso}")
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
        if entry['state']:
            record += f"<STATE:{len(entry['state'])}>{entry['state']}"
        record += f"<COMMENT:{len(entry['comment'])}>{entry['comment']}"
        record += "<EOR>\
