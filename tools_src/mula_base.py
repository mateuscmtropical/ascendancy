"""Realistic horse body for the Mula sem cabeça, taken from "Equine Model" by Lova Dahn (CC BY 4.0,
https://sketchfab.com/3d-models/equine-model-06efca4a943b48fdaa99973c674c8aa3; credit in CREDITS.md).

The download needs a Sketchfab login, so it is not fetched by fetch_assets.py: save "Horse Update 2026.obj" (inside
the "Original format" archive) as tools/vendor/mobs/equine_model/Horse Update 2026.obj.

Only the body mesh is used (no eyes, teeth, tongue), and its shape is kept: the neck is raised and thickened into a
trunk, chest and shoulders get a little volume, the dock is shortened. It is scaled to the units of the CC0 pack
horse whose skeleton and animations the mula rides on. The generator works in the proportions of that pack horse and
then moves the bones into the anatomy of this mesh (`stretched`), so the game mesh is loaded through the inverse of
that move (`unstretched`) and ends exactly in its own shape; the full-resolution mesh is loaded as it is, to bake
its relief onto the game mesh."""

from pathlib import Path

import math

import bpy
from mathutils import Matrix, Vector

SOURCE = Path(__file__).resolve().parent.parent / "tools/vendor/mobs/equine_model/Horse Update 2026.obj"
BODY_PREFIX = "Body"
WORK_VERTICES = 40000  # enough skin for the neck cut; mula_body.lighten brings it down to the game count
UNITS_PER_METRE = 4.68  # elbow of the mesh (0.85 m) on the shoulder joint of the moved skeleton
FORWARD_SHIFT = -0.149  # knees and hocks of the mesh on the knee and hock joints
# Neck axis on the source mesh, in metres (Y forward is negative, Z up): from the base to the middle, where it is cut.
NECK_BASE_METRES = Vector((0.0, -0.5, 1.28))
NECK_MOUTH_METRES = Vector((0.0, -0.78, 1.56))
NECK_SWELL_START, NECK_SWELL_END = -0.25, 0.0  # metres along the axis where the neck grows into a tree trunk
NECK_SWELL_SIDEWAYS, NECK_SWELL_DEPTH = 0.3, 0.15
NECK_TOP_SWELL = 0.4  # share of the sideways swell left at the mouth: the trunk tapers
NECK_RAISE = math.radians(8.0)  # the model carries its neck at 45 degrees, the mula a little higher
NECK_LENGTHEN = 1.0
CHEST_MIDDLE_METRES = Vector((0.0, -0.45, 1.05))  # shoulder and breast get fuller around this point...
CHEST_REACH_METRES = 0.28
CHEST_FILL = 0.18  # ...by this share of their distance to the middle plane, fading out with distance
TAIL_START_Y, TAIL_SHORTEN, TAIL_DROOP = 0.72, 0.5, 0.6  # the model's dock sticks straight out
UNSTRETCH_PASSES = 12
# Muscle added to the legs, on the source mesh (metres): (is front leg, axis low point, axis high point, share of
# extra girth at the middle of the span). The skin swells away from the axis, most at mid-span, nothing at the ends.
LEG_MUSCLES = [
    (True, Vector((0.107, -0.44, 0.50)), Vector((0.107, -0.40, 0.92)), 0.4),  # forearm
    (False, Vector((0.141, 0.68, 0.55)), Vector((0.141, 0.47, 0.90)), 0.4),  # gaskin
    (False, Vector((0.141, 0.47, 0.84)), Vector((0.141, 0.45, 1.22)), 0.16),  # thigh
]
LEG_MUSCLE_REACH = (0.16, 0.3)  # metres from the axis: full swell within the first, none beyond the second
# Joints of the left legs on the source mesh (metres): where the leg leaves the trunk, knee or hock, hoof.
FRONT_JOINTS = (Vector((0.107, -0.40, 0.92)), Vector((0.107, -0.44, 0.50)), Vector((0.107, -0.50, 0.03)))
HIND_JOINTS = (Vector((0.141, 0.45, 0.92)), Vector((0.141, 0.68, 0.55)), Vector((0.141, 0.60, 0.03)))
# The fore legs take the girth of the hind legs: hind over fore half-width (outer, inner, back, front), measured on the
# source mesh (muscles included) in 24 steps from the hoof (0) to where the leg leaves the trunk (1), knee at 0.5.
HIND_GIRTH_ON_FORE = (
    (1.16, 0.90, 1.35, 0.90),
    (1.20, 0.93, 1.31, 0.90),
    (1.23, 0.97, 1.24, 0.90),
    (1.30, 1.03, 1.25, 0.90),
    (1.31, 1.04, 1.26, 0.93),
    (1.27, 1.03, 1.29, 0.97),
    (1.17, 0.99, 1.29, 1.04),
    (1.10, 0.95, 1.28, 1.13),
    (1.07, 0.91, 1.23, 1.29),
    (1.10, 0.91, 1.12, 1.50),
    (1.10, 0.91, 1.03, 1.68),
    (1.28, 0.95, 0.97, 1.78),
    (1.48, 1.16, 0.99, 1.80),
    (1.65, 1.40, 1.00, 1.78),
    (1.61, 1.55, 1.03, 1.69),
    (1.45, 1.55, 1.09, 1.53),
    (1.28, 1.55, 1.21, 1.36),
    (1.15, 1.56, 1.37, 1.24),
    (1.10, 1.45, 1.51, 1.19),
    (1.12, 1.28, 1.35, 1.15),
    (1.09, 1.17, 1.14, 1.06),
    (1.07, 1.19, 0.91, 0.97),
    (1.04, 1.41, 0.97, 0.91),
    (1.04, 1.52, 1.00, 0.92),
)
HIND_GIRTH_FADE = (0.75, 0.9)  # share of the fore leg: full hind girth below the first, none above the second (chest)
GIRDLE_X = 0.035  # the short bone that carries each leg starts this far from the middle plane
FOOT_LENGTH = 0.2


