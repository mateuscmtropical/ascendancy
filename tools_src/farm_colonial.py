"""Colonial Brazilian building pieces of the fazenda for build_farm.py: hipped capa-e-canal roofs with exposed
rafter tails, tall shuttered windows and plank doors, turned-post verandas, and the sede (casa-grande) itself.

Everything draws in facade coords of the Builder (u across, d into the building from the front plane d = 0, z up),
through a frame, so one window or door helper serves the front, back and end walls. Blender coords: X = Godot X,
Y = -Godot Z, Z up; a building at yaw 0 faces Godot +Z.
"""

import itertools
import math

import bmesh
from mathutils import Matrix, Vector

from build_town_houses import STONE, WOOD, WOOD_DARK_BAND, WOOD_LIGHT_BAND, WHITE, Builder, Opening, srgb
from shop_props_common import lathe

CAIADO = "F2EFE6"  # whitewash
CREAM = "F7F2E4"  # mouldings
ACCENT = "2F5FA8"  # the one accent colour: frames, doors, shutters
ACCENT_LIGHT = "4A78BD"
ROOF_TINT = "EFB391"
ROOF_RIB_TINT = "E49F7C"
ROOF_UV = ("world", 1.35)
TIMBER = WOOD["escura"]
IRON = "3A3438"
GOLD = "C9A24A"
RIB_SPACING = 0.27
RIB_RADIUS = 0.07

TIMBER_UV = ("band", *WOOD_DARK_BAND, 1.5)
PLANK_UV = ("band", *WOOD_LIGHT_BAND, 1.5)
INNER_PANE_DEPTH = 0.2  # the glass seen from inside a hollow wall: dark at night, behind the glass that glows outside


# ---------- wall frames: one drawing helper, any wall ----------

def wall_frames(half: float, depth: float) -> dict:
    """Frame of each wall of a box building (u = -half..half, d = 0..depth): facade coords look at that wall from
    outside, d = 0 on its face."""
    return {
        "front": Matrix.Identity(4),
        "back": Matrix.Translation((0.0, depth, 0.0)) @ Matrix.Rotation(math.pi, 4, "Z"),
        "west": Matrix.Translation((-half, depth / 2.0, 0.0)) @ Matrix.Rotation(-math.pi / 2.0, 4, "Z"),
        "east": Matrix.Translation((half, depth / 2.0, 0.0)) @ Matrix.Rotation(math.pi / 2.0, 4, "Z"),
    }


# ---------- small solids ----------

def aligned_frame(start: tuple, end: tuple, up: tuple) -> Matrix:
    """Frame at start whose Z runs to end and whose X is as close to `up` as it can be."""
    axis = (Vector(end) - Vector(start)).normalized()
    side = Vector(up).cross(axis).normalized()
    top = axis.cross(side).normalized()

    return Matrix.Translation(start) @ Matrix((top, side, axis)).transposed().to_4x4()


def tube(b: Builder, start: tuple, end: tuple, radius: float, sides: int, material: str, tint: str, up: tuple = (0.0, 0.0, 1.0), uv: tuple = None, frame: Matrix = None) -> None:
    """Prism with `sides` faces from start to end (3 sides: a triangular rib, apex toward `up`)."""
    length = (Vector(end) - Vector(start)).length

    lathe(b, [(radius, 0.0), (radius, length)], sides, material, tint, (frame or Matrix.Identity(4)) @ aligned_frame(start, end, up), uv=uv)


def ring_prism(b: Builder, outer: list, inner: list, depth_from: float, depth_to: float, material: str, tint: tuple, frame: Matrix, uv: tuple = None) -> None:
    """Frame around an opening: two matching outlines (outer, inner; (u, z) points) extruded from d = depth_from to
    depth_to. The hole stays open."""
    ring = bmesh.new()
    layers = {depth: ([ring.verts.new((u, depth, z)) for u, z in outer], [ring.verts.new((u, depth, z)) for u, z in inner]) for depth in (depth_from, depth_to)}
    count = len(outer)

    for depth, (outer_ring, inner_ring) in layers.items():
        for index in range(count):
            following = (index + 1) % count
            ring.faces.new((outer_ring[index], outer_ring[following], inner_ring[following], inner_ring[index]))

    first_outer, first_inner = layers[depth_from]
    second_outer, second_inner = layers[depth_to]

    for index in range(count):
        following = (index + 1) % count
        ring.faces.new((first_outer[index], first_outer[following], second_outer[following], second_outer[index]))
        ring.faces.new((first_inner[index], first_inner[following], second_inner[following], second_inner[index]))

    b._link(ring, material, tint, uv, frame)


