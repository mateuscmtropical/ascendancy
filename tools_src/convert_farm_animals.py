"""Convert the cow, pig and horse of the CC0 Quaternius "Farm Animals Animated" pack to glTF for the farm and the
street carriages (art/town/farm/animals/<animal>.gltf, plus horse_harness.gltf for the carriage horse).

The pack (python tools_src/fetch_assets.py animals -> tools/vendor/animals) ships FBX in centimetres with the
animals facing whichever way the author modelled them. For each animal this script:
  1. imports the first file whose name matches (glTF/GLB preferred, then FBX), anywhere under the pack folder;
  2. repaints the materials (richer colours, dark hooves, rosy pig snout) and smooths the shading;
  3. glues eyes (iris, pupil, shine) to the Head bone, sunk into the skin found by rays on the head mesh; the carriage horse also gets a padded collar, a
     draught saddle, a girth and the shaft rings (argolas) glued to the Neck and Torso bones;
  4. paints vertex colours: soft belly shade on everybody and the mud of the pig (legs, belly, snout);
  5. scales the top-level object so the rest pose stands ANIMALS[animal] metres tall and turns it so the head (Head
     bone) points to Godot +Z (Blender -Y);
  6. keeps the actions the game plays (ACTIONS) with the game names, drops the duplicated last key of every loop and
     removes translation of the root bone (the game moves the body); the pig, which ships without a walk, borrows the
     cow's walk (same skeleton, same bone names) retimed to PIG_WALK_SECONDS;
  7. exports glTF; the sidecar JSON keeps the height, the original action names and what was built.

Usage:
  blender -b --factory-startup -P tools_src/convert_farm_animals.py -- [cow pig horse] [--source <pack folder>]
"""

import json
import math
import sys
from itertools import product
from pathlib import Path

import bmesh
import bpy
from mathutils import Matrix, Vector
from mathutils import noise as mathutils_noise
from mathutils.bvhtree import BVHTree

PROJECT_DIR = Path(__file__).resolve().parent.parent
PACK_DIR = PROJECT_DIR / "tools" / "vendor" / "animals"
OUTPUT_DIR = PROJECT_DIR / "art" / "town" / "farm" / "animals"
ANIMALS = {"cow": 1.4, "pig": 0.7, "horse": 1.75}  # altura do modelo em repouso, metros
HARNESS_NAME = "horse_harness"  # variante do cavalo para a carroça
# último trecho do nome original ("Armature|Armature|Walk", minúsculo) -> nome no jogo, por bicho.
# O "Walk" da vaca e do cavalo no pacote fica de fora: as pernas só andam na primeira metade do ciclo e congelam
# na segunda (a cabeça e o rabo seguem), então o bicho desliza. O passo completo é o WalkSlow.
ACTIONS = {
    "cow": {"idle": "Idle", "walkslow": "WalkSlow"},
    "pig": {"idle": "Idle"},
    "horse": {"idle": "Idle", "walkslow": "WalkSlow", "run": "Run"},
}
PIG_WALK_DONOR_FOR = "pig"
PIG_WALK_DONOR = ("cow", "walkslow")  # o porco do pacote só tem Idle: pega o andar da vaca (mesmo esqueleto)
PIG_WALK_SECONDS = 1.2  # ciclo do andar do porco: ~0,55 m/s, perto da velocidade com que o jogo move o bicho
ROOT_BONE = "root"
SOURCE_SUFFIXES = (".gltf", ".glb", ".fbx")
HOOF_HEIGHT_SHARE = 0.046  # faces abaixo desta fração da altura são o casco
SUBDIVISIONS = {"pig": 2}  # cortes por aresta antes de pintar (o porco tem poucos vértices para a lama)
SMOOTH_ANGLE = math.radians(65)  # arestas mais agudas que isso ficam vincadas

COAT = {  # material original -> cor sRGB; os nomes do pacote não dizem nada, a função está no comentário
    "cow": {"White": "F6EEE2", "Black": "2B2733", "Pink": "EFA5A8"},  # pelagem clara, manchas, focinho
    "pig": {"Material.003": "F1AEA6", "Material": "7B4B3E"},  # pele, orelhas e bordas escuras
    "horse": {"Material.003": "8F4F2B", "Material.006": "2A1B15"},  # castanho, crina e focinho
}
HOOF_COLOR = {"cow": "2F2A2D", "pig": "3E2D2A", "horse": "2B2427"}
SNOUT_COLOR = "F08C9A"  # focinho do porco
SNOUT_SHARE = 0.17  # fração do comprimento da cabeça, a partir da ponta, que é focinho
EYE_COLORS = {"EyeIris": "3B2416", "EyePupil": "0B0A0D", "EyeShine": "F4F0E8"}  # olho de bicho: castanho escuro, sem branco à vista

