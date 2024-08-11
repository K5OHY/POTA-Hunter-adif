import streamlit as st
import pandas as pd
from io import StringIO
from datetime import datetime, timedelta

# Function to parse the QRZ ADIF file into a pandas DataFrame
def parse_adif_to_df(adif_data):
    adif_lines = adif_data.strip().splitlines()
    records = []

    current_qso = {}
    for line in adif_lines:
        if line.startswith('<EOR>'):
            if current_qso:
                records.append(current_qso)
            current_qso = {}
        else:
            parts = line.split('<')
            for part in parts:
                if ':' in part:
                    key, value = part.split('>', 1)
                    key = key.split(':')[0].upper().strip()
                    current_qso[key] = value.strip().lower()

    df = pd.DataFrame(records)
    return df

# Function to parse the log data into a pandas DataFrame
def parse_log_to_df(log_data):
    records = []
    lines = log_data.strip().split("\n")

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
                    'CALL': call,
                    'QSO_DATE': qso_date,
                    'TIME_ON': time_on,
                    'BAND': band,
                    'MODE': mode,
                    'STATION_CALLSIGN': station_callsign
                }
                records.append(qso_entry)
                i += 4
            except IndexError:
                i += 1
                continue
        else:
            i += 1
    
    df = pd.DataFrame(records)
    return df

# Function to detect duplicates within a 30-minute window
def detect_duplicates(log_df, adif_df):
    log_df['QSO_TIME'] = pd.to_datetime(log_df['QSO_DATE'] + ' ' + log_df['TIME_ON'], format='%Y%m%d %H%M')
    adif_df['QSO_TIME'] = pd.to_datetime(adif_df['QSO_DATE'] + ' ' + adif_df['TIME_ON'], format='%Y%m%d %H%M')

    log_df['DUPLICATE'] = False

    for index, row in log_df.iterrows():
        potential_duplicates = adif_df[
            (adif_df['CALL'] == row['CALL']) &
            (adif_df['BAND'] == row['BAND']) &
            (adif_df['MODE'] == row['MODE']) &
            (adif_df['STATION_CALLSIGN'] == row['STATION_CALLSIGN']) &
            (abs(adif_df['QSO_TIME'] - row['QSO_TIME']) <= timedelta(minutes=30))
        ]
        
        if not potential_duplicates.empty:
            log_df.at[index, 'DUPLICATE'] = True
    
    return log_df

# Streamlit app interface
st.title("POTA Log to ADIF Converter with Advanced Duplicate Detection")

st.write("Paste your POTA hunters log data below:")

log_data = st.text_area("Hunters Log Data", height=300)

uploaded_adif = st.file_uploader("Upload your existing QRZ ADIF file", type="adi")

if st.button("Generate ADIF"):
    if log_data:
        log_df = parse_log_to_df(log_data)

        if uploaded_adif:
            try:
                adif_content = StringIO(uploaded_adif.getvalue().decode("utf-8", errors='replace')).read()
                adif_df = parse_adif_to_df(adif_content)
            except UnicodeDecodeError:
                st.error("There was an issue decoding the ADIF file. Please ensure it is encoded in UTF-8.")
                st.stop()

            # Detect and mark duplicates
            log_df = detect_duplicates(log_df, adif_df)
            
            # Filter out duplicates
            filtered_df = log_df[log_df['DUPLICATE'] == False]

            if not filtered_df.empty:
                adif_data = filtered_df.apply(lambda x: f"<CALL:{len(x['CALL'])}>{x['CALL']}<QSO_DATE:{len(x['QSO_DATE'])}>{x['QSO_DATE']}<TIME_ON:{len(x['TIME_ON'])}>{x['TIME_ON']}<BAND:{len(x['BAND'])}>{x['BAND']}<MODE:{len(x['MODE'])}>{x['MODE']}<STATION_CALLSIGN:{len(x['STATION_CALLSIGN'])}>{x['STATION_CALLSIGN']}<EOR>\n", axis=1).sum()
                
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
            st.warning("Please upload an ADIF file to check against.")
    else:
        st.warning("Please paste the log data before generating the ADIF file.")
