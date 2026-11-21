"""Arcane shop props (block D): magic, alchemy, books, jewels, bank, herbs, tailor and general store.

Runs inside Blender, imported by build_prop_sheet.py and the shop layout engine. Every prop follows the
contract in shop_props_common.py: def name(b, frame, **options) -> None, local X width centred on 0, Y depth
centred on 0 with the customer side at -Y and the wall at +Y, Z up from the floor; built with Builder
primitives only, always with frame=frame. Ceiling props ("hang": True) put local z = 0 at the ceiling mount
and grow down (negative z); size[2] is how far they reach down. "clearance" is the free space needed in front.
"""

import itertools
import math
import random
import sys
from pathlib import Path

from mathutils import Matrix, Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))

from build_town_houses import BRICK, IRON, STONE, TRIM_SMOOTH_BAND, WOOD, WOOD_DARK_BAND, WOOD_LIGHT_BAND, Builder, srgb  # noqa: E402,F401
from shop_props_common import GLASS_PALETTE, GOODS_PALETTE, filled_row, filled_shelves, lathe, ring  # noqa: E402,F401

CEILING = 3.6
GOLD = "E8B64A"
BRASS = "D9A441"
COPPER = "C8693F"
SILVER = "C9D3E8"
DARK_IRON = "3A3B5E"  # forged iron with a violet-blue cast: never a dead grey
PARCHMENT = "EFDDB4"
BONE = "EFE3C8"
CANDLE_WAX = "F7EBD0"
NAVY = "23306B"
PLUM = "6A2E6E"
WINE = "8E2F45"
TEAL = "1F6B6B"
LEAF = "7FC46A"
DEEP_LEAF = "3F8A50"
LILAC_STONE = "C9B3EA"
MARBLE = "F3E6DA"  # warm cream marble (flat paint: the trim texture reads grey)
DARK_WOOD = "8B5A3C"  # structural wood: WOOD["escura"] reads black under the dark wood band
PLUM_WOOD = "9A78B8"  # magic-shop plum wood, light enough to keep its hue
GLOWS = ("glow_cyan", "glow_pink", "glow_green", "glow_amber", "glow_warm")
GLOW_HEX = {"glow_cyan": "8FD8FF", "glow_pink": "F59AD8", "glow_green": "7FE08A", "glow_amber": "FFB347", "glow_warm": "FFD9A0", "glow_ember": "FF7A2A"}
BOOK_COLORS = ("8E2F45", "28356E", "2F6B4F", "6A2E6E", "B5533F", "C08A55", "1F6B6B", "D9A441", "4F8FC9", "C46AA8")
FLOWER_COLORS = ("F25C7A", "F2B13C", "B57FE0", "F2F0E6", "E0884A", "4FB0D9", "F59AD8")
MATERIAL_ALIASES = {  # alias -> (Builder material, uv mapping)
    "wood": ("wood", ("band", *WOOD_DARK_BAND, 1.5)),
    "wood_light": ("wood", ("band", *WOOD_LIGHT_BAND, 1.5)),
    "trim": ("trim", ("band", *TRIM_SMOOTH_BAND, 1.5)),
}


# ---------- primitive wrappers (material alias + hex colour, always in the prop frame) ----------

def resolve(material: str, color: str = None) -> tuple:
    """Builder material key, linear tint and uv mapping for a material alias and a hex colour (glows: white)."""
    key, uv = MATERIAL_ALIASES.get(material, (material, None))

    return key, srgb(color or "FFFFFF"), uv


def at(frame: Matrix, offset: tuple, degrees: float = 0.0, axis: str = "Z") -> Matrix:
    """Child frame moved to offset and turned around one local axis."""
    return frame @ Matrix.Translation(offset) @ Matrix.Rotation(math.radians(degrees), 4, axis)


def box(b: Builder, frame: Matrix, minimum: tuple, maximum: tuple, material: str, color: str = None):
    key, tint, uv = resolve(material, color)

    return b.box(minimum, maximum, key, tint, frame=frame, uv=uv)


def block(b: Builder, frame: Matrix, center: tuple, size: tuple, material: str, color: str = None):
    minimum = tuple(middle - extent / 2.0 for middle, extent in zip(center, size))
    maximum = tuple(middle + extent / 2.0 for middle, extent in zip(center, size))

    return box(b, frame, minimum, maximum, material, color)


def rod(b: Builder, frame: Matrix, start: tuple, end: tuple, thickness: float, material: str, color: str = None, depth: float = None):
    key, tint, uv = resolve(material, color)

    return b.beam(start, end, thickness, depth or thickness, key, tint, frame=frame, uv=uv)


def cyl(b: Builder, frame: Matrix, base: tuple, radius: float, height: float, material: str, color: str = None, sides: int = 8, top: float = None, axis: str = "Z"):
    key, tint, uv = resolve(material, color)

    return b.cylinder(base, radius, height, sides, key, tint, top_radius=top, frame=frame, uv=uv, axis=axis)


def ball(b: Builder, frame: Matrix, center: tuple, radius: float, material: str, color: str = None, scale: tuple = (1.0, 1.0, 1.0), segments: int = 8):
    key, tint, _ = resolve(material, color)

    return b.sphere(center, radius, key, tint, scale=scale, frame=frame, segments=segments)


def spin(b: Builder, frame: Matrix, profile: list, material: str, color: str = None, sides: int = 8, base: tuple = (0.0, 0.0, 0.0), closed: bool = False):
    """lathe() with a material alias: profile [(radius, z), ...] turned around local Z at base."""
    key, _, uv = resolve(material)

    return lathe(b, profile, sides, key, color or "FFFFFF", frame, base=base, closed=closed, uv=uv)


def hoop(b: Builder, frame: Matrix, center: tuple, radius: float, tube: float, material: str, color: str = None, sides: int = 12, tube_sides: int = 4, axis: str = "Z"):
    key, _, _ = resolve(material)

    return ring(b, center, radius, tube, key, color or "FFFFFF", frame, sides=sides, tube_sides=tube_sides, axis=axis)


def flat_ring(b: Builder, frame: Matrix, radius: float, width: float, material: str, color: str = None, sides: int = 32, height: float = 0.012, z: float = 0.0):
    """Ring painted on the floor: a low ridge of triangular section (6 tris per side)."""
    profile = [(radius - width / 2.0, z), (radius + width / 2.0, z), (radius, z + height)]

    return spin(b, frame, profile, material, color, sides=sides, closed=True)


def gem(b: Builder, frame: Matrix, center: tuple, radius: float, material: str, color: str = None, scale: tuple = (1.0, 1.0, 1.4)):
    """Octahedron (8 tris): cut gems, sparkles, tiny flames."""
    x, y, z = center
    size_x, size_y, size_z = (radius * factor for factor in scale)
    points = [(x + size_x, y, z), (x - size_x, y, z), (x, y + size_y, z), (x, y - size_y, z), (x, y, z + size_z), (x, y, z - size_z)]
    key, tint, _ = resolve(material, color)

    return b.hull(points, key, tint, frame=frame)


def sparkle(b: Builder, frame: Matrix, center: tuple, radius: float, material: str = "glow_warm") -> None:
    """Four-point star facing -Y: a tall and a wide flat diamond."""
    gem(b, frame, center, radius, material, scale=(0.25, 0.2, 1.0))
    gem(b, frame, center, radius, material, scale=(1.0, 0.2, 0.25))


def crystal(b: Builder, frame: Matrix, base: tuple, radius: float, height: float, material: str, color: str = None, tilt: tuple = (0.0, 0.0)):
    """Hexagonal crystal with a pointed tip, standing at base and tilted (degrees around X, then Y)."""
    placed = frame @ Matrix.Translation(base) @ Matrix.Rotation(math.radians(tilt[0]), 4, "X") @ Matrix.Rotation(math.radians(tilt[1]), 4, "Y")
    corners = [(math.cos(math.pi / 3.0 * side), math.sin(math.pi / 3.0 * side)) for side in range(6)]
    points = [(radius * 0.8 * x, radius * 0.8 * y, 0.0) for x, y in corners] + [(radius * x, radius * y, height * 0.7) for x, y in corners] + [(0.0, 0.0, height)]
    key, tint, _ = resolve(material, color)

    return b.hull(points, key, tint, frame=placed)


def candle(b: Builder, frame: Matrix, base: tuple, height: float, radius: float = 0.03, color: str = CANDLE_WAX) -> None:
    x, y, z = base

    cyl(b, frame, base, radius, height, "paint", color, sides=6)
    gem(b, frame, (x, y, z + height + 0.035), 0.022, "glow_warm", scale=(0.8, 0.8, 1.6))


def rng(options: dict) -> random.Random:
    return random.Random(options.get("seed", 1))


# ---------- shared furniture ----------

def table(b: Builder, frame: Matrix, width: float, depth: float, height: float, tone: str = WOOD["media"], top_tone: str = WOOD["mel"], leg: float = 0.07, inset: float = 0.06, shelf: bool = False) -> float:
    """Table with a bevelled top, four turned legs, a beaded apron, stretchers and an optional low shelf; returns the
    top height."""
    half_x, half_y = width / 2.0, depth / 2.0
    leg_x, leg_y = half_x - inset - leg / 2.0, half_y - inset - leg / 2.0
    radius = leg * 0.5
    turning = [(radius * 0.8, 0.0), (radius * 1.1, 0.04), (radius * 0.8, 0.1), (radius * 0.85, height * 0.42), (radius * 1.15, height * 0.48), (radius * 0.85, height * 0.54), (radius * 0.85, height - 0.3), (radius * 1.25, height - 0.2), (radius * 1.25, height - 0.06)]

    box(b, frame, (-half_x, -half_y, height - 0.05), (half_x, half_y, height), "wood_light", top_tone)
    box(b, frame, (-half_x + 0.015, -half_y + 0.015, height - 0.075), (half_x - 0.015, half_y - 0.015, height - 0.05), "wood", tone)

    for sign_x, sign_y in itertools.product((-1.0, 1.0), repeat=2):
        spin(b, frame, turning, "wood", tone, sides=6, base=(sign_x * leg_x, sign_y * leg_y, 0.0))

    for sign_y in (-1.0, 1.0):
        box(b, frame, (-leg_x, sign_y * leg_y - 0.012, height - 0.2), (leg_x, sign_y * leg_y + 0.012, height - 0.075), "wood", tone)
        box(b, frame, (-leg_x, sign_y * leg_y - 0.02, height - 0.2), (leg_x, sign_y * leg_y + 0.02, height - 0.18), "wood_light", top_tone)

    for sign_x in (-1.0, 1.0):
        box(b, frame, (sign_x * leg_x - 0.012, -leg_y, height - 0.2), (sign_x * leg_x + 0.012, leg_y, height - 0.075), "wood", tone)

    if width > 1.2:
        rod(b, frame, (-leg_x, 0.0, 0.2), (leg_x, 0.0, 0.2), 0.035, "wood", tone)

    for sign_x in (-1.0, 1.0):
        rod(b, frame, (sign_x * leg_x, -leg_y, 0.2), (sign_x * leg_x, leg_y, 0.2), 0.035, "wood", tone)

    if shelf:
        box(b, frame, (-leg_x, -leg_y, 0.14), (leg_x, leg_y, 0.18), "wood", tone)

    return height


def shelf_unit(b: Builder, frame: Matrix, width: float, depth: float, height: float, boards: list, tone: str = DARK_WOOD, back: str = None, crown: str = None, bays: int = 1) -> list:
    """Open wall shelf against +Y: sides, bay dividers, boards at the given heights (their top z), optional
    painted back panel and a crown moulding (hex colour). Returns the top z of every board."""
    half_x, half_y = width / 2.0, depth / 2.0
    side = 0.05
    board = 0.03
    dividers = [-half_x + width * bay / bays for bay in range(1, bays)]

    for x in (-half_x + side / 2.0, half_x - side / 2.0, *dividers):
        block(b, frame, (x, 0.0, height / 2.0), (side, depth, height), "wood", tone)

    for z in boards:
        box(b, frame, (-half_x + side, -half_y, z - board), (half_x - side, half_y - 0.02, z), "wood_light", tone)

    if back:
        box(b, frame, (-half_x + side, half_y - 0.02, 0.0), (half_x - side, half_y, height), "paint", back)

    if crown:
        box(b, frame, (-half_x, -half_y, height - 0.08), (half_x, half_y, height), "wood", crown)

    box(b, frame, (-half_x + side, -half_y, 0.0), (half_x - side, half_y - 0.02, 0.08), "wood", tone)

    return boards


def book(b: Builder, frame: Matrix, x: float, y: float, z: float, width: float, depth: float, height: float, color: str, band: bool = False) -> None:
    """Standing book, spine to -Y, its left side at x; band adds a gold spine band."""
    box(b, frame, (x, y - depth / 2.0, z), (x + width, y + depth / 2.0, z + height), "paint", color)

    if band:
        box(b, frame, (x - 0.002, y - depth / 2.0 - 0.004, z + height * 0.72), (x + width + 0.002, y - depth / 2.0 + 0.01, z + height * 0.8), "metal", GOLD)


def book_row(b: Builder, frame: Matrix, x_from: float, x_to: float, y: float, z: float, depth: float, max_height: float, generator: random.Random, palette: tuple = BOOK_COLORS) -> None:
    """A shelf of books with gaps; the last book leans on its neighbour when there is room."""
    cursor = x_from
    last_height = max_height

    while cursor < x_to - 0.12:
        width = generator.uniform(0.05, 0.1)
        height = max_height * generator.uniform(0.7, 1.0)

        if generator.random() < 0.9:
            book(b, frame, cursor, y, z, width, depth * generator.uniform(0.8, 1.0), height, generator.choice(palette), band=generator.random() < 0.2)
            last_height = height

        cursor += width + 0.004

    lean = math.radians(18.0)
    height = min(max_height * 0.85, last_height / math.cos(lean))
    pivot = cursor + height * math.sin(lean)

    if pivot + 0.06 < x_to:
        book(b, at(frame, (pivot, 0.0, z), -18.0, "Y"), 0.0, y, 0.0, 0.05, depth * 0.85, height, generator.choice(palette))


FLASK_PROFILES = {  # unit profiles (radius, height) for flask(): body then neck
    "round": [(0.55, 0.0), (1.0, 0.25), (0.85, 0.5), (0.3, 0.62), (0.3, 1.0)],
    "tall": [(0.9, 0.0), (1.0, 0.55), (0.35, 0.7), (0.35, 1.0)],
    "cone": [(1.0, 0.0), (0.3, 0.7), (0.3, 1.0)],
    "squat": [(0.85, 0.0), (1.0, 0.35), (0.45, 0.6), (0.45, 1.0)],
}


def flask(b: Builder, frame: Matrix, base: tuple, radius: float, height: float, material: str, color: str = None, shape: str = "tall", cork: bool = False, sides: int = 6) -> None:
    profile = [(radius * unit_radius, height * unit_height) for unit_radius, unit_height in FLASK_PROFILES[shape]]

    spin(b, frame, profile, material, color, sides=sides, base=base)

    if cork:
        cyl(b, frame, (base[0], base[1], base[2] + height), radius * 0.36, height * 0.14, "wood_light", WOOD["mel"], sides=6)


# ---------- magic shop ----------

def crystal_ball_pedestal(b: Builder, frame: Matrix, **options) -> None:
    """Lilac marble pedestal with a gold cup and three claws holding a glowing crystal ball."""
    stone = options.get("tint", LILAC_STONE)

    spin(b, frame, [(0.28, 0.0), (0.28, 0.07), (0.22, 0.12), (0.12, 0.2), (0.08, 0.32), (0.08, 0.85), (0.13, 0.93), (0.19, 1.0), (0.19, 1.06), (0.12, 1.1)], "paint", stone)
    hoop(b, frame, (0.0, 0.0, 0.88), 0.085, 0.02, "metal", GOLD, sides=8)
    spin(b, frame, [(0.06, 1.1), (0.15, 1.15), (0.16, 1.19)], "metal", GOLD)

    for claw in range(3):
        angle = math.radians(90.0 + claw * 120.0)
        rod(b, frame, (0.14 * math.cos(angle), 0.14 * math.sin(angle), 1.15), (0.16 * math.cos(angle), 0.16 * math.sin(angle), 1.33), 0.03, "metal", GOLD)

    ball(b, frame, (0.0, 0.0, 1.32), 0.17, "glow_cyan", segments=10)

    for spark in range(3):
        angle = math.radians(30.0 + spark * 120.0)
        gem(b, frame, (0.26 * math.cos(angle), 0.26 * math.sin(angle), 1.3 + 0.07 * spark), 0.025, "glow_pink")


STAFF_HEADS = ("orb", "crystal", "crescent", "prongs")


def staff_head(b: Builder, frame: Matrix, x: float, top: float, kind: str, glow: str) -> None:
    gem_center = (x, 0.0, top + 0.08)
    heads = {
        "orb": lambda: (cyl(b, frame, (x, 0.0, top - 0.02), 0.03, 0.05, "metal", GOLD, sides=6, top=0.045), ball(b, frame, (x, 0.0, top + 0.08), 0.055, glow, segments=6)),
        "crystal": lambda: (cyl(b, frame, (x, 0.0, top - 0.02), 0.026, 0.04, "metal", BRASS, sides=6), crystal(b, frame, (x, 0.0, top + 0.01), 0.035, 0.16, glow)),
        "crescent": lambda: (hoop(b, frame, (x, 0.0, top + 0.08), 0.065, 0.012, "metal", GOLD, sides=8, tube_sides=3, axis="Y"), gem(b, frame, gem_center, 0.035, glow)),
        "prongs": lambda: ([rod(b, frame, (x, 0.0, top - 0.02), (x + lean, 0.0, top + 0.14), 0.014, "metal", SILVER) for lean in (-0.06, 0.0, 0.06)], gem(b, frame, gem_center, 0.04, glow)),
    }

    heads[kind]()


def staff_rack(b: Builder, frame: Matrix, **options) -> None:
    """Rack of ten staffs with glowing heads in a plum wood stand (back rail against the wall)."""
    generator = rng(options)
    woods = (DARK_WOOD, WOOD["media"], WOOD["mel"], PLUM_WOOD)

    box(b, frame, (-0.9, -0.2, 0.0), (0.9, 0.2, 0.16), "wood", PLUM_WOOD)
    box(b, frame, (-0.92, -0.22, 0.12), (0.92, -0.18, 0.17), "metal", GOLD)
    box(b, frame, (-0.88, 0.03, 1.28), (0.88, 0.25, 1.38), "wood", PLUM_WOOD)
    box(b, frame, (-0.88, 0.025, 1.36), (0.88, 0.04, 1.39), "metal", GOLD)

    for side in (-1.0, 1.0):
        block(b, frame, (side * 0.86, 0.14, 0.8), (0.08, 0.22, 1.6), "wood", PLUM_WOOD)
        gem(b, frame, (side * 0.86, 0.14, 1.66), 0.06, "metal", GOLD)

    for staff in range(10):
        x = -0.72 + staff * 0.16
        top = 1.62 + generator.uniform(0.0, 0.2)
        cyl(b, frame, (x, 0.0, 0.1), 0.022, top - 0.1, "wood", woods[staff % len(woods)], sides=6)
        staff_head(b, frame, x, top, STAFF_HEADS[staff % len(STAFF_HEADS)], GLOWS[(staff * 3) % len(GLOWS)])


def wand_case(b: Builder, frame: Matrix, **options) -> None:
    """Plum cabinet with a velvet-lined glass top holding seven wands with glowing tips."""
    generator = rng(options)
    lining = options.get("tint", WINE)

    for sign_x, sign_y in itertools.product((-1.0, 1.0), repeat=2):
        block(b, frame, (sign_x * 0.54, sign_y * 0.2, 0.05), (0.08, 0.08, 0.1), "metal", GOLD)

    box(b, frame, (-0.6, -0.25, 0.1), (0.6, 0.25, 0.78), "wood", PLUM_WOOD)

    for drawer_x in (-0.29, 0.29):
        box(b, frame, (drawer_x - 0.25, -0.26, 0.4), (drawer_x + 0.25, -0.24, 0.68), "wood_light", WOOD["mel"])
        gem(b, frame, (drawer_x, -0.27, 0.54), 0.025, "metal", GOLD, scale=(1.0, 1.0, 1.0))

    box(b, frame, (-0.6, -0.25, 0.78), (0.6, 0.25, 0.8), "paint", lining)
    box(b, frame, (-0.62, -0.27, 0.78), (0.62, -0.24, 0.84), "metal", GOLD)
    box(b, frame, (-0.62, 0.24, 0.78), (0.62, 0.27, 0.84), "metal", GOLD)
    box(b, frame, (-0.62, -0.24, 0.78), (-0.59, 0.24, 0.84), "metal", GOLD)
    box(b, frame, (0.59, -0.24, 0.78), (0.62, 0.24, 0.84), "metal", GOLD)
    box(b, frame, (-0.59, -0.24, 0.84), (0.59, 0.24, 0.95), "vitrine")

    for wand in range(7):
        x = -0.48 + wand * 0.16
        placed = at(frame, (x, 0.0, 0.815), generator.uniform(-18.0, 18.0))
        cyl(b, placed, (0.0, -0.16, 0.0), 0.012, 0.32, "wood", (DARK_WOOD, WOOD["mel"], PLUM_WOOD)[wand % 3], sides=6, axis="Y")
        cyl(b, placed, (0.0, 0.08, 0.0), 0.018, 0.09, "metal", (GOLD, SILVER)[wand % 2], sides=6, axis="Y")
        gem(b, placed, (0.0, -0.175, 0.012), 0.022, GLOWS[wand % len(GLOWS)], scale=(1.0, 1.4, 1.0))


def summoning_circle(b: Builder, frame: Matrix, **options) -> None:
    """Glowing summoning circle painted on the floor: two rings, a hexagram, runes and six candles."""
    cyl(b, frame, (0.0, 0.0, 0.0), 1.25, 0.006, "paint", options.get("tint", "2B2152"), sides=24)
    flat_ring(b, frame, 1.16, 0.06, "glow_cyan", z=0.006)
    flat_ring(b, frame, 0.82, 0.04, "glow_cyan", z=0.006)
    flat_ring(b, frame, 0.22, 0.03, "glow_pink", sides=12, z=0.006)

    tips = [(0.82 * math.cos(math.radians(90.0 + 60.0 * tip)), 0.82 * math.sin(math.radians(90.0 + 60.0 * tip))) for tip in range(6)]

    for start, end in zip(tips, tips[2:] + tips[:2]):
        rod(b, frame, (*start, 0.012), (*end, 0.012), 0.012, "glow_cyan", depth=0.03)

    for rune in range(12):
        angle = 15.0 + rune * 30.0
        placed = at(frame, (0.99 * math.cos(math.radians(angle)), 0.99 * math.sin(math.radians(angle)), 0.006), angle)
        box(b, placed, (-0.02, -0.07, 0.0), (0.02, 0.07, 0.01), "glow_pink")
        box(b, placed, (-0.07, -0.015 + 0.03 * (rune % 3 - 1), 0.0), (0.0, 0.015 + 0.03 * (rune % 3 - 1), 0.01), "glow_pink")

    for flame in range(6):
        angle = math.radians(60.0 * flame)
        candle(b, frame, (1.0 * math.cos(angle), 1.0 * math.sin(angle), 0.006), 0.12 + 0.05 * (flame % 2))


def celestial_globe(b: Builder, frame: Matrix, **options) -> None:
    """Night-blue star globe in gold horizon and meridian rings on a four-legged wooden stand."""
    generator = rng(options)

    spin(b, frame, [(0.3, 0.0), (0.3, 0.05), (0.14, 0.1), (0.06, 0.16)], "wood", DARK_WOOD)

    for leg in range(4):
        angle = math.radians(45.0 + leg * 90.0)
        rod(b, frame, (0.24 * math.cos(angle), 0.24 * math.sin(angle), 0.04), (0.42 * math.cos(angle), 0.42 * math.sin(angle), 0.92), 0.04, "wood", DARK_WOOD)

    cyl(b, frame, (0.0, 0.0, 0.1), 0.04, 0.48, "wood", DARK_WOOD, sides=6)
    hoop(b, frame, (0.0, 0.0, 0.94), 0.44, 0.025, "metal", GOLD, sides=14)
    hoop(b, frame, (0.0, 0.0, 0.96), 0.39, 0.016, "metal", BRASS, sides=16, axis="Y")

    tilted = at(frame, (0.0, 0.0, 0.96), 23.0, "Y")
    ball(b, tilted, (0.0, 0.0, 0.0), 0.33, "paint", options.get("tint", "2B3C8C"), segments=10)
    rod(b, tilted, (0.0, 0.0, -0.39), (0.0, 0.0, 0.39), 0.018, "metal", GOLD)
    gem(b, tilted, (0.0, 0.0, 0.42), 0.035, "glow_amber")

    for star in range(10):
        azimuth = generator.uniform(0.0, 2.0 * math.pi)
        height = generator.uniform(-0.8, 0.8)
        spread = math.sqrt(1.0 - height * height) * 0.335
        gem(b, tilted, (spread * math.cos(azimuth), spread * math.sin(azimuth), height * 0.335), 0.022, "glow_warm", scale=(1.0, 1.0, 1.0))


def astrolabe(b: Builder, frame: Matrix, **options) -> None:
    """Brass armillary astrolabe on a turned stand: three crossed rings around a glowing sun."""
    spin(b, frame, [(0.22, 0.0), (0.22, 0.05), (0.1, 0.1), (0.05, 0.18)], "wood", PLUM_WOOD)
    cyl(b, frame, (0.0, 0.0, 0.16), 0.03, 0.56, "metal", BRASS, sides=6)
    spin(b, frame, [(0.03, 0.68), (0.07, 0.72), (0.03, 0.75)], "metal", GOLD)
    hoop(b, frame, (0.0, 0.0, 1.03), 0.28, 0.016, "metal", GOLD, sides=14, axis="Y")
    hoop(b, frame, (0.0, 0.0, 1.03), 0.25, 0.014, "metal", BRASS, sides=14, axis="X")
    hoop(b, at(frame, (0.0, 0.0, 1.03), 23.0, "X"), (0.0, 0.0, 0.0), 0.265, 0.02, "metal", COPPER, sides=14)
    ball(b, frame, (0.0, 0.0, 1.03), 0.07, "glow_amber", segments=8)
    rod(b, at(frame, (0.0, 0.0, 1.03), 35.0, "Y"), (0.0, 0.0, -0.3), (0.0, 0.0, 0.3), 0.012, "metal", SILVER)

    for planet, glow in enumerate(("glow_cyan", "glow_pink", "glow_green")):
        angle = math.radians(40.0 + planet * 110.0)
        gem(b, frame, (0.28 * math.cos(angle), 0.0, 1.03 + 0.28 * math.sin(angle)), 0.03, glow, scale=(1.0, 1.0, 1.0))

    cyl(b, frame, (0.0, 0.0, 1.31), 0.012, 0.04, "metal", GOLD, sides=6)


def floating_book(b: Builder, frame: Matrix, color: str, is_open: bool) -> None:
    """Book centred on the frame origin: closed (covers, pages, spine) or open (two tilted halves)."""
    if not is_open:
        box(b, frame, (-0.11, -0.15, -0.03), (0.11, 0.15, -0.02), "paint", color)
        box(b, frame, (-0.11, -0.15, 0.02), (0.11, 0.15, 0.03), "paint", color)
        box(b, frame, (-0.1, -0.14, -0.02), (0.1, 0.14, 0.02), "paint", PARCHMENT)
        box(b, frame, (-0.12, -0.15, -0.03), (-0.1, 0.15, 0.03), "paint", color)
        return

    for side in (-1.0, 1.0):
        half = at(frame, (0.0, 0.0, 0.0), side * -12.0, "Y")
        box(b, half, (min(0.0, side * 0.2), -0.15, -0.01), (max(0.0, side * 0.2), 0.15, 0.0), "paint", color)
        box(b, half, (min(0.0, side * 0.19), -0.14, 0.0), (max(0.0, side * 0.19), 0.14, 0.025), "paint", PARCHMENT)


def floating_books(b: Builder, frame: Matrix, **options) -> None:
    """Ceiling prop: a glowing rune sigil on the ceiling with six spellbooks spiralling down under it."""
    generator = rng(options)

    flat_ring(b, at(frame, (0.0, 0.0, 0.0), 180.0, "X"), 0.36, 0.035, "glow_pink", sides=16)
    flat_ring(b, at(frame, (0.0, 0.0, 0.0), 180.0, "X"), 0.2, 0.025, "glow_cyan", sides=12)

    for index in range(6):
        angle = index * 60.0
        position = (0.24 * math.cos(math.radians(angle)), 0.24 * math.sin(math.radians(angle)), -0.55 - index * 0.2)
        placed = at(at(frame, position, angle + generator.uniform(-20.0, 20.0)), (0.0, 0.0, 0.0), generator.uniform(-15.0, 15.0), "X")
        floating_book(b, placed, BOOK_COLORS[(index * 3) % len(BOOK_COLORS)], index % 2 == 1)

    for spark in range(6):
        angle = math.radians(spark * 60.0 + 30.0)
        gem(b, frame, (0.36 * math.cos(angle), 0.36 * math.sin(angle), -0.45 - spark * 0.22), 0.025, ("glow_pink", "glow_cyan")[spark % 2])


