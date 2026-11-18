"""Assemble the playable/NPC characters from the CC0 Quaternius packs and export them as .glb.

Every character = outfit (body parts + clothes) + head/eyes/eyebrows cut from a base body + hairstyle,
all skinned to the outfit armature (65-bone Universal rig, same as the UAL animation libraries).

Usage:
  blender -b --factory-startup -P tools_src/build_characters.py -- [character_name ...]
"""

import sys
from pathlib import Path

import bmesh
import bpy

sys.path.insert(0, str(Path(__file__).resolve().parent))

from face_shapes import add_face_shapes  # noqa: E402

PROJECT_DIR = Path(__file__).resolve().parent.parent
VENDOR_DIR = PROJECT_DIR / "tools" / "vendor"
OUTPUT_DIR = PROJECT_DIR / "art" / "characters"

BASE_BODY_DIR = VENDOR_DIR / "ubc" / "Universal Base Characters[Standard]" / "Base Characters" / "Godot - UE"
HAIR_DIR = VENDOR_DIR / "ubc" / "Universal Base Characters[Standard]" / "Hairstyles" / "Rigged to Head Bone" / "glTF (Godot -Unreal)"
OUTFIT_DIR = VENDOR_DIR / "outfits" / "Modular Character Outfits - Fantasy[Standard]" / "Exports" / "glTF (Godot-Unreal)" / "Outfits"

HEAD_BONES = ("Head", "neck_01")
HEAD_MESH_NAME = "Head_Skin"
MAX_TEXTURE_SIZE = 2048

CHARACTERS = {
    "adventurer_male": {
        "outfit": "Male_Ranger",
        "base_body": "Superhero_Male_FullBody",
        "hair": ["Hair_SimpleParted"],
        "hidden_parts": ["Head_Hood"],
        "head_weight_to_keep": 0.5,
        "neck_shrink_meters": 0.008,
    },
    "adventurer_female": {
        "outfit": "Female_Ranger",
        "base_body": "Superhero_Female_FullBody",
        "hair": ["Hair_Long"],
        "hidden_parts": ["Head_Hood"],
        "head_weight_to_keep": 0.5,
        "neck_shrink_meters": 0.008,
    },
    "villager_male": {
        "outfit": "Male_Peasant",
        "base_body": "Superhero_Male_FullBody",
        "hair": ["Hair_Buzzed", "Hair_Beard"],
        "hidden_parts": [],
        "head_weight_to_keep": 0.15,
        "neck_shrink_meters": 0.0,
    },
    "villager_female": {
        "outfit": "Female_Peasant",
        "base_body": "Superhero_Female_FullBody",
        "hair": ["Hair_Buns"],
        "hidden_parts": [],
        "head_weight_to_keep": 0.15,
        "neck_shrink_meters": 0.0,
    },
}


def import_gltf(path: Path) -> list:
    objects_before = set(bpy.data.objects)

    bpy.ops.import_scene.gltf(filepath=str(path))

    return list(set(bpy.data.objects) - objects_before)


def find_armature(objects: list):
    return next(scene_object for scene_object in objects if scene_object.type == "ARMATURE")


def bind_mesh_to_armature(mesh_object, armature) -> None:
    mesh_object.parent = armature

    armature_modifiers = [modifier for modifier in mesh_object.modifiers if modifier.type == "ARMATURE"]
    armature_modifiers[0].object = armature


def delete_objects(objects: list) -> None:
    for scene_object in objects:
        bpy.data.objects.remove(scene_object, do_unlink=True)


def head_weight_of_vertex(vertex, head_group_indices: set) -> float:
    head_weights = [group.weight for group in vertex.groups if group.group in head_group_indices]

    return sum(head_weights)


def cut_body_to_head(body_mesh, head_weight_to_keep: float) -> None:
    head_group_indices = {body_mesh.vertex_groups[bone].index for bone in HEAD_BONES}
    mesh_data = body_mesh.data
    indices_to_remove = {
        vertex.index for vertex in mesh_data.vertices
        if head_weight_of_vertex(vertex, head_group_indices) < head_weight_to_keep
    }
    body_bmesh = bmesh.new()

    body_bmesh.from_mesh(mesh_data)
    body_bmesh.verts.ensure_lookup_table()

    vertices_to_remove = [body_bmesh.verts[index] for index in indices_to_remove]

    bmesh.ops.delete(body_bmesh, geom=vertices_to_remove, context="VERTS")
    body_bmesh.to_mesh(mesh_data)
    body_bmesh.free()


