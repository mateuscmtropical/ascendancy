"""The Saci (Brazilian folklore): a one-legged boy in a red cap with a pipe, hopping about the farm.

Built from the CC0 Quaternius pieces the town characters use, so he shares their 65-bone rig, the UAL clips and
the face shapes: the base body with the skin tinted brown and its briefs recoloured into linen shorts, the head grown to
a boy's proportions, the right leg cut at mid-thigh with a rounded stump, short hair, and two meshes made here and riveted to the head bone: the floppy
red cap and the clay pipe in the corner of the mouth. The hop and the one-legged idle are clips of
build_combat_animations.py; features/hub/walking_npc.gd plays them at the scale of a boy.

Usage:
  blender -b --factory-startup -P tools_src/build_saci.py
"""

import math
import sys
from pathlib import Path

import bmesh
import bpy
import numpy
from mathutils import Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))

from build_characters import BASE_BODY_DIR, HAIR_DIR, OUTPUT_DIR, bind_mesh_to_armature, delete_objects, downscale_large_textures, import_gltf  # noqa: E402
from face_shapes import add_face_shapes, find_eyes  # noqa: E402

OUTPUT_PATH = OUTPUT_DIR / "saci.gltf"
BODY_MESH_NAME = "Saci_Skin"  # not a bone name: Godot would rename the bone
RIGHT_LEG_BONES = ("thigh_r", "calf_r", "foot_r", "ball_r")
STUMP_HEIGHT = 0.64  # metres above the soles where the right leg ends, mid-thigh (the knee is at ~0.5)
SEAM_WELD_DISTANCE = 0.00001
STUMP_ROUNDING = 0.035  # how far the middle of the stump cap bulges down
# the base skin texture is light with dark grey briefs: the skin is tinted brown and the briefs become linen shorts
SKIN_TINT = (0.60, 0.43, 0.33)
SHORTS_LINEN = (0.60, 0.54, 0.44)
BRIEFS_MAX_SATURATION = 0.14
BRIEFS_MAX_VALUE = 0.5
HEAD_SCALE = 1.14  # a boy's head is big for his body
MUSCLE_BONE_PREFIXES = ("spine", "clavicle", "upperarm", "lowerarm", "thigh", "calf", "pelvis")
MUSCLE_SMOOTHING_PASSES = 6
CAP_COLOR = (0.30, 0.012, 0.01, 1.0)  # linear: a deep sRGB red
# linear values (the glTF factor): sRGB about (0.33, 0.2, 0.12) and (0.25, 0.15, 0.1)
PIPE_WOOD_COLOR = (0.09, 0.035, 0.014, 1.0)
PIPE_BOWL_COLOR = (0.05, 0.02, 0.01, 1.0)
HAIR = "Hair_Buzzed"
# the cap: brim ring (centre height at the front and at the back, half width, half depth), then the path of its
# middle as a quadratic curve to the drooping tip, and the radius along it
CAP_BRIM = (1.79, 1.725, 0.106, 0.122)
CAP_PATH = ((0.0, 0.012), (0.0, 0.06, 2.0), (0.07, 0.30, 1.84))
CAP_RINGS = 22
CAP_SIDES = 24
CAP_CUFF = 0.012  # the rolled edge stands out this much from the brim
MOUTH_DROP = 0.074  # metres below the eye centres
MOUTH_HALF_WIDTH = 0.024
MOUTH_INSET = 0.006  # the stem starts this far inside the lips
PIPE_STEM = (0.07, 0.005)  # length and radius
PIPE_BOWL = (0.024, 0.011)  # height and radius
PIPE_DROOP = math.radians(18.0)  # the stem hangs down and out from the corner of the mouth
PIPE_SPLAY = math.radians(35.0)


def weight_in(vertex, group_indices: set) -> float:
    return sum(group.weight for group in vertex.groups if group.group in group_indices)


def deform_layer(mesh_bmesh):
    return mesh_bmesh.verts.layers.deform.verify()


