"""Tavern, inn and bakery props (block C) for the shop interiors; follows the prop contract of shop_props_common.

Runs inside Blender, imported by build_market_shops.py and build_prop_sheet.py. Ceiling props ("hang": True)
have z = 0 at the ceiling mount and grow down; everything else stands on the floor at z = 0.
"""

import itertools
import math
import random
import sys
from pathlib import Path

from mathutils import Matrix

sys.path.insert(0, str(Path(__file__).resolve().parent))

from build_town_houses import BRICK, STONE, WOOD_DARK_BAND, WOOD_LIGHT_BAND, Builder, srgb  # noqa: E402
from shop_props_common import GLASS_PALETTE, GOODS_PALETTE, filled_row, lathe  # noqa: E402

WALNUT = "A8693F"
OAK = "D29A5E"
HONEY = "EDB77A"
PALE_WOOD = "FAD9A8"
BRASS = "D9A441"
COPPER = "D27A45"
WARM_IRON = "4A3A3E"  # dark iron leaning plum, never dead grey
CREAM = "F2E6CF"
FOAM = "FFF4DC"
SOOT = "2B1C1E"
CHALKBOARD = "2F4A3F"
BREAD = ("D9A05B", "C9873F", "E8C17A", "B5713A")
JAM = ("C9304A", "7A2F6A", "E0884A", "D94F8C", "E8C14F")
CAKE = ("F59AB5", "7A4A32", "F2D27A", "FFF4DC", "B57FE0", "7FD9C0")
BERRY = "D94F5C"
BOTTLE_PALETTE = (*GLASS_PALETTE, "8E2F3A", "3F8A50", "4F5FB0")


# ---------- small building blocks ----------

def turned(frame: Matrix, x: float, y: float, z: float, degrees: float = 0.0) -> Matrix:
    return frame @ Matrix.Translation((x, y, z)) @ Matrix.Rotation(math.radians(degrees), 4, "Z")


def plank(b: Builder, frame: Matrix, minimum: tuple, maximum: tuple, color: str = OAK, dark: bool = False):
    """Wooden box with planks running along its longest side."""
    band = WOOD_DARK_BAND if dark else WOOD_LIGHT_BAND

    return b.box(minimum, maximum, "wood", srgb(color), frame=frame, uv=("band", *band, 1.5))


def painted(b: Builder, frame: Matrix, minimum: tuple, maximum: tuple, color: str):
    return b.box(minimum, maximum, "paint", srgb(color), frame=frame)


def stick(b: Builder, frame: Matrix, start: tuple, end: tuple, thickness: float, color: str = OAK, material: str = "wood") -> None:
    b.beam(start, end, thickness, thickness, material, srgb(color), frame=frame, uv=("band", *WOOD_LIGHT_BAND, 1.0))


def arch(half: float, spring: float, rise: float = None, segments: int = 8) -> list:
    """Points of an (elliptic) arch from right to left over the top."""
    rise = half if rise is None else rise

    return [(half * math.cos(math.pi * step / segments), spring + rise * math.sin(math.pi * step / segments)) for step in range(segments + 1)]


def arched_frame(outer_top: list, outer_half: float, inner_half: float, inner_spring: float, inner_rise: float, base: float = 0.0) -> list:
    """Outline (u, z) of a wall piece with an arched opening cut from the bottom; outer_top runs right to left."""
    inner = list(reversed(arch(inner_half, inner_spring, inner_rise)))

    return [(-outer_half, base), (-inner_half, base), *inner, (inner_half, base), (outer_half, base), *outer_top]


def flame(b: Builder, frame: Matrix, base: tuple, radius: float, height: float, material: str = "glow_ember", lean: float = 0.0) -> None:
    """Teardrop flame: a square ring at a third of its height, a point below and a tip above."""
    x, y, z = base
    middle = z + height * 0.3
    ring_points = [(x + radius * math.cos(angle), y + radius * math.sin(angle), middle) for angle in (0.4, 1.97, 3.54, 5.11)]

    b.hull([(x, y, z), *ring_points, (x + lean, y, z + height)], material, frame=frame)


def bulb(b: Builder, frame: Matrix, center: tuple, radius: float, height: float, color: str, material: str = "paint") -> None:
    """Cheap faceted bulb (garlic, onion, roll, bubble): a ring of five points between a flat bottom and a tip."""
    x, y, z = center
    ring_points = [(x + radius * math.cos(2.0 * math.pi * index / 5.0), y + radius * math.sin(2.0 * math.pi * index / 5.0), z) for index in range(5)]
    bottom = [(x + radius * 0.5 * math.cos(2.0 * math.pi * index / 3.0), y + radius * 0.5 * math.sin(2.0 * math.pi * index / 3.0), z - height * 0.4) for index in range(3)]

    b.hull([*bottom, *ring_points, (x, y, z + height * 0.6)], material, srgb(color), frame=frame)


def loaf(b: Builder, frame: Matrix, center: tuple, size: tuple, color: str, degrees: float = 0.0) -> None:
    """Bread loaf (boule, batard, baguette, roll): a squashed sphere resting on center, long along local X."""
    b.sphere((0.0, 0.0, size[2]), 1.0, "paint", srgb(color), scale=size, frame=turned(frame, *center, degrees), segments=6)


def mug(b: Builder, frame: Matrix, x: float, y: float, z: float, foam: bool = True, color: str = HONEY) -> None:
    """Wooden tankard with a brass band, handle towards +X and an optional head of foam."""
    b.cylinder((x, y, z), 0.045, 0.12, 8, "wood", srgb(color), frame=frame, uv=("band", *WOOD_LIGHT_BAND, 0.4))

    b.cylinder((x, y, z + 0.075), 0.048, 0.02, 8, "metal", srgb(BRASS), frame=frame)

    b.box((x + 0.04, y - 0.012, z + 0.025), (x + 0.085, y + 0.012, z + 0.1), "wood", srgb(color), frame=frame)

    if foam:
        b.cylinder((x, y, z + 0.115), 0.042, 0.025, 6, "paint", srgb(FOAM), top_radius=0.03, frame=frame)


def plate(b: Builder, frame: Matrix, x: float, y: float, z: float, radius: float = 0.12, color: str = CREAM) -> None:
    b.cylinder((x, y, z), radius * 0.75, 0.014, 10, "paint", srgb(color), top_radius=radius, frame=frame)


def candle(b: Builder, frame: Matrix, x: float, y: float, z: float, height: float = 0.12, holder: bool = False) -> None:
    """Cream candle with a warm flame, optionally in a little brass dish."""
    lift = 0.02 if holder else 0.0

    if holder:
        b.cylinder((x, y, z), 0.05, 0.02, 8, "metal", srgb(BRASS), frame=frame)

    b.cylinder((x, y, z + lift), 0.022, height, 6, "paint", srgb(FOAM), frame=frame)

    flame(b, frame, (x, y, z + lift + height + 0.005), 0.012, 0.045, "glow_warm")


def barrel(b: Builder, frame: Matrix, radius: float, length: float, staves: str = HONEY, bands: str = WARM_IRON, head: str = PALE_WOOD) -> None:
    """Bulging barrel along local Z from 0 to length; the head at z = length gets a lighter lid."""
    profile = [(radius * 0.86, 0.0), (radius * 0.97, length * 0.2), (radius, length * 0.5), (radius * 0.97, length * 0.8), (radius * 0.86, length)]

    lathe(b, profile, 10, "wood", staves, frame, uv=("band", *WOOD_LIGHT_BAND, 0.8))

    for band_z in (length * 0.1, length * 0.82):
        b.cylinder((0.0, 0.0, band_z), radius * 0.955, length * 0.08, 10, "metal", srgb(bands), frame=frame)

    b.cylinder((0.0, 0.0, length - 0.005), radius * 0.8, 0.012, 10, "wood", srgb(head), frame=frame, uv=("band", *WOOD_LIGHT_BAND, 0.6))


def lying(frame: Matrix, x: float, z: float, length: float) -> Matrix:
    """Frame for a barrel lying along Y with its head (local z = length) facing the customer at -Y."""
    return frame @ Matrix.Translation((x, length / 2.0, z)) @ Matrix.Rotation(math.pi / 2.0, 4, "X")


def fire(b: Builder, frame: Matrix, x: float, y: float, z: float, width: float, seed: int = 0) -> None:
    """Crossed logs on a glowing ember bed with a few flames."""
    generator = random.Random(seed)

    b.sphere((x, y, z + width * 0.055), width * 0.45, "glow_ember", scale=(1.0, 0.7, 0.12), frame=frame, segments=8)

    for angle in (0.5, -0.5, 1.6):
        log_frame = frame @ Matrix.Translation((x, y, z + 0.06)) @ Matrix.Rotation(angle, 4, "Z")
        b.cylinder((-width * 0.42, 0.0, 0.0), 0.05, width * 0.84, 6, "wood", srgb(OAK), frame=log_frame, axis="X")

    flames = [(-0.2, 0.0, 0.55), (0.18, 0.05, 0.5), (0.0, -0.05, 0.75), (0.05, 0.1, 0.45)]

    for offset_x, offset_y, scale in flames:
        material = "glow_ember" if scale > 0.5 else "glow_amber"
        flame(b, frame, (x + offset_x * width, y + offset_y * width, z + 0.06), width * 0.12, width * scale, material, lean=generator.uniform(-0.04, 0.04))


def chair(b: Builder, frame: Matrix, wood: str = HONEY, cushion: str = "C9483B", material: str = "wood") -> None:
    """Dining chair facing -Y (backrest at +Y), seat at 0.45 m, 0.44 x 0.42 footprint."""
    tint = srgb(wood)
    legs = [(-0.18, -0.17, 0.43), (0.18, -0.17, 0.43), (-0.18, 0.17, 0.95), (0.18, 0.17, 0.95)]

    for leg_x, leg_y, top in legs:
        b.box((leg_x - 0.025, leg_y - 0.025, 0.0), (leg_x + 0.025, leg_y + 0.025, top), material, tint, frame=frame, uv=("band", *WOOD_LIGHT_BAND, 1.0))

    b.box((-0.22, -0.21, 0.41), (0.22, 0.21, 0.45), material, tint, frame=frame, uv=("band", *WOOD_LIGHT_BAND, 1.0))

    b.box((-0.2, 0.15, 0.82), (0.2, 0.2, 0.93), material, tint, frame=frame, uv=("band", *WOOD_LIGHT_BAND, 1.0))

    b.box((-0.06, 0.16, 0.45), (0.06, 0.19, 0.82), material, tint, frame=frame, uv=("band", *WOOD_LIGHT_BAND, 1.0))

    b.box((-0.18, -0.15, 0.15), (0.18, -0.12, 0.19), material, tint, frame=frame, uv=("band", *WOOD_LIGHT_BAND, 1.0))

    painted(b, frame, (-0.19, -0.19, 0.45), (0.19, 0.15, 0.49), cushion)


def chair_around(frame: Matrix, radius: float, degrees: float) -> Matrix:
    """Chair frame on a circle of the given radius, turned to face the centre."""
    angle = math.radians(degrees)

    return turned(frame, -radius * math.sin(angle), radius * math.cos(angle), 0.0, degrees)


def counter_body(b: Builder, frame: Matrix, minimum: tuple, maximum: tuple, body: str, trim: str, pilasters: int) -> None:
    """Panelled counter run facing -Y: dark plinth, body, raised pilasters and a mid rail on the front face."""
    (left, front, _), (right, back, top) = minimum, maximum

    plank(b, frame, (left + 0.03, front + 0.04, 0.0), (right - 0.03, back, 0.12), WALNUT, dark=True)

    plank(b, frame, (left, front + 0.02, 0.12), (right, back, top), body)

    plank(b, frame, (left, front, 0.5), (right, front + 0.02, 0.56), trim)

    for index in range(pilasters):
        pilaster_x = left + 0.04 + (right - left - 0.08) * index / max(1, pilasters - 1)
        plank(b, frame, (pilaster_x - 0.04, front, 0.12), (pilaster_x + 0.04, front + 0.02, top), trim)


def cake(b: Builder, frame: Matrix, x: float, y: float, z: float, radius: float, sponge: str, icing: str) -> None:
    """Round layer cake: sponge, icing cap and a cherry."""
    b.cylinder((x, y, z), radius, radius * 0.8, 10, "paint", srgb(sponge), frame=frame)

    b.cylinder((x, y, z + radius * 0.8), radius * 1.04, radius * 0.22, 10, "paint", srgb(icing), top_radius=radius * 0.9, frame=frame)

    b.sphere((x, y, z + radius * 1.1), radius * 0.16, "paint", srgb(BERRY), frame=frame, segments=4)


def cupcake(b: Builder, frame: Matrix, x: float, y: float, z: float, paper: str, icing: str) -> None:
    b.cylinder((x, y, z), 0.025, 0.04, 6, "paint", srgb(paper), top_radius=0.033, frame=frame)

    b.cylinder((x, y, z + 0.04), 0.036, 0.035, 6, "paint", srgb(icing), top_radius=0.006, frame=frame)


# ---------- tavern ----------

