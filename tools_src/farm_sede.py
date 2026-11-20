"""The sede (casa-grande) of the fazenda for build_farm.py: whitewashed single storey on a stone plinth, tall shuttered
windows in an even rhythm, a hipped capa-e-canal roof on exposed rafter tails, a deep veranda with turned posts and a
stone stair, a chimney. Origin at the middle of the front wall at ground level; the front faces -d (Godot +Z)."""

import itertools
import math

from mathutils import Matrix

from build_town_houses import STONE, WOOD, Builder, Opening, blender_to_godot, srgb
from farm_colonial import (
    ACCENT_LIGHT,
    CAIADO,
    CREAM,
    PLANK_UV,
    ROOF_RIB_TINT,
    ROOF_TINT,
    ROOF_UV,
    TIMBER,
    TIMBER_UV,
    balustrade_run,
    entrance_door,
    hip_roof,
    rafter_tails,
    slope_ribs,
    solid_hull,
    stone_stair,
    turned_post,
    wall_frames,
    window,
)
from farm_sede_rooms import WALL, build_rooms, hollow_wall
from shop_props_common import lathe

BASE = 0.9  # stone plinth: the floor of the house and of the veranda
WALL_HEIGHT = 3.9
WALL_TOP = BASE + WALL_HEIGHT
NIGHT_AMBIENT = 0.05  # ambient of the rooms at night, lit by their oil lamps (casarão wings use 0.08)
EAVE = WALL_TOP + 0.18
OVERHANG = 0.9
HIP_PITCH = 27.0
VERANDA_DEPTH = 3.0
VERANDA_ROOF_REACH = 3.4  # from the wall to the veranda eave
VERANDA_PITCH = 12.0
VERANDA_POST_D = -(VERANDA_DEPTH - 0.25)
WINDOW_BOTTOM = BASE + 0.5
WINDOW_SIZE = (1.0, 2.3)
BAY = 2.4
STAIR_STEPS = 5
STAIR_TREAD = 0.34
STAIR_HALF_WIDTH = 1.5
ROOF_THICKNESS = 0.16
IDENTITY = Matrix.Identity(4)
WINDOW_AXES = (-3.0 * BAY, -2.0 * BAY, -BAY, BAY, 2.0 * BAY, 3.0 * BAY)
END_WINDOW_AXES = (-2.35, 2.35)
FRONT_DOOR = (1.5, 2.4)  # (width, leaf height)
BACK_DOOR = (1.3, 2.3)
CHIMNEY = (-5.9, 5.2)  # over the kitchen range (farm_sede_rooms.py)
TRIM_STRIP_UV = ("band", 0.44, 0.66, 1.0)


def corner_strips(b: Builder, frame: Matrix, half: float, extend: float) -> None:
    """Raised cream pilaster strips (cunhais) up both ends of a wall, each with a base block."""
    for side in (-1, 1):
        low, high = sorted((side * (half - 0.5), side * (half + extend)))

        b.box((low, -0.07, BASE), (high, 0.0, WALL_TOP - 0.1), "trim", srgb(CREAM), frame=frame, uv=TRIM_STRIP_UV)
        b.box((low - 0.03, -0.1, BASE), (high + 0.03, 0.0, BASE + 0.3), "trim", srgb(CREAM), frame=frame)


def cornice(b: Builder, frame: Matrix, half: float) -> None:
    """Stepped moulding (cimalha) at the top of a wall."""
    b.box((-half - 0.12, -0.14, WALL_TOP - 0.16), (half + 0.12, 0.0, WALL_TOP - 0.04), "trim", srgb(CREAM), frame=frame, uv=TRIM_STRIP_UV)
    b.box((-half - 0.2, -0.26, WALL_TOP - 0.04), (half + 0.2, 0.0, WALL_TOP + 0.08), "trim", srgb(CAIADO), frame=frame, uv=TRIM_STRIP_UV)
    b.box((-half - 0.2, -0.26, WALL_TOP + 0.08), (half + 0.2, -0.1, WALL_TOP + 0.14), "trim", srgb(CREAM), frame=frame)


def front_wall(b: Builder, frame: Matrix) -> list:
    fan_height = FRONT_DOOR[0] * 0.32 + 0.1

    for u in WINDOW_AXES:
        window(b, frame, u, WINDOW_BOTTOM, *WINDOW_SIZE, inside_glass=True)

    entrance_door(b, frame @ Matrix.Translation((0.0, 0.0, BASE)), 0.0, *FRONT_DOOR, open_into=WALL)

    return window_openings(WINDOW_AXES) + [Opening(0.0, FRONT_DOOR[0], BASE, FRONT_DOOR[1] + fan_height + 0.12, "segment")]


def back_wall(b: Builder, frame: Matrix) -> list:
    for u in WINDOW_AXES:
        window(b, frame, u, WINDOW_BOTTOM, *WINDOW_SIZE, inside_glass=True)

    entrance_door(b, frame @ Matrix.Translation((0.0, 0.0, BASE)), 0.0, *BACK_DOOR, double=False, fanlight=False, open_into=WALL)
    stone_stair(b, frame, 0.8, BASE, 0.0, 3, 0.36, name="BackStair")

    return window_openings(WINDOW_AXES) + [Opening(0.0, BACK_DOOR[0], BASE, BACK_DOOR[1], "flat")]


