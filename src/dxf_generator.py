import ezdxf
from pathlib import Path
from typing import Dict

# ---------- CONFIGURATION (A3 LANDSCAPE MM) ----------
A3_W = 420.0
A3_H = 297.0

MARGIN_LEFT = 30.0
MARGIN_RIGHT = 30.0
MARGIN_TOP = 15.0
MARGIN_BOTTOM = 15.0

TITLEBLOCK_W = 160.0 
TITLEBLOCK_H = 40.0

# Text Sizes
TEXT_H_DIM = 1.5       # Dimension text
TEXT_H_TITLE = 3.5     # View titles (e.g. "SECTION AT MIDSPAN")
TEXT_H_BIG = 10.0      # Drawing Number

# Dimensioning
DIM_OFFSET = 12.0      # Distance from object
TICK_SIZE = 2.0        # Size of the bold tick
TICK_WIDTH = 0.7       # Thickness of tick line

# Layers
L_BORDER = "BORDER"
L_OBJECT = "OBJECT"
L_DIM    = "DIMENSIONS"
L_TEXT   = "TEXT"
L_BRACING = "BRACING"

# Colors (ACI)
C_WHITE = 7

DEFAULTS = {
    "length_m": 20.0,
    "carriage_width_m": 12.0,
    "depth_mm": 1500.0,
    "num_girders": 3,
    "pier_cap_length_m": 10.5,
    "pier_cap_width_m": 1.2,
    "pier_cap_depth_center_m": 1.5,
    "pier_cap_depth_end_m": 0.6,
    "drawing_number": "2025-06-11-R1-AB-01"
}

def _to_mm(val_m):
    try: return float(val_m) * 1000.0
    except: return 0.0

def _setup_doc():
    doc = ezdxf.new("R2010")
    doc.header["$INSUNITS"] = 4 # Millimeters
    
    # Layers
    doc.layers.new(L_BORDER, dxfattribs={"color": C_WHITE, "lineweight": 60})
    doc.layers.new(L_OBJECT, dxfattribs={"color": C_WHITE, "lineweight": 45})
    doc.layers.new(L_BRACING, dxfattribs={"color": C_WHITE, "lineweight": 30})
    doc.layers.new(L_DIM,    dxfattribs={"color": C_WHITE, "lineweight": 25})
    doc.layers.new(L_TEXT,   dxfattribs={"color": C_WHITE, "lineweight": 25})

    if "ROMANS" not in doc.styles:
        doc.styles.new("ROMANS", dxfattribs={"font": "romans.shx", "width": 0.8})
    return doc

import math # Needed for trigonometric functions for rotation

# --- DEFINITIONS TO BE PLACED NEAR THE START OF YOUR SCRIPT ---
# Assuming L_OBJECT or a similar layer is used for the arrow fill.
L_TERMINATOR = "DIM_ARROW" 

def _calc_arrow_size(p1, p2, base=3.0):
    """
    Arrow size depends on dimension length.
    Engineering rule: minimum length = 6 × arrow size
    """
    dim_len = math.dist(p1, p2)
    return min(base, dim_len / 6.0)


def _draw_arrow(msp, center_point, size, angle_deg):
    """
    Draws a filled triangular arrowhead at the center_point.
    
    Args:
        msp: Model Space object (drawing canvas).
        center_point (tuple): (x, y) location of the arrow tip.
        size (float): Length of the arrowhead along the dimension line.
        angle_deg (float): Angle of the dimension line (0, 90, 180, 270).
    """
    cx, cy = center_point
    
    # Define the arrow geometry (a symmetric triangle relative to the tip (0, 0))
    # Standard arrowhead height is about 3 times the width.
    h = size  # Height of arrow (along dim line)
    w = h / 3.0 # Base width of arrow
    
    # Points in arrow-local coordinates, assuming the tip is at (h/2, 0)
    # The tip must be at the dimension line endpoint (cx, cy), so we define 
    # the points relative to that tip and then rotate/translate.
    
    # Pts: Tip, Base Left, Base Right, Tip (closed)
    local_points = [
        (0.0, 0.0),        # Tip (Reference Point)
        (-h, w / 2.0),     # Base Left
        (-h, -w / 2.0)     # Base Right
    ]
    
    # Convert angle to radians
    angle_rad = math.radians(angle_deg)
    
    # Rotation and Translation
    rotated_points = []
    for px, py in local_points:
        # 1. Rotate the point
        new_x = px * math.cos(angle_rad) - py * math.sin(angle_rad)
        new_y = px * math.sin(angle_rad) + py * math.cos(angle_rad)
        # 2. Translate the point to the center_point
        rotated_points.append((new_x + cx, new_y + cy))
        
    # Draw the filled arrow (closed polyline)
    # Using 'L_OBJECT' or a dedicated layer for fill.
    msp.add_lwpolyline(rotated_points, dxfattribs={"layer": L_TERMINATOR, "closed": True, "flags": 1})
    # NOTE: 'flags: 1' might be needed for specific libraries to force closing the polyline.
    