# Olho: (y, z) do centro no espaço do esqueleto (cabeça para -Y), raio. O x vem da superfície da cabeça.
EYE_SPOTS = {"cow": (-4.38, 4.45, 0.135), "pig": (-4.42, 2.78, 0.115), "horse": (-4.15, 5.95, 0.13)}
EYE_RAY_START = 6.0  # de onde sai o raio que acha a pele do lado da cabeça (fora de qualquer malha)
EYE_BULGE = 0.3  # fração do raio que o olho salta para fora da pele
EYE_SHAPE = (0.42, 1.0, 0.72)  # raios do olho / raio: achatado para fora (não salta da cabeça), amendoado ao longo da cara
PUPIL_SHAPE = (0.16, 0.5, 0.26)  # pupila horizontal, como a de vaca, porco e cavalo

MUD_COLOR = (0.28, 0.17, 0.08)  # multiplica a pele do porco onde há lama
MUD_NOISE_SCALE = 0.55  # tamanho das manchas de lama, em unidades do esqueleto
MUD_REACH = (0.95, 0.42)  # alturas (fração do corpo) onde a lama some / é cheia
BELLY_SHADE = (0.64, 0.2, 0.74)  # altura (fração) sem sombra, altura de sombra cheia, brilho da sombra cheia

HARNESS_MATERIALS = {"Harness": "3B2417", "HarnessPad": "C58E5A", "HarnessBrass": "D2AA52"}
HARNESS_SADDLE_Y = -0.95  # posição do arreio ao longo do corpo (esqueleto, cabeça para -Y)
HARNESS_COLLAR_ALONG_NECK = 0.0  # onde a coelheira fica no osso do pescoço (0 = base)


def hex_to_linear(code: str) -> tuple:
    """sRGB hex like 'F6EEE2' -> linear RGBA (Blender and glTF store linear colours)."""
    channels = [int(code[index:index + 2], 16) / 255.0 for index in (0, 2, 4)]
    linear = [value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4 for value in channels]

    return (*linear, 1.0)


def find_source(pack_dir: Path, animal: str) -> Path:
    """First model file of the pack whose stem is the animal's name (case-insensitive), by preferred format."""
    candidates = [path for path in pack_dir.rglob("*") if path.suffix.lower() in SOURCE_SUFFIXES and path.stem.lower() == animal]
    ranked = sorted(candidates, key=lambda path: (SOURCE_SUFFIXES.index(path.suffix.lower()), len(path.parts)))

    if not ranked:
        raise FileNotFoundError(f"{animal}: nenhum arquivo {SOURCE_SUFFIXES} com esse nome em {pack_dir}")

    return ranked[0]


def import_source(path: Path) -> None:
    importers = {".gltf": bpy.ops.import_scene.gltf, ".glb": bpy.ops.import_scene.gltf, ".fbx": bpy.ops.import_scene.fbx}

    importers[path.suffix.lower()](filepath=str(path))


def scene_object(object_type: str) -> bpy.types.Object:
    """The only object of this type in the scene (the pack has one armature and one mesh per animal)."""
    return next(candidate for candidate in bpy.context.scene.objects if candidate.type == object_type)


def mesh_world_vertices() -> list:
    depsgraph = bpy.context.evaluated_depsgraph_get()
    vertices = []

    for mesh_object in (candidate for candidate in bpy.context.scene.objects if candidate.type == "MESH"):
        evaluated = mesh_object.evaluated_get(depsgraph)
        vertices += [evaluated.matrix_world @ vertex.co for vertex in evaluated.data.vertices]

    return vertices


def heading_turn(armature: bpy.types.Object) -> float:
    """Yaw (radians, around Blender Z) that brings the head to -Y: the head is where the Head bone sits relative to
    the Hips bone (the tallest vertices are no hint: the pig's back is higher than its head)."""
    bones = armature.data.bones
    head_direction = armature.matrix_world @ bones["Head"].head_local - armature.matrix_world @ bones["Hips"].head_local

    return math.atan2(-1.0, 0.0) - math.atan2(head_direction.y, head_direction.x)


