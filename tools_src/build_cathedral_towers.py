"""Model the walkable inside of the two cathedral towers and the attic over the nave: art/town/cathedral_towers.gltf
(+ JSON sidecar with the lanterns and the stair path), placed by build_hub_scene.py at the cathedral's transform.

Laid out after real church towers and roof spaces:
  Stair shaft: a square well running hollow from the floor to the clock room; steep wooden flights hug the four
    walls with a landing in every corner (an open-newel stair: four newel posts stand the full height at the corners
    of the well and carry the handrails), the door to the nave at the foot.
  Attic door: four laps up, the corner landing by the nave has a low door into the roof space.
  Bell chamber: the stair goes on up past the louvered openings; the bell hangs in the well from an oak headstock
    with its ringing wheel, and its rope drops down the well to a striped sally at the foot of the tower.
  Clock room: on top, the stair comes up through a hatch with a rail around it; in the middle an iron birdcage
    movement on a wooden stand (going and striking trains, winding barrels, escapement, pendulum dropping through the
    floor, weights on cables hanging in the well) and leading-off rods to the motion work behind the four dials.
  Attic: queen-post trusses every 2.7 m (tie beam on the ceiling, principal rafters, queen posts, straining beam,
    struts), purlins and ridge beam under the roof boards, a plank catwalk with handrails down the middle and a cross
    walk to each tower door, odds and ends of the roofers.

Same coordinates as build_cathedral.py (x across, y along the nave from the facade, z up).

Usage (after build_cathedral.py):
  blender -b --factory-startup -P tools_src/build_cathedral_towers.py
"""

import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Matrix, Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))

from build_cathedral import (  # noqa: E402
    ATTIC_DOOR_X, ATTIC_FLOOR, ATTIC_WALK, BASE, BELFRY_BOTTOM, BODY_LENGTH, CLOCK_FLOOR, CLOCK_HEIGHT, NARTHEX_DEPTH, NAVE_HALF,
    OUTPUT_DIR, TOWER_CENTER_Y, TOWER_DOOR, TOWER_MIDDLE_X, TOWER_SHAFT_HALF, TOWER_UPPER_SCALE, WALL, build_materials, make_box,
    make_cylinder, make_lathe, make_plain_material, make_span, make_sphere, map_uvs_per_face, merge_meshes_by_material, roof_underside_height,
)

BAND = 0.75  # largura dos lances, encostados nas paredes do poço
WELL = TOWER_SHAFT_HALF - BAND  # meia largura do vão no meio (onde ficam os pilares, o sino e a corda)
CORNER = TOWER_SHAFT_HALF - BAND / 2.0  # centro dos patamares de canto
RUN = 2.0 * CORNER - BAND  # comprimento de cada lance entre dois patamares
STEPS_PER_FLIGHT = 6
TREAD = RUN / STEPS_PER_FLIGHT
CORNERS = [(-CORNER, CORNER), (-CORNER, -CORNER), (CORNER, -CORNER), (CORNER, CORNER)]  # (u, v): fundo-dentro, frente-dentro, frente-fora, fundo-fora
ATTIC_FLIGHTS = 16  # quatro voltas do chão até o patamar da porta do sótão (volta ao canto 0)
CLOCK_FLIGHTS = 14  # do sótão até a sala do relógio (chega no canto 2)
HANDRAIL_HEIGHT = 0.95
BELL_AXLE = BELFRY_BOTTOM + 6.0
BELL_MOUTH = 1.15  # diâmetro da boca do sino
WHEEL_RADIUS = 0.65
TRUSS_PITCH = 2.7
TRUSS_FIRST_Y = NARTHEX_DEPTH + 1.35
TIE_BEAM = 0.16  # altura das linhas das tesouras, deitadas na laje do forro
CATWALK_HALF = 0.5
QUEEN_POST_X = 1.6
PURLIN_X = (1.6, 4.0, 6.2)
CROSS_WALK_Y = (NARTHEX_DEPTH, NARTHEX_DEPTH + 0.9)
LANTERN = {"color": "FFC780", "energy": 1.1, "range": 7.5}  # sRGB, como no sidecar da cripta


class TowerFrame:
    """Plan coordinates of one tower: u across (negative toward the nave axis), v along the nave from the tower centre."""

    def __init__(self, side_sign: int) -> None:
        self.side_sign = side_sign
        self.tag = "L" if side_sign < 0 else "R"

    def point(self, u: float, v: float, z: float) -> Vector:
        return Vector((self.side_sign * (TOWER_MIDDLE_X + u), TOWER_CENTER_Y + v, z))

    def span(self, name: str, low: tuple, high: tuple, material) -> bpy.types.Object:
        """Box between plan corners (u, v, z); mirrored sides keep min < max."""
        first, second = self.point(*low), self.point(*high)

        stem, separator, suffix = name.partition("-")

        return make_span(f"{stem}{self.tag}{separator}{suffix}", tuple(map(min, first, second)), tuple(map(max, first, second)), material)


