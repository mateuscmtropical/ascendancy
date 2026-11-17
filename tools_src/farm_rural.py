"""Rural buildings and props of the fazenda for build_farm.py: the tulha (grain and coffee store: whitewashed walls
with a dark timber frame on a stone base), the rancho on round posts that shelters the animals, plank doors, the
loading platform and its ladder.

Facade coords as in farm_colonial.py: u across, d into the building from the front plane d = 0, z up; the front
faces -d. A building at yaw 0 faces Godot +Z.
"""

import itertools
import math

from mathutils import Matrix

from build_town_houses import STONE, WOOD, WOOD_DARK_BAND, WOOD_LIGHT_BAND, Builder, srgb
from farm_colonial import (
    ACCENT,
    CAIADO,
    CREAM,
    IRON,
    PLANK_UV,
    ROOF_RIB_TINT,
    ROOF_TINT,
    ROOF_UV,
    TIMBER,
    TIMBER_UV,
    hip_roof,
    rafter_tails,
    slope_ribs,
    solid_hull,
    tube,
    wall_frames,
    window,
)
from shop_props_common import ring

IDENTITY = Matrix.Identity(4)
TRIM_STRIP_UV = ("band", 0.44, 0.66, 1.0)
ROUGH_WOOD = "7A5438"  # unpainted round posts and sawn boards


def shade(tint: tuple, factor: float) -> tuple:
    return tuple(min(1.0, channel * factor) for channel in tint)


# ---------- plank doors, platform and ladder ----------

def plank_door(b: Builder, frame: Matrix, u: float, width: float, height: float, bottom: float = 0.0) -> None:
    """Big double door of vertical planks in the accent colour, with battens, a diagonal brace in each leaf, strap
    hinges, ring handles, a timber lintel and jambs."""
    leaf_width = width / 2.0
    plank_count = max(2, round(leaf_width / 0.2))
    plank = leaf_width / plank_count
    accent = srgb(ACCENT)
    timber = srgb(TIMBER)
    iron = srgb(IRON)

    for side, index in itertools.product((-1, 1), range(plank_count)):
        low = u + (index * plank if side > 0 else -leaf_width + index * plank)
        tint = shade(accent, 0.9 + 0.2 * ((index * 7 + (3 if side > 0 else 0)) % 5) / 4.0)

        b.box((low + 0.004, -0.09, bottom), (low + plank - 0.004, -0.02, bottom + height), "paint", tint, frame=frame)

    for side in (-1, 1):
        inner = u + side * 0.05
        outer = u + side * (width / 2.0 - 0.02)
        low, high = sorted((inner, outer))
        sign = side

        for fraction in (0.12, 0.84):
            b.box((low, -0.13, bottom + height * fraction), (high, -0.09, bottom + height * fraction + 0.16), "paint", shade(accent, 0.78), frame=frame)

        b.beam((inner, -0.12, bottom + 0.2 + (height - 0.5 if sign < 0 else 0.0)), (outer, -0.12, bottom + 0.2 + (0.0 if sign < 0 else height - 0.5)), 0.16, 0.04, "paint", shade(accent, 0.78), frame=frame, uv=None)

        for fraction in (0.2, 0.5, 0.8):
            strap_from, strap_to = sorted((outer, outer - side * 0.6))
            b.box((strap_from, -0.145, bottom + height * fraction - 0.04), (strap_to, -0.125, bottom + height * fraction + 0.04), "metal", iron, frame=frame)

        ring(b, (u + side * 0.16, -0.15, bottom + height * 0.45), 0.055, 0.013, "metal", IRON, frame, sides=8, tube_sides=4, axis="Y")

    b.box((u - width / 2.0 - 0.25, -0.18, bottom), (u - width / 2.0, 0.0, bottom + height + 0.3), "wood", timber, frame=frame, uv=TIMBER_UV)
    b.box((u + width / 2.0, -0.18, bottom), (u + width / 2.0 + 0.25, 0.0, bottom + height + 0.3), "wood", timber, frame=frame, uv=TIMBER_UV)
    b.box((u - width / 2.0 - 0.35, -0.2, bottom + height), (u + width / 2.0 + 0.35, 0.0, bottom + height + 0.32), "wood", timber, frame=frame, uv=TIMBER_UV)
    b.box((u - width / 2.0 - 0.3, -0.5, bottom), (u + width / 2.0 + 0.3, 0.0, bottom + 0.06), "stone", srgb(STONE["clara"]), frame=frame)