def end_wall(b: Builder, frame: Matrix) -> list:
    for u in END_WINDOW_AXES:
        window(b, frame, u, WINDOW_BOTTOM, *WINDOW_SIZE, inside_glass=True)

    return window_openings(END_WINDOW_AXES)


def window_openings(axes: tuple) -> list:
    return [Opening(u, WINDOW_SIZE[0], WINDOW_BOTTOM, WINDOW_SIZE[1], "segment") for u in axes]


WALL_DRAWERS = {"front": front_wall, "back": back_wall, "west": end_wall, "east": end_wall}


def veranda(b: Builder, half: float) -> None:
    """Deck of boards on a stone base, eight turned posts under a beam, balustrade, a sloped ceiling and roof, and a
    stone stair at the middle with its cheek walls."""
    stone = srgb(STONE["clara"])
    wood = srgb(WOOD["media"])
    deck_top = BASE
    boards = 12
    board = VERANDA_DEPTH / boards
    post_us = [side * u for side in (-1, 1) for u in (2.2, 4.2, 6.2, 8.2)]
    beam_z = deck_top + 2.54
    roof_half = half + 0.55
    eave = beam_z + 0.06

    b.box((-half - 0.1, -VERANDA_DEPTH, 0.0), (half + 0.1, 0.0, deck_top - 0.1), "stone", stone)
    b.box((-half - 0.16, -VERANDA_DEPTH - 0.06, deck_top - 0.2), (half + 0.16, 0.0, deck_top - 0.08), "trim", srgb(CREAM))

    for index in range(boards):
        b.box((-half, -VERANDA_DEPTH + index * board + 0.004, deck_top - 0.1), (half, -VERANDA_DEPTH + (index + 1) * board - 0.004, deck_top), "wood", wood, uv=PLANK_UV)

    b.collider((-half, -VERANDA_DEPTH, deck_top - 0.2), (half, 0.0, deck_top), name="WoodFloor")

    for u in post_us:
        turned_post(b, IDENTITY, u, VERANDA_POST_D, deck_top, beam_z)

    b.box((-half - 0.1, VERANDA_POST_D - 0.16, beam_z), (half + 0.1, VERANDA_POST_D + 0.16, beam_z + 0.22), "paint", srgb(CAIADO))
    b.box((-half - 0.1, VERANDA_POST_D - 0.2, beam_z + 0.22), (half + 0.1, VERANDA_POST_D + 0.2, beam_z + 0.3), "trim", srgb(CREAM))
    railings(b, deck_top)
    veranda_roof(b, roof_half, eave)
    stone_stair(b, IDENTITY, STAIR_HALF_WIDTH, deck_top, -VERANDA_DEPTH, STAIR_STEPS, STAIR_TREAD)


def railings(b: Builder, deck_top: float) -> None:
    """Balustrade each side of the stair opening and along both ends, with a collider per run."""
    spans = [((-8.2, VERANDA_POST_D), (-2.2, VERANDA_POST_D)), ((2.2, VERANDA_POST_D), (8.2, VERANDA_POST_D)), ((-8.2, VERANDA_POST_D), (-8.2, 0.0)), ((8.2, VERANDA_POST_D), (8.2, 0.0))]

    for start, end in spans:
        low = (min(start[0], end[0]) - 0.08, min(start[1], end[1]) - 0.08, deck_top)
        high = (max(start[0], end[0]) + 0.08, max(start[1], end[1]) + 0.08, deck_top + 1.0)

        balustrade_run(b, IDENTITY, start, end, deck_top)
        b.collider(low, high, name="Railing")


def veranda_roof(b: Builder, roof_half: float, eave: float) -> None:
    """Shallower hipped roof over the veranda, thick like the tiles, with a blue ceiling board under it."""
    rise = VERANDA_ROOF_REACH * math.tan(math.radians(VERANDA_PITCH))
    top_at_wall = eave + ROOF_THICKNESS + rise
    corners = [(side * roof_half, -VERANDA_ROOF_REACH, level) for side, level in itertools.product((-1, 1), (eave, eave + ROOF_THICKNESS))]
    wall_line = [(side * (roof_half - VERANDA_ROOF_REACH), 0.05, level) for side, level in itertools.product((-1, 1), (top_at_wall - ROOF_THICKNESS, top_at_wall))]
    wall_ends = [(side * roof_half, 0.05, level) for side, level in itertools.product((-1, 1), (eave, eave + ROOF_THICKNESS))]

    solid_hull(b, corners + wall_line + wall_ends, "tiles", srgb(ROOF_TINT), ROOF_UV)
    slope_ribs(b, (0.0, -VERANDA_ROOF_REACH), (1.0, 0.0), (0.0, 1.0), roof_half, VERANDA_ROOF_REACH, eave + ROOF_THICKNESS - 0.02, VERANDA_PITCH, ROOF_RIB_TINT)
    b.box((-roof_half, -VERANDA_ROOF_REACH - 0.04, eave - 0.1), (roof_half, -VERANDA_ROOF_REACH + 0.04, eave + ROOF_THICKNESS + 0.04), "wood", srgb(TIMBER), uv=TIMBER_UV)