def paint_cap_with_rim_skin(mesh_bmesh, cap_faces: list) -> None:
    """The filled hole has no UVs of its own: each corner takes the skin UV its vertex has on the thigh."""
    uv_layer = mesh_bmesh.loops.layers.uv.active
    mesh_bmesh.faces.index_update()
    cap = {face.index for face in cap_faces}
    rim_uv = {}

    for face in cap_faces:
        for loop in face.loops:
            outside = next((other for other in loop.vert.link_loops if other.face.index not in cap), None)
            rim_uv[loop.vert.index] = outside[uv_layer].uv.copy() if outside else None

    fallback = next(uv for uv in rim_uv.values() if uv is not None)

    for face in cap_faces:
        for loop in face.loops:
            uv = rim_uv.get(loop.vert.index)
            loop[uv_layer].uv = fallback if uv is None else uv


def weld_seams(body) -> None:
    """The glTF import splits vertices along UV seams; welding them back around the cut makes it a single closed
    rim. Only the legs: the face measurements need the lips split."""
    to_world = body.matrix_world
    mesh_bmesh = bmesh.new()

    mesh_bmesh.from_mesh(body.data)

    legs = [vertex for vertex in mesh_bmesh.verts if (to_world @ vertex.co).z < STUMP_HEIGHT + 0.2]

    bmesh.ops.remove_doubles(mesh_bmesh, verts=legs, dist=SEAM_WELD_DISTANCE)
    mesh_bmesh.to_mesh(body.data)
    mesh_bmesh.free()


def cut_right_leg(body) -> None:
    """Deletes the right leg below STUMP_HEIGHT and closes the hole with a rounded cap carried by the thigh."""
    leg_groups = {body.vertex_groups[name].index for name in RIGHT_LEG_BONES}
    to_world = body.matrix_world
    mesh_bmesh = bmesh.new()

    mesh_bmesh.from_mesh(body.data)
    mesh_bmesh.verts.ensure_lookup_table()

    leg = [vertex for vertex in mesh_bmesh.verts if weight_in(body.data.vertices[vertex.index], leg_groups) > 0.5 and (to_world @ vertex.co).z < STUMP_HEIGHT]

    leg_side = math.copysign(1.0, sum((to_world @ vertex.co).x for vertex in leg))

    bmesh.ops.delete(mesh_bmesh, geom=leg, context="VERTS")

    deform = deform_layer(mesh_bmesh)
    thigh = body.vertex_groups["thigh_r"].index
    rim = [edge for edge in mesh_bmesh.edges if edge.is_boundary and all((to_world @ vertex.co).x * leg_side > 0.0 and (to_world @ vertex.co).z < STUMP_HEIGHT + 0.12 for vertex in edge.verts)]
    cap = bmesh.ops.holes_fill(mesh_bmesh, edges=rim, sides=0)["faces"]
    poked = bmesh.ops.poke(mesh_bmesh, faces=cap)

    bmesh.ops.recalc_face_normals(mesh_bmesh, faces=poked["faces"])

    for centre in poked["verts"]:
        centre.co.z -= STUMP_ROUNDING / to_world.to_scale().z
        centre[deform].clear()
        centre[deform][thigh] = 1.0

    mesh_bmesh.verts.index_update()
    paint_cap_with_rim_skin(mesh_bmesh, poked["faces"])

    print(f"  right leg: {len(leg)} vertices off, stump cap of {len(rim)} edges, {len(poked['faces'])} faces")
    mesh_bmesh.to_mesh(body.data)
    mesh_bmesh.free()


