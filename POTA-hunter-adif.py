import streamlit as st
import re

def parse_log_data(log_data):
    # Split the log into individual lines
    lines = log_data.strip().split("\n")
    parsed_data = []

    # Regular expression pattern to extract the required fields
    pattern = re.compile(
        r'(?P<date>\d{4}-\d{2}-\d{2})\s+(?P<time>\d{2}:\d{2})\s+(?P<hunter_call>\S+)\s+'
        r'(?P<activator_call>\S+)\s+(?P<band>\S+)\s+(?P<mode>\S+)\s+\S+\s+(?P<state>\S+)\s+(?P<pota_id>\S+)\s+(?P<location>.+)'
    )

    # Process each line using the regular expression
    for line in lines:
        match = pattern.search(line)
        if match:
            entry = {
                "date": match.group("date"),
                "time": match.group("time").replace(":", ""),
                "hunter_call": match.group("hunter_call"),
                "activator_call": match.group("activator_call"),
                "band": match.group("band"),
                "mode": match.group("mode").replace("(", "").replace(")", ""),
                "state": match.group("state"),
                "pota_id": match.group("pota_id"),
                "location": match.group("location"),
            }
            parsed_data.append(entry)

    return parsed_data

def convert_to_adif(parsed_data):
    adif_records = []
    for entry in parsed_data:
        record = f"<CALL:{len(entry['activator_call'])}>{entry['activator_call']}"
        record += f"<QSO_DATE:{len(entry['date'])}>{entry['date'].replace('-', '')}"
        record += f"<TIME_ON:{len(entry['time'])}>{entry['time']}"
        record += f"<BAND:{len(entry['band'])}>{entry['band']}"
        record += f"<MODE:{len(entry['mode'])}>{entry['mode']}"
        record += f"<STATION_CALLSIGN:{len(entry['hunter_call'])}>{entry['hunter_call']}"
        record += f"<MY_STATE:{len(entry['state'])}>{entry['state']}"
        record += f"<MY_SIG_INFO:{len(entry['pota_id'])}>{entry['pota_id']}"
        record += "<EOR>"
        adif_records.append(record)
    return "\n".join(adif_records)

# Streamlit app interface
st.title("POTA Log to ADIF Converter")

st.write("Paste your POTA hunters log data below:")

log_data = st.text_area("Hunters Log Data")

if log_data:
    parsed_data = parse_log_data(log_data)
    adif_data = convert_to_adif(parsed_data)
    
    st.text_area("ADIF Output", adif_data)

    st.download_button(
        label="Download ADIF",
        data=adif_data,
        file_name="pota_log.adi",
        mime="text/plain",
    )
