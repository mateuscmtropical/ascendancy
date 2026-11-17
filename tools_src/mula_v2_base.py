"""Realistic bull-built body for the Mula sem cabeça, sculpted over "Equine Model" by Lova Dahn (CC BY 4.0,
https://sketchfab.com/3d-models/equine-model-06efca4a943b48fdaa99973c674c8aa3; credit in CREDITS.md).

Save "Horse Update 2026.obj" (inside the "Original format" archive) as
tools/vendor/mobs/equine_model/Horse Update 2026.obj.

Reshapes the riding-horse mesh into the heavy, bull-chested silhouette of the concept sheet: wide forehand stance,
massive twin pectorals with a deep sternal cleft, smooth rounded shoulders/scapula/deltoid/triceps flowing into
thick forearms, prominent knees/hocks/fetlocks with cannon flexor tendons, heavy draft hooves, and a thick conical
neck cut cleanly at upper-mid neck."""

from pathlib import Path
import math

import bpy
from mathutils import Matrix, Vector

SOURCE = Path(__file__).resolve().parent.parent / "tools/vendor/mobs/equine_model/Horse Update 2026.obj"
BODY_PREFIX = "Body"
WORK_VERTICES = 50000
UNITS_PER_METRE = 4.68
FORWARD_SHIFT = -0.149

# True centreline of the neck cylinder on the source mesh (metres, Y forward is negative, Z up):
# cut higher up the neck (just below the jaw/throat-latch at Y=-0.70, Z=1.54) so a tall, thick conical neck rises
# boldly above the shoulders like the concept sheet, while still keeping 100% of the head/ears above the cut.
NECK_PIVOT_METRES = Vector((0.0, -0.36, 1.18))
NECK_BASE_METRES = Vector((0.0, -0.42, 1.24))
NECK_MOUTH_METRES = Vector((0.0, -0.70, 1.55))
NECK_RAISE = math.radians(15.0)
NECK_LENGTHEN = 1.12

FRONT_JOINTS = (Vector((0.107, -0.43, 0.93)), Vector((0.107, -0.44, 0.48)), Vector((0.107, -0.52, 0.025)))
HIND_JOINTS = (Vector((0.141, 0.46, 0.93)), Vector((0.146, 0.66, 0.52)), Vector((0.147, 0.59, 0.025)))
GIRDLE_X = 0.04
FOOT_LENGTH = 0.20

TAIL_START_Y = 0.70
TAIL_SHORTEN = 0.32
TAIL_DROOP = 0.78

# Smooth anatomical intermuscular grooves on the +X half of the source mesh (metres):
# (point A, point B, radius, depth).
ANATOMICAL_GROOVES = [
    # Sternal cleft between the twin pectoral globes
    (Vector((0.0, -0.64, 1.15)), Vector((0.0, -0.35, 0.80)), 0.046, 0.022),
    # Deltopectoral groove separating pectoral from deltoid/brachiocephalic
    (Vector((0.058, -0.59, 0.88)), Vector((0.165, -0.51, 1.17)), 0.036, 0.014),
    # Jugular / brachiocephalic groove climbing the conical neck
    (Vector((0.068, -0.55, 1.12)), Vector((0.080, -0.65, 1.52)), 0.038, 0.012),
    # Splenius / trapezius groove along upper neck
    (Vector((0.092, -0.42, 1.30)), Vector((0.078, -0.60, 1.56)), 0.038, 0.010),
    # Spine of scapula groove
    (Vector((0.145, -0.26, 1.32)), Vector((0.215, -0.47, 1.04)), 0.038, 0.011),
    # Posterior border of triceps against the ribcage (broad & organic, not a sharp cliff)
    (Vector((0.210, -0.36, 0.85)), Vector((0.200, -0.17, 1.13)), 0.045, 0.013),
    # Division between long and lateral heads of triceps
    (Vector((0.228, -0.46, 0.98)), Vector((0.210, -0.24, 0.94)), 0.032, 0.011),
    # Forearm extensor / flexor groove
    (Vector((0.148, -0.45, 0.86)), Vector((0.130, -0.44, 0.53)), 0.026, 0.012),
    # Front cannon flexor-tendon grooves (lateral & medial)
    (Vector((0.125, -0.45, 0.42)), Vector((0.120, -0.47, 0.19)), 0.019, 0.010),
    (Vector((0.088, -0.45, 0.42)), Vector((0.092, -0.47, 0.19)), 0.019, 0.009),
    # Anterior border of thigh / tensor fasciae latae
    (Vector((0.215, 0.34, 1.24)), Vector((0.215, 0.46, 0.88)), 0.038, 0.014),
    # Biceps femoris anterior-middle division
    (Vector((0.250, 0.47, 1.21)), Vector((0.215, 0.58, 0.85)), 0.034, 0.014),
    # Groove between biceps femoris and semitendinosus
    (Vector((0.220, 0.58, 1.19)), Vector((0.182, 0.68, 0.80)), 0.034, 0.015),
    # Gaskin lateral groove above the hock
    (Vector((0.185, 0.56, 0.84)), Vector((0.165, 0.65, 0.57)), 0.026, 0.012),
    # Hind cannon flexor-tendon groove
    (Vector((0.165, 0.65, 0.45)), Vector((0.162, 0.62, 0.19)), 0.020, 0.010),
    # Dorsal sacral cleft between the twin gluteal globes
    (Vector((0.0, 0.28, 1.37)), Vector((0.0, 0.67, 1.32)), 0.048, 0.016),
]


