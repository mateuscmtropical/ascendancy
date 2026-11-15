"""Model the town houses (12 archetypes after real vernacular architecture) and the enterable RPG shop buildings.

Outputs, each with a JSON sidecar beside it (AABB in Godot coords, lot size, doors, colour, lights):
  art/town/houses/<archetype>_w<width>_<variant>.gltf
  art/town/shops/shop_<type>.gltf

Blender coords: the lot front line is the plane Y = 0 and the street is toward -Y (Godot +Z after export);
width along X centred on 0, depth toward +Y, origin on the ground. The body is the lot minus 0.15 m on
each side; nothing passes x = +-(lot / 2 - 0.02). Toward the street things may hang out up to 1.2 m.

Shells are boxes and prisms wearing the Medieval Village MegaKit textures (world-planar UVs, colour by
vertex, so one material serves every plaster colour); kit pieces are grafted in only as doors, shutters
and vines. Shop ground floors are real rooms: 0.3 m walls with inner faces, ceiling at 3.6 m, a 1.6 x 2.5 m
door with the floor flush to the pavement, every wall its own box collider (*-colonly).

Usage:
  blender -b --factory-startup -P tools_src/build_town_houses.py -- [model_name ...]
"""

import json
import math
import random
import sys
from pathlib import Path

import bmesh
import bpy
import numpy
from mathutils import Matrix, Vector

PROJECT_DIR = Path(__file__).resolve().parent.parent
KIT_DIR = PROJECT_DIR / "tools" / "vendor" / "village" / "Medieval Village MegaKit[Standard]" / "glTF"
PROPS_KIT_DIR = PROJECT_DIR / "tools" / "vendor" / "props" / "Exports" / "glTF"
TEXTURE_DIR = PROJECT_DIR / "art" / "town" / "textures"
PROPS_TEXTURE_DIR = PROJECT_DIR / "art" / "props"
HOUSE_DIR = PROJECT_DIR / "art" / "town" / "houses"
SHOP_DIR = PROJECT_DIR / "art" / "town" / "shops"

SIDE_MARGIN = 0.15
LOT_EDGE_CLEARANCE = 0.02
STREET_OVERHANG = 1.2
WALL = 0.3
SHOP_CEILING = 3.6
SHOP_GROUND_STOREY = 4.0
SHOP_DOOR = (1.6, 2.5)


def srgb(hex_color: str) -> tuple:
    """Palette colours are written as sRGB hex; vertex colours and material factors are linear."""
    return tuple((int(hex_color[index:index + 2], 16) / 255.0) ** 2.2 for index in (0, 2, 4))


WHITE = (1.0, 1.0, 1.0)
PLASTERS = {
    "cal": "F4EFE6", "creme": "F2E6CF", "ocre": "E3B76A", "rosa": "D99A84", "azul": "9FB6C9", "salvia": "A9C19A",
    "amarelo": "EFD08A", "terra": "C98A6A", "lilas": "C9B6D9",
}
ACCENTS = {"azul": "3E6A9A", "verde": "2F6B4F", "vinho": "7A2F3A", "amarelo": "D9A441", "oxido": "B5533F"}
ROOFS = {"terracota": "D0745A", "velha": "9A5A48", "clara": "E59A78"}
STONE = {"clara": "E9DCC6", "media": "C9BBA2", "dourada": "D9C08A", "cinza": "B4ADA6", "caiada": "F2EEE6"}
BRICK = {"vermelho": "B45A44", "escuro": "8E3E30", "claro": "D9A07E", "tudor": "A85A45"}
WOOD = {"escura": "5A3A26", "media": "8B5A3C", "mel": "C08A55", "roxa": "4A3A5E", "cinza": "8C8378"}
IRON = "2E2A2C"

# Texture atlases: band (v from, v to) of the strip a box face maps onto.
WOOD_DARK_BAND = (0.42, 0.67)
WOOD_LIGHT_BAND = (0.72, 0.98)
TRIM_SMOOTH_BAND = (0.44, 0.66)
TRIM_BLOCK_BAND = (0.72, 0.98)


# ---------- textures and materials ----------

