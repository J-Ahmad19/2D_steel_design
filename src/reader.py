import pandas as pd
from pathlib import Path

# Mapping user headers (loose) to code keys (strict)
HEADER_MAP = {
    # Drawing Info
    "drawing_number": ["drawing number", "drawing no", "drg no"],
    
    # Bridge Dimensions
    "length_m": ["length of bridge (l)", "length of bridge", "length (m)"],
    "carriage_width_m": ["width of carriageway (w)", "width of carriageway", "carriageway width"],
    "depth_mm": ["depth of the bridge girder (d)", "depth of girder", "depth (mm)"],
    "num_girders": ["number of girder (ng)", "number of girders", "no. of girders"],
    
    # Pier Dimensions
    "pier_cap_length_m": ["length of pier cap (lpc)", "length of pier cap"],
    "pier_cap_depth_center_m": ["depth of pier cap at centre (dpcc)", "depth at centre"],
    "pier_cap_depth_end_m": ["depth of pier cap at end (dpce)", "depth at end"],
    "pier_cap_width_m": ["width of pier cap (wpc)", "width of pier cap"]
}

def normalize_header(h):
    """Cleans a header string for comparison."""
    return str(h).lower().strip().replace("\n", " ").replace("  ", " ")

def get_mapped_columns(df_columns):
    """Creates a rename dictionary for pandas."""
    rename_dict = {}
    for col in df_columns:
        norm_col = normalize_header(col)
        matched = False
        for key, aliases in HEADER_MAP.items():
            if norm_col == key or any(alias in norm_col for alias in aliases):
                rename_dict[col] = key
                matched = True
                break
        # If no match found, keep original (or drop later)
    return rename_dict

def read_excel(path_str):
    """Reads Excel and returns a clean list of dicts."""
    p = Path(path_str)
    if not p.exists():
        raise FileNotFoundError(f"Input file not found at {p}")
        
    # Read Excel (assume header is in first non-empty row)
    df = pd.read_excel(p, header=0)
    
    # Apply mapping
    rename_map = get_mapped_columns(df.columns)
    df = df.rename(columns=rename_map)
    
    # Filter for required keys only
    valid_keys = HEADER_MAP.keys()
    filtered_df = df[df.columns.intersection(valid_keys)]
    
    # Convert to records and sanitize
    records = filtered_df.to_dict(orient="records")
    return records