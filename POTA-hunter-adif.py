import streamlit as st

# Function to parse a single line from the hunter log
def parse_hunter_log_line(line):
    # Split the line by whitespace and tabs
    parts = line.strip().split('\t')
    
    if len(parts) >= 8:
        qso_date, qso_time = parts[0].split()
        station = parts[1]  # Station
        operator = parts[2]  # Operator
        worked = parts[3]  # Worked station
        band = parts[4]  # Band
        mode = parts[5].split()[0]  # Mode (only first part before space)
        location = parts[6]  # Location
        park = parts[7]  # Park
        
        # Create a comment with the location and park information
        comment = f"[POTA {location} {park}]"

        # Return a dictionary representing the ADIF fields
        return {
            "qso_date": qso_date.replace("-", ""),
            "qso_time": qso_time.replace(":", ""),
            "station": station,
            "operator": operator,
            "worked": worked,
            "band": band.lower(),
            "mode": mode.upper(),
            "comment": comment
        }
    else:
        return None

# Function to convert parsed QSOs to ADIF format
def convert_to_adif(parsed_qsos):
    adif_entries = []
    for qso in parsed_qsos:
        adif_entry = (
            f"<qso_date:{len(qso['qso_date'])}>{qso['qso_date']} "
            f"<time_on:{len(qso['qso_time'])}>{qso['qso_time']} "
            f"<call:{len(qso['worked'])}>{qso['worked']} "
            f"<band:{len(qso['band'])}>{qso['band']} "
            f"<mode:{len(qso['mode'])}>{qso['mode']} "
            f"<comment:{len(qso['comment'])}>{qso['comment']} "
            "<eor>"
        )
        adif_entries.append(adif_entry)
    return adif_entries

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

    # Convert parsed QSOs to ADIF
    if parsed_qsos:
        final_adif = "\n".join(convert_to_adif(parsed_qsos))
        st.text_area("Generated ADIF File", final_adif)
    else:
        st.write("No valid QSOs found in the pasted log.")
