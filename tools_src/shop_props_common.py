"""Shared shop prop helpers plus the common furniture kit (PROPS) used by every shop interior.

Runs inside Blender, imported by build_market_shops.py and build_prop_sheet.py.

Prop contract (every shop_props_<group>.py follows it):
  def name(b: Builder, frame: Matrix, **options) -> None   # Builder primitives only, always frame=frame
  PROPS = {"name": {"build": name, "size": (x, y, z), "solid": bool, "light": optional ((x, y, z), "HEX", energy, range),
                    "variants": optional [str, ...] (only for the prop sheet),
                    "beside_window": optional True (may stand by a window, like a stair climbing past it)}}
Local axes: X width centred on 0; Y depth centred on 0, the customer side faces -Y, the back at
Y = +size[1] / 2 (wall props touch the wall there); Z up from the floor at 0. Wall props are built at
their mounting height. options: variant (str), tint (hex), seed (int, random.Random(seed) for fill).
"""

import itertools
import math
import random
import sys
from pathlib import Path

import bmesh
from mathutils import Matrix

sys.path.insert(0, str(Path(__file__).resolve().parent))

from build_town_houses import STONE, TRIM_SMOOTH_BAND, WHITE, WOOD_DARK_BAND, WOOD_LIGHT_BAND, Builder, srgb  # noqa: E402,F401

# Vivid, clean anime-fantasy goods colours (style bible: bright, never dead grey).
GOODS_PALETTE = ("C9483B", "E0884A", "E8C14F", "7FC46A", "3F8A50", "4F8FC9", "6C5BB8", "C46AA8", "F2E6CF", "8B5A3C")
GLASS_PALETTE = ("D94F5C", "4FB0D9", "7FD96A", "B57FE0", "F2B13C", "5FD9C0")


def lathe(b: Builder, profile: list, sides: int, material: str, tint: str, frame: Matrix, base: tuple = (0.0, 0.0, 0.0), closed: bool = False, uv: tuple = None):
    """Solid of revolution around local Z: profile is [(radius, z), ...] bottom to top. Ends with radius > 0
    get flat caps; closed=True joins the last point back to the first (tori, rings)."""
    lathe_bmesh = bmesh.new()
    angles = [2.0 * math.pi * index / sides for index in range(sides)]
    rings = [[lathe_bmesh.verts.new((radius * math.cos(angle), radius * math.sin(angle), z)) for angle in angles] for radius, z in profile]
    ring_pairs = list(zip(rings, rings[1:] + (rings[:1] if closed else [])))

    for (lower, upper), index in itertools.product(ring_pairs, range(sides)):
        lathe_bmesh.faces.new((lower[index], lower[(index + 1) % sides], upper[(index + 1) % sides], upper[index]))

    if not closed and profile[0][0] > 1e-4:
        lathe_bmesh.faces.new(list(reversed(rings[0])))

    if not closed and profile[-1][0] > 1e-4:
        lathe_bmesh.faces.new(rings[-1])

    bmesh.ops.remove_doubles(lathe_bmesh, verts=lathe_bmesh.verts, dist=1e-5)

    return b._link(lathe_bmesh, material, srgb(tint), uv, frame @ Matrix.Translation(base))


def ring(b: Builder, center: tuple, radius: float, tube: float, material: str, tint: str, frame: Matrix, sides: int = 12, tube_sides: int = 6, axis: str = "Z"):
    """Torus (hoop, barrel band, chandelier wheel) of the given radius and tube radius around local axis."""
    circle = [(radius + tube * math.cos(2.0 * math.pi * index / tube_sides), tube * math.sin(2.0 * math.pi * index / tube_sides)) for index in range(tube_sides)]
    turn = {"Z": Matrix.Identity(4), "X": Matrix.Rotation(math.pi / 2.0, 4, "Y"), "Y": Matrix.Rotation(math.pi / 2.0, 4, "X")}[axis]

    return lathe(b, circle, sides, material, tint, frame @ Matrix.Translation(center) @ turn, closed=True)


def _book(b: Builder, frame: Matrix, x: float, y: float, z: float, width: float, depth: float, height: float, color: str) -> None:
    b.box((x, y - depth / 2.0, z), (x + width, y + depth / 2.0, z + height), "paint", srgb(color), frame=frame)


def _jar(b: Builder, frame: Matrix, x: float, y: float, z: float, width: float, depth: float, height: float, color: str) -> None:
    radius = min(width, depth) / 2.0
    b.cylinder((x + width / 2.0, y, z), radius, height * 0.82, 6, "paint", srgb(color), frame=frame)
    b.cylinder((x + width / 2.0, y, z + height * 0.82), radius * 0.8, height * 0.18, 6, "wood", srgb("8B5A3C"), frame=frame, uv=("band", *WOOD_LIGHT_BAND, 1.0))


def _bottle(b: Builder, frame: Matrix, x: float, y: float, z: float, width: float, depth: float, height: float, color: str) -> None:
    radius = min(width, depth) / 2.0
    b.cylinder((x + width / 2.0, y, z), radius, height * 0.6, 6, "paint", srgb(color), frame=frame)
    b.cylinder((x + width / 2.0, y, z + height * 0.6), radius * 0.35, height * 0.4, 6, "paint", srgb(color), frame=frame)


def _box(b: Builder, frame: Matrix, x: float, y: float, z: float, width: float, depth: float, height: float, color: str) -> None:
    b.box((x, y - depth / 2.0, z), (x + width, y + depth / 2.0, z + height * 0.8), "paint", srgb(color), frame=frame)


def _ball(b: Builder, frame: Matrix, x: float, y: float, z: float, width: float, depth: float, height: float, color: str) -> None:
    radius = min(width, depth, height) / 2.0
    b.sphere((x + width / 2.0, y, z + radius), radius, "paint", srgb(color), scale=(1.0, 1.0, height / (2.0 * radius)), frame=frame, segments=6)


def _roll(b: Builder, frame: Matrix, x: float, y: float, z: float, width: float, depth: float, height: float, color: str) -> None:
    radius = min(height, width) / 2.0
    b.cylinder((x, y - depth / 2.0, z + radius), radius, depth, 6, "paint", srgb(color), frame=frame, axis="Y")


ITEM_SHAPES = {"book": _book, "jar": _jar, "bottle": _bottle, "box": _box, "ball": _ball, "roll": _roll}
ITEM_WIDTH = {"book": (0.04, 0.08), "jar": (0.1, 0.16), "bottle": (0.07, 0.11), "box": (0.14, 0.3), "ball": (0.1, 0.2), "roll": (0.12, 0.2)}


def filled_row(b: Builder, frame: Matrix, x_from: float, x_to: float, y: float, z: float, depth: float, max_height: float, generator: random.Random, shapes: tuple = ("book",), palette: tuple = GOODS_PALETTE, gap: float = 0.01, fill: float = 0.9) -> int:
    """One shelf board of goods from x_from to x_to standing at height z (front-back centre y): items of the
    given shapes, colours and heights drawn from the generator; about `fill` of the length is used.
    Returns the number of items."""
    cursor = x_from
    count = 0

    while cursor < x_to:
        shape = generator.choice(shapes)
        low, high = ITEM_WIDTH[shape]
        width = generator.uniform(low, high)

        if cursor + width > x_to:
            break

        if generator.random() < fill:
            height = max_height * generator.uniform(0.6, 1.0)
            ITEM_SHAPES[shape](b, frame, cursor, y, z, width, depth * generator.uniform(0.7, 1.0), height, generator.choice(palette))
            count += 1

        cursor += width + gap

    return count


def filled_shelves(b: Builder, frame: Matrix, x_from: float, x_to: float, y: float, board_heights: list, depth: float, clearance: float, seed: int, shapes: tuple = ("book",), palette: tuple = GOODS_PALETTE) -> int:
    """Fills every board of a shelf unit (board_heights = top of each board) with filled_row."""
    generator = random.Random(seed)

    return sum(filled_row(b, frame, x_from, x_to, y, board_z, depth, clearance, generator, shapes, palette) for board_z in board_heights)


PROPS = {}

# ---------- common furniture kit ----------
# Ceiling props follow the lead's contract: z = 0 at the ceiling mount and growing DOWN, "hang": True.

SMOOTH_UV = ("band", *TRIM_SMOOTH_BAND, 1.0)
WOOD_DARK_UV = ("band", *WOOD_DARK_BAND, 1.5)
WOOD_LIGHT_UV = ("band", *WOOD_LIGHT_BAND, 1.0)
WOOD_BODY, WOOD_TOP, WOOD_DEEP, WOOD_HONEY = "BE8A58", "E0B678", "98623C", "D9A468"
IRON, BRASS, STEEL, GOLD = "5A4A5E", "E8B84F", "B4C4DC", "FFD24A"
BREAD_PALETTE = ("D9A05B", "C8843F", "E8B97A", "F0C98C")
STEEL_PALETTE = ("A9BAD0", "B9C9E0", "9BB0CE")
PAPER_PALETTE = ("F2E6CF", "E8D7B0", "F7EFD9")
CLOTH_PALETTE = ("C9483B", "4F8FC9", "7FC46A", "E8C14F", "C46AA8", "6C5BB8")
SHOE_PALETTE = ("8B5A3C", "B87C4A", "5A3A26", "C9483B", "4F6FA8")
CRYSTAL_PALETTE = ("B57FE0", "5FD9C0", "4FB0D9", "F2B13C", "F59AD8")
TOOL_PALETTE = ("8B5A3C", "C08A55", "5A3A26")
HERB_PALETTE = ("7FC46A", "3F8A50", "A9D26B")


def wood_box(b: Builder, frame: Matrix, low: tuple, high: tuple, tint: str = WOOD_BODY, light: bool = False):
    return b.box(low, high, "wood", srgb(tint), frame=frame, uv=WOOD_LIGHT_UV if light else WOOD_DARK_UV)


def paint_box(b: Builder, frame: Matrix, low: tuple, high: tuple, tint: str):
    return b.box(low, high, "paint", srgb(tint), frame=frame)


def metal_box(b: Builder, frame: Matrix, low: tuple, high: tuple, tint: str = BRASS):
    return b.box(low, high, "metal", srgb(tint), frame=frame)


def wood_beam(b: Builder, frame: Matrix, start: tuple, end: tuple, width: float, depth: float, tint: str = WOOD_BODY, light: bool = False):
    return b.beam(start, end, width, depth, "wood", srgb(tint), frame=frame, uv=WOOD_LIGHT_UV if light else WOOD_DARK_UV)


def wood_cylinder(b: Builder, frame: Matrix, base: tuple, radius: float, height: float, sides: int = 8, tint: str = WOOD_BODY, top_radius: float = None, axis: str = "Z"):
    return b.cylinder(base, radius, height, sides, "wood", srgb(tint), top_radius=top_radius, frame=frame, uv=WOOD_LIGHT_UV, axis=axis)


# ---------- craft kit: chamfered boxes, turned legs, mouldings, hardware ----------

TURNED_PROFILES = {  # (radius factor, height fraction) bottom to top, radius factor 1.0 = the leg's nominal radius
    "baluster": [(0.7, 0.0), (0.95, 0.03), (0.75, 0.07), (0.6, 0.1), (0.6, 0.34), (0.95, 0.44), (0.72, 0.54), (0.6, 0.6), (0.6, 0.86), (1.0, 0.91), (1.0, 1.0)],
    "column": [(1.1, 0.0), (1.1, 0.05), (0.8, 0.09), (0.7, 0.14), (0.62, 0.5), (0.7, 0.86), (0.85, 0.92), (1.1, 0.96), (1.1, 1.0)],
    "ball": [(0.55, 0.0), (0.7, 0.05), (0.5, 0.12), (0.5, 0.58), (0.78, 0.66), (0.9, 0.78), (0.78, 0.9), (0.5, 0.96), (0.5, 1.0)],
    "taper": [(0.5, 0.0), (0.62, 0.06), (0.8, 0.5), (1.0, 0.94), (1.0, 1.0)],
}


def solid_hull(b: Builder, points: list, material: str, tint: str, frame: Matrix, uv: tuple = None):
    """Convex hull that tolerates points on its faces (Builder.hull hands those to bmesh.ops.delete twice)."""
    hull_bmesh = bmesh.new()
    vertices = [hull_bmesh.verts.new(point) for point in points]
    result = bmesh.ops.convex_hull(hull_bmesh, input=vertices)
    unused = list(dict.fromkeys(element for element in result["geom_interior"] + result["geom_unused"] if isinstance(element, bmesh.types.BMVert)))
    bmesh.ops.delete(hull_bmesh, geom=unused, context="VERTS")

    return b._link(hull_bmesh, material, srgb(tint), uv, frame)


def bevel_box(b: Builder, frame: Matrix, low: tuple, high: tuple, tint: str = None, bevel: float = 0.012, material: str = "wood", light: bool = False):
    """Box with every edge chamfered (24 hull points): catches the light along its edges."""
    chamfer = min(bevel, min(high_value - low_value for low_value, high_value in zip(low, high)) / 2.4)
    points = []

    for corner in itertools.product(*zip(low, high)):
        step = [chamfer if value == low_value else -chamfer for value, low_value in zip(corner, low)]
        points += [tuple(value + (0.0 if axis == kept else step[axis]) for axis, value in enumerate(corner)) for kept in range(3)]

    return solid_hull(b, points, material, tint or WOOD_BODY, frame, (WOOD_LIGHT_UV if light else WOOD_DARK_UV) if material == "wood" else None)


def turned_leg(b: Builder, frame: Matrix, x: float, y: float, height: float, radius: float, tint: str = None, style: str = "baluster", z: float = 0.0, sides: int = 8):
    """Lathe-turned leg or post standing on z at (x, y)."""
    profile = [(radius * factor, z + height * fraction) for factor, fraction in TURNED_PROFILES[style]]

    return lathe(b, profile, sides, "wood", tint or WOOD_DEEP, frame, base=(x, y, 0.0), uv=WOOD_LIGHT_UV)


def run_profile(b: Builder, frame: Matrix, x_from: float, x_to: float, profile: list, tint: str = None, material: str = "wood"):
    """Moulding: a (y, z) polygon extruded along X."""
    return b.side_prism(profile, x_from, x_to, material, srgb(tint or WOOD_TOP), frame=frame, uv=WOOD_LIGHT_UV if material == "wood" else None)


def cornice_profile(y_wall: float, z: float, reach: float, height: float, toward: float = -1.0) -> list:
    """Stepped cove moulding hanging from z up to z + height, jutting `reach` from y_wall toward `toward` (+-1)."""
    steps = [(0.0, 0.0), (0.55, 0.0), (0.55, 0.22), (0.8, 0.3), (0.8, 0.55), (1.0, 0.6), (1.0, 1.0), (0.0, 1.0)]

    return [(y_wall + toward * reach * out, z + height * rise) for out, rise in steps]