def recolor_skin(body) -> None:
    """Copy of the body texture with the skin tinted brown and the briefs turned into linen shorts."""
    material = body.data.materials[0]
    texture = next(node for node in material.node_tree.nodes if node.type == "TEX_IMAGE" and node.image and "Normal" not in node.image.name and "Roughness" not in node.image.name)
    source = texture.image
    image = source.copy()
    pixels = numpy.array(source.pixels[:]).reshape(-1, 4)
    value = pixels[:, :3].max(axis=1)
    saturation = (value - pixels[:, :3].min(axis=1)) / numpy.maximum(value, 1e-4)
    briefs = (saturation < BRIEFS_MAX_SATURATION) & (value < BRIEFS_MAX_VALUE)
    luminance = pixels[:, :3].mean(axis=1, keepdims=True)

    pixels[:, :3] *= numpy.array(SKIN_TINT)
    pixels[briefs, :3] = numpy.array(SHORTS_LINEN) * (0.75 + luminance[briefs])
    image.name = "T_Saci_Skin"
    image.filepath_raw = "//T_Saci_Skin.png"
    image.pixels[:] = pixels.clip(0.0, 1.0).ravel()
    image.pack()
    texture.image = image
    print(f"  skin recoloured, {int(briefs.sum())} pixels of shorts")


def soften_muscles(body) -> None:
    """A boy, not a strongman: relaxes the sculpted muscles of trunk, arms and leg (smoothing also slims them)
    and drops the normal map that draws the six-pack."""
    material = body.data.materials[0]
    groups = {group.index for group in body.vertex_groups if group.name.startswith(MUSCLE_BONE_PREFIXES)}
    mesh_bmesh = bmesh.new()

    for node in [node for node in material.node_tree.nodes if node.type == "NORMAL_MAP"]:
        material.node_tree.nodes.remove(node)

    mesh_bmesh.from_mesh(body.data)
    mesh_bmesh.verts.ensure_lookup_table()

    muscle = [vertex for vertex in mesh_bmesh.verts if not vertex.is_boundary and weight_in(body.data.vertices[vertex.index], groups) > 0.6]

    for _ in range(MUSCLE_SMOOTHING_PASSES):
        bmesh.ops.smooth_vert(mesh_bmesh, verts=muscle, factor=0.5, use_axis_x=True, use_axis_y=True, use_axis_z=True)

    mesh_bmesh.to_mesh(body.data)
    mesh_bmesh.free()


def scale_head(meshes: list, armature) -> None:
    """Grows everything the head bone carries (skin up the neck blending out) around the top of the neck."""
    pivot = armature.matrix_world @ armature.data.bones["Head"].head_local

    for mesh_object in meshes:
        head_group = mesh_object.vertex_groups.get("Head")
        to_world = mesh_object.matrix_world
        to_local = to_world.inverted()

        if head_group is None:
            continue

        for vertex in mesh_object.data.vertices:
            weight = weight_in(vertex, {head_group.index})
            position = to_world @ vertex.co
            vertex.co = to_local @ (pivot + (position - pivot) * (1.0 + (HEAD_SCALE - 1.0) * weight))


def plain_material(name: str, color: tuple, roughness: float):
    material = bpy.data.materials.new(name)
    principled = material.node_tree.nodes["Principled BSDF"] if material.use_nodes else None

    if principled is None:
        material.use_nodes = True
        principled = material.node_tree.nodes["Principled BSDF"]

    principled.inputs["Base Color"].default_value = color
    principled.inputs["Roughness"].default_value = roughness

    return material


def riveted_to_head(mesh_object, armature) -> None:
    group = mesh_object.vertex_groups.new(name="Head")

    group.add(list(range(len(mesh_object.data.vertices))), 1.0, "REPLACE")
    mesh_object.modifiers.new("Armature", "ARMATURE").object = armature
    mesh_object.parent = armature


def facing(eyes: list) -> float:
    """+1 when the face looks down +Y in the imported scene, -1 when it looks down -Y."""
    return 1.0 if eyes[0].centre.y > 0.0 else -1.0


