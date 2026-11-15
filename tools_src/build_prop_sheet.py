"""Render a validation sheet of shop props: every PROPS entry of the given modules on a grid, each with its
name on the floor and a 1.7 m human ruler per row, seen in 3/4 from the customer side (-Y).

Usage:
  blender -b --factory-startup -P tools_src/build_prop_sheet.py -- <module> [<module> ...] --out <sheet.png>
      [--only name,name] [--columns 6] [--size 2400x1600]
Props that declare "variants" get one copy per variant. Ceiling props ("hang": True, z = 0 at the ceiling
mount, growing down) are lifted so they hang above the floor. Also prints each prop's triangle count and
whether it stays inside its declared size (OVER means some geometry pokes out of the box).
"""

import importlib
import math
import sys
from pathlib import Path

import bpy
from mathutils import Matrix, Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))

from build_town_houses import Builder, map_uvs, paint_vertex_colors, srgb  # noqa: E402

CELL_MARGIN = 1.2
SIZE_TOLERANCE = 0.03
RULER_HEIGHT = 1.7
HANG_GAP = 0.3  # ceiling props hang this far above the sheet floor


def parse_arguments() -> dict:
    arguments = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    options = {"modules": [], "out": "prop_sheet.png", "only": None, "columns": 6, "size": (2400, 1600)}
    readers = {
        "--out": lambda value: options.update(out=value),
        "--only": lambda value: options.update(only=set(value.split(","))),
        "--columns": lambda value: options.update(columns=int(value)),
        "--size": lambda value: options.update(size=tuple(int(part) for part in value.split("x"))),
    }
    pending = None

    for argument in arguments:
        if pending:
            readers[pending](argument)
            pending = None
        elif argument in readers:
            pending = argument
        else:
            options["modules"].append(argument)

    return options


def sheet_entries(modules: list, only: set) -> list:
    """(label, build, size, options, is_hanging) for every prop (and variant) of the modules."""
    entries = []

    for module_name in modules:
        props = importlib.import_module(module_name).PROPS
        selected = [(name, spec) for name, spec in props.items() if only is None or name in only]
        entries += [(f"{name}:{variant}" if variant else name, spec["build"], spec["size"], {"variant": variant} if variant else {}, spec.get("hang", False)) for name, spec in selected for variant in spec.get("variants", [None])]

    return entries


def scene_objects() -> set:
    return set(bpy.context.scene.objects)


def triangle_count(objects: set) -> int:
    return sum(sum(len(polygon.vertices) - 2 for polygon in scene_object.data.polygons) for scene_object in objects if scene_object.type == "MESH")


def bounds(objects: set) -> tuple:
    corners = [scene_object.matrix_world @ Vector(corner) for scene_object in objects if scene_object.type == "MESH" for corner in scene_object.bound_box]

    if not corners:
        return (0.0, 0.0, 0.0), (0.0, 0.0, 0.0)

    return tuple(min(corner[axis] for corner in corners) for axis in range(3)), tuple(max(corner[axis] for corner in corners) for axis in range(3))


def label(text: str, location: tuple, size: float) -> None:
    curve = bpy.data.curves.new(f"Label_{text}", type="FONT")
    curve.body = text
    curve.size = size
    curve.align_x = "CENTER"
    text_object = bpy.data.objects.new(f"Label_{text}", curve)
    text_object.location = location
    material = bpy.data.materials.new(f"LabelInk_{text}")
    material.diffuse_color = (0.05, 0.04, 0.08, 1.0)
    curve.materials.append(material)
    bpy.context.scene.collection.objects.link(text_object)


def ruler(b: Builder, x: float, y: float) -> None:
    stripes = int(RULER_HEIGHT / 0.1)

    for stripe in range(stripes):
        color = "C9483B" if stripe % 2 else "F2E6CF"
        b.box((x - 0.06, y - 0.06, stripe * 0.1), (x + 0.06, y + 0.06, (stripe + 1) * 0.1), "paint", srgb(color))

    b.sphere((x, y, RULER_HEIGHT + 0.1), 0.11, "paint", srgb("F7D6C4"), segments=8)


