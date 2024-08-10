import streamlit as st

def clean_and_parse_log_data(log_data):
    lines = log_data.strip().split("\n")
    parsed_data = []

    for line in lines:
        # Strip the line and split by whitespace or tab
        parts = line.strip().split()
        
        # Debug: print the line and its parts to see what is being parsed
        st.write(f"Parsing line: {line}")
        st.write(f"Parts: {parts}")
        
        # Check if the line contains the minimum number of parts to be valid
        if len(parts) >= 8:
            qso_date = parts[0].split()[0].replace("-", "")  # Extracting date
            time_on = parts[1].replace(":", "")   # Extracting time
            call = parts[1].strip()                          # Station call (the other operator)
            station_callsign = parts[3].strip()              # Your call sign
            band = parts[4].strip().lower()                  # Band, converted to lowercase
            mode = parts[5].strip().split()[0].replace("(", "").replace(")", "")  # Mode
            state = parts[6].split('-')[-1]                  # State
            pota_ref = parts[7].split()[0]                   # POTA reference
            park_name = " ".join(parts[7].split()[1:])       # Park name
            
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

    return parsed_data

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