# --- END OF HELPER FUNCTION ---

# ---------- UTILS ----------

def _draw_rect(msp, x, y, w, h, layer=L_BORDER):
    pts = [(x, y), (x+w, y), (x+w, y+h), (x, y+h), (x, y)]
    msp.add_lwpolyline(pts, dxfattribs={"layer": layer, "closed": True})

def _add_dim(msp, p1, p2, text_val, offset=10.0, vertical=False, text_rotation=0,override=False):
    x1, y1 = p1
    x2, y2 = p2

    # ------------------ ADDED ------------------
    ARROW_SIZE = _calc_arrow_size(p1, p2, base=3.0)  # <<< ADDED
    # -------------------------------------------

    EXT_LINE_OVERRUN = 1.5 * ARROW_SIZE
    EXT_LINE_GAP = 0.5 * ARROW_SIZE

    if vertical:
        dx = x1 + offset
        gap_direction = 1 if dx > x1 else -1

        # Extension lines
        msp.add_line((x1 + gap_direction * EXT_LINE_GAP, y1), (dx, y1),
                     dxfattribs={"layer": L_DIM})
        msp.add_line((x2 + gap_direction * EXT_LINE_GAP, y2), (dx, y2),
                     dxfattribs={"layer": L_DIM})

        # Dimension line
        msp.add_line((dx, y1), (dx, y2), dxfattribs={"layer": L_DIM})

        # ------------------ ADDED ------------------
        dim_len = abs(y2 - y1)
        arrows_inside = dim_len >= 6 * ARROW_SIZE
        # -------------------------------------------

        # Arrow at P1
        if y1 > y2:
            _draw_arrow(
                msp,
                (dx, y1 if arrows_inside else y1 + ARROW_SIZE),
                ARROW_SIZE,
                90 if arrows_inside else 270
            )
        else:
            _draw_arrow(
                msp,
                (dx, y1 if arrows_inside else y1 - ARROW_SIZE),
                ARROW_SIZE,
                270 if arrows_inside else 90
            )

        # Arrow at P2
        if y2 > y1:
            _draw_arrow(
                msp,
                (dx, y2 if arrows_inside else y2 + ARROW_SIZE),
                ARROW_SIZE,
                90 if arrows_inside else 270
            )
        else:
            _draw_arrow(
                msp,
                (dx, y2 if arrows_inside else y2 - ARROW_SIZE),
                ARROW_SIZE,
                270 if arrows_inside else 90
            )

          # ---------- FIXED TEXT (NOW SAME LOGIC AS HORIZONTAL) ----------
        if text_val:
            mid_y = (y1 + y2) / 2
            text_x_shift = (2 * ARROW_SIZE) * gap_direction

            if text_rotation == 0:
                text_x_shift += (0.5 * TEXT_H_DIM + 4* ARROW_SIZE) * gap_direction

            t = msp.add_text(
                str(text_val),
                dxfattribs={
                    "height": TEXT_H_DIM,
                    "layer": L_TEXT,
                    "style": "ROMANS"
                }
            )

            t.dxf.halign = 1      # Center (same as horizontal)
            t.dxf.valign = 2      # Middle (same as horizontal)
            t.dxf.rotation = text_rotation     # Middle (same as horizontal)

            pos = (dx + text_x_shift, mid_y)

            t.dxf.insert = pos
            t.dxf.align_point = pos   # <-- KEY: same point like horizontal

    else:
        dy = y1 + offset
        gap_direction = 1 if dy > y1 else -1

        # Extension lines
        msp.add_line((x1, y1 + gap_direction * EXT_LINE_GAP), (x1, dy),
                     dxfattribs={"layer": L_DIM})
        msp.add_line((x2, y2 + gap_direction * EXT_LINE_GAP), (x2, dy),
                     dxfattribs={"layer": L_DIM})

        # Dimension line
        msp.add_line((x1, dy), (x2, dy), dxfattribs={"layer": L_DIM})

        # ------------------ ADDED ------------------
        dim_len = abs(x2 - x1)
        arrows_inside = dim_len >= 6 * ARROW_SIZE
        # -------------------------------------------

        _draw_arrow(
            msp,
            (x1 if arrows_inside else x1 - ARROW_SIZE, dy),
            ARROW_SIZE,
            180 if arrows_inside else 0
        )
        _draw_arrow(
            msp,
            (x2 if arrows_inside else x2 + ARROW_SIZE, dy),
            ARROW_SIZE,
            0 if arrows_inside else 180
        )
        if text_val:
            mid_x = (x1 + x2) / 2
            text_y_shift = (2 * ARROW_SIZE) * gap_direction

            t = msp.add_text(
                str(text_val),
                dxfattribs={
                    "height": TEXT_H_DIM,
                    "layer": L_TEXT,
                    "style": "ROMANS"
                }
            )
            # Proper DXF justification without set_pos()
            t.dxf.halign = 1      # Center
            t.dxf.valign = 2      # Middle
            t.dxf.rotation = text_rotation

            pos = (mid_x, dy + text_y_shift)

            t.dxf.insert = pos
            t.dxf.align_point = pos