def muscled(position: Vector) -> Vector:
    """A point of the source mesh with the leg muscles filled out."""
    filled = position.copy()
    side = 1.0 if position.x > 0.0 else -1.0

    for is_front, low, high, girth in LEG_MUSCLES:
        span = (position.z - low.z) / (high.z - low.z)

        if (position.y < 0.0) != is_front or not 0.0 < span < 1.0:
            continue

        on_axis = low.lerp(high, span)
        away = Vector((position.x - on_axis.x * side, position.y - on_axis.y, 0.0))
        fade = min(1.0, max(0.0, (LEG_MUSCLE_REACH[1] - away.length) / (LEG_MUSCLE_REACH[1] - LEG_MUSCLE_REACH[0])))
        filled += away * girth * math.sin(math.pi * span) ** 2 * fade

    return filled


def hind_girth_ratios(share: float) -> tuple:
    """(outer, inner, back, front) girth ratios at a share of the fore leg, between the measured steps."""
    steps = len(HIND_GIRTH_ON_FORE)
    place = min(steps - 1.0, max(0.0, share * steps - 0.5))
    below = int(place)
    above = min(steps - 1, below + 1)

    return tuple(low + (high - low) * (place - below) for low, high in zip(HIND_GIRTH_ON_FORE[below], HIND_GIRTH_ON_FORE[above]))


def with_hind_girth(position: Vector) -> Vector:
    """A point of a fore leg pushed out from the leg axis to the girth of the hind leg at the same share of the leg."""
    top, knee, hoof = FRONT_JOINTS
    side = 1.0 if position.x > 0.0 else -1.0

    if position.y >= 0.0 or not hoof.z < position.z < top.z:
        return position

    is_lower = position.z < knee.z
    span = (position.z - hoof.z) / (knee.z - hoof.z) if is_lower else (position.z - knee.z) / (top.z - knee.z)
    on_axis = hoof.lerp(knee, span) if is_lower else knee.lerp(top, span)
    share = span * 0.5 if is_lower else 0.5 + span * 0.5
    away_x, away_y = position.x - on_axis.x * side, position.y - on_axis.y
    outer, inner, back, front = hind_girth_ratios(share)
    across = (away_x * away_x + away_y * away_y) ** 0.5
    near = min(1.0, max(0.0, (LEG_MUSCLE_REACH[1] - across) / (LEG_MUSCLE_REACH[1] - LEG_MUSCLE_REACH[0])))
    low = min(1.0, max(0.0, (HIND_GIRTH_FADE[1] - share) / (HIND_GIRTH_FADE[1] - HIND_GIRTH_FADE[0])))
    ratio_x = outer if away_x * side > 0.0 else inner
    ratio_y = back if away_y > 0.0 else front

    return Vector((position.x + away_x * (ratio_x - 1.0) * near * low, position.y + away_y * (ratio_y - 1.0) * near * low, position.z))