def normalize(animal: str) -> float:
    """Hang the imported objects under a new root that scales and turns them so the animal stands ANIMALS[animal]
    tall with its head to Godot +Z. FBX actions animate the armature object itself, so its own transform cannot be
    changed: the exporter would sample the action over it."""
    roots = [candidate for candidate in bpy.context.scene.objects if candidate.parent is None]
    vertices = mesh_world_vertices()
    height = max(vertex.z for vertex in vertices) - min(vertex.z for vertex in vertices)
    factor = ANIMALS[animal] / height
    animal_root = bpy.data.objects.new(animal.title(), None)

    bpy.context.scene.collection.objects.link(animal_root)

    for root in roots:
        root.parent = animal_root

    animal_root.matrix_world = Matrix.Rotation(heading_turn(scene_object("ARMATURE")), 4, "Z") @ Matrix.Scale(factor, 4)
    bpy.context.view_layer.update()
    animal_root.location.z -= min(vertex.z for vertex in mesh_world_vertices())

    return factor


# ---------- animations ----------

def action_curves(action: bpy.types.Action) -> list:
    """F-curves of the action's only slot (layered actions of Blender 4.4+)."""
    return list(action.layers[0].strips[0].channelbags[0].fcurves)


def graft_walk(animal: str) -> bpy.types.Action:
    """The donor's walk as an action of this scene (same bone names drive the pig's skeleton); the donor's objects
    are deleted again so only the action stays."""
    donor, action_part = PIG_WALK_DONOR
    donor_path = find_source(PACK_DIR, donor)
    objects_before = set(bpy.data.objects)

    import_source(donor_path)

    walk = next(action for action in bpy.data.actions if action.name.rsplit("|", 1)[-1].lower() == action_part)
    walk.use_fake_user = True

    for donor_object in set(bpy.data.objects) - objects_before:
        bpy.data.objects.remove(donor_object)

    return walk


def drop_unknown_bones(action: bpy.types.Action, armature: bpy.types.Object) -> None:
    """Some actions drive bones this skeleton lacks (the pig has no tail bones): their curves go."""
    channel_bag = action.layers[0].strips[0].channelbags[0]

    for curve in action_curves(action):
        bone_name = curve.data_path.split('"')[1] if curve.data_path.startswith("pose.bones[") else None

        if bone_name is not None and bone_name not in armature.data.bones:
            channel_bag.fcurves.remove(curve)


def retime(action: bpy.types.Action, seconds: float) -> None:
    """Stretch the keys so the loop lasts `seconds` at the scene frame rate (key handles follow)."""
    start, end = action.frame_range
    factor = seconds * bpy.context.scene.render.fps / (end - start)
    points = [point for curve in action_curves(action) for point in curve.keyframe_points]

    for point in points:
        point.co.x = start + (point.co.x - start) * factor
        point.handle_left.x = start + (point.handle_left.x - start) * factor
        point.handle_right.x = start + (point.handle_right.x - start) * factor

    action.frame_range = (start, start + (end - start) * factor)


def drop_loop_duplicate(action: bpy.types.Action) -> None:
    """Pack loops repeat the first pose on the last frame, which holds the pose for one extra frame at every
    wrap-around: the loop ends one frame earlier."""
    start, end = action.frame_range
    action.use_frame_range = True
    action.frame_start = start
    action.frame_end = end - 1.0


def flatten_root_motion(action: bpy.types.Action) -> float:
    """Remove translation of the root bone (the game moves the body). Returns how far it travelled in the pack."""
    root_path = f'pose.bones["{ROOT_BONE}"].location'
    root_curves = [curve for curve in action_curves(action) if curve.data_path == root_path]
    travelled = max((max(point.co.y for point in curve.keyframe_points) - min(point.co.y for point in curve.keyframe_points) for curve in root_curves), default=0.0)

    for point in (point for curve in root_curves for point in curve.keyframe_points):
        point.co.y = 0.0
        point.handle_left.y = 0.0
        point.handle_right.y = 0.0

    return travelled


def finish_actions(animal: str, donated_walk: bpy.types.Action | None) -> tuple:
    """Game name -> original action name for the kept actions, and root travel of the pack per action."""
    kept = {}
    root_travel = {}
    names = ACTIONS[animal]
    armature = scene_object("ARMATURE")

    if donated_walk is not None:
        armature.animation_data_create()
        armature.animation_data.action = donated_walk
        armature.animation_data.action_slot = donated_walk.slots[0]
        retime(donated_walk, PIG_WALK_SECONDS)
        kept["Walk"] = f"{PIG_WALK_DONOR[0]}:{donated_walk.name}"
        donated_walk.name = "Walk"

    for action in list(bpy.data.actions):
        if action.name == "Walk" and donated_walk is not None:
            root_travel["Walk"] = flatten_root_motion(action)
            drop_loop_duplicate(action)
            drop_unknown_bones(action, armature)
            continue

        game_name = names.get(action.name.rsplit("|", 1)[-1].lower())

        if game_name is None:
            bpy.data.actions.remove(action)
            continue

        kept[game_name] = action.name
        action.name = game_name
        root_travel[game_name] = flatten_root_motion(action)
        drop_loop_duplicate(action)
        drop_unknown_bones(action, armature)

    return kept, root_travel


