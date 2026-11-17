"""Water of the fazenda for build_farm.py: the cacimba with its sarilho, the spring box that feeds a stone trough
through a bamboo bica, the monjolo (water-driven pounding mallet) and the little mill house with its overshot water
wheel.

All pieces draw in a local frame (origin on the ground, Blender Z up, Y = -Godot Z), placed by the caller's frame.
"""

import itertools
import math

from mathutils import Matrix

from build_town_houses import STONE, WOOD, WOOD_DARK_BAND, WOOD_LIGHT_BAND, Builder, srgb
from farm_colonial import (
    CAIADO,
    CREAM,
    IRON,
    ROOF_TINT,
    ROOF_UV,
    TIMBER,
    TIMBER_UV,
    entrance_door,
    hip_roof,
    rafter_tails,
    tube,
    window,
)
from shop_props_common import lathe

IDENTITY = Matrix.Identity(4)
BAMBOO = "B9B35E"
BAMBOO_NODE = "8E8A3E"
ROPE = "B89A62"
WOOD_BARE = "7A5438"
WATER_KEY = "water"


def bucket(b: Builder, frame: Matrix, position: tuple, radius: float = 0.17, height: float = 0.3) -> None:
    """Wooden bucket (balde) with two iron hoops and a rope handle."""
    lathe(b, [(radius * 0.8, 0.0), (radius, height), (radius * 0.92, height), (radius * 0.72, 0.03)], 10, "wood", WOOD["media"], frame, base=position, closed=True, uv=("band", *WOOD_DARK_BAND, 1.0))

    for level in (0.25, 0.78):
        b.cylinder((position[0], position[1], position[2] + height * level), radius * (0.82 + 0.18 * level) + 0.008, 0.025, 10, "metal", srgb(IRON), frame=frame)

    b.beam((position[0] - radius, position[1], position[2] + height), (position[0], position[1], position[2] + height + 0.2), 0.015, 0.015, "paint", srgb(ROPE), frame=frame, uv=None)
    b.beam((position[0], position[1], position[2] + height + 0.2), (position[0] + radius, position[1], position[2] + height), 0.015, 0.015, "paint", srgb(ROPE), frame=frame, uv=None)


def forked_post(b: Builder, frame: Matrix, x: float, y: float, height: float) -> None:
    """Rough post with a Y fork at the top that carries a horizontal pole."""
    pole = srgb(WOOD_BARE)

    b.cylinder((x, y, 0.0), 0.1, height - 0.2, 7, "wood", pole, top_radius=0.085, frame=frame, uv=TIMBER_UV)

    for side in (-1, 1):
        b.beam((x, y + side * 0.02, height - 0.25), (x + side * 0.0, y + side * 0.2, height + 0.08), 0.09, 0.09, "wood", pole, frame=frame, uv=None)

    b.box((x - 0.2, y - 0.2, 0.0), (x + 0.2, y + 0.2, 0.14), "stone", srgb(STONE["media"]), frame=frame)


def cacimba(b: Builder, frame: Matrix) -> None:
    """Hand-dug well with a masonry curb, a sarilho (windlass on two forked posts with a crank), rope and bucket,
    a second bucket on the curb. The curb is axis-aligned; the windlass runs along local X."""
    curb = [(0.95, 0.0), (0.95, 0.82), (0.66, 0.82), (0.66, 0.1)]

    lathe(b, curb, 14, "stone", STONE["media"], frame, closed=True)
    b.cylinder((0.0, 0.0, 0.82), 1.02, 0.1, 14, "trim", srgb(CREAM), frame=frame)
    b.cylinder((0.0, 0.0, 0.3), 0.66, 0.02, 14, WATER_KEY, srgb("5A8FA8"), frame=frame)

    for side in (-1, 1):
        forked_post(b, frame, side * 1.2, 0.0, 2.1)

    b.cylinder((-1.45, 0.0, 1.95), 0.11, 2.9, 8, "wood", srgb(WOOD["mel"]), frame=frame, axis="X", uv=TIMBER_UV)
    b.cylinder((-0.35, 0.0, 1.95), 0.16, 0.75, 10, "paint", srgb(ROPE), frame=frame, axis="X")
    b.beam((1.45, 0.0, 1.95), (1.45, 0.38, 1.95), 0.07, 0.07, "wood", srgb(WOOD_BARE), frame=frame, uv=None)
    b.cylinder((1.45, 0.38, 1.95), 0.035, 0.45, 6, "wood", srgb(WOOD_BARE), frame=frame, axis="X", uv=None)
    b.cylinder((0.0, 0.0, 1.05), 0.014, 0.9, 4, "paint", srgb(ROPE), frame=frame)
    bucket(b, frame, (-0.35, 0.0, 0.75))
    bucket(b, frame, (0.55, 0.78, 0.82))
    b.collider((-1.4, -1.0, 0.0), (1.4, 1.0, 0.9), frame=frame)