def smoothstep(edge0: float, edge1: float, value: float) -> float:
    t = min(1.0, max(0.0, (value - edge0) / (edge1 - edge0)))
    return t * t * (3.0 - 2.0 * t)


def gaussian(distance: float, radius: float) -> float:
    ratio = distance / radius
    return math.exp(-ratio * ratio)


def segment_distance(point: Vector, start: Vector, end: Vector) -> float:
    span = end - start
    length_sq = span.length_squared
    if length_sq <= 1e-9:
        return (point - start).length
    share = min(1.0, max(0.0, (point - start).dot(span) / length_sq))
    return (point - (start + span * share)).length


def sculpt_muscle_detail(raw: Vector, shaped: Vector) -> Vector:
    """Carve anatomical intermuscular grooves, subtle rib/serratus digitations and directional muscle fascicles."""
    sym = Vector((abs(raw.x), raw.y, raw.z))
    side = 1.0 if raw.x >= 0.0 else -1.0
    outward = Vector((side * 0.85, 0.0, 0.25)).normalized()

    if raw.y < -0.50 and raw.z < 1.22:
        outward = Vector((side * 0.55, -0.80, 0.15)).normalized()
    elif raw.z < 0.88:
        leg_x = 0.107 if raw.y < 0.0 else 0.145
        leg_y = -0.45 if raw.y < 0.0 else 0.60
        radial = Vector((sym.x - leg_x, sym.y - leg_y, 0.0))
        if radial.length > 1e-4:
            radial.normalize()
            outward = Vector((radial.x * side, radial.y, 0.0))

    carve = 0.0
    for start, end, radius, depth in ANATOMICAL_GROOVES:
        dist = segment_distance(sym, start, end)
        if dist < radius * 1.9:
            carve += depth * gaussian(dist, radius * 0.80)

    rib_band = smoothstep(-0.20, -0.06, sym.y) * (1.0 - smoothstep(0.16, 0.28, sym.y))
    rib_height = smoothstep(0.84, 0.94, sym.z) * (1.0 - smoothstep(1.14, 1.24, sym.z))
    rib_side = smoothstep(0.16, 0.23, sym.x)
    rib_wave = math.sin((sym.y + sym.z * 0.38) * 54.0)
    rib_relief = 0.0038 * rib_band * rib_height * rib_side * rib_wave

    above_hoof = smoothstep(0.14, 0.28, sym.z)
    if sym.z > 1.22 and sym.y < -0.32:
        flow_coord = sym.x * 40.0 + (sym.y * 0.65 + sym.z * 0.76) * 14.0
        bundle_strength = 0.0042
    elif sym.y < -0.20 and sym.z > 0.82:
        flow_coord = (sym.z - sym.y * 0.55) * 38.0 + sym.x * 20.0
        bundle_strength = 0.0052
    elif sym.y > 0.25 and sym.z > 0.82:
        flow_coord = (sym.y * 0.82 + sym.z * 0.55) * 38.0 + sym.x * 18.0
        bundle_strength = 0.0050
    elif sym.z <= 0.82:
        flow_coord = math.atan2(sym.y - (-0.45 if sym.y < 0.0 else 0.60), sym.x - (0.107 if sym.y < 0.0 else 0.145)) * 9.0
        bundle_strength = 0.0040 * smoothstep(0.46, 0.62, sym.z)
    else:
        flow_coord = (sym.z * 0.90 - sym.y * 0.25) * 40.0
        bundle_strength = 0.0030

    fascicle = (abs(math.sin(flow_coord)) - 0.5) * 2.0 * bundle_strength * above_hoof
    secondary = math.sin(flow_coord * 2.1 + sym.y * 9.0) * bundle_strength * 0.32 * above_hoof

    return shaped + outward * (-carve + rib_relief + fascicle + secondary)


