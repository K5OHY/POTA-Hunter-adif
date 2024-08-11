import streamlit as st
import re

# Function to parse a single line from the hunter log
def parse_hunter_log_line(line):
    # Simplified pattern to match QSO lines
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

    # Debug: Show all lines
    st.write("Lines in pasted log:")
    st.write(lines)

    # Process each line
    for line in lines:
        # Only consider lines that have a date in the expected format at the beginning
        if re.match(r"\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}", line.strip()):
            st.write(f"Processing line: {line}")
            parsed_qso = parse_hunter_log_line(line)
            if parsed_qso:
                st.write(f"Parsed QSO: {parsed_qso}")
                parsed_qsos.append(parsed_qso)
            else:
                st.write(f"Failed to parse line: {line}")
        else:
            st.write(f"Ignored non-QSO line: {line}")
    
    # Debugging: Display parsed QSOs
    if parsed_qsos:
        st.write("Parsed QSOs:")
        st.write(parsed_qsos)
    else:
        st.write("No QSOs were parsed.")

    # Convert to ADIF if QSOs were parsed
    if parsed_qsos:
        # (Convert and filter logic here, similar to before)
        final_adif = "\n".join(convert_to_adif(parsed_qsos))
        st.text_area("Generated ADIF File", final_adif, height=300)
        st.download_button("Download ADIF", final_adif, file_name="hunter_log.adif")
    else:
        st.write("No ADIF content generated.")