def giant_hourglass(b: Builder, frame: Matrix, **options) -> None:
    """Hourglass as tall as a table: wooden plates, three spindles, glass bulbs and glowing golden sand."""
    wood = options.get("tint", DARK_WOOD)

    for plate_z in (0.0, 0.92):
        cyl(b, frame, (0.0, 0.0, plate_z), 0.28, 0.08, "wood", wood, sides=8)
        hoop(b, frame, (0.0, 0.0, plate_z + 0.04), 0.28, 0.012, "metal", GOLD, sides=8, tube_sides=3)

    for post in range(3):
        angle = math.radians(90.0 + post * 120.0)
        spin(b, frame, [(0.025, 0.08), (0.04, 0.14), (0.025, 0.2), (0.025, 0.8), (0.04, 0.86), (0.025, 0.92)], "wood", wood, sides=6, base=(0.23 * math.cos(angle), 0.23 * math.sin(angle), 0.0))

    spin(b, frame, [(0.11, 0.08), (0.18, 0.14), (0.19, 0.26), (0.13, 0.4), (0.025, 0.5), (0.13, 0.6), (0.19, 0.74), (0.18, 0.86), (0.11, 0.92)], "vitrine", sides=8)
    cyl(b, frame, (0.0, 0.0, 0.08), 0.17, 0.1, "glow_amber", sides=8, top=0.05)
    cyl(b, frame, (0.0, 0.0, 0.56), 0.02, 0.18, "glow_amber", sides=8, top=0.15)
    cyl(b, frame, (0.0, 0.0, 0.18), 0.006, 0.38, "glow_amber", sides=4)
    gem(b, frame, (0.0, 0.0, 1.04), 0.04, "metal", GOLD)


def star_tapestry(b: Builder, frame: Matrix, **options) -> None:
    """Night-sky tapestry on a brass rod (wall prop, rod at 3.1 m): crescent moon, sparkles, constellations, tassels."""
    generator = rng(options)
    cloth = options.get("tint", NAVY)
    outline = [(-0.7, 0.95), (0.0, 0.7), (0.7, 0.95), (0.7, 3.06), (-0.7, 3.06)]

    for side in (-1.0, 1.0):
        box(b, frame, (side * 0.62 - 0.03, 0.0, 3.07), (side * 0.62 + 0.03, 0.06, 3.13), "metal", BRASS)
        ball(b, frame, (side * 0.79, -0.02, 3.1), 0.04, "metal", GOLD, segments=6)

    cyl(b, frame, (-0.76, -0.02, 3.1), 0.022, 1.52, "metal", BRASS, sides=6, axis="X")
    b.prism(outline, 0.02, 0.045, "paint", srgb(cloth), frame=frame)

    for start, end in zip(outline, outline[1:] + outline[:1]):
        rod(b, frame, (start[0], 0.012, start[1]), (end[0], 0.012, end[1]), 0.04, "metal", GOLD, depth=0.012)

    cyl(b, frame, (0.25, 0.0, 2.55), 0.17, 0.015, "glow_warm", sides=12, axis="Y")
    cyl(b, frame, (0.32, -0.008, 2.6), 0.15, 0.015, "paint", cloth, sides=12, axis="Y")

    stars = [(generator.uniform(-0.55, 0.55), generator.uniform(1.15, 2.85)) for _ in range(9)]

    for x, z in stars:
        sparkle(b, frame, (x, 0.0, z), generator.uniform(0.04, 0.08))

    for start, end in zip(stars[:5], stars[1:6]):
        rod(b, frame, (start[0], 0.012, start[1]), (end[0], 0.012, end[1]), 0.008, "paint", "BFD8F2", depth=0.004)

    for x, z in outline[:3]:
        cyl(b, frame, (x, 0.03, z - 0.18), 0.035, 0.18, "metal", GOLD, sides=6, top=0.01)


def wizard_hat(b: Builder, frame: Matrix, color: str, band: str = GOLD) -> None:
    """Pointed hat with a bent tip, its brim centred on the frame origin."""
    cyl(b, frame, (0.0, 0.0, 0.0), 0.2, 0.015, "paint", color, sides=10)
    cyl(b, frame, (0.0, 0.0, 0.015), 0.11, 0.18, "paint", color, sides=8, top=0.065)
    cyl(b, frame, (0.0, 0.0, 0.015), 0.112, 0.035, "paint", band, sides=8, top=0.105)
    cyl(b, at(frame, (0.0, 0.0, 0.19), 28.0, "Y"), (0.0, 0.0, 0.0), 0.065, 0.2, "paint", color, sides=8, top=0.008)
    gem(b, frame, (0.0, -0.105, 0.05), 0.025, "glow_warm")


def mage_hat_stand(b: Builder, frame: Matrix, **options) -> None:
    """Coat stand with wizard hats and a teal cloak with a gold clasp."""
    spin(b, frame, [(0.26, 0.0), (0.26, 0.04), (0.12, 0.08), (0.04, 0.12)], "wood", PLUM_WOOD)
    cyl(b, frame, (0.0, 0.0, 0.1), 0.03, 1.48, "wood", PLUM_WOOD, sides=6)
    ball(b, frame, (0.0, 0.0, 1.6), 0.04, "metal", GOLD, segments=6)

    for hook in range(4):
        angle = math.radians(hook * 90.0)
        rod(b, frame, (0.03 * math.cos(angle), 0.03 * math.sin(angle), 1.4), (0.18 * math.cos(angle), 0.18 * math.sin(angle), 1.5), 0.02, "metal", GOLD)

    wizard_hat(b, at(frame, (0.0, 0.0, 1.62), 15.0), options.get("tint", "5B3FA8"))
    wizard_hat(b, at(at(frame, (0.17, 0.0, 1.38), 0.0), (0.0, 0.0, 0.0), 35.0, "Y"), "2F6BB0", "F2E6CF")
    wizard_hat(b, at(at(frame, (-0.12, -0.12, 1.36), 45.0), (0.0, 0.0, 0.0), -35.0, "Y"), WINE)

    b.hull([(0.02, 0.12, 1.5), (-0.04, 0.12, 1.5), (0.0, 0.18, 1.46), (0.24, 0.02, 0.45), (-0.24, 0.02, 0.45), (0.28, 0.24, 0.45), (-0.28, 0.24, 0.45), (0.0, 0.3, 0.5)], "paint", srgb(TEAL), frame=frame)
    gem(b, frame, (0.0, 0.1, 1.38), 0.035, "metal", GOLD, scale=(1.0, 1.0, 1.0))


def mana_crystal_crate(b: Builder, frame: Matrix, **options) -> None:
    """Open wooden crate on straw packed with glowing mana crystals."""
    generator = rng(options)

    box(b, frame, (-0.38, -0.28, 0.0), (0.38, 0.28, 0.06), "wood", WOOD["media"])

    for sign_x, sign_y in itertools.product((-1.0, 1.0), repeat=2):
        block(b, frame, (sign_x * 0.36, sign_y * 0.26, 0.23), (0.07, 0.07, 0.46), "wood", DARK_WOOD)

    for plank_z in (0.08, 0.28):
        box(b, frame, (-0.34, -0.29, plank_z), (0.34, -0.25, plank_z + 0.16), "wood_light", WOOD["mel"])
        box(b, frame, (-0.34, 0.25, plank_z), (0.34, 0.29, plank_z + 0.16), "wood_light", WOOD["mel"])
        box(b, frame, (-0.39, -0.24, plank_z), (-0.35, 0.24, plank_z + 0.16), "wood_light", WOOD["mel"])
        box(b, frame, (0.35, -0.24, plank_z), (0.39, 0.24, plank_z + 0.16), "wood_light", WOOD["mel"])

    box(b, frame, (-0.34, -0.24, 0.06), (0.34, 0.24, 0.4), "paint", "E8C14F")
    block(b, frame, (0.0, -0.3, 0.27), (0.22, 0.01, 0.14), "paint", PARCHMENT)
    gem(b, frame, (0.0, -0.31, 0.27), 0.04, "glow_cyan", scale=(1.0, 0.5, 1.4))

    for index, (x, y) in enumerate(itertools.product((-0.2, 0.0, 0.2), (-0.1, 0.1))):
        glow = ("glow_cyan", "glow_pink", "glow_cyan", "glow_green")[index % 4]
        crystal(b, frame, (x + generator.uniform(-0.04, 0.04), y, 0.38), generator.uniform(0.04, 0.065), generator.uniform(0.2, 0.33), glow, tilt=(generator.uniform(-22.0, 22.0), generator.uniform(-22.0, 22.0)))


# ---------- alchemist ----------

def big_cauldron(b: Builder, frame: Matrix, **options) -> None:
    """Iron cauldron (Ø1.2) on three legs over a log fire in a ring of stones, brimming with glowing green brew."""
    generator = rng(options)
    pot = options.get("tint", "4A4870")
    stones = (STONE["media"], STONE["dourada"], STONE["clara"])

    for index in range(10):
        angle = 2.0 * math.pi * index / 10.0
        ball(b, frame, (0.68 * math.cos(angle), 0.68 * math.sin(angle), 0.075), 0.13, "paint", stones[index % 3], scale=(1.0, 0.85, 0.58), segments=6)

    for log in range(3):
        cyl(b, at(frame, (0.0, 0.0, 0.06), 60.0 * log), (-0.42, 0.0, 0.0), 0.06, 0.84, "wood", DARK_WOOD, sides=6, axis="X")

    for index, (x, y) in enumerate(((0.12, 0.0), (-0.08, 0.1), (-0.06, -0.1), (0.0, 0.0))):
        cyl(b, frame, (x, y, 0.08), 0.1 if index < 3 else 0.07, 0.26 if index < 3 else 0.32, "glow_ember" if index < 3 else "glow_amber", sides=6, top=0.004)

    for leg in range(3):
        angle = math.radians(90.0 + 120.0 * leg)
        rod(b, frame, (0.42 * math.cos(angle), 0.42 * math.sin(angle), 0.03), (0.5 * math.cos(angle), 0.5 * math.sin(angle), 0.5), 0.06, "metal", pot)

    spin(b, frame, [(0.18, 0.36), (0.42, 0.42), (0.57, 0.58), (0.6, 0.78), (0.55, 0.98), (0.5, 1.06)], "metal", pot, sides=12)
    hoop(b, frame, (0.0, 0.0, 1.06), 0.52, 0.04, "metal", pot, sides=12)
    cyl(b, frame, (0.0, 0.0, 1.04), 0.5, 0.04, "glow_green", sides=12)

    for side in (-1.0, 1.0):
        hoop(b, frame, (side * 0.6, 0.0, 0.9), 0.07, 0.015, "metal", pot, sides=8, tube_sides=3, axis="Y")

    for bubble in range(5):
        angle = generator.uniform(0.0, 2.0 * math.pi)
        spread = generator.uniform(0.05, 0.36)
        ball(b, frame, (spread * math.cos(angle), spread * math.sin(angle), 1.08), generator.uniform(0.04, 0.08), ("glow_green", "paint")[bubble % 2], "4FD96A", segments=6)

    for wisp in range(3):
        gem(b, frame, (0.15 * math.cos(wisp * 2.1), 0.15 * math.sin(wisp * 2.1), 1.2 + 0.08 * wisp), 0.03, "glow_green")

    rod(b, frame, (0.18, 0.14, 0.98), (0.4, 0.3, 1.42), 0.035, "wood_light", WOOD["mel"])


def alembic_table(b: Builder, frame: Matrix, **options) -> None:
    """Distilling bench: copper boiler on a burner, glass head, copper pipe into a glowing receiver, test tubes."""
    generator = rng(options)
    top = table(b, frame, 1.6, 0.8, 0.85, DARK_WOOD, WOOD["mel"], shelf=True)
    boiler = (-0.42, 0.08)
    receiver = (0.22, 0.02)

    cyl(b, frame, (*boiler, top), 0.1, 0.07, "metal", BRASS, sides=8)
    gem(b, frame, (*boiler, top + 0.12), 0.04, "glow_ember", scale=(1.0, 1.0, 1.5))
    hoop(b, frame, (*boiler, top + 0.2), 0.13, 0.012, "metal", DARK_IRON, sides=8, tube_sides=3)

    for leg in range(3):
        angle = math.radians(90.0 + 120.0 * leg)
        foot = (boiler[0] + 0.13 * math.cos(angle), boiler[1] + 0.13 * math.sin(angle))
        rod(b, frame, (*foot, top), (*foot, top + 0.2), 0.02, "metal", DARK_IRON)

    spin(b, frame, [(0.08, 0.18), (0.17, 0.25), (0.18, 0.36), (0.12, 0.46), (0.05, 0.52), (0.05, 0.6)], "metal", COPPER, sides=10, base=(*boiler, top))
    ball(b, frame, (*boiler, top + 0.7), 0.11, "vitrine", segments=8)
    ball(b, frame, (*boiler, top + 0.7), 0.06, "glow_pink", segments=6)
    rod(b, frame, (boiler[0] + 0.08, boiler[1], top + 0.74), (receiver[0], receiver[1], top + 0.34), 0.025, "metal", COPPER)
    flask(b, frame, (*receiver, top), 0.14, 0.36, "glow_cyan", shape="round", cork=True)
    rod(b, frame, (-0.68, 0.28, top), (-0.68, 0.28, top + 0.85), 0.03, "metal", DARK_IRON)
    rod(b, frame, (-0.68, 0.28, top + 0.72), (boiler[0], boiler[1] + 0.09, top + 0.72), 0.02, "metal", BRASS)

    box(b, frame, (0.44, -0.24, top), (0.74, -0.08, top + 0.03), "wood_light", WOOD["mel"])
    box(b, frame, (0.44, -0.18, top + 0.1), (0.74, -0.14, top + 0.12), "wood_light", WOOD["mel"])

    for tube in range(5):
        cyl(b, frame, (0.48 + tube * 0.055, -0.16, top + 0.03), 0.016, 0.18, GLOWS[tube], sides=6)

    for index, shape in enumerate(("cone", "squat", "round")):
        flask(b, frame, (0.48 + index * 0.12, 0.22, top), generator.uniform(0.05, 0.07), generator.uniform(0.16, 0.24), "paint", GLASS_PALETTE[index * 2], shape=shape)

    for index, color in enumerate(("7FD96A", "B57FE0")):
        cyl(b, frame, (-0.3 + index * 0.35, 0.05, 0.18), 0.1, 0.22, "paint", color, sides=8)
        cyl(b, frame, (-0.3 + index * 0.35, 0.05, 0.4), 0.08, 0.04, "wood_light", WOOD["mel"], sides=8)


def potion_wall(b: Builder, frame: Matrix, **options) -> None:
    """Three-bay wall shelf on a teal back panel, every board full of coloured and glowing flasks."""
    generator = rng(options)
    boards = shelf_unit(b, frame, 2.4, 0.35, 2.3, [0.62, 1.18, 1.74], DARK_WOOD, back=options.get("tint", "2E6B66"), crown=WOOD["mel"], bays=3)
    surfaces = (0.08, *boards)
    shapes = tuple(FLASK_PROFILES)

    for bay, surface, slot in itertools.product(range(3), surfaces, range(3)):
        x = -1.2 + 0.8 * bay + 0.2 * (slot + 1) + generator.uniform(-0.03, 0.03)
        is_glowing = generator.random() < 0.35
        material = generator.choice(GLOWS) if is_glowing else "paint"
        flask(b, frame, (x, 0.0, surface), generator.uniform(0.05, 0.075), generator.uniform(0.22, 0.42), material, None if is_glowing else generator.choice(GLASS_PALETTE), shape=generator.choice(shapes))


def herb_bundle(b: Builder, frame: Matrix, x: float, y: float, kind: str, color: str) -> None:
    """One bundle hanging on a string from the drying beam (tie at z = -0.86)."""
    tie = -0.86

    rod(b, frame, (x, y, -0.74), (x, y, tie), 0.01, "paint", "C9A46A")
    cyl(b, frame, (x, y, tie - 0.05), 0.028, 0.05, "paint", "C9483B", sides=6)
    shapes = {
        "leafy": lambda: cyl(b, frame, (x, y, tie - 0.5), 0.11, 0.45, "paint", color, sides=6, top=0.03),
        "flower": lambda: (cyl(b, frame, (x, y, tie - 0.38), 0.08, 0.33, "paint", DEEP_LEAF, sides=6, top=0.025), [ball(b, frame, (x + dx, y + dy, tie - 0.4), 0.045, "paint", color, segments=4) for dx, dy in ((0.05, 0.0), (-0.04, 0.03), (0.0, -0.05))]),
        "garlic": lambda: [ball(b, frame, (x + dx, y, tie - 0.12 - dz), 0.055, "paint", BONE, scale=(1.0, 1.0, 1.2), segments=6) for dx, dz in ((0.0, 0.0), (0.05, 0.12), (-0.05, 0.12), (0.0, 0.24))],
        "chili": lambda: [cyl(b, frame, (x + dx, y, tie - 0.05 - length), 0.006, length, "paint", color, sides=5, top=0.022) for dx, length in ((-0.04, 0.2), (-0.015, 0.26), (0.015, 0.22), (0.04, 0.18))],
    }

    shapes[kind]()


HERB_KINDS = (("leafy", DEEP_LEAF), ("flower", "B57FE0"), ("garlic", BONE), ("leafy", LEAF), ("chili", "D63A2E"), ("flower", "E8C14F"), ("leafy", "5FA05A"), ("flower", "F25C7A"), ("chili", "E0884A"))


def herb_bundles(b: Builder, frame: Matrix, **options) -> None:
    """Ceiling prop: a 2 m drying beam on two ropes with nine bundles of herbs, flowers, garlic and chillies."""
    for side in (-1.0, 1.0):
        box(b, frame, (side * 0.85 - 0.06, -0.06, -0.02), (side * 0.85 + 0.06, 0.06, 0.0), "metal", DARK_IRON)
        rod(b, frame, (side * 0.85, 0.0, -0.02), (side * 0.85, 0.0, -0.7), 0.025, "paint", "C9A46A")

    box(b, frame, (-1.0, -0.05, -0.78), (1.0, 0.05, -0.7), "wood", DARK_WOOD)

    for index, (kind, color) in enumerate(HERB_KINDS):
        herb_bundle(b, frame, -0.8 + 0.2 * index, 0.04 * (1 - 2 * (index % 2)), kind, color)


JAR_GLOWS = {"green": "glow_green", "cyan": "glow_cyan", "pink": "glow_pink", "amber": "glow_amber"}


def glowing_jar(b: Builder, frame: Matrix, **options) -> None:
    """Big glass jar (Ø0.5) of glowing liquid with a wooden lid, rope tie and label; variant = glow colour."""
    glow = JAR_GLOWS.get(options.get("variant"), "glow_green")

    cyl(b, frame, (0.0, 0.0, 0.02), 0.21, 0.56, glow, sides=10)
    spin(b, frame, [(0.18, 0.0), (0.24, 0.07), (0.24, 0.62), (0.16, 0.72), (0.14, 0.78)], "vitrine", sides=10)
    hoop(b, frame, (0.0, 0.0, 0.75), 0.15, 0.012, "paint", "C9A46A", sides=10, tube_sides=3)
    cyl(b, frame, (0.0, 0.0, 0.78), 0.165, 0.06, "wood_light", WOOD["mel"], sides=10)
    gem(b, frame, (0.0, 0.0, 0.86), 0.035, "metal", BRASS, scale=(1.0, 1.0, 0.8))
    box(b, frame, (-0.08, -0.255, 0.25), (0.08, -0.245, 0.4), "paint", PARCHMENT)


def mortar_table(b: Builder, frame: Matrix, **options) -> None:
    """Small work table: stone mortar and pestle, cutting board with leaves, a bowl of glowing powder and jars."""
    generator = rng(options)
    top = table(b, frame, 1.0, 0.6, 0.8, DARK_WOOD, WOOD["mel"])

    spin(b, frame, [(0.09, top), (0.15, top + 0.05), (0.16, top + 0.14), (0.13, top + 0.16)], "paint", STONE["media"], base=(-0.25, 0.0, 0.0))
    cyl(b, frame, (-0.25, 0.0, top + 0.16), 0.11, 0.006, "paint", LEAF, sides=8)
    rod(b, frame, (-0.25, 0.0, top + 0.1), (-0.15, 0.08, top + 0.36), 0.045, "paint", STONE["clara"])
    box(b, frame, (0.02, -0.24, top), (0.4, 0.04, top + 0.025), "wood_light", WOOD["mel"])

    for leaf in range(5):
        center = (generator.uniform(0.08, 0.34), generator.uniform(-0.18, -0.02), top + 0.03)
        b.hull([(center[0] - 0.05, center[1], center[2]), (center[0] + 0.05, center[1], center[2]), (center[0], center[1] - 0.025, center[2]), (center[0], center[1] + 0.025, center[2]), (center[0], center[1], center[2] + 0.008)], "paint", srgb((LEAF, DEEP_LEAF)[leaf % 2]), frame=frame)

    spin(b, frame, [(0.05, top), (0.11, top + 0.04), (0.12, top + 0.07)], "paint", "F2E6CF", base=(-0.3, -0.18, 0.0))
    cyl(b, frame, (-0.3, -0.18, top + 0.065), 0.1, 0.02, "glow_pink", sides=8, top=0.03)
    flask(b, frame, (0.3, 0.18, top), 0.07, 0.2, "paint", "4FB0D9", shape="squat", cork=True)
    flask(b, frame, (0.14, 0.2, top), 0.06, 0.28, "paint", "D94F5C", shape="tall", cork=True)
    rod(b, frame, (0.06, -0.22, top + 0.03), (0.26, -0.26, top + 0.03), 0.01, "metal", SILVER, depth=0.03)


def recipe_board(b: Builder, frame: Matrix, **options) -> None:
    """Wall chalkboard (1.0 to 1.95 m) with a chalk flask diagram, recipe lines and two pinned notes."""
    generator = rng(options)
    chalk = "F2F0E6"

    box(b, frame, (-0.55, 0.02, 1.0), (0.55, 0.05, 1.95), "paint", options.get("tint", "2F4A3E"))
    box(b, frame, (-0.6, 0.0, 0.96), (0.6, 0.05, 1.0), "wood_light", WOOD["mel"])
    box(b, frame, (-0.6, 0.0, 1.95), (0.6, 0.05, 1.99), "wood_light", WOOD["mel"])
    box(b, frame, (-0.6, 0.0, 1.0), (-0.55, 0.05, 1.95), "wood_light", WOOD["mel"])
    box(b, frame, (0.55, 0.0, 1.0), (0.6, 0.05, 1.95), "wood_light", WOOD["mel"])
    box(b, frame, (-0.5, -0.05, 0.94), (0.5, 0.05, 0.97), "wood", DARK_WOOD)
    box(b, frame, (-0.3, -0.03, 0.97), (-0.22, -0.01, 0.985), "paint", chalk)
    box(b, frame, (0.1, -0.03, 0.97), (0.15, -0.01, 0.985), "paint", "F59AD8")

    hoop(b, frame, (-0.3, 0.015, 1.35), 0.11, 0.008, "paint", chalk, sides=10, tube_sides=3, axis="Y")
    rod(b, frame, (-0.34, 0.015, 1.455), (-0.34, 0.015, 1.6), 0.012, "paint", chalk, depth=0.004)
    rod(b, frame, (-0.26, 0.015, 1.455), (-0.26, 0.015, 1.6), 0.012, "paint", chalk, depth=0.004)
    rod(b, frame, (-0.4, 0.015, 1.33), (-0.2, 0.015, 1.33), 0.012, "glow_green", depth=0.004)
    rod(b, frame, (-0.12, 0.015, 1.35), (0.02, 0.015, 1.35), 0.012, "paint", chalk, depth=0.004)

    for line in range(5):
        length = generator.uniform(0.18, 0.42)
        rod(b, frame, (0.02, 0.015, 1.84 - 0.08 * line), (0.02 + length, 0.015, 1.84 - 0.08 * line), 0.012, "paint", chalk, depth=0.004)

    for note, (x, z, tilt) in enumerate(((0.3, 1.22, 8.0), (-0.32, 1.78, -6.0))):
        placed = at(frame, (x, 0.01, z), tilt, "Y")
        box(b, placed, (-0.11, 0.0, -0.13), (0.11, 0.008, 0.13), "paint", PARCHMENT)
        gem(b, placed, (0.0, -0.01, 0.1), 0.018, "paint", ("C9483B", "4F8FC9")[note], scale=(1.0, 1.0, 1.0))
        rod(b, placed, (-0.07, -0.002, 0.02), (0.07, -0.002, 0.02), 0.01, "paint", "6C5BB8", depth=0.003)
        rod(b, placed, (-0.07, -0.002, -0.04), (0.04, -0.002, -0.04), 0.01, "paint", "6C5BB8", depth=0.003)


def slime_jar(b: Builder, frame: Matrix, **options) -> None:
    """Small glass jar holding a cute glowing slime with two dark eyes."""
    spin(b, frame, [(0.15, 0.0), (0.18, 0.05), (0.18, 0.42), (0.13, 0.5)], "vitrine", sides=8)
    ball(b, frame, (0.0, 0.0, 0.12), 0.14, JAR_GLOWS.get(options.get("variant"), "glow_green"), scale=(1.0, 1.0, 0.85), segments=6)

    for side in (-1.0, 1.0):
        gem(b, frame, (side * 0.045, -0.115, 0.15), 0.02, "paint", "2B2236", scale=(1.0, 0.6, 1.5))

    cyl(b, frame, (0.0, 0.0, 0.5), 0.14, 0.04, "metal", BRASS, sides=8)


def skeleton_stand(b: Builder, frame: Matrix, **options) -> None:
    """Anatomy skeleton hanging from an iron stand, with faintly glowing eye sockets."""
    bone = options.get("tint", BONE)

    cyl(b, frame, (0.0, 0.04, 0.0), 0.24, 0.05, "wood", DARK_WOOD, sides=8)
    rod(b, frame, (0.0, 0.16, 0.05), (0.0, 0.16, 1.86), 0.035, "metal", DARK_IRON)
    rod(b, frame, (0.0, 0.16, 1.84), (0.0, 0.0, 1.84), 0.03, "metal", DARK_IRON)
    rod(b, frame, (0.0, 0.0, 1.84), (0.0, 0.0, 1.76), 0.02, "metal", DARK_IRON)

    ball(b, frame, (0.0, 0.0, 1.67), 0.1, "paint", bone, scale=(0.85, 1.0, 1.0), segments=8)
    block(b, frame, (0.0, -0.035, 1.56), (0.11, 0.1, 0.05), "paint", bone)

    for side in (-1.0, 1.0):
        gem(b, frame, (side * 0.035, -0.085, 1.68), 0.022, "glow_cyan", scale=(1.0, 0.5, 1.0))

    cyl(b, frame, (0.0, 0.02, 0.95), 0.022, 0.6, "paint", bone, sides=6)
    rod(b, frame, (-0.17, 0.0, 1.49), (0.17, 0.0, 1.49), 0.03, "paint", bone)

    for rib in range(4):
        ribcage = frame @ Matrix.Translation((0.0, -0.02, 1.43 - rib * 0.07)) @ Matrix.Diagonal((1.0, 0.7, 1.0, 1.0))
        hoop(b, ribcage, (0.0, 0.0, 0.0), 0.13 - rib * 0.012, 0.012, "paint", bone, sides=8, tube_sides=3)

    b.hull([(-0.14, -0.04, 1.0), (0.14, -0.04, 1.0), (-0.14, 0.06, 1.0), (0.14, 0.06, 1.0), (-0.08, -0.02, 0.9), (0.08, -0.02, 0.9), (-0.08, 0.05, 0.9), (0.08, 0.05, 0.9)], "paint", srgb(bone), frame=frame)

    for side in (-1.0, 1.0):
        rod(b, frame, (side * 0.17, 0.0, 1.48), (side * 0.21, -0.02, 1.2), 0.035, "paint", bone)
        rod(b, frame, (side * 0.21, -0.02, 1.2), (side * 0.2, -0.1, 0.98), 0.03, "paint", bone)
        block(b, frame, (side * 0.2, -0.11, 0.93), (0.05, 0.03, 0.09), "paint", bone)
        rod(b, frame, (side * 0.08, 0.0, 0.93), (side * 0.09, 0.0, 0.5), 0.045, "paint", bone)
        rod(b, frame, (side * 0.09, 0.0, 0.5), (side * 0.09, 0.02, 0.09), 0.038, "paint", bone)
        box(b, frame, (side * 0.09 - 0.04, -0.12, 0.05), (side * 0.09 + 0.04, 0.04, 0.09), "paint", bone)


# ---------- bank ----------

def arch_spandrel(b: Builder, frame: Matrix, x_left: float, x_right: float, spring: float, top: float, rise: float, depth: tuple, material: str, color: str) -> None:
    """Wall piece above an elliptic arch: from the arch curve up to top, extruded over depth (y from, y to)."""
    center, half = (x_left + x_right) / 2.0, (x_right - x_left) / 2.0
    arc = [(center + half * math.cos(math.pi * step / 10.0), spring + rise * math.sin(math.pi * step / 10.0)) for step in range(11)]
    key, tint, uv = resolve(material, color)

    b.prism([(x_left, top), (x_right, top)] + arc, depth[0], depth[1], key, tint, frame=frame, uv=uv)


