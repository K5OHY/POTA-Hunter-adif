import streamlit as st
import pandas as pd
import io
from datetime import datetime, timedelta

# Function to parse the POTA log
def parse_pota_log(log_data):
    lines = log_data.strip().split("\n")
    data = []
    for i in range(0, len(lines), 4):
        if i + 3 >= len(lines) or not lines[i].strip().split() or not lines[i+1].strip():
            continue
        call, band, mode, _ = lines[i:i+4]
        data.append({
            'CALL': call.strip(),
            'BAND': band.strip(),
            'MODE': mode.strip(),
            'QSO_DATE': datetime.now().strftime('%Y%m%d'),
            'TIME_ON': '0000',  # Assuming all QSOs are at midnight for simplicity
            'STATION_CALLSIGN': 'YOUR_CALLSIGN'  # Replace with your callsign
        })
    return pd.DataFrame(data)

# Function to detect duplicates
def detect_duplicates(log_df, adif_df):
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

# Function to generate ADIF
def generate_adif(df):
    adif_lines = [
        "<EOH>",
        "<eor>"
    ]
    for _, row in df.iterrows():
        adif_lines.append(f"<CALL:{row['CALL']}>")
        adif_lines.append(f"<BAND:{row['BAND']}>")
        adif_lines.append(f"<MODE:{row['MODE']}>")
        adif_lines.append(f"<QSO_DATE:{row['QSO_DATE']}>")
        adif_lines.append(f"<TIME_ON:{row['TIME_ON']}>")
        adif_lines.append(f"<STATION_CALLSIGN:{row['STATION_CALLSIGN']}>")
        adif_lines.append("<eor>")
    return "\n".join(adif_lines)

# Streamlit App
st.title("POTA Log to ADIF Converter")

# Input for POTA log
pota_log = st.text_area("Paste your POTA log here:")

if st.button("Convert to ADIF"):
    if not pota_log:
        st.error("Please paste your POTA log.")
    else:
        log_df = parse_pota_log(pota_log)

        # File upload for existing ADIF
        uploaded_adif = st.file_uploader("Upload your existing ADIF file", type=["adi"])
        if uploaded_adif is not None:
            try:
                adif_content = io.StringIO(uploaded_adif.getvalue().decode("utf-8", errors='replace')).read()
                adif_df = pd.read_csv(io.StringIO(adif_content), sep="\n", header=None, names=["ADIF"])
                adif_df = adif_df[0].str.split(":", expand=True)
                adif_df.columns = adif_df.iloc[0]
                adif_df = adif_df[1:].reset_index(drop=True)
                log_df = detect_duplicates(log_df, adif_df)
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
