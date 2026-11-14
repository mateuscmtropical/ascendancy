"""Assemble town houses from the CC0 Medieval Village MegaKit pieces and export them as .gltf.

Footprint convention (Blender, Z up): front facade faces -Y, width along X, depth along Y.
Every kit wall is 2 m wide, 3.12 m tall, exterior face toward -Y; window/door inserts share the wall origin.

Wall tokens: kit wall name, optionally suffixed with "+shutters" or "+balcony".

Usage:
  blender -b --factory-startup -P tools_src/build_houses.py -- [house_name ...]
"""

import math
import re
import sys
from pathlib import Path

import bmesh
import bpy
from mathutils import Matrix, Vector

PROJECT_DIR = Path(__file__).resolve().parent.parent
KIT_DIR = PROJECT_DIR / "tools" / "vendor" / "village" / "Medieval Village MegaKit[Standard]" / "glTF"
OUTPUT_DIR = PROJECT_DIR / "art" / "town"

WALL_WIDTH = 2.0
STOREY_HEIGHT = 3.12
CORNER_HEIGHT = 3.01
DOOR_HINGE_OFFSET = -0.53

FRONT, BACK, LEFT, RIGHT = "front", "back", "left", "right"
SIDE_ROTATION = {FRONT: 0.0, BACK: 180.0, LEFT: -90.0, RIGHT: 90.0}

# Opening in the wall name -> pieces that fill it, with their offset along the wall.
INSERTS = {
    "Window_Wide_Round": [("Window_Wide_Round1", 0.0)],
    "Window_Thin_Round": [("Window_Thin_Round1", 0.0)],
    "Window_Wide_Flat": [("Window_Wide_Flat1", 0.0)],
    "Door_Round": [("DoorFrame_Round_Brick", 0.0), ("Door_2_Round", DOOR_HINGE_OFFSET)],
    "Door_Flat": [("DoorFrame_Flat_Brick", 0.0), ("Door_2_Flat", DOOR_HINGE_OFFSET)],
}
SHUTTERS = {
    "Window_Wide_Round": "WindowShutters_Wide_Round_Open",
    "Window_Thin_Round": "WindowShutters_Thin_Round_Open",
    "Window_Wide_Flat": "WindowShutters_Wide_Flat_Open",
}
# Footprint -> (roof, gable, ridge height, eave half width) measured from the kit pieces.
ROOF_BY_FOOTPRINT = {
    (3, 3): ("Roof_RoundTiles_6x6", "Roof_Front_Brick6", 4.89, 4.12),
    (3, 4): ("Roof_RoundTiles_6x8", "Roof_Front_Brick6", 4.89, 4.12),
    (3, 5): ("Roof_RoundTiles_6x10", "Roof_Front_Brick6", 4.89, 4.12),
    (4, 4): ("Roof_RoundTiles_8x8", "Roof_Front_Brick8", 6.0, 4.98),
    (4, 5): ("Roof_RoundTiles_8x10", "Roof_Front_Brick8", 6.0, 4.98),
}
CHIMNEY_SINK = 0.7

STONE = "Wall_UnevenBrick_"
PLASTER = "Wall_Plaster_"


def ring(front: list, back: list, left: list, right: list) -> dict:
    return {FRONT: front, BACK: back, LEFT: left, RIGHT: right}


