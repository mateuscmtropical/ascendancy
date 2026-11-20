"""Coffee-farm furniture: what the tulha and the casa-grande need beyond the orphanage library (same 19th-century
southern colonial era): plank coffee bins full of dried coffee, piles of jute sacks, the decimal platform scale,
the rack of wooden rakes, shovels and sieves of the terreiro, the pilão, the household oratory and the cane
settee of the front room.

Runs inside Blender, imported by build_prop_sheet.py and build_farm.py. Contract of shop_props_common.py: X width
centred on 0, front faces -Y, back at +size[1] / 2, Z up from the floor.
"""

import itertools
import math
import random
import sys
from pathlib import Path

import bmesh
from mathutils import Matrix

sys.path.insert(0, str(Path(__file__).resolve().parent))

from build_town_houses import Builder, srgb  # noqa: E402
from shop_props_common import wicker_basket, wood_box  # noqa: E402
from shop_props_orphanage import (  # noqa: E402
    BRASS_AGED,
    CAST_IRON,
    BOOK_COLOURS,
    CHAPEL_WINE,
    HONEY_WOOD,
    LINEN_CREAM,
    PINE_SCRUB,
    SLATE_DARK,
    TERRACOTTA_DARK,
    WALNUT_DARK,
    WALNUT_MID,
    _at,
    _beam,
    _book_closed,
    _box,
    _candlestick,
    _cyl,
    _soft_block,
    _sphere,
)

COFFEE_SHADES = ("5B3322", "6E3F27", "4E2C1E")  # café em coco seco no terreiro
JUTE = "B59A6A"
JUTE_DARK = "9C8257"
STENCIL = "3B3A44"
CANE = "D8BE84"


def coffee_heap(b: Builder, frame: Matrix, half_x: float, half_y: float, bottom: float, top: float, generator: random.Random) -> None:
    """Heap of dried coffee filling a bin: a low hull, darker speckles of beans on its face."""
    points = [(x, y, bottom) for x in (-half_x, half_x) for y in (-half_y, half_y)]
    points += [(x * half_x * 0.6, y * half_y * 0.5, top) for x in (-1.0, 1.0) for y in (-1.0, 1.0)]

    b.hull(points, "paint", srgb(COFFEE_SHADES[0]), frame=frame)

    for _ in range(14):
        x, y = generator.uniform(-half_x * 0.7, half_x * 0.7), generator.uniform(-half_y * 0.8, half_y * 0.3)
        _sphere(b, frame, (x, y, bottom + (top - bottom) * 0.6), 0.09, "paint", generator.choice(COFFEE_SHADES), scale=(1.4, 1.0, 0.35), segments=5)


MOUND_RINGS = 16
MOUND_SIDES = 36
MOUND_SHAPE = 1.6  # exponent of the profile: the crest is round, the flank falls at about the angle of repose


def mound_height(radius_fraction: float, top: float) -> float:
    """Height of the mound at a fraction of its radius: a round crest and a flank that runs out onto the floor."""
    return top * (1.0 - radius_fraction**MOUND_SHAPE)


def mound_reach(angle: float) -> float:
    """Outline of the heap: the radius at an angle, slightly lumpy so it is not a perfect ellipse."""
    return 1.0 + 0.06 * math.sin(2.0 * angle + 1.0) + 0.04 * math.sin(3.0 * angle + 2.0)


