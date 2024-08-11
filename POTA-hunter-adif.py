import streamlit as st
import re
import pandas as pd

# Function to parse a single line from the hunter log
def parse_hunter_log_line(line):
    # Pattern to match lines with the QSO data
    pattern = r"(\d{4}-\d{2}-\d{2})\s+(\d{2}:\d{2})\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(.*)"
    match = re.match(pattern, line.strip())
    if match:
        qso_date = match.group(1)
        qso_time = match.group(2)
        station_worked = match.group(3)
        band = match.group(5)
        mode = match.group(6).split(" ")[0]
        comment = f"[POTA {match.group(7)} {match.group(8)}]"
        return {
            "qso_date": qso_date,
            "qso_time": qso_time,
            "station_worked": station_worked,
            "band": band,
            "mode": mode,
            "comment": comment
        }
    else:
        return None

# Function to convert parsed QSOs to ADIF format
def convert_to_adif(parsed_qsos):
    adif_qsos = []
    for qso in parsed_qsos:
        adif_entry = f"<qso_date:{len(qso['qso_date'])}>{qso['qso_date']}"
        adif_entry += f"<time_on:{len(qso['qso_time'])}>{qso['qso_time'].replace(':', '')}"
        adif_entry += f"<call:{len(qso['station_worked'])}>{qso['station_worked']}"
        adif_entry += f"<band:{len(qso['band'])}>{qso['band']}"
        adif_entry += f"<mode:{len(qso['mode'])}>{qso['mode']}"
        adif_entry += f"<comment:{len(qso['comment'])}>{qso['comment']}"
        adif_entry += "<eor>"
        adif_qsos.append(adif_entry)
    return adif_qsos

# Function to filter out duplicates
def filter_duplicates(parsed_qsos):
    filtered_qsos = []
    for qso in parsed_qsos:
        is_duplicate = False
        for existing_qso in filtered_qsos:
            if (qso['station_worked'] == existing_qso['station_worked'] and
                qso['band'] == existing_qso['band'] and
                qso['mode'] == existing_qso['mode']):
                # Time difference logic
                time_diff = abs(pd.to_datetime(f"{qso['qso_date']} {qso['qso_time']}") -
                                pd.to_datetime(f"{existing_qso['qso_date']} {existing_qso['qso_time']}"))
                if time_diff.total_seconds() / 60 <= 10:
                    is_duplicate = True
                    break
        if not is_duplicate:
            filtered_qsos.append(qso)
    return filtered_qsos

# Streamlit app layout
st.title("Hunter Log ADIF Converter")

# Initialize an empty list for parsed QSOs
parsed_qsos = []

# Text area to paste the log
pasted_log = st.text_area("Paste your hunter log here:")

# Button to process the log
if st.button("Process Log"):
    # Split pasted log into lines and parse each line
    lines = pasted_log.strip().splitlines()

    # Process each line
    for line in lines:
        parsed_qso = parse_hunter_log_line(line)
        if parsed_qso:
            parsed_qsos.append(parsed_qso)
    
    # Debugging: Display parsed QSOs
    if parsed_qsos:
        st.write("Parsed QSOs:")
        st.write(parsed_qsos)
    else:
        st.write("No QSOs were parsed.")

    # Convert to ADIF
    adif_qsos = convert_to_adif(parsed_qsos)
    
    # Filter out duplicates
    filtered_qsos = filter_duplicates(parsed_qsos)
    
    # Convert filtered QSOs to ADIF format
    final_adif = "\n".join(convert_to_adif(filtered_qsos))
    
    # Display the final ADIF content
    if final_adif:
        st.text_area("Generated ADIF File", final_adif, height=300)
        st.download_button("Download ADIF", final_adif, file_name="hunter_log.adif")
    else:
        st.write("No ADIF content generated.")