def base_profile(y_wall: float, z: float, reach: float, height: float, toward: float = -1.0) -> list:
    """Skirting: a step, a bead and a cove up to the wall."""
    steps = [(0.0, 0.0), (1.0, 0.0), (1.0, 0.4), (0.7, 0.45), (0.7, 0.62), (0.4, 0.75), (0.0, 1.0)]

    return [(y_wall + toward * reach * out, z + height * rise) for out, rise in steps]


def knob(b: Builder, frame: Matrix, x: float, y: float, z: float, radius: float = 0.016, tint: str = None) -> None:
    """Round drawer pull standing proud of a face on -Y."""
    b.sphere((x, y - radius * 0.7, z), radius, "metal", srgb(tint or BRASS), frame=frame, segments=6)
    b.cylinder((x, y, z), radius * 0.35, radius * 0.5, 5, "metal", srgb(tint or BRASS), frame=frame, axis="Y")


def rivets(b: Builder, frame: Matrix, centres: list, y: float, radius: float = 0.012, tint: str = None) -> None:
    """Row of iron rivet heads on a -Y face at y."""
    for x, z in centres:
        b.cylinder((x, y, z), radius, 0.01, 5, "metal", srgb(tint or STEEL), frame=frame, axis="Y")


def strap_hinge(b: Builder, frame: Matrix, x: float, y: float, z: float, length: float, tint: str = None) -> None:
    """Iron strap hinge lying on a -Y face: a tapering strap with a round eye at the pivot end."""
    colour = tint or IRON
    b.prism([(x, z - 0.014), (x + length, z - 0.006), (x + length + 0.02, z), (x + length, z + 0.006), (x, z + 0.014)], y - 0.008, y, "metal", srgb(colour), frame=frame)
    b.cylinder((x, y - 0.012, z), 0.022, 0.016, 6, "metal", srgb(colour), frame=frame, axis="Y")


def raised_panel(b: Builder, frame: Matrix, x_from: float, x_to: float, z_from: float, z_to: float, y: float, tint: str = None, border: float = 0.05, depth: float = 0.014) -> None:
    """Raised panel on a -Y face at y: a bevelled frame around a recessed field."""
    frame_tint, field_tint = tint or WOOD_TOP, WOOD_HONEY
    bevel_box(b, frame, (x_from, y - depth, z_from), (x_to, y, z_to), frame_tint, bevel=0.006, light=True)
    wood_box(b, frame, (x_from + border, y - depth * 1.5, z_from + border), (x_to - border, y - depth * 0.5, z_to - border), field_tint, light=True)


def leaf(b: Builder, frame: Matrix, base: tuple, length: float, width: float, degrees: float, lift: float, tint: str) -> None:
    """Flat pointed leaf (convex hull, 6 triangles) leaning outward at `degrees` around Z and rising by `lift`."""
    turn = Matrix.Rotation(math.radians(degrees), 4, "Z")
    points = [(0.0, 0.0, 0.0), (-width / 2.0, length * 0.4, lift * 0.5), (width / 2.0, length * 0.4, lift * 0.5), (0.0, length, lift), (0.0, length * 0.4, lift * 0.5 + 0.012)]
    b.hull(points, "paint", srgb(tint), frame=frame @ Matrix.Translation(base) @ turn)


def pyramid_pile(b: Builder, frame: Matrix, center: tuple, radius: float, palette: tuple, generator: random.Random) -> None:
    """Five balls (2x2 plus one on top) resting at center (x, y, floor z)."""
    step = radius * 1.9
    offsets = [(dx * step / 2.0, dy * step / 2.0, 0.0) for dx, dy in itertools.product((-1, 1), repeat=2)] + [(0.0, 0.0, radius * 1.5)]

    for dx, dy, dz in offsets:
        b.sphere((center[0] + dx, center[1] + dy, center[2] + radius + dz), radius, "paint", srgb(generator.choice(palette)), frame=frame, segments=6)


# ---------- shelf goods (extra shapes for filled_row) ----------

def _shoe(b: Builder, frame: Matrix, x: float, y: float, z: float, width: float, depth: float, height: float, color: str) -> None:
    b.box((x, y - depth / 2.0, z), (x + width, y + depth / 2.0, z + 0.035), "paint", srgb("4A3020"), frame=frame)
    b.box((x, y - depth / 2.0, z + 0.035), (x + width, y, z + height * 0.4), "paint", srgb(color), frame=frame)
    b.box((x, y, z + 0.035), (x + width, y + depth / 2.0, z + height), "paint", srgb(color), frame=frame)


def _crystal(b: Builder, frame: Matrix, x: float, y: float, z: float, width: float, depth: float, height: float, color: str) -> None:
    radius = min(width, depth) / 2.0
    b.cylinder((x + width / 2.0, y, z), radius, height * 0.55, 5, "paint", srgb(color), frame=frame)
    b.cylinder((x + width / 2.0, y, z + height * 0.55), radius, height * 0.45, 5, "paint", srgb(color), top_radius=0.004, frame=frame)


def _helmet(b: Builder, frame: Matrix, x: float, y: float, z: float, width: float, depth: float, height: float, color: str) -> None:
    radius = min(width, depth, height) / 2.0
    center_x = x + width / 2.0
    b.sphere((center_x, y, z + radius), radius, "metal", srgb(color), frame=frame, segments=6)
    b.box((center_x - radius * 0.6, y - radius * 1.0, z + radius * 0.85), (center_x + radius * 0.6, y - radius * 0.8, z + radius * 1.15), "paint", srgb("3A2E48"), frame=frame)


def _loaf(b: Builder, frame: Matrix, x: float, y: float, z: float, width: float, depth: float, height: float, color: str) -> None:
    radius = width / 2.0
    b.sphere((x + radius, y, z + radius * 0.7), radius, "paint", srgb(color), scale=(1.0, min(1.5, depth / (2.0 * radius)), 0.7), frame=frame, segments=6)


def _tool(b: Builder, frame: Matrix, x: float, y: float, z: float, width: float, depth: float, height: float, color: str) -> None:
    b.box((x + width * 0.35, y - 0.02, z), (x + width * 0.65, y + 0.02, z + height), "wood", srgb(color), frame=frame, uv=WOOD_LIGHT_UV)
    b.box((x, y - 0.02, z + height - 0.1), (x + width, y + 0.02, z + height), "metal", srgb(STEEL), frame=frame)


ITEM_SHAPES.update({"shoe": _shoe, "crystal": _crystal, "helmet": _helmet, "loaf": _loaf, "tool": _tool})
ITEM_WIDTH.update({"shoe": (0.1, 0.15), "crystal": (0.07, 0.12), "helmet": (0.16, 0.21), "loaf": (0.14, 0.2), "tool": (0.08, 0.13)})
SHELF_FILL = {"bottles": 0.7, "potions": 0.7, "crystals": 0.75, "jars": 0.9, "tools": 0.8}  # triangle-heavy goods are stocked more sparsely

SHELF_GOODS = {  # shelf variant -> (item shapes, palette)
    "books": (("book",), GOODS_PALETTE),
    "jars": (("jar",), GOODS_PALETTE),
    "bottles": (("bottle",), GLASS_PALETTE),
    "boxes": (("box",), GOODS_PALETTE),
    "bread": (("loaf", "roll"), BREAD_PALETTE),
    "cloth": (("box",), CLOTH_PALETTE),
    "helmets": (("helmet",), STEEL_PALETTE),
    "scrolls": (("roll", "book"), PAPER_PALETTE),
    "potions": (("bottle", "jar"), GLASS_PALETTE),
    "crystals": (("crystal",), CRYSTAL_PALETTE),
    "shoes": (("shoe",), SHOE_PALETTE),
    "tools": (("tool",), TOOL_PALETTE),
}
SHELF_VARIANTS = list(SHELF_GOODS) + ["empty"]


def stock_boards(b: Builder, frame: Matrix, x_from: float, x_to: float, y: float, board_tops: list, depth: float, clearance: float, seed: int, variant: str, fill: float = 0.85) -> int:
    """Goods of one shelf variant on every board (no goods for 'empty')."""
    if variant not in SHELF_GOODS:
        return 0

    shapes, palette = SHELF_GOODS[variant]
    generator = random.Random(seed)

    return sum(filled_row(b, frame, x_from, x_to, y, top, depth, clearance, generator, shapes, palette, fill=fill * SHELF_FILL.get(variant, 1.0)) for top in board_tops)


def shelf_boards(b: Builder, frame: Matrix, x_from: float, x_to: float, y_from: float, y_to: float, board_tops: list, tint: str) -> None:
    for top in board_tops:
        wood_box(b, frame, (x_from, y_from, top - 0.04), (x_to, y_to, top), tint, light=True)


def wall_shelf(b: Builder, frame: Matrix, variant: str = "books", seed: int = 1, tint: str = None, **options) -> None:
    half_width, half_depth, height = 1.0, 0.175, 2.2
    board_tops = [0.12, 0.62, 1.12, 1.62]
    body = tint or WOOD_BODY
    side_front = -0.15
    carcass_top = height - 0.07

    wood_box(b, frame, (-half_width + 0.05, 0.15, 0.0), (half_width - 0.05, half_depth, carcass_top), WOOD_DEEP)

    for groove_x in (-0.5, 0.0, 0.5):
        wood_box(b, frame, (groove_x - 0.006, 0.146, 0.1), (groove_x + 0.006, 0.15, carcass_top), "6E4529")

    for side_x in (-half_width, half_width - 0.05):
        bevel_box(b, frame, (side_x, side_front, 0.0), (side_x + 0.05, 0.15, carcass_top), body, bevel=0.008)

    bevel_box(b, frame, (-half_width + 0.05, side_front, 0.0), (half_width - 0.05, 0.15, 0.1), WOOD_DEEP, bevel=0.008)
    run_profile(b, frame, -half_width + 0.05, half_width - 0.05, base_profile(side_front, 0.0, 0.025, 0.1), WOOD_DEEP)
    run_profile(b, frame, -half_width, half_width, cornice_profile(side_front, carcass_top - 0.07, 0.025, 0.07), WOOD_TOP)
    bevel_box(b, frame, (-half_width, -half_depth, carcass_top), (half_width, half_depth, height), WOOD_TOP, bevel=0.016, light=True)

    for top in board_tops:
        bevel_box(b, frame, (-half_width + 0.05, side_front, top - 0.04), (half_width - 0.05, 0.15, top), body, bevel=0.007, light=True)
        wood_box(b, frame, (-half_width + 0.05, side_front - 0.012, top - 0.075), (half_width - 0.05, side_front, top), WOOD_TOP, light=True)

    for tag_x, tag_top in ((-0.62, board_tops[0]), (0.18, board_tops[1]), (-0.2, board_tops[2]), (0.7, board_tops[3])):
        paint_box(b, frame, (tag_x - 0.03, side_front - 0.016, tag_top - 0.07), (tag_x + 0.03, side_front - 0.012, tag_top - 0.025), "F2E6CF")

    stock_boards(b, frame, -half_width + 0.09, half_width - 0.09, -0.01, board_tops, 0.26, 0.4, seed, variant)


def floor_shelf(b: Builder, frame: Matrix, variant: str = "books", seed: int = 1, tint: str = None, **options) -> None:
    half_width, height = 0.75, 1.76
    board_tops = [0.14, 0.7, 1.26]
    body = tint or WOOD_BODY
    turned = frame @ Matrix.Rotation(math.pi, 4, "Z")

    wood_box(b, frame, (-half_width + 0.04, -0.015, 0.0), (half_width - 0.04, 0.015, height - 0.04), WOOD_DEEP)

    for side_x in (-half_width, half_width - 0.04):
        bevel_box(b, frame, (side_x, -0.24, 0.1), (side_x + 0.04, 0.24, height), body, bevel=0.008)

    for foot_x, foot_y in itertools.product((-half_width + 0.01, half_width - 0.1), (-0.24, 0.14)):
        bevel_box(b, frame, (foot_x, foot_y, 0.0), (foot_x + 0.09, foot_y + 0.1, 0.12), WOOD_DEEP, bevel=0.01)

    bevel_box(b, frame, (-half_width + 0.04, -0.24, 0.1), (half_width - 0.04, 0.24, 0.16), WOOD_DEEP, bevel=0.008)
    bevel_box(b, frame, (-half_width, -0.25, height - 0.07), (half_width, 0.25, height), WOOD_TOP, bevel=0.016, light=True)

    for finial_x, finial_y in itertools.product((-half_width + 0.04, half_width - 0.04), (-0.19, 0.19)):
        b.sphere((finial_x, finial_y, height), 0.03, "wood", srgb(WOOD_DEEP), frame=frame, segments=6)

    for side_frame, sign in ((frame, -1.0), (turned, 1.0)):
        run_profile(b, side_frame, -half_width, half_width, cornice_profile(-0.24, height - 0.14, 0.01, 0.07), WOOD_TOP)

        for top in board_tops:
            bevel_box(b, side_frame, (-half_width + 0.04, -0.245, top - 0.04), (half_width - 0.04, -0.015, top), body, bevel=0.007, light=True)
            wood_box(b, side_frame, (-half_width + 0.04, -0.25, top - 0.07), (half_width - 0.04, -0.245, top), WOOD_TOP, light=True)

        stock_boards(b, side_frame, -half_width + 0.09, half_width - 0.09, -0.13, board_tops, 0.2, 0.5, seed + int(sign), variant, fill=0.75)


# ---------- counters ----------

