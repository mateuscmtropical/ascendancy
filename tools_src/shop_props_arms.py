"""Arms, armour and adventurers' guild props (block B) for the shop interiors: smithy, armourer and guild hall.

Runs inside Blender, imported by build_market_shops.py and build_prop_sheet.py. Follows the prop contract in
shop_props_common.py: every prop is def name(b, frame, **options) built from Builder primitives with frame=frame;
X width centred, customer side -Y, back (wall) at +size[1] / 2, Z up from the floor; wall props are built at their
mounting height. Weapon, shield, helmet and armour pieces are small helpers reused across the racks.
"""

import itertools
import math
import random
import sys
from pathlib import Path

import bmesh
from mathutils import Euler, Matrix, Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))

from build_town_houses import BRICK, STONE, TRIM_SMOOTH_BAND, WOOD, WOOD_DARK_BAND, WOOD_LIGHT_BAND, Builder, srgb  # noqa: E402
from shop_props_common import GOODS_PALETTE, base_profile, bevel_box, cornice_profile, filled_row, knob, lathe, raised_panel, ring, run_profile, solid_hull, turned_leg  # noqa: E402

# Bright, clean metals and cloths (style bible: never dead grey; steel leans blue, iron leans violet).
STEEL = "CDD8E6"
STEEL_BRIGHT = "E4ECF5"
STEEL_DARK = "8593B0"
IRON_DARK = "4A4458"
GOLD = "E8C14F"
BRASS = "D9A441"
BRONZE = "C98A4A"
COPPER = "D9824A"
LEATHER = "9A5A35"
LEATHER_DARK = "6B3E2A"
BONE = "EFE3C8"
PARCHMENT = "F2E6CF"
INK = "3A3152"
SOCKET = "2B2236"
COAL = "3B3445"
CLOTH_RED = "C9483B"
CLOTH_BLUE = "3561B0"
CLOTH_GREEN = "3F8A50"
CLOTH_PURPLE = "6C5BB8"
PAPERS = ("F2E6CF", "EAD9B0", "F7E08A", "C9E3F2", "F2C6C0", "D9EFC4", "E6D2F2")

DARK_GRAIN = ("band", *WOOD_DARK_BAND, 1.0)
LIGHT_GRAIN = ("band", *WOOD_LIGHT_BAND, 1.0)
SMOOTH_TRIM = ("band", *TRIM_SMOOTH_BAND, 1.0)

GUILD_HALL_CEILING = 7.0  # the hanging dragon skull is modelled in a 7 m hall, then moved so z = 0 is the ceiling mount


# ---------- small geometry helpers ----------

def place(frame: Matrix, location: tuple = (0.0, 0.0, 0.0), rotation: tuple = (0.0, 0.0, 0.0), scale: tuple = (1.0, 1.0, 1.0)) -> Matrix:
    """Child frame: translate, then rotate (degrees, X then Y then Z), then scale."""
    turn = Euler(tuple(math.radians(angle) for angle in rotation), "XYZ").to_matrix().to_4x4()

    return frame @ Matrix.Translation(location) @ turn @ Matrix.Diagonal((*scale, 1.0))


def along(frame: Matrix, start: tuple, end: tuple) -> tuple:
    """Frame whose +Z runs from start to end, and that length (for cylinders following a curve)."""
    direction = Vector(end) - Vector(start)
    turn = Vector((0.0, 0.0, 1.0)).rotation_difference(direction).to_matrix().to_4x4()

    return frame @ Matrix.Translation(start) @ turn, direction.length


def hull(b: Builder, points: list, material: str, tint: tuple, frame: Matrix = None, uv: tuple = None):
    """Convex hull like Builder.hull, but tolerant of points lying inside or on the hull (Builder.hull hands
    such points to bmesh.ops.delete twice and fails)."""
    hull_bmesh = bmesh.new()
    vertices = [hull_bmesh.verts.new(point) for point in points]
    result = bmesh.ops.convex_hull(hull_bmesh, input=vertices)
    unused = list(dict.fromkeys(element for element in result["geom_interior"] + result["geom_unused"] if isinstance(element, bmesh.types.BMVert)))
    bmesh.ops.delete(hull_bmesh, geom=unused, context="VERTS")

    return b._link(hull_bmesh, material, tint, uv, frame or Matrix.Identity(4))


def box(b: Builder, frame: Matrix, minimum: tuple, maximum: tuple, material: str, hex_color: str, uv: tuple = None):
    return b.box(minimum, maximum, material, srgb(hex_color), frame=frame, uv=uv)


def plank(b: Builder, frame: Matrix, minimum: tuple, maximum: tuple, hex_color: str = WOOD["media"], light: bool = False):
    return b.box(minimum, maximum, "wood", srgb(hex_color), frame=frame, uv=LIGHT_GRAIN if light else DARK_GRAIN)


def gem(b: Builder, frame: Matrix, center: tuple, radius: float, material: str, hex_color: str, stretch: tuple = (1.0, 1.0, 1.0)):
    """Octahedron: pommels, studs, knobs, cut gems."""
    x, y, z = center
    sx, sy, sz = (radius * factor for factor in stretch)
    points = [(x + sx, y, z), (x - sx, y, z), (x, y + sy, z), (x, y - sy, z), (x, y, z + sz), (x, y, z - sz)]

    return hull(b, points, material, srgb(hex_color), frame=frame)


def lump(b: Builder, frame: Matrix, center: tuple, radius: float, hex_color: str, generator: random.Random, material: str = "paint"):
    """Irregular rock: coal, ore, rubble."""
    directions = [(1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -0.6), (0.6, 0.6, 0.5), (-0.6, -0.5, 0.4)]
    points = [tuple(center[axis] + direction[axis] * radius * generator.uniform(0.7, 1.1) for axis in range(3)) for direction in directions]

    return hull(b, points, material, srgb(hex_color), frame=frame)


def curved_horn(b: Builder, frame: Matrix, points: list, radius: float, colors: tuple, sides: int = 6) -> None:
    """Tapered horn, talon or tusk following the point list; colour blends along colors (one per segment)."""
    segments = list(zip(points, points[1:]))

    for index, (start, end) in enumerate(segments):
        segment_frame, length = along(frame, start, end)
        base_radius = radius * (1.0 - index / len(segments))
        tip_radius = radius * (1.0 - (index + 1) / len(segments))
        b.cylinder((0.0, 0.0, -0.01), base_radius, length + 0.02, sides, "paint", srgb(colors[min(index, len(colors) - 1)]), top_radius=max(tip_radius, 0.002), frame=segment_frame)


def quill(b: Builder, frame: Matrix, base: tuple, tip: tuple) -> None:
    """Feather pen standing in an ink pot: flat white vane from base to tip."""
    b.beam(base, tip, 0.035, 0.006, "paint", srgb("F7F2E8"), frame=frame, uv=None)


def lantern(b: Builder, frame: Matrix, drop: float = 0.3) -> None:
    """Hanging lantern: rod down from z = drop to the cap, glowing glass, iron cap and base (bottom at z = 0)."""
    b.cylinder((0.0, 0.0, 0.2), 0.008, drop - 0.2, 6, "metal", srgb(IRON_DARK), frame=frame)
    b.cylinder((0.0, 0.0, 0.16), 0.08, 0.06, 8, "metal", srgb(IRON_DARK), top_radius=0.015, frame=frame)
    b.cylinder((0.0, 0.0, 0.03), 0.055, 0.13, 8, "glow_warm", srgb("FFFFFF"), frame=frame)
    b.cylinder((0.0, 0.0, 0.0), 0.07, 0.035, 8, "metal", srgb(IRON_DARK), top_radius=0.06, frame=frame)


def chain(b: Builder, frame: Matrix, x: float, y: float, z_from: float, z_to: float, link: float, hex_color: str) -> None:
    """Hanging chain of elongated links, alternating plane, from z_from up to z_to."""
    count = max(1, int((z_to - z_from) / (link * 0.78)))

    for index in range(count):
        center = (x, y, z_from + link * 0.5 + index * (z_to - z_from - link) / max(1, count - 1))
        link_frame = place(frame, center, (0.0, 0.0, 90.0 * (index % 2)), (1.0, 1.0, 1.7))
        ring(b, (0.0, 0.0, 0.0), link * 0.3, link * 0.09, "metal", hex_color, link_frame, sides=6, tube_sides=3, axis="Y")


def arch_outline(half_width: float, bottom: float, spring: float, segments: int = 8) -> list:
    """Round-headed opening (u, z) outline: straight jambs from bottom to spring, half circle on top."""
    arc = [(half_width * math.cos(math.pi * index / segments), spring + half_width * math.sin(math.pi * index / segments)) for index in range(segments + 1)]

    return [(-half_width, bottom), (half_width, bottom)] + arc


def heater_outline(half_width: float, height: float) -> list:
    """Heater shield (u, z) outline centred on 0: flat top, straight flanks, curving to a point."""
    top = height / 2.0
    right = [(half_width, top), (half_width, top - height * 0.38), (half_width * 0.86, top - height * 0.62), (half_width * 0.55, top - height * 0.84)]
    left = [(-u, z) for u, z in reversed(right)]

    return left + right + [(0.0, -top)]


def star_outline(points: int, outer: float, inner: float, center: tuple = (0.0, 0.0), turn: float = 90.0) -> list:
    angles = [math.radians(turn) + math.pi * index / points for index in range(points * 2)]

    return [(center[0] + (outer if index % 2 == 0 else inner) * math.cos(angle), center[1] + (outer if index % 2 == 0 else inner) * math.sin(angle)) for index, angle in enumerate(angles)]


def scaled(outline: list, factor: float, center: tuple = (0.0, 0.0)) -> list:
    return [(center[0] + (u - center[0]) * factor, center[1] + (z - center[1]) * factor) for u, z in outline]


EMBLEMS = {
    "cross": lambda s: [(-0.14 * s, 0.6 * s), (0.14 * s, 0.6 * s), (0.14 * s, 0.14 * s), (0.5 * s, 0.14 * s), (0.5 * s, -0.14 * s), (0.14 * s, -0.14 * s), (0.14 * s, -0.7 * s), (-0.14 * s, -0.7 * s), (-0.14 * s, -0.14 * s), (-0.5 * s, -0.14 * s), (-0.5 * s, 0.14 * s), (-0.14 * s, 0.14 * s)],
    "chevron": lambda s: [(-0.6 * s, -0.4 * s), (0.0, 0.2 * s), (0.6 * s, -0.4 * s), (0.6 * s, -0.08 * s), (0.0, 0.52 * s), (-0.6 * s, -0.08 * s)],
    "sun": lambda s: star_outline(8, 0.55 * s, 0.32 * s),
    "star": lambda s: star_outline(5, 0.6 * s, 0.25 * s),
    "band": lambda s: [(-0.62 * s, 0.38 * s), (-0.38 * s, 0.62 * s), (0.62 * s, -0.38 * s), (0.38 * s, -0.62 * s)],
    "diamond": lambda s: [(0.0, 0.55 * s), (0.38 * s, 0.0), (0.0, -0.55 * s), (-0.38 * s, 0.0)],
}


# ---------- weapons (each stands on +Z from z = 0, flat side facing -Y) ----------

def sword(b: Builder, frame: Matrix, length: float, blade: str = STEEL_BRIGHT, hilt: str = GOLD, grip: str = LEATHER, width: float = None, jewel: str = None) -> None:
    width = width or max(0.045, length * 0.06)
    pommel = width * 0.42
    grip_length = max(0.1, length * 0.16)
    guard_z = pommel * 1.6 + grip_length
    guard_half = width * 1.9
    guard_height = width * 0.42
    thickness = width * 0.13
    blade_base = guard_z + guard_height
    shoulder = length - width * 1.3
    guard_points = [
        (side * reach * guard_half, depth * thickness * spread, guard_z + lift * guard_height)
        for side, depth, (reach, spread, lift) in itertools.product((-1, 1), (-1, 1), ((1.0, 1.4, 0.25), (1.0, 1.4, 1.15), (0.25, 2.2, 0.0), (0.25, 2.2, 1.0)))
    ]

    gem(b, frame, (0.0, 0.0, pommel), pommel, "metal", hilt)

    b.cylinder((0.0, 0.0, pommel * 1.6), width * 0.22, grip_length, 6, "paint", srgb(grip), frame=frame)

    hull(b, guard_points, "metal", srgb(hilt), frame=frame)

    hull(b, 
        [(width / 2.0, 0.0, blade_base), (-width / 2.0, 0.0, blade_base), (0.0, thickness, blade_base), (0.0, -thickness, blade_base),
         (width * 0.46, 0.0, shoulder), (-width * 0.46, 0.0, shoulder), (0.0, thickness, shoulder), (0.0, -thickness, shoulder), (0.0, 0.0, length)],
        "metal", srgb(blade), frame=frame,
    )

    if jewel:
        gem(b, frame, (0.0, -thickness * 2.2, guard_z + guard_height / 2.0), guard_height * 0.55, jewel if jewel.startswith("glow") else "paint", "FFFFFF" if jewel.startswith("glow") else jewel)


def haft(b: Builder, frame: Matrix, length: float, wood: str, wrap: str, radius: float = 0.017) -> None:
    b.cylinder((0.0, 0.0, 0.0), radius, length, 6, "wood", srgb(wood), frame=frame, uv=LIGHT_GRAIN)
    b.cylinder((0.0, 0.0, 0.03), radius * 1.25, 0.16, 6, "paint", srgb(wrap), frame=frame)


AXE_BLADE = [(0.022, -0.035), (0.09, -0.05), (0.15, -0.1), (0.175, -0.09), (0.19, -0.02), (0.19, 0.03), (0.175, 0.09), (0.15, 0.1), (0.09, 0.05), (0.022, 0.035)]


def axe(b: Builder, frame: Matrix, length: float, head: str = STEEL, wood: str = WOOD["mel"], double: bool = False, size: float = 1.0) -> None:
    head_z = length - 0.1 * size

    haft(b, frame, length, wood, LEATHER_DARK)

    box(b, frame, (-0.028, -0.022, head_z - 0.06 * size), (0.028, 0.022, head_z + 0.06 * size), "metal", STEEL_DARK)

    b.prism([(u * size, head_z + z * size) for u, z in AXE_BLADE], -0.01, 0.01, "metal", srgb(head), frame=frame)

    if double:
        b.prism([(-u * size, head_z + z * size) for u, z in AXE_BLADE], -0.01, 0.01, "metal", srgb(head), frame=frame)
    else:
        b.prism([(-0.022, head_z - 0.025), (-0.085 * size, head_z - 0.006), (-0.085 * size, head_z + 0.006), (-0.022, head_z + 0.025)], -0.012, 0.012, "metal", srgb(STEEL_DARK), frame=frame)


def mace(b: Builder, frame: Matrix, length: float, head: str = STEEL, wood: str = WOOD["escura"], knob: str = GOLD) -> None:
    head_z = length - 0.15

    haft(b, frame, head_z + 0.02, wood, CLOTH_RED)

    b.cylinder((0.0, 0.0, head_z), 0.042, 0.12, 8, "metal", srgb(head), top_radius=0.034, frame=frame)

    for angle in (0.0, 60.0, 120.0):
        flange_frame = place(frame, (0.0, 0.0, head_z), (0.0, 0.0, angle))
        hull(b, [(side * reach, depth * 0.007, lift) for side, depth, (reach, lift) in itertools.product((-1, 1), (-1, 1), ((0.075, 0.03), (0.075, 0.09), (0.035, -0.005), (0.035, 0.125)))], "metal", srgb(head), frame=flange_frame)

    gem(b, frame, (0.0, 0.0, head_z + 0.135), 0.03, "metal", knob)


def warhammer(b: Builder, frame: Matrix, length: float, head: str = STEEL, wood: str = WOOD["media"]) -> None:
    head_z = length - 0.09

    haft(b, frame, length - 0.03, wood, CLOTH_BLUE)

    box(b, frame, (-0.03, -0.035, head_z - 0.045), (0.11, 0.035, head_z + 0.045), "metal", head)

    hull(b, [(-0.03, -0.025, head_z - 0.03), (-0.03, 0.025, head_z - 0.03), (-0.03, -0.025, head_z + 0.03), (-0.03, 0.025, head_z + 0.03), (-0.14, 0.0, head_z)], "metal", srgb(STEEL_DARK), frame=frame)

    gem(b, frame, (0.0, 0.0, length - 0.02), 0.025, "metal", GOLD)


def spear(b: Builder, frame: Matrix, length: float, head: str = STEEL_BRIGHT, wood: str = WOOD["mel"], tassel: str = CLOTH_RED, halberd: bool = False) -> None:
    socket = length - 0.3

    b.cylinder((0.0, 0.0, 0.0), 0.016, socket, 6, "wood", srgb(wood), frame=frame, uv=LIGHT_GRAIN)
    b.cylinder((0.0, 0.0, 0.0), 0.02, 0.05, 6, "metal", srgb(STEEL_DARK), frame=frame)
    b.cylinder((0.0, 0.0, socket - 0.02), 0.022, 0.09, 6, "metal", srgb(STEEL_DARK), top_radius=0.013, frame=frame)
    b.cylinder((0.0, 0.0, socket - 0.12), 0.04, 0.1, 6, "paint", srgb(tassel), top_radius=0.017, frame=frame)

    hull(b, [(0.0, 0.0, socket + 0.05), (0.042, 0.0, socket + 0.15), (-0.042, 0.0, socket + 0.15), (0.0, 0.01, socket + 0.15), (0.0, -0.01, socket + 0.15), (0.0, 0.0, length)], "metal", srgb(head), frame=frame)

    if halberd:
        blade = [(0.02, -0.11), (0.1, -0.13), (0.17, -0.17), (0.18, 0.0), (0.17, 0.1), (0.1, 0.05), (0.02, 0.03)]
        b.prism([(u, socket + z) for u, z in blade], -0.009, 0.009, "metal", srgb(head), frame=frame)
        b.prism([(-0.02, socket - 0.05), (-0.13, socket + 0.02), (-0.02, socket - 0.01)], -0.01, 0.01, "metal", srgb(STEEL_DARK), frame=frame)


def smith_hammer(b: Builder, frame: Matrix, length: float = 0.42, head: str = STEEL_DARK, wood: str = WOOD["mel"], head_size: float = 1.0) -> None:
    """Handle on +Z, head across X at the top (z = length)."""
    half = 0.05 * head_size
    height = 0.04 * head_size

    b.cylinder((0.0, 0.0, 0.0), 0.014, length - height * 0.5, 6, "wood", srgb(wood), frame=frame, uv=LIGHT_GRAIN)

    box(b, frame, (-half, -height * 0.55, length - height), (half * 1.3, height * 0.55, length), "metal", head)

    hull(b, [(-half, -height * 0.55, length - height), (-half, height * 0.55, length - height), (-half, -height * 0.55, length), (-half, height * 0.55, length), (-half * 1.9, 0.0, length - height * 0.5)], "metal", srgb(head), frame=frame)