def shrink_lower_neck(body_mesh, shrink_meters: float) -> None:
    """Push neck vertices inward so a tight collar covers them; the jaw (pure Head weight) stays put."""
    head_group_index = body_mesh.vertex_groups["Head"].index
    object_scale = body_mesh.matrix_world.to_scale().x

    print(f"  neck shrink {shrink_meters} m, object scale {object_scale}")

    for vertex in body_mesh.data.vertices:
        jaw_weight = head_weight_of_vertex(vertex, {head_group_index})
        vertex.co -= vertex.normal * (shrink_meters / object_scale) * (1.0 - jaw_weight)


def attach_base_head(base_body_name: str, head_weight_to_keep: float, neck_shrink_meters: float, armature) -> None:
    base_objects = import_gltf(BASE_BODY_DIR / f"{base_body_name}.gltf")
    base_meshes = [scene_object for scene_object in base_objects if scene_object.type == "MESH" and scene_object.vertex_groups]
    body_mesh = max(base_meshes, key=lambda mesh_object: len(mesh_object.data.vertices))

    cut_body_to_head(body_mesh, head_weight_to_keep)
    shrink_lower_neck(body_mesh, neck_shrink_meters)
    # Not "Head": Godot renames the Head bone when a mesh node takes that name, and no clip moves the head.
    body_mesh.name = HEAD_MESH_NAME

    for mesh_object in base_meshes:
        bind_mesh_to_armature(mesh_object, armature)

    leftovers = [scene_object for scene_object in base_objects if scene_object not in base_meshes]
    delete_objects(leftovers)


def attach_hair(hair_name: str, armature) -> None:
    hair_objects = import_gltf(HAIR_DIR / f"{hair_name}.gltf")
    hair_meshes = [scene_object for scene_object in hair_objects if scene_object.type == "MESH" and scene_object.vertex_groups]

    for hair_mesh in hair_meshes:
        bind_mesh_to_armature(hair_mesh, armature)

    leftovers = [scene_object for scene_object in hair_objects if scene_object not in hair_meshes]
    delete_objects(leftovers)


def downscale_large_textures() -> None:
    large_images = [image for image in bpy.data.images if max(image.size) > MAX_TEXTURE_SIZE]

    for image in large_images:
        image.scale(MAX_TEXTURE_SIZE, MAX_TEXTURE_SIZE)


def build_character(character_name: str) -> Path:
    recipe = CHARACTERS[character_name]
    output_path = OUTPUT_DIR / f"{character_name}.gltf"

    bpy.ops.wm.read_factory_settings(use_empty=True)

    outfit_objects = import_gltf(OUTFIT_DIR / f"{recipe['outfit']}.gltf")
    armature = find_armature(outfit_objects)
    hidden_meshes = [
        scene_object for scene_object in outfit_objects
        if any(part in scene_object.name for part in recipe["hidden_parts"]) or not scene_object.vertex_groups and scene_object.type == "MESH"
    ]

    delete_objects(hidden_meshes)
    armature.name = "Armature"

    attach_base_head(recipe["base_body"], recipe["head_weight_to_keep"], recipe["neck_shrink_meters"], armature)

    for hair_name in recipe["hair"]:
        attach_hair(hair_name, armature)

    add_face_shapes(bpy.data.objects[HEAD_MESH_NAME], bpy.data.objects["Eyes"], bpy.data.objects["Eyebrows"])
    downscale_large_textures()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    bpy.ops.export_scene.gltf(
        filepath=str(output_path),
        export_format="GLTF_SEPARATE",
        export_texture_dir="textures",
        export_animations=False,
        export_yup=True,
    )

    return output_path


if __name__ == "__main__":
    script_arguments = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    requested_characters = script_arguments or list(CHARACTERS)

    for requested_character in requested_characters:
        exported_path = build_character(requested_character)
        print(f"BUILT {requested_character} -> {exported_path}")