# ---------- VIEW RENDERERS ----------
# --- New Function to Calculate Scale Safely ---
# This function calculates a single scale factor that safely fits all dimensions (L, W, D) 
# and their required margins into the given box (bx, by, bw, bh).
MAX_DRAWING_MARGIN_MM = 15.0

def _calculate_section_scale(box, params):
    bx, by, bw, bh = box

    W = _to_mm(params["carriage_width_m"])
    D = params["depth_mm"]

    Wm = W + 2*MAX_DRAWING_MARGIN_MM
    Dm = D + 2*MAX_DRAWING_MARGIN_MM

    sx = (bw * 0.85) / Wm
    sy = (bh * 0.70) / Dm

    return min(sx, sy)

def _calculate_pier_scale(box, params):
    bx, by, bw, bh = box

    LPC = _to_mm(params["pier_cap_length_m"])
    DPCC = _to_mm(params["pier_cap_depth_center_m"])

    H_core = DPCC + 2000.0    # pier + assumed column part

    Lm = LPC + 2 * MAX_DRAWING_MARGIN_MM
    Hm = H_core + 2 * MAX_DRAWING_MARGIN_MM

    sx = (bw * 0.80) / Lm     # 80% width
    sy = (bh * 0.70) / Hm     # 70% height
    return min(sx, sy)


def _calculate_plan_scale(box, params):
    bx, by, bw, bh = box

    L = _to_mm(params["length_m"])
    W = _to_mm(params["carriage_width_m"])

    Lm = L + 2 * MAX_DRAWING_MARGIN_MM
    Wm = W + 2 * MAX_DRAWING_MARGIN_MM

    sx = (bw * 0.9) / Lm     # 85% width
    sy = (bh * 0.8) / Wm     # 70% height
    return min(sx, sy)


# --- Updated _render_section function ---

