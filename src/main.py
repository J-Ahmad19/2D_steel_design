import logging
import pandas as pd
from pathlib import Path
from reader import read_excel
from dxf_generator import create_bridge_dxf, DEFAULTS
from utils import sanitize_filename

# --- NEW IMPORTS FOR VALIDATION ---
from validators import BridgeDataSchema
from pydantic import ValidationError
# ---------------------------------

# Setup Paths
BASE_DIR = Path(__file__).parent.parent
INPUT_FILE = BASE_DIR / "input" / "dxf-input-values.xlsx"
OUTPUT_DIR = BASE_DIR / "output"

logging.basicConfig(level=logging.INFO, format="%(message)s")

# --- 1. FIELD MAPPING: Technical Name -> Professional Label ---
# NOTE: The order here defines columns: A, B, C, D, E...
FIELD_LABELS = {
    "drawing_number": "DRAWING NUMBER",              # Col A (1)
    "length_m": "Length of Bridge (m)",              # Col B (2)
    "depth_mm": "Depth of Bridge Girder (mm)",       # Col C (3)
    "carriage_width_m": "Width of Carriageway (m)",  # Col D (4)
    "num_girders": "Number of Girders",              # Col E (5)
    "pier_cap_length_m": "Length of Pier Cap (m)",   # Col F (6)
    "pier_cap_depth_center_m": "Depth of Pier Cap at Centre (m)", # Col G (7)
    "pier_cap_depth_end_m": "Depth of Pier Cap at End (m)",       # Col H (8)
    "pier_cap_width_m": "Width of Pier Cap (m)",     # Col I (9)
}

# --- 2. LOGIC ERROR MAPPING: Error Phrase -> Involved Fields ---
# This maps global errors to the specific columns they affect
LOGIC_FIELD_MAP = {
    "Structural Taper Error": ["pier_cap_depth_center_m", "pier_cap_depth_end_m"],
    "Geometric Error": ["carriage_width_m", "pier_cap_length_m"],
    "Girder spacing": ["num_girders", "carriage_width_m"],
}

# Define strict header order for column calculation
ORDERED_HEADERS = list(FIELD_LABELS.keys())

def get_column_index(field_name):
    """Returns the 1-based integer column index."""
    try:
        return ORDERED_HEADERS.index(field_name) + 1
    except ValueError:
        return 0

def get_readable_name(field_name):
    """Returns the professional label for a field."""
    return FIELD_LABELS.get(field_name, field_name.upper().replace("_", " "))

def col_to_letter(n):
    """Converts a 1-based column number to Excel letter (e.g., 1->A, 28->AB)."""
    string = ""
    while n > 0:
        n, remainder = divmod(n - 1, 26)
        string = chr(65 + remainder) + string
    return string or "?"

def process_data():
    logging.info(f"--- STARTING PROCESS: {INPUT_FILE} ---")
    
    try:
        # reader.py handles the Excel parsing and header mapping
        data = read_excel(INPUT_FILE)
    except Exception as e:
        logging.error(f"CRITICAL ERROR: Error reading Excel: {e}")
        return

    if not data:
        logging.warning("No data found in Excel file.")
        return

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    success_count = 0
    
    # Iterate starting at 2 (assuming Row 1 is headers in Excel)
    for i, row in enumerate(data, start=2):
        
        # 1. Clean None/NaN values
        clean_row = {k: v for k, v in row.items() if pd.notna(v) and v != ""}
        
        # Get Drawing Number for logging (or fallback)
        dwg_id = clean_row.get("drawing_number", "UNKNOWN_ID")
        
        # 2. VALIDATION STEP
        try:
            validated_data = BridgeDataSchema(**clean_row)
            
            # Convert to dict and merge with DEFAULTS
            valid_dict = validated_data.model_dump(exclude_none=True)
            params = DEFAULTS.copy()
            params.update(valid_dict)
            
        except ValidationError as e:
            # --- EXCEL CELL ADDRESS ERROR FORMATTING ---
            logging.error(f"-" * 65)
            logging.error(f"❌  VALIDATION FAILED FOR \"{dwg_id}\"")
            
            for error in e.errors():
                raw_msg = error['msg'].replace("Value error, ", "")
                loc = error['loc']
                
                # --- INTELLIGENT ERROR PARSING ---
                if loc:
                    # Case A: Single Field Error
                    field_key = loc[0]
                    col_num = get_column_index(field_key)
                    col_char = col_to_letter(col_num)
                    
                    # Construct Address: e.g., "B" + "3" = "B3"
                    cell_addr = f"{col_char}{i}"
                    field_label = get_readable_name(field_key)
                    
                    # REPLACE "Input" or "Field" with actual Professional Label
                    final_msg = raw_msg.replace("Input", field_label).replace("Field", field_label)
                    
                    logging.error(f"    ERROR AT CELL {cell_addr} ({field_label}) :")
                    logging.error(f"    -> {final_msg}")
                
                else:
                    # Case B: Global Logic Error (Multi-cell)
                    involved_fields = []
                    for key_phrase, fields in LOGIC_FIELD_MAP.items():
                        if key_phrase in raw_msg:
                            involved_fields = fields
                            break
                    
                    if involved_fields:
                        # Create list of addresses: e.g., "G5 & H5"
                        addresses = []
                        names = []
                        for f in involved_fields:
                            c_num = get_column_index(f)
                            c_char = col_to_letter(c_num)
                            addresses.append(f"{c_char}{i}")
                            names.append(get_readable_name(f))
                        
                        addr_str = " & ".join(addresses)
                        name_str = ", ".join(names)
                        
                        logging.error(f"    ERROR AT CELL {addr_str} ({name_str}) :")
                        logging.error(f"    -> {raw_msg}")
                    else:
                        # Fallback for unknown global errors
                        logging.error(f"    ERROR IN LOGIC CHECK (ROW {i}) :")
                        logging.error(f"    -> {raw_msg}")

            logging.error(f"-" * 65)
            continue # Skip this row
        
        # 3. FILENAME & GENERATION
        dwg_num = str(params.get("drawing_number", f"output_{success_count}"))
        safe_name = sanitize_filename(dwg_num)
        out_path = OUTPUT_DIR / f"{safe_name}.dxf"
        
        try:
            create_bridge_dxf(params, str(out_path))
            logging.info(f"✅  Generated: {out_path.name}")
            success_count += 1
        except Exception as e:
            logging.error(f"⚠️  Failed to generate {dwg_num}: {e}")

    logging.info(f"\nDone. Successfully generated {success_count} files in {OUTPUT_DIR}")

if __name__ == "__main__":
    process_data()