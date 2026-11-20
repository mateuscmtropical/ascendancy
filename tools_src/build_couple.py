"""The couple on the west fountain bench: a young man and a young woman in everyday clothes, sitting and chatting.

Built from the same CC0 Quaternius pieces as the town characters (65-bone rig, UAL clips, face shapes):

- couple_him: the peasant outfit recoloured into a black short-sleeved shirt, dark trousers and dark shoes; the
  Buzzed hair with a fuller, curly top over the short sides; the beard trimmed down to a thin goatee and moustache;
  the skin of head and arms tinted a light brown.
- couple_her: the peasant outfit with the blouse kept white, the vest and corset recoloured into a sleeveless
  light-wash denim vest, dark trousers and shoes; the sleeves cut at the elbow over bare forearms taken from the base
  body; the Long hair grown below the shoulders with waves at the ends, draped over the body; the skin lifted lighter.

Each recolour works on a copy of the outfit atlas, inside the UV footprint of the one garment it changes, so the
browns of vest, belt and boots that share the atlas never bleed into each other. Hair colour is left to the scene
(features/player/character_model.gd tints every MI_Hair material).

Usage:
  blender -b --factory-startup -P tools_src/build_couple.py -- [couple_him|couple_her ...]
"""

import math
import sys
from pathlib import Path

import bmesh
import bpy
import numpy
from mathutils import Vector, noise
from mathutils.bvhtree import BVHTree

sys.path.insert(0, str(Path(__file__).resolve().parent))

from build_characters import BASE_BODY_DIR, HAIR_DIR, HEAD_MESH_NAME, OUTFIT_DIR, OUTPUT_DIR, attach_base_head, attach_hair, bind_mesh_to_armature, delete_objects, downscale_large_textures, find_armature, import_gltf  # noqa: E402
from face_shapes import add_face_shapes  # noqa: E402

FOREARM_PREFIXES = ("lowerarm", "hand", "thumb", "index", "middle", "ring", "pinky")
SLEEVE_CUT_WEIGHT = 0.5  # sleeve vertices carried more than this by the forearm and hand go
FOREARM_KEEP_WEIGHT = 0.3  # bare-skin vertices kept from the base body: a little above where the sleeve ends
MASK_GROW_PIXELS = 3  # the UV footprint grows this much so the seams take the new colour too
HAIR_CLEARANCE = 0.012  # metres the lengthened hair keeps off the body
BEARD_THICKNESS = 0.3
CURL_SCALE = 70.0  # curls of about 1.5 cm on top of his head  # share of its height over the skin the trimmed beard keeps
# Garment colours (sRGB), applied over the luminance of the original cloth so its folds and seams stay.
BLACK_SHIRT = (0.075, 0.075, 0.085)
DARK_TROUSERS = (0.12, 0.13, 0.16)
DARK_SHOES = (0.11, 0.095, 0.085)
WHITE_BLOUSE = (0.93, 0.92, 0.89)
LIGHT_DENIM = (0.50, 0.62, 0.76)
VEST_MIN_SATURATION = 0.22  # on her body piece, the leather and corset are saturated or dark; the blouse is neither
VEST_MAX_VALUE = 0.42

COUPLE = {
    "couple_him": {
        "outfit": "Male_Peasant",
        "base_body": "Superhero_Male_FullBody",
        "hair": ["Hair_Buzzed", "Hair_Beard"],
        "skin": ("multiply", (0.92, 0.80, 0.70)),
        "garments": {"Body": ("all", BLACK_SHIRT), "Arms": ("all", BLACK_SHIRT), "Legs": ("all", DARK_TROUSERS), "Feet": ("all", DARK_SHOES)},
    },
    "couple_her": {
        "outfit": "Female_Peasant",
        "base_body": "Superhero_Female_FullBody",
        "hair": ["Hair_Long"],
        "skin": ("lift", (1.0, 0.95, 0.93)),
        "garments": {"Body": ("vest", LIGHT_DENIM), "Arms": ("all", WHITE_BLOUSE), "Legs": ("all", DARK_TROUSERS), "Feet": ("all", DARK_SHOES)},
    },
}


def weight_in(vertex, group_indices: set) -> float:
    return sum(group.weight for group in vertex.groups if group.group in group_indices)


def groups_named(mesh_object, prefixes: tuple) -> set:
    return {group.index for group in mesh_object.vertex_groups if group.name.startswith(prefixes)}


def delete_vertices(mesh_object, keep) -> None:
    mesh_bmesh = bmesh.new()

    mesh_bmesh.from_mesh(mesh_object.data)
    mesh_bmesh.verts.ensure_lookup_table()
    doomed = [mesh_bmesh.verts[vertex.index] for vertex in mesh_object.data.vertices if not keep(vertex)]
    bmesh.ops.delete(mesh_bmesh, geom=doomed, context="VERTS")
    mesh_bmesh.to_mesh(mesh_object.data)
    mesh_bmesh.free()


