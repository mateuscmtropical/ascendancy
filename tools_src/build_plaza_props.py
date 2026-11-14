"""Model the plaza props (fountains, lamp post, planter) and export them to art/town/.

Reuses the geometry helpers and stone textures of build_cathedral.py (run that first: it writes the textures).
Meshes named "Water" get the water shader in Godot; *-colonly boxes become collision.

Usage:
  blender -b --factory-startup -P tools_src/build_plaza_props.py
"""

import math
import sys
from pathlib import Path

import bpy

sys.path.insert(0, str(Path(__file__).resolve().parent))

from build_cathedral import (  # noqa: E402
    GENERATED_TEXTURES,
    OUTPUT_DIR,
    load_kit_image,
    make_cone,
    make_cylinder,
    make_material,
    make_plain_material,
    map_uvs_per_face,
)


def build_prop_materials() -> dict:
    stone_image = bpy.data.images.load(str(GENERATED_TEXTURES / "T_CathedralStone_BaseColor.png"))
    trim_image = bpy.data.images.load(str(GENERATED_TEXTURES / "T_CathedralTrim_BaseColor.png"))

    return {
        "stone": make_material("M_CathedralStone", stone_image, load_kit_image("T_Brick_Normal.png", False)),
        "trim": make_material("M_CathedralTrim", trim_image, load_kit_image("T_Plaster_Normal.png", False)),
        "water": make_plain_material("M_Water", (0.25, 0.55, 0.65), 0.0, 0.05),
        "metal": make_plain_material("M_LampMetal", (0.09, 0.09, 0.11), 0.8, 0.45),
        "lamp_glass": make_lamp_glass_material(),
        "soil": make_plain_material("M_Soil", (0.22, 0.15, 0.10), 0.0, 1.0),
    }


def make_lamp_glass_material():
    material = make_plain_material("M_LampGlass", (0.75, 0.6, 0.38), 0.0, 0.3)
    shader = material.node_tree.nodes["Principled BSDF"]

    shader.inputs["Emission Color"].default_value = (1.0, 0.78, 0.45, 1.0)
    shader.inputs["Emission Strength"].default_value = 0.9

    return material


def make_frustum(name: str, base_z: float, bottom_radius: float, top_radius: float, height: float, sides: int, material):
    import bmesh

    frustum_bmesh = bmesh.new()
    bmesh.ops.create_cone(frustum_bmesh, cap_ends=True, segments=sides, radius1=bottom_radius, radius2=top_radius, depth=height)
    bmesh.ops.translate(frustum_bmesh, vec=(0, 0, base_z + height / 2.0), verts=frustum_bmesh.verts)

    from build_cathedral import object_from_bmesh

    return object_from_bmesh(name, frustum_bmesh, material)


def make_octagon_ring(name: str, outer_radius: float, inner_radius: float, height: float, material):
    ring = make_cylinder(name, (0, 0, 0), outer_radius, height, 8, material)
    hole = make_cylinder(name + "_hole", (0, 0, -0.1), inner_radius, height + 0.2, 8, None)
    modifier = ring.modifiers.new("hole", "BOOLEAN")

    modifier.operation = "DIFFERENCE"
    modifier.solver = "EXACT"
    modifier.object = hole
    bpy.context.view_layer.objects.active = ring
    bpy.ops.object.modifier_apply(modifier="hole")
    bpy.data.objects.remove(hole, do_unlink=True)
    ring.rotation_euler.z = math.pi / 8.0

    return ring


def build_large_fountain(materials: dict) -> None:
    make_octagon_ring("BasinStep", 5.7, 4.0, 0.18, materials["trim"])
    make_octagon_ring("BasinWall", 5.0, 4.55, 0.75, materials["stone"])
    make_octagon_ring("BasinRim", 5.12, 4.45, 0.12, materials["trim"]).location.z = 0.75
    make_cylinder("BasinFloor", (0, 0, 0), 4.6, 0.3, 8, materials["stone"]).rotation_euler.z = math.pi / 8.0
    make_cylinder("Water", (0, 0, 0.3), 4.58, 0.28, 32, materials["water"])
    make_frustum("Pedestal", 0.3, 0.9, 0.55, 0.5, 8, materials["trim"])
    make_cylinder("Column", (0, 0, 0.8), 0.42, 1.0, 12, materials["trim"])
    make_frustum("LowerBowl", 1.8, 0.45, 2.1, 0.5, 24, materials["trim"])
    make_cylinder("LowerBowlRim", (0, 0, 2.3), 2.12, 0.08, 24, materials["trim"])
    make_cylinder("Water", (0, 0, 2.2), 1.95, 0.16, 24, materials["water"])
    make_cylinder("UpperColumn", (0, 0, 2.38), 0.24, 0.9, 12, materials["trim"])
    make_frustum("UpperBowl", 3.28, 0.25, 1.05, 0.35, 20, materials["trim"])
    make_cylinder("Water", (0, 0, 3.5), 0.95, 0.1, 20, materials["water"])
    make_frustum("FinialBase", 3.6, 0.22, 0.14, 0.35, 12, materials["trim"])
    make_cone("Finial", (0, 0, 3.95), 0.16, 0.6, 12, materials["trim"])
    make_cylinder("Fountain-colonly", (0, 0, 0), 5.1, 1.2, 8, None).rotation_euler.z = math.pi / 8.0