def beam(name: str, start: Vector, end: Vector, width: float, height: float, material) -> bpy.types.Object:
    """Box from start to end with a width x height cross-section (height kept as vertical as the direction allows)."""
    axis = end - start
    along = axis.normalized()
    up = Vector((0.0, 0.0, 1.0)) if abs(along.z) < 0.95 else Vector((1.0, 0.0, 0.0))
    across = up.cross(along).normalized()
    up = along.cross(across).normalized()
    basis = Matrix((along, across, up)).transposed().to_4x4()
    piece = make_box(name, (0, 0, 0), (axis.length, width, height), material)
    piece.matrix_world = Matrix.Translation((start + end) / 2.0) @ basis

    return piece


def flight_rises() -> list:
    """Rise of every flight: the first ones end on the attic landing, the rest on the clock room floor."""
    attic_rise = (ATTIC_WALK - BASE) / (ATTIC_FLIGHTS * STEPS_PER_FLIGHT)
    clock_rise = (CLOCK_FLOOR - ATTIC_WALK) / (CLOCK_FLIGHTS * STEPS_PER_FLIGHT)

    return [attic_rise] * ATTIC_FLIGHTS + [clock_rise] * CLOCK_FLIGHTS


def stair_plan() -> list:
    """(start corner, end corner, bottom height, rise) of every flight, from the floor to the clock room."""
    flights = []
    bottom = BASE

    for index, rise in enumerate(flight_rises()):
        flights.append((CORNERS[index % 4], CORNERS[(index + 1) % 4], bottom, rise))
        bottom += STEPS_PER_FLIGHT * rise

    return flights


def flight_axes(start: tuple, end: tuple) -> tuple:
    """Unit direction along the flight and the unit normal toward the well, in (u, v)."""
    along = Vector((end[0] - start[0], end[1] - start[1])).normalized()
    middle = Vector(((start[0] + end[0]) / 2.0, (start[1] + end[1]) / 2.0))
    toward_well = -middle.normalized()

    return along, toward_well


def build_flight(frame: TowerFrame, index: int, flight: tuple, materials: dict) -> None:
    """Treads, risers, two stringers, handrail with a baluster per step, ramp collider and the landing at its end."""
    start, end, bottom, rise = flight
    along, toward_well = flight_axes(start, end)
    origin = Vector(start) + along * (BAND / 2.0)
    top = bottom + STEPS_PER_FLIGHT * rise
    name = f"Flight{index:02d}"

    def plan(distance: float, lateral: float) -> tuple:
        position = origin + along * distance + toward_well * lateral
        return position.x, position.y

    for step in range(1, STEPS_PER_FLIGHT + 1):
        tread_top = bottom + step * rise
        front, back = plan((step - 1) * TREAD - 0.03, -BAND / 2.0 + 0.04), plan(step * TREAD, BAND / 2.0 - 0.04)
        frame.span(f"{name}Tread{step}", (min(front[0], back[0]), min(front[1], back[1]), tread_top - 0.05), (max(front[0], back[0]), max(front[1], back[1]), tread_top), materials["timber"])
        riser_front, riser_back = plan((step - 1) * TREAD, -BAND / 2.0 + 0.04), plan((step - 1) * TREAD + 0.025, BAND / 2.0 - 0.04)
        frame.span(f"{name}Riser{step}", (min(riser_front[0], riser_back[0]), min(riser_front[1], riser_back[1]), tread_top - rise), (max(riser_front[0], riser_back[0]), max(riser_front[1], riser_back[1]), tread_top - 0.05), materials["timber_dark"])

        baluster_base = frame.point(*plan((step - 0.5) * TREAD, BAND / 2.0 - 0.03), tread_top)
        beam(f"{name}Baluster{step}{frame.tag}", baluster_base, baluster_base + Vector((0, 0, HANDRAIL_HEIGHT - 0.05)), 0.035, 0.035, materials["timber_dark"])

    for lateral, label in ((BAND / 2.0 - 0.03, "Well"), (-BAND / 2.0 + 0.03, "Wall")):
        stringer_start = frame.point(*plan(-0.05, lateral), bottom - 0.12)
        stringer_end = frame.point(*plan(RUN + 0.05, lateral), top - 0.12)
        beam(f"{name}{label}Stringer{frame.tag}", stringer_start, stringer_end, 0.05, 0.26, materials["timber_dark"])

    rail_start = frame.point(*plan(0.0, BAND / 2.0 - 0.03), bottom + rise + HANDRAIL_HEIGHT)
    rail_end = frame.point(*plan(RUN, BAND / 2.0 - 0.03), top + HANDRAIL_HEIGHT)
    beam(f"{name}Handrail{frame.tag}", rail_start, rail_end, 0.07, 0.06, materials["timber"])

    ramp_start = frame.point(*plan(-TREAD, 0.0), bottom)
    ramp_end = frame.point(*plan(RUN - TREAD, 0.0), top)
    slope_normal = Vector((0, 0, 1)) - (ramp_end - ramp_start).normalized() * (ramp_end - ramp_start).normalized().z
    ramp = beam(f"{name}Ramp{frame.tag}-colonly", ramp_start - slope_normal.normalized() * 0.05, ramp_end - slope_normal.normalized() * 0.05, BAND - 0.02, 0.1, None)
    ramp.name = f"{name}Ramp{frame.tag}-colonly"
    landing_low, landing_high = plan(RUN - TREAD, -BAND / 2.0), plan(RUN + BAND, BAND / 2.0)
    frame.span(f"{name}Landing-colonly", (min(landing_low[0], landing_high[0]), min(landing_low[1], landing_high[1]), top - 0.1), (max(landing_low[0], landing_high[0]), max(landing_low[1], landing_high[1]), top), None)

    corner_u, corner_v = end
    frame.span(f"{name}CornerBoards", (corner_u - BAND / 2.0, corner_v - BAND / 2.0, top - 0.08), (corner_u + BAND / 2.0, corner_v + BAND / 2.0, top), materials["timber"])