def bar_counter_l(b: Builder, frame: Matrix, **options) -> None:
    """L-shaped bar: a 6 m run facing the room and a return leg back to the wall on the right
    (variant "left" mirrors it). Brass foot rail, honey top, mugs and a candle on top."""
    body = options.get("tint", OAK)
    side = Matrix.Scale(-1.0, 4, (1.0, 0.0, 0.0)) if options.get("variant") == "left" else Matrix.Identity(4)
    bar = frame @ side
    generator = random.Random(options.get("seed", 0))

    counter_body(b, bar, (-2.95, -1.16, 0.0), (2.95, -0.45, 1.03), body, HONEY, 9)

    counter_body(b, turned(bar, 2.6, 0.38, 0.0, 90.0), (-0.82, -0.36, 0.0), (0.82, 0.32, 1.03), body, HONEY, 3)

    for board in range(3):
        plank(b, bar, (-3.0, -1.2 + board * 0.8 / 3.0, 1.03), (3.0, -1.2 + (board + 1) * 0.8 / 3.0 - 0.004, 1.1), (HONEY, PALE_WOOD)[board % 2])
        plank(b, bar, (2.2 + board * 0.8 / 3.0, -0.4, 1.03), (2.2 + (board + 1) * 0.8 / 3.0 - 0.004, 1.2, 1.1), (HONEY, PALE_WOOD)[board % 2])

    b.cylinder((-2.85, -1.17, 0.2), 0.025, 5.0, 8, "metal", srgb(BRASS), frame=bar, axis="X")

    for bracket_x in (-2.6, -0.9, 0.8, 2.0):
        b.box((bracket_x - 0.015, -1.17, 0.19), (bracket_x + 0.015, -1.14, 0.21), "metal", srgb(BRASS), frame=bar)

    plank(b, bar, (-2.9, -0.45, 0.84), (2.2, -0.3, 0.88), HONEY)

    for mug_x in (-2.6, -2.45, -0.3, 1.3):
        mug(b, bar, mug_x + generator.uniform(-0.05, 0.05), -0.8 + generator.uniform(-0.1, 0.1), 1.1, foam=mug_x > -2.5)

    for spare_x in (-1.8, -1.65, -1.5):
        mug(b, bar, spare_x, -0.37, 0.88, foam=False)

    candle(b, bar, 0.5, -0.7, 1.1, 0.1, holder=True)

    for tower_x in (-1.0, 1.9):
        b.cylinder((tower_x, -0.55, 1.1), 0.04, 0.32, 8, "metal", srgb(BRASS), frame=bar)
        b.cylinder((tower_x - 0.15, -0.55, 1.36), 0.025, 0.3, 6, "metal", srgb(BRASS), frame=bar, axis="X")

        for tap_x, handle in ((tower_x - 0.1, "C9483B"), (tower_x + 0.1, "3F8A50")):
            b.box((tap_x - 0.012, -0.64, 1.3), (tap_x + 0.012, -0.55, 1.33), "metal", srgb(BRASS), frame=bar)
            b.box((tap_x - 0.018, -0.58, 1.36), (tap_x + 0.018, -0.55, 1.48), "paint", srgb(handle), frame=bar)

    lathe(b, [(0.06, 1.1), (0.13, 1.14), (0.15, 1.18)], 8, "wood", PALE_WOOD, bar @ Matrix.Translation((-2.0, -0.6, 0.0)))

    for apple_x, apple_y, color in ((-2.05, -0.62, BERRY), (-1.95, -0.57, "7FC46A"), (-2.0, -0.66, BERRY), (-1.97, -0.62, "E8C14F")):
        bulb(b, bar, (apple_x, apple_y, 1.19), 0.04, 0.06, color)

    painted(b, bar, (-1.2, -0.75, 1.1), (-0.9, -0.6, 1.11), CREAM)


def bar_stool(b: Builder, frame: Matrix, **options) -> None:
    """Three-legged bar stool with a round padded seat."""
    cushion = options.get("tint", "C9483B")
    legs = [(0.15 * math.cos(angle), 0.15 * math.sin(angle)) for angle in (math.pi / 2.0, math.pi * 7.0 / 6.0, math.pi * 11.0 / 6.0)]

    for leg_x, leg_y in legs:
        stick(b, frame, (leg_x, leg_y, 0.0), (leg_x * 0.55, leg_y * 0.55, 0.68), 0.045, OAK)

    for (start_x, start_y), (end_x, end_y) in zip(legs, legs[1:] + legs[:1]):
        stick(b, frame, (start_x * 0.78, start_y * 0.78, 0.25), (end_x * 0.78, end_y * 0.78, 0.25), 0.03, HONEY)

    b.cylinder((0.0, 0.0, 0.66), 0.19, 0.05, 8, "wood", srgb(HONEY), frame=frame, uv=("band", *WOOD_LIGHT_BAND, 0.6))

    b.cylinder((0.0, 0.0, 0.71), 0.17, 0.06, 8, "paint", srgb(cushion), top_radius=0.14, frame=frame)


def keg_rack(b: Builder, frame: Matrix, **options) -> None:
    """Three barrels lying in a pyramid on a wooden cradle, each with a brass tap facing the customer."""
    length = 0.8
    radius = 0.31
    stain = options.get("tint", HONEY)
    cradle_top = 0.3
    barrels = [(-0.35, cradle_top + radius), (0.35, cradle_top + radius), (0.0, cradle_top + radius + 0.54)]

    for rail_y in (-0.3, 0.3):
        plank(b, frame, (-0.75, rail_y - 0.06, 0.0), (0.75, rail_y + 0.06, cradle_top), OAK)

    for barrel_x, barrel_z in barrels:
        barrel_frame = lying(frame @ Matrix.Translation((0.0, 0.035, 0.0)), barrel_x, barrel_z, length)
        barrel(b, barrel_frame, radius, length, staves=stain)
        b.cylinder((0.0, -radius * 0.45, length), 0.025, 0.06, 6, "metal", srgb(BRASS), frame=barrel_frame)
        b.box((-0.015, -radius * 0.45 - 0.09, length + 0.04), (0.015, -radius * 0.45, length + 0.07), "metal", srgb(BRASS), frame=barrel_frame)
        b.box((-0.012, -radius * 0.45 + 0.01, length + 0.045), (0.012, -radius * 0.45 + 0.12, length + 0.065), "paint", srgb("C9483B"), frame=barrel_frame)


def bottle_shelf(b: Builder, frame: Matrix, **options) -> None:
    """Back bar against the wall: a cabinet with three doors, then open shelves of colourful bottles."""
    generator = random.Random(options.get("seed", 0))
    body = options.get("tint", OAK)
    boards = (1.0, 1.42, 1.84)

    plank(b, frame, (-1.17, -0.2, 0.08), (1.17, 0.225, 0.95), body)

    plank(b, frame, (-1.15, -0.18, 0.0), (1.15, 0.2, 0.08), WALNUT, dark=True)

    plank(b, frame, (-1.2, -0.225, 0.95), (1.2, 0.225, 1.0), HONEY)

    for door_x in (-0.78, 0.0, 0.78):
        plank(b, frame, (door_x - 0.36, -0.215, 0.14), (door_x + 0.36, -0.2, 0.88), HONEY)
        plank(b, frame, (door_x - 0.27, -0.225, 0.24), (door_x + 0.27, -0.215, 0.78), body)
        b.box((door_x + 0.22, -0.225, 0.62), (door_x + 0.26, -0.215, 0.68), "metal", srgb(BRASS), frame=frame)

    plank(b, frame, (-1.15, 0.19, 1.0), (1.15, 0.225, 2.25), body)

    for side_x in (-1.2, 1.15):
        plank(b, frame, (side_x, -0.06, 1.0), (side_x + 0.05, 0.225, 2.3), body)

    for board_z in boards[1:]:
        plank(b, frame, (-1.15, -0.06, board_z - 0.03), (1.15, 0.19, board_z), HONEY)

    plank(b, frame, (-1.2, -0.1, 2.25), (1.2, 0.225, 2.32), HONEY)

    plank(b, frame, (-1.17, -0.08, 2.32), (1.17, 0.225, 2.4), body)

    barrel(b, lying(frame, -0.95, 1.15, 0.28), 0.14, 0.28)

    for mug_x in (-0.68, -0.55):
        mug(b, frame, mug_x, 0.0, 1.0, foam=False)

    filled_row(b, frame, -0.4, 1.1, 0.05, boards[0], 0.12, 0.34, generator, ("bottle", "bottle", "jar"), BOTTLE_PALETTE, gap=0.09)

    for board_z in boards[1:]:
        filled_row(b, frame, -1.1, 1.1, 0.06, board_z, 0.12, 0.36, generator, ("bottle", "bottle", "jar"), BOTTLE_PALETTE, gap=0.11, fill=0.85)


def mug_rail(b: Builder, frame: Matrix, **options) -> None:
    """Wall rail at 1.75 m with five pegs, a tankard hanging upside down from each, and a little top shelf."""
    rail = options.get("tint", HONEY)
    peg_z = 1.72
    hang = Matrix.Rotation(-math.pi / 2.0, 4, "Y")
    generator = random.Random(options.get("seed", 0))

    plank(b, frame, (-0.6, 0.07, 1.62), (0.6, 0.11, 1.84), rail)

    plank(b, frame, (-0.6, -0.06, 1.84), (0.6, 0.11, 1.87), OAK)

    for bracket_x in (-0.52, 0.52):
        b.side_prism([(0.07, 1.84), (-0.05, 1.84), (0.07, 1.72)], bracket_x - 0.02, bracket_x + 0.02, "wood", srgb(OAK), frame=frame)

    for peg_x in (-0.44, -0.22, 0.0, 0.22, 0.44):
        b.cylinder((peg_x, -0.04, peg_z), 0.012, 0.11, 6, "metal", srgb(BRASS), frame=frame, axis="Y")
        mug_color = generator.choice((HONEY, PALE_WOOD, OAK))
        mug(b, frame @ Matrix.Translation((peg_x + 0.06, -0.02, peg_z - 0.1)) @ hang, 0.0, 0.0, 0.0, foam=False, color=mug_color)

    for jug_x, color in ((-0.3, "4F8FC9"), (0.25, "E0884A")):
        lathe(b, [(0.04, 1.87), (0.06, 1.93), (0.035, 2.0), (0.045, 2.02)], 8, "paint", color, frame @ Matrix.Translation((jug_x, 0.02, 0.0)))


def fireplace(b: Builder, frame: Matrix, **options) -> None:
    """Big stone hearth with an arched firebox, a wooden mantel with candles and a crackling fire."""
    stone = options.get("tint", STONE["dourada"])
    opening_half = 0.62
    spring = 0.85
    surround = arched_frame([(1.25, 1.45), (-1.25, 1.45)], 1.25, opening_half, spring, 0.35)

    b.prism(surround, -0.38, -0.25, "stone", srgb(stone), frame=frame)

    b.box((-1.2, 0.15, 0.0), (1.2, 0.4, 1.45), "brick", srgb(BRICK["tudor"]), frame=frame)

    for cheek_x in (-1.2, opening_half):
        b.box((cheek_x, -0.25, 0.0), (cheek_x + 1.2 - opening_half, 0.15, 1.45), "brick", srgb(BRICK["tudor"]), frame=frame)

    b.box((-opening_half, -0.25, spring + 0.33), (opening_half, 0.15, 1.45), "brick", srgb(BRICK["tudor"]), frame=frame)

    painted(b, frame, (-opening_half, 0.12, 0.0), (opening_half, 0.15, spring + 0.33), SOOT)

    b.box((-1.0, -0.4, 0.0), (1.0, 0.15, 0.06), "stone", srgb(STONE["clara"]), frame=frame)

    b.box((-0.12, -0.4, spring + 0.24), (0.12, -0.36, 1.32), "stone", srgb(STONE["clara"]), frame=frame)

    for corbel_x in (-1.05, 1.05):
        b.side_prism([(-0.4, 1.45), (-0.25, 1.45), (-0.25, 1.3)], corbel_x - 0.08, corbel_x + 0.08, "wood", srgb(OAK), frame=frame)

    plank(b, frame, (-1.25, -0.4, 1.45), (1.25, 0.4, 1.56), OAK)

    b.box((-0.95, -0.15, 1.56), (0.95, 0.4, 2.2), "stone", srgb(stone), frame=frame)

    for andiron_x in (-0.35, 0.35):
        b.box((andiron_x - 0.02, -0.2, 0.06), (andiron_x + 0.02, 0.05, 0.12), "metal", srgb(WARM_IRON), frame=frame)
        b.cylinder((andiron_x, -0.2, 0.06), 0.03, 0.16, 6, "metal", srgb(BRASS), frame=frame)

    fire(b, frame, 0.0, -0.05, 0.06, 0.8, options.get("seed", 0))

    for candle_x, height in ((-1.05, 0.1), (-0.9, 0.16), (1.05, 0.13)):
        candle(b, frame, candle_x, -0.28, 1.56, height)

    lathe(b, [(0.05, 1.56), (0.09, 1.62), (0.07, 1.72), (0.04, 1.76), (0.05, 1.8)], 8, "paint", "4F8FC9", frame @ Matrix.Translation((0.55, -0.27, 0.0)))

    for plate_x, color in ((-0.5, "E0884A"), (0.75, "7FC46A")):
        b.cylinder((plate_x, -0.22, 1.66), 0.1, 0.015, 10, "paint", srgb(color), frame=frame @ Matrix.Translation((0.0, -0.22, 1.66)) @ Matrix.Rotation(-0.2, 4, "X") @ Matrix.Translation((0.0, 0.22, -1.66)), axis="Y")


def tavern_table_set(b: Builder, frame: Matrix, **options) -> None:
    """Long trestle table (1.6 x 0.9) with a bench on each side, set with tankards, plates of food and a candle."""
    generator = random.Random(options.get("seed", 0))
    top = options.get("tint", HONEY)

    for plank_index in range(3):
        plank(b, frame, (-0.8, -0.45 + plank_index * 0.3, 0.72), (0.8, -0.45 + (plank_index + 1) * 0.3 - 0.006, 0.78), (top, PALE_WOOD, top)[plank_index])

    plank(b, frame, (-0.78, -0.43, 0.68), (0.78, 0.43, 0.72), WALNUT, dark=True)

    for leg_x in (-0.58, 0.58):
        trestle = [(-0.38, 0.0), (-0.3, 0.1), (-0.06, 0.2), (-0.06, 0.66), (0.06, 0.66), (0.06, 0.2), (0.3, 0.1), (0.38, 0.0)]

        b.side_prism(trestle, leg_x - 0.05, leg_x + 0.05, "wood", srgb(OAK), frame=frame, uv=("band", *WOOD_LIGHT_BAND, 1.0))
        plank(b, frame, (leg_x - 0.06, -0.4, 0.0), (leg_x + 0.06, 0.4, 0.04), WALNUT, dark=True)
        plank(b, frame, (leg_x - 0.06, -0.38, 0.66), (leg_x + 0.06, 0.38, 0.72), OAK)

    plank(b, frame, (-0.68, -0.04, 0.3), (0.68, 0.04, 0.38), OAK)

    for wedge_x in (-0.65, 0.65):
        plank(b, frame, (wedge_x - 0.015, -0.05, 0.28), (wedge_x + 0.015, 0.05, 0.4), WALNUT, dark=True)

    for bench_y in (-0.8, 0.8):
        plank(b, frame, (-0.75, bench_y - 0.17, 0.41), (0.75, bench_y + 0.17, 0.46), top)
        plank(b, frame, (-0.73, bench_y - 0.15, 0.37), (0.73, bench_y + 0.15, 0.41), WALNUT, dark=True)

        for leg_x in (-0.57, 0.57):
            b.side_prism([(bench_y - 0.17, 0.0), (bench_y + 0.17, 0.0), (bench_y + 0.09, 0.2), (bench_y + 0.09, 0.37), (bench_y - 0.09, 0.37), (bench_y - 0.09, 0.2)], leg_x - 0.03, leg_x + 0.03, "wood", srgb(OAK), frame=frame, uv=("band", *WOOD_LIGHT_BAND, 1.0))

    plate(b, frame, -0.42, -0.2, 0.78)
    loaf(b, frame, (-0.42, -0.2, 0.792), (0.08, 0.06, 0.045), "C9782F")
    b.cylinder((-0.52, -0.2, 0.83), 0.012, 0.08, 6, "paint", srgb(FOAM), frame=frame, axis="X")

    plate(b, frame, 0.38, 0.2, 0.78, color="4F8FC9")
    loaf(b, frame, (0.36, 0.2, 0.792), (0.09, 0.05, 0.04), BREAD[0], 20.0)
    b.hull([(0.42, 0.12, 0.795), (0.5, 0.15, 0.795), (0.44, 0.2, 0.795), (0.44, 0.15, 0.84)], "paint", srgb("F2C14F"), frame=frame)

    for mug_x, mug_y in ((-0.12, -0.28), (0.08, 0.3), (0.6, -0.25), (-0.6, 0.22)):
        mug(b, frame, mug_x + generator.uniform(-0.04, 0.04), mug_y, 0.78)

    candle(b, frame, 0.0, 0.0, 0.78, 0.12, holder=True)


