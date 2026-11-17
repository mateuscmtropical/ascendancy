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
from shop_props_common import lathe, ring

IDENTITY = Matrix.Identity(4)
BAMBOO = "B9B35E"
BAMBOO_NODE = "8E8A3E"
ROPE = "B89A62"
WOOD_BARE = "7A5438"
WATER_KEY = "water"
CURB_RADIUS = 0.95
CURB_TOP = 0.82
WELL_RADIUS = 0.66
SARILHO_POST_X = 1.2  # fora da capa da borda (raio 1,02)
AXLE_Z = 1.3  # altura do eixo: manivela entre 0,95 e 1,65 m, na mão de quem puxa
AXLE_RADIUS = 0.075
DRUM_RADIUS = 0.13
DRUM_HALF_LENGTH = 0.5
ROPE_RADIUS = 0.018
ROPE_TURNS = 11
CRANK_ARM = 0.34
BUCKET_BAIL_RISE = 0.16


def bucket(b: Builder, frame: Matrix, position: tuple, radius: float = 0.17, height: float = 0.3) -> None:
    """Wooden bucket (balde) of staves: three iron hoops, water inside, an iron bail standing up over the rim."""
    x, y, z = position
    bail_points = 7

    lathe(b, [(radius * 0.8, 0.0), (radius, height), (radius * 0.92, height), (radius * 0.72, 0.03)], 12, "wood", WOOD["media"], frame, base=position, closed=True, uv=("band", *WOOD_DARK_BAND, 1.0))
    b.cylinder((x, y, z + height * 0.68), radius * 0.86, 0.01, 12, WATER_KEY, srgb("5A8FA8"), frame=frame)

    for level in (0.12, 0.5, 0.88):
        ring(b, (x, y, z + height * level), radius * (0.8 + 0.2 * level) + 0.006, 0.012, "metal", IRON, frame, sides=12, tube_sides=4)

    for side in (-1, 1):
        b.box((x + side * radius - 0.018, y - 0.025, z + height - 0.07), (x + side * radius + 0.018, y + 0.025, z + height + 0.01), "metal", srgb(IRON), frame=frame)

    arc = [(x - math.cos(math.pi * index / (bail_points - 1)) * radius, y, z + height + math.sin(math.pi * index / (bail_points - 1)) * BUCKET_BAIL_RISE) for index in range(bail_points)]

    for start, end in zip(arc, arc[1:]):
        tube(b, start, end, 0.009, 4, "metal", IRON, frame=frame)


def forked_post(b: Builder, frame: Matrix, x: float, y: float, height: float) -> None:
    """Rough post with a Y fork at the top that carries a horizontal pole."""
    pole = srgb(WOOD_BARE)

    b.cylinder((x, y, 0.0), 0.1, height - 0.2, 7, "wood", pole, top_radius=0.085, frame=frame, uv=TIMBER_UV)

    for side in (-1, 1):
        b.beam((x, y + side * 0.02, height - 0.25), (x + side * 0.0, y + side * 0.2, height + 0.08), 0.09, 0.09, "wood", pole, frame=frame, uv=None)

    b.box((x - 0.2, y - 0.2, 0.0), (x + 0.2, y + 0.2, 0.14), "stone", srgb(STONE["media"]), frame=frame)


def cacimba(b: Builder, frame: Matrix) -> None:
    """Hand-dug well: masonry curb with a cream cap, and the sarilho over it. Two braced squared posts on stone
    footings tied by a crossbar carry a round axle in iron collars; the middle of the axle is a drum with the rope wound
    on it, the end past the +X post an iron crank with a wooden grip. The rope runs off the front of the drum
    down to a bucket just under the cap; a second bucket stands on the cap. Windlass along local X."""
    curb = [(CURB_RADIUS, 0.0), (CURB_RADIUS, CURB_TOP), (WELL_RADIUS, CURB_TOP), (WELL_RADIUS, 0.1)]
    cap_top = CURB_TOP + 0.1
    rope_y = DRUM_RADIUS + ROPE_RADIUS
    rope_x = DRUM_HALF_LENGTH - 0.1 - ROPE_TURNS * ROPE_RADIUS * 2.2
    hanging_bucket = (rope_x, rope_y, cap_top - 0.36)

    lathe(b, curb, 14, "stone", STONE["media"], frame, closed=True)
    b.cylinder((0.0, 0.0, CURB_TOP), CURB_RADIUS + 0.07, 0.1, 14, "trim", srgb(CREAM), frame=frame)
    b.cylinder((0.0, 0.0, 0.3), WELL_RADIUS, 0.02, 14, WATER_KEY, srgb("5A8FA8"), frame=frame)

    for side in (-1, 1):
        sarilho_post(b, frame, side * SARILHO_POST_X)

    b.box((-SARILHO_POST_X - 0.1, -0.07, AXLE_Z + 0.16), (SARILHO_POST_X + 0.1, 0.07, AXLE_Z + 0.28), "wood", srgb(TIMBER), frame=frame, uv=TIMBER_UV)
    b.cylinder((-SARILHO_POST_X - 0.14, 0.0, AXLE_Z), AXLE_RADIUS, 2.0 * SARILHO_POST_X + 0.3, 12, "wood", srgb(WOOD["mel"]), frame=frame, axis="X", uv=TIMBER_UV)
    b.cylinder((-DRUM_HALF_LENGTH, 0.0, AXLE_Z), DRUM_RADIUS, 2.0 * DRUM_HALF_LENGTH, 14, "wood", srgb(WOOD["media"]), frame=frame, axis="X", uv=TIMBER_UV)

    for side in (-1, 1):
        b.cylinder((side * DRUM_HALF_LENGTH - 0.025, 0.0, AXLE_Z), DRUM_RADIUS + 0.05, 0.05, 14, "wood", srgb(WOOD["escura"]), frame=frame, axis="X", uv=TIMBER_UV)

    for side, offset in itertools.product((-1, 1), (-0.12, 0.12)):
        ring(b, (side * SARILHO_POST_X + offset, 0.0, AXLE_Z), AXLE_RADIUS + 0.008, 0.014, "metal", IRON, frame, sides=12, tube_sides=4, axis="X")

    for turn in range(ROPE_TURNS):
        ring(b, (DRUM_HALF_LENGTH - 0.1 - turn * ROPE_RADIUS * 2.2, 0.0, AXLE_Z), DRUM_RADIUS + ROPE_RADIUS, ROPE_RADIUS, "paint", ROPE, frame, sides=14, tube_sides=4, axis="X")

    crank(b, frame, SARILHO_POST_X + 0.2)
    b.cylinder((rope_x, rope_y, hanging_bucket[2] + 0.3 + BUCKET_BAIL_RISE), ROPE_RADIUS, AXLE_Z - hanging_bucket[2] - 0.3 - BUCKET_BAIL_RISE, 6, "paint", srgb(ROPE), frame=frame)
    bucket(b, frame, hanging_bucket)
    bucket(b, frame, (0.48, 0.7, cap_top))
    b.collider((-CURB_RADIUS - 0.07, -CURB_RADIUS - 0.07, 0.0), (CURB_RADIUS + 0.07, CURB_RADIUS + 0.07, cap_top), frame=frame)

    for side in (-1, 1):
        b.collider((side * SARILHO_POST_X - 0.18, -0.18, 0.0), (side * SARILHO_POST_X + 0.18, 0.18, AXLE_Z + 0.28), frame=frame)


def sarilho_post(b: Builder, frame: Matrix, x: float) -> None:
    """Squared post on a stone footing, braced front and back (the side toward the crank stays clear), the axle
    passing through it at AXLE_Z."""
    b.box((x - 0.18, -0.18, 0.0), (x + 0.18, 0.18, 0.2), "stone", srgb(STONE["media"]), frame=frame)
    b.box((x - 0.08, -0.08, 0.2), (x + 0.08, 0.08, AXLE_Z + 0.16), "wood", srgb(TIMBER), frame=frame, uv=TIMBER_UV)

    for side in (-1, 1):
        b.beam((x, side * 0.5, 0.16), (x, side * 0.07, 0.95), 0.07, 0.07, "wood", srgb(TIMBER), frame=frame, uv=TIMBER_UV)
        b.box((x - 0.1, side * 0.5 - 0.1, 0.0), (x + 0.1, side * 0.5 + 0.1, 0.16), "stone", srgb(STONE["media"]), frame=frame)


def crank(b: Builder, frame: Matrix, x: float) -> None:
    """Iron crank on the axle end at x: a hub, an arm hanging down and a wooden grip sticking out along +X."""
    grip_z = AXLE_Z - CRANK_ARM

    b.cylinder((x - 0.06, 0.0, AXLE_Z), AXLE_RADIUS + 0.025, 0.1, 10, "metal", srgb(IRON), frame=frame, axis="X")
    b.box((x + 0.02, -0.03, grip_z - 0.03), (x + 0.06, 0.03, AXLE_Z + 0.03), "metal", srgb(IRON), frame=frame)
    b.cylinder((x + 0.02, 0.0, grip_z), 0.014, 0.3, 6, "metal", srgb(IRON), frame=frame, axis="X")
    b.cylinder((x + 0.07, 0.0, grip_z), 0.032, 0.2, 8, "wood", srgb(WOOD["escura"]), frame=frame, axis="X", uv=TIMBER_UV)


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
