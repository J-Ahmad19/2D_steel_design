# 2D Steel Bridge Drawing Generator

An automated Python-based CAD tool built with `ezdxf` to generate standardized technical drawings for steel bridge structures. This project automates the drafting of Cross Sections, Pier Elevations, and Plan Views directly into A3-sized DXF files.

---

## 📂 Project Structure

As shown in the development environment, the project is organized as follows:

```text
2D_STEEL_DESIGN/
├── input/
│   ├── dxf-input-values.xlsx      # Excel sheet containing bridge parameters
│   └── dxf-input-values copy.xlsx # Backup of input parameters
├── output/
│   └── 2025-06-11-R1-AB-01.dxf    # Generated CAD drawings
├── src/
│   ├── __init__.py
│   ├── dxf_generator.py           # Core rendering engine and ezdxf logic
│   ├── main.py                    # Application entry point
│   ├── reader.py                  # Input parser (Excel/Dict)
│   └── utils.py                   # Geometric and scaling helpers
├── venv/                          # Python virtual environment
└── requirements.txt               # Project dependencies (ezdxf, openpyxl, etc.)

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