def round_table_set(b: Builder, frame: Matrix, **options) -> None:
    """Round table (1.2 m) on a pedestal with four chairs, a candle, tankards and a pie."""
    top = options.get("tint", HONEY)
    cushions = ("C9483B", "3F8A50", "C9483B", "3F8A50")

    b.cylinder((0.0, 0.0, 0.72), 0.6, 0.05, 12, "wood", srgb(top), frame=frame, uv=("band", *WOOD_LIGHT_BAND, 1.2))

    lathe(b, [(0.07, 0.08), (0.06, 0.3), (0.09, 0.5), (0.06, 0.72)], 8, "wood", OAK, frame, uv=("band", *WOOD_LIGHT_BAND, 1.0))

    for angle in (45.0, 135.0):
        plank(b, turned(frame, 0.0, 0.0, 0.0, angle), (-0.38, -0.05, 0.0), (0.38, 0.05, 0.09), OAK)

    for degrees, cushion in zip((0.0, 90.0, 180.0, 270.0), cushions):
        chair(b, chair_around(frame, 0.8, degrees), HONEY, cushion)

    candle(b, frame, 0.0, 0.0, 0.77, 0.14, holder=True)

    plate(b, frame, -0.22, 0.2, 0.77, 0.14, "E8C14F")
    b.cylinder((-0.22, 0.2, 0.784), 0.1, 0.035, 10, "paint", srgb("D9A05B"), top_radius=0.09, frame=frame)

    mug(b, frame, 0.25, -0.15, 0.77)
    mug(b, frame, 0.2, 0.28, 0.77, foam=False, color=PALE_WOOD)


def stage(b: Builder, frame: Matrix, **options) -> None:
    """Low music stage (3 x 2 x 0.3) with a velvet skirt, a step, a stool with a lute, a drum and candle footlights."""
    skirt = options.get("tint", "A83A48")

    plank(b, frame, (-1.45, -0.72, 0.0), (1.45, 0.97, 0.24), OAK)

    for index in range(7):
        plank(b, frame, (-1.5, -0.75 + index * 0.25, 0.24), (1.5, -0.75 + (index + 1) * 0.25 - 0.005, 0.3), (HONEY, PALE_WOOD)[index % 2])

    painted(b, frame, (-1.45, -0.75, 0.04), (1.45, -0.72, 0.22), skirt)

    for tassel_x in [-1.3 + 0.325 * index for index in range(9)]:
        b.box((tassel_x - 0.03, -0.76, 0.12), (tassel_x + 0.03, -0.75, 0.22), "metal", srgb(BRASS), frame=frame)

    plank(b, frame, (-0.45, -1.0, 0.0), (0.45, -0.75, 0.15), HONEY)

    bar_stool(b, frame @ Matrix.Translation((0.25, 0.35, 0.3)) @ Matrix.Scale(0.75, 4), tint="3F8A50")

    lute_frame = frame @ Matrix.Translation((-0.1, 0.18, 0.56)) @ Matrix.Rotation(-0.3, 4, "X") @ Matrix.Rotation(0.35, 4, "Y")
    b.sphere((0.0, 0.0, 0.0), 1.0, "paint", srgb("E0A060"), scale=(0.2, 0.1, 0.25), frame=lute_frame, segments=8)
    b.cylinder((0.0, -0.105, 0.05), 0.05, 0.02, 8, "paint", srgb(SOOT), frame=lute_frame, axis="Y")
    b.box((-0.03, -0.09, 0.2), (0.03, -0.04, 0.62), "wood", srgb(OAK), frame=lute_frame)
    stick(b, lute_frame, (0.0, -0.065, 0.62), (0.0, 0.03, 0.76), 0.06, WALNUT)
    b.box((-0.04, -0.11, -0.16), (0.04, -0.09, -0.12), "wood", srgb(WALNUT), frame=lute_frame)

    b.cylinder((0.95, 0.45, 0.3), 0.2, 0.32, 10, "paint", srgb("C9483B"), frame=frame)
    b.cylinder((0.95, 0.45, 0.62), 0.21, 0.02, 10, "paint", srgb(CREAM), frame=frame)
    b.cylinder((0.95, 0.45, 0.3), 0.21, 0.03, 10, "metal", srgb(BRASS), frame=frame)

    for footlight_x in (-1.3, 1.3):
        candle(b, frame, footlight_x, -0.6, 0.3, 0.1, holder=True)


def mounted_head(b: Builder, frame: Matrix, **options) -> None:
    """Stylized hunting trophy on a wooden shield plaque (centre at 2.1 m): variants boar and stag."""
    variant = options.get("variant", "boar")
    shield = [(-0.3, 2.42), (0.3, 2.42), (0.3, 2.05), (0.0, 1.72), (-0.3, 2.05)]
    inner_shield = [(u * 0.85, 2.07 + (z - 2.07) * 0.85) for u, z in shield]

    b.prism(shield, 0.31, 0.35, "wood", srgb(OAK), frame=frame, uv=("band", *WOOD_LIGHT_BAND, 1.0))

    b.prism(inner_shield, 0.28, 0.31, "wood", srgb(HONEY), frame=frame, uv=("band", *WOOD_LIGHT_BAND, 1.0))

    HEADS[variant](b, frame)


def boar_head(b: Builder, frame: Matrix) -> None:
    fur = srgb("7A4A32")
    neck = [(x, 0.28, z) for x, z in itertools.product((-0.19, 0.19), (1.9, 2.24))]
    cheek = [(x, 0.02, z) for x, z in itertools.product((-0.18, 0.18), (1.88, 2.2))]
    snout = [(x, -0.2, z) for x, z in itertools.product((-0.09, 0.09), (1.92, 2.06))]

    b.hull([*neck, *cheek, *snout, (0.0, 0.2, 2.32)], "paint", fur, frame=frame)

    b.cylinder((0.0, -0.25, 1.99), 0.085, 0.06, 8, "paint", srgb("E8A3A0"), frame=frame, axis="Y")

    for side in (-1.0, 1.0):
        b.box((side * 0.035 - 0.012, -0.255, 1.98), (side * 0.035 + 0.012, -0.25, 2.01), "paint", srgb(SOOT), frame=frame)
        b.hull([(side * 0.08, -0.12, 1.92), (side * 0.11, -0.12, 1.94), (side * 0.09, -0.1, 1.9), (side * 0.14, -0.2, 2.05)], "paint", srgb(FOAM), frame=frame)
        b.hull([(side * 0.1, 0.18, 2.2), (side * 0.2, 0.2, 2.2), (side * 0.15, 0.14, 2.18), (side * 0.24, 0.14, 2.38)], "paint", fur, frame=frame)
        b.sphere((side * 0.12, -0.04, 2.13), 0.025, "paint", srgb(SOOT), frame=frame, segments=6)

    b.hull([(-0.03, 0.25, 2.28), (0.03, 0.25, 2.28), (0.0, 0.05, 2.22), (0.0, 0.2, 2.4)], "paint", srgb("4A2E22"), frame=frame)


def stag_head(b: Builder, frame: Matrix) -> None:
    fur = srgb("B87A48")
    antler = "F2E2C0"
    neck = [(x, 0.28, z) for x, z in itertools.product((-0.16, 0.16), (1.86, 2.2))]
    cheek = [(x, 0.03, z) for x, z in itertools.product((-0.12, 0.12), (1.95, 2.2))]
    muzzle = [(x, -0.24, z) for x, z in itertools.product((-0.06, 0.06), (1.95, 2.05))]

    b.hull([*neck, *cheek, *muzzle], "paint", fur, frame=frame)

    b.sphere((0.0, -0.25, 2.03), 0.04, "paint", srgb(SOOT), frame=frame, segments=6)

    b.hull([(x, -0.2, z) for x, z in itertools.product((-0.065, 0.065), (1.95, 2.0))] + [(0.0, 0.0, 1.95), (0.0, 0.1, 1.86)], "paint", srgb(CREAM), frame=frame)

    for side in (-1.0, 1.0):
        b.sphere((side * 0.1, -0.02, 2.14), 0.025, "paint", srgb(SOOT), frame=frame, segments=6)
        b.hull([(side * 0.12, 0.12, 2.18), (side * 0.13, 0.18, 2.22), (side * 0.12, 0.15, 2.14), (side * 0.32, 0.12, 2.24)], "paint", fur, frame=frame)
        stick(b, frame, (side * 0.07, 0.1, 2.2), (side * 0.28, 0.12, 2.5), 0.035, antler, "paint")
        stick(b, frame, (side * 0.28, 0.12, 2.5), (side * 0.42, 0.15, 2.72), 0.03, antler, "paint")
        stick(b, frame, (side * 0.15, 0.1, 2.32), (side * 0.2, -0.02, 2.42), 0.025, antler, "paint")
        stick(b, frame, (side * 0.28, 0.12, 2.5), (side * 0.25, 0.0, 2.68), 0.025, antler, "paint")
        stick(b, frame, (side * 0.36, 0.14, 2.62), (side * 0.46, 0.08, 2.6), 0.022, antler, "paint")


HEADS = {"boar": boar_head, "stag": stag_head}


def barrel_table(b: Builder, frame: Matrix, **options) -> None:
    """Standing barrel turned into a high table, with a round top, tankards, dice and a candle."""
    generator = random.Random(options.get("seed", 0))

    barrel(b, frame, 0.32, 0.95, staves=options.get("tint", HONEY))

    b.cylinder((0.0, 0.0, 0.95), 0.4, 0.05, 12, "wood", srgb(OAK), frame=frame, uv=("band", *WOOD_LIGHT_BAND, 0.8))

    mug(b, frame, -0.18, -0.1, 1.0)
    mug(b, frame, 0.12, 0.18, 1.0, foam=generator.random() < 0.5, color=PALE_WOOD)

    for die_x, die_y in ((0.12, -0.15), (0.2, -0.08)):
        painted(b, frame, (die_x - 0.02, die_y - 0.02, 1.0), (die_x + 0.02, die_y + 0.02, 1.04), "C9483B" if die_x < 0.15 else CREAM)

    candle(b, frame, -0.05, 0.2, 1.0, 0.09, holder=True)


def stew_pot(b: Builder, frame: Matrix, **options) -> None:
    """Big bubbling cauldron hanging from an iron A-frame crossbar over a stone fire ring."""
    stew = options.get("tint", "C8702F")
    generator = random.Random(options.get("seed", 0))
    stones = [(0.45 * math.cos(2.0 * math.pi * index / 9.0), 0.45 * math.sin(2.0 * math.pi * index / 9.0)) for index in range(9)]

    for stone_x, stone_y in stones:
        bulb(b, frame, (stone_x, stone_y, 0.065), 0.11, 0.15, generator.choice((STONE["dourada"], STONE["clara"], "D9B48A")), "stone")

    fire(b, frame, 0.0, 0.0, 0.0, 0.6, options.get("seed", 0))

    for side, foot_y in itertools.product((-1.0, 1.0), (-0.3, 0.3)):
        stick(b, frame, (side * 0.52, foot_y, 0.0), (side * 0.48, 0.0, 1.5), 0.045, WARM_IRON, "metal")

    b.cylinder((-0.54, 0.0, 1.47), 0.025, 1.08, 6, "metal", srgb(WARM_IRON), frame=frame, axis="X")

    stick(b, frame, (0.0, 0.0, 1.47), (0.0, 0.0, 1.05), 0.02, WARM_IRON, "metal")

    cauldron = [(0.14, 0.42), (0.28, 0.48), (0.34, 0.6), (0.33, 0.76), (0.29, 0.84), (0.32, 0.87), (0.3, 0.89)]
    lathe(b, cauldron, 10, "metal", WARM_IRON, frame)

    b.cylinder((0.0, 0.0, 0.86), 0.28, 0.035, 10, "paint", srgb(stew), frame=frame)

    for bit_x, bit_y, color in ((0.1, 0.05, "E0884A"), (-0.12, 0.08, "F2E6CF"), (0.02, -0.14, "7FC46A"), (-0.05, -0.02, "E0884A")):
        bulb(b, frame, (bit_x, bit_y, 0.9), 0.035, 0.03, color)

    for side in (-1.0, 1.0):
        stick(b, frame, (side * 0.31, 0.0, 0.86), (0.0, 0.0, 1.06), 0.015, WARM_IRON, "metal")

    stick(b, frame, (0.05, 0.05, 0.85), (0.24, 0.16, 1.05), 0.025, OAK)


def spit_roast(b: Builder, frame: Matrix, **options) -> None:
    """Roasting spit: a stone fire trough, two forked iron posts, a crank and a golden roast pig with an apple."""
    crust = options.get("tint", "C9782F")
    spit_z = 0.75

    b.box((-0.55, -0.3, 0.0), (0.55, 0.3, 0.16), "stone", srgb(STONE["media"]), frame=frame)

    painted(b, frame, (-0.47, -0.22, 0.16), (0.47, 0.22, 0.17), "6B4A3A")

    fire(b, frame, 0.0, 0.0, 0.16, 0.55, options.get("seed", 0))

    for post_x in (-0.7, 0.7):
        stick(b, frame, (post_x, 0.0, 0.0), (post_x, 0.0, spit_z - 0.05), 0.04, WARM_IRON, "metal")
        stick(b, frame, (post_x, 0.0, spit_z - 0.06), (post_x, -0.07, spit_z + 0.08), 0.025, WARM_IRON, "metal")
        stick(b, frame, (post_x, 0.0, spit_z - 0.06), (post_x, 0.07, spit_z + 0.08), 0.025, WARM_IRON, "metal")

    b.cylinder((-0.78, 0.0, spit_z), 0.015, 1.5, 6, "metal", srgb(WARM_IRON), frame=frame, axis="X")

    stick(b, frame, (0.72, 0.0, spit_z), (0.72, 0.0, spit_z - 0.18), 0.025, WARM_IRON, "metal")
    b.cylinder((0.72, 0.0, spit_z - 0.2), 0.02, 0.07, 6, "wood", srgb(OAK), frame=frame, axis="X")

    b.sphere((0.04, 0.0, spit_z), 1.0, "paint", srgb(crust), scale=(0.34, 0.17, 0.16), frame=frame, segments=10)

    b.sphere((-0.3, 0.0, spit_z + 0.03), 1.0, "paint", srgb(crust), scale=(0.11, 0.1, 0.1), frame=frame, segments=8)

    b.cylinder((-0.44, 0.0, spit_z + 0.02), 0.05, 0.05, 8, "paint", srgb("B5602A"), frame=frame, axis="X")

    bulb(b, frame, (-0.47, 0.0, spit_z + 0.0), 0.045, 0.08, BERRY)

    for side in (-1.0, 1.0):
        b.hull([(-0.3, side * 0.06, spit_z + 0.1), (-0.26, side * 0.08, spit_z + 0.1), (-0.28, side * 0.07, spit_z + 0.08), (-0.31, side * 0.11, spit_z + 0.17)], "paint", srgb("B5602A"), frame=frame)
        stick(b, frame, (0.25, side * 0.08, spit_z - 0.06), (0.36, side * 0.07, spit_z - 0.1), 0.04, "B5602A", "paint")
        stick(b, frame, (-0.15, side * 0.08, spit_z - 0.06), (-0.24, side * 0.07, spit_z - 0.1), 0.04, "B5602A", "paint")


