# 2D Steel Bridge Design - DXF Generator

An automated Python tool built using `ezdxf` to generate standardized technical drawings for steel bridge structures. This project automates the drafting process by taking structural parameters (from Excel or dictionaries) and producing A3-sized CAD drawings with accurate scaling and dimensioning.

---

## 🚀 Features

* **Automated Scaling Logic:** Safely calculates scale factors for Section, Pier, and Plan views to ensure they fit perfectly within sheet quadrants without overlapping.
* **Custom Dimensioning Engine:** Includes a robust `_add_dim` function that renders:
    * Dynamic arrowhead sizing based on dimension length.
    * Rotated text for vertical and horizontal dimensions.
    * Proper extension line offsets and overruns.
* **Professional Layout:**
    * **Top Left:** Bridge Cross Section (Girders, Deck, and Bracing).
    * **Top Right:** Pier Elevation.
    * **Bottom Left:** Plan View showing pier caps.
    * **Bottom Right:** Centered Title Block with drawing numbers.
* **Layer Management:** Organized CAD layers (`BORDER`, `OBJECT`, `DIMENSIONS`, `TEXT`, `BRACING`) with specific lineweights and colors for industry-standard plotting.

---

## 📂 Project Structure

```text
2D_STEEL_DESIGN/
├── input/
│   ├── dxf-input-values.xlsx      # Parameter source (Excel)
│   └── dxf-input-values copy.xlsx # Backup/Sample input
├── output/                        # Destination for generated .dxf files
├── src/
│   ├── dxf_generator.py           # Core drawing & geometry logic
│   ├── main.py                    # Script entry point
│   ├── reader.py                  # Excel/Input data parser
│   ├── utils.py                   # Geometric helper functions
│   └── __init__.py
├── requirements.txt               # Python dependencies
└── venv/                          # Virtual environment