def counter_block(b: Builder, frame: Matrix, x_from: float, x_to: float, y_from: float, y_to: float, top: float = 1.05, panels: bool = True, inset: float = 0.03) -> None:
    """Counter run: recessed plinth with skirting, body, pilasters, framed doors and drawers on the y_from face,
    moulded underside and a bevelled overhanging top."""
    body_front = y_from + inset
    door_top = top - (0.28 if top > 0.9 else 0.17)

    bevel_box(b, frame, (x_from + 0.06, y_from + 0.06, 0.0), (x_to - 0.06, y_to - 0.06, 0.1), WOOD_DEEP, bevel=0.01)
    bevel_box(b, frame, (x_from + inset, y_from + inset, 0.1), (x_to - inset, y_to - inset, top - 0.07), WOOD_BODY, bevel=0.008)
    run_profile(b, frame, x_from + inset, x_to - inset, base_profile(body_front, 0.1, inset, 0.09), WOOD_DEEP)
    run_profile(b, frame, x_from, x_to, cornice_profile(body_front, top - 0.14, inset, 0.07), WOOD_TOP)
    bevel_box(b, frame, (x_from, y_from, top - 0.07), (x_to, y_to, top), WOOD_TOP, bevel=0.018, light=True)

    if not panels:
        return

    count = max(1, round((x_to - x_from) / 0.95))
    span = (x_to - x_from) / count

    for index in range(count + 1):
        pilaster_x = min(max(x_from + index * span, x_from + 0.045 + inset), x_to - 0.045 - inset)
        bevel_box(b, frame, (pilaster_x - 0.045, y_from + 0.008, 0.1), (pilaster_x + 0.045, body_front, top - 0.14), WOOD_DEEP, bevel=0.007)

    for index in range(count):
        panel_from, panel_to = x_from + index * span + 0.09, x_from + (index + 1) * span - 0.09
        raised_panel(b, frame, panel_from, panel_to, 0.17, door_top, body_front)
        knob(b, frame, panel_to - 0.07, body_front - 0.021, door_top - 0.14, 0.016)

        if top > 0.9:
            raised_panel(b, frame, panel_from, panel_to, door_top + 0.03, top - 0.17, body_front, border=0.035)
            knob(b, frame, (panel_from + panel_to) / 2.0, body_front - 0.021, (door_top + top - 0.14) / 2.0, 0.014)


def counter_straight(b: Builder, frame: Matrix, **options) -> None:
    counter_block(b, frame, -1.5, 1.5, -0.35, 0.35)


def counter_l(b: Builder, frame: Matrix, **options) -> None:
    counter_block(b, frame, -1.5, 1.5, -1.0, -0.3)
    counter_block(b, frame, 0.8, 1.5, -0.3, 1.0, panels=False)
    wood_box(b, frame, (0.83, -0.34, 0.1), (1.47, -0.26, 0.98), WOOD_BODY)


def counter_glass(b: Builder, frame: Matrix, seed: int = 1, **options) -> None:
    generator = random.Random(seed)
    base_top, case_top = 0.6, 1.0

    counter_block(b, frame, -1.2, 1.2, -0.4, 0.4, top=base_top)

    for corner_x, corner_y in itertools.product((-1.2, 1.15), (-0.4, 0.35)):
        wood_box(b, frame, (corner_x, corner_y, base_top), (corner_x + 0.05, corner_y + 0.05, case_top), WOOD_BODY)

    for bar_low, bar_high in (((-1.2, -0.4, case_top), (1.2, -0.35, case_top + 0.06)), ((-1.2, 0.35, case_top), (1.2, 0.4, case_top + 0.06)), ((-1.2, -0.35, case_top), (-1.15, 0.35, case_top + 0.06)), ((1.15, -0.35, case_top), (1.2, 0.35, case_top + 0.06))):
        wood_box(b, frame, bar_low, bar_high, WOOD_TOP, light=True)

    b.box((-1.15, -0.35, base_top), (1.15, 0.35, case_top), "vitrine", WHITE, frame=frame)
    paint_box(b, frame, (-1.14, -0.34, base_top), (1.14, 0.34, base_top + 0.02), "8C2F4A")
    paint_box(b, frame, (-1.14, 0.0, base_top + 0.02), (1.14, 0.34, base_top + 0.12), "6C4F9A")
    filled_row(b, frame, -1.1, 1.1, -0.17, base_top + 0.02, 0.2, 0.2, generator, ("crystal", "ball", "bottle"), GLASS_PALETTE, fill=0.8)
    filled_row(b, frame, -1.1, 1.1, 0.17, base_top + 0.12, 0.2, 0.2, generator, ("crystal", "ball", "box"), GOODS_PALETTE, fill=0.8)


def counter_till(b: Builder, frame: Matrix, **options) -> None:
    top = 1.05
    counter_block(b, frame, -1.5, 1.5, -0.35, 0.35)

    # balance scale on the left: weighted base, post, bevelled beam, hanging pans on three cords each
    bevel_box(b, frame, (-1.0, -0.1, top), (-0.8, 0.1, top + 0.03), BRASS, bevel=0.008, material="metal")
    b.cylinder((-0.9, 0.0, top + 0.03), 0.014, 0.3, 6, "metal", srgb(BRASS), frame=frame)
    bevel_box(b, frame, (-1.13, -0.01, top + 0.31), (-0.67, 0.01, top + 0.335), BRASS, bevel=0.004, material="metal")
    b.sphere((-0.9, 0.0, top + 0.345), 0.02, "metal", srgb(GOLD), frame=frame, segments=6)

    for pan_x in (-1.1, -0.7):
        lathe(b, [(0.03, top + 0.06), (0.09, top + 0.08), (0.105, top + 0.1), (0.09, top + 0.1)], 10, "metal", BRASS, frame, base=(pan_x, 0.0, 0.0))

        for degrees in (0, 120, 240):
            foot = (pan_x + 0.09 * math.cos(math.radians(degrees)), 0.09 * math.sin(math.radians(degrees)), top + 0.095)
            b.beam(foot, (pan_x, 0.0, top + 0.31), 0.004, 0.004, "metal", srgb(BRASS), frame=frame)

    # cash box: banded lid, hasp and carry handle, coin stacks and loose coins beside it
    bevel_box(b, frame, (0.4, -0.13, top), (0.82, 0.11, top + 0.14), WOOD_DEEP, bevel=0.01)
    bevel_box(b, frame, (0.4, -0.13, top + 0.11), (0.82, 0.11, top + 0.14), WOOD_TOP, bevel=0.012, light=True)

    for band_x in (0.44, 0.75):
        metal_box(b, frame, (band_x, -0.135, top), (band_x + 0.03, 0.115, top + 0.145), IRON)

    metal_box(b, frame, (0.59, -0.14, top + 0.07), (0.63, -0.12, top + 0.13), BRASS)
    ring(b, (0.61, 0.0, top + 0.14), 0.05, 0.007, "metal", IRON, frame, sides=8, tube_sides=4, axis="Y")

    for coin_x, coin_count in ((0.95, 3), (1.05, 6), (1.15, 2), (1.25, 4)):
        b.cylinder((coin_x, -0.12, top), 0.035, 0.012 * coin_count, 10, "metal", srgb(GOLD), frame=frame)

    for coin_x, coin_y in ((0.98, -0.02), (1.1, 0.08), (1.22, -0.05)):
        b.cylinder((coin_x, coin_y, top), 0.03, 0.008, 10, "metal", srgb("FFE27A"), frame=frame)

    # open ledger with ruled pages, inkwell and quill, little brass bell
    bevel_box(b, frame, (0.05, -0.1, top), (0.3, 0.14, top + 0.025), "7A2F3A", bevel=0.006, material="paint")
    page_points = [(0.07, -0.08), (0.175, -0.08), (0.28, -0.08), (0.07, 0.12), (0.175, 0.12), (0.28, 0.12)]
    solid_hull(b, [(u, v, top + 0.025 + (0.005 if u == 0.175 else 0.0)) for u, v in page_points] + [(u, v, top + 0.035 + (0.005 if u == 0.175 else 0.0)) for u, v in page_points], "paint", "F2E6CF", frame)
    paint_box(b, frame, (0.12, -0.05, top + 0.04), (0.17, 0.1, top + 0.0415), "5A4A5E")
    paint_box(b, frame, (0.19, -0.05, top + 0.04), (0.25, 0.1, top + 0.0415), "5A4A5E")
    lathe(b, [(0.03, top), (0.034, top + 0.03), (0.02, top + 0.045), (0.016, top + 0.05)], 8, "paint", "2B2236", frame, base=(-0.35, 0.1, 0.0))
    b.beam((-0.35, 0.1, top + 0.04), (-0.28, 0.14, top + 0.2), 0.03, 0.005, "paint", srgb("F7F2E8"), frame=frame, uv=None)
    lathe(b, [(0.001, top), (0.045, top), (0.05, top + 0.012), (0.03, top + 0.05), (0.012, top + 0.08), (0.001, top + 0.09)], 10, "metal", BRASS, frame, base=(-0.5, -0.12, 0.0))


PROPS.update(
    {
        "wall_shelf": {"build": wall_shelf, "size": (2.0, 0.35, 2.2), "solid": True, "clearance": 0.6, "variants": SHELF_VARIANTS},
        "floor_shelf": {"build": floor_shelf, "size": (1.5, 0.5, 1.8), "solid": True, "clearance": 0.6, "variants": SHELF_VARIANTS},
        "counter_straight": {"build": counter_straight, "size": (3.0, 0.7, 1.05), "solid": True, "clearance": 0.8},
        "counter_l": {"build": counter_l, "size": (3.0, 2.0, 1.05), "solid": True, "clearance": 0.8},
        "counter_glass": {"build": counter_glass, "size": (2.4, 0.8, 1.06), "solid": True, "clearance": 0.8},
        "counter_till": {"build": counter_till, "size": (3.0, 0.7, 1.4), "solid": True, "clearance": 0.8},
    }
)

# ---------- tables, crates, sacks, barrels ----------

def display_fruit(b: Builder, frame: Matrix, generator: random.Random, top: float) -> None:
    pyramid_pile(b, frame, (-0.3, 0.0, top), 0.07, ("C9483B", "E0884A", "D9573F"), generator)
    pyramid_pile(b, frame, (0.3, 0.0, top), 0.07, ("7FC46A", "E8C14F", "A9D26B"), generator)


def display_bread(b: Builder, frame: Matrix, generator: random.Random, top: float) -> None:
    for loaf_x, loaf_y in itertools.product((-0.5, -0.2, 0.1, 0.4), (-0.18, 0.18)):
        _loaf(b, frame, loaf_x, loaf_y, top, 0.2, 0.3, 0.14, generator.choice(BREAD_PALETTE))


def display_cloth(b: Builder, frame: Matrix, generator: random.Random, top: float) -> None:
    for stack_x, stack_y in itertools.product((-0.45, 0.0, 0.45), (-0.17, 0.17)):
        paint_box(b, frame, (stack_x - 0.19, stack_y - 0.14, top), (stack_x + 0.19, stack_y + 0.14, top + 0.05 * generator.randint(2, 4)), generator.choice(CLOTH_PALETTE))


def display_pottery(b: Builder, frame: Matrix, generator: random.Random, top: float) -> None:
    for vase_x, scale in ((-0.5, 0.8), (-0.2, 1.1), (0.15, 1.0), (0.5, 0.85)):
        profile = [(0.05 * scale, 0.0), (0.085 * scale, 0.06 * scale), (0.09 * scale, 0.13 * scale), (0.05 * scale, 0.22 * scale), (0.04 * scale, 0.27 * scale), (0.06 * scale, 0.3 * scale)]
        lathe(b, profile, 8, "paint", generator.choice(("C9683F", "4F8FC9", "E8C14F", "7FC46A", "C46AA8")), frame, base=(vase_x, generator.uniform(-0.12, 0.12), top))


TABLE_GOODS = {"fruit": display_fruit, "bread": display_bread, "cloth": display_cloth, "pottery": display_pottery}


def display_table(b: Builder, frame: Matrix, variant: str = "fruit", seed: int = 1, tint: str = None, **options) -> None:
    top = 0.84

    for leg_x, leg_y in itertools.product((-0.6, 0.6), (-0.36, 0.36)):
        turned_leg(b, frame, leg_x, leg_y, top - 0.12, 0.045, WOOD_DEEP, "baluster")

    for rail_y in (-0.36, 0.36):
        bevel_box(b, frame, (-0.6, rail_y - 0.015, top - 0.2), (0.6, rail_y + 0.015, top - 0.12), WOOD_BODY, bevel=0.008)
        bevel_box(b, frame, (-0.6, rail_y - 0.012, 0.2), (0.6, rail_y + 0.012, 0.24), WOOD_DEEP, bevel=0.006)

    for rail_x in (-0.6, 0.6):
        bevel_box(b, frame, (rail_x - 0.015, -0.36, top - 0.2), (rail_x + 0.015, 0.36, top - 0.12), WOOD_BODY, bevel=0.008)

    bevel_box(b, frame, (-0.7, -0.45, top - 0.06), (0.7, 0.45, top), tint or WOOD_TOP, bevel=0.016, light=True)
    paint_box(b, frame, (-0.6, -0.4, top), (0.6, 0.4, top + 0.006), "EBD3A0")
    paint_box(b, frame, (-0.6, -0.4, top - 0.08), (0.6, -0.395, top), "EBD3A0")
    paint_box(b, frame, (-0.6, -0.4, top - 0.1), (0.6, -0.39, top - 0.08), "C9483B")
    TABLE_GOODS[variant](b, frame, random.Random(seed), top + 0.006)


def crate(b: Builder, frame: Matrix, x: float, y: float, z: float, width: float, depth: float, height: float, tint: str = WOOD_BODY) -> None:
    """Slatted crate standing on z: dark inner body, three gapped slats per long face, corner posts and a brace."""
    half_width, half_depth = width / 2.0, depth / 2.0
    slat = height / 3.0 - 0.012
    wood_box(b, frame, (x - half_width + 0.02, y - half_depth + 0.02, z + 0.01), (x + half_width - 0.02, y + half_depth - 0.02, z + height - 0.01), WOOD_DEEP, light=True)

    for sign_x, sign_y in itertools.product((-1.0, 1.0), repeat=2):
        corner_x, corner_y = x + sign_x * (half_width - 0.025), y + sign_y * (half_depth - 0.025)
        bevel_box(b, frame, (corner_x - 0.025, corner_y - 0.025, z), (corner_x + 0.025, corner_y + 0.025, z + height), WOOD_DEEP, bevel=0.006, light=True)

    for sign_y, row in itertools.product((-1.0, 1.0), range(3)):
        edge = y + sign_y * half_depth
        low = z + 0.006 + row * (slat + 0.012)
        wood_box(b, frame, (x - half_width + 0.05, min(edge, edge - sign_y * 0.02), low), (x + half_width - 0.05, max(edge, edge - sign_y * 0.02), low + slat), tint if row % 2 == 0 else WOOD_TOP, light=True)

    for sign_x in (-1.0, 1.0):
        edge = x + sign_x * half_width
        wood_box(b, frame, (min(edge, edge - sign_x * 0.02), y - half_depth + 0.05, z + 0.02), (max(edge, edge - sign_x * 0.02), y + half_depth - 0.05, z + height - 0.02), tint, light=True)

    if width > 0.45:
        wood_beam(b, frame, (x - half_width + 0.08, y - half_depth - 0.004, z + 0.06), (x + half_width - 0.08, y - half_depth - 0.004, z + height - 0.06), 0.04, 0.012, WOOD_DEEP, light=True)