def plate_rack(b: Builder, frame: Matrix, **options) -> None:
    """Wall plate rack (1.25 to 2.1 m): two shelves of painted plates standing on edge behind a rail."""
    wood = options.get("tint", HONEY)
    colors = ("4F8FC9", "E0884A", "7FC46A", "C9483B")
    plate_tilt = Matrix.Rotation(-0.15, 4, "X")

    for side_x in (-0.6, 0.56):
        plank(b, frame, (side_x, -0.06, 1.25), (side_x + 0.04, 0.125, 2.1), wood)

    plank(b, frame, (-0.56, 0.1, 1.25), (0.56, 0.125, 2.05), OAK)

    for shelf_z in (1.3, 1.7):
        plank(b, frame, (-0.56, -0.06, shelf_z - 0.03), (0.56, 0.1, shelf_z), wood)
        b.cylinder((-0.56, -0.04, shelf_z + 0.09), 0.012, 1.12, 6, "wood", srgb(OAK), frame=frame, axis="X")

    plank(b, frame, (-0.62, -0.08, 2.05), (0.62, 0.125, 2.1), wood)

    for (shelf_z, plate_x), color in zip(itertools.product((1.3, 1.7), (-0.39, -0.13, 0.13, 0.39)), itertools.cycle(colors)):
        plate_frame = frame @ Matrix.Translation((plate_x, 0.03, shelf_z + 0.11)) @ plate_tilt
        b.cylinder((0.0, -0.01, 0.0), 0.12, 0.012, 8, "paint", srgb(color), frame=plate_frame, axis="Y")
        b.cylinder((0.0, -0.016, 0.0), 0.08, 0.008, 8, "paint", srgb(CREAM), frame=plate_frame, axis="Y")


def menu_board(b: Builder, frame: Matrix, **options) -> None:
    """Wall chalkboard (centre 1.65 m) with chalk lines of dishes and a little drawn tankard."""
    generator = random.Random(options.get("seed", 0))
    chalks = (CREAM, CREAM, "F2D27A", "F59AB5", "8FD8FF")

    painted(b, frame, (-0.35, 0.0, 1.2), (0.35, 0.03, 2.1), CHALKBOARD)

    for minimum, maximum in (((-0.4, -0.01, 1.15), (0.4, 0.04, 1.2)), ((-0.4, -0.01, 2.1), (0.4, 0.04, 2.15)), ((-0.4, -0.01, 1.2), (-0.35, 0.04, 2.1)), ((0.35, -0.01, 1.2), (0.4, 0.04, 2.1))):
        plank(b, frame, minimum, maximum, HONEY)

    painted(b, frame, (-0.2, -0.004, 1.98), (0.2, 0.0, 2.02), "F2D27A")

    for line_z in (1.86, 1.76, 1.66, 1.56, 1.46, 1.36):
        length = generator.uniform(0.25, 0.42)
        painted(b, frame, (-0.28, -0.004, line_z), (-0.28 + length, 0.0, line_z + 0.022), generator.choice(chalks))
        painted(b, frame, (0.2, -0.004, line_z), (0.27, 0.0, line_z + 0.022), "F2D27A")

    painted(b, frame, (0.12, -0.004, 1.22), (0.2, 0.0, 1.32), "F2D27A")
    painted(b, frame, (0.2, -0.004, 1.25), (0.23, 0.0, 1.3), "F2D27A")
    painted(b, frame, (0.12, -0.004, 1.3), (0.2, 0.0, 1.33), CREAM)


def dart_board(b: Builder, frame: Matrix, **options) -> None:
    """Painted wooden target (centre 1.73 m) with rings and two darts stuck in it."""
    rings = ((0.3, OAK, "wood"), (0.25, "C9483B", "paint"), (0.19, CREAM, "paint"), (0.13, "3F8A50", "paint"), (0.08, CREAM, "paint"), (0.035, "C9483B", "paint"))

    for index, (radius, color, material) in enumerate(rings):
        front = 0.04 - index * 0.004
        b.cylinder((0.0, front, 1.73), radius, 0.09 - front, 12, material, srgb(color), frame=frame, axis="Y")

    for dart_x, dart_z, color in ((0.05, 1.79, BERRY), (-0.11, 1.68, "4F8FC9")):
        stick(b, frame, (dart_x, 0.02, dart_z), (dart_x + 0.01, -0.05, dart_z + 0.015), 0.012, BRASS, "metal")
        b.box((dart_x - 0.002, -0.08, dart_z - 0.01), (dart_x + 0.022, -0.05, dart_z + 0.04), "paint", srgb(color), frame=frame)


def kitchen_stove(b: Builder, frame: Matrix, **options) -> None:
    """Cast-iron cooking range with a glowing firebox, brass rail and towel, a copper pot and a kettle,
    and a stovepipe bending into the wall."""
    iron = options.get("tint", WARM_IRON)

    for leg_x, leg_y in itertools.product((-0.5, 0.5), (-0.25, 0.25)):
        b.box((leg_x - 0.04, leg_y - 0.04, 0.0), (leg_x + 0.04, leg_y + 0.04, 0.15), "metal", srgb(iron), frame=frame)

    b.box((-0.55, -0.3, 0.15), (0.55, 0.3, 0.85), "metal", srgb(iron), frame=frame)

    b.box((-0.6, -0.33, 0.85), (0.6, 0.33, 0.9), "metal", srgb("3A2E32"), frame=frame)

    b.box((-0.47, -0.31, 0.27), (-0.07, -0.3, 0.68), "metal", srgb(BRASS), frame=frame)
    b.box((-0.42, -0.32, 0.32), (-0.12, -0.31, 0.63), "glow_ember", frame=frame)

    b.box((0.05, -0.31, 0.27), (0.47, -0.3, 0.68), "metal", srgb("5A4448"), frame=frame)
    b.box((0.1, -0.33, 0.6), (0.42, -0.31, 0.63), "metal", srgb(BRASS), frame=frame)

    b.cylinder((-0.55, -0.34, 0.76), 0.012, 1.1, 6, "metal", srgb(BRASS), frame=frame, axis="X")
    painted(b, frame, (0.12, -0.355, 0.5), (0.35, -0.335, 0.78), CREAM)
    painted(b, frame, (0.12, -0.358, 0.56), (0.35, -0.355, 0.6), "C9483B")

    lathe(b, [(0.14, 0.9), (0.16, 0.95), (0.16, 1.08), (0.17, 1.1), (0.12, 1.13), (0.02, 1.15), (0.025, 1.18)], 10, "metal", COPPER, frame @ Matrix.Translation((-0.28, -0.05, 0.0)))

    lathe(b, [(0.09, 0.9), (0.12, 0.96), (0.1, 1.05), (0.04, 1.09), (0.015, 1.12)], 8, "metal", BRASS, frame @ Matrix.Translation((0.2, -0.08, 0.0)))
    stick(b, frame, (0.3, -0.08, 0.96), (0.38, -0.08, 1.04), 0.025, BRASS, "metal")

    b.cylinder((0.38, 0.18, 0.9), 0.075, 1.25, 8, "metal", srgb(iron), frame=frame)
    b.cylinder((0.38, 0.1, 2.08), 0.08, 0.25, 8, "metal", srgb(iron), frame=frame, axis="Y")
    b.cylinder((0.38, 0.18, 1.5), 0.085, 0.05, 8, "metal", srgb(BRASS), frame=frame)


# ---------- bakery ----------

def stone_oven(b: Builder, frame: Matrix, **options) -> None:
    """Domed bread oven on a stone base: brick-arched mouth glowing with embers, firewood niche, chimney,
    a peel resting on the right ledge and fresh rolls cooling on the left."""
    dome = options.get("tint", "F0C9A0")
    generator = random.Random(options.get("seed", 0))
    mouth = arched_frame(arch(0.45, 1.18), 0.45, 0.28, 1.08, 0.24, 0.92)

    b.box((-0.95, -0.75, 0.0), (0.95, 0.75, 0.85), "stone", srgb(STONE["clara"]), frame=frame)

    b.box((-1.0, -0.8, 0.85), (1.0, 0.8, 0.92), "stone", srgb(STONE["dourada"]), frame=frame)

    b.sphere((0.0, 0.05, 0.92), 0.7, "plaster", srgb(dome), scale=(1.0, 1.0, 0.95), frame=frame, segments=12)

    b.prism(mouth, -0.8, -0.5, "brick", srgb(BRICK["claro"]), frame=frame)

    b.box((-0.28, -0.68, 0.92), (0.28, -0.3, 1.3), "glow_ember", frame=frame)

    for loaf_x in (-0.12, 0.13):
        loaf(b, frame, (loaf_x, -0.72, 0.92), (0.09, 0.06, 0.045), BREAD[1], 15.0)

    b.cylinder((0.0, 0.4, 1.3), 0.13, 0.62, 8, "brick", srgb(BRICK["vermelho"]), frame=frame)
    b.cylinder((0.0, 0.4, 1.92), 0.17, 0.08, 8, "stone", srgb(STONE["dourada"]), frame=frame)

    painted(b, frame, (-0.55, -0.76, 0.1), (0.55, -0.75, 0.6), SOOT)

    for log_x, log_z in ((-0.36, 0.17), (-0.18, 0.17), (0.0, 0.17), (0.18, 0.17), (0.36, 0.17), (-0.27, 0.31), (-0.09, 0.31), (0.09, 0.31), (0.27, 0.31), (-0.18, 0.45), (0.0, 0.45), (0.18, 0.45)):
        b.cylinder((log_x, -0.79, log_z), 0.075, 0.05, 6, "wood", srgb(generator.choice((HONEY, PALE_WOOD, OAK))), frame=frame, axis="Y")

    plank(b, frame, (0.72, 0.2, 0.92), (0.98, 0.68, 0.94), PALE_WOOD)
    b.cylinder((0.85, -0.78, 0.94), 0.022, 0.98, 6, "wood", srgb(HONEY), frame=frame, axis="Y")

    plank(b, frame, (-0.98, -0.3, 0.92), (-0.72, 0.4, 0.94), OAK)

    for roll_y in (-0.2, 0.0, 0.2):
        loaf(b, frame, (-0.85, roll_y, 0.94), (0.06, 0.06, 0.04), generator.choice(BREAD))


def dough_table(b: Builder, frame: Matrix, **options) -> None:
    """Baker's worktable (2.0 x 1.0) dusted with flour: dough balls, rolling pin, mixing bowl, eggs and
    a crock and sack on the lower shelf."""
    top = options.get("tint", PALE_WOOD)

    plank(b, frame, (-1.0, -0.5, 0.84), (1.0, 0.5, 0.9), top)

    for leg_x, leg_y in itertools.product((-0.9, 0.9), (-0.4, 0.4)):
        plank(b, frame, (leg_x - 0.05, leg_y - 0.05, 0.0), (leg_x + 0.05, leg_y + 0.05, 0.84), OAK)

    plank(b, frame, (-0.9, -0.4, 0.18), (0.9, 0.4, 0.22), HONEY)

    for dust_x, dust_y, dust_size in ((-0.2, 0.0, (0.38, 0.28)), (-0.5, 0.1, (0.22, 0.18)), (0.05, -0.25, (0.2, 0.12))):
        b.sphere((dust_x, dust_y, 0.9), 1.0, "paint", srgb("F7EBD3"), scale=(*dust_size, 0.005), frame=frame, segments=8)

    for dough_x, dough_y, size in ((-0.4, -0.05, 0.13), (-0.12, 0.12, 0.1), (0.08, -0.12, 0.09)):
        loaf(b, frame, (dough_x, dough_y, 0.9), (size, size * 0.9, size * 0.55), "F5DDB0")

    b.cylinder((-0.2, -0.32, 0.93), 0.035, 0.36, 8, "wood", srgb(PALE_WOOD), frame=frame, axis="X")
    b.cylinder((-0.3, -0.32, 0.93), 0.015, 0.56, 6, "wood", srgb(HONEY), frame=frame, axis="X")

    lathe(b, [(0.08, 0.9), (0.15, 0.94), (0.19, 1.02), (0.2, 1.04)], 10, "paint", "4F8FC9", frame @ Matrix.Translation((0.5, 0.15, 0.0)))
    b.cylinder((0.5, 0.15, 1.04), 0.17, 0.008, 10, "paint", srgb("F5DDB0"), frame=frame)
    stick(b, frame, (0.48, 0.18, 1.0), (0.62, 0.28, 1.1), 0.02, PALE_WOOD)

    b.cylinder((0.75, -0.25, 0.9), 0.11, 0.07, 8, "wood", srgb(HONEY), frame=frame, uv=("band", *WOOD_LIGHT_BAND, 0.5))
    for egg_x, egg_y in ((0.72, -0.27), (0.78, -0.22), (0.76, -0.3)):
        bulb(b, frame, (egg_x, egg_y, 0.98), 0.03, 0.06, "FFF4DC")

    lathe(b, [(0.12, 0.22), (0.15, 0.3), (0.14, 0.45), (0.1, 0.5), (0.11, 0.52)], 8, "paint", "E0884A", frame @ Matrix.Translation((-0.6, 0.1, 0.0)))
    b.sphere((0.4, 0.05, 0.4), 1.0, "paint", srgb("EADBC0"), scale=(0.32, 0.2, 0.17), frame=frame, segments=8)


