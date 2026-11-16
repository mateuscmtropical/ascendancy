"""Convert the cow, pig and horse of the CC0 Quaternius "Farm Animals Animated" pack to glTF for the farm and the
street carriages (art/town/farm/animals/<animal>.gltf).

The pack (python tools_src/fetch_assets.py animals -> tools/vendor/animals) ships FBX in centimetres with the
animals facing whichever way the author modelled them. For each animal this script:
  1. imports the first file whose name matches (glTF/GLB preferred, then FBX), anywhere under the pack folder;
  2. scales the top-level object so the rest pose stands ANIMALS[animal] metres tall;
  3. turns it so the head points to Godot +Z (Blender -Y): the head is the end of the long axis that carries the
     highest vertices;
  4. renames the actions to the names the game plays (Idle, Walk) and drops the rest;
  5. exports glTF with only those animations; the sidecar JSON keeps the height and the original action names.

Usage:
  blender -b --factory-startup -P tools_src/convert_farm_animals.py -- [cow pig horse] [--source <pack folder>]
"""

import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Matrix, Vector

PROJECT_DIR = Path(__file__).resolve().parent.parent
PACK_DIR = PROJECT_DIR / "tools" / "vendor" / "animals"
OUTPUT_DIR = PROJECT_DIR / "art" / "town" / "farm" / "animals"
ANIMALS = {"cow": 1.4, "pig": 0.7, "horse": 1.75}  # altura do modelo em repouso, metros
ACTION_NAMES = {"idle": "Idle", "walk": "Walk"}  # último trecho do nome original ("Armature|Armature|Walk", minúsculo) -> nome no jogo
SOURCE_SUFFIXES = (".gltf", ".glb", ".fbx")
HEAD_HEIGHT_SHARE = 0.75  # vértices acima desta fração da altura marcam a ponta da cabeça


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


def mesh_world_vertices() -> list:
    depsgraph = bpy.context.evaluated_depsgraph_get()
    vertices = []

    for mesh_object in (scene_object for scene_object in bpy.context.scene.objects if scene_object.type == "MESH"):
        evaluated = mesh_object.evaluated_get(depsgraph)
        vertices += [evaluated.matrix_world @ vertex.co for vertex in evaluated.data.vertices]

    return vertices


def heading_turn(vertices: list) -> float:
    """Yaw (radians, around Blender Z) that brings the head to -Y: the long horizontal axis is the body, and the
    end where the tallest vertices gather is the head."""
    heights = [vertex.z for vertex in vertices]
    head_level = min(heights) + (max(heights) - min(heights)) * HEAD_HEIGHT_SHARE
    span_x = max(vertex.x for vertex in vertices) - min(vertex.x for vertex in vertices)
    span_y = max(vertex.y for vertex in vertices) - min(vertex.y for vertex in vertices)
    axis = 0 if span_x > span_y else 1
    center = sum(vertex[axis] for vertex in vertices) / len(vertices)
    high = [vertex[axis] - center for vertex in vertices if vertex.z >= head_level]
    head_sign = 1.0 if sum(high) >= 0.0 else -1.0
    head_direction = Vector((head_sign, 0.0)) if axis == 0 else Vector((0.0, head_sign))

    return math.atan2(-1.0, 0.0) - math.atan2(head_direction.y, head_direction.x)


def normalize(animal: str) -> float:
    """Hang the imported objects under a new root that scales and turns them so the animal stands ANIMALS[animal]
    tall with its head to Godot +Z. FBX actions animate the armature object itself, so its own transform cannot be
    changed: the exporter would sample the action over it."""
    roots = [scene_object for scene_object in bpy.context.scene.objects if scene_object.parent is None]
    vertices = mesh_world_vertices()
    height = max(vertex.z for vertex in vertices) - min(vertex.z for vertex in vertices)
    factor = ANIMALS[animal] / height
    animal_root = bpy.data.objects.new(animal.title(), None)

    bpy.context.scene.collection.objects.link(animal_root)

    for root in roots:
        root.parent = animal_root

    animal_root.matrix_world = Matrix.Rotation(heading_turn(vertices), 4, "Z") @ Matrix.Scale(factor, 4)
    bpy.context.view_layer.update()
    animal_root.location.z -= min(vertex.z for vertex in mesh_world_vertices())

    return factor


def rename_actions() -> dict:
    """Game name -> original action name; actions the game does not use are removed."""
    kept = {}

    for action in list(bpy.data.actions):
        last_part = action.name.rsplit("|", 1)[-1].lower()
        game_name = ACTION_NAMES.get(last_part)

        if game_name is None:
            bpy.data.actions.remove(action)
            continue

        kept[game_name] = action.name
        action.name = game_name

    return kept


def convert(animal: str, pack_dir: Path) -> dict:
    source = find_source(pack_dir, animal)
    output_path = OUTPUT_DIR / f"{animal}.gltf"

    bpy.ops.wm.read_factory_settings(use_empty=True)
    import_source(source)
    factor = normalize(animal)
    actions = rename_actions()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    bpy.ops.export_scene.gltf(filepath=str(output_path), export_format="GLTF_SEPARATE", export_yup=True, export_animation_mode="ACTIONS", export_force_sampling=True)

    sidecar = {"source": source.name, "height": ANIMALS[animal], "scale": round(factor, 5), "animations": actions}
    output_path.with_suffix(".json").write_text(json.dumps(sidecar, indent=1), encoding="utf-8", newline="\n")

    return sidecar


if __name__ == "__main__":
    arguments = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    source_dir = Path(arguments[arguments.index("--source") + 1]) if "--source" in arguments else PACK_DIR
    requested = [argument for argument in arguments if argument in ANIMALS]

    for animal_name in requested or list(ANIMALS):
        result = convert(animal_name, source_dir)
        print(f"BUILT {animal_name}: {result}")

        if "Idle" not in result["animations"] or "Walk" not in result["animations"]:
            print(f"AVISO {animal_name}: faltou Idle ou Walk; animações do pacote: {result['animations']}")