def ladder(b: Builder, frame: Matrix, u: float, foot_d: float, top_d: float, top_z: float) -> None:
    """Wooden ladder leaning from the ground at d = foot_d to d = top_d at top_z, rungs every 0.3 m."""
    wood = srgb(WOOD["media"])
    rungs = int(top_z / 0.3)

    for side in (-1, 1):
        b.beam((u + side * 0.27, foot_d, 0.0), (u + side * 0.27, top_d, top_z + 0.35), 0.07, 0.05, "wood", wood, frame=frame, uv=TIMBER_UV)

    for rung in range(1, rungs):
        height = rung * top_z / rungs
        reach = foot_d + (top_d - foot_d) * (height / (top_z + 0.35))

        b.beam((u - 0.27, reach, height), (u + 0.27, reach, height), 0.05, 0.05, "wood", wood, frame=frame, uv=None)


def loading_platform(b: Builder, frame: Matrix, u: float, top_z: float, reach: float, half_width: float) -> None:
    """Raised landing in front of the loading door: boards on two posts and a stone footing, rail ends, collider."""
    wood = srgb(WOOD["media"])
    timber = srgb(TIMBER)
    boards = int(reach / 0.22)
    board = reach / boards

    for index in range(boards):
        b.box((u - half_width, -reach + index * board + 0.004, top_z - 0.1), (u + half_width, -reach + (index + 1) * board - 0.004, top_z), "wood", wood, frame=frame, uv=PLANK_UV)

    b.box((u - half_width, -reach, top_z - 0.28), (u + half_width, 0.0, top_z - 0.1), "wood", timber, frame=frame, uv=TIMBER_UV)

    for side in (-1, 1):
        b.box((u + side * (half_width - 0.1) - 0.09, -reach + 0.12, 0.0), (u + side * (half_width - 0.1) + 0.09, -reach + 0.3, top_z - 0.28), "wood", timber, frame=frame, uv=TIMBER_UV)
        b.box((u + side * (half_width - 0.1) - 0.2, -reach + 0.05, 0.0), (u + side * (half_width - 0.1) + 0.2, -reach + 0.37, 0.18), "stone", srgb(STONE["media"]), frame=frame)

    b.collider((u - half_width, -reach, 0.0), (u + half_width, 0.0, top_z), frame=frame, name="Platform")


# ---------- the tulha ----------

TULHA_BASE = 0.7
TULHA_WALL_TOP = 3.9
TULHA_EAVE = TULHA_WALL_TOP + 0.16
TULHA_OVERHANG = 1.0
TULHA_PITCH = 28.0
TULHA_BAY = 2.25
TULHA_DOOR_WIDTH = 3.0
TULHA_LOADING_AXIS = 5.625
TULHA_LOADING_SILL = 1.55


