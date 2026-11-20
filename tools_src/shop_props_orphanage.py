"""19th-century southern colonial orphanage furniture library: dormitory, refectory, kitchen, classroom, chapel,
washroom, infirmary, laundry, playroom, office and lighting props.

Runs inside Blender, imported by build_prop_sheet.py and layout builders. Follows the contract in
shop_props_common.py: X width centred on 0, customer/front side faces -Y, back at +size[1] / 2, Z up from
the floor at 0 (wall props built at their mounting height; ceiling props have hang=True with z = 0 at the
ceiling mount growing down).
"""

import itertools
import math
import random
import sys
from pathlib import Path

from mathutils import Matrix

sys.path.insert(0, str(Path(__file__).resolve().parent))

from build_town_houses import Builder, srgb  # noqa: E402
from shop_props_common import (  # noqa: E402
    WOOD_DARK_UV,
    WOOD_LIGHT_UV,
    base_profile,
    bevel_box,
    cornice_profile,
    knob,
    lathe,
    metal_box,
    raised_panel,
    ring,
    rivets,
    run_profile,
    solid_hull,
    turned_leg,
    wood_box,
)

# ---------- muted 19th-century colonial palette ----------

WALNUT_DARK = "7A4E33"
WALNUT_MID = "9C6B46"
HONEY_WOOD = "BA8754"
PINE_SCRUB = "CFA572"
WROUGHT_IRON = "3A363C"
CAST_IRON = "4A464E"
BRASS_AGED = "C89B45"
BRASS_BRIGHT = "D9AE54"
COPPER_WARE = "BF6D42"
TIN_PAINTED = "8C9AA3"
PEWTER = "9EA6AD"

ENAMEL_CREAM = "EDE6D6"
ENAMEL_RIM = "3B5A7A"
AZULEJO_BLUE = "3A5E8C"
AZULEJO_WHITE = "ECE6D8"
TERRACOTTA = "B86544"
TERRACOTTA_DARK = "944D32"
STONE_WARM = "CFC5B2"
STONE_LIGHT = "DFD7C6"
MARBLE_CREAM = "EAE3D5"
PLASTER_WARM = "E5DEC9"
BRICK_OLD = "9E5442"

LINEN_CREAM = "E8E0CE"
LINEN_RAW = "D6C9AE"
PARCHMENT = "E6D8B8"
SLATE_DARK = "364240"
LEATHER_BROWN = "6E422C"
LEATHER_GREEN = "375743"
CHAPEL_WINE = "6E2D38"
LAMP_SHADE_GREEN = "355E43"
OPAL_GLASS = "F3EDE0"
LAMP_LIGHT = "FFE8CC"

BLANKET_COLOURS = {
    "grey_blue": "5A738E",
    "ochre": "B88B4A",
    "dull_red": "8E423F",
    "green": "4D6E56",
}
CURTAIN_COLOURS = {
    "cream": ("E3DAC6", "C2B295"),
    "dull_green": ("536E59", "9E8D66"),
    "wine": ("73343C", "B5975E"),
}
BOOK_COLOURS = ("6E333A", "3A4E6E", "43614B", "73573E", "5B4861", "8A6C42")
BOTTLE_COLOURS = ("4A7A68", "3B5882", "8E5D38", "6E7A50", "9C6658")


# ---------- shared local helpers ----------

def _at(frame: Matrix, offset: tuple = (0.0, 0.0, 0.0), degrees: float = 0.0, axis: str = "Z") -> Matrix:
    return frame @ Matrix.Translation(offset) @ Matrix.Rotation(math.radians(degrees), 4, axis)


def _box(b: Builder, frame: Matrix, low: tuple, high: tuple, material: str, hex_col: str, uv: tuple = None):
    return b.box(low, high, material, srgb(hex_col), frame=frame, uv=uv)


def _cyl(b: Builder, frame: Matrix, base: tuple, radius: float, height: float, sides: int, material: str, hex_col: str, top_radius: float = None, axis: str = "Z", uv: tuple = None):
    return b.cylinder(base, radius, height, sides, material, srgb(hex_col), top_radius=top_radius, frame=frame, axis=axis, uv=uv)


def _sphere(b: Builder, frame: Matrix, center: tuple, radius: float, material: str, hex_col: str, scale: tuple = (1.0, 1.0, 1.0), segments: int = 8):
    return b.sphere(center, radius, material, srgb(hex_col), scale=scale, frame=frame, segments=segments)


def _beam(b: Builder, frame: Matrix, start: tuple, end: tuple, width: float, depth: float, material: str, hex_col: str, uv: tuple = None):
    return b.beam(start, end, width, depth, material, srgb(hex_col), frame=frame, uv=uv)


def _arch_pts(half_w: float, spring: float, rise: float, segs: int = 10) -> list:
    return [(half_w * math.cos(math.pi * i / segs), spring + rise * math.sin(math.pi * i / segs)) for i in range(segs + 1)]


def _soft_block(b: Builder, frame: Matrix, center: tuple, half: tuple, hex_col: str, bevel: float = 0.025) -> None:
    low = tuple(c - h for c, h in zip(center, half))
    high = tuple(c + h for c, h in zip(center, half))
    bevel_box(b, frame, low, high, hex_col, bevel=bevel, material="paint")


def _pillow(b: Builder, frame: Matrix, x: float, y: float, z: float, sx: float, sy: float, sz: float, hex_col: str = LINEN_CREAM) -> None:
    _sphere(b, frame, (x, y, z), 1.0, "paint", hex_col, scale=(sx, sy, sz), segments=10)


def _enamel_plate(b: Builder, frame: Matrix, x: float, y: float, z: float, radius: float = 0.11, body: str = ENAMEL_CREAM, rim: str = ENAMEL_RIM, sides: int = 12) -> None:
    profile = [(0.001, 0.0), (radius * 0.62, 0.0), (radius * 0.96, 0.016), (radius, 0.019), (radius * 0.62, 0.005), (0.001, 0.005)]
    lathe(b, profile, sides, "paint", body, frame, base=(x, y, z))
    ring(b, (x, y, z + 0.017), radius * 0.96, 0.003, "paint", rim, frame, sides=sides, tube_sides=3)


def _enamel_bowl(b: Builder, frame: Matrix, x: float, y: float, z: float, radius: float = 0.085, height: float = 0.055, body: str = ENAMEL_CREAM, rim: str = ENAMEL_RIM, sides: int = 14) -> None:
    profile = [(0.001, 0.0), (radius * 0.55, 0.0), (radius * 0.85, height * 0.45), (radius, height), (radius * 0.92, height), (radius * 0.52, 0.01), (0.001, 0.01)]
    lathe(b, profile, sides, "paint", body, frame, base=(x, y, z))
    ring(b, (x, y, z + height - 0.002), radius * 0.97, 0.004, "paint", rim, frame, sides=sides, tube_sides=3)


def _enamel_mug(b: Builder, frame: Matrix, x: float, y: float, z: float, body: str = ENAMEL_CREAM, rim: str = ENAMEL_RIM, handle_dir: float = 1.0, sides: int = 10) -> None:
    r, h = 0.042, 0.085
    lathe(b, [(0.001, 0.0), (r, 0.0), (r, h), (r * 0.86, h), (r * 0.86, 0.008), (0.001, 0.008)], sides, "paint", body, frame, base=(x, y, z))
    ring(b, (x, y, z + h - 0.002), r, 0.003, "paint", rim, frame, sides=sides, tube_sides=3)
    ring(b, (x + handle_dir * r, y, z + h * 0.52), 0.022, 0.005, "paint", rim, frame, sides=8, tube_sides=3, axis="Y")


def _ceramic_jug(b: Builder, frame: Matrix, x: float, y: float, z: float, scale: float = 1.0, body: str = ENAMEL_CREAM, band: str = AZULEJO_BLUE, sides: int = 16) -> None:
    profile = [
        (0.001, 0.0), (0.052 * scale, 0.0), (0.075 * scale, 0.07 * scale),
        (0.078 * scale, 0.13 * scale), (0.042 * scale, 0.21 * scale),
        (0.055 * scale, 0.25 * scale), (0.048 * scale, 0.25 * scale), (0.036 * scale, 0.21 * scale),
    ]
    lathe(b, profile, sides, "paint", body, frame, base=(x, y, z))
    ring(b, (x, y, z + 0.12 * scale), 0.078 * scale, 0.006 * scale, "paint", band, frame, sides=sides, tube_sides=3)
    ring(b, (x + 0.052 * scale, y, z + 0.15 * scale), 0.038 * scale, 0.007 * scale, "paint", body, frame, sides=8, tube_sides=3, axis="Y")
    solid_hull(b, [(x - 0.04 * scale, y, z + 0.22 * scale), (x - 0.08 * scale, y, z + 0.255 * scale), (x - 0.045 * scale, y - 0.015 * scale, z + 0.245 * scale), (x - 0.045 * scale, y + 0.015 * scale, z + 0.245 * scale)], "paint", body, frame)


def _copper_pot(b: Builder, frame: Matrix, x: float, y: float, z: float, radius: float = 0.14, height: float = 0.16, material: str = "metal", tint: str = COPPER_WARE, lid: bool = True, sides: int = 16) -> None:
    profile = [(0.001, 0.0), (radius * 0.88, 0.0), (radius, height * 0.25), (radius, height * 0.92), (radius * 1.07, height)]
    lathe(b, profile, sides, material, tint, frame, base=(x, y, z))
    for side in (-1.0, 1.0):
        ring(b, (x + side * radius, y, z + height * 0.72), 0.028, 0.007, "metal", CAST_IRON, frame, sides=8, tube_sides=3, axis="X")
    if lid:
        lathe(b, [(radius * 1.04, height), (radius * 0.9, height + 0.025), (0.001, height + 0.035)], sides, material, tint, frame, base=(x, y, z))
        _sphere(b, frame, (x, y, z + height + 0.048), 0.018, "metal", BRASS_AGED, segments=6)


def _copper_pan(b: Builder, frame: Matrix, x: float, y: float, z: float, radius: float = 0.13, height: float = 0.045, handle_len: float = 0.22, yaw: float = 0.0, tint: str = COPPER_WARE, sides: int = 16) -> None:
    pan_f = _at(frame, (x, y, z), yaw)
    lathe(b, [(0.001, 0.0), (radius * 0.86, 0.0), (radius, height), (radius * 0.93, height), (radius * 0.82, 0.008), (0.001, 0.008)], sides, "metal", tint, pan_f)
    _beam(b, pan_f, (radius * 0.95, 0.0, height * 0.75), (radius + handle_len, 0.0, height + 0.04), 0.018, 0.012, "metal", WROUGHT_IRON)


def _book_closed(b: Builder, frame: Matrix, x: float, y: float, z: float, w: float, d: float, h: float, color: str, yaw: float = 0.0) -> None:
    bf = _at(frame, (x, y, z), yaw)
    _box(b, bf, (-w / 2.0, -d / 2.0, 0.0), (w / 2.0, d / 2.0, 0.005), "paint", color)
    _box(b, bf, (-w / 2.0, -d / 2.0, h - 0.005), (w / 2.0, d / 2.0, h), "paint", color)
    _box(b, bf, (-w / 2.0 - 0.004, -d / 2.0, 0.0), (-w / 2.0 + 0.006, d / 2.0, h), "paint", color)
    _box(b, bf, (-w / 2.0 + 0.006, -d / 2.0 + 0.006, 0.005), (w / 2.0 - 0.006, d / 2.0 - 0.006, h - 0.005), "paint", PARCHMENT)


def _book_open(b: Builder, frame: Matrix, x: float, y: float, z: float, w: float, d: float, color: str, yaw: float = 0.0) -> None:
    bf = _at(frame, (x, y, z), yaw)
    for side in (-1.0, 1.0):
        wing = _at(bf, (0.0, 0.0, 0.004), side * -11.0, "Y")
        lo_x, hi_x = sorted((0.0, side * w / 2.0))
        _box(b, wing, (lo_x, -d / 2.0, -0.004), (hi_x, d / 2.0, 0.0), "paint", color)
        _box(b, wing, (lo_x * 0.94, -d / 2.0 + 0.008, 0.0), (hi_x * 0.94, d / 2.0 - 0.008, 0.018), "paint", PARCHMENT)
    _box(b, bf, (-0.006, -d / 2.0 - 0.02, 0.0), (0.006, d / 2.0, 0.008), "paint", "8E343C")


def _candlestick(b: Builder, frame: Matrix, x: float, y: float, z: float, stand_h: float = 0.16, candle_h: float = 0.11) -> None:
    cf = _at(frame, (x, y, z))
    profile = [(0.001, 0.0), (0.048, 0.0), (0.045, 0.014), (0.016, 0.04), (0.012, stand_h * 0.65), (0.02, stand_h * 0.78), (0.013, stand_h * 0.9), (0.032, stand_h), (0.001, stand_h)]
    lathe(b, profile, 16, "metal", BRASS_AGED, cf)
    _cyl(b, cf, (0.0, 0.0, stand_h), 0.011, candle_h, 8, "paint", LINEN_CREAM)
    _cyl(b, cf, (0.0, 0.0, stand_h + candle_h), 0.009, 0.026, 6, "glow_warm", "FFFFFF", top_radius=0.002)


def _oil_lamp_unit(b: Builder, frame: Matrix, x: float, y: float, z: float, shade_col: str = OPAL_GLASS, scale: float = 1.0) -> None:
    lf = _at(frame, (x, y, z)) @ Matrix.Scale(scale, 4)
    base_prof = [(0.001, 0.0), (0.072, 0.0), (0.068, 0.018), (0.032, 0.04), (0.022, 0.13), (0.075, 0.17), (0.08, 0.21), (0.042, 0.25), (0.046, 0.27), (0.001, 0.27)]
    lathe(b, base_prof, 16, "metal", BRASS_AGED, lf)
    lathe(b, [(0.028, 0.26), (0.036, 0.31), (0.022, 0.4), (0.024, 0.48), (0.018, 0.48), (0.028, 0.31), (0.024, 0.26)], 16, "vitrine", "FFFFFF", lf)
    _cyl(b, lf, (0.0, 0.0, 0.28), 0.012, 0.04, 6, "glow_warm", "FFFFFF", top_radius=0.003)
    shade_prof = [(0.105, 0.28), (0.095, 0.34), (0.055, 0.41), (0.042, 0.41), (0.088, 0.34), (0.098, 0.28)]
    lathe(b, shade_prof, 16, "paint", shade_col, lf, closed=True)


def _azulejo_panel(b: Builder, frame: Matrix, x0: float, x1: float, z0: float, z1: float, y: float, cols: int, rows: int, facing: float = -1.0) -> None:
    back_lo, back_hi = sorted((y, y - facing * 0.01))
    _box(b, frame, (x0, back_lo, z0), (x1, back_hi, z1), "paint", STONE_LIGHT)
    tw, th = (x1 - x0) / cols, (z1 - z0) / rows
    tile_lo, tile_hi = sorted((y + facing * 0.012, y))
    for c, r in itertools.product(range(cols), range(rows)):
        cx0, cz0 = x0 + c * tw + 0.005, z0 + r * th + 0.005
        cx1, cz1 = x0 + (c + 1) * tw - 0.005, z0 + (r + 1) * th - 0.005
        _box(b, frame, (cx0, tile_lo, cz0), (cx1, tile_hi, cz1), "paint", AZULEJO_WHITE)
        inset = min(tw, th) * 0.22
        _box(b, frame, (cx0 + inset, tile_lo + facing * 0.002 if facing < 0 else tile_lo, cz0 + inset), (cx1 - inset, tile_hi + (facing * 0.002 if facing > 0 else 0.0), cz1 - inset), "paint", AZULEJO_BLUE)


def _wicker_basket(b: Builder, frame: Matrix, x: float, y: float, z: float, r_bot: float = 0.14, r_top: float = 0.2, height: float = 0.26, tint: str = "B88A52") -> None:
    prof = [(0.001, 0.0), (r_bot, 0.0), (r_top * 0.92, height * 0.55), (r_top, height), (r_top * 0.88, height), (r_bot * 0.9, 0.02), (0.001, 0.02)]
    lathe(b, prof, 14, "paint", tint, frame, base=(x, y, z))
    ring(b, (x, y, z + height - 0.01), r_top * 0.97, 0.012, "paint", "986C3A", frame, sides=14, tube_sides=4)


def _glass_bottle(b: Builder, frame: Matrix, x: float, y: float, z: float, r: float = 0.04, h: float = 0.22, hex_col: str = "4A7A68", cork: bool = True, label: bool = False) -> None:
    prof = [(0.001, 0.0), (r, 0.0), (r, h * 0.58), (r * 0.36, h * 0.72), (r * 0.34, h * 0.95), (r * 0.44, h), (0.001, h)]
    lathe(b, prof, 12, "paint", hex_col, frame, base=(x, y, z))
    if cork:
        _cyl(b, frame, (x, y, z + h), r * 0.3, h * 0.1, 8, "wood", HONEY_WOOD, uv=WOOD_LIGHT_UV)
    if label:
        _box(b, frame, (x - r * 0.55, y - r - 0.003, z + h * 0.22), (x + r * 0.55, y - r + 0.004, z + h * 0.48), "paint", PARCHMENT)


def _draped_towel(b: Builder, frame: Matrix, x: float, y: float, z_bar: float, width: float, drop: float, hex_col: str = LINEN_CREAM, axis: str = "X", stripe: str = AZULEJO_BLUE) -> None:
    if axis == "X":
        _cyl(b, frame, (x - width / 2.0, y, z_bar), 0.02, width, 10, "paint", hex_col, axis="X")
        _box(b, frame, (x - width / 2.0, y - 0.02, z_bar - drop), (x + width / 2.0, y - 0.004, z_bar), "paint", hex_col)
        _box(b, frame, (x - width / 2.0, y + 0.004, z_bar - drop * 0.85), (x + width / 2.0, y + 0.018, z_bar), "paint", hex_col)
        if stripe:
            _box(b, frame, (x - width / 2.0, y - 0.022, z_bar - drop + 0.03), (x + width / 2.0, y - 0.018, z_bar - drop + 0.05), "paint", stripe)
    else:
        _cyl(b, frame, (x, y - width / 2.0, z_bar), 0.02, width, 10, "paint", hex_col, axis="Y")
        _box(b, frame, (x - 0.02, y - width / 2.0, z_bar - drop), (x - 0.004, y + width / 2.0, z_bar), "paint", hex_col)
        _box(b, frame, (x + 0.004, y - width / 2.0, z_bar - drop * 0.85), (x + 0.018, y + width / 2.0, z_bar), "paint", hex_col)
        if stripe:
            _box(b, frame, (x - 0.022, y - width / 2.0, z_bar - drop + 0.03), (x - 0.018, y + width / 2.0, z_bar - drop + 0.05), "paint", stripe)


def _cabinet_base(b: Builder, frame: Matrix, half_w: float, half_d: float, foot_h: float = 0.08, plinth_h: float = 0.1) -> None:
    for sx, sy in itertools.product((-1.0, 1.0), repeat=2):
        lathe(b, [(0.024, 0.0), (0.044, foot_h * 0.5), (0.034, foot_h)], 10, "wood", WALNUT_DARK, frame, base=(sx * (half_w - 0.07), sy * (half_d - 0.07), 0.0), uv=WOOD_DARK_UV)
    bevel_box(b, frame, (-half_w, -half_d, foot_h), (half_w, half_d, foot_h + plinth_h), WALNUT_DARK, bevel=0.01)
    run_profile(b, frame, -half_w + 0.02, half_w - 0.02, base_profile(-half_d, foot_h, 0.015, plinth_h), WALNUT_DARK)


# ---------- dormitory ----------