def neutral_texture(source_name: str, target_name: str, mean: float, contrast: float) -> Path:
    """Desaturated, brightened copy of a kit texture so vertex colour can paint it any hue."""
    target = TEXTURE_DIR / f"{target_name}.png"

    if target.exists():
        return target

    source = bpy.data.images.load(str(TEXTURE_DIR / f"{source_name}.png"))
    source.scale(1024, 1024)
    pixels = numpy.array(source.pixels[:]).reshape(1024, 1024, 4)
    luminance = pixels[..., :3] @ numpy.array([0.3, 0.59, 0.11])
    value = numpy.clip(mean + (luminance - luminance.mean()) * contrast, 0.0, 1.0)
    rgba = numpy.stack([value, value * 0.99, value * 0.97, numpy.ones_like(value)], axis=-1)
    image = bpy.data.images.new(target_name, 1024, 1024, alpha=False)

    image.pixels.foreach_set(rgba.astype(numpy.float32).ravel())
    image.filepath_raw = str(target)
    image.file_format = "PNG"
    image.save()

    return target


def load_image(path: Path, is_color: bool):
    image = bpy.data.images.load(str(path), check_existing=True)
    image.colorspace_settings.name = "sRGB" if is_color else "Non-Color"

    return image


def textured_material(name: str, base: Path, normal: Path = None, roughness: float = 0.85, metallic: float = 0.0):
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    shader = nodes["Principled BSDF"]
    base_node = nodes.new("ShaderNodeTexImage")

    base_node.image = load_image(base, True)
    links.new(base_node.outputs["Color"], shader.inputs["Base Color"])
    shader.inputs["Roughness"].default_value = roughness
    shader.inputs["Metallic"].default_value = metallic

    if normal:
        normal_texture = nodes.new("ShaderNodeTexImage")
        normal_map = nodes.new("ShaderNodeNormalMap")
        normal_texture.image = load_image(normal, False)
        links.new(normal_texture.outputs["Color"], normal_map.inputs["Color"])
        links.new(normal_map.outputs["Normal"], shader.inputs["Normal"])

    return material


def plain_material(name: str, color: tuple, roughness: float, metallic: float = 0.0, emission: float = 0.0, alpha: float = 1.0):
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    shader = material.node_tree.nodes["Principled BSDF"]
    shader.inputs["Base Color"].default_value = (*color, 1.0)
    shader.inputs["Roughness"].default_value = roughness
    shader.inputs["Metallic"].default_value = metallic

    if emission > 0.0:
        shader.inputs["Emission Color"].default_value = (*color, 1.0)
        shader.inputs["Emission Strength"].default_value = emission

    if alpha < 1.0:
        shader.inputs["Alpha"].default_value = alpha
        material.surface_render_method = "BLENDED"

    return material


GLOWS = {  # key -> (sRGB colour, strength)
    "glow_warm": ("FFD9A0", 2.2),
    "glow_ember": ("FF7A2A", 3.0),
    "glow_cyan": ("8FD8FF", 2.2),
    "glow_pink": ("F59AD8", 2.0),
    "glow_green": ("7FE08A", 2.2),
    "glow_amber": ("FFB347", 1.8),
}


