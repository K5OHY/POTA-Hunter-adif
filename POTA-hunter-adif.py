import streamlit as st
import datetime

def parse_pota_log(log_text):
    adif_records = []
    lines = log_text.strip().splitlines()

    for line in lines:
        if "Hunter" in line:
            try:
                # Extracting data assuming space-separated format after "Hunter"
                parts = line.split()
                if len(parts) < 8:  # Ensure there are enough columns in the data
                    st.warning(f"Skipping line due to unexpected format: {line}")
                    continue
                
                date_time_str = parts[1] + " " + parts[2]
                station = parts[3]
                operator = parts[4]
                worked = parts[5]
                band = parts[6]
                mode = parts[7].strip('()')
                park = parts[-1]
                
                # Convert date and time to ADIF format
                dt = datetime.datetime.strptime(date_time_str, "%Y-%m-%d %H:%M")
                qso_date = dt.strftime("%Y%m%d")
                time_on = dt.strftime("%H%M")
                
                # Create ADIF record
                adif_record = f"<CALL:{len(worked)}>{worked} <BAND:{len(band)}>{band} <MODE:{len(mode)}>{mode} "
                adif_record += f"<QSO_DATE:{len(qso_date)}>{qso_date} <TIME_ON:{len(time_on)}>{time_on} "
                adif_record += f"<STATION_CALLSIGN:{len(station)}>{station} <OPERATOR:{len(operator)}>{operator} "
                adif_record += f"<MY_SIG_INFO:{len(park)}>{park} <EOR>"
                
                adif_records.append(adif_record)
            
            except Exception as e:
                st.error(f"Error processing line: {line}\nError: {str(e)}")
    
    return "\n".join(adif_records)

st.title("POTA Log to ADIF Converter")

st.write("Paste your POTA Hunter log data below:")

log_text = st.text_area("POTA Hunter Log Data", height=300)

if st.button("Convert to ADIF"):
    if log_text:
        adif_data = parse_pota_log(log_text)
        
        if adif_data:
            # Allow user to download the ADIF file
            st.download_button(
                label="Download ADIF File",
                data=adif_data,
                file_name="pota_log.adif",
                mime="text/plain"
            )
        else:
            st.error("No valid ADIF data generated. Please check your input.")
    else:
        st.error("Please paste the POTA log data to convert.")