def iron_bed(b: Builder, frame: Matrix, variant: str = None, **options) -> None:
    """Single colonial wrought-iron bedstead with brass finials, mattress, turned-down sheet, blanket and slippers."""
    blanket_hex = BLANKET_COLOURS.get(variant or "grey_blue", BLANKET_COLOURS["grey_blue"])
    half_w, half_l = 0.46, 0.98
    post_x = 0.44
    head_y, foot_y = 0.95, -0.95

    for px, py, top_z in ((-post_x, head_y, 1.09), (post_x, head_y, 1.09), (-post_x, foot_y, 0.78), (post_x, foot_y, 0.78)):
        _cyl(b, frame, (px, py, 0.02), 0.018, top_z - 0.02, 10, "metal", WROUGHT_IRON)
        _cyl(b, frame, (px, py, 0.0), 0.024, 0.025, 10, "metal", BRASS_AGED)
        _sphere(b, frame, (px, py, top_z + 0.03), 0.032, "metal", BRASS_BRIGHT, segments=8)

    # Headboard and footboard crossbars and spindles
    for rail_y, rail_zs, bar_top in ((head_y, (0.34, 0.96), 0.96), (foot_y, (0.34, 0.74), 0.74)):
        for rz in rail_zs:
            _cyl(b, frame, (-post_x, rail_y, rz), 0.014, post_x * 2.0, 8, "metal", WROUGHT_IRON, axis="X")
        for bar_i in range(5):
            bx = -0.3 + bar_i * 0.15
            _cyl(b, frame, (bx, rail_y, 0.34), 0.008, bar_top - 0.34, 6, "metal", WROUGHT_IRON)
    # Curved crest arch on headboard
    crest = [(-post_x + (post_x * 2.0) * i / 8.0, 0.96 + 0.12 * math.sin(math.pi * i / 8.0)) for i in range(9)]
    for (x0, z0), (x1, z1) in zip(crest, crest[1:]):
        _beam(b, frame, (x0, head_y, z0), (x1, head_y, z1), 0.02, 0.02, "metal", WROUGHT_IRON)
    ring(b, (0.0, head_y, 0.76), 0.08, 0.009, "metal", BRASS_AGED, frame, sides=12, tube_sides=3, axis="Y")

    # Side rails and wooden slats
    for side in (-1.0, 1.0):
        _box(b, frame, (side * post_x - 0.015, foot_y, 0.29), (side * post_x + 0.015, head_y, 0.34), "metal", WROUGHT_IRON)
    for slat_y in (-0.7, -0.35, 0.0, 0.35, 0.7):
        wood_box(b, frame, (-post_x + 0.02, slat_y - 0.04, 0.295), (post_x - 0.02, slat_y + 0.04, 0.315), HONEY_WOOD, light=True)

    # Soft mattress, turned-down sheet, blanket and folded coverlet roll at foot
    _soft_block(b, frame, (0.0, 0.0, 0.405), (half_w - 0.02, half_l - 0.05, 0.085), "E2D9C6", bevel=0.03)
    _soft_block(b, frame, (0.0, -0.26, 0.425), (half_w - 0.005, 0.67, 0.092), blanket_hex, bevel=0.03)
    _soft_block(b, frame, (0.0, 0.37, 0.455), (half_w - 0.01, 0.13, 0.062), LINEN_CREAM, bevel=0.025)
    _cyl(b, frame, (-half_w + 0.02, -0.78, 0.545), 0.065, half_w * 2.0 - 0.04, 12, "paint", blanket_hex, axis="X")
    _pillow(b, frame, 0.0, 0.7, 0.54, 0.33, 0.18, 0.075, LINEN_CREAM)

    # Pair of slippers tucked neatly under the side edge
    for s_idx, (sx, sy) in enumerate(((-0.26, -0.42), (-0.13, -0.47))):
        sf = _at(frame, (sx, sy, 0.0), -12.0 + s_idx * 18.0)
        _box(b, sf, (-0.045, -0.1, 0.0), (0.045, 0.1, 0.016), "paint", LEATHER_BROWN)
        _sphere(b, sf, (0.0, -0.02, 0.022), 1.0, "paint", "5E4034", scale=(0.045, 0.07, 0.024), segments=6)


def bed_trunk(b: Builder, frame: Matrix, **options) -> None:
    """Wooden foot locker with iron strap bands, brass lock plate and rope side handles."""
    wood_box(b, frame, (-0.36, -0.185, 0.0), (0.36, 0.185, 0.03), WALNUT_DARK)
    bevel_box(b, frame, (-0.38, -0.205, 0.03), (0.38, 0.205, 0.34), WALNUT_MID, bevel=0.01)
    bevel_box(b, frame, (-0.39, -0.21, 0.34), (0.39, 0.21, 0.44), HONEY_WOOD, bevel=0.018, light=True)

    for band_x in (-0.27, 0.27):
        metal_box(b, frame, (band_x - 0.022, -0.215, 0.03), (band_x + 0.022, 0.215, 0.448), WROUGHT_IRON)
        rivets(b, frame, [(band_x, z) for z in (0.08, 0.2, 0.3, 0.39)], -0.216, 0.008, PEWTER)

    metal_box(b, frame, (-0.045, -0.218, 0.26), (0.045, -0.208, 0.36), BRASS_AGED)
    metal_box(b, frame, (-0.018, -0.223, 0.3), (0.018, -0.21, 0.38), BRASS_BRIGHT)
    _box(b, frame, (-0.006, -0.224, 0.28), (0.006, -0.216, 0.31), "paint", WROUGHT_IRON)

    for side in (-1.0, 1.0):
        metal_box(b, frame, (side * 0.38, -0.06, 0.2), (side * 0.392, 0.06, 0.25), WROUGHT_IRON)
        _beam(b, frame, (side * 0.38, -0.05, 0.21), (side * 0.39, 0.0, 0.14), 0.016, 0.016, "paint", LINEN_RAW)
        _beam(b, frame, (side * 0.39, 0.0, 0.14), (side * 0.38, 0.05, 0.21), 0.016, 0.016, "paint", LINEN_RAW)


def night_table(b: Builder, frame: Matrix, **options) -> None:
    """Small bedside table with drawer, brass candlestick and closed book."""
    top_z = 0.68
    for lx, ly in itertools.product((-0.16, 0.16), (-0.14, 0.14)):
        turned_leg(b, frame, lx, ly, top_z - 0.03, 0.022, WALNUT_DARK, "taper", sides=8)

    wood_box(b, frame, (-0.17, -0.15, 0.16), (0.17, 0.15, 0.19), WALNUT_MID)
    bevel_box(b, frame, (-0.18, -0.16, 0.48), (0.18, 0.16, top_z - 0.03), WALNUT_MID, bevel=0.006)
    bevel_box(b, frame, (-0.16, -0.17, 0.5), (0.16, -0.155, 0.63), HONEY_WOOD, bevel=0.006, light=True)
    knob(b, frame, 0.0, -0.172, 0.565, 0.013, BRASS_AGED)
    bevel_box(b, frame, (-0.21, -0.19, top_z - 0.03), (0.21, 0.19, top_z), HONEY_WOOD, bevel=0.01, light=True)

    _book_closed(b, frame, -0.04, 0.02, top_z, 0.16, 0.22, 0.032, BOOK_COLOURS[0], yaw=14.0)
    _candlestick(b, frame, 0.1, -0.05, top_z, stand_h=0.14, candle_h=0.1)


def linen_press(b: Builder, frame: Matrix, **options) -> None:
    """Tall two-door panelled colonial wardrobe with lower drawers, cornice and turned feet."""
    half_w, half_d = 0.78, 0.27
    _cabinet_base(b, frame, half_w, half_d, foot_h=0.09, plinth_h=0.1)
    bevel_box(b, frame, (-half_w + 0.02, -half_d + 0.02, 0.19), (half_w - 0.02, half_d, 2.12), WALNUT_MID, bevel=0.008)

    for px in (-half_w + 0.05, 0.0, half_w - 0.05):
        bevel_box(b, frame, (px - 0.035, -half_d - 0.005, 0.19), (px + 0.035, -half_d + 0.02, 2.1), WALNUT_DARK, bevel=0.006)

    # Two lower drawers + two tall two-panel cupboard doors
    for side in (-1.0, 1.0):
        x0, x1 = (side * 0.39 - 0.31, side * 0.39 + 0.31)
        raised_panel(b, frame, x0, x1, 0.22, 0.44, -half_d + 0.01, HONEY_WOOD, border=0.03, depth=0.012)
        knob(b, frame, (x0 + x1) / 2.0, -half_d - 0.008, 0.33, 0.015, BRASS_AGED)
        raised_panel(b, frame, x0, x1, 0.5, 1.24, -half_d + 0.01, WALNUT_MID, border=0.045, depth=0.012)
        raised_panel(b, frame, x0, x1, 1.28, 2.04, -half_d + 0.01, WALNUT_MID, border=0.045, depth=0.012)
        knob(b, frame, side * 0.11, -half_d - 0.01, 1.26, 0.016, BRASS_BRIGHT)

    run_profile(b, frame, -half_w, half_w, cornice_profile(-half_d + 0.01, 2.1, 0.025, 0.09), WALNUT_DARK)
    bevel_box(b, frame, (-0.8, -0.3, 2.19), (0.8, 0.3, 2.25), HONEY_WOOD, bevel=0.012, light=True)


def wall_crucifix(b: Builder, frame: Matrix, **options) -> None:
    """Wooden wall cross with a small canopy shelf, mounted at 1.60..2.30 m (back at +Y edge)."""
    wall_y = 0.04
    # Small canopy shelf at top (2.23..2.30)
    bevel_box(b, frame, (-0.19, -0.04, 2.25), (0.19, wall_y, 2.29), WALNUT_DARK, bevel=0.006)
    for bx in (-0.14, 0.14):
        b.side_prism([(wall_y, 2.25), (-0.03, 2.25), (wall_y, 2.15)], bx - 0.015, bx + 0.015, "wood", srgb(WALNUT_DARK), frame=frame, uv=WOOD_DARK_UV)

    # Stepped wooden cross
    wood_box(b, frame, (-0.035, 0.015, 1.6), (0.035, wall_y, 2.24), WALNUT_DARK)
    wood_box(b, frame, (-0.18, 0.015, 1.98), (0.18, wall_y, 2.05), WALNUT_DARK)
    wood_box(b, frame, (-0.022, 0.008, 1.62), (0.022, 0.016, 2.22), HONEY_WOOD, light=True)
    wood_box(b, frame, (-0.165, 0.008, 1.992), (0.165, 0.016, 2.038), HONEY_WOOD, light=True)
    metal_box(b, frame, (-0.025, 0.003, 2.14), (0.025, 0.009, 2.17), BRASS_AGED)

    # Carved ivory/pale corpus and halo
    ring(b, (0.0, 0.004, 2.09), 0.036, 0.004, "metal", BRASS_BRIGHT, frame, sides=12, tube_sides=3, axis="Y")
    _sphere(b, frame, (0.0, -0.002, 2.09), 0.018, "paint", LINEN_CREAM, segments=6)
    _cyl(b, frame, (0.0, -0.002, 1.93), 0.016, 0.14, 6, "paint", LINEN_CREAM, top_radius=0.02)
    _cyl(b, frame, (0.0, -0.002, 1.81), 0.013, 0.12, 6, "paint", LINEN_CREAM)
    for side in (-1.0, 1.0):
        _beam(b, frame, (0.0, -0.002, 2.03), (side * 0.13, -0.002, 2.025), 0.014, 0.014, "paint", LINEN_CREAM)


def clothes_pegs(b: Builder, frame: Matrix, **options) -> None:
    """Wall peg rail at 1.6 m with shelf, pegs, three hanging coats/nightshirts and caps."""
    wall_y = 0.125
    coat_styles = ((-0.5, "4F6278", 0.86, True), (0.0, LINEN_CREAM, 0.78, False), (0.5, "5B4942", 0.9, True))

    wood_box(b, frame, (-0.8, wall_y - 0.03, 1.54), (0.8, wall_y, 1.66), WALNUT_DARK)
    bevel_box(b, frame, (-0.8, wall_y - 0.16, 1.66), (0.8, wall_y, 1.695), HONEY_WOOD, bevel=0.006, light=True)
    for bx in (-0.68, 0.0, 0.68):
        b.side_prism([(wall_y - 0.03, 1.66), (wall_y - 0.14, 1.66), (wall_y - 0.03, 1.48)], bx - 0.018, bx + 0.018, "wood", srgb(WALNUT_DARK), frame=frame, uv=WOOD_DARK_UV)

    for peg_i in range(6):
        px = -0.65 + peg_i * 0.26
        _cyl(b, frame, (px, wall_y - 0.12, 1.6), 0.011, 0.095, 8, "wood", HONEY_WOOD, axis="Y", uv=WOOD_LIGHT_UV)
        _sphere(b, frame, (px, wall_y - 0.125, 1.6), 0.017, "wood", WALNUT_DARK, segments=6)

    for gx, gcol, drop, has_collar in coat_styles:
        pts = [
            (gx - 0.07, wall_y - 0.11, 1.59), (gx + 0.07, wall_y - 0.11, 1.59),
            (gx - 0.09, wall_y - 0.03, 1.56), (gx + 0.09, wall_y - 0.03, 1.56),
            (gx - 0.16, wall_y - 0.14, 1.59 - drop), (gx + 0.16, wall_y - 0.14, 1.59 - drop),
            (gx - 0.15, wall_y - 0.02, 1.59 - drop), (gx + 0.15, wall_y - 0.02, 1.59 - drop),
        ]
        solid_hull(b, pts, "paint", gcol, frame)
        if has_collar:
            _box(b, frame, (gx - 0.06, wall_y - 0.12, 1.53), (gx + 0.06, wall_y - 0.06, 1.61), "paint", "3D4B5C")

    for cap_x, cap_col in ((-0.45, "424A56"), (0.12, "5E4B3C"), (0.55, "6E333A")):
        _sphere(b, frame, (cap_x, wall_y - 0.08, 1.72), 1.0, "paint", cap_col, scale=(0.095, 0.085, 0.06), segments=8)
        _box(b, frame, (cap_x - 0.07, wall_y - 0.16, 1.695), (cap_x + 0.07, wall_y - 0.08, 1.705), "paint", "2E2A2C")


def supervisor_alcove(b: Builder, frame: Matrix, **options) -> None:
    """Wooden frame with brass rods and drawn curtains on three sides to enclose a supervisor's bed."""
    half = 1.26
    top_z, rod_z = 2.24, 2.12
    curtain_col = CURTAIN_COLOURS["cream"][0]
    trim_col = "7A6B52"

    for px, py in itertools.product((-half, half), repeat=2):
        bevel_box(b, frame, (px - 0.04, py - 0.04, 0.0), (px + 0.04, py + 0.04, top_z), WALNUT_DARK, bevel=0.008)
        _sphere(b, frame, (px, py, 2.275), 0.03, "metal", BRASS_AGED, segments=6)

    # Top frame beams and dado rails on the three closed sides (+Y, -X, +X)
    bevel_box(b, frame, (-half, half - 0.03, top_z - 0.1), (half, half + 0.03, top_z), WALNUT_MID, bevel=0.006)
    bevel_box(b, frame, (-half, -half - 0.03, top_z - 0.1), (half, -half + 0.03, top_z), WALNUT_MID, bevel=0.006)
    bevel_box(b, frame, (-half, half - 0.02, 0.0), (half, half + 0.02, 0.12), WALNUT_DARK, bevel=0.005)
    for sx in (-half, half):
        bevel_box(b, frame, (sx - 0.03, -half, top_z - 0.1), (sx + 0.03, half, top_z), WALNUT_MID, bevel=0.006)
        bevel_box(b, frame, (sx - 0.02, -half, 0.0), (sx + 0.02, half, 0.12), WALNUT_DARK, bevel=0.005)

    # Brass curtain rods
    _cyl(b, frame, (-half + 0.04, half - 0.06, rod_z), 0.012, half * 2.0 - 0.08, 8, "metal", BRASS_AGED, axis="X")
    _cyl(b, frame, (-half + 0.04, -half + 0.06, rod_z), 0.012, half * 2.0 - 0.08, 8, "metal", BRASS_AGED, axis="X")
    for sx in (-1.0, 1.0):
        _cyl(b, frame, (sx * (half - 0.06), -half + 0.04, rod_z), 0.012, half * 2.0 - 0.08, 8, "metal", BRASS_AGED, axis="Y")

    # Pleated side and back curtains
    for i in range(11):
        px = -1.1 + i * 0.22
        dy = 0.025 if i % 2 else -0.025
        _box(b, _at(frame, (px, half - 0.06 + dy, 0.12), 18.0 if i % 2 else -18.0), (-0.11, -0.012, 0.0), (0.11, 0.012, rod_z - 0.13), "paint", curtain_col)
        ring(b, (px, half - 0.06, rod_z), 0.02, 0.004, "metal", BRASS_AGED, frame, sides=8, tube_sides=3, axis="X")

    for sx in (-1.0, 1.0):
        cx = sx * (half - 0.06)
        for i in range(11):
            py = -1.1 + i * 0.22
            dx = 0.025 if i % 2 else -0.025
            _box(b, _at(frame, (cx + dx, py, 0.12), 18.0 if i % 2 else -18.0), (-0.012, -0.11, 0.0), (0.012, 0.11, rod_z - 0.13), "paint", curtain_col)
            ring(b, (cx, py, rod_z), 0.02, 0.004, "metal", BRASS_AGED, frame, sides=8, tube_sides=3, axis="Y")

    # Drawn-back front entry curtains framing the -Y opening
    for sx in (-1.0, 1.0):
        inner = sx * 0.85
        outer = sx * (half - 0.06)
        _box(b, frame, (min(outer, inner), -half + 0.04, 0.95), (max(outer, inner), -half + 0.08, rod_z - 0.01), "paint", curtain_col)
        _box(b, frame, (min(outer, sx * 0.72), -half + 0.04, 0.04), (max(outer, sx * 0.72), -half + 0.08, 0.95), "paint", curtain_col)
        _box(b, frame, (min(outer, sx * 0.82) - 0.02, -half + 0.03, 0.92), (max(outer, sx * 0.82) + 0.02, -half + 0.09, 0.98), "paint", trim_col)

    # Thin wall colliders on the three closed sides so furniture can sit inside
    b.collider((-half - 0.04, half - 0.06, 0.0), (half + 0.04, half + 0.04, top_z), frame)
    b.collider((-half - 0.04, -half, 0.0), (-half + 0.06, half, top_z), frame)
    b.collider((half - 0.06, -half, 0.0), (half + 0.04, half, top_z), frame)


# ---------- refectory ----------

def long_table_set(b: Builder, frame: Matrix, **options) -> None:
    """Long refectory trestle table laid with enamel plates, mugs, spoons, bread basket, soup tureen and water jugs."""
    top_z = 0.76
    for i in range(3):
        y0 = -0.45 + i * 0.3
        wood_box(b, frame, (-1.8, y0, top_z - 0.045), (1.8, y0 + 0.296, top_z), PINE_SCRUB if i == 1 else HONEY_WOOD, light=True)
    wood_box(b, frame, (-1.74, -0.42, top_z - 0.075), (1.74, 0.42, top_z - 0.045), WALNUT_DARK)

    trestle = [(-0.34, 0.0), (-0.28, 0.07), (-0.07, 0.14), (-0.07, 0.68), (0.07, 0.68), (0.07, 0.14), (0.28, 0.07), (0.34, 0.0)]
    for lx in (-1.4, 0.0, 1.4):
        b.side_prism(trestle, lx - 0.04, lx + 0.04, "wood", srgb(WALNUT_MID), frame=frame, uv=WOOD_DARK_UV)
        wood_box(b, frame, (lx - 0.05, -0.36, 0.0), (lx + 0.05, 0.36, 0.04), WALNUT_DARK)
    wood_box(b, frame, (-1.52, -0.035, 0.22), (1.52, 0.035, 0.29), WALNUT_DARK)

    # Eight meal settings (4 per side)
    for place_i in range(4):
        px = -1.2 + place_i * 0.8
        for sy in (-1.0, 1.0):
            py = sy * 0.25
            _enamel_plate(b, frame, px, py, top_z, radius=0.11, sides=12)
            _enamel_mug(b, frame, px + sy * 0.15, py - sy * 0.04, top_z, handle_dir=sy, sides=8)
            _box(b, frame, (px - sy * 0.15 - 0.008, py - 0.07, top_z), (px - sy * 0.15 + 0.008, py + 0.07, top_z + 0.008), "metal", PEWTER)

    # Soup tureen with ladle, bread basket and two water jugs down the centre
    _copper_pot(b, frame, -0.35, 0.0, top_z, radius=0.125, height=0.12, material="paint", tint=ENAMEL_CREAM, lid=True, sides=16)
    _beam(b, frame, (-0.31, 0.02, top_z + 0.08), (-0.21, -0.08, top_z + 0.22), 0.012, 0.008, "metal", PEWTER)

    _wicker_basket(b, frame, 0.38, 0.0, top_z, r_bot=0.11, r_top=0.15, height=0.07)
    for lx, ly in ((0.33, -0.03), (0.43, 0.02), (0.37, 0.04)):
        _sphere(b, frame, (lx, ly, top_z + 0.07), 1.0, "paint", "C98F54", scale=(0.06, 0.045, 0.038), segments=6)

    for jx, jy in ((-0.88, 0.02), (0.88, -0.02)):
        _ceramic_jug(b, frame, jx, jy, top_z, scale=0.9, sides=14)