def teller_counter(b: Builder, frame: Matrix, **options) -> None:
    """6 m marble-and-wood bank counter with three arched service windows behind gilded iron grilles."""
    panel = options.get("tint", WINE)
    windows = (-2.0, 0.0, 2.0)

    box(b, frame, (-3.0, -0.42, 0.0), (3.0, 0.4, 0.14), "paint", MARBLE)
    box(b, frame, (-2.97, -0.38, 0.14), (2.97, 0.38, 1.0), "wood", DARK_WOOD)
    box(b, frame, (-3.0, -0.48, 1.0), (3.0, 0.45, 1.08), "paint", MARBLE)

    for column in range(6):
        x = -2.5 + column
        box(b, frame, (x - 0.43, -0.392, 0.22), (x + 0.43, -0.38, 0.92), "metal", GOLD)
        box(b, frame, (x - 0.4, -0.4, 0.25), (x + 0.4, -0.392, 0.89), "paint", panel)

    for x in (-2.93, -1.0, 1.0, 2.93):
        box(b, frame, (x - 0.07, -0.06, 1.08), (x + 0.07, 0.08, 2.4), "paint", MARBLE)
        box(b, frame, (x - 0.09, -0.08, 2.3), (x + 0.09, 0.1, 2.4), "metal", GOLD)

    box(b, frame, (-3.0, -0.07, 2.4), (3.0, 0.09, 2.6), "wood", DARK_WOOD)
    box(b, frame, (-3.0, -0.08, 2.42), (3.0, -0.07, 2.45), "metal", GOLD)
    box(b, frame, (-3.0, -0.08, 2.55), (3.0, -0.07, 2.58), "metal", GOLD)
    cyl(b, frame, (0.0, -0.1, 2.5), 0.08, 0.03, "metal", GOLD, sides=10, axis="Y")

    for center in windows:
        left, right = center - 0.93, center + 0.93
        arch_spandrel(b, frame, left, right, 2.05, 2.4, 0.3, (-0.04, 0.04), "wood", DARK_WOOD)
        box(b, frame, (left, -0.04, 1.27), (right, 0.04, 1.31), "metal", GOLD)
        box(b, frame, (left, -0.03, 1.72), (right, 0.03, 1.75), "metal", GOLD)

        for bar in range(9):
            x = left + (right - left) * (bar + 1) / 10.0
            box(b, frame, (x - 0.011, -0.011, 1.31), (x + 0.011, 0.011, 2.36), "metal", DARK_IRON)
            gem(b, frame, (x, 0.0, 1.78), 0.022, "metal", GOLD, scale=(1.0, 1.0, 1.6))

        box(b, frame, (center - 0.22, -0.09, 2.46), (center + 0.22, -0.08, 2.54), "metal", BRASS)
        spin(b, frame, [(0.05, 1.08), (0.045, 1.1), (0.02, 1.15), (0.006, 1.17)], "metal", GOLD, sides=6, base=(center - 0.5, -0.3, 0.0))
        box(b, frame, (center + 0.2, -0.38, 1.08), (center + 0.45, -0.18, 1.11), "paint", BOOK_COLORS[windows.index(center)])
        cyl(b, frame, (center + 0.55, -0.3, 1.08), 0.03, 0.05, "paint", NAVY, sides=6)


def vault_door(b: Builder, frame: Matrix, **options) -> None:
    """Round vault door (Ø2.0) set in a golden stone wall block: brass ring, bolts, spoked wheel, glowing seal."""
    steel = options.get("tint", "6E7FA8")
    center = 1.2

    box(b, frame, (-1.2, 0.15, 0.0), (1.2, 0.35, 2.4), "stone", STONE["dourada"])
    box(b, frame, (-1.05, -0.3, 0.0), (1.05, 0.15, 0.1), "paint", MARBLE)
    hoop(b, frame, (0.0, 0.1, center), 1.05, 0.08, "metal", BRASS, sides=24, axis="Y")
    cyl(b, frame, (0.0, -0.05, center), 1.0, 0.2, "metal", steel, sides=24, axis="Y")
    cyl(b, frame, (0.0, -0.1, center), 0.72, 0.06, "metal", "8A9BC4", sides=24, axis="Y")

    for bolt in range(16):
        angle = 2.0 * math.pi * bolt / 16.0
        gem(b, frame, (0.87 * math.cos(angle), -0.06, center + 0.87 * math.sin(angle)), 0.04, "metal", GOLD, scale=(1.0, 0.8, 1.0))

    hoop(b, frame, (0.0, -0.22, center), 0.34, 0.035, "metal", GOLD, sides=12, axis="Y")

    for spoke in range(3):
        angle = math.radians(90.0 + 60.0 * spoke)
        rod(b, frame, (0.38 * math.cos(angle), -0.22, center + 0.38 * math.sin(angle)), (-0.38 * math.cos(angle), -0.22, center - 0.38 * math.sin(angle)), 0.04, "metal", GOLD)

    cyl(b, frame, (0.0, -0.26, center), 0.1, 0.16, "metal", BRASS, sides=10, axis="Y")
    gem(b, frame, (0.0, -0.28, center), 0.06, "glow_amber", scale=(1.0, 0.6, 1.0))

    for hinge_z in (center - 0.55, center + 0.55):
        box(b, frame, (0.9, -0.12, hinge_z - 0.1), (1.18, 0.15, hinge_z + 0.1), "metal", DARK_IRON)
        cyl(b, frame, (1.1, -0.14, hinge_z - 0.14), 0.04, 0.28, "metal", GOLD, sides=8)


def deposit_boxes(b: Builder, frame: Matrix, **options) -> None:
    """Wall of 20 numbered deposit boxes (4 x 5 steel doors with brass plates); one stands open showing gold."""
    door = options.get("tint", "7F90C0")

    box(b, frame, (-0.8, -0.08, 0.0), (0.8, 0.3, 2.1), "wood", DARK_WOOD)
    box(b, frame, (-0.84, -0.12, 2.1), (0.84, 0.3, 2.18), "metal", GOLD)
    box(b, frame, (-0.84, -0.12, 0.0), (0.84, 0.3, 0.1), "wood", DARK_WOOD)

    for column, row in itertools.product(range(4), range(5)):
        x, z = -0.6 + column * 0.4, 0.3 + row * 0.37
        is_open = (column, row) == (2, 1)
        leaf = at(frame, (x - 0.18, -0.08, z), -30.0 if is_open else 0.0)
        box(b, leaf, (0.0, -0.025, -0.16), (0.36, 0.0, 0.16), "metal", door)
        box(b, leaf, (0.13, -0.035, 0.06), (0.23, -0.025, 0.11), "metal", BRASS)
        box(b, leaf, (0.165, -0.035, -0.04), (0.195, -0.025, 0.02), "paint", "2B2236")
        box(b, leaf, (0.17 - 0.015 * (column % 2), -0.04, 0.075), (0.19 + 0.015 * (row % 2), -0.035, 0.095), "paint", "2B2236")

    gem(b, frame, (0.2, 0.05, 0.6), 0.06, "glow_amber", scale=(1.6, 1.0, 0.7))


def coin_table(b: Builder, frame: Matrix, **options) -> None:
    """Counting table: green baize, coin stacks and heap, brass balance and an open ledger."""
    generator = rng(options)
    top = table(b, frame, 1.4, 0.8, 0.8, DARK_WOOD, WOOD["mel"])

    box(b, frame, (-0.6, -0.3, top), (0.6, 0.3, top + 0.006), "paint", "2F6B4F")
    spin(b, frame, [(0.16, top), (0.1, top + 0.05), (0.03, top + 0.08)], "metal", GOLD, base=(-0.35, -0.08, 0.0))

    for stack in range(7):
        cyl(b, frame, (-0.1 + 0.07 * stack, -0.18 + 0.05 * (stack % 2), top + 0.006), 0.03, generator.uniform(0.02, 0.12), "metal", (GOLD, SILVER, COPPER)[stack % 3], sides=8)

    cyl(b, frame, (0.4, 0.15, top), 0.07, 0.02, "metal", BRASS, sides=8)
    cyl(b, frame, (0.4, 0.15, top + 0.02), 0.012, 0.3, "metal", BRASS, sides=6)
    rod(b, frame, (0.24, 0.15, top + 0.3), (0.56, 0.15, top + 0.3), 0.015, "metal", BRASS)

    for pan_x in (0.25, 0.55):
        rod(b, frame, (pan_x, 0.15, top + 0.3), (pan_x, 0.15, top + 0.12), 0.006, "metal", BRASS)
        cyl(b, frame, (pan_x, 0.15, top + 0.1), 0.06, 0.02, "metal", GOLD, sides=8, top=0.04)

    floating_book(b, at(frame, (-0.3, 0.17, top + 0.03), 8.0), "8E2F45", True)
    cyl(b, frame, (0.05, 0.22, top), 0.03, 0.05, "paint", NAVY, sides=6)
    rod(b, frame, (0.05, 0.22, top + 0.04), (0.12, 0.3, top + 0.22), 0.01, "paint", "F2F0E6", depth=0.035)


def money_sacks(b: Builder, frame: Matrix, **options) -> None:
    """Three tied coin sacks with gold coin emblems and coins spilling on the floor."""
    generator = rng(options)
    sack_profile = [(0.16, 0.0), (0.24, 0.08), (0.26, 0.22), (0.2, 0.36), (0.07, 0.44), (0.06, 0.46), (0.12, 0.54)]

    for index, (x, y, scale, color) in enumerate(((-0.25, 0.1, 1.0, "D2B07A"), (0.22, 0.12, 0.85, "C9A46A"), (0.05, -0.18, 0.7, WINE))):
        placed = at(frame, (x, y, 0.0), 25.0 * index) @ Matrix.Diagonal((scale, scale, scale, 1.0))
        spin(b, placed, sack_profile, "paint", color)
        cyl(b, placed, (0.0, 0.0, 0.43), 0.075, 0.04, "paint", "C9483B", sides=6)
        cyl(b, placed, (0.0, -0.27, 0.2), 0.08, 0.02, "metal", GOLD, sides=8, axis="Y")

    for coin in range(5):
        cyl(b, frame, (generator.uniform(-0.4, 0.4), generator.uniform(-0.38, -0.28), 0.0), 0.03, 0.008, "metal", GOLD, sides=6)


def iron_safe(b: Builder, frame: Matrix, **options) -> None:
    """Deep blue steel safe on gold feet: framed door, dial, handle wheel, hinges and a painted crest."""
    steel = options.get("tint", "3E4A7A")

    for sign_x, sign_y in itertools.product((-1.0, 1.0), repeat=2):
        block(b, frame, (sign_x * 0.33, sign_y * 0.3 + 0.04, 0.03), (0.08, 0.08, 0.06), "metal", GOLD)

    box(b, frame, (-0.4, -0.32, 0.06), (0.4, 0.4, 1.0), "metal", steel)
    box(b, frame, (-0.33, -0.36, 0.14), (0.33, -0.32, 0.92), "metal", "4D5C94")

    for start, end in (((-0.33, 0.14), (0.33, 0.14)), ((-0.33, 0.92), (0.33, 0.92)), ((-0.33, 0.14), (-0.33, 0.92)), ((0.33, 0.14), (0.33, 0.92))):
        rod(b, frame, (start[0], -0.36, start[1]), (end[0], -0.36, end[1]), 0.03, "metal", GOLD, depth=0.02)

    cyl(b, frame, (0.12, -0.4, 0.66), 0.08, 0.04, "metal", GOLD, sides=10, axis="Y")
    gem(b, frame, (0.12, -0.405, 0.66), 0.025, "paint", WINE, scale=(1.0, 0.5, 1.0))
    hoop(b, frame, (0.12, -0.4, 0.4), 0.09, 0.012, "metal", GOLD, sides=8, tube_sides=3, axis="Y")
    rod(b, frame, (0.03, -0.4, 0.4), (0.21, -0.4, 0.4), 0.02, "metal", GOLD)
    rod(b, frame, (0.12, -0.4, 0.31), (0.12, -0.4, 0.49), 0.02, "metal", GOLD)

    for hinge_z in (0.3, 0.76):
        cyl(b, frame, (-0.35, -0.37, hinge_z - 0.07), 0.025, 0.14, "metal", DARK_IRON, sides=6)

    gem(b, frame, (-0.12, -0.37, 0.7), 0.07, "metal", BRASS, scale=(1.0, 0.3, 1.2))
    box(b, frame, (-0.42, -0.34, 0.97), (0.42, 0.42, 1.0), "metal", GOLD)


def pillar_marble(b: Builder, frame: Matrix, **options) -> None:
    """Free-standing marble column with gilded bands; options height (default 4.0 m, floor to its abacus)."""
    height = options.get("height", 4.0)
    marble = options.get("tint", MARBLE)

    box(b, frame, (-0.4, -0.4, 0.0), (0.4, 0.4, 0.2), "paint", marble)
    spin(b, frame, [(0.34, 0.2), (0.34, 0.26), (0.3, 0.3), (0.27, 0.36)], "paint", marble, sides=12)
    cyl(b, frame, (0.0, 0.0, 0.36), 0.25, height - 0.86, "paint", marble, sides=12)
    hoop(b, frame, (0.0, 0.0, 0.42), 0.255, 0.025, "metal", GOLD, sides=12)
    hoop(b, frame, (0.0, 0.0, height - 0.56), 0.255, 0.025, "metal", GOLD, sides=12)
    spin(b, frame, [(0.26, height - 0.5), (0.3, height - 0.42), (0.36, height - 0.3), (0.4, height - 0.22)], "paint", marble, sides=12)
    box(b, frame, (-0.4, -0.4, height - 0.22), (0.4, 0.4, height), "paint", marble)
    box(b, frame, (-0.41, -0.41, height - 0.2), (0.41, 0.41, height - 0.16), "metal", GOLD)


# ---------- bookshop ----------

def tall_bookcase(b: Builder, frame: Matrix, **options) -> None:
    """Floor-to-ceiling bookcase (4 m) on an indigo back: six boards of books, a glowing jar and a fern."""
    generator = rng(options)
    boards = shelf_unit(b, frame, 2.0, 0.4, 3.84, [0.62, 1.2, 1.78, 2.36, 2.94, 3.52], DARK_WOOD, back=options.get("tint", "3E3263"), crown=WOOD["mel"])
    surfaces = (0.08, *boards[:-1])

    for index, surface in enumerate(surfaces):
        x_to = 0.35 if index == 2 else 0.93
        book_row(b, frame, -0.93, x_to, 0.0, surface, 0.3, 0.46, generator)

    for side in (-1.0, 1.0):
        box(b, frame, (side * 0.96 - 0.035, -0.21, 0.1), (side * 0.96 + 0.035, -0.19, 3.78), "wood", WOOD["mel"])
        box(b, frame, (side * 0.96 - 0.05, -0.215, 0.1), (side * 0.96 + 0.05, -0.2, 0.18), "wood", DARK_WOOD)
        box(b, frame, (side * 0.96 - 0.05, -0.215, 3.7), (side * 0.96 + 0.05, -0.2, 3.78), "wood", DARK_WOOD)

    for plate_z in (0.62, 1.2, 1.78, 2.36, 2.94, 3.52):
        box(b, frame, (-0.1, -0.215, plate_z - 0.045), (0.1, -0.2, plate_z - 0.015), "metal", BRASS)

    box(b, frame, (-1.0, -0.21, 3.84), (1.0, 0.2, 3.9), "wood", DARK_WOOD)
    b.hull([(-0.55, -0.21, 3.9), (0.55, -0.21, 3.9), (-0.55, 0.0, 3.9), (0.55, 0.0, 3.9), (0.0, -0.2, 4.0), (0.0, 0.0, 4.0)], "wood", srgb(DARK_WOOD), frame=frame)
    gem(b, frame, (0.0, -0.215, 3.935), 0.04, "metal", GOLD, scale=(1.0, 0.3, 1.0))
    cyl(b, frame, (0.6, 0.0, surfaces[2]), 0.11, 0.26, "glow_amber", sides=8)
    cyl(b, frame, (0.6, 0.0, surfaces[2] + 0.26), 0.09, 0.05, "wood_light", WOOD["mel"], sides=8)
    cyl(b, frame, (0.84, 0.0, surfaces[2]), 0.07, 0.12, "paint", "D0745A", sides=6, top=0.08)

    for layer, color in enumerate(("8E2F45", "28356E", "D9A441")):
        block(b, at(frame, (-0.6, 0.0, boards[-1]), 10.0 * layer), (0.0, 0.0, 0.035 + 0.07 * layer), (0.34 - 0.03 * layer, 0.26, 0.07), "paint", color)

    ball(b, frame, (0.55, 0.0, boards[-1] + 0.12), 0.12, "paint", BONE, scale=(0.85, 1.0, 1.0), segments=6)
    gem(b, frame, (0.85, 0.0, boards[-1] + 0.1), 0.07, "glow_cyan")
    ball(b, frame, (0.84, 0.0, surfaces[2] + 0.2), 0.11, "paint", LEAF, scale=(1.0, 1.0, 0.8), segments=6)


def tall_bookcase_slim(b: Builder, frame: Matrix, **options) -> None:
    """The tall bookcase narrowed to 1.92 m so it fits a corner pier between two windows."""
    tall_bookcase(b, frame @ Matrix.Scale(0.96, 4, (1.0, 0.0, 0.0)), **options)


def rolling_ladder(b: Builder, frame: Matrix, **options) -> None:
    """Library ladder leaning on its bookcase rail: honey rails, eleven rungs, wheels below and brass hooks above."""
    wood = options.get("tint", WOOD["mel"])
    bottom, top = (-0.3, 0.08), (0.22, 3.36)

    for side in (-0.22, 0.22):
        rod(b, frame, (side, bottom[0], bottom[1]), (side, top[0], top[1]), 0.06, "wood_light", wood, depth=0.05)
        cyl(b, frame, (side - 0.03, bottom[0], 0.07), 0.07, 0.06, "metal", BRASS, sides=8, axis="X")
        rod(b, frame, (side, top[0], top[1]), (side, 0.34, top[1] + 0.02), 0.03, "metal", BRASS)

    for rung in range(11):
        amount = (rung + 0.6) / 11.5
        y, z = bottom[0] + (top[0] - bottom[0]) * amount, bottom[1] + (top[1] - bottom[1]) * amount
        box(b, frame, (-0.22, y - 0.03, z - 0.02), (0.22, y + 0.03, z + 0.02), "wood_light", wood)


def reading_table(b: Builder, frame: Matrix, **options) -> None:
    """Reading table with a green leather inlay, open book, book stack, oil lamp, inkwell and quill."""
    top = table(b, frame, 2.0, 1.0, 0.78, DARK_WOOD, WOOD["mel"], leg=0.09)

    box(b, frame, (-0.85, -0.38, top), (0.85, 0.38, top + 0.005), "paint", options.get("tint", "2F6B4F"))
    floating_book(b, at(frame, (-0.15, -0.1, top + 0.03), -6.0), "28356E", True)

    for layer, color in enumerate(("8E2F45", "D9A441", "2F6B4F", "6A2E6E")):
        block(b, at(frame, (-0.65, 0.18, top), 12.0 * layer), (0.0, 0.0, 0.03 + 0.06 * layer), (0.3 - 0.02 * layer, 0.22, 0.055), "paint", color)

    spin(b, frame, [(0.09, top), (0.07, top + 0.03), (0.04, top + 0.08), (0.07, top + 0.12)], "metal", BRASS, base=(0.6, 0.18, 0.0))
    ball(b, frame, (0.6, 0.18, top + 0.2), 0.08, "vitrine", segments=8)
    gem(b, frame, (0.6, 0.18, top + 0.19), 0.035, "glow_warm", scale=(1.0, 1.0, 1.6))
    cyl(b, frame, (0.6, 0.18, top + 0.27), 0.04, 0.06, "metal", BRASS, sides=6)
    cyl(b, frame, (0.3, 0.25, top), 0.035, 0.06, "paint", NAVY, sides=6)
    rod(b, frame, (0.3, 0.25, top + 0.05), (0.38, 0.33, top + 0.26), 0.012, "paint", "F2F0E6", depth=0.04)


def lectern(b: Builder, frame: Matrix, **options) -> None:
    """Turned wooden lectern with a slanted rest holding a big open book with a red ribbon, and a candle arm."""
    wood = options.get("tint", DARK_WOOD)

    for degrees in (0.0, 90.0):
        rod(b, at(frame, (0.0, 0.0, 0.0), degrees), (-0.26, 0.0, 0.04), (0.26, 0.0, 0.04), 0.08, "wood", wood)

    spin(b, frame, [(0.08, 0.08), (0.05, 0.14), (0.05, 0.85), (0.08, 0.92), (0.05, 1.0)], "wood", wood)
    rest = at(frame, (0.0, 0.0, 1.06), 25.0, "X")
    box(b, rest, (-0.28, -0.2, -0.04), (0.28, 0.2, 0.0), "wood", wood)
    box(b, rest, (-0.28, -0.22, -0.04), (0.28, -0.2, 0.03), "metal", GOLD)
    floating_book(b, rest, "6A2E6E", True)
    box(b, rest, (-0.01, -0.21, -0.12), (0.01, -0.19, 0.03), "paint", "C9483B")
    rod(b, frame, (0.05, 0.0, 0.8), (0.27, 0.0, 0.86), 0.02, "metal", BRASS)
    cyl(b, frame, (0.27, 0.0, 0.85), 0.045, 0.02, "metal", BRASS, sides=6)
    candle(b, frame, (0.27, 0.0, 0.87), 0.14)


def globe_stand(b: Builder, frame: Matrix, **options) -> None:
    """World globe (Ø0.7) of blue seas and green and sand continents in a brass meridian on a three-legged stand."""
    generator = rng(options)
    center = (0.0, 0.0, 0.8)

    for leg in range(3):
        angle = math.radians(90.0 + 120.0 * leg)
        foot = (0.34 * math.cos(angle), 0.34 * math.sin(angle), 0.025)
        knee = (0.2 * math.cos(angle), 0.2 * math.sin(angle), 0.3)
        rod(b, frame, foot, knee, 0.05, "wood", DARK_WOOD)
        rod(b, frame, knee, (0.36 * math.cos(angle), 0.36 * math.sin(angle), 0.78), 0.04, "wood", DARK_WOOD)

    hoop(b, frame, (0.0, 0.0, 0.3), 0.2, 0.02, "wood", DARK_WOOD, sides=8, tube_sides=3)
    hoop(b, frame, (0.0, 0.0, 0.79), 0.38, 0.022, "wood_light", WOOD["mel"], sides=12)
    hoop(b, frame, center, 0.37, 0.014, "metal", BRASS, sides=12, axis="Y")
    tilted = at(frame, center, 23.0, "Y")
    ball(b, tilted, (0.0, 0.0, 0.0), 0.35, "paint", options.get("tint", "3F8FD0"), segments=10)
    gem(b, tilted, (0.0, 0.0, 0.38), 0.03, "metal", GOLD)

    for patch in range(4):
        direction = Vector((generator.uniform(-1.0, 1.0), generator.uniform(-1.0, 1.0), generator.uniform(-0.7, 0.7))).normalized()
        placed = tilted @ Matrix.Translation(direction * 0.33) @ direction.to_track_quat("Z", "Y").to_matrix().to_4x4()
        ball(b, placed, (0.0, 0.0, 0.0), generator.uniform(0.09, 0.15), "paint", (LEAF, "E8D3A0", DEEP_LEAF)[patch % 3], scale=(1.0, 0.7, 0.25), segments=6)


def printing_press(b: Builder, frame: Matrix, **options) -> None:
    """Wooden screw press: two uprights, brass screw with an iron bar, platen, inked type bed and a raised paper frame."""
    wood = options.get("tint", DARK_WOOD)

    for side in (-1.0, 1.0):
        box(b, frame, (side * 0.45 - 0.07, -0.42, 0.0), (side * 0.45 + 0.07, 0.42, 0.12), "wood", wood)
        box(b, frame, (side * 0.45 - 0.06, -0.08, 0.12), (side * 0.45 + 0.06, 0.08, 1.85), "wood", wood)
        box(b, frame, (side * 0.3 - 0.03, -0.45, 0.72), (side * 0.3 + 0.03, 0.45, 0.78), "wood_light", WOOD["mel"])

    box(b, frame, (-0.55, -0.1, 1.62), (0.55, 0.1, 1.85), "wood", wood)
    box(b, frame, (-0.51, -0.09, 1.2), (0.51, 0.09, 1.32), "wood", wood)
    cyl(b, frame, (0.0, 0.0, 0.95), 0.05, 0.67, "metal", BRASS, sides=8)
    rod(b, frame, (0.0, 0.0, 1.08), (0.5, -0.38, 1.08), 0.03, "metal", DARK_IRON)
    ball(b, frame, (0.52, -0.4, 1.08), 0.045, "wood_light", WOOD["mel"], segments=6)
    box(b, frame, (-0.25, -0.2, 0.9), (0.25, 0.2, 0.96), "metal", "6E7FA8")
    box(b, frame, (-0.32, -0.35, 0.78), (0.32, 0.3, 0.82), "wood_light", WOOD["mel"])
    box(b, frame, (-0.25, -0.2, 0.82), (0.25, 0.2, 0.84), "paint", "2B2236")

    paper = at(frame, (0.0, -0.35, 0.82), -60.0, "X")
    box(b, paper, (-0.26, -0.34, 0.0), (0.26, 0.0, 0.012), "paint", PARCHMENT)
    box(b, paper, (-0.28, -0.36, -0.01), (0.28, -0.33, 0.015), "wood_light", WOOD["mel"])

    for side in (-1.0, 1.0):
        ball(b, frame, (side * 0.45, 0.3, 0.17), 0.06, "paint", "5A3A26", segments=6)
        cyl(b, frame, (side * 0.45, 0.3, 0.2), 0.015, 0.14, "wood_light", WOOD["mel"], sides=6)


def scroll_rack(b: Builder, frame: Matrix, **options) -> None:
    """Wall rack of 4 x 5 cubbies, each holding two parchment scrolls tied with coloured ribbons."""
    generator = rng(options)
    wood = options.get("tint", DARK_WOOD)
    columns, rows = 4, 5

    box(b, frame, (-0.6, 0.18, 0.0), (0.6, 0.2, 2.0), "paint", "6B3A2E")

    for column in range(columns + 1):
        box(b, frame, (-0.6 + column * 0.3 - 0.02, -0.2, 0.0), (-0.6 + column * 0.3 + 0.02, 0.18, 2.0), "wood", wood)

    for row in range(rows + 1):
        box(b, frame, (-0.6, -0.2, 0.1 + row * 0.38 - 0.02), (0.6, 0.18, 0.1 + row * 0.38 + 0.02), "wood_light", WOOD["mel"])

    for column, row, slot in itertools.product(range(columns), range(rows), range(2)):
        radius = generator.uniform(0.035, 0.05)
        x = -0.45 + column * 0.3 + (slot - 0.5) * 0.11
        z = 0.12 + row * 0.38 + radius + slot * 0.02
        cyl(b, frame, (x, -0.18, z), radius, 0.33, "paint", PARCHMENT, sides=6, axis="Y")
        box(b, frame, (x - radius - 0.004, -0.15, z - radius - 0.004), (x + radius + 0.004, -0.12, z + radius + 0.004), "paint", generator.choice(BOOK_COLORS))


def map_table(b: Builder, frame: Matrix, **options) -> None:
    """Cartographer's table: a big painted map (sea, lands, mountains, red route, gold compass rose), rolled maps and tools."""
    generator = rng(options)
    top = table(b, frame, 2.4, 1.4, 0.85, DARK_WOOD, WOOD["mel"])
    paper = top + 0.006

    box(b, frame, (-0.95, -0.55, top), (0.95, 0.55, paper), "paint", PARCHMENT)
    box(b, frame, (0.25, -0.5, paper), (0.9, 0.5, paper + 0.002), "paint", "8EC8E8")

    for index, (x, y, radius) in enumerate(((-0.45, 0.1, 0.32), (-0.1, -0.25, 0.2), (0.5, 0.2, 0.15))):
        cyl(b, frame, (x, y, paper), radius, 0.004, "paint", (LEAF, "E8D3A0", LEAF)[index], sides=7)

    for peak in range(4):
        cyl(b, frame, (-0.6 + 0.09 * peak, 0.2 - 0.05 * (peak % 2), paper + 0.004), 0.04, 0.05, "paint", "8B5A3C", sides=5, top=0.004)

    for dash in range(6):
        x, y = -0.35 + dash * 0.12, -0.05 + 0.05 * math.sin(dash)
        box(b, frame, (x - 0.03, y - 0.008, paper + 0.004), (x + 0.03, y + 0.008, paper + 0.007), "paint", "C9483B")

    gem(b, frame, (0.7, -0.3, paper + 0.006), 0.13, "metal", GOLD, scale=(0.22, 1.0, 0.04))
    gem(b, frame, (0.7, -0.3, paper + 0.006), 0.13, "metal", GOLD, scale=(1.0, 0.22, 0.04))

    for sign_x, sign_y in itertools.product((-1.0, 1.0), repeat=2):
        cyl(b, frame, (sign_x * 0.9, sign_y * 0.5, paper), 0.035, 0.04, "metal", BRASS, sides=6)

    for roll in range(2):
        cyl(b, frame, (-1.15, -0.45 + roll * 0.12, top + 0.04), 0.04, 0.5, "paint", (PARCHMENT, "E8D3A0")[roll], sides=6, axis="X")

    rod(b, frame, (0.1, 0.35, paper + 0.01), (0.25, 0.42, paper + 0.01), 0.01, "metal", BRASS)
    rod(b, frame, (0.1, 0.35, paper + 0.01), (0.27, 0.3, paper + 0.01), 0.01, "metal", BRASS)
    candle(b, frame, (1.05, 0.55, top), 0.12 + generator.uniform(0.0, 0.05))