def coffee_mound(b: Builder, frame: Matrix, half_x: float, half_y: float, top: float, generator: random.Random) -> None:
    """Rounded mound of dried coffee: rings of smooth-shaded faces along the heap profile, a lumpy outline stretched
    to the ellipse of the heap, with bean speckles lying on the surface."""
    angles = [2.0 * math.pi * side / MOUND_SIDES for side in range(MOUND_SIDES)]
    fractions = [1.0 - ring / MOUND_RINGS for ring in range(MOUND_RINGS)]
    mound = bmesh.new()
    rings = [
        [mound.verts.new((half_x * fraction * mound_reach(angle) * math.cos(angle), half_y * fraction * mound_reach(angle) * math.sin(angle), mound_height(fraction, top))) for angle in angles]
        for fraction in fractions
    ]
    peak = mound.verts.new((0.0, 0.0, top))

    for (lower, upper), side in itertools.product(zip(rings, rings[1:]), range(MOUND_SIDES)):
        mound.faces.new((lower[side], lower[(side + 1) % MOUND_SIDES], upper[(side + 1) % MOUND_SIDES], upper[side]))

    for side in range(MOUND_SIDES):
        mound.faces.new((rings[-1][side], rings[-1][(side + 1) % MOUND_SIDES], peak))

    for face in mound.faces:
        face.smooth = True

    b._link(mound, "paint", srgb(COFFEE_SHADES[0]), None, frame)

    for _ in range(40):
        angle, fraction = generator.uniform(0.0, 2.0 * math.pi), math.sqrt(generator.uniform(0.0, 0.8))
        reach = fraction * mound_reach(angle)
        spot = (half_x * reach * math.cos(angle), half_y * reach * math.sin(angle), mound_height(fraction, top) - 0.01)
        _sphere(b, frame, spot, 0.09, "paint", generator.choice(COFFEE_SHADES), scale=(1.4, 1.0, 0.35), segments=5)


def coffee_floor_heap(b: Builder, frame: Matrix, **options) -> None:
    """Coffee in the husk dumped on the tulha floor to finish drying: a broad rounded mound, the wooden rake
    (rodo) left in it and a round sieve leaning on its flank."""
    generator = random.Random(options.get("seed", 4))

    coffee_mound(b, frame, 1.55, 1.1, 0.72, generator)
    _beam(b, frame, (0.5, -0.3, 0.45), (1.6, -1.6, 1.35), 0.035, 0.035, "wood", HONEY_WOOD)
    _box(b, frame, (0.2, -0.36, 0.3), (0.8, -0.24, 0.5), "wood", HONEY_WOOD)
    sieve = _at(frame, (-1.3, -0.95, 0.3), 25.0) @ Matrix.Rotation(1.15, 4, "X")
    _cyl(b, sieve, (0.0, 0.0, 0.0), 0.32, 0.06, 12, "wood", PINE_SCRUB)
    _cyl(b, sieve, (0.0, 0.0, 0.015), 0.3, 0.03, 12, "paint", JUTE_DARK)


def basket_coffee(b: Builder, frame: Matrix, generator: random.Random) -> None:
    coffee_heap(b, frame, 0.17, 0.17, 0.22, 0.36, generator)


def coffee_basket(b: Builder, frame: Matrix, seed: int = 1, **options) -> None:
    """Balaio of picked coffee waiting for the terreiro."""
    wicker_basket(b, frame, seed=seed, fill=basket_coffee)


def coffee_bin(b: Builder, frame: Matrix, **options) -> None:
    """One compartment of the tulha: plank walls on posts, the front closed by loose boards dropped into grooves
    up to the coffee level, the bin heaped with dried coffee, a wooden shovel stuck in it."""
    generator = random.Random(options.get("seed", 1))
    width, depth, height = 2.2, 2.0, 1.6
    front, back = -depth / 2.0, depth / 2.0
    boards = generator.randint(4, 6)

    for side in (-1.0, 1.0):
        wood_box(b, frame, (side * width / 2.0 - 0.025 * (side > 0), front, 0.0), (side * width / 2.0 + 0.025 * (side < 0), back, height), WALNUT_MID)
        _box(b, frame, (side * (width / 2.0 - 0.06) - 0.05, front, 0.0), (side * (width / 2.0 - 0.06) + 0.05, front + 0.1, height + 0.1), "wood", WALNUT_DARK)

    wood_box(b, frame, (-width / 2.0, back - 0.05, 0.0), (width / 2.0, back, height), WALNUT_MID)

    for board in range(boards):
        _box(b, frame, (-width / 2.0 + 0.11, front + 0.02, board * 0.2), (width / 2.0 - 0.11, front + 0.07, board * 0.2 + 0.19), "wood", PINE_SCRUB if board % 2 else HONEY_WOOD)

    coffee_heap(b, frame, width / 2.0 - 0.05, depth / 2.0 - 0.05, boards * 0.2 - 0.1, boards * 0.2 + 0.25, generator)
    _beam(b, frame, (0.4, 0.1, boards * 0.2 + 0.1), (0.62, -0.5, boards * 0.2 + 1.2), 0.04, 0.04, "wood", HONEY_WOOD)
    _box(b, frame, (0.28, 0.12, boards * 0.2 - 0.05), (0.52, 0.16, boards * 0.2 + 0.25), "wood", HONEY_WOOD)