def outfit_piece(part: str):
    return next(scene_object for scene_object in bpy.data.objects if scene_object.type == "MESH" and scene_object.name.endswith(f"_{part}"))


# ---------- recolour ----------

def base_color_image(material):
    return next(node.image for node in material.node_tree.nodes if node.type == "TEX_IMAGE" and node.image and "Normal" not in node.image.name and "ORM" not in node.image.name and "Roughness" not in node.image.name)


def set_base_color_image(material, image) -> None:
    texture = next(node for node in material.node_tree.nodes if node.type == "TEX_IMAGE" and node.image and base_color_image(material) == node.image)
    texture.image = image


def image_pixels(image) -> numpy.ndarray:
    return numpy.array(image.pixels[:], dtype=numpy.float32).reshape(image.size[1], image.size[0], 4)


def store_pixels(image, pixels: numpy.ndarray) -> None:
    image.pixels[:] = pixels.clip(0.0, 1.0).ravel()
    image.pack()


def copy_image(source, name: str):
    image = source.copy()

    if tuple(image.size) != tuple(source.size):  # the copy reloads the file, undoing the downscale
        image.scale(*source.size)

    image.name = name
    image.filepath_raw = f"//{name}.png"

    return image


def uv_footprint(mesh_object, material_index: int, width: int, height: int) -> numpy.ndarray:
    """Pixels of the atlas the mesh's faces with this material cover (rows from the bottom, as Blender stores them)."""
    mesh = mesh_object.data
    uv_data = mesh.uv_layers.active.data
    mask = numpy.zeros((height, width), dtype=bool)

    mesh.calc_loop_triangles()

    for triangle in mesh.loop_triangles:
        if triangle.material_index != material_index:
            continue

        corners = numpy.array([uv_data[loop].uv[:] for loop in triangle.loops]) * (width, height)
        low = numpy.floor(corners.min(axis=0)).astype(int).clip(0, (width - 1, height - 1))
        high = numpy.ceil(corners.max(axis=0)).astype(int).clip(0, (width - 1, height - 1))
        xs, ys = numpy.meshgrid(numpy.arange(low[0], high[0] + 1) + 0.5, numpy.arange(low[1], high[1] + 1) + 0.5)
        (ax, ay), (bx, by), (cx, cy) = corners
        area = (bx - ax) * (cy - ay) - (cx - ax) * (by - ay)

        if abs(area) < 1e-9:
            continue

        first = ((bx - xs) * (cy - ys) - (cx - xs) * (by - ys)) / area
        second = ((cx - xs) * (ay - ys) - (ax - xs) * (cy - ys)) / area
        inside = (first >= -0.02) & (second >= -0.02) & (first + second <= 1.02)
        mask[low[1]:high[1] + 1, low[0]:high[0] + 1] |= inside

    for _ in range(MASK_GROW_PIXELS):
        grown = mask.copy()
        grown[1:, :] |= mask[:-1, :]
        grown[:-1, :] |= mask[1:, :]
        grown[:, 1:] |= mask[:, :-1]
        grown[:, :-1] |= mask[:, 1:]
        mask = grown

    return mask


def dye(pixels: numpy.ndarray, mask: numpy.ndarray, color: tuple) -> None:
    """Paints the masked cloth in color, keeping its light and shade relative to its own average."""
    luminance = pixels[..., :3].mean(axis=2)
    average = max(float(numpy.median(luminance[mask])), 1e-3)
    shade = (0.55 + 0.45 * luminance / average)[..., None]

    pixels[mask, :3] = (numpy.array(color) * shade)[mask]


def vest_pixels(pixels: numpy.ndarray) -> numpy.ndarray:
    value = pixels[..., :3].max(axis=2)
    saturation = (value - pixels[..., :3].min(axis=2)) / numpy.maximum(value, 1e-4)

    return (saturation > VEST_MIN_SATURATION) | (value < VEST_MAX_VALUE)