# ---------- materials ----------

def make_materials_opaque() -> None:
    """The pack's FBX materials import with alpha 0, which glTF exports as MASK: the animal would be invisible."""
    for material in bpy.data.materials:
        shader = material.node_tree.nodes.get("Principled BSDF") if material.use_nodes else None

        if shader is None:
            continue

        alpha_input = shader.inputs["Alpha"]

        for link in list(alpha_input.links):
            material.node_tree.links.remove(link)

        alpha_input.default_value = 1.0


def new_material(name: str, code: str, roughness: float = 0.85, metallic: float = 0.0) -> bpy.types.Material:
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    shader = material.node_tree.nodes["Principled BSDF"]
    shader.inputs["Base Color"].default_value = hex_to_linear(code)
    shader.inputs["Roughness"].default_value = roughness
    shader.inputs["Metallic"].default_value = metallic

    return material


def recolor_materials(animal: str) -> None:
    for name, code in COAT[animal].items():
        shader = bpy.data.materials[name].node_tree.nodes["Principled BSDF"]
        shader.inputs["Base Color"].default_value = hex_to_linear(code)
        shader.inputs["Roughness"].default_value = 0.88


def slot_for(mesh_object: bpy.types.Object, material: bpy.types.Material) -> int:
    """Index of the material in the mesh, adding a slot if the mesh does not have it yet."""
    if material.name not in mesh_object.data.materials:
        mesh_object.data.materials.append(material)

    return list(mesh_object.data.materials).index(material)


def vertex_height(mesh_object: bpy.types.Object) -> tuple:
    heights = [vertex.co.z for vertex in mesh_object.data.vertices]

    return min(heights), max(heights)


def head_vertices(mesh_object: bpy.types.Object) -> list:
    """Vertices that belong (weight > 0.5) to the Head bone."""
    group_index = mesh_object.vertex_groups["Head"].index

    return [vertex for vertex in mesh_object.data.vertices if any(entry.group == group_index and entry.weight > 0.5 for entry in vertex.groups)]


def subdivide(mesh_object: bpy.types.Object, cuts: int) -> None:
    """Split every edge in `cuts` + 1 pieces without moving anything: more vertices to carry mud and snout edges.
    Skin weights and materials are interpolated by bmesh."""
    builder = bmesh.new()

    builder.from_mesh(mesh_object.data)
    bmesh.ops.subdivide_edges(builder, edges=builder.edges[:], cuts=cuts, use_grid_fill=True)
    builder.to_mesh(mesh_object.data)
    builder.free()


def paint_faces(animal: str, mesh_object: bpy.types.Object) -> None:
    """Dark hooves on every animal, rosy snout on the pig."""
    low, high = vertex_height(mesh_object)
    hoof_top = low + (high - low) * HOOF_HEIGHT_SHARE
    hoof_slot = slot_for(mesh_object, new_material("Hoof", HOOF_COLOR[animal], roughness=0.6))
    polygons = mesh_object.data.polygons

    for polygon in (candidate for candidate in polygons if candidate.center.z < hoof_top):
        polygon.material_index = hoof_slot

    if animal == "pig":
        paint_snout(mesh_object, hoof_top)

    put_material_first(mesh_object, hoof_slot)


def paint_snout(mesh_object: bpy.types.Object, hoof_top: float) -> None:
    head = head_vertices(mesh_object)
    nose_y = min(vertex.co.y for vertex in head)
    head_length = max(vertex.co.y for vertex in head) - nose_y
    snout_slot = slot_for(mesh_object, new_material("Snout", SNOUT_COLOR, roughness=0.7))

    for polygon in (candidate for candidate in mesh_object.data.polygons if candidate.center.y < nose_y + head_length * SNOUT_SHARE and candidate.center.z > hoof_top):
        polygon.material_index = snout_slot


def put_material_first(mesh_object: bpy.types.Object, slot: int) -> None:
    """Godot's glTF importer forgets the vertex-colour flag on the first primitive of a mesh, so the slot that never
    needs vertex colours (the hooves) goes first and the skin keeps its belly shade and mud."""
    mesh = mesh_object.data
    materials = list(mesh.materials)
    order = [slot] + [index for index in range(len(materials)) if index != slot]
    new_index = {old: new for new, old in enumerate(order)}
    polygon_slots = [new_index[polygon.material_index] for polygon in mesh.polygons]

    mesh.materials.clear()

    for old_index in order:
        mesh.materials.append(materials[old_index])

    mesh.polygons.foreach_set("material_index", polygon_slots)