def jute_sack(b: Builder, frame: Matrix, center: tuple, turn: float, tint: str) -> None:
    """A 60 kg sack lying down: a soft block with the tied neck and a stencil."""
    sack = _at(frame, center, turn)

    _soft_block(b, sack, (0.0, 0.0, 0.0), (0.33, 0.22, 0.14), tint, bevel=0.07)
    _cyl(b, sack, (0.33, 0.0, 0.0), 0.06, 0.08, 6, "paint", tint, axis="X")
    _box(b, sack, (-0.12, -0.225, -0.05), (0.12, -0.215, 0.06), "paint", STENCIL)


def sack_pile(b: Builder, frame: Matrix, **options) -> None:
    """Coffee sacks stacked in the binder's pattern, three layers stepping back, on a plank pallet."""
    generator = random.Random(options.get("seed", 2))
    layers = ((3, 2), (3, 2), (2, 1))

    wood_box(b, frame, (-0.8, -0.55, 0.0), (0.8, 0.55, 0.08), PINE_SCRUB, light=True)

    for layer, (columns, rows) in enumerate(layers):
        for column in range(columns):
            for row in range(rows):
                x = (column - (columns - 1) / 2.0) * 0.5 + generator.uniform(-0.03, 0.03)
                y = (row - (rows - 1) / 2.0) * 0.46 + generator.uniform(-0.02, 0.02)
                jute_sack(b, frame, (x, y, 0.22 + layer * 0.28), 90.0 + generator.uniform(-6.0, 6.0), generator.choice((JUTE, JUTE_DARK)))


def decimal_scale(b: Builder, frame: Matrix, **options) -> None:
    """Decimal platform scale for the sacks: an iron-shod plank platform, the column at the back with its beam,
    the sliding poise and the hanger of counterweights."""
    wood_box(b, frame, (-0.45, -0.4, 0.0), (0.45, 0.25, 0.14), HONEY_WOOD, light=True)
    _box(b, frame, (-0.47, -0.42, 0.0), (0.47, 0.27, 0.03), "metal", CAST_IRON)
    _box(b, frame, (-0.08, 0.25, 0.0), (0.08, 0.4, 1.25), "metal", CAST_IRON)
    _box(b, frame, (-0.46, 0.29, 1.2), (0.36, 0.33, 1.26), "metal", CAST_IRON)
    _box(b, frame, (-0.1, 0.27, 1.18), (-0.02, 0.35, 1.3), "metal", BRASS_AGED)
    _beam(b, frame, (0.36, 0.31, 1.2), (0.36, 0.31, 0.75), 0.012, 0.012, "metal", CAST_IRON)

    for weight in range(3):
        _cyl(b, frame, (0.36, 0.31, 0.72 - weight * 0.05), 0.06 - weight * 0.012, 0.04, 8, "metal", CAST_IRON)

    for weight in range(4):
        _cyl(b, frame, (-0.3 + weight * 0.12, -0.2, 0.14), 0.045, 0.06, 8, "metal", CAST_IRON)