HOUSES = {
    "house_stone_tall": {
        "modules": (3, 4),
        "storeys": [
            ring(
                [STONE + "Window_Wide_Round+shutters", STONE + "Door_Round", STONE + "Window_Wide_Round+shutters"],
                [STONE + "Straight", STONE + "Window_Thin_Round", STONE + "Straight"],
                [STONE + "Straight", STONE + "Window_Thin_Round", STONE + "Window_Thin_Round", STONE + "Straight"],
                [STONE + "Straight", STONE + "Window_Thin_Round", STONE + "Window_Thin_Round", STONE + "Straight"],
            ),
            ring(
                [PLASTER + "Window_Wide_Round", PLASTER + "WoodGrid+balcony", PLASTER + "Window_Wide_Round"],
                [PLASTER + "WoodGrid", PLASTER + "Window_Thin_Round", PLASTER + "WoodGrid"],
                [PLASTER + "WoodGrid", PLASTER + "Window_Wide_Flat", PLASTER + "Window_Wide_Flat", PLASTER + "WoodGrid"],
                [PLASTER + "WoodGrid", PLASTER + "Window_Wide_Flat", PLASTER + "Window_Wide_Flat", PLASTER + "WoodGrid"],
            ),
        ],
        "chimney": (1.6, 1.0),
        "vines": [(FRONT, 0, 0)],
    },
    "house_plaster_wide": {
        "modules": (4, 4),
        "storeys": [
            ring(
                [STONE + "Window_Wide_Flat", STONE + "Door_Flat", STONE + "Straight", STONE + "Window_Wide_Flat"],
                [STONE + "Straight", STONE + "Window_Wide_Flat", STONE + "Window_Wide_Flat", STONE + "Straight"],
                [STONE + "Straight", STONE + "Window_Thin_Round", STONE + "Window_Thin_Round", STONE + "Straight"],
                [STONE + "Straight", STONE + "Window_Thin_Round", STONE + "Window_Thin_Round", STONE + "Straight"],
            ),
            ring(
                [PLASTER + "Window_Wide_Flat+shutters", PLASTER + "WoodGrid", PLASTER + "WoodGrid", PLASTER + "Window_Wide_Flat+shutters"],
                [PLASTER + "Straight", PLASTER + "Window_Wide_Flat", PLASTER + "Window_Wide_Flat", PLASTER + "Straight"],
                [PLASTER + "WoodGrid", PLASTER + "Window_Wide_Round", PLASTER + "Window_Wide_Round", PLASTER + "WoodGrid"],
                [PLASTER + "WoodGrid", PLASTER + "Window_Wide_Round", PLASTER + "Window_Wide_Round", PLASTER + "WoodGrid"],
            ),
        ],
        "chimney": (-2.2, 1.5),
        "vines": [],
    },
    "house_narrow_three": {
        "modules": (3, 4),
        "storeys": [
            ring(
                [STONE + "Straight", STONE + "Door_Round", STONE + "Window_Thin_Round"],
                [STONE + "Straight", STONE + "Straight", STONE + "Straight"],
                [STONE + "Straight", STONE + "Window_Thin_Round", STONE + "Straight", STONE + "Straight"],
                [STONE + "Straight", STONE + "Straight", STONE + "Window_Thin_Round", STONE + "Straight"],
            ),
            ring(
                [PLASTER + "Window_Thin_Round+shutters", PLASTER + "Window_Wide_Round", PLASTER + "Window_Thin_Round+shutters"],
                [PLASTER + "WoodGrid", PLASTER + "Window_Thin_Round", PLASTER + "WoodGrid"],
                [PLASTER + "WoodGrid", PLASTER + "Window_Thin_Round", PLASTER + "Window_Thin_Round", PLASTER + "WoodGrid"],
                [PLASTER + "WoodGrid", PLASTER + "Window_Thin_Round", PLASTER + "Window_Thin_Round", PLASTER + "WoodGrid"],
            ),
            ring(
                [PLASTER + "WoodGrid", PLASTER + "Window_Wide_Flat+balcony", PLASTER + "WoodGrid"],
                [PLASTER + "WoodGrid", PLASTER + "Window_Wide_Flat", PLASTER + "WoodGrid"],
                [PLASTER + "WoodGrid", PLASTER + "Window_Wide_Flat", PLASTER + "WoodGrid", PLASTER + "WoodGrid"],
                [PLASTER + "WoodGrid", PLASTER + "WoodGrid", PLASTER + "Window_Wide_Flat", PLASTER + "WoodGrid"],
            ),
        ],
        "chimney": (-1.5, 2.0),
        "vines": [(FRONT, 0, 2)],
    },
    "house_shop": {
        "modules": (4, 5),
        "storeys": [
            ring(
                [STONE + "Window_Wide_Flat", STONE + "Door_Round", STONE + "Window_Wide_Flat", STONE + "Window_Wide_Flat"],
                [STONE + "Straight", STONE + "Door_Flat", STONE + "Straight", STONE + "Straight"],
                [STONE + "Straight", STONE + "Window_Wide_Round", STONE + "Straight", STONE + "Window_Wide_Round", STONE + "Straight"],
                [STONE + "Straight", STONE + "Window_Wide_Round", STONE + "Straight", STONE + "Window_Wide_Round", STONE + "Straight"],
            ),
            ring(
                [PLASTER + "Window_Wide_Round+shutters", PLASTER + "WoodGrid+balcony", PLASTER + "WoodGrid+balcony", PLASTER + "Window_Wide_Round+shutters"],
                [PLASTER + "WoodGrid", PLASTER + "Window_Wide_Flat", PLASTER + "Window_Wide_Flat", PLASTER + "WoodGrid"],
                [PLASTER + "WoodGrid", PLASTER + "Window_Thin_Round", PLASTER + "WoodGrid", PLASTER + "Window_Thin_Round", PLASTER + "WoodGrid"],
                [PLASTER + "WoodGrid", PLASTER + "Window_Thin_Round", PLASTER + "WoodGrid", PLASTER + "Window_Thin_Round", PLASTER + "WoodGrid"],
            ),
        ],
        "chimney": (2.3, 2.5),
        "vines": [(FRONT, 3, 0)],
    },
    "house_cottage": {
        "modules": (3, 3),
        "storeys": [
            ring(
                [PLASTER + "Window_Wide_Round+shutters", PLASTER + "Door_Round", PLASTER + "Window_Wide_Round+shutters"],
                [PLASTER + "WoodGrid", PLASTER + "Window_Wide_Flat", PLASTER + "WoodGrid"],
                [PLASTER + "WoodGrid", PLASTER + "Window_Wide_Flat", PLASTER + "WoodGrid"],
                [PLASTER + "WoodGrid", PLASTER + "Window_Wide_Flat", PLASTER + "WoodGrid"],
            ),
        ],
        "chimney": (1.4, 0.8),
        "vines": [(FRONT, 2, 0)],
    },
}