def smooth_shading(mesh_object: bpy.types.Object) -> None:
    mesh_object.data.shade_smooth()
    mesh_object.data.set_sharp_from_angle(angle=SMOOTH_ANGLE)


# ---------- parts glued to bones ----------

def tube_ring(center: Vector, axis_u: Vector, axis_v: Vector, radius_u: float, radius_v: float, tube: tuple, segments: tuple = (28, 8)) -> bmesh.types.BMesh:
    """Closed tube following the ellipse centre + u*cos + v*sin; `tube` = (radial, axial) half-thickness."""
    ring_segments, tube_segments = segments
    axial = axis_u.cross(axis_v).normalized()
    builder = bmesh.new()
    corners = {}

    for ring_index, tube_index in product(range(ring_segments), range(tube_segments)):
        ring_angle = 2.0 * math.pi * ring_index / ring_segments
        tube_angle = 2.0 * math.pi * tube_index / tube_segments
        path_point = center + axis_u * radius_u * math.cos(ring_angle) + axis_v * radius_v * math.sin(ring_angle)
        outward = (axis_u * math.cos(ring_angle) / radius_u + axis_v * math.sin(ring_angle) / radius_v).normalized()
        corners[(ring_index, tube_index)] = builder.verts.new(path_point + outward * tube[0] * math.cos(tube_angle) + axial * tube[1] * math.sin(tube_angle))

    for ring_index, tube_index in product(range(ring_segments), range(tube_segments)):
        next_ring = (ring_index + 1) % ring_segments
        next_tube = (tube_index + 1) % tube_segments
        builder.faces.new((corners[(ring_index, tube_index)], corners[(next_ring, tube_index)], corners[(next_ring, next_tube)], corners[(ring_index, next_tube)]))

    return builder


def ball(center: Vector, radii: tuple, segments: tuple = (12, 8), rotation: Matrix = Matrix.Identity(4)) -> bmesh.types.BMesh:
    builder = bmesh.new()
    scale = Matrix.Diagonal(Vector((*radii, 1.0)))

    bmesh.ops.create_uvsphere(builder, u_segments=segments[0], v_segments=segments[1], radius=1.0, matrix=Matrix.Translation(center) @ rotation @ scale)

    return builder


def block(center: Vector, half_sizes: tuple, rotation: Matrix = Matrix.Identity(4)) -> bmesh.types.BMesh:
    builder = bmesh.new()
    scale = Matrix.Diagonal(Vector((*half_sizes, 1.0)))

    bmesh.ops.create_cube(builder, size=2.0, matrix=Matrix.Translation(center) @ rotation @ scale)

    return builder


def make_part(name: str, builder: bmesh.types.BMesh, bone: str, material: bpy.types.Material, armature: bpy.types.Object) -> bpy.types.Object:
    """Mesh object skinned 100% to `bone`, ready to be joined into the animal's mesh."""
    mesh = bpy.data.meshes.new(name)
    builder.to_mesh(mesh)
    builder.free()
    part = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(part)
    part.parent = armature
    mesh.materials.append(material)
    part.vertex_groups.new(name=bone).add(list(range(len(mesh.vertices))), 1.0, "REPLACE")

    return part


def join_parts(body: bpy.types.Object, parts: list) -> None:
    for candidate in bpy.context.view_layer.objects:
        candidate.select_set(False)

    for part in parts:
        part.select_set(True)

    body.select_set(True)
    bpy.context.view_layer.objects.active = body
    bpy.ops.object.join()


def head_skin(surface: BVHTree, side: float, y: float, z: float) -> tuple:
    """Point and outward normal of the head surface on `side` where the line of sight through (y, z) meets it. The
    heads are a few dozen flat panels, so the vertices near the eye (cheek, ear) say nothing about where the skin
    is: a ray finds it."""
    origin = Vector((side * EYE_RAY_START, y, z))
    direction = Vector((-side, 0.0, 0.0))
    point, normal, _index, _distance = surface.ray_cast(origin, direction)

    if point is None:
        raise ValueError(f"nenhuma superfície da cabeça em y={y}, z={z}: ajuste EYE_SPOTS")

    return point, normal if normal.dot(direction) < 0.0 else -normal