def tongs(b: Builder, frame: Matrix, length: float = 0.55, tint: str = IRON_DARK) -> None:
    """Handles at z = 0, jaws at the top."""
    pivot = length * 0.72

    b.beam((-0.035, 0.0, 0.0), (0.012, 0.0, pivot), 0.016, 0.012, "metal", srgb(tint), frame=frame, uv=None)
    b.beam((0.035, 0.0, 0.0), (-0.012, 0.0, pivot), 0.016, 0.012, "metal", srgb(tint), frame=frame, uv=None)
    b.beam((0.012, 0.0, pivot), (-0.016, 0.0, length), 0.018, 0.014, "metal", srgb(tint), frame=frame, uv=None)
    b.beam((-0.012, 0.0, pivot), (0.016, 0.0, length), 0.018, 0.014, "metal", srgb(tint), frame=frame, uv=None)

    b.cylinder((0.0, -0.012, pivot), 0.012, 0.024, 6, "metal", srgb(BRASS), frame=frame, axis="Y")


def bow(b: Builder, frame: Matrix, length: float = 1.3, wood: str = WOOD["mel"], grip: str = CLOTH_RED) -> None:
    """Strung bow standing on +Z, belly towards +X."""
    half = length / 2.0
    points = [(0.12 * math.cos(angle) - 0.12 * 0.35, 0.0, half + half * math.sin(angle)) for angle in (math.radians(value) for value in (-90, -60, -30, 0, 30, 60, 90))]
    limb_points = [(-0.12 * 0.35 + 0.12 * math.cos(math.asin(max(-1.0, min(1.0, (z - half) / half)))) * 1.0, 0.0, z) for _, _, z in points]

    for start, end in zip(limb_points, limb_points[1:]):
        b.beam(start, end, 0.026, 0.02, "wood", srgb(wood), frame=frame)

    b.beam(limb_points[0], limb_points[-1], 0.004, 0.004, "paint", srgb(PARCHMENT), frame=frame, uv=None)
    box(b, frame, (limb_points[3][0] - 0.018, -0.016, half - 0.07), (limb_points[3][0] + 0.018, 0.016, half + 0.07), "paint", grip)


# ---------- shields (face towards -Y, back face on y = 0, centred on the origin) ----------

def round_shield(b: Builder, frame: Matrix, radius: float, face: str, emblem: str = None, emblem_color: str = GOLD, rim: str = STEEL_DARK, boss: str = GOLD, wooden: bool = False) -> None:
    b.cylinder((0.0, -0.03, 0.0), radius, 0.03, 12, "metal", srgb(rim), frame=frame, axis="Y")

    if wooden:
        b.cylinder((0.0, -0.042, 0.0), radius * 0.9, 0.012, 12, "wood", srgb(face), frame=frame, axis="Y", uv=LIGHT_GRAIN)
    else:
        b.cylinder((0.0, -0.042, 0.0), radius * 0.9, 0.012, 12, "paint", srgb(face), frame=frame, axis="Y")

    if emblem:
        b.prism(EMBLEMS[emblem](radius * 1.25), -0.05, -0.041, "paint", srgb(emblem_color), frame=frame)

    b.cylinder((0.0, -0.085, 0.0), radius * 0.08, 0.04, 8, "metal", srgb(boss), top_radius=radius * 0.24, frame=frame, axis="Y")


def heater_shield(b: Builder, frame: Matrix, half_width: float, height: float, face: str, emblem: str = None, emblem_color: str = GOLD, rim: str = STEEL_DARK) -> None:
    outline = heater_outline(half_width, height)

    b.prism(outline, -0.03, 0.0, "metal", srgb(rim), frame=frame)
    b.prism(scaled(outline, 0.88, (0.0, height * 0.04)), -0.042, -0.029, "paint", srgb(face), frame=frame)

    if emblem:
        b.prism([(u, z + height * 0.06) for u, z in EMBLEMS[emblem](half_width * 1.1)], -0.05, -0.041, "paint", srgb(emblem_color), frame=frame)


# ---------- helmets (rim at z = 0, about 0.13 radius and 0.3 tall) ----------

DOME = [(0.125, 0.0), (0.13, 0.1), (0.12, 0.19), (0.09, 0.26), (0.04, 0.295), (0.0, 0.3)]
GREAT_HELM = [(0.12, 0.0), (0.125, 0.2), (0.11, 0.27), (0.06, 0.3), (0.0, 0.305)]
CAP = [(0.13, 0.0), (0.13, 0.08), (0.11, 0.17), (0.06, 0.22), (0.0, 0.235)]


def helmet(b: Builder, frame: Matrix, style: str, shell: str = STEEL, trim: str = GOLD, plume: str = CLOTH_RED) -> None:
    profile = {"great": GREAT_HELM, "leather": CAP}.get(style, DOME)
    material = "paint" if style == "leather" else "metal"

    lathe(b, profile, 8, material, shell, frame)

    HELMET_DETAILS[style](b, frame, shell, trim, plume)


def _helmet_dome(b: Builder, frame: Matrix, shell: str, trim: str, plume: str) -> None:
    box(b, frame, (-0.014, -0.138, -0.06), (0.014, -0.115, 0.17), "metal", trim)
    hull(b, [(side * 0.015, y, z) for side, (y, z) in itertools.product((-1, 1), ((-0.06, 0.27), (-0.05, 0.4), (0.12, 0.37), (0.17, 0.2)))], "paint", srgb(plume), frame=frame)


def _helmet_great(b: Builder, frame: Matrix, shell: str, trim: str, plume: str) -> None:
    box(b, frame, (-0.09, -0.128, 0.15), (0.09, -0.115, 0.168), "paint", SOCKET)
    box(b, frame, (-0.012, -0.132, 0.02), (0.012, -0.118, 0.27), "metal", trim)
    b.cylinder((0.0, 0.0, 0.0), 0.128, 0.03, 8, "metal", srgb(trim), frame=frame)
    b.cylinder((0.0, 0.0, 0.29), 0.025, 0.06, 6, "metal", srgb(trim), frame=frame)
    b.cylinder((0.0, 0.0, 0.33), 0.012, 0.1, 6, "paint", srgb(plume), top_radius=0.055, frame=frame)


def _helmet_sallet(b: Builder, frame: Matrix, shell: str, trim: str, plume: str) -> None:
    hull(b, [(side * 0.12, y, z) for side, (y, z) in itertools.product((-1, 1), ((0.0, 0.02), (0.12, 0.06), (0.1, 0.14), (0.2, -0.02)))], "metal", srgb(shell), frame=frame)
    box(b, frame, (-0.11, -0.135, 0.12), (0.11, -0.12, 0.135), "paint", SOCKET)
    b.cylinder((0.0, 0.0, 0.0), 0.132, 0.025, 8, "metal", srgb(trim), frame=frame)


def _helmet_winged(b: Builder, frame: Matrix, shell: str, trim: str, plume: str) -> None:
    wing = [(0.0, 0.0), (0.08, 0.05), (0.15, 0.16), (0.11, 0.15), (0.13, 0.22), (0.07, 0.15), (0.06, 0.2), (0.02, 0.1)]

    for side in (-1, 1):
        wing_frame = place(frame, (side * 0.115, 0.0, 0.14), (0.0, 0.0, -side * 12.0))
        b.prism([(side * u, z) for u, z in wing], -0.008, 0.008, "paint", srgb(PARCHMENT), frame=wing_frame)

    b.cylinder((0.0, 0.0, 0.0), 0.132, 0.03, 8, "metal", srgb(trim), frame=frame)
    box(b, frame, (-0.014, -0.138, -0.05), (0.014, -0.115, 0.17), "metal", trim)


def _helmet_horned(b: Builder, frame: Matrix, shell: str, trim: str, plume: str) -> None:
    for side in (-1, 1):
        curved_horn(b, frame, [(side * 0.1, 0.0, 0.15), (side * 0.17, -0.01, 0.2), (side * 0.2, -0.02, 0.28), (side * 0.19, -0.03, 0.35)], 0.032, (BONE, "E2CFA6", "B89A7A"))

    b.cylinder((0.0, 0.0, 0.0), 0.132, 0.03, 8, "metal", srgb(trim), frame=frame)


def _helmet_leather(b: Builder, frame: Matrix, shell: str, trim: str, plume: str) -> None:
    for side in (-1, 1):
        box(b, frame, (side * 0.115 - 0.02, -0.05, -0.1), (side * 0.115 + 0.02, 0.05, 0.04), "paint", shell)

    b.cylinder((0.0, 0.0, 0.0), 0.135, 0.03, 8, "paint", srgb(trim), frame=frame)


HELMET_DETAILS = {"dome": _helmet_dome, "great": _helmet_great, "sallet": _helmet_sallet, "winged": _helmet_winged, "horned": _helmet_horned, "leather": _helmet_leather}


# ---------- smithy ----------

def forge(b: Builder, frame: Matrix, **options) -> None:
    """Stone hearth with a glowing ember bed, fire mouth in the back wall, brick hood and chimney up to 4.5 m."""
    generator = random.Random(options.get("seed", 1))
    stone = options.get("tint", "D9B88A")
    brick = BRICK["vermelho"]

    box(b, frame, (-1.0, -0.8, 0.0), (1.0, 0.5, 0.75), "stone", stone)
    box(b, frame, (-1.0, 0.5, 0.0), (1.0, 0.8, 1.95), "stone", stone)

    trim = "F0D2A4"

    box(b, frame, (-1.0, -0.8, 0.75), (1.0, -0.58, 0.86), "trim", trim, SMOOTH_TRIM)
    box(b, frame, (-1.0, -0.58, 0.75), (-0.78, 0.5, 0.86), "trim", trim, SMOOTH_TRIM)
    box(b, frame, (0.78, -0.58, 0.75), (1.0, 0.5, 0.86), "trim", trim, SMOOTH_TRIM)
    box(b, frame, (-0.78, -0.58, 0.75), (0.78, 0.5, 0.8), "paint", COAL)
    lathe(b, [(0.36, 0.0), (0.28, 0.05), (0.12, 0.09), (0.0, 0.1)], 8, "glow_ember", "FFFFFF", place(frame, (0.0, -0.05, 0.79), scale=(1.5, 1.0, 1.0)))

    for index in range(22):
        angle = generator.uniform(0.0, 2.0 * math.pi)
        reach = generator.uniform(0.3, 0.62)
        center = (reach * 1.15 * math.cos(angle), -0.05 + reach * 0.6 * math.sin(angle), 0.8)
        lump(b, frame, center, generator.uniform(0.045, 0.075), ("2F2A38", "453D52", COAL)[index % 3], generator)

    b.prism(arch_outline(0.52, 0.8, 1.22), 0.46, 0.5, "trim", srgb(trim), frame=frame, uv=SMOOTH_TRIM)
    b.prism(arch_outline(0.4, 0.8, 1.18), 0.44, 0.46, "paint", srgb(SOCKET), frame=frame)
    box(b, frame, (-0.36, 0.43, 0.8), (0.36, 0.445, 0.98), "glow_ember", "FFFFFF")

    box(b, frame, (-0.7, -0.81, 0.08), (0.7, -0.79, 0.52), "paint", SOCKET)

    for index, x in enumerate((-0.42, 0.0, 0.42)):
        b.cylinder((x - 0.18, -0.79, 0.15 + (index % 2) * 0.12), 0.07, 0.36, 8, "wood", srgb(WOOD["mel"]), frame=frame, axis="X", uv=LIGHT_GRAIN)

    for x in (-0.95, 0.95):
        box(b, frame, (x - 0.05, -0.8, 0.86), (x + 0.05, -0.7, 1.9), "metal", IRON_DARK)

    box(b, frame, (-1.0, -0.8, 1.86), (1.0, 0.8, 2.02), "trim", trim, SMOOTH_TRIM)
    hull(b, [(x, y, 2.0) for x, y in itertools.product((-0.98, 0.98), (-0.76, 0.8))] + [(x, y, 3.05) for x, y in itertools.product((-0.42, 0.42), (0.12, 0.8))], "brick", srgb(brick), frame=frame)

    box(b, frame, (-0.42, 0.12, 3.0), (0.42, 0.8, 4.38), "brick", brick)
    box(b, frame, (-0.5, 0.04, 4.36), (0.5, 0.8, 4.5), "trim", trim, SMOOTH_TRIM)

    tongs(b, place(frame, (0.89, -0.5, 0.87), (-90.0, 0.0, 0.0)), 0.7)
    smith_hammer(b, place(frame, (-0.89, -0.45, 0.875), (-90.0, 0.0, 0.0)), 0.4)


def bellows(b: Builder, frame: Matrix, **options) -> None:
    """Big leather bellows on a low trestle; the brass nozzle points to -X (towards the forge)."""
    outline = [(0.5, 0.2), (0.38, 0.24), (0.1, 0.22), (-0.18, 0.15), (-0.36, 0.06), (-0.36, -0.06), (-0.18, -0.15), (0.1, -0.22), (0.38, -0.24), (0.5, -0.2)]
    top_z = lambda x: 0.31 + (x + 0.36) / 0.86 * 0.12  # noqa: E731 - top board leans up towards the handle

    for x, y in itertools.product((-0.32, 0.42), (-0.16, 0.16)):
        plank(b, frame, (x - 0.03, y - 0.03, 0.0), (x + 0.03, y + 0.03, 0.2))

    for y in (-0.16, 0.16):
        plank(b, frame, (-0.36, y - 0.035, 0.14), (0.46, y + 0.035, 0.2), WOOD["media"], True)

    hull(b, [(x, y, z) for (x, y), z in itertools.product(outline, (0.2, 0.24))], "wood", srgb(WOOD["mel"]), frame=frame, uv=LIGHT_GRAIN)
    hull(b, [(x * 0.94, y * 0.92, z) for (x, y), z in itertools.product(outline, (0.24,))] + [(x * 0.97, y * 1.04, (0.24 + top_z(x)) / 2.0) for x, y in outline] + [(x * 0.94, y * 0.92, top_z(x)) for x, y in outline], "paint", srgb(LEATHER), frame=frame)
    hull(b, [(x, y, top_z(x) + dz) for (x, y), dz in itertools.product(outline, (0.0, 0.04))], "wood", srgb(WOOD["mel"]), frame=frame, uv=LIGHT_GRAIN)

    box(b, frame, (0.05, -0.23, top_z(0.05) + 0.035), (0.12, 0.23, top_z(0.12) + 0.055), "metal", BRASS)
    b.beam((0.5, 0.0, top_z(0.5) + 0.03), (0.6, 0.0, top_z(0.5) + 0.05), 0.04, 0.05, "wood", srgb(WOOD["escura"]), frame=frame)
    b.cylinder((-0.6, 0.0, 0.25), 0.02, 0.26, 8, "metal", srgb(BRASS), top_radius=0.05, frame=frame, axis="X")


def anvil_block(b: Builder, frame: Matrix, **options) -> None:
    """Kit anvil on an iron-banded oak stump, a hammer resting on the face."""
    b.cylinder((0.0, 0.0, 0.0), 0.27, 0.5, 10, "wood", srgb(WOOD["media"]), frame=frame, uv=LIGHT_GRAIN)
    b.cylinder((0.0, 0.0, 0.5), 0.25, 0.008, 10, "paint", srgb("D9A770"), frame=frame)

    for z in (0.07, 0.4):
        b.cylinder((0.0, 0.0, z), 0.278, 0.045, 10, "metal", srgb(IRON_DARK), frame=frame)

    b.kit("Anvil", (-0.04, 0.0, 0.5), 0.0, (0.65, 0.65, 0.65), tints={"MI_Trim_Metal": srgb("DCE6F7")}, frame=frame, props=True)

    smith_hammer(b, place(frame, (0.05, -0.02, 0.88), (0.0, 90.0, 30.0)), 0.36)


def quench_barrel(b: Builder, frame: Matrix, **options) -> None:
    """Oak quench barrel full of water, two iron hoops, tongs dipped in it."""
    profile = [(0.33, 0.0), (0.37, 0.2), (0.39, 0.4), (0.37, 0.6), (0.34, 0.8), (0.31, 0.8), (0.31, 0.72)]

    lathe(b, profile, 10, "wood", WOOD["mel"], frame, uv=LIGHT_GRAIN)
    b.cylinder((0.0, 0.0, 0.715), 0.312, 0.012, 10, "water", srgb("5FB0D0"), frame=frame)

    for z, radius in ((0.1, 0.36), (0.62, 0.366)):
        b.cylinder((0.0, 0.0, z), radius, 0.05, 10, "metal", srgb(IRON_DARK), frame=frame)

    tongs(b, place(frame, (0.12, -0.05, 0.6), (0.0, -150.0, 0.0)), 0.55)


def grindstone(b: Builder, frame: Matrix, **options) -> None:
    """Treadle grindstone: sandstone wheel over a water trough, seat on the left, crank and pedal on the right."""
    for x in (-0.12, 0.12):
        plank(b, frame, (x - 0.035, -0.04, 0.0), (x + 0.035, 0.04, 0.66))
        plank(b, frame, (x - 0.04, -0.28, 0.0), (x + 0.04, 0.28, 0.06), WOOD["escura"])

    for y in (-0.2, 0.2):
        plank(b, frame, (-0.48, y - 0.03, 0.0), (0.48, y + 0.03, 0.06), WOOD["escura"])

    plank(b, frame, (-0.09, -0.2, 0.06), (0.09, 0.2, 0.27), WOOD["media"], True)
    b.box((-0.08, -0.18, 0.2), (0.08, 0.18, 0.262), "water", srgb("5FB0D0"), frame=frame)

    b.cylinder((-0.05, 0.0, 0.62), 0.32, 0.1, 12, "paint", srgb("D9B47E"), frame=frame, axis="X")
    b.cylinder((-0.055, 0.0, 0.62), 0.1, 0.11, 8, "paint", srgb("B79E74"), frame=frame, axis="X")
    b.cylinder((-0.3, 0.0, 0.62), 0.022, 0.64, 6, "metal", srgb(IRON_DARK), frame=frame, axis="X")

    b.beam((0.33, 0.0, 0.62), (0.33, -0.02, 0.48), 0.03, 0.02, "metal", srgb(IRON_DARK), frame=frame, uv=None)
    b.beam((0.36, -0.02, 0.48), (0.36, -0.02, 0.1), 0.02, 0.02, "metal", srgb(IRON_DARK), frame=frame, uv=None)
    plank(b, frame, (0.18, -0.14, 0.06), (0.46, 0.14, 0.1), WOOD["mel"], True)

    for x, y in itertools.product((-0.45, -0.3), (-0.15, 0.15)):
        plank(b, frame, (x - 0.025, y - 0.025, 0.06), (x + 0.025, y + 0.025, 0.44))

    plank(b, frame, (-0.49, -0.2, 0.44), (-0.26, 0.2, 0.49), WOOD["mel"], True)

    sword(b, place(frame, (0.2, 0.0, 0.27), (0.0, -78.0, 0.0)), 0.7)