def timber_frame(b: Builder, frame: Matrix, half: float, bays: int, gaps: tuple) -> None:
    """Exposed timber frame (taipa look) on a whitewashed wall: posts, sill, mid rail, top plate and a diagonal brace
    in every bay that has no opening. gaps: (centre, half width) of openings that interrupt posts and rails."""
    timber = srgb(TIMBER)
    posts = [-half + 2.0 * half * index / bays for index in range(bays + 1)]
    kept = [post for post in posts if not any(abs(post - centre) < reach for centre, reach in gaps)]
    mid = TULHA_BASE + 1.6
    spans = frame_spans(half, gaps)

    for post in kept:
        b.box((post - 0.1, -0.12, TULHA_BASE), (post + 0.1, 0.0, TULHA_WALL_TOP), "wood", timber, frame=frame, uv=TIMBER_UV)

    for low, high in spans:
        b.box((low, -0.1, TULHA_BASE), (high, 0.0, TULHA_BASE + 0.2), "wood", timber, frame=frame, uv=TIMBER_UV)
        b.box((low, -0.1, mid - 0.07), (high, 0.0, mid + 0.07), "wood", timber, frame=frame, uv=TIMBER_UV)
        b.box((low, -0.12, TULHA_WALL_TOP - 0.24), (high, 0.0, TULHA_WALL_TOP), "wood", timber, frame=frame, uv=TIMBER_UV)

    for index, (left, right) in enumerate(zip(posts, posts[1:])):
        if any(left - 0.01 < centre + reach and right + 0.01 > centre - reach for centre, reach in gaps):
            continue

        flip = index % 2
        start, end = (left + 0.1, right - 0.1) if not flip else (right - 0.1, left + 0.1)

        b.beam((start, -0.08, mid + 0.1), (end, -0.08, TULHA_WALL_TOP - 0.26), 0.13, 0.05, "wood", timber, frame=frame)


def frame_spans(half: float, gaps: tuple) -> list:
    """Runs of wall between the openings (u from, u to)."""
    edges = [-half]

    for centre, reach in sorted(gaps):
        edges += [centre - reach, centre + reach]

    edges.append(half)

    return [(low, high) for low, high in zip(edges[::2], edges[1::2]) if high - low > 0.05]


def vent_window(b: Builder, frame: Matrix, u: float, bottom: float) -> None:
    """Small barred vent window: frame, dark opening, four iron bars."""
    window(b, frame, u, bottom, 0.6, 0.8, shutters=False, top="flat")

    for index in range(4):
        bar = u - 0.225 + index * 0.15

        b.box((bar - 0.012, -0.075, bottom), (bar + 0.012, -0.04, bottom + 0.8), "metal", srgb(IRON), frame=frame)


def tulha_front(b: Builder, frame: Matrix, half: float) -> None:
    gaps = ((0.0, TULHA_DOOR_WIDTH / 2.0 + 0.4), (TULHA_LOADING_AXIS, 0.95))

    timber_frame(b, frame, half, 8, gaps)
    plank_door(b, frame, 0.0, TULHA_DOOR_WIDTH, 3.0, TULHA_BASE)
    plank_door(b, frame, TULHA_LOADING_AXIS, 1.2, 1.6, TULHA_LOADING_SILL)

    for u in (-7.875, -5.625, -3.375, 3.375, 7.875):
        vent_window(b, frame, u, TULHA_BASE + 1.9)

    loading_platform(b, frame, TULHA_LOADING_AXIS, TULHA_LOADING_SILL - 0.05, 1.5, 1.05)
    ladder(b, frame, TULHA_LOADING_AXIS - 0.1, -2.2, -1.45, TULHA_LOADING_SILL - 0.05)


def tulha_back(b: Builder, frame: Matrix, half: float) -> None:
    timber_frame(b, frame, half, 8, ())

    for u in (-5.625, -1.125, 3.375, 7.875):
        vent_window(b, frame, u, TULHA_BASE + 1.9)


def tulha_end(b: Builder, frame: Matrix, half: float) -> None:
    timber_frame(b, frame, half, 3, ())
    vent_window(b, frame, 0.0, TULHA_BASE + 1.9)