def sculpt_anatomy(position: Vector, sculpt_detail: bool = True) -> Vector:
    """Reshape one vertex of the source OBJ (metres) into the bull-built Mula anatomy (still in metres)."""
    raw = position.copy()
    side = 1.0 if raw.x >= 0.0 else -1.0
    abs_x = abs(raw.x)
    x, y, z = raw.x, raw.y, raw.z

    # 1. Tall, powerful athletic legs (+11.5 cm between pastern and elbow/stifle)
    leg_lift = 0.115 * smoothstep(0.05, 0.86, z)

    # 2. Very smooth bull stance & barrel width transition (no sudden cliff behind the scapula!)
    front_to_mid = smoothstep(-0.58, 0.12, y)
    mid_to_hind = smoothstep(0.05, 0.52, y)
    stance_scale = 1.45 * (1.0 - front_to_mid) + 1.25 * front_to_mid * (1.0 - mid_to_hind) + 1.30 * mid_to_hind
    x *= stance_scale

    # 3. Massive bull forehand: deep brisket between the forelegs, athletic tucked waist behind
    brisket_zone = (1.0 - smoothstep(-0.58, -0.14, y)) * smoothstep(0.72, 0.88, z) * (1.0 - smoothstep(1.04, 1.20, z)) * (1.0 - smoothstep(0.08, 0.16, abs_x))
    waist_tuck = smoothstep(-0.06, 0.16, y) * (1.0 - smoothstep(0.28, 0.48, y)) * (1.0 - smoothstep(0.78, 0.98, z)) * smoothstep(0.65, 0.78, z)
    z += -0.040 * brisket_zone + 0.038 * waist_tuck

    # Twin medial pectoral globes (strictly medial between the shoulders so no shelf overhangs the forelegs!)
    pec_dist = Vector(((abs_x - 0.070) / 0.085, (y - (-0.55)) / 0.16, (z - 0.99) / 0.20)).length
    pec_cleft = smoothstep(0.008, 0.042, abs_x) * (1.0 - smoothstep(0.11, 0.18, abs_x))
    pec_lobe = gaussian(pec_dist, 1.0) * pec_cleft
    x += side * 0.042 * pec_lobe
    y -= 0.076 * pec_lobe
    z -= 0.018 * pec_lobe

    # Broad, smoothly rounded bull withers & trapezius blending far back into the thoracic spine
    hump_dist = Vector(((y - (-0.28)) / 0.38, (z - 1.32) / 0.28, 0.0)).length
    hump = gaussian(hump_dist, 1.0)
    z += 0.036 * hump
    x += side * 0.056 * hump * smoothstep(0.02, 0.16, abs_x)

    # Rounded scapula, deltoid and humerus flowing continuously down into the forearm
    shoulder_dist = Vector(((abs_x - 0.18) / 0.13, (y - (-0.40)) / 0.26, (z - 1.06) / 0.28)).length
    shoulder = gaussian(shoulder_dist, 1.0) * smoothstep(0.06, 0.14, abs_x)
    x += side * 0.062 * shoulder
    y -= 0.028 * shoulder

    arm_bridge_dist = Vector(((abs_x - 0.12) / 0.10, (y - (-0.47)) / 0.15, (z - 0.82) / 0.18)).length
    arm_bridge = gaussian(arm_bridge_dist, 1.0) * smoothstep(0.05, 0.10, abs_x)
    x += side * 0.045 * arm_bridge
    y -= 0.042 * arm_bridge

    triceps_dist = Vector(((abs_x - 0.19) / 0.12, (y - (-0.29)) / 0.18, (z - 0.94) / 0.20)).length
    triceps = gaussian(triceps_dist, 1.0) * smoothstep(0.08, 0.15, abs_x)
    x += side * 0.052 * triceps
    y += 0.032 * triceps

    # 4. Tall, thick, smooth conical bull neck — swells ONLY the narrow neck cylinder (never inflating the wide
    # scapula behind it, so there is zero shoulder-pad shelf!)
    neck_dir = (NECK_MOUTH_METRES - NECK_PIVOT_METRES).normalized()
    neck_span = (NECK_MOUTH_METRES - NECK_PIVOT_METRES).length
    along_neck = (raw - NECK_PIVOT_METRES).dot(neck_dir)
    # Gate begins smoothly above the shoulder/withers plane and tapers out laterally so scapula stays clean
    neck_gate = smoothstep(-0.02, 0.30, along_neck) * smoothstep(1.06, 1.26, raw.z)

    if neck_gate > 0.0:
        progress = min(1.25, max(0.0, along_neck / neck_span))
        taper = 1.0 - 0.28 * progress
        # Add width mainly where the source mesh is narrow (abs_x < 0.16 m), fading to 0 on wide shoulder blades
        narrow_neck = 1.0 - smoothstep(0.11, 0.21, abs_x)
        x += side * (0.095 * narrow_neck * smoothstep(0.0, 0.055, abs_x)) * neck_gate * taper

        on_axis = NECK_PIVOT_METRES + neck_dir * max(0.0, along_neck)
        across_yz = Vector((0.0, y - on_axis.y, z - on_axis.z))
        lengthen = neck_dir * (max(0.0, along_neck) * (NECK_LENGTHEN - 1.0) * neck_gate)
        turn = Matrix.Rotation(-NECK_RAISE * neck_gate, 3, "X")
        pivoted = NECK_PIVOT_METRES + turn @ (
            Vector((0.0, y, z)) - NECK_PIVOT_METRES + lengthen + across_yz * (0.20 * neck_gate * taper * narrow_neck)
        )
        y, z = pivoted.y, pivoted.z

    # 5. Broad, rounded double croup and heavy thighs
    croup_dist = Vector(((abs_x - 0.15) / 0.15, (y - 0.46) / 0.25, (z - 1.28) / 0.19)).length
    croup = gaussian(croup_dist, 1.0) * smoothstep(0.015, 0.07, abs_x)
    z += 0.044 * croup
    x += side * 0.054 * croup

    thigh_dist = Vector(((abs_x - 0.21) / 0.12, (y - 0.52) / 0.21, (z - 1.04) / 0.23)).length
    thigh = gaussian(thigh_dist, 1.0) * smoothstep(0.10, 0.17, abs_x)
    x += side * 0.068 * thigh
    y += 0.042 * thigh

    # 6. Forearms, gaskins, marked knees/hocks/fetlocks, flexor tendons and heavy draft hooves
    if raw.z < 0.95:
        is_front = raw.y < 0.0
        axis_x = (0.107 if is_front else 0.145) * stance_scale
        if is_front:
            axis_y = -0.52 + 0.09 * smoothstep(0.02, 0.48, raw.z)
        else:
            axis_y = 0.59 + 0.09 * smoothstep(0.02, 0.52, raw.z) - 0.18 * smoothstep(0.52, 0.90, raw.z)

        dx = abs(x) - axis_x
        dy = y - axis_y
        radial_x = x - side * axis_x
        in_leg = 1.0 - smoothstep(0.17, 0.30, math.hypot(dx, dy))

        if is_front:
            forearm_swell = 0.48 * math.sin(math.pi * min(1.0, max(0.0, (raw.z - 0.48) / 0.46))) ** 1.35 * (
                1.0 if 0.48 < raw.z < 0.94 else 0.0
            )
            knee_bump = 0.26 * gaussian(raw.z - 0.47, 0.048)
            cannon_band = smoothstep(0.17, 0.23, raw.z) * (1.0 - smoothstep(0.40, 0.45, raw.z))
            fetlock_bump = 0.25 * gaussian(raw.z - 0.145, 0.042)
            hoof_flare = (0.38 + 0.14 * (1.0 - smoothstep(0.0, 0.10, raw.z))) * (1.0 - smoothstep(0.085, 0.13, raw.z))

            girth = (forearm_swell + knee_bump + 0.14 * cannon_band + fetlock_bump + hoof_flare) * in_leg
            x += radial_x * girth
            y += dy * (girth + (0.10 * knee_bump if dy < 0.0 else 0.0))
            if dy > 0.0:
                y += 0.016 * cannon_band * in_leg
        else:
            gaskin_swell = 0.48 * math.sin(math.pi * min(1.0, max(0.0, (raw.z - 0.53) / 0.40))) ** 1.4 * (
                1.0 if 0.53 < raw.z < 0.93 else 0.0
            )
            hock_bump = 0.26 * gaussian(raw.z - 0.52, 0.052)
            cannon_band = smoothstep(0.17, 0.23, raw.z) * (1.0 - smoothstep(0.44, 0.49, raw.z))
            fetlock_bump = 0.25 * gaussian(raw.z - 0.145, 0.042)
            hoof_flare = (0.38 + 0.14 * (1.0 - smoothstep(0.0, 0.10, raw.z))) * (1.0 - smoothstep(0.085, 0.13, raw.z))

            girth = (gaskin_swell + hock_bump + 0.14 * cannon_band + fetlock_bump + hoof_flare) * in_leg
            x += radial_x * girth
            y += dy * girth
            if dy > 0.0:
                y += (0.032 * gaussian(raw.z - 0.535, 0.045) + 0.016 * cannon_band) * in_leg

    # 7. Shorten and droop the dock stub so it hides cleanly inside the wide fire tail
    beyond_dock = max(0.0, raw.y - TAIL_START_Y)
    if beyond_dock > 0.0 and raw.z > 1.10:
        y -= beyond_dock * (1.0 - TAIL_SHORTEN)
        z -= beyond_dock * TAIL_DROOP

    z = max(0.0, z + leg_lift)
    shaped = Vector((x, y, z))

    if sculpt_detail:
        shaped = sculpt_muscle_detail(raw, shaped)
        shaped.z = max(0.0, shaped.z)

    return shaped