def _render_section(msp, box, params):
    """Top Left: Cross Section"""
    
    # Calculate scale using the new safe function (assuming 'box' here is the CS box)
    scale = _calculate_section_scale(box, params) 
    
    bx, by, bw, bh = box
    
    W = _to_mm(params.get("carriage_width_m"))
    D = float(params.get("depth_mm"))
    NG = int(params.get("num_girders"))
    
    # Use the calculated scale
    dw, dd = W * scale, D * scale
    deck_t = 250 * scale
    
    cx, cy = bx + bw/2, by + bh/2
    left, right = cx - dw/2, cx + dw/2
    top, bot = cy + dd/2, cy - dd/2
    
    # 1. Deck (NO CHANGE)
    msp.add_lwpolyline([(left, top), (right, top), (right, top-deck_t), (left, top-deck_t)], 
                       dxfattribs={"layer": L_OBJECT, "closed": True})
    
    # 2. Girders & Bracing (NO CHANGE)
    overhang = 500 * scale
    g_span = dw - 2*overhang
    spacing = g_span / (NG - 1)
    
    g_x = []
    g_width = 300 * scale
    
    for i in range(NG):
        gx = (left + overhang) + i*spacing
        g_x.append(gx)
        # Top Flange
        # Giving the flange a physical thickness (e.g., 2.0 drawing units)
        msp.add_lwpolyline(
            [(gx - g_width/2, top - deck_t), (gx + g_width/2, top - deck_t)], 
            dxfattribs={
                "layer": L_OBJECT, 
                "const_width": 0.5  # Physical thickness in your mm scale
            }
        )
        # Web
        # Giving the web a physical width (e.g., 1.5 units wide)
        msp.add_lwpolyline(
            [(gx, top - deck_t), (gx, bot)], 
            dxfattribs={
                "layer": L_OBJECT, 
                "const_width": 0.2  # This width is in your drawing units (mm)
            }
        )
        # Bottom Flange
        msp.add_lwpolyline(
            [(gx - g_width/2, bot), (gx + g_width/2, bot)], 
            dxfattribs={
                "layer": L_OBJECT, 
                "const_width": 0.5  # Physical thickness in your mm scale
            }
        )

        # Label
        lbl = msp.add_text(f"G{i+1}", dxfattribs={"height": TEXT_H_DIM, "layer": L_TEXT})
        lbl.dxf.insert = (gx + g_width/2-1, (top + bot)/2-2)
        
    # Cross Bracing
    for i in range(NG-1):
        x1, x2 = g_x[i], g_x[i+1]
        msp.add_line((x1, top-deck_t), (x2, bot), dxfattribs={"layer": L_BRACING})
        msp.add_line((x1, bot), (x2, top-deck_t), dxfattribs={"layer": L_BRACING})
        _add_dim(msp, (x1, bot), (x2, bot), "Eq", offset=-5)

    # Dimensions (NO CHANGE - Dims should now fit due to safe scale)
    _add_dim(msp, (left, top), (right, top), "Width of Carriageway", offset=5)
    # Vertical dimension on LEFT side
    _add_dim(
        msp,
        (left, top-deck_t),
        (left, bot),
        "Depth of Girder",
        offset=-5,  # try 8 or 10; flip sign if it appears inside
        vertical=True,
        text_rotation=90
    )



    _add_dim(msp, (left, top-deck_t/2), (g_x[0], top-deck_t/2), "500", offset=-5)
    _add_dim(msp, (g_x[-1], top-deck_t/2), (right, top-deck_t/2), "500", offset=-5)

def _render_pier(msp, box, params):
    """Top Right: Pier Elevation"""
    bx, by, bw, bh = box
    scale = _calculate_pier_scale(box, params)
    
    LPC = _to_mm(params.get("pier_cap_length_m"))
    DPCC = _to_mm(params.get("pier_cap_depth_center_m"))
    DPCE = _to_mm(params.get("pier_cap_depth_end_m"))
    
    # 1. Define total required height (total_h) and depth-constrained height (H_required)
    # The total drawing height is governed by the center depth plus the vertical support below.
    # We use 2000mm as the assumed height of the column segment/bearing area below the pier cap.
    H_core = DPCC + 2000 
    
    # 2. Apply Margins to Dimensions for Safe Scaling
    # The drawing will extend past LPC and H_core due to dimension lines.
    
    # Length of Pier Cap (LPC) constrained by bw * 0.8
    LPC_with_margin = LPC + 2 * MAX_DRAWING_MARGIN_MM 
    
    # Total Height (H_core) constrained by bh * 0.7
    H_core_with_margin = H_core + 2 * MAX_DRAWING_MARGIN_MM 

    # 3. Calculate Safe Scale Factor
    # We use the most restrictive scale factor to ensure the drawing fits.
    scale_l = (bw * 0.8) / LPC_with_margin
    scale_h = (bh * 0.7) / H_core_with_margin
    scale = min(scale_l, scale_h) # This is the unified/safe scale for this view
    
    # 4. Calculate Scaled Dimensions
    dlpc = LPC * scale
    ddc = DPCC * scale
    dde = DPCE * scale
    
    # 5. Define Center and Coordinates
    # The coordinate system is chosen to center the drawing around the pier cap.
    # The center of the box is cx, cy. We shift the drawing up slightly (ddc/3) so the base 
    # of the pier cap is lower, allowing room for the vertical column representation below.
    cx, cy = bx + bw/2, by + bh/2 + ddc/3
    left, right = cx - dlpc/2, cx + dlpc/2
    top = cy
    bot_mid = top - ddc
    bot_end = top - dde
    
    # 6. Pier Cap Polyline (NO CHANGE in geometry, points are now safely scaled)
    pts = [
        (left, top), (right, top), (right, bot_end),
        (cx + 200*scale, bot_mid),
        (cx + 200*scale, bot_mid - 1500*scale), # Assuming 1500mm is part of the 2000mm support below
        (cx - 200*scale, bot_mid - 1500*scale),
        (cx - 200*scale, bot_mid),
        (left, bot_end)
    ]
    msp.add_lwpolyline(pts, dxfattribs={"layer": L_OBJECT, "closed": True})
    
    # 7. Dimensions (Offsets are small enough now due to the safe scale calculation)
    _add_dim(msp, (cx, top), (cx, bot_mid), "  Depth of Pier Cap at Centre", offset=5, vertical=True,text_rotation=0)
    _add_dim(msp, (left, top), (left, bot_end), "Depth of Pier Cap at End", offset=-5, vertical=True,text_rotation=90)
    
    
    