def chimney(b: Builder, u: float, d: float, base_z: float, top_z: float) -> None:
    """Plastered stack with a moulded cap and two clay pots."""
    b.box((u - 0.45, d - 0.4, base_z), (u + 0.45, d + 0.4, top_z), "plaster", srgb(CAIADO))
    b.box((u - 0.55, d - 0.5, top_z - 0.3), (u + 0.55, d + 0.5, top_z - 0.15), "trim", srgb(CREAM))
    b.box((u - 0.6, d - 0.55, top_z - 0.15), (u + 0.6, d + 0.55, top_z), "trim", srgb(CREAM))

    for side in (-1, 1):
        lathe(b, [(0.14, 0.0), (0.12, 0.12), (0.1, 0.34), (0.15, 0.4)], 8, "tiles", "B4573C", IDENTITY, base=(u + side * 0.25, d, top_z))


def veranda_furniture(b: Builder) -> None:
    """A bench against the wall each side of the door and a pair of clay pots with leafy plants."""
    wood = srgb(WOOD["media"])

    for side in (-1, 1):
        u = side * 3.4
        pot_u = side * 1.5

        b.box((u - 0.8, -0.5, BASE + 0.42), (u + 0.8, -0.05, BASE + 0.48), "wood", wood, uv=PLANK_UV)
        b.box((u - 0.8, -0.1, BASE + 0.48), (u + 0.8, -0.05, BASE + 1.0), "wood", wood, uv=PLANK_UV)
        lathe(b, [(0.2, 0.0), (0.24, 0.16), (0.28, 0.4), (0.25, 0.42)], 10, "tiles", "B4573C", IDENTITY, base=(pot_u, -0.6, BASE))
        b.sphere((pot_u, -0.6, BASE + 0.72), 0.34, "paint", srgb("3F8A50"), scale=(1.0, 1.0, 0.9), segments=8)
        b.sphere((pot_u + 0.12, -0.5, BASE + 0.95), 0.2, "paint", srgb("E9A6C0"), segments=6)

        for leg in (-0.7, 0.7):
            b.box((u + leg - 0.04, -0.54, BASE), (u + leg + 0.04, -0.46, BASE + 0.42), "wood", srgb(TIMBER), uv=TIMBER_UV)


def casa_grande(b: Builder, half: float, depth: float) -> dict:
    """Draw the sede into the builder; returns the sidecar entries. half = half the length of the front wall."""
    frames = wall_frames(half, depth)
    wall_halves = {"front": half, "back": half, "west": depth / 2.0, "east": depth / 2.0}
    wall_extension = {"front": 0.06, "back": 0.06, "west": 0.0, "east": 0.0}
    roof_half = half + OVERHANG

    b.box((-half - 0.1, 0.0, 0.0), (half + 0.1, depth + 0.1, BASE - 0.1), "stone", srgb(STONE["media"]))
    b.box((-half - 0.14, -0.14, BASE - 0.12), (half + 0.14, depth + 0.14, BASE), "trim", srgb(CREAM))

    for wall, drawer in WALL_DRAWERS.items():
        corner_strips(b, frames[wall], wall_halves[wall], wall_extension[wall])
        cornice(b, frames[wall], wall_halves[wall])
        openings = drawer(b, frames[wall])
        span = wall_halves[wall] - (0.0 if wall in ("front", "back") else WALL)
        hollow_wall(b, frames[wall], -span, span, BASE, WALL_TOP, openings)

    build_rooms(b, half, depth, BASE, WALL_TOP)

    ridge_z = hip_roof(b, roof_half, -OVERHANG, depth + OVERHANG, EAVE, HIP_PITCH)
    rafter_tails(b, (roof_half, -OVERHANG, depth + OVERHANG), (half, 0.0, depth), EAVE)
    veranda(b, half)
    veranda_furniture(b)
    chimney(b, *CHIMNEY, WALL_TOP + 1.2, ridge_z + 0.9)
    b.marker("door", (0.0, -VERANDA_DEPTH - STAIR_STEPS * STAIR_TREAD - 0.4, 0.0))

    return {
        "lot_width": half * 2.0,
        "lot_depth": depth,
        "doors": [{"x": 0.0, "width": FRONT_DOOR[0], "enterable": True}],
        "ambient_volume": interior_volume(half, depth),
        "night_ambient": NIGHT_AMBIENT,
    }


def interior_volume(half: float, depth: float) -> dict:
    """Box (model-local Godot coords) of the air inside the house for the interior ambient probe: floor to forro, walls to their inner faces."""
    low = blender_to_godot((-half + WALL, WALL, BASE))
    high = blender_to_godot((half - WALL, depth - WALL, WALL_TOP - 0.12))

    return {"min": low, "max": high}