def place_entries(b: Builder, entries: list, columns: int) -> tuple:
    """Builds each entry in its grid cell; returns the sheet extent and the report lines."""
    cell = max(max(size[0], size[1]) for _, _, size, _, _ in entries) + CELL_MARGIN
    report = []

    for index, (text, build, size, options, is_hanging) in enumerate(entries):
        column, row = index % columns, index // columns
        mount = size[2] + HANG_GAP if is_hanging else 0.0
        bottom, top = (-size[2], 0.0) if is_hanging else (0.0, size[2])
        origin = (column * cell, -row * cell, mount)
        before = scene_objects()
        build(b, Matrix.Translation(origin), seed=index + 1, **options)
        added = scene_objects() - before
        minimum, maximum = bounds(added)
        local_minimum = [minimum[axis] - origin[axis] for axis in range(3)]
        local_maximum = [maximum[axis] - origin[axis] for axis in range(3)]
        half = (size[0] / 2.0, size[1] / 2.0)
        is_inside = all(
            [
                local_minimum[0] >= -half[0] - SIZE_TOLERANCE,
                local_maximum[0] <= half[0] + SIZE_TOLERANCE,
                local_minimum[1] >= -half[1] - SIZE_TOLERANCE,
                local_maximum[1] <= half[1] + SIZE_TOLERANCE,
                local_minimum[2] >= bottom - SIZE_TOLERANCE,
                local_maximum[2] <= top + SIZE_TOLERANCE,
            ]
        )
        extent = tuple(round(local_maximum[axis] - local_minimum[axis], 2) for axis in range(3))
        report.append(f"PROP {text}: tris={triangle_count(added)} extent={extent} declared={tuple(size)} {'ok' if is_inside else 'OVER'} zmin={round(local_minimum[2], 3)}")
        label(text, (origin[0], origin[1] - size[1] / 2.0 - 0.45, 0.01), 0.22)

    rows = (len(entries) + columns - 1) // columns

    for row in range(rows):
        ruler(b, -cell * 0.5, -row * cell)

    return (columns * cell, rows * cell, cell), report


def tint_by_vertex_color() -> None:
    """Godot multiplies the glTF vertex colour into the albedo; do the same for the Blender render."""
    for material in bpy.data.materials:
        if not material.use_nodes or "Principled BSDF" not in material.node_tree.nodes:
            continue

        nodes = material.node_tree.nodes
        links = material.node_tree.links
        shader = nodes["Principled BSDF"]
        attribute = nodes.new("ShaderNodeVertexColor")
        attribute.layer_name = "Color"
        multiply = nodes.new("ShaderNodeMix")
        multiply.data_type = "RGBA"
        multiply.blend_type = "MULTIPLY"
        multiply.inputs["Factor"].default_value = 1.0
        base_input = shader.inputs["Base Color"]
        source = base_input.links[0].from_socket if base_input.links else None

        if source:
            links.new(source, multiply.inputs["A"])
        else:
            multiply.inputs["A"].default_value = base_input.default_value

        links.new(attribute.outputs["Color"], multiply.inputs["B"])
        links.new(multiply.outputs["Result"], base_input)


def finish_meshes() -> None:
    for scene_object in bpy.context.scene.objects:
        if scene_object.type != "MESH" or "uv" not in scene_object:
            continue

        map_uvs(scene_object)
        paint_vertex_colors(scene_object)

    tint_by_vertex_color()


def stage(extent: tuple, size: tuple, out: str) -> None:
    width, depth, cell = extent
    scene = bpy.context.scene
    floor = bpy.data.meshes.new("Floor")
    floor.from_pydata([(-cell, cell * 0.5, 0), (width, cell * 0.5, 0), (width, -depth, 0), (-cell, -depth, 0)], [], [(0, 1, 2, 3)])
    floor_object = bpy.data.objects.new("Floor", floor)
    floor_material = bpy.data.materials.new("FloorMat")
    floor_material.diffuse_color = (0.78, 0.74, 0.68, 1.0)
    floor.materials.append(floor_material)
    scene.collection.objects.link(floor_object)

    sun_data = bpy.data.lights.new("Sun", "SUN")
    sun_data.energy = 3.5
    sun_data.angle = math.radians(8.0)
    sun = bpy.data.objects.new("Sun", sun_data)
    sun.rotation_euler = (math.radians(50.0), 0.0, math.radians(-30.0))
    scene.collection.objects.link(sun)

    world = bpy.data.worlds.new("SheetWorld")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.66, 0.78, 0.92, 1.0)
    world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.9
    scene.world = world

    camera_data = bpy.data.cameras.new("SheetCamera")
    camera_data.type = "ORTHO"
    camera_data.ortho_scale = max(width + cell, (depth + cell) * size[0] / size[1] * 0.9)
    camera = bpy.data.objects.new("SheetCamera", camera_data)
    center = Vector(((width - cell) / 2.0, -(depth - cell) / 2.0, 0.6))
    direction = Vector((0.35, -1.0, 0.8)).normalized()
    camera.location = center + direction * 60.0
    camera.rotation_euler = (-direction).to_track_quat("-Z", "Y").to_euler()
    camera_data.clip_end = 200.0
    scene.collection.objects.link(camera)
    scene.camera = camera

    engines = [item.identifier for item in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items]
    scene.render.engine = next(engine for engine in ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT", "BLENDER_WORKBENCH") if engine in engines)
    scene.render.resolution_x, scene.render.resolution_y = size
    scene.render.filepath = out
    scene.view_settings.view_transform = "Standard"
    bpy.ops.render.render(write_still=True)


def main() -> None:
    options = parse_arguments()
    entries = sheet_entries(options["modules"], options["only"])
    b = Builder("PropSheet")
    extent, report = place_entries(b, entries, options["columns"])

    finish_meshes()
    stage(extent, options["size"], options["out"])
    print("\n".join(report))
    print(f"SHEET {options['out']} props={len(entries)}")


main()