def long_bench(b: Builder, frame: Matrix, **options) -> None:
    """Backless wooden refectory bench matching the long table."""
    bevel_box(b, frame, (-1.8, -0.16, 0.42), (1.8, 0.16, 0.46), HONEY_WOOD, bevel=0.01, light=True)
    wood_box(b, frame, (-1.75, -0.14, 0.39), (1.75, 0.14, 0.42), WALNUT_DARK)
    leg_prof = [(-0.14, 0.0), (-0.08, 0.0), (-0.06, 0.07), (0.06, 0.07), (0.08, 0.0), (0.14, 0.0), (0.12, 0.39), (-0.12, 0.39)]
    for lx in (-1.4, 0.0, 1.4):
        b.side_prism(leg_prof, lx - 0.035, lx + 0.035, "wood", srgb(WALNUT_MID), frame=frame, uv=WOOD_DARK_UV)
    wood_box(b, frame, (-1.48, -0.025, 0.15), (1.48, 0.025, 0.2), WALNUT_DARK)


def crockery_dresser(b: Builder, frame: Matrix, **options) -> None:
    """Colonial sideboard with drawers and cupboards below, and open plate racks above."""
    half_w, half_d = 0.93, 0.225
    _cabinet_base(b, frame, half_w, half_d, foot_h=0.07, plinth_h=0.08)
    bevel_box(b, frame, (-half_w + 0.02, -half_d + 0.02, 0.15), (half_w - 0.02, half_d, 0.85), WALNUT_MID, bevel=0.008)

    for bx in (-0.6, 0.0, 0.6):
        raised_panel(b, frame, bx - 0.26, bx + 0.26, 0.18, 0.62, -half_d + 0.01, WALNUT_MID, border=0.04, depth=0.012)
        knob(b, frame, bx + 0.19, -half_d - 0.008, 0.44, 0.014, BRASS_AGED)
        raised_panel(b, frame, bx - 0.26, bx + 0.26, 0.66, 0.82, -half_d + 0.01, HONEY_WOOD, border=0.03, depth=0.012)
        knob(b, frame, bx, -half_d - 0.008, 0.74, 0.013, BRASS_AGED)

    bevel_box(b, frame, (-0.95, -0.25, 0.85), (0.95, 0.25, 0.89), PINE_SCRUB, bevel=0.01, light=True)

    # Upper open dresser rack (+0.02..+0.24 in Y)
    wood_box(b, frame, (-0.9, 0.21, 0.89), (0.9, 0.245, 2.08), WALNUT_DARK)
    for sx in (-0.93, 0.89):
        b.side_prism([(0.02, 0.89), (0.245, 0.89), (0.245, 2.08), (0.0, 2.08), (0.0, 1.35)], sx, sx + 0.04, "wood", srgb(WALNUT_MID), frame=frame, uv=WOOD_DARK_UV)
    for sz in (1.28, 1.68):
        wood_box(b, frame, (-0.89, 0.02, sz - 0.03), (0.89, 0.21, sz), HONEY_WOOD, light=True)
        _cyl(b, frame, (-0.89, 0.04, sz + 0.08), 0.009, 1.78, 6, "wood", WALNUT_DARK, axis="X", uv=WOOD_LIGHT_UV)

    run_profile(b, frame, -0.94, 0.94, cornice_profile(0.01, 2.01, 0.03, 0.07), WALNUT_DARK)
    bevel_box(b, frame, (-0.95, -0.02, 2.08), (0.95, 0.25, 2.15), HONEY_WOOD, bevel=0.01, light=True)

    # Crockery display: standing plates, nested bowls, jugs
    for sz, px in itertools.product((1.28, 1.68), (-0.7, -0.42, -0.14, 0.14, 0.42, 0.7)):
        pf = _at(frame, (px, 0.12, sz + 0.12), -12.0, "X")
        _cyl(b, pf, (0.0, -0.01, 0.0), 0.115, 0.012, 12, "paint", ENAMEL_CREAM, axis="Y")
        ring(b, (0.0, -0.012, 0.0), 0.095, 0.004, "paint", AZULEJO_BLUE, pf, sides=12, tube_sides=3, axis="Y")

    for bx in (-0.65, -0.38):
        for stack in range(3):
            _enamel_bowl(b, frame, bx, -0.04, 0.89 + stack * 0.038, radius=0.085, height=0.048, sides=12)
    for jx, sc in ((0.15, 1.0), (0.48, 0.85), (0.74, 1.05)):
        _ceramic_jug(b, frame, jx, -0.02, 0.89, scale=sc, sides=14)


def serving_counter(b: Builder, frame: Matrix, **options) -> None:
    """Refectory serving counter with colonial tiled front, stacked plates, large soup pot with ladle and bread tray."""
    bevel_box(b, frame, (-1.16, -0.35, 0.0), (1.16, 0.35, 0.1), WALNUT_DARK, bevel=0.008)
    wood_box(b, frame, (-1.14, -0.33, 0.1), (1.14, 0.34, 0.89), WALNUT_MID)
    for px in (-1.14, -0.38, 0.38, 1.14):
        bevel_box(b, frame, (px - 0.04, -0.36, 0.1), (px + 0.04, -0.32, 0.89), WALNUT_DARK, bevel=0.006)
    for bay_x in (-0.76, 0.0, 0.76):
        _azulejo_panel(b, frame, bay_x - 0.32, bay_x + 0.32, 0.14, 0.84, -0.335, 4, 4, facing=-1.0)

    bevel_box(b, frame, (-1.2, -0.375, 0.89), (1.2, 0.375, 0.94), PINE_SCRUB, bevel=0.012, light=True)

    # Stacked enamel plates
    for sx in (-0.9, -0.64):
        for i in range(5):
            _enamel_plate(b, frame, sx, 0.04, 0.94 + i * 0.02, radius=0.115, sides=12)

    # Large soup pot with ladle
    _copper_pot(b, frame, 0.0, 0.0, 0.94, radius=0.19, height=0.22, material="metal", tint=COPPER_WARE, lid=False, sides=16)
    _cyl(b, frame, (0.0, 0.0, 1.11), 0.18, 0.01, 16, "paint", "B57E48")
    _beam(b, frame, (0.02, -0.02, 1.06), (0.16, -0.1, 1.19), 0.015, 0.01, "metal", PEWTER)

    # Wooden bread tray with loaves
    bevel_box(b, frame, (0.48, -0.2, 0.94), (1.02, 0.2, 0.99), HONEY_WOOD, bevel=0.008, light=True)
    for lx, ly in ((0.64, -0.06), (0.86, 0.05), (0.72, 0.09)):
        _sphere(b, frame, (lx, ly, 1.025), 1.0, "paint", "C98F54", scale=(0.11, 0.065, 0.048), segments=6)


# ---------- kitchen ----------

def masonry_range(b: Builder, frame: Matrix, **options) -> None:
    """Built-in colonial masonry wood-burning range with tile facing, iron hotplate, pots and chimney hood."""
    # Masonry body and recessed firewood arch
    _box(b, frame, (-1.4, -0.5, 0.0), (1.4, 0.52, 0.1), "stone", STONE_WARM)
    _box(b, frame, (-1.36, -0.47, 0.1), (1.36, 0.52, 0.86), "plaster", PLASTER_WARM)
    _azulejo_panel(b, frame, -1.34, -0.92, 0.14, 0.82, -0.47, 3, 4, facing=-1.0)
    _azulejo_panel(b, frame, 0.92, 1.34, 0.14, 0.82, -0.47, 3, 4, facing=-1.0)

    # Wood recess below firebox
    _box(b, frame, (-0.82, -0.48, 0.1), (0.82, -0.18, 0.36), "paint", "382E2C")
    for lx in (-0.56, -0.28, 0.0, 0.28, 0.56):
        _cyl(b, frame, (lx, -0.46, 0.18), 0.065, 0.26, 7, "wood", WALNUT_MID, axis="Y", uv=WOOD_LIGHT_UV)

    # Cast-iron firebox & two oven doors
    metal_box(b, frame, (-0.86, -0.49, 0.4), (0.86, -0.45, 0.84), CAST_IRON)
    metal_box(b, frame, (-0.78, -0.5, 0.44), (-0.28, -0.47, 0.78), WROUGHT_IRON)
    _box(b, frame, (-0.68, -0.505, 0.5), (-0.38, -0.495, 0.72), "glow_ember", "FFFFFF")
    for bar_x in (-0.62, -0.53, -0.44):
        metal_box(b, frame, (bar_x - 0.01, -0.51, 0.5), (bar_x + 0.01, -0.5, 0.72), WROUGHT_IRON)

    for ox in (-0.08, 0.52):
        metal_box(b, frame, (ox - 0.2, -0.5, 0.44), (ox + 0.2, -0.47, 0.78), CAST_IRON)
        metal_box(b, frame, (ox - 0.06, -0.515, 0.68), (ox + 0.06, -0.495, 0.71), BRASS_AGED)

    # Hot plate with concentric ring lids
    metal_box(b, frame, (-1.4, -0.505, 0.86), (1.4, 0.525, 0.92), WROUGHT_IRON)
    for rx, ry, rr in ((-0.75, -0.1, 0.17), (-0.25, 0.12, 0.15), (0.35, -0.08, 0.16), (0.85, 0.08, 0.14)):
        _cyl(b, frame, (rx, ry, 0.92), rr, 0.012, 16, "metal", CAST_IRON)
        ring(b, (rx, ry, 0.93), rr * 0.65, 0.005, "metal", WROUGHT_IRON, frame, sides=16, tube_sides=3)

    # Brass front guard rail and towel
    _cyl(b, frame, (-1.32, -0.505, 0.84), 0.011, 2.64, 8, "metal", BRASS_AGED, axis="X")
    _draped_towel(b, frame, 0.9, -0.485, 0.84, 0.22, 0.26, LINEN_CREAM, axis="X", stripe="9C403B")

    # Copper stockpot and kettle on hot plate
    _copper_pot(b, frame, -0.75, -0.1, 0.932, radius=0.16, height=0.18, sides=16)
    kf = _at(frame, (0.35, -0.08, 0.932))
    lathe(b, [(0.001, 0.0), (0.11, 0.0), (0.14, 0.07), (0.11, 0.15), (0.05, 0.18), (0.001, 0.19)], 16, "metal", COPPER_WARE, kf)
    ring(b, (0.0, 0.0, 0.17), 0.095, 0.009, "metal", WROUGHT_IRON, kf, sides=12, tube_sides=3, axis="Y")
    _beam(b, kf, (-0.11, 0.0, 0.09), (-0.19, 0.0, 0.17), 0.022, 0.022, "metal", COPPER_WARE)

    # Tapering plaster-and-brick chimney hood above
    _box(b, frame, (-1.38, -0.45, 1.62), (1.38, 0.52, 1.72), "wood", WALNUT_DARK, uv=WOOD_DARK_UV)
    for cx in (-1.28, 1.28):
        b.side_prism([(0.52, 1.62), (-0.38, 1.62), (0.52, 1.35)], cx - 0.05, cx + 0.05, "metal", srgb(WROUGHT_IRON), frame=frame)
    hood_pts = [(sx * 1.34, sy, 1.72) for sx, sy in itertools.product((-1.0, 1.0), (-0.42, 0.52))] + [(sx * 0.42, sy, 2.52) for sx, sy in itertools.product((-1.0, 1.0), (0.08, 0.52))]
    solid_hull(b, hood_pts, "plaster", PLASTER_WARM, frame)
    _box(b, frame, (-0.44, 0.06, 2.52), (0.44, 0.52, 2.7), "brick", BRICK_OLD)


def kitchen_worktable(b: Builder, frame: Matrix, **options) -> None:
    """Heavy kitchen work table with drawers, chopping board, knife, bowls, vegetables, rolling pin and baskets below."""
    top_z = 0.86
    for lx, ly in itertools.product((-1.08, 1.08), (-0.42, 0.42)):
        turned_leg(b, frame, lx, ly, top_z - 0.05, 0.045, WALNUT_MID, "baluster", sides=10)
    wood_box(b, frame, (-1.1, -0.44, 0.18), (1.1, 0.44, 0.22), HONEY_WOOD, light=True)
    wood_box(b, frame, (-1.1, -0.44, top_z - 0.2), (1.1, 0.44, top_z - 0.05), WALNUT_MID)
    for dx in (-0.55, 0.55):
        bevel_box(b, frame, (dx - 0.42, -0.455, top_z - 0.18), (dx + 0.42, -0.435, top_z - 0.07), HONEY_WOOD, bevel=0.006, light=True)
        knob(b, frame, dx, -0.456, top_z - 0.125, 0.015, BRASS_AGED)
    bevel_box(b, frame, (-1.2, -0.5, top_z - 0.05), (1.2, 0.5, top_z), PINE_SCRUB, bevel=0.012, light=True)

    # Chopping board, knife, rolling pin, mixing bowls and vegetables on top
    bevel_box(b, frame, (-0.85, -0.24, top_z), (-0.28, 0.16, top_z + 0.035), HONEY_WOOD, bevel=0.006, light=True)
    _box(b, _at(frame, (-0.42, -0.1, top_z + 0.036), 24.0), (-0.1, -0.015, 0.0), (0.08, 0.015, 0.006), "metal", PEWTER)
    _box(b, _at(frame, (-0.42, -0.1, top_z + 0.036), 24.0), (0.08, -0.012, 0.0), (0.18, 0.012, 0.014), "wood", WALNUT_DARK, uv=WOOD_DARK_UV)

    _cyl(b, frame, (-0.12, -0.25, top_z + 0.025), 0.025, 0.3, 12, "wood", PINE_SCRUB, axis="X", uv=WOOD_LIGHT_UV)
    _cyl(b, frame, (-0.19, -0.25, top_z + 0.025), 0.012, 0.44, 8, "wood", HONEY_WOOD, axis="X", uv=WOOD_LIGHT_UV)

    for bx, by, br, bcol in ((0.32, 0.12, 0.15, ENAMEL_CREAM), (0.68, -0.12, 0.12, TERRACOTTA)):
        _enamel_bowl(b, frame, bx, by, top_z, radius=br, height=br * 0.6, body=bcol, rim=AZULEJO_BLUE if bcol == ENAMEL_CREAM else TERRACOTTA_DARK, sides=16)

    # Cabbage & carrots on board/table
    _sphere(b, frame, (-0.72, 0.04, top_z + 0.09), 0.065, "paint", "5E8C54", segments=8)
    for cx, cy in ((-0.58, 0.06), (-0.54, 0.02)):
        _cyl(b, _at(frame, (cx, cy, top_z + 0.05), 35.0), (0.0, 0.0, 0.0), 0.018, 0.13, 6, "paint", "C96B36", top_radius=0.005, axis="X")
    # Onions by bowl
    for ox, oy in ((0.06, 0.12), (0.12, 0.05), (0.04, -0.01)):
        _sphere(b, frame, (ox, oy, top_z + 0.035), 0.035, "paint", "B87E45", scale=(1.0, 1.0, 0.85), segments=8)

    # Wicker baskets on lower shelf
    for kx in (-0.6, 0.05, 0.65):
        _wicker_basket(b, frame, kx, 0.0, 0.22, r_bot=0.16, r_top=0.22, height=0.22)
        for px, py in ((-0.06, -0.04), (0.06, 0.04), (0.0, 0.0)):
            _sphere(b, frame, (kx + px, py, 0.44), 0.05, "paint", "C2A274" if kx < 0 else "B87E45", segments=6)


def stone_sink(b: Builder, frame: Matrix, **options) -> None:
    """Carved stone trough sink on masonry piers with hand pump, bucket and plate drying rack."""
    for sx in (-0.65, 0.65):
        _box(b, frame, (sx - 0.16, -0.32, 0.0), (sx + 0.16, 0.32, 0.56), "stone", STONE_WARM)
    wood_box(b, frame, (-0.5, -0.26, 0.14), (0.5, 0.26, 0.18), HONEY_WOOD, light=True)

    # Stone trough walls and water surface
    _box(b, frame, (-0.82, -0.34, 0.56), (0.82, 0.34, 0.64), "stone", STONE_LIGHT)
    _box(b, frame, (-0.82, -0.34, 0.64), (0.82, -0.25, 0.86), "stone", STONE_LIGHT)
    _box(b, frame, (-0.82, 0.23, 0.64), (0.82, 0.34, 0.86), "stone", STONE_LIGHT)
    _box(b, frame, (-0.82, -0.25, 0.64), (-0.72, 0.23, 0.86), "stone", STONE_LIGHT)
    _box(b, frame, (0.72, -0.25, 0.64), (0.82, 0.23, 0.86), "stone", STONE_LIGHT)
    _box(b, frame, (-0.72, -0.25, 0.64), (0.72, 0.23, 0.78), "water", "5D9AB8")

    # Cast-iron hand pump on the right back corner
    px, py = 0.68, 0.25
    _cyl(b, frame, (px, py, 0.86), 0.05, 0.58, 12, "metal", WROUGHT_IRON)
    _sphere(b, frame, (px, py, 1.46), 0.048, "metal", BRASS_AGED, segments=8)
    _beam(b, frame, (px, py, 1.15), (px - 0.16, py - 0.18, 1.07), 0.032, 0.032, "metal", WROUGHT_IRON)
    _beam(b, frame, (px, py + 0.03, 1.4), (px + 0.12, py - 0.15, 1.16), 0.022, 0.022, "metal", WROUGHT_IRON)

    # Stave bucket on lower shelf
    _wicker_basket(b, frame, -0.22, -0.02, 0.18, r_bot=0.11, r_top=0.14, height=0.28, tint=HONEY_WOOD)
    ring(b, (-0.22, -0.02, 0.24), 0.12, 0.007, "metal", WROUGHT_IRON, frame, sides=12, tube_sides=3)
    ring(b, (-0.22, -0.02, 0.4), 0.136, 0.007, "metal", WROUGHT_IRON, frame, sides=12, tube_sides=3)

    # Drying rack on the left back
    wood_box(b, frame, (-0.78, 0.3, 0.86), (0.36, 0.34, 1.68), WALNUT_MID)
    for rz in (1.02, 1.36):
        wood_box(b, frame, (-0.75, 0.1, rz - 0.025), (0.33, 0.3, rz), HONEY_WOOD, light=True)
        _cyl(b, frame, (-0.75, 0.12, rz + 0.08), 0.008, 1.08, 6, "wood", WALNUT_DARK, axis="X", uv=WOOD_LIGHT_UV)
    for rz, dx in itertools.product((1.02, 1.36), (-0.58, -0.34, -0.1, 0.14)):
        pf = _at(frame, (dx, 0.2, rz + 0.11), -12.0, "X")
        _cyl(b, pf, (0.0, -0.01, 0.0), 0.105, 0.01, 12, "paint", ENAMEL_CREAM, axis="Y")