def book_cart(b: Builder, frame: Matrix, **options) -> None:
    """Two-shelf rolling book cart with brass wheels and a push handle."""
    generator = rng(options)
    wood = options.get("tint", WOOD["media"])

    for side in (-1.0, 1.0):
        box(b, frame, (side * 0.45 - 0.03, -0.2, 0.1), (side * 0.45 + 0.03, 0.2, 0.9), "wood", wood)
        cyl(b, frame, (side * 0.45 - 0.02, -0.12, 0.06), 0.06, 0.04, "metal", BRASS, sides=8, axis="X")
        cyl(b, frame, (side * 0.45 - 0.02, 0.12, 0.06), 0.06, 0.04, "metal", BRASS, sides=8, axis="X")

    for shelf_z in (0.14, 0.52):
        box(b, frame, (-0.42, -0.2, shelf_z), (0.42, 0.2, shelf_z + 0.03), "wood_light", WOOD["mel"])
        book_row(b, frame, -0.41, 0.41, 0.0, shelf_z + 0.03, 0.26, 0.32, generator)

    box(b, frame, (-0.48, -0.22, 0.9), (0.48, 0.22, 0.93), "wood_light", WOOD["mel"])
    rod(b, frame, (0.48, 0.0, 0.92), (0.58, 0.0, 1.0), 0.03, "metal", BRASS)
    cyl(b, frame, (0.58, -0.18, 1.0), 0.02, 0.36, "wood_light", WOOD["mel"], sides=6, axis="Y")
    floating_book(b, at(frame, (-0.15, 0.0, 0.96), 15.0), "4F8FC9", False)
    floating_book(b, at(frame, (-0.12, 0.0, 1.02), -10.0), "C46AA8", False)


# ---------- jeweller and enchanter ----------

def jewel_case(b: Builder, frame: Matrix, **options) -> None:
    """Glass-topped jewellery counter: velvet bed with cushioned gems, a little crown, rings and a necklace."""
    velvet = options.get("tint", WINE)
    lid = 0.9

    for sign_x, sign_y in itertools.product((-1.0, 1.0), repeat=2):
        block(b, frame, (sign_x * 0.72, sign_y * 0.28, 0.05), (0.08, 0.08, 0.1), "metal", GOLD)

    box(b, frame, (-0.78, -0.33, 0.1), (0.78, 0.33, 0.88), "wood", DARK_WOOD)
    box(b, frame, (-0.7, -0.345, 0.22), (0.7, -0.33, 0.8), "metal", GOLD)
    box(b, frame, (-0.67, -0.35, 0.25), (0.67, -0.345, 0.77), "paint", NAVY)
    box(b, frame, (-0.78, -0.33, 0.88), (0.78, 0.33, lid), "paint", velvet)

    for sign_x, sign_y in itertools.product((-1.0, 1.0), repeat=2):
        block(b, frame, (sign_x * 0.765, sign_y * 0.315, 1.01), (0.03, 0.03, 0.22), "metal", GOLD)

    box(b, frame, (-0.75, -0.3, lid), (0.75, 0.3, 1.11), "vitrine")
    for start, end in (((-0.78, -0.315), (0.78, -0.315)), ((-0.78, 0.315), (0.78, 0.315)), ((-0.765, -0.315), (-0.765, 0.315)), ((0.765, -0.315), (0.765, 0.315))):
        rod(b, frame, (start[0], start[1], 1.12), (end[0], end[1], 1.12), 0.025, "metal", GOLD, depth=0.03)

    for index, glow in enumerate(("glow_pink", "glow_cyan", "glow_green")):
        x = -0.55 + index * 0.25
        block(b, frame, (x, 0.05, lid + 0.02), (0.14, 0.14, 0.04), "paint", NAVY)
        gem(b, frame, (x, 0.05, lid + 0.08), 0.035, glow)

    spin(b, frame, [(0.07, lid), (0.08, lid + 0.04), (0.08, lid + 0.06)], "metal", GOLD, base=(0.35, 0.08, 0.0))

    for point in range(5):
        angle = 2.0 * math.pi * point / 5.0
        gem(b, frame, (0.35 + 0.075 * math.cos(angle), 0.08 + 0.075 * math.sin(angle), lid + 0.08), 0.02, ("glow_pink", "metal")[point % 2], GOLD)

    for ring_index in range(4):
        x = 0.1 + ring_index * 0.17
        hoop(b, frame, (x, -0.18, lid + 0.03), 0.025, 0.006, "metal", (GOLD, SILVER)[ring_index % 2], sides=8, tube_sides=3, axis="Y")
        gem(b, frame, (x, -0.18, lid + 0.06), 0.014, GLOWS[ring_index])

    hoop(b, frame, (-0.4, -0.16, lid + 0.005), 0.09, 0.006, "metal", GOLD, sides=10, tube_sides=3)
    gem(b, frame, (-0.4, -0.25, lid + 0.015), 0.025, "glow_pink", scale=(1.0, 1.4, 0.5))


def necklace_busts(b: Builder, frame: Matrix, **options) -> None:
    """Display plinth with three velvet busts wearing necklaces with glowing pendants."""
    velvets = (NAVY, PLUM, TEAL)

    box(b, frame, (-0.5, -0.2, 0.0), (0.5, 0.2, 0.85), "wood", DARK_WOOD)
    box(b, frame, (-0.52, -0.22, 0.85), (0.52, 0.22, 0.88), "metal", GOLD)

    for index, x in enumerate((-0.32, 0.0, 0.32)):
        lift = 0.06 if index == 1 else 0.0
        base, shoulder, neck = 0.88, 1.06 + lift, 1.26 + lift
        points = [(x + dx, dy, base) for dx, dy in itertools.product((-0.12, 0.12), (-0.07, 0.07))]
        points += [(x + dx, dy, shoulder) for dx, dy in itertools.product((-0.13, 0.13), (-0.06, 0.06))]
        points += [(x + dx, dy, neck) for dx, dy in itertools.product((-0.04, 0.04), (-0.035, 0.035))]
        b.hull(points, "paint", srgb(velvets[index]), frame=frame)
        hoop(b, at(frame, (x, -0.015, shoulder + 0.02), -28.0, "X"), (0.0, 0.0, 0.0), 0.065, 0.007, "metal", (GOLD, SILVER, GOLD)[index], sides=10, tube_sides=3)
        gem(b, frame, (x, -0.085, shoulder - 0.03), 0.03, ("glow_cyan", "glow_pink", "glow_green")[index], scale=(1.0, 0.6, 1.4))


def goldsmith_bench(b: Builder, frame: Matrix, **options) -> None:
    """Goldsmith's bench: bench pin, leather catch, gem tray, tools, a little brick crucible furnace and a lens lamp."""
    generator = rng(options)
    top = table(b, frame, 1.4, 0.7, 0.9, DARK_WOOD, WOOD["mel"])

    box(b, frame, (-0.1, -0.38, top - 0.04), (0.1, -0.3, top - 0.01), "wood_light", WOOD["mel"])
    box(b, frame, (-0.4, -0.3, top - 0.25), (0.4, 0.2, top - 0.22), "paint", "8B5A3C")
    box(b, frame, (-0.2, 0.05, top), (0.1, 0.22, top + 0.03), "paint", NAVY)

    for gem_index in range(5):
        gem(b, frame, (-0.16 + gem_index * 0.055, 0.13, top + 0.05), 0.02, GLOWS[gem_index])

    for tool in range(4):
        x = -0.5 + tool * 0.05
        rod(b, frame, (x, -0.2, top + 0.01), (x + generator.uniform(-0.03, 0.03), 0.05, top + 0.01), 0.012, "metal", (SILVER, BRASS)[tool % 2])

    box(b, frame, (0.4, 0.0, top), (0.68, 0.32, top + 0.3), "paint", BRICK["vermelho"])
    box(b, frame, (0.46, -0.005, top + 0.06), (0.62, 0.0, top + 0.18), "glow_ember")
    spin(b, frame, [(0.04, top + 0.3), (0.06, top + 0.38), (0.06, top + 0.4)], "paint", "B5533F", sides=6, base=(0.54, 0.16, 0.0))
    cyl(b, frame, (0.54, 0.16, top + 0.4), 0.05, 0.005, "glow_amber", sides=6)

    rod(b, frame, (-0.6, 0.3, top), (-0.6, 0.3, top + 0.5), 0.03, "metal", BRASS)
    rod(b, frame, (-0.6, 0.3, top + 0.5), (-0.3, 0.0, top + 0.35), 0.025, "metal", BRASS)
    hoop(b, frame, (-0.28, -0.02, top + 0.33), 0.08, 0.012, "metal", GOLD, sides=10, tube_sides=3)
    cyl(b, frame, (-0.28, -0.02, top + 0.325), 0.07, 0.01, "vitrine", sides=10)
    gem(b, frame, (-0.6, 0.3, top + 0.53), 0.035, "glow_warm")


def enchant_table(b: Builder, frame: Matrix, **options) -> None:
    """Enchanting altar: lilac stone pedestals under an indigo slab with a glowing rune circle and a floating crystal."""
    slab = options.get("tint", "3E3263")

    for side in (-1.0, 1.0):
        box(b, frame, (side * 0.55 - 0.15, -0.35, 0.0), (side * 0.55 + 0.15, 0.35, 0.1), "paint", LILAC_STONE)
        box(b, frame, (side * 0.55 - 0.11, -0.28, 0.1), (side * 0.55 + 0.11, 0.28, 0.82), "paint", LILAC_STONE)
        gem(b, frame, (side * 0.55, -0.285, 0.5), 0.05, "glow_cyan", scale=(1.0, 0.4, 1.4))

    box(b, frame, (-0.75, -0.5, 0.82), (0.75, 0.5, 0.92), "paint", slab)
    box(b, frame, (-0.76, -0.51, 0.82), (0.76, 0.51, 0.84), "metal", GOLD)
    flat_ring(b, frame, 0.34, 0.03, "glow_cyan", sides=24, z=0.92)
    flat_ring(b, frame, 0.22, 0.02, "glow_pink", sides=16, z=0.92)

    for rune in range(8):
        angle = 22.5 + rune * 45.0
        placed = at(frame, (0.28 * math.cos(math.radians(angle)), 0.28 * math.sin(math.radians(angle)), 0.92), angle)
        box(b, placed, (-0.012, -0.035, 0.0), (0.012, 0.035, 0.008), "glow_cyan")

    crystal(b, frame, (0.0, 0.0, 1.12), 0.07, 0.24, "glow_cyan")
    crystal(b, at(frame, (0.0, 0.0, 1.12), 180.0, "X"), (0.0, 0.0, 0.0), 0.07, 0.12, "glow_cyan")
    floating_book(b, at(frame, (-0.52, 0.18, 0.95), 20.0), PLUM, True)
    candle(b, frame, (0.6, 0.35, 0.92), 0.16)
    candle(b, frame, (0.5, 0.4, 0.92), 0.1)


def rune_pillar(b: Builder, frame: Matrix, **options) -> None:
    """Tapered lilac stone obelisk carved with glowing runes, a crystal hovering above its tip."""
    stone = options.get("tint", LILAC_STONE)

    box(b, frame, (-0.3, -0.3, 0.0), (0.3, 0.3, 0.12), "paint", stone)
    b.hull([(x, y, z) for x, y, z in itertools.product((-0.22, 0.22), (-0.22, 0.22), (0.12,))] + [(x, y, 1.75) for x, y in itertools.product((-0.15, 0.15), repeat=2)] + [(0.0, 0.0, 1.95)], "paint", srgb(stone), frame=frame)

    for face, level in itertools.product(range(4), range(3)):
        z = 0.5 + level * 0.4
        half = 0.22 - 0.07 * (z - 0.12) / 1.63
        placed = at(frame, (0.0, 0.0, z), 90.0 * face)
        box(b, placed, (-0.03, -half - 0.012, -0.08), (0.03, -half + 0.01, 0.08), "glow_cyan")
        box(b, placed, (-0.08 + 0.05 * (level % 2), -half - 0.012, 0.02), (0.0 + 0.05 * (level % 2), -half + 0.01, 0.05), "glow_cyan")

    crystal(b, frame, (0.0, 0.0, 2.02), 0.05, 0.16, "glow_pink")


# ---------- tailor ----------

def fabric_shelf(b: Builder, frame: Matrix, **options) -> None:
    """Wall shelf of fabric bolts rolled in every colour, ends facing the customer."""
    generator = rng(options)
    boards = shelf_unit(b, frame, 2.0, 0.5, 2.2, [0.55, 1.05, 1.55], DARK_WOOD, back=options.get("tint", "F2D7C9"), crown=WOOD["mel"])
    colors = GOODS_PALETTE + ("F25C7A", "B57FE0", "4FB0D9")

    for surface in (0.08, *boards):
        cursor = -0.93

        while cursor < 0.75:
            radius = generator.uniform(0.07, 0.09)
            cyl(b, frame, (cursor + radius, -0.23, surface + radius), radius, 0.44, "paint", generator.choice(colors), sides=8, axis="Y")
            cursor += 2.0 * radius + 0.012


DRESS_STYLES = {  # variant -> (default colour, profile of the dressed body, accent colour)
    "dress": ("F25C7A", [(0.3, 0.42), (0.24, 0.7), (0.14, 1.04), (0.13, 1.12), (0.16, 1.3), (0.17, 1.4), (0.12, 1.48), (0.04, 1.52)], GOLD),
    "gown": ("B57FE0", [(0.38, 0.12), (0.3, 0.5), (0.15, 1.04), (0.13, 1.12), (0.16, 1.3), (0.17, 1.4), (0.12, 1.48), (0.04, 1.52)], "F2F0E6"),
    "cloak": (BONE, [(0.15, 0.9), (0.13, 1.1), (0.16, 1.3), (0.17, 1.4), (0.12, 1.48), (0.04, 1.52)], GOLD),
}


def dress_form(b: Builder, frame: Matrix, **options) -> None:
    """Tailor's mannequin on a tripod; variant dress | gown | cloak (a cloak over a linen form), tint = garment colour."""
    variant = options.get("variant") or "dress"
    default_color, profile, accent = DRESS_STYLES[variant]
    color = options.get("tint", "2F6BB0" if variant == "cloak" else default_color)

    for leg in range(3):
        angle = math.radians(90.0 + 120.0 * leg)
        rod(b, frame, (0.0, 0.0, 0.12), (0.24 * math.cos(angle), 0.24 * math.sin(angle), 0.02), 0.035, "wood", DARK_WOOD)

    cyl(b, frame, (0.0, 0.0, 0.1), 0.025, 1.0, "metal", BRASS, sides=6)
    spin(b, frame, profile, "paint", default_color if variant == "cloak" else color, sides=10)
    ball(b, frame, (0.0, 0.0, 1.6), 0.07, "wood_light", WOOD["mel"], segments=6)
    hoop(b, frame, (0.0, 0.0, 1.08), 0.135, 0.015, "metal", accent, sides=10, tube_sides=3)

    if variant == "cloak":
        b.hull([(-0.19, -0.02, 1.42), (0.19, -0.02, 1.42), (-0.15, 0.1, 1.5), (0.15, 0.1, 1.5), (-0.3, 0.0, 0.5), (0.3, 0.0, 0.5), (-0.34, 0.26, 0.45), (0.34, 0.26, 0.45), (0.0, 0.22, 1.62)], "paint", srgb(color), frame=frame)
        gem(b, frame, (0.0, -0.16, 1.38), 0.035, "metal", GOLD, scale=(1.0, 0.6, 1.0))
        return

    gem(b, frame, (0.0, -0.15, 1.2), 0.035, "glow_pink" if variant == "dress" else "glow_cyan", scale=(1.0, 0.6, 1.2))


