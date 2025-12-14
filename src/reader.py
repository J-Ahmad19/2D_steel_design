# src/reader.py
import pandas as pd
from pathlib import Path

# Updated and comprehensive mapping based on the spreadsheet image and project requirements.
EXPECTED_HEADERS = {
    "Drawing Number": "drawing_number",
    "Drawing Numbe": "drawing_number", # Slight variation possible
    "Length of Bridg": "length_m", 
    "Length of Bridge (m)": "length_m", # Added from spreadsheet image
    "Length of Bridge (L)": "length_m",
    "Width of Carriageway (m)": "carriage_width_m", # Added from spreadsheet image
    "Width of Bridg Carria": "carriage_width_m",
    "Number of Girders": "num_girders",
    "No. of Girders": "num_girders", # Shortened version
    "Number of Girders (NG)": "num_girders",
    "Length of Pier Cap (m)": "pier_cap_length_m", # Added from spreadsheet image
    "Length of Pier Cap (LPC)": "pier_cap_length_m",
    "Depth of Pier Cap C (m)": "pier_cap_depth_center_m", # Added from spreadsheet image
    "Depth of Pier Cap at Centre (DPCC)": "pier_cap_depth_center_m",
    "Depth of Pier Cap D (m)": "pier_cap_depth_end_m", # Added from spreadsheet image (assuming 'D' is meant to be 'E' or End)
    "Depth of Pier Cap at End (DPCE)": "pier_cap_depth_end_m",
    "Width of Pier Cap (m)": "pier_cap_width_m", # Added from spreadsheet image
    "Width of Pier Cap (WPC)": "pier_cap_width_m",
}

def read_excel(path: str):
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"{path} not found")
    
    # Read the data, skipping potential header rows that are empty or merged (common in spreadsheets)
    # The actual header row is assumed to be the first one with non-null values.
    df = pd.read_excel(path, engine="openpyxl", skiprows=1, header=None)
    # Re-read the header row separately
    header_df = pd.read_excel(path, engine="openpyxl", nrows=1, header=None)
    
    # Use the first non-NaN row as the actual header
    raw_headers = header_df.iloc[0].tolist() if not header_df.empty else []
    
    # If using the simplified header row from the input image (Row 1):
    # raw_headers should be the content of the first row of data shown in the image.
    if len(raw_headers) >= df.shape[1]:
        df.columns = raw_headers[:df.shape[1]]
    
    # If the sheet is simple, this block will work better:
    df = pd.read_excel(path, engine="openpyxl") 
    
    # Trim headers and map to canonical names
    col_map = {}
    for c in df.columns:
        # Normalize and strip header for mapping
        c_stripped = str(c).strip().replace(" (m)", "").replace(" (L)", "").replace(" (NG)", "") 
        c_mapped = EXPECTED_HEADERS.get(c_stripped, None)
        
        if c_mapped:
            col_map[c] = c_mapped
        else:
            # make a readable snake_case fallback
            col_map[c] = c_stripped.lower().replace(" ", "_").replace("(", "").replace(")", "").replace(".", "")

    df = df.rename(columns=col_map)
    
    # Drop rows where all canonical input parameters are NaN (e.g., empty rows at the bottom)
    canonical_cols = list(set(EXPECTED_HEADERS.values()))
    df = df.dropna(subset=[c for c in canonical_cols if c in df.columns], how='all')

    return df