def farm_tool_rack(b: Builder, frame: Matrix, **options) -> None:
    """Wall rack of the terreiro tools: wooden rakes (rodos) and shovels upright on a rail, round sieves and a hoe
    on pegs, a broom of twigs."""
    width = 1.6
    back = 0.15

    _box(b, frame, (-width / 2.0, back - 0.05, 1.5), (width / 2.0, back, 1.6), "wood", WALNUT_DARK)
    _box(b, frame, (-width / 2.0, back - 0.05, 0.25), (width / 2.0, back, 0.33), "wood", WALNUT_DARK)

    for tool in range(5):
        x = -0.6 + tool * 0.24
        _beam(b, frame, (x, back - 0.08, 0.05), (x, back - 0.08, 1.85), 0.035, 0.035, "wood", HONEY_WOOD)
        head = (0.45, 0.04, 0.14) if tool % 2 else (0.2, 0.04, 0.32)
        _box(b, frame, (x - head[0] / 2.0, back - 0.13, 0.0), (x + head[0] / 2.0, back - 0.09, head[2]), "wood", PINE_SCRUB)

    for sieve in range(2):
        _cyl(b, frame, (0.45 + sieve * 0.06, back - 0.06, 1.15 - sieve * 0.12), 0.24, 0.06, 12, "wood", CANE, axis="Y")

    _beam(b, frame, (0.72, back - 0.1, 0.0), (0.7, back - 0.1, 1.7), 0.035, 0.035, "wood", HONEY_WOOD)
    _box(b, frame, (0.62, back - 0.22, 1.62), (0.82, back - 0.1, 1.72), "metal", CAST_IRON)


def pilao(b: Builder, frame: Matrix, **options) -> None:
    """Pilão: a hollowed trunk standing on the floor with the long two-ended pestle leaning on it."""
    _cyl(b, frame, (0.0, 0.0, 0.0), 0.22, 0.75, 10, "wood", WALNUT_MID, top_radius=0.2)
    _cyl(b, frame, (0.0, 0.0, 0.751), 0.15, 0.004, 10, "paint", "3A2A20")
    _beam(b, frame, (0.05, 0.05, 0.5), (0.12, 0.18, 1.6), 0.07, 0.07, "wood", HONEY_WOOD)


def home_oratory(b: Builder, frame: Matrix, **options) -> None:
    """Household oratory: a carved cabinet on a chest of drawers, its doors open on a painted niche with a saint,
    two candlesticks and a vase of flowers on the ledge."""
    width, back = 0.9, 0.22

    wood_box(b, frame, (-width / 2.0, -back, 0.0), (width / 2.0, back, 0.95), WALNUT_DARK)

    for drawer in range(3):
        _box(b, frame, (-width / 2.0 + 0.05, -back - 0.01, 0.1 + drawer * 0.28), (width / 2.0 - 0.05, -back, 0.33 + drawer * 0.28), "wood", WALNUT_MID)
        _sphere(b, frame, (0.0, -back - 0.03, 0.22 + drawer * 0.28), 0.02, "metal", BRASS_AGED, segments=5)

    wood_box(b, frame, (-0.35, -0.12, 0.95), (0.35, back, 1.95), WALNUT_DARK)
    _box(b, frame, (-0.28, -0.13, 1.0), (0.28, -0.11, 1.85), "paint", "2E4A78")
    _box(b, frame, (-0.4, -0.15, 1.95), (0.4, back, 2.05), "wood", WALNUT_DARK)
    _box(b, frame, (-0.08, -0.06, 2.05), (0.08, 0.02, 2.2), "metal", BRASS_AGED)

    for side in (-1.0, 1.0):
        leaf = _at(frame, (side * 0.35, -0.12, 0.95), side * 110.0)
        _box(b, leaf, (min(0.0, -side * 0.34), -0.02, 0.05), (max(0.0, -side * 0.34), 0.0, 0.95), "paint", CHAPEL_WINE)
        _candlestick(b, frame, side * 0.32, -0.18, 0.95)

    _cyl(b, frame, (0.0, -0.02, 1.02), 0.06, 0.06, 6, "paint", "C9A86A")
    _cyl(b, frame, (0.0, -0.02, 1.08), 0.07, 0.42, 8, "paint", "6E5A8A", top_radius=0.05)
    _sphere(b, frame, (0.0, -0.02, 1.57), 0.06, "paint", "E9CDB0", segments=6)
    _sphere(b, frame, (0.0, -0.02, 1.68), 0.08, "metal", BRASS_AGED, scale=(1.0, 0.2, 1.0), segments=6)