def solid_hull(b: Builder, points: list, material: str, tint: tuple, uv: tuple = None, frame: Matrix = None):
    """Convex hull of the points as one solid. Builder.hull deletes interior and unused vertices in one call, which
    Blender refuses when the same vertex is in both lists (coplanar roof corners)."""
    hull_bmesh = bmesh.new()
    vertices = [hull_bmesh.verts.new(point) for point in points]
    result = bmesh.ops.convex_hull(hull_bmesh, input=vertices)
    doomed = {*result["geom_interior"], *result["geom_unused"]}

    bmesh.ops.delete(hull_bmesh, geom=list(doomed), context="VERTS")

    return b._link(hull_bmesh, material, tint, uv, frame or Matrix.Identity(4))


def hex_box(b: Builder, minimum: tuple, maximum: tuple, material: str, tint: str, frame: Matrix, uv: tuple = None):
    return b.box(minimum, maximum, material, srgb(tint), frame=frame, uv=uv)


# ---------- roofs ----------

def slope_ribs(b: Builder, edge_start: tuple, along: tuple, up_slope: tuple, half_edge: float, run: float, eave_z: float, pitch: float, tint: str, spacing: float = RIB_SPACING, hipped: bool = True, frame: Matrix = None) -> None:
    """Ribs (the capas of capa-e-canal) down one roof slope, from its eave edge toward the ridge.

    edge_start: plan point (u, d) at the middle of the eave edge; along: unit plan vector along the edge; up_slope: unit
    plan vector pointing up the slope. A rib at distance s along the edge climbs min(run, half_edge - |s|): the hips
    meet the neighbouring slope at 45 degrees in plan."""
    rise = math.tan(math.radians(pitch))
    count = int(half_edge / spacing)
    stations = [spacing * index for index in range(-count, count + 1)]
    normal = (0.0, 0.0, 1.0)

    for station in stations:
        climb = (min(run, half_edge - abs(station)) if hipped else run) - 0.12
        base = (edge_start[0] + along[0] * station, edge_start[1] + along[1] * station)

        if climb < 0.3:
            continue

        start = (base[0], base[1], eave_z + 0.05)
        end = (base[0] + up_slope[0] * climb, base[1] + up_slope[1] * climb, eave_z + 0.05 + climb * rise)

        tube(b, start, end, RIB_RADIUS, 3, "tiles", tint, normal, frame=frame)


def hip_roof(b: Builder, half_u: float, depth_from: float, depth_to: float, eave_z: float, pitch: float, tint: str = ROOF_TINT, ribs: bool = True, thickness: float = 0.16, frame: Matrix = None) -> float:
    """Four-slope roof over the plan u = -half_u..half_u, d = depth_from..depth_to (the eave outline, overhang
    included), eave edge at eave_z. Returns the ridge height. Ridge, hips and ribs are laid on top."""
    half_depth = (depth_to - depth_from) / 2.0
    middle = (depth_from + depth_to) / 2.0
    rise = half_depth * math.tan(math.radians(pitch))
    ridge_half = max(0.05, half_u - half_depth)
    ridge_z = eave_z + thickness + rise
    corners = [(side * half_u, edge, level) for side, edge, level in itertools.product((-1, 1), (depth_from, depth_to), (eave_z, eave_z + thickness))]

    solid_hull(b, corners + [(-ridge_half, middle, ridge_z), (ridge_half, middle, ridge_z)], "tiles", srgb(tint), ROOF_UV, frame=frame)

    if ribs:
        down_front, down_back = (0.0, 1.0), (0.0, -1.0)
        slope_ribs(b, (0.0, depth_from), (1.0, 0.0), down_front, half_u, half_depth, eave_z + thickness - 0.02, pitch, ROOF_RIB_TINT, frame=frame)
        slope_ribs(b, (0.0, depth_to), (1.0, 0.0), down_back, half_u, half_depth, eave_z + thickness - 0.02, pitch, ROOF_RIB_TINT, frame=frame)
        slope_ribs(b, (-half_u, middle), (0.0, 1.0), (1.0, 0.0), half_depth, half_depth, eave_z + thickness - 0.02, pitch, ROOF_RIB_TINT, frame=frame)
        slope_ribs(b, (half_u, middle), (0.0, 1.0), (-1.0, 0.0), half_depth, half_depth, eave_z + thickness - 0.02, pitch, ROOF_RIB_TINT, frame=frame)

    roof_caps(b, half_u, depth_from, depth_to, eave_z + thickness, ridge_half, ridge_z, frame)

    return ridge_z