def to_pack_units(position: Vector) -> Vector:
    """A point of the source mesh (metres) with its legs muscled and its neck swollen, in pack units."""
    position = with_hind_girth(muscled(position))
    axis = (NECK_MOUTH_METRES - NECK_BASE_METRES).normalized()
    along = (position - NECK_BASE_METRES).dot(axis)
    swell = min(1.0, max(0.0, (along - NECK_SWELL_START) / (NECK_SWELL_END - NECK_SWELL_START))) if position.y < 0.0 else 0.0
    swell = swell * swell * (3.0 - 2.0 * swell)
    raise_neck = Matrix.Rotation(-NECK_RAISE * swell, 3, "X")
    on_axis = NECK_BASE_METRES + axis * along
    across = Vector((0.0, position.y - on_axis.y, position.z - on_axis.z))
    longer = along * (1.0 + (NECK_LENGTHEN - 1.0) * swell) if along > 0.0 else along
    swollen = NECK_BASE_METRES + raise_neck @ (axis * longer + across * (1.0 + NECK_SWELL_DEPTH * swell))
    taper = 1.0 - (1.0 - NECK_TOP_SWELL) * min(1.0, max(0.0, along / (NECK_MOUTH_METRES - NECK_BASE_METRES).length))
    beyond_dock = max(0.0, position.y - TAIL_START_Y)
    swollen.y -= beyond_dock * (1.0 - TAIL_SHORTEN)
    swollen.z -= beyond_dock * TAIL_DROOP

    chest = math.exp(-((Vector((0.0, position.y, position.z)) - CHEST_MIDDLE_METRES).length / CHEST_REACH_METRES) ** 2)

    return Vector((position.x * (1.0 + CHEST_FILL * chest) * (1.0 + NECK_SWELL_SIDEWAYS * swell * taper) * UNITS_PER_METRE,
                   swollen.y * UNITS_PER_METRE + FORWARD_SHIFT, swollen.z * UNITS_PER_METRE))


def leg_bones() -> dict:
    """{bone of the pack skeleton: (head, tail)} that puts both pairs of legs on the joints of this mesh, pack units."""
    bones = {}
    legs = {"Front": (FRONT_JOINTS, -FOOT_LENGTH), "Back": (HIND_JOINTS, -FOOT_LENGTH)}
    sides = {"L": 1.0, "R": -1.0}

    for leg, side in [(leg, side) for leg in legs for side in sides]:
        (top, middle, hoof), foot_reach = legs[leg]
        girdle = Vector((GIRDLE_X, top.y, top.z))
        below = hoof - Vector((0.0, 0.0, FOOT_LENGTH))
        toe = hoof + Vector((0.0, foot_reach, 0.0))
        beyond = toe + Vector((0.0, foot_reach, 0.0))
        chain = {f"{leg}Leg": (girdle, top), f"{leg}UpLeg": (top, middle), f"{leg}LowLeg": (middle, hoof), f"{leg}LowLeg.{side}_end": (hoof, below),
                 f"{leg}Foot": (hoof, toe), f"{leg}Foot.{side}_end": (toe, beyond)}

        for name, ends in chain.items():
            full_name = name if name.endswith("_end") else f"{name}.{side}"
            bones[full_name] = tuple(to_pack_units(Vector((end.x * sides[side], end.y, end.z))) for end in ends)

    return bones


def unstretched(target: Vector, stretched) -> Vector:
    """The point that `stretched` sends to `target` (the stretch is close to a shift, so stepping back converges)."""
    guess = target.copy()

    for _ in range(UNSTRETCH_PASSES):
        guess += target - stretched(guess)

    return guess


def neck_axis(stretched) -> tuple:
    """(base, mouth) of the neck cut where the generator works: pack units, before the proportion stretch."""
    return unstretched(to_pack_units(NECK_BASE_METRES), stretched), unstretched(to_pack_units(NECK_MOUTH_METRES), stretched)


def load_body(stretched=None):
    """The body of the source horse in pack units. With `stretched`: object "Mula", lightened, where the generator
    works (before the bones move). Without: object "MulaRelief", every vertex, in its final place."""
    before = set(bpy.context.scene.objects)
    bpy.ops.wm.obj_import(filepath=str(SOURCE))
    imported = [scene_object for scene_object in bpy.context.scene.objects if scene_object not in before]
    body = next(scene_object for scene_object in imported if scene_object.name.startswith(BODY_PREFIX))

    for scene_object in imported:
        if scene_object != body:
            bpy.data.objects.remove(scene_object)

    decimate = body.modifiers.new("Decimate", "DECIMATE")
    decimate.ratio = min(1.0, WORK_VERTICES / len(body.data.vertices)) if stretched else 1.0
    mesh = bpy.data.meshes.new_from_object(body.evaluated_get(bpy.context.evaluated_depsgraph_get()))
    world = body.matrix_world.copy()
    bpy.data.objects.remove(body)

    for vertex in mesh.vertices:
        placed = to_pack_units(world @ vertex.co)
        vertex.co = unstretched(placed, stretched) if stretched else placed

    mesh.materials.clear()
    mesh.name = "Mula"
    mula = bpy.data.objects.new("Mula" if stretched else "MulaRelief", mesh)
    bpy.context.scene.collection.objects.link(mula)

    return mula
