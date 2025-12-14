# src/dxf_generator.py

from pathlib import Path
from typing import Dict, Tuple
import ezdxf

# ---------- CONFIGURATION (A3 LANDSCAPE MM) ----------
A3_W = 420.0
A3_H = 297.0
MARGIN = 15.0 
VIEW_PADDING = 30.0 
TITLEBLOCK_W = 160.0
TITLEBLOCK_H = 40.0

# Layer Definitions
LAYER_BORDER = "BORDER"
LAYER_GRAPH = "GRAPHIC"
LAYER_TEXT = "TEXT"
LAYER_DIM = "DIM"
LAYER_HIDDEN = "HIDDEN"
LAYER_CENTER = "CENTER"

# Colors (White/Black)
COL_MAIN = 7 
TEXT_HEIGHT = 2.5
ARROW_SIZE = 3.0
DIM_OFFSET = 10.0 

DEFAULTS = {
    "length_m": 20.0,
    "carriage_width_m": 9.5,
    "depth_mm": 1200.0,
    "num_girders": 3,
    "pier_cap_length_m": 10.5,
    "pier_cap_width_m": 0.9,
    "pier_cap_depth_center_m": 1.2,
    "pier_cap_depth_end_m": 0.6,
}

# ---------- UTILS ----------
def _to_float(v, default=0.0):
    try: return float(v)
    except: return float(default)

def _to_int(v, default=1):
    try: return int(float(v))
    except: return int(default)

def _mm(m: float) -> float:
    return m * 1000.0

# ---------- DXF SETUP ----------
def _new_doc():
    doc = ezdxf.new(dxfversion="R2010")
    doc.header["$INSUNITS"] = 6
    doc.header["$LTSCALE"] = 20.0 
    
    if "DASHED" not in doc.linetypes:
        doc.linetypes.new("DASHED", dxfattribs={"description": "Dashed", "pattern": [2.0, -2.0]})
    if "CENTER" not in doc.linetypes:
        doc.linetypes.new("CENTER", dxfattribs={"description": "Center", "pattern": [3.0, -1.0, 0.5, -1.0]})

    for name in [LAYER_BORDER, LAYER_GRAPH, LAYER_TEXT, LAYER_DIM]:
        doc.layers.new(name, dxfattribs={"color": COL_MAIN})
    doc.layers.new(LAYER_HIDDEN, dxfattribs={"color": COL_MAIN, "linetype": "DASHED"})
    doc.layers.new(LAYER_CENTER, dxfattribs={"color": COL_MAIN, "linetype": "CENTER"})
    
    if "ROMANS" not in doc.styles:
         doc.styles.new("ROMANS", dxfattribs={"font": "romans.shx", "flags": 0})
    return doc

def _layout_boxes(px1, py1, px2, py2):
    split_y = py1 + (py2 - py1) * 0.50 
    split_x = px1 + (px2 - px1) * 0.5 
    
    box_sec = (px1, split_y, split_x, py2)
    box_pier = (split_x, split_y, px2, py2)
    plan_max_x = px2 - TITLEBLOCK_W - 10.0
    box_plan = (px1, py1, plan_max_x, split_y)
    
    return box_sec, box_pier, box_plan

# ---------- PRIMITIVES ----------
def _arrow(msp, x, y, dir='right', size=ARROW_SIZE):
    s = size
    if dir=='left': pts=[(x+s,y+s*0.3),(x,y),(x+s,y-s*0.3)]
    elif dir=='right': pts=[(x-s,y+s*0.3),(x,y),(x-s,y-s*0.3)]
    elif dir=='up': pts=[(x-s*0.3,y-s),(x,y),(x+s*0.3,y-s)]
    else: pts=[(x-s*0.3,y+s),(x,y),(x+s*0.3,y+s)]
    msp.add_lwpolyline(pts, dxfattribs={"layer":LAYER_DIM, "closed":True})

