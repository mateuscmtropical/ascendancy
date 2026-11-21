"""Props of the tavern and inn (tavern_layout.py): the inglenook of the taproom, the tiled stove, wall benches,
tables and chairs of the Stube, plate shelves and the plank doors of the back rooms.

Prop contract of shop_props_common: origin at the middle of the footprint on the floor, front toward -Y, back toward
+Y (the wall side), z up. Runs inside Blender, imported by build_market_shops.py.
"""

import random
import sys
from pathlib import Path

from mathutils import Matrix

sys.path.insert(0, str(Path(__file__).resolve().parent))

from build_town_houses import BRICK, STONE, WOOD_DARK_BAND, WOOD_LIGHT_BAND, Builder, srgb  # noqa: E402
from shop_props_food import BRASS, CREAM, HONEY, LIGHT_FIRE, OAK, SOOT, WALNUT, WARM_IRON, candle, fire, painted, plank  # noqa: E402

BLACK_OAK = "5A3A26"
TILE_GREEN = "2F6B4F"
TILE_GLAZE = "4F9A72"
TILE_CREAM = "EFE3C8"
CLOTH_WHITE = "F7F2E6"
CLOTH_GREEN = "3F6B55"
CUSHION_CHECK = ("C9483B", "E8C14F", "3F8A50")
PLATE_COLOURS = ("F2E6CF", "4F8FC9", "E0884A", "F2E6CF", "7FC46A", "C9483B")
INGLENOOK_HEIGHT = 3.55  # breast to the tavern's ceiling


def inglenook(b: Builder, frame: Matrix, **options) -> None:
    """Wide brick inglenook: a chimney breast up to the ceiling on an oak bressummer hung with horse brasses, a sooty
    firebox with a log fire and a pot on a chain, a stone hearth slab and a salt box in the cheek."""
    height = options.get("height", INGLENOOK_HEIGHT)
    brick = srgb(BRICK["tudor"])
    lintel = 1.78

    b.box((-1.5, -0.5, lintel + 0.24), (1.5, 0.55, height), "brick", brick, frame=frame)

    for cheek_x in (-1.5, 1.12):
        b.box((cheek_x, -0.5, 0.0), (cheek_x + 0.38, 0.55, lintel + 0.24), "brick", brick, frame=frame)

    b.box((-1.12, 0.3, 0.0), (1.12, 0.55, lintel + 0.24), "brick", srgb(BRICK["escuro"]), frame=frame)
    painted(b, frame, (-1.12, 0.28, 0.0), (1.12, 0.3, lintel), SOOT)
    plank(b, frame, (-1.55, -0.58, lintel), (1.55, -0.4, lintel + 0.26), BLACK_OAK, dark=True)
    b.box((-1.45, -0.85, 0.0), (1.45, 0.3, 0.05), "stone", srgb(STONE["clara"]), frame=frame)
    b.box((-1.12, -0.05, 0.05), (1.12, 0.28, 0.12), "brick", srgb(BRICK["escuro"]), frame=frame)

    for brass_x in (-1.2, -0.6, 0.0, 0.6, 1.2):
        b.cylinder((brass_x, -0.6, lintel + 0.13), 0.07, 0.015, 10, "metal", srgb(BRASS), frame=frame, axis="Y")

    fire(b, frame, 0.0, 0.0, 0.12, 0.9, options.get("seed", 3))
    b.box((-0.02, 0.05, 0.9), (0.02, 0.09, lintel), "metal", srgb(WARM_IRON), frame=frame)
    b.cylinder((0.0, 0.07, 0.62), 0.2, 0.26, 10, "metal", srgb(WARM_IRON), top_radius=0.17, frame=frame)

    for andiron_x in (-0.4, 0.4):
        b.box((andiron_x - 0.025, -0.25, 0.12), (andiron_x + 0.025, 0.2, 0.18), "metal", srgb(WARM_IRON), frame=frame)
        b.cylinder((andiron_x, -0.25, 0.12), 0.03, 0.22, 6, "metal", srgb(BRASS), frame=frame)

    plank(b, frame, (-1.0, 0.2, 1.3), (-0.75, 0.3, 1.55), OAK)
    b.box((0.75, -0.35, 0.05), (1.05, -0.1, 0.6), "wood", srgb(WALNUT), frame=frame, uv=("band", *WOOD_DARK_BAND, 1.0))

    for log_index in range(4):
        b.cylinder((0.78 + 0.12 * (log_index % 2), -0.25, 0.08 + 0.1 * log_index), 0.05, 0.5, 6, "wood", srgb(OAK), frame=frame, axis="Y")