def import_piece(piece_name: str, location: Vector, rotation_degrees: float) -> list:
    objects_before = set(bpy.data.objects)

    bpy.ops.import_scene.gltf(filepath=str(KIT_DIR / f"{piece_name}.gltf"))

    new_objects = list(set(bpy.data.objects) - objects_before)
    root_objects = [scene_object for scene_object in new_objects if scene_object.parent is None]

    for root_object in root_objects:
        root_object.location = location
        root_object.rotation_mode = "XYZ"
        root_object.rotation_euler = (0.0, 0.0, math.radians(rotation_degrees))

    return root_objects


def offset_along_wall(location: Vector, rotation_degrees: float, offset: float) -> Vector:
    return location + Matrix.Rotation(math.radians(rotation_degrees), 3, "Z") @ Vector((offset, 0.0, 0.0))


def wall_slot_transform(side: str, module_index: int, module_count: int, footprint: Vector, height: float) -> tuple:
    offset = (module_index - (module_count - 1) / 2.0) * WALL_WIDTH
    slot_positions = {
        FRONT: (offset, -footprint.y),
        BACK: (-offset, footprint.y),
        LEFT: (-footprint.x, -offset),
        RIGHT: (footprint.x, offset),
    }
    x, y = slot_positions[side]

    return Vector((x, y, height)), SIDE_ROTATION[side]


def opening_of(wall_name: str) -> str:
    return next((opening for opening in INSERTS if opening in wall_name), "")


def place_wall(token: str, location: Vector, rotation: float, is_top_storey: bool) -> None:
    wall_name, *extras = token.split("+")
    opening = opening_of(wall_name)

    import_piece(wall_name, location, rotation)

    for insert_name, offset in INSERTS.get(opening, []):
        import_piece(insert_name, offset_along_wall(location, rotation, offset), rotation)

    if "shutters" in extras:
        import_piece(SHUTTERS[opening], location, rotation)

    if "balcony" in extras:
        import_piece("Balcony_Cross_Straight", location, rotation)
        import_piece("Floor_WoodDark_Half1", offset_along_wall(location, rotation, 0.0) + Matrix.Rotation(math.radians(rotation), 3, "Z") @ Vector((0.0, -0.5, 0.0)), rotation)


def place_storey(storey: dict, storey_index: int, footprint: Vector, is_top_storey: bool) -> None:
    height = storey_index * STOREY_HEIGHT
    corners = [((-footprint.x, -footprint.y), 0.0), ((footprint.x, -footprint.y), 90.0), ((footprint.x, footprint.y), 180.0), ((-footprint.x, footprint.y), -90.0)]
    wall_slots = [(side, module_index, len(tokens), token) for side, tokens in storey.items() for module_index, token in enumerate(tokens)]

    for side, module_index, module_count, token in wall_slots:
        location, rotation = wall_slot_transform(side, module_index, module_count, footprint, height)
        place_wall(token, location, rotation, is_top_storey)

    for (x, y), rotation in corners:
        for corner_object in import_piece("Corner_Exterior_Brick", Vector((x, y, height)), rotation):
            corner_object.scale.z = STOREY_HEIGHT / CORNER_HEIGHT


def place_floors(modules: tuple, storey_count: int) -> None:
    tiles_per_storey = modules[0] * modules[1]

    for tile_index in range(tiles_per_storey * storey_count):
        storey_index, cell_index = divmod(tile_index, tiles_per_storey)
        column, row = cell_index % modules[0], cell_index // modules[0]
        x = (column - (modules[0] - 1) / 2.0) * WALL_WIDTH
        y = (row - (modules[1] - 1) / 2.0) * WALL_WIDTH
        import_piece("Floor_WoodDark", Vector((x, y, storey_index * STOREY_HEIGHT + 0.02)), 0.0)


