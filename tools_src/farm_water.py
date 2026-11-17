"""Water of the fazenda for build_farm.py: the cacimba with its sarilho, the spring box that feeds a stone trough
through a bamboo bica, the monjolo (water-driven pounding mallet) and the little mill house with its overshot water
wheel.

All pieces draw in a local frame (origin on the ground, Blender Z up, Y = -Godot Z), placed by the caller's frame.
"""

import itertools
import math

from mathutils import Matrix, Vector

from build_town_houses import STONE, WHITE, WOOD, WOOD_DARK_BAND, WOOD_LIGHT_BAND, Builder, srgb
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
ROPE = "8A6A40"
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
ROPE_RADIUS = 0.02
ROPE_TURNS = 8
ROPE_PITCH = 0.052  # voltas com um vão entre elas: lê como corda enrolada, não como um tubo liso
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
    rope_x = DRUM_HALF_LENGTH - 0.1 - ROPE_TURNS * ROPE_PITCH
    hanging_bucket = (rope_x, rope_y, cap_top - 0.36)

    lathe(b, curb, 14, "stone", STONE["media"], frame, closed=True)
    lathe(b, [(WELL_RADIUS - 0.03, CURB_TOP), (CURB_RADIUS + 0.07, CURB_TOP), (CURB_RADIUS + 0.07, cap_top), (WELL_RADIUS - 0.03, cap_top)], 14, "trim", CREAM, frame, closed=True)
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
        ring(b, (DRUM_HALF_LENGTH - 0.1 - turn * ROPE_PITCH, 0.0, AXLE_Z), DRUM_RADIUS + ROPE_RADIUS, ROPE_RADIUS, "paint", ROPE, frame, sides=14, tube_sides=6, axis="X")

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

MONJOLO_PIVOT_Z = 1.05
MONJOLO_FEED = (-3.15, 0.0, 2.17)  # topo da forquilha onde a bica de bambu chega ao monjolo
MONJOLO_SCOOP_END = (-1.55, 0.0, 0.28)  # pontas do braço a partir do pino, em repouso (pilão no fundo)
MONJOLO_PESTLE_END = (1.75, 0.0, -0.28)
MONJOLO_MORTAR_HOLLOW = 0.4  # fundo da boca do pilão de toco, onde a mão do pilão bate


def monjolo(b: Builder, frame: Matrix) -> None:
    """Fixed part of the monjolo: two forked posts with the iron pin, the stump mortar, the forked post that carries
    the bamboo spout and the water falling from it into the scoop. The beam swings (monjolo_beam, its own model,
    sidecar marker monjolo_beam at the pin). Beam along local X; scoop at -X."""
    pestle_x = MONJOLO_PESTLE_END[0]
    spout_end = (-1.7, 0.0, MONJOLO_PIVOT_Z + 0.9)

    for side in (-1, 1):
        forked_post(b, frame, 0.0, side * 0.5, MONJOLO_PIVOT_Z + 0.2)

    b.cylinder((0.0, -0.58, MONJOLO_PIVOT_Z), 0.045, 1.16, 6, "metal", srgb(IRON), frame=frame, axis="Y", uv=None)
    lathe(b, [(0.36, 0.0), (0.38, 0.1), (0.36, 0.5), (0.2, 0.48), (0.18, MONJOLO_MORTAR_HOLLOW)], 12, "wood", WOOD["media"], frame, base=(pestle_x, 0.0, 0.0), closed=True, uv=("band", *WOOD_LIGHT_BAND, 1.0))
    bamboo_pipe(b, frame, MONJOLO_FEED, spout_end)
    forked_post(b, frame, MONJOLO_FEED[0] - 0.05, 0.0, MONJOLO_FEED[2] - 0.17)
    b.cylinder((spout_end[0] + 0.03, 0.0, MONJOLO_PIVOT_Z + 0.38), 0.02, 0.5, 6, WATER_KEY, srgb("8FC4D8"), frame=frame)
    b.marker("monjolo_beam", (0.0, 0.0, MONJOLO_PIVOT_Z), frame)
    b.collider((-0.3, -0.7, 0.0), (0.3, 0.7, 1.3), frame=frame)
    b.collider((pestle_x - 0.4, -0.4, 0.0), (pestle_x + 0.4, 0.4, 0.6), frame=frame)
    b.collider((MONJOLO_FEED[0] - 0.25, -0.25, 0.0), (MONJOLO_FEED[0] + 0.15, 0.25, MONJOLO_FEED[2]), frame=frame)


def monjolo_beam(b: Builder, frame: Matrix) -> None:
    """The swinging beam of the monjolo, origin at the pin: a hollow log with the scoop (an open plank box) on the -X
    end and the pestle hanging from the +X end down into the mortar hollow. In rest pose the pestle is down."""
    scoop_floor = MONJOLO_SCOOP_END[2] + 0.02
    pestle_x, _pestle_y, pestle_z = MONJOLO_PESTLE_END
    pestle_bottom = MONJOLO_MORTAR_HOLLOW + 0.02 - MONJOLO_PIVOT_Z

    tube(b, MONJOLO_SCOOP_END, MONJOLO_PESTLE_END, 0.12, 8, "wood", WOOD["mel"], frame=frame, uv=TIMBER_UV)
    b.box((-1.95, -0.2, scoop_floor), (-1.2, 0.2, scoop_floor + 0.06), "wood", srgb(WOOD["media"]), frame=frame, uv=TIMBER_UV)

    for side in (-1, 1):
        b.box((-1.95, side * 0.2 - 0.025, scoop_floor), (-1.2, side * 0.2 + 0.025, scoop_floor + 0.2), "wood", srgb(WOOD["media"]), frame=frame, uv=TIMBER_UV)

    b.box((-1.97, -0.2, scoop_floor), (-1.93, 0.2, scoop_floor + 0.2), "wood", srgb(WOOD["media"]), frame=frame, uv=TIMBER_UV)
    b.cylinder((pestle_x, 0.0, pestle_bottom), 0.09, pestle_z + 0.05 - pestle_bottom, 8, "wood", srgb(WOOD["escura"]), frame=frame, uv=TIMBER_UV)
    ring(b, (pestle_x, 0.0, pestle_bottom + 0.06), 0.095, 0.012, "iron", "FFFFFF", frame, sides=10, tube_sides=4)


# ---------- the mill ----------

MILL_WIDTH = 4.6
MILL_DEPTH = 4.0
MILL_BASE = 0.5
MILL_WALL_TOP = 3.0
MILL_EAVE = 0.6
WHEEL_RADIUS = 1.45
WHEEL_WIDTH = 0.9
WHEEL_AXLE_Z = 1.75
WHEEL_PADDLES = 14
WHEEL_AXLE_REACH = WHEEL_WIDTH / 2.0 + 0.9  # meio eixo, do centro da roda até cada ponta
WHEEL_X = MILL_WIDTH / 2.0 + MILL_EAVE + 0.6  # aro de dentro fora do beiral (o telhado passa da parede 0,6 m)
WHEEL_Y = MILL_DEPTH / 2.0
FLUME_TOP = WHEEL_AXLE_Z + WHEEL_RADIUS + 0.15  # fundo da calha 7 cm acima do topo da roda
FLUME_HALF_WIDTH = 0.31
FLUME_START_Y = MILL_DEPTH + 6.0  # caixa d'água de pedra atrás da casa, de onde a calha sai
FLUME_LAST_POST_Y = WHEEL_Y + WHEEL_RADIUS + 0.55  # cavalete mais perto da roda; dali a calha vai em balanço com mão-francesa
FLUME_SPILL_Y = WHEEL_Y - 0.15  # a água cai logo depois do topo, do lado da frente: a roda gira com o topo para -Y
CHANNEL_INNER = (MILL_WIDTH / 2.0 + 0.08, WHEEL_X + WHEEL_AXLE_REACH - 0.6)  # do embasamento da casa até o muro de fora
CHANNEL_Y = (-3.2, WHEEL_Y + WHEEL_RADIUS + 0.15)
CHANNEL_KERB = (0.25, 0.25)  # largura e altura dos muretes do rego
CHANNEL_WATER = 0.13
POND_RADIUS = 1.55
POND_Y = CHANNEL_Y[0] - POND_RADIUS + 0.05
POND_RIM = 0.25
CHANNEL_INTO_POND = POND_Y + 0.9  # muretes do rego entram na borda do tanque até aqui: nos cantos a borda curva fica mais longe
MILL_FOOTPRINT = (-MILL_WIDTH / 2.0 - MILL_EAVE - 0.3, WHEEL_X + WHEEL_AXLE_REACH + 0.3, POND_Y - POND_RADIUS - 0.3, FLUME_START_Y + 1.7)  # x, y locais sem tufo de grama
MONJOLO_FOOTPRINT = (MONJOLO_FEED[0] - 0.4, MONJOLO_PESTLE_END[0] + 0.6, -1.3, 1.0)


def water_wheel(b: Builder, frame: Matrix) -> None:
    """Overshot wheel turning around local X at the origin: two rims, spokes in two sets, buckets of boards, the axle
    with its iron hubs. Its own model (water_wheel.gltf): features/hub/water_wheel.gd turns it. The hubs use the
    farm builder's untinted "iron" so the mesh has a neutral first surface."""
    wood = srgb(WOOD["media"])
    timber = srgb(TIMBER)
    around_x = frame @ Matrix.Rotation(math.radians(90.0), 4, "Y")
    half = WHEEL_WIDTH / 2.0

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

    b.cylinder((-WHEEL_AXLE_REACH, 0.0, 0.0), 0.14, 2.0 * WHEEL_AXLE_REACH, 8, "wood", timber, frame=frame, axis="X", uv=TIMBER_UV)
    b.cylinder((-half - 0.04, 0.0, 0.0), 0.2, 0.2, 8, "iron", WHITE, frame=frame, axis="X")
    b.cylinder((half - 0.16, 0.0, 0.0), 0.2, 0.2, 8, "iron", WHITE, frame=frame, axis="X")


def flume(b: Builder, frame: Matrix, length: float, supported: float, spill_bottom: float) -> None:
    """Wooden water channel running along local +X from the origin with water in it: trestles up to `supported`, the
    rest cantilevered on knee braces from the last trestle, and a spill falling from the open end to `spill_bottom`."""
    wood = srgb(WOOD["media"])
    timber = srgb(TIMBER)
    top_z = FLUME_TOP
    posts = math.ceil((supported - 0.3) / 1.4) + 1

    b.box((0.0, -0.28, top_z - 0.08), (length, 0.28, top_z), "wood", wood, frame=frame, uv=TIMBER_UV)

    for side in (-1, 1):
        low, high = sorted((side * 0.25, side * FLUME_HALF_WIDTH))

        b.box((0.0, low, top_z), (length, high, top_z + 0.3), "wood", wood, frame=frame, uv=TIMBER_UV)

    b.box((0.0, -0.25, top_z), (length - 0.02, 0.25, top_z + 0.2), WATER_KEY, srgb("5A8FA8"), frame=frame)
    b.cylinder((length - 0.08, 0.0, spill_bottom), 0.07, top_z + 0.2 - spill_bottom, 6, WATER_KEY, srgb("8FC4D8"), frame=frame)

    for index in range(posts):
        x = 0.3 + index * (supported - 0.3) / max(1, posts - 1)

        for side in (-1, 1):
            b.box((x - 0.07, side * 0.38 - 0.07, 0.0), (x + 0.07, side * 0.38 + 0.07, top_z - 0.08), "wood", timber, frame=frame, uv=TIMBER_UV)
            b.box((x - 0.14, side * 0.38 - 0.14, 0.0), (x + 0.14, side * 0.38 + 0.14, 0.12), "stone", srgb(STONE["media"]), frame=frame)

        b.box((x - 0.08, -0.45, top_z - 0.18), (x + 0.08, 0.45, top_z - 0.08), "wood", timber, frame=frame, uv=TIMBER_UV)
        b.collider((x - 0.15, -0.53, 0.0), (x + 0.15, 0.53, top_z), frame=frame)

    for side in (-1, 1):
        b.beam((supported, side * 0.38, top_z - 1.35), (supported + 0.8, side * 0.38, top_z - 0.08), 0.08, 0.08, "wood", timber, frame=frame, uv=TIMBER_UV)


def head_tank(b: Builder, frame: Matrix) -> None:
    """Stone cistern the flume starts from, standing on the ground behind it (local +Y), water up to the coping."""
    top_z = FLUME_TOP + 0.3
    half = 0.7

    b.box((-half, 0.0, 0.0), (half, 2.0 * half, top_z - 0.1), "stone", srgb(STONE["media"]), frame=frame)
    b.box((-half - 0.06, -0.06, top_z - 0.1), (half + 0.06, 2.0 * half + 0.06, top_z), "trim", srgb(CREAM), frame=frame)
    b.box((-half + 0.12, 0.12, top_z - 0.12), (half - 0.12, 2.0 * half - 0.12, top_z - 0.1 + 0.005), WATER_KEY, srgb("5A8FA8"), frame=frame)
    b.collider((-half - 0.06, -0.06, 0.0), (half + 0.06, 2.0 * half + 0.06, top_z), frame=frame)


def tailrace(b: Builder, frame: Matrix) -> None:
    """Stone channel (rego) under the wheel along local Y: the house base is its inner wall beside the house, low
    kerbs elsewhere, an end wall behind the wheel and a round stone tank (tanque) in front that it empties into.
    A stone pier on the outer kerb carries the far end of the wheel axle in an iron bearing."""
    inner_x, outer_x = CHANNEL_INNER
    start_y, end_y = CHANNEL_Y
    kerb_width, kerb_height = CHANNEL_KERB
    stone = srgb(STONE["media"])
    pier_x = WHEEL_X + WHEEL_AXLE_REACH - 0.3  # a ponta do eixo passa 6 cm do pilar: nada de face rente girando

    b.box((outer_x, CHANNEL_INTO_POND, 0.0), (outer_x + kerb_width, end_y + kerb_width, kerb_height), "stone", stone, frame=frame)
    b.box((inner_x - kerb_width, end_y, 0.0), (outer_x, end_y + kerb_width, kerb_height), "stone", stone, frame=frame)

    b.box((inner_x - kerb_width, CHANNEL_INTO_POND, 0.0), (inner_x, 0.0, kerb_height), "stone", stone, frame=frame)

    b.box((inner_x, start_y - 0.2, 0.01), (outer_x, end_y, CHANNEL_WATER - 0.015), "paint", srgb("2E4A5A"), frame=frame)
    b.box((inner_x, start_y - 0.2, CHANNEL_WATER - 0.015), (outer_x, end_y, CHANNEL_WATER), WATER_KEY, srgb("5A8FA8"), frame=frame)
    b.collider((outer_x, start_y, 0.0), (outer_x + kerb_width, end_y + kerb_width, kerb_height), frame=frame)
    b.collider((inner_x - kerb_width, start_y, 0.0), (inner_x, 0.0, kerb_height), frame=frame)
    b.collider((inner_x - kerb_width, end_y, 0.0), (outer_x, end_y + kerb_width, kerb_height), frame=frame)

    b.box((pier_x - 0.2, WHEEL_Y - 0.3, 0.0), (pier_x + 0.2, WHEEL_Y + 0.3, WHEEL_AXLE_Z - 0.26), "stone", srgb(STONE["clara"]), frame=frame)
    b.box((pier_x - 0.24, WHEEL_Y - 0.34, WHEEL_AXLE_Z - 0.26), (pier_x + 0.24, WHEEL_Y + 0.34, WHEEL_AXLE_Z - 0.16), "trim", srgb(CREAM), frame=frame)
    b.collider((pier_x - 0.24, WHEEL_Y - 0.34, 0.0), (pier_x + 0.24, WHEEL_Y + 0.34, WHEEL_AXLE_Z), frame=frame)

    for bearing_x in (pier_x - 0.1, MILL_WIDTH / 2.0 + 0.04):
        b.box((bearing_x - 0.08, WHEEL_Y - 0.22, WHEEL_AXLE_Z - 0.18), (bearing_x + 0.08, WHEEL_Y + 0.22, WHEEL_AXLE_Z - 0.13), "metal", srgb(IRON), frame=frame)
        ring(b, (bearing_x, WHEEL_Y, WHEEL_AXLE_Z), 0.16, 0.025, "metal", IRON, frame, sides=12, tube_sides=4, axis="X")

    pond = frame @ Matrix.Translation((WHEEL_X - 0.15, POND_Y, 0.0))

    lathe(b, [(POND_RADIUS, 0.0), (POND_RADIUS, 0.3), (POND_RADIUS - POND_RIM, 0.3), (POND_RADIUS - POND_RIM, 0.02)], 18, "stone", STONE["media"], pond, closed=True)
    b.cylinder((0.0, 0.0, 0.01), POND_RADIUS - POND_RIM, 0.005, 18, "paint", srgb("2E4A5A"), frame=pond)
    b.cylinder((0.0, 0.0, CHANNEL_WATER - 0.02), POND_RADIUS - POND_RIM, 0.01, 18, WATER_KEY, srgb("5A8FA8"), frame=pond)
    b.collider((-POND_RADIUS, -POND_RADIUS, 0.0), (POND_RADIUS, POND_RADIUS, 0.3), frame=pond)


def mill_house(b: Builder, frame: Matrix) -> None:
    """Little whitewashed mill house (door and window frames in the accent colour, hipped tile roof). Front at local
    -Y (like every facade, d = 0 there); the wheel turns past the +X wall."""
    half = MILL_WIDTH / 2.0
    west = frame @ Matrix.Translation((-half, MILL_DEPTH / 2.0, 0.0)) @ Matrix.Rotation(-math.pi / 2.0, 4, "Z")

    b.box((-half - 0.08, -0.08, 0.0), (half + 0.08, MILL_DEPTH + 0.08, MILL_BASE - 0.08), "stone", srgb(STONE["media"]), frame=frame)
    b.box((-half, 0.0, MILL_BASE), (half, MILL_DEPTH, MILL_WALL_TOP), "plaster", srgb(CAIADO), frame=frame)
    b.box((-half - 0.1, -0.1, MILL_BASE - 0.1), (half + 0.1, MILL_DEPTH + 0.1, MILL_BASE), "trim", srgb(CREAM), frame=frame)
    b.collider((-half - 0.08, 0.0, 0.0), (half + 0.08, MILL_DEPTH + 0.08, MILL_WALL_TOP), frame=frame)
    entrance_door(b, frame @ Matrix.Translation((-half / 2.0, 0.0, MILL_BASE)), 0.0, 1.1, 2.0, double=False, fanlight=False)
    window(b, frame, half / 2.0 + 0.2, MILL_BASE + 0.7, 0.8, 1.2, shutters=True, top="flat")
    window(b, west, 0.0, MILL_BASE + 0.7, 0.8, 1.2, shutters=True, top="flat")
    hip_roof(b, half + MILL_EAVE, -MILL_EAVE, MILL_DEPTH + MILL_EAVE, MILL_WALL_TOP + 0.12, 28.0, frame=frame)
    rafter_tails(b, (half + MILL_EAVE, -MILL_EAVE, MILL_DEPTH + MILL_EAVE), (half, 0.0, MILL_DEPTH), MILL_WALL_TOP + 0.12, spacing=0.7, frame=frame)
    b.box((-half - 0.3, -0.28, 0.0), (-0.1, -0.02, 0.1), "stone", srgb(STONE["clara"]), frame=frame)


def water_mill(b: Builder, frame: Matrix) -> None:
    """The mill: the house, the stone tank behind it, the flume on trestles carrying the water to the top of the
    wheel, and the rego under the wheel into the tanque in front. The wheel itself is water_wheel.gltf, placed by the
    scene at the sidecar marker water_wheel (its axle)."""
    flume_frame = frame @ Matrix.Translation((WHEEL_X, FLUME_START_Y, 0.0)) @ Matrix.Rotation(-math.pi / 2.0, 4, "Z")
    flume_length = FLUME_START_Y - FLUME_SPILL_Y
    spill_bottom = WHEEL_AXLE_Z + WHEEL_RADIUS - 0.3
    wheel_reach = WHEEL_RADIUS + 0.05

    mill_house(b, frame)
    tailrace(b, frame)
    head_tank(b, frame @ Matrix.Translation((WHEEL_X, FLUME_START_Y, 0.0)))
    flume(b, flume_frame, flume_length, FLUME_START_Y - FLUME_LAST_POST_Y, spill_bottom)
    b.marker("water_wheel", (WHEEL_X, WHEEL_Y, WHEEL_AXLE_Z), frame)
    b.collider((WHEEL_X - WHEEL_WIDTH / 2.0 - 0.05, WHEEL_Y - wheel_reach, WHEEL_AXLE_Z - wheel_reach), (WHEEL_X + WHEEL_WIDTH / 2.0 + 0.05, WHEEL_Y + wheel_reach, WHEEL_AXLE_Z + wheel_reach), frame=frame)


def flume_tap(frame: Matrix, target: tuple) -> tuple:
    """Point on the flume's +X wall (mill frame) level with a world point, a little under the water line: where a
    bamboo branch taking water off the flume toward `target` starts. Returns world (Blender) coords."""
    local_target = frame.inverted() @ Vector(target)
    side = 1.0 if local_target.x > WHEEL_X else -1.0
    tap = Vector((WHEEL_X + side * FLUME_HALF_WIDTH, local_target.y, FLUME_TOP + 0.12))

    return tuple(frame @ tap)