def mouth_corner(body, eyes: list, back: float) -> Vector:
    """Left corner of the lips: MOUTH_DROP below the eyes, on the front of the face."""
    eye_height = eyes[0].centre.z
    corner_height = eye_height - MOUTH_DROP
    to_world = body.matrix_world
    near = [to_world @ vertex.co for vertex in body.data.vertices]
    lips = [point for point in near if abs(point.x - MOUTH_HALF_WIDTH) < 0.006 and abs(point.z - corner_height) < 0.006 and point.y * back < 0.0]
    front = min(lips, key=lambda point: point.y * back)

    return Vector((MOUTH_HALF_WIDTH, front.y + MOUTH_INSET * back, corner_height))


def cap_ring(t: float, back: float) -> tuple:
    """Centre, tilt and radius scale of one ring of the cap; t runs from the brim (0) to the tip (1)."""
    start = Vector((CAP_PATH[0][0], CAP_PATH[0][1] * back, (CAP_BRIM[0] + CAP_BRIM[1]) / 2.0))
    bend = Vector((CAP_PATH[1][0], CAP_PATH[1][1] * back, CAP_PATH[1][2]))
    tip = Vector((CAP_PATH[2][0], CAP_PATH[2][1] * back, CAP_PATH[2][2]))
    centre = start * (1.0 - t) ** 2 + bend * 2.0 * t * (1.0 - t) + tip * t * t
    # a beanie: the crown keeps its width over the head, then the felt narrows into the floppy tip
    shape = 1.0 if t < 0.18 else max(0.0, 1.0 - (t - 0.18) / 0.82) ** 1.15
    dome = math.sqrt(max(0.0, 1.0 - (max(0.0, t - 0.12) / 0.3) ** 2)) * 0.35 + 0.65 if t < 0.42 else 0.0

    return centre, max(shape, dome * shape if t >= 0.18 else shape)


def build_cap(armature, back: float):
    mesh_bmesh = bmesh.new()
    rings = []
    tilt = (CAP_BRIM[0] - CAP_BRIM[1]) / 2.0

    for ring_index in range(CAP_RINGS + 1):
        t = ring_index / CAP_RINGS
        centre, scale = cap_ring(t, back)
        lean = tilt * max(0.0, 1.0 - t * 3.0)
        ring = []

        for side in range(CAP_SIDES):
            angle = 2.0 * math.pi * side / CAP_SIDES
            across, along = math.cos(angle), math.sin(angle) * back  # along * back > 0 is the back of the head
            point = centre + Vector((across * CAP_BRIM[2] * scale, along * CAP_BRIM[3] * scale, -lean * along * back))
            ring.append(mesh_bmesh.verts.new(point))

        rings.append(ring)

    cuff = [mesh_bmesh.verts.new(vertex.co + (vertex.co - Vector((0.0, CAP_PATH[0][1] * back, vertex.co.z))).normalized() * CAP_CUFF + Vector((0.0, 0.0, -0.022))) for vertex in rings[0]]
    hem = [mesh_bmesh.verts.new(vertex.co + Vector((0.0, 0.0, -0.03))) for vertex in rings[0]]

    for lower, upper in [(hem, cuff), (cuff, rings[0])] + list(zip(rings[:-1], rings[1:])):
        for side in range(CAP_SIDES):
            following = (side + 1) % CAP_SIDES
            mesh_bmesh.faces.new((lower[side], lower[following], upper[following], upper[side]))

    mesh_bmesh.faces.new(list(reversed(rings[-1])))
    bmesh.ops.recalc_face_normals(mesh_bmesh, faces=mesh_bmesh.faces)

    mesh = bpy.data.meshes.new("Saci_Cap")
    mesh_bmesh.to_mesh(mesh)
    mesh_bmesh.free()

    for polygon in mesh.polygons:
        polygon.use_smooth = True

    cap = bpy.data.objects.new("Saci_Cap", mesh)
    bpy.context.collection.objects.link(cap)
    cap.data.materials.append(plain_material("M_SaciCap", CAP_COLOR, 0.95))
    riveted_to_head(cap, armature)

    return cap