def roof_caps(b: Builder, half_u: float, depth_from: float, depth_to: float, eave_z: float, ridge_half: float, ridge_z: float, frame: Matrix = None) -> None:
    """Cumeeira along the ridge (a round tile row, ends capped) and the four hip caps down to the eave corners."""
    middle = (depth_from + depth_to) / 2.0
    cap_tint = ROOF_RIB_TINT

    tube(b, (-ridge_half - 0.1, middle, ridge_z + 0.06), (ridge_half + 0.1, middle, ridge_z + 0.06), 0.17, 8, "tiles", cap_tint, frame=frame)
    b.sphere((-ridge_half - 0.1, middle, ridge_z + 0.06), 0.17, "tiles", srgb(cap_tint), segments=8, frame=frame)
    b.sphere((ridge_half + 0.1, middle, ridge_z + 0.06), 0.17, "tiles", srgb(cap_tint), segments=8, frame=frame)

    for side, edge in itertools.product((-1, 1), (depth_from, depth_to)):
        start = (side * ridge_half, middle, ridge_z + 0.06)
        end = (side * half_u, edge, eave_z + 0.04)

        tube(b, start, end, 0.12, 6, "tiles", cap_tint, frame=frame)


def rafter_tails(b: Builder, outline: tuple, walls: tuple, eave_z: float, spacing: float = 0.6, frame: Matrix = None) -> None:
    """Exposed rafter ends (cachorros) under the eave all round, plus a thin fascia board along every edge.

    outline: eave plan (half_u, depth_from, depth_to); walls: (half_wall, wall_from, wall_to), the wall lines the
    tails come out of."""
    half_u, depth_from, depth_to = outline
    half_wall, wall_from, wall_to = walls
    tail = srgb(TIMBER)
    across = frange(-half_u + 0.35, half_u - 0.3, spacing)
    along = frange(depth_from + 0.35, depth_to - 0.3, spacing)
    fronts = [(u, depth_from, wall_from) for u in across] + [(u, depth_to, wall_to) for u in across]
    ends = [(d, -half_u, -half_wall) for d in along] + [(d, half_u, half_wall) for d in along]

    for u, edge, wall in fronts:
        low, high = sorted((edge, wall))
        b.box((u - 0.045, low + 0.05, eave_z - 0.14), (u + 0.045, high, eave_z - 0.02), "wood", tail, uv=TIMBER_UV, frame=frame)

    for d, edge, wall in ends:
        low, high = sorted((edge, wall))
        b.box((low + 0.05, d - 0.045, eave_z - 0.14), (high, d + 0.045, eave_z - 0.02), "wood", tail, uv=TIMBER_UV, frame=frame)

    for edge in (depth_from, depth_to):
        b.box((-half_u - 0.04, edge - 0.04, eave_z - 0.1), (half_u + 0.04, edge + 0.04, eave_z + 0.1), "wood", tail, uv=TIMBER_UV, frame=frame)

    for side in (-1, 1):
        b.box((side * half_u - 0.04, depth_from, eave_z - 0.1), (side * half_u + 0.04, depth_to, eave_z + 0.1), "wood", tail, uv=TIMBER_UV, frame=frame)