def eye_frame(normal: Vector) -> Matrix:
    """Rotation that turns the eye's X (its flat axis) along the skin normal, keeping its Z as close to up as the
    slope allows: the eye lies on the panel instead of standing off one edge of it."""
    up = Vector((0.0, 0.0, 1.0))
    vertical = (up - normal * up.dot(normal)).normalized()
    along = vertical.cross(normal)

    return Matrix((normal, along, vertical)).transposed().to_4x4()


def eye_parts(animal: str, body: bpy.types.Object, armature: bpy.types.Object) -> list:
    """Flattened almond eye (dark iris, horizontal pupil, small shine) set into each side of the head, skinned to
    the Head bone. Round white balls read as cartoon googly eyes stuck on the head."""
    spot_y, spot_z, radius = EYE_SPOTS[animal]
    mesh = body.data
    surface = BVHTree.FromPolygons([tuple(vertex.co) for vertex in mesh.vertices], [tuple(polygon.vertices) for polygon in mesh.polygons])
    materials = {name: new_material(name, code, roughness=0.25) for name, code in EYE_COLORS.items()}
    parts = []

    for side in (-1.0, 1.0):
        skin, normal = head_skin(surface, side, spot_y, spot_z)
        frame = eye_frame(normal)
        center = skin - normal * radius * (EYE_SHAPE[0] - EYE_BULGE)
        gaze = (normal * 0.8 + Vector((0.0, -0.55, 0.0))).normalized()
        pupil_center = center + normal * radius * (EYE_SHAPE[0] - PUPIL_SHAPE[0] * 0.6) + gaze * radius * 0.08
        shine_center = center + normal * radius * EYE_SHAPE[0] * 0.92 + Vector((0.0, -0.25, 0.35)) * radius
        label = "L" if side < 0 else "R"

        for suffix, builder, material_name in (
            ("ball", ball(center, tuple(radius * share for share in EYE_SHAPE), rotation=frame), "EyeIris"),
            ("pupil", ball(pupil_center, tuple(radius * share for share in PUPIL_SHAPE), rotation=frame), "EyePupil"),
            ("shine", ball(shine_center, (radius * 0.1,) * 3, (8, 6)), "EyeShine"),
        ):
            parts.append(make_part(f"Eye{label}_{suffix}", builder, "Head", materials[material_name], armature))

    return parts


def trunk_slice(body: bpy.types.Object, y: float, reach: float) -> list:
    """Coordinates of the trunk vertices (Body/Torso/Back/Hips/Shoulders bones, weight > 0.5) near plane Y=y."""
    trunk_indices = {body.vertex_groups[name].index for name in ("Body", "Torso", "Back", "Hips", "Shoulders") if name in body.vertex_groups}

    return [
        vertex.co.copy()
        for vertex in body.data.vertices
        if abs(vertex.co.y - y) < reach and any(entry.group in trunk_indices and entry.weight > 0.5 for entry in vertex.groups)
    ]