def build_shaft(frame: TowerFrame, materials: dict) -> None:
    """Newel posts at the corners of the well, the guard that keeps the player out of it, the clock room floor
    with its hatch rail, the ground floor boards and the stair door leaf."""
    floor_top = CLOCK_FLOOR
    half = TOWER_SHAFT_HALF

    for corner_u, corner_v in [(-WELL, -WELL), (-WELL, WELL), (WELL, -WELL), (WELL, WELL)]:
        frame.span(f"Newel{corner_u:+.1f}{corner_v:+.1f}", (corner_u - 0.07, corner_v - 0.07, BASE), (corner_u + 0.07, corner_v + 0.07, floor_top + 1.0), materials["timber_dark"])

    frame.span("WellGuardInner-colonly", (-WELL - 0.03, -WELL, BASE), (-WELL + 0.02, WELL, floor_top - 0.15), None)
    frame.span("WellGuardOuter-colonly", (WELL - 0.02, -WELL, BASE), (WELL + 0.03, WELL, floor_top - 0.15), None)
    frame.span("WellGuardFront-colonly", (-WELL, -WELL - 0.03, BASE), (WELL, -WELL + 0.02, floor_top - 0.15), None)
    frame.span("WellGuardBack-colonly", (-WELL, WELL - 0.02, BASE), (WELL, WELL + 0.03, floor_top - 0.15), None)
    frame.span("GroundBoards", (-half, -half, BASE - 0.05), (half, half, BASE + 0.01), materials["timber_dark"])

    # Clock room floor: everything but the hatch the stair comes up through (the two inner corners, the inner band and
    # the front band), so nobody on the last two flights bumps the head on the floor.
    floor_pieces = [((-WELL, -WELL), (WELL, half)), ((WELL, -half), (half, half))]

    for piece_index, ((low_u, low_v), (high_u, high_v)) in enumerate(floor_pieces):
        frame.span(f"ClockFloor{piece_index}", (low_u, low_v, floor_top - 0.15), (high_u, high_v, floor_top), materials["timber"])
        frame.span(f"ClockFloor{piece_index}-colonly", (low_u, low_v, floor_top - 0.15), (high_u, high_v, floor_top), None)

    hatch_rails = [((-WELL, -WELL), (-WELL, half)), ((-WELL, -WELL), (WELL, -WELL))]

    for rail_index, (rail_start, rail_end) in enumerate(hatch_rails):
        low = (min(rail_start[0], rail_end[0]) - 0.03, min(rail_start[1], rail_end[1]) - 0.03)
        high = (max(rail_start[0], rail_end[0]) + 0.03, max(rail_start[1], rail_end[1]) + 0.03)
        frame.span(f"HatchRail{rail_index}", (low[0], low[1], floor_top + HANDRAIL_HEIGHT - 0.06), (high[0], high[1], floor_top + HANDRAIL_HEIGHT), materials["timber"])
        frame.span(f"HatchRail{rail_index}-colonly", (low[0], low[1], floor_top), (high[0], high[1], floor_top + HANDRAIL_HEIGHT), None)

    # Folha aberta para fora, deitada na parede da nave ao lado da porta.
    wall_face_v = NARTHEX_DEPTH - TOWER_CENTER_Y
    frame.span("TowerDoorLeaf", (-TOWER_DOOR[0] / 2.0 - 0.14 - TOWER_DOOR[0], wall_face_v + 0.08, BASE + 0.02), (-TOWER_DOOR[0] / 2.0 - 0.14, wall_face_v + 0.14, BASE + TOWER_DOOR[1] - 0.1), materials["door"])


