import streamlit as st

def clean_and_parse_log_data(log_data):
    # Split the log into individual lines
    lines = log_data.strip().split("\n")
    parsed_data = []

    for line in lines:
        parts = line.split()
        if len(parts) >= 9:
            date = parts[0]
            time = parts[1].replace(":", "")
            hunter_call = parts[2]
            activator_call = parts[3]
            band = parts[4]
            mode = parts[5].replace("(", "").replace(")", "")
            state = parts[6]
            pota_id = parts[7]
            location = " ".join(parts[8:])
            
            entry = {
                "date": date,
                "time": time,
                "hunter_call": hunter_call,
                "activator_call": activator_call,
                "band": band,
                "mode": mode,
                "state": state,
                "pota_id": pota_id,
                "location": location,
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
        record += "<EOR>\n"
        adif_records.append(record)
    return "\n".join(adif_records)

# Streamlit app interface
st.title("POTA Log to ADIF Converter")

st.write("Paste your POTA hunters log data below:")

log_data = st.text_area("Hunters Log Data")

if st.button("Generate ADIF"):
    if log_data:
        parsed_data = clean_and_parse_log_data(log_data)
        if parsed_data:  # Check if any data was parsed successfully
            adif_data = convert_to_adif(parsed_data)
            st.text_area("ADIF Output", adif_data, height=300)

            st.download_button(
                label="Download ADIF",
                data=adif_data,
                file_name="pota_log.adi",
                mime="text/plain",
            )
        else:
            st.warning("No valid log data was found. Please check the format of your log.")
    else:
        st.warning("Please paste the log data before generating the ADIF file.")