def pot_shelf(b: Builder, frame: Matrix, **options) -> None:
    """Open kitchen shelves holding cast-iron and copper pots, skillets, clay jars and a colander."""
    boards = (0.14, 0.68, 1.24, 1.76)
    for px, py in itertools.product((-0.86, 0.86), (-0.18, 0.18)):
        bevel_box(b, frame, (px - 0.03, py - 0.03, 0.0), (px + 0.03, py + 0.03, 2.02), WALNUT_DARK, bevel=0.006)
    bevel_box(b, frame, (-0.9, -0.21, 1.98), (0.9, 0.21, 2.05), WALNUT_MID, bevel=0.008)
    for bz in boards:
        bevel_box(b, frame, (-0.86, -0.19, bz - 0.035), (0.86, 0.19, bz), HONEY_WOOD, bevel=0.006, light=True)

    # Bottom: heavy iron stew pots
    for px, r in ((-0.54, 0.15), (0.0, 0.17), (0.54, 0.14)):
        _copper_pot(b, frame, px, 0.0, boards[0], radius=r, height=r * 1.15, material="metal", tint=CAST_IRON, sides=14)
    # Second: copper pots & pans
    _copper_pot(b, frame, -0.58, 0.0, boards[1], radius=0.14, height=0.17, sides=14)
    _copper_pot(b, frame, -0.16, 0.0, boards[1], radius=0.12, height=0.14, sides=14)
    _copper_pan(b, frame, 0.32, 0.02, boards[1], radius=0.14, yaw=18.0, sides=14)
    _copper_pan(b, frame, 0.32, 0.02, boards[1] + 0.05, radius=0.11, yaw=-25.0, sides=14)
    # Third: clay storage jars
    for jx, h in ((-0.62, 0.28), (-0.28, 0.24), (0.08, 0.3), (0.45, 0.22), (0.7, 0.25)):
        lathe(b, [(0.001, 0.0), (0.07, 0.0), (0.1, h * 0.55), (0.06, h * 0.9), (0.075, h), (0.001, h)], 12, "paint", TERRACOTTA, frame, base=(jx, 0.0, boards[2]))
    # Top: copper colander & small saucepans
    lathe(b, [(0.07, 0.0), (0.14, 0.04), (0.17, 0.14), (0.185, 0.15), (0.16, 0.15), (0.13, 0.05), (0.001, 0.03)], 16, "metal", COPPER_WARE, frame, base=(-0.45, 0.0, boards[3]))
    _copper_pot(b, frame, 0.12, 0.0, boards[3], radius=0.11, height=0.13, sides=14)
    _ceramic_jug(b, frame, 0.56, 0.0, boards[3], scale=0.85, sides=12)


def hanging_pan_rack(b: Builder, frame: Matrix, **options) -> None:
    """Ceiling-mounted wrought-iron pan rack with copper skillets, ladles, skimmers and herb bundles (hang)."""
    rack_z = -0.45
    for cx, cy in itertools.product((-0.78, 0.78), (-0.18, 0.18)):
        _beam(b, frame, (cx, cy, rack_z), (cx * 0.92, 0.0, 0.0), 0.015, 0.015, "metal", WROUGHT_IRON)
    for ry in (-0.18, 0.18):
        metal_box(b, frame, (-0.9, ry - 0.015, rack_z - 0.02), (0.9, ry + 0.015, rack_z + 0.02), WROUGHT_IRON)
    for rx in (-0.9, -0.3, 0.3, 0.9):
        metal_box(b, frame, (rx - 0.015, -0.19, rack_z - 0.02), (rx + 0.015, 0.19, rack_z + 0.02), WROUGHT_IRON)

    # Hanging copper pans on front bar
    for px, r, drop in ((-0.65, 0.13, 0.34), (-0.15, 0.11, 0.31), (0.4, 0.14, 0.35)):
        _cyl(b, frame, (px, -0.18, rack_z - 0.08), 0.006, 0.08, 6, "metal", BRASS_AGED)
        _beam(b, frame, (px, -0.18, rack_z - 0.08), (px, -0.18, rack_z - drop), 0.018, 0.012, "metal", WROUGHT_IRON)
        _cyl(b, frame, (px, -0.16, rack_z - drop - r), r, 0.038, 16, "metal", COPPER_WARE, axis="Y")

    # Ladles and pierced skimmers on back bar
    for lx, is_skimmer in ((-0.5, False), (0.05, True), (0.55, False)):
        _beam(b, frame, (lx, 0.18, rack_z - 0.04), (lx, 0.18, rack_z - 0.44), 0.014, 0.01, "metal", BRASS_AGED)
        if is_skimmer:
            _cyl(b, frame, (lx, 0.175, rack_z - 0.5), 0.065, 0.01, 12, "metal", COPPER_WARE, axis="Y")
        else:
            lathe(b, [(0.001, -0.52), (0.05, -0.5), (0.055, -0.46), (0.001, -0.48)], 12, "metal", COPPER_WARE, frame, base=(lx, 0.17, rack_z))

    # Dried herb bundles hanging from centre
    for hx, hcol in ((-0.25, "4E7344"), (0.25, "6E8A4F")):
        _cyl(b, frame, (hx, 0.0, rack_z - 0.48), 0.08, 0.36, 8, "paint", hcol, top_radius=0.02)
        _cyl(b, frame, (hx, 0.0, rack_z - 0.14), 0.022, 0.08, 6, "paint", LINEN_RAW)


def water_filter(b: Builder, frame: Matrix, **options) -> None:
    """Porous clay water-filter jar on a four-legged wooden stand with brass tap and enamel mug."""
    stand_h = 0.68
    for lx, ly in itertools.product((-0.18, 0.18), repeat=2):
        turned_leg(b, frame, lx, ly, stand_h, 0.024, WALNUT_DARK, "baluster", sides=8)
    wood_box(b, frame, (-0.19, -0.19, 0.2), (0.19, 0.19, 0.23), HONEY_WOOD, light=True)
    bevel_box(b, frame, (-0.23, -0.23, stand_h - 0.04), (0.23, 0.23, stand_h), WALNUT_MID, bevel=0.008)

    jar_prof = [(0.001, 0.0), (0.12, 0.0), (0.21, 0.2), (0.22, 0.36), (0.17, 0.52), (0.19, 0.56), (0.15, 0.58), (0.15, 0.61), (0.04, 0.64), (0.045, 0.67), (0.001, 0.67)]
    lathe(b, jar_prof, 16, "paint", TERRACOTTA, frame, base=(0.0, 0.0, stand_h))
    ring(b, (0.0, 0.0, stand_h + 0.58), 0.18, 0.012, "paint", TERRACOTTA_DARK, frame, sides=16, tube_sides=4)

    # Brass tap protruding to -Y and enamel mug below
    _cyl(b, frame, (0.0, -0.24, stand_h + 0.07), 0.012, 0.08, 8, "metal", BRASS_AGED, axis="Y")
    _cyl(b, frame, (0.0, -0.23, stand_h + 0.05), 0.01, 0.025, 8, "metal", BRASS_AGED)
    _enamel_mug(b, frame, 0.0, -0.04, 0.23, sides=12)


def firewood_stack(b: Builder, frame: Matrix, **options) -> None:
    """Split firewood stacked in a wrought-iron cradle with an axe and a basket of kindling."""
    generator = random.Random(options.get("seed", 1))

    # Iron cradle at x = -0.62..0.28
    for rx in (-0.58, 0.22):
        metal_box(b, frame, (rx - 0.015, -0.22, 0.0), (rx + 0.015, 0.22, 0.04), WROUGHT_IRON)
        for ry in (-0.2, 0.2):
            metal_box(b, frame, (rx - 0.015, ry - 0.015, 0.04), (rx + 0.015, ry + 0.015, 0.76), WROUGHT_IRON)
    for ry in (-0.14, 0.14):
        metal_box(b, frame, (-0.58, ry - 0.012, 0.06), (0.22, ry + 0.012, 0.09), WROUGHT_IRON)

    # Stacked split logs
    for row in range(5):
        z = 0.15 + row * 0.115
        count = 5 - (row % 2)
        for col in range(count):
            lx = -0.48 + (row % 2) * 0.08 + col * 0.165 + generator.uniform(-0.01, 0.01)
            r = generator.uniform(0.055, 0.072)
            _cyl(b, frame, (lx, -0.21, z), r, 0.42, 7, "wood", WALNUT_MID if (row + col) % 2 else HONEY_WOOD, axis="Y", uv=WOOD_LIGHT_UV)

    # Wood-splitter's axe leaning against the left side
    _beam(b, frame, (-0.56, -0.22, 0.02), (-0.42, -0.05, 0.82), 0.032, 0.026, "wood", PINE_SCRUB, uv=WOOD_LIGHT_UV)
    b.prism([(-0.56, 0.04), (-0.49, 0.06), (-0.48, 0.16), (-0.58, 0.2)], -0.24, -0.18, "metal", srgb(CAST_IRON), frame=frame)

    # Kindling basket on the right
    _wicker_basket(b, frame, 0.44, 0.0, 0.0, r_bot=0.14, r_top=0.19, height=0.28)
    for i in range(7):
        ang = i * 0.9
        _beam(b, frame, (0.44 + 0.05 * math.cos(ang), 0.05 * math.sin(ang), 0.12), (0.44 + 0.14 * math.cos(ang), 0.14 * math.sin(ang), 0.48 + (i % 3) * 0.04), 0.018, 0.016, "wood", HONEY_WOOD, uv=WOOD_LIGHT_UV)


def pantry_shelf(b: Builder, frame: Matrix, **options) -> None:
    """Deep pantry shelves stocked with sacks, labelled jars, onion baskets, cheese wheels and hanging sausages."""
    boards = (0.14, 0.72, 1.32)
    for px, py in itertools.product((-0.91, 0.91), (-0.24, 0.24)):
        bevel_box(b, frame, (px - 0.035, py - 0.035, 0.0), (px + 0.035, py + 0.035, 2.18), WALNUT_DARK, bevel=0.006)
    bevel_box(b, frame, (-0.94, -0.26, 2.12), (0.94, 0.26, 2.2), WALNUT_MID, bevel=0.008)
    for bz in boards:
        bevel_box(b, frame, (-0.91, -0.24, bz - 0.035), (0.91, 0.24, bz), HONEY_WOOD, bevel=0.006, light=True)
    _cyl(b, frame, (-0.9, -0.05, 1.98), 0.012, 1.8, 8, "metal", WROUGHT_IRON, axis="X")

    # Bottom: flour sacks and onion baskets
    for sx, h in ((-0.68, 0.42), (-0.28, 0.38)):
        lathe(b, [(0.11, 0.0), (0.17, 0.08), (0.18, 0.22), (0.13, 0.31), (0.06, h - 0.02), (0.08, h + 0.03)], 10, "paint", LINEN_RAW, frame, base=(sx, 0.0, boards[0]))
        ring(b, (sx, 0.0, boards[0] + h - 0.025), 0.065, 0.009, "paint", "7D5C3E", frame, sides=8, tube_sides=3)
    for bx in (0.22, 0.66):
        _wicker_basket(b, frame, bx, 0.0, boards[0], r_bot=0.14, r_top=0.19, height=0.22)
        for ox, oy in ((-0.06, -0.04), (0.06, -0.04), (0.0, 0.06), (-0.04, 0.05), (0.05, 0.05), (0.0, 0.0)):
            _sphere(b, frame, (bx + ox, oy, boards[0] + 0.24), 0.038, "paint", "C28448", segments=6)

    # Middle: cheese wheels and crocks
    for cx, cr, ch in ((-0.6, 0.16, 0.11), (-0.22, 0.14, 0.1)):
        _cyl(b, frame, (cx, 0.0, boards[1]), cr, ch, 14, "paint", "D9B25F")
        _cyl(b, frame, (cx, 0.0, boards[1] + ch), cr * 0.94, 0.006, 14, "paint", "E8CC82")
    for jx, jcol in ((0.2, TERRACOTTA), (0.58, "4A6E82")):
        lathe(b, [(0.001, 0.0), (0.09, 0.0), (0.11, 0.15), (0.08, 0.24), (0.09, 0.26), (0.001, 0.26)], 12, "paint", jcol, frame, base=(jx, 0.0, boards[1]))

    # Upper: labelled preserve jars
    for ji in range(6):
        jx = -0.72 + ji * 0.28
        _glass_bottle(b, frame, jx, 0.0, boards[2], r=0.055, h=0.2, hex_col=BOTTLE_COLOURS[ji % len(BOTTLE_COLOURS)], cork=True, label=True)

    # Top rail: hanging sausages
    for sx in (-0.65, -0.25, 0.25, 0.65):
        _cyl(b, frame, (sx, -0.05, 1.88), 0.006, 0.1, 4, "paint", LINEN_RAW)
        for link in range(3):
            _cyl(b, frame, (sx, -0.05, 1.74 - link * 0.13), 0.028, 0.11, 8, "paint", "8E4238")


# ---------- classroom and study ----------

def double_desk(b: Builder, frame: Matrix, **options) -> None:
    """Two-seat school desk with sloped lid, brass inkwells, attached bench, cast-iron sides, slate and book."""
    for sx in (-0.52, 0.52):
        metal_box(b, frame, (sx - 0.02, -0.43, 0.0), (sx + 0.02, 0.43, 0.045), WROUGHT_IRON)
        _beam(b, frame, (sx, -0.34, 0.04), (sx, -0.24, 0.72), 0.04, 0.035, "metal", WROUGHT_IRON)
        _beam(b, frame, (sx, -0.04, 0.04), (sx, -0.16, 0.72), 0.035, 0.035, "metal", WROUGHT_IRON)
        _beam(b, frame, (sx, 0.26, 0.04), (sx, 0.26, 0.41), 0.035, 0.035, "metal", WROUGHT_IRON)
        _beam(b, frame, (sx, 0.36, 0.41), (sx, 0.4, 0.76), 0.03, 0.03, "metal", WROUGHT_IRON)

    # Book cubby underneath + sloped writing top facing +Y pupils (tilted down toward +Y)
    wood_box(b, frame, (-0.54, -0.36, 0.56), (0.54, -0.06, 0.59), WALNUT_MID)
    wood_box(b, frame, (-0.57, -0.43, 0.75), (0.57, -0.33, 0.785), HONEY_WOOD, light=True)
    lid = _at(frame, (0.0, -0.18, 0.735), -10.0, "X")
    bevel_box(b, lid, (-0.57, -0.16, -0.025), (0.57, 0.16, 0.0), PINE_SCRUB, bevel=0.006, light=True)

    # Two brass inkwells in the flat upper ledge
    for wx in (-0.3, 0.3):
        _cyl(b, frame, (wx, -0.38, 0.785), 0.025, 0.012, 10, "metal", BRASS_AGED)
        _cyl(b, frame, (wx, -0.38, 0.797), 0.013, 0.005, 8, "paint", "23304A")

    # Slate and closed book resting on the sloped lid
    _box(b, lid, (-0.42, -0.1, 0.0), (-0.14, 0.1, 0.012), "wood", WALNUT_DARK, uv=WOOD_LIGHT_UV)
    _box(b, lid, (-0.39, -0.07, 0.008), (-0.17, 0.07, 0.014), "paint", SLATE_DARK)
    _book_closed(b, lid, 0.26, 0.0, 0.0, 0.18, 0.22, 0.028, BOOK_COLOURS[1], yaw=-8.0)

    # Attached seat and backrest
    bevel_box(b, frame, (-0.56, 0.16, 0.41), (0.56, 0.42, 0.445), HONEY_WOOD, bevel=0.006, light=True)
    bevel_box(b, frame, (-0.56, 0.38, 0.66), (0.56, 0.42, 0.78), HONEY_WOOD, bevel=0.006, light=True)


def bentwood_chair(b: Builder, frame: Matrix, **options) -> None:
    """Simple colonial bentwood cafe/classroom chair with curved hooped backrest."""
    seat_z = 0.44
    for lx, ly in ((-0.16, -0.17), (0.16, -0.17), (-0.15, 0.17), (0.15, 0.17)):
        _beam(b, frame, (lx * 1.12, ly * 1.12, 0.0), (lx * 0.9, ly * 0.9, seat_z), 0.024, 0.024, "wood", WALNUT_DARK, uv=WOOD_LIGHT_UV)

    ring(b, (0.0, 0.0, 0.18), 0.155, 0.01, "wood", WALNUT_MID, frame, sides=16, tube_sides=4)
    _cyl(b, frame, (0.0, 0.0, seat_z - 0.025), 0.2, 0.028, 16, "wood", HONEY_WOOD, uv=WOOD_LIGHT_UV)
    _cyl(b, frame, (0.0, 0.0, seat_z + 0.002), 0.175, 0.005, 16, "paint", "C9B48C")

    # Outer and inner steam-bent backrest hoops
    outer = [(-0.16 * math.cos(math.pi * i / 8.0), 0.16 + 0.06 * math.sin(math.pi * i / 8.0), seat_z + 0.44 * math.sin(math.pi * i / 8.0)) for i in range(9)]
    inner = [(-0.09 * math.cos(math.pi * i / 6.0), 0.17 + 0.035 * math.sin(math.pi * i / 6.0), seat_z + 0.34 * math.sin(math.pi * i / 6.0)) for i in range(7)]
    for pts in (outer, inner):
        for p0, p1 in zip(pts, pts[1:]):
            _beam(b, frame, p0, p1, 0.02, 0.02, "wood", WALNUT_DARK, uv=WOOD_LIGHT_UV)


def teacher_platform(b: Builder, frame: Matrix, **options) -> None:
    """Low wooden dais with teacher's desk, bentwood chair, hand bell, pile of exercise books and globe."""
    plat_h = 0.16
    bevel_box(b, frame, (-1.3, -0.9, 0.0), (1.3, 0.9, plat_h), WALNUT_DARK, bevel=0.015)
    bevel_box(b, frame, (-1.26, -0.86, plat_h - 0.02), (1.26, 0.86, plat_h + 0.005), PINE_SCRUB, bevel=0.006, light=True)

    # Teacher's desk near front-centre of platform
    desk_f = _at(frame, (0.0, -0.28, plat_h))
    for side in (-1.0, 1.0):
        bevel_box(b, desk_f, (side * 0.55 - 0.16, -0.32, 0.0), (side * 0.55 + 0.16, 0.32, 0.72), WALNUT_MID, bevel=0.008)
        for d in range(3):
            wood_box(b, desk_f, (side * 0.55 - 0.13, 0.32, 0.08 + d * 0.21), (side * 0.55 + 0.13, 0.335, 0.25 + d * 0.21), HONEY_WOOD, light=True)
    wood_box(b, desk_f, (-0.42, -0.3, 0.22), (0.42, -0.26, 0.72), WALNUT_DARK)
    bevel_box(b, desk_f, (-0.78, -0.38, 0.72), (0.78, 0.38, 0.76), HONEY_WOOD, bevel=0.01, light=True)
    _box(b, desk_f, (-0.68, -0.28, 0.76), (0.68, 0.28, 0.766), "paint", LEATHER_GREEN)

    # Hand bell, pile of exercise books, and world globe on desk (z = 0.92 up to 1.25)
    top_z = 0.766
    lathe(b, [(0.04, 0.0), (0.032, 0.02), (0.014, 0.065), (0.012, 0.12), (0.02, 0.14), (0.001, 0.15)], 12, "metal", BRASS_BRIGHT, desk_f, base=(0.45, -0.18, top_z))
    for i in range(4):
        _book_closed(b, desk_f, 0.02, 0.05, top_z + i * 0.026, 0.22, 0.16, 0.024, BOOK_COLOURS[i % len(BOOK_COLOURS)], yaw=5.0 * i)

    gf = _at(desk_f, (-0.48, 0.0, top_z))
    lathe(b, [(0.001, 0.0), (0.075, 0.0), (0.025, 0.03), (0.02, 0.07)], 12, "wood", WALNUT_DARK, gf, uv=WOOD_DARK_UV)
    ring(b, (0.0, 0.0, 0.18), 0.12, 0.008, "metal", BRASS_AGED, gf, sides=16, tube_sides=3, axis="Y")
    _sphere(b, gf, (0.0, 0.0, 0.18), 0.105, "paint", "5484A8", segments=12)
    _sphere(b, gf, (0.04, -0.05, 0.2), 0.045, "paint", "6B8E5B", scale=(1.0, 0.7, 0.8), segments=6)

    # Teacher's chair behind desk (facing -Y toward desk)
    bentwood_chair(b, _at(frame, (0.0, 0.42, plat_h), 0.0))


MAP_STYLES = ("world", "country", "botany", "alphabet")


