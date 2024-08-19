import streamlit as st
import pandas as pd
import io
from datetime import datetime, timedelta
import re

# ... (previous functions remain the same)

def detect_duplicates(log_df, adif_content):
    # Parse ADIF content
    adif_lines = adif_content.strip().split("\n")
    adif_data = []
    current_qso = {}
    
    for line in adif_lines:
        if line == "<EOH>" or line == "<eor>":
            continue
        if line.startswith("<") and line.endswith(">"):
            key, value = line[1:-1].split(":", 1)
            if key in ['CALL', 'BAND', 'MODE', 'QSO_DATE', 'TIME_ON', 'STATION_CALLSIGN']:
                current_qso[key] = value
            if key == 'STATION_CALLSIGN':
                adif_data.append(current_qso)
                current_qso = {}
    
    adif_df = pd.DataFrame(adif_data)

    log_df['QSO_TIME'] = pd.to_datetime(log_df['QSO_DATE'] + ' ' + log_df['TIME_ON'], format='%Y%m%d %H%M')
    adif_df['QSO_TIME'] = pd.to_datetime(adif_df['QSO_DATE'] + ' ' + adif_df['TIME_ON'], format='%Y%m%d %H%M')

    # Create a key for each QSO
    log_df['QSO_KEY'] = log_df.apply(lambda row: f"{row['CALL']}_{row['BAND']}_{row['MODE']}_{row['STATION_CALLSIGN']}_{row['QSO_TIME'].strftime('%Y%m%d%H%M')}", axis=1)
    adif_df['QSO_KEY'] = adif_df.apply(lambda row: f"{row['CALL']}_{row['BAND']}_{row['MODE']}_{row['STATION_CALLSIGN']}_{row['QSO_TIME'].strftime('%Y%m%d%H%M')}", axis=1)

    adif_keys = set(adif_df['QSO_KEY'])
    log_df['DUPLICATE'] = log_df['QSO_KEY'].apply(lambda key: key in adif_keys)

    def is_within_30_mins(row, adif_df):
        similar_qsos = adif_df[
            (adif_df['CALL'] == row['CALL']) &
            (adif_df['BAND'] == row['BAND']) &
            (adif_df['MODE'] == row['MODE']) &
            (adif_df['STATION_CALLSIGN'] == row['STATION_CALLSIGN'])
        ]
        if similar_qsos.empty:
            return False
        time_diff = abs(similar_qsos['QSO_TIME'] - row['QSO_TIME']).min()
        return time_diff <= timedelta(minutes=30)

    log_df['DUPLICATE'] = log_df.apply(lambda row: is_within_30_mins(row, adif_df) if not row['DUPLICATE'] else True, axis=1)

    return log_df

# ... (rest of the script remains the same)

# Streamlit App
st.title("POTA Log to ADIF Converter")

# Input for POTA log
pota_log = st.text_area("Paste your POTA log here:")

# File upload for existing ADIF
uploaded_adif = st.file_uploader("Upload your existing ADIF file", type=["adi"])

if st.button("Convert to ADIF"):
    if not pota_log:
        st.error("Please paste your POTA log.")
    else:
        log_df = parse_pota_log(pota_log)

        if uploaded_adif is not None:
            try:
                adif_content = io.StringIO(uploaded_adif.getvalue().decode("utf-8", errors='replace')).read()
                log_df = detect_duplicates(log_df, adif_content)
            except Exception as e:
                st.error(f"Error processing ADIF file: {e}")

        # Filter out duplicates
        unique_qsos = log_df[~log_df['DUPLICATE']]
        adif_output = generate_adif(unique_qsos)

        st.subheader("Generated ADIF")
        st.text_area("ADIF Content", adif_output, height=300)

        # Download button
        st.download_button(
            label="Download ADIF",
            data=adif_output,
            file_name="pota_log.adif",
            mime="text/plain"
        )

        st.write(f"Number of unique QSOs: {len(unique_qsos)}")
        st.write(f"Number of duplicates removed: {log_df['DUPLICATE'].sum()}")