def _dim_linear(msp, p1, p2, offset=DIM_OFFSET, text="", text_h=TEXT_HEIGHT, vertical=False):
    x1, y1 = p1
    x2, y2 = p2
    
    if vertical:
        dx = x1 + offset
        msp.add_line((x1,y1), (dx,y1), dxfattribs={"layer":LAYER_DIM})
        msp.add_line((x2,y2), (dx,y2), dxfattribs={"layer":LAYER_DIM})
        msp.add_line((dx,y1), (dx,y2), dxfattribs={"layer":LAYER_DIM})
        _arrow(msp, dx, y1, 'up')
        _arrow(msp, dx, y2, 'down')
        if text:
            t_offset = 2.0 if offset > 0 else -2.0
            t = msp.add_text(text, dxfattribs={"height":text_h, "layer":LAYER_TEXT, "style":"ROMANS", "rotation":90})
            t.dxf.insert = (dx + t_offset, (y1+y2)/2)
            t.dxf.halign = 1 
            t.dxf.valign = 1
    else:
        dy = y1 + offset
        msp.add_line((x1,y1), (x1,dy), dxfattribs={"layer":LAYER_DIM})
        msp.add_line((x2,y2), (x2,dy), dxfattribs={"layer":LAYER_DIM})
        msp.add_line((x1,dy), (x2,dy), dxfattribs={"layer":LAYER_DIM})
        _arrow(msp, x1, dy, 'right')
        _arrow(msp, x2, dy, 'left')
        if text:
            t_offset = 1.0 if offset > 0 else -1.0
            t = msp.add_text(text, dxfattribs={"height":text_h, "layer":LAYER_TEXT, "style":"ROMANS"})
            t.dxf.insert = ((x1+x2)/2, dy + t_offset)
            t.dxf.halign = 1 
            t.dxf.valign = 1 if offset > 0 else 4

# ---------- VIEWS ----------

