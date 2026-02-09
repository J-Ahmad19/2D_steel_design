import pandas as pd
from pathlib import Path

def generate_validation_excel():
    # 1. Define the exact columns from your screenshot
    columns = [
        "drawing number", 
        "length of bridge", 
        "depth of bridge", 
        "width of carriageway", 
        "number of girders", 
        "length of pier cap", 
        "depth of pier cap at centre", 
        "depth of pier cap at end", 
        "width of pier cap (m)"
    ]

    # 2. Create data that tests your Pydantic validators
    data = [
        # VALID: Standard data
        ["2025-01-R1", 20.0, 1500, 9.5, 3, 10.5, 1.8, 0.9, 0.9],
        
        # INVALID: Negative Length (Tests 'gt=0' in validators.py)
        ["2025-02-R1", -5.0, 1200, 9.5, 3, 10.5, 1.6, 0.8, 0.9],
        
        # INVALID: Only 1 Girder (Tests 'ge=2' in validators.py)
        ["2025-03-R1", 15.0, 1000, 9.5, 1, 10.5, 1.4, 0.7, 0.9],
        
        # INVALID: Center depth < End depth (Tests custom @field_validator)
        ["2025-04-R1", 30.0, 2300, 11.5, 4, 12.5, 0.5, 1.2, 0.9],
        
        # INVALID: Missing required value (Tests presence validation)
        ["2025-05-R1", 10.0, 800, 9.5, 3, 10.5, None, 0.6, 0.9],
        
        # VALID: Maximum limit test
        ["2025-06-R1", 45.0, 2850, 13.5, 5, 14.5, 2.8, 1.4, 1.2]
    ]

    # 3. Create DataFrame
    df = pd.DataFrame(data, columns=columns)

    # 4. Define the path (saves to your 'input' folder)
    base_dir = Path(__file__).parent.parent
    output_path = base_dir / "input" / "dxf-validation-test.xlsx"

    # Ensure the input directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # 5. Save the file
    try:
        df.to_excel(output_path, index=False)
        print(f"✅ Success! Validation test file saved to: {output_path}")
        print("Now run your main.py to see the validators catch the errors.")
    except Exception as e:
        print(f"❌ Failed to save file: {e}")

if __name__ == "__main__":
    generate_validation_excel()