def build_bell(frame: TowerFrame, materials: dict) -> None:
    """One bell on an oak headstock across the well, ringing wheel, clapper and the rope down to its sally."""
    axle = BELL_AXLE
    bell_center = frame.point(0.0, 0.0, 0.0)
    radius = BELL_MOUTH / 2.0
    profile = [(radius, -1.05), (radius * 1.02, -0.98), (radius * 0.86, -0.85), (radius * 0.68, -0.55), (radius * 0.6, -0.3), (radius * 0.58, -0.2), (radius * 0.45, -0.14), (0.0, -0.12)]

    for bearer_u in (-WELL, WELL):
        frame.span(f"BellBearer{bearer_u:+.1f}", (bearer_u - 0.09, -WELL, axle - 0.34), (bearer_u + 0.09, WELL, axle - 0.12), materials["timber_dark"])

    frame.span("Headstock", (-WELL + 0.05, -0.14, axle - 0.12), (WELL - 0.05, 0.14, axle + 0.18), materials["timber_dark"])
    make_lathe(f"Bell{frame.tag}", (bell_center.x, bell_center.y, axle), profile, 24, materials["bronze"])
    make_lathe(f"BellLip{frame.tag}", (bell_center.x, bell_center.y, axle), [(radius * 1.04, -1.07), (radius * 1.05, -1.0), (radius * 0.9, -0.98)], 24, materials["bronze"])
    beam(f"BellClapper{frame.tag}", frame.point(0.0, 0.0, axle - 0.2), frame.point(0.0, 0.0, axle - 1.0), 0.05, 0.05, materials["iron"])
    make_sphere(f"BellClapperBall{frame.tag}", tuple(frame.point(0.0, 0.0, axle - 0.95)), 0.08, materials["iron"])
    wheel_u = WELL - 0.18
    spokes = 8

    for spoke in range(spokes):
        first = 2.0 * math.pi * spoke / spokes
        second = 2.0 * math.pi * (spoke + 1) / spokes
        rim_start = frame.point(wheel_u, WHEEL_RADIUS * math.cos(first), axle + WHEEL_RADIUS * math.sin(first))
        rim_end = frame.point(wheel_u, WHEEL_RADIUS * math.cos(second), axle + WHEEL_RADIUS * math.sin(second))
        beam(f"BellWheelRim{spoke}{frame.tag}", rim_start, rim_end, 0.05, 0.09, materials["timber"])

        if spoke % 2 == 0:
            beam(f"BellWheelSpoke{spoke}{frame.tag}", frame.point(wheel_u, 0.0, axle), rim_start, 0.04, 0.04, materials["timber"])

    rope_top = frame.point(wheel_u, WHEEL_RADIUS, axle)
    rope_bottom = frame.point(wheel_u, WHEEL_RADIUS, BASE + 1.0)
    beam(f"BellRope{frame.tag}", rope_top, rope_bottom, 0.025, 0.025, materials["rope"])

    for stripe in range(5):
        stripe_bottom = BASE + 2.0 + stripe * 0.16
        sally = frame.point(wheel_u, WHEEL_RADIUS, stripe_bottom)
        make_cylinder(f"BellSally{stripe}{frame.tag}", (sally.x, sally.y, sally.z), 0.045, 0.16, 8, materials["sally_red" if stripe % 2 == 0 else "sally_blue"])


def build_clock_movement(frame: TowerFrame, materials: dict) -> None:
    """Iron birdcage movement on a wooden stand in the middle of the clock room, wheels, barrels, pendulum, weights,
    leading-off rods to the four dials and the motion work behind each dial."""
    floor = CLOCK_FLOOR
    stand_top = floor + 0.55
    cage_top = stand_top + 0.95
    dial_height = floor + 1.8 * TOWER_UPPER_SCALE
    half = TOWER_SHAFT_HALF

    frame.span("ClockStandTop", (-0.65, -0.42, stand_top - 0.08), (0.65, 0.42, stand_top), materials["timber"])

    for leg_u in (-0.58, 0.58):
        for leg_v in (-0.36, 0.36):
            frame.span(f"ClockStandLeg{leg_u:+.1f}{leg_v:+.1f}", (leg_u - 0.05, leg_v - 0.05, floor), (leg_u + 0.05, leg_v + 0.05, stand_top - 0.08), materials["timber_dark"])

    for post_u in (-0.5, 0.5):
        for post_v in (-0.3, 0.3):
            frame.span(f"ClockCagePost{post_u:+.1f}{post_v:+.1f}", (post_u - 0.025, post_v - 0.025, stand_top), (post_u + 0.025, post_v + 0.025, cage_top), materials["iron"])

    for rail_z in (stand_top + 0.02, cage_top - 0.02):
        for rail_v in (-0.3, 0.3):
            frame.span(f"ClockCageRail{rail_z:.2f}{rail_v:+.1f}", (-0.52, rail_v - 0.02, rail_z - 0.02), (0.52, rail_v + 0.02, rail_z + 0.02), materials["iron"])

        for rail_u in (-0.5, 0.0, 0.5):
            frame.span(f"ClockCageBar{rail_z:.2f}{rail_u:+.1f}", (rail_u - 0.02, -0.32, rail_z - 0.02), (rail_u + 0.02, 0.32, rail_z + 0.02), materials["iron"])

    wheels = [(-0.28, 0.25, 0.26, "brass"), (-0.3, 0.62, 0.15, "brass"), (-0.22, 0.8, 0.09, "brass"), (0.26, 0.28, 0.3, "brass"), (0.28, 0.66, 0.16, "brass"), (0.2, 0.84, 0.1, "brass")]

    for wheel_index, (wheel_u, wheel_height, radius, material_key) in enumerate(wheels):
        axle_start = frame.point(wheel_u, -0.3, stand_top + wheel_height)
        axle_end = frame.point(wheel_u, 0.3, stand_top + wheel_height)
        beam(f"ClockArbor{wheel_index}{frame.tag}", axle_start, axle_end, 0.025, 0.025, materials["iron"])
        wheel_center = frame.point(wheel_u, 0.08 - 0.04 * wheel_index, stand_top + wheel_height)
        wheel = make_cylinder(f"ClockWheel{wheel_index}{frame.tag}", (0, 0, -0.015), radius, 0.03, 32, materials[material_key])
        wheel.matrix_world = Matrix.Translation(wheel_center) @ Matrix.Rotation(math.pi / 2.0, 4, "X")
        hub = make_cylinder(f"ClockWheelHub{wheel_index}{frame.tag}", (0, 0, -0.04), radius * 0.25, 0.08, 12, materials["iron"])
        hub.matrix_world = wheel.matrix_world

    for barrel_u in (-0.28, 0.26):
        barrel = make_cylinder(f"ClockBarrel{barrel_u:+.1f}{frame.tag}", (0, 0, -0.2), 0.11, 0.4, 16, materials["timber_dark"])
        barrel.matrix_world = Matrix.Translation(frame.point(barrel_u, 0.0, stand_top + 0.25)) @ Matrix.Rotation(math.pi / 2.0, 4, "X")
        cable_top = frame.point(barrel_u, -0.11 if barrel_u < 0 else 0.11, stand_top + 0.25)
        weight_top = frame.point(barrel_u * 1.6, -0.45 if barrel_u < 0 else 0.45, floor - 3.2)
        beam(f"ClockCable{barrel_u:+.1f}{frame.tag}", cable_top, weight_top, 0.015, 0.015, materials["iron"])
        make_cylinder(f"ClockWeight{barrel_u:+.1f}{frame.tag}", (weight_top.x, weight_top.y, weight_top.z - 0.7), 0.12, 0.7, 12, materials["iron"])

    beam(f"ClockEscapement{frame.tag}", frame.point(-0.32, -0.32, cage_top - 0.08), frame.point(-0.12, -0.32, cage_top - 0.18), 0.03, 0.03, materials["brass"])
    pendulum_top = frame.point(-0.22, -0.34, cage_top - 0.12)
    pendulum_bob = frame.point(-0.22, -0.34, floor - 2.1)
    beam(f"ClockPendulum{frame.tag}", pendulum_top, pendulum_bob, 0.02, 0.02, materials["iron"])
    bob = make_cylinder(f"ClockPendulumBob{frame.tag}", (0, 0, -0.04), 0.17, 0.08, 20, materials["brass"])
    bob.matrix_world = Matrix.Translation(pendulum_bob) @ Matrix.Rotation(math.pi / 2.0, 4, "X")

    hub_point = frame.point(0.0, 0.0, dial_height)
    beam(f"ClockLeadOffUp{frame.tag}", frame.point(0.0, 0.0, cage_top), hub_point, 0.03, 0.03, materials["iron"])
    frame.span("ClockBevelBox", (-0.09, -0.09, dial_height - 0.09), (0.09, 0.09, dial_height + 0.09), materials["iron"])

    for dial_u, dial_v in ((0.0, -half), (0.0, half), (-half, 0.0), (half, 0.0)):
        wall_point = frame.point(dial_u * 0.92, dial_v * 0.92, dial_height)
        beam(f"ClockLeadOff{dial_u:+.1f}{dial_v:+.1f}{frame.tag}", hub_point, wall_point, 0.025, 0.025, materials["iron"])
        frame.span(f"ClockMotionWork{dial_u:+.1f}{dial_v:+.1f}", (dial_u * 0.92 - 0.14, dial_v * 0.92 - 0.14, dial_height - 0.16), (dial_u * 0.92 + 0.14, dial_v * 0.92 + 0.14, dial_height + 0.16), materials["iron"])

    frame.span("ClockMovement-colonly", (-0.66, -0.43, floor), (0.66, 0.43, cage_top), None)


def build_lantern(name: str, position: Vector, materials: dict, chain: float) -> dict:
    """Iron lantern hanging on a chain (glass glows; the real light is listed in the sidecar)."""
    beam(f"{name}Chain", position + Vector((0, 0, 0.25)), position + Vector((0, 0, 0.25 + chain)), 0.02, 0.02, materials["iron"])
    make_span(f"{name}Cap", tuple(position + Vector((-0.12, -0.12, 0.18))), tuple(position + Vector((0.12, 0.12, 0.25))), materials["iron"])
    make_span(f"{name}Glass", tuple(position + Vector((-0.09, -0.09, -0.12))), tuple(position + Vector((0.09, 0.09, 0.18))), materials["lantern_glow"])
    make_span(f"{name}Base", tuple(position + Vector((-0.11, -0.11, -0.16))), tuple(position + Vector((0.11, 0.11, -0.12))), materials["iron"])

    return {"position": godot(position), **LANTERN}


def build_tower_inside(side_sign: int, materials: dict) -> tuple:
    """Stair, bell and clock of one tower; returns its lanterns and its stair path."""
    frame = TowerFrame(side_sign)
    flights = stair_plan()
    lantern_heights = [BASE + 3.4, BASE + 11.5, ATTIC_WALK + 1.6, BELFRY_BOTTOM + 3.2, CLOCK_FLOOR + 2.9]
    lantern_spots = [(0.0, -0.35, height) for height in lantern_heights[:-1]] + [(0.9, 0.9, lantern_heights[-1])]

    for index, flight in enumerate(flights):
        build_flight(frame, index, flight, materials)

    build_shaft(frame, materials)
    build_bell(frame, materials)
    build_clock_movement(frame, materials)
    lights = [build_lantern(f"TowerLantern{index}{frame.tag}", frame.point(*spot), materials, 1.2) for index, spot in enumerate(lantern_spots)]

    for index, (_, lantern_v, height) in enumerate(lantern_spots[:-1]):
        frame.span(f"LanternBearer{index}", (-WELL, lantern_v - 0.05, height + 1.45), (WELL, lantern_v + 0.05, height + 1.57), materials["timber_dark"])

    return lights, stair_path(frame, flights)


def stair_path(frame: TowerFrame, flights: list) -> list:
    """Walk from the nave through the stair door, up to the attic and onto the catwalk, back, and on up to the clock room."""
    half = TOWER_SHAFT_HALF
    outside = [frame.point(0.0, half + 1.8, BASE), frame.point(0.0, half - 0.4, BASE)]
    corners = [frame.point(CORNERS[0][0], CORNERS[0][1], BASE)] + [frame.point(end[0], end[1], bottom + STEPS_PER_FLIGHT * rise) for _, end, bottom, rise in flights]
    door_u = (sum(ATTIC_DOOR_X) / 2.0) - TOWER_MIDDLE_X
    attic_landing = corners[ATTIC_FLIGHTS]
    attic = [frame.point(door_u, half + 0.5, ATTIC_WALK), frame.point(door_u, half + 1.6, ATTIC_WALK), Vector((0.0, sum(CROSS_WALK_Y) / 2.0, ATTIC_WALK)), Vector((0.0, BODY_LENGTH - 6.0, ATTIC_WALK))]
    back = list(reversed(attic[:-1])) + [attic_landing]
    clock_room = [frame.point(CORNER, CORNER, CLOCK_FLOOR)]
    path = outside + corners[: ATTIC_FLIGHTS + 1] + attic + back + corners[ATTIC_FLIGHTS + 1:] + clock_room

    return [godot(point) for point in path]


def build_attic(materials: dict) -> list:
    """Queen-post trusses, purlins, ridge, catwalk with handrails and cross walks; returns its lanterns."""
    truss_ys = [TRUSS_FIRST_Y + TRUSS_PITCH * index for index in range(int((BODY_LENGTH - WALL - TRUSS_FIRST_Y) / TRUSS_PITCH) + 1)]
    tie_top = ATTIC_FLOOR + TIE_BEAM
    eave_inner = NAVE_HALF + WALL - 0.05
    queen_top = roof_underside_height(QUEEN_POST_X) - 0.2
    lights = []

    for truss_index, truss_y in enumerate(truss_ys):
        name = f"Truss{truss_index:02d}"
        make_span(f"{name}Tie", (-eave_inner, truss_y - 0.11, ATTIC_FLOOR), (eave_inner, truss_y + 0.11, tie_top), materials["timber_dark"])
        make_span(f"{name}Tie-colonly", (-eave_inner, truss_y - 0.11, ATTIC_FLOOR), (eave_inner, truss_y + 0.11, tie_top), None)
        make_span(f"{name}Straining", (-QUEEN_POST_X, truss_y - 0.1, queen_top - 0.2), (QUEEN_POST_X, truss_y + 0.1, queen_top), materials["timber_dark"])

        for side_sign in (-1, 1):
            rafter_foot = Vector((side_sign * (eave_inner - 0.1), truss_y, roof_underside_height(eave_inner - 0.1) - 0.1))
            rafter_head = Vector((side_sign * 0.12, truss_y, roof_underside_height(0.12) - 0.1))
            beam(f"{name}Rafter{side_sign:+d}", rafter_foot, rafter_head, 0.2, 0.2, materials["timber_dark"])
            make_span(f"{name}Ashlar{side_sign:+d}", (side_sign * (eave_inner - 0.35) - 0.08, truss_y - 0.08, tie_top), (side_sign * (eave_inner - 0.35) + 0.08, truss_y + 0.08, roof_underside_height(eave_inner - 0.35) - 0.1), materials["timber_dark"])
            queen_x = side_sign * QUEEN_POST_X
            make_span(f"{name}Queen{side_sign:+d}", (queen_x - 0.1, truss_y - 0.1, tie_top), (queen_x + 0.1, truss_y + 0.1, queen_top), materials["timber_dark"])
            make_span(f"{name}Queen{side_sign:+d}-colonly", (queen_x - 0.1, truss_y - 0.1, tie_top), (queen_x + 0.1, truss_y + 0.1, queen_top), None)
            strut_x = side_sign * 4.4
            beam(f"{name}Strut{side_sign:+d}", Vector((queen_x, truss_y, tie_top + 0.25)), Vector((strut_x, truss_y, roof_underside_height(4.4) - 0.2)), 0.12, 0.12, materials["timber_dark"])

    for side_sign in (-1, 1):
        for purlin_x in PURLIN_X:
            purlin_z = roof_underside_height(purlin_x) - 0.12
            make_span(f"Purlin{side_sign:+d}{purlin_x}", (side_sign * purlin_x - 0.09, NARTHEX_DEPTH, purlin_z - 0.12), (side_sign * purlin_x + 0.09, BODY_LENGTH - WALL, purlin_z + 0.06), materials["timber"])

    make_span("RidgeBeam", (-0.1, NARTHEX_DEPTH, roof_underside_height(0.0) - 0.22), (0.1, BODY_LENGTH - WALL, roof_underside_height(0.0)), materials["timber"])
    build_catwalk(materials, truss_ys)

    for lantern_index, lantern_y in enumerate(truss_ys[2::4]):
        lights.append(build_lantern(f"AtticLantern{lantern_index}", Vector((0.0, lantern_y, queen_top - 1.25)), materials, 0.85))

    build_attic_clutter(materials)

    return lights


def build_catwalk(materials: dict, truss_ys: list) -> None:
    """Boards over the tie beams down the middle, a cross walk to each tower door, posts and handrails."""
    walk_bottom = ATTIC_WALK - 0.04
    far_end = BODY_LENGTH - WALL - 0.3

    make_span("Catwalk", (-CATWALK_HALF, NARTHEX_DEPTH, walk_bottom), (CATWALK_HALF, far_end, ATTIC_WALK), materials["timber"])
    make_span("Catwalk-colonly", (-CATWALK_HALF, NARTHEX_DEPTH, ATTIC_FLOOR), (CATWALK_HALF, far_end, ATTIC_WALK), None)

    for side_sign in (-1, 1):
        door_far = side_sign * ATTIC_DOOR_X[1]
        low_x, high_x = sorted((side_sign * CATWALK_HALF, door_far))
        make_span(f"CrossWalk{side_sign:+d}", (low_x, CROSS_WALK_Y[0], walk_bottom), (high_x, CROSS_WALK_Y[1], ATTIC_WALK), materials["timber"])
        make_span(f"CrossWalk{side_sign:+d}-colonly", (low_x, CROSS_WALK_Y[0], ATTIC_FLOOR), (high_x, CROSS_WALK_Y[1], ATTIC_WALK), None)
        rail_x = side_sign * (CATWALK_HALF + 0.04)
        rail_start = CROSS_WALK_Y[1] + 0.05

        make_span(f"CatwalkRail{side_sign:+d}", (rail_x - 0.035, rail_start, ATTIC_WALK + HANDRAIL_HEIGHT - 0.06), (rail_x + 0.035, far_end, ATTIC_WALK + HANDRAIL_HEIGHT), materials["timber"])
        make_span(f"CrossRail{side_sign:+d}", (low_x, CROSS_WALK_Y[1] + 0.01, ATTIC_WALK + HANDRAIL_HEIGHT - 0.06), (high_x, CROSS_WALK_Y[1] + 0.08, ATTIC_WALK + HANDRAIL_HEIGHT), materials["timber"])

        for post_y in [rail_start] + [truss_y for truss_y in truss_ys if truss_y > rail_start]:
            make_span(f"CatwalkPost{side_sign:+d}{post_y:.1f}", (rail_x - 0.035, post_y - 0.035, ATTIC_WALK), (rail_x + 0.035, post_y + 0.035, ATTIC_WALK + HANDRAIL_HEIGHT), materials["timber"])


def build_attic_clutter(materials: dict) -> None:
    """What the roofers left: a stack of spare tiles, planks against a truss, a bucket and a coil of rope."""
    for tile_index in range(6):
        make_span(f"SpareTiles{tile_index}", (2.4, 15.2 + tile_index * 0.05, ATTIC_FLOOR), (2.85, 15.24 + tile_index * 0.05, ATTIC_FLOOR + 0.42), materials["tile"])

    for plank_index in range(3):
        beam(f"LeaningPlank{plank_index}", Vector((-3.2 - plank_index * 0.14, 24.6, ATTIC_FLOOR)), Vector((-2.7 - plank_index * 0.14, 24.75, ATTIC_FLOOR + 2.0)), 0.25, 0.03, materials["timber"])

    make_cylinder("Bucket", (1.1, 28.4, ATTIC_FLOOR), 0.16, 0.3, 12, materials["timber_dark"])
    make_cylinder("RopeCoil", (-1.2, 9.3, ATTIC_FLOOR), 0.28, 0.12, 16, materials["rope"])


def ambience_boxes() -> list:
    """Godot (center, size, energy) of the interior probes: the two shafts (some daylight through slits and louvers)
    and the attic (dark under the roof); they keep the open sky's ambient light out."""
    shaft_low = Vector((TOWER_MIDDLE_X - TOWER_SHAFT_HALF, TOWER_CENTER_Y - TOWER_SHAFT_HALF, BASE))
    shaft_high = Vector((TOWER_MIDDLE_X + TOWER_SHAFT_HALF, TOWER_CENTER_Y + TOWER_SHAFT_HALF, CLOCK_FLOOR + CLOCK_HEIGHT))
    attic_low = Vector((-NAVE_HALF - WALL, NARTHEX_DEPTH, ATTIC_FLOOR))
    attic_high = Vector((NAVE_HALF + WALL, BODY_LENGTH - WALL, roof_underside_height(0.0)))
    boxes = []

    for side_sign, low, high, energy in ((-1, shaft_low, shaft_high, 0.55), (1, shaft_low, shaft_high, 0.55), (1, attic_low, attic_high, 0.3)):
        first = Vector((side_sign * low.x, low.y, low.z))
        second = Vector((side_sign * high.x, high.y, high.z))
        center = (first + second) / 2.0
        size = [abs(value) for value in godot(second - first)]
        boxes.append({"center": godot(center), "size": size, "energy": energy})

    return boxes


def godot(point: Vector) -> list:
    """Blender (x, y, z) to the Godot model space of the glTF (x, z, -y)."""
    return [round(point.x, 4), round(point.z, 4), round(-point.y, 4)]


def build_tower_materials() -> dict:
    materials = build_materials()

    return {
        **materials,
        "timber": make_plain_material("M_TowerTimber", (0.42, 0.3, 0.2), 0.0, 0.85),
        "timber_dark": make_plain_material("M_TowerTimberDark", (0.27, 0.19, 0.13), 0.0, 0.9),
        "door": materials["wood"],
        "bronze": make_plain_material("M_BellBronze", (0.36, 0.3, 0.17), 0.85, 0.4),
        "brass": make_plain_material("M_ClockBrass", (0.78, 0.6, 0.3), 0.9, 0.35),
        "iron": materials["iron"],
        "rope": make_plain_material("M_BellRope", (0.72, 0.62, 0.45), 0.0, 0.95),
        "sally_red": make_plain_material("M_SallyRed", (0.62, 0.12, 0.14), 0.0, 0.9),
        "sally_blue": make_plain_material("M_SallyBlue", (0.14, 0.22, 0.55), 0.0, 0.9),
        "tile": materials["roof"],
        "lantern_glow": materials["lamp_glow"],
    }


def build_towers() -> Path:
    output_path = OUTPUT_DIR / "cathedral_towers.gltf"
    lights = []
    paths = {}

    bpy.ops.wm.read_factory_settings(use_empty=True)
    materials = build_tower_materials()

    for side_sign in (-1, 1):
        tower_lights, path = build_tower_inside(side_sign, materials)
        lights += tower_lights
        paths["L" if side_sign < 0 else "R"] = path

    lights += build_attic(materials)
    finalize(materials)
    bpy.ops.export_scene.gltf(filepath=str(output_path), export_format="GLTF_SEPARATE", export_texture_dir="textures", export_yup=True)
    output_path.with_suffix(".json").write_text(json.dumps({"lights": lights, "stair_paths": paths, "ambience": ambience_boxes()}, indent=1))

    return output_path


def finalize(materials: dict) -> None:
    tile_sizes = {materials["roof"].name: 3.0}
    visible_meshes = [scene_object for scene_object in bpy.data.objects if scene_object.type == "MESH" and not scene_object.name.endswith("-colonly")]

    bpy.context.view_layer.update()

    for mesh_object in visible_meshes:
        map_uvs_per_face(mesh_object, tile_sizes.get(mesh_object.data.materials[0].name, 2.0))

    merge_meshes_by_material("Towers")


if __name__ == "__main__":
    print(f"BUILT towers -> {build_towers()}")