def wall_map(b: Builder, frame: Matrix, variant: str = None, **options) -> None:
    """Rolled-down classroom chart on wooden rods (variants: world, country, botany, alphabet); top at 2.3 m."""
    variant = variant or "world"
    wall_y = 0.03
    top_z, bot_z = 2.24, 1.13

    # Suspension cord & wall tack (reaching 2.30 m)
    _cyl(b, frame, (0.0, wall_y - 0.015, 2.29), 0.012, 0.015, 8, "metal", BRASS_AGED, axis="Y")
    _beam(b, frame, (-0.35, wall_y - 0.01, top_z), (0.0, wall_y - 0.01, 2.29), 0.008, 0.008, "paint", LINEN_RAW)
    _beam(b, frame, (0.35, wall_y - 0.01, top_z), (0.0, wall_y - 0.01, 2.29), 0.008, 0.008, "paint", LINEN_RAW)

    for rz in (top_z, bot_z):
        _cyl(b, frame, (-0.71, wall_y - 0.025, rz), 0.018, 1.42, 10, "wood", WALNUT_DARK, axis="X", uv=WOOD_LIGHT_UV)
        for fx in (-0.72, 0.72):
            _sphere(b, frame, (fx, wall_y - 0.025, rz), 0.022, "wood", HONEY_WOOD, segments=6)

    # Chart canvas
    _box(b, frame, (-0.66, wall_y - 0.018, bot_z + 0.015), (0.66, wall_y - 0.005, top_z - 0.015), "paint", PARCHMENT)

    if variant == "world":
        for hx in (-0.31, 0.31):
            _cyl(b, frame, (hx, wall_y - 0.021, 1.68), 0.27, 0.004, 16, "paint", "8EB8CC", axis="Y")
        for cx, cz, rx, rz in ((-0.38, 1.76, 0.12, 0.11), (-0.24, 1.56, 0.08, 0.1), (0.26, 1.78, 0.15, 0.1), (0.38, 1.56, 0.09, 0.08)):
            _sphere(b, frame, (cx, wall_y - 0.022, cz), 1.0, "paint", "759460", scale=(rx, 0.004, rz), segments=8)
    elif variant == "country":
        _box(b, frame, (-0.6, wall_y - 0.02, 1.2), (0.6, wall_y - 0.018, 2.18), "paint", "9ABFD1")
        b.prism([(-0.42, 1.32), (0.35, 1.28), (0.48, 1.72), (0.18, 2.08), (-0.25, 2.02), (-0.46, 1.68)], wall_y - 0.024, wall_y - 0.019, "paint", srgb("D4C48C"), frame=frame)
        _beam(b, frame, (-0.1, wall_y - 0.025, 1.98), (0.22, wall_y - 0.025, 1.42), 0.015, 0.004, "paint", "4C7B9C")
        for cx, cz in ((-0.15, 1.72), (0.18, 1.64), (0.02, 1.88)):
            _box(b, frame, (cx - 0.02, wall_y - 0.026, cz - 0.02), (cx + 0.02, wall_y - 0.022, cz + 0.02), "paint", "9E423B")
    elif variant == "botany":
        for idx, (cx, cz, flower) in enumerate(((-0.34, 1.88, "B55248"), (0.32, 1.88, "C99A3E"), (-0.34, 1.42, "5E7EA8"), (0.32, 1.42, "8E547A"))):
            _beam(b, frame, (cx, wall_y - 0.021, cz - 0.16), (cx, wall_y - 0.021, cz + 0.12), 0.014, 0.004, "paint", "4B7344")
            _sphere(b, frame, (cx, wall_y - 0.022, cz + 0.12), 0.055, "paint", flower, scale=(1.0, 0.1, 0.8), segments=8)
            _box(b, frame, (cx - 0.14, wall_y - 0.021, cz - 0.21), (cx + 0.14, wall_y - 0.019, cz - 0.19), "paint", "4A423A")
    else:
        _box(b, frame, (-0.42, wall_y - 0.022, 2.08), (0.42, wall_y - 0.018, 2.15), "paint", "3A5E8C")
        for r in range(3):
            for c in range(5):
                tx, tz = -0.46 + c * 0.23, 1.88 - r * 0.28
                col = ("9E423B", "3A5E8C", "4D6E56", "B88B4A")[(r + c) % 4]
                _box(b, frame, (tx - 0.075, wall_y - 0.021, tz - 0.08), (tx + 0.075, wall_y - 0.018, tz + 0.08), "paint", col)


def abacus_stand(b: Builder, frame: Matrix, **options) -> None:
    """Large classroom counting abacus on a splayed wooden A-frame stand."""
    generator = random.Random(options.get("seed", 1))
    for sx in (-0.42, 0.42):
        _beam(b, frame, (sx, -0.2, 0.0), (sx, -0.02, 0.56), 0.045, 0.04, "wood", WALNUT_DARK, uv=WOOD_DARK_UV)
        _beam(b, frame, (sx, 0.2, 0.0), (sx, 0.02, 0.56), 0.045, 0.04, "wood", WALNUT_DARK, uv=WOOD_DARK_UV)
        bevel_box(b, frame, (sx - 0.028, -0.03, 0.52), (sx + 0.028, 0.03, 1.42), WALNUT_MID, bevel=0.006)
    wood_box(b, frame, (-0.42, -0.02, 0.24), (0.42, 0.02, 0.29), WALNUT_DARK)
    bevel_box(b, frame, (-0.45, -0.035, 0.52), (0.45, 0.035, 0.57), HONEY_WOOD, bevel=0.006, light=True)
    bevel_box(b, frame, (-0.47, -0.04, 1.38), (0.47, 0.04, 1.45), HONEY_WOOD, bevel=0.008, light=True)

    bead_cols = ("8E423F", "5A738E", "B88B4A", "4D6E56", WALNUT_DARK, HONEY_WOOD)
    for row in range(6):
        wz = 0.66 + row * 0.12
        _cyl(b, frame, (-0.42, 0.0, wz), 0.006, 0.84, 6, "metal", BRASS_AGED, axis="X")
        left_count = generator.randint(2, 7)
        for i in range(10):
            bx = (-0.36 + i * 0.052) if i < left_count else (0.36 - (9 - i) * 0.052)
            # 12-triangle bicone bead
            pts = [(0.024 * math.cos(math.pi * k / 3.0), 0.032 * math.sin(math.pi * k / 3.0), 0.0) for k in range(6)]
            pts = [(bx + px, py, wz) for px, py, _ in pts] + [(bx - 0.02, 0.0, wz), (bx + 0.02, 0.0, wz)]
            solid_hull(b, pts, "paint", bead_cols[row], frame)


def specimen_cupboard(b: Builder, frame: Matrix, **options) -> None:
    """Glazed natural-history cabinet with books, jars, a stuffed bird and mineral samples."""
    half_w, half_d = 0.63, 0.23
    _cabinet_base(b, frame, half_w, half_d, foot_h=0.07, plinth_h=0.08)
    bevel_box(b, frame, (-half_w + 0.02, -half_d + 0.02, 0.15), (half_w - 0.02, half_d, 0.64), WALNUT_MID, bevel=0.006)
    for sx in (-1.0, 1.0):
        raised_panel(b, frame, sx * 0.31 - 0.24, sx * 0.31 + 0.24, 0.18, 0.6, -half_d + 0.01, WALNUT_MID, border=0.04, depth=0.012)
        knob(b, frame, sx * 0.09, -half_d - 0.008, 0.42, 0.014, BRASS_AGED)

    # Upper glazed case (0.64..2.05)
    wood_box(b, frame, (-half_w, 0.2, 0.64), (half_w, half_d, 1.97), WALNUT_DARK)
    for sx in (-half_w, half_w - 0.05):
        wood_box(b, frame, (sx, -half_d, 0.64), (sx + 0.05, 0.2, 1.97), WALNUT_MID)
    for sz in (0.66, 1.1, 1.52):
        wood_box(b, frame, (-half_w + 0.05, -half_d + 0.03, sz - 0.03), (half_w - 0.05, 0.2, sz), HONEY_WOOD, light=True)

    # Glazed doors with wooden stiles & mullions
    _box(b, frame, (-half_w + 0.06, -half_d + 0.008, 0.68), (half_w - 0.06, -half_d + 0.014, 1.94), "vitrine", "FFFFFF")
    for mx in (-half_w + 0.06, -0.02, half_w - 0.09):
        wood_box(b, frame, (mx, -half_d - 0.006, 0.68), (mx + 0.035, -half_d + 0.015, 1.94), WALNUT_DARK)
    for mz in (0.68, 1.32, 1.92):
        wood_box(b, frame, (-half_w + 0.05, -half_d - 0.006, mz), (half_w - 0.05, -half_d + 0.015, mz + 0.03), WALNUT_DARK)
    run_profile(b, frame, -0.64, 0.64, cornice_profile(-half_d, 1.91, 0.025, 0.06), WALNUT_DARK)
    bevel_box(b, frame, (-0.65, -0.25, 1.97), (0.65, 0.25, 2.05), HONEY_WOOD, bevel=0.01, light=True)

    # Specimens inside: books, jars, stuffed bird, minerals
    for i in range(6):
        _book_closed(b, frame, -0.46 + i * 0.065, 0.02, 0.66, 0.05, 0.24, 0.24 + (i % 3) * 0.04, BOOK_COLOURS[i % len(BOOK_COLOURS)])
    for i in range(3):
        _glass_bottle(b, frame, 0.1 + i * 0.17, 0.02, 0.66, r=0.055, h=0.22 + (i % 2) * 0.05, hex_col=BOTTLE_COLOURS[i], label=True)

    # Stuffed bird on wooden T-perch (middle shelf z = 1.10)
    _cyl(b, frame, (-0.28, 0.0, 1.1), 0.045, 0.02, 8, "wood", WALNUT_DARK, uv=WOOD_LIGHT_UV)
    _cyl(b, frame, (-0.28, 0.0, 1.12), 0.01, 0.14, 6, "wood", HONEY_WOOD)
    _cyl(b, frame, (-0.36, 0.0, 1.25), 0.008, 0.16, 6, "wood", HONEY_WOOD, axis="X")
    _sphere(b, frame, (-0.28, 0.0, 1.31), 1.0, "paint", "6A5240", scale=(0.05, 0.08, 0.055), segments=8)
    _sphere(b, frame, (-0.28, -0.075, 1.36), 0.032, "paint", "523C2C", segments=6)
    _beam(b, frame, (-0.28, -0.1, 1.36), (-0.28, -0.14, 1.35), 0.012, 0.012, "paint", "C89B45")
    _beam(b, frame, (-0.28, 0.06, 1.3), (-0.28, 0.16, 1.26), 0.04, 0.01, "paint", "4B3629")

    # Mineral crystals on top shelf (z = 1.52) and jars beside bird
    _glass_bottle(b, frame, 0.25, 0.02, 1.1, r=0.06, h=0.24, hex_col="5E8C8A", label=True)
    for mx, mcol in ((-0.4, "7E5E9C"), (-0.1, "5C8C68"), (0.2, "C8A054"), (0.44, "8C5248")):
        _box(b, frame, (mx - 0.06, -0.06, 1.52), (mx + 0.06, 0.06, 1.54), "wood", WALNUT_DARK, uv=WOOD_LIGHT_UV)
        _cyl(b, frame, (mx, 0.0, 1.54), 0.042, 0.14, 6, "paint", mcol, top_radius=0.005)
        _cyl(b, _at(frame, (mx + 0.025, -0.01, 1.54), 22.0, "Y"), (0.0, 0.0, 0.0), 0.028, 0.1, 6, "paint", mcol, top_radius=0.004)


def study_table(b: Builder, frame: Matrix, **options) -> None:
    """Long study table with two green-shaded oil lamps, open books, inkstand and papers."""
    top_z = 0.78
    for lx, ly in itertools.product((-1.32, 0.0, 1.32), (-0.38, 0.38)):
        turned_leg(b, frame, lx, ly, top_z - 0.05, 0.042, WALNUT_DARK, "baluster", sides=8)
    wood_box(b, frame, (-1.34, -0.03, 0.2), (1.34, 0.03, 0.24), WALNUT_DARK)
    for lx in (-1.32, 0.0, 1.32):
        wood_box(b, frame, (lx - 0.025, -0.38, 0.2), (lx + 0.025, 0.38, 0.24), WALNUT_DARK)

    wood_box(b, frame, (-1.42, -0.44, top_z - 0.16), (1.42, 0.44, top_z - 0.05), WALNUT_MID)
    bevel_box(b, frame, (-1.5, -0.5, top_z - 0.05), (1.5, 0.5, top_z), HONEY_WOOD, bevel=0.012, light=True)
    _box(b, frame, (-1.36, -0.38, top_z), (1.36, 0.38, top_z + 0.005), "paint", LEATHER_GREEN)

    for lamp_x in (-0.85, 0.85):
        _oil_lamp_unit(b, frame, lamp_x, 0.0, top_z + 0.005, shade_col=LAMP_SHADE_GREEN)

    # Open books, stacked closed books, inkstand and papers
    _book_open(b, frame, -0.35, -0.18, top_z + 0.005, 0.34, 0.24, BOOK_COLOURS[0], yaw=-8.0)
    _book_open(b, frame, 0.35, 0.16, top_z + 0.005, 0.34, 0.24, BOOK_COLOURS[1], yaw=172.0)
    for i in range(3):
        _book_closed(b, frame, -1.24, 0.2, top_z + 0.005 + i * 0.032, 0.2, 0.26, 0.03, BOOK_COLOURS[i], yaw=6.0 * i)

    # Brass inkstand and papers in centre
    _box(b, frame, (-0.1, -0.07, top_z + 0.005), (0.1, 0.07, top_z + 0.02), "metal", BRASS_AGED)
    for wx in (-0.055, 0.055):
        _cyl(b, frame, (wx, 0.0, top_z + 0.02), 0.024, 0.04, 10, "paint", "2C354A")
        _cyl(b, frame, (wx, 0.0, top_z + 0.06), 0.014, 0.01, 10, "metal", BRASS_BRIGHT)
    _beam(b, frame, (-0.055, 0.0, top_z + 0.05), (0.04, 0.06, top_z + 0.22), 0.012, 0.006, "paint", LINEN_CREAM)

    for px, py, yaw in ((0.08, -0.24, 10.0), (1.18, -0.16, -15.0)):
        pf = _at(frame, (px, py, top_z + 0.006), yaw)
        _box(b, pf, (-0.1, -0.13, 0.0), (0.1, 0.13, 0.006), "paint", PARCHMENT)


# ---------- chapel ----------

def confessional(b: Builder, frame: Matrix, **options) -> None:
    """Three-bay wooden confessional with curtains on side alcoves, panelled door, cornice and cross."""
    bevel_box(b, frame, (-0.98, -0.48, 0.0), (0.98, 0.48, 0.08), WALNUT_DARK, bevel=0.01)
    wood_box(b, frame, (-0.96, 0.42, 0.08), (0.96, 0.48, 2.2), WALNUT_DARK)
    for sx in (-0.96, -0.34, 0.34, 0.96):
        wood_box(b, frame, (sx - 0.03, -0.46, 0.08), (sx + 0.03, 0.44, 2.2), WALNUT_MID)

    # Central priest bay door + upper lattice grille
    raised_panel(b, frame, -0.28, 0.28, 0.12, 1.15, -0.44, WALNUT_MID, border=0.04, depth=0.012)
    knob(b, frame, 0.2, -0.465, 0.85, 0.014, BRASS_AGED)
    wood_box(b, frame, (-0.31, -0.45, 1.18), (0.31, -0.42, 2.12), WALNUT_DARK)
    for gx in (-0.2, -0.07, 0.07, 0.2):
        wood_box(b, frame, (gx - 0.012, -0.46, 1.24), (gx + 0.012, -0.44, 2.06), HONEY_WOOD, light=True)

    # Flanking penitent alcoves: kneelers, brass rods & pleated wine curtains
    for sx in (-1.0, 1.0):
        bx = sx * 0.65
        _box(b, frame, (bx - 0.24, -0.28, 0.08), (bx + 0.24, -0.05, 0.16), "paint", CHAPEL_WINE)
        _cyl(b, frame, (bx - 0.28, -0.44, 2.06), 0.012, 0.56, 8, "metal", BRASS_AGED, axis="X")
        for i in range(4):
            cx = bx - 0.21 + i * 0.11
            _box(b, _at(frame, (cx, -0.43, 0.12), 18.0 if i % 2 else -18.0), (-0.06, -0.012, 0.0), (0.06, 0.012, 1.94), "paint", CHAPEL_WINE)

    # Moulded cornice, pediment and cross (top 2.50 m)
    run_profile(b, frame, -0.99, 0.99, cornice_profile(-0.46, 2.16, 0.04, 0.08), WALNUT_DARK)
    bevel_box(b, frame, (-1.0, -0.5, 2.2), (1.0, 0.5, 2.28), HONEY_WOOD, bevel=0.012, light=True)
    b.prism([(-0.42, 2.28), (0.42, 2.28), (0.0, 2.38)], -0.48, -0.42, "wood", srgb(WALNUT_DARK), frame=frame, uv=WOOD_DARK_UV)
    wood_box(b, frame, (-0.025, -0.47, 2.35), (0.025, -0.43, 2.5), WALNUT_DARK)
    wood_box(b, frame, (-0.075, -0.47, 2.43), (0.075, -0.43, 2.47), WALNUT_DARK)


def harmonium(b: Builder, frame: Matrix, **options) -> None:
    """Chapel reed organ with manual keyboard, foot treadles, music desk with hymn book and round stool."""
    # Case placed toward +Y so stool fits cleanly within -0.475..+0.475
    bevel_box(b, frame, (-0.6, -0.04, 0.0), (0.6, 0.45, 0.72), WALNUT_DARK, bevel=0.008)
    _box(b, frame, (-0.42, -0.045, 0.08), (0.42, 0.04, 0.64), "paint", "2E2320")
    for px in (-0.16, 0.16):
        pf = _at(frame, (px, -0.04, 0.06), -22.0, "X")
        _box(b, pf, (-0.07, -0.12, 0.0), (0.07, 0.02, 0.025), "paint", CHAPEL_WINE)

    # Keyboard shelf and keys
    bevel_box(b, frame, (-0.62, -0.2, 0.7), (0.62, 0.45, 0.76), HONEY_WOOD, bevel=0.01, light=True)
    _box(b, frame, (-0.52, -0.18, 0.76), (0.52, -0.02, 0.785), "paint", OPAL_GLASS)
    for k in range(21):
        if k % 7 in (2, 6):
            continue
        kx = -0.49 + k * 0.049
        _box(b, frame, (kx - 0.012, -0.11, 0.785), (kx + 0.012, -0.02, 0.8), "paint", "242024")

    # Upper organ case, stops, music desk and hymn book
    bevel_box(b, frame, (-0.6, 0.0, 0.76), (0.6, 0.45, 1.18), WALNUT_MID, bevel=0.008)
    for sx in range(8):
        knob(b, frame, -0.35 + sx * 0.1, -0.01, 0.835, 0.012, OPAL_GLASS)
    _box(b, frame, (-0.48, -0.005, 0.9), (0.48, 0.01, 1.12), "paint", CHAPEL_WINE)
    bevel_box(b, frame, (-0.62, -0.02, 1.18), (0.62, 0.47, 1.24), HONEY_WOOD, bevel=0.01, light=True)

    desk = _at(frame, (0.0, -0.02, 0.94), 20.0, "X")
    _box(b, desk, (-0.24, -0.015, 0.0), (0.24, 0.015, 0.2), "wood", WALNUT_DARK, uv=WOOD_DARK_UV)
    _book_open(b, _at(desk, (0.0, -0.02, 0.1), -70.0, "X"), 0.0, 0.0, 0.0, 0.3, 0.2, CHAPEL_WINE)

    # Round turned stool in front (-Y)
    sf = _at(frame, (0.0, -0.31, 0.0))
    lathe(b, [(0.15, 0.0), (0.15, 0.03), (0.04, 0.07), (0.035, 0.42), (0.15, 0.45), (0.15, 0.49), (0.001, 0.49)], 14, "wood", WALNUT_DARK, sf, uv=WOOD_LIGHT_UV)
    _cyl(b, sf, (0.0, 0.0, 0.49), 0.145, 0.04, 14, "paint", CHAPEL_WINE)


def holy_water_font(b: Builder, frame: Matrix, **options) -> None:
    """Carved stone holy water stoup on a turned baluster pedestal."""
    _box(b, frame, (-0.21, -0.21, 0.0), (0.21, 0.21, 0.08), "stone", STONE_WARM)
    pedestal = [
        (0.17, 0.08), (0.17, 0.13), (0.11, 0.19), (0.08, 0.28),
        (0.12, 0.48), (0.075, 0.68), (0.11, 0.78), (0.1, 0.84),
    ]
    lathe(b, pedestal, 16, "stone", STONE_LIGHT, frame)
    bowl = [(0.08, 0.84), (0.19, 0.92), (0.22, 1.04), (0.22, 1.09), (0.18, 1.09), (0.16, 0.98), (0.001, 0.95)]
    lathe(b, bowl, 16, "stone", STONE_LIGHT, frame)
    _cyl(b, frame, (0.0, 0.0, 1.03), 0.17, 0.015, 16, "water", "6CA8C4")