def tiled_stove(b: Builder, frame: Matrix, **options) -> None:
    """Green tiled stove (Kachelofen) of a Stube: stone plinth, a two-stage body of raised tiles, a moulded cornice and
    crown, and a warm bench with a cushion running along its front."""
    green, glaze = srgb(options.get("tint", TILE_GREEN)), srgb(TILE_GLAZE)
    stages = ((0.25, 1.35, 0.62, 0.45), (1.47, 2.2, 0.48, 0.35))  # (z from, z to, half width, half depth)

    b.box((-0.68, -0.2, 0.0), (0.68, 0.7, 0.25), "stone", srgb(STONE["clara"]), frame=frame)

    for z_from, z_to, half_width, half_depth in stages:
        centre = 0.25
        b.box((-half_width, centre - half_depth, z_from), (half_width, centre + half_depth, z_to), "paint", green, frame=frame)
        b.box((-half_width - 0.05, centre - half_depth - 0.05, z_to), (half_width + 0.05, centre + half_depth + 0.05, z_to + 0.12), "paint", glaze, frame=frame)
        stove_tiles(b, frame, (-half_width, half_width), centre - half_depth, (z_from + 0.06, z_to - 0.06))

    b.box((-0.3, 0.0, 2.32), (0.3, 0.5, 2.42), "paint", srgb(TILE_CREAM), frame=frame)
    plank(b, frame, (-0.68, -0.7, 0.0), (0.68, -0.25, 0.42), HONEY)
    plank(b, frame, (-0.7, -0.72, 0.42), (0.7, -0.2, 0.47), OAK)
    painted(b, frame, (-0.6, -0.66, 0.47), (0.2, -0.25, 0.53), CUSHION_CHECK[0])


def stove_tiles(b: Builder, frame: Matrix, span: tuple, face: float, heights: tuple) -> None:
    """Raised square tiles on the front face of a stove stage, a pale glaze in each."""
    columns = max(2, round((span[1] - span[0]) / 0.28))
    rows = max(2, round((heights[1] - heights[0]) / 0.28))
    tile_width, tile_height = (span[1] - span[0]) / columns, (heights[1] - heights[0]) / rows
    cells = [(column, row) for column in range(columns) for row in range(rows)]

    for column, row in cells:
        left, bottom = span[0] + column * tile_width, heights[0] + row * tile_height
        b.box((left + 0.02, face - 0.025, bottom + 0.02), (left + tile_width - 0.02, face, bottom + tile_height - 0.02), "paint", srgb(TILE_GLAZE), frame=frame)
        b.box((left + 0.07, face - 0.03, bottom + 0.07), (left + tile_width - 0.07, face - 0.025, bottom + tile_height - 0.07), "paint", srgb(TILE_CREAM), frame=frame)


def wall_bench(b: Builder, frame: Matrix, **options) -> None:
    """Built-in wall bench of a Stube (2.4 m): box seat with a panelled front, a plank back to the wall with a moulded
    top rail, and checked cushions."""
    wood = options.get("tint", HONEY)
    generator = random.Random(options.get("seed", 0))

    plank(b, frame, (-1.2, -0.25, 0.0), (1.2, 0.2, 0.42), WALNUT, dark=True)
    plank(b, frame, (-1.22, -0.27, 0.42), (1.22, 0.2, 0.47), wood)
    plank(b, frame, (-1.2, 0.12, 0.47), (1.2, 0.22, 0.86), wood)
    plank(b, frame, (-1.22, 0.08, 0.86), (1.22, 0.24, 0.92), OAK)

    for panel in range(4):
        plank(b, frame, (-1.12 + panel * 0.58, -0.26, 0.08), (-0.66 + panel * 0.58, -0.25, 0.36), OAK)

    for cushion in range(3):
        painted(b, frame, (-1.12 + cushion * 0.76, -0.22, 0.47), (-0.42 + cushion * 0.76, 0.1, 0.53), CUSHION_CHECK[generator.randrange(3)])


def stube_table(b: Builder, frame: Matrix, **options) -> None:
    """Square Stube table (0.95 m) on turned legs with a green cloth under a white runner, a jug, a candle and two
    place settings."""
    top = options.get("tint", HONEY)

    plank(b, frame, (-0.475, -0.475, 0.72), (0.475, 0.475, 0.77), top)

    for leg_x, leg_y in ((-0.38, -0.38), (0.38, -0.38), (-0.38, 0.38), (0.38, 0.38)):
        b.cylinder((leg_x, leg_y, 0.0), 0.04, 0.72, 8, "wood", srgb(OAK), top_radius=0.03, frame=frame)

    painted(b, frame, (-0.5, -0.5, 0.77), (0.5, 0.5, 0.78), CLOTH_GREEN)
    painted(b, frame, (-0.36, -0.52, 0.78), (0.36, 0.52, 0.785), CLOTH_WHITE)
    b.cylinder((0.12, 0.08, 0.785), 0.07, 0.18, 8, "paint", srgb("C9873F"), top_radius=0.05, frame=frame)
    candle(b, frame, -0.12, 0.1, 0.785, 0.14, holder=True)

    for plate_y in (-0.3, 0.3):
        b.cylinder((0.0, plate_y, 0.785), 0.11, 0.012, 10, "paint", srgb(CREAM), frame=frame)