def build_materials() -> dict:
    plaster = neutral_texture("T_Plaster_BaseColor", "T_TownPlaster_BaseColor", 0.9, 0.8)
    stone = neutral_texture("T_UnevenBrick_BaseColor", "T_TownStone_BaseColor", 0.78, 1.1)
    brick = neutral_texture("T_Brick_BaseColor", "T_TownBrick_BaseColor", 0.8, 1.2)
    materials = {
        "plaster": textured_material("M_TownPlaster", plaster, TEXTURE_DIR / "T_Plaster_Normal.png", 0.95),
        "stone": textured_material("M_TownStone", stone, TEXTURE_DIR / "T_UnevenBrick_Normal.png", 0.9),
        "brick": textured_material("M_TownBrick", brick, TEXTURE_DIR / "T_Brick_Normal.png", 0.9),
        "trim": textured_material("M_TownTrim", TEXTURE_DIR / "T_RockTrim_BaseColor.png", TEXTURE_DIR / "T_RockTrim_Normal.png", 0.85),
        "wood": textured_material("M_TownWood", TEXTURE_DIR / "T_WoodTrim_BaseColor.png", TEXTURE_DIR / "T_WoodTrim_Normal.png", 0.8),
        "tiles": textured_material("M_TownTiles", TEXTURE_DIR / "T_RoundTiles_BaseColor.png", TEXTURE_DIR / "T_RoundTiles_Normal.png", 0.8),
        "slate": textured_material("M_TownSlate", TEXTURE_DIR / "T_SlateTiles_BaseColor.png", TEXTURE_DIR / "T_RoundTiles_Normal.png", 0.7),
        "glass": plain_material("M_TownGlass", srgb("3A4E66"), 0.12, 0.4),
        "vitrine": plain_material("M_TownVitrine", srgb("BFD8E8"), 0.05, 0.0, alpha=0.25),
        "paint": plain_material("M_TownPaint", WHITE, 0.75),
        "metal": plain_material("M_TownMetal", WHITE, 0.45, 0.7),
        "water": plain_material("M_Water", srgb("3C7FA0"), 0.1),
    }

    for key, (color, strength) in GLOWS.items():
        materials[key] = plain_material(f"M_Town{key.title().replace('_', '')}", srgb(color), 0.4, emission=strength)

    return materials


WORLD_TILE = {"plaster": 3.0, "stone": 2.4, "brick": 1.6, "tiles": 1.8, "slate": 1.8, "glass": 2.0, "vitrine": 2.0, "paint": 1.0, "metal": 1.0, "water": 2.0}


# ---------- geometry ----------

def box_bmesh(minimum: tuple, maximum: tuple):
    box = bmesh.new()
    bmesh.ops.create_cube(box, size=1.0)
    bmesh.ops.scale(box, vec=[high - low for low, high in zip(minimum, maximum)], verts=box.verts)
    bmesh.ops.translate(box, vec=[(low + high) / 2.0 for low, high in zip(minimum, maximum)], verts=box.verts)

    return box


def frame_at(u: float, d: float, degrees: float) -> Matrix:
    return Matrix.Translation((u, d, 0.0)) @ Matrix.Rotation(math.radians(degrees), 4, "Z")