def crate_stack(b: Builder, frame: Matrix, tint: str = None, **options) -> None:
    body = tint or WOOD_BODY
    crate(b, frame, -0.4, 0.15, 0.0, 0.6, 0.6, 0.5, body)
    crate(b, frame, 0.4, 0.15, 0.0, 0.6, 0.6, 0.5, WOOD_HONEY)
    crate(b, frame, 0.0, 0.15, 0.5, 0.6, 0.6, 0.5, body)
    crate(b, frame, -0.4, -0.3, 0.0, 0.4, 0.3, 0.32, WOOD_HONEY)


def open_crate_shell(b: Builder, frame: Matrix, height: float) -> None:
    """Open-topped crate 0.7 x 0.5: floor, gapped slat walls, corner posts, rim."""
    wood_box(b, frame, (-0.35, -0.25, 0.0), (0.35, 0.25, 0.04), WOOD_DEEP, light=True)
    wood_box(b, frame, (-0.33, -0.23, 0.04), (0.33, 0.23, height - 0.02), WOOD_DEEP, light=True)
    slat = (height - 0.04) / 3.0 - 0.01

    for row in range(3):
        low = 0.04 + row * (slat + 0.01)
        tone = WOOD_BODY if row % 2 == 0 else WOOD_TOP
        wood_box(b, frame, (-0.35, -0.25, low), (0.35, -0.22, low + slat), tone, light=True)
        wood_box(b, frame, (-0.35, 0.22, low), (0.35, 0.25, low + slat), tone, light=True)
        wood_box(b, frame, (-0.35, -0.22, low), (-0.32, 0.22, low + slat), tone, light=True)
        wood_box(b, frame, (0.32, -0.22, low), (0.35, 0.22, low + slat), tone, light=True)

    for corner_x, corner_y in itertools.product((-0.35, 0.3), (-0.25, 0.2)):
        bevel_box(b, frame, (corner_x, corner_y, 0.0), (corner_x + 0.05, corner_y + 0.05, height + 0.02), WOOD_DEEP, bevel=0.006, light=True)


def contents_apples(b: Builder, frame: Matrix, generator: random.Random) -> None:
    for apple_x, apple_y in itertools.product((-0.225, -0.075, 0.075, 0.225), (-0.1, 0.1)):
        b.sphere((apple_x, apple_y, 0.2), 0.072, "paint", srgb(generator.choice(("C9483B", "E0884A", "D9573F"))), frame=frame, segments=6)

    pyramid_pile(b, frame, (0.0, 0.0, 0.3), 0.065, ("C9483B", "E0884A"), generator)


def contents_ingots(b: Builder, frame: Matrix, generator: random.Random) -> None:
    half_width, half_depth = 0.085, 0.07
    stacks = itertools.product(itertools.product((-0.2, 0.0, 0.2), (-0.1, 0.1)), range(3))

    for (ingot_x, ingot_y), layer in stacks:
        low, high = 0.04 + layer * 0.08, 0.04 + (layer + 1) * 0.08
        points = [(sx * half_width, sy * half_depth, low) for sx, sy in itertools.product((-1, 1), repeat=2)] + [(sx * half_width * 0.8, sy * half_depth * 0.75, high) for sx, sy in itertools.product((-1, 1), repeat=2)]
        b.hull(points, "metal", srgb(GOLD if (ingot_x > 0) == (layer % 2 == 0) else STEEL), frame=frame @ Matrix.Translation((ingot_x, ingot_y, 0.0)))


def contents_roots(b: Builder, frame: Matrix, generator: random.Random) -> None:
    for root_x, root_y in itertools.product((-0.24, -0.12, 0.0, 0.12, 0.24), (-0.1, 0.1)):
        height = generator.uniform(0.2, 0.28)
        b.cylinder((root_x, root_y, 0.04), 0.036, height, 5, "paint", srgb(generator.choice(("E0884A", "E8A24A", "D9742F"))), top_radius=0.006, frame=frame)
        leaf(b, frame, (root_x, root_y, 0.04 + height * 0.6), 0.12, 0.05, generator.uniform(0, 360), 0.1, "3F8A50")


def contents_cloth(b: Builder, frame: Matrix, generator: random.Random) -> None:
    for fold_x, fold_y, layer in itertools.product((-0.17, 0.17), (-0.1, 0.1), range(3)):
        paint_box(b, frame, (fold_x - 0.15, fold_y - 0.09, 0.04 + layer * 0.07), (fold_x + 0.15, fold_y + 0.09, 0.04 + (layer + 1) * 0.07), generator.choice(CLOTH_PALETTE))


def contents_bottles(b: Builder, frame: Matrix, generator: random.Random) -> None:
    filled_row(b, frame, -0.3, 0.3, -0.1, 0.04, 0.12, 0.36, generator, ("bottle",), GLASS_PALETTE, fill=1.0)
    filled_row(b, frame, -0.3, 0.3, 0.1, 0.04, 0.12, 0.36, generator, ("bottle",), GLASS_PALETTE, fill=1.0)


CRATE_CONTENTS = {"apples": contents_apples, "ingots": contents_ingots, "roots": contents_roots, "cloth": contents_cloth, "bottles": contents_bottles}


def crate_open(b: Builder, frame: Matrix, variant: str = "apples", seed: int = 1, **options) -> None:
    open_crate_shell(b, frame, 0.36)
    CRATE_CONTENTS[variant](b, frame, random.Random(seed))


def sack(b: Builder, frame: Matrix, x: float, y: float, z: float, radius: float, height: float, tint: str) -> None:
    """Sack: flat base, round belly with a slump, gathered neck, rope tie, two dog-ear tips."""
    profile = [(0.75 * radius, 0.0), (0.95 * radius, 0.1 * height), (radius, 0.3 * height), (0.97 * radius, 0.5 * height), (0.78 * radius, 0.68 * height), (0.34 * radius, 0.82 * height), (0.42 * radius, 0.92 * height), (0.16 * radius, height)]
    lathe(b, profile, 8, "paint", tint, frame, base=(x, y, z))
    ring(b, (x, y, z + 0.8 * height), 0.3 * radius, 0.012, "wood", "8B5A3C", frame, sides=8, tube_sides=3)

    for degrees in (35, 215):
        tip = (x + 0.24 * radius * math.cos(math.radians(degrees)), y + 0.24 * radius * math.sin(math.radians(degrees)), z + height * 1.0)
        b.beam((x, y, z + 0.9 * height), tip, 0.1 * radius, 0.02, "paint", srgb(tint), frame=frame, uv=None)


def sack_pile(b: Builder, frame: Matrix, tint: str = None, **options) -> None:
    flour, grain, wheat = tint or "F2E6CF", "DDAE62", "C98F4F"
    for sack_x, sack_y, sack_z, radius, height, color in ((-0.32, 0.12, 0.0, 0.27, 0.42, flour), (0.12, 0.15, 0.0, 0.27, 0.42, grain), (0.35, -0.05, 0.0, 0.25, 0.4, wheat), (-0.1, 0.12, 0.4, 0.27, 0.36, wheat), (-0.3, -0.22, 0.0, 0.22, 0.34, grain)):
        sack(b, frame, sack_x, sack_y, sack_z, radius, height, color)


def barrel_profile(radius: float, height: float) -> list:
    return [(radius * 0.8, 0.0), (radius * 0.9, height * 0.1), (radius * 0.97, height * 0.28), (radius, height * 0.5), (radius * 0.97, height * 0.72), (radius * 0.9, height * 0.9), (radius * 0.8, height)]


def barrel(b: Builder, frame: Matrix, x: float, y: float, radius: float, height: float, tint: str = WOOD_HONEY) -> None:
    """Staved barrel: bellied body, recessed lid with chime, bung, four iron hoops hugging the belly."""
    profile = barrel_profile(radius, height)
    lathe(b, profile, 12, "wood", tint, frame, base=(x, y, 0.0), uv=WOOD_LIGHT_UV)
    b.cylinder((x, y, height - 0.03), radius * 0.74, 0.035, 12, "wood", srgb(WOOD_DEEP), frame=frame, uv=WOOD_LIGHT_UV)
    ring(b, (x, y, height - 0.012), radius * 0.77, 0.014, "wood", WOOD_TOP, frame, sides=12, tube_sides=4)
    b.cylinder((x + radius * 0.3, y - radius * 0.1, height - 0.005), 0.03, 0.02, 6, "wood", srgb("5A3A26"), frame=frame)

    for hoop_fraction in (0.14, 0.34, 0.66, 0.86):
        hoop_z = height * hoop_fraction
        below = max((point for point in profile if point[1] <= hoop_z), key=lambda point: point[1])
        above = min((point for point in profile if point[1] >= hoop_z), key=lambda point: point[1])
        span = above[1] - below[1]
        hoop_radius = below[0] + (above[0] - below[0]) * ((hoop_z - below[1]) / span if span > 1e-6 else 0.0)
        ring(b, (x, y, hoop_z), hoop_radius, 0.011, "metal", IRON, frame, sides=12, tube_sides=4)


def barrel_group(b: Builder, frame: Matrix, tint: str = None, **options) -> None:
    barrel(b, frame, -0.33, 0.2, 0.3, 0.95, tint or WOOD_HONEY)
    barrel(b, frame, 0.3, 0.2, 0.3, 0.95, WOOD_BODY)
    barrel(b, frame, -0.05, -0.23, 0.27, 0.85, tint or WOOD_HONEY)


# rug colours: (field, border, accent)
RUG_COLOURS = {"red": ("B03A48", "E8C14F", "7A2F3A"), "blue": ("3E6A9A", "F2E6CF", "27466B"), "green": ("3F8A50", "E8C14F", "2F6B4F"), "gold": ("E3B76A", "7A2F3A", "B5533F")}


def rug(b: Builder, frame: Matrix, variant: str = "red", **options) -> None:
    field, border, accent = RUG_COLOURS[variant]
    paint_box(b, frame, (-0.96, -0.7, 0.0), (0.96, 0.7, 0.008), field)

    for low, high in (((-0.96, -0.7, 0.008), (0.96, -0.6, 0.012)), ((-0.96, 0.6, 0.008), (0.96, 0.7, 0.012)), ((-0.96, -0.6, 0.008), (-0.86, 0.6, 0.012)), ((0.86, -0.6, 0.008), (0.96, 0.6, 0.012))):
        paint_box(b, frame, low, high, border)

    for low, high in (((-0.84, -0.58, 0.008), (0.84, -0.55, 0.0125)), ((-0.84, 0.55, 0.008), (0.84, 0.58, 0.0125)), ((-0.84, -0.55, 0.008), (-0.81, 0.55, 0.0125)), ((0.81, -0.55, 0.008), (0.84, 0.55, 0.0125))):
        paint_box(b, frame, low, high, accent)

    diamond = [(0.0, -0.4), (0.7, 0.0), (0.0, 0.4), (-0.7, 0.0)]
    inner = [(0.0, -0.22), (0.4, 0.0), (0.0, 0.22), (-0.4, 0.0)]
    centre = [(0.0, -0.1), (0.18, 0.0), (0.0, 0.1), (-0.18, 0.0)]

    for outline, tone, low, high in ((diamond, accent, 0.012, 0.018), (inner, border, 0.018, 0.02), (centre, accent, 0.02, 0.022)):
        b.hull([(u, v, low) for u, v in outline] + [(u, v, high) for u, v in outline], "paint", srgb(tone), frame=frame)

    corner_diamond = [(-0.07, 0.0), (0.0, -0.07), (0.07, 0.0), (0.0, 0.07)]

    for corner_u, corner_v in itertools.product((-0.72, 0.72), (-0.42, 0.42)):
        b.hull([(corner_u + du, corner_v + dv, 0.012) for du, dv in corner_diamond] + [(corner_u + du, corner_v + dv, 0.016) for du, dv in corner_diamond], "paint", srgb(border), frame=frame)

    for fringe_x, fringe_y in itertools.product((-0.99, 0.97), [-0.62 + 0.1 * index for index in range(13)]):
        paint_box(b, frame, (fringe_x, fringe_y, 0.0), (fringe_x + 0.03, fringe_y + 0.05, 0.006), "F2E6CF")


def chest_gold(b: Builder, frame: Matrix, **options) -> None:
    frame = frame @ Matrix.Translation((0.0, -0.035, 0.0))  # centres body plus the open lid on the prop box
    body_top = 0.38
    bevel_box(b, frame, (-0.4, -0.22, 0.0), (0.4, 0.22, 0.05), WOOD_DEEP, bevel=0.008)
    bevel_box(b, frame, (-0.4, -0.22, 0.05), (0.4, -0.18, body_top), WOOD_BODY, bevel=0.008)
    bevel_box(b, frame, (-0.4, 0.18, 0.05), (0.4, 0.22, body_top), WOOD_BODY, bevel=0.008)
    bevel_box(b, frame, (-0.4, -0.18, 0.05), (-0.36, 0.18, body_top), WOOD_BODY, bevel=0.008)
    bevel_box(b, frame, (0.36, -0.18, 0.05), (0.4, 0.18, body_top), WOOD_BODY, bevel=0.008)

    for corner_x, corner_y in itertools.product((-0.37, 0.37), (-0.19, 0.19)):
        b.sphere((corner_x, corner_y, 0.04), 0.03, "metal", srgb(BRASS), frame=frame, segments=6)

    for strap_x in (-0.3, 0.3):
        metal_box(b, frame, (strap_x - 0.035, -0.225, 0.0), (strap_x + 0.035, -0.18, body_top + 0.01), IRON)

    metal_box(b, frame, (-0.04, -0.235, body_top - 0.12), (0.04, -0.215, body_top - 0.02), BRASS)

    mound = [(sx * 0.34, sy * 0.15, 0.3) for sx, sy in itertools.product((-1, 1), repeat=2)] + [(0.0, 0.0, 0.5), (-0.17, 0.0, 0.46), (0.17, 0.0, 0.46), (0.0, -0.12, 0.42), (0.0, 0.12, 0.42)]
    b.hull(mound, "metal", srgb(GOLD), frame=frame)

    for coin_x, coin_y, coin_z in ((-0.12, -0.05, 0.48), (0.2, -0.02, 0.43), (0.05, 0.1, 0.46), (-0.26, 0.05, 0.38)):
        b.sphere((coin_x, coin_y, coin_z), 0.05, "metal", srgb("FFE27A"), scale=(1.0, 1.0, 0.45), frame=frame, segments=6)

    # lid swung open past vertical: hinge on the back edge, slab leans back
    hinge = (0.22, body_top)
    lid_angle = math.radians(96.0)
    along = (-math.cos(lid_angle), math.sin(lid_angle))
    outward = (math.sin(lid_angle), math.cos(lid_angle))
    lid_length, lid_thickness = 0.44, 0.04
    points = [(sx, hinge[0] + along[0] * span + outward[0] * thickness, hinge[1] + along[1] * span + outward[1] * thickness) for sx, span, thickness in itertools.product((-0.4, 0.4), (0.0, lid_length), (0.0, lid_thickness))]
    b.hull(points, "wood", srgb(WOOD_BODY), frame=frame, uv=WOOD_DARK_UV)

    for strap_x in (-0.3, 0.3):
        lid_points = [(strap_x + sx, hinge[0] + along[0] * span + outward[0] * (lid_thickness + 0.008 * reach), hinge[1] + along[1] * span + outward[1] * (lid_thickness + 0.008 * reach)) for sx, span, reach in itertools.product((-0.035, 0.035), (0.0, lid_length), (0, 1))]
        b.hull(lid_points, "metal", srgb(IRON), frame=frame)


# ---------- baskets, plants, ladder ----------

def basket_bread(b: Builder, frame: Matrix, generator: random.Random) -> None:
    for loaf_x, loaf_y in itertools.product((-0.12, 0.1), (-0.09, 0.09)):
        _loaf(b, frame, loaf_x - 0.07, loaf_y, 0.2, 0.15, 0.2, 0.14, generator.choice(BREAD_PALETTE))


def basket_herbs(b: Builder, frame: Matrix, generator: random.Random) -> None:
    for degrees in range(0, 360, 40):
        leaf(b, frame, (0.0, 0.0, 0.2), 0.2, 0.07, degrees, generator.uniform(0.1, 0.22), generator.choice(HERB_PALETTE))


def basket_wool(b: Builder, frame: Matrix, generator: random.Random) -> None:
    for ball_x, ball_y, ball_z in ((-0.1, -0.06, 0.28), (0.1, -0.06, 0.28), (0.0, 0.1, 0.28), (0.0, 0.0, 0.36)):
        b.sphere((ball_x, ball_y, ball_z), 0.1, "paint", srgb(generator.choice(("F2E6CF", "F59AD8", "BFD8E8", "F7D6C4"))), frame=frame, segments=6)


def basket_fruit(b: Builder, frame: Matrix, generator: random.Random) -> None:
    pyramid_pile(b, frame, (0.0, 0.0, 0.2), 0.075, ("C9483B", "E0884A", "E8C14F"), generator)


def basket_mushrooms(b: Builder, frame: Matrix, generator: random.Random) -> None:
    for mushroom_x, mushroom_y, stem in ((-0.1, -0.05, 0.12), (0.08, -0.08, 0.1), (0.05, 0.08, 0.14), (-0.08, 0.09, 0.09)):
        b.cylinder((mushroom_x, mushroom_y, 0.2), 0.02, stem, 5, "paint", srgb("F2E6CF"), frame=frame)
        b.sphere((mushroom_x, mushroom_y, 0.2 + stem), 0.055, "paint", srgb(generator.choice(("C9483B", "E0884A", "B5784A"))), scale=(1.0, 1.0, 0.6), frame=frame, segments=6)


BASKET_CONTENTS = {"bread": basket_bread, "herbs": basket_herbs, "wool": basket_wool, "fruit": basket_fruit, "mushrooms": basket_mushrooms}


def wicker_basket(b: Builder, frame: Matrix, variant: str = "bread", seed: int = 1, tint: str = None, **options) -> None:
    profile = [(0.16, 0.0), (0.22, 0.04), (0.235, 0.2), (0.25, 0.3), (0.25, 0.32), (0.22, 0.32), (0.22, 0.18)]
    lathe(b, profile, 10, "paint", tint or "E2B466", frame)
    lathe(b, [(0.254, 0.26), (0.254, 0.32), (0.22, 0.32), (0.22, 0.26)], 10, "paint", "B07A3C", frame, closed=True)
    lathe(b, [(0.236, 0.07), (0.236, 0.11), (0.226, 0.11), (0.226, 0.07)], 10, "paint", "B07A3C", frame, closed=True)
    ring(b, (0.0, 0.0, 0.28), 0.16, 0.012, "paint", "B07A3C", frame, sides=10, tube_sides=4, axis="Y")
    BASKET_CONTENTS[variant](b, frame, random.Random(seed))


def plant_fern(b: Builder, frame: Matrix, generator: random.Random) -> None:
    for degrees in range(0, 360, 40):
        leaf(b, frame, (0.0, 0.0, 0.3), 0.22, 0.09, degrees + generator.uniform(-8, 8), generator.uniform(0.2, 0.34), generator.choice(("3F8A50", "7FC46A", "5FA85A")))


def plant_flower(b: Builder, frame: Matrix, generator: random.Random) -> None:
    for angle in range(0, 360, 72):
        stem_x, stem_y = 0.08 * math.cos(math.radians(angle)), 0.08 * math.sin(math.radians(angle))
        height = generator.uniform(0.25, 0.42)
        b.cylinder((stem_x, stem_y, 0.3), 0.01, height, 4, "paint", srgb("3F8A50"), frame=frame)
        b.sphere((stem_x, stem_y, 0.3 + height), 0.055, "paint", srgb(generator.choice(("F59AD8", "E8C14F", "F2E6CF", "E0884A", "B57FE0"))), frame=frame, segments=6)
        leaf(b, frame, (stem_x, stem_y, 0.32), 0.14, 0.06, angle, 0.06, "5FA85A")


def plant_bush(b: Builder, frame: Matrix, generator: random.Random) -> None:
    for blob_x, blob_y, blob_z, radius in ((0.0, 0.0, 0.5, 0.2), (-0.12, 0.04, 0.4, 0.15), (0.12, -0.03, 0.4, 0.16), (0.02, 0.12, 0.38, 0.14), (0.0, -0.12, 0.38, 0.13)):
        b.sphere((blob_x, blob_y, blob_z), radius, "paint", srgb(generator.choice(("3F8A50", "5FA85A", "7FC46A"))), frame=frame, segments=7)


PLANT_BUILDERS = {"fern": plant_fern, "flower": plant_flower, "bush": plant_bush}


def plant_pot(b: Builder, frame: Matrix, variant: str = "fern", seed: int = 1, **options) -> None:
    """Terracotta pot on a saucer with a banded rim, dark soil and the plant."""
    profile = [(0.12, 0.0), (0.14, 0.02), (0.2, 0.26), (0.205, 0.285), (0.225, 0.29), (0.225, 0.34), (0.19, 0.34), (0.19, 0.3)]
    lathe(b, profile, 12, "paint", "C9683F", frame)
    lathe(b, [(0.001, 0.0), (0.17, 0.0), (0.18, 0.012), (0.12, 0.02), (0.001, 0.02)], 12, "paint", "A9532F", frame)
    ring(b, (0.0, 0.0, 0.22), 0.205, 0.012, "paint", "A9532F", frame, sides=12, tube_sides=4)
    b.cylinder((0.0, 0.0, 0.29), 0.19, 0.012, 12, "paint", srgb("5A3A26"), frame=frame)
    PLANT_BUILDERS[variant](b, frame, random.Random(seed))


def step_ladder(b: Builder, frame: Matrix, **options) -> None:
    for side in (-0.25, 0.25):
        wood_beam(b, frame, (side, -0.36, 0.0), (side, -0.05, 1.44), 0.05, 0.035, WOOD_BODY)
        wood_beam(b, frame, (side, 0.36, 0.0), (side, 0.06, 1.44), 0.04, 0.03, WOOD_DEEP)

    for rung_z in (0.3, 0.6, 0.9, 1.2):
        rung_y = -0.36 + 0.31 * rung_z / 1.44
        wood_box(b, frame, (-0.25, rung_y - 0.06, rung_z - 0.015), (0.25, rung_y + 0.06, rung_z + 0.015), WOOD_TOP, light=True)

    wood_box(b, frame, (-0.28, -0.1, 1.44), (0.28, 0.12, 1.5), WOOD_TOP, light=True)
    wood_box(b, frame, (-0.2, 0.0, 0.32), (0.2, 0.03, 0.35), WOOD_DEEP)


# ---------- lighting ----------

def lantern_body(b: Builder, frame: Matrix, center: tuple) -> None:
    """Small iron lantern around center (x, y, z): glowing core, four corner posts, cap and base."""
    center_x, center_y, center_z = center
    b.cylinder((center_x, center_y, center_z - 0.1), 0.065, 0.2, 6, "glow_warm", WHITE, frame=frame)

    for corner_x, corner_y in itertools.product((-0.065, 0.065), repeat=2):
        metal_box(b, frame, (center_x + corner_x - 0.008, center_y + corner_y - 0.008, center_z - 0.11), (center_x + corner_x + 0.008, center_y + corner_y + 0.008, center_z + 0.1), IRON)

    b.cylinder((center_x, center_y, center_z - 0.12), 0.09, 0.025, 6, "metal", srgb(IRON), frame=frame)
    b.cylinder((center_x, center_y, center_z + 0.1), 0.1, 0.07, 6, "metal", srgb(IRON), top_radius=0.02, frame=frame)
    b.sphere((center_x, center_y, center_z + 0.185), 0.022, "metal", srgb(IRON), frame=frame, segments=5)


def wall_lantern(b: Builder, frame: Matrix, **options) -> None:
    mount_z, wall_y = 1.85, 0.16
    lantern_y = wall_y - 0.22
    metal_box(b, frame, (-0.03, wall_y - 0.015, mount_z - 0.14), (0.03, wall_y, mount_z + 0.14), IRON)
    metal_box(b, frame, (-0.012, lantern_y, mount_z + 0.1), (0.012, wall_y - 0.015, mount_z + 0.125), IRON)
    metal_box(b, frame, (-0.012, lantern_y - 0.012, mount_z + 0.035), (0.012, lantern_y + 0.012, mount_z + 0.125), IRON)
    metal_box(b, frame, (-0.012, wall_y - 0.07, mount_z - 0.1), (0.012, wall_y - 0.015, mount_z - 0.075), IRON)
    lantern_body(b, frame, (0.0, lantern_y, mount_z - 0.1))


def wheel_chandelier(b: Builder, frame: Matrix, **options) -> None:
    wheel_z = -0.9
    ring(b, (0.0, 0.0, wheel_z), 0.5, 0.03, "metal", IRON, frame, sides=14, tube_sides=4)
    ring(b, (0.0, 0.0, wheel_z + 0.02), 0.27, 0.016, "metal", IRON, frame, sides=12, tube_sides=4)
    lathe(b, [(0.001, wheel_z - 0.06), (0.05, wheel_z - 0.05), (0.09, wheel_z - 0.01), (0.07, wheel_z + 0.03), (0.04, wheel_z + 0.1), (0.001, wheel_z + 0.12)], 8, "metal", BRASS, frame)

    for link in range(10):
        ring(b, (0.0, 0.0, -0.06 - link * 0.07), 0.032, 0.007, "metal", IRON, frame @ Matrix.Rotation(math.pi / 2.0 * (link % 2), 4, "Z"), sides=6, tube_sides=3, axis="X")

    for degrees in range(0, 360, 90):
        spoke_end = (0.5 * math.cos(math.radians(degrees)), 0.5 * math.sin(math.radians(degrees)), wheel_z)
        b.beam((0.0, 0.0, wheel_z), spoke_end, 0.03, 0.03, "metal", srgb(IRON), frame=frame)
        b.beam((0.0, 0.0, -0.1), spoke_end, 0.012, 0.012, "metal", srgb(IRON), frame=frame)

    for degrees in range(0, 360, 45):
        candle_x, candle_y = 0.5 * math.cos(math.radians(degrees)), 0.5 * math.sin(math.radians(degrees))
        b.cylinder((candle_x, candle_y, wheel_z + 0.03), 0.04, 0.02, 8, "metal", srgb(IRON), top_radius=0.03, frame=frame)
        b.cylinder((candle_x, candle_y, wheel_z + 0.05), 0.026, 0.13, 6, "paint", srgb("F2E6CF"), frame=frame)
        b.cylinder((candle_x, candle_y, wheel_z + 0.18), 0.024, 0.08, 4, "glow_warm", WHITE, top_radius=0.003, frame=frame)


def hanging_lantern(b: Builder, frame: Matrix, **options) -> None:
    """Lantern on a chain of round links with a ceiling rosette and a decorative bracket under the cap."""
    ring(b, (0.0, 0.0, -0.03), 0.04, 0.008, "metal", IRON, frame, sides=8, tube_sides=3)

    for link in range(5):
        ring(b, (0.0, 0.0, -0.1 - link * 0.12), 0.026, 0.006, "metal", IRON, frame @ Matrix.Rotation(math.pi / 2.0 * (link % 2), 4, "Z"), sides=6, tube_sides=3, axis="X")

    b.cylinder((0.0, 0.0, -0.72), 0.03, 0.04, 6, "metal", srgb(IRON), top_radius=0.012, frame=frame)
    lantern_body(b, frame, (0.0, 0.0, -0.95))


def hook_nothing(b: Builder, frame: Matrix, hook_x: float, generator: random.Random) -> None:
    return None


def hook_herbs(b: Builder, frame: Matrix, hook_x: float, generator: random.Random) -> None:
    b.cylinder((hook_x, 0.05, -1.0), 0.07, 0.36, 5, "paint", srgb(generator.choice(HERB_PALETTE)), top_radius=0.015, frame=frame)
    b.cylinder((hook_x, 0.05, -0.68), 0.02, 0.06, 5, "paint", srgb("8B5A3C"), frame=frame)


def hook_sausages(b: Builder, frame: Matrix, hook_x: float, generator: random.Random) -> None:
    for link in range(3):
        b.cylinder((hook_x, 0.05, -0.8 - link * 0.14), 0.032, 0.13, 6, "paint", srgb(generator.choice(("B5533F", "C9483B", "9A4A3A"))), frame=frame)

    b.cylinder((hook_x, 0.05, -0.68), 0.01, 0.1, 4, "paint", srgb("F2E6CF"), frame=frame)


HOOK_GOODS = {"hooks": hook_nothing, "herbs": hook_herbs, "sausages": hook_sausages}


def ceiling_beam_hooks(b: Builder, frame: Matrix, variant: str = "hooks", seed: int = 1, **options) -> None:
    generator = random.Random(seed)
    wood_box(b, frame, (-1.0, -0.14, -0.2), (1.0, 0.15, 0.0), WOOD_BODY)
    metal_box(b, frame, (-1.0, -0.15, -0.1), (1.0, -0.14, -0.08), IRON)

    for hook_x in (-0.75, -0.25, 0.25, 0.75):
        metal_box(b, frame, (hook_x - 0.006, -0.006, -0.62), (hook_x + 0.006, 0.006, -0.2), IRON)
        metal_box(b, frame, (hook_x - 0.006, -0.006, -0.66), (hook_x + 0.006, 0.05, -0.64), IRON)
        metal_box(b, frame, (hook_x - 0.006, 0.044, -0.66), (hook_x + 0.006, 0.05, -0.58), IRON)
        HOOK_GOODS[variant](b, frame, hook_x, generator)


# ---------- boards and signs ----------

def notice_board(b: Builder, frame: Matrix, seed: int = 1, **options) -> None:
    generator = random.Random(seed)
    bottom, top, half_width = 1.0, 1.9, 0.6
    paint_box(b, frame, (-half_width + 0.06, 0.0, bottom + 0.06), (half_width - 0.06, 0.04, top - 0.06), "D9A25F")

    for low, high in (((-half_width, -0.04, bottom), (half_width, 0.04, bottom + 0.06)), ((-half_width, -0.04, top - 0.06), (half_width, 0.04, top)), ((-half_width, -0.04, bottom + 0.06), (-half_width + 0.06, 0.04, top - 0.06)), ((half_width - 0.06, -0.04, bottom + 0.06), (half_width, 0.04, top - 0.06))):
        bevel_box(b, frame, low, high, WOOD_DEEP, bevel=0.012)

    for corner_x, corner_z in itertools.product((-half_width + 0.03, half_width - 0.03), (bottom + 0.03, top - 0.03)):
        b.cylinder((corner_x, -0.04, corner_z), 0.012, 0.008, 6, "metal", srgb(BRASS), frame=frame, axis="Y")

    for column, row in itertools.product(range(3), range(2)):
        paper_x = -0.38 + column * 0.38 + generator.uniform(-0.05, 0.05)
        paper_z = bottom + 0.27 + row * 0.4 + generator.uniform(-0.04, 0.04)
        width, height = generator.uniform(0.2, 0.3), generator.uniform(0.24, 0.34)
        paint_box(b, frame, (paper_x - width / 2.0, -0.012, paper_z - height / 2.0), (paper_x + width / 2.0, 0.0, paper_z + height / 2.0), generator.choice(PAPER_PALETTE))
        paint_box(b, frame, (paper_x - 0.012, -0.02, paper_z + height / 2.0 - 0.03), (paper_x + 0.012, -0.012, paper_z + height / 2.0 - 0.006), "C9483B")
        paint_box(b, frame, (paper_x - width * 0.35, -0.014, paper_z - height * 0.1), (paper_x + width * 0.35, -0.012, paper_z - height * 0.1 + 0.015), "5A4A5E")
        paint_box(b, frame, (paper_x - width * 0.3, -0.014, paper_z - height * 0.3), (paper_x + width * 0.2, -0.012, paper_z - height * 0.3 + 0.012), "5A4A5E")


def price_board(b: Builder, frame: Matrix, seed: int = 1, **options) -> None:
    generator = random.Random(seed)

    for post_x in (-0.3, 0.26):
        wood_box(b, frame, (post_x, -0.025, 0.0), (post_x + 0.04, 0.025, 1.1), WOOD_BODY)
        wood_box(b, frame, (post_x - 0.04, -0.15, 0.0), (post_x + 0.08, 0.15, 0.05), WOOD_DEEP)

    paint_box(b, frame, (-0.26, -0.015, 0.45), (0.26, 0.015, 1.05), "2E4A5A")
    wood_box(b, frame, (-0.26, -0.02, 0.43), (0.26, 0.02, 0.45), WOOD_TOP, light=True)
    wood_box(b, frame, (-0.3, -0.03, 1.05), (0.3, 0.03, 1.1), WOOD_TOP, light=True)
    paint_box(b, frame, (-0.16, -0.02, 0.94), (0.16, -0.015, 0.98), "F2E6CF")

    for row in range(4):
        line_z = 0.82 - row * 0.1
        paint_box(b, frame, (-0.2, -0.02, line_z), (-0.2 + generator.uniform(0.18, 0.3), -0.015, line_z + 0.025), "F2E6CF")
        paint_box(b, frame, (0.14, -0.02, line_z), (0.22, -0.015, line_z + 0.025), "F5D68A")


# ---------- seating ----------

def bench_long(b: Builder, frame: Matrix, tint: str = None, **options) -> None:
    """Plank bench: bevelled seat with a moulded edge, scalloped trestle ends, pegged stretcher."""
    bevel_box(b, frame, (-0.9, -0.2, 0.43), (0.9, 0.2, 0.5), tint or WOOD_TOP, bevel=0.012, light=True)
    run_profile(b, frame, -0.88, 0.88, cornice_profile(-0.18, 0.4, 0.02, 0.04), WOOD_DEEP)
    foot = [(-0.17, 0.0), (-0.1, 0.0), (-0.085, 0.1), (0.085, 0.1), (0.1, 0.0), (0.17, 0.0), (0.17, 0.43), (-0.17, 0.43)]

    for leg_x in (-0.78, 0.7):
        b.side_prism(foot, leg_x, leg_x + 0.08, "wood", srgb(WOOD_BODY), frame=frame, uv=WOOD_LIGHT_UV)

    bevel_box(b, frame, (-0.72, -0.03, 0.17), (0.72, 0.03, 0.24), WOOD_DEEP, bevel=0.01)

    for peg_x in (-0.7, 0.7):
        b.cylinder((peg_x, -0.035, 0.205), 0.014, 0.012, 6, "wood", srgb(WOOD_TOP), frame=frame, axis="Y")


def stool_round(b: Builder, frame: Matrix, tint: str = None, **options) -> None:
    """Three-legged stool: dished round seat with a rolled edge, splayed legs and a ring stretcher."""
    lathe(b, [(0.001, 0.4), (0.15, 0.4), (0.19, 0.41), (0.2, 0.435), (0.19, 0.46), (0.12, 0.455), (0.001, 0.45)], 12, "wood", tint or WOOD_TOP, frame, uv=WOOD_LIGHT_UV)

    for degrees in (90, 210, 330):
        foot = (0.155 * math.cos(math.radians(degrees)), 0.155 * math.sin(math.radians(degrees)), 0.0)
        top = (0.1 * math.cos(math.radians(degrees)), 0.1 * math.sin(math.radians(degrees)), 0.42)
        wood_beam(b, frame, foot, top, 0.04, 0.04, WOOD_BODY)

    ring(b, (0.0, 0.0, 0.18), 0.131, 0.012, "wood", WOOD_DEEP, frame, sides=12, tube_sides=4)


def chair(b: Builder, frame: Matrix, tint: str = None, **options) -> None:
    """Dining chair: tapered front legs, tall back posts, piped cushion, vase-shaped splat under a crest rail."""
    for leg_x, leg_y in itertools.product((-0.2, 0.16), (-0.2, 0.16)):
        height = 0.9 if leg_y > 0 else 0.42
        bevel_box(b, frame, (leg_x, leg_y, 0.0), (leg_x + 0.04, leg_y + 0.04, height), WOOD_BODY, bevel=0.006)

    bevel_box(b, frame, (-0.21, -0.21, 0.4), (0.21, 0.21, 0.45), WOOD_TOP, bevel=0.01, light=True)
    bevel_box(b, frame, (-0.19, -0.19, 0.45), (0.19, 0.17, 0.49), tint or "B03A48", bevel=0.015, material="paint")

    for rail_y in (-0.18, 0.18):
        bevel_box(b, frame, (-0.17, rail_y - 0.008, 0.2), (0.17, rail_y + 0.008, 0.24), WOOD_DEEP, bevel=0.004)

    splat = [(-0.045, 0.5), (0.045, 0.5), (0.065, 0.58), (0.04, 0.66), (0.075, 0.76), (-0.075, 0.76), (-0.04, 0.66), (-0.065, 0.58)]
    b.prism(splat, 0.18, 0.2, "wood", srgb(WOOD_TOP), frame=frame, uv=WOOD_LIGHT_UV)
    bevel_box(b, frame, (-0.2, 0.17, 0.78), (0.2, 0.21, 0.9), WOOD_TOP, bevel=0.012, light=True)
    bevel_box(b, frame, (-0.2, 0.17, 0.5), (0.2, 0.21, 0.54), WOOD_DEEP, bevel=0.006)


# ---------- banner, stairs, railing ----------

def wall_banner(b: Builder, frame: Matrix, tint: str = None, **options) -> None:
    frame = frame @ Matrix.Translation((0.0, -0.03, 0.0))  # wall at y = +0.035
    cloth = tint or "B03A48"
    swallow_tail = [(-0.28, 2.5), (0.28, 2.5), (0.28, 1.1), (0.0, 1.32), (-0.28, 1.1)]
    b.prism(swallow_tail, 0.035, 0.045, "paint", srgb(cloth), frame=frame)
    b.prism([(-0.28, 2.3), (0.28, 2.3), (0.28, 2.36), (-0.28, 2.36)], 0.025, 0.035, "paint", srgb("E8C14F"), frame=frame)
    b.prism([(0.0, 1.62), (0.15, 1.9), (0.0, 2.18), (-0.15, 1.9)], 0.025, 0.035, "paint", srgb("F2E6CF"), frame=frame)
    b.prism([(0.0, 1.76), (0.07, 1.9), (0.0, 2.04), (-0.07, 1.9)], 0.015, 0.025, "paint", srgb(cloth), frame=frame)
    wood_cylinder(b, frame, (-0.33, 0.03, 2.55), 0.02, 0.66, 6, WOOD_DEEP, axis="X")

    for finial_x in (-0.33, 0.33):
        b.sphere((finial_x, 0.03, 2.55), 0.032, "metal", srgb(BRASS), frame=frame, segments=6)


STAIR_STEPS, STAIR_RISE, STAIR_RUN, STAIR_HALF_LENGTH = 16, 0.2, 0.29625, 2.37


def stairs_straight(b: Builder, frame: Matrix, **options) -> None:
    """Bottom at the customer side (-Y), climbing toward the back; handrail on the +X side."""
    heights = [(step + 1) * STAIR_RISE for step in range(STAIR_STEPS)]
    fronts = [-STAIR_HALF_LENGTH + step * STAIR_RUN for step in range(STAIR_STEPS)]
    profile = [(-STAIR_HALF_LENGTH, 0.0), (STAIR_HALF_LENGTH, 0.0)]
    profile += [point for step in reversed(range(STAIR_STEPS)) for point in ((fronts[step] + STAIR_RUN, heights[step]), (fronts[step], heights[step]))]
    b.side_prism(profile, -0.7, 0.7, "wood", srgb(WOOD_BODY), frame=frame, uv=WOOD_LIGHT_UV)

    for front, height in zip(fronts, heights):
        wood_box(b, frame, (-0.7, front - 0.03, height), (0.7, front + STAIR_RUN, height + 0.03), WOOD_TOP, light=True)

    rail_x = 0.62
    post_steps = (0, 5, 10, 15)

    for step in range(STAIR_STEPS):
        if step in post_steps or step % 2 == 0:
            thickness = 0.04 if step in post_steps else 0.014
            base = heights[step] + 0.03
            centre = fronts[step] + STAIR_RUN / 2.0
            wood_box(b, frame, (rail_x - thickness, centre - thickness, base), (rail_x + thickness, centre + thickness, base + 0.95), WOOD_BODY)

    rail_start = (rail_x, fronts[0] + STAIR_RUN / 2.0, heights[0] + 0.98)
    rail_end = (rail_x, fronts[-1] + STAIR_RUN / 2.0, heights[-1] + 0.98)
    wood_beam(b, frame, rail_start, rail_end, 0.07, 0.06, WOOD_TOP, light=True)


def railing(b: Builder, frame: Matrix, tint: str = None, **options) -> None:
    for post_x in (-0.96, -0.02, 0.92):
        wood_box(b, frame, (post_x, -0.04, 0.0), (post_x + 0.08, 0.04, 1.0), WOOD_BODY)

    wood_box(b, frame, (-1.0, -0.05, 0.93), (1.0, 0.05, 1.0), tint or WOOD_TOP, light=True)
    wood_box(b, frame, (-0.96, -0.02, 0.4), (0.96, 0.02, 0.46), WOOD_BODY)

    for baluster_x in [-1.0 + step * 0.125 for step in range(1, 16)]:
        if abs(baluster_x) > 0.07:
            wood_box(b, frame, (baluster_x - 0.015, -0.015, 0.0), (baluster_x + 0.015, 0.015, 0.93), WOOD_DEEP)


def wainscot_a(b: Builder, frame: Matrix, tint: str = None, **options) -> None:
    """Panelled dado 2.0 m wide, 1.05 m tall, flush against the wall: skirting, stiles, raised panels, chair rail.
    The backing reaches 0.068 behind the origin because on_wall leaves the usual 3 cm gap to the wall."""
    body = tint or WOOD_BODY
    wood_box(b, frame, (-1.0, 0.0, 0.0), (1.0, 0.068, 1.05), WOOD_DEEP)
    run_profile(b, frame, -1.0, 1.0, base_profile(0.0, 0.0, 0.04, 0.14), WOOD_DEEP)
    run_profile(b, frame, -1.0, 1.0, cornice_profile(0.0, 0.97, 0.04, 0.08), WOOD_TOP)
    bevel_box(b, frame, (-1.0, -0.025, 0.86), (1.0, 0.0, 0.97), body, bevel=0.006, light=True)

    for stile_x in (-0.95, 0.0, 0.95):
        bevel_box(b, frame, (stile_x - 0.05, -0.025, 0.14), (stile_x + 0.05, 0.0, 0.88), body, bevel=0.006, light=True)

    for panel_from, panel_to in ((-0.9, -0.06), (0.06, 0.9)):
        raised_panel(b, frame, panel_from, panel_to, 0.2, 0.82, -0.002, body, border=0.045, depth=0.014)