def add_cylinder(name: str, start: Vector, direction: Vector, length: float, radius: float, material):
    bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=radius, depth=length, location=start + direction * length / 2.0)

    part = bpy.context.active_object
    part.name = name
    part.rotation_mode = "QUATERNION"
    part.rotation_quaternion = Vector((0.0, 0.0, 1.0)).rotation_difference(direction)
    part.data.materials.append(material)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    bpy.ops.object.shade_smooth()

    return part


def build_pipe(armature, body, eyes: list, back: float):
    """Stem from the left corner of the mouth, out and down; the bowl stands up at its end."""
    corner = mouth_corner(body, eyes, back)
    outwards = Vector((math.sin(PIPE_SPLAY) * math.copysign(1.0, corner.x), -math.cos(PIPE_SPLAY) * back, 0.0))
    stem_direction = (outwards * math.cos(PIPE_DROOP) + Vector((0.0, 0.0, -math.sin(PIPE_DROOP)))).normalized()
    stem = add_cylinder("Saci_PipeStem", corner, stem_direction, PIPE_STEM[0], PIPE_STEM[1], plain_material("M_SaciPipe", PIPE_WOOD_COLOR, 0.6))
    bowl_base = corner + stem_direction * PIPE_STEM[0] + Vector((0.0, 0.0, -PIPE_BOWL[1] * 0.6))
    bowl = add_cylinder("Saci_PipeBowl", bowl_base, Vector((0.0, 0.0, 1.0)), PIPE_BOWL[0], PIPE_BOWL[1], plain_material("M_SaciPipeBowl", PIPE_BOWL_COLOR, 0.7))

    bpy.ops.object.select_all(action="DESELECT")
    stem.select_set(True)
    bowl.select_set(True)
    bpy.context.view_layer.objects.active = stem
    bpy.ops.object.join()
    stem.name = "Saci_Pipe"
    riveted_to_head(stem, armature)
    print(f"  pipe at the mouth corner {tuple(round(value, 3) for value in corner)}")

    return stem


def build_saci() -> Path:
    bpy.ops.wm.read_factory_settings(use_empty=True)

    body_objects = import_gltf(BASE_BODY_DIR / "Superhero_Male_FullBody.gltf")
    armature = next(scene_object for scene_object in body_objects if scene_object.type == "ARMATURE")
    body = next(scene_object for scene_object in body_objects if scene_object.name.startswith("SuperHero_Male"))
    eyes_object = bpy.data.objects["Eyes"]
    eyebrows = bpy.data.objects["Eyebrows"]

    delete_objects([scene_object for scene_object in body_objects if scene_object.type == "MESH" and not scene_object.vertex_groups])
    armature.name = "Armature"
    body.name = BODY_MESH_NAME

    hair_objects = import_gltf(HAIR_DIR / f"{HAIR}.gltf")
    hair_meshes = [scene_object for scene_object in hair_objects if scene_object.type == "MESH" and scene_object.vertex_groups]

    for hair_mesh in hair_meshes:
        bind_mesh_to_armature(hair_mesh, armature)

    delete_objects([scene_object for scene_object in hair_objects if scene_object not in hair_meshes])

    eyes = find_eyes(body, eyes_object)
    back = -facing(eyes)

    recolor_skin(body)
    weld_seams(body)
    soften_muscles(body)
    cut_right_leg(body)
    build_pipe(armature, body, eyes, back)
    build_cap(armature, back)
    scale_head([scene_object for scene_object in bpy.data.objects if scene_object.type == "MESH"], armature)
    add_face_shapes(body, eyes_object, eyebrows)
    downscale_large_textures()
    bpy.ops.export_scene.gltf(filepath=str(OUTPUT_PATH), export_format="GLTF_SEPARATE", export_texture_dir="textures", export_animations=False, export_yup=True)

    return OUTPUT_PATH


if __name__ == "__main__":
    print(f"BUILT saci -> {build_saci()}")