def harness_parts(body: bpy.types.Object, armature: bpy.types.Object, bones: dict) -> tuple:
    """Padded collar on the neck, draught saddle on the back, girth under the barrel and the shaft rings on both
    flanks. Returns the parts and the ring centres (skeleton space)."""
    leather = new_material("Harness", HARNESS_MATERIALS["Harness"], roughness=0.55)
    pad = new_material("HarnessPad", HARNESS_MATERIALS["HarnessPad"], roughness=0.8)
    brass = new_material("HarnessBrass", HARNESS_MATERIALS["HarnessBrass"], roughness=0.3, metallic=0.6)
    neck_base, neck_tip = bones["Neck"]
    neck_axis = (neck_tip - neck_base).normalized()
    collar_center = neck_base + (neck_tip - neck_base) * HARNESS_COLLAR_ALONG_NECK
    neck_points = [
        vertex.co.copy()
        for vertex in body.data.vertices
        if abs((vertex.co - collar_center).dot(neck_axis)) < 0.3 and (vertex.co - collar_center).length < 2.0 and vertex.co.z > collar_center.z - 1.3
    ]
    collar_side = Vector((1.0, 0.0, 0.0))
    collar_up = neck_axis.cross(collar_side).normalized()
    side_reach = max(abs(point.x) for point in neck_points)
    up_reach = max(abs((point - collar_center).dot(collar_up)) for point in neck_points)
    collar_center = collar_center + collar_up * (max((point - collar_center).dot(collar_up) for point in neck_points) + min((point - collar_center).dot(collar_up) for point in neck_points)) / 2.0
    trunk = trunk_slice(body, HARNESS_SADDLE_Y, 0.5)
    back_top = max(point.z for point in trunk)
    belly = min(point.z for point in trunk)
    flank = max(point.x for point in trunk)
    barrel_center = Vector((0.0, HARNESS_SADDLE_Y, (back_top + belly) / 2.0))
    saddle_center = Vector((0.0, HARNESS_SADDLE_Y, back_top + 0.1))
    ring_z = back_top - 0.34
    ring_x = flank * 1.02 + 0.24
    ring_radius = 0.3
    ring_centers = [Vector((side * ring_x, HARNESS_SADDLE_Y, ring_z)) for side in (-1.0, 1.0)]
    parts = [
        make_part("HarnessCollar", tube_ring(collar_center, collar_side, collar_up, side_reach * 1.04, up_reach * 1.0, (0.28, 0.26)), "Neck", pad, armature),
        make_part("HarnessCollarBand", tube_ring(collar_center + neck_axis * 0.02, collar_side, collar_up, side_reach * 1.04, up_reach * 1.0, (0.31, 0.06), (28, 6)), "Neck", leather, armature),
        make_part("HarnessHame", ball(collar_center + collar_up * (up_reach * 1.0 + 0.33), (0.12, 0.12, 0.2)), "Neck", brass, armature),
        make_part("HarnessSaddlePad", ball(saddle_center, (flank * 1.0, 1.15, 0.3), (14, 8)), "Torso", pad, armature),
        make_part("HarnessSaddle", ball(saddle_center + Vector((0.0, 0.0, 0.2)), (flank * 0.6, 0.8, 0.26), (14, 8)), "Torso", leather, armature),
        make_part("HarnessGirth", tube_ring(barrel_center, Vector((1.0, 0.0, 0.0)), Vector((0.0, 0.0, 1.0)), flank * 1.04, (back_top - belly) / 2.0 * 1.04, (0.09, 0.2), (32, 6)), "Torso", leather, armature),
    ]

    for side, ring_center in zip((-1.0, 1.0), ring_centers):
        label = "L" if side < 0 else "R"
        strap_top = Vector((side * flank * 0.78, HARNESS_SADDLE_Y, back_top))
        strap_center = (strap_top + ring_center) / 2.0
        strap_half_length = (strap_top - ring_center).length / 2.0
        strap_axis = (strap_top - ring_center).normalized()
        strap_rotation = strap_axis.to_track_quat("Z", "Y").to_matrix().to_4x4()
        parts.append(make_part(f"HarnessStrap{label}", block(strap_center, (0.07, 0.19, strap_half_length), strap_rotation), "Torso", leather, armature))
        parts.append(make_part(f"HarnessRing{label}", tube_ring(ring_center, Vector((0.0, 1.0, 0.0)), Vector((0.0, 0.0, 1.0)), ring_radius, ring_radius, (0.07, 0.07), (20, 6)), "Torso", brass, armature))

    return parts, ring_centers


# ---------- vertex colours ----------

def smoothstep(edge_start: float, edge_end: float, value: float) -> float:
    amount = min(1.0, max(0.0, (value - edge_start) / (edge_end - edge_start)))

    return amount * amount * (3.0 - 2.0 * amount)


def mud_amount(animal: str, vertex: Vector, ground: float, height: float, nose_y: float, head_length: float) -> float:
    """0..1: how muddy a vertex is. Legs and belly are the muddiest, the snout is smeared, patches vary by noise."""
    if animal != "pig":
        return 0.0

    near_ground = smoothstep(MUD_REACH[0], MUD_REACH[1], (vertex.z - ground) / height)
    snout = smoothstep(0.7, 0.0, (vertex.y - nose_y) / (head_length * 0.5))
    patches = 0.5 + 0.5 * mathutils_noise.noise(vertex / MUD_NOISE_SCALE)
    splashes = smoothstep(0.55, 0.78, 0.5 + 0.5 * mathutils_noise.noise(vertex / MUD_NOISE_SCALE * 2.3 + Vector((9.0, 4.0, 1.0))))

    raw = max(near_ground * (0.3 + 1.0 * patches), snout * 0.5 * (0.6 + 0.6 * patches), splashes * smoothstep(0.95, 0.5, (vertex.z - ground) / height))

    return smoothstep(0.3, 0.7, raw)  # bordas mais nítidas: mancha de lama, não degradê