def cutting_table(b: Builder, frame: Matrix, **options) -> None:
    """Cutting table: fabric spread and draped over the front, pattern paper, scissors, tape, pincushion and spools."""
    top = table(b, frame, 2.4, 1.2, 0.9, DARK_WOOD, WOOD["mel"], shelf=True)
    cloth = options.get("tint", "4F8FC9")

    box(b, frame, (-0.95, -0.6, top), (0.6, 0.45, top + 0.008), "paint", cloth)
    box(b, frame, (-0.95, -0.61, top - 0.35), (0.2, -0.6, top + 0.008), "paint", cloth)
    box(b, frame, (-0.6, -0.2, top + 0.008), (-0.1, 0.25, top + 0.012), "paint", PARCHMENT)

    for blade in (-35.0, 35.0):
        rod(b, at(frame, (0.3, -0.15, top + 0.02), blade), (-0.04, 0.0, 0.0), (0.22, 0.0, 0.0), 0.01, "metal", SILVER, depth=0.025)

    for side in (-1.0, 1.0):
        hoop(b, frame, (0.27, -0.15 + side * 0.04, top + 0.02), 0.03, 0.007, "metal", GOLD, sides=8, tube_sides=3)

    box(b, frame, (-1.1, 0.48, top), (0.9, 0.5, top + 0.003), "paint", "E8C14F")
    hoop(b, frame, (0.95, 0.42, top + 0.012), 0.05, 0.012, "paint", "E8C14F", sides=8, tube_sides=3)
    ball(b, frame, (0.8, -0.3, top + 0.04), 0.06, "paint", "C9483B", scale=(1.0, 1.0, 0.7), segments=6)

    for pin in range(3):
        gem(b, frame, (0.78 + 0.02 * pin, -0.32 + 0.02 * pin, top + 0.1), 0.01, "metal", (GOLD, SILVER)[pin % 2])

    for spool, color in enumerate(("F25C7A", "7FC46A", "6C5BB8", "E8C14F")):
        x = 0.75 + (spool % 2) * 0.12
        y = 0.05 + (spool // 2) * 0.14
        cyl(b, frame, (x, y, top), 0.035, 0.01, "wood_light", WOOD["mel"], sides=6)
        cyl(b, frame, (x, y, top + 0.01), 0.028, 0.07, "paint", color, sides=6)
        cyl(b, frame, (x, y, top + 0.08), 0.035, 0.01, "wood_light", WOOD["mel"], sides=6)

    for roll, color in enumerate(("C46AA8", "3F8A50", "E0884A")):
        cyl(b, frame, (-1.0, -0.4 + roll * 0.3, 0.18 + 0.08), 0.08, 1.9, "paint", color, sides=8, axis="X")


def spinning_wheel(b: Builder, frame: Matrix, **options) -> None:
    """Honey-wood spinning wheel (Ø0.7) on a slanted bench, with a treadle, a spindle of yarn and a wool distaff."""
    wood = options.get("tint", WOOD["mel"])
    hub = (0.22, 0.0, 0.62)

    rod(b, frame, (-0.45, 0.0, 0.42), (0.45, 0.0, 0.32), 0.06, "wood_light", wood, depth=0.22)

    for x, y in ((-0.38, -0.09), (-0.38, 0.09), (0.38, 0.0)):
        rod(b, frame, (x, y, 0.0), (x, y, 0.38), 0.04, "wood", DARK_WOOD)

    for side in (-1.0, 1.0):
        rod(b, frame, (hub[0], side * 0.06, 0.33), (hub[0], side * 0.06, hub[2] + 0.04), 0.035, "wood_light", wood)

    hoop(b, frame, hub, 0.34, 0.02, "wood_light", wood, sides=16, axis="Y")
    cyl(b, frame, (hub[0], -0.08, hub[2]), 0.045, 0.16, "wood", DARK_WOOD, sides=8, axis="Y")

    for spoke in range(4):
        angle = math.radians(spoke * 45.0)
        rod(b, frame, (hub[0] + 0.33 * math.cos(angle), 0.0, hub[2] + 0.33 * math.sin(angle)), (hub[0] - 0.33 * math.cos(angle), 0.0, hub[2] - 0.33 * math.sin(angle)), 0.02, "wood_light", wood)

    box(b, frame, (0.05, -0.2, 0.0), (0.4, -0.08, 0.03), "wood", DARK_WOOD)
    rod(b, frame, (-0.25, 0.0, 0.4), (-0.25, 0.0, 0.62), 0.04, "wood", DARK_WOOD)
    cyl(b, frame, (-0.35, 0.0, 0.62), 0.04, 0.2, "paint", options.get("yarn", "C46AA8"), sides=8, axis="X")
    rod(b, frame, (-0.42, 0.0, 0.38), (-0.42, 0.0, 0.88), 0.03, "wood", DARK_WOOD)
    ball(b, frame, (-0.42, 0.0, 0.9), 0.09, "paint", "F2F0E6", scale=(1.0, 1.0, 1.4), segments=6)


def loom(b: Builder, frame: Matrix, **options) -> None:
    """Floor loom: posts and beams, striped warp threads, half-woven cloth, heddle frame and a shuttle."""
    wood = options.get("tint", WOOD["media"])
    stripes = ("C9483B", "E8C14F", "4F8FC9", "F2F0E6", "3F8A50", "C46AA8")

    for x, y in itertools.product((-0.6, 0.6), (-0.45, 0.45)):
        rod(b, frame, (x, y, 0.0), (x, y, 1.0 if y < 0.0 else 1.5), 0.07, "wood", wood)

    for side in (-0.6, 0.6):
        rod(b, frame, (side, -0.45, 0.25), (side, 0.45, 0.25), 0.05, "wood", wood)

    cyl(b, frame, (-0.6, -0.45, 0.88), 0.06, 1.2, "wood_light", WOOD["mel"], sides=8, axis="X")
    cyl(b, frame, (-0.6, 0.45, 1.45), 0.06, 1.2, "wood_light", WOOD["mel"], sides=8, axis="X")

    for index, color in enumerate(stripes):
        x = -0.48 + index * 0.19
        rod(b, frame, (x, -0.1, 1.02), (x, 0.42, 1.48), 0.008, "paint", color, depth=0.17)

    for band, color in enumerate(stripes[:4]):
        box(b, frame, (-0.56, -0.44 + band * 0.08, 0.93), (0.56, -0.36 + band * 0.08, 0.95), "paint", color)

    box(b, frame, (-0.58, -0.08, 0.95), (0.58, -0.04, 1.3), "wood_light", WOOD["mel"])
    box(b, frame, (-0.58, -0.08, 1.12), (0.58, -0.04, 1.15), "metal", BRASS)
    b.hull([(-0.12, -0.2, 0.96), (0.12, -0.2, 0.96), (0.0, -0.18, 0.96), (0.0, -0.22, 0.96), (0.0, -0.2, 0.99)], "wood", srgb(DARK_WOOD), frame=frame)


GARMENT_SHAPES = {  # kind -> (top half width, bottom half width, length)
    "shirt": (0.19, 0.22, 0.6),
    "coat": (0.2, 0.26, 0.95),
    "dress": (0.15, 0.3, 1.0),
}


def clothes_rail(b: Builder, frame: Matrix, **options) -> None:
    """Brass clothes rail with eight hanging garments (shirts, coats and dresses) in assorted colours."""
    generator = rng(options)
    rail = 1.6
    colors = ("F25C7A", "4F8FC9", "7FC46A", "E8C14F", "B57FE0", "E0884A", "1F6B6B", "C9483B")

    for side in (-0.76, 0.76):
        rod(b, frame, (side, -0.28, 0.02), (side, 0.28, 0.02), 0.04, "metal", BRASS)
        rod(b, frame, (side, 0.0, 0.02), (side, 0.0, rail + 0.04), 0.035, "metal", BRASS)
        ball(b, frame, (side, 0.0, rail + 0.07), 0.035, "metal", GOLD, segments=6)

    cyl(b, frame, (-0.76, 0.0, rail), 0.02, 1.52, "metal", BRASS, sides=6, axis="X")

    for index in range(8):
        x = -0.6 + index * 0.17 + generator.uniform(-0.02, 0.02)
        top_half, bottom_half, length = GARMENT_SHAPES[("shirt", "coat", "dress")[index % 3]]
        hoop(b, frame, (x, 0.0, rail + 0.01), 0.025, 0.005, "metal", SILVER, sides=6, tube_sides=3, axis="X")
        rod(b, frame, (x, -top_half, rail - 0.04), (x, top_half, rail - 0.04), 0.015, "wood_light", WOOD["mel"])
        b.side_prism([(-top_half, rail - 0.05), (top_half, rail - 0.05), (bottom_half, rail - 0.05 - length), (-bottom_half, rail - 0.05 - length)], x - 0.035, x + 0.035, "paint", srgb(colors[index]), frame=frame)


def fitting_booth(b: Builder, frame: Matrix, **options) -> None:
    """Fitting booth: wooden back and side panels, a pleated velvet curtain on a gold rod, mirror and stool inside."""
    curtain = options.get("tint", TEAL)
    wood = DARK_WOOD

    box(b, frame, (-0.7, 0.62, 0.0), (0.7, 0.7, 2.2), "wood", wood)

    for side in (-1.0, 1.0):
        box(b, frame, (side * 0.7 - 0.04, -0.7, 0.0), (side * 0.7 + 0.04, 0.7, 2.2), "wood", wood)
        box(b, frame, (side * 0.7 - 0.045, -0.55, 0.3), (side * 0.7 + 0.045, 0.55, 1.9), "paint", "F2D7C9")

    box(b, frame, (-0.74, -0.7, 2.2), (0.74, 0.7, 2.3), "wood", wood)
    box(b, frame, (-0.75, -0.71, 2.22), (0.75, -0.69, 2.26), "metal", GOLD)
    cyl(b, frame, (-0.66, -0.62, 2.12), 0.018, 1.32, "metal", GOLD, sides=6, axis="X")

    for pleat in range(8):
        x = -0.62 + pleat * 0.1
        placed = at(frame, (x, -0.62, 0.04), 30.0 if pleat % 2 else -30.0)
        box(b, placed, (-0.06, -0.012, 0.0), (0.06, 0.012, 2.08), "paint", curtain)

    box(b, frame, (-0.25, 0.6, 0.35), (0.25, 0.62, 1.85), "metal", GOLD)
    box(b, frame, (-0.22, 0.595, 0.38), (0.22, 0.6, 1.82), "paint", "CFE6F2")
    cyl(b, frame, (0.35, 0.2, 0.0), 0.16, 0.42, "wood_light", WOOD["mel"], sides=8)
    cyl(b, frame, (0.35, 0.2, 0.42), 0.17, 0.05, "paint", WINE, sides=8)
    b.side_prism([(-0.18, 1.75), (0.18, 1.75), (0.22, 1.05), (-0.22, 1.05)], -0.6, -0.55, "paint", srgb("E8C14F"), frame=frame)


def hat(b: Builder, frame: Matrix, kind: str, color: str) -> None:
    """One hat standing on its brim at the frame origin."""
    shapes = {
        "wizard": lambda: wizard_hat(b, frame, color),
        "top": lambda: (cyl(b, frame, (0.0, 0.0, 0.0), 0.15, 0.012, "paint", color, sides=10), cyl(b, frame, (0.0, 0.0, 0.012), 0.09, 0.2, "paint", color, sides=10, top=0.1), cyl(b, frame, (0.0, 0.0, 0.03), 0.093, 0.04, "paint", GOLD, sides=10)),
        "sun": lambda: (cyl(b, frame, (0.0, 0.0, 0.0), 0.2, 0.012, "paint", color, sides=10), ball(b, frame, (0.0, 0.0, 0.01), 0.1, "paint", color, scale=(1.0, 1.0, 0.8), segments=8), cyl(b, frame, (0.0, 0.0, 0.012), 0.102, 0.03, "paint", "F25C7A", sides=8)),
        "beret": lambda: ball(b, frame, (0.0, 0.0, 0.05), 0.13, "paint", color, scale=(1.0, 1.0, 0.4), segments=8),
        "feather": lambda: (ball(b, frame, (0.0, 0.0, 0.0), 0.11, "paint", color, scale=(1.0, 1.0, 0.75), segments=8), b.hull([(0.06, 0.0, 0.05), (0.1, 0.0, 0.05), (0.2, 0.0, 0.3), (0.13, 0.015, 0.2)], "paint", srgb("F2F0E6"), frame=frame)),
    }

    shapes[kind]()


def hat_shelf(b: Builder, frame: Matrix, **options) -> None:
    """Wall shelf of hats on a blush back panel: wizard, top, sun, beret and feathered caps."""
    generator = rng(options)
    boards = shelf_unit(b, frame, 1.2, 0.45, 1.9, [0.45, 0.95, 1.45], DARK_WOOD, back=options.get("tint", "F2D7C9"), crown=WOOD["mel"])
    kinds = ("top", "sun", "beret", "wizard", "feather", "top", "beret", "sun", "wizard")
    colors = ("2B2236", "F2E6CF", "C9483B", "5B3FA8", "3F8A50", "8E2F45", "4F8FC9", "E8C14F", "1F6B6B")

    for index, (surface, slot) in enumerate(itertools.product(boards, range(3))):
        hat(b, at(frame, (-0.37 + slot * 0.37, 0.0, surface), generator.uniform(-20.0, 20.0)), kinds[index], colors[index])


def yarn_basket(b: Builder, frame: Matrix, **options) -> None:
    """Wicker basket heaped with balls of yarn and two knitting needles."""
    generator = rng(options)
    colors = ("F25C7A", "4FB0D9", "E8C14F", "7FC46A", "B57FE0", "E0884A")

    spin(b, frame, [(0.2, 0.0), (0.27, 0.05), (0.29, 0.24), (0.27, 0.25)], "wood_light", options.get("tint", "D9B07A"), sides=10)
    hoop(b, frame, (0.0, 0.0, 0.245), 0.285, 0.02, "wood_light", "C08A55", sides=10, tube_sides=3)

    for index, color in enumerate(colors):
        angle = index * 1.05
        spread = 0.0 if index == 5 else 0.15
        ball(b, frame, (spread * math.cos(angle), spread * math.sin(angle), 0.3 + (0.06 if index == 5 else 0.0)), generator.uniform(0.08, 0.1), "paint", color, segments=6)

    for lean in (-0.05, 0.05):
        rod(b, frame, (lean, -0.05, 0.3), (lean + 0.1, 0.1, 0.44), 0.012, "metal", SILVER)


def dye_vats(b: Builder, frame: Matrix, **options) -> None:
    """Three hooped wooden dye tubs (crimson, indigo, saffron), a paddle, and dyed cloth drying on a rod behind."""
    colors = ("C9283B", "2F3FA8", "F2B13C")

    for index, color in enumerate(colors):
        x = -0.6 + index * 0.6
        spin(b, frame, [(0.25, 0.0), (0.29, 0.6)], "wood_light", WOOD["mel"], sides=10, base=(x, -0.1, 0.0))
        hoop(b, frame, (x, -0.1, 0.12), 0.26, 0.015, "metal", DARK_IRON, sides=10, tube_sides=3)
        hoop(b, frame, (x, -0.1, 0.48), 0.28, 0.015, "metal", DARK_IRON, sides=10, tube_sides=3)
        cyl(b, frame, (x, -0.1, 0.6), 0.27, 0.01, "paint", color, sides=10)
        box(b, frame, (x - 0.15, 0.31, 0.45), (x + 0.15, 0.33, 0.93), "paint", color)

    rod(b, frame, (0.55, -0.1, 0.55), (0.72, 0.05, 0.95), 0.03, "wood_light", WOOD["mel"])
    box(b, frame, (-0.4, -0.33, 0.35), (-0.25, -0.31, 0.61), "paint", colors[0])
    box(b, frame, (-0.4, -0.31, 0.61), (-0.25, -0.15, 0.625), "paint", colors[0])

    for side in (-0.88, 0.88):
        rod(b, frame, (side, 0.32, 0.0), (side, 0.32, 0.98), 0.04, "wood", DARK_WOOD)

    cyl(b, frame, (-0.9, 0.32, 0.95), 0.018, 1.8, "wood", DARK_WOOD, sides=6, axis="X")


# ---------- herbalist and florist ----------

def drying_rack_herbs(b: Builder, frame: Matrix, **options) -> None:
    """Open drying rack: three mesh trays of leaves and petals, herb bundles hanging from the top rail."""
    generator = rng(options)
    colors = (LEAF, DEEP_LEAF, "B57FE0", "F2B13C", "F25C7A")

    for x, y in itertools.product((-0.56, 0.56), (-0.26, 0.26)):
        rod(b, frame, (x, y, 0.0), (x, y, 1.8), 0.05, "wood", DARK_WOOD)

    rod(b, frame, (-0.56, 0.0, 1.75), (0.56, 0.0, 1.75), 0.05, "wood", DARK_WOOD)

    for tray_z in (0.25, 0.6, 0.95):
        box(b, frame, (-0.54, -0.26, tray_z), (0.54, 0.26, tray_z + 0.02), "paint", "E8D9B0")
        box(b, frame, (-0.56, -0.28, tray_z + 0.02), (0.56, -0.25, tray_z + 0.05), "wood_light", WOOD["mel"])

        for leaf in range(6):
            gem(b, frame, (generator.uniform(-0.45, 0.45), generator.uniform(-0.18, 0.18), tray_z + 0.03), generator.uniform(0.04, 0.06), "paint", generator.choice(colors), scale=(1.6, 1.0, 0.3))

    for index, (kind, color) in enumerate(HERB_KINDS[:4]):
        herb_bundle(b, at(frame, (0.0, 0.0, 1.75 + 0.7), 0.0), -0.39 + index * 0.26, 0.0, kind, color)


def seed_drawers(b: Builder, frame: Matrix, **options) -> None:
    """Apothecary seed cabinet: 4 x 5 labelled drawers with brass knobs (one pulled out) and seed jars on top."""
    wood = options.get("tint", DARK_WOOD)
    frame = at(frame, (0.0, 0.075, 0.0))

    box(b, frame, (-0.6, -0.2, 0.0), (0.6, 0.225, 1.3), "wood", wood)
    box(b, frame, (-0.62, -0.22, 1.3), (0.62, 0.225, 1.34), "wood_light", WOOD["mel"])

    for column, row in itertools.product(range(4), range(5)):
        x, z = -0.42 + column * 0.28, 0.18 + row * 0.24
        pull = -0.08 if (column, row) == (1, 1) else 0.0
        box(b, frame, (x - 0.12, -0.22 + pull, z - 0.1), (x + 0.12, -0.2 + pull, z + 0.1), "wood_light", WOOD["mel"])
        box(b, frame, (x - 0.06, -0.225 + pull, z + 0.02), (x + 0.06, -0.22 + pull, z + 0.07), "paint", PARCHMENT)
        gem(b, frame, (x, -0.235 + pull, z - 0.03), 0.02, "metal", BRASS, scale=(1.0, 0.8, 1.0))



    for index, color in enumerate(("E8C14F", "8B5A3C", "7FC46A")):
        x = -0.35 + index * 0.35
        cyl(b, frame, (x, 0.0, 1.34), 0.08, 0.16, "paint", color, sides=8)
        cyl(b, frame, (x, 0.0, 1.5), 0.07, 0.03, "wood_light", WOOD["mel"], sides=8)


def bouquet(b: Builder, frame: Matrix, x: float, y: float, z: float, generator: random.Random) -> None:
    """Coloured bucket of flowers standing at (x, y, z)."""
    cyl(b, frame, (x, y, z), 0.09, 0.22, "metal", generator.choice(("8EC8E8", "F2B13C", "D0745A", "7FC46A")), sides=8, top=0.11)
    cyl(b, frame, (x, y, z + 0.2), 0.05, 0.16, "paint", DEEP_LEAF, sides=6, top=0.13)

    for bloom in range(4):
        angle = bloom * math.pi / 2.0 + generator.uniform(0.0, 0.6)
        ball(b, frame, (x + 0.08 * math.cos(angle), y + 0.08 * math.sin(angle), z + 0.38 + 0.05 * (bloom % 2)), 0.05, "paint", generator.choice(FLOWER_COLORS), segments=4)


def flower_steps(b: Builder, frame: Matrix, **options) -> None:
    """Three wooden steps of flower buckets, front step lowest."""
    generator = rng(options)
    steps = ((-0.5, 0.3), (-0.17, 0.6), (0.17, 0.9))

    for front, height in steps:
        box(b, frame, (-0.8, front, 0.0), (0.8, 0.5, height), "wood_light", options.get("tint", WOOD["mel"]))
        box(b, frame, (-0.8, front - 0.01, height - 0.04), (0.8, front, height), "paint", "F2F0E6")

    for (front, height), slot in itertools.product(steps, range(3)):
        bouquet(b, frame, -0.5 + slot * 0.5 + generator.uniform(-0.05, 0.05), front + 0.16, height, generator)


def planter_box(b: Builder, frame: Matrix, **options) -> None:
    """Long painted planter on short legs, full of leafy clumps and flowers."""
    generator = rng(options)
    paint = options.get("tint", "6FA0C8")

    for x in (-0.55, 0.55):
        box(b, frame, (x - 0.04, -0.2, 0.0), (x + 0.04, 0.2, 0.1), "wood", DARK_WOOD)

    box(b, frame, (-0.6, -0.25, 0.1), (0.6, 0.25, 0.5), "paint", paint)
    box(b, frame, (-0.62, -0.27, 0.48), (0.62, 0.27, 0.52), "wood_light", WOOD["mel"])
    box(b, frame, (-0.56, -0.21, 0.5), (0.56, 0.21, 0.53), "paint", "6B4A3A")

    for clump in range(4):
        x = -0.42 + clump * 0.28
        ball(b, frame, (x, 0.0, 0.62), 0.16, "paint", (LEAF, DEEP_LEAF)[clump % 2], scale=(1.0, 0.9, 0.75), segments=6)
        ball(b, frame, (x + 0.06, -0.1, 0.72), 0.05, "paint", generator.choice(FLOWER_COLORS), segments=4)


def hanging_pot(b: Builder, frame: Matrix, x: float, drop: float, generator: random.Random) -> None:
    """Terracotta pot hung on three ropes from the ceiling (z = 0) with foliage and trailing vines."""
    rim = -drop + 0.22

    cyl(b, frame, (x, 0.0, -0.03), 0.04, 0.03, "metal", DARK_IRON, sides=6)

    for rope in range(3):
        angle = math.radians(90.0 + rope * 120.0)
        rod(b, frame, (x, 0.0, -0.03), (x + 0.15 * math.cos(angle), 0.15 * math.sin(angle), rim), 0.012, "paint", "C9A46A")

    spin(b, frame, [(0.09, -drop), (0.16, rim - 0.02), (0.17, rim)], "paint", "D0745A", base=(x, 0.0, 0.0))
    ball(b, frame, (x, 0.0, rim + 0.04), 0.17, "paint", LEAF, scale=(1.0, 1.0, 0.5), segments=6)

    for vine in range(4):
        angle = vine * math.pi / 2.0 + 0.4
        start = (x + 0.15 * math.cos(angle), 0.15 * math.sin(angle), rim)
        end = (start[0] + 0.05 * math.cos(angle), start[1] + 0.05 * math.sin(angle), rim - generator.uniform(0.3, 0.5))
        rod(b, frame, start, end, 0.015, "paint", DEEP_LEAF)
        gem(b, frame, end, 0.04, "paint", LEAF, scale=(1.0, 1.0, 0.6))

    ball(b, frame, (x + 0.05, -0.08, rim + 0.1), 0.04, "paint", generator.choice(FLOWER_COLORS), segments=4)


def hanging_plants(b: Builder, frame: Matrix, **options) -> None:
    """Ceiling prop: two rope-hung terracotta pots at different drops with trailing vines."""
    generator = rng(options)

    hanging_pot(b, frame, -0.3, 1.0, generator)
    hanging_pot(b, frame, 0.3, 0.75, generator)


def watering_cans(b: Builder, frame: Matrix, **options) -> None:
    """Three painted watering cans (copper, sage, blue) with spouts, roses and handles."""
    for index, color in enumerate((COPPER, "5FA08A", "4F8FC9")):
        x, size = -0.27 + index * 0.27, (1.3, 1.05, 0.85)[index]
        cyl(b, frame, (x, 0.0, 0.0), 0.09 * size, 0.24 * size, "metal", color, sides=8)
        rod(b, frame, (x + 0.06 * size, -0.03, 0.05 * size), (x + 0.06 * size, -0.2 * size, 0.28 * size), 0.025 * size, "metal", color)
        cyl(b, frame, (x + 0.06 * size, -0.2 * size, 0.27 * size), 0.03 * size, 0.03 * size, "metal", BRASS, sides=6)
        hoop(b, frame, (x, 0.0, 0.24 * size), 0.07 * size, 0.012, "metal", color, sides=8, tube_sides=3, axis="X")


# ---------- general store ----------

def hanging_lantern(b: Builder, frame: Matrix, x: float, top: float) -> None:
    rod(b, frame, (x, 0.0, top), (x, 0.0, top - 0.12), 0.012, "metal", DARK_IRON)
    cyl(b, frame, (x, 0.0, top - 0.2), 0.08, 0.08, "metal", DARK_IRON, sides=4, top=0.02)
    box(b, frame, (x - 0.06, -0.06, top - 0.42), (x + 0.06, 0.06, top - 0.2), "glow_warm")
    box(b, frame, (x - 0.075, -0.075, top - 0.45), (x + 0.075, 0.075, top - 0.42), "metal", DARK_IRON)


def hanging_goods(b: Builder, frame: Matrix, **options) -> None:
    """Ceiling prop: chain-hung goods rack with lanterns, copper pots and pans, rope coils and a basket."""
    rack = -0.5

    for side in (-0.85, 0.85):
        box(b, frame, (side - 0.05, -0.05, -0.02), (side + 0.05, 0.05, 0.0), "metal", DARK_IRON)
        rod(b, frame, (side, 0.0, -0.02), (side, 0.0, rack), 0.02, "metal", DARK_IRON)

    box(b, frame, (-1.0, -0.04, rack - 0.06), (1.0, 0.04, rack), "wood", DARK_WOOD)
    hanging_lantern(b, frame, -0.9, rack - 0.06)
    hanging_lantern(b, frame, 0.9, rack - 0.06)

    for x in (-0.6, -0.15):
        rod(b, frame, (x, 0.0, rack - 0.06), (x, 0.0, rack - 0.2), 0.012, "metal", DARK_IRON)
        spin(b, frame, [(0.08, rack - 0.42), (0.13, rack - 0.36), (0.13, rack - 0.24), (0.1, rack - 0.2)], "metal", COPPER, sides=8, base=(x, 0.0, 0.0))

    for x in (0.15, 0.62):
        rod(b, frame, (x, 0.0, rack - 0.06), (x, 0.0, rack - 0.3), 0.025, "metal", DARK_IRON)
        cyl(b, frame, (x, -0.015, rack - 0.42), 0.12, 0.03, "metal", DARK_IRON, sides=10, axis="Y")

    hoop(b, frame, (-0.38, 0.0, rack - 0.25), 0.12, 0.03, "paint", "C9A46A", sides=10, tube_sides=4, axis="Y")
    hoop(b, frame, (0.38, 0.0, rack - 0.22), 0.1, 0.028, "paint", "B79A6A", sides=10, tube_sides=4, axis="Y")
    rod(b, frame, (0.38, 0.0, rack - 0.06), (0.38, 0.0, rack - 0.12), 0.02, "metal", DARK_IRON)
    rod(b, frame, (-0.38, 0.0, rack - 0.06), (-0.38, 0.0, rack - 0.13), 0.02, "metal", DARK_IRON)


def backpack(b: Builder, frame: Matrix, x: float, z: float, color: str, roll: str) -> None:
    """Leather backpack hung on a wall peg at (x, z): body, flap, pocket, buckles and a bedroll on top."""
    box(b, frame, (x - 0.17, 0.0, z - 0.45), (x + 0.17, 0.18, z), "paint", color)
    box(b, frame, (x - 0.175, -0.01, z - 0.2), (x + 0.175, 0.06, z + 0.01), "paint", "6B3A2E")
    box(b, frame, (x - 0.11, -0.04, z - 0.42), (x + 0.11, 0.0, z - 0.24), "paint", color)
    gem(b, frame, (x, -0.02, z - 0.2), 0.02, "metal", BRASS, scale=(1.0, 0.6, 1.0))
    cyl(b, frame, (x - 0.2, 0.08, z + 0.07), 0.07, 0.4, "paint", roll, sides=8, axis="X")


def backpack_wall(b: Builder, frame: Matrix, **options) -> None:
    """Pegboard wall of four adventurer's backpacks with bedrolls, and a low shelf of rolled blankets and waterskins."""
    board = options.get("tint", WOOD["mel"])

    box(b, frame, (-0.9, 0.17, 0.0), (0.9, 0.2, 2.1), "wood_light", board)
    box(b, frame, (-0.9, -0.2, 0.42), (0.9, 0.17, 0.46), "wood", DARK_WOOD)

    for x in (-0.85, 0.85):
        box(b, frame, (x - 0.03, -0.2, 0.0), (x + 0.03, 0.17, 0.42), "wood", DARK_WOOD)

    for index, (color, roll) in enumerate((("B5533F", "F2E6CF"), ("3F8A50", "C9483B"), ("4F8FC9", "E8C14F"), ("C08A55", "6C5BB8"))):
        x = -0.63 + index * 0.42
        cyl(b, frame, (x, -0.02, 1.8), 0.015, 0.19, "metal", BRASS, sides=6, axis="Y")
        backpack(b, frame, x, 1.75, color, roll)

    for index, color in enumerate(("C9483B", "4F8FC9", "7FC46A")):
        cyl(b, frame, (-0.8, -0.1 + 0.0 * index, 0.54 + index * 0.16), 0.08, 0.8, "paint", color, sides=8, axis="X")

    for x in (0.35, 0.6):
        ball(b, frame, (x, 0.0, 0.6), 0.13, "paint", "8B5A3C", scale=(0.9, 0.7, 1.1), segments=6)
        cyl(b, frame, (x, 0.0, 0.73), 0.03, 0.08, "wood_light", WOOD["mel"], sides=6)


def tool_rack(b: Builder, frame: Matrix, **options) -> None:
    """Wall tool rack: a floor trough and a pegged rail holding shovels, pickaxes, a rake and a hoe."""
    wood = options.get("tint", DARK_WOOD)

    box(b, frame, (-0.7, 0.16, 0.0), (0.7, 0.2, 1.8), "paint", options.get("board", "A9C79A"))
    box(b, frame, (-0.7, -0.2, 0.0), (0.7, 0.16, 0.1), "wood", wood)
    box(b, frame, (-0.7, 0.04, 1.35), (0.7, 0.16, 1.45), "wood", wood)

    for index, kind in enumerate(("shovel", "pick", "rake", "shovel", "pick", "hoe")):
        x = -0.55 + index * 0.22
        handle_top = 1.6 if kind == "shovel" else 1.3
        rod(b, frame, (x, -0.02, 0.12), (x, 0.0, handle_top), 0.035, "wood_light", "E0B070")
        tools = {
            "shovel": lambda: (b.hull([(x - 0.1, -0.05, 0.16), (x + 0.1, -0.05, 0.16), (x - 0.11, -0.05, 0.44), (x + 0.11, -0.05, 0.44), (x, -0.08, 0.11), (x, -0.03, 0.46)], "metal", srgb(SILVER), frame=frame), rod(b, frame, (x - 0.06, 0.0, handle_top), (x + 0.06, 0.0, handle_top), 0.03, "wood", wood)),
            "pick": lambda: (rod(b, frame, (x - 0.2, -0.01, 1.22), (x, -0.01, 1.32), 0.035, "metal", "B8C6E8"), rod(b, frame, (x, -0.01, 1.32), (x + 0.2, -0.01, 1.22), 0.035, "metal", "B8C6E8")),
            "rake": lambda: (rod(b, frame, (x - 0.12, -0.01, 1.3), (x + 0.12, -0.01, 1.3), 0.03, "metal", "B8C6E8"), [rod(b, frame, (x + tooth * 0.06, -0.01, 1.3), (x + tooth * 0.06, -0.06, 1.24), 0.012, "metal", "B8C6E8") for tooth in range(-2, 3)]),
            "hoe": lambda: box(b, frame, (x - 0.07, -0.1, 1.24), (x + 0.07, -0.02, 1.32), "metal", "B8C6E8"),
        }
        tools[kind]()


def blanket_pile(b: Builder, frame: Matrix, **options) -> None:
    """Stack of five folded quilts with stripes, a pillow on top and a rolled blanket leaning on it."""
    colors = (("C9483B", "F2E6CF"), ("4F8FC9", "E8C14F"), ("7FC46A", "F2F0E6"), ("B57FE0", "F25C7A"), ("E0884A", "6C5BB8"))

    for layer, (color, stripe) in enumerate(colors):
        placed = at(frame, (0.0, 0.0, layer * 0.11), (-6.0, 4.0, -3.0, 7.0, 0.0)[layer])
        box(b, placed, (-0.36, -0.28, 0.0), (0.36, 0.28, 0.11), "paint", color)
        box(b, placed, (-0.365, -0.285, 0.035), (0.365, 0.285, 0.065), "paint", stripe)

    ball(b, frame, (0.05, 0.0, 0.62), 0.2, "paint", "F2F0E6", scale=(1.2, 0.8, 0.35), segments=8)
    cyl(b, at(frame, (0.42, 0.0, 0.0), 0.0), (0.0, -0.3, 0.1), 0.1, 0.6, "paint", "3F8A50", sides=8, axis="Y")


def cat_sleeping(b: Builder, frame: Matrix, **options) -> None:
    """Small prop: a ginger cat curled up asleep on a cushion (closed eyes, ears, tail around the body)."""
    fur = options.get("tint", "E0884A")

    cyl(b, frame, (0.0, 0.0, 0.0), 0.22, 0.05, "paint", WINE, sides=6)
    ball(b, frame, (0.02, 0.03, 0.12), 0.16, "paint", fur, scale=(1.0, 0.75, 0.5), segments=6)
    ball(b, frame, (-0.11, -0.06, 0.15), 0.075, "paint", fur, segments=6)

    for side in (-1.0, 1.0):
        b.hull([(-0.11 + side * 0.05, -0.06, 0.2), (-0.11 + side * 0.02, -0.08, 0.2), (-0.11 + side * 0.03, -0.04, 0.2), (-0.11 + side * 0.05, -0.06, 0.26)], "paint", srgb(fur), frame=frame)
        box(b, frame, (-0.11 + side * 0.03 - 0.018, -0.137, 0.155), (-0.11 + side * 0.03 + 0.018, -0.13, 0.162), "paint", "2B2236")

    rod(b, frame, (0.15, 0.0, 0.08), (0.1, -0.13, 0.07), 0.04, "paint", fur)
    rod(b, frame, (0.1, -0.13, 0.07), (-0.04, -0.15, 0.07), 0.035, "paint", "F2E6CF")


# ---------- architecture: screens, doorways, wainscot, galleries, stairs ----------

PLASTER = "F1E4CB"
INDIGO = "3E3263"
SCREEN_HEIGHT = 3.0
RUG_PALETTES = {  # variant -> (field, border, medallion, motif)
    "red": ("B5333F", "E8B64A", "7A1F33", "F2E6CF"),
    "blue": ("2F4FA3", "E8B64A", "1C2D6B", "BFD8F2"),
    "green": ("2F7A4F", "E8B64A", "1F5236", "F2E6CF"),
    "plum": ("7A3F8E", "F2C86B", "4A2A63", "F5D9F2"),
}


def arch_outline(half: float, spring: float, rise: float, segments: int = 8) -> list:
    """Points (x, z) of an elliptic arch from the left springing to the right one."""
    return [(-half * math.cos(math.pi * step / segments), spring + rise * math.sin(math.pi * step / segments)) for step in range(segments + 1)]


def screen_panels(b: Builder, frame: Matrix, x_from: float, x_to: float, z_from: float, z_to: float, tone: str, thickness: float = 0.07) -> None:
    """A field of wood with a raised panel proud of each face, centred on y = 0."""
    box(b, frame, (x_from, -thickness, z_from), (x_to, thickness, z_to), "wood_light", tone)

    for sign in (-1.0, 1.0):
        near, far = sorted((sign * thickness, sign * (thickness + 0.018)))
        box(b, frame, (x_from + 0.07, near, z_from + 0.07), (x_to - 0.07, far, z_to - 0.07), "wood", DARK_WOOD)


def panel_screen(b: Builder, frame: Matrix, **options) -> None:
    """Freestanding timber partition run, 2.0 m: plinth, raised-panel dado, mid rail, glazed, lattice or panelled
    upper band, end posts and a moulded cornice. variant: glazed, lattice or solid."""
    variant = options.get("variant", "glazed")
    top = options.get("height", SCREEN_HEIGHT)
    wood = options.get("tint", DARK_WOOD)
    band_from, band_to = 1.12, top - 0.14
    band_middle = (band_from + band_to) / 2.0

    box(b, frame, (-1.0, -0.115, 0.0), (1.0, 0.115, 0.14), "wood", wood)
    box(b, frame, (-1.0, -0.12, 0.14), (1.0, 0.12, 0.17), "trim", PLASTER)
    screen_panels(b, frame, -0.94, 0.94, 0.17, 1.02, WOOD["mel"])
    box(b, frame, (-1.0, -0.115, 1.02), (1.0, 0.115, band_from), "wood", wood)
    box(b, frame, (-1.0, -0.125, band_from), (1.0, 0.125, band_from + 0.025), "trim", PLASTER)

    if variant == "solid":
        screen_panels(b, frame, -0.94, 0.94, band_from + 0.025, band_to, WOOD["mel"])
    elif variant == "lattice":
        for index in range(19):
            spindle_x = -0.9 + index * 0.1
            box(b, frame, (spindle_x - 0.015, -0.015, band_from + 0.025), (spindle_x + 0.015, 0.015, band_to), "wood", wood)

        box(b, frame, (-0.94, -0.05, band_middle - 0.02), (0.94, 0.05, band_middle + 0.02), "wood", wood)
    else:
        box(b, frame, (-0.94, -0.008, band_from + 0.025), (0.94, 0.008, band_to), "vitrine")

        for mullion_x in (-0.47, 0.0, 0.47):
            box(b, frame, (mullion_x - 0.02, -0.045, band_from + 0.025), (mullion_x + 0.02, 0.045, band_to), "wood", wood)

        box(b, frame, (-0.94, -0.045, band_middle - 0.015), (0.94, 0.045, band_middle + 0.015), "wood", wood)

    box(b, frame, (-0.94, -0.1, band_to), (0.94, 0.1, top - 0.1), "wood", wood)
    box(b, frame, (-1.0, -0.14, top - 0.1), (1.0, 0.14, top - 0.04), "wood", WOOD["mel"])
    box(b, frame, (-1.0, -0.12, top - 0.04), (1.0, 0.12, top), "trim", PLASTER)

    for side in (-1.0, 1.0):
        box(b, frame, (side * 0.97 - 0.04, -0.1, 0.0), (side * 0.97 + 0.04, 0.1, top - 0.1), "wood", wood)


def partition_doorway(b: Builder, frame: Matrix, **options) -> None:
    """Doorway between two screen runs (2.0 m slot, 1.5 m opening): posts, a corbelled lintel and a panelled or
    plastered arch header up to the screen height. variant: timber or arch."""
    style = options.get("variant", "timber")
    top = options.get("height", SCREEN_HEIGHT)
    wood = options.get("tint", DARK_WOOD)
    door_top = 2.25

    for side in (-1.0, 1.0):
        box(b, frame, (side * 0.875 - 0.125, -0.115, 0.0), (side * 0.875 + 0.125, 0.115, top - 0.1), "wood", wood)
        box(b, frame, (side * 0.875 - 0.14, -0.13, 0.0), (side * 0.875 + 0.14, 0.13, 0.14), "trim", PLASTER)

    box(b, frame, (-1.0, -0.14, top - 0.1), (1.0, 0.14, top - 0.04), "wood", WOOD["mel"])
    box(b, frame, (-1.0, -0.12, top - 0.04), (1.0, 0.12, top), "trim", PLASTER)

    if style == "arch":
        spring, rise = door_top - 0.25, 0.55
        arc = arch_outline(0.75, spring, rise)
        infill = [(-0.75, top - 0.1), *arc, (0.75, top - 0.1)]
        band = arch_outline(0.89, spring, rise + 0.14) + list(reversed(arc))

        b.prism(infill, -0.085, 0.085, "paint", srgb(options.get("plaster", PLASTER)), frame=frame)
        b.prism(band, -0.125, 0.125, "trim", srgb(PLASTER), frame=frame)
        gem(b, frame, (0.0, -0.13, spring + rise + 0.1), 0.06, "metal", GOLD, scale=(1.0, 0.4, 1.3))
        return

    box(b, frame, (-0.95, -0.13, door_top), (0.95, 0.13, door_top + 0.18), "wood", wood)
    box(b, frame, (-0.95, -0.14, door_top + 0.18), (0.95, 0.14, door_top + 0.21), "trim", PLASTER)
    screen_panels(b, frame, -0.75, 0.75, door_top + 0.21, top - 0.1, WOOD["mel"])

    for side in (-1.0, 1.0):
        corners = [(side * 0.75, -0.12, door_top - 0.3), (side * 0.75, 0.12, door_top - 0.3), (side * 0.75, -0.12, door_top), (side * 0.75, 0.12, door_top), (side * 0.5, -0.12, door_top), (side * 0.5, 0.12, door_top)]

        b.hull(corners, "wood", srgb(wood), frame=frame)


def wainscot(b: Builder, frame: Matrix, **options) -> None:
    """Wall dado 2.0 m x 1.1 m: skirting, raised panels between stiles, chair rail; its back sits on the wall."""
    wood = options.get("tint", WOOD["mel"])
    stile_x = (-1.0, -0.34, 0.34, 1.0)

    box(b, frame, (-1.0, -0.04, 0.0), (1.0, 0.08, 0.13), "wood", DARK_WOOD)
    box(b, frame, (-1.0, -0.03, 0.13), (1.0, 0.08, 0.16), "trim", PLASTER)
    box(b, frame, (-1.0, -0.01, 0.16), (1.0, 0.08, 0.96), "wood_light", wood)

    for x_from, x_to in zip(stile_x, stile_x[1:]):
        box(b, frame, (x_from + 0.06, -0.03, 0.26), (x_to - 0.06, -0.01, 0.86), "wood", DARK_WOOD)
        box(b, frame, (x_from + 0.1, -0.035, 0.3), (x_to - 0.1, -0.03, 0.82), "wood_light", wood)

    box(b, frame, (-1.0, -0.04, 0.96), (1.0, 0.08, 1.04), "wood", DARK_WOOD)
    box(b, frame, (-1.0, -0.055, 1.04), (1.0, 0.08, 1.1), "wood_light", WOOD["mel"])


def stock_bay(b: Builder, frame: Matrix, boards: list, x_from: float, x_to: float, depth: float, clearance: float, generator: random.Random) -> None:
    """Books on every board of one bay (boards are the tops, the first row stands on the plinth at 0.08)."""
    for surface in (0.08, *boards[:-1]):
        book_row(b, frame, x_from, x_to, 0.0, surface, depth, clearance, generator)


def baluster_run(b: Builder, frame: Matrix, x_from: float, x_to: float, y: float, z: float, height: float, pitch: float, tone: str) -> None:
    """Rail with turned balusters from x_from to x_to at depth y, standing on z."""
    count = max(2, int(round((x_to - x_from) / pitch)))

    box(b, frame, (x_from, y - 0.045, z + height - 0.05), (x_to, y + 0.045, z + height), "wood_light", WOOD["mel"])
    box(b, frame, (x_from, y - 0.03, z + 0.08), (x_to, y + 0.03, z + 0.12), "wood", tone)

    for index in range(count + 1):
        baluster_x = x_from + (x_to - x_from) * index / count
        spin(b, frame, [(0.02, z + 0.12), (0.03, z + 0.3), (0.018, z + 0.5), (0.03, z + 0.7), (0.02, z + height - 0.05)], "wood", tone, sides=4, base=(baluster_x, y, 0.0))


def book_gallery(b: Builder, frame: Matrix, **options) -> None:
    """Two-tier library bay against a wall, 4.0 m: a lower bookcase, a deck on turned posts with corbels and a
    balustrade, and the upper bookcase behind it. open_end -1 or 1 leaves that end of the railing open for a stair."""
    generator = rng(options)
    wood = options.get("tint", DARK_WOOD)
    open_end = options.get("open_end", 0)
    wall_y = 0.65
    deck_z = 2.56
    rail_z = deck_z + 0.16
    lower = at(frame, (0.0, wall_y - 0.2, 0.0))
    upper = at(frame, (0.0, wall_y - 0.2, rail_z))
    lower_boards = shelf_unit(b, lower, 4.0, 0.4, deck_z - 0.01, [0.62, 1.2, 1.78, 2.36], wood, back=INDIGO, bays=2)
    upper_boards = shelf_unit(b, upper, 4.0, 0.4, 2.14, [0.5, 1.0, 1.5, 2.0], wood, back=INDIGO, crown=WOOD["mel"], bays=2)

    for x_from, x_to in ((-1.93, -0.04), (0.04, 1.93)):
        stock_bay(b, lower, lower_boards, x_from, x_to, 0.3, 0.46, generator)
        stock_bay(b, upper, upper_boards, x_from, x_to, 0.3, 0.4, generator)

    box(b, frame, (-2.06, -wall_y - 0.04, deck_z), (2.06, wall_y, rail_z), "wood_light", WOOD["mel"])
    box(b, frame, (-2.08, -wall_y - 0.07, deck_z - 0.1), (2.08, -wall_y, deck_z + 0.2), "wood", wood)
    box(b, frame, (-2.08, -wall_y - 0.075, deck_z + 0.1), (2.08, -wall_y - 0.03, deck_z + 0.14), "metal", BRASS)

    for post_x in (-1.8, 0.0, 1.8):
        spin(b, frame, [(0.1, 0.0), (0.1, 0.1), (0.06, 0.16), (0.07, 0.5), (0.05, 0.6), (0.05, 1.7), (0.08, 1.78), (0.06, 1.9), (0.06, 2.2), (0.1, 2.3), (0.1, deck_z - 0.1)], "wood", wood, sides=8, base=(post_x, -wall_y + 0.12, 0.0))

        for direction in (-1.0, 1.0):
            if abs(post_x + direction * 0.5) > 2.0:
                continue

            rod(b, frame, (post_x + direction * 0.07, -wall_y + 0.06, deck_z - 0.5), (post_x + direction * 0.5, -wall_y + 0.06, deck_z - 0.1), 0.05, "wood", wood, depth=0.07)

    baluster_run(b, frame, -1.93, 1.93, -wall_y + 0.06, rail_z, 0.94, 0.15, wood)

    for end in (-1.0, 1.0):
        if end != open_end:
            baluster_run(b, at(frame, (end * 1.97, 0.0, 0.0), 90.0), -wall_y + 0.06, wall_y - 0.06, 0.0, rail_z, 0.94, 0.15, wood)

    for newel_x in (-1.98, 1.98):
        box(b, frame, (newel_x - 0.05, -wall_y + 0.01, rail_z), (newel_x + 0.05, -wall_y + 0.11, rail_z + 1.0), "wood", wood)
        ball(b, frame, (newel_x, -wall_y + 0.06, rail_z + 1.07), 0.065, "metal", BRASS, segments=6)

    for lamp_x in (-1.0, 1.0):
        rod(b, frame, (lamp_x, wall_y - 0.45, rail_z + 1.5), (lamp_x, wall_y - 0.2, rail_z + 1.62), 0.02, "metal", BRASS)
        candle(b, frame, (lamp_x, wall_y - 0.45, rail_z + 1.5), 0.1)


def gallery_stair(b: Builder, frame: Matrix, **options) -> None:
    """Spiral stair of 13 wedge treads round a turned newel up to the gallery deck at 2.72 m, with a baluster
    rail and handrail on the outer edge. winding 1 climbs counter-clockwise (ends toward -X), -1 the mirror."""
    wood = options.get("tint", DARK_WOOD)
    winding = options.get("winding", 1)
    steps, deck = 13, 2.72
    rise = deck / steps
    half_turn = math.radians(10.8)
    posts = []

    spin(b, frame, [(0.12, 0.0), (0.12, 0.12), (0.08, 0.2), (0.08, deck - 0.15), (0.11, deck - 0.05), (0.11, deck + 0.05), (0.05, deck + 0.12)], "wood", wood, sides=8)

    for step in range(steps):
        angle = math.radians(-90.0) + winding * math.radians(20.8) * step
        edges = [angle - half_turn, angle + half_turn]
        top = (step + 1) * rise
        inner = [(0.09 * math.cos(edge), 0.09 * math.sin(edge)) for edge in edges]
        outer = [(0.86 * math.cos(edge), 0.86 * math.sin(edge)) for edge in edges]
        points = [(x, y, top) for x, y in inner + outer] + [(x, y, top - 0.07) for x, y in inner + outer]

        b.hull(points, *resolve("wood_light", WOOD["mel"])[:2], frame=frame)
        b.hull([(x, y, top - 0.07) for x, y in outer] + [(x * 0.96, y * 0.96, top - 0.2) for x, y in outer], *resolve("wood", wood)[:2], frame=frame)
        post = (0.82 * math.cos(angle), 0.82 * math.sin(angle))
        rod(b, frame, (*post, top), (*post, top + 0.9), 0.035, "wood", wood)
        posts.append((*post, top + 0.9))

    for start, end in zip(posts, posts[1:]):
        rod(b, frame, start, end, 0.05, "wood_light", WOOD["mel"], depth=0.05)

    ball(b, frame, posts[0], 0.05, "metal", BRASS, segments=6)
    ball(b, frame, posts[-1], 0.05, "metal", BRASS, segments=6)


# ---------- rugs and floor pieces ----------

def rug_build(b: Builder, frame: Matrix, width: float, length: float, variant: str) -> None:
    """Woven rug: fringe, field, double border, a corner motif and a stepped medallion with a star."""
    field, border, medallion, motif = RUG_PALETTES[variant]
    half_x, half_y = width / 2.0, length / 2.0
    inner_x, inner_y = half_x - 0.3, half_y - 0.3
    middle = min(inner_x, inner_y) * 0.62

    for sign in (-1.0, 1.0):
        box(b, frame, (-half_x, sign * (half_y + 0.001) + min(0.0, sign * 0.06), 0.0), (half_x, sign * (half_y + 0.001) + max(0.0, sign * 0.06), 0.004), "paint", motif)

    box(b, frame, (-half_x, -half_y, 0.0), (half_x, half_y, 0.008), "paint", border)
    box(b, frame, (-half_x + 0.07, -half_y + 0.07, 0.008), (half_x - 0.07, half_y - 0.07, 0.012), "paint", medallion)
    box(b, frame, (-half_x + 0.12, -half_y + 0.12, 0.012), (half_x - 0.12, half_y - 0.12, 0.016), "paint", field)
    box(b, frame, (-inner_x, -inner_y, 0.016), (inner_x, inner_y, 0.02), "paint", border)
    box(b, frame, (-inner_x + 0.04, -inner_y + 0.04, 0.02), (inner_x - 0.04, inner_y - 0.04, 0.024), "paint", field)

    for sign_x, sign_y in itertools.product((-1.0, 1.0), repeat=2):
        corner = [(sign_x * inner_x, sign_y * inner_y, 0.024), (sign_x * (inner_x - 0.5), sign_y * inner_y, 0.024), (sign_x * inner_x, sign_y * (inner_y - 0.5), 0.024)]

        b.hull(corner + [(x, y, 0.028) for x, y, _ in corner], *resolve("paint", motif)[:2], frame=frame)

    for scale, color, lift in ((1.0, medallion, 0.024), (0.78, motif, 0.028), (0.56, border, 0.032), (0.36, medallion, 0.036)):
        radius = middle * scale
        diamond = [(radius * 1.5 * x_sign * (axis == 0), radius * y_sign * (axis == 1), lift) for axis, x_sign, y_sign in ((0, 1, 0), (0, -1, 0), (1, 0, 1), (1, 0, -1))]

        b.hull(diamond + [(x, y, lift + 0.004) for x, y, _ in diamond], *resolve("paint", color)[:2], frame=frame)


def rug_ornate(b: Builder, frame: Matrix, **options) -> None:
    rug_build(b, frame, 3.0, 2.0, options.get("variant", "red"))


def rug_runner(b: Builder, frame: Matrix, **options) -> None:
    rug_build(b, frame, 1.2, 4.0, options.get("variant", "red"))


# ---------- library, school and seminary pieces ----------

PAPER_WHITE = "F7F2E6"
CHALK_COLORS = ("F7F2E6", "F2C86B", "8FD8F2", "F59AD8")
SLATE = "2F4F4A"
VELVET = "8E2F45"


def screen_post(b: Builder, frame: Matrix, **options) -> None:
    """Square corner post for screen runs: stone foot, chamfered shaft and a capped head."""
    height = options.get("height", SCREEN_HEIGHT)
    wood = options.get("tint", DARK_WOOD)

    box(b, frame, (-0.14, -0.14, 0.0), (0.14, 0.14, 0.14), "trim", PLASTER)
    box(b, frame, (-0.11, -0.11, 0.14), (0.11, 0.11, height - 0.1), "wood", wood)
    box(b, frame, (-0.14, -0.14, height - 0.1), (0.14, 0.14, height - 0.04), "wood", WOOD["mel"])
    box(b, frame, (-0.12, -0.12, height - 0.04), (0.12, 0.12, height), "trim", PLASTER)


def study_chair(b: Builder, frame: Matrix, **options) -> None:
    """Library chair: turned legs with a stretcher ring, padded seat, a back with splats and a carved top rail."""
    wood = options.get("tint", DARK_WOOD)
    cushion = options.get("cushion", VELVET)

    for leg_x, leg_y in itertools.product((-0.19, 0.19), repeat=2):
        profile = [(0.025, 0.0), (0.03, 0.06), (0.02, 0.2), (0.03, 0.28), (0.025, 0.45)]

        spin(b, frame, profile, "wood", wood, sides=6, base=(leg_x, leg_y, 0.0))

    for rail_y in (-0.19, 0.19):
        rod(b, frame, (-0.19, rail_y, 0.17), (0.19, rail_y, 0.17), 0.025, "wood", wood)

    for rail_x in (-0.19, 0.19):
        rod(b, frame, (rail_x, -0.19, 0.17), (rail_x, 0.19, 0.17), 0.025, "wood", wood)

    box(b, frame, (-0.23, -0.23, 0.43), (0.23, 0.23, 0.46), "wood", wood)
    box(b, frame, (-0.21, -0.21, 0.46), (0.21, 0.21, 0.51), "paint", cushion)
    box(b, frame, (-0.19, -0.19, 0.51), (0.19, 0.19, 0.525), "paint", options.get("trim", "E8B64A"))

    for post_x in (-0.19, 0.19):
        spin(b, frame, [(0.025, 0.46), (0.03, 0.7), (0.025, 0.88), (0.035, 0.9)], "wood", wood, sides=6, base=(post_x, 0.2, 0.0))

    for splat_x in (-0.07, 0.07):
        box(b, frame, (splat_x - 0.018, 0.19, 0.52), (splat_x + 0.018, 0.21, 0.82), "wood", wood)

    box(b, frame, (-0.2, 0.18, 0.78), (0.2, 0.22, 0.84), "wood_light", WOOD["mel"])
    b.hull([(-0.21, 0.18, 0.84), (0.21, 0.18, 0.84), (-0.21, 0.22, 0.84), (0.21, 0.22, 0.84), (0.0, 0.18, 0.93), (0.0, 0.22, 0.93)], *resolve("wood", wood)[:2], frame=frame)


def card_catalog(b: Builder, frame: Matrix, **options) -> None:
    """Card catalogue: a moulded cabinet of 4 x 5 labelled drawers with brass pulls, a banker's lamp, an open
    index book and a stack of cards on top."""
    wood = options.get("tint", DARK_WOOD)
    columns, rows = 4, 5
    drawer_width, drawer_height = 1.28 / columns, 0.85 / rows

    box(b, frame, (-0.68, -0.28, 0.0), (0.68, 0.28, 0.1), "wood", wood)
    box(b, frame, (-0.66, -0.26, 0.1), (0.66, 0.26, 1.02), "wood_light", WOOD["media"])
    box(b, frame, (-0.72, -0.3, 1.02), (0.72, 0.3, 1.07), "wood_light", WOOD["mel"])
    box(b, frame, (-0.7, -0.285, 1.0), (0.7, -0.26, 1.02), "wood", wood)

    for column, row in itertools.product(range(columns), range(rows)):
        x = -0.64 + (column + 0.5) * drawer_width
        z = 0.13 + (row + 0.5) * drawer_height

        box(b, frame, (x - drawer_width / 2.0 + 0.012, -0.275, z - drawer_height / 2.0 + 0.012), (x + drawer_width / 2.0 - 0.012, -0.26, z + drawer_height / 2.0 - 0.012), "wood", WOOD["mel"])
        box(b, frame, (x - 0.04, -0.286, z + 0.02), (x + 0.04, -0.275, z + 0.045), "paint", PAPER_WHITE)
        box(b, frame, (x - 0.03, -0.295, z - 0.035), (x + 0.03, -0.275, z - 0.025), "metal", BRASS)

    spin(b, frame, [(0.07, 1.07), (0.05, 1.1), (0.025, 1.15), (0.03, 1.26)], "metal", BRASS, sides=8, base=(-0.45, 0.0, 0.0))
    box(b, frame, (-0.62, -0.1, 1.27), (-0.28, 0.1, 1.32), "paint", "2F7A4F")
    box(b, frame, (-0.62, -0.1, 1.255), (-0.28, 0.1, 1.27), "metal", BRASS)
    floating_book(b, at(frame, (0.1, 0.0, 1.095), 8.0), "28356E", True)

    for layer in range(5):
        box(b, at(frame, (0.5, 0.05, 1.07 + layer * 0.012), 3.0 * layer), (-0.07, -0.05, 0.0), (0.07, 0.05, 0.011), "paint", PAPER_WHITE)


def school_desk(b: Builder, frame: Matrix, **options) -> None:
    """Two-seat pupils' desk, 1.5 m: sloped lid with ink wells and a groove, a book shelf underneath, timber
    A-frame ends and a plank bench behind (pupils look toward -Y)."""
    wood = options.get("tint", WOOD["media"])
    generator = rng(options)

    for end in (-1.0, 1.0):
        x = end * 0.68
        box(b, frame, (x - 0.025, -0.44, 0.0), (x + 0.025, -0.34, 0.74), "wood", wood)
        box(b, frame, (x - 0.025, -0.06, 0.0), (x + 0.025, 0.04, 0.6), "wood", wood)
        box(b, frame, (x - 0.025, 0.2, 0.0), (x + 0.025, 0.4, 0.06), "wood", wood)
        box(b, frame, (x - 0.025, 0.28, 0.06), (x + 0.025, 0.34, 0.42), "wood", wood)
        rod(b, frame, (x, -0.39, 0.12), (x, 0.0, 0.5), 0.04, "wood", wood, depth=0.04)

    lid = at(frame, (0.0, -0.2, 0.74), 11.0, "X")
    box(b, lid, (-0.74, -0.27, -0.025), (0.74, 0.27, 0.0), "wood_light", WOOD["mel"])
    box(b, lid, (-0.74, 0.26, 0.0), (0.74, 0.3, 0.035), "wood", wood)

    for well_x in (-0.38, 0.38):
        cyl(b, lid, (well_x, -0.1, 0.0), 0.035, 0.012, "metal", BRASS, sides=8)
        cyl(b, lid, (well_x, -0.1, 0.012), 0.022, 0.004, "paint", "23306B", sides=8)

    box(b, lid, (-0.68, -0.22, 0.0), (-0.52, -0.1, 0.012), "paint", generator.choice(BOOK_COLORS))
    box(b, lid, (0.1, -0.02, 0.0), (0.42, 0.2, 0.012), "paint", PAPER_WHITE)
    box(b, frame, (-0.7, -0.38, 0.32), (0.7, -0.04, 0.35), "wood_light", WOOD["mel"])
    box(b, frame, (-0.66, 0.18, 0.4), (0.66, 0.46, 0.44), "wood_light", WOOD["mel"])
    box(b, frame, (-0.66, 0.18, 0.4), (0.66, 0.22, 0.425), "wood", wood)


def teacher_desk(b: Builder, frame: Matrix, **options) -> None:
    """Master's desk, 2.0 m: two drawer pedestals, a leather-inlaid top with a raised book rest, a hand bell,
    a stack of exercise books, an inkwell with quill and a brass lamp."""
    wood = options.get("tint", DARK_WOOD)

    for side in (-1.0, 1.0):
        x = side * 0.78
        box(b, frame, (x - 0.2, -0.4, 0.0), (x + 0.2, 0.4, 0.08), "wood", wood)
        box(b, frame, (x - 0.18, -0.38, 0.08), (x + 0.18, 0.38, 0.72), "wood_light", WOOD["media"])

        for drawer in range(3):
            z = 0.12 + drawer * 0.2
            box(b, frame, (x - 0.16, -0.395, z), (x + 0.16, -0.38, z + 0.17), "wood", WOOD["mel"])
            box(b, frame, (x - 0.05, -0.41, z + 0.07), (x + 0.05, -0.395, z + 0.09), "metal", BRASS)

    box(b, frame, (-0.6, 0.2, 0.08), (0.6, 0.38, 0.72), "wood", wood)
    box(b, frame, (-1.0, -0.44, 0.72), (1.0, 0.44, 0.78), "wood_light", WOOD["mel"])
    box(b, frame, (-1.02, -0.46, 0.78), (1.02, 0.46, 0.8), "wood", wood)
    box(b, frame, (-0.9, -0.34, 0.8), (0.9, 0.34, 0.805), "paint", "2F7A4F")
    box(b, frame, (-0.9, -0.34, 0.8), (-0.88, 0.34, 0.812), "metal", GOLD)
    box(b, frame, (0.88, -0.34, 0.8), (0.9, 0.34, 0.812), "metal", GOLD)

    rest = at(frame, (-0.35, 0.1, 0.805), 22.0, "X")
    box(b, rest, (-0.24, -0.16, 0.0), (0.24, 0.16, 0.025), "wood", wood)
    floating_book(b, at(rest, (0.0, 0.0, 0.05), 0.0), "28356E", True)

    spin(b, frame, [(0.04, 0.805), (0.045, 0.83), (0.02, 0.9), (0.015, 0.93), (0.045, 0.99)], "metal", BRASS, sides=8, base=(0.5, 0.15, 0.0))

    for layer in range(4):
        box(b, at(frame, (0.15, 0.1, 0.805 + layer * 0.04), 7.0 * layer), (-0.14, -0.1, 0.0), (0.14, 0.1, 0.038), "paint", BOOK_COLORS[layer * 2])

    cyl(b, frame, (0.62, -0.15, 0.805), 0.035, 0.05, "paint", NAVY, sides=6)
    rod(b, frame, (0.62, -0.15, 0.85), (0.7, -0.08, 1.08), 0.01, "paint", PAPER_WHITE, depth=0.03)
    spin(b, frame, [(0.04, 0.805), (0.035, 0.84), (0.015, 0.86)], "metal", BRASS, sides=8, base=(-0.8, -0.2, 0.0))


def blackboard_big(b: Builder, frame: Matrix, **options) -> None:
    """Classroom board 3.2 m wide hung at 0.9 m: wooden frame with a gabled crown, slate panel with chalk
    diagrams and writing, a ledge with chalk and a felt rubber."""
    generator = rng(options)
    wood = options.get("tint", DARK_WOOD)
    bottom, top = 0.9, 2.6

    box(b, frame, (-1.6, 0.0, bottom - 0.12), (1.6, 0.08, top + 0.1), "wood", wood)
    box(b, frame, (-1.5, -0.01, bottom), (1.5, 0.0, top), "paint", options.get("slate", SLATE))
    box(b, frame, (-1.62, -0.07, bottom - 0.14), (1.62, 0.04, bottom - 0.06), "wood_light", WOOD["mel"])
    box(b, frame, (-1.65, -0.02, top + 0.1), (1.65, 0.1, top + 0.17), "wood_light", WOOD["mel"])
    b.hull([(-0.5, -0.02, top + 0.17), (0.5, -0.02, top + 0.17), (-0.5, 0.1, top + 0.17), (0.5, 0.1, top + 0.17), (0.0, 0.0, top + 0.34), (0.0, 0.1, top + 0.34)], *resolve("wood", wood)[:2], frame=frame)

    for chalk_ring, (x, z, radius) in enumerate(((-0.9, 1.9, 0.32), (-0.9, 1.9, 0.18))):
        cyl(b, frame, (x, -0.011, z), radius, 0.004, "paint", CHALK_COLORS[chalk_ring], sides=14, axis="Y", top=radius)

    cyl(b, frame, (-0.9, -0.016, 1.9), 0.15, 0.004, "paint", SLATE, sides=14, axis="Y")
    rod(b, frame, (-1.3, -0.012, 1.55), (-0.4, -0.012, 2.25), 0.012, "paint", CHALK_COLORS[1], depth=0.004)

    for line in range(5):
        x_from = 0.1 + generator.uniform(0.0, 0.2)
        x_to = x_from + generator.uniform(0.6, 1.2)
        rod(b, frame, (x_from, -0.012, 2.3 - line * 0.22), (x_to, -0.012, 2.3 - line * 0.22), 0.016, "paint", CHALK_COLORS[line % 2], depth=0.004)

    for chalk in range(3):
        cyl(b, frame, (-0.6 + chalk * 0.07, -0.05, bottom - 0.06), 0.012, 0.09, "paint", CHALK_COLORS[chalk], sides=5, axis="X")

    box(b, frame, (0.9, -0.06, bottom - 0.06), (1.1, -0.02, bottom - 0.02), "paint", "8E2F45")
    box(b, frame, (0.9, -0.06, bottom - 0.02), (1.1, -0.02, bottom + 0.01), "paint", "F2E6CF")


def coat_rack_wall(b: Builder, frame: Matrix, **options) -> None:
    """Wall board 2.0 m with eight pegs: cloaks, a satchel, caps and a scarf hang from them, a hat shelf above."""
    wood = options.get("tint", DARK_WOOD)
    cloaks = ("2F4FA3", "B5333F", "2F7A4F", "7A3F8E")

    box(b, frame, (-1.0, 0.0, 1.35), (1.0, 0.07, 1.85), "wood_light", WOOD["media"])
    box(b, frame, (-1.04, -0.02, 1.85), (1.04, 0.1, 1.9), "wood", wood)
    box(b, frame, (-1.04, -0.12, 1.9), (1.04, 0.1, 1.94), "wood_light", WOOD["mel"])
    box(b, frame, (-1.0, -0.02, 1.32), (1.0, 0.07, 1.36), "wood", wood)

    for peg in range(8):
        x = -0.875 + peg * 0.25

        rod(b, frame, (x, 0.0, 1.5), (x, -0.16, 1.54), 0.03, "wood", wood)
        ball(b, frame, (x, -0.17, 1.54), 0.032, "wood_light", WOOD["mel"], segments=6)

        if peg % 2 == 0:
            cloak = cloaks[(peg // 2) % len(cloaks)]
            b.hull([(x - 0.08, -0.12, 1.5), (x + 0.08, -0.12, 1.5), (x - 0.12, -0.15, 0.7), (x + 0.12, -0.15, 0.7), (x - 0.1, -0.02, 1.48), (x + 0.1, -0.02, 1.48), (x - 0.13, -0.05, 0.7), (x + 0.13, -0.05, 0.7)], "paint", srgb(cloak), frame=frame)
            ball(b, frame, (x, -0.13, 1.52), 0.035, "metal", BRASS, segments=6)

    box(b, frame, (0.38, -0.22, 0.95), (0.62, -0.14, 1.2), "paint", "C08A55")
    box(b, frame, (0.4, -0.24, 1.1), (0.6, -0.2, 1.22), "paint", "8B5A3C")

    for cap_x, color in ((-0.7, "B5333F"), (-0.25, "2F4FA3"), (0.4, "E8B64A")):
        ball(b, frame, (cap_x, -0.05, 1.99), 0.1, "paint", color, scale=(1.3, 1.0, 0.7), segments=6)


def easel(b: Builder, frame: Matrix, **options) -> None:
    """Painter's easel: A-frame with a rear leg, a canvas with a small landscape and a paint tray with a palette."""
    wood = options.get("tint", WOOD["mel"])
    sky, hill, sun = "8FC8F2", "7FC46A", "F2C86B"

    for leg_x in (-0.3, 0.3):
        rod(b, frame, (leg_x, -0.2, 0.0), (leg_x * 0.5, 0.0, 1.75), 0.05, "wood_light", wood, depth=0.04)

    rod(b, frame, (0.0, 0.5, 0.0), (0.0, 0.08, 1.45), 0.045, "wood_light", wood, depth=0.04)
    box(b, frame, (-0.42, -0.25, 0.55), (0.42, -0.19, 0.6), "wood", wood)
    box(b, frame, (-0.42, -0.26, 0.6), (0.42, -0.18, 0.62), "wood_light", WOOD["media"])
    canvas = at(frame, (0.0, -0.22, 0.0), -6.0, "X")
    box(b, canvas, (-0.37, 0.0, 0.62), (0.37, 0.025, 1.4), "paint", PAPER_WHITE)
    box(b, canvas, (-0.34, -0.003, 0.7), (0.34, 0.0, 1.37), "paint", sky)
    b.hull([(-0.34, -0.004, 0.7), (0.34, -0.004, 0.7), (-0.34, -0.004, 0.95), (0.34, -0.004, 1.0), (0.0, -0.004, 1.12)], "paint", srgb(hill), frame=canvas)
    cyl(b, canvas, (0.2, -0.004, 1.2), 0.07, 0.003, "paint", sun, sides=10, axis="Y", top=0.07)
    box(b, canvas, (0.36, -0.01, 0.7), (0.38, 0.0, 1.37), "wood", wood)
    box(b, frame, (-0.2, -0.38, 0.62), (0.2, -0.26, 0.64), "wood_light", WOOD["media"])

    for dab, color in enumerate(("B5333F", "F2C86B", "2F4FA3", "2F7A4F")):
        ball(b, frame, (-0.14 + dab * 0.09, -0.32, 0.66), 0.03, "paint", color, scale=(1.0, 1.0, 0.5), segments=6)


def lab_bench(b: Builder, frame: Matrix, **options) -> None:
    """Teaching lab bench, 2.2 m: stone top on a timber frame with a lower shelf, a spirit burner with a
    flask on a tripod, a brass microscope, a rack of test tubes and a few beakers."""
    wood = options.get("tint", DARK_WOOD)

    for leg_x, leg_y in itertools.product((-1.0, 1.0), (-0.34, 0.34)):
        spin(b, frame, [(0.05, 0.0), (0.05, 0.08), (0.035, 0.14), (0.035, 0.7), (0.05, 0.78), (0.05, 0.9)], "wood", wood, sides=6, base=(leg_x, leg_y, 0.0))

    box(b, frame, (-1.05, -0.38, 0.14), (1.05, 0.38, 0.18), "wood_light", WOOD["mel"])
    box(b, frame, (-1.05, -0.4, 0.76), (1.05, 0.4, 0.86), "wood", wood)
    box(b, frame, (-1.12, -0.46, 0.86), (1.12, 0.46, 0.92), "stone", STONE["clara"])
    box(b, frame, (-1.12, -0.46, 0.86), (1.12, -0.44, 0.94), "trim", PLASTER)
    box(b, frame, (-0.95, -0.4, 0.35), (-0.1, 0.38, 0.7), "paint", "4F3A66")
    box(b, frame, (0.1, 0.1, 0.18), (0.9, 0.34, 0.45), "wood", WOOD["media"])

    for tripod_leg in range(3):
        angle = math.radians(90.0 + 120.0 * tripod_leg)
        rod(b, frame, (-0.6 + 0.1 * math.cos(angle), 0.1 * math.sin(angle), 0.92), (-0.6, 0.0, 1.1), 0.012, "metal", DARK_IRON)

    hoop(b, frame, (-0.6, 0.0, 1.1), 0.08, 0.008, "metal", DARK_IRON, sides=10, tube_sides=3)
    spin(b, frame, [(0.03, 0.92), (0.04, 0.96), (0.03, 0.99)], "metal", BRASS, sides=8, base=(-0.6, 0.0, 0.0))
    gem(b, frame, (-0.6, 0.0, 1.0), 0.02, "glow_amber", scale=(0.8, 0.8, 1.8))
    flask(b, frame, (-0.6, 0.0, 1.12), 0.07, 0.22, "vitrine", None, shape="round", cork=True)
    cyl(b, frame, (-0.6, 0.0, 1.14), 0.052, 0.07, "glow_green", sides=8)

    cyl(b, frame, (0.35, -0.1, 0.92), 0.09, 0.02, "metal", BRASS, sides=8)
    rod(b, frame, (0.35, -0.1, 0.94), (0.35, -0.02, 1.1), 0.03, "metal", BRASS)
    cyl(b, at(frame, (0.35, -0.1, 1.04), 25.0, "X"), (0.0, 0.0, 0.0), 0.025, 0.2, "metal", BRASS, sides=8)
    cyl(b, frame, (0.35, -0.16, 0.92), 0.05, 0.1, "metal", BRASS, sides=8)

    box(b, frame, (0.6, 0.1, 0.92), (0.95, 0.24, 0.94), "wood", wood)

    for tube in range(5):
        flask(b, frame, (0.65 + tube * 0.06, 0.17, 0.94), 0.02, 0.2, "vitrine", None, shape="cone")

    for beaker, color in enumerate(("glow_cyan", "glow_pink", "glow_amber")):
        cyl(b, frame, (0.55 + beaker * 0.16, -0.25, 0.92), 0.045, 0.1, "vitrine", sides=8)
        cyl(b, frame, (0.55 + beaker * 0.16, -0.25, 0.925), 0.04, 0.05, color, sides=8)


def planet_mobile(b: Builder, frame: Matrix, **options) -> None:
    """Ceiling prop: a brass orrery mobile of six painted planets on arms round a glowing gold sun, hung on a chain."""
    arms = ((0.28, -1.05, 0.06, "C9483B"), (0.45, -0.95, 0.09, "4F8FC9"), (0.62, -1.1, 0.07, "7FC46A"), (0.52, -1.25, 0.1, "F2B13C"), (0.38, -1.2, 0.05, "B57FE0"), (0.68, -1.3, 0.08, "5FD9C0"))

    cyl(b, frame, (0.0, 0.0, -0.04), 0.05, 0.04, "metal", BRASS, sides=8)
    rod(b, frame, (0.0, 0.0, -0.04), (0.0, 0.0, -0.9), 0.012, "metal", BRASS)
    ball(b, frame, (0.0, 0.0, -1.0), 0.12, "glow_warm", segments=8)

    for index, (reach, drop, radius, color) in enumerate(arms):
        angle = math.radians(index * 60.0 + 15.0)
        tip = (reach * math.cos(angle), reach * math.sin(angle), drop)

        flat_ring(b, frame, reach, 0.012, "metal", GOLD, sides=24, z=drop + 0.0)
        rod(b, frame, (0.0, 0.0, -0.9), tip, 0.008, "metal", BRASS)
        ball(b, frame, tip, radius, "paint", color, segments=8)

    hoop(b, frame, (0.0, 0.0, -1.0), 0.22, 0.008, "metal", GOLD, sides=16, tube_sides=3, axis="Y")


def school_bell(b: Builder, frame: Matrix, **options) -> None:
    """Ceiling prop: a brass hand bell on an iron bracket with a long knotted pull rope."""
    spin(b, frame, [(0.03, -0.2), (0.05, -0.26), (0.11, -0.4), (0.2, -0.6), (0.23, -0.66), (0.2, -0.66), (0.01, -0.6)], "metal", BRASS, sides=10)
    box(b, frame, (-0.2, -0.04, -0.2), (0.2, 0.04, -0.14), "metal", DARK_IRON)

    for side in (-1.0, 1.0):
        box(b, frame, (side * 0.17 - 0.015, -0.04, -0.18), (side * 0.17 + 0.015, 0.04, -0.06), "metal", DARK_IRON)

    ball(b, frame, (0.0, 0.0, -0.64), 0.05, "metal", DARK_IRON, segments=6)
    rod(b, frame, (0.0, 0.0, -0.66), (0.0, 0.0, -1.9), 0.012, "paint", "C9A26B")

    for knot in (-1.2, -1.55, -1.9):
        ball(b, frame, (0.0, 0.0, knot), 0.03, "paint", "C9A26B", segments=6)

    cyl(b, frame, (0.0, 0.0, -2.05), 0.018, 0.16, "paint", "B5333F", sides=6, top=0.04)


def pew(b: Builder, frame: Matrix, **options) -> None:
    """Chapel pew, 2.4 m: carved poppy-head ends with an arched cut-out, seat, a tall panelled back, a hymn-book
    ledge and a padded kneeler on the front foot (sitters face -Y; the pew behind has its back at +Y)."""
    wood = options.get("tint", WOOD["media"])
    cushion = options.get("cushion", "7A1F33")

    for end in (-1.0, 1.0):
        x = end * 1.16
        outline = [(-0.4, 0.0), (0.4, 0.0), (0.4, 0.75), (0.33, 0.95), (0.0, 1.05), (-0.33, 0.95), (-0.4, 0.75)]

        b.side_prism(outline, x - 0.04, x + 0.04, "wood", srgb(wood), frame=frame)
        ball(b, frame, (x, 0.0, 1.07), 0.05, "wood_light", WOOD["mel"], segments=6)
        box(b, frame, (x - 0.05, -0.4, 0.0), (x + 0.05, 0.4, 0.06), "wood", DARK_WOOD)

    box(b, frame, (-1.12, -0.18, 0.43), (1.12, 0.22, 0.47), "wood_light", WOOD["mel"])
    box(b, frame, (-1.12, 0.2, 0.47), (1.12, 0.26, 0.98), "wood_light", WOOD["media"])
    box(b, frame, (-1.12, 0.17, 0.95), (1.12, 0.29, 1.0), "wood", DARK_WOOD)
    box(b, frame, (-1.12, 0.2, 0.27), (1.12, 0.26, 0.3), "wood", DARK_WOOD)

    for panel in range(6):
        x = -0.93 + panel * 0.372
        box(b, frame, (x - 0.14, 0.185, 0.58), (x + 0.14, 0.2, 0.9), "wood", DARK_WOOD)

    box(b, frame, (-1.1, -0.34, 0.25), (1.1, -0.1, 0.29), "wood", DARK_WOOD)
    box(b, frame, (-1.06, -0.32, 0.29), (1.06, -0.12, 0.34), "paint", cushion)
    box(b, frame, (-1.1, -0.2, 0.7), (1.1, -0.14, 0.73), "wood", DARK_WOOD)

    for book_index in range(3):
        box(b, frame, (-0.6 + book_index * 0.9, -0.2, 0.73), (-0.45 + book_index * 0.9, -0.14, 0.77), "paint", BOOK_COLORS[book_index])


def candle_stand(b: Builder, frame: Matrix, **options) -> None:
    """Tall wrought-iron floor candelabrum: three-footed base, twisted-look stem and five candles on drip pans."""
    iron = options.get("tint", DARK_IRON)

    for foot in range(3):
        angle = math.radians(90.0 + 120.0 * foot)
        rod(b, frame, (0.0, 0.0, 0.2), (0.22 * math.cos(angle), 0.22 * math.sin(angle), 0.02), 0.03, "metal", iron)

    spin(b, frame, [(0.04, 0.2), (0.05, 0.4), (0.03, 0.6), (0.05, 0.8), (0.03, 1.0), (0.05, 1.2), (0.03, 1.4), (0.06, 1.5)], "metal", iron, sides=6)

    for arm in range(5):
        angle = math.radians(arm * 72.0)
        tip = (0.2 * math.cos(angle), 0.2 * math.sin(angle), 1.56 + 0.05 * (arm % 2))

        rod(b, frame, (0.0, 0.0, 1.5), tip, 0.02, "metal", iron)
        cyl(b, frame, (tip[0], tip[1], tip[2]), 0.045, 0.02, "metal", BRASS, sides=8)
        candle(b, frame, (tip[0], tip[1], tip[2] + 0.02), 0.16 + 0.03 * (arm % 3))


def chancel_altar(b: Builder, frame: Matrix, **options) -> None:
    """Chapel altar against the wall, 3.6 m: a stone table with arcaded front, a gold-fringed linen cloth, a
    chalice, a missal and candlesticks, backed by a tall arched reredos with a rose and a gilded cross."""
    stone = options.get("tint", STONE["clara"])
    gold = GOLD

    box(b, frame, (-1.7, -0.62, 0.0), (1.7, -0.3, 0.07), "stone", STONE["media"])
    box(b, frame, (-1.6, -0.34, 0.07), (1.6, 0.3, 0.92), "stone", stone)
    box(b, frame, (-1.66, -0.4, 0.92), (1.66, 0.34, 1.0), "stone", STONE["clara"])

    for arcade in range(5):
        x = -1.28 + arcade * 0.64
        arch_points = arch_outline(0.24, 0.52, 0.2)
        b.prism([(x - 0.24, 0.16), *[(x + px, pz) for px, pz in arch_points], (x + 0.24, 0.16)], -0.37, -0.33, "paint", srgb("C9B6D9"), frame=frame)

    box(b, frame, (-1.3, -0.5, 1.0), (1.3, 0.3, 1.012), "paint", PAPER_WHITE)
    box(b, frame, (-1.3, -0.5, 0.78), (1.3, -0.48, 1.0), "paint", PAPER_WHITE)
    box(b, frame, (-1.3, -0.505, 0.78), (1.3, -0.495, 0.84), "metal", gold)

    outline = [(-1.5, 0.0), (1.5, 0.0), (1.5, 2.45), (0.75, 3.05), (0.0, 3.2), (-0.75, 3.05), (-1.5, 2.45)]
    box(b, frame, (-1.6, 0.34, 0.0), (1.6, 0.62, 1.0), "stone", stone)
    b.prism(outline, 0.4, 0.62, "paint", srgb("E9D9F2"), frame=frame)
    b.prism([(-1.2, 1.1), (1.2, 1.1), (1.2, 2.35), (0.6, 2.8), (0.0, 2.92), (-0.6, 2.8), (-1.2, 2.35)], 0.38, 0.4, "paint", srgb(WINE), frame=frame)

    for start, end in zip(outline, outline[1:] + outline[:1]):
        if start[1] > 0.0 or end[1] > 0.0:
            rod(b, frame, (start[0], 0.385, start[1]), (end[0], 0.385, end[1]), 0.07, "metal", gold, depth=0.03)

    cyl(b, frame, (0.0, 0.376, 2.2), 0.3, 0.012, "glow_warm", sides=12, axis="Y", top=0.3)
    cyl(b, frame, (0.0, 0.372, 2.2), 0.25, 0.012, "paint", WINE, sides=12, axis="Y", top=0.25)

    for ray in range(6):
        angle = math.radians(ray * 30.0)
        rod(b, frame, (0.0, 0.36, 2.2), (0.27 * math.cos(angle), 0.36, 2.2 + 0.27 * math.sin(angle)), 0.025, "metal", gold, depth=0.012)

    box(b, frame, (-0.04, 0.37, 2.52), (0.04, 0.395, 2.9), "metal", gold)
    box(b, frame, (-0.2, 0.37, 2.72), (0.2, 0.395, 2.78), "metal", gold)

    spin(b, frame, [(0.05, 1.012), (0.03, 1.04), (0.02, 1.1), (0.05, 1.15), (0.07, 1.25), (0.05, 1.28)], "metal", gold, sides=8, base=(0.0, -0.05, 0.0))
    floating_book(b, at(frame, (-0.55, -0.1, 1.04), 10.0), "7A1F33", True)

    for candle_x in (-1.2, -0.9, 0.9, 1.2):
        spin(b, frame, [(0.07, 1.012), (0.03, 1.05), (0.03, 1.2), (0.05, 1.23)], "metal", gold, sides=8, base=(candle_x, -0.05, 0.0))
        candle(b, frame, (candle_x, -0.05, 1.23), 0.3)


def reading_pulpit(b: Builder, frame: Matrix, **options) -> None:
    """Refectory reader's pulpit: an octagonal panelled drum on a stone plinth with a few steps, a slanted book
    rest with a bound book and a brass lamp arm."""
    wood = options.get("tint", WOOD["media"])

    box(b, frame, (-0.5, -0.5, 0.0), (0.5, 0.5, 0.1), "stone", STONE["media"])
    box(b, frame, (-0.4, -0.5, 0.1), (0.4, -0.3, 0.2), "stone", STONE["clara"])
    spin(b, frame, [(0.34, 0.2), (0.4, 0.25), (0.4, 1.0), (0.46, 1.06), (0.5, 1.12), (0.5, 1.2)], "wood", wood, sides=8, base=(0.0, 0.1, 0.0))

    for panel in range(8):
        angle = math.radians(22.5 + panel * 45.0)
        box(b, at(frame, (0.4 * math.cos(angle), 0.1 + 0.4 * math.sin(angle), 0.0), math.degrees(angle) - 90.0), (-0.12, -0.035, 0.38), (0.12, 0.0, 0.92), "wood_light", WOOD["mel"])

    rest = at(frame, (0.0, 0.1, 1.2), 25.0, "X")
    box(b, rest, (-0.3, -0.22, 0.0), (0.3, 0.22, 0.03), "wood", DARK_WOOD)
    floating_book(b, at(rest, (0.0, 0.0, 0.07), 0.0), "6A2E6E", True)
    rod(b, frame, (0.4, 0.4, 1.2), (0.4, 0.4, 1.7), 0.03, "metal", BRASS)
    rod(b, frame, (0.4, 0.4, 1.68), (0.15, 0.2, 1.62), 0.02, "metal", BRASS)
    candle(b, frame, (0.15, 0.2, 1.62), 0.1)


def refectory_table(b: Builder, frame: Matrix, **options) -> None:
    """Long refectory table, 3.4 m, with a bench each side: trestle ends with a stretcher, a scrubbed top set with
    bowls, bread, jugs and candles."""
    wood = options.get("tint", WOOD["media"])
    generator = rng(options)

    for end in (-1.4, 1.4):
        box(b, frame, (end - 0.05, -0.38, 0.0), (end + 0.05, 0.38, 0.1), "wood", DARK_WOOD)
        box(b, frame, (end - 0.04, -0.36, 0.1), (end + 0.04, 0.36, 0.72), "wood", wood)
        b.hull([(end - 0.04, -0.36, 0.72), (end + 0.04, -0.36, 0.72), (end - 0.04, -0.1, 0.4), (end + 0.04, -0.1, 0.4)], *resolve("wood", wood)[:2], frame=frame)

    rod(b, frame, (-1.4, 0.0, 0.3), (1.4, 0.0, 0.3), 0.07, "wood", DARK_WOOD, depth=0.07)
    box(b, frame, (-1.7, -0.45, 0.72), (1.7, 0.45, 0.78), "wood_light", WOOD["mel"])
    box(b, frame, (-1.72, -0.47, 0.76), (1.72, 0.47, 0.8), "wood", DARK_WOOD)

    for side in (-1.0, 1.0):
        bench_y = side * 0.72

        box(b, frame, (-1.5, bench_y - 0.17, 0.42), (1.5, bench_y + 0.17, 0.46), "wood_light", WOOD["mel"])

        for leg_x in (-1.3, 1.3):
            box(b, frame, (leg_x - 0.04, bench_y - 0.15, 0.0), (leg_x + 0.04, bench_y + 0.15, 0.42), "wood", wood)

    for place in range(6):
        x = -1.35 + place * 0.54

        for side in (-1.0, 1.0):
            cyl(b, frame, (x, side * 0.25, 0.8), 0.1, 0.012, "paint", PAPER_WHITE, sides=10, top=0.12)
            cyl(b, frame, (x, side * 0.25, 0.812), 0.07, 0.035, "paint", "C9A26B", sides=8, top=0.09)

    for loaf_x in (-0.6, 0.4):
        b.sphere((loaf_x, 0.0, 0.84), 0.08, "paint", srgb("D9A05B"), scale=(1.4, 0.9, 0.6), frame=frame, segments=6)

    for jug_x in (-0.1, 0.9):
        spin(b, frame, [(0.04, 0.8), (0.07, 0.86), (0.07, 0.95), (0.04, 1.0), (0.05, 1.03)], "paint", "C9A26B", sides=8, base=(jug_x, generator.uniform(-0.1, 0.1), 0.0))

    for candle_x in (-1.0, 0.0, 1.0):
        candle(b, frame, (candle_x, 0.0, 0.8), 0.1 + generator.uniform(0.0, 0.1))


def cell_curtain(b: Builder, frame: Matrix, **options) -> None:
    """Dormitory curtain on a frame: two posts with a rail and a pleated linen curtain gathered to one side."""
    wood = options.get("tint", DARK_WOOD)
    cloth = options.get("cloth", "C9B6D9")
    pleats = 7

    for side in (-1.0, 1.0):
        box(b, frame, (side * 0.55 - 0.04, -0.05, 0.0), (side * 0.55 + 0.04, 0.05, 2.0), "wood", wood)
        ball(b, frame, (side * 0.55, 0.0, 2.04), 0.045, "metal", BRASS, segments=6)

    box(b, frame, (-0.55, -0.025, 1.92), (0.55, 0.025, 1.97), "wood", wood)

    for pleat in range(pleats):
        x = -0.5 + pleat * 0.09
        depth = 0.045 * (1 if pleat % 2 else -1)
        b.hull([(x - 0.03, depth, 1.92), (x + 0.03, depth, 1.92), (x - 0.04, -depth, 0.15), (x + 0.04, -depth, 0.15), (x - 0.03, 0.0, 1.92), (x + 0.03, 0.0, 1.92), (x - 0.04, 0.0, 0.15), (x + 0.04, 0.0, 0.15)], "paint", srgb(cloth), frame=frame)

    box(b, frame, (-0.04, -0.02, 1.9), (0.08, 0.02, 1.95), "metal", GOLD)


def censer_hanging(b: Builder, frame: Matrix, **options) -> None:
    """Ceiling prop: brass censer on three chains with an openwork bowl, a domed lid and a glowing ember."""
    for chain in range(3):
        angle = math.radians(chain * 120.0 + 30.0)

        rod(b, frame, (0.0, 0.0, 0.0), (0.09 * math.cos(angle), 0.09 * math.sin(angle), -1.1), 0.012, "metal", DARK_IRON)

    ball(b, frame, (0.0, 0.0, -0.05), 0.05, "metal", BRASS, segments=6)
    spin(b, frame, [(0.04, -1.2), (0.12, -1.28), (0.14, -1.4), (0.07, -1.5), (0.03, -1.52)], "metal", BRASS, sides=8)
    spin(b, frame, [(0.14, -1.4), (0.13, -1.28), (0.09, -1.2), (0.04, -1.12), (0.02, -1.08)], "metal", GOLD, sides=8)
    gem(b, frame, (0.0, 0.0, -1.34), 0.05, "glow_ember", scale=(1.0, 1.0, 0.8))
    hoop(b, frame, (0.0, 0.0, -1.4), 0.14, 0.012, "metal", GOLD, sides=10, tube_sides=3)


# ---------- magic and alchemy centrepieces ----------

def summoning_dais(b: Builder, frame: Matrix, **options) -> None:
    """Three-step round dais of lilac stone, 3.4 m: a gilded rim, glowing rune rings, an inlaid hexagram and
    eight rune stones set into the lowest step (walkable: it stays below 0.3 m)."""
    stone = options.get("tint", LILAC_STONE)

    spin(b, frame, [(1.7, 0.0), (1.7, 0.1), (1.5, 0.1), (1.5, 0.2), (1.3, 0.2), (1.3, 0.3)], "paint", stone, sides=16)
    flat_ring(b, frame, 1.62, 0.05, "metal", GOLD, sides=16, z=0.1)
    flat_ring(b, frame, 1.42, 0.04, "metal", GOLD, sides=16, z=0.2)
    flat_ring(b, frame, 1.15, 0.05, "glow_cyan", sides=24, z=0.3)
    flat_ring(b, frame, 0.55, 0.04, "glow_pink", sides=16, z=0.3)

    points = [(0.95 * math.cos(math.radians(90.0 + 60.0 * corner)), 0.95 * math.sin(math.radians(90.0 + 60.0 * corner))) for corner in range(6)]

    for corner in range(6):
        start, end = points[corner], points[(corner + 2) % 6]

        rod(b, frame, (*start, 0.305), (*end, 0.305), 0.035, "glow_cyan", depth=0.01)

    for stone_index in range(8):
        angle = math.radians(stone_index * 45.0 + 22.5)

        gem(b, frame, (1.6 * math.cos(angle), 1.6 * math.sin(angle), 0.12), 0.07, ("glow_pink", "glow_cyan")[stone_index % 2], scale=(1.0, 1.0, 0.7))


def orrery(b: Builder, frame: Matrix, **options) -> None:
    """Brass orrery on a carved plum-wood stand: a glowing gold sun, four tilted orbit rings with painted planets,
    an armillary hoop pair and a little moon on its own arm."""
    wood = options.get("tint", PLUM_WOOD)
    planets = ((0.28, 0.09, "C9483B", 0.0), (0.46, 0.1, "4F8FC9", 90.0), (0.64, 0.12, "7FC46A", 180.0), (0.8, 0.14, "F2B13C", 270.0))

    spin(b, frame, [(0.62, 0.0), (0.62, 0.06), (0.55, 0.1), (0.45, 0.16), (0.3, 0.24), (0.2, 0.34), (0.08, 0.44), (0.1, 0.7), (0.06, 0.8), (0.07, 1.0)], "wood", wood, sides=8)
    hoop(b, frame, (0.0, 0.0, 0.12), 0.58, 0.02, "metal", GOLD, sides=16, tube_sides=4)

    for leg in range(4):
        angle = math.radians(leg * 90.0 + 45.0)

        rod(b, frame, (0.18 * math.cos(angle), 0.18 * math.sin(angle), 0.9), (0.55 * math.cos(angle), 0.55 * math.sin(angle), 0.28), 0.04, "wood", wood)

    ball(b, frame, (0.0, 0.0, 1.2), 0.15, "glow_warm", segments=10)
    hoop(b, frame, (0.0, 0.0, 1.2), 0.2, 0.01, "metal", GOLD, sides=12, tube_sides=3, axis="X")

    for index, (radius, size, color, start) in enumerate(planets):
        orbit = at(frame, (0.0, 0.0, 1.2), 0.0)
        angle = math.radians(start)
        tilt = at(orbit, (0.0, 0.0, 0.0), 8.0 * (index - 1.5), "X")

        hoop(b, tilt, (0.0, 0.0, 0.0), radius, 0.008, "metal", BRASS, sides=24, tube_sides=3)
        rod(b, tilt, (0.0, 0.0, 0.0), (radius * math.cos(angle), radius * math.sin(angle), 0.0), 0.012, "metal", BRASS)
        ball(b, tilt, (radius * math.cos(angle), radius * math.sin(angle), 0.0), size, "paint", color, segments=8)

    ball(b, frame, (0.64 * math.cos(math.radians(180.0)) + 0.14, 0.64 * math.sin(math.radians(180.0)) + 0.12, 1.3), 0.04, "paint", BONE, segments=6)
    hoop(b, frame, (0.0, 0.0, 1.2), 0.95, 0.012, "metal", GOLD, sides=24, tube_sides=3, axis="Y")


def floating_candles(b: Builder, frame: Matrix, **options) -> None:
    """Ceiling prop: eleven candles hovering at different heights in a loose spiral, each with a flame and a
    drip of wax, held by nothing but magic (a faint rune ring on the ceiling)."""
    generator = rng(options)

    flat_ring(b, at(frame, (0.0, 0.0, 0.0), 180.0, "X"), 0.4, 0.03, "glow_amber", sides=16)

    for index in range(11):
        angle = math.radians(index * 137.5)
        reach = 0.12 + 0.065 * index
        base = (reach * math.cos(angle), reach * math.sin(angle), -0.55 - index * 0.12 - generator.uniform(0.0, 0.08))

        candle(b, frame, base, generator.uniform(0.18, 0.3), radius=0.035)
        cyl(b, frame, (base[0], base[1], base[2] - 0.03), 0.045, 0.03, "paint", CANDLE_WAX, sides=6, top=0.03)


def copper_pipes(b: Builder, frame: Matrix, **options) -> None:
    """Ceiling prop: a run of copper pipes 3.2 m long with flanges, elbows, a brass valve wheel, hanging
    brackets and a glass catch-flask dripping at the low end."""
    run_z = -0.38

    for bracket in (-1.4, 0.0, 1.4):
        box(b, frame, (bracket - 0.03, -0.08, run_z), (bracket + 0.03, 0.08, 0.0), "metal", DARK_IRON)
        box(b, frame, (bracket - 0.05, -0.1, run_z - 0.03), (bracket + 0.05, 0.1, run_z), "metal", DARK_IRON)

    cyl(b, frame, (-1.6, 0.0, run_z + 0.0), 0.06, 3.2, "metal", COPPER, sides=8, axis="X")
    cyl(b, frame, (-1.6, 0.0, run_z - 0.2), 0.04, 3.2 * 0.5, "metal", COPPER, sides=8, axis="X")

    for flange in (-1.0, -0.2, 0.7, 1.3):
        hoop(b, frame, (flange, 0.0, run_z), 0.068, 0.014, "metal", BRASS, sides=8, tube_sides=3, axis="X")

    ball(b, frame, (-1.6, 0.0, run_z), 0.075, "metal", COPPER, segments=8)
    ball(b, frame, (1.6, 0.0, run_z), 0.075, "metal", COPPER, segments=8)
    cyl(b, frame, (1.6, 0.0, run_z - 0.7), 0.06, 0.7, "metal", COPPER, sides=8)
    cyl(b, frame, (-0.6, 0.0, run_z - 0.2), 0.04, 0.2, "metal", COPPER, sides=8)
    rod(b, frame, (0.35, 0.0, run_z), (0.35, 0.0, run_z + 0.22), 0.025, "metal", BRASS)
    hoop(b, frame, (0.35, 0.0, run_z + 0.24), 0.09, 0.012, "metal", BRASS, sides=10, tube_sides=3)
    rod(b, frame, (0.26, 0.0, run_z + 0.24), (0.44, 0.0, run_z + 0.24), 0.012, "metal", BRASS)
    rod(b, frame, (0.35, 0.0, run_z + 0.15), (0.35, 0.0, run_z + 0.33), 0.012, "metal", BRASS)
    flask(b, frame, (1.6, 0.0, run_z - 1.1), 0.1, 0.22, "vitrine", None, shape="round", cork=False)
    cyl(b, frame, (1.6, 0.0, run_z - 1.08), 0.075, 0.1, "glow_green", sides=8)
    gem(b, frame, (1.6, 0.0, run_z - 0.8), 0.015, "glow_green", scale=(0.8, 0.8, 1.6))


def athanor_furnace(b: Builder, frame: Matrix, **options) -> None:
    """Alchemist's furnace against the wall, 1.8 m: a brick body with a stone cap, a glowing firebox door with a
    brass handle, an ash drawer, a copper hood and a chimney pipe up to the ceiling joists."""
    brick = options.get("brick", BRICK["tudor"])

    box(b, frame, (-0.9, -0.55, 0.0), (0.9, 0.55, 0.12), "stone", STONE["media"])
    box(b, frame, (-0.8, -0.48, 0.12), (0.8, 0.5, 1.2), "brick", brick)
    box(b, frame, (-0.86, -0.52, 1.2), (0.86, 0.54, 1.3), "stone", STONE["clara"])
    box(b, frame, (-0.5, -0.5, 0.46), (0.5, -0.46, 1.04), "metal", DARK_IRON)
    box(b, frame, (-0.4, -0.52, 0.56), (0.4, -0.5, 0.94), "glow_ember")
    box(b, frame, (-0.44, -0.54, 0.52), (0.44, -0.5, 0.56), "metal", DARK_IRON)
    box(b, frame, (-0.44, -0.54, 0.94), (0.44, -0.5, 0.98), "metal", DARK_IRON)

    for bar in range(5):
        box(b, frame, (-0.34 + bar * 0.17, -0.545, 0.56), (-0.32 + bar * 0.17, -0.52, 0.94), "metal", DARK_IRON)

    box(b, frame, (-0.3, -0.5, 0.2), (0.3, -0.46, 0.36), "metal", DARK_IRON)
    box(b, frame, (-0.08, -0.53, 0.26), (0.08, -0.5, 0.3), "metal", BRASS)
    rod(b, frame, (0.45, -0.54, 0.6), (0.45, -0.58, 0.9), 0.02, "metal", BRASS)

    spin(b, frame, [(0.55, 1.3), (0.5, 1.45), (0.36, 1.7), (0.2, 1.9), (0.13, 2.0)], "metal", COPPER, sides=10, base=(0.0, 0.0, 0.0))
    hoop(b, frame, (0.0, 0.0, 1.45), 0.5, 0.025, "metal", BRASS, sides=10, tube_sides=3)
    hoop(b, frame, (0.0, 0.0, 1.9), 0.2, 0.02, "metal", BRASS, sides=10, tube_sides=3)
    cyl(b, frame, (0.0, 0.0, 2.0), 0.12, 2.0, "metal", COPPER, sides=10)

    for collar in (2.6, 3.3):
        hoop(b, frame, (0.0, 0.0, collar), 0.13, 0.02, "metal", BRASS, sides=10, tube_sides=3)

    for kettle_x in (-0.4, 0.3):
        spin(b, frame, [(0.1, 1.3), (0.13, 1.36), (0.14, 1.44), (0.1, 1.5), (0.04, 1.52)], "metal", COPPER, sides=8, base=(kettle_x, 0.05, 0.0))


def hearth_ring(b: Builder, frame: Matrix, **options) -> None:
    """Flat stone hearth under the big cauldron: a ring of wedge-cut flags round a sooty pit."""
    spin(b, frame, [(1.0, 0.0), (1.0, 0.025)], "paint", "3B2C3A", sides=16)
    spin(b, frame, [(1.0, 0.0), (1.32, 0.0), (1.32, 0.12), (1.0, 0.12)], "stone", STONE["media"], sides=16, closed=True)
    spin(b, frame, [(1.0, 0.12), (1.32, 0.12), (1.34, 0.14), (1.0, 0.14)], "stone", STONE["clara"], sides=16, closed=True)

    for flag in range(16):
        angle = math.radians(flag * 22.5)

        rod(b, frame, (1.0 * math.cos(angle), 1.0 * math.sin(angle), 0.145), (1.33 * math.cos(angle), 1.33 * math.sin(angle), 0.145), 0.012, "paint", "8E8AA0", depth=0.004)


# ---------- cabinet of curiosities (Wunderkammer) ----------

CURIO_WOOD = "6B4A3A"


def _curio_skull(b: Builder, frame: Matrix, x: float, z: float, generator: random.Random) -> None:
    ball(b, frame, (x, 0.0, z + 0.1), 0.085, "paint", BONE, scale=(0.85, 1.0, 0.9))
    block(b, frame, (x, -0.04, z + 0.03), (0.1, 0.08, 0.06), "paint", BONE)

    for side in (-1, 1):
        ball(b, frame, (x + side * 0.032, -0.07, z + 0.1), 0.022, "paint", "3A3152")


def _curio_jar(b: Builder, frame: Matrix, x: float, z: float, generator: random.Random) -> None:
    flask(b, frame, (x, 0.0, z), 0.08, 0.26, "glass", "CFE9E0", shape="tall", cork=True)
    ball(b, frame, (x, 0.0, z + 0.1), 0.045, "paint", generator.choice(("C9A36B", "8FA86B", "D99A84")), scale=(1.0, 1.0, 1.6))


def _curio_crystals(b: Builder, frame: Matrix, x: float, z: float, generator: random.Random) -> None:
    tone = generator.choice(("glow_cyan", "glow_pink", "glow_green"))

    for index in range(3):
        crystal(b, frame, (x - 0.06 + index * 0.06, 0.0, z), 0.03, generator.uniform(0.12, 0.22), tone, tilt=(generator.uniform(-15.0, 15.0), generator.uniform(-20.0, 20.0)))


def _curio_books(b: Builder, frame: Matrix, x: float, z: float, generator: random.Random) -> None:
    book_row(b, frame, x - 0.26, x + 0.26, 0.0, z, 0.2, 0.3, generator)


def _curio_coral(b: Builder, frame: Matrix, x: float, z: float, generator: random.Random) -> None:
    cyl(b, frame, (x, 0.0, z), 0.06, 0.04, "wood", DARK_WOOD, sides=6)

    for index in range(5):
        angle = math.radians(index * 72.0 + generator.uniform(-20.0, 20.0))
        rod(b, frame, (x, 0.0, z + 0.04), (x + 0.1 * math.cos(angle), 0.05 * math.sin(angle), z + generator.uniform(0.18, 0.3)), 0.022, "paint", "E0604A")


def _curio_shell(b: Builder, frame: Matrix, x: float, z: float, generator: random.Random) -> None:
    spin(b, at(frame, (x, 0.0, z + 0.07), 90.0, "Y"), [(0.0, -0.12), (0.07, -0.06), (0.08, 0.02), (0.04, 0.1), (0.0, 0.13)], "paint", "F2D9C0", sides=7)


def _curio_horn(b: Builder, frame: Matrix, x: float, z: float, generator: random.Random) -> None:
    points = [(x - 0.2, 0.0, z + 0.03), (x - 0.05, 0.0, z + 0.08), (x + 0.1, 0.0, z + 0.16), (x + 0.2, 0.0, z + 0.3)]

    for (start, end), radius in zip(zip(points, points[1:]), (0.04, 0.03, 0.018)):
        rod(b, frame, start, end, radius * 2.0, "paint", "E2CFA6")


CURIOS = (_curio_skull, _curio_jar, _curio_crystals, _curio_books, _curio_coral, _curio_shell, _curio_horn)


def curiosity_cabinet(b: Builder, frame: Matrix, **options) -> None:
    """Wall-high curiosity shelving 2.0 x 0.5 x 3.4 as in the old Wunderkammer engravings: a dark carcass of
    three bays and five open shelves crammed with skulls, specimen jars, crystals, books, coral, shells and horns
    over a base of drawers, a cornice on top."""
    generator = rng(options)
    shelves = (1.0, 1.5, 2.0, 2.5, 2.95)
    bays = (-0.62, 0.0, 0.62)
    slots = list(itertools.product(shelves, bays))

    for x in (-0.98, -0.31, 0.31, 0.98):
        block(b, frame, (x, 0.0, 1.7), (0.05, 0.46, 3.4), "wood", CURIO_WOOD)

    block(b, frame, (0.0, 0.2, 1.7), (2.0, 0.04, 3.4), "wood", "4F3A2E")
    block(b, frame, (0.0, 0.0, 0.45), (2.0, 0.48, 0.9), "wood", CURIO_WOOD)
    block(b, frame, (0.0, -0.02, 3.42), (2.12, 0.56, 0.1), "wood_light", WOOD["mel"])

    for x, z in itertools.product((-0.62, 0.0, 0.62), (0.25, 0.65)):
        block(b, frame, (x, -0.245, z), (0.52, 0.02, 0.3), "wood_light", WOOD["mel"])
        ball(b, frame, (x, -0.265, z), 0.02, "metal", BRASS, segments=6)

    for z in shelves:
        block(b, frame, (0.0, 0.0, z - 0.02), (1.96, 0.44, 0.04), "wood", CURIO_WOOD)

    for z, x in slots:
        CURIOS[generator.randrange(len(CURIOS))](b, frame, x, z, generator)


def vitrine_case(b: Builder, frame: Matrix, **options) -> None:
    """Kunstkammer table case 1.2 x 0.7: turned oak legs, a velvet bed under a glass box with brass edges, and on
    it a crystal cluster, a small skull and a gem on a cushion."""
    generator = rng(options)
    top = 0.86
    glass_top = top + 0.6

    for x, y in itertools.product((-0.52, 0.52), (-0.28, 0.28)):
        spin(b, frame, [(0.04, 0.0), (0.05, 0.3), (0.035, 0.55), (0.045, top - 0.08)], "wood", CURIO_WOOD, sides=6, base=(x, y, 0.0))

    block(b, frame, (0.0, 0.0, top - 0.05), (1.2, 0.7, 0.1), "wood", CURIO_WOOD)
    block(b, frame, (0.0, 0.0, top + 0.01), (1.12, 0.62, 0.02), "paint", options.get("velvet", NAVY))
    box(b, frame, (-0.56, -0.31, top), (0.56, 0.31, glass_top), "glass", "DCEFF2")

    for x, y in itertools.product((-0.56, 0.56), (-0.31, 0.31)):
        rod(b, frame, (x, y, top), (x, y, glass_top), 0.02, "metal", BRASS)

    for y in (-0.31, 0.31):
        rod(b, frame, (-0.56, y, glass_top), (0.56, y, glass_top), 0.02, "metal", BRASS)

    _curio_crystals(b, frame, -0.3, top + 0.02, generator)
    _curio_skull(b, frame, 0.05, top + 0.02, generator)
    block(b, frame, (0.33, 0.0, top + 0.05), (0.16, 0.16, 0.06), "paint", WINE)
    gem(b, frame, (0.33, 0.0, top + 0.12), 0.04, generator.choice(("glow_cyan", "glow_pink", "glow_amber")))


def armillary_sphere(b: Builder, frame: Matrix, **options) -> None:
    """Great gilded armillary sphere 1.4 m across on a carved stone pedestal: horizon ring on four claws,
    meridian, equator, tilted ecliptic band and the two colures around a small blue earth on its axis."""
    centre = (0.0, 0.0, 1.55)
    radius = 0.62
    tilted = at(frame, centre, 23.5, "Y")

    spin(b, frame, [(0.5, 0.0), (0.5, 0.12), (0.36, 0.2), (0.24, 0.3), (0.2, 0.62), (0.28, 0.7), (0.12, 0.82)], "paint", MARBLE, sides=10)

    for leg in range(4):
        angle = math.radians(45.0 + leg * 90.0)
        rod(b, frame, (0.1 * math.cos(angle), 0.1 * math.sin(angle), 0.8), ((radius + 0.06) * math.cos(angle), (radius + 0.06) * math.sin(angle), centre[2]), 0.05, "metal", GOLD)

    hoop(b, frame, centre, radius + 0.06, 0.035, "metal", GOLD, sides=24)
    hoop(b, frame, centre, radius, 0.022, "metal", BRASS, sides=24, axis="X")
    hoop(b, tilted, (0.0, 0.0, 0.0), radius - 0.03, 0.02, "metal", GOLD, sides=24)
    hoop(b, tilted, (0.0, 0.0, 0.0), radius - 0.03, 0.02, "metal", GOLD, sides=24, axis="Y")
    hoop(b, at(tilted, (0.0, 0.0, 0.0), 23.5, "X"), (0.0, 0.0, 0.0), radius - 0.05, 0.05, "metal", BRASS, sides=24, tube_sides=4)
    rod(b, tilted, (0.0, 0.0, -radius - 0.08), (0.0, 0.0, radius + 0.08), 0.03, "metal", GOLD)
    ball(b, tilted, (0.0, 0.0, 0.0), 0.16, "paint", "3E6AB0", segments=10)
    gem(b, tilted, (0.0, 0.0, radius + 0.12), 0.05, "glow_amber")


def hanging_crocodile(b: Builder, frame: Matrix, **options) -> None:
    """Stuffed crocodile hung under the ceiling on two chains (z = 0 at the mount), belly down, as in the
    curiosity cabinets' ceilings."""
    hide, belly = "5E6B3A", "B8B07A"
    body_z = -0.85
    segments = [(-1.45, 0.05, 0.04), (-1.1, 0.09, 0.07), (-0.7, 0.13, 0.1), (-0.3, 0.2, 0.14), (0.1, 0.24, 0.16), (0.5, 0.22, 0.15), (0.85, 0.14, 0.1), (1.15, 0.09, 0.07), (1.45, 0.05, 0.04)]

    for (x_from, width_from, height_from), (x_to, width_to, height_to) in zip(segments, segments[1:]):
        points = [(x, side * width, body_z + vertical * height) for x, width, height in ((x_from, width_from, height_from), (x_to, width_to, height_to)) for side, vertical in itertools.product((-1, 1), (-1, 1))]
        b.hull(points, "paint", srgb(hide), frame=frame)

    block(b, frame, (0.1, 0.0, body_z - 0.14), (1.2, 0.36, 0.04), "paint", belly)

    for x in (-0.6, -0.2, 0.2, 0.6, 0.9):
        gem(b, frame, (x, 0.0, body_z + 0.17), 0.04, "paint", "4A5530", scale=(1.0, 0.6, 1.0))

    for x, side in itertools.product((-0.15, 0.55), (-1, 1)):
        rod(b, frame, (x, side * 0.2, body_z - 0.04), (x + 0.12, side * 0.38, body_z - 0.16), 0.06, "paint", hide)

    for side in (-1, 1):
        ball(b, frame, (1.3, side * 0.04, body_z + 0.06), 0.018, "glow_amber")

    for x in (-0.6, 0.6):
        rod(b, frame, (x, 0.0, 0.0), (x, 0.0, body_z + 0.1), 0.015, "metal", DARK_IRON)


# ---------- draper and tailor ----------

def haberdashery_drawers(b: Builder, frame: Matrix, **options) -> None:
    """Haberdasher's wall cabinet 2.0 x 0.55 x 2.4: a base of small glass-fronted drawers (buttons, ribbons, thread
    in every colour behind the glass), a counter-height ledge, and open pigeonholes of spools and folded lace above."""
    generator = rng(options)
    columns, rows = 6, 5
    drawer_width, drawer_height = 1.9 / columns, 1.0 / rows
    drawers = list(itertools.product(range(columns), range(rows)))
    holes = list(itertools.product(range(4), range(3)))

    block(b, frame, (0.0, 0.0, 0.55), (2.0, 0.55, 1.1), "wood", DARK_WOOD)
    block(b, frame, (0.0, 0.12, 1.75), (2.0, 0.3, 1.3), "wood", DARK_WOOD)
    block(b, frame, (0.0, -0.04, 1.13), (2.06, 0.62, 0.05), "wood_light", WOOD["mel"])
    block(b, frame, (0.0, 0.1, 2.43), (2.06, 0.36, 0.07), "wood_light", WOOD["mel"])

    for column, row in drawers:
        x = -0.95 + drawer_width * (column + 0.5)
        z = 0.06 + drawer_height * (row + 0.5)
        block(b, frame, (x, -0.28, z), (drawer_width - 0.03, 0.02, drawer_height - 0.03), "paint", generator.choice(GOODS_PALETTE))
        block(b, frame, (x, -0.292, z), (drawer_width - 0.05, 0.006, drawer_height - 0.06), "glass", "DCEFF2")
        ball(b, frame, (x, -0.3, z - drawer_height * 0.3), 0.012, "metal", BRASS, segments=6)

    for column, row in holes:
        x = -0.72 + column * 0.48
        z = 1.22 + row * 0.4
        block(b, frame, (x, -0.02, z + 0.17), (0.44, 0.26, 0.02), "wood", DARK_WOOD)

        for spool in range(3):
            cyl(b, frame, (x - 0.12 + spool * 0.12, -0.04, z), 0.045, 0.12, "paint", generator.choice(GOODS_PALETTE), sides=6)


def pressing_stove(b: Builder, frame: Matrix, **options) -> None:
    """Tailor's pressing stove: a squat cast-iron stove with a pipe to the wall and four flat irons heating on its
    shelf, a pressing board on trestles beside it with a folded coat and a goose iron."""
    cyl(b, frame, (-0.45, 0.0, 0.0), 0.3, 0.75, "metal", DARK_IRON, sides=10)
    cyl(b, frame, (-0.45, 0.0, 0.75), 0.34, 0.06, "metal", DARK_IRON, sides=10)
    block(b, frame, (-0.45, -0.31, 0.3), (0.2, 0.02, 0.16), "glow_ember")
    rod(b, frame, (-0.45, 0.05, 0.81), (-0.45, 0.05, 2.1), 0.12, "metal", DARK_IRON)
    rod(b, frame, (-0.45, 0.05, 2.1), (-0.45, 0.28, 2.3), 0.12, "metal", DARK_IRON)

    for index in range(4):
        angle = math.radians(index * 90.0 + 45.0)
        hull_points = [(-0.45 + 0.2 * math.cos(angle) + dx, 0.2 * math.sin(angle) + dy, 0.81 + dz) for dx, dy, dz in itertools.product((-0.06, 0.06), (-0.035, 0.035), (0.0, 0.05))]
        b.hull(hull_points + [(-0.45 + 0.2 * math.cos(angle) + 0.09, 0.2 * math.sin(angle), 0.82)], "metal", srgb(DARK_IRON), frame=frame)

    for x in (0.2, 0.9):
        rod(b, frame, (x, -0.15, 0.0), (x, 0.15, 0.85), 0.04, "wood", DARK_WOOD)
        rod(b, frame, (x, 0.15, 0.0), (x, -0.15, 0.85), 0.04, "wood", DARK_WOOD)

    block(b, frame, (0.55, 0.0, 0.88), (0.95, 0.36, 0.05), "wood_light", WOOD["mel"])
    block(b, frame, (0.48, 0.0, 0.93), (0.5, 0.3, 0.05), "paint", options.get("tint", "2B3C6E"))
    block(b, frame, (0.85, 0.02, 0.95), (0.18, 0.08, 0.08), "metal", DARK_IRON)


def cloth_bolt_table(b: Builder, frame: Matrix, **options) -> None:
    """Draper's sale table 1.8 x 0.9: bolts of cloth stacked flat in two piles and one unrolled length draped over
    the front edge, a measuring yardstick and shears on top."""
    generator = rng(options)
    top = 0.8

    for x, y in itertools.product((-0.82, 0.82), (-0.38, 0.38)):
        block(b, frame, (x, y, top / 2.0), (0.06, 0.06, top), "wood", DARK_WOOD)

    block(b, frame, (0.0, 0.0, top - 0.03), (1.8, 0.9, 0.06), "wood_light", WOOD["mel"])
    block(b, frame, (0.0, 0.0, 0.18), (1.66, 0.76, 0.03), "wood", DARK_WOOD)

    for pile_x, level in itertools.product((-0.45, 0.4), range(4)):
        width = 0.62 - level * 0.03
        block(b, frame, (pile_x, 0.05, top + 0.06 + level * 0.11), (width, 0.5, 0.1), "paint", generator.choice(GOODS_PALETTE))

    cloth = generator.choice(GOODS_PALETTE)
    block(b, frame, (0.0, -0.2, top + 0.01), (0.5, 0.5, 0.02), "paint", cloth)
    block(b, frame, (0.0, -0.46, top - 0.3), (0.5, 0.02, 0.6), "paint", cloth)
    block(b, frame, (0.0, 0.38, top + 0.015), (1.6, 0.04, 0.01), "wood_light", WOOD["mel"])

    for side in (-1, 1):
        rod(b, frame, (0.55, -0.3, top + 0.02), (0.75, -0.3 + side * 0.05, top + 0.02), 0.012, "metal", SILVER)


PROPS = {
    "haberdashery_drawers": {"build": haberdashery_drawers, "size": (2.06, 0.62, 2.47), "solid": True, "clearance": 0.8},
    "pressing_stove": {"build": pressing_stove, "size": (2.0, 0.7, 2.35), "solid": True},
    "cloth_bolt_table": {"build": cloth_bolt_table, "size": (1.8, 0.94, 1.3), "solid": True, "clearance": 0.8},
    "curiosity_cabinet": {"build": curiosity_cabinet, "size": (2.12, 0.56, 3.47), "solid": True, "clearance": 1.0},
    "vitrine_case": {"build": vitrine_case, "size": (1.2, 0.7, 1.47), "solid": True, "clearance": 0.8},
    "armillary_sphere": {"build": armillary_sphere, "size": (1.4, 1.4, 2.3), "solid": True},
    "hanging_crocodile": {"build": hanging_crocodile, "size": (3.0, 0.8, 1.05), "solid": False, "hang": True},
    "crystal_ball_pedestal": {"build": crystal_ball_pedestal, "size": (0.56, 0.57, 1.49), "solid": True, "light": ((0.0, 0.0, 1.32), "8FD8FF", 1.0, 4.0)},
    "staff_rack": {"build": staff_rack, "size": (1.85, 0.5, 1.96), "solid": True},
    "wand_case": {"build": wand_case, "size": (1.24, 0.59, 0.95), "solid": True},
    "summoning_circle": {"build": summoning_circle, "size": (2.5, 2.5, 0.25), "solid": False, "light": ((0.0, 0.0, 0.4), "8FD8FF", 1.2, 4.5)},
    "celestial_globe": {"build": celestial_globe, "size": (0.93, 0.91, 1.4), "solid": True},
    "astrolabe": {"build": astrolabe, "size": (0.6, 0.52, 1.35), "solid": True},
    "floating_books": {"build": floating_books, "size": (0.91, 0.91, 1.59), "solid": False, "hang": True, "light": ((0.0, 0.0, -1.0), "F59AD8", 0.8, 4.0)},
    "giant_hourglass": {"build": giant_hourglass, "size": (0.59, 0.59, 1.1), "solid": True},
    "star_tapestry": {"build": star_tapestry, "size": (1.65, 0.13, 3.14), "solid": False},
    "mage_hat_stand": {"build": mage_hat_stand, "size": (0.93, 0.62, 2), "solid": True},
    "big_cauldron": {"build": big_cauldron, "size": (1.59, 1.52, 1.44), "solid": True, "light": ((0.0, 0.0, 1.2), "7FE08A", 1.5, 5.0)},
    "alembic_table": {"build": alembic_table, "size": (1.61, 0.81, 1.71), "solid": True, "light": ((0.22, 0.02, 1.05), "8FD8FF", 0.5, 3.0)},
    "potion_wall": {"build": potion_wall, "size": (2.41, 0.36, 2.3), "solid": True, "clearance": 0.8},
    "herb_bundles": {"build": herb_bundles, "size": (2, 0.31, 1.37), "solid": False, "hang": True},
    "glowing_jar": {"build": glowing_jar, "size": (0.48, 0.51, 0.89), "solid": True, "light": ((0.0, 0.0, 0.5), "7FE08A", 0.6, 3.0), "variants": ["green", "cyan", "pink", "amber"]},
    "mortar_table": {"build": mortar_table, "size": (1, 0.61, 1.18), "solid": True},
    "recipe_board": {"build": recipe_board, "size": (1.21, 0.1, 1.99), "solid": False},
    "slime_jar": {"build": slime_jar, "size": (0.37, 0.37, 0.55), "solid": True},
    "skeleton_stand": {"build": skeleton_stand, "size": (0.48, 0.56, 1.87), "solid": True},
    "teller_counter": {"build": teller_counter, "size": (6.04, 0.96, 2.6), "solid": True, "clearance": 1.5},
    "vault_door": {"build": vault_door, "size": (2.41, 0.7, 2.41), "solid": True, "clearance": 1.5},
    "deposit_boxes": {"build": deposit_boxes, "size": (1.68, 0.61, 2.19), "solid": True, "clearance": 1.0},
    "coin_table": {"build": coin_table, "size": (1.4, 0.81, 1.12), "solid": True},
    "money_sacks": {"build": money_sacks, "size": (1.02, 0.82, 0.55), "solid": True},
    "iron_safe": {"build": iron_safe, "size": (0.84, 0.84, 1), "solid": True, "clearance": 1.0},
    "pillar_marble": {"build": pillar_marble, "size": (0.82, 0.82, 4), "solid": True},
    "tall_bookcase": {"build": tall_bookcase, "size": (2, 0.4, 4), "solid": True, "clearance": 1.0},
    "tall_bookcase_slim": {"build": tall_bookcase_slim, "size": (1.92, 0.4, 4), "solid": True, "clearance": 1.0},
    "rolling_ladder": {"build": rolling_ladder, "size": (0.5, 0.74, 3.4), "solid": True},
    "reading_table": {"build": reading_table, "size": (2, 1, 1.11), "solid": True},
    "lectern": {"build": lectern, "size": (0.62, 0.52, 1.18), "solid": True, "clearance": 0.8},
    "globe_stand": {"build": globe_stand, "size": (0.81, 0.81, 1.19), "solid": True},
    "printing_press": {"build": printing_press, "size": (1.12, 1.08, 1.86), "solid": True},
    "scroll_rack": {"build": scroll_rack, "size": (1.24, 0.4, 2.02), "solid": True, "clearance": 0.8},
    "map_table": {"build": map_table, "size": (2.41, 1.4, 1.05), "solid": True},
    "book_cart": {"build": book_cart, "size": (1.2, 0.44, 1.05), "solid": True},
    "jewel_case": {"build": jewel_case, "size": (1.56, 0.7, 1.14), "solid": True, "clearance": 1.0},
    "necklace_busts": {"build": necklace_busts, "size": (1.04, 0.44, 1.33), "solid": True, "clearance": 0.8},
    "goldsmith_bench": {"build": goldsmith_bench, "size": (1.4, 0.76, 1.48), "solid": True, "light": ((0.54, 0.0, 1.05), "FF8A3A", 0.6, 3.0)},
    "enchant_table": {"build": enchant_table, "size": (1.52, 1.02, 1.37), "solid": True, "light": ((0.0, 0.0, 1.25), "8FD8FF", 1.2, 4.5), "clearance": 1.0},
    "rune_pillar": {"build": rune_pillar, "size": (0.61, 0.61, 2.19), "solid": True, "light": ((0.0, 0.0, 2.05), "F59AD8", 0.5, 3.0)},
    "fabric_shelf": {"build": fabric_shelf, "size": (2, 0.5, 2.21), "solid": True, "clearance": 0.8},
    "dress_form": {"build": dress_form, "size": (0.76, 0.73, 1.68), "solid": True, "variants": ["dress", "gown", "cloak"]},
    "cutting_table": {"build": cutting_table, "size": (2.41, 1.23, 1.02), "solid": True},
    "spinning_wheel": {"build": spinning_wheel, "size": (1.17, 0.4, 1.03), "solid": True},
    "loom": {"build": loom, "size": (1.28, 1.02, 1.55), "solid": True},
    "clothes_rail": {"build": clothes_rail, "size": (1.59, 0.61, 1.71), "solid": True},
    "fitting_booth": {"build": fitting_booth, "size": (1.5, 1.42, 2.3), "solid": True, "clearance": 1.0},
    "hat_shelf": {"build": hat_shelf, "size": (1.21, 0.46, 1.9), "solid": True, "clearance": 0.8},
    "yarn_basket": {"build": yarn_basket, "size": (0.62, 0.59, 0.45), "solid": True},
    "dye_vats": {"build": dye_vats, "size": (1.8, 0.77, 0.99), "solid": True},
    "drying_rack_herbs": {"build": drying_rack_herbs, "size": (1.17, 0.57, 1.8), "solid": True},
    "seed_drawers": {"build": seed_drawers, "size": (1.24, 0.61, 1.53), "solid": True, "clearance": 0.8},
    "flower_steps": {"build": flower_steps, "size": (1.61, 1.02, 1.38), "solid": True},
    "planter_box": {"build": planter_box, "size": (1.24, 0.55, 0.78), "solid": True},
    "hanging_plants": {"build": hanging_plants, "size": (1.05, 0.45, 1.28), "solid": False, "hang": True},
    "watering_cans": {"build": watering_cans, "size": (0.78, 0.6, 0.42), "solid": True},
    "hanging_goods": {"build": hanging_goods, "size": (2, 0.26, 1.04), "solid": False, "hang": True, "light": ((-0.9, 0.0, -0.85), "FFD9A0", 0.8, 4.0)},
    "backpack_wall": {"build": backpack_wall, "size": (1.8, 0.4, 2.1), "solid": True, "clearance": 0.8},
    "tool_rack": {"build": tool_rack, "size": (1.4, 0.4, 1.8), "solid": True},
    "blanket_pile": {"build": blanket_pile, "size": (1.04, 0.66, 0.69), "solid": True},
    "cat_sleeping": {"build": cat_sleeping, "size": (0.39, 0.44, 0.26), "solid": False},
    "mana_crystal_crate": {"build": mana_crystal_crate, "size": (0.8, 0.67, 0.7), "solid": True, "light": ((0.0, 0.0, 0.6), "8FD8FF", 0.6, 3.0)},
}

PROPS.update(
    {
        "panel_screen": {"build": panel_screen, "size": (2.0, 0.28, 3.0), "solid": True, "variants": ["glazed", "lattice", "solid"]},
        "partition_doorway": {"build": partition_doorway, "size": (2.0, 0.28, 3.0), "solid": False, "variants": ["timber", "arch"]},
        "wainscot": {"build": wainscot, "size": (2.0, 0.12, 1.1), "solid": False},
        "book_gallery": {"build": book_gallery, "size": (4.16, 1.4, 4.9), "solid": True, "clearance": 1.0},
        "gallery_stair": {"build": gallery_stair, "size": (1.8, 1.8, 3.7), "solid": True, "clearance": 0.8},
        "rug_ornate": {"build": rug_ornate, "size": (3.0, 2.12, 0.04), "solid": False, "variants": list(RUG_PALETTES)},
        "rug_runner": {"build": rug_runner, "size": (1.2, 4.12, 0.04), "solid": False, "variants": list(RUG_PALETTES)},
    }
)

PROPS.update(
    {
        "screen_post": {"build": screen_post, "size": (0.28, 0.28, 3.0), "solid": True},
        "study_chair": {"build": study_chair, "size": (0.5, 0.5, 0.95), "solid": True, "clearance": 0.4},
        "card_catalog": {"build": card_catalog, "size": (1.44, 0.62, 1.4), "solid": True, "clearance": 0.8},
        "school_desk": {"build": school_desk, "size": (1.5, 0.96, 0.95), "solid": True},
        "teacher_desk": {"build": teacher_desk, "size": (2.06, 0.94, 1.1), "solid": True, "clearance": 1.0},
        "blackboard_big": {"build": blackboard_big, "size": (3.3, 0.18, 2.95), "solid": False},
        "coat_rack_wall": {"build": coat_rack_wall, "size": (2.1, 0.34, 2.08), "solid": False},
        "easel": {"build": easel, "size": (0.9, 1.0, 1.8), "solid": True},
        "lab_bench": {"build": lab_bench, "size": (2.24, 0.92, 1.45), "solid": True, "clearance": 0.8},
        "planet_mobile": {"build": planet_mobile, "size": (1.4, 1.4, 1.45), "solid": False, "hang": True},
        "school_bell": {"build": school_bell, "size": (0.5, 0.5, 2.1), "solid": False, "hang": True},
        "pew": {"build": pew, "size": (2.56, 0.8, 1.12), "solid": True},
        "candle_stand": {"build": candle_stand, "size": (0.5, 0.5, 1.9), "solid": True},
        "chancel_altar": {"build": chancel_altar, "size": (3.4, 1.3, 3.25), "solid": True, "clearance": 1.0},
        "reading_pulpit": {"build": reading_pulpit, "size": (1.0, 1.1, 1.8), "solid": True},
        "refectory_table": {"build": refectory_table, "size": (3.44, 1.8, 1.1), "solid": True},
        "cell_curtain": {"build": cell_curtain, "size": (1.2, 0.12, 2.1), "solid": True},
        "censer_hanging": {"build": censer_hanging, "size": (0.3, 0.3, 1.55), "solid": False, "hang": True},
    }
)

PROPS.update(
    {
        "summoning_dais": {"build": summoning_dais, "size": (3.4, 3.4, 0.34), "solid": False, "light": ((0.0, 0.0, 0.5), "8FD8FF", 1.2, 4.5)},
        "orrery": {"build": orrery, "size": (1.92, 1.9, 2.16), "solid": True},
        "floating_candles": {"build": floating_candles, "size": (1.6, 1.6, 2.1), "solid": False, "hang": True, "light": ((0.0, 0.0, -1.2), "FFC27A", 1.0, 4.5)},
        "copper_pipes": {"build": copper_pipes, "size": (3.4, 0.3, 1.5), "solid": False, "hang": True},
        "athanor_furnace": {"build": athanor_furnace, "size": (1.8, 1.2, 4.0), "solid": True, "light": ((0.0, -0.7, 0.75), "FF8A3A", 1.6, 4.5), "clearance": 1.0},
        "hearth_ring": {"build": hearth_ring, "size": (2.7, 2.7, 0.16), "solid": False},
    }
)