def recolor_garments(garments: dict, prefix: str) -> None:
    """One recoloured copy of every outfit atlas, each garment dyed inside its own UV footprint."""
    pieces = {part: outfit_piece(part) for part in garments}
    sources = {}

    for part, piece in pieces.items():
        for index, material in enumerate(piece.data.materials):
            if material.name.startswith("MI_Peasant"):
                sources.setdefault(base_color_image(material).name, []).append((part, piece, index, material))

    for number, (image_name, users) in enumerate(sources.items()):
        source = bpy.data.images[image_name]
        image = copy_image(source, f"T_{prefix}_Outfit{number + 1}")
        width, height = image.size
        pixels = image_pixels(source)
        original = pixels.copy()

        for part, piece, index, material in users:
            mode, color = garments[part]
            mask = uv_footprint(piece, index, width, height)

            if mode == "vest":
                dye(pixels, mask & vest_pixels(original), color)
                dye(pixels, mask & ~vest_pixels(original), WHITE_BLOUSE)
            else:
                dye(pixels, mask, color)

            set_base_color_image(material, image)
            print(f"  {part}: {int(mask.sum())} pixels of {image_name} dyed")

        store_pixels(image, pixels)


def recolor_skin(materials: list, skin: tuple, prefix: str) -> None:
    """Tints every skin texture of the character the same way: multiply darkens, lift lightens toward a pale tone."""
    mode, tone = skin
    done = {}

    for material in dict.fromkeys(materials):  # a material shared by two meshes is tinted once
        source = base_color_image(material)

        if source.name not in done:
            pixels = image_pixels(source)
            rgb = pixels[..., :3]
            pixels[..., :3] = rgb * numpy.array(tone) if mode == "multiply" else (rgb + (1.0 - rgb) * 0.28) * numpy.array(tone)
            done[source.name] = copy_image(source, f"T_{prefix}_Skin{len(done) + 1}")
            store_pixels(done[source.name], pixels)

        set_base_color_image(material, done[source.name])


# ---------- shapes ----------

def head_frame(armature) -> tuple:
    head = armature.data.bones["Head"]

    return armature.matrix_world @ head.head_local, armature.matrix_world @ head.tail_local


def curly_top(hair, armature) -> None:
    """Fuller hair on top, the sides kept short (a fade), with small bumps for the curls."""
    pivot, _ = head_frame(armature)
    positions = [hair.matrix_world @ vertex.co for vertex in hair.data.vertices]
    top = max(point.z for point in positions)
    to_local = hair.matrix_world.inverted()
    centre = Vector((pivot.x, sum(point.y for point in positions) / len(positions), pivot.z + 0.09))

    for vertex, point in zip(hair.data.vertices, positions):
        rise = min(max((point.z - (top - 0.075)) / 0.06, 0.0), 1.0)
        curls = 0.5 + 0.5 * noise.noise(point * CURL_SCALE)
        outward = (point - centre).normalized()
        vertex.co = to_local @ (point + outward * rise * (0.008 + 0.010 * curls) + Vector((0.0, 0.0, rise * 0.006)))

    recompute_normals(hair)


def trimmed_beard(beard, head, eyes_z: float) -> None:
    """Only a thin goatee on the chin and a light moustache stay; cheeks and sideburns go, and what stays hugs the skin."""
    to_world = beard.matrix_world
    to_local = to_world.inverted()
    skin = body_tree([head])

    def keep(vertex) -> bool:
        point = to_world @ vertex.co
        below_eyes = eyes_z - point.z
        chin = abs(point.x) < 0.03 and below_eyes > 0.095
        moustache = abs(point.x) < 0.024 and 0.064 < below_eyes < 0.08

        return chin or moustache

    delete_vertices(beard, keep)

    for vertex in beard.data.vertices:
        point = to_world @ vertex.co
        nearest, normal, _, gap = skin.find_nearest(point)
        vertex.co = to_local @ (nearest + normal * max(gap * BEARD_THICKNESS, 0.0015))


def recompute_normals(mesh_object) -> None:
    """The imported custom normals would keep the old shading over the moved vertices."""
    bpy.ops.object.select_all(action="DESELECT")
    mesh_object.select_set(True)
    bpy.context.view_layer.objects.active = mesh_object
    bpy.ops.mesh.customdata_custom_splitnormals_clear()
    bpy.ops.object.shade_smooth()


def body_tree(meshes: list) -> BVHTree:
    depsgraph = bpy.context.evaluated_depsgraph_get()
    vertices, polygons = [], []

    for mesh_object in meshes:
        mesh = mesh_object.evaluated_get(depsgraph).to_mesh()
        offset = len(vertices)
        vertices += [mesh_object.matrix_world @ vertex.co for vertex in mesh.vertices]
        polygons += [[offset + index for index in polygon.vertices] for polygon in mesh.polygons]
        mesh_object.evaluated_get(depsgraph).to_mesh_clear()

    return BVHTree.FromPolygons(vertices, polygons)


def long_wavy_hair(hair, armature, body_meshes: list) -> None:
    """Grows the hair below the shoulders, waves the lower half and drapes it over the body instead of through it."""
    tree = body_tree(body_meshes)
    positions = [hair.matrix_world @ vertex.co for vertex in hair.data.vertices]
    to_local = hair.matrix_world.inverted()
    bottom = min(point.z for point in positions)
    start = bottom + 0.16  # the hair grows from here down
    stretch = 2.3

    for vertex, point in zip(hair.data.vertices, positions):
        depth = max(start - point.z, 0.0)
        reach = depth / (start - bottom)
        grown = Vector((point.x * (1.0 + 0.18 * reach), point.y, point.z - depth * (stretch - 1.0)))
        wave = math.sin(depth * stretch * 38.0 + point.x * 25.0) * 0.012 * reach
        grown += Vector((wave * math.copysign(1.0, point.x), wave * 0.5, 0.0))
        nearest, normal, _, gap = tree.find_nearest(grown)

        if nearest is not None and depth > 0.0 and ((grown - nearest).dot(normal) < 0.0 or gap < HAIR_CLEARANCE):
            grown = nearest + normal * HAIR_CLEARANCE

        vertex.co = to_local @ grown

    recompute_normals(hair)


def short_sleeves_and_bare_forearms(base_body_name: str, armature, skin_material) -> None:
    """Cuts the long sleeves at the elbow and puts the base body's own forearms and hands under them."""
    sleeves = outfit_piece("Arms")
    forearm_groups = groups_named(sleeves, FOREARM_PREFIXES)

    delete_vertices(sleeves, lambda vertex: weight_in(vertex, forearm_groups) <= SLEEVE_CUT_WEIGHT)

    base_objects = import_gltf(BASE_BODY_DIR / f"{base_body_name}.gltf")
    base_meshes = [scene_object for scene_object in base_objects if scene_object.type == "MESH" and scene_object.vertex_groups]
    forearms = max(base_meshes, key=lambda mesh_object: len(mesh_object.data.vertices))
    skin_groups = groups_named(forearms, FOREARM_PREFIXES)

    delete_vertices(forearms, lambda vertex: weight_in(vertex, skin_groups) >= FOREARM_KEEP_WEIGHT)
    forearms.name = "Forearms_Skin"
    forearms.data.materials.clear()
    forearms.data.materials.append(skin_material)
    bind_mesh_to_armature(forearms, armature)
    delete_objects([scene_object for scene_object in base_objects if scene_object is not forearms])


def eye_height() -> float:
    eyes = bpy.data.objects["Eyes"]

    return sum((eyes.matrix_world @ vertex.co).z for vertex in eyes.data.vertices) / len(eyes.data.vertices)


def build_partner(name: str) -> Path:
    recipe = COUPLE[name]
    prefix = "".join(word.title() for word in name.split("_"))
    output_path = OUTPUT_DIR / f"{name}.gltf"

    bpy.ops.wm.read_factory_settings(use_empty=True)

    outfit_objects = import_gltf(OUTFIT_DIR / f"{recipe['outfit']}.gltf")
    armature = find_armature(outfit_objects)

    delete_objects([scene_object for scene_object in outfit_objects if scene_object.type == "MESH" and not scene_object.vertex_groups])
    armature.name = "Armature"
    attach_base_head(recipe["base_body"], 0.15, 0.0, armature)

    for hair_name in recipe["hair"]:
        attach_hair(hair_name, armature)

    head = bpy.data.objects[HEAD_MESH_NAME]
    bpy.context.view_layer.update()  # matrix_world of the re-parented pieces is stale until then
    downscale_large_textures()
    recolor_garments(recipe["garments"], prefix)

    if name == "couple_her":
        short_sleeves_and_bare_forearms(recipe["base_body"], armature, head.data.materials[0])
        long_wavy_hair(bpy.data.objects["Hair_Long"], armature, [outfit_piece("Body")])
    else:
        curly_top(bpy.data.objects["Hair_Buzzed"], armature)
        trimmed_beard(bpy.data.objects["Hair_Beard"], head, eye_height())

    skin_materials = [material for scene_object in bpy.data.objects if scene_object.type == "MESH" for material in scene_object.data.materials if material and material.name.startswith(("MI_Superhero", "MI_Regular"))]
    recolor_skin(skin_materials, recipe["skin"], prefix)
    add_face_shapes(head, bpy.data.objects["Eyes"], bpy.data.objects["Eyebrows"])
    downscale_large_textures()
    bpy.ops.export_scene.gltf(filepath=str(output_path), export_format="GLTF_SEPARATE", export_texture_dir="textures", export_animations=False, export_yup=True)

    return output_path


if __name__ == "__main__":
    script_arguments = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []

    for partner in script_arguments or list(COUPLE):
        print(f"BUILT {partner} -> {build_partner(partner)}")