def _draw_section_view(msp, box, params):
    # Data
    W_mm = _mm(_to_float(params.get("carriage_width_m"), DEFAULTS["carriage_width_m"]))
    D_mm = _to_float(params.get("depth_mm"), DEFAULTS["depth_mm"])
    num_g = max(2, _to_int(params.get("num_girders"), DEFAULTS["num_girders"]))
    
    avail_w = (box[2] - box[0]) - VIEW_PADDING
    avail_h = (box[3] - box[1]) - VIEW_PADDING
    
    scale = min(avail_w / W_mm, avail_h / (D_mm * 2.5))
    
    draw_W = W_mm * scale
    draw_D = D_mm * scale
    deck_thk = 200 * scale 
    overhang = 500 * scale 
    
    cx = (box[0] + box[2]) / 2
    cy = (box[1] + box[3]) / 2
    top = cy + draw_D/2
    bot = cy - draw_D/2
    left = cx - draw_W/2
    right = cx + draw_W/2
    
    # 1. Slab
    msp.add_lwpolyline([(left,top), (right,top), (right,top-deck_thk), (left,top-deck_thk), (left,top)], 
                       dxfattribs={"layer":LAYER_GRAPH, "closed":True})
    
    # 2. Girders
    girder_span_width = draw_W - (2 * overhang)
    g_spacing = girder_span_width / (num_g - 1)
    
    flange_w = 300 * scale
    flange_t = 25 * scale
    
    g_centers = []
    
    for i in range(num_g):
        gx = (left + overhang) + i * g_spacing
        g_centers.append(gx)
        
        # Schematic I-Girder
        msp.add_lwpolyline([(gx-flange_w/2, top-deck_thk), (gx+flange_w/2, top-deck_thk), 
                            (gx+flange_w/2, top-deck_thk-flange_t), (gx-flange_w/2, top-deck_thk-flange_t), 
                            (gx-flange_w/2, top-deck_thk)], dxfattribs={"layer":LAYER_GRAPH, "closed":True})
        msp.add_lwpolyline([(gx-flange_w/2, bot), (gx+flange_w/2, bot), 
                            (gx+flange_w/2, bot+flange_t), (gx-flange_w/2, bot+flange_t), 
                            (gx-flange_w/2, bot)], dxfattribs={"layer":LAYER_GRAPH, "closed":True})
        msp.add_lwpolyline([(gx, top-deck_thk-flange_t), (gx, bot+flange_t)], 
                           dxfattribs={"layer":LAYER_GRAPH, "const_width": 2.0 * scale})
        
        t = msp.add_text(f"G{i+1}", dxfattribs={"height":TEXT_HEIGHT, "layer":LAYER_TEXT, "style":"ROMANS"})
        t.dxf.insert = (gx + flange_w/2 + 2.0, (top+bot)/2)
        t.dxf.halign = 0
        t.dxf.valign = 1

    # 3. Bracing
    for i in range(num_g-1):
        gx1 = g_centers[i]
        gx2 = g_centers[i+1]
        msp.add_line((gx1, top-deck_thk), (gx2, bot), dxfattribs={"layer":LAYER_GRAPH})
        msp.add_line((gx1, bot), (gx2, top-deck_thk), dxfattribs={"layer":LAYER_GRAPH})
        
        _dim_linear(msp, (gx1, bot), (gx2, bot), offset=-15.0, text="Eq")

    # 4. Dimensions
    _dim_linear(msp, (left, top), (right, top), offset=15.0, text="Width of Carriageway")
    
    # Depth Leader Style
    dim_x = left - 15.0 
    msp.add_line((left, top), (dim_x, top), dxfattribs={"layer":LAYER_DIM})
    msp.add_line((left, bot), (dim_x, bot), dxfattribs={"layer":LAYER_DIM})
    msp.add_line((dim_x, top), (dim_x, bot), dxfattribs={"layer":LAYER_DIM})
    _arrow(msp, dim_x, top, 'up')
    _arrow(msp, dim_x, bot, 'down')
    t = msp.add_text("Depth of Girder", dxfattribs={"height":TEXT_HEIGHT, "layer":LAYER_TEXT, "style":"ROMANS", "rotation":90})
    t.dxf.insert = (dim_x - 2.0, (top+bot)/2)
    t.dxf.halign = 1
    t.dxf.valign = 1
    
    # Overhangs
    _dim_linear(msp, (left, top-deck_thk/2), (g_centers[0], top-deck_thk/2), offset=0, text="500", text_h=2.0)
    _dim_linear(msp, (g_centers[-1], top-deck_thk/2), (right, top-deck_thk/2), offset=0, text="500", text_h=2.0)

    l = msp.add_text("Section at Midspan", dxfattribs={"height":3.5, "layer":LAYER_TEXT, "style":"ROMANS"})
    l.dxf.insert = (box[0] + 5, box[3] - 10)