# --- Updated _render_plan function ---
def _render_plan(msp, box, params):
    """Bottom Left: Plan View"""
    
    # Calculate scale using the new safe function (assuming 'box' here is the Plan box)
    scale = _calculate_plan_scale(box, params) 
    
    bx, by, bw, bh = box
    
    L = _to_mm(params.get("length_m"))
    W = _to_mm(params.get("carriage_width_m"))
    WPC = _to_mm(params.get("pier_cap_width_m"))
    
    # Use the calculated scale
    dl, dw, dwpc = L * scale, W * scale, WPC * scale
    
    cx, cy = bx + bw/2, by + bh/2
    left, right = cx - dl/2, cx + dl/2
    top, bot = cy + dw/2, cy - dw/2
   
    # --- MODIFIED SECTION (Bridge Lines) ---
    # These lines are drawn inside the core bridge area (left, right, top, bot). 
    # They should not cause overflow. (NO CHANGE)
    # Top line
    msp.add_line((left, top-3), (right, top-3), dxfattribs={"layer": L_OBJECT})
    msp.add_line((left, top-1), (right, top-1), dxfattribs={"layer": L_OBJECT,"lineweight": 60})
    msp.add_lwpolyline(
    [(left, top-2), (right, top-2)], 
    dxfattribs={
        "layer": L_OBJECT,
        "const_width": 0.3  # Adjust this value to your desired thickness
    }
)
    # Center line
   # This creates a line that is physically 'thick' in the drawing space
    msp.add_lwpolyline(
        [(left, cy), (right, cy)], 
        dxfattribs={
            "layer": L_OBJECT, 
            "const_width": 0.3  # Adjust this value based on your scale
        }
    )
    msp.add_line((left, cy+1), (right, cy+1), dxfattribs={"layer": L_OBJECT,"lineweight": 60})
    msp.add_line((left, cy-1), (right, cy-1), dxfattribs={"layer": L_OBJECT})
    # Bottom line
    msp.add_line((left, bot+3), (right, bot+3), dxfattribs={"layer": L_OBJECT})
    msp.add_line((left, bot+1), (right, bot+1), dxfattribs={"layer": L_OBJECT,"lineweight": 60})
    # Increasing physical width for the bottom edge middle line
    msp.add_lwpolyline(
        [(left, bot+2), (right, bot+2)], 
        dxfattribs={
            "layer": L_OBJECT, 
            "const_width": 0.3  # Physical units (mm)
        }
    )
    # ------------------------
    
    # Pier Caps (Ends) - MODIFIED: Use scaled offsets instead of fixed offsets
    pc_l_end = left + dwpc
    pc_r_start = right - dwpc
    
    
    # Draw pier caps as rectangles at the ends
    msp.add_lwpolyline([(left-5, bot), (pc_l_end, bot), 
                        (pc_l_end, top), (left-5, top)], 
                       dxfattribs={"layer": L_OBJECT, "closed": True})
    msp.add_lwpolyline([(right+5, bot), (pc_r_start, bot), 
                        (pc_r_start, top), (right+5, top)], 
                       dxfattribs={"layer": L_OBJECT, "closed": True})
    
    # Dimensions - MODIFIED: Calculate offsets in scaled units (mm)
    
    # dim_offset_outer was 12.0
    dim_offset_outer_scaled = 25
    # dim_offset_inner was 5.0
    dim_offset_inner_scaled = 10 

    # Width of Pier Cap (Top, outer)
    # We must ensure the offset for the dimension is small enough, which is guaranteed 
    # by the margin added to L and W in the scale calculation.
    
    # Use the outside edge of the drawing: left-pc_offset
    _add_dim(msp, (left-5, top), (pc_l_end, top), 
             "Width of Pier Cap", offset=dim_offset_outer_scaled)
    
    _add_dim(msp, (pc_r_start, top), (right+5, top), 
             "Width of Pier Cap", offset=dim_offset_outer_scaled)
    
    # Length of Bridge (Top, inner)
    # The dimension is shown between the inner edges of the pier caps (pc_l_end-pc_offset, pc_r_start+pc_offset)
    _add_dim(msp, (left, top), (right, top), 
             f"Length of Bridge", offset=dim_offset_inner_scaled)