def cane_settee(b: Builder, frame: Matrix, **options) -> None:
    """Canapé de palhinha: jacaranda frame on turned legs, caned seat and back in three panels, curled arms."""
    width, seat, back = 1.9, 0.46, 0.3

    for corner_x in (-width / 2.0 + 0.05, width / 2.0 - 0.05):
        for corner_y in (-back + 0.05, back - 0.05):
            _cyl(b, frame, (corner_x, corner_y, 0.0), 0.028, seat, 6, "wood", WALNUT_DARK)

    _box(b, frame, (-width / 2.0, -back, seat - 0.06), (width / 2.0, back, seat), "wood", WALNUT_DARK)
    _box(b, frame, (-width / 2.0 + 0.06, -back + 0.05, seat), (width / 2.0 - 0.06, back - 0.05, seat + 0.01), "paint", CANE)
    _box(b, frame, (-width / 2.0, back - 0.06, seat), (width / 2.0, back, 1.0), "wood", WALNUT_DARK)

    for panel in range(3):
        panel_x = -0.6 + panel * 0.6
        _box(b, frame, (panel_x - 0.26, back - 0.07, seat + 0.1), (panel_x + 0.26, back - 0.06, 0.92), "paint", CANE)

    for side in (-1.0, 1.0):
        _box(b, frame, (side * width / 2.0 - 0.04, -back, seat), (side * width / 2.0 + 0.04, back, 0.68), "wood", WALNUT_DARK)
        _cyl(b, frame, (side * width / 2.0, -back, 0.68), 0.05, 0.08, 8, "wood", WALNUT_DARK, axis="Y")

    _soft_block(b, frame, (-0.55, 0.12, seat + 0.13), (0.18, 0.06, 0.13), LINEN_CREAM, bevel=0.05)


def child_desk(b: Builder, frame: Matrix, **options) -> None:
    """Small pine writing table of a child (0.9 x 0.5 m, child sits on the -Y side): turned legs, an apron with a
    drawer knob, a slate in a wooden frame, two copybooks and a clay inkwell."""
    width, depth, top = 0.9, 0.5, 0.68

    for corner_x in (-width / 2.0 + 0.04, width / 2.0 - 0.04):
        for corner_y in (-depth / 2.0 + 0.04, depth / 2.0 - 0.04):
            _cyl(b, frame, (corner_x, corner_y, 0.0), 0.025, top, 6, "wood", WALNUT_MID)

    _box(b, frame, (-width / 2.0, -depth / 2.0, top - 0.1), (width / 2.0, depth / 2.0, top - 0.02), "wood", WALNUT_MID)
    _box(b, frame, (-0.2, -depth / 2.0 - 0.012, top - 0.09), (0.2, -depth / 2.0, top - 0.03), "wood", HONEY_WOOD)
    _sphere(b, frame, (0.0, -depth / 2.0 - 0.025, top - 0.06), 0.014, "metal", BRASS_AGED, segments=6)
    _box(b, frame, (-width / 2.0 - 0.02, -depth / 2.0 - 0.02, top - 0.02), (width / 2.0 + 0.02, depth / 2.0 + 0.02, top), "wood", PINE_SCRUB)
    _box(b, frame, (-0.36, -0.12, top), (-0.08, 0.1, top + 0.012), "wood", WALNUT_DARK)
    _box(b, frame, (-0.345, -0.105, top + 0.012), (-0.095, 0.085, top + 0.016), "paint", SLATE_DARK)
    _book_closed(b, frame, 0.15, 0.0, top, 0.16, 0.2, 0.02, BOOK_COLOURS[1], yaw=8.0)
    _book_closed(b, frame, 0.15, 0.0, top + 0.02, 0.15, 0.19, 0.016, BOOK_COLOURS[4], yaw=-6.0)
    _cyl(b, frame, (0.33, 0.14, top), 0.025, 0.04, 8, "paint", TERRACOTTA_DARK)


def toy_blocks(b: Builder, frame: Matrix, **options) -> None:
    """Floor toys: a few painted wooden cubes tumbled over, a spinning top and a rag ball."""
    generator = random.Random(options.get("seed", 3))

    for index, hue in enumerate(("B5453A", "3E6B94", "D9B347", "5E8A4E", "B5453A")):
        spot = (generator.uniform(-0.18, 0.18), generator.uniform(-0.12, 0.12), 0.0)
        block = _at(frame, spot, generator.uniform(0.0, 90.0))
        _box(b, block, (-0.035, -0.035, 0.0), (0.035, 0.035, 0.07), "paint", hue)

    top = _at(frame, (0.24, 0.1, 0.0))
    _cyl(b, top, (0.0, 0.0, 0.0), 0.002, 0.05, 8, "wood", HONEY_WOOD, top_radius=0.04)
    _cyl(b, top, (0.0, 0.0, 0.05), 0.04, 0.012, 8, "paint", "B5453A")
    _sphere(b, frame, (-0.25, -0.1, 0.055), 0.055, "paint", LINEN_CREAM, segments=8)


def toy_shelf(b: Builder, frame: Matrix, **options) -> None:
    """Narrow wall shelf for a child (0.9 m, built at its mounting height, back against +Y): a plank on two
    brackets with a row of primers, a wooden horse and a rag doll leaning on the books."""
    _box(b, frame, (-0.45, -0.1, 0.0), (0.45, 0.11, 0.025), "wood", HONEY_WOOD)

    for side in (-0.34, 0.34):
        _box(b, frame, (side - 0.015, 0.0, -0.12), (side + 0.015, 0.11, 0.0), "wood", WALNUT_DARK)

    for index in range(6):
        _book_closed(b, frame, -0.38 + index * 0.05, 0.02, 0.025, 0.04, 0.16, 0.14 + (index % 3) * 0.03, BOOK_COLOURS[index % len(BOOK_COLOURS)])

    _box(b, frame, (0.02, -0.04, 0.025), (0.16, 0.0, 0.05), "wood", WALNUT_MID)
    _box(b, frame, (0.03, -0.035, 0.05), (0.15, -0.005, 0.12), "wood", WALNUT_MID)
    _box(b, frame, (0.11, -0.035, 0.12), (0.15, -0.005, 0.2), "wood", WALNUT_MID)
    doll = _at(frame, (0.3, 0.02, 0.025), 0.0)
    _box(b, doll, (-0.04, -0.02, 0.0), (0.04, 0.02, 0.16), "paint", "B5453A")
    _sphere(b, doll, (0.0, 0.0, 0.2), 0.04, "paint", "E9CDB0", segments=8)


PROPS = {
    "child_desk": {"build": child_desk, "size": (0.94, 0.54, 0.78), "solid": True},
    "toy_blocks": {"build": toy_blocks, "size": (0.6, 0.35, 0.1), "solid": False},
    "toy_shelf": {"build": toy_shelf, "size": (0.9, 0.22, 0.3), "solid": False},
    "coffee_floor_heap": {"build": coffee_floor_heap, "size": (3.2, 2.3, 0.75), "solid": True},
    "coffee_basket": {"build": coffee_basket, "size": (0.5, 0.5, 0.4), "solid": True},
    "coffee_bin": {"build": coffee_bin, "size": (2.2, 2.0, 2.05), "solid": True},
    "sack_pile": {"build": sack_pile, "size": (1.6, 1.25, 1.0), "solid": True},
    "decimal_scale": {"build": decimal_scale, "size": (0.95, 0.85, 1.32), "solid": True},
    "farm_tool_rack": {"build": farm_tool_rack, "size": (1.6, 0.3, 1.9), "solid": False},
    "pilao": {"build": pilao, "size": (0.5, 0.5, 1.6), "solid": True},
    "home_oratory": {"build": home_oratory, "size": (1.0, 0.7, 2.2), "solid": True},
    "cane_settee": {"build": cane_settee, "size": (2.0, 0.6, 1.0), "solid": True},
}