def tulha(b: Builder, half: float, depth: float) -> dict:
    """The tulha: 2 * half long, depth deep, doors on the long front. Origin at the middle of the front wall."""
    frames = wall_frames(half, depth)
    drawers = {"front": (tulha_front, half), "back": (tulha_back, half), "west": (tulha_end, depth / 2.0), "east": (tulha_end, depth / 2.0)}
    roof_half = half + TULHA_OVERHANG
    stone = srgb(STONE["media"])

    b.box((-half - 0.1, -0.1, 0.0), (half + 0.1, depth + 0.1, TULHA_BASE - 0.1), "stone", stone)
    b.box((-half - 0.14, -0.14, TULHA_BASE - 0.12), (half + 0.14, depth + 0.14, TULHA_BASE), "trim", srgb(CREAM))
    b.box((-half, 0.0, TULHA_BASE), (half, depth, TULHA_WALL_TOP), "plaster", srgb(CAIADO))
    b.collider((-half - 0.1, 0.0, 0.0), (half + 0.1, depth + 0.1, TULHA_WALL_TOP + 0.2))

    for vent in (-6.0, -1.5, 1.5, 6.0):
        b.box((vent - 0.2, -0.14, 0.18), (vent + 0.2, -0.09, 0.45), "glass", (1.0, 1.0, 1.0), frame=frames["front"])

    for wall, (drawer, wall_half) in drawers.items():
        drawer(b, frames[wall], wall_half)

    hip_roof(b, roof_half, -TULHA_OVERHANG, depth + TULHA_OVERHANG, TULHA_EAVE, TULHA_PITCH)
    rafter_tails(b, (roof_half, -TULHA_OVERHANG, depth + TULHA_OVERHANG), (half, 0.0, depth), TULHA_EAVE, spacing=0.75)
    b.marker("door", (0.0, -2.2, 0.0))

    return {"lot_width": half * 2.0, "lot_depth": depth, "doors": [{"x": 0.0, "width": TULHA_DOOR_WIDTH, "enterable": False}]}


# ---------- the rancho (animal shelter on round posts) ----------

RANCHO_PITCH = 28.0
RANCHO_OVERHANG = 0.6


def round_post(b: Builder, frame: Matrix, x: float, y: float, height: float, radius: float = 0.13) -> None:
    """Rough round pole with a flared foot stone and a square cap."""
    pole = srgb(ROUGH_WOOD)

    b.cylinder((x, y, 0.0), radius, height, 8, "wood", pole, top_radius=radius * 0.9, frame=frame, uv=TIMBER_UV)
    b.box((x - radius - 0.06, y - radius - 0.06, 0.0), (x + radius + 0.06, y + radius + 0.06, 0.16), "stone", srgb(STONE["media"]), frame=frame)


