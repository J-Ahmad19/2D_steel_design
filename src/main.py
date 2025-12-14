# src/main.py
import sys
from pathlib import Path
from reader import read_excel
# Assuming dxf_generator.py is updated as per the previous response
from dxf_generator import create_bridge_dxf, DEFAULTS 
from utils import sanitize_filename
import pandas as pd
import logging

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

# Ensure paths are correct relative to the `src/` directory
INPUT = Path("../input/dxf-input-values.xlsx")
OUTPUT_DIR = Path("../output")

def sanitize_row_params(row: pd.Series) -> dict:
    d = row.to_dict()
    
    # 1. Ensure drawing_number present
    if not d.get("drawing_number"):
        d["drawing_number"] = f"row-{int(row.name)+1}"
        
    # 2. Coerce numeric types and apply defaults for ALL required parameters
    # The DEFAULTS dictionary from dxf_generator.py is the source of truth for defaults.
    REQUIRED_NUMERIC_KEYS = [k for k in DEFAULTS.keys() if k != "drawing_number"]
    
    for key in REQUIRED_NUMERIC_KEYS:
        # Check for NaN, None, or empty string
        is_nan_or_missing = pd.isna(d.get(key)) or d.get(key) == ""
        
        if key in d and not is_nan_or_missing:
            try:
                d[key] = float(d[key])
            except Exception:
                # If conversion fails, use the defined default
                d[key] = DEFAULTS[key]
                logging.warning(f"Coercion failed for key '{key}' in row {row.name+1}. Using default: {d[key]}")
        elif key not in d or is_nan_or_missing:
            # If missing or NaN, supply default from dxf_generator
            d[key] = DEFAULTS[key]

    return d

def run():
    if not INPUT.exists():
        logging.error(f"Input file {INPUT} not found. Please ensure it is in the correct location.")
        # 
        sys.exit(1)
        
    try:
        df = read_excel(str(INPUT))
    except Exception as e:
        logging.error(f"Failed to read and process Excel file {INPUT}: {e}")
        sys.exit(1)
        
    if df.empty:
        logging.warning("No valid data rows found in the input spreadsheet. Exiting.")
        sys.exit(0)
        
    logging.info(f"Read {len(df)} valid data row(s) from {INPUT}")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    failures = 0
    for idx, row in df.iterrows():
        params = sanitize_row_params(row)
        filename_safe = sanitize_filename(params.get("drawing_number"))
        out_path = OUTPUT_DIR / f"{filename_safe}.dxf"
        
        try:
            logging.info(f"Generating {out_path} ...")
            # The create_bridge_dxf function now expects the parameters in the cleaned dictionary format
            create_bridge_dxf(params, str(out_path))
            
        except Exception as e:
            logging.exception(f"Failed to generate {out_path} for row {idx+1} ({params.get('drawing_number')}): {e}")
            failures += 1
            
    if failures:
        logging.info(f"Completed with {failures} failure(s). Check the logs for details.")
    else:
        logging.info("All DXF files generated successfully.")

if __name__ == "__main__":
    run()