def tool_wall_rack(b: Builder, frame: Matrix, **options) -> None:
    """Wall board 1.0-1.85 m with hanging hammers and tongs and a ledge of punches. Back on the wall at y = +0.1."""
    for index, z in enumerate((1.0, 1.29, 1.58)):
        plank(b, frame, (-0.75, 0.065, z), (0.75, 0.1, z + 0.27), WOOD["media"] if index % 2 else WOOD["mel"], True)

    plank(b, frame, (-0.75, 0.0, 1.62), (0.75, 0.065, 1.69), WOOD["escura"])

    hammers = [(-0.6, 0.44, 1.5), (-0.38, 0.38, 1.3), (-0.16, 0.32, 1.1)]

    for x, length, size in hammers:
        for side in (-1, 1):
            b.cylinder((x + side * 0.03, -0.05, 1.655), 0.01, 0.05, 6, "metal", srgb(BRASS), frame=frame, axis="Y")

        smith_hammer(b, place(frame, (x, -0.03, 1.645 - length)), length, STEEL_DARK, WOOD["mel"], size)

    for x in (0.12, 0.32):
        b.cylinder((x, -0.05, 1.655), 0.012, 0.05, 6, "metal", srgb(BRASS), frame=frame, axis="Y")
        tongs(b, place(frame, (x, -0.04, 1.69), (0.0, 180.0, 0.0)), 0.6)

    box(b, frame, (0.5, 0.04, 1.2), (0.53, 0.06, 1.62), "metal", STEEL_DARK)
    b.cylinder((0.515, 0.05, 1.6), 0.012, 0.05, 6, "metal", srgb(BRASS), frame=frame, axis="Y")

    plank(b, frame, (0.38, -0.08, 1.12), (0.75, 0.065, 1.15), WOOD["escura"])

    for index, x in enumerate((0.42, 0.47, 0.52, 0.57)):
        b.cylinder((x, -0.02, 1.15), 0.012, 0.1 + index * 0.02, 6, "metal", srgb(STEEL_DARK if index % 2 else IRON_DARK), frame=frame)

    box(b, frame, (0.62, -0.06, 1.15), (0.73, 0.04, 1.22), "paint", CLOTH_RED)


def sword_wall(b: Builder, frame: Matrix, **options) -> None:
    """3.0 x 2.0 display panel (0.85-2.85 m): velvet inset, 6 upright swords and 2 crossed over a gilded crest."""
    velvet = options.get("tint", "B23A3A")
    hilts = (GOLD, BRASS, STEEL_DARK, GOLD, BRONZE, STEEL)
    grips = (CLOTH_BLUE, LEATHER, CLOTH_RED, LEATHER_DARK, CLOTH_GREEN, CLOTH_PURPLE)
    lengths = (0.95, 1.1, 0.85, 0.9, 1.05, 1.0)

    plank(b, frame, (-1.5, 0.11, 0.85), (1.5, 0.15, 2.85), WOOD["escura"])
    box(b, frame, (-1.4, 0.1, 0.95), (1.4, 0.115, 2.75), "paint", velvet)

    for minimum, maximum in (((-1.5, 0.08, 0.85), (1.5, 0.12, 0.93)), ((-1.5, 0.08, 2.77), (1.5, 0.12, 2.85)), ((-1.5, 0.08, 0.93), (-1.42, 0.12, 2.77)), ((1.42, 0.08, 0.93), (1.5, 0.12, 2.77))):
        plank(b, frame, minimum, maximum, WOOD["mel"], True)

    for x, z in itertools.product((-1.46, 1.46), (0.89, 2.81)):
        gem(b, frame, (x, 0.07, z), 0.05, "metal", GOLD)

    plank(b, frame, (-1.4, 0.03, 0.95), (1.4, 0.1, 1.0), WOOD["mel"], True)

    for index, x in enumerate((-1.2, -0.92, -0.64, 0.64, 0.92, 1.2)):
        box(b, frame, (x - 0.07, 0.04, 1.32), (x + 0.07, 0.1, 1.36), "metal", BRASS)
        sword(b, place(frame, (x, 0.065, 1.0)), lengths[index], STEEL_BRIGHT, hilts[index], grips[index], jewel=(CLOTH_RED, None, "4FB0D9", None, "7FC46A", None)[index])

    b.cylinder((0.0, 0.03, 1.85), 0.3, 0.07, 12, "metal", srgb(GOLD), frame=frame, axis="Y")
    b.cylinder((0.0, 0.02, 1.85), 0.22, 0.02, 12, "paint", srgb(CLOTH_BLUE), frame=frame, axis="Y")
    b.prism(star_outline(4, 0.16, 0.05, (0.0, 1.85)), 0.0, 0.02, "metal", srgb(GOLD), frame=frame)

    for angle in (-38.0, 38.0):
        sword(b, place(frame, (0.0, -0.02, 1.85), (0.0, angle, 0.0)) @ Matrix.Translation((0.0, 0.0, -0.55)), 1.25, STEEL_BRIGHT, GOLD, CLOTH_RED, width=0.075, jewel="4FB0D9")


def spear_rack(b: Builder, frame: Matrix, **options) -> None:
    """Floor rack 1.0 x 0.3 with spears and a halberd in a trough, held by a notched rail."""
    plank(b, frame, (-0.5, -0.15, 0.0), (0.5, 0.15, 0.04), WOOD["escura"])
    plank(b, frame, (-0.47, -0.12, 0.04), (0.47, 0.12, 0.14), WOOD["media"], True)

    for x in (-0.47, 0.47):
        plank(b, frame, (x - 0.03, -0.05, 0.0), (x + 0.03, 0.05, 1.45))
        gem(b, frame, (x, 0.0, 1.47), 0.035, "metal", BRASS)

    plank(b, frame, (-0.5, -0.06, 1.28), (0.5, 0.06, 1.36), WOOD["mel"], True)

    polearms = [(-0.36, CLOTH_RED, False), (-0.18, CLOTH_BLUE, False), (0.0, GOLD, True), (0.22, CLOTH_GREEN, False), (0.38, CLOTH_PURPLE, False)]

    for x, tassel, halberd in polearms:
        spear(b, place(frame, (x, -0.07, 0.08)), 2.1 if not halberd else 2.12, STEEL_BRIGHT, WOOD["mel"], tassel, halberd)


def axe_mace_rack(b: Builder, frame: Matrix, **options) -> None:
    """Floor rack 1.4 wide: axe, mace, double axe and war hammer standing in a slotted rail."""
    for x in (-0.66, 0.66):
        plank(b, frame, (x - 0.035, -0.04, 0.0), (x + 0.035, 0.04, 0.72))
        plank(b, frame, (x - 0.05, -0.2, 0.0), (x + 0.05, 0.2, 0.07), WOOD["escura"])
        gem(b, frame, (x, 0.0, 0.75), 0.04, "metal", BRASS)

    plank(b, frame, (-0.7, -0.12, 0.07), (0.7, 0.12, 0.13), WOOD["media"], True)
    plank(b, frame, (-0.7, -0.05, 0.6), (0.7, 0.05, 0.67), WOOD["mel"], True)

    axe(b, place(frame, (-0.52, -0.08, 0.1)), 1.0, STEEL_BRIGHT, WOOD["mel"])
    mace(b, place(frame, (-0.17, -0.08, 0.1)), 0.85, STEEL, WOOD["escura"], GOLD)
    axe(b, place(frame, (0.15, -0.08, 0.1)), 1.12, STEEL_BRIGHT, WOOD["media"], double=True)
    warhammer(b, place(frame, (0.5, -0.08, 0.1)), 0.95)


def shield_wall(b: Builder, frame: Matrix, **options) -> None:
    """Five painted shields on two wall battens (0.9-2.8 m), back on the wall at y = +0.1."""
    for z in (1.33, 2.3):
        plank(b, frame, (-1.25, 0.06, z - 0.04), (1.25, 0.1, z + 0.04), WOOD["escura"])

    shields = [
        (round_shield, (-0.62, 2.32), (0.34, "C9483B", "sun", GOLD)),
        (heater_shield, (0.62, 2.32), (0.3, 0.72, CLOTH_BLUE, "chevron", STEEL_BRIGHT)),
        (heater_shield, (-0.88, 1.33), (0.28, 0.68, CLOTH_GREEN, "cross", GOLD)),
        (round_shield, (0.0, 1.33), (0.36, WOOD["mel"], "band", CLOTH_BLUE, IRON_DARK, STEEL, True)),
        (heater_shield, (0.88, 1.33), (0.28, 0.68, GOLD, "star", CLOTH_RED)),
    ]

    for builder, (x, z), arguments in shields:
        builder(b, place(frame, (x, 0.06, z)), *arguments)


def helmet_shelf(b: Builder, frame: Matrix, **options) -> None:
    """Three-tier helmet shelf 1.5 x 0.45 x 1.9 with nine helmets on little stands."""
    styles = ("great", "dome", "winged", "sallet", "horned", "dome", "leather", "great", "winged")
    shells = (STEEL, STEEL_BRIGHT, STEEL_BRIGHT, STEEL, "B4C2D6", BRONZE, LEATHER, GOLD, STEEL)
    trims = (GOLD, GOLD, GOLD, BRASS, BRONZE, STEEL_DARK, LEATHER_DARK, STEEL_BRIGHT, GOLD)
    plumes = (CLOTH_RED, CLOTH_BLUE, CLOTH_RED, CLOTH_GREEN, CLOTH_RED, CLOTH_PURPLE, CLOTH_RED, CLOTH_BLUE, GOLD)
    boards = (0.1, 0.72, 1.34)

    for x in (-0.75, 0.71):
        plank(b, frame, (x, -0.225, 0.0), (x + 0.04, 0.225, 1.86))

    plank(b, frame, (-0.71, 0.19, 0.0), (0.71, 0.225, 1.86), WOOD["media"], True)
    plank(b, frame, (-0.78, -0.25, 1.86), (0.78, 0.225, 1.9), WOOD["mel"], True)

    for z in boards:
        plank(b, frame, (-0.71, -0.225, z - 0.04), (0.71, 0.19, z), WOOD["mel"], True)

    for index, (z, x) in enumerate(itertools.product(boards, (-0.45, 0.0, 0.45))):
        b.cylinder((x, 0.0, z), 0.07, 0.02, 8, "wood", srgb(WOOD["escura"]), frame=frame, uv=DARK_GRAIN)
        b.cylinder((x, 0.0, z + 0.02), 0.03, 0.05, 6, "wood", srgb(WOOD["escura"]), frame=frame, uv=DARK_GRAIN)
        helmet(b, place(frame, (x, -0.02, z + 0.07)), styles[index], shells[index], trims[index], plumes[index])


# ---------- armour stands ----------

def _stand_base(b: Builder, frame: Matrix) -> None:
    b.cylinder((0.0, 0.0, 0.0), 0.28, 0.06, 8, "wood", srgb(WOOD["escura"]), frame=frame, uv=DARK_GRAIN)


def _legs(b: Builder, frame: Matrix, thigh: tuple, shin: tuple, foot: tuple, knee: tuple = None) -> None:
    """thigh, shin, foot, knee are (material, hex)."""
    for side in (-1, 1):
        x = side * 0.1
        hull(b, [(x + dx, y, z) for dx, (y, z) in itertools.product((-0.055, 0.055), ((0.07, 0.06), (0.07, 0.17), (-0.15, 0.06), (-0.15, 0.1)))], foot[0], srgb(foot[1]), frame=frame)
        b.cylinder((x, 0.0, 0.14), 0.058, 0.38, 6, shin[0], srgb(shin[1]), top_radius=0.068, frame=frame)
        b.cylinder((x, 0.0, 0.52), 0.07, 0.4, 6, thigh[0], srgb(thigh[1]), top_radius=0.088, frame=frame)

        if knee:
            gem(b, frame, (x, -0.035, 0.53), 0.06, knee[0], knee[1], (1.0, 0.8, 1.0))


def _arms(b: Builder, frame: Matrix, upper: tuple, lower: tuple, hand: tuple) -> None:
    for side in (-1, 1):
        x = side * 0.255
        b.cylinder((x, 0.0, 1.1), 0.05, 0.3, 6, upper[0], srgb(upper[1]), top_radius=0.056, frame=frame)
        b.cylinder((x, 0.0, 0.86), 0.048, 0.25, 6, lower[0], srgb(lower[1]), top_radius=0.06, frame=frame)
        box(b, frame, (x - 0.035, -0.05, 0.74), (x + 0.035, 0.05, 0.87), hand[0], hand[1])


def _pauldrons(b: Builder, frame: Matrix, material: str, hex_color: str) -> None:
    for side in (-1, 1):
        lathe(b, [(0.11, -0.06), (0.115, 0.0), (0.085, 0.06), (0.0, 0.09)], 6, material, hex_color, place(frame, (side * 0.22, 0.0, 1.38), (0.0, side * 22.0, 0.0)))


def _torso(b: Builder, frame: Matrix, material: str, hex_color: str, hem: float = 0.96) -> None:
    profile = [(0.165, hem), (0.18, 1.12), (0.2, 1.3), (0.17, 1.43), (0.07, 1.5)]
    lathe(b, profile, 8, material, hex_color, place(frame, scale=(1.0, 0.72, 1.0)))


def _belt(b: Builder, frame: Matrix, z: float, strap: str, buckle: str, radius: float = 0.168) -> None:
    b.cylinder((0.0, 0.0, z), radius, 0.05, 8, "paint", srgb(strap), frame=place(frame, scale=(1.0, 0.74, 1.0)))
    box(b, frame, (-0.035, -0.135, z - 0.005), (0.035, -0.11, z + 0.055), "metal", buckle)


def _armour_plate(b: Builder, frame: Matrix, plate: str, trim: str, cloth: str, helm: str) -> None:
    _legs(b, frame, ("metal", plate), ("metal", plate), ("metal", trim), ("metal", trim))
    lathe(b, [(0.2, 0.74), (0.165, 0.97)], 8, "metal", plate, place(frame, scale=(1.0, 0.75, 1.0)))
    _torso(b, frame, "metal", plate)
    box(b, frame, (-0.012, -0.152, 1.0), (0.012, -0.13, 1.4), "metal", trim)
    _belt(b, frame, 0.95, LEATHER, trim)
    b.cylinder((0.0, 0.0, 1.45), 0.08, 0.08, 8, "metal", srgb(trim), frame=frame)
    _pauldrons(b, frame, "metal", trim if helm == "winged" else plate)
    _arms(b, frame, ("metal", plate), ("metal", plate), ("metal", trim))
    helmet(b, place(frame, (0.0, 0.0, 1.52)), helm, plate, trim, cloth)


def armour_plate(b: Builder, frame: Matrix) -> None:
    _armour_plate(b, frame, STEEL, GOLD, CLOTH_RED, "great")


def armour_knight_gold(b: Builder, frame: Matrix) -> None:
    cape = [(-0.26, 1.42), (0.26, 1.42), (0.3, 0.42), (0.0, 0.48), (-0.3, 0.42)]

    b.prism(cape, 0.15, 0.17, "paint", srgb(CLOTH_BLUE), frame=frame)
    b.prism([(u * 1.04, z - 0.03) for u, z in cape], 0.17, 0.18, "paint", srgb(GOLD), frame=frame)
    _armour_plate(b, frame, STEEL_BRIGHT, GOLD, CLOTH_BLUE, "winged")


def armour_mail(b: Builder, frame: Matrix) -> None:
    mail = "A9BCD4"
    tabard = [(-0.15, 1.38), (0.15, 1.38), (0.14, 0.62), (-0.14, 0.62)]

    _legs(b, frame, ("metal", mail), ("paint", LEATHER), ("paint", LEATHER_DARK))
    _torso(b, frame, "metal", mail, hem=0.7)

    for depth in (-0.16, 0.16):
        b.prism(tabard, depth - 0.008, depth + 0.008, "paint", srgb(CLOTH_RED), frame=frame)

    b.prism(EMBLEMS["cross"](0.2), -0.172, -0.166, "paint", srgb(GOLD), frame=place(frame, (0.0, 0.0, 1.08)))
    _belt(b, frame, 0.95, LEATHER_DARK, BRASS, 0.172)
    lathe(b, [(0.2, 1.36), (0.15, 1.46), (0.1, 1.52)], 8, "metal", mail, place(frame, scale=(1.0, 0.8, 1.0)))
    _arms(b, frame, ("metal", mail), ("metal", mail), ("paint", LEATHER))
    helmet(b, place(frame, (0.0, 0.0, 1.52)), "dome", STEEL, BRASS, CLOTH_GREEN)


def armour_leather(b: Builder, frame: Matrix) -> None:
    _legs(b, frame, ("paint", "5A4A6E"), ("paint", LEATHER_DARK), ("paint", LEATHER_DARK))
    _torso(b, frame, "paint", LEATHER, hem=0.72)

    for side in (-1, 1):
        box(b, frame, (side * 0.06 - 0.012, -0.15, 0.8), (side * 0.06 + 0.012, -0.13, 1.38), "paint", LEATHER_DARK)

    _belt(b, frame, 0.93, LEATHER_DARK, BRASS, 0.172)
    box(b, frame, (0.09, -0.16, 0.82), (0.17, -0.1, 0.92), "paint", "C08A55")
    lathe(b, [(0.22, 1.38), (0.2, 1.44), (0.1, 1.5)], 8, "paint", "EADFC8", place(frame, scale=(1.0, 0.8, 1.0)))
    lathe(b, [(0.11, -0.06), (0.115, 0.0), (0.085, 0.06), (0.0, 0.09)], 6, "paint", LEATHER_DARK, place(frame, (-0.22, 0.0, 1.38), (0.0, -22.0, 0.0)))
    _arms(b, frame, ("paint", CLOTH_GREEN), ("paint", LEATHER_DARK), ("paint", LEATHER))
    b.sphere((0.0, 0.0, 1.62), 0.1, "wood", srgb(WOOD["mel"]), frame=frame, segments=8)
    helmet(b, place(frame, (0.0, 0.0, 1.6)), "leather", LEATHER, LEATHER_DARK, CLOTH_RED)


ARMOURS = {"plate": armour_plate, "knight_gold": armour_knight_gold, "mail": armour_mail, "leather": armour_leather}


def armor_stand(b: Builder, frame: Matrix, **options) -> None:
    """Mannequin in full armour on a round base; variant plate | leather | mail | knight_gold."""
    _stand_base(b, frame)

    ARMOURS[options.get("variant") or "plate"](b, frame)


def armor_stand_row(b: Builder, frame: Matrix, **options) -> None:
    """Plinth 2.4 x 0.8 with three dressed mannequins (leather, knight, mail) and a brass rail."""
    plank(b, frame, (-1.2, -0.4, 0.0), (1.2, 0.4, 0.15), WOOD["escura"])
    box(b, frame, (-1.2, -0.41, 0.12), (1.2, 0.41, 0.15), "metal", BRASS)

    for x, variant in ((-0.8, "leather"), (0.0, "knight_gold"), (0.8, "mail")):
        armor_stand(b, place(frame, (x, 0.05, 0.15)), variant=variant)


# ---------- forge stock ----------

def coal_pile(b: Builder, frame: Matrix, **options) -> None:
    """Heap of coal 1.2 x 1.0 x 0.6 in a three-sided plank bin, loose lumps spilling out the front and a shovel;
    the warm bin walls frame the dark heap so it reads against the floor."""
    generator = random.Random(options.get("seed", 1))
    profile = [(0.48, 0.0), (0.42, 0.18), (0.31, 0.36), (0.15, 0.5), (0.0, 0.56)]
    stretch = (1.05, 0.85)
    radius_at = lambda z: next(r0 + (r1 - r0) * (z - z0) / (z1 - z0) for (r0, z0), (r1, z1) in zip(profile, profile[1:]) if z <= z1)  # noqa: E731

    lathe(b, profile, 8, "paint", COAL, place(frame, scale=(*stretch, 1.0)))

    plank(b, frame, (-0.6, 0.44, 0.0), (0.6, 0.5, 0.44), WOOD["media"], True)
    plank(b, frame, (-0.6, -0.34, 0.0), (-0.54, 0.44, 0.38), WOOD["media"], True)
    plank(b, frame, (0.54, -0.34, 0.0), (0.6, 0.44, 0.38), WOOD["media"], True)
    plank(b, frame, (-0.54, -0.34, 0.0), (0.54, -0.3, 0.1), WOOD["escura"])

    for x in (-0.6, 0.54):
        plank(b, frame, (x - 0.01, 0.42, 0.0), (x + 0.07, 0.52, 0.5), WOOD["escura"])
        plank(b, frame, (x - 0.01, -0.36, 0.0), (x + 0.07, -0.28, 0.42), WOOD["escura"])

    for index in range(16):
        z = generator.uniform(0.04, 0.5)
        angle = generator.uniform(0.0, 2.0 * math.pi)
        radius = radius_at(z) * 0.98
        lump(b, frame, (radius * stretch[0] * math.cos(angle), radius * stretch[1] * math.sin(angle), z), generator.uniform(0.045, 0.075), ("2F2A38", "453D52", COAL)[index % 3], generator)

    for index in range(5):
        angle = generator.uniform(-2.6, -0.5)
        lump(b, frame, (0.56 * math.cos(angle), 0.46 * math.sin(angle), 0.03), 0.04, "453D52", generator)

    b.beam((0.12, -0.2, 0.36), (0.5, -0.42, 0.05), 0.03, 0.03, "wood", srgb(WOOD["mel"]), frame=frame)
    hull(b, [(0.0 + dx, -0.12 + dy, 0.42 + dz) for dx, dy, dz in ((-0.1, 0.0, 0.0), (0.1, 0.0, 0.0), (-0.08, -0.06, -0.12), (0.08, -0.06, -0.12), (0.0, 0.03, 0.02))], "metal", srgb(STEEL_DARK), frame=place(frame, (0.1, -0.05, -0.05), (0.0, 0.0, -30.0)))


def _open_crate(b: Builder, frame: Matrix, width: float, depth: float, height: float, wood: str) -> None:
    half_x, half_y = width / 2.0, depth / 2.0

    plank(b, frame, (-half_x, -half_y, 0.0), (half_x, half_y, 0.04), wood)

    for side in (-1, 1):
        plank(b, frame, (-half_x, side * half_y - 0.025, 0.0), (half_x, side * half_y + 0.025, height), wood, True)
        plank(b, frame, (side * half_x - 0.025, -half_y, 0.0), (side * half_x + 0.025, half_y, height), wood, True)

    for x, y in itertools.product((-half_x, half_x), (-half_y, half_y)):
        plank(b, frame, (x - 0.035, y - 0.035, 0.0), (x + 0.035, y + 0.035, height + 0.02), WOOD["escura"])


def ingot(b: Builder, frame: Matrix, center: tuple, hex_color: str, turn: float = 0.0) -> None:
    ingot_frame = place(frame, center, (0.0, 0.0, turn))
    hull(b, [(sx * 0.1, sy * 0.045, 0.0) for sx, sy in itertools.product((-1, 1), (-1, 1))] + [(sx * 0.08, sy * 0.03, 0.045) for sx, sy in itertools.product((-1, 1), (-1, 1))], "metal", srgb(hex_color), frame=ingot_frame)


def ingot_crates(b: Builder, frame: Matrix, **options) -> None:
    """Two open crates of iron and copper ingots and a small stack of gold bars in front."""
    for x, metal in ((-0.36, "A9B8CC"), (0.36, COPPER)):
        crate_frame = place(frame, (x, 0.1, 0.0))
        _open_crate(b, crate_frame, 0.62, 0.56, 0.42, WOOD["media"])

        for row, column in itertools.product(range(3), range(3)):
            ingot(b, crate_frame, ((column - 1) * 0.17, (row - 1) * 0.15, 0.38 + 0.01 * ((row + column) % 2)), metal, 4.0 * ((row * 3 + column) % 3 - 1))

    stack = [(-0.1, 0.0), (0.1, 0.0), (0.0, 0.045)]

    for x, z in stack:
        ingot(b, frame, (x, -0.3, z), GOLD)


def giant_sword(b: Builder, frame: Matrix, **options) -> None:
    """Decorative 2.2 m sword, point down, on a heraldic plaque; hung from 0.85 to 3.05 m."""
    plaque = heater_outline(0.42, 0.95)

    b.prism([(u, z + 2.55) for u, z in plaque], 0.08, 0.125, "wood", srgb(WOOD["escura"]), frame=frame, uv=DARK_GRAIN)
    b.prism([(u, z + 2.58) for u, z in scaled(plaque, 0.86)], 0.06, 0.08, "paint", srgb(CLOTH_BLUE), frame=frame)

    for z in (1.35, 2.18):
        box(b, frame, (-0.16, 0.0, z), (0.16, 0.125, z + 0.06), "metal", IRON_DARK)

    sword(b, place(frame, (0.0, 0.0, 3.05), (0.0, 180.0, 0.0)), 2.2, STEEL_BRIGHT, GOLD, CLOTH_RED, width=0.2, jewel="glow_cyan")
    box(b, frame, (-0.02, -0.03, 1.0), (0.02, -0.024, 2.45), "metal", "9FB4D8")


def blade_shelf(b: Builder, frame: Matrix, **options) -> None:
    """Open shelf of blade blanks and finished blades, guards and pommels in a tray at the bottom."""
    generator = random.Random(options.get("seed", 1))

    for x in (-0.7, 0.66):
        plank(b, frame, (x, -0.225, 0.0), (x + 0.04, 0.225, 1.6))

    plank(b, frame, (-0.66, 0.19, 0.0), (0.66, 0.225, 1.6), WOOD["media"], True)

    for z in (0.08, 0.5, 0.95, 1.4):
        plank(b, frame, (-0.66, -0.225, z - 0.04), (0.66, 0.19, z), WOOD["mel"], True)

    plank(b, frame, (-0.72, -0.24, 1.56), (0.72, 0.225, 1.6), WOOD["escura"])

    for index, z in enumerate((0.5, 0.95, 1.4)):
        for slot in range(3):
            y = -0.12 + slot * 0.12
            turn = generator.uniform(-6.0, 6.0)
            finished = (index + slot) % 3 == 0
            blank_frame = place(frame, (generator.uniform(-0.2, 0.2) - 0.42, y, z + 0.012), (0.0, 90.0, turn))
            hull(b, [(0.0, dy, dz) for dy, dz in itertools.product((-0.006, 0.006), (0.0,))] + [(sx * 0.03, sy * 0.006, z_) for sx, sy, z_ in itertools.product((-1, 1), (-1, 1), (0.12, 0.72))] + [(0.0, 0.0, 0.8)], "metal", srgb(STEEL_BRIGHT if finished else "8E9AB8"), frame=blank_frame)
            box(b, blank_frame, (-0.012, -0.005, -0.12), (0.012, 0.005, 0.12), "metal", IRON_DARK)

    box(b, frame, (-0.6, -0.18, 0.08), (0.0, 0.15, 0.16), "wood", WOOD["escura"], DARK_GRAIN)

    for index in range(6):
        gem(b, frame, (-0.52 + index * 0.09, -0.02, 0.18), 0.035, "metal", (GOLD, BRASS, STEEL)[index % 3])

    box(b, frame, (0.1, -0.15, 0.08), (0.55, 0.12, 0.3), "paint", LEATHER)
    box(b, frame, (0.12, -0.155, 0.22), (0.53, 0.125, 0.25), "paint", LEATHER_DARK)


def plans_table(b: Builder, frame: Matrix, **options) -> None:
    """Design table: blueprint of a sword, scrolls, ink and quill, dividers and a candle."""
    plank(b, frame, (-0.7, -0.4, 0.72), (0.7, 0.4, 0.78), WOOD["mel"], True)

    for x, y in itertools.product((-0.62, 0.62), (-0.32, 0.32)):
        plank(b, frame, (x - 0.035, y - 0.035, 0.0), (x + 0.035, y + 0.035, 0.72))

    plank(b, frame, (-0.62, -0.02, 0.12), (0.62, 0.02, 0.17))

    sheet = place(frame, (-0.1, -0.05, 0.78), (0.0, 0.0, 4.0))
    box(b, sheet, (-0.38, -0.26, 0.0), (0.38, 0.26, 0.004), "paint", "D8E8F4")
    box(b, sheet, (-0.3, -0.012, 0.004), (0.24, 0.012, 0.007), "paint", "3F6FB0")
    box(b, sheet, (0.22, -0.08, 0.004), (0.24, 0.08, 0.007), "paint", "3F6FB0")
    box(b, sheet, (0.24, -0.02, 0.004), (0.33, 0.02, 0.007), "paint", "3F6FB0")
    box(b, sheet, (-0.3, -0.2, 0.004), (0.1, -0.19, 0.007), "paint", "3F6FB0")

    paper = place(frame, (0.42, 0.12, 0.78), (0.0, 0.0, -12.0))
    box(b, paper, (-0.15, -0.2, 0.0), (0.15, 0.2, 0.006), "paint", PARCHMENT)

    for index in range(3):
        b.cylinder((-0.6, 0.18 + index * 0.06, 0.81 + (index % 2) * 0.0), 0.028, 0.34 - index * 0.04, 8, "paint", srgb(("EAD9B0", PARCHMENT, "F7E08A")[index]), frame=frame, axis="X")
        box(b, frame, (-0.46 + index * 0.01, 0.15 + index * 0.06, 0.78), (-0.44 + index * 0.01, 0.21 + index * 0.06, 0.84), "paint", CLOTH_RED)

    b.cylinder((0.38, -0.25, 0.78), 0.04, 0.06, 8, "paint", srgb(INK), frame=frame)
    quill(b, frame, (0.38, -0.25, 0.82), (0.47, -0.32, 1.02))

    b.beam((0.12, -0.3, 0.79), (0.24, -0.2, 0.79), 0.008, 0.008, "metal", srgb(BRASS), frame=frame, uv=None)
    b.beam((0.12, -0.3, 0.79), (0.26, -0.33, 0.79), 0.008, 0.008, "metal", srgb(BRASS), frame=frame, uv=None)

    b.cylinder((0.55, 0.28, 0.78), 0.06, 0.02, 8, "metal", srgb(BRASS), frame=frame)
    b.cylinder((0.55, 0.28, 0.8), 0.022, 0.14, 8, "paint", srgb("F7F2E8"), frame=frame)
    gem(b, frame, (0.55, 0.28, 0.97), 0.022, "glow_warm", "FFFFFF", (1.0, 1.0, 1.7))

    for x, y in ((-0.44, -0.27), (0.24, 0.19)):
        lump(b, frame, (x, y, 0.8), 0.03, "8593B0", random.Random(3), "metal")


def chainmail_stand(b: Builder, frame: Matrix, **options) -> None:
    """T-stand with a mail shirt and coif, a rolled mail skirt at its foot."""
    mail = options.get("tint", "A9BCD4")

    plank(b, frame, (-0.3, -0.04, 0.0), (0.3, 0.04, 0.06), WOOD["escura"])
    plank(b, frame, (-0.04, -0.28, 0.0), (0.04, 0.28, 0.06), WOOD["escura"])
    plank(b, frame, (-0.03, -0.03, 0.06), (0.03, 0.03, 1.5))
    plank(b, frame, (-0.32, -0.03, 1.42), (0.32, 0.03, 1.48), WOOD["mel"], True)

    hull(b, [(sx * w, sy * d, z) for sx, sy, (w, d, z) in itertools.product((-1, 1), (-1, 1), ((0.3, 0.07, 1.47), (0.25, 0.11, 1.3), (0.24, 0.11, 0.9), (0.26, 0.1, 0.72)))], "metal", srgb(mail), frame=frame)

    for side in (-1, 1):
        hull(b, [(side * w, sy * 0.06, z) for sy, (w, z) in itertools.product((-1, 1), ((0.25, 1.47), (0.33, 1.42), (0.34, 1.12), (0.25, 1.2)))], "metal", srgb(mail), frame=frame)

    hull(b, [(sx * 0.255, sy * 0.118, z) for sx, sy, z in itertools.product((-1, 1), (-1, 1), (0.95, 1.0))], "paint", srgb(LEATHER), frame=frame)
    box(b, frame, (-0.04, -0.125, 0.94), (0.04, -0.115, 1.01), "metal", BRASS)
    hull(b, [(sx * 0.27, sy * 0.115, z) for sx, sy, z in itertools.product((-1, 1), (-1, 1), (0.72, 0.76))], "metal", srgb(BRASS), frame=frame)
    lathe(b, [(0.16, 1.44), (0.12, 1.52), (0.11, 1.62), (0.08, 1.7), (0.0, 1.73)], 8, "metal", mail, frame)
    b.cylinder((-0.25, -0.18, 0.075), 0.075, 0.5, 8, "metal", srgb(mail), frame=frame, axis="X")

    for x in (-0.18, 0.12):
        b.cylinder((x, -0.18, 0.075), 0.08, 0.03, 8, "paint", srgb(LEATHER), frame=frame, axis="X")


def fitting_platform(b: Builder, frame: Matrix, **options) -> None:
    """Round fitting dais 1.5 x 0.2: stone skirting, plank drum, red carpet with gold border, brass studs."""
    carpet = options.get("tint", "B8443C")

    b.cylinder((0.0, 0.0, 0.0), 0.75, 0.05, 12, "paint", srgb("E9D3AE"), frame=frame)
    b.cylinder((0.0, 0.0, 0.05), 0.71, 0.14, 12, "wood", srgb(WOOD["media"]), frame=frame, uv=LIGHT_GRAIN)
    b.cylinder((0.0, 0.0, 0.19), 0.62, 0.006, 12, "paint", srgb(GOLD), frame=frame)
    b.cylinder((0.0, 0.0, 0.196), 0.57, 0.006, 12, "paint", srgb(carpet), frame=frame)
    b.prism(star_outline(8, 0.3, 0.16), -0.001, 0.001, "paint", srgb(GOLD), frame=place(frame, (0.0, 0.0, 0.203), (90.0, 0.0, 0.0)))

    for index in range(8):
        angle = 2.0 * math.pi * (index + 0.5) / 8.0
        b.cylinder((0.71 * math.cos(angle), 0.71 * math.sin(angle), 0.11), 0.02, 0.02, 6, "metal", srgb(BRASS), frame=place(frame, rotation=(0.0, 0.0, 0.0)), axis="Z")


def standing_mirror(b: Builder, frame: Matrix, **options) -> None:
    """Cheval mirror 0.8 x 1.9: tilting arched glass between two posts on sledge feet, gilt frame."""
    outline = arch_outline(0.28, 0.0, 1.12, 10)
    mirror_frame = place(frame, (0.0, 0.0, 0.42), (-5.0, 0.0, 0.0))

    for x in (-0.36, 0.36):
        plank(b, frame, (x - 0.035, -0.22, 0.0), (x + 0.035, 0.22, 0.06), WOOD["escura"])
        plank(b, frame, (x - 0.025, -0.025, 0.06), (x + 0.025, 0.025, 1.45), WOOD["media"], True)
        gem(b, frame, (x, 0.0, 1.48), 0.04, "metal", GOLD)

    plank(b, frame, (-0.34, -0.02, 0.26), (0.34, 0.02, 0.31))

    for x in (-0.33, 0.31):
        b.cylinder((x, 0.0, 1.0), 0.018, 0.02, 6, "metal", srgb(GOLD), frame=frame, axis="X")

    b.prism(scaled(outline, 1.1, (0.0, 0.7)), -0.02, 0.02, "paint", srgb(BRASS), frame=mirror_frame)
    b.prism(outline, -0.026, -0.019, "paint", srgb("BFE0F0"), frame=mirror_frame)
    b.prism([(-0.2, 0.25), (-0.12, 0.25), (0.14, 0.95), (0.06, 0.95)], -0.03, -0.025, "paint", srgb("F4FBFF"), frame=mirror_frame)
    b.prism([(-0.02, 0.2), (0.02, 0.2), (0.2, 0.68), (0.16, 0.68)], -0.03, -0.025, "paint", srgb("F4FBFF"), frame=mirror_frame)
    b.prism(star_outline(4, 0.06, 0.022, (0.0, 1.42)), -0.03, 0.0, "metal", srgb(GOLD), frame=mirror_frame)


def _boot(b: Builder, frame: Matrix, x: float, z: float, shaft: str, material: str = "paint", height: float = 0.28) -> None:
    b.cylinder((x, 0.03, z), 0.05, height, 6, material, srgb(shaft), top_radius=0.058, frame=frame)
    hull(b, [(x + dx, y, z + dz) for dx, (y, dz) in itertools.product((-0.048, 0.048), ((0.075, 0.0), (0.075, 0.09), (-0.13, 0.0), (-0.12, 0.05)))], material, srgb(shaft), frame=frame)


def boots_rack(b: Builder, frame: Matrix, **options) -> None:
    """Two-tier rack 1.2 x 0.4 with pairs of boots below and steel greaves and sabatons on top."""
    for x in (-0.6, 0.56):
        plank(b, frame, (x, -0.2, 0.0), (x + 0.04, 0.2, 0.95))

    for z in (0.08, 0.5):
        plank(b, frame, (-0.56, -0.2, z - 0.04), (0.56, 0.2, z), WOOD["mel"], True)
        plank(b, frame, (-0.56, -0.2, z), (0.56, -0.18, z + 0.04), WOOD["escura"])

    plank(b, frame, (-0.6, 0.16, 0.5), (0.6, 0.2, 0.95), WOOD["media"], True)
    plank(b, frame, (-0.62, -0.2, 0.92), (0.62, 0.2, 0.96), WOOD["escura"])

    for index, (x, color) in enumerate(((-0.38, LEATHER), (0.0, "4A3A5E"), (0.38, "C08A55"))):
        _boot(b, frame, x - 0.06, 0.08, color)
        _boot(b, frame, x + 0.06, 0.08, color)

    for x in (-0.3, 0.3):
        _boot(b, frame, x - 0.06, 0.5, STEEL, "metal", 0.33)
        _boot(b, frame, x + 0.06, 0.5, STEEL, "metal", 0.33)
        gem(b, frame, (x - 0.06, -0.02, 0.73), 0.04, "metal", GOLD)
        gem(b, frame, (x + 0.06, -0.02, 0.73), 0.04, "metal", GOLD)


def _gauntlet(b: Builder, frame: Matrix, shell: str, material: str) -> None:
    """Cuff at z = 0, fingers curling at the top."""
    b.cylinder((0.0, 0.0, 0.0), 0.06, 0.12, 6, material, srgb(shell), top_radius=0.045, frame=frame)
    box(b, frame, (-0.045, -0.025, 0.12), (0.045, 0.025, 0.22), material, shell)
    b.beam((0.0, -0.01, 0.21), (0.0, -0.05, 0.28), 0.085, 0.04, material, srgb(shell), frame=frame, uv=None)
    b.beam((0.045, 0.0, 0.14), (0.07, -0.03, 0.2), 0.025, 0.025, material, srgb(shell), frame=frame, uv=None)


def gauntlet_basket(b: Builder, frame: Matrix, **options) -> None:
    """Wicker basket (Ø0.6) full of steel, gold and leather gauntlets."""
    profile = [(0.2, 0.0), (0.27, 0.15), (0.29, 0.36), (0.26, 0.36), (0.24, 0.15), (0.17, 0.04), (0.0, 0.04)]
    gauntlets = [(0.0, 0.08, -20.0, 0.0, STEEL, "metal"), (0.1, -0.06, 15.0, 120.0, GOLD, "metal"), (-0.1, -0.06, 25.0, 230.0, LEATHER, "paint"), (0.05, -0.12, 35.0, 190.0, STEEL_BRIGHT, "metal"), (-0.12, 0.08, -30.0, 60.0, "C08A55", "paint")]

    lathe(b, profile, 10, "wood", "E0BE80", frame, uv=LIGHT_GRAIN)
    b.cylinder((0.0, 0.0, 0.34), 0.295, 0.03, 10, "wood", srgb("C9A26B"), frame=frame, uv=LIGHT_GRAIN)
    lathe(b, [(0.18, 0.06), (0.24, 0.24), (0.14, 0.32), (0.0, 0.34)], 8, "paint", CLOTH_RED, frame)

    for x, y, tilt, turn, shell, material in gauntlets:
        _gauntlet(b, place(frame, (x, y, 0.22), (tilt, 0.0, turn), (1.3, 1.3, 1.3)), shell, material)


def plate_pile(b: Builder, frame: Matrix, **options) -> None:
    """Armour goods on a low oak trestle: a stack of steel sheets, a breastplate standing on a T-rack and a
    pauldron, so the plates read as wares on display and not as something dropped on the floor."""
    generator = random.Random(options.get("seed", 1))
    trestle_top = 0.42
    sheet_tones = ("C8D2E0", STEEL, "BCC8D8", STEEL_BRIGHT)

    plank(b, frame, (-0.44, -0.29, trestle_top - 0.05), (0.44, 0.29, trestle_top), WOOD["mel"], True)

    for x in (-0.36, 0.36):
        plank(b, frame, (x - 0.04, -0.25, 0.0), (x + 0.04, 0.25, 0.06), WOOD["escura"])
        plank(b, frame, (x - 0.035, -0.035, 0.06), (x + 0.035, 0.035, trestle_top - 0.05), WOOD["escura"])

    plank(b, frame, (-0.36, -0.02, 0.16), (0.36, 0.02, 0.22), WOOD["media"])

    for index, tone in enumerate(sheet_tones):
        sheet = place(frame, (-0.17 + generator.uniform(-0.03, 0.03), generator.uniform(-0.03, 0.03), trestle_top + index * 0.022), (0.0, 0.0, generator.uniform(-8.0, 8.0)))
        hull(b, [(sx * 0.2, sy * 0.17, dz) for sx, sy, dz in itertools.product((-1, 1), (-1, 1), (0.0, 0.018))], "metal", srgb(tone), frame=sheet)
        gem(b, sheet, (0.16, -0.13, 0.02), 0.01, "metal", BRASS)

    plank(b, frame, (0.2, 0.0, trestle_top), (0.24, 0.04, trestle_top + 0.38), WOOD["escura"])
    plank(b, frame, (0.08, 0.0, trestle_top + 0.32), (0.36, 0.04, trestle_top + 0.36), WOOD["escura"])
    lathe(b, [(0.15, 0.0), (0.17, 0.12), (0.155, 0.24), (0.07, 0.3)], 8, "metal", STEEL_BRIGHT, place(frame, (0.22, -0.03, trestle_top + 0.06), (0.0, 0.0, 0.0), (1.0, 0.55, 1.0)))
    b.cylinder((0.0, 0.0, 0.0), 0.162, 0.025, 8, "metal", srgb(GOLD), frame=place(frame, (0.22, -0.03, trestle_top + 0.05), scale=(1.0, 0.55, 1.0)))
    lathe(b, [(0.09, 0.0), (0.07, 0.05), (0.0, 0.075)], 6, "metal", GOLD, place(frame, (-0.3, 0.14, trestle_top + 0.09)))

    for x in (0.16, 0.22, 0.28):
        gem(b, frame, (x, -0.115, trestle_top + 0.22), 0.012, "metal", BRASS)


def weapon_barrel(b: Builder, frame: Matrix, **options) -> None:
    """Open oak barrel (Ø0.7) of swords hilt-up and spears for sale, the cheap end of the smithy's stock."""
    generator = random.Random(options.get("seed", 1))
    profile = [(0.29, 0.0), (0.33, 0.2), (0.345, 0.38), (0.33, 0.56), (0.3, 0.72), (0.27, 0.72), (0.27, 0.64)]
    swords = [(0.1, 0.08, STEEL_BRIGHT, GOLD), (-0.12, 0.05, STEEL, BRASS), (0.02, -0.13, STEEL_BRIGHT, STEEL_DARK), (-0.06, -0.02, STEEL, COPPER), (0.15, -0.08, STEEL_BRIGHT, BRONZE)]
    spears = [(-0.14, 0.13, CLOTH_RED), (0.12, 0.15, CLOTH_BLUE)]

    lathe(b, profile, 10, "wood", WOOD["media"], frame, uv=LIGHT_GRAIN)
    b.cylinder((0.0, 0.0, 0.5), 0.265, 0.012, 10, "paint", srgb(COAL), frame=frame)

    for z, radius in ((0.1, 0.326), (0.62, 0.322)):
        b.cylinder((0.0, 0.0, z), radius, 0.05, 10, "metal", srgb(IRON_DARK), frame=frame)

    for x, y, blade, hilt in swords:
        tilt = (generator.uniform(-6.0, 6.0), generator.uniform(-6.0, 6.0))
        sword(b, place(frame, (x * 0.8, y * 0.8, 1.32), (180.0 + tilt[0], tilt[1], generator.uniform(0.0, 180.0))), 1.18, blade=blade, hilt=hilt, width=0.075)

    for x, y, tassel in spears:
        spear(b, place(frame, (x, y, 0.06), (generator.uniform(-5.0, 5.0), generator.uniform(-5.0, 5.0), generator.uniform(0.0, 180.0))), 2.0, tassel=tassel)


# ---------- guild hall ----------

def quest_board(b: Builder, frame: Matrix, **options) -> None:
    """Hero quest board 3.0 x 2.0 on posts under a small roof, crowded with coloured job papers and pins."""
    generator = random.Random(options.get("seed", 1))

    for x in (-1.46, 1.46):
        plank(b, frame, (x - 0.05, 0.04, 0.0), (x + 0.05, 0.16, 2.95), WOOD["escura"])

    plank(b, frame, (-1.41, 0.1, 0.75), (1.41, 0.16, 2.75), WOOD["media"], True)
    box(b, frame, (-1.36, 0.085, 0.8), (1.36, 0.1, 2.7), "paint", "D6A56A")

    for minimum, maximum in (((-1.41, 0.06, 0.7), (1.41, 0.12, 0.8)), ((-1.41, 0.06, 2.7), (1.41, 0.12, 2.8))):
        plank(b, frame, minimum, maximum, WOOD["mel"], True)

    b.prism([(-1.55, 2.86), (1.55, 2.86), (0.0, 3.1)], 0.02, 0.16, "wood", srgb(WOOD["escura"]), frame=frame, uv=DARK_GRAIN)

    for side in (-1, 1):
        b.beam((side * 1.6, 0.0, 2.84), (0.0, 0.0, 3.16), 0.06, 0.4, "tiles", srgb("D0745A"), frame=frame, uv=None)

    box(b, frame, (-0.5, 0.04, 2.6), (0.5, 0.085, 2.84), "paint", CLOTH_BLUE)
    box(b, frame, (-0.54, 0.05, 2.58), (0.54, 0.09, 2.86), "metal", GOLD)
    b.prism(star_outline(5, 0.09, 0.04, (0.0, 2.72)), 0.025, 0.04, "metal", srgb(GOLD), frame=frame)

    cells = list(itertools.product(range(8), range(4)))
    generator.shuffle(cells)

    for index, (column, row) in enumerate(cells[:28]):
        width, height = generator.uniform(0.2, 0.28), generator.uniform(0.26, 0.38)
        x = -1.17 + column * 0.335 + generator.uniform(-0.04, 0.04)
        z = 0.98 + row * 0.42 + generator.uniform(-0.03, 0.03)
        depth = 0.083 - (index % 4) * 0.002
        sheet = place(frame, (x, depth, z), (0.0, generator.uniform(-7.0, 7.0), 0.0))
        box(b, sheet, (-width / 2.0, -0.003, -height / 2.0), (width / 2.0, 0.0, height / 2.0), "paint", generator.choice(PAPERS))
        box(b, sheet, (-width * 0.36, -0.005, height * 0.22), (width * 0.36, -0.003, height * 0.3), "paint", INK)
        box(b, sheet, (-0.015, -0.012, height / 2.0 - 0.035), (0.015, -0.003, height / 2.0 - 0.01), "paint", generator.choice((CLOTH_RED, CLOTH_BLUE, GOLD, CLOTH_GREEN)))

        if index % 3 == 0:
            b.cylinder((width * 0.22, -0.006, -height * 0.25), 0.035, 0.003, 6, "paint", srgb(generator.choice((CLOTH_RED, GOLD, CLOTH_PURPLE))), frame=sheet, axis="Y")


def guild_counter(b: Builder, frame: Matrix, **options) -> None:
    """6 m reception counter with three numbered service windows, ledgers, a bell and a loot scale."""
    windows = (-2.0, 0.0, 2.0)
    badges = (CLOTH_BLUE, CLOTH_GREEN, GOLD)

    box(b, frame, (-2.95, -0.38, 0.0), (2.95, 0.38, 0.12), "stone", STONE["dourada"])
    plank(b, frame, (-2.92, -0.35, 0.12), (2.92, 0.35, 1.0), WOOD["escura"])
    plank(b, frame, (-3.0, -0.45, 1.0), (3.0, 0.42, 1.08), WOOD["mel"], True)
    box(b, frame, (-3.0, -0.46, 1.0), (3.0, -0.44, 1.08), "metal", BRASS)

    for index in range(6):
        x = -2.45 + index * 0.98
        plank(b, frame, (x - 0.4, -0.37, 0.24), (x + 0.4, -0.35, 0.9), WOOD["mel"], True)

    box(b, frame, (-2.92, -0.38, 0.92), (2.92, -0.35, 0.96), "metal", BRASS)
    b.cylinder((0.0, -0.4, 0.57), 0.18, 0.04, 10, "metal", srgb(GOLD), frame=frame, axis="Y")
    b.prism(star_outline(5, 0.13, 0.055, (0.0, 0.57)), -0.41, -0.4, "paint", srgb(CLOTH_BLUE), frame=frame)

    for x in (-2.95, -1.0, 1.0, 2.95):
        clamp = max(-2.93, min(2.93, x))
        plank(b, frame, (clamp - 0.05, 0.12, 1.08), (clamp + 0.05, 0.22, 2.3))
        b.side_prism([(0.2, 1.08), (-0.42, 1.08), (-0.42, 1.36), (-0.22, 1.7), (0.2, 1.85)], clamp - 0.025, clamp + 0.025, "wood", srgb(WOOD["media"]), frame=frame, uv=LIGHT_GRAIN)

    plank(b, frame, (-3.0, 0.08, 2.28), (3.0, 0.26, 2.45), WOOD["escura"])
    plank(b, frame, (-3.0, 0.06, 2.42), (3.0, 0.28, 2.5), WOOD["mel"], True)

    for x, badge in zip(windows, badges):
        b.cylinder((x, 0.0, 2.36), 0.13, 0.08, 10, "metal", srgb(GOLD), frame=frame, axis="Y")
        b.cylinder((x, -0.01, 2.36), 0.1, 0.02, 10, "paint", srgb(badge), frame=frame, axis="Y")
        lantern(b, place(frame, (x + 0.55, 0.0, 1.8)), 0.48)

    ledger = place(frame, (-2.2, -0.1, 1.08), (0.0, 0.0, 6.0))
    box(b, ledger, (-0.24, -0.16, 0.0), (0.24, 0.16, 0.02), "paint", CLOTH_RED)
    box(b, ledger, (-0.22, -0.15, 0.02), (0.22, 0.15, 0.04), "paint", PARCHMENT)
    box(b, ledger, (-0.004, -0.15, 0.02), (0.004, 0.15, 0.045), "paint", "D9C08A")
    lathe(b, [(0.07, 0.0), (0.065, 0.03), (0.04, 0.08), (0.0, 0.1)], 8, "metal", GOLD, place(frame, (-1.6, -0.2, 1.08)))
    gem(b, frame, (-1.6, -0.2, 1.2), 0.02, "metal", GOLD)

    for index in range(3):
        box(b, frame, (-0.35 + index * 0.02, -0.15 + index * 0.01, 1.08 + index * 0.012), (-0.05 + index * 0.02, 0.1 + index * 0.01, 1.092 + index * 0.012), "paint", PAPERS[index])

    b.cylinder((0.3, -0.12, 1.08), 0.035, 0.06, 8, "paint", srgb(INK), frame=frame)
    quill(b, frame, (0.3, -0.12, 1.12), (0.39, -0.2, 1.32))

    b.cylinder((1.75, -0.05, 1.08), 0.1, 0.03, 8, "metal", srgb(BRASS), frame=frame)
    b.cylinder((1.75, -0.05, 1.11), 0.018, 0.38, 6, "metal", srgb(BRASS), frame=frame)
    box(b, frame, (1.5, -0.065, 1.47), (2.0, -0.035, 1.5), "metal", BRASS)

    for x in (1.53, 1.97):
        b.beam((x, -0.05, 1.47), (x, -0.05, 1.24), 0.006, 0.006, "metal", srgb(BRASS), frame=frame, uv=None)
        b.cylinder((x, -0.05, 1.2), 0.1, 0.04, 10, "metal", srgb(BRASS), top_radius=0.12, frame=frame)

    for index in range(3):
        b.cylinder((1.53, -0.05, 1.24 + index * 0.012), 0.05 - index * 0.008, 0.012, 8, "metal", srgb(GOLD), frame=frame)

    lump(b, frame, (1.97, -0.05, 1.27), 0.045, "C46AA8", random.Random(5), "metal")

    for index in range(4):
        b.cylinder((2.3 + index * 0.05, -0.2, 1.08), 0.03, 0.03 + index * 0.012, 8, "metal", srgb(GOLD), frame=frame)


def world_map_wall(b: Builder, frame: Matrix, **options) -> None:
    """Framed 2.5 x 1.8 world map (1.0-2.8 m): seas, three continents with forests and mountains, route pins."""
    generator = random.Random(options.get("seed", 1))
    continents = [((-0.62, 1.95), 0.42, "D9C78F"), ((0.45, 2.2), 0.36, "A9CF84"), ((0.55, 1.45), 0.3, "E3C08A")]

    plank(b, frame, (-1.25, 0.04, 1.0), (1.25, 0.1, 2.8), WOOD["escura"])
    box(b, frame, (-1.17, 0.03, 1.08), (1.17, 0.04, 2.72), "paint", "EAD9B0")
    box(b, frame, (-1.08, 0.025, 1.16), (1.08, 0.03, 2.64), "paint", "8FC3D9")

    for minimum, maximum in (((-1.25, 0.02, 1.0), (1.25, 0.06, 1.06)), ((-1.25, 0.02, 2.74), (1.25, 0.06, 2.8)), ((-1.25, 0.02, 1.06), (-1.19, 0.06, 2.74)), ((1.19, 0.02, 1.06), (1.25, 0.06, 2.74))):
        box(b, frame, minimum, maximum, "metal", BRASS)

    for (cx, cz), radius, color in continents:
        outline = [(cx + radius * generator.uniform(0.7, 1.15) * math.cos(angle) * 1.25, cz + radius * generator.uniform(0.7, 1.15) * math.sin(angle) * 0.85) for angle in (2.0 * math.pi * index / 11.0 for index in range(11))]
        b.prism(outline, 0.02, 0.025, "paint", srgb(color), frame=frame)

        for index in range(3):
            angle = generator.uniform(0.0, 2.0 * math.pi)
            px, pz = cx + radius * 0.45 * math.cos(angle), cz + radius * 0.35 * math.sin(angle)
            mountain = index % 2 == 0
            outline = [(px - 0.07, pz - 0.04), (px + 0.07, pz - 0.04), (px, pz + 0.07)] if mountain else [(px + 0.06 * math.cos(a), pz + 0.045 * math.sin(a)) for a in (2.0 * math.pi * step / 6.0 for step in range(6))]
            b.prism(outline, 0.016, 0.02, "paint", srgb("A07850" if mountain else "5E9A55"), frame=frame)

    route = [(-0.62, 1.95), (-0.2, 1.85), (0.15, 1.95), (0.45, 2.2), (0.6, 1.75), (0.55, 1.45)]

    for (x0, z0), (x1, z1) in zip(route, route[1:]):
        b.beam((x0, 0.014, z0), (x1, 0.014, z1), 0.012, 0.004, "paint", srgb(CLOTH_RED), frame=frame, uv=None)

    for x, z in route[::2]:
        b.cylinder((x, -0.03, z), 0.008, 0.045, 6, "metal", srgb(STEEL), frame=frame, axis="Y")
        gem(b, frame, (x, -0.035, z), 0.025, "paint", CLOTH_RED)

    b.cylinder((-0.85, 0.016, 1.38), 0.13, 0.005, 10, "paint", srgb("F2E6CF"), frame=frame, axis="Y")
    b.prism(star_outline(4, 0.17, 0.04, (-0.85, 1.38)), 0.008, 0.015, "metal", srgb(GOLD), frame=frame)

    b.prism(star_outline(3, 0.09, 0.04, (0.0, 2.88), 90.0), 0.04, 0.09, "metal", srgb(GOLD), frame=frame)