def saint_niche(b: Builder, frame: Matrix, **options) -> None:
    """Wall bracket with gothic-colonial canopy holding a painted statue and two candles (bottom at 1.2 m)."""
    wall_y = 0.175
    # Bracket shelf and carved corbel (1.20..1.52)
    b.side_prism([(wall_y, 1.2), (wall_y - 0.04, 1.2), (-0.12, 1.46), (wall_y, 1.46)], -0.14, 0.14, "wood", srgb(WALNUT_DARK), frame=frame, uv=WOOD_DARK_UV)
    bevel_box(b, frame, (-0.39, -0.16, 1.46), (0.39, wall_y, 1.52), WALNUT_MID, bevel=0.01)

    # Back panel, flanking colonnettes, and pointed canopy (1.52..2.90)
    wood_box(b, frame, (-0.36, wall_y - 0.04, 1.52), (0.36, wall_y, 2.58), WALNUT_DARK)
    _box(b, frame, (-0.28, wall_y - 0.048, 1.56), (0.28, wall_y - 0.04, 2.48), "paint", "3D4F6E")
    for sx in (-0.32, 0.32):
        turned_leg(b, frame, sx, -0.1, 1.02, 0.024, HONEY_WOOD, "column", z=1.52, sides=10)
    bevel_box(b, frame, (-0.4, -0.17, 2.54), (0.4, wall_y, 2.64), WALNUT_MID, bevel=0.01)
    b.prism([(-0.36, 2.64), (0.36, 2.64), (0.0, 2.84)], -0.15, wall_y, "wood", srgb(WALNUT_DARK), frame=frame, uv=WOOD_DARK_UV)
    wood_box(b, frame, (-0.02, -0.05, 2.8), (0.02, 0.0, 2.9), HONEY_WOOD, light=True)
    wood_box(b, frame, (-0.05, -0.05, 2.85), (0.05, 0.0, 2.88), HONEY_WOOD, light=True)

    # Painted saint statue on plinth
    _cyl(b, frame, (0.0, 0.02, 1.52), 0.11, 0.06, 12, "stone", STONE_LIGHT)
    lathe(b, [(0.1, 1.58), (0.085, 1.85), (0.105, 2.12), (0.06, 2.2), (0.001, 2.22)], 12, "paint", LINEN_CREAM, frame, base=(0.0, 0.02, 0.0))
    lathe(b, [(0.108, 1.72), (0.112, 2.13), (0.05, 2.21)], 12, "paint", AZULEJO_BLUE, frame, base=(0.0, 0.02, 0.0))
    _sphere(b, frame, (0.0, 0.02, 2.29), 0.058, "paint", "E0C0A4", segments=8)
    ring(b, (0.0, 0.05, 2.31), 0.085, 0.007, "metal", BRASS_BRIGHT, frame, sides=16, tube_sides=3, axis="Y")

    # Two flanking candlesticks
    for cx in (-0.23, 0.23):
        _candlestick(b, frame, cx, -0.06, 1.52, stand_h=0.14, candle_h=0.12)


def prie_dieu(b: Builder, frame: Matrix, **options) -> None:
    """Wooden prayer kneeler with padded kneeler, pierced front panel, sloped armrest shelf and prayer book."""
    for sx in (-0.26, 0.26):
        bevel_box(b, frame, (sx - 0.03, -0.32, 0.0), (sx + 0.03, 0.32, 0.05), WALNUT_DARK, bevel=0.006)
        bevel_box(b, frame, (sx - 0.025, -0.28, 0.05), (sx + 0.025, -0.2, 0.85), WALNUT_MID, bevel=0.006)

    # Kneeler pad at +Y (worshipper faces -Y)
    wood_box(b, frame, (-0.26, 0.04, 0.05), (0.26, 0.31, 0.1), WALNUT_MID)
    _soft_block(b, frame, (0.0, 0.175, 0.135), (0.24, 0.125, 0.04), CHAPEL_WINE, bevel=0.015)

    # Front cross-carved panel and mid book shelf
    wood_box(b, frame, (-0.24, -0.26, 0.14), (0.24, -0.22, 0.8), WALNUT_DARK)
    wood_box(b, frame, (-0.03, -0.27, 0.24), (0.03, -0.21, 0.7), HONEY_WOOD, light=True)
    wood_box(b, frame, (-0.14, -0.27, 0.5), (0.14, -0.21, 0.56), HONEY_WOOD, light=True)
    wood_box(b, frame, (-0.24, -0.22, 0.56), (0.24, -0.06, 0.6), WALNUT_MID)

    # Sloped armrest / book rest and prayer book
    rest = _at(frame, (0.0, -0.18, 0.86), -16.0, "X")
    bevel_box(b, rest, (-0.3, -0.15, -0.025), (0.3, 0.15, 0.015), HONEY_WOOD, bevel=0.008, light=True)
    _soft_block(b, rest, (0.0, 0.09, 0.025), (0.27, 0.045, 0.02), CHAPEL_WINE, bevel=0.01)
    _book_closed(b, rest, 0.0, -0.04, 0.015, 0.18, 0.14, 0.032, CHAPEL_WINE, yaw=4.0)


def sanctuary_lamp(b: Builder, frame: Matrix, **options) -> None:
    """Brass sanctuary lamp on three chains with red glass cup (hang, soft warm light)."""
    lathe(b, [(0.08, 0.0), (0.06, -0.03), (0.025, -0.06), (0.001, -0.06)], 16, "metal", BRASS_AGED, frame)
    _cyl(b, frame, (0.0, 0.0, -0.5), 0.007, 0.44, 6, "metal", BRASS_AGED)
    _sphere(b, frame, (0.0, 0.0, -0.5), 0.024, "metal", BRASS_BRIGHT, segments=8)

    ring_z = -1.04
    for i in range(3):
        ang = math.radians(i * 120.0 + 30.0)
        _beam(b, frame, (0.0, 0.0, -0.5), (0.135 * math.cos(ang), 0.135 * math.sin(ang), ring_z), 0.009, 0.009, "metal", BRASS_AGED)

    ring(b, (0.0, 0.0, ring_z), 0.14, 0.012, "metal", BRASS_BRIGHT, frame, sides=16, tube_sides=4)
    lathe(b, [(0.03, -1.2), (0.085, -1.16), (0.11, -1.04), (0.125, -0.94), (0.1, -0.94), (0.075, -1.12), (0.001, -1.14)], 16, "paint", "8E1B24", frame)
    _cyl(b, frame, (0.0, 0.0, -1.05), 0.015, 0.06, 6, "glow_warm", "FFFFFF", top_radius=0.004)
    lathe(b, [(0.035, -1.2), (0.045, -1.25), (0.015, -1.34), (0.001, -1.4)], 12, "metal", BRASS_AGED, frame)


# ---------- washroom, infirmary, linen ----------

def basin_row(b: Builder, frame: Matrix, **options) -> None:
    """Four-station colonial washstand: marble top, four enamel basins with jugs and soap, towel bar, four mirrors."""
    top_z = 0.78
    for lx, ly in itertools.product((-1.2, 0.0, 1.2), (-0.22, 0.22)):
        turned_leg(b, frame, lx, ly, top_z - 0.04, 0.032, WALNUT_DARK, "baluster", sides=8)

    wood_box(b, frame, (-1.22, -0.23, 0.18), (1.22, 0.23, 0.21), WALNUT_MID)
    wood_box(b, frame, (-1.24, -0.25, top_z - 0.16), (1.24, 0.25, top_z - 0.04), WALNUT_MID)
    bevel_box(b, frame, (-1.3, -0.28, top_z - 0.04), (1.3, 0.28, top_z + 0.01), MARBLE_CREAM, bevel=0.008, material="paint")

    # Brass front towel bar with four draped hand towels
    _cyl(b, frame, (-1.22, -0.27, 0.66), 0.01, 2.44, 8, "metal", BRASS_AGED, axis="X")
    for sx in (-0.93, -0.31, 0.31, 0.93):
        _draped_towel(b, frame, sx, -0.27, 0.66, 0.24, 0.26, LINEN_CREAM, axis="X", stripe=AZULEJO_BLUE)

        # Basin, pitcher and soap dish per station
        _enamel_bowl(b, frame, sx - 0.07, -0.02, top_z + 0.01, radius=0.14, height=0.095, sides=16)
        _cyl(b, frame, (sx - 0.07, -0.02, top_z + 0.07), 0.115, 0.01, 14, "water", "72AFC9")
        _ceramic_jug(b, frame, sx + 0.14, 0.05, top_z + 0.01, scale=0.88, sides=12)
        _box(b, frame, (sx + 0.09, -0.18, top_z + 0.01), (sx + 0.19, -0.1, top_z + 0.025), "paint", ENAMEL_CREAM)
        _box(b, frame, (sx + 0.11, -0.16, top_z + 0.025), (sx + 0.17, -0.12, top_z + 0.042), "paint", "D9C39E")

    # Backboard and four small framed mirrors (0.81..1.75)
    wood_box(b, frame, (-1.28, 0.23, top_z + 0.01), (1.28, 0.28, 1.7), WALNUT_DARK)
    bevel_box(b, frame, (-1.3, 0.2, 1.69), (1.3, 0.29, 1.75), HONEY_WOOD, bevel=0.01, light=True)
    for sx in (-0.93, -0.31, 0.31, 0.93):
        wood_box(b, frame, (sx - 0.19, 0.2, 1.06), (sx + 0.19, 0.23, 1.62), HONEY_WOOD, light=True)
        _box(b, frame, (sx - 0.15, 0.195, 1.1), (sx + 0.15, 0.205, 1.58), "paint", "B7CED9")


def tin_bathtub(b: Builder, frame: Matrix, **options) -> None:
    """Painted tin hip bath with rolled rim, water, bucket and bath stool with folded towel."""
    oval = _at(frame, (-0.28, 0.0, 0.0)) @ Matrix.Diagonal((1.0, 0.72, 1.0, 1.0))
    _cyl(b, oval, (0.0, 0.0, 0.0), 0.38, 0.04, 16, "metal", WROUGHT_IRON)
    lathe(b, [(0.36, 0.04), (0.44, 0.22), (0.48, 0.44), (0.45, 0.44), (0.41, 0.22), (0.33, 0.08), (0.001, 0.08)], 16, "paint", TIN_PAINTED, oval)
    ring(b, (0.0, 0.0, 0.445), 0.47, 0.016, "metal", BRASS_AGED, oval, sides=16, tube_sides=4)
    _cyl(b, oval, (0.0, 0.0, 0.36), 0.41, 0.015, 16, "water", "6BA9C4")

    # Raised curved hip-bath backrest on -X end (up to 0.72 m)
    b.prism([(-0.77, 0.42), (-0.42, 0.42), (-0.52, 0.66), (-0.72, 0.72)], -0.26, 0.26, "paint", srgb(TIN_PAINTED), frame=frame)
    _box(b, frame, (-0.78, -0.27, 0.68), (-0.7, 0.27, 0.73), "metal", BRASS_AGED)

    # Water bucket & stool with towel on the +X side
    _wicker_basket(b, frame, 0.56, -0.18, 0.0, r_bot=0.11, r_top=0.14, height=0.28, tint=TIN_PAINTED)
    ring(b, (0.56, -0.18, 0.27), 0.14, 0.007, "metal", WROUGHT_IRON, frame, sides=12, tube_sides=3)

    sf = _at(frame, (0.56, 0.18, 0.0))
    for sx, sy in itertools.product((-0.11, 0.11), repeat=2):
        _cyl(b, sf, (sx, sy, 0.0), 0.018, 0.36, 8, "wood", WALNUT_MID, uv=WOOD_LIGHT_UV)
    _cyl(b, sf, (0.0, 0.0, 0.35), 0.17, 0.035, 14, "wood", HONEY_WOOD, uv=WOOD_LIGHT_UV)
    _soft_block(b, sf, (0.0, 0.0, 0.415), (0.13, 0.11, 0.028), LINEN_CREAM, bevel=0.012)


def towel_rack(b: Builder, frame: Matrix, **options) -> None:
    """Free-standing wooden towel horse with tiered rails and hanging linen towels."""
    for sx in (-0.54, 0.54):
        bevel_box(b, frame, (sx - 0.03, -0.17, 0.0), (sx + 0.03, 0.17, 0.06), WALNUT_DARK, bevel=0.008)
        turned_leg(b, frame, sx, 0.0, 1.4, 0.025, WALNUT_MID, "baluster", z=0.06, sides=10)
        _sphere(b, frame, (sx, 0.0, 1.475), 0.025, "wood", HONEY_WOOD, segments=8)

    wood_box(b, frame, (-0.54, -0.02, 0.22), (0.54, 0.02, 0.25), WALNUT_DARK)
    for ry, rz in ((-0.09, 0.85), (0.0, 1.15), (0.09, 1.4)):
        _cyl(b, frame, (-0.54, ry, rz), 0.014, 1.08, 10, "wood", HONEY_WOOD, axis="X", uv=WOOD_LIGHT_UV)

    towels = ((-0.28, -0.09, 0.85, 0.28, 0.36, LINEN_CREAM), (0.28, -0.09, 0.85, 0.26, 0.34, LINEN_RAW), (-0.22, 0.0, 1.15, 0.32, 0.42, LINEN_CREAM), (0.26, 0.09, 1.4, 0.34, 0.45, LINEN_RAW))
    for tx, ty, tz, tw, td, tcol in towels:
        _draped_towel(b, frame, tx, ty, tz, tw, td, tcol, axis="X", stripe=AZULEJO_BLUE)


def copper_boiler(b: Builder, frame: Matrix, **options) -> None:
    """Riveted copper hot-water boiler on a cylindrical brick firebox with tap and flue pipe."""
    _box(b, frame, (-0.38, -0.38, 0.0), (0.38, 0.38, 0.1), "stone", STONE_WARM)
    _cyl(b, frame, (0.0, 0.0, 0.1), 0.33, 0.62, 16, "brick", BRICK_OLD)
    metal_box(b, frame, (-0.14, -0.35, 0.22), (0.14, -0.31, 0.56), WROUGHT_IRON)
    _box(b, frame, (-0.09, -0.355, 0.28), (0.09, -0.345, 0.5), "glow_ember", "FFFFFF")
    metal_box(b, frame, (-0.18, -0.36, 0.16), (0.18, -0.32, 0.22), CAST_IRON)

    boiler_prof = [(0.001, 0.72), (0.32, 0.72), (0.33, 0.78), (0.33, 1.32), (0.28, 1.4), (0.12, 1.44), (0.001, 1.45)]
    lathe(b, boiler_prof, 16, "metal", COPPER_WARE, frame)
    for hz in (0.82, 1.28):
        ring(b, (0.0, 0.0, hz), 0.335, 0.01, "metal", BRASS_AGED, frame, sides=16, tube_sides=4)

    # Brass water tap at front (-Y) and top lid handle
    _cyl(b, frame, (0.0, -0.39, 0.8), 0.015, 0.08, 8, "metal", BRASS_BRIGHT, axis="Y")
    _cyl(b, frame, (0.0, -0.38, 0.76), 0.011, 0.04, 8, "metal", BRASS_BRIGHT)
    _sphere(b, frame, (0.0, 0.0, 1.47), 0.025, "metal", BRASS_AGED, segments=6)

    # Flue pipe rising at back (+Y) to 2.0 m
    _cyl(b, frame, (0.0, 0.22, 0.72), 0.075, 1.28, 12, "metal", WROUGHT_IRON)
    ring(b, (0.0, 0.22, 1.45), 0.085, 0.01, "metal", BRASS_AGED, frame, sides=12, tube_sides=3)


def folding_screen(b: Builder, frame: Matrix, **options) -> None:
    """Three-panel infirmary privacy screen of white linen stretched inside hinged wooden frames."""
    panel_w = 0.58
    angles = (26.0, -26.0, 26.0)
    # Place panel hinges in a zig-zag centered around X=0, Y=0
    cx = -panel_w * math.cos(math.radians(26.0)) * 1.5
    cy = -panel_w * math.sin(math.radians(26.0)) * 0.5
    for idx, deg in enumerate(angles):
        rad = math.radians(deg)
        nx = cx + panel_w * math.cos(rad)
        ny = cy + panel_w * math.sin(rad)
        pf = _at(frame, ((cx + nx) / 2.0, (cy + ny) / 2.0, 0.0), deg)
        hw = panel_w / 2.0
        for sx in (-hw + 0.02, hw - 0.02):
            wood_box(b, pf, (sx - 0.02, -0.02, 0.0), (sx + 0.02, 0.02, 1.76), WALNUT_DARK)
            _sphere(b, pf, (sx, 0.0, 1.78), 0.02, "wood", HONEY_WOOD, segments=6)
        for rz in (0.1, 0.5, 1.72):
            wood_box(b, pf, (-hw + 0.04, -0.018, rz), (hw - 0.04, 0.018, rz + 0.035), WALNUT_MID)
        # Pleated linen insert
        for p in range(5):
            px = -hw + 0.08 + p * ((panel_w - 0.16) / 4.0)
            dy = 0.008 if p % 2 else -0.008
            _box(b, pf, (px - 0.055, dy - 0.006, 0.135), (px + 0.055, dy + 0.006, 1.72), "paint", LINEN_CREAM)
        if idx > 0:
            for hz in (0.4, 1.4):
                _cyl(b, frame, (cx, cy, hz), 0.012, 0.06, 8, "metal", BRASS_AGED)
        cx, cy = nx, ny


def medicine_cabinet(b: Builder, frame: Matrix, **options) -> None:
    """Glazed infirmary apothecary cabinet with bottles and pill boxes above, labelled drawers below."""
    half_w, half_d = 0.48, 0.185
    _cabinet_base(b, frame, half_w, half_d, foot_h=0.07, plinth_h=0.08)
    bevel_box(b, frame, (-half_w + 0.02, -half_d + 0.02, 0.15), (half_w - 0.02, half_d, 0.68), WALNUT_MID, bevel=0.006)

    for col, row in itertools.product(range(2), range(2)):
        dx = -0.22 + col * 0.44
        dz = 0.29 + row * 0.24
        bevel_box(b, frame, (dx - 0.19, -half_d - 0.005, dz - 0.1), (dx + 0.19, -half_d + 0.015, dz + 0.1), HONEY_WOOD, bevel=0.005, light=True)
        _box(b, frame, (dx - 0.06, -half_d - 0.009, dz + 0.025), (dx + 0.06, -half_d - 0.004, dz + 0.065), "paint", PARCHMENT)
        knob(b, frame, dx, -half_d - 0.01, dz - 0.035, 0.013, BRASS_AGED)

    # Upper glazed section (0.68..1.95)
    wood_box(b, frame, (-half_w, 0.17, 0.68), (half_w, half_d, 1.88), WALNUT_DARK)
    for sx in (-half_w, half_w - 0.04):
        wood_box(b, frame, (sx, -half_d, 0.68), (sx + 0.04, 0.17, 1.88), WALNUT_MID)
    for sz in (0.7, 1.1, 1.48):
        wood_box(b, frame, (-half_w + 0.04, -half_d + 0.02, sz - 0.025), (half_w - 0.04, 0.17, sz), HONEY_WOOD, light=True)

    _box(b, frame, (-half_w + 0.04, -half_d + 0.006, 0.72), (half_w - 0.04, -half_d + 0.012, 1.85), "vitrine", "FFFFFF")
    for mx in (-half_w + 0.04, -0.015, half_w - 0.07):
        wood_box(b, frame, (mx, -half_d - 0.005, 0.72), (mx + 0.03, -half_d + 0.012, 1.85), WALNUT_DARK)
    run_profile(b, frame, -half_w - 0.01, half_w + 0.01, cornice_profile(-half_d, 1.82, 0.02, 0.06), WALNUT_DARK)
    bevel_box(b, frame, (-0.5, -0.21, 1.88), (0.5, 0.21, 1.95), HONEY_WOOD, bevel=0.01, light=True)

    # Medicine bottles & boxes on shelves
    for s_idx, sz in enumerate((0.7, 1.1, 1.48)):
        for i in range(4):
            bx = -0.32 + i * 0.21
            if (s_idx + i) % 3 == 0:
                _box(b, frame, (bx - 0.06, -0.08, sz), (bx + 0.06, 0.08, sz + 0.08), "paint", ENAMEL_CREAM)
                _box(b, frame, (bx - 0.065, -0.085, sz + 0.065), (bx + 0.065, 0.085, sz + 0.085), "paint", AZULEJO_BLUE)
            else:
                _glass_bottle(b, frame, bx, 0.0, sz, r=0.042, h=0.2 + (i % 2) * 0.05, hex_col=BOTTLE_COLOURS[(s_idx + i) % len(BOTTLE_COLOURS)], label=True)


