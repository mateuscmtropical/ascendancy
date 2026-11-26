"""Props of the tavern and inn (tavern_layout.py): the inglenook on the terrace, the U bar with its lifting flap and
the plank doors of the back rooms.

Prop contract of shop_props_common: origin at the middle of the footprint on the floor, front toward -Y, back toward
+Y (the wall side), z up. Runs inside Blender, imported by build_market_shops.py.
"""

import sys
from pathlib import Path

from mathutils import Matrix

sys.path.insert(0, str(Path(__file__).resolve().parent))

from build_town_houses import BRICK, STONE, WOOD_DARK_BAND, Builder, srgb  # noqa: E402
from shop_props_food import BRASS, HONEY, LIGHT_FIRE, OAK, PALE_WOOD, SOOT, WALNUT, WARM_IRON, bar_counter_l, counter_body, fire, painted, plank, turned  # noqa: E402

BLACK_OAK = "5A3A26"
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


def tavern_bar(b: Builder, frame: Matrix, **options) -> None:
    """U bar against a wall (+Y): the 6 m run and its far return of bar_counter_l, and a near return whose end by the
    run is the pass-through: the hinged top section lifted upright over the latched half door."""
    flap = (-3.0, -2.2, -0.4, 0.35)  # x from, x to, y from, y to of the lifting section

    bar_counter_l(b, frame, **options)
    counter_body(b, turned(frame, -2.6, 0.775, 0.0, -90.0), (-0.425, -0.36, 0.0), (0.425, 0.32, 1.03), options.get("tint", OAK), HONEY, 2)

    for board in range(3):
        board_from = flap[0] + board * 0.8 / 3.0
        plank(b, frame, (board_from, flap[3], 1.03), (board_from + 0.8 / 3.0 - 0.004, 1.2, 1.1), (HONEY, PALE_WOOD)[board % 2])

    plank(b, frame, (flap[0], flap[3], 1.1), (flap[1], flap[3] + 0.07, 1.1 + flap[3] - flap[2]), HONEY)

    for hinge_x in (flap[0] + 0.15, flap[1] - 0.15):
        b.box((hinge_x - 0.04, flap[3] - 0.005, 1.08), (hinge_x + 0.04, flap[3] + 0.075, 1.16), "metal", srgb(BRASS), frame=frame)

    plank(b, frame, (-2.63, flap[2] + 0.02, 0.12), (-2.57, flap[3] - 0.02, 0.95), OAK)
    b.cylinder((-2.64, flap[2] + 0.12, 0.6), 0.035, 0.01, 8, "metal", srgb(WARM_IRON), frame=frame, axis="X")


PROPS = {
    "inglenook": {"build": inglenook, "size": (3.1, 1.1, INGLENOOK_HEIGHT), "solid": True, "light": ((0.0, -0.3, 0.6), LIGHT_FIRE, 2.6, 6.5), "clearance": 1.5},
    "plank_door": {"build": plank_door, "size": (1.2, 0.1, 2.25), "solid": False},
    "tavern_bar": {"build": tavern_bar, "size": (6.0, 2.4, 1.85), "solid": True, "clearance": 1.5, "parts": ((-3.0, 3.0, -1.2, -0.4), (2.2, 3.0, -0.4, 1.2), (-3.0, -2.2, -0.4, 1.2))},  # the run and both returns: the barkeep's aisle stays free
}