# ---------- MAIN ----------

def create_bridge_dxf(params: Dict, out_path: str):
    doc = _setup_doc()
    msp = doc.modelspace()
    
    # 1. Main Border
    _draw_rect(msp, 0, 0, A3_W, A3_H)
    
    # CALCULATE EFFECTIVE DRAWING AREA
    eff_x = MARGIN_LEFT
    eff_y = MARGIN_BOTTOM
    eff_w = A3_W - MARGIN_LEFT - MARGIN_RIGHT
    eff_h = A3_H - MARGIN_BOTTOM - MARGIN_TOP
    
    # Draw Inner Border Line
    _draw_rect(msp, eff_x, eff_y, eff_w, eff_h)
    
    # --- MODIFIED LAYOUT CALCULATION (4 Equal Quadrants) ---
    
    # Calculate Midpoints for 4 Quadrant Split
    mid_x = eff_x + eff_w / 2
    mid_y = eff_y + eff_h / 2
    
    # View Width and Height (Half of the effective area)
    view_w = eff_w / 2
    view_h = eff_h / 2
    
    # Box Coordinates: (x, y, w, h)
    
    # Left Top: Cross Section
    box_sec = (eff_x, mid_y, view_w, view_h)
    
    # Right Top: Pier Elevation
    box_pier = (mid_x, mid_y, view_w, view_h)
    
    # Left Bottom: Plan View
    box_plan = (eff_x, eff_y, view_w, view_h)
    
    # The Bottom Right quadrant is left empty (or reserved for Title Block)
    # The Title Block will slightly overlap this quadrant.
    
    # --------------------------------------------------------
    
    # 3. Render Views
    # NOTE: These functions still use the old scaling logic (which may cause distortion)
    _render_section(msp, box_sec, params)
    _render_pier(msp, box_pier, params)
    _render_plan(msp, box_plan, params)
  # 4. Title Block (Bottom Right)
    tb_x = A3_W - MARGIN_RIGHT - TITLEBLOCK_W
    tb_y = MARGIN_BOTTOM

    _draw_rect(msp, tb_x, tb_y, TITLEBLOCK_W, TITLEBLOCK_H)
    doc.styles.new("BOLD_TEXT", dxfattribs={
         "font": "arial.ttf",
    })

    # Drawing Number Text (Perfectly Centered)
    dn = str(params.get("drawing_number", "UNKNOWN"))

    mtext = msp.add_mtext(
        dn,
        dxfattribs={
            "layer": L_TEXT,
            "style": "BOLD_TEXT",
            "char_height": TEXT_H_BIG   # <-- correct attribute
        }
    )

    # True center placement
    mtext.set_location(
        (tb_x + TITLEBLOCK_W / 2, tb_y + TITLEBLOCK_H / 2),
        attachment_point=5   # Middle Center
    )

    doc.saveas(out_path)
    return str(out_path)