def nurse_table(b: Builder, frame: Matrix, **options) -> None:
    """Enamel-topped infirmary dressing table with basin, bottles, folded cloths and metal tray."""
    top_z = 0.78
    for lx, ly in itertools.product((-0.52, 0.52), (-0.24, 0.24)):
        turned_leg(b, frame, lx, ly, top_z - 0.04, 0.028, WALNUT_MID, "taper", sides=8)
    wood_box(b, frame, (-0.54, -0.25, 0.2), (0.54, 0.25, 0.23), HONEY_WOOD, light=True)
    wood_box(b, frame, (-0.54, -0.25, top_z - 0.16), (0.54, 0.25, top_z - 0.04), WALNUT_MID)
    for dx in (-0.26, 0.26):
        bevel_box(b, frame, (dx - 0.22, -0.26, top_z - 0.14), (dx + 0.22, -0.245, top_z - 0.06), HONEY_WOOD, bevel=0.005, light=True)
        knob(b, frame, dx, -0.262, top_z - 0.1, 0.012, BRASS_AGED)

    # White enamel top with raised lip
    bevel_box(b, frame, (-0.6, -0.3, top_z - 0.04), (0.6, 0.3, top_z), ENAMEL_CREAM, bevel=0.008, material="paint")
    _box(b, frame, (-0.6, 0.285, top_z), (0.6, 0.3, top_z + 0.025), "paint", ENAMEL_RIM)

    _enamel_bowl(b, frame, -0.36, -0.02, top_z, radius=0.13, height=0.075, sides=16)
    for i, col in enumerate(("8E5D38", "3B5882", "4A7A68")):
        _glass_bottle(b, frame, -0.06 + i * 0.11, 0.1, top_z, r=0.036, h=0.16 + (i % 2) * 0.04, hex_col=col, label=True)

    # Metal tray and stacked folded cloths
    _box(b, frame, (-0.08, -0.22, top_z), (0.24, -0.02, top_z + 0.015), "metal", PEWTER)
    _cyl(b, frame, (0.0, -0.12, top_z + 0.015), 0.015, 0.14, 6, "metal", TIN_PAINTED, axis="X")
    for layer in range(3):
        _soft_block(b, frame, (0.4, 0.0, top_z + 0.018 + layer * 0.035), (0.13, 0.14, 0.017), LINEN_CREAM if layer != 1 else LINEN_RAW, bevel=0.008)
    for layer in range(2):
        _soft_block(b, frame, (-0.24, 0.0, 0.248 + layer * 0.04), (0.18, 0.15, 0.02), LINEN_CREAM, bevel=0.008)


def laundry_tubs(b: Builder, frame: Matrix, **options) -> None:
    """Two hooped wooden wash tubs on a bench with corrugated washboard and a basket of linen."""
    bench_z = 0.44
    for lx, ly in itertools.product((-0.78, 0.32), (-0.28, 0.28)):
        wood_box(b, frame, (lx - 0.035, ly - 0.035, 0.0), (lx + 0.035, ly + 0.035, bench_z - 0.04), WALNUT_DARK)
    wood_box(b, frame, (-0.82, -0.03, 0.14), (0.36, 0.03, 0.18), WALNUT_DARK)
    bevel_box(b, frame, (-0.88, -0.35, bench_z - 0.04), (0.42, 0.35, bench_z), HONEY_WOOD, bevel=0.01, light=True)

    for tx in (-0.54, 0.08):
        lathe(b, [(0.23, 0.0), (0.29, 0.34), (0.27, 0.34), (0.21, 0.04), (0.001, 0.04)], 16, "wood", PINE_SCRUB, frame, base=(tx, 0.0, bench_z), uv=WOOD_LIGHT_UV)
        for hz, hr in ((0.09, 0.248), (0.27, 0.282)):
            ring(b, (tx, 0.0, bench_z + hz), hr, 0.009, "metal", WROUGHT_IRON, frame, sides=16, tube_sides=3)
        _cyl(b, frame, (tx, 0.0, bench_z + 0.26), 0.255, 0.015, 14, "water", "7CB4CC")

    # Corrugated washboard leaning in right tub
    wb_f = _at(frame, (0.08, 0.0, bench_z + 0.14), -26.0, "X")
    wood_box(b, wb_f, (-0.16, -0.02, 0.0), (-0.13, 0.02, 0.46), WALNUT_MID)
    wood_box(b, wb_f, (0.13, -0.02, 0.0), (0.16, 0.02, 0.46), WALNUT_MID)
    wood_box(b, wb_f, (-0.16, -0.02, 0.4), (0.16, 0.02, 0.46), WALNUT_MID)
    for r in range(7):
        _cyl(b, wb_f, (-0.13, 0.0, 0.08 + r * 0.042), 0.01, 0.26, 6, "metal", PEWTER, axis="X")

    # Wicker laundry basket heaped with linen on the right (+X)
    _wicker_basket(b, frame, 0.66, 0.0, 0.0, r_bot=0.17, r_top=0.24, height=0.34)
    for lx, ly, lz, sc in ((0.61, -0.04, 0.36, (0.12, 0.1, 0.07)), (0.71, 0.05, 0.38, (0.11, 0.09, 0.07)), (0.65, 0.01, 0.43, (0.12, 0.1, 0.06))):
        _sphere(b, frame, (lx, ly, lz), 1.0, "paint", LINEN_CREAM, scale=sc, segments=8)


def ironing_table(b: Builder, frame: Matrix, **options) -> None:
    """Ironing table with draped woollen blanket, two flat irons on a trivet and stacks of folded linen."""
    top_z = 0.82
    for lx, ly in itertools.product((-0.82, 0.82), (-0.3, 0.3)):
        turned_leg(b, frame, lx, ly, top_z - 0.04, 0.038, WALNUT_DARK, "baluster", sides=8)
    wood_box(b, frame, (-0.84, -0.31, 0.18), (0.84, 0.31, 0.21), HONEY_WOOD, light=True)
    bevel_box(b, frame, (-0.95, -0.37, top_z - 0.04), (0.95, 0.37, top_z), PINE_SCRUB, bevel=0.01, light=True)

    # Draped blanket cover
    _soft_block(b, frame, (0.0, 0.0, top_z + 0.015), (0.92, 0.35, 0.016), LINEN_RAW, bevel=0.012)
    for sy in (-0.365, 0.355):
        _box(b, frame, (-0.86, sy, top_z - 0.07), (0.86, sy + 0.015, top_z + 0.015), "paint", LINEN_RAW)

    # Brass trivet + two flat irons
    _box(b, frame, (-0.74, -0.14, top_z + 0.03), (-0.42, 0.14, top_z + 0.048), "metal", BRASS_AGED)
    for ix, iy, yaw in ((-0.64, -0.02, 10.0), (-0.5, 0.04, -15.0)):
        iff = _at(frame, (ix, iy, top_z + 0.048), yaw)
        solid_hull(b, [(-0.045, -0.07, 0.0), (0.045, -0.07, 0.0), (0.0, 0.08, 0.0), (-0.04, -0.06, 0.022), (0.04, -0.06, 0.022), (0.0, 0.07, 0.022)], "metal", CAST_IRON, iff)
        _beam(b, iff, (0.0, -0.045, 0.022), (0.0, -0.04, 0.085), 0.012, 0.012, "metal", WROUGHT_IRON)
        _beam(b, iff, (0.0, 0.035, 0.022), (0.0, 0.03, 0.085), 0.012, 0.012, "metal", WROUGHT_IRON)
        _beam(b, iff, (0.0, -0.045, 0.085), (0.0, 0.035, 0.085), 0.016, 0.016, "wood", WALNUT_DARK, uv=WOOD_LIGHT_UV)

    # Stacks of folded linen on top and basket underneath
    for sx, layers in ((0.18, 4), (0.6, 3)):
        for l_i in range(layers):
            _soft_block(b, frame, (sx, 0.0, top_z + 0.052 + l_i * 0.042), (0.16, 0.19, 0.02), LINEN_CREAM if l_i % 2 == 0 else "D9D0BE", bevel=0.01)
    _wicker_basket(b, frame, 0.0, 0.0, 0.21, r_bot=0.16, r_top=0.22, height=0.24)


# ---------- play and office ----------

def rocking_horse(b: Builder, frame: Matrix, **options) -> None:
    """Painted wooden rocking horse facing -X in profile on curved timber rockers."""
    # Curved rockers along X
    pts = [(-0.56 + 1.12 * i / 8.0, 0.14 * ((i - 4.0) / 4.0) ** 2 + 0.02) for i in range(9)]
    for ry in (-0.15, 0.15):
        for (x0, z0), (x1, z1) in zip(pts, pts[1:]):
            _beam(b, frame, (x0, ry, z0), (x1, ry, z1), 0.032, 0.032, "wood", WALNUT_DARK, uv=WOOD_LIGHT_UV)
    for cx in (-0.35, 0.0, 0.35):
        cz = 0.02 + 0.14 * (cx / 0.56) ** 2
        wood_box(b, frame, (cx - 0.02, -0.16, cz - 0.015), (cx + 0.02, 0.16, cz + 0.015), WALNUT_MID)

    # Four splayed legs and dappled grey painted barrel body
    for lx, rx, ly in ((-0.26, -0.18, -0.09), (-0.26, -0.18, 0.09), (0.28, 0.2, -0.09), (0.28, 0.2, 0.09)):
        _beam(b, frame, (lx, ly * 1.4, 0.08), (rx, ly, 0.5), 0.036, 0.036, "paint", "C9C2B2")
    _cyl(b, frame, (-0.26, 0.0, 0.54), 0.115, 0.52, 14, "paint", "D6CFC0", axis="X")
    _sphere(b, frame, (-0.26, 0.0, 0.54), 0.115, "paint", "D6CFC0", segments=10)
    _sphere(b, frame, (0.26, 0.0, 0.54), 0.115, "paint", "D6CFC0", segments=10)

    # Saddle, arched neck, sculpted head, ears, mane and tail
    _box(b, frame, (-0.09, -0.11, 0.59), (0.09, 0.11, 0.67), "paint", "8E3B36")
    _beam(b, frame, (-0.22, 0.0, 0.57), (-0.34, 0.0, 0.84), 0.11, 0.09, "paint", "D6CFC0")
    solid_hull(b, [(-0.31, -0.055, 0.8), (-0.31, 0.055, 0.8), (-0.34, -0.05, 0.91), (-0.34, 0.05, 0.91), (-0.53, -0.032, 0.72), (-0.53, 0.032, 0.72), (-0.51, -0.03, 0.78), (-0.51, 0.03, 0.78)], "paint", "D6CFC0", frame)
    for ey in (-0.035, 0.035):
        _beam(b, frame, (-0.33, ey, 0.89), (-0.34, ey, 0.95), 0.02, 0.016, "paint", "C9C2B2")
    _beam(b, frame, (-0.21, 0.0, 0.62), (-0.31, 0.0, 0.89), 0.035, 0.025, "paint", "54453B")
    _beam(b, frame, (0.35, 0.0, 0.56), (0.5, 0.0, 0.34), 0.04, 0.035, "paint", "54453B")


def toy_chest(b: Builder, frame: Matrix, **options) -> None:
    """Open painted toy chest containing building blocks, ball, pull-cart and rag doll (height <= 0.7 m)."""
    body_h = 0.38
    bevel_box(b, frame, (-0.42, -0.23, 0.0), (0.42, 0.23, 0.04), WALNUT_DARK, bevel=0.006)
    _box(b, frame, (-0.42, -0.23, 0.04), (0.42, -0.19, body_h), "paint", "5A7A68")
    _box(b, frame, (-0.42, 0.19, 0.04), (0.42, 0.23, body_h), "paint", "5A7A68")
    _box(b, frame, (-0.42, -0.19, 0.04), (-0.38, 0.19, body_h), "paint", "5A7A68")
    _box(b, frame, (0.38, -0.19, 0.04), (0.42, 0.19, body_h), "paint", "5A7A68")
    _box(b, frame, (-0.38, -0.19, 0.04), (0.38, 0.19, 0.26), "wood", HONEY_WOOD, uv=WOOD_LIGHT_UV)

    for bx in (-0.32, 0.32):
        metal_box(b, frame, (bx - 0.02, -0.235, 0.04), (bx + 0.02, -0.19, body_h), WROUGHT_IRON)
    metal_box(b, frame, (-0.04, -0.24, 0.28), (0.04, -0.225, 0.36), BRASS_AGED)

    # Open lid tilted -50 deg around X so it swings up and back (max Z <= 0.70)
    lid_f = _at(frame, (0.0, 0.21, body_h), -50.0, "X")
    bevel_box(b, lid_f, (-0.43, -0.38, 0.0), (0.43, 0.02, 0.035), WALNUT_MID, bevel=0.006)

    # Toys inside: painted wooden blocks, ball, toy cart, rag doll
    for bx, by, bz, col in ((-0.26, -0.06, 0.26, "B55248"), (-0.16, -0.05, 0.26, "C99A3E"), (-0.21, -0.055, 0.34, "4F759E")):
        _box(b, frame, (bx - 0.04, by - 0.04, bz), (bx + 0.04, by + 0.04, bz + 0.08), "paint", col)
    _sphere(b, frame, (0.04, -0.04, 0.35), 0.09, "paint", "B55248", segments=10)
    _box(b, frame, (0.16, -0.12, 0.26), (0.33, 0.04, 0.34), "wood", PINE_SCRUB, uv=WOOD_LIGHT_UV)
    for wx in (0.19, 0.3):
        _cyl(b, frame, (wx, -0.13, 0.27), 0.028, 0.015, 10, "paint", "3A5E8C", axis="Y")

    # Rag doll propped in right-back corner
    _cyl(b, _at(frame, (0.28, 0.09, 0.32), -14.0, "X"), (0.0, 0.0, 0.0), 0.06, 0.14, 8, "paint", "8E546A", top_radius=0.03)
    _sphere(b, frame, (0.28, 0.12, 0.49), 0.052, "paint", LINEN_CREAM, segments=8)
    _sphere(b, frame, (0.28, 0.14, 0.51), 0.054, "paint", "7A4E33", scale=(1.0, 0.9, 0.8), segments=6)


def dollhouse(b: Builder, frame: Matrix, **options) -> None:
    """Open-front two-storey colonial dollhouse on a low wooden play table."""
    tbl_z = 0.42
    for lx, ly in itertools.product((-0.4, 0.4), (-0.2, 0.2)):
        turned_leg(b, frame, lx, ly, tbl_z - 0.03, 0.024, WALNUT_MID, "baluster", sides=8)
    bevel_box(b, frame, (-0.45, -0.25, tbl_z - 0.03), (0.45, 0.25, tbl_z), HONEY_WOOD, bevel=0.008, light=True)

    # Dollhouse body (0.42..1.00) + pitched terracotta roof (1.00..1.25)
    _box(b, frame, (-0.39, 0.17, tbl_z), (0.39, 0.2, 1.0), "plaster", PLASTER_WARM)
    for sx in (-0.39, 0.36):
        _box(b, frame, (sx, -0.2, tbl_z), (sx + 0.03, 0.2, 1.0), "plaster", PLASTER_WARM)
    _box(b, frame, (-0.38, -0.2, 0.7), (0.38, 0.18, 0.72), "wood", HONEY_WOOD, uv=WOOD_LIGHT_UV)
    _box(b, frame, (-0.015, -0.19, tbl_z), (0.015, 0.18, 1.0), "plaster", LINEN_CREAM)

    roof = [(-0.42, 1.0), (0.42, 1.0), (0.0, 1.24)]
    b.prism(roof, -0.22, 0.22, "paint", srgb(TERRACOTTA), frame=frame)
    _box(b, frame, (0.2, 0.04, 1.12), (0.28, 0.14, 1.25), "brick", BRICK_OLD)

    # Miniature room furniture inside the 4 rooms
    _box(b, frame, (-0.3, -0.08, tbl_z), (-0.1, 0.12, tbl_z + 0.06), "paint", "5A738E")
    _box(b, frame, (0.12, -0.06, tbl_z), (0.28, 0.08, tbl_z + 0.08), "wood", WALNUT_DARK, uv=WOOD_LIGHT_UV)
    _box(b, frame, (-0.32, -0.06, 0.72), (-0.12, 0.1, 0.79), "paint", "8E423F")
    _box(b, frame, (0.12, -0.06, 0.72), (0.26, 0.08, 0.8), "wood", WALNUT_MID, uv=WOOD_LIGHT_UV)


def director_desk(b: Builder, frame: Matrix, **options) -> None:
    """Mahogany pedestal desk with leather top, ledger, inkstand, oil lamp and director's armchair behind."""
    # Desk positioned toward -Y (-0.78..0.06), armchair behind at +Y (0.25..0.76)
    df = _at(frame, (0.0, -0.35, 0.0))
    for side in (-1.0, 1.0):
        px = side * 0.66
        bevel_box(b, df, (px - 0.2, -0.39, 0.0), (px + 0.2, 0.39, 0.08), WALNUT_DARK, bevel=0.008)
        bevel_box(b, df, (px - 0.19, -0.37, 0.08), (px + 0.19, 0.37, 0.72), WALNUT_MID, bevel=0.008)
        for d in range(3):
            dz = 0.11 + d * 0.2
            bevel_box(b, df, (px - 0.16, 0.365, dz), (px + 0.16, 0.382, dz + 0.17), HONEY_WOOD, bevel=0.005, light=True)
            _sphere(b, df, (px, 0.39, dz + 0.085), 0.013, "metal", BRASS_AGED, segments=6)
    wood_box(b, df, (-0.48, -0.35, 0.14), (0.48, -0.31, 0.72), WALNUT_DARK)
    bevel_box(b, df, (-0.88, -0.43, 0.72), (0.88, 0.43, 0.78), HONEY_WOOD, bevel=0.012, light=True)
    _box(b, df, (-0.76, -0.33, 0.78), (0.76, 0.33, 0.786), "paint", LEATHER_GREEN)

    # Ledger, inkstand, papers and brass oil lamp on desk top
    _book_open(b, df, 0.05, 0.04, 0.786, 0.38, 0.26, CHAPEL_WINE, yaw=175.0)
    _box(b, df, (0.46, -0.1, 0.786), (0.64, 0.06, 0.8), "metal", BRASS_AGED)
    _cyl(b, df, (0.55, -0.02, 0.8), 0.024, 0.038, 10, "paint", "242D42")
    _beam(b, df, (0.55, -0.02, 0.82), (0.62, 0.06, 1.0), 0.012, 0.006, "paint", LINEN_CREAM)
    _box(b, _at(df, (0.44, 0.18, 0.787), 12.0), (-0.1, -0.13, 0.0), (0.1, 0.13, 0.006), "paint", PARCHMENT)
    _oil_lamp_unit(b, df, -0.55, -0.04, 0.786, shade_col=OPAL_GLASS)

    # Director's leather armchair behind the desk (at +Y = 0.45, facing -Y)
    cf = _at(frame, (0.0, 0.48, 0.0))
    for lx, ly in itertools.product((-0.24, 0.24), (-0.22, 0.22)):
        turned_leg(b, cf, lx, ly, 0.44, 0.028, WALNUT_DARK, "baluster", sides=8)
    _soft_block(b, cf, (0.0, 0.0, 0.47), (0.26, 0.25, 0.055), CHAPEL_WINE, bevel=0.02)
    _soft_block(b, cf, (0.0, 0.22, 0.78), (0.25, 0.055, 0.26), CHAPEL_WINE, bevel=0.02)
    for sx in (-0.25, 0.25):
        wood_box(b, cf, (sx - 0.025, -0.22, 0.48), (sx + 0.025, -0.18, 0.66), WALNUT_DARK)
        bevel_box(b, cf, (sx - 0.035, -0.24, 0.65), (sx + 0.035, 0.22, 0.7), HONEY_WOOD, bevel=0.008, light=True)