def paint_vertex_colors(animal: str, body: bpy.types.Object, original_vertices: int) -> None:
    """COLOR_0 (Godot multiplies it into the albedo): belly shade for everybody, mud for the pig. Vertices added
    after the pack's own (eyes, harness) stay white."""
    mesh = body.data
    low, high = vertex_height(body)
    height = high - low
    nose_y, head_length = 0.0, 1.0

    if animal == "pig":
        head = head_vertices(body)
        nose_y = min(vertex.co.y for vertex in head)
        head_length = max(vertex.co.y for vertex in head) - nose_y

    if "Col" in mesh.color_attributes:
        mesh.color_attributes.remove(mesh.color_attributes["Col"])

    attribute = mesh.color_attributes.new("Col", "FLOAT_COLOR", "POINT")
    colors = []

    for vertex in mesh.vertices:
        shade_start, shade_end, shade_floor = BELLY_SHADE
        shade = 1.0 - (1.0 - shade_floor) * smoothstep(shade_start, shade_end, (vertex.co.z - low) / height)
        mud = mud_amount(animal, vertex.co, low, height, nose_y, head_length)
        tint = [shade * (1.0 - mud * (1.0 - channel)) for channel in MUD_COLOR]

        if vertex.index >= original_vertices:
            tint = [1.0, 1.0, 1.0]

        colors += [tint[0] * 1.0, tint[1] * 0.985, tint[2], 1.0]

    attribute.data.foreach_set("color", colors)
    mesh.color_attributes.active_color = attribute


# ---------- conversion ----------

def bone_ends(armature: bpy.types.Object, names: tuple) -> dict:
    return {name: (armature.data.bones[name].head_local.copy(), armature.data.bones[name].tail_local.copy()) for name in names}


def sidecar_measurements(animal: str, factor: float, ring_centers: list, root_travel: dict) -> dict:
    """Numbers the game side needs: stride per action and, for the harness, ring centres in Godot axes (x, y, z+ front)."""
    measurements = {"root_travel_in_pack": {name: round(value, 4) for name, value in root_travel.items()}}

    if ring_centers:
        armature = scene_object("ARMATURE")
        root_matrix = armature.parent.matrix_world
        godot = [root_matrix @ center for center in ring_centers]
        measurements["harness_rings"] = [[round(point.x, 3), round(point.z, 3), round(-point.y, 3)] for point in godot]

    return measurements


def convert(animal: str, pack_dir: Path, harness: bool = False) -> dict:
    source = find_source(pack_dir, animal)
    output_name = HARNESS_NAME if harness else animal
    output_path = OUTPUT_DIR / f"{output_name}.gltf"

    bpy.ops.wm.read_factory_settings(use_empty=True)
    donated_walk = graft_walk(animal) if animal == PIG_WALK_DONOR_FOR else None
    import_source(source)
    make_materials_opaque()

    armature = scene_object("ARMATURE")
    body = scene_object("MESH")
    original_vertices = len(body.data.vertices)

    recolor_materials(animal)
    subdivide(body, SUBDIVISIONS.get(animal, 0)) if animal in SUBDIVISIONS else None
    paint_faces(animal, body)
    parts = eye_parts(animal, body, armature)
    ring_centers = []

    if harness:
        harness_pieces, ring_centers = harness_parts(body, armature, bone_ends(armature, ("Neck", "Torso")))
        parts += harness_pieces

    join_parts(body, parts)
    smooth_shading(body)
    paint_vertex_colors(animal, body, original_vertices)

    factor = normalize(animal)
    actions, root_travel = finish_actions(animal, donated_walk)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    bpy.ops.export_scene.gltf(
        filepath=str(output_path),
        export_format="GLTF_SEPARATE",
        export_yup=True,
        export_animation_mode="ACTIONS",
        export_force_sampling=True,
        export_vertex_color="ACTIVE",
        export_active_vertex_color_when_no_material=True,
    )

    sidecar = {"source": source.name, "height": ANIMALS[animal], "scale": round(factor, 5), "animations": actions}
    sidecar.update(sidecar_measurements(animal, factor, ring_centers, root_travel))
    output_path.with_suffix(".json").write_text(json.dumps(sidecar, indent=1), encoding="utf-8", newline="\n")

    return sidecar


if __name__ == "__main__":
    arguments = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    source_dir = Path(arguments[arguments.index("--source") + 1]) if "--source" in arguments else PACK_DIR
    requested = [argument for argument in arguments if argument in ANIMALS]

    for animal_name in requested or list(ANIMALS):
        variants = (False, True) if animal_name == "horse" else (False,)

        for with_harness in variants:
            result = convert(animal_name, source_dir, with_harness)
            print(f"BUILT {HARNESS_NAME if with_harness else animal_name}: {result}")

            if "Idle" not in result["animations"] or not {"Walk", "WalkSlow"} & set(result["animations"]):
                print(f"AVISO {animal_name}: faltou Idle ou passo; animações do pacote: {result['animations']}")