def _plaque(b: Builder, frame: Matrix, center_z: float) -> None:
    outline = heater_outline(0.3, 0.72)

    b.prism([(u, z + center_z) for u, z in scaled(outline, 1.1)], 0.31, 0.35, "wood", srgb(WOOD["mel"]), frame=frame, uv=LIGHT_GRAIN)
    b.prism([(u, z + center_z + 0.02) for u, z in outline], 0.29, 0.31, "wood", srgb(WOOD["escura"]), frame=frame, uv=DARK_GRAIN)
    box(b, frame, (-0.1, 0.27, center_z - 0.28), (0.1, 0.29, center_z - 0.22), "metal", BRASS)


def fang(b: Builder, frame: Matrix, tip: tuple, length: float, radius: float, pointing_down: bool = True) -> None:
    """Small cone tooth with its point at tip."""
    x, y, z = tip
    base_z = z if pointing_down else z - length
    b.cylinder((x, y, base_z), 0.001 if pointing_down else radius, length, 4, "paint", srgb("FFF8EA"), top_radius=radius if pointing_down else 0.001, frame=frame)


def _trophy_horns(b: Builder, frame: Matrix) -> None:
    """Horned beast frontlet: bone brow plate with sockets, long horns sweeping out, up and in."""
    hull(b, [(sx * w, y, z) for sx, (w, y, z) in itertools.product((-1, 1), ((0.13, 0.28, 2.18), (0.1, 0.28, 1.86), (0.12, 0.1, 2.14), (0.07, 0.04, 1.84), (0.05, -0.02, 1.98)))], "paint", srgb(BONE), frame=frame)

    for side in (-1, 1):
        gem(b, frame, (side * 0.085, 0.09, 2.06), 0.04, "paint", SOCKET, (0.9, 0.5, 1.0))
        points = [(side * 0.1, 0.2, 2.13), (side * 0.22, 0.17, 2.16), (side * 0.34, 0.12, 2.22), (side * 0.41, 0.06, 2.34), (side * 0.4, 0.02, 2.47), (side * 0.33, 0.0, 2.56)]
        curved_horn(b, frame, points, 0.065, (BONE, BONE, "E2CFA6", "C9A97F", "9A7A5A"))


def _trophy_skull(b: Builder, frame: Matrix) -> None:
    """Wolf-like beast skull with fangs and two short swept horns."""
    hull(b, [(sx * 0.16, y, z) for sx, (y, z) in itertools.product((-1, 1), ((0.28, 2.2), (0.28, 1.9), (0.05, 2.22), (0.08, 1.92)))] + [(0.0, 0.0, 2.27)], "paint", srgb(BONE), frame=frame)
    hull(b, [(sx * w, y, z) for sx, (w, y, z) in itertools.product((-1, 1), ((0.12, 0.06, 2.12), (0.12, 0.06, 1.94), (0.06, -0.3, 2.02), (0.06, -0.3, 1.94)))], "paint", srgb(BONE), frame=frame)
    hull(b, [(sx * w, y, z) for sx, (w, y, z) in itertools.product((-1, 1), ((0.1, 0.12, 1.9), (0.1, 0.12, 1.84), (0.05, -0.26, 1.88), (0.05, -0.26, 1.85)))], "paint", srgb("E2CFA6"), frame=frame)

    for side in (-1, 1):
        gem(b, frame, (side * 0.11, 0.03, 2.13), 0.05, "paint", SOCKET, (0.8, 0.6, 1.0))
        gem(b, frame, (side * 0.025, -0.3, 2.0), 0.015, "paint", SOCKET)
        curved_horn(b, frame, [(side * 0.12, 0.12, 2.2), (side * 0.2, 0.18, 2.32), (side * 0.22, 0.24, 2.45)], 0.04, ("E2CFA6", "9A7A5A"))
        fang(b, frame, (side * 0.05, -0.26, 1.86), 0.09, 0.016)
        fang(b, frame, (side * 0.06, -0.14, 1.89), 0.05, 0.012)


def _trophy_claw(b: Builder, frame: Matrix) -> None:
    """Severed paw of a great beast: furred wrist with a gold band, four hooked talons."""
    fur = "6B5A8A"

    b.cylinder((0.0, 0.08, 2.02), 0.12, 0.22, 8, "paint", srgb(fur), top_radius=0.14, frame=frame, axis="Y")
    b.cylinder((0.0, 0.12, 2.02), 0.135, 0.04, 8, "metal", srgb(GOLD), frame=frame, axis="Y")
    hull(b, [(sx * w, y, z) for sx, (w, y, z) in itertools.product((-1, 1), ((0.13, 0.1, 2.12), (0.12, 0.1, 1.92), (0.16, -0.06, 2.1), (0.15, -0.1, 1.95), (0.1, -0.14, 2.04)))], "paint", srgb(fur), frame=frame)

    for index, x in enumerate((-0.12, -0.04, 0.04, 0.12)):
        lift = 0.02 * (1 - abs(index - 1.5) / 1.5)
        points = [(x, -0.08, 2.04 + lift), (x * 1.15, -0.18, 2.04 + lift), (x * 1.25, -0.26, 1.97), (x * 1.25, -0.28, 1.86)]
        curved_horn(b, frame, points, 0.035, (BONE, "E2CFA6", "8A7A9A"))


TROPHIES = {"horns": _trophy_horns, "skull": _trophy_skull, "claw": _trophy_claw}


def monster_trophy(b: Builder, frame: Matrix, **options) -> None:
    """Hunting trophy on a wall plaque centred at 2.0 m; variant horns | skull | claw."""
    _plaque(b, frame, 2.0)

    TROPHIES[options.get("variant") or "horns"](b, frame)


def dragon_skull_hanging(b: Builder, frame: Matrix, **options) -> None:
    """3 m dragon skull on two chains, ceiling prop ("hang": z = 0 at the ceiling mount, drops 2.6 m).

    Sized for the 7 m double-height guild hall: the jaw bottom then sits at about 4.4 m, clearing 3 m banners,
    2.8 m wall displays and a jumping player while staying below mid-height so it reads from the floor.
    Snout points to -X, so place it with the profile towards the entrance."""
    frame = place(frame, (0.0, 0.0, -GUILD_HALL_CEILING))
    bone = options.get("tint", "E8D5B0")
    bone_shadow = "D2BC93"
    horn = ("C9A97F", "B08A66", "93704F", "77583E", "5E4532")
    snout_width = lambda x: 0.15 + (x + 1.38) / 0.78 * 0.09 if x < -0.6 else 0.24 + (x + 0.6) / 1.25 * 0.1  # noqa: E731
    jaw_top = lambda x: 4.5 + (x + 1.2) / 1.95 * 0.24  # noqa: E731
    jaw_width = lambda x: 0.12 + (x + 1.2) / 1.95 * 0.18  # noqa: E731

    hull(b, [(x, sy * w, z) for sy, (x, w, z) in itertools.product((-1, 1), ((1.25, 0.32, 5.25), (1.3, 0.3, 4.75), (0.55, 0.45, 5.3), (0.5, 0.42, 4.7), (0.9, 0.48, 5.05)))], "paint", srgb(bone), frame=frame)
    hull(b, [(x, sy * w, z) for sy, (x, w, z) in itertools.product((-1, 1), ((0.65, 0.34, 5.15), (0.65, 0.34, 4.72), (-0.6, 0.24, 5.0), (-0.6, 0.24, 4.72), (-1.38, 0.15, 4.88), (-1.38, 0.15, 4.72)))], "paint", srgb(bone), frame=frame)
    hull(b, [(x, sy * w, z) for sy, (x, w, z) in itertools.product((-1, 1), ((0.75, 0.3, 4.74), (0.75, 0.3, 4.6), (-1.2, 0.12, 4.5), (-1.2, 0.12, 4.43), (0.2, 0.26, 4.48)))], "paint", srgb(bone_shadow), frame=frame)
    hull(b, [(x, sy * 0.06, z) for sy, (x, z) in itertools.product((-1, 1), ((0.6, 5.12), (0.6, 5.2), (-1.2, 4.9), (-1.2, 4.94)))], "paint", srgb(bone_shadow), frame=frame)

    for side in (-1, 1):
        hull(b, [(x, side * w, z) for x, w, z in ((0.8, 0.4, 5.32), (0.35, 0.36, 5.24), (0.6, 0.5, 5.14), (0.55, 0.3, 5.36))], "paint", srgb(bone_shadow), frame=frame)
        gem(b, frame, (0.55, side * 0.44, 5.0), 0.15, "paint", SOCKET, (1.0, 0.35, 0.75))
        gem(b, frame, (-1.28, side * 0.1, 4.86), 0.05, "paint", SOCKET, (1.0, 0.8, 0.6))
        curved_horn(b, frame, [(1.1, side * 0.28, 5.2), (1.35, side * 0.38, 5.4), (1.5, side * 0.5, 5.65), (1.52, side * 0.6, 5.9), (1.45, side * 0.64, 6.08)], 0.15, horn)
        curved_horn(b, frame, [(1.15, side * 0.42, 4.85), (1.4, side * 0.55, 4.8), (1.55, side * 0.62, 4.68)], 0.08, horn[1:])
        curved_horn(b, frame, [(0.85, side * 0.44, 5.2), (1.05, side * 0.6, 5.25), (1.2, side * 0.68, 5.22)], 0.05, horn[1:])

        for index in range(6):
            x = -1.25 + index * 0.33
            fang(b, frame, (x, side * (snout_width(x) - 0.04), 4.6 - 0.02 * (index == 1)), 0.13 + 0.05 * (index == 1), 0.035)

        for index in range(4):
            x = -1.05 + index * 0.4
            fang(b, frame, (x, side * (jaw_width(x) - 0.03), jaw_top(x) + 0.1), 0.11, 0.03, pointing_down=False)

    for x, height in ((0.75, 0.28), (1.0, 0.24), (1.22, 0.18)):
        b.prism([(x - 0.12, 5.2), (x + 0.1, 5.2), (x + 0.08, 5.2 + height)], -0.025, 0.025, "paint", srgb(horn[2]), frame=frame)

    for x in (-0.3, 1.0):
        chain(b, frame, x, 0.0, 5.08 if x > 0 else 4.95, GUILD_HALL_CEILING - 0.06, 0.26, IRON_DARK)
        box(b, frame, (x - 0.15, -0.15, GUILD_HALL_CEILING - 0.06), (x + 0.15, 0.15, GUILD_HALL_CEILING), "metal", IRON_DARK)


def guild_banner(b: Builder, frame: Matrix, **options) -> None:
    """1.0 x 3.0 swallow-tailed guild banner on a gilt rod at 4.1 m (6 m hall), original winged-star crest."""
    cloth = options.get("tint", CLOTH_BLUE)
    outline = [(-0.45, 4.02), (0.45, 4.02), (0.45, 1.12), (0.0, 1.4), (-0.45, 1.12)]

    b.cylinder((-0.55, 0.0, 4.1), 0.025, 1.1, 8, "wood", srgb(WOOD["escura"]), frame=frame, axis="X", uv=DARK_GRAIN)

    for x in (-0.53, 0.53):
        gem(b, frame, (x, 0.0, 4.1), 0.045, "metal", GOLD)

    for x in (-0.3, 0.3):
        box(b, frame, (x - 0.02, -0.02, 4.08), (x + 0.02, 0.06, 4.13), "metal", IRON_DARK)

    b.prism([(u * 1.06, z - (0.06 if z < 1.5 else 0.0)) for u, z in outline], 0.0, 0.01, "paint", srgb(GOLD), frame=frame)
    b.prism(outline, -0.01, 0.0, "paint", srgb(cloth), frame=frame)

    b.cylinder((0.0, -0.02, 3.0), 0.3, 0.012, 12, "paint", srgb(GOLD), frame=frame, axis="Y")
    b.cylinder((0.0, -0.025, 3.0), 0.25, 0.006, 12, "paint", srgb("F2EEE6"), frame=frame, axis="Y")
    b.prism(star_outline(4, 0.2, 0.06, (0.0, 3.0)), -0.03, -0.025, "paint", srgb(cloth), frame=frame)

    for side in (-1, 1):
        wing = [(side * 0.08, 2.48), (side * 0.36, 2.62), (side * 0.32, 2.5), (side * 0.38, 2.42), (side * 0.3, 2.36), (side * 0.32, 2.26), (side * 0.08, 2.36)]
        b.prism(wing, -0.016, -0.01, "paint", srgb(GOLD), frame=frame)

    b.prism(star_outline(5, 0.1, 0.045, (0.0, 2.4)), -0.016, -0.01, "paint", srgb(GOLD), frame=frame)

    for z in (1.75, 1.85):
        box(b, frame, (-0.45, -0.015, z), (0.45, -0.01, z + 0.035), "paint", GOLD)

    for x in (-0.45, 0.45):
        b.cylinder((x, -0.005, 0.98), 0.03, 0.12, 6, "paint", srgb(GOLD), top_radius=0.012, frame=frame)


def rank_board(b: Builder, frame: Matrix, **options) -> None:
    """Adventurer rank board (1.0-2.6 m): arched header crest, six rank rows S to E with name plates."""
    ranks = (GOLD, CLOTH_RED, CLOTH_PURPLE, "4F8FC9", "7FC46A", BRONZE)

    plank(b, frame, (-0.62, 0.02, 1.0), (0.62, 0.05, 2.25), WOOD["escura"])
    b.prism(arch_outline(0.62, 2.2, 2.25, 10), 0.02, 0.05, "wood", srgb(WOOD["escura"]), frame=frame, uv=DARK_GRAIN)
    b.prism(arch_outline(0.54, 2.2, 2.25, 10), 0.01, 0.02, "paint", srgb(CLOTH_BLUE), frame=frame)
    b.prism(star_outline(5, 0.18, 0.08, (0.0, 2.45)), 0.0, 0.01, "metal", srgb(GOLD), frame=frame)
    box(b, frame, (-0.58, 0.01, 1.05), (0.58, 0.02, 2.2), "paint", PARCHMENT)

    for index, color in enumerate(ranks):
        z = 2.08 - index * 0.18
        b.cylinder((-0.46, -0.01, z), 0.065, 0.02, 8, "metal", srgb(color), frame=frame, axis="Y")
        box(b, frame, (-0.38, 0.0, z - 0.012), (0.54, 0.01, z + 0.012), "paint", color)

        for plate in range(3 - index % 2):
            x = -0.3 + plate * 0.28
            box(b, frame, (x, -0.004, z + 0.02), (x + 0.24, 0.01, z + 0.07), "paint", "FFF8EA")


def registry_crystal(b: Builder, frame: Matrix, **options) -> None:
    """Registration crystal: carved stone pedestal with a glowing rune ring, gold cradle, floating cyan crystal."""
    generator = random.Random(options.get("seed", 1))
    profile = [(0.38, 0.0), (0.38, 0.1), (0.3, 0.14), (0.22, 0.2), (0.17, 0.3), (0.15, 0.85), (0.2, 0.92), (0.28, 0.98), (0.28, 1.05)]

    lathe(b, profile, 8, "paint", "F2E8D4", frame)
    b.cylinder((0.0, 0.0, 0.3), 0.172, 0.05, 8, "metal", srgb(GOLD), frame=frame)
    b.cylinder((0.0, 0.0, 0.88), 0.17, 0.04, 8, "metal", srgb(GOLD), frame=frame)
    b.cylinder((0.0, 0.0, 1.05), 0.25, 0.012, 12, "glow_cyan", srgb("FFFFFF"), frame=frame)
    b.cylinder((0.0, 0.0, 1.05), 0.2, 0.02, 12, "paint", srgb("F2E8D4"), frame=frame)

    for index in range(4):
        angle = math.pi / 8.0 + index * math.pi / 2.0
        rune = place(frame, (0.16 * math.cos(angle), 0.16 * math.sin(angle), 0.0), (0.0, 0.0, math.degrees(angle)))
        box(b, rune, (-0.004, -0.02, 0.4), (0.008, 0.02, 0.8), "glow_cyan", "FFFFFF")

    for index in range(3):
        angle = 2.0 * math.pi * index / 3.0 + math.pi / 2.0
        b.beam((0.17 * math.cos(angle), 0.17 * math.sin(angle), 1.06), (0.09 * math.cos(angle), 0.09 * math.sin(angle), 1.38), 0.03, 0.03, "metal", srgb(GOLD), frame=frame, uv=None)

    hull(b, [(0.0, 0.0, 1.2), (0.0, 0.0, 1.9)] + [(0.13 * math.cos(a), 0.13 * math.sin(a), z) for a, z in itertools.product((math.pi * index / 3.0 for index in range(6)), (1.45, 1.62))], "glow_cyan", srgb("FFFFFF"), frame=frame)

    for index in range(3):
        angle = 2.0 * math.pi * index / 3.0 + generator.uniform(0.0, 0.5)
        gem(b, frame, (0.28 * math.cos(angle), 0.28 * math.sin(angle), 1.5 + index * 0.1), 0.04, "glow_cyan", "FFFFFF", (0.6, 0.6, 1.6))


def _cup(b: Builder, frame: Matrix, hex_color: str = GOLD) -> None:
    lathe(b, [(0.07, 0.0), (0.06, 0.02), (0.02, 0.05), (0.02, 0.12), (0.07, 0.16), (0.09, 0.26), (0.08, 0.27)], 8, "metal", hex_color, frame)

    for side in (-1, 1):
        b.beam((side * 0.08, 0.0, 0.24), (side * 0.12, 0.0, 0.17), 0.015, 0.012, "metal", srgb(hex_color), frame=frame, uv=None)


def _crown(b: Builder, frame: Matrix) -> None:
    b.cylinder((0.0, 0.0, 0.0), 0.09, 0.06, 8, "metal", srgb(GOLD), frame=frame)

    for index in range(5):
        angle = 2.0 * math.pi * index / 5.0
        b.cylinder((0.085 * math.cos(angle), 0.085 * math.sin(angle), 0.06), 0.02, 0.06, 4, "metal", srgb(GOLD), top_radius=0.0, frame=frame)

    gem(b, frame, (0.0, -0.09, 0.03), 0.02, "paint", CLOTH_RED)