def rancho(b: Builder, frame: Matrix, width: float, depth: float, eave: float) -> None:
    """Open-fronted rancho: rough round posts in two rows carrying plates, tie beams, king posts, ridge and visible
    rafters under a capa-e-canal gable roof; plank walls at the back and low on both sides. Front at y = 0 (open),
    back at y = depth; ridge runs along x."""
    half = width / 2.0
    post_count = max(2, round(width / 3.0) + 1)
    post_xs = [-half + width * index / (post_count - 1) for index in range(post_count)]
    timber = srgb(TIMBER)
    boards = srgb(ROUGH_WOOD)
    rise = (depth / 2.0 + RANCHO_OVERHANG) * math.tan(math.radians(RANCHO_PITCH))
    ridge_under = eave + rise - 0.1
    roof_half = half + 0.5
    thickness = 0.16
    edge_z = eave + 0.1

    for x, y in itertools.product(post_xs, (0.0, depth)):
        round_post(b, frame, x, y, eave)

    for y in (0.0, depth):
        b.box((-half - 0.2, y - 0.1, eave - 0.12), (half + 0.2, y + 0.1, eave + 0.1), "wood", timber, frame=frame, uv=TIMBER_UV)

    for x in post_xs:
        b.box((x - 0.08, 0.0, eave - 0.2), (x + 0.08, depth, eave - 0.05), "wood", timber, frame=frame, uv=TIMBER_UV)
        b.cylinder((x, depth / 2.0, eave - 0.05), 0.08, ridge_under - eave + 0.05, 6, "wood", boards, frame=frame, uv=TIMBER_UV)

    b.box((-half - 0.3, depth / 2.0 - 0.08, ridge_under - 0.08), (half + 0.3, depth / 2.0 + 0.08, ridge_under + 0.08), "wood", timber, frame=frame, uv=TIMBER_UV)

    for x, side in itertools.product([-half + 0.4 + 0.8 * index for index in range(int((width - 0.8) / 0.8) + 1)], (0, 1)):
        edge_y = -RANCHO_OVERHANG if side == 0 else depth + RANCHO_OVERHANG
        b.beam((x, edge_y, edge_z - 0.12), (x, depth / 2.0, ridge_under), 0.09, 0.09, "wood", timber, frame=frame, uv=TIMBER_UV)

    corners = [(side * roof_half, edge, level) for side, edge, level in itertools.product((-1, 1), (-RANCHO_OVERHANG, depth + RANCHO_OVERHANG), (edge_z, edge_z + thickness))]
    ridge_z = ridge_under + thickness + 0.1
    ridge = [(side * roof_half, depth / 2.0, ridge_z) for side in (-1, 1)]

    solid_hull(b, corners + ridge, "tiles", srgb(ROOF_TINT), ROOF_UV, frame=frame)
    slope_ribs_frame(b, frame, roof_half, depth, edge_z + thickness - 0.02)
    tube_along(b, frame, (-roof_half - 0.05, depth / 2.0, ridge_z + 0.06), (roof_half + 0.05, depth / 2.0, ridge_z + 0.06), 0.15)

    b.box((-half, depth - 0.09, 0.0), (half, depth - 0.02, eave - 0.1), "wood", boards, frame=frame, uv=("band", *WOOD_LIGHT_BAND, 2.0))

    for index in range(int(width / 0.45) + 1):
        x = -half + index * width / int(width / 0.45)
        b.box((x - 0.03, depth - 0.12, 0.0), (x + 0.03, depth - 0.09, eave - 0.1), "wood", timber, frame=frame, uv=TIMBER_UV)

    for side in (-1, 1):
        b.box((side * half - 0.04, 0.3, 0.0), (side * half + 0.04, depth - 0.1, 1.25), "wood", boards, frame=frame, uv=("band", *WOOD_LIGHT_BAND, 2.0))
        b.box((side * half - 0.07, 0.3, 1.25), (side * half + 0.07, depth - 0.1, 1.35), "wood", timber, frame=frame, uv=TIMBER_UV)
        b.collider((side * half - 0.12, 0.0, 0.0), (side * half + 0.12, depth, 1.4), frame=frame)

    b.collider((-half, depth - 0.15, 0.0), (half, depth + 0.1, eave), frame=frame)


def slope_ribs_frame(b: Builder, frame: Matrix, roof_half: float, depth: float, eave_z: float) -> None:
    """Ribs of both slopes of a gable roof (the frame places the whole roof)."""
    run = depth / 2.0 + RANCHO_OVERHANG

    slope_ribs(b, (0.0, -RANCHO_OVERHANG), (1.0, 0.0), (0.0, 1.0), roof_half, run, eave_z, RANCHO_PITCH, ROOF_RIB_TINT, hipped=False, frame=frame)
    slope_ribs(b, (0.0, depth + RANCHO_OVERHANG), (1.0, 0.0), (0.0, -1.0), roof_half, run, eave_z, RANCHO_PITCH, ROOF_RIB_TINT, hipped=False, frame=frame)


def tube_along(b: Builder, frame: Matrix, start: tuple, end: tuple, radius: float) -> None:
    tube(b, start, end, radius, 8, "tiles", ROOF_RIB_TINT, frame=frame)
