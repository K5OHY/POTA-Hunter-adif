import streamlit as st

def clean_and_parse_log_data(log_data):
    # Split the log into individual lines
    lines = log_data.strip().split("\n")
    parsed_data = []

    for line in lines:
        parts = line.split()
        if len(parts) >= 9:
            date = parts[0].replace("-", "")
            time = parts[1].replace(":", "")
            station_call = parts[2]
            worked_call = parts[3]  # This is your call sign, K5OHY
            band = parts[4]
            mode = parts[5].replace("(", "").replace(")", "")
            location_state = parts[6]
            pota_ref = parts[7]
            park_name = " ".join(parts[8:])
            
            entry = {
                "qso_date": date,
                "time_on": time,
                "station_callsign": station_call,
                "call": worked_call,
                "band": band,
                "mode": mode,
                "my_state": location_state,
                "my_sig_info": pota_ref,
                "comment": park_name,  # This field can store additional comments like the park name
            }
            parsed_data.append(entry)

    return parsed_data

def convert_to_adif(parsed_data):
    adif_records = []
    for entry in parsed_data:
        record = f"<CALL:{len(entry['call'])}>{entry['call']}"
        record += f"<QSO_DATE:{len(entry['qso_date'])}>{entry['qso_date']}"
        record += f"<TIME_ON:{len(entry['time_on'])}>{entry['time_on']}"
        record += f"<BAND:{len(entry['band'])}>{entry['band']}"
        record += f"<MODE:{len(entry['mode'])}>{entry['mode']}"
        record += f"<STATION_CALLSIGN:{len(entry['station_callsign'])}>{entry['station_callsign']}"
        record += f"<MY_STATE:{len(entry['my_state'])}>{entry['my_state']}"
        record += f"<MY_SIG_INFO:{len(entry['my_sig_info'])}>{entry['my_sig_info']}"
        record += f"<COMMENT:{len(entry['comment'])}>{entry['comment']}"
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