def trophy_case(b: Builder, frame: Matrix, **options) -> None:
    """Glass display cabinet of guild trophies: golden cups, crown, gems, a fang, a glowing orb and a medal."""
    plank(b, frame, (-0.8, -0.3, 0.0), (0.8, 0.3, 0.3), WOOD["escura"])
    plank(b, frame, (-0.8, -0.3, 1.95), (0.8, 0.3, 2.1), WOOD["escura"])
    box(b, frame, (-0.8, -0.31, 0.26), (0.8, 0.31, 0.3), "metal", GOLD)
    box(b, frame, (-0.8, -0.31, 1.95), (0.8, 0.31, 1.99), "metal", GOLD)
    box(b, frame, (-0.76, 0.24, 0.3), (0.76, 0.28, 1.95), "paint", "2F4E8E")

    for x, y in itertools.product((-0.78, 0.78), (-0.28, 0.26)):
        plank(b, frame, (x - 0.025, y - 0.02, 0.3), (x + 0.025, y + 0.02, 1.95), WOOD["mel"], True)

    for z in (0.85, 1.4):
        plank(b, frame, (-0.76, -0.25, z - 0.03), (0.76, 0.24, z), WOOD["mel"], True)

    box(b, frame, (-0.76, -0.29, 0.3), (0.76, -0.28, 1.95), "vitrine", "FFFFFF")

    for x in (-0.79, 0.79):
        box(b, frame, (x - 0.005, -0.26, 0.3), (x + 0.005, 0.24, 1.95), "vitrine", "FFFFFF")

    _cup(b, place(frame, (0.0, 0.0, 0.3), scale=(1.4, 1.4, 1.4)))
    _cup(b, place(frame, (-0.45, 0.02, 0.3)), STEEL_BRIGHT)

    for x, color in ((0.38, CLOTH_RED), (0.56, "7FC46A")):
        b.cylinder((x, 0.0, 0.3), 0.05, 0.08, 6, "metal", srgb(BRASS), frame=frame)
        gem(b, frame, (x, 0.0, 0.43), 0.05, "paint", color, (1.0, 1.0, 1.3))

    _crown(b, place(frame, (-0.4, 0.0, 0.85)))
    curved_horn(b, frame, [(0.15, 0.05, 0.86), (0.2, 0.02, 1.0), (0.3, 0.0, 1.1), (0.42, -0.02, 1.13)], 0.05, (BONE, "E2CFA6", "C9A97F"))
    b.cylinder((0.5, 0.1, 0.85), 0.012, 0.16, 6, "metal", srgb(BRASS), frame=frame)
    b.cylinder((0.5, 0.12, 1.12), 0.12, 0.01, 12, "metal", srgb(STEEL_BRIGHT), frame=place(frame, (0.0, 0.0, 0.0), (0.0, 0.0, 0.0)), axis="Y")

    b.cylinder((0.3, 0.0, 1.4), 0.06, 0.06, 8, "metal", srgb(GOLD), top_radius=0.04, frame=frame)
    b.sphere((0.3, 0.0, 1.55), 0.1, "glow_pink", srgb("FFFFFF"), frame=frame, segments=8)
    box(b, frame, (-0.6, -0.08, 1.4), (-0.34, 0.12, 1.47), "paint", CLOTH_PURPLE)
    box(b, frame, (-0.58, -0.07, 1.47), (-0.36, 0.11, 1.5), "paint", "F7E08A")
    b.cylinder((-0.05, 0.12, 1.4), 0.008, 0.25, 6, "paint", srgb(CLOTH_RED), frame=frame)
    b.cylinder((-0.05, 0.1, 1.56), 0.07, 0.015, 10, "metal", srgb(GOLD), frame=frame, axis="Y")


def weapon_rental_rack(b: Builder, frame: Matrix, **options) -> None:
    """Guild rental rack: tagged loaner weapons in a slotted frame under a hanging coin sign, a bow on the side."""
    tags = GOODS_PALETTE

    for x in (-0.76, 0.76):
        plank(b, frame, (x - 0.04, -0.06, 0.0), (x + 0.04, 0.06, 1.95), WOOD["escura"])
        plank(b, frame, (x - 0.05, -0.24, 0.0), (x + 0.05, 0.24, 0.07), WOOD["escura"])

    plank(b, frame, (-0.72, -0.14, 0.07), (0.72, 0.14, 0.14), WOOD["media"], True)
    plank(b, frame, (-0.72, -0.05, 0.92), (0.72, 0.05, 0.98), WOOD["mel"], True)
    plank(b, frame, (-0.8, -0.06, 1.88), (0.8, 0.06, 1.95), WOOD["mel"], True)

    for x in (-0.3, 0.3):
        b.beam((x, 0.0, 1.88), (x, 0.0, 1.8), 0.008, 0.008, "metal", srgb(IRON_DARK), frame=frame, uv=None)

    box(b, frame, (-0.42, -0.02, 1.5), (0.42, 0.02, 1.8), "paint", CLOTH_GREEN)
    box(b, frame, (-0.44, -0.015, 1.48), (0.44, 0.015, 1.82), "wood", WOOD["mel"], LIGHT_GRAIN)
    b.cylinder((0.0, -0.05, 1.65), 0.1, 0.03, 10, "metal", srgb(GOLD), frame=frame, axis="Y")

    weapons = [
        (-0.62, lambda f: spear(b, f, 1.75, STEEL, WOOD["mel"], CLOTH_BLUE)),
        (-0.42, lambda f: sword(b, f, 0.95, STEEL, BRONZE, LEATHER)),
        (-0.2, lambda f: axe(b, f, 0.85, STEEL, WOOD["media"])),
        (0.04, lambda f: mace(b, f, 0.8, STEEL, WOOD["escura"], BRASS)),
        (0.26, lambda f: sword(b, f, 1.0, STEEL_BRIGHT, STEEL_DARK, CLOTH_RED)),
        (0.6, lambda f: spear(b, f, 1.7, STEEL, WOOD["escura"], GOLD)),
    ]

    for index, (x, build) in enumerate(weapons):
        build(place(frame, (x, -0.07, 0.1)))
        box(b, frame, (x - 0.035, -0.1, 0.8), (x + 0.035, -0.09, 0.88), "paint", tags[index])

    bow(b, place(frame, (0.82, 0.0, 0.25), (0.0, 0.0, 90.0)), 1.3)


def group_table(b: Builder, frame: Matrix, **options) -> None:
    """Party table 1.6 x 0.9 with four chairs pulled out, mugs, a map, bread, dice and a candle."""
    generator = random.Random(options.get("seed", 1))

    plank(b, frame, (-0.8, -0.45, 0.72), (0.8, 0.45, 0.78), WOOD["mel"], True)

    for x, y in itertools.product((-0.7, 0.7), (-0.36, 0.36)):
        plank(b, frame, (x - 0.04, y - 0.04, 0.0), (x + 0.04, y + 0.04, 0.72))

    plank(b, frame, (-0.7, -0.03, 0.12), (0.7, 0.03, 0.18))

    for x, side in itertools.product((-0.4, 0.4), (-1, 1)):
        chair = place(frame, (x + generator.uniform(-0.05, 0.05), side * 0.68, 0.0), (0.0, 0.0, (0.0 if side < 0 else 180.0) + generator.uniform(-8.0, 8.0)))
        plank(b, chair, (-0.21, -0.2, 0.42), (0.21, 0.2, 0.46), WOOD["media"], True)

        for lx, ly in itertools.product((-0.18, 0.18), (-0.17, 0.17)):
            plank(b, chair, (lx - 0.025, ly - 0.025, 0.0), (lx + 0.025, ly + 0.025, 0.42))

        for lx in (-0.18, 0.18):
            plank(b, chair, (lx - 0.025, -0.2, 0.46), (lx + 0.025, -0.15, 0.98))

        plank(b, chair, (-0.2, -0.2, 0.78), (0.2, -0.16, 0.92), WOOD["mel"], True)
        box(b, chair, (-0.17, -0.17, 0.46), (0.17, 0.15, 0.48), "paint", (CLOTH_RED, CLOTH_BLUE, CLOTH_GREEN, CLOTH_PURPLE)[int(x > 0) * 2 + int(side > 0)])

    for x, y in ((-0.45, -0.25), (0.42, -0.22), (-0.38, 0.24), (0.45, 0.26)):
        b.cylinder((x, y, 0.78), 0.045, 0.13, 8, "wood", srgb(WOOD["mel"]), frame=frame, uv=LIGHT_GRAIN)
        b.cylinder((x, y, 0.89), 0.042, 0.015, 8, "paint", srgb("FFF8EA"), frame=frame)
        box(b, frame, (x + 0.04, y - 0.01, 0.81), (x + 0.075, y + 0.01, 0.88), "wood", WOOD["escura"], DARK_GRAIN)

    sheet = place(frame, (0.0, 0.0, 0.78), (0.0, 0.0, -8.0))
    box(b, sheet, (-0.28, -0.2, 0.0), (0.28, 0.2, 0.004), "paint", "EAD9B0")
    box(b, sheet, (-0.2, -0.1, 0.004), (0.05, 0.12, 0.007), "paint", "A9CF84")
    box(b, sheet, (0.08, -0.15, 0.004), (0.22, 0.02, 0.007), "paint", "8FC3D9")

    b.cylinder((-0.1, 0.27, 0.78), 0.12, 0.02, 10, "wood", srgb(WOOD["escura"]), frame=frame, uv=DARK_GRAIN)
    b.sphere((-0.1, 0.27, 0.84), 0.08, "paint", srgb("D9A060"), scale=(1.4, 0.9, 0.6), frame=frame, segments=8)

    for index, color in enumerate((PARCHMENT, CLOTH_RED)):
        dice = place(frame, (0.25 + index * 0.06, 0.12, 0.78), (0.0, 0.0, 20.0 * index + 10.0))
        box(b, dice, (-0.018, -0.018, 0.0), (0.018, 0.018, 0.036), "paint", color)

    b.cylinder((0.62, 0.0, 0.78), 0.05, 0.02, 8, "metal", srgb(BRASS), frame=frame)
    b.cylinder((0.62, 0.0, 0.8), 0.02, 0.12, 8, "paint", srgb("F7F2E8"), frame=frame)
    gem(b, frame, (0.62, 0.0, 0.95), 0.02, "glow_warm", "FFFFFF", (1.0, 1.0, 1.7))


def wanted_posters(b: Builder, frame: Matrix, **options) -> None:
    """Five bounty posters on a plank (1.15-2.4 m): monster silhouette, red header, gold reward seal."""
    generator = random.Random(options.get("seed", 1))
    posters = [(-0.56, 1.92, 0.36, 0.48), (-0.1, 1.98, 0.34, 0.44), (0.4, 1.9, 0.38, 0.5), (-0.34, 1.42, 0.34, 0.44), (0.2, 1.4, 0.36, 0.46)]

    plank(b, frame, (-0.8, 0.02, 1.15), (0.8, 0.04, 2.4), WOOD["media"], True)

    for x in (-0.76, 0.76):
        plank(b, frame, (x - 0.04, 0.0, 1.15), (x + 0.04, 0.04, 2.4), WOOD["escura"])

    for index, (x, z, width, height) in enumerate(posters):
        sheet = place(frame, (x, 0.02 - index * 0.002, z), (0.0, generator.uniform(-6.0, 6.0), 0.0))
        box(b, sheet, (-width / 2.0, -0.004, -height / 2.0), (width / 2.0, 0.0, height / 2.0), "paint", ("EAD9B0", PARCHMENT)[index % 2])
        box(b, sheet, (-width * 0.42, -0.006, height * 0.3), (width * 0.42, -0.004, height * 0.44), "paint", CLOTH_RED)

        silhouette = [(width * 0.3 * generator.uniform(0.6, 1.1) * math.cos(angle), height * 0.04 + height * 0.2 * generator.uniform(0.5, 1.1) * math.sin(angle)) for angle in (2.0 * math.pi * step / 9.0 for step in range(9))]
        b.prism(silhouette, -0.006, -0.004, "paint", srgb(INK), frame=sheet)
        gem(b, sheet, (-width * 0.08, -0.007, height * 0.08), 0.018, "paint", "F7E08A")
        gem(b, sheet, (width * 0.08, -0.007, height * 0.08), 0.018, "paint", "F7E08A")

        box(b, sheet, (-width * 0.35, -0.006, -height * 0.4), (width * 0.1, -0.004, -height * 0.33), "paint", INK)
        b.cylinder((width * 0.28, -0.008, -height * 0.36), 0.04, 0.004, 8, "metal", srgb(GOLD), frame=sheet, axis="Y")
        box(b, sheet, (-0.012, -0.012, height / 2.0 - 0.04), (0.012, -0.004, height / 2.0 - 0.016), "metal", BRASS)


def masterwork_plinth_a(b: Builder, frame: Matrix, **options) -> None:
    """Showpiece of the smithy: a stepped stone plinth carrying a glass case with a jewelled sword lying on red
    velvet, brass corner posts, a plaque on the front and a pair of velvet-rope stanchions."""
    lathe(b, [(0.44, 0.0), (0.44, 0.1), (0.36, 0.14), (0.34, 0.2), (0.3, 0.24), (0.3, 0.8), (0.34, 0.84), (0.34, 0.88), (0.4, 0.92), (0.4, 0.98)], 8, "stone", "D9C8A8", frame)
    bevel_box(b, frame, (-0.34, -0.22, 0.98), (0.34, 0.22, 1.02), "5A3A26", bevel=0.008)
    box(b, frame, (-0.3, -0.18, 1.02), (0.3, 0.18, 1.045), "paint", "A8323C")

    for tassel_x in (-0.32, 0.32):
        b.sphere((tassel_x, -0.2, 1.03), 0.025, "metal", srgb(GOLD), frame=frame, segments=6)

    sword(b, place(frame, (-0.27, 0.0, 1.06), (0.0, 90.0, 0.0)), 0.56, STEEL_BRIGHT, GOLD, CLOTH_BLUE, jewel="glow_cyan")
    b.box((-0.32, -0.2, 1.02), (0.32, 0.2, 1.42), "vitrine", srgb("FFFFFF"), frame=frame)

    for post_x, post_y in itertools.product((-0.32, 0.31), (-0.2, 0.19)):
        box(b, frame, (post_x, post_y, 1.02), (post_x + 0.015, post_y + 0.015, 1.42), "metal", BRASS)

    for rail_low, rail_high in (((-0.33, -0.21, 1.42), (0.33, -0.19, 1.45)), ((-0.33, 0.19, 1.42), (0.33, 0.21, 1.45)), ((-0.33, -0.21, 1.42), (-0.31, 0.21, 1.45)), ((0.31, -0.21, 1.42), (0.33, 0.21, 1.45))):
        box(b, frame, rail_low, rail_high, "metal", BRASS)

    gem(b, frame, (0.0, 0.0, 1.5), 0.035, "metal", GOLD, (1.0, 1.0, 1.3))
    box(b, frame, (-0.1, -0.31, 0.5), (0.1, -0.295, 0.58), "metal", BRASS)


def hanging_tool_rack_a(b: Builder, frame: Matrix, **options) -> None:
    """Smith's overhead rack, z = 0 at the ceiling: two chains carry a bar with hooks for tongs, hammers, horseshoes,
    a ladle and a coil of chain."""
    bar_z = -1.1

    for chain_x in (-0.82, 0.82):
        chain(b, frame, chain_x, 0.0, bar_z, 0.0, 0.1, IRON_DARK)

    bevel_box(b, frame, (-0.95, -0.05, bar_z - 0.06), (0.95, 0.05, bar_z), WOOD["escura"], bevel=0.01)

    for hook_x in (-0.78, -0.5, -0.22, 0.06, 0.34, 0.62, 0.84):
        box(b, frame, (hook_x - 0.006, -0.05, bar_z - 0.1), (hook_x + 0.006, -0.036, bar_z), "metal", IRON_DARK)

    tongs(b, place(frame, (-0.78, -0.06, bar_z - 0.62)), 0.55)
    smith_hammer(b, place(frame, (-0.5, -0.06, bar_z - 0.5)), 0.4, STEEL_DARK, WOOD["mel"], 1.1)
    tongs(b, place(frame, (-0.22, -0.06, bar_z - 0.7)), 0.6)
    smith_hammer(b, place(frame, (0.06, -0.06, bar_z - 0.42)), 0.34, STEEL, WOOD["media"], 0.9)

    for shoe_x in (0.28, 0.4):
        ring(b, (shoe_x, -0.06, bar_z - 0.14), 0.065, 0.013, "metal", IRON_DARK, frame, sides=8, tube_sides=4, axis="Y")

    b.cylinder((0.62, -0.06, bar_z - 0.5), 0.012, 0.42, 6, "wood", srgb(WOOD["mel"]), frame=frame)
    lathe(b, [(0.001, bar_z - 0.62), (0.05, bar_z - 0.6), (0.06, bar_z - 0.54), (0.04, bar_z - 0.5)], 8, "metal", COPPER, frame, base=(0.62, -0.06, 0.0))
    ring(b, (0.84, -0.06, bar_z - 0.3), 0.1, 0.014, "metal", IRON_DARK, frame, sides=10, tube_sides=4, axis="Y")
    ring(b, (0.84, -0.06, bar_z - 0.3), 0.07, 0.012, "metal", IRON_DARK, frame, sides=10, tube_sides=4, axis="Y")


