import pandas as pd
from pathlib import Path
import math

# Mapping user headers (loose) to code keys (strict)
HEADER_MAP = {
    # Drawing Info
    "drawing_number": ["drawing number", "drawing no", "drg no"],

    # Bridge Dimensions
    "length_m": ["length of bridge (l)", "length of bridge", "length (m)"],
    "carriage_width_m": [
        "width of carriageway (w)", 
        "width of carriageway", 
        "carriageway width"
    ],

    # ONLY THIS IS IN mm
    "depth_mm": [
        "depth of bridge girder",
        "depth of girder",
        "depth of bridge",
        "depth (mm)"
    ],

    "num_girders": ["number of girder (ng)", "number of girders", "no. of girders"],

    # Pier Dimensions (ALL METRES)
    "pier_cap_length_m": ["length of pier cap"],
    "pier_cap_depth_center_m": ["depth of pier cap at centre","depth of pier cap at center","pier cap depth center","pcc"],
    "pier_cap_depth_end_m": ["depth of pier cap at end","pier cap depth end","pce"],
    "pier_cap_width_m": ["width of pier cap"],
}


def normalize_header(h):
    return str(h).lower().strip().replace("\n", " ").replace("  ", " ")


def get_mapped_columns(df_columns):
    rename_dict = {}
    for col in df_columns:
        norm = normalize_header(col)
        for key, aliases in HEADER_MAP.items():
            if norm == key or any(alias in norm for alias in aliases):
                rename_dict[col] = key
                break
    return rename_dict


def _to_float(v):
    """Safe numeric conversion."""
    if pd.isna(v):
        return None
    try:
        return float(v)
    except Exception:
        return None


def read_excel(path_str):
    p = Path(path_str)
    if not p.exists():
        raise FileNotFoundError(f"Input file not found at {p}")

    df = pd.read_excel(p, header=0)

    # Apply mapping
    rename_map = get_mapped_columns(df.columns)
    df = df.rename(columns=rename_map)

    # Filter valid columns
    valid_keys = HEADER_MAP.keys()
    df = df[df.columns.intersection(valid_keys)]

    records = []

    for _, row in df.iterrows():
        rec = {}

        # -------- Drawing Number --------
        rec["drawing_number"] = str(row.get("drawing_number", "")).strip()

        # -------- Bridge Dimensions (metres) --------
        rec["length_m"] = _to_float(row.get("length_m"))
        rec["carriage_width_m"] = _to_float(row.get("carriage_width_m"))

        # -------- Depth of Girder (ONLY FIELD IN mm) --------
        depth_val = _to_float(row.get("depth_mm"))

        if depth_val is not None:
            # Safety: if someone mistakenly enters metres (like 2.8 instead of 2800)
            # convert to mm if value is suspiciously small
            if depth_val < 100:       # e.g., 2.5 m → 2500 mm
                depth_val *= 1000.0

        rec["depth_mm"] = depth_val

        # -------- Number of girders --------
        ng = row.get("num_girders")
        rec["num_girders"] = int(ng) if not pd.isna(ng) else None

        # -------- Pier Dimensions (ALL METRES) --------
        rec["pier_cap_length_m"] = _to_float(row.get("pier_cap_length_m"))
        rec["pier_cap_depth_center_m"] = _to_float(row.get("pier_cap_depth_center_m"))
        rec["pier_cap_depth_end_m"] = _to_float(row.get("pier_cap_depth_end_m"))
        rec["pier_cap_width_m"] = _to_float(row.get("pier_cap_width_m"))

        records.append(rec)

    return records