def doorway_lintel_a(b: Builder, frame: Matrix, width: float = 2.0, height: float = 4.8, **options) -> None:
    """Hanging wall infill above a doorway cut in an inner partition (0.3 thick): stone over a segmental arch with a
    moulded ring and keystone on both faces, plus a pilaster strip down each jamb. z = 0 is the ceiling."""
    half = width / 2.0
    drop, rise = 1.7, 0.5
    radius = (half * half + rise * rise) / (2.0 * rise)
    arc = [(u, -drop + math.sqrt(radius * radius - u * u) - (radius - rise)) for u in [-half + width * index / 12.0 for index in range(13)]]
    ring = arc + [(u, z + 0.16) for u, z in reversed(arc)]
    crown = arc[6][1]

    b.prism([(-half, 0.0), (half, 0.0)] + list(reversed(arc)), -0.15, 0.15, "stone", srgb(STONE["media"]), frame=frame)

    for face, direction in ((-0.15, -1.0), (0.15, 1.0)):
        b.prism(ring, min(face, face + direction * 0.02), max(face, face + direction * 0.02), "trim", srgb(STONE["clara"]), frame=frame, uv=SMOOTH_UV)
        b.prism([(-0.16, crown + 0.2), (0.16, crown + 0.2), (0.11, crown - 0.05), (-0.11, crown - 0.05)], min(face, face + direction * 0.04), max(face, face + direction * 0.04), "trim", srgb(STONE["clara"]), frame=frame, uv=SMOOTH_UV)

    for jamb_x, face_y in itertools.product((-half - 0.14, half), (-0.18, 0.15)):
        bevel_box(b, frame, (jamb_x, face_y, -height + 0.3), (jamb_x + 0.14, face_y + 0.03, -drop - 0.1), WOOD_DEEP, bevel=0.008)
        bevel_box(b, frame, (jamb_x - 0.03, face_y - 0.02, -height), (jamb_x + 0.17, face_y + 0.05, -height + 0.3), WOOD_DEEP, bevel=0.012)
        bevel_box(b, frame, (jamb_x - 0.03, face_y - 0.02, -drop - 0.1), (jamb_x + 0.17, face_y + 0.05, -drop + 0.05), WOOD_TOP, bevel=0.012)


def timber_screen_a(b: Builder, frame: Matrix, variant: str = "lattice", tint: str = None, **options) -> None:
    """Free-standing screen 2.0 m wide, 2.3 m tall, 0.14 deep: turned posts with ball finials, a panelled kick board,
    and either a diagonal timber lattice (lattice), iron spear-topped bars (bars) or raised panels (panels)."""
    body = tint or WOOD_BODY
    top = 2.2

    for post_x in (-0.95, 0.95):
        turned_leg(b, frame, post_x, 0.0, top, 0.055, WOOD_DEEP, "column")
        b.sphere((post_x, 0.0, top + 0.07), 0.055, "wood", srgb(WOOD_DEEP), frame=frame, segments=7)

    bevel_box(b, frame, (-1.0, -0.06, 0.0), (1.0, 0.06, 0.12), WOOD_DEEP, bevel=0.01)
    bevel_box(b, frame, (-0.9, -0.05, 0.12), (0.9, 0.05, 0.9 if variant != "panels" else top - 0.1), body, bevel=0.01)

    for panel_from in (-0.88, -0.28, 0.32):
        raised_panel(b, frame, panel_from, panel_from + 0.56, 0.2, 0.82 if variant != "panels" else 1.1, -0.05, WOOD_TOP, border=0.05)

    if variant == "panels":
        for panel_from in (-0.88, -0.28, 0.32):
            raised_panel(b, frame, panel_from, panel_from + 0.56, 1.2, top - 0.2, -0.05, WOOD_TOP, border=0.05)

        bevel_box(b, frame, (-1.0, -0.07, top - 0.1), (1.0, 0.07, top), WOOD_TOP, bevel=0.012, light=True)
        return

    bevel_box(b, frame, (-0.9, -0.05, 0.9), (0.9, 0.05, 0.98), WOOD_TOP, bevel=0.01, light=True)
    bevel_box(b, frame, (-1.0, -0.07, top - 0.1), (1.0, 0.07, top), WOOD_TOP, bevel=0.012, light=True)

    if variant == "bars":
        for bar_index in range(17):
            bar_x = -0.85 + bar_index * 0.10625
            b.cylinder((bar_x, 0.0, 0.98), 0.012, top - 1.08, 6, "metal", srgb(IRON), frame=frame)
            b.cylinder((bar_x, 0.0, top - 0.14), 0.02, 0.05, 6, "metal", srgb(IRON), top_radius=0.002, frame=frame)

        for rail_z in (1.35, 1.8):
            metal_box(b, frame, (-0.9, -0.014, rail_z), (0.9, 0.014, rail_z + 0.03), IRON)

        return

    cell_width, cell_height = 0.45, (top - 0.1 - 0.98) / 2.0

    for column, row in itertools.product(range(4), range(2)):
        x_from, z_from = -0.9 + column * cell_width, 0.98 + row * cell_height
        wood_beam(b, frame, (x_from, 0.0, z_from), (x_from + cell_width, 0.0, z_from + cell_height), 0.035, 0.03, body, light=True)
        wood_beam(b, frame, (x_from + cell_width, 0.0, z_from), (x_from, 0.0, z_from + cell_height), 0.035, 0.03, WOOD_TOP, light=True)

    for rail_z in (0.98 + cell_height - 0.02,):
        bevel_box(b, frame, (-0.9, -0.04, rail_z), (0.9, 0.04, rail_z + 0.04), WOOD_DEEP, bevel=0.008)


def forge_floor_a(b: Builder, frame: Matrix, **options) -> None:
    """Slate apron 4.2 x 3.2 round a hearth: flagstones in two shades with a scorched middle, just above the floor."""
    columns, rows = 6, 4
    slab_width, slab_depth = 4.2 / columns, 3.2 / rows

    for column, row in itertools.product(range(columns), range(rows)):
        shade = ("4A4458", "5A5368", "3F3A4E", "665E78")[(column * 3 + row * 5) % 4]
        x_from, y_from = -2.1 + column * slab_width, -1.6 + row * slab_depth
        bevel_box(b, frame, (x_from + 0.012, y_from + 0.012, 0.0), (x_from + slab_width - 0.012, y_from + slab_depth - 0.012, 0.022), shade, bevel=0.008, material="stone")

    paint_box(b, frame, (-0.7, 0.2, 0.022), (0.7, 1.4, 0.024), "2B2236")


def guild_hearth_a(b: Builder, frame: Matrix, **options) -> None:
    """Great hearth of dressed stone, 2.6 wide, against a wall: raised hearthstone, arched firebox with logs and
    andirons, a heavy timber mantel with candlesticks, and a tapering hood rising to the ceiling beams."""
    stone, trim = "D9C8A8", "EFE3C8"
    mouth_half, mouth_top = 0.75, 1.5

    bevel_box(b, frame, (-1.3, -0.62, 0.0), (1.3, 0.62, 0.12), "B9AA92", bevel=0.015, material="stone")
    bevel_box(b, frame, (-1.3, 0.2, 0.12), (-mouth_half - 0.05, 0.62, 2.0), stone, bevel=0.012, material="stone")
    bevel_box(b, frame, (mouth_half + 0.05, 0.2, 0.12), (1.3, 0.62, 2.0), stone, bevel=0.012, material="stone")
    bevel_box(b, frame, (-1.3, 0.2, 1.5), (1.3, 0.62, 2.0), stone, bevel=0.012, material="stone")
    b.prism(arch_outline_a(mouth_half + 0.14, 0.12, 1.1), 0.18, 0.22, "trim", srgb(trim), frame=frame, uv=SMOOTH_UV)
    b.prism(arch_outline_a(mouth_half, 0.12, 1.1), 0.2, 0.62, "paint", srgb("2B2236"), frame=frame)
    b.box((-mouth_half, 0.5, 0.12), (mouth_half, 0.62, 0.7), "glow_ember", WHITE, frame=frame)

    for log_y, log_z, log_x in ((0.0, 0.3, -0.2), (0.12, 0.34, 0.15), (0.3, 0.3, 0.0)):
        wood_cylinder(b, frame, (log_x - 0.35, log_y + 0.1, log_z), 0.07, 0.7, 7, "6B3E2A", axis="X")

    for andiron_x in (-0.5, 0.5):
        metal_box(b, frame, (andiron_x - 0.02, -0.15, 0.12), (andiron_x + 0.02, 0.5, 0.17), IRON)
        b.cylinder((andiron_x, -0.15, 0.17), 0.02, 0.38, 6, "metal", srgb(IRON), frame=frame)
        b.sphere((andiron_x, -0.15, 0.58), 0.035, "metal", srgb(BRASS), frame=frame, segments=6)

    bevel_box(b, frame, (-1.45, -0.1, 2.0), (1.45, 0.62, 2.14), WOOD_DEEP, bevel=0.02)
    run_profile(b, frame, -1.45, 1.45, cornice_profile(-0.1, 1.94, 0.08, 0.1), WOOD_TOP)

    for candle_x in (-1.0, -0.55, 0.55, 1.0):
        lathe(b, [(0.001, 2.14), (0.05, 2.14), (0.03, 2.19), (0.015, 2.34), (0.03, 2.38), (0.001, 2.38)], 8, "metal", BRASS, frame, base=(candle_x, 0.3, 0.0))
        b.cylinder((candle_x, 0.3, 2.38), 0.016, 0.12, 6, "paint", srgb("F2E6CF"), frame=frame)
        b.cylinder((candle_x, 0.3, 2.5), 0.012, 0.05, 4, "glow_warm", WHITE, top_radius=0.002, frame=frame)

    hood_low, hood_high = 2.14, 6.4
    hull_points = [(x, y, hood_low) for x, y in itertools.product((-1.3, 1.3), (0.0, 0.62))] + [(x, y, hood_high) for x, y in itertools.product((-0.55, 0.55), (0.38, 0.62))]
    solid_hull(b, hull_points, "stone", stone, frame)

    for course_z in (3.3, 4.5, 5.7):
        shrink = 1.0 - (course_z - hood_low) / (hood_high - hood_low) * 0.58
        bevel_box(b, frame, (-1.3 * shrink - 0.04, 0.0 + (1.0 - shrink) * 0.38 - 0.04, course_z), (1.3 * shrink + 0.04, 0.62, course_z + 0.1), trim, bevel=0.012, material="stone")

    bevel_box(b, frame, (-0.62, 0.34, hood_high), (0.62, 0.62, hood_high + 0.2), trim, bevel=0.014, material="stone")


def arch_outline_a(half_width: float, bottom: float, spring: float, segments: int = 10) -> list:
    """Round-headed (u, z) outline: jambs from bottom to spring, half circle above."""
    arc = [(half_width * math.cos(math.pi * index / segments), spring + half_width * math.sin(math.pi * index / segments)) for index in range(segments + 1)]

    return [(-half_width, bottom), (half_width, bottom)] + arc


def dagger_a(b: Builder, frame: Matrix, x: float, y: float, z: float, degrees: float, blade_tint: str = "E4ECF5") -> None:
    """Small dagger lying flat at (x, y, z), pointing along `degrees` around Z (0 = +Y): blade, guard, grip, pommel."""
    turn = Matrix.Rotation(math.radians(degrees), 4, "Z") @ Matrix.Translation((0.0, 0.0, 0.0))
    local = frame @ Matrix.Translation((x, y, z)) @ turn
    solid_hull(b, [(0.0, 0.06, 0.004), (-0.014, 0.06, 0.004), (0.014, 0.06, 0.004), (0.0, 0.2, 0.004), (-0.014, 0.075, 0.0), (0.014, 0.075, 0.0), (0.0, 0.075, 0.008)], "metal", blade_tint, local)
    b.box((-0.03, 0.05, 0.0), (0.03, 0.065, 0.016), "metal", srgb(BRASS), frame=local)
    b.cylinder((0.0, -0.04, 0.008), 0.009, 0.09, 6, "paint", srgb("6B3E2A"), frame=local, axis="Y")
    b.sphere((0.0, -0.045, 0.008), 0.014, "metal", srgb(BRASS), frame=local, segments=6)


def display_daggers(b: Builder, frame: Matrix, generator: random.Random, top: float) -> None:
    """Fan of daggers on a red velvet cloth."""
    paint_box(b, frame, (-0.55, -0.3, top), (0.55, 0.3, top + 0.012), "A8323C")

    for index in range(7):
        dagger_a(b, frame, -0.45 + index * 0.15, -0.2 + abs(index - 3) * 0.015, top + 0.012, -12.0 + index * 4.0 + generator.uniform(-2.0, 2.0), "E4ECF5" if index % 2 else "CDD8E6")


def display_ingots(b: Builder, frame: Matrix, generator: random.Random, top: float) -> None:
    """Two pyramids of metal bars."""
    for centre_x, tone in ((-0.3, "B4C4DC"), (0.3, "D9824A")):
        for row, count in enumerate((3, 2, 1)):
            for index in range(count):
                low = top + row * 0.05
                span = (index - (count - 1) / 2.0) * 0.17
                points = [(centre_x + span + sx * 0.08, sy * 0.06, low) for sx, sy in itertools.product((-1, 1), repeat=2)] + [(centre_x + span + sx * 0.065, sy * 0.045, low + 0.05) for sx, sy in itertools.product((-1, 1), repeat=2)]
                solid_hull(b, points, "metal", tone if (row + index) % 2 else GOLD, frame)


TABLE_GOODS.update({"daggers": display_daggers, "ingots": display_ingots})