def workbench_vise_a(b: Builder, frame: Matrix, **options) -> None:
    """Heavy smith's workbench 1.6 x 0.7: thick planked top, chunky chamfered legs with a low shelf of ingots,
    an iron vise on the front corner, a drawer, hammers and files on a tool strip along the back edge."""
    top = 0.92
    bevel_box(b, frame, (-0.8, -0.35, top - 0.1), (0.8, 0.35, top), WOOD["media"], bevel=0.02, light=True)

    for seam_y in (-0.12, 0.12):
        box(b, frame, (-0.79, seam_y - 0.004, top - 0.001), (0.79, seam_y + 0.004, top + 0.001), "wood", WOOD["escura"], DARK_GRAIN)

    for leg_x, leg_y in itertools.product((-0.72, 0.66), (-0.28, 0.22)):
        bevel_box(b, frame, (leg_x, leg_y, 0.0), (leg_x + 0.08, leg_y + 0.08, top - 0.1), WOOD["escura"], bevel=0.012)

    for shelf_x in (-0.64, 0.58):
        bevel_box(b, frame, (shelf_x, -0.26, 0.2), (shelf_x + 0.06, 0.26, 0.26), WOOD["mel"], bevel=0.008, light=True)

    bevel_box(b, frame, (-0.66, -0.28, 0.2), (0.66, 0.24, 0.26), WOOD["mel"], bevel=0.01, light=True)
    bevel_box(b, frame, (-0.66, -0.3, top - 0.24), (0.66, -0.26, top - 0.1), WOOD["mel"], bevel=0.008, light=True)

    for drawer_from in (-0.64, 0.0):
        bevel_box(b, frame, (drawer_from + 0.04, -0.32, top - 0.22), (drawer_from + 0.6, -0.28, top - 0.12), WOOD["media"], bevel=0.006, light=True)
        b.sphere((drawer_from + 0.32, -0.335, top - 0.17), 0.018, "metal", srgb(BRASS), frame=frame, segments=6)

    for ingot_index in range(4):
        ingot(b, frame, (-0.3 + (ingot_index % 2) * 0.22, -0.05, 0.26 + (ingot_index // 2) * 0.045), STEEL if ingot_index % 2 else COPPER)

    box(b, frame, (0.46, -0.3, top), (0.64, -0.18, top + 0.14), "metal", IRON_DARK)
    box(b, frame, (0.43, -0.34, top + 0.1), (0.5, -0.14, top + 0.16), "metal", STEEL_DARK)
    b.cylinder((0.56, -0.34, top + 0.07), 0.014, 0.2, 6, "metal", srgb(IRON_DARK), frame=frame, axis="Y")
    b.cylinder((0.46, -0.39, top + 0.07), 0.01, 0.2, 6, "metal", srgb(IRON_DARK), frame=frame, axis="X")

    strip_z = top + 0.02
    box(b, frame, (-0.76, 0.22, strip_z), (0.0, 0.32, strip_z + 0.025), "wood", WOOD["escura"], DARK_GRAIN)
    smith_hammer(b, place(frame, (-0.5, -0.12, strip_z + 0.012), (0.0, 90.0, 20.0)), 0.3, STEEL_DARK, WOOD["mel"], 0.9)
    tongs(b, place(frame, (-0.2, -0.05, strip_z + 0.012), (0.0, 90.0, -15.0)), 0.4)

    for file_index in range(3):
        box(b, frame, (-0.76 + file_index * 0.06, 0.24, strip_z + 0.025), (-0.745 + file_index * 0.06, 0.26, strip_z + 0.25 - file_index * 0.03), "metal", STEEL_DARK)

    lump(b, frame, (0.2, 0.1, top + 0.03), 0.05, STEEL_DARK, random.Random(5), "metal")
    lump(b, frame, (-0.05, 0.12, top + 0.025), 0.04, COPPER, random.Random(6), "metal")


ARMOUR_STYLES_A = {
    "plate": dict(plate="C9D6E8", trim=GOLD, cloth=CLOTH_RED, helm="great", material="metal"),
    "knight_gold": dict(plate="EDCB62", trim="FFF1B8", cloth=CLOTH_BLUE, helm="winged", material="metal"),
    "mail": dict(plate="A9BCD4", trim=BRASS, cloth=CLOTH_RED, helm="dome", material="metal"),
    "leather": dict(plate=LEATHER, trim=LEATHER_DARK, cloth=CLOTH_GREEN, helm="leather", material="paint"),
}


def _limb_a(b: Builder, frame: Matrix, start: tuple, end: tuple, radius: float, top_radius: float, material: str, tint: str) -> None:
    limb_frame, length = along(frame, start, end)
    b.cylinder((0.0, 0.0, 0.0), radius, length, 8, material, srgb(tint), top_radius=top_radius, frame=limb_frame)


def armor_stand_a(b: Builder, frame: Matrix, variant: str = "plate", **options) -> None:
    """Armour on a turned oak stand: brass-ringed base, post, greaves with knee cops, overlapping skirt lames or a
    tabard, a ridged cuirass, belt, gorget, three-lame pauldrons, bent arms with elbow cops and fists, a helmet
    with plume; the gold knight also has a cape. Variant plate | knight_gold | mail | leather."""
    style = ARMOUR_STYLES_A[variant]
    plate, trim, cloth, material = style["plate"], style["trim"], style["cloth"], style["material"]
    lathe(b, [(0.001, 0.0), (0.3, 0.0), (0.31, 0.025), (0.29, 0.06), (0.12, 0.085), (0.07, 0.13), (0.001, 0.15)], 12, "wood", WOOD["escura"], frame, uv=DARK_GRAIN)
    ring(b, (0.0, 0.0, 0.045), 0.3, 0.014, "metal", BRASS, frame, sides=12, tube_sides=4)
    b.cylinder((0.0, 0.0, 0.1), 0.04, 0.9, 8, "wood", srgb(WOOD["escura"]), frame=frame)

    for side in (-1, 1):
        x = side * 0.1
        hull(b, [(x + dx, y, z) for dx, (y, z) in itertools.product((-0.055, 0.055), ((0.08, 0.08), (0.08, 0.15), (-0.16, 0.08), (-0.16, 0.12)))], "metal" if material == "metal" else "paint", srgb(trim), frame=frame)
        b.cylinder((x, 0.0, 0.14), 0.052, 0.4, 8, material, srgb(plate if material == "metal" else LEATHER_DARK), top_radius=0.066, frame=frame)
        b.sphere((x, -0.02, 0.55), 0.068, material, srgb(trim), frame=frame, segments=6)
        b.cylinder((x, 0.0, 0.52), 0.068, 0.46, 8, material, srgb(plate), top_radius=0.086, frame=frame)

    if variant in ("plate", "knight_gold"):
        for lame in range(4):
            lathe(b, [(0.21 + lame * 0.02, 1.0 - lame * 0.085), (0.235 + lame * 0.02, 0.9 - lame * 0.085)], 12, material, plate if lame % 2 == 0 else trim, place(frame, scale=(1.0, 0.78, 1.0)))
    else:
        tabard = [(-0.16, 1.38), (0.16, 1.38), (0.15, 0.58), (0.0, 0.52), (-0.15, 0.58)]

        for depth in (-0.165, 0.165):
            b.prism(tabard, depth - 0.008, depth + 0.008, "paint", srgb(cloth), frame=frame)

        b.prism(EMBLEMS["cross"](0.2), -0.178, -0.172, "paint", srgb(GOLD if variant == "mail" else LEATHER_DARK), frame=place(frame, (0.0, 0.0, 1.0)))

    lathe(b, [(0.172, 0.98), (0.155, 1.08), (0.19, 1.2), (0.205, 1.31), (0.18, 1.4), (0.1, 1.47), (0.001, 1.48)], 12, material, plate, place(frame, scale=(1.0, 0.76, 1.0)))
    box(b, frame, (-0.013, -0.168, 1.05), (0.013, -0.152, 1.4), "metal" if material == "metal" else "paint", trim)

    for band_z in (1.12, 1.24):
        ring(b, (0.0, 0.0, band_z), 0.185 if band_z > 1.15 else 0.165, 0.008, "metal" if material == "metal" else "paint", trim, place(frame, scale=(1.0, 0.76, 1.0)), sides=12, tube_sides=4)

    _belt(b, frame, 0.97, LEATHER_DARK, trim if material == "metal" else BRASS, 0.176)
    lathe(b, [(0.125, 1.42), (0.118, 1.5), (0.09, 1.56)], 10, material, trim if variant != "mail" else plate, frame)

    for side in (-1, 1):
        for lame in range(3):
            lathe(b, [(0.13 - lame * 0.01, -0.02), (0.14 - lame * 0.01, 0.0), (0.1, 0.05), (0.001, 0.075)], 8, material, trim if lame == 2 else plate, place(frame, (side * 0.235, 0.0, 1.42 - lame * 0.045), (0.0, side * 24.0, 0.0)))

        shoulder, elbow, wrist = (side * 0.27, 0.0, 1.36), (side * 0.31, 0.0, 1.07), (side * 0.3, -0.07, 0.84)
        _limb_a(b, frame, shoulder, elbow, 0.05, 0.043, material, plate)
        b.sphere(elbow, 0.058, material, srgb(trim), frame=frame, segments=6)
        _limb_a(b, frame, elbow, wrist, 0.046, 0.054, material, plate)
        b.sphere((wrist[0], wrist[1] - 0.01, wrist[2] - 0.05), 0.055, "paint", srgb(LEATHER_DARK), frame=frame, segments=6)

    b.cylinder((0.0, 0.0, 1.48), 0.075, 0.1, 8, "paint", srgb(LEATHER), frame=frame)
    helmet(b, place(frame, (0.0, 0.0, 1.55)), style["helm"], plate if style["helm"] != "leather" else LEATHER, trim, cloth)

    if variant == "knight_gold":
        cape = [(-0.26, 1.42), (0.26, 1.42), (0.3, 0.42), (0.0, 0.48), (-0.3, 0.42)]
        b.prism(cape, 0.17, 0.19, "paint", srgb(cloth), frame=frame)
        b.prism([(u * 1.04, z - 0.03) for u, z in cape], 0.19, 0.2, "paint", srgb(GOLD), frame=frame)


def armor_stand_row_a(b: Builder, frame: Matrix, **options) -> None:
    """Oak plinth 2.4 x 0.8 with a moulded edge and brass rail carrying three mannequins (leather, gold knight, mail)."""
    bevel_box(b, frame, (-1.2, -0.4, 0.0), (1.2, 0.4, 0.15), WOOD["escura"], bevel=0.02)
    bevel_box(b, frame, (-1.22, -0.42, 0.11), (1.22, 0.42, 0.15), WOOD["mel"], bevel=0.01, light=True)
    box(b, frame, (-1.2, -0.43, 0.12), (1.2, -0.41, 0.14), "metal", BRASS)

    for x, variant in ((-0.8, "leather"), (0.0, "knight_gold"), (0.8, "mail")):
        armor_stand_a(b, place(frame, (x, 0.05, 0.15), scale=(0.9, 0.9, 0.9)), variant=variant)


# @@NEW


def iron_stock_rack(b: Builder, frame: Matrix, **options) -> None:
    """Rack of iron stock: two trestles with three rails and round and square bars of every length leaning in it."""
    generator = random.Random(options.get("seed", 3))
    wood = WOOD["escura"]

    for x in (-0.75, 0.75):
        plank(b, frame, (x - 0.05, 0.1, 0.0), (x + 0.05, 0.2, 1.9), wood)
        plank(b, frame, (x - 0.05, -0.28, 0.0), (x + 0.05, -0.18, 0.25), wood)
        b.beam((x, -0.23, 0.22), (x, 0.15, 1.6), 0.08, 0.08, "wood", srgb(wood), frame=frame)

    for z in (0.5, 1.15, 1.75):
        plank(b, frame, (-0.85, 0.1, z - 0.04), (0.85, 0.2, z + 0.04), WOOD["media"])

    for index in range(22):
        x = -0.68 + 1.36 * index / 21 + generator.uniform(-0.02, 0.02)
        top = generator.uniform(1.2, 2.3)
        foot = generator.uniform(-0.25, -0.12)
        thickness = generator.choice((0.022, 0.03, 0.04))
        tint = generator.choice((IRON_DARK, "5A5466", "6E6878", "3E3A48"))
        b.beam((x, foot, 0.02), (x + generator.uniform(-0.03, 0.03), 0.12, top), thickness, thickness, "metal", srgb(tint), frame=frame)


def horseshoe(b: Builder, frame: Matrix, center: tuple, size: float, tint: str) -> None:
    """One horseshoe hung by its toe on a nail, opening down."""
    x, z = center
    steel = srgb(tint)

    b.beam((x - size, -0.03, z - size * 1.1), (x - size * 0.75, -0.03, z + size * 0.55), 0.025, size * 0.45, "metal", steel, frame=frame)
    b.beam((x + size, -0.03, z - size * 1.1), (x + size * 0.75, -0.03, z + size * 0.55), 0.025, size * 0.45, "metal", steel, frame=frame)
    b.beam((x - size * 0.8, -0.03, z + size * 0.5), (x + size * 0.8, -0.03, z + size * 0.5), 0.025, size * 0.45, "metal", steel, frame=frame)
    box(b, frame, (x - 0.008, -0.06, z + size * 0.72), (x + 0.008, 0.0, z + size * 0.78), "metal", IRON_DARK)


def horseshoe_board(b: Builder, frame: Matrix, **options) -> None:
    """Farrier's board on the wall: rows of new horseshoes on nails by size, a rasp and pincers hung at the end."""
    generator = random.Random(options.get("seed", 5))
    spots = list(itertools.product(range(4), range(7)))

    plank(b, frame, (-0.75, 0.0, 0.6), (0.75, 0.06, 1.85), WOOD["media"])
    plank(b, frame, (-0.8, -0.02, 1.85), (0.8, 0.08, 1.92), WOOD["escura"])

    for row, column in spots:
        size = 0.06 + 0.012 * (3 - row)
        horseshoe(b, frame, (-0.6 + column * 0.17, 0.78 + row * 0.3), size, generator.choice((STEEL_DARK, IRON_DARK, "6E6878")))

    tongs(b, place(frame, (0.66, -0.06, 1.2), (0.0, 0.0, 0.0)), 0.45)


def wagon_wheel_lean(b: Builder, frame: Matrix, **options) -> None:
    """A spoked cart wheel waiting for its new iron tyre, leaning on the wall."""
    radius = options.get("radius", 0.62)
    lean = place(frame, (0.0, -0.12, radius + 0.02), (0.0, -12.0, 0.0))
    rim = [(radius * math.cos(2.0 * math.pi * index / 14), radius * math.sin(2.0 * math.pi * index / 14)) for index in range(15)]
    wood = srgb(WOOD["media"])

    for (x_from, z_from), (x_to, z_to) in zip(rim, rim[1:]):
        b.beam((x_from, 0.0, z_from), (x_to, 0.0, z_to), 0.07, 0.08, "wood", wood, frame=lean)

    for index in range(12):
        angle = 2.0 * math.pi * index / 12
        b.beam((0.0, 0.0, 0.0), (radius * 0.95 * math.cos(angle), 0.0, radius * 0.95 * math.sin(angle)), 0.035, 0.04, "wood", wood, frame=lean)

    b.cylinder((0.0, -0.12, 0.0), 0.11, 0.24, 10, "wood", srgb(WOOD["escura"]), frame=lean, axis="Y")


PROPS = {
    "iron_stock_rack": {"build": iron_stock_rack, "size": (1.7, 0.6, 2.3), "solid": True},
    "horseshoe_board": {"build": horseshoe_board, "size": (1.6, 0.12, 1.92), "solid": False},
    "wagon_wheel_lean": {"build": wagon_wheel_lean, "size": (1.4, 0.45, 1.3), "solid": True},
    "forge": {"build": forge, "size": (2.0, 1.7, 4.5), "solid": True, "clearance": 1.5, "light": ((0.0, -0.25, 1.3), "FF8A3A", 3.0, 7.0)},
    "bellows": {"build": bellows, "size": (1.2, 0.5, 0.5), "solid": True},
    "anvil_block": {"build": anvil_block, "size": (0.8, 0.6, 0.95), "solid": True},
    "quench_barrel": {"build": quench_barrel, "size": (0.8, 0.8, 0.85), "solid": True},
    "grindstone": {"build": grindstone, "size": (1.0, 0.6, 1.0), "solid": True},
    "tool_wall_rack": {"build": tool_wall_rack, "size": (1.5, 0.2, 1.85), "solid": False},
    "sword_wall": {"build": sword_wall, "size": (3.0, 0.3, 2.85), "solid": False},
    "spear_rack": {"build": spear_rack, "size": (1.0, 0.3, 2.2), "solid": True},
    "axe_mace_rack": {"build": axe_mace_rack, "size": (1.4, 0.45, 1.2), "solid": True},
    "shield_wall": {"build": shield_wall, "size": (2.5, 0.2, 2.8), "solid": False},
    "helmet_shelf": {"build": helmet_shelf, "size": (1.56, 0.5, 1.9), "solid": True},
    "armor_stand": {"build": armor_stand, "size": (0.7, 0.6, 1.95), "solid": True, "variants": ["plate", "leather", "mail", "knight_gold"]},
    "armor_stand_row": {"build": armor_stand_row, "size": (2.4, 0.82, 2.15), "solid": True},
    "coal_pile": {"build": coal_pile, "size": (1.2, 1.0, 0.6), "solid": True},
    "ingot_crates": {"build": ingot_crates, "size": (1.4, 0.8, 0.5), "solid": True},
    "giant_sword": {"build": giant_sword, "size": (0.9, 0.25, 3.1), "solid": False},
    "blade_shelf": {"build": blade_shelf, "size": (1.44, 0.5, 1.6), "solid": True},
    "plans_table": {"build": plans_table, "size": (1.4, 0.8, 1.05), "solid": True},
    "chainmail_stand": {"build": chainmail_stand, "size": (0.7, 0.6, 1.75), "solid": True},
    "fitting_platform": {"build": fitting_platform, "size": (1.5, 1.5, 0.22), "solid": True},
    "standing_mirror": {"build": standing_mirror, "size": (0.8, 0.5, 1.9), "solid": True},
    "boots_rack": {"build": boots_rack, "size": (1.24, 0.4, 0.96), "solid": True},
    "gauntlet_basket": {"build": gauntlet_basket, "size": (0.6, 0.6, 0.6), "solid": True},
    "plate_pile": {"build": plate_pile, "size": (0.9, 0.6, 0.85), "solid": True},
    "weapon_barrel": {"build": weapon_barrel, "size": (0.7, 0.7, 2.1), "solid": True},
    "quest_board": {"build": quest_board, "size": (3.2, 0.4, 3.2), "solid": True, "clearance": 1.8},
    "guild_counter": {"build": guild_counter, "size": (6.0, 0.9, 2.5), "solid": True, "clearance": 2.0},
    "world_map_wall": {"build": world_map_wall, "size": (2.5, 0.2, 3.0), "solid": False},
    "monster_trophy": {"build": monster_trophy, "size": (0.9, 0.7, 2.6), "solid": False, "variants": ["horns", "skull", "claw"]},
    "dragon_skull_hanging": {"build": dragon_skull_hanging, "size": (3.2, 1.4, 2.6), "solid": False, "hang": True},
    "guild_banner": {"build": guild_banner, "size": (1.1, 0.12, 4.15), "solid": False},
    "rank_board": {"build": rank_board, "size": (1.3, 0.1, 2.9), "solid": False},
    "registry_crystal": {"build": registry_crystal, "size": (0.8, 0.8, 1.95), "solid": True, "light": ((0.0, 0.0, 1.6), "8FD8FF", 1.5, 5.0)},
    "trophy_case": {"build": trophy_case, "size": (1.6, 0.62, 2.1), "solid": True},
    "weapon_rental_rack": {"build": weapon_rental_rack, "size": (1.8, 0.5, 1.95), "solid": True},
    "group_table": {"build": group_table, "size": (1.7, 2.0, 1.0), "solid": True},
    "wanted_posters": {"build": wanted_posters, "size": (1.6, 0.1, 2.4), "solid": False},
    "masterwork_plinth_a": {"build": masterwork_plinth_a, "size": (0.9, 0.9, 1.6), "solid": True},
    "hanging_tool_rack_a": {"build": hanging_tool_rack_a, "size": (1.9, 0.2, 1.8), "solid": False, "hang": True},
    "workbench_vise_a": {"build": workbench_vise_a, "size": (1.6, 0.8, 1.2), "solid": True},
    "armor_stand_a": {"build": armor_stand_a, "size": (0.84, 0.64, 2.0), "solid": True, "variants": list(ARMOUR_STYLES_A)},
    "armor_stand_row_a": {"build": armor_stand_row_a, "size": (2.4, 0.86, 2.2), "solid": True},
}