def bread_rack(b: Builder, frame: Matrix, **options) -> None:
    """Open bakery rack (1.4 x 0.5 x 1.9): boules, baguettes, batards and rolls on four shelves and a
    basket of standing baguettes on top."""
    generator = random.Random(options.get("seed", 0))
    wood = options.get("tint", HONEY)
    shelves = (0.25, 0.65, 1.05, 1.45)

    for post_x, post_y in itertools.product((-0.68, 0.64), (-0.23, 0.19)):
        plank(b, frame, (post_x, post_y, 0.0), (post_x + 0.04, post_y + 0.04, 1.55), OAK)

    for shelf_z in shelves:
        plank(b, frame, (-0.68, -0.23, shelf_z - 0.03), (0.68, 0.23, shelf_z), wood)

    plank(b, frame, (-0.68, 0.19, 0.3), (0.68, 0.23, 0.36), OAK)

    for boule_x in (-0.45, -0.15, 0.15, 0.45):
        loaf(b, frame, (boule_x, 0.0, shelves[0]), (0.12, 0.12, 0.08), generator.choice(BREAD), generator.uniform(0.0, 90.0))

    for baguette_y in (-0.12, -0.02, 0.08, 0.18):
        loaf(b, frame, (generator.uniform(-0.1, 0.1), baguette_y, shelves[1]), (0.3, 0.04, 0.035), BREAD[0], generator.uniform(-6.0, 6.0))

    for batard_x in (-0.48, -0.24, 0.0, 0.24, 0.48):
        loaf(b, frame, (batard_x, 0.0, shelves[2]), (0.07, 0.14, 0.06), generator.choice(BREAD))

    for roll_x, roll_y in itertools.product((-0.45, -0.15, 0.15, 0.45), (-0.08, 0.1)):
        loaf(b, frame, (roll_x + generator.uniform(-0.03, 0.03), roll_y, shelves[3]), (0.06, 0.055, 0.04), generator.choice(BREAD[:3]))

    b.cylinder((-0.35, 0.0, shelves[3]), 0.15, 0.2, 8, "wood", srgb(PALE_WOOD), top_radius=0.17, frame=frame, uv=("band", *WOOD_LIGHT_BAND, 0.4))

    for lean_x, lean_y in ((-0.06, 0.0), (0.04, 0.05), (0.03, -0.05)):
        stick(b, frame, (-0.35 + lean_x * 0.5, lean_y * 0.5, shelves[3] + 0.05), (-0.35 + lean_x * 2.5, lean_y * 2.5, 1.88), 0.06, BREAD[0], "paint")


def cake_stand(b: Builder, frame: Matrix, **options) -> None:
    """Little pedestal table with a lace cloth and a three-tier porcelain stand of cupcakes, macarons and a cake."""
    generator = random.Random(options.get("seed", 0))
    cloth = options.get("tint", "F7B6C8")
    tiers = ((0.8, 0.27), (1.03, 0.19), (1.24, 0.12))

    lathe(b, [(0.2, 0.0), (0.12, 0.05), (0.05, 0.12), (0.04, 0.45), (0.06, 0.6)], 8, "wood", HONEY, frame, uv=("band", *WOOD_LIGHT_BAND, 0.8))

    b.cylinder((0.0, 0.0, 0.56), 0.35, 0.22, 12, "paint", srgb(cloth), top_radius=0.33, frame=frame)

    b.cylinder((0.0, 0.0, 0.78), 0.012, 0.6, 6, "metal", srgb(BRASS), frame=frame)
    b.sphere((0.0, 0.0, 1.4), 0.025, "metal", srgb(BRASS), frame=frame, segments=6)

    for tier_z, radius in tiers:
        b.cylinder((0.0, 0.0, tier_z), radius * 0.6, 0.02, 12, "paint", srgb("FFF8EE"), top_radius=radius, frame=frame)

    for angle in range(0, 360, 72):
        cupcake(b, frame, 0.19 * math.cos(math.radians(angle)), 0.19 * math.sin(math.radians(angle)), 0.82, generator.choice(("F59AB5", "7FD9C0", "F2D27A")), generator.choice((FOAM, "F59AB5", "B57FE0")))

    for angle in range(15, 375, 60):
        macaron_x, macaron_y = 0.13 * math.cos(math.radians(angle)), 0.13 * math.sin(math.radians(angle))
        b.cylinder((macaron_x, macaron_y, 1.05), 0.03, 0.03, 6, "paint", srgb(generator.choice(("F59AB5", "7FD9C0", "B57FE0", "F2D27A"))), frame=frame)

    cake(b, frame, 0.0, 0.0, 1.26, 0.09, "F59AB5", FOAM)


def pastry_case(b: Builder, frame: Matrix, **options) -> None:
    """Glass pastry counter (1.8 x 0.7): panelled wooden base, glass case with cakes, tarts and cupcakes."""
    generator = random.Random(options.get("seed", 0))
    body = options.get("tint", HONEY)

    counter_body(b, frame, (-0.9, -0.35, 0.0), (0.9, 0.35, 0.75), body, PALE_WOOD, 4)

    plank(b, frame, (-0.9, -0.35, 0.75), (0.9, 0.35, 0.78), PALE_WOOD)

    painted(b, frame, (-0.86, -0.32, 0.78), (0.86, 0.32, 0.785), "FFF8EE")

    for post_x, post_y in itertools.product((-0.88, 0.85), (-0.34, 0.31)):
        plank(b, frame, (post_x, post_y, 0.78), (post_x + 0.03, post_y + 0.03, 1.1), PALE_WOOD)

    for rail_y in (-0.35, 0.29):
        plank(b, frame, (-0.9, rail_y, 1.1), (0.9, rail_y + 0.06, 1.13), PALE_WOOD)

    b.box((-0.88, -0.29, 1.11), (0.88, 0.29, 1.12), "vitrine", frame=frame)

    b.box((-0.85, -0.335, 0.78), (0.85, -0.325, 1.1), "vitrine", frame=frame)
    painted(b, frame, (-0.85, 0.05, 0.785), (0.85, 0.3, 0.9), "FFF8EE")

    for side_x in (-0.875, 0.865):
        b.box((side_x, -0.31, 0.78), (side_x + 0.01, 0.31, 1.1), "vitrine", frame=frame)

    for cake_x in (-0.55, 0.0, 0.55):
        cake(b, frame, cake_x, -0.13, 0.785, 0.1, generator.choice(CAKE[:3]), generator.choice((FOAM, "F59AB5", "7A4A32")))

    for tart_x, fruit in ((-0.6, BERRY), (-0.25, "4F5FB0"), (0.25, "E8C14F")):
        b.cylinder((tart_x, 0.17, 0.9), 0.1, 0.03, 8, "paint", srgb("D9A05B"), frame=frame)
        b.cylinder((tart_x, 0.17, 0.93), 0.085, 0.006, 8, "paint", srgb(fruit), frame=frame)

    for cupcake_x in (0.5, 0.62, 0.74):
        cupcake(b, frame, cupcake_x, 0.17, 0.9, generator.choice(("F59AB5", "7FD9C0")), generator.choice((FOAM, "B57FE0", "F59AB5")))

    painted(b, frame, (-0.1, -0.345, 0.82), (0.1, -0.335, 0.88), CREAM)


def flour_sacks(b: Builder, frame: Matrix, **options) -> None:
    """Pile of tied canvas flour sacks with blue stripes, one lying down and one open with a scoop."""
    stripe = options.get("tint", "4F8FC9")
    canvas = "E3C9A0"
    tied = [(0.15, 0.0), (0.22, 0.05), (0.24, 0.3), (0.2, 0.5), (0.09, 0.58), (0.05, 0.6), (0.09, 0.68)]
    open_sack = [(0.15, 0.0), (0.22, 0.05), (0.24, 0.32), (0.23, 0.42), (0.27, 0.46)]

    for sack_x, sack_y, degrees in ((-0.32, 0.12, 10.0), (0.05, 0.18, -20.0)):
        sack_frame = turned(frame, sack_x, sack_y, 0.0, degrees)
        lathe(b, tied, 8, "paint", canvas, sack_frame)
        b.cylinder((0.0, 0.0, 0.24), 0.245, 0.06, 8, "paint", srgb(stripe), frame=sack_frame)
        b.cylinder((0.0, 0.0, 0.57), 0.06, 0.03, 6, "paint", srgb("A8693F"), frame=sack_frame)

    lying_frame = frame @ Matrix.Translation((-0.45, -0.15, 0.2)) @ Matrix.Rotation(math.pi / 2.0, 4, "Y") @ Matrix.Diagonal((0.8, 1.0, 1.0, 1.0))
    lathe(b, tied, 8, "paint", canvas, lying_frame @ Matrix.Translation((0.0, 0.0, -0.05)))
    b.cylinder((0.0, 0.0, 0.19), 0.245, 0.06, 8, "paint", srgb(stripe), frame=lying_frame)

    open_frame = turned(frame, 0.33, -0.12, 0.0)
    lathe(b, open_sack, 8, "paint", canvas, open_frame)
    b.cylinder((0.0, 0.0, 0.2), 0.245, 0.06, 8, "paint", srgb(stripe), frame=open_frame)
    b.sphere((0.0, 0.0, 0.42), 0.22, "paint", srgb("FBF6EC"), scale=(1.0, 1.0, 0.45), frame=open_frame, segments=8)
    stick(b, open_frame, (0.04, -0.02, 0.45), (0.14, -0.1, 0.62), 0.025, PALE_WOOD)
    lathe(b, [(0.0, 0.0), (0.06, 0.02), (0.07, 0.07)], 6, "metal", BRASS, open_frame @ Matrix.Translation((0.02, 0.0, 0.43)))


def cafe_table_set(b: Builder, frame: Matrix, **options) -> None:
    """Small round café table with a pink cloth, teapot, cups and a flower vase, and two painted chairs."""
    paint = options.get("tint", "7FC4A8")

    lathe(b, [(0.22, 0.0), (0.06, 0.04), (0.035, 0.1), (0.035, 0.7)], 8, "metal", "3A2E32", frame)

    b.cylinder((0.0, 0.0, 0.7), 0.35, 0.04, 12, "wood", srgb(PALE_WOOD), frame=frame, uv=("band", *WOOD_LIGHT_BAND, 0.8))

    b.cylinder((0.0, 0.0, 0.56), 0.37, 0.19, 12, "paint", srgb("F7C6D4"), top_radius=0.355, frame=frame)

    for degrees in (90.0, 270.0):
        chair(b, chair_around(frame, 0.58, degrees), paint, FOAM, "paint")

    lathe(b, [(0.05, 0.75), (0.08, 0.79), (0.08, 0.84), (0.05, 0.87), (0.015, 0.9)], 8, "paint", FOAM, frame @ Matrix.Translation((0.0, 0.08, 0.0)))
    stick(b, frame, (0.07, 0.08, 0.8), (0.14, 0.08, 0.86), 0.02, FOAM, "paint")

    for cup_x in (-0.18, 0.18):
        b.cylinder((cup_x, -0.08, 0.74), 0.06, 0.01, 8, "paint", srgb(FOAM), frame=frame)
        b.cylinder((cup_x, -0.08, 0.75), 0.03, 0.045, 6, "paint", srgb("F59AB5"), top_radius=0.04, frame=frame)

    b.cylinder((-0.1, 0.17, 0.74), 0.03, 0.1, 6, "paint", srgb("4F8FC9"), top_radius=0.02, frame=frame)

    for petal_x, petal_y, color in ((-0.1, 0.17, "F2D27A"), (-0.13, 0.15, "F59AB5"), (-0.07, 0.19, "C9483B")):
        stick(b, frame, (-0.1, 0.17, 0.84), (petal_x, petal_y, 0.91), 0.008, "3F8A50", "paint")
        bulb(b, frame, (petal_x, petal_y, 0.92), 0.022, 0.03, color)


# ---------- ceiling-hung (z = 0 at the ceiling mount, growing down) ----------

def hanging_pots(b: Builder, frame: Matrix, **options) -> None:
    """Iron pot rack on two chains 0.5 m under the ceiling: copper pans and pots on S-hooks."""
    copper = options.get("tint", COPPER)
    rack_z = -0.5
    frame = frame @ Matrix.Translation((0.0, -0.05, 0.0))

    for chain_x in (-0.55, 0.55):
        stick(b, frame, (chain_x, -0.15, rack_z), (chain_x, 0.0, 0.0), 0.02, WARM_IRON, "metal")
        stick(b, frame, (chain_x, 0.15, rack_z), (chain_x, 0.0, 0.0), 0.02, WARM_IRON, "metal")

    for rail_y in (-0.15, 0.15):
        b.cylinder((-0.6, rail_y, rack_z), 0.015, 1.2, 6, "metal", srgb(WARM_IRON), frame=frame, axis="X")

    for end_x in (-0.6, 0.6):
        b.box((end_x - 0.015, -0.16, rack_z - 0.015), (end_x + 0.015, 0.16, rack_z + 0.015), "metal", srgb(WARM_IRON), frame=frame)

    for pan_x, radius in ((-0.4, 0.14), (0.38, 0.11)):
        b.box((pan_x - 0.006, -0.156, rack_z - 0.1), (pan_x + 0.006, -0.144, rack_z), "metal", srgb(WARM_IRON), frame=frame)
        stick(b, frame, (pan_x, -0.15, rack_z - 0.08), (pan_x, -0.15, rack_z - 0.3), 0.025, OAK)
        b.cylinder((pan_x, -0.17, rack_z - 0.3 - radius), radius, 0.04, 10, "metal", srgb(copper), frame=frame, axis="Y")

    for pot_x, radius in ((-0.1, 0.12), (0.15, 0.09)):
        lathe(b, [(radius * 0.8, -0.42 - radius * 1.5), (radius, -0.42 - radius * 1.3), (radius, -0.42), (radius * 1.08, -0.41)], 10, "metal", copper, frame @ Matrix.Translation((pot_x, 0.15, rack_z)))
        stick(b, frame, (pot_x - radius, 0.15, rack_z - 0.42), (pot_x, 0.15, rack_z - 0.05), 0.012, WARM_IRON, "metal")
        stick(b, frame, (pot_x + radius, 0.15, rack_z - 0.42), (pot_x, 0.15, rack_z - 0.05), 0.012, WARM_IRON, "metal")

    stick(b, frame, (0.55, 0.15, rack_z), (0.55, 0.15, rack_z - 0.4), 0.02, BRASS, "metal")
    lathe(b, [(0.0, -0.5), (0.06, -0.48), (0.07, -0.43)], 8, "metal", BRASS, frame @ Matrix.Translation((0.55, 0.15, rack_z)))