def filing_cabinet(b: Builder, frame: Matrix, **options) -> None:
    """Wooden office cabinet with 4 x 5 labelled drawers and brass pulls, one drawer pulled open."""
    half_w, front_y, back_y = 0.53, -0.18, 0.25
    for sx, sy in itertools.product((-1.0, 1.0), repeat=2):
        lathe(b, [(0.024, 0.0), (0.044, 0.03), (0.034, 0.06)], 10, "wood", WALNUT_DARK, frame, base=(sx * (half_w - 0.07), front_y + 0.06 if sy < 0 else back_y - 0.06, 0.0), uv=WOOD_DARK_UV)
    bevel_box(b, frame, (-half_w, front_y, 0.06), (half_w, back_y, 0.14), WALNUT_DARK, bevel=0.008)
    bevel_box(b, frame, (-half_w + 0.01, front_y + 0.02, 0.14), (half_w - 0.01, back_y, 1.43), WALNUT_MID, bevel=0.006)
    run_profile(b, frame, -half_w, half_w, cornice_profile(front_y + 0.01, 1.38, 0.02, 0.06), WALNUT_DARK)
    bevel_box(b, frame, (-0.55, front_y - 0.01, 1.43), (0.55, back_y, 1.5), HONEY_WOOD, bevel=0.01, light=True)

    cols, rows = 4, 5
    dw, dh = 0.96 / cols, 1.2 / rows
    for c, r in itertools.product(range(cols), range(rows)):
        dx = -0.48 + (c + 0.5) * dw
        dz = 0.18 + (r + 0.5) * dh
        pull = -0.05 if (c, r) == (1, 2) else 0.0
        _box(b, frame, (dx - dw / 2.0 + 0.01, front_y + pull, dz - dh / 2.0 + 0.01), (dx + dw / 2.0 - 0.01, front_y + 0.025 + pull, dz + dh / 2.0 - 0.01), "wood", HONEY_WOOD, uv=WOOD_LIGHT_UV)
        _box(b, frame, (dx - 0.045, front_y - 0.006 + pull, dz + 0.02), (dx + 0.045, front_y + pull, dz + 0.06), "paint", PARCHMENT)
        _box(b, frame, (dx - 0.03, front_y - 0.012 + pull, dz - 0.04), (dx + 0.03, front_y + pull, dz - 0.025), "metal", BRASS_AGED)
        if pull < 0.0:
            _box(b, frame, (dx - dw / 2.0 + 0.02, front_y + 0.025 + pull, dz - dh / 2.0 + 0.02), (dx + dw / 2.0 - 0.02, front_y + 0.02, dz + dh / 2.0 - 0.04), "wood", WALNUT_DARK, uv=WOOD_DARK_UV)
            _box(b, frame, (dx - 0.065, front_y + 0.028 + pull, dz - 0.05), (dx + 0.065, front_y + 0.018, dz + 0.07), "paint", PARCHMENT)


# ---------- lighting and windows ----------

def oil_lamp_table(b: Builder, frame: Matrix, **options) -> None:
    """Brass table oil lamp with glass chimney and opal shade."""
    _oil_lamp_unit(b, frame, 0.0, 0.0, 0.0, shade_col=OPAL_GLASS)


def wall_sconce(b: Builder, frame: Matrix, **options) -> None:
    """Double-arm brass wall sconce with frosted glass tulip shades, mounted at 2.1 m."""
    wall_y = 0.15
    mount_z = 2.1
    lathe(b, [(0.001, 0.0), (0.075, 0.0), (0.065, 0.02), (0.001, 0.025)], 14, "metal", BRASS_AGED, _at(frame, (0.0, wall_y, mount_z), 90.0, "X"))
    _cyl(b, frame, (0.0, wall_y - 0.08, mount_z), 0.02, 0.08, 10, "metal", BRASS_AGED, axis="Y")

    for sx in (-1.0, 1.0):
        ax = sx * 0.15
        _beam(b, frame, (0.0, wall_y - 0.07, mount_z), (ax, wall_y - 0.16, mount_z + 0.04), 0.016, 0.016, "metal", BRASS_AGED)
        _cyl(b, frame, (ax, wall_y - 0.16, mount_z + 0.04), 0.036, 0.018, 14, "metal", BRASS_BRIGHT)
        lathe(b, [(0.024, 0.0), (0.055, 0.05), (0.065, 0.13), (0.058, 0.13), (0.048, 0.05), (0.02, 0.005)], 16, "paint", OPAL_GLASS, frame, base=(ax, wall_y - 0.16, mount_z + 0.058))
        _cyl(b, frame, (ax, wall_y - 0.16, mount_z + 0.07), 0.011, 0.035, 6, "glow_warm", "FFFFFF", top_radius=0.003)


def hanging_oil_lamp(b: Builder, frame: Matrix, **options) -> None:
    """Brass hanging oil lamp with opal shade on twin chains and central counterweight (hang)."""
    lathe(b, [(0.075, 0.0), (0.06, -0.025), (0.02, -0.05), (0.001, -0.05)], 16, "metal", BRASS_AGED, frame)
    _cyl(b, frame, (-0.15, 0.0, -0.06), 0.008, 0.3, 8, "metal", BRASS_AGED, axis="X")

    # Central brass counterweight
    lathe(b, [(0.001, -0.35), (0.045, -0.4), (0.05, -0.48), (0.025, -0.55), (0.001, -0.58)], 16, "metal", BRASS_AGED, frame)
    _cyl(b, frame, (0.0, 0.0, -0.35), 0.006, 0.3, 6, "metal", BRASS_AGED)

    for sx in (-0.14, 0.14):
        _beam(b, frame, (sx, 0.0, -0.06), (sx, 0.0, -0.82), 0.008, 0.008, "metal", BRASS_AGED)
        _beam(b, frame, (sx, 0.0, -0.82), (sx * 1.4, 0.0, -1.04), 0.01, 0.01, "metal", BRASS_AGED)

    # Ring harp, oil reservoir, chimney & wide opal shade
    ring(b, (0.0, 0.0, -1.04), 0.195, 0.01, "metal", BRASS_BRIGHT, frame, sides=16, tube_sides=4)
    lathe(b, [(0.001, -1.27), (0.018, -1.2), (0.09, -1.14), (0.11, -1.07), (0.055, -1.01), (0.001, -1.01)], 16, "metal", BRASS_AGED, frame)
    lathe(b, [(0.26, -0.96), (0.21, -0.88), (0.09, -0.82), (0.075, -0.82), (0.195, -0.88), (0.245, -0.96)], 16, "paint", OPAL_GLASS, frame, closed=True)
    lathe(b, [(0.03, -1.01), (0.036, -0.94), (0.022, -0.78), (0.018, -0.78), (0.03, -0.94), (0.025, -1.01)], 16, "vitrine", "FFFFFF", frame)
    _cyl(b, frame, (0.0, 0.0, -0.99), 0.014, 0.045, 6, "glow_warm", "FFFFFF", top_radius=0.003)


def curtain_pair(b: Builder, frame: Matrix, width: float = 2.0, height: float = 3.4, variant: str = None, **options) -> None:
    """Curtain rod with brass rings and two tied-back curtains framing a window (wall prop, beside_window)."""
    width = width or 2.0
    height = height or 3.4
    cloth_hex, trim_hex = CURTAIN_COLOURS.get(variant or "cream", CURTAIN_COLOURS["cream"])
    wall_y = 0.11
    rod_z = height - 0.08
    half_w = width / 2.0

    # Rod, finials, wall brackets and curtain rings
    _cyl(b, frame, (-half_w + 0.06, 0.0, rod_z), 0.016, width - 0.12, 12, "wood", WALNUT_DARK, axis="X", uv=WOOD_LIGHT_UV)
    for sx in (-1.0, 1.0):
        _sphere(b, frame, (sx * (half_w - 0.04), 0.0, rod_z), 0.034, "metal", BRASS_AGED, segments=8)
        _box(b, frame, (sx * (half_w - 0.14) - 0.015, 0.0, rod_z - 0.02), (sx * (half_w - 0.14) + 0.015, wall_y, rod_z + 0.02), "metal", BRASS_AGED)

    tie_z = max(0.7, height * 0.38)
    for side in (-1.0, 1.0):
        # 5 vertical pleats curving cleanly toward outer tieback waist
        for p in range(5):
            frac = p / 4.0
            top_x = side * (half_w * 0.44 + frac * half_w * 0.48)
            waist_x = side * (half_w * 0.72 + frac * half_w * 0.21)
            bot_x = side * (half_w * 0.56 + frac * half_w * 0.37)
            dy = 0.028 if p % 2 else -0.028
            upper = [
                (top_x - 0.055, dy, rod_z - 0.01), (top_x + 0.055, dy, rod_z - 0.01),
                (top_x - 0.055, 0.0, rod_z - 0.01), (top_x + 0.055, 0.0, rod_z - 0.01),
                (waist_x - 0.045, dy * 0.6, tie_z), (waist_x + 0.045, dy * 0.6, tie_z),
                (waist_x - 0.045, 0.0, tie_z), (waist_x + 0.045, 0.0, tie_z),
            ]
            lower = [
                (waist_x - 0.045, dy * 0.6, tie_z), (waist_x + 0.045, dy * 0.6, tie_z),
                (waist_x - 0.045, 0.0, tie_z), (waist_x + 0.045, 0.0, tie_z),
                (bot_x - 0.06, dy, 0.04), (bot_x + 0.06, dy, 0.04),
                (bot_x - 0.06, 0.0, 0.04), (bot_x + 0.06, 0.0, 0.04),
            ]
            solid_hull(b, upper, "paint", cloth_hex, frame)
            solid_hull(b, lower, "paint", cloth_hex, frame)
            ring(b, (top_x, 0.0, rod_z), 0.024, 0.005, "metal", BRASS_BRIGHT, frame, sides=10, tube_sides=3, axis="X")

        # Tieback band
        ring(b, (side * (half_w * 0.82), 0.0, tie_z), 0.13, 0.012, "paint", trim_hex, _at(frame, (0.0, 0.0, 0.0)) @ Matrix.Diagonal((1.0, 0.4, 1.0, 1.0)), sides=12, tube_sides=4)


def retable_altar(b: Builder, frame: Matrix, **options) -> None:
    """Narrow chapel altar, 2.0 m wide, against the wall: stone table with a linen cloth, tabernacle, cross and two
    candlesticks, backed by an arched retable of painted panels with a gilt rim and a rose window."""
    back = 0.45
    outline = [(-1.0, 0.0), (1.0, 0.0), (1.0, 2.4), (0.5, 2.9), (0.0, 3.05), (-0.5, 2.9), (-1.0, 2.4)]

    _box(b, frame, (-0.95, -0.4, 0.0), (0.95, 0.25, 0.08), "stone", STONE_WARM)
    _box(b, frame, (-0.85, -0.34, 0.08), (0.85, 0.2, 0.93), "stone", STONE_LIGHT)
    _box(b, frame, (-0.9, -0.38, 0.93), (0.9, 0.24, 1.0), "stone", MARBLE_CREAM)
    _box(b, frame, (-0.78, -0.42, 0.62), (0.78, -0.38, 1.0), "paint", LINEN_CREAM)
    _box(b, frame, (-0.78, -0.425, 0.62), (0.78, -0.415, 0.68), "metal", BRASS_AGED)

    _box(b, frame, (-0.3, 0.0, 1.0), (0.3, 0.22, 1.4), "wood", WALNUT_DARK, uv=WOOD_DARK_UV)
    b.prism([(-0.3, 1.4), (0.3, 1.4), (0.0, 1.62)], 0.0, 0.22, "metal", srgb(BRASS_BRIGHT), frame=frame)
    _box(b, frame, (-0.025, 0.05, 1.62), (0.025, 0.09, 2.05), "metal", BRASS_BRIGHT)
    _box(b, frame, (-0.14, 0.05, 1.84), (0.14, 0.09, 1.9), "metal", BRASS_BRIGHT)

    for candle_x in (-0.62, 0.62):
        _candlestick(b, frame, candle_x, -0.08, 1.0, stand_h=0.3, candle_h=0.26)

    _box(b, frame, (-1.02, back - 0.45, 0.0), (1.02, back, 1.0), "stone", STONE_LIGHT)
    b.prism(outline, back - 0.17, back, "paint", srgb("E9D9F2"), frame=frame)
    b.prism([(-0.8, 1.2), (0.8, 1.2), (0.8, 2.3), (0.4, 2.65), (0.0, 2.78), (-0.4, 2.65), (-0.8, 2.3)], back - 0.2, back - 0.17, "paint", srgb(CHAPEL_WINE), frame=frame)
    _cyl(b, frame, (0.0, back - 0.205, 2.0), 0.28, 0.02, 12, "paint", BRASS_AGED, axis="Y")

    for start, end in zip(outline, outline[1:] + outline[:1]):
        if start[1] > 0.0 or end[1] > 0.0:
            _beam(b, frame, (start[0], back - 0.18, start[1]), (end[0], back - 0.18, end[1]), 0.06, 0.03, "metal", BRASS_AGED)


PROPS = {
    # Dormitory
    "retable_altar": {"build": retable_altar, "size": (2.0, 0.9, 3.1), "solid": True, "clearance": 0.9},
    "iron_bed": {"build": iron_bed, "size": (0.95, 2.0, 1.15), "solid": True, "variants": list(BLANKET_COLOURS)},
    "bed_trunk": {"build": bed_trunk, "size": (0.8, 0.45, 0.45), "solid": True},
    "night_table": {"build": night_table, "size": (0.42, 0.38, 0.95), "solid": True},
    "linen_press": {"build": linen_press, "size": (1.6, 0.6, 2.25), "solid": True, "clearance": 0.8},
    "wall_crucifix": {"build": wall_crucifix, "size": (0.4, 0.08, 2.3), "solid": False},
    "clothes_pegs": {"build": clothes_pegs, "size": (1.6, 0.25, 1.9), "solid": False},
    "supervisor_alcove": {"build": supervisor_alcove, "size": (2.6, 2.6, 2.3), "solid": False},
    # Refectory
    "long_table_set": {"build": long_table_set, "size": (3.6, 0.9, 1.0), "solid": True},
    "long_bench": {"build": long_bench, "size": (3.6, 0.32, 0.46), "solid": True},
    "crockery_dresser": {"build": crockery_dresser, "size": (1.9, 0.5, 2.15), "solid": True, "clearance": 0.8},
    "serving_counter": {"build": serving_counter, "size": (2.4, 0.75, 1.2), "solid": True, "clearance": 0.8},
    # Kitchen
    "masonry_range": {"build": masonry_range, "size": (2.8, 1.05, 2.7), "solid": True, "clearance": 1.0},
    "kitchen_worktable": {"build": kitchen_worktable, "size": (2.4, 1.0, 1.05), "solid": True},
    "stone_sink": {"build": stone_sink, "size": (1.7, 0.7, 1.7), "solid": True, "clearance": 0.8},
    "pot_shelf": {"build": pot_shelf, "size": (1.8, 0.42, 2.05), "solid": True, "clearance": 0.8},
    "hanging_pan_rack": {"build": hanging_pan_rack, "size": (2.0, 0.6, 1.1), "solid": False, "hang": True},
    "water_filter": {"build": water_filter, "size": (0.5, 0.5, 1.35), "solid": True},
    "firewood_stack": {"build": firewood_stack, "size": (1.3, 0.5, 0.95), "solid": True},
    "pantry_shelf": {"build": pantry_shelf, "size": (1.9, 0.55, 2.2), "solid": True, "clearance": 0.8},
    # Classroom and study
    "double_desk": {"build": double_desk, "size": (1.15, 0.9, 0.82), "solid": True},
    "teacher_platform": {"build": teacher_platform, "size": (2.6, 1.8, 1.25), "solid": True, "clearance": 0.8},
    "wall_map": {"build": wall_map, "size": (1.5, 0.06, 2.3), "solid": False, "variants": list(MAP_STYLES)},
    "abacus_stand": {"build": abacus_stand, "size": (0.95, 0.45, 1.45), "solid": True},
    "specimen_cupboard": {"build": specimen_cupboard, "size": (1.3, 0.5, 2.05), "solid": True, "clearance": 0.8},
    "study_table": {"build": study_table, "size": (3.0, 1.0, 1.3), "solid": True, "light": ((-0.85, 0.0, 1.15), LAMP_LIGHT, 1.2, 6.0)},
    "bentwood_chair": {"build": bentwood_chair, "size": (0.45, 0.48, 0.9), "solid": True},
    # Chapel
    "confessional": {"build": confessional, "size": (2.0, 1.0, 2.5), "solid": True, "clearance": 1.0},
    "harmonium": {"build": harmonium, "size": (1.25, 0.95, 1.25), "solid": True, "clearance": 0.6},
    "holy_water_font": {"build": holy_water_font, "size": (0.45, 0.45, 1.1), "solid": True},
    "saint_niche": {"build": saint_niche, "size": (0.8, 0.35, 2.9), "solid": False},
    "prie_dieu": {"build": prie_dieu, "size": (0.6, 0.65, 0.95), "solid": True},
    "sanctuary_lamp": {"build": sanctuary_lamp, "size": (0.35, 0.35, 1.4), "solid": False, "hang": True, "light": ((0.0, 0.0, -1.05), LAMP_LIGHT, 0.7, 4.0)},
    # Washroom, infirmary, linen
    "basin_row": {"build": basin_row, "size": (2.6, 0.6, 1.75), "solid": True, "clearance": 0.8},
    "tin_bathtub": {"build": tin_bathtub, "size": (1.6, 0.8, 0.75), "solid": True, "clearance": 0.6},
    "towel_rack": {"build": towel_rack, "size": (1.2, 0.35, 1.5), "solid": True},
    "copper_boiler": {"build": copper_boiler, "size": (0.8, 0.8, 2.0), "solid": True, "clearance": 0.8},
    "folding_screen": {"build": folding_screen, "size": (1.8, 0.4, 1.8), "solid": True},
    "medicine_cabinet": {"build": medicine_cabinet, "size": (1.0, 0.42, 1.95), "solid": True, "clearance": 0.8},
    "nurse_table": {"build": nurse_table, "size": (1.2, 0.6, 1.0), "solid": True},
    "laundry_tubs": {"build": laundry_tubs, "size": (1.8, 0.8, 1.0), "solid": True, "clearance": 0.8},
    "ironing_table": {"build": ironing_table, "size": (1.9, 0.75, 1.05), "solid": True},
    # Play and office
    "rocking_horse": {"build": rocking_horse, "size": (1.15, 0.4, 0.95), "solid": True},
    "toy_chest": {"build": toy_chest, "size": (0.9, 0.5, 0.7), "solid": True, "clearance": 0.5},
    "dollhouse": {"build": dollhouse, "size": (0.9, 0.5, 1.25), "solid": True},
    "director_desk": {"build": director_desk, "size": (1.8, 1.6, 1.35), "solid": True, "clearance": 0.8, "light": ((-0.55, -0.39, 1.15), LAMP_LIGHT, 1.1, 5.5)},
    "filing_cabinet": {"build": filing_cabinet, "size": (1.1, 0.5, 1.5), "solid": True, "clearance": 0.8},
    # Lighting and windows
    "oil_lamp_table": {"build": oil_lamp_table, "size": (0.22, 0.22, 0.5), "solid": False, "light": ((0.0, 0.0, 0.34), LAMP_LIGHT, 1.0, 5.0)},
    "wall_sconce": {"build": wall_sconce, "size": (0.5, 0.3, 2.35), "solid": False, "light": ((0.0, -0.02, 2.18), LAMP_LIGHT, 1.2, 6.0)},
    "hanging_oil_lamp": {"build": hanging_oil_lamp, "size": (0.6, 0.6, 1.3), "solid": False, "hang": True, "light": ((0.0, 0.0, -1.0), LAMP_LIGHT, 1.5, 7.5)},
    "curtain_pair": {"build": curtain_pair, "size": (2.0, 0.22, 3.4), "solid": False, "beside_window": True, "variants": list(CURTAIN_COLOURS)},
}
