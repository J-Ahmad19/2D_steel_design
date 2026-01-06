import sys
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
INPUT_FILE = BASE_DIR / "input" / "dxf-validation-test.xlsx"
OUTPUT_DIR = BASE_DIR / "output"

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

def process_data():
    logging.info(f"Reading input from: {INPUT_FILE}")
    
    try:
        # reader.py handles the Excel parsing and header mapping
        data = read_excel(INPUT_FILE)
    except Exception as e:
        logging.error(f"Error reading Excel: {e}")
        return

    if not data:
        logging.warning("No data found in Excel file.")
        return

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    success_count = 0
    # iterate using enumerate to track row numbers for better error reporting
    for i, row in enumerate(data, start=1):
        
        # 1. Clean None/NaN values from raw Excel row
        # We process ONLY the Excel data first to ensure strict validation
        clean_row = {k: v for k, v in row.items() if pd.notna(v) and v != ""}
        
        # 2. VALIDATION STEP: Use Pydantic to verify data logic/types
        try:
            # This creates a BridgeDataSchema instance.
            # It will now correctly trigger the Taper Error because of the global validator.
            validated_data = BridgeDataSchema(**clean_row)
            
            # Convert the validated object back to a dictionary, excluding None values
            valid_dict = validated_data.model_dump(exclude_none=True)
            
            # 3. MERGE WITH DEFAULTS: Only if the Excel data is 100% valid
            params = DEFAULTS.copy()
            params.update(valid_dict)
            
        except ValidationError as e:
            # Identify the failing drawing number if possible
            dwg_id = clean_row.get("drawing_number", f"Row {i}")
            logging.error(f"❌ Validation failed for {dwg_id}:")
            for error in e.errors():
                # Display the specific error message (including our Taper Error)
                message = error['msg']
                logging.error(f"   - {message}")
            continue # Skip this row and move to the next valid record
        
        # 4. FILENAME & GENERATION
        dwg_num = str(params.get("drawing_number", f"output_{success_count}"))
        safe_name = sanitize_filename(dwg_num)
        out_path = OUTPUT_DIR / f"{safe_name}.dxf"
        
        try:
            # Use the merged and validated params to generate the CAD file
            create_bridge_dxf(params, str(out_path))
            logging.info(f"✅ Generated: {out_path.name}")
            success_count += 1
        except Exception as e:
            # Catch crashes inside the generator, like NoneType errors
            logging.error(f"⚠️ Failed to generate {dwg_num}: {e}")

    logging.info(f"Done. Successfully generated {success_count} files in {OUTPUT_DIR}")

if __name__ == "__main__":
    process_data()