def to_pack_units(position: Vector, sculpt_detail: bool = True) -> Vector:
    shaped = sculpt_anatomy(position, sculpt_detail=sculpt_detail)
    return Vector((shaped.x * UNITS_PER_METRE, shaped.y * UNITS_PER_METRE + FORWARD_SHIFT, shaped.z * UNITS_PER_METRE))


def hoof_fires() -> dict:
    front = to_pack_units(FRONT_JOINTS[2], sculpt_detail=False)
    hind = to_pack_units(HIND_JOINTS[2], sculpt_detail=False)
    return {
        "FrontL": Vector((abs(front.x), front.y, 0.20)),
        "FrontR": Vector((-abs(front.x), front.y, 0.20)),
        "BackL": Vector((abs(hind.x), hind.y, 0.20)),
        "BackR": Vector((-abs(hind.x), hind.y, 0.20)),
    }


def tail_dock() -> Vector:
    return to_pack_units(Vector((0.0, TAIL_START_Y + 0.02, 1.28)), sculpt_detail=False)


def leg_bones() -> dict:
    bones = {}
    legs = {"Front": (FRONT_JOINTS, -FOOT_LENGTH), "Back": (HIND_JOINTS, -FOOT_LENGTH)}
    sides = {"L": 1.0, "R": -1.0}

    for leg in legs:
        for side, sign in sides.items():
            (top, middle, hoof), foot_reach = legs[leg]
            girdle = Vector((GIRDLE_X, top.y, top.z))
            below = hoof - Vector((0.0, 0.0, FOOT_LENGTH))
            toe = hoof + Vector((0.0, foot_reach, 0.0))
            beyond = toe + Vector((0.0, foot_reach, 0.0))
            chain = {
                f"{leg}Leg": (girdle, top),
                f"{leg}UpLeg": (top, middle),
                f"{leg}LowLeg": (middle, hoof),
                f"{leg}LowLeg.{side}_end": (hoof, below),
                f"{leg}Foot": (hoof, toe),
                f"{leg}Foot.{side}_end": (toe, beyond),
            }

            for name, ends in chain.items():
                full_name = name if name.endswith("_end") else f"{name}.{side}"
                bones[full_name] = tuple(
                    to_pack_units(Vector((end.x * sign, end.y, end.z)), sculpt_detail=False) for end in ends
                )

    return bones


def neck_axis() -> tuple:
    return (
        to_pack_units(NECK_BASE_METRES, sculpt_detail=False),
        to_pack_units(NECK_MOUTH_METRES, sculpt_detail=False),
    )


def load_body(light: bool = True):
    before = set(bpy.context.scene.objects)
    bpy.ops.wm.obj_import(filepath=str(SOURCE))
    imported = [scene_object for scene_object in bpy.context.scene.objects if scene_object not in before]
    body = next(scene_object for scene_object in imported if scene_object.name.startswith(BODY_PREFIX))

    for scene_object in imported:
        if scene_object != body:
            bpy.data.objects.remove(scene_object)

    if light:
        decimate = body.modifiers.new("Decimate", "DECIMATE")
        decimate.ratio = min(1.0, WORK_VERTICES / len(body.data.vertices))
        mesh = bpy.data.meshes.new_from_object(body.evaluated_get(bpy.context.evaluated_depsgraph_get()))
    else:
        mesh = body.data.copy()

    world = body.matrix_world.copy()
    bpy.data.objects.remove(body)

    for vertex in mesh.vertices:
        vertex.co = to_pack_units(world @ vertex.co, sculpt_detail=True)

    mesh.materials.clear()
    mesh.name = "Mula" if light else "MulaRelief"
    mula = bpy.data.objects.new(mesh.name, mesh)
    bpy.context.scene.collection.objects.link(mula)

    return mula