def frange(start: float, stop: float, step: float) -> list:
    count = int((stop - start) / step) + 1

    return [start + step * index for index in range(count)]


# ---------- openings ----------

def window(b: Builder, frame: Matrix, u: float, bottom: float, width: float, height: float, shutters: bool = True, top: str = "segment", inside_glass: bool = False) -> None:
    """Tall window on a whitewashed wall: accent frame ring with a cream moulding, dark glass in a recessed plane,
    white glazing bars, sill on corbels and louvred shutters folded back against the wall."""
    opening = Opening(u, width, bottom, height, top)
    glass = opening.outline(0.0)

    b.prism(glass, -0.025, 0.0, "glass", WHITE, frame=frame)

    if inside_glass:
        b.pane(glass, INNER_PANE_DEPTH, "inner_glass", frame=frame)

    ring_prism(b, opening.outline(0.15), glass, -0.09, 0.0, "paint", srgb(ACCENT), frame)
    ring_prism(b, opening.outline(0.24), opening.outline(0.15), -0.06, 0.0, "trim", srgb(CREAM), frame, uv=("band", 0.44, 0.66, 1.0))

    for fraction in (1.0 / 3.0, 2.0 / 3.0):
        bar_z = bottom + height * fraction * (0.86 if top != "flat" else 1.0)
        b.box((u - width / 2.0, -0.055, bar_z - 0.018), (u + width / 2.0, -0.025, bar_z + 0.018), "paint", srgb(CAIADO), frame=frame)

    b.box((u - 0.018, -0.055, bottom), (u + 0.018, -0.025, opening.spring), "paint", srgb(CAIADO), frame=frame)
    b.box((u - width / 2.0 - 0.3, -0.24, bottom - 0.2), (u + width / 2.0 + 0.3, -0.04, bottom - 0.1), "trim", srgb(CREAM), frame=frame)
    b.box((u - width / 2.0 - 0.34, -0.26, bottom - 0.24), (u + width / 2.0 + 0.34, -0.2, bottom - 0.2), "trim", srgb(CREAM), frame=frame)

    for side in (-1, 1):
        corbel = u + side * (width / 2.0 + 0.16)
        b.box((corbel - 0.05, -0.16, bottom - 0.42), (corbel + 0.05, -0.04, bottom - 0.2), "trim", srgb(CREAM), frame=frame)

    if shutters:
        shutter_pair(b, frame, u, bottom, width, opening.spring - bottom)


def shutter_pair(b: Builder, frame: Matrix, u: float, bottom: float, width: float, height: float) -> None:
    """Two louvred leaves (venezianas) opened flat against the wall each side of a window."""
    leaf_width = width * 0.44
    louvres = int(height / 0.14)

    for side in (-1, 1):
        centre = u + side * (width / 2.0 + 0.26 + leaf_width / 2.0)
        low, high = centre - leaf_width / 2.0, centre + leaf_width / 2.0

        b.box((low, -0.06, bottom), (high, -0.01, bottom + height), "paint", srgb(ACCENT), frame=frame)

        for louvre in range(louvres):
            slat_z = bottom + 0.08 + louvre * (height - 0.16) / louvres
            b.box((low + 0.05, -0.085, slat_z), (high - 0.05, -0.06, slat_z + 0.07), "paint", srgb(ACCENT_LIGHT), frame=frame)

        b.box((low, -0.075, bottom), (low + 0.05, -0.06, bottom + height), "paint", srgb(ACCENT), frame=frame)
        b.box((high - 0.05, -0.075, bottom), (high, -0.06, bottom + height), "paint", srgb(ACCENT), frame=frame)


def entrance_door(b: Builder, frame: Matrix, u: float, width: float, leaf_height: float, double: bool = True, fanlight: bool = True, open_into: float = 0.0) -> None:
    """Panelled plank door in an accent surround with a fanlight over a transom bar, brass knobs, stone threshold.
    open_into = thickness of a hollow wall: the leaves stand open against its inner face instead of closing the door."""
    fan_height = width * 0.32 + 0.1
    total = Opening(u, width, 0.0, leaf_height + fan_height + 0.12, "segment" if fanlight else "flat")
    leaf = Opening(u, width, 0.0, leaf_height, "flat")
    panels = ((0.1, 0.46), (0.54, 1.0)) if leaf_height > 2.0 else ((0.1, 1.0),)

    ring_prism(b, total.outline(0.17), total.outline(0.0), -0.1, 0.0, "paint", srgb(ACCENT), frame)
    ring_prism(b, total.outline(0.27), total.outline(0.17), -0.07, 0.0, "trim", srgb(CREAM), frame, uv=("band", 0.72, 0.98, 1.0))
    b.box((u - width / 2.0, -0.12, leaf_height), (u + width / 2.0, -0.02, leaf_height + 0.12), "paint", srgb(ACCENT), frame=frame)

    if fanlight:
        fan = Opening(u, width, leaf_height + 0.12, fan_height, "segment")

        b.prism(fan.outline(0.0), -0.04, 0.0, "glass", WHITE, frame=frame)

        if open_into:
            b.pane(fan.outline(0.0), INNER_PANE_DEPTH, "inner_glass", frame=frame)

        for spoke in range(-2, 3):
            tip = (u + spoke * width * 0.22, fan.apex - 0.08)
            b.beam((u, -0.06, leaf_height + 0.14), (tip[0], -0.06, tip[1]), 0.03, 0.03, "paint", srgb(CAIADO), frame=frame, uv=None)

    b.box((u - width / 2.0 - 0.3, -0.45, 0.0), (u + width / 2.0 + 0.3, -0.05, 0.05), "trim", srgb(CREAM), frame=frame)

    if open_into:
        open_leaves(b, frame, u, width, leaf_height, double, open_into)
        return

    b.prism(leaf.outline(0.0), -0.07, 0.0, "paint", srgb(ACCENT), frame=frame)
    leaves = [(u - width / 2.0 + 0.1, u - 0.04), (u + 0.04, u + width / 2.0 - 0.1)] if double else [(u - width / 2.0 + 0.1, u + width / 2.0 - 0.1)]

    for (left, right), (panel_low, panel_high) in itertools.product(leaves, panels):
        b.box((left, -0.11, leaf_height * panel_low), (right, -0.07, leaf_height * panel_high - 0.08), "paint", srgb(ACCENT_LIGHT), frame=frame)

    if double:
        b.box((u - 0.02, -0.1, 0.05), (u + 0.02, -0.07, leaf_height), "paint", srgb("1F3F73"), frame=frame)

    for side in (-1, 1):
        b.sphere((u + side * 0.12, -0.14, 1.05), 0.04, "metal", srgb(GOLD), frame=frame, segments=6)


def open_leaves(b: Builder, frame: Matrix, u: float, width: float, leaf_height: float, double: bool, wall: float) -> None:
    """Door leaves swung 100 degrees into the house, hinged at the inner face of a wall `wall` thick."""
    swing = math.radians(100.0)
    hinges = (-1, 1) if double else (-1,)
    leaf = width / len(hinges) - 0.04

    for side in hinges:
        hinge_u = u + side * width / 2.0
        tip = (hinge_u - side * leaf * math.cos(swing), wall + 0.03 + leaf * math.sin(swing))

        b.beam((hinge_u, wall + 0.03, leaf_height / 2.0), (tip[0], tip[1], leaf_height / 2.0), leaf_height, 0.06, "paint", srgb(ACCENT), frame=frame, uv=None)


# ---------- veranda (alpendre) ----------

def turned_post(b: Builder, frame: Matrix, u: float, d: float, base: float, top: float, tint: str = CAIADO) -> None:
    """Turned timber post: square plinth, vase shaft with a neck ring, capital block."""
    height = top - base
    profile = [(0.13, 0.0), (0.13, height * 0.05), (0.09, height * 0.08), (0.095, height * 0.2), (0.115, height * 0.4), (0.095, height * 0.78), (0.115, height * 0.82), (0.08, height * 0.86), (0.08, height * 0.94), (0.12, height * 0.95), (0.12, height)]

    lathe(b, profile, 10, "paint", tint, frame, base=(u, d, base))
    b.box((u - 0.17, d - 0.17, base), (u + 0.17, d + 0.17, base + 0.14), "trim", srgb(CREAM), frame=frame)
    b.box((u - 0.17, d - 0.17, top - 0.1), (u + 0.17, d + 0.17, top), "trim", srgb(CREAM), frame=frame)


def baluster(b: Builder, frame: Matrix, u: float, d: float, base: float, height: float) -> None:
    profile = [(0.03, 0.0), (0.045, height * 0.06), (0.03, height * 0.16), (0.05, height * 0.4), (0.03, height * 0.7), (0.045, height * 0.9), (0.04, height)]

    lathe(b, profile, 6, "paint", CAIADO, frame, base=(u, d, base))


def balustrade_run(b: Builder, frame: Matrix, start: tuple, end: tuple, base: float, height: float = 0.95, spacing: float = 0.15) -> None:
    """Rail, foot rail and turned balusters between two plan points (u, d)."""
    length = math.dist(start, end)
    count = max(1, int(length / spacing))
    direction = ((end[0] - start[0]) / length, (end[1] - start[1]) / length)
    cream = srgb(CAIADO)

    def at(distance: float) -> tuple:
        return start[0] + direction[0] * distance, start[1] + direction[1] * distance

    b.beam((*start, base + height), (*end, base + height), 0.1, 0.1, "paint", cream, frame=frame, uv=None)
    b.beam((*start, base + height - 0.06), (*end, base + height - 0.06), 0.16, 0.05, "paint", cream, frame=frame, uv=None)
    b.beam((*start, base + 0.1), (*end, base + 0.1), 0.1, 0.1, "paint", cream, frame=frame, uv=None)

    for index in range(count):
        u, d = at(length * (index + 0.5) / count)
        baluster(b, frame, u, d, base + 0.14, height - 0.28)


def stone_stair(b: Builder, frame: Matrix, half_width: float, top_z: float, edge_d: float, steps: int, tread: float, name: str = "Stair") -> float:
    """Front stair of cut stone (cantaria) down from the veranda edge at d = edge_d (front is -d), flanked by cheek
    walls capped on a slope, with a ramp collider (steps this low are climbed as a slope). Returns the foot d."""
    riser = top_z / steps
    foot = edge_d - steps * tread
    stone = srgb(STONE["clara"])
    cap = srgb(STONE["caiada"])

    for step in range(1, steps):
        level = top_z - step * riser
        b.box((-half_width, edge_d - step * tread, 0.0), (half_width, edge_d - (step - 1) * tread, level + 0.0), "stone", stone, frame=frame)
        b.box((-half_width - 0.04, edge_d - step * tread - 0.06, level - 0.06), (half_width + 0.04, edge_d - (step - 1) * tread - 0.0, level + 0.02), "trim", cap, frame=frame)

    for side in (-1, 1):
        wall_in = side * (half_width + 0.02)
        wall_out = side * (half_width + 0.42)
        low, high = sorted((wall_in, wall_out))
        profile = [(edge_d, 0.0), (foot, 0.0), (foot, 0.45), (edge_d, top_z + 0.55)]

        b.side_prism(profile, low, high, "stone", stone, frame=frame)
        b.side_prism([(edge_d + 0.02, top_z + 0.55), (foot - 0.06, 0.45), (foot - 0.06, 0.55), (edge_d + 0.02, top_z + 0.65)], low - 0.05, high + 0.05, "trim", cap, frame=frame)

    slope = math.atan2(top_z, steps * tread)
    ramp_length = math.hypot(top_z, steps * tread)
    ramp = frame @ Matrix.Translation((0.0, edge_d - steps * tread / 2.0, top_z / 2.0)) @ Matrix.Rotation(slope, 4, "X")

    b.collider((-half_width, -ramp_length / 2.0 - 0.05, -0.12), (half_width, ramp_length / 2.0 + 0.05, 0.0), frame=ramp, name=name)

    return foot
