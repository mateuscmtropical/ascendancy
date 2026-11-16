"""Realistic horse body for the Mula sem cabeça, taken from "Equine Model" by Lova Dahn (CC BY 4.0,
https://sketchfab.com/3d-models/equine-model-06efca4a943b48fdaa99973c674c8aa3; credit in CREDITS.md).

The download needs a Sketchfab login, so it is not fetched by fetch_assets.py: save "Horse Update 2026.obj" (inside
the "Original format" archive) as tools/vendor/mobs/equine_model/Horse Update 2026.obj.

Only the body mesh is used (no eyes, teeth, tongue). It is bulked sideways, its neck thickened into a trunk, scaled
to the units of the CC0 pack horse whose skeleton and animations the mula rides on, and then mapped back through the
generator's proportion stretch: the generator later stretches skeleton and skin together, which puts every bone
inside the anatomy of this mesh (elbows, knees, hocks and hooves line up) and gives the mesh its true shape back."""

from pathlib import Path

import math

import bpy
from mathutils import Matrix, Vector

SOURCE = Path(__file__).resolve().parent.parent / "tools/vendor/mobs/equine_model/Horse Update 2026.obj"
BODY_PREFIX = "Body"
WORK_VERTICES = 45000  # enough skin for the neck cut; mula_body.lighten brings it down to the game count
UNITS_PER_METRE = 4.68  # elbow of the mesh (0.85 m) on the shoulder joint of the stretched skeleton
FORWARD_SHIFT = -0.149  # knees and hocks of the mesh on the knee and hock joints
SIDEWAYS_BULK = 1.3  # heavier than the model horse, as in the concept sheet
# Neck axis on the source mesh, in metres (Y forward is negative, Z up): from the base to the middle, where it is cut.
NECK_BASE_METRES = Vector((0.0, -0.5, 1.28))
NECK_MOUTH_METRES = Vector((0.0, -0.78, 1.56))
NECK_SWELL_START, NECK_SWELL_END = -0.25, 0.0  # metres along the axis where the neck grows into a tree trunk
NECK_SWELL_SIDEWAYS, NECK_SWELL_DEPTH = 0.6, 0.2
NECK_TOP_SWELL = 0.4  # share of the sideways swell left at the mouth: the trunk tapers
NECK_RAISE = math.radians(15.0)  # the model carries its neck at 45 degrees, the mula at 60
NECK_LENGTHEN = 1.3
LEG_FATTEN_METRES = 0.02  # draught-horse legs: the skin moves away from the middle of its leg...
LEG_FATTEN_Z = (0.6, 0.85)  # ...fully below the first height, not at all above the second
LEG_SLICE_METRES = 0.02
TAIL_START_Y, TAIL_SHORTEN, TAIL_DROOP = 0.72, 0.5, 0.6  # the model's dock sticks straight out
UNSTRETCH_PASSES = 12


def to_pack_units(position: Vector) -> Vector:
    """A point of the source mesh (metres) bulked, with the neck swollen, in pack units."""
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

    return Vector((position.x * SIDEWAYS_BULK * (1.0 + NECK_SWELL_SIDEWAYS * swell * taper) * UNITS_PER_METRE,
                   swollen.y * UNITS_PER_METRE + FORWARD_SHIFT, swollen.z * UNITS_PER_METRE))


def leg_slice(position: Vector) -> tuple:
    return position.x > 0.0, position.y > 0.0, int(position.z / LEG_SLICE_METRES)


def fatten_legs(positions: list) -> list:
    """The points with every leg thickened around the middle of each of its horizontal slices."""
    sums = {}

    for position in positions:
        total, count = sums.get(leg_slice(position), (Vector((0.0, 0.0, 0.0)), 0))
        sums[leg_slice(position)] = (total + position, count + 1)

    middles = {key: total / count for key, (total, count) in sums.items()}

    return [fattened(position, middles[leg_slice(position)]) for position in positions]


def fattened(position: Vector, middle: Vector) -> Vector:
    share = min(1.0, max(0.0, (LEG_FATTEN_Z[1] - position.z) / (LEG_FATTEN_Z[1] - LEG_FATTEN_Z[0])))
    outwards = Vector((position.x - middle.x, position.y - middle.y, 0.0))

    return position + outwards.normalized() * LEG_FATTEN_METRES * share


def unstretched(target: Vector, stretched) -> Vector:
    """The point that `stretched` sends to `target` (the stretch is close to a shift, so stepping back converges)."""
    guess = target.copy()

    for _ in range(UNSTRETCH_PASSES):
        guess += target - stretched(guess)

    return guess


def neck_axis(stretched) -> tuple:
    """(base, mouth) of the neck cut where the generator works: pack units, before the proportion stretch."""
    return unstretched(to_pack_units(NECK_BASE_METRES), stretched), unstretched(to_pack_units(NECK_MOUTH_METRES), stretched)


def load_body(stretched):
    """Object "Mula": the body of the source horse, lightened, in pack units before the proportion stretch."""
    before = set(bpy.context.scene.objects)
    bpy.ops.wm.obj_import(filepath=str(SOURCE))
    imported = [scene_object for scene_object in bpy.context.scene.objects if scene_object not in before]
    body = next(scene_object for scene_object in imported if scene_object.name.startswith(BODY_PREFIX))

    for scene_object in imported:
        if scene_object != body:
            bpy.data.objects.remove(scene_object)

    decimate = body.modifiers.new("Decimate", "DECIMATE")
    decimate.ratio = min(1.0, WORK_VERTICES / len(body.data.vertices))
    mesh = bpy.data.meshes.new_from_object(body.evaluated_get(bpy.context.evaluated_depsgraph_get()))
    world = body.matrix_world.copy()
    bpy.data.objects.remove(body)
    positions = fatten_legs([world @ vertex.co for vertex in mesh.vertices])

    for vertex, position in zip(mesh.vertices, positions):
        vertex.co = unstretched(to_pack_units(position), stretched)

    mesh.materials.clear()
    mesh.name = "Mula"
    mula = bpy.data.objects.new("Mula", mesh)
    bpy.context.scene.collection.objects.link(mula)

    return mula