def place_vines(vines: list, modules: tuple, footprint: Vector) -> None:
    for side, module_index, storey_index in vines:
        module_count = modules[0] if side in (FRONT, BACK) else modules[1]
        location, rotation = wall_slot_transform(side, module_index, module_count, footprint, (storey_index + 1) * STOREY_HEIGHT - 0.2)
        import_piece("Prop_Vine2", location + Matrix.Rotation(math.radians(rotation), 3, "Z") @ Vector((-0.6, -0.12, 0.0)), rotation)


def add_collision_box(footprint: Vector, height: float) -> None:
    """Godot turns *-colonly meshes into a StaticBody3D collision shape."""
    collision_bmesh = bmesh.new()
    bmesh.ops.create_cube(collision_bmesh, size=1.0)
    bmesh.ops.scale(collision_bmesh, vec=(footprint.x * 2 + 0.6, footprint.y * 2 + 0.6, height), verts=collision_bmesh.verts)
    bmesh.ops.translate(collision_bmesh, vec=(0, 0, height / 2.0), verts=collision_bmesh.verts)
    mesh_data = bpy.data.meshes.new("House-colonly")
    collision_bmesh.to_mesh(mesh_data)
    collision_bmesh.free()
    bpy.context.scene.collection.objects.link(bpy.data.objects.new("House-colonly", mesh_data))


def merge_duplicate_datablocks() -> None:
    """Every kit import brings its own copy of MI_Plaster etc.; point all users at the first copy."""
    for collection in (bpy.data.materials, bpy.data.images):
        duplicates = [block for block in collection if re.search(r"\.\d{3}$", block.name) and block.name[:-4] in collection]

        for duplicate in duplicates:
            duplicate.user_remap(collection[duplicate.name[:-4]])
            collection.remove(duplicate)


def merge_visible_meshes() -> None:
    """Join every kit piece into one mesh (one surface per material) so a house costs a handful of draw calls."""
    meshes = [scene_object for scene_object in bpy.data.objects if scene_object.type == "MESH" and not scene_object.name.endswith("-colonly")]
    world_matrices = [mesh_object.matrix_world.copy() for mesh_object in meshes]

    for mesh_object, world_matrix in zip(meshes, world_matrices):
        mesh_object.parent = None
        mesh_object.matrix_world = world_matrix
        mesh_object.data = mesh_object.data.copy()

    for empty in [scene_object for scene_object in bpy.data.objects if scene_object.type == "EMPTY"]:
        bpy.data.objects.remove(empty, do_unlink=True)

    with bpy.context.temp_override(active_object=meshes[0], selected_editable_objects=meshes):
        bpy.ops.object.join()

    meshes[0].name = "House"


def build_house(house_name: str) -> Path:
    recipe = HOUSES[house_name]
    modules = recipe["modules"]
    storeys = recipe["storeys"]
    footprint = Vector((modules[0] * WALL_WIDTH / 2.0, modules[1] * WALL_WIDTH / 2.0, 0.0))
    roof_height = len(storeys) * STOREY_HEIGHT
    roof_name, gable_name, ridge_height, eave_half_width = ROOF_BY_FOOTPRINT[modules]
    chimney_x, chimney_y = recipe["chimney"]
    chimney_base = roof_height + ridge_height * (1.0 - abs(chimney_x) / eave_half_width) - CHIMNEY_SINK
    output_path = OUTPUT_DIR / f"{house_name}.gltf"

    bpy.ops.wm.read_factory_settings(use_empty=True)

    for storey_index, storey in enumerate(storeys):
        place_storey(storey, storey_index, footprint, storey_index == len(storeys) - 1)

    place_floors(modules, len(storeys))
    place_vines(recipe["vines"], modules, footprint)
    import_piece(roof_name, Vector((0.0, 0.0, roof_height)), 0.0)
    import_piece(gable_name, Vector((0.0, -footprint.y, roof_height)), 0.0)
    import_piece(gable_name, Vector((0.0, footprint.y, roof_height)), 180.0)
    import_piece("Prop_Chimney", Vector((chimney_x, chimney_y, chimney_base)), 0.0)
    add_collision_box(footprint, roof_height)
    merge_duplicate_datablocks()
    merge_visible_meshes()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    bpy.ops.export_scene.gltf(filepath=str(output_path), export_format="GLTF_SEPARATE", export_texture_dir="textures", export_yup=True)

    return output_path


if __name__ == "__main__":
    script_arguments = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []

    for requested_house in script_arguments or list(HOUSES):
        print(f"BUILT {requested_house} -> {build_house(requested_house)}")