def build_small_fountain(materials: dict) -> None:
    make_octagon_ring("BasinWall", 2.0, 1.7, 0.6, materials["stone"])
    make_octagon_ring("BasinRim", 2.08, 1.62, 0.1, materials["trim"]).location.z = 0.6
    make_cylinder("BasinFloor", (0, 0, 0), 1.75, 0.25, 8, materials["stone"]).rotation_euler.z = math.pi / 8.0
    make_cylinder("Water", (0, 0, 0.25), 1.72, 0.22, 24, materials["water"])
    make_cylinder("Column", (0, 0, 0.25), 0.22, 1.1, 10, materials["trim"])
    make_frustum("Bowl", 1.35, 0.22, 0.8, 0.3, 16, materials["trim"])
    make_cylinder("Water", (0, 0, 1.55), 0.72, 0.08, 16, materials["water"])
    make_cone("Finial", (0, 0, 1.65), 0.12, 0.45, 10, materials["trim"])
    make_cylinder("Fountain-colonly", (0, 0, 0), 2.1, 1.0, 8, None).rotation_euler.z = math.pi / 8.0


def build_lamp_post(materials: dict) -> None:
    make_frustum("Base", 0.0, 0.28, 0.2, 0.35, 8, materials["metal"])
    make_cylinder("Post", (0, 0, 0.35), 0.065, 2.85, 10, materials["metal"])
    make_cylinder("Collar", (0, 0, 3.1), 0.12, 0.1, 10, materials["metal"])
    make_frustum("LanternBottom", 3.2, 0.12, 0.22, 0.12, 6, materials["metal"])
    make_cylinder("LanternGlass", (0, 0, 3.32), 0.2, 0.5, 6, materials["lamp_glass"])
    make_frustum("LanternRoof", 3.82, 0.3, 0.05, 0.32, 6, materials["metal"])
    make_cylinder("LampPost-colonly", (0, 0, 0), 0.2, 2.5, 8, None)


def build_planter(materials: dict) -> None:
    make_octagon_ring("PlanterWall", 1.3, 1.08, 0.5, materials["stone"])
    make_octagon_ring("PlanterRim", 1.36, 1.02, 0.08, materials["trim"]).location.z = 0.5
    make_cylinder("Soil", (0, 0, 0), 1.1, 0.42, 8, materials["soil"]).rotation_euler.z = math.pi / 8.0
    make_cylinder("Planter-colonly", (0, 0, 0), 1.3, 1.0, 8, None).rotation_euler.z = math.pi / 8.0


PROPS = {
    "fountain_large": build_large_fountain,
    "fountain_small": build_small_fountain,
    "lamp_post": build_lamp_post,
    "planter": build_planter,
}


def build_prop(prop_name: str) -> Path:
    output_path = OUTPUT_DIR / f"{prop_name}.gltf"
    tile_sizes = {"M_CathedralStone": 3.0, "M_CathedralTrim": 1.5}

    bpy.ops.wm.read_factory_settings(use_empty=True)

    materials = build_prop_materials()
    PROPS[prop_name](materials)
    bpy.context.view_layer.update()

    for mesh_object in [scene_object for scene_object in bpy.data.objects if scene_object.type == "MESH" and scene_object.data.materials]:
        map_uvs_per_face(mesh_object, tile_sizes.get(mesh_object.data.materials[0].name, 2.0))

    bpy.ops.export_scene.gltf(filepath=str(output_path), export_format="GLTF_SEPARATE", export_texture_dir="textures", export_yup=True)

    return output_path


if __name__ == "__main__":
    script_arguments = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []

    for requested_prop in script_arguments or list(PROPS):
        print(f"BUILT {requested_prop} -> {build_prop(requested_prop)}")
