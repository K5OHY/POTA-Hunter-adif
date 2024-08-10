import streamlit as st

def clean_and_parse_log_data(log_data):
    lines = log_data.strip().split("\n")
    parsed_data = []
    
    i = 0
    while i < len(lines):
        # Look for a line that starts with a date and time
        if len(lines[i].strip().split()) == 2 and "-" in lines[i] and ":" in lines[i]:
            try:
                # First line with date and time
                date_time = lines[i].strip().split()
                qso_date = date_time[0].replace("-", "")
                time_on = date_time[1].replace(":", "")
                
                # Second line with the station callsign
                call = lines[i + 1].strip()
                
                # Third line with the operator's callsign (can be skipped)
                operator = lines[i + 2].strip()
                
                # Fourth line with the rest of the details
                details = lines[i + 3].strip().split()
                
                # Check if the details line has enough parts
                if len(details) < 6:
                    i += 1
                    continue
                
                station_callsign = details[0].strip()  # Your callsign (K5OHY)
                band = details[1].strip().lower()  # Band
                mode = details[2].strip().replace("(", "").replace(")", "")  # Mode
                state = details[3].split('-')[-1]  # State (e.g., IN from US-IN)
                pota_ref = details[4].strip()  # POTA reference
                park_name = " ".join(details[5:])  # Park name
                
                # Build the ADIF entry
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
                i += 4  # Move to the next entry
            except IndexError:
                # If there's any error, skip to the next line
                i += 1
                continue
        else:
            i += 1  # Move to the next line if it's not the start of a new QSO
    
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
        record += f"<STATE:{len(entry['state'])}>{entry['state']}"
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