def _draw_pier_view(msp, box, params):
    LPC = _mm(_to_float(params.get("pier_cap_length_m"), DEFAULTS["pier_cap_length_m"]))
    DPCC = _mm(_to_float(params.get("pier_cap_depth_center_m"), DEFAULTS["pier_cap_depth_center_m"]))
    DPCE = _mm(_to_float(params.get("pier_cap_depth_end_m"), DEFAULTS["pier_cap_depth_end_m"]))
    
    avail_w = (box[2] - box[0]) - VIEW_PADDING
    avail_h = (box[3] - box[1]) - VIEW_PADDING
    total_h = DPCC + 2000
    scale = min(avail_w / LPC, avail_h / total_h)
    
    cx = (box[0] + box[2]) / 2
    cy = (box[1] + box[3]) / 2 + (total_h*scale)*0.2 
    
    draw_LPC = LPC * scale
    draw_DPCC = DPCC * scale
    draw_DPCE = DPCE * scale
    
    left = cx - draw_LPC/2
    right = cx + draw_LPC/2
    top = cy
    bot_center = top - draw_DPCC
    
    pts = [(left, top), (right, top), (right, top-draw_DPCE), (cx, bot_center), (left, top-draw_DPCE), (left, top)]
    msp.add_lwpolyline(pts, dxfattribs={"layer":LAYER_GRAPH, "closed":True})
    
    cw = 1200 * scale
    ch = 1500 * scale
    msp.add_lwpolyline([(cx-cw/2, bot_center), (cx+cw/2, bot_center), (cx+cw/2, bot_center-ch), (cx-cw/2, bot_center-ch), (cx-cw/2, bot_center)], 
                       dxfattribs={"layer":LAYER_GRAPH})
    
    msp.add_line((cx, top + 5.0), (cx, bot_center - ch - 5.0), dxfattribs={"layer":LAYER_CENTER})

    _dim_linear(msp, (left, top), (right, top), offset=10.0, text=f"LPC={int(LPC)}")
    _dim_linear(msp, (right, top-draw_DPCE), (right, top), offset=10.0, text=f"DPCE={int(DPCE)}", vertical=True)
    
    t = msp.add_text(f"DPCC={int(DPCC)}", dxfattribs={"height":2.5, "layer":LAYER_TEXT, "style":"ROMANS", "rotation":90})
    t.dxf.insert = (cx+2.5, (bot_center+top)/2)
    t.dxf.halign = 0 
    t.dxf.valign = 1 
    
    l = msp.add_text("Pier Elevation", dxfattribs={"height":3.5, "layer":LAYER_TEXT, "style":"ROMANS"})
    l.dxf.insert = (box[0] + 5, box[3] - 10)

def _draw_plan_view(msp, box, params):
    # Data - Convert to mm
    L = _mm(_to_float(params.get("length_m"), DEFAULTS["length_m"]))
    W = _mm(_to_float(params.get("carriage_width_m"), DEFAULTS["carriage_width_m"]))
    WPC = _mm(_to_float(params.get("pier_cap_width_m"), DEFAULTS["pier_cap_width_m"]))
    num_g = max(2, _to_int(params.get("num_girders"), DEFAULTS["num_girders"]))
    
    # Scale Calculation (Using explicit box keys for clarity, assuming the function is part of the class context)
    avail_w = (box[2] - box[0]) - VIEW_PADDING
    avail_h = (box[3] - box[1]) - VIEW_PADDING
    
    draw_h_max = avail_h - 50.0 
    scale = min(avail_w / L, draw_h_max / W)
    
    draw_L = L * scale
    draw_W = W * scale
    draw_WPC = WPC * scale
    
    cx = (box[0] + box[2]) / 2
    # Shift down to make room for stacked top dimensions
    cy = (box[1] + box[3]) / 2 - 15.0 
    
    left = cx - draw_L/2
    right = cx + draw_L/2
    top = cy + draw_W/2
    bot = cy - draw_W/2
    
    # 1. Deck Outline (Full Length and Width)
    msp.add_lwpolyline([(left, bot), (right, bot), (right, top), (left, top), (left, bot)], 
                       dxfattribs={"layer":LAYER_GRAPH, "closed":True})
    
    # 2. Pier Cap / Abutment Areas (Visual demarcation)
    pc_left_end = left + draw_WPC
    pc_right_start = right - draw_WPC
    
    # Draw solid lines for the pier caps to show the supporting structure
    msp.add_lwpolyline([(left, bot), (pc_left_end, bot), (pc_left_end, top), (left, top), (left, bot)], dxfattribs={"layer":LAYER_GRAPH})
    msp.add_lwpolyline([(pc_right_start, bot), (right, bot), (right, top), (pc_right_start, top), (pc_right_start, bot)], dxfattribs={"layer":LAYER_GRAPH})
    
    # 3. Girder Lines (Continuous from end to end)
    g_spacing = draw_W / (num_g - 1)
    for i in range(num_g):
        gy = bot + i * g_spacing
        # Draw girder line from one end of the bridge to the other
        msp.add_line((left, gy), (right, gy), dxfattribs={"layer":LAYER_GRAPH})

    # 4. Dimensions (Strictly Stacked)
    
    # Tier 1 (Inner): Width of Pier Cap (Offset 12.0)
    dim_tier_1 = 12.0
    _dim_linear(msp, (left, top), (pc_left_end, top), offset=dim_tier_1, text=f"Width of Pier Cap")
    _dim_linear(msp, (pc_right_start, top), (right, top), offset=dim_tier_1, text=f"Width of Pier Cap")
    
    # Tier 2 (Outer): Length of Span (Offset 30.0)
    dim_tier_2 = 30.0 
    # Length of Span is the distance between the pier caps
    _dim_linear(msp, (pc_left_end, top), (pc_right_start, top), offset=dim_tier_2, text=f"Length of Bridge = {int(L)}")
    
    # Side Dimension: Carriageway Width
    _dim_linear(msp, (right, bot), (right, top), offset=12.0, text="Carriageway Width", vertical=True)
    
    # View Label
    l = msp.add_text("Bridge Plan", dxfattribs={"height":3.5, "layer":LAYER_TEXT, "style":"ROMANS"})
    l.dxf.insert = (box[0] + 5, box[3] - 10)


# ---------- MAIN ----------
def create_bridge_dxf(params: Dict, out_path: str):
    p = {}
    for k,v in DEFAULTS.items(): 
        val = params.get(k, params.get(k.capitalize(), v))
        p[k] = val
        
    p["drawing_number"] = params.get("drawing_number", "UNNAMED")
    p["length_m"] = _to_float(params.get("length of Bridg", DEFAULTS["length_m"]))
    p["depth_mm"] = _to_float(params.get("Depth of Bridg", DEFAULTS["depth_mm"]))
    p["carriage_width_m"] = _to_float(params.get("Width of Carria", DEFAULTS["carriage_width_m"]))
    p["num_girders"] = _to_int(params.get("Circ Length of Pier", params.get("num_girders", 3)))
    p["pier_cap_length_m"] = _to_float(params.get("Depth of Pier C", DEFAULTS["pier_cap_length_m"])) 
    p["pier_cap_width_m"] = _to_float(params.get("Width of Pier Cap", DEFAULTS["pier_cap_width_m"]))
    p["pier_cap_depth_center_m"] = _to_float(params.get("Depth of Pier C.1", DEFAULTS["pier_cap_depth_center_m"]))
    p["pier_cap_depth_end_m"] = _to_float(params.get("Depth of Pier C", DEFAULTS["pier_cap_depth_end_m"]))
    
    doc = _new_doc()
    msp = doc.modelspace()
    
    msp.add_lwpolyline([(0,0),(A3_W,0),(A3_W,A3_H),(0,A3_H),(0,0)], dxfattribs={"layer":LAYER_BORDER})
    px1, py1 = MARGIN, MARGIN
    px2, py2 = A3_W - MARGIN, A3_H - MARGIN
    msp.add_lwpolyline([(px1,py1),(px2,py1),(px2,py2),(px1,py2),(px1,py1)], dxfattribs={"layer":LAYER_BORDER})
    
    box_sec, box_pier, box_plan = _layout_boxes(px1, py1, px2, py2)
    
    _draw_section_view(msp, box_sec, p)
    _draw_pier_view(msp, box_pier, p)
    _draw_plan_view(msp, box_plan, p)
    
    tx1, ty1 = px2 - TITLEBLOCK_W, py1
    tx2, ty2 = px2, py1 + TITLEBLOCK_H
    msp.add_lwpolyline([(tx1,ty1),(tx2,ty1),(tx2,ty2),(tx1,ty2),(tx1,ty1)], dxfattribs={"layer":LAYER_BORDER})
    
    t = msp.add_text(str(p["drawing_number"]), dxfattribs={"height":7.0, "layer":LAYER_TEXT, "style":"ROMANS"})
    t.dxf.insert = ((tx1+tx2)/2, (ty1+ty2)/2)
    t.dxf.halign = 1
    t.dxf.valign = 1
    
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    doc.saveas(str(out_path))
    return str(out_path)