def garlic_strings(b: Builder, frame: Matrix, **options) -> None:
    """Pole hung on ropes 0.3 m under the ceiling with a garlic braid, chilli and onion strings and
    herb bundles drying."""
    generator = random.Random(options.get("seed", 0))
    pole_z = -0.3
    strings = {"garlic": (-0.4, "F5EBD8", 8, 0.045), "chilli": (-0.12, "D9302A", 11, 0.022), "onion": (0.15, "D98A3D", 6, 0.05), "garlic_small": (0.42, "F5EBD8", 6, 0.04)}

    for rope_x in (-0.5, 0.5):
        stick(b, frame, (rope_x, 0.0, pole_z), (rope_x, 0.0, 0.0), 0.015, "C9A85B", "paint")

    b.cylinder((-0.58, 0.0, pole_z), 0.03, 1.16, 8, "wood", srgb(HONEY), frame=frame, axis="X")

    for string_x, color, count, radius in strings.values():
        stick(b, frame, (string_x, 0.0, pole_z), (string_x, 0.0, pole_z - 0.08 - count * radius * 1.7), 0.02, "C9A85B", "paint")
        chilli = radius < 0.03

        for index in range(count):
            side = 1.0 if index % 2 else -1.0
            item_x = string_x + side * radius * 0.7
            item_z = pole_z - 0.1 - index * radius * 1.7
            item_y = generator.uniform(-0.03, 0.03)

            if chilli:
                b.cylinder((item_x, item_y, item_z - 0.09), 0.0, 0.09, 4, "paint", srgb(color), top_radius=0.02, frame=frame)
            else:
                bulb(b, frame, (item_x, item_y, item_z), radius, radius * 1.6, color)

    for herb_x, herb_color in ((-0.26, "3F8A50"), (0.29, "7FC46A")):
        b.cylinder((herb_x, 0.0, pole_z - 0.32), 0.0, 0.26, 6, "paint", srgb(herb_color), top_radius=0.07, frame=frame)
        b.cylinder((herb_x, 0.0, pole_z - 0.08), 0.02, 0.06, 6, "paint", srgb("A8693F"), frame=frame)


def jam_shelf(b: Builder, frame: Matrix, **options) -> None:
    """Wall shelf (1.15 to 1.95 m) with a scalloped crest and two boards of jam jars under cloth caps."""
    generator = random.Random(options.get("seed", 0))
    wood = options.get("tint", HONEY)
    boards = (1.2, 1.58)
    caps = ("C9483B", CREAM, "4F8FC9", "F59AB5")

    plank(b, frame, (-0.6, 0.1, 1.15), (0.6, 0.125, 1.8), OAK)

    b.prism([(-0.6, 1.8), (0.6, 1.8), (0.6, 1.86), (0.3, 1.93), (0.0, 1.95), (-0.3, 1.93), (-0.6, 1.86)], 0.1, 0.125, "wood", srgb(wood), frame=frame, uv=("band", *WOOD_LIGHT_BAND, 1.0))

    for board_z, bracket_x in itertools.product(boards, (-0.5, 0.5)):
        b.side_prism([(0.1, board_z - 0.03), (-0.04, board_z - 0.03), (0.1, board_z - 0.15)], bracket_x - 0.02, bracket_x + 0.02, "wood", srgb(OAK), frame=frame)

    for board_z in boards:
        plank(b, frame, (-0.6, -0.125, board_z - 0.03), (0.6, 0.1, board_z), wood)

    for board_z, jar_x in itertools.product(boards, (-0.45, -0.27, -0.09, 0.09, 0.27, 0.45)):
        height = generator.uniform(0.1, 0.15)
        b.cylinder((jar_x, 0.0, board_z), 0.055, height, 6, "paint", srgb(generator.choice(JAM)), frame=frame)
        b.cylinder((jar_x, 0.0, board_z + height), 0.068, 0.03, 6, "paint", srgb(generator.choice(caps)), top_radius=0.045, frame=frame)


# ---------- inn ----------

def key_board(b: Builder, frame: Matrix, **options) -> None:
    """Inn key board on the wall (1.4 to 2.1 m): twelve hooks with brass keys and coloured room tags,
    a few rooms taken; a crescent moon on the crest."""
    generator = random.Random(options.get("seed", 0))
    tags = ("C9483B", "4F8FC9", "3F8A50", "E8C14F")

    plank(b, frame, (-0.5, 0.0, 1.4), (0.5, 0.05, 2.0), OAK)

    plank(b, frame, (-0.45, -0.01, 1.45), (0.45, 0.0, 1.95), HONEY)

    b.prism(arch(0.3, 2.0, 0.1, 6), 0.0, 0.05, "wood", srgb(OAK), frame=frame)

    b.cylinder((0.0, -0.01, 2.04), 0.045, 0.01, 8, "metal", srgb(BRASS), frame=frame, axis="Y")

    for (row_z, key_x), tag in zip(itertools.product((1.88, 1.71, 1.54), (-0.33, -0.11, 0.11, 0.33)), itertools.cycle(tags)):
        b.box((key_x - 0.008, -0.03, row_z - 0.008), (key_x + 0.008, -0.01, row_z + 0.008), "metal", srgb(BRASS), frame=frame)

        if generator.random() < 0.25:
            continue

        b.box((key_x - 0.02, -0.03, row_z - 0.05), (key_x + 0.02, -0.02, row_z - 0.01), "metal", srgb(BRASS), frame=frame)
        b.box((key_x - 0.006, -0.03, row_z - 0.11), (key_x + 0.006, -0.02, row_z - 0.05), "metal", srgb(BRASS), frame=frame)
        b.box((key_x - 0.035, -0.025, row_z - 0.13), (key_x - 0.006, -0.015, row_z - 0.08), "paint", srgb(tag), frame=frame)


def reception_desk(b: Builder, frame: Matrix, **options) -> None:
    """Inn reception: panelled desk with the guest book, quill, bell, candle and a potted plant,
    and the key board on the wall behind the clerk."""
    body = options.get("tint", OAK)

    counter_body(b, frame, (-1.15, -0.76, 0.0), (1.15, -0.15, 1.0), body, HONEY, 5)

    plank(b, frame, (-1.2, -0.8, 1.0), (1.2, -0.1, 1.05), HONEY)

    painted(b, frame, (-0.5, -0.6, 1.05), (-0.1, -0.32, 1.06), "8E2F3A")
    b.box((-0.48, -0.58, 1.06), (-0.31, -0.34, 1.075), "paint", srgb(FOAM), frame=frame)
    b.box((-0.29, -0.58, 1.06), (-0.12, -0.34, 1.075), "paint", srgb(FOAM), frame=frame)

    b.cylinder((0.05, -0.45, 1.05), 0.03, 0.05, 6, "paint", srgb(SOOT), frame=frame)
    stick(b, frame, (0.05, -0.45, 1.08), (0.1, -0.4, 1.25), 0.02, FOAM, "paint")

    lathe(b, [(0.06, 1.05), (0.055, 1.07), (0.045, 1.1), (0.02, 1.12), (0.008, 1.14)], 8, "metal", BRASS, frame @ Matrix.Translation((0.45, -0.6, 0.0)))

    candle(b, frame, 0.85, -0.35, 1.05, 0.14, holder=True)

    lathe(b, [(0.06, 1.05), (0.09, 1.17), (0.1, 1.19)], 8, "paint", "C9683B", frame @ Matrix.Translation((-0.95, -0.4, 0.0)))
    for leaf_x, leaf_y, leaf_z in ((-0.95, -0.4, 1.28), (-1.02, -0.36, 1.24), (-0.89, -0.45, 1.23)):
        bulb(b, frame, (leaf_x, leaf_y, leaf_z), 0.07, 0.12, "3F8A50")

    key_board(b, frame @ Matrix.Translation((0.0, 0.75, 0.0)), seed=options.get("seed", 0))


def couch(b: Builder, frame: Matrix, width: float, fabric: str, seats: int, wings: bool) -> None:
    """Upholstered seat facing -Y with rolled arms, seat cushions, back and turned feet (armchair and sofa)."""
    half = width / 2.0
    cushion_width = (width - 0.3) / seats

    for foot_x, foot_y in itertools.product((-half + 0.08, half - 0.08), (-0.33, 0.33)):
        b.cylinder((foot_x, foot_y, 0.0), 0.035, 0.12, 6, "wood", srgb(OAK), top_radius=0.045, frame=frame)

    painted(b, frame, (-half + 0.08, -0.38, 0.12), (half - 0.08, 0.38, 0.4), fabric)

    painted(b, frame, (-half + 0.12, 0.22, 0.4), (half - 0.12, 0.4, 0.98 if wings else 0.88), fabric)

    for side in (-1.0, 1.0):
        painted(b, frame, (min(side * half, side * (half - 0.15)), -0.38, 0.12), (max(side * half, side * (half - 0.15)), 0.36, 0.6), fabric)
        b.cylinder((side * (half - 0.075), -0.42, 0.6), 0.085, 0.78, 8, "paint", srgb(fabric), frame=frame, axis="Y")

        if wings:
            b.hull([(side * (half - 0.15), 0.38, 0.62), (side * half, 0.38, 0.62), (side * (half - 0.15), 0.38, 1.04), (side * half, 0.38, 1.0), (side * (half - 0.15), 0.1, 0.62), (side * half, 0.12, 0.62), (side * (half - 0.15), 0.18, 0.95), (side * half, 0.2, 0.93)], "paint", srgb(fabric), frame=frame)

    for index in range(seats):
        left = -half + 0.15 + index * cushion_width
        painted(b, frame, (left + 0.01, -0.41, 0.4), (left + cushion_width - 0.01, 0.22, 0.5), fabric)

    b.cylinder((-half + 0.12, 0.31, 0.95 if wings else 0.85), 0.05, width - 0.24, 8, "paint", srgb(fabric), frame=frame, axis="X")

    painted(b, frame, (-half + 0.08, -0.395, 0.14), (half - 0.08, -0.38, 0.18), BRASS)


def armchair(b: Builder, frame: Matrix, **options) -> None:
    """Wingback armchair in wine velvet with a gold cushion."""
    couch(b, frame, 0.9, options.get("tint", "A83A48"), 1, True)

    b.sphere((0.18, 0.12, 0.62), 1.0, "paint", srgb("E8C14F"), scale=(0.13, 0.06, 0.12), frame=frame, segments=6)


def sofa(b: Builder, frame: Matrix, **options) -> None:
    """Three-seat sofa in forest green with rolled arms and two throw pillows."""
    couch(b, frame, 2.0, options.get("tint", "3F7A55"), 3, False)

    for pillow_x, color in ((-0.65, "E8C14F"), (0.62, "C9483B")):
        b.sphere((pillow_x, 0.12, 0.64), 1.0, "paint", srgb(color), scale=(0.16, 0.07, 0.14), frame=frame, segments=6)


def bed_frame(b: Builder, frame: Matrix, width: float, length: float, head_top: float, blanket: str) -> None:
    """Bed with head at +Y: rails, arched headboard, footboard, mattress, blanket with turned-down sheet and pillows."""
    half = width / 2.0
    head_y = length / 2.0

    for side in (-1.0, 1.0):
        plank(b, frame, (min(side * half, side * (half - 0.04)), -head_y + 0.05, 0.2), (max(side * half, side * (half - 0.04)), head_y - 0.05, 0.38), OAK)

    rise = half * 0.4
    headboard = [(-half, 0.0), (half, 0.0), *arch(half, head_top - rise, rise)]
    pillows = [(-half / 2.0, half / 2.0 - 0.04), (half / 2.0, half / 2.0 - 0.04)] if width > 1.2 else [(0.0, half - 0.12)]

    b.prism(headboard, head_y - 0.06, head_y, "wood", srgb(HONEY), frame=frame, uv=("band", *WOOD_LIGHT_BAND, 1.0))

    plank(b, frame, (-half, -head_y, 0.0), (half, -head_y + 0.06, 0.62), HONEY)
    plank(b, frame, (-half, -head_y, 0.62), (half, -head_y + 0.06, 0.67), OAK)

    painted(b, frame, (-half + 0.02, -head_y + 0.06, 0.3), (half - 0.02, head_y - 0.06, 0.55), FOAM)

    painted(b, frame, (-half, -head_y + 0.07, 0.32), (half, head_y * 0.35, 0.58), blanket)

    painted(b, frame, (-half + 0.01, head_y * 0.32, 0.55), (half - 0.01, head_y * 0.45, 0.6), CREAM)

    for pillow_x, pillow_half in pillows:
        b.sphere((pillow_x, head_y - 0.28, 0.62), 1.0, "paint", srgb("FFFFFF"), scale=(pillow_half, 0.16, 0.07), frame=frame, segments=6)


def bed_canopy(b: Builder, frame: Matrix, **options) -> None:
    """Inn canopy bed (2.0 x 1.6): four posts, fabric roof with a gold-trimmed valance and tied curtains."""
    fabric = options.get("tint", "8E2F5A")
    half_x, half_y, top = 0.82, 1.02, 2.3

    bed_frame(b, frame, 1.6, 2.0, 1.25, fabric)

    for post_x, post_y in itertools.product((-half_x, half_x), (-half_y + 0.04, half_y - 0.04)):
        b.cylinder((post_x, post_y, 0.0), 0.045, top, 8, "wood", srgb(OAK), frame=frame, uv=("band", *WOOD_LIGHT_BAND, 1.0))

    plank(b, frame, (-half_x - 0.03, -half_y, top - 0.06), (half_x + 0.03, half_y, top), OAK)

    for minimum, maximum in (((-half_x - 0.03, -half_y - 0.0, top - 0.32), (half_x + 0.03, -half_y + 0.02, top)), ((-half_x - 0.03, -half_y, top - 0.32), (-half_x - 0.01, half_y, top)), ((half_x + 0.01, -half_y, top - 0.32), (half_x + 0.03, half_y, top))):
        painted(b, frame, minimum, maximum, fabric)

    for minimum, maximum in (((-half_x - 0.04, -half_y - 0.01, top - 0.34), (half_x + 0.04, -half_y + 0.01, top - 0.3)), ((-half_x - 0.04, -half_y, top - 0.34), (-half_x - 0.02, half_y, top - 0.3)), ((half_x + 0.02, -half_y, top - 0.34), (half_x + 0.04, half_y, top - 0.3))):
        painted(b, frame, minimum, maximum, BRASS)

    painted(b, frame, (-half_x, -half_y, top), (half_x, half_y, top + 0.05), fabric)

    for curtain_x, curtain_y in itertools.product((-half_x, half_x), (-half_y + 0.2, half_y - 0.2)):
        inward = -0.06 if curtain_x > 0.0 else 0.06
        b.hull([(curtain_x, curtain_y - 0.18, top - 0.32), (curtain_x, curtain_y + 0.18, top - 0.32), (curtain_x + inward, curtain_y, top - 0.32), (curtain_x, curtain_y - 0.05, 1.1), (curtain_x, curtain_y + 0.05, 1.1), (curtain_x + inward * 0.5, curtain_y, 1.1)], "paint", srgb(fabric), frame=frame)
        b.hull([(curtain_x, curtain_y - 0.05, 1.1), (curtain_x, curtain_y + 0.05, 1.1), (curtain_x + inward * 0.5, curtain_y, 1.1), (curtain_x, curtain_y - 0.12, 0.02), (curtain_x, curtain_y + 0.12, 0.02), (curtain_x + inward, curtain_y, 0.02)], "paint", srgb(fabric), frame=frame)
        painted(b, frame, (curtain_x - 0.05, curtain_y - 0.07, 1.06), (curtain_x + 0.05, curtain_y + 0.07, 1.12), BRASS)


