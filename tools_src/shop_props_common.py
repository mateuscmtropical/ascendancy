"""Shared shop prop helpers plus the common furniture kit (PROPS) used by every shop interior.

Runs inside Blender, imported by build_market_shops.py and build_prop_sheet.py.

Prop contract (every shop_props_<group>.py follows it):
  def name(b: Builder, frame: Matrix, **options) -> None   # Builder primitives only, always frame=frame
  PROPS = {"name": {"build": name, "size": (x, y, z), "solid": bool, "light": optional ((x, y, z), "HEX", energy, range),
                    "variants": optional [str, ...] (only for the prop sheet)}}
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

from build_town_houses import WOOD_DARK_BAND, WOOD_LIGHT_BAND, Builder, srgb  # noqa: E402,F401

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