class Opening:
    """A hole in a facade, in facade coords (u along the wall seen from outside, z up).

    top: flat | round | segment | pointed | circle. height is to the apex."""

    def __init__(self, u: float, width: float, bottom: float, height: float, top: str = "flat", kind: str = "window", **style) -> None:
        self.u, self.width, self.bottom, self.height, self.top, self.kind, self.style = u, width, bottom, height, top, kind, style

    @property
    def apex(self) -> float:
        return self.bottom + self.height

    @property
    def spring(self) -> float:
        rises = {"flat": 0.0, "round": self.width / 2.0, "segment": self.width * 0.18, "pointed": self.width * POINTED_RISE, "circle": self.height}

        return self.apex - rises[self.top]

    def arc(self, expand: float = 0.0, segments: int = 10) -> list:
        """Points of the top edge from right to left, grown by expand."""
        half = self.width / 2.0 + expand
        spring = self.spring
        apex = self.apex + expand

        if self.top == "flat":
            return [(self.u + half, apex), (self.u - half, apex)]

        if self.top in ("round", "circle"):
            radius = half if self.top == "round" else self.height / 2.0 + expand
            center = spring if self.top == "round" else self.bottom + self.height / 2.0

            return [(self.u + radius * math.cos(math.pi * step / segments), center + radius * math.sin(math.pi * step / segments)) for step in range(segments + 1)]

        if self.top == "segment":
            rise = apex - spring
            radius = (half * half + rise * rise) / (2.0 * rise)
            half_angle = math.asin(half / radius)
            angles = [math.pi / 2.0 - half_angle + 2.0 * half_angle * step / segments for step in range(segments + 1)]

            return [(self.u + radius * math.cos(angle), apex - radius + radius * math.sin(angle)) for angle in angles]

        radius = 2.0 * half * POINTED_RADIUS
        right_center = self.u + half - radius
        top_angle = math.acos((radius - half) / radius)
        right = [(right_center + radius * math.cos(top_angle * step / (segments // 2)), spring + radius * math.sin(top_angle * step / (segments // 2))) for step in range(segments // 2 + 1)]

        return right + [(2.0 * self.u - u, z) for u, z in reversed(right[:-1])]

    def outline(self, expand: float = 0.0) -> list:
        """Closed polygon, counter-clockwise, starting at the bottom left corner (circles: at the right)."""
        half = self.width / 2.0 + expand
        arc = self.arc(expand)

        if self.top == "circle":
            center = self.bottom + self.height / 2.0

            return arc + [(2.0 * self.u - u, 2.0 * center - z) for u, z in arc[1:-1]]

        return [(self.u - half, self.bottom - expand), (self.u + half, self.bottom - expand)] + arc


class Builder:
    """Collects the pieces of one building; finish() maps UVs, paints vertex colours and joins them."""

    def __init__(self, name: str) -> None:
        bpy.ops.wm.read_factory_settings(use_empty=True)
        self.name = name
        self.materials = build_materials()
        self.library = {}
        self.count = 0
        self.lights = []
        self.markers = {}

    # -- low level --

    def _link(self, mesh_bmesh, material_key: str, tint: tuple, uv: tuple, transform: Matrix):
        bmesh.ops.transform(mesh_bmesh, matrix=transform, verts=mesh_bmesh.verts)
        bmesh.ops.recalc_face_normals(mesh_bmesh, faces=mesh_bmesh.faces)
        self.count += 1
        mesh_data = bpy.data.meshes.new(f"P{self.count}")
        mesh_bmesh.to_mesh(mesh_data)
        mesh_bmesh.free()
        mesh_object = bpy.data.objects.new(f"P{self.count}", mesh_data)
        bpy.context.scene.collection.objects.link(mesh_object)
        mesh_data.materials.append(self.materials[material_key])
        mesh_object["tint"] = tint
        mesh_object["uv"] = uv or ("world", WORLD_TILE.get(material_key, 2.0))

        return mesh_object

    def box(self, minimum: tuple, maximum: tuple, material_key: str, tint: tuple = WHITE, frame: Matrix = None, uv: tuple = None):
        if any(high - low < 1e-4 for low, high in zip(minimum, maximum)):
            return None

        return self._link(box_bmesh(minimum, maximum), material_key, tint, uv, frame or Matrix.Identity(4))

    def beam(self, start: tuple, end: tuple, width: float, depth: float, material_key: str, tint: tuple, frame: Matrix = None, uv: tuple = ("band", *WOOD_DARK_BAND, 1.5)):
        """Box from start to end (facade coords u, d, z), width across in the facade plane, depth along d."""
        start_vector, end_vector = Vector(start), Vector(end)
        axis = end_vector - start_vector
        length = axis.length
        along = axis.normalized()
        normal = Vector((0.0, 1.0, 0.0)) if abs(along.y) < 0.9 else Vector((1.0, 0.0, 0.0))
        across = along.cross(normal).normalized()
        normal = across.cross(along).normalized()
        basis = Matrix((along, normal, across)).transposed().to_4x4()
        placed = Matrix.Translation((start_vector + end_vector) / 2.0) @ basis
        beam_bmesh = box_bmesh((-length / 2.0, -depth / 2.0, -width / 2.0), (length / 2.0, depth / 2.0, width / 2.0))

        return self._link(beam_bmesh, material_key, tint, uv, (frame or Matrix.Identity(4)) @ placed)

    def prism(self, profile: list, depth_from: float, depth_to: float, material_key: str, tint: tuple = WHITE, frame: Matrix = None, uv: tuple = None):
        """Polygon in the facade plane (u, z), extruded from d = depth_from to depth_to."""
        prism_bmesh = bmesh.new()
        face = prism_bmesh.faces.new([prism_bmesh.verts.new((u, depth_from, z)) for u, z in profile])
        extruded = bmesh.ops.extrude_face_region(prism_bmesh, geom=[face])
        moved = [element for element in extruded["geom"] if isinstance(element, bmesh.types.BMVert)]
        bmesh.ops.translate(prism_bmesh, vec=(0.0, depth_to - depth_from, 0.0), verts=moved)

        return self._link(prism_bmesh, material_key, tint, uv, frame or Matrix.Identity(4))

    def side_prism(self, profile: list, u_from: float, u_to: float, material_key: str, tint: tuple = WHITE, frame: Matrix = None, uv: tuple = None):
        """Polygon in the (d, z) plane extruded along u: cornices, slabs and roof sections."""
        swap = Matrix(((0, 0, 1, 0), (1, 0, 0, 0), (0, 1, 0, 0), (0, 0, 0, 1)))
        prism_bmesh = bmesh.new()
        face = prism_bmesh.faces.new([prism_bmesh.verts.new((d, z, u_from)) for d, z in profile])
        extruded = bmesh.ops.extrude_face_region(prism_bmesh, geom=[face])
        moved = [element for element in extruded["geom"] if isinstance(element, bmesh.types.BMVert)]
        bmesh.ops.translate(prism_bmesh, vec=(0.0, 0.0, u_to - u_from), verts=moved)
        bmesh.ops.transform(prism_bmesh, matrix=swap, verts=prism_bmesh.verts)

        return self._link(prism_bmesh, material_key, tint, uv, frame or Matrix.Identity(4))

    def hull(self, points: list, material_key: str, tint: tuple = WHITE, frame: Matrix = None, uv: tuple = None):
        hull_bmesh = bmesh.new()
        vertices = [hull_bmesh.verts.new(point) for point in points]
        result = bmesh.ops.convex_hull(hull_bmesh, input=vertices)
        bmesh.ops.delete(hull_bmesh, geom=result["geom_interior"] + result["geom_unused"], context="VERTS")

        return self._link(hull_bmesh, material_key, tint, uv, frame or Matrix.Identity(4))

    def cylinder(self, base: tuple, radius: float, height: float, sides: int, material_key: str, tint: tuple = WHITE, top_radius: float = None, frame: Matrix = None, uv: tuple = None, axis: str = "Z"):
        cylinder_bmesh = bmesh.new()
        bmesh.ops.create_cone(cylinder_bmesh, cap_ends=True, segments=sides, radius1=radius, radius2=radius if top_radius is None else top_radius, depth=height)
        bmesh.ops.translate(cylinder_bmesh, vec=(0.0, 0.0, height / 2.0), verts=cylinder_bmesh.verts)
        turn = {"Z": Matrix.Identity(4), "X": Matrix.Rotation(math.pi / 2.0, 4, "Y"), "Y": Matrix.Rotation(-math.pi / 2.0, 4, "X")}[axis]

        return self._link(cylinder_bmesh, material_key, tint, uv, (frame or Matrix.Identity(4)) @ Matrix.Translation(base) @ turn)

    def sphere(self, center: tuple, radius: float, material_key: str, tint: tuple = WHITE, scale: tuple = (1.0, 1.0, 1.0), frame: Matrix = None, segments: int = 10):
        sphere_bmesh = bmesh.new()
        bmesh.ops.create_uvsphere(sphere_bmesh, u_segments=segments, v_segments=max(4, segments // 2 + 1), radius=radius)
        bmesh.ops.scale(sphere_bmesh, vec=scale, verts=sphere_bmesh.verts)

        return self._link(sphere_bmesh, material_key, tint, None, (frame or Matrix.Identity(4)) @ Matrix.Translation(center))

    def collider(self, minimum: tuple, maximum: tuple, frame: Matrix = None) -> None:
        self.count += 1
        collider_bmesh = box_bmesh(minimum, maximum)
        bmesh.ops.transform(collider_bmesh, matrix=frame or Matrix.Identity(4), verts=collider_bmesh.verts)
        mesh_data = bpy.data.meshes.new(f"Collider{self.count}-colonly")
        collider_bmesh.to_mesh(mesh_data)
        collider_bmesh.free()
        bpy.context.scene.collection.objects.link(bpy.data.objects.new(f"Collider{self.count}-colonly", mesh_data))

    def light(self, position: tuple, color: str, energy: float, light_range: float = 7.0, frame: Matrix = None) -> None:
        world = (frame or Matrix.Identity(4)) @ Vector(position)
        self.lights.append({"position": blender_to_godot(world), "color": color, "energy": energy, "range": light_range})

    def marker(self, name: str, position: tuple, frame: Matrix = None) -> None:
        self.markers[name] = blender_to_godot((frame or Matrix.Identity(4)) @ Vector(position))

    # -- kit grafts --

    def kit(self, piece: str, location: tuple, degrees: float = 0.0, scale: tuple = (1.0, 1.0, 1.0), tints: dict = None, frame: Matrix = None, props: bool = False):
        """Copy of a kit piece (imported once per building), placed in facade coords; tints by material name prefix."""
        if piece not in self.library:
            self.library[piece] = import_kit_piece(piece, PROPS_KIT_DIR if props else KIT_DIR)

        placed = (frame or Matrix.Identity(4)) @ Matrix.Translation(location) @ Matrix.Rotation(math.radians(degrees), 4, "Z") @ Matrix.Diagonal((*scale, 1.0))
        copies = []

        for template, template_matrix in self.library[piece]:
            copy = bpy.data.objects.new(f"K{self.count}", template.data.copy())
            self.count += 1
            copy.data.transform(placed @ template_matrix)

            if scale[0] * scale[1] * scale[2] < 0.0:
                copy.data.flip_normals()

            bpy.context.scene.collection.objects.link(copy)
            copy["uv"] = ("keep",)
            copy["tints"] = json.dumps({prefix: list(color) for prefix, color in (tints or {}).items()})
            copies.append(copy)

        return copies

    # -- finish --

    def finish(self, output_path: Path, sidecar: dict) -> dict:
        visible = [scene_object for scene_object in bpy.context.scene.objects if scene_object.type == "MESH" and not scene_object.name.endswith("-colonly")]
        colliders = [scene_object for scene_object in bpy.context.scene.objects if scene_object.name.endswith("-colonly")]

        for mesh_object in visible:
            map_uvs(mesh_object)
            paint_vertex_colors(mesh_object)

        unify_materials(visible)

        with bpy.context.temp_override(active_object=visible[0], selected_editable_objects=visible):
            bpy.ops.object.join()

        building = visible[0]
        building.name = self.name
        corners = [vertex.co for vertex in building.data.vertices] + [vertex.co for collider in colliders for vertex in collider.data.vertices]
        minimum = [min(corner[axis] for corner in corners) for axis in range(3)]
        maximum = [max(corner[axis] for corner in corners) for axis in range(3)]
        godot_minimum = [minimum[0], minimum[2], -maximum[1]]
        godot_maximum = [maximum[0], maximum[2], -minimum[1]]

        for template_objects in self.library.values():
            for template, _matrix in template_objects:
                bpy.data.objects.remove(template, do_unlink=True)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        bpy.ops.export_scene.gltf(
            filepath=str(output_path),
            export_format="GLTF_SEPARATE",
            export_yup=True,
            export_keep_originals=True,
            export_vertex_color="ACTIVE",
            export_active_vertex_color_when_no_material=True,
            use_visible=True,
        )

        sidecar = {
            "aabb_min": [round(value, 3) for value in godot_minimum],
            "aabb_max": [round(value, 3) for value in godot_maximum],
            **sidecar,
            "lights": self.lights,
            "markers": self.markers,
        }
        output_path.with_suffix(".json").write_text(json.dumps(sidecar, indent=1), encoding="utf-8", newline="\n")

        return sidecar


def blender_to_godot(point) -> list:
    return [round(point[0], 3), round(point[2], 3), round(-point[1], 3)]


def import_kit_piece(piece: str, directory: Path) -> list:
    """Import a kit glTF, keep its meshes hidden as templates, point its images at the project copies."""
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(directory / f"{piece}.gltf"))
    bpy.context.view_layer.update()
    templates = []

    for scene_object in set(bpy.data.objects) - before:
        if scene_object.type == "MESH":
            templates.append((scene_object, scene_object.matrix_world.copy()))
            bpy.context.scene.collection.objects.unlink(scene_object) if scene_object.name in bpy.context.scene.collection.objects else None

            for collection in list(scene_object.users_collection):
                collection.objects.unlink(scene_object)
        else:
            bpy.data.objects.remove(scene_object, do_unlink=True)

    relink_images()

    return templates


def relink_images() -> None:
    """Kit images live in tools/vendor (outside the project): point each at its copy under art/."""
    for image in bpy.data.images:
        if not image.filepath or image.get("relinked"):
            continue

        file_name = Path(bpy.path.abspath(image.filepath)).name
        candidates = [PROPS_TEXTURE_DIR / file_name, TEXTURE_DIR / file_name]
        target = next((candidate for candidate in candidates if candidate.exists()), None)

        if target is None:
            target = TEXTURE_DIR / file_name
            target.write_bytes(Path(bpy.path.abspath(image.filepath)).read_bytes())

        image.filepath = str(target)
        image["relinked"] = True


def unify_materials(objects: list) -> None:
    """Every kit import brings its own copy of MI_WoodTrim etc.: point all users at one copy."""
    by_name = {}

    for mesh_object in objects:
        for slot in mesh_object.material_slots:
            base_name = slot.material.name.split(".")[0]
            slot.material = by_name.setdefault(base_name, slot.material)


def face_frame(face):
    horizontal = face.normal.cross(Vector((0.0, 0.0, 1.0)))

    if horizontal.length > 0.01:
        u_axis = horizontal.normalized()
        v_axis = face.normal.cross(u_axis).normalized()
    else:
        u_axis, v_axis = Vector((1.0, 0.0, 0.0)), Vector((0.0, 1.0, 0.0))

    return u_axis, v_axis


def map_uvs(mesh_object) -> None:
    """world: planar UVs per face in metres / tile. band: long side of each face runs along U, the short
    side spans one strip of a trim atlas (wood planks, stone moulding)."""
    mode, *parameters = mesh_object["uv"]

    if mode == "keep":
        return

    uv_bmesh = bmesh.new()
    uv_bmesh.from_mesh(mesh_object.data)
    uv_layer = uv_bmesh.loops.layers.uv.verify()

    for face in uv_bmesh.faces:
        u_axis, v_axis = face_frame(face)
        planar = [(loop.vert.co.dot(u_axis), loop.vert.co.dot(v_axis)) for loop in face.loops]

        if mode == "world":
            uvs = [(u / parameters[0], v / parameters[0]) for u, v in planar]
        else:
            band_from, band_to, meters = parameters
            u_values, v_values = [u for u, _ in planar], [v for _, v in planar]
            is_tall = max(v_values) - min(v_values) > max(u_values) - min(u_values)
            along, across = (v_values, u_values) if is_tall else (u_values, v_values)
            low, span = min(across), max(1e-4, max(across) - min(across))
            uvs = [(value / meters, band_from + (cross - low) / span * (band_to - band_from)) for value, cross in zip(along, across)]

        for loop, uv in zip(face.loops, uvs):
            loop[uv_layer].uv = uv

    uv_bmesh.to_mesh(mesh_object.data)
    uv_bmesh.free()


def paint_vertex_colors(mesh_object) -> None:
    tint = tuple(mesh_object.get("tint", WHITE))
    tints = json.loads(mesh_object.get("tints", "{}"))
    layer = mesh_object.data.color_attributes.new("Color", "FLOAT_COLOR", "CORNER")
    slot_colors = [next((tuple(color) for prefix, color in tints.items() if slot.material.name.startswith(prefix)), tint) for slot in mesh_object.material_slots]
    colors = numpy.ones((len(mesh_object.data.loops), 4), dtype=numpy.float32)

    for polygon in mesh_object.data.polygons:
        colors[polygon.loop_start:polygon.loop_start + polygon.loop_total, :3] = slot_colors[polygon.material_index] if slot_colors else tint

    layer.data.foreach_set("color", colors.ravel())
    mesh_object.data.color_attributes.active_color = layer
    mesh_object.data.color_attributes.render_color_index = mesh_object.data.color_attributes.find("Color")