def bed_single(b: Builder, frame: Matrix, **options) -> None:
    """Single bed (1.0 x 2.0) with a patchwork quilt."""
    generator = random.Random(options.get("seed", 0))
    quilt = options.get("tint", "4F8FC9")

    bed_frame(b, frame, 1.0, 2.0, 1.0, quilt)

    for patch_x, patch_y in itertools.product((-0.25, 0.1), (-0.75, -0.35, 0.0)):
        painted(b, frame, (patch_x, patch_y, 0.58), (patch_x + 0.18, patch_y + 0.22, 0.585), generator.choice(GOODS_PALETTE[:6]))


def nightstand(b: Builder, frame: Matrix, **options) -> None:
    """Bedside table with a drawer, a candle in a brass dish and a book."""
    wood = options.get("tint", HONEY)

    for leg_x, leg_y in itertools.product((-0.2, 0.2), (-0.17, 0.17)):
        b.box((leg_x - 0.025, leg_y - 0.025, 0.0), (leg_x + 0.025, leg_y + 0.025, 0.1), "wood", srgb(OAK), frame=frame)

    plank(b, frame, (-0.23, -0.19, 0.1), (0.23, 0.2, 0.55), OAK)

    plank(b, frame, (-0.25, -0.21, 0.55), (0.25, 0.21, 0.59), wood)

    plank(b, frame, (-0.2, -0.2, 0.38), (0.2, -0.19, 0.51), wood)

    b.box((-0.02, -0.21, 0.43), (0.02, -0.2, 0.46), "metal", srgb(BRASS), frame=frame)

    candle(b, frame, 0.1, 0.05, 0.59, 0.1, holder=True)

    painted(b, frame, (-0.2, -0.12, 0.59), (-0.03, 0.1, 0.63), "6C5BB8")


def wardrobe(b: Builder, frame: Matrix, **options) -> None:
    """Two-door wardrobe with painted door panels (a little flower each), a bottom drawer, brass handles
    and a stepped crown."""
    body = OAK
    panels = options.get("tint", "5E9C94")

    for foot_x in (-0.55, 0.55):
        plank(b, frame, (foot_x - 0.05, -0.25, 0.0), (foot_x + 0.05, 0.28, 0.1), WALNUT, dark=True)

    plank(b, frame, (-0.6, -0.27, 0.1), (0.6, 0.3, 1.95), body)

    plank(b, frame, (-0.56, -0.285, 0.15), (0.56, -0.27, 0.42), HONEY)

    for door_x, (panel_bottom, panel_top) in itertools.product((-0.285, 0.285), ((0.56, 1.1), (1.2, 1.8))):
        painted(b, frame, (door_x - 0.2, -0.295, panel_bottom), (door_x + 0.2, -0.285, panel_top), panels)
        middle = (panel_bottom + panel_top) / 2.0
        painted(b, frame, (door_x - 0.05, -0.3, middle - 0.05), (door_x + 0.05, -0.295, middle + 0.05), "F2D27A")
        painted(b, frame, (door_x - 0.02, -0.302, middle - 0.02), (door_x + 0.02, -0.3, middle + 0.02), "C9483B")

    for door_x in (-0.285, 0.285):
        plank(b, frame, (door_x - 0.27, -0.285, 0.47), (door_x + 0.27, -0.27, 1.9), HONEY)

    for handle_x in (-0.04, 0.04):
        b.box((handle_x - 0.01, -0.3, 1.05), (handle_x + 0.01, -0.285, 1.25), "metal", srgb(BRASS), frame=frame)

    for knob_x in (-0.3, 0.3):
        b.box((knob_x - 0.025, -0.3, 0.27), (knob_x + 0.025, -0.285, 0.3), "metal", srgb(BRASS), frame=frame)

    b.side_prism([(-0.3, 1.95), (0.3, 1.95), (0.3, 2.15), (-0.3, 2.15), (-0.3, 2.08), (-0.27, 2.02), (-0.27, 1.98)], -0.6, 0.6, "wood", srgb(HONEY), frame=frame, uv=("band", *WOOD_LIGHT_BAND, 1.0))


def bathtub(b: Builder, frame: Matrix, **options) -> None:
    """Oval wooden tub with brass hoops, soapy water, a towel over the rim and a little wooden duck."""
    oval = frame @ Matrix.Diagonal((1.0, 0.5, 1.0, 1.0))
    staves = options.get("tint", HONEY)

    for foot_x, foot_y in itertools.product((-0.55, 0.55), (-0.22, 0.22)):
        b.box((foot_x - 0.05, foot_y - 0.05, 0.0), (foot_x + 0.05, foot_y + 0.05, 0.06), "wood", srgb(OAK), frame=frame)

    lathe(b, [(0.7, 0.06), (0.76, 0.14), (0.79, 0.7), (0.73, 0.7), (0.7, 0.18)], 12, "wood", staves, oval, uv=("band", *WOOD_LIGHT_BAND, 0.8))

    for hoop_z in (0.16, 0.42):
        b.cylinder((0.0, 0.0, hoop_z), 0.775, 0.05, 12, "metal", srgb(BRASS), frame=oval)

    b.cylinder((0.0, 0.0, 0.5), 0.72, 0.04, 12, "water", srgb("8FD8FF"), frame=oval)

    for bubble_x, bubble_y, radius in ((-0.4, 0.1, 0.07), (-0.3, -0.12, 0.06), (-0.5, -0.05, 0.05), (-0.2, 0.05, 0.05), (0.35, 0.15, 0.05)):
        bulb(b, frame, (bubble_x, bubble_y, 0.55), radius, radius, "FFFFFF")

    bulb(b, frame, (0.25, -0.05, 0.56), 0.05, 0.06, "F2C14F")
    bulb(b, frame, (0.21, -0.05, 0.62), 0.03, 0.05, "F2C14F")
    b.box((0.16, -0.06, 0.62), (0.19, -0.04, 0.635), "paint", srgb("E0884A"), frame=frame)

    painted(b, frame, (0.45, -0.4, 0.68), (0.7, -0.33, 0.72), "F7C6D4")
    painted(b, frame, (0.45, -0.41, 0.38), (0.7, -0.39, 0.72), "F7C6D4")


def washstand(b: Builder, frame: Matrix, **options) -> None:
    """Washstand with a porcelain basin and pitcher, folded towels below, a towel rail and a mirror above."""
    wood = options.get("tint", HONEY)

    for leg_x, leg_y in itertools.product((-0.32, 0.32), (-0.17, 0.17)):
        plank(b, frame, (leg_x - 0.025, leg_y - 0.025, 0.0), (leg_x + 0.025, leg_y + 0.025, 0.78), OAK)

    plank(b, frame, (-0.35, -0.2, 0.78), (0.35, 0.2, 0.82), wood)

    plank(b, frame, (-0.32, -0.17, 0.2), (0.32, 0.17, 0.23), wood)

    plank(b, frame, (-0.35, 0.18, 0.82), (0.35, 0.22, 1.0), wood)

    lathe(b, [(0.08, 0.82), (0.14, 0.86), (0.18, 0.92), (0.2, 0.93)], 10, "paint", FOAM, frame @ Matrix.Translation((-0.05, -0.02, 0.0)))
    b.cylinder((-0.05, -0.02, 0.905), 0.165, 0.01, 10, "water", srgb("8FD8FF"), frame=frame)

    lathe(b, [(0.06, 0.82), (0.075, 0.9), (0.05, 1.0), (0.055, 1.06)], 8, "paint", "4F8FC9", frame @ Matrix.Translation((0.22, 0.02, 0.0)))
    stick(b, frame, (0.28, 0.02, 0.88), (0.29, 0.02, 1.02), 0.02, "4F8FC9", "paint")

    for towel_z, color in ((0.23, CREAM), (0.29, "F7C6D4")):
        painted(b, frame, (-0.2, -0.12, towel_z), (0.15, 0.12, towel_z + 0.06), color)

    stick(b, frame, (-0.37, -0.15, 0.7), (-0.37, 0.15, 0.7), 0.02, BRASS, "metal")
    painted(b, frame, (-0.385, -0.12, 0.42), (-0.355, 0.12, 0.72), "7FC4A8")

    plank(b, frame, (-0.25, 0.17, 1.15), (0.25, 0.22, 1.7), OAK)
    painted(b, frame, (-0.2, 0.165, 1.2), (0.2, 0.17, 1.65), "BFE0EE")
    stick(b, frame, (-0.12, 0.164, 1.35), (0.02, 0.164, 1.6), 0.03, FOAM, "paint")


def luggage_pile(b: Builder, frame: Matrix, **options) -> None:
    """Travellers' luggage: domed trunk with brass straps, two suitcases, a striped hat box and a bedroll."""
    leather = options.get("tint", "8B4A2F")

    plank(b, frame, (-0.5, -0.02, 0.0), (0.3, 0.33, 0.36), leather)

    b.side_prism([(-0.02, 0.36), (0.33, 0.36), (0.3, 0.44), (0.22, 0.49), (0.09, 0.49), (0.01, 0.44)], -0.5, 0.3, "wood", srgb(leather), frame=frame, uv=("band", *WOOD_LIGHT_BAND, 1.0))

    for strap_x in (-0.35, 0.15):
        b.box((strap_x - 0.025, -0.03, 0.0), (strap_x + 0.025, 0.34, 0.37), "metal", srgb(BRASS), frame=frame)
        b.side_prism([(-0.03, 0.36), (0.34, 0.36), (0.31, 0.45), (0.22, 0.5), (0.09, 0.5), (0.0, 0.45)], strap_x - 0.025, strap_x + 0.025, "metal", srgb(BRASS), frame=frame)

    b.box((-0.14, -0.035, 0.28), (-0.06, -0.02, 0.36), "metal", srgb(BRASS), frame=frame)

    painted(b, frame, (-0.5, -0.33, 0.0), (0.12, -0.06, 0.18), "C08A55")
    painted(b, frame, (-0.3, -0.34, 0.0), (-0.26, -0.05, 0.185), "6B3A26")
    painted(b, frame, (-0.04, -0.34, 0.0), (0.0, -0.05, 0.185), "6B3A26")

    painted(b, frame, (-0.45, -0.3, 0.18), (0.02, -0.08, 0.32), "3E6A9A")
    b.box((-0.25, -0.31, 0.32), (-0.18, -0.29, 0.36), "metal", srgb(BRASS), frame=frame)

    b.cylinder((0.38, -0.12, 0.0), 0.17, 0.24, 10, "paint", srgb("F59AB5"), frame=frame)
    b.cylinder((0.38, -0.12, 0.15), 0.175, 0.04, 10, "paint", srgb(FOAM), frame=frame)
    b.cylinder((0.38, -0.12, 0.24), 0.18, 0.04, 10, "paint", srgb(FOAM), frame=frame)

    b.cylinder((-0.42, 0.15, 0.6), 0.1, 0.62, 8, "paint", srgb("3F8A50"), frame=frame, axis="X")
    for buckle_x in (-0.3, 0.05):
        b.cylinder((buckle_x, 0.15, 0.6), 0.105, 0.03, 8, "paint", srgb("6B3A26"), frame=frame, axis="X")


def parasol_table(b: Builder, frame: Matrix, **options) -> None:
    """Outdoor café table with two painted chairs under a red-and-cream striped parasol (2 m wide)."""
    stripes = (options.get("tint", "C9483B"), FOAM)
    panels = 8
    rim_z, apex_z, radius = 2.05, 2.36, 0.98

    lathe(b, [(0.25, 0.0), (0.06, 0.04), (0.035, 0.1), (0.035, 0.72)], 8, "metal", "3A2E32", frame)

    b.cylinder((0.0, 0.0, 0.72), 0.4, 0.04, 12, "wood", srgb(PALE_WOOD), frame=frame, uv=("band", *WOOD_LIGHT_BAND, 0.8))

    for degrees in (90.0, 270.0):
        chair(b, chair_around(frame, 0.62, degrees), stripes[0], FOAM, "paint")

    b.cylinder((0.0, 0.0, 0.76), 0.025, apex_z - 0.76, 8, "wood", srgb(HONEY), frame=frame)

    b.sphere((0.0, 0.0, apex_z + 0.04), 0.04, "metal", srgb(BRASS), frame=frame, segments=6)

    for index in range(panels):
        start, end = 2.0 * math.pi * index / panels, 2.0 * math.pi * (index + 1) / panels
        rim = [(radius * math.cos(angle), radius * math.sin(angle)) for angle in (start, end)]
        color = srgb(stripes[index % 2])
        b.hull([(0.0, 0.0, apex_z), (0.0, 0.0, apex_z - 0.03), *[(x, y, rim_z) for x, y in rim], *[(x * 0.97, y * 0.97, rim_z - 0.02) for x, y in rim]], "paint", color, frame=frame)
        b.hull([*[(x, y, rim_z) for x, y in rim], *[(x, y, rim_z - 0.12) for x, y in rim], *[(x * 0.98, y * 0.98, rim_z - 0.12) for x, y in rim]], "paint", srgb(stripes[(index + 1) % 2]), frame=frame)

    mug(b, frame, 0.15, -0.15, 0.76, foam=False, color=PALE_WOOD)
    b.cylinder((-0.15, 0.1, 0.76), 0.05, 0.16, 8, "vitrine", frame=frame)
    b.cylinder((-0.15, 0.1, 0.765), 0.045, 0.1, 8, "paint", srgb("F2D27A"), frame=frame)


LIGHT_FIRE = "FF8A3D"

# ---------- tavern architecture and dressing ----------