def dais_a(b: Builder, frame: Matrix, width: float = 3.6, depth: float = 2.4, carpet: str = "A8323C", **options) -> None:
    """Low display dais 0.3 m high: plank top on a stone plinth with a moulded edge, two wide steps on the customer
    side (-Y), a carpet runner with a gold border and brass corner studs. Carries its own collider so props on it can
    be put at z = 0.35 without a footprint clash; it is not 'solid' in the PROPS sense."""
    half_w, half_d, top = width / 2.0, depth / 2.0, 0.3
    step_depth = 0.34
    bevel_box(b, frame, (-half_w, -half_d + step_depth * 2, 0.0), (half_w, half_d, 0.12), WOOD_DEEP, bevel=0.02)
    bevel_box(b, frame, (-half_w + 0.04, -half_d + step_depth * 2 + 0.04, 0.12), (half_w - 0.04, half_d - 0.04, top - 0.02), WOOD_BODY, bevel=0.01, light=True)
    bevel_box(b, frame, (-half_w, -half_d + step_depth * 2 - 0.02, top - 0.04), (half_w, half_d, top), WOOD_TOP, bevel=0.012, light=True)
    run_profile(b, frame, -half_w, half_w, cornice_profile(-half_d + step_depth * 2 - 0.02, 0.0, 0.02, 0.03), WOOD_DEEP)

    for step_index in range(2):
        low = -half_d + step_depth * step_index
        step_top = 0.1 + 0.1 * step_index
        bevel_box(b, frame, (-half_w + 0.3 * (1 - step_index), low, 0.0), (half_w - 0.3 * (1 - step_index), low + step_depth, step_top), WOOD_BODY, bevel=0.015)
        bevel_box(b, frame, (-half_w + 0.3 * (1 - step_index) + 0.02, low - 0.01, step_top - 0.03), (half_w - 0.3 * (1 - step_index) - 0.02, low + step_depth, step_top), WOOD_TOP, bevel=0.008, light=True)

    runner_half = min(0.55, half_w * 0.3)
    paint_box(b, frame, (-runner_half, -half_d + 0.02, 0.1 + 0.001), (runner_half, -half_d + step_depth, 0.1 + 0.006), carpet)
    paint_box(b, frame, (-runner_half, -half_d + step_depth + 0.02, 0.2 + 0.001), (runner_half, -half_d + step_depth * 2, 0.2 + 0.006), carpet)
    paint_box(b, frame, (-half_w + 0.35, -half_d + step_depth * 2 + 0.2, top), (half_w - 0.35, half_d - 0.2, top + 0.008), carpet)
    paint_box(b, frame, (-half_w + 0.35, -half_d + step_depth * 2 + 0.2, top + 0.008), (half_w - 0.35, -half_d + step_depth * 2 + 0.26, top + 0.011), GOLD)
    paint_box(b, frame, (-half_w + 0.35, half_d - 0.26, top + 0.008), (half_w - 0.35, half_d - 0.2, top + 0.011), GOLD)

    for stud_x, stud_y in itertools.product((-half_w + 0.12, half_w - 0.12), (-half_d + step_depth * 2 + 0.12, half_d - 0.12)):
        b.sphere((stud_x, stud_y, top), 0.028, "metal", srgb(BRASS), frame=frame, segments=6)

    b.collider((-half_w, -half_d, 0.0), (half_w, half_d, top), frame)


DRESS_STYLES_A = {
    "dress": ("E56C94", "FFE3A0"),
    "gown": ("5B7BD6", "F4EFE6"),
    "cloak": ("3C8F6B", "E8B84F"),
}


def dress_form_a(b: Builder, frame: Matrix, variant: str = "dress", tint: str = None, **options) -> None:
    """Tailor's mannequin on a turned post and tripod: padded torso under a draped dress with ruffled hem and a
    ribbon belt (dress), a long gown with a train (gown) or a hooded cloak over a linen form (cloak)."""
    colour, accent = DRESS_STYLES_A[variant]
    colour = tint or colour

    for angle in (90.0, 210.0, 330.0):
        foot = (0.27 * math.cos(math.radians(angle)), 0.27 * math.sin(math.radians(angle)), 0.0)
        wood_beam(b, frame, (0.0, 0.0, 0.3), foot, 0.045, 0.04, WOOD_DEEP)
        b.sphere(foot, 0.028, "wood", srgb(WOOD_BODY), frame=frame, segments=6)

    turned_leg(b, frame, 0.0, 0.0, 1.0, 0.032, WOOD_BODY, "baluster")
    ring(b, (0.0, 0.0, 0.3), 0.05, 0.012, "metal", BRASS, frame, sides=8, tube_sides=4)

    if variant == "cloak":
        lathe(b, [(0.2, 0.9), (0.16, 1.05), (0.19, 1.2), (0.17, 1.34), (0.09, 1.44), (0.001, 1.47)], 12, "paint", "EADFC8", place_scale(frame, 0.78))
        b.hull([(-0.2, -0.03, 1.46), (0.2, -0.03, 1.46), (-0.17, 0.12, 1.5), (0.17, 0.12, 1.5), (-0.32, 0.0, 0.5), (0.32, 0.0, 0.5), (-0.37, 0.28, 0.45), (0.37, 0.28, 0.45), (0.0, 0.24, 1.66)], "paint", srgb(colour), frame=frame)
        b.hull([(-0.12, 0.1, 1.5), (0.12, 0.1, 1.5), (-0.06, 0.2, 1.72), (0.06, 0.2, 1.72), (0.0, 0.0, 1.44)], "paint", srgb(colour), frame=frame)
        b.sphere((0.0, -0.17, 1.4), 0.04, "metal", srgb(accent), frame=frame, segments=6)
        return

    hem = 0.16 if variant == "gown" else 0.46
    hem_radius = 0.4 if variant == "gown" else 0.33
    lathe(b, [(hem_radius, hem), (0.3, 0.7), (0.15, 0.96), (0.115, 1.0), (0.17, 1.2), (0.185, 1.3), (0.14, 1.4), (0.07, 1.47), (0.001, 1.49)], 12, "paint", colour, place_scale(frame, 0.82))
    ring(b, (0.0, 0.0, hem + 0.02), hem_radius, 0.02, "paint", accent, place_scale(frame, 0.82), sides=12, tube_sides=4)
    ring(b, (0.0, 0.0, hem + 0.22), hem_radius * 0.88, 0.015, "paint", accent, place_scale(frame, 0.82), sides=12, tube_sides=4)
    ring(b, (0.0, 0.0, 1.0), 0.125, 0.015, "paint", accent, place_scale(frame, 0.82), sides=12, tube_sides=4)
    b.sphere((0.0, -0.11, 1.0), 0.032, "paint", srgb(accent), frame=frame, segments=6)
    b.cylinder((0.0, 0.0, 1.46), 0.03, 0.1, 8, "wood", srgb(WOOD_TOP), frame=frame)
    b.sphere((0.0, 0.0, 1.6), 0.07, "wood", srgb(WOOD_TOP), frame=frame, segments=8)
    ring(b, (0.0, 0.0, 1.4), 0.1, 0.012, "paint", accent, place_scale(frame, 0.82), sides=10, tube_sides=4)

    if variant == "gown":
        b.hull([(-0.22, 0.1, 0.3), (0.22, 0.1, 0.3), (-0.4, 0.5, 0.03), (0.4, 0.5, 0.03), (-0.2, 0.3, 1.0), (0.2, 0.3, 1.0)], "paint", srgb(colour), frame=frame)


def place_scale(frame: Matrix, depth_scale: float) -> Matrix:
    """Frame squashed along local Y (round forms read better a little flat from the side)."""
    return frame @ Matrix.Diagonal((1.0, depth_scale, 1.0, 1.0))


def hanging_fabrics_a(b: Builder, frame: Matrix, **options) -> None:
    """Dyed cloth hung from a pole on two chains, z = 0 at the ceiling: five bolts draped in scalloped swags with
    gilded hems, wooden finials on the pole. Looks good in any shop that sells or sews."""
    pole_z = -0.85
    colours = ("C9483B", "3561B0", "E8B84F", "5FA862", "9A5AB8")

    for chain_x in (-0.95, 0.95):
        b.cylinder((chain_x, 0.0, pole_z), 0.007, -pole_z, 6, "metal", srgb(IRON), frame=frame)
        ring(b, (chain_x, 0.0, -0.04), 0.03, 0.007, "metal", IRON, frame, sides=8, tube_sides=3, axis="Y")

    b.cylinder((-1.08, 0.0, pole_z), 0.028, 2.16, 8, "wood", srgb(WOOD_DEEP), frame=frame, axis="X")

    for finial_x in (-1.1, 1.1):
        b.sphere((finial_x, 0.0, pole_z), 0.045, "wood", srgb(WOOD_TOP), frame=frame, segments=7)

    for index, colour in enumerate(colours):
        left, right = -0.95 + index * 0.38, -0.95 + (index + 1) * 0.38 - 0.02
        drop_left, drop_right = 0.5 + 0.12 * (index % 2), 0.5 + 0.12 * ((index + 1) % 2)
        middle = (left + right) / 2.0
        swag = [(left, pole_z + 0.03), (right, pole_z + 0.03), (right, pole_z - drop_right), (middle + 0.06, pole_z - drop_right - 0.06), (middle - 0.06, pole_z - drop_left - 0.1), (left, pole_z - drop_left)]
        b.prism(swag, -0.025, 0.025, "paint", srgb(colour), frame=frame)
        b.prism([(left + 0.03, pole_z - 0.05), (middle, pole_z - 0.05), (middle - 0.02, pole_z - drop_left * 0.8), (left + 0.03, pole_z - drop_left * 0.85)], -0.04, -0.025, "paint", srgb(colours[(index + 2) % 5]), frame=frame)
        b.prism([(left, pole_z - drop_left), (right, pole_z - drop_right), (right, pole_z - drop_right - 0.03), (left, pole_z - drop_left - 0.03)], -0.027, 0.027, "metal", srgb(GOLD), frame=frame)


def bunting_a(b: Builder, frame: Matrix, **options) -> None:
    """Festive string of triangular pennants sagging between two ceiling hooks, z = 0 at the ceiling: 3.6 m of cord,
    ten two-tone flags and a tassel at each end."""
    span = 3.6
    colours = ("C9483B", "F4EFE6", "3561B0", "E8B84F", "5FA862")
    cord = [(-span / 2.0 + span * step / 20.0, -0.12 - 0.3 * math.sin(math.pi * step / 20.0)) for step in range(21)]

    for start, end in zip(cord, cord[1:]):
        b.beam((start[0], 0.0, start[1]), (end[0], 0.0, end[1]), 0.012, 0.012, "paint", srgb("8B6B4A"), frame=frame)

    for flag in range(10):
        centre_x, centre_z = cord[1 + flag * 2]
        b.prism([(centre_x - 0.13, centre_z), (centre_x + 0.13, centre_z), (centre_x, centre_z - 0.3)], -0.008, 0.008, "paint", srgb(colours[flag % 5]), frame=frame)
        b.prism([(centre_x - 0.13, centre_z), (centre_x + 0.13, centre_z), (centre_x + 0.07, centre_z - 0.1), (centre_x - 0.07, centre_z - 0.1)], -0.01, 0.01, "paint", srgb(colours[(flag + 2) % 5]), frame=frame)

    for end_x in (-span / 2.0, span / 2.0):
        b.sphere((end_x, 0.0, -0.14), 0.03, "metal", srgb(GOLD), frame=frame, segments=6)
        b.cylinder((end_x, 0.0, -0.26), 0.025, 0.12, 6, "paint", srgb("C9483B"), frame=frame, top_radius=0.005)


# @@NEW


PROPS.update(
    {
        "display_table": {"build": display_table, "size": (1.4, 0.9, 1.2), "solid": True, "clearance": 0.6, "variants": list(TABLE_GOODS)},
        "crate_stack": {"build": crate_stack, "size": (1.4, 0.9, 1.0), "solid": True},
        "crate_open": {"build": crate_open, "size": (0.7, 0.5, 0.54), "solid": True, "clearance": 0.3, "variants": list(CRATE_CONTENTS)},
        "sack_pile": {"build": sack_pile, "size": (1.2, 0.9, 0.78), "solid": True},
        "barrel_group": {"build": barrel_group, "size": (1.3, 1.0, 0.95), "solid": True},
        "rug": {"build": rug, "size": (2.0, 1.4, 0.02), "solid": False, "variants": list(RUG_COLOURS)},
        "wall_lantern": {"build": wall_lantern, "size": (0.18, 0.32, 2.0), "solid": False, "light": ((0.0, -0.06, 1.75), "FFB347", 1.2, 5.5)},
        "wheel_chandelier": {"build": wheel_chandelier, "size": (1.08, 1.08, 0.96), "solid": False, "hang": True, "light": ((0.0, 0.0, -0.85), "FFB347", 1.6, 7.0)},
        "hanging_lantern": {"build": hanging_lantern, "size": (0.2, 0.2, 1.08), "solid": False, "hang": True, "light": ((0.0, 0.0, -0.95), "FFB347", 1.0, 5.0)},
        "notice_board": {"build": notice_board, "size": (1.2, 0.08, 1.9), "solid": False, "clearance": 0.6},
        "price_board": {"build": price_board, "size": (0.68, 0.3, 1.1), "solid": True, "clearance": 0.4},
        "wicker_basket": {"build": wicker_basket, "size": (0.5, 0.5, 0.46), "solid": True, "variants": list(BASKET_CONTENTS)},
        "plant_pot": {"build": plant_pot, "size": (0.54, 0.5, 0.76), "solid": True, "variants": list(PLANT_BUILDERS)},
        "step_ladder": {"build": step_ladder, "size": (0.58, 0.76, 1.5), "solid": True},
        "chest_gold": {"build": chest_gold, "size": (0.8, 0.56, 0.84), "solid": True, "clearance": 0.5},
        "bench_long": {"build": bench_long, "size": (1.8, 0.4, 0.5), "solid": True, "clearance": 0.4},
        "stool_round": {"build": stool_round, "size": (0.38, 0.38, 0.46), "solid": True},
        "chair": {"build": chair, "size": (0.42, 0.42, 0.9), "solid": True, "clearance": 0.4},
        "wall_banner": {"build": wall_banner, "size": (0.72, 0.065, 2.6), "solid": False},
        "ceiling_beam_hooks": {"build": ceiling_beam_hooks, "size": (2.0, 0.3, 1.1), "solid": False, "hang": True, "variants": list(HOOK_GOODS)},
        "stairs_straight": {"build": stairs_straight, "size": (1.4, 4.8, 4.2), "solid": True, "clearance": 0.8, "beside_window": True},
        "railing": {"build": railing, "size": (2.0, 0.1, 1.0), "solid": True},
        "dress_form_a": {"build": dress_form_a, "size": (0.9, 1.0, 1.78), "solid": True, "variants": list(DRESS_STYLES_A)},
        "hanging_fabrics_a": {"build": hanging_fabrics_a, "size": (2.3, 0.12, 1.6), "solid": False, "hang": True},
        "bunting_a": {"build": bunting_a, "size": (3.7, 0.1, 0.8), "solid": False, "hang": True},
        "dais_a": {"build": dais_a, "size": (3.6, 2.4, 0.3), "solid": False},
        "wainscot_a": {"build": wainscot_a, "size": (2.0, 0.08, 1.05), "solid": False},
        "doorway_lintel_a": {"build": doorway_lintel_a, "size": (2.6, 0.4, 4.9), "solid": False, "hang": True},
        "timber_screen_a": {"build": timber_screen_a, "size": (2.0, 0.14, 2.3), "solid": True, "variants": ["lattice", "bars", "panels"]},
        "forge_floor_a": {"build": forge_floor_a, "size": (4.2, 3.2, 0.03), "solid": False},
        "guild_hearth_a": {"build": guild_hearth_a, "size": (2.9, 1.24, 6.6), "solid": True, "clearance": 1.5, "beside_window": True, "light": ((0.0, 0.3, 0.6), "FF8A3A", 2.6, 8.0)},
    }
)