def bamboo_pipe(b: Builder, frame: Matrix, start: tuple, end: tuple, radius: float = 0.055) -> None:
    """Bamboo from start to end: cane segments with a darker ring at every node."""
    length = math.dist(start, end)
    segments = max(1, round(length / 0.55))
    steps = [tuple(start[axis] + (end[axis] - start[axis]) * index / segments for axis in range(3)) for index in range(segments + 1)]

    for first, second in zip(steps, steps[1:]):
        tube(b, first, second, radius, 8, "paint", BAMBOO, frame=frame)

    for node in steps[1:-1]:
        b.sphere(node, radius * 1.3, "paint", srgb(BAMBOO_NODE), scale=(1.0, 1.0, 0.45), frame=frame, segments=8)


def spring_box(b: Builder, frame: Matrix) -> None:
    """Whitewashed little masonry box over the spring with a tile cap and a bamboo bica coming out of its wall
    toward local +Y, ending over a stone trough (cocho) with water falling into it."""
    trough_y = 1.9

    b.box((-0.5, -0.5, 0.0), (0.5, 0.5, 0.35), "stone", srgb(STONE["media"]), frame=frame)
    b.box((-0.45, -0.45, 0.35), (0.45, 0.45, 1.1), "plaster", srgb(CAIADO), frame=frame)
    b.box((-0.55, -0.55, 1.1), (0.55, 0.55, 1.2), "trim", srgb(CREAM), frame=frame)
    b.hull([(-0.62, -0.62, 1.2), (0.62, -0.62, 1.2), (-0.62, 0.62, 1.2), (0.62, 0.62, 1.2), (0.0, -0.62, 1.5), (0.0, 0.62, 1.5)], "tiles", srgb(ROOF_TINT), frame=frame, uv=ROOF_UV)
    b.box((-0.18, 0.44, 0.44), (0.18, 0.5, 0.82), "glass", (1.0, 1.0, 1.0), frame=frame)
    bamboo_pipe(b, frame, (0.0, 0.5, 0.7), (0.0, 1.2, 0.62))
    b.cylinder((0.0, 1.2, 0.04), 0.022, 0.58, 6, WATER_KEY, srgb("8FC4D8"), frame=frame)
    trough(b, frame @ Matrix.Translation((0.0, trough_y, 0.0)), 2.4)
    b.collider((-0.65, -0.65, 0.0), (0.65, 0.65, 1.5), frame=frame)


def trough(b: Builder, frame: Matrix, length: float) -> None:
    """Cocho of dressed stone on two stone footings, water in the hollow, a chipped lip."""
    stone = srgb(STONE["clara"])

    for side in (-1, 1):
        b.box((side * (length / 2.0 - 0.3) - 0.2, -0.3, 0.0), (side * (length / 2.0 - 0.3) + 0.2, 0.3, 0.2), "stone", srgb(STONE["media"]), frame=frame)

    b.box((-length / 2.0, -0.38, 0.2), (length / 2.0, 0.38, 0.62), "stone", stone, frame=frame)
    b.box((-length / 2.0 - 0.04, -0.42, 0.58), (length / 2.0 + 0.04, 0.42, 0.66), "trim", srgb(CREAM), frame=frame)
    b.box((-length / 2.0 + 0.1, -0.28, 0.58), (length / 2.0 - 0.1, 0.28, 0.59), "paint", srgb("2E4A5A"), frame=frame)
    b.box((-length / 2.0 + 0.1, -0.28, 0.59), (length / 2.0 - 0.1, 0.28, 0.6), WATER_KEY, srgb("5A8FA8"), frame=frame)
    b.collider((-length / 2.0, -0.45, 0.0), (length / 2.0, 0.45, 0.66), frame=frame)


# ---------- monjolo ----------

def monjolo(b: Builder, frame: Matrix) -> None:
    """Monjolo: a hollow-log beam pivoting on two forked posts, a scoop at one end that the bamboo spout fills, a
    pestle at the other end that falls into the stump mortar when the scoop tips. Beam along local X; scoop at -X."""
    beam_wood = srgb(WOOD["mel"])
    pivot_z = 1.05
    scoop_end = (-1.55, 0.0, pivot_z + 0.28)
    pestle_end = (1.75, 0.0, pivot_z - 0.28)

    for side in (-1, 1):
        forked_post(b, frame, 0.0, side * 0.5, pivot_z + 0.2)

    b.cylinder((0.0, -0.58, pivot_z), 0.045, 1.16, 6, "metal", srgb(IRON), frame=frame, axis="Y", uv=None)
    tube(b, scoop_end, pestle_end, 0.12, 8, "wood", WOOD["mel"], frame=frame, uv=TIMBER_UV)
    b.box((-1.95, -0.2, pivot_z + 0.3), (-1.2, 0.2, pivot_z + 0.36), "wood", srgb(WOOD["media"]), frame=frame, uv=TIMBER_UV)

    for side in (-1, 1):
        b.box((-1.95, side * 0.2 - 0.025, pivot_z + 0.3), (-1.2, side * 0.2 + 0.025, pivot_z + 0.5), "wood", srgb(WOOD["media"]), frame=frame, uv=TIMBER_UV)

    b.box((-1.97, -0.2, pivot_z + 0.3), (-1.93, 0.2, pivot_z + 0.5), "wood", srgb(WOOD["media"]), frame=frame, uv=TIMBER_UV)
    b.cylinder((pestle_end[0], 0.0, 0.55), 0.09, pestle_end[2] - 0.5, 8, "wood", srgb(WOOD["escura"]), frame=frame, uv=TIMBER_UV)
    lathe(b, [(0.36, 0.0), (0.38, 0.1), (0.36, 0.5), (0.2, 0.48), (0.18, 0.4)], 12, "wood", WOOD["media"], frame, base=(pestle_end[0], 0.0, 0.0), closed=True, uv=("band", *WOOD_LIGHT_BAND, 1.0))
    bamboo_pipe(b, frame, (-3.1, 0.0, 2.15), (-1.7, 0.0, pivot_z + 0.9))
    forked_post(b, frame, -3.2, 0.0, 2.0)
    b.cylinder((-1.67, 0.0, pivot_z + 0.38), 0.02, 0.5, 6, WATER_KEY, srgb("8FC4D8"), frame=frame)
    b.collider((-0.3, -0.7, 0.0), (0.3, 0.7, 1.3), frame=frame)
    b.collider((pestle_end[0] - 0.4, -0.4, 0.0), (pestle_end[0] + 0.4, 0.4, 0.6), frame=frame)


# ---------- the mill ----------

MILL_WIDTH = 4.6
MILL_DEPTH = 4.0
MILL_BASE = 0.5
MILL_WALL_TOP = 3.0
WHEEL_RADIUS = 1.45
WHEEL_AXLE_Z = 1.75
WHEEL_PADDLES = 14


def water_wheel(b: Builder, frame: Matrix, width: float) -> None:
    """Overshot wheel turning around local X at the origin: two rims, spokes in two sets, buckets of boards, the axle."""
    wood = srgb(WOOD["media"])
    timber = srgb(TIMBER)
    iron = srgb(IRON)
    around_x = frame @ Matrix.Rotation(math.radians(90.0), 4, "Y")
    half = width / 2.0

    for rim in (-half, half):
        lathe(b, [(WHEEL_RADIUS - 0.12, rim - 0.05), (WHEEL_RADIUS, rim - 0.05), (WHEEL_RADIUS, rim + 0.05), (WHEEL_RADIUS - 0.12, rim + 0.05)], 14, "wood", WOOD["media"], around_x, closed=True, uv=("band", *WOOD_DARK_BAND, 1.0))

    for paddle in range(WHEEL_PADDLES):
        angle = 2.0 * math.pi * paddle / WHEEL_PADDLES
        inner = (0.0, math.cos(angle) * (WHEEL_RADIUS - 0.2), math.sin(angle) * (WHEEL_RADIUS - 0.2))
        outer = (0.0, math.cos(angle + 0.28) * (WHEEL_RADIUS - 0.02), math.sin(angle + 0.28) * (WHEEL_RADIUS - 0.02))

        b.beam((-half, inner[1], inner[2]), (half, inner[1], inner[2]), 0.045, 0.2, "wood", wood, frame=frame, uv=None)
        b.beam((-half, inner[1], inner[2]), (-half, outer[1], outer[2]), 0.045, 0.05, "wood", wood, frame=frame, uv=None)
        b.beam((half, inner[1], inner[2]), (half, outer[1], outer[2]), 0.045, 0.05, "wood", wood, frame=frame, uv=None)

    for rim, spoke in itertools.product((-half, half), range(6)):
        angle = math.pi * spoke / 6.0 * 2.0
        tip = (rim, math.cos(angle) * (WHEEL_RADIUS - 0.1), math.sin(angle) * (WHEEL_RADIUS - 0.1))

        b.beam((rim, 0.0, 0.0), tip, 0.09, 0.07, "wood", timber, frame=frame)

    b.cylinder((-half - 0.9, 0.0, 0.0), 0.14, width + 1.8, 8, "wood", timber, frame=frame, axis="X", uv=TIMBER_UV)
    b.cylinder((-half - 0.04, 0.0, 0.0), 0.2, 0.2, 8, "metal", iron, frame=frame, axis="X")
    b.cylinder((half - 0.16, 0.0, 0.0), 0.2, 0.2, 8, "metal", iron, frame=frame, axis="X")


def flume(b: Builder, frame: Matrix, length: float, top_z: float) -> None:
    """Wooden water channel on trestles running along local +X from the origin, water in it, ending in a spill."""
    wood = srgb(WOOD["media"])
    timber = srgb(TIMBER)
    posts = int(length / 1.4) + 1

    b.box((0.0, -0.28, top_z - 0.08), (length, 0.28, top_z), "wood", wood, frame=frame, uv=TIMBER_UV)

    for side in (-1, 1):
        low, high = sorted((side * 0.25, side * 0.31))

        b.box((0.0, low, top_z), (length, high, top_z + 0.3), "wood", wood, frame=frame, uv=TIMBER_UV)

    b.box((0.04, -0.25, top_z + 0.0), (length - 0.02, 0.25, top_z + 0.2), WATER_KEY, srgb("5A8FA8"), frame=frame)

    for index in range(posts):
        x = 0.3 + index * (length - 0.6) / max(1, posts - 1)

        for side in (-1, 1):
            b.box((x - 0.07, side * 0.38 - 0.07, 0.0), (x + 0.07, side * 0.38 + 0.07, top_z - 0.08), "wood", timber, frame=frame, uv=TIMBER_UV)

        b.box((x - 0.08, -0.45, top_z - 0.18), (x + 0.08, 0.45, top_z - 0.08), "wood", timber, frame=frame, uv=TIMBER_UV)

    b.cylinder((length - 0.05, 0.0, 1.9), 0.09, top_z - 1.9 + 0.1, 6, WATER_KEY, srgb("8FC4D8"), frame=frame)


def mill_house(b: Builder, frame: Matrix) -> None:
    """Little whitewashed mill house (door and window frames in the accent colour, hipped tile roof) with the wheel on
    its +X wall and the flume coming from the +X side, over a stream that runs under the wheel along local Y.
    Front at local -Y (like every facade, d = 0 there)."""
    half = MILL_WIDTH / 2.0
    frames = {"front": Matrix.Identity(4), "west": Matrix.Translation((-half, MILL_DEPTH / 2.0, 0.0)) @ Matrix.Rotation(-math.pi / 2.0, 4, "Z")}
    house = frame

    b.box((-half - 0.08, -0.08, 0.0), (half + 0.08, MILL_DEPTH + 0.08, MILL_BASE - 0.08), "stone", srgb(STONE["media"]), frame=house)
    b.box((-half, 0.0, MILL_BASE), (half, MILL_DEPTH, MILL_WALL_TOP), "plaster", srgb(CAIADO), frame=house)
    b.box((-half - 0.1, -0.1, MILL_BASE - 0.1), (half + 0.1, MILL_DEPTH + 0.1, MILL_BASE), "trim", srgb(CREAM), frame=house)
    b.collider((-half - 0.08, 0.0, 0.0), (half + 0.08, MILL_DEPTH + 0.08, MILL_WALL_TOP), frame=house)
    entrance_door(b, house @ Matrix.Translation((-half / 2.0, 0.0, MILL_BASE)), 0.0, 1.1, 2.0, double=False, fanlight=False)
    window(b, house, half / 2.0 + 0.2, MILL_BASE + 0.7, 0.8, 1.2, shutters=True, top="flat")
    window(b, house @ frames["west"], 0.0, MILL_BASE + 0.7, 0.8, 1.2, shutters=True, top="flat")
    hip_roof(b, half + 0.6, -0.6, MILL_DEPTH + 0.6, MILL_WALL_TOP + 0.12, 28.0, frame=house)
    rafter_tails(b, (half + 0.6, -0.6, MILL_DEPTH + 0.6), (half, 0.0, MILL_DEPTH), MILL_WALL_TOP + 0.12, spacing=0.7, frame=house)
    b.box((-half - 0.3, -0.28, 0.0), (half + 0.3, -0.02, 0.1), "stone", srgb(STONE["clara"]), frame=house)