def tavern_booth(b: Builder, frame: Matrix, **options) -> None:
    """Wall booth, 2.2 m wide and 1.5 deep: two high-backed padded benches facing each other over a small table,
    a panelled end screen against the wall with a hanging lamp bracket, and a padded back on each bench."""
    wood = options.get("tint", OAK)
    cushion = options.get("cushion", "A83A48")

    plank(b, frame, (-1.1, 0.6, 0.0), (1.1, 0.7, 1.55), WALNUT, dark=True)

    for panel_x in (-0.75, 0.0, 0.75):
        plank(b, frame, (panel_x - 0.3, 0.55, 0.3), (panel_x + 0.3, 0.6, 1.2), HONEY)
        plank(b, frame, (panel_x - 0.26, 0.545, 0.34), (panel_x + 0.26, 0.55, 1.16), OAK)

    plank(b, frame, (-1.12, 0.55, 1.45), (1.12, 0.72, 1.55), HONEY)

    for side in (-1.0, 1.0):
        bench_x = side * 0.95
        outline = [(-0.6, 0.0), (0.62, 0.0), (0.62, 1.05), (0.5, 1.3), (0.2, 1.42), (-0.2, 1.46), (-0.5, 1.42), (-0.6, 1.2)]

        b.side_prism(outline, bench_x + side * 0.08, bench_x + side * 0.14, "wood", srgb(WALNUT), frame=frame, uv=("band", *WOOD_DARK_BAND, 1.0))
        plank(b, frame, (bench_x - 0.14, -0.6, 0.4), (bench_x + 0.14, 0.6, 0.45), wood)
        painted(b, frame, (bench_x - 0.12, -0.58, 0.45), (bench_x + 0.12, 0.58, 0.5), cushion)
        plank(b, frame, (bench_x + side * 0.1 - 0.015, -0.6, 0.45), (bench_x + side * 0.1 + 0.015, 0.6, 1.2), HONEY)
        painted(b, frame, (bench_x + side * 0.085 - 0.02, -0.56, 0.52), (bench_x + side * 0.085, 0.56, 1.05), cushion)
        plank(b, frame, (bench_x - 0.14, -0.6, 0.0), (bench_x + 0.14, -0.55, 0.4), WALNUT, dark=True)
        plank(b, frame, (bench_x - 0.14, 0.55, 0.0), (bench_x + 0.14, 0.6, 0.4), WALNUT, dark=True)

    for leg_x in (-0.32, 0.32):
        lathe(b, [(0.045, 0.0), (0.06, 0.05), (0.04, 0.2), (0.05, 0.4), (0.04, 0.6), (0.05, 0.7)], 6, "wood", WALNUT, frame @ Matrix.Translation((leg_x, 0.0, 0.0)), uv=("band", *WOOD_DARK_BAND, 1.0))

    plank(b, frame, (-0.45, -0.3, 0.72), (0.45, 0.3, 0.77), HONEY)
    plank(b, frame, (-0.47, -0.32, 0.755), (0.47, 0.32, 0.77), OAK)
    mug(b, frame, -0.15, -0.1, 0.77)
    mug(b, frame, 0.2, 0.1, 0.77, foam=False)
    candle(b, frame, 0.0, 0.0, 0.77, 0.1, holder=True)
    plate(b, frame, 0.2, -0.12, 0.77, 0.1, "E8C14F")
    stick(b, frame, (0.0, 0.58, 1.2), (0.0, 0.2, 1.35), 0.03, WARM_IRON, "metal")
    b.cylinder((0.0, 0.2, 1.32), 0.05, 0.1, 6, "metal", srgb(BRASS), frame=frame)
    flame(b, frame, (0.0, 0.2, 1.34), 0.025, 0.07, "glow_warm")


def settle_bench(b: Builder, frame: Matrix, **options) -> None:
    """Fireside settle, 1.9 m: a high panelled back with a scalloped crest, scrolled arms, a padded seat with
    cushions and a box base."""
    wood = options.get("tint", WALNUT)
    cushion = options.get("cushion", "C9483B")
    crest = [(-0.95, 1.1), (-0.95, 1.3), (-0.6, 1.38), (-0.3, 1.3), (0.0, 1.42), (0.3, 1.3), (0.6, 1.38), (0.95, 1.3), (0.95, 1.1)]

    plank(b, frame, (-0.95, 0.22, 0.2), (0.95, 0.3, 1.1), wood, dark=True)
    b.prism(crest, 0.22, 0.3, "wood", srgb(wood), frame=frame, uv=("band", *WOOD_DARK_BAND, 1.0))

    for panel in range(3):
        plank(b, frame, (-0.88 + panel * 0.6, 0.2, 0.55), (-0.38 + panel * 0.6, 0.22, 1.05), HONEY)

    plank(b, frame, (-0.95, -0.3, 0.0), (0.95, 0.3, 0.4), wood, dark=True)
    plank(b, frame, (-0.9, -0.31, 0.08), (0.9, -0.3, 0.36), OAK)
    plank(b, frame, (-0.95, -0.32, 0.4), (0.95, 0.3, 0.45), HONEY)
    painted(b, frame, (-0.88, -0.28, 0.45), (0.88, 0.2, 0.52), cushion)

    for arm_x in (-0.88, 0.88):
        plank(b, frame, (arm_x - 0.07, -0.3, 0.45), (arm_x + 0.07, 0.3, 0.75), wood, dark=True)
        b.cylinder((arm_x, -0.32, 0.77), 0.065, 0.14, 8, "wood", srgb(HONEY), frame=frame, axis="X")

    for cushion_x, color in ((-0.4, "E8C14F"), (0.45, "3F8A50")):
        b.sphere((cushion_x, 0.12, 0.64), 1.0, "paint", srgb(color), scale=(0.17, 0.05, 0.14), frame=frame @ Matrix.Rotation(0.12, 4, "Y"), segments=6)


def bunting(b: Builder, frame: Matrix, **options) -> None:
    """Ceiling prop: a string of 14 festive pennants swagged between two beam hooks over 4 m."""
    colors = ("C9483B", "E8C14F", "3F8A50", "4F8FC9", "E0884A", "B57FE0", "F2E6CF")
    points = [(-2.0 + 4.0 * step / 14.0, -0.1 - 0.22 * math.sin(math.pi * step / 14.0)) for step in range(15)]

    for hook_x in (-2.0, 2.0):
        b.cylinder((hook_x, 0.0, -0.1), 0.02, 0.1, 6, "metal", srgb(WARM_IRON), frame=frame)

    for (start_x, start_z), (end_x, end_z) in zip(points, points[1:]):
        stick(b, frame, (start_x, 0.0, start_z), (end_x, 0.0, end_z), 0.012, CREAM, "paint")

    for index, (x, z) in enumerate(points[:-1]):
        b.hull([(x + 0.02, 0.0, z - 0.01), (x + 0.24, 0.0, z - 0.02), (x + 0.13, 0.0, z - 0.26), (x + 0.02, 0.012, z - 0.01), (x + 0.24, 0.012, z - 0.02)], "paint", srgb(colors[index % len(colors)]), frame=frame)


def fireplace_tall(b: Builder, frame: Matrix, **options) -> None:
    """The big stone hearth with its chimney breast carried up to the ceiling: a tapering hood with a moulded
    cornice, a corbelled cap and a mounted sconce on each shoulder. options.height: top of the breast (default 4.4)."""
    height = options.get("height", 4.4)
    stone = options.get("tint", STONE["dourada"])
    shoulder = 2.2

    fireplace(b, frame, **options)
    b.hull([(-0.95, -0.15, shoulder), (0.95, -0.15, shoulder), (-0.95, 0.4, shoulder), (0.95, 0.4, shoulder), (-0.55, -0.1, shoulder + 0.7), (0.55, -0.1, shoulder + 0.7), (-0.55, 0.4, shoulder + 0.7), (0.55, 0.4, shoulder + 0.7)], "stone", srgb(stone), frame=frame)
    b.box((-0.55, -0.1, shoulder + 0.7), (0.55, 0.4, height - 0.15), "stone", srgb(stone), frame=frame)
    b.box((-0.65, -0.16, height - 0.2), (0.65, 0.4, height - 0.12), "stone", srgb(STONE["clara"]), frame=frame)
    b.box((-0.72, -0.2, height - 0.12), (0.72, 0.4, height), "stone", srgb(STONE["media"]), frame=frame)

    for sconce_x in (-0.78, 0.78):
        stick(b, frame, (sconce_x, -0.12, 2.5), (sconce_x, -0.3, 2.6), 0.03, WARM_IRON, "metal")
        b.cylinder((sconce_x, -0.3, 2.6), 0.05, 0.02, 8, "metal", srgb(BRASS), frame=frame)
        candle(b, frame, sconce_x, -0.3, 2.62, 0.14)

    stick(b, frame, (-0.5, -0.12, shoulder + 0.4), (0.5, -0.12, shoulder + 0.4), 0.03, WARM_IRON, "metal")
    b.hull([(-0.14, -0.2, shoulder + 0.5), (0.14, -0.2, shoulder + 0.5), (0.0, -0.2, shoulder + 0.7), (-0.14, -0.14, shoulder + 0.5), (0.14, -0.14, shoulder + 0.5), (0.0, -0.14, shoulder + 0.7)], "metal", srgb(BRASS), frame=frame)


PROPS = {
    "bar_counter_l": {"build": bar_counter_l, "size": (6.0, 2.4, 1.5), "solid": True, "variants": ["right", "left"], "clearance": 1.5},
    "bar_stool": {"build": bar_stool, "size": (0.4, 0.4, 0.78), "solid": True},
    "keg_rack": {"build": keg_rack, "size": (1.5, 0.95, 1.45), "solid": True, "clearance": 0.8},
    "bottle_shelf": {"build": bottle_shelf, "size": (2.4, 0.45, 2.4), "solid": True, "clearance": 0.9},
    "mug_rail": {"build": mug_rail, "size": (1.2, 0.22, 2.03), "solid": False, "clearance": 0.6},
    "fireplace_tall": {"build": fireplace_tall, "size": (2.5, 0.8, 4.4), "solid": True, "light": ((0.0, -0.3, 0.6), LIGHT_FIRE, 2.5, 6.0), "clearance": 1.5},
    "tavern_booth": {"build": tavern_booth, "size": (2.24, 1.32, 1.55), "solid": True, "clearance": 0.6},
    "settle_bench": {"build": settle_bench, "size": (1.98, 0.7, 1.45), "solid": True},
    "bunting": {"build": bunting, "size": (4.04, 0.04, 0.6), "solid": False, "hang": True},
    "fireplace": {"build": fireplace, "size": (2.5, 0.8, 2.2), "solid": True, "light": ((0.0, -0.3, 0.6), LIGHT_FIRE, 2.5, 6.0), "clearance": 1.5},
    "tavern_table_set": {"build": tavern_table_set, "size": (1.6, 1.95, 0.97), "solid": True},
    "round_table_set": {"build": round_table_set, "size": (2.05, 2.05, 0.98), "solid": True},
    "stage": {"build": stage, "size": (3.0, 2.0, 1.27), "solid": True, "clearance": 1.0},
    "mounted_head": {"build": mounted_head, "size": (0.95, 0.7, 2.75), "solid": False, "variants": ["boar", "stag"]},
    "barrel_table": {"build": barrel_table, "size": (0.8, 0.8, 1.16), "solid": True},
    "stew_pot": {"build": stew_pot, "size": (1.15, 1.15, 1.56), "solid": True, "light": ((0.0, 0.0, 0.3), LIGHT_FIRE, 1.6, 5.0), "clearance": 1.0},
    "spit_roast": {"build": spit_roast, "size": (1.6, 0.6, 0.92), "solid": True, "light": ((0.0, 0.0, 0.35), LIGHT_FIRE, 1.6, 5.0), "clearance": 1.0},
    "plate_rack": {"build": plate_rack, "size": (1.25, 0.25, 2.1), "solid": False, "clearance": 0.6},
    "menu_board": {"build": menu_board, "size": (0.8, 0.08, 2.15), "solid": False, "clearance": 1.0},
    "dart_board": {"build": dart_board, "size": (0.6, 0.18, 2.03), "solid": False, "clearance": 2.4},
    "kitchen_stove": {"build": kitchen_stove, "size": (1.2, 0.72, 2.16), "solid": True, "light": ((-0.27, -0.45, 0.45), LIGHT_FIRE, 0.8, 3.0), "clearance": 1.0},
    "stone_oven": {"build": stone_oven, "size": (2.0, 1.6, 2.0), "solid": True, "light": ((0.0, -0.7, 1.1), LIGHT_FIRE, 2.0, 5.0), "clearance": 1.5},
    "dough_table": {"build": dough_table, "size": (2.0, 1.0, 1.12), "solid": True, "clearance": 0.9},
    "bread_rack": {"build": bread_rack, "size": (1.36, 0.46, 1.9), "solid": True, "clearance": 0.9},
    "cake_stand": {"build": cake_stand, "size": (0.7, 0.7, 1.43), "solid": True},
    "pastry_case": {"build": pastry_case, "size": (1.8, 0.7, 1.13), "solid": True, "clearance": 1.2},
    "flour_sacks": {"build": flour_sacks, "size": (1.2, 0.82, 0.7), "solid": True},
    "cafe_table_set": {"build": cafe_table_set, "size": (1.58, 0.74, 0.95), "solid": True},
    "hanging_pots": {"build": hanging_pots, "size": (1.25, 0.45, 1.1), "solid": False, "hang": True},
    "garlic_strings": {"build": garlic_strings, "size": (1.2, 0.16, 1.0), "solid": False, "hang": True},
    "jam_shelf": {"build": jam_shelf, "size": (1.2, 0.25, 1.95), "solid": False, "clearance": 0.6},
    "reception_desk": {"build": reception_desk, "size": (2.4, 1.6, 2.1), "solid": True, "clearance": 1.5},
    "key_board": {"build": key_board, "size": (1.0, 0.1, 2.1), "solid": False, "clearance": 0.6},
    "armchair": {"build": armchair, "size": (0.92, 0.84, 1.05), "solid": True},
    "sofa": {"build": sofa, "size": (2.02, 0.84, 0.9), "solid": True},
    "bed_canopy": {"build": bed_canopy, "size": (1.75, 2.06, 2.35), "solid": True},
    "bed_single": {"build": bed_single, "size": (1.0, 2.0, 1.0), "solid": True},
    "nightstand": {"build": nightstand, "size": (0.5, 0.42, 0.76), "solid": True},
    "wardrobe": {"build": wardrobe, "size": (1.2, 0.6, 2.15), "solid": True, "clearance": 0.8},
    "bathtub": {"build": bathtub, "size": (1.6, 0.82, 0.72), "solid": True, "clearance": 0.6},
    "washstand": {"build": washstand, "size": (0.78, 0.44, 1.7), "solid": True, "clearance": 0.6},
    "luggage_pile": {"build": luggage_pile, "size": (1.1, 0.7, 0.71), "solid": True},
    "parasol_table": {"build": parasol_table, "size": (2.0, 2.0, 2.45), "solid": True},
}