def stube_chair(b: Builder, frame: Matrix, **options) -> None:
    """Stube chair with a splayed seat and a carved board back (a heart cut out of it); faces -Y."""
    wood = srgb(options.get("tint", HONEY))
    back = [(-0.19, 0.45), (-0.21, 0.75), (-0.14, 0.95), (0.0, 0.92), (0.14, 0.95), (0.21, 0.75), (0.19, 0.45)]

    b.box((-0.21, -0.2, 0.42), (0.21, 0.2, 0.47), "wood", wood, frame=frame, uv=("band", *WOOD_LIGHT_BAND, 1.0))

    for leg_x, leg_y in ((-0.16, -0.15), (0.16, -0.15), (-0.16, 0.15), (0.16, 0.15)):
        b.beam((leg_x * 1.25, leg_y * 1.25, 0.0), (leg_x, leg_y, 0.42), 0.04, 0.04, "wood", wood)

    b.prism(back, 0.15, 0.19, "wood", wood, frame=frame, uv=("band", *WOOD_LIGHT_BAND, 1.0))
    painted(b, frame, (-0.05, 0.145, 0.7), (0.05, 0.195, 0.8), SOOT)


def plate_shelf(b: Builder, frame: Matrix, **options) -> None:
    """Plate shelf of 2 m hung on the panelling: a moulded board on brackets with a groove rail, plates and jugs
    standing along it."""
    generator = random.Random(options.get("seed", 0))
    plate_count = 7

    plank(b, frame, (-1.0, -0.1, 0.0), (1.0, 0.1, 0.04), OAK)
    plank(b, frame, (-1.0, -0.12, 0.04), (1.0, -0.1, 0.08), WALNUT, dark=True)

    for bracket_x in (-0.8, 0.0, 0.8):
        b.side_prism([(0.1, 0.0), (0.1, -0.22), (-0.08, 0.0)], bracket_x - 0.02, bracket_x + 0.02, "wood", srgb(OAK), frame=frame)

    for index in range(plate_count):
        plate_x = -0.85 + 1.7 * index / (plate_count - 1)
        tilt = frame @ Matrix.Translation((plate_x, 0.04, 0.17)) @ Matrix.Rotation(-0.18, 4, "X")
        b.cylinder((0.0, 0.0, 0.0), 0.13, 0.012, 12, "paint", srgb(PLATE_COLOURS[generator.randrange(len(PLATE_COLOURS))]), frame=tilt, axis="Y")


def plank_door(b: Builder, frame: Matrix, **options) -> None:
    """Closed ledged plank door on a wall (back door, the boxed stair to the rooms): oak frame, boards, iron strap
    hinges and a ring handle."""
    width, height = 1.0, 2.15
    boards = 5

    plank(b, frame, (-width / 2.0 - 0.1, 0.0, 0.0), (width / 2.0 + 0.1, 0.06, height + 0.1), BLACK_OAK, dark=True)

    for board in range(boards):
        left = -width / 2.0 + board * width / boards
        plank(b, frame, (left + 0.005, -0.04, 0.02), (left + width / boards - 0.005, 0.0, height), (OAK, HONEY)[board % 2])

    for strap_z in (0.35, height - 0.4):
        b.box((-width / 2.0, -0.055, strap_z), (width * 0.25, -0.04, strap_z + 0.06), "metal", srgb(WARM_IRON), frame=frame)

    b.cylinder((0.33, -0.06, 1.05), 0.06, 0.012, 10, "metal", srgb(WARM_IRON), frame=frame, axis="Y")


PROPS = {
    "inglenook": {"build": inglenook, "size": (3.1, 1.1, INGLENOOK_HEIGHT), "solid": True, "light": ((0.0, -0.3, 0.6), LIGHT_FIRE, 2.6, 6.5), "clearance": 1.5},
    "tiled_stove": {"build": tiled_stove, "size": (1.4, 1.45, 2.42), "solid": True, "clearance": 0.8},
    "wall_bench": {"build": wall_bench, "size": (2.44, 0.5, 0.92), "solid": True},
    "stube_table": {"build": stube_table, "size": (1.0, 1.0, 0.98), "solid": True},
    "stube_chair": {"build": stube_chair, "size": (0.44, 0.44, 0.95), "solid": True},
    "plate_shelf": {"build": plate_shelf, "size": (2.0, 0.24, 0.32), "solid": False},
    "plank_door": {"build": plank_door, "size": (1.2, 0.1, 2.25), "solid": False},
}
