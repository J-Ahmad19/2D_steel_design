import sys
import logging
from pathlib import Path
from reader import read_excel
from dxf_generator import create_bridge_dxf, DEFAULTS
from utils import sanitize_filename

# Setup Paths
BASE_DIR = Path(__file__).parent.parent
INPUT_FILE = BASE_DIR / "input" / "dxf-input-values.xlsx"
OUTPUT_DIR = BASE_DIR / "output"

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

def process_data():
    logging.info(f"Reading input from: {INPUT_FILE}")
    
    try:
        data = read_excel(INPUT_FILE)
    except Exception as e:
        logging.error(f"Error reading Excel: {e}")
        return

    if not data:
        logging.warning("No data found in Excel file.")
        return

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    count = 0
    for row in data:
        # Merge row data with defaults to ensure no missing keys
        params = DEFAULTS.copy()
        # Clean None/NaN values from row
        clean_row = {k: v for k, v in row.items() if pd.notna(v) and v != ""}
        params.update(clean_row)
        
        # Determine filename
        dwg_num = str(params.get("drawing_number", f"output_{count}"))
        safe_name = sanitize_filename(dwg_num)
        out_path = OUTPUT_DIR / f"{safe_name}.dxf"
        
        try:
            create_bridge_dxf(params, str(out_path))
            logging.info(f"Generated: {out_path.name}")
            count += 1
        except Exception as e:
            logging.error(f"Failed to generate {dwg_num}: {e}")

    logging.info(f"Done. Generated {count} files in {OUTPUT_DIR}")

if __name__ == "__main__":
    import pandas as pd # Import here to ensure dependency check
    process_data()