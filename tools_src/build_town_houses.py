"""Model the town houses (12 archetypes after vernacular architecture). The big walk-in shops of the market
squares are built on top of this module by build_market_shops.py.

Outputs, each with a JSON sidecar beside it (AABB in Godot coords, lot size, doors, colour, lights):
  art/town/houses/<archetype>_w<width>_<variant>.gltf

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

import contextlib
import hashlib
import itertools
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
FLOOR_BOARD_WIDTH = 0.4  # piso das lojas em tábuas: cada uma ocupa uma faixa do atlas de madeira
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
        "shopfront": plain_material("M_TownShopfront", srgb("BFD8E8"), 0.05, 0.0, alpha=0.25),  # vitrine da loja: acende à noite (features/sky/window_glass.gd)
        "inner_glass": plain_material("M_TownInnerGlass", srgb("1A2A44"), 0.1, alpha=0.3),  # vidro de dentro das janelas do casarão: escuro à noite (features/sky/window_glass.gd)
        "paint": plain_material("M_TownPaint", WHITE, 0.75),
        "metal": plain_material("M_TownMetal", WHITE, 0.45, 0.7),
        "water": plain_material("M_Water", srgb("3C7FA0"), 0.1),
    }

    for key, (color, strength) in GLOWS.items():
        materials[key] = plain_material(f"M_Town{key.title().replace('_', '')}", srgb(color), 0.4, emission=strength)

    return materials


WORLD_TILE = {"plaster": 3.0, "stone": 2.4, "brick": 1.6, "tiles": 1.8, "slate": 1.8, "glass": 2.0, "vitrine": 2.0, "shopfront": 2.0, "paint": 1.0, "metal": 1.0, "water": 2.0}


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
        self.turning_parts = {}

    # -- low level --

    def _link(self, mesh_bmesh, material_key: str, tint: tuple, uv: tuple, transform: Matrix, recalc_normals: bool = True):
        bmesh.ops.transform(mesh_bmesh, matrix=transform, verts=mesh_bmesh.verts)

        if recalc_normals:
            bmesh.ops.recalc_face_normals(mesh_bmesh, faces=mesh_bmesh.faces)

        self.count += 1
        mesh_data = bpy.data.meshes.new(f"P{self.count}")
        mesh_bmesh.to_mesh(mesh_data)
        mesh_bmesh.free()
        mesh_object = bpy.data.objects.new(f"P{self.count}", mesh_data)
        bpy.context.scene.collection.objects.link(mesh_object)
        mesh_data.materials.append(self.materials[material_key])
        mesh_object["tint"] = tint
        mesh_object["uv"] = json.dumps(uv or ("world", WORLD_TILE.get(material_key, 2.0)))

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

    def pane(self, profile: list, depth: float, material_key: str, tint: tuple = WHITE, frame: Matrix = None, facing: int = 1):
        """One single-sided polygon in the facade plane (u, z) at d = depth, its face toward +d (facing 1: into the
        building, seen from inside only by a back-culling material) or -d (facing -1)."""
        pane_bmesh = bmesh.new()
        points = profile if facing < 0 else list(reversed(profile))
        pane_bmesh.faces.new([pane_bmesh.verts.new((u, depth, z)) for u, z in points])

        return self._link(pane_bmesh, material_key, tint, None, frame or Matrix.Identity(4), recalc_normals=False)

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

    def collider(self, minimum: tuple, maximum: tuple, frame: Matrix = None, name: str = "Collider") -> None:
        """Static collision box. The name prefix tells the import which ground it is for footsteps ("WoodFloor")."""
        self.count += 1
        collider_bmesh = box_bmesh(minimum, maximum)
        bmesh.ops.transform(collider_bmesh, matrix=frame or Matrix.Identity(4), verts=collider_bmesh.verts)
        mesh_data = bpy.data.meshes.new(f"{name}{self.count}-colonly")
        collider_bmesh.to_mesh(mesh_data)
        collider_bmesh.free()
        bpy.context.scene.collection.objects.link(bpy.data.objects.new(f"{name}{self.count}-colonly", mesh_data))

    def light(self, position: tuple, color: str, energy: float, light_range: float = 7.0, frame: Matrix = None, group: str = "") -> None:
        """group: Godot group of the light node (day_lights lamps are on by day only, see features/sky/day_night_cycle.gd)."""
        world = (frame or Matrix.Identity(4)) @ Vector(position)
        self.lights.append({"position": blender_to_godot(world), "color": color, "energy": energy, "range": light_range, **({"group": group} if group else {})})

    def marker(self, name: str, position: tuple, frame: Matrix = None) -> None:
        self.markers[name] = blender_to_godot((frame or Matrix.Identity(4)) @ Vector(position))

    @contextlib.contextmanager
    def turning_part(self, name: str, axle: tuple, frame: Matrix = None):
        """Pieces made inside the block leave finish() as ONE mesh called `name` whose origin sits on `axle` (facade
        coords), so the game can spin it around the axle (the wheels of a wagon)."""
        before = set(bpy.data.objects)

        yield

        for index, piece in enumerate(sorted(set(bpy.data.objects) - before, key=lambda candidate: candidate.name)):
            piece.name = f"{name}_{index}"

        self.turning_parts[name] = (frame or Matrix.Identity(4)) @ Vector(axle)

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
            copy["uv"] = json.dumps(("keep",))
            copy["tints"] = json.dumps({prefix: list(color) for prefix, color in (tints or {}).items()})
            copies.append(copy)

        return copies

    # -- finish --

    def finish(self, output_path: Path, sidecar: dict, separate: tuple = ()) -> dict:
        """Join every visible part into one mesh and export. Parts whose name starts with a `separate` prefix stay
        objects of their own (the scene gives them a visibility range: the crops of one plot)."""
        everything = [scene_object for scene_object in bpy.context.scene.objects if scene_object.type == "MESH" and not scene_object.name.endswith("-colonly")]
        colliders = [scene_object for scene_object in bpy.context.scene.objects if scene_object.name.endswith("-colonly")]

        for mesh_object in everything:
            strip_extra_layers(mesh_object)
            map_uvs(mesh_object)
            paint_vertex_colors(mesh_object)

        unify_materials(everything)
        apart = [scene_object for scene_object in everything if separate and scene_object.name.startswith(separate)]
        turning = {name: [part for part in everything if part.name.startswith(f"{name}_")] for name in self.turning_parts}
        loose = {part for parts in turning.values() for part in parts}
        visible = untinted_first([scene_object for scene_object in everything if scene_object not in apart and scene_object not in loose])

        with bpy.context.temp_override(active_object=visible[0], selected_editable_objects=visible):
            bpy.ops.object.join()

        building = visible[0]
        building.name = self.name
        turned = [self.join_turning_part(name, parts) for name, parts in turning.items()]
        corners = [vertex.co for part in [building, *apart, *turned, *colliders] for vertex in part.data.vertices]
        minimum = [min(corner[axis] for corner in corners) for axis in range(3)]
        maximum = [max(corner[axis] for corner in corners) for axis in range(3)]
        godot_minimum = [minimum[0], minimum[2], -maximum[1]]
        godot_maximum = [maximum[0], maximum[2], -minimum[1]]

        for template_objects in self.library.values():
            for template, _matrix in template_objects:
                bpy.data.objects.remove(template, do_unlink=True)

        for wheel in turned:
            axle = self.turning_parts[wheel.name]

            wheel.data.transform(Matrix.Translation(-axle))
            wheel.location = axle

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
        stamp_buffer_hash(output_path)

        sidecar = {
            "aabb_min": [round(value, 3) for value in godot_minimum],
            "aabb_max": [round(value, 3) for value in godot_maximum],
            **sidecar,
            "lights": self.lights,
            "markers": self.markers,
        }
        output_path.with_suffix(".json").write_text(json.dumps(sidecar, indent=1), encoding="utf-8", newline="\n")

        return sidecar

    def join_turning_part(self, name: str, parts: list):
        """The pieces of one turning part as a single object (the origin moves to the axle just before export)."""
        ordered = untinted_first(parts)

        with bpy.context.temp_override(active_object=ordered[0], selected_editable_objects=ordered):
            bpy.ops.object.join()

        ordered[0].name = name

        return ordered[0]


def stamp_buffer_hash(gltf_path: Path) -> None:
    """Write the hash of the .bin into the .gltf: Godot only reimports when the .gltf text changes, and a rebuild
    that only moves vertices or UVs changes nothing but the .bin."""
    document = json.loads(gltf_path.read_text(encoding="utf-8"))
    document["asset"]["extras"] = {"buffer_md5": hashlib.md5(gltf_path.with_suffix(".bin").read_bytes()).hexdigest()}
    gltf_path.write_text(json.dumps(document, indent=1), encoding="utf-8", newline="\n")


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
    mode, *parameters = json.loads(mesh_object["uv"])

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


def slot_tints(mesh_object) -> list:
    """Vertex-colour tint of each material slot of the object."""
    tint = tuple(mesh_object.get("tint", WHITE))
    tints = json.loads(mesh_object.get("tints", "{}"))

    return [next((tuple(color) for prefix, color in tints.items() if slot.material.name.startswith(prefix)), tint) for slot in mesh_object.material_slots]


def untinted_first(objects: list) -> list:
    """Godot's glTF import leaves "vertex colour as albedo" off on the material of the first surface, so that material
    shows up white. Lead the join with an object whose first material is never tinted (glow, glass): for it the
    missing flag changes nothing."""
    slots = [(slot.material.name, tint[:3]) for mesh_object in objects for slot, tint in zip(mesh_object.material_slots, slot_tints(mesh_object))]
    tinted = {name for name, tint in slots if tint != WHITE}
    leader = next((mesh_object for mesh_object in objects if mesh_object.material_slots and mesh_object.material_slots[0].material.name not in tinted), None)

    if leader is None:
        print("AVISO sem material neutro para a primeira superfície: o primeiro material vai aparecer sem tinta")

    return sorted(objects, key=lambda mesh_object: mesh_object is not leader)


def strip_extra_layers(mesh_object) -> None:
    """Meshes carved from imported characters bring their own UV sets and colour layers, and the join keeps the union
    of every part's layers (six UV sets and four colour sets per vertex in the cathedral). Keep one UV set and drop
    the colours: paint_vertex_colors writes the tint."""
    mesh = mesh_object.data

    for uv_layer in list(mesh.uv_layers)[1:]:
        mesh.uv_layers.remove(uv_layer)

    for attribute in list(mesh.color_attributes):
        mesh.color_attributes.remove(attribute)


def paint_vertex_colors(mesh_object) -> None:
    tint = tuple(mesh_object.get("tint", WHITE))
    layer = mesh_object.data.color_attributes.new("Color", "FLOAT_COLOR", "CORNER")
    slot_colors = slot_tints(mesh_object)
    colors = numpy.ones((len(mesh_object.data.loops), 4), dtype=numpy.float32)

    for polygon in mesh_object.data.polygons:
        colors[polygon.loop_start:polygon.loop_start + polygon.loop_total, :3] = slot_colors[polygon.material_index] if slot_colors else tint

    layer.data.foreach_set("color", colors.ravel())
    mesh_object.data.color_attributes.active_color = layer
    mesh_object.data.color_attributes.render_color_index = mesh_object.data.color_attributes.find("Color")


# ---------- town plan shared with build_hub_scene.py ----------

sys.path.insert(0, str(Path(__file__).resolve().parent))

from build_hub_scene import ALLEY_WALL_HEIGHT, HOUSE_ARCHETYPES, STREET_GABLE_ARCHETYPES, town_lots  # noqa: E402  (plano puro em Python, sem bpy)

POINTED_RADIUS = 1.0  # arco ogival equilátero: raio = largura do vão
POINTED_RISE = math.sqrt(3.0) / 2.0
WALL_FINISHES = {  # nome de cor do plano -> (material, cor sRGB)
    **{name: ("plaster", hex_value) for name, hex_value in PLASTERS.items()},
    "tijolo": ("brick", BRICK["vermelho"]),
    "tijolo_escuro": ("brick", BRICK["escuro"]),
    "tijolo_claro": ("brick", BRICK["claro"]),
    **{name: ("stone", hex_value) for name, hex_value in STONE.items()},
}
ROOF_FINISHES = {"terracota": ("tiles", ROOFS["terracota"]), "velha": ("tiles", ROOFS["velha"]), "clara": ("tiles", ROOFS["clara"]), "ardosia": ("slate", "7E8AA6"), "madeira": ("slate", "9A948A"), "cobre": ("metal", "5FA08A")}
ACCENT_ORDER = ("azul", "verde", "vinho", "amarelo", "oxido")
FRAME_DEPTH = 0.06
BACK_EAVE_ALLOWANCE = 0.6  # o corpo termina antes do fundo do lote para o beiral de trás caber nele
GLASS_DEPTH = 0.08


class House:
    """Measurements and colours of one building, in facade coords (u across, d into the lot, z up)."""

    def __init__(self, width: float, depth: float, storeys: tuple, wall: str, roof: str, accent: str, seed: int, setback: float = 0.0) -> None:
        self.width = width
        self.depth = depth - BACK_EAVE_ALLOWANCE
        self.storeys = storeys
        self.half = width / 2.0 - SIDE_MARGIN
        self.limit = width / 2.0 - LOT_EDGE_CLEARANCE
        self.levels = [sum(storeys[:index]) for index in range(len(storeys) + 1)]
        self.top = self.levels[-1]
        self.wall_material, wall_hex = WALL_FINISHES[wall]
        self.wall_tint = srgb(wall_hex)
        self.roof_material, roof_hex = ROOF_FINISHES[roof]
        self.roof_tint = srgb(roof_hex)
        self.accent = srgb(ACCENTS[accent])
        self.trim_tint = srgb(STONE["clara"])
        self.wood_tint = srgb(WOOD["escura"])
        self.iron_tint = srgb(IRON)
        self.generator = random.Random(seed)
        self.setback = setback
        self.jetty = 0.0
        self.ground_recess = 0.0
        self.doors = []

    def bays(self, count: int, margin: float = 0.6) -> list:
        """u of count evenly spaced window axes across the facade."""
        span = 2.0 * (self.half - margin)

        return [-self.half + margin + span * (index + 0.5) / count for index in range(count)]


# ---------- facade pieces ----------

def draw_window(b: Builder, house: House, opening: Opening, shutters: bool = False, bars: int = 1, frame_tint: tuple = None, front: float = None) -> None:
    """Window laid on a solid wall: moulded frame, dark glass with glazing bars, stone sill, optional shutters."""
    front = house.setback if front is None else front
    tint = frame_tint or house.trim_tint
    sill_half = opening.width / 2.0 + 0.12

    b.prism(opening.outline(0.1), front - FRAME_DEPTH, front, "trim", tint, uv=("band", *TRIM_SMOOTH_BAND, 1.0))
    b.prism(opening.outline(), front - GLASS_DEPTH, front - FRAME_DEPTH, "glass")
    b.box((opening.u - sill_half, front - 0.16, opening.bottom - 0.1), (opening.u + sill_half, front, opening.bottom - 0.02), "trim", tint)

    for bar_index in range(bars):
        bar_z = opening.bottom + opening.height * (bar_index + 1) / (bars + 1)
        b.box((opening.u - opening.width / 2.0, front - GLASS_DEPTH - 0.02, bar_z - 0.02), (opening.u + opening.width / 2.0, front - GLASS_DEPTH, bar_z + 0.02), "paint", WHITE)

    b.box((opening.u - 0.02, front - GLASS_DEPTH - 0.02, opening.bottom), (opening.u + 0.02, front - GLASS_DEPTH, opening.spring), "paint", WHITE)

    if shutters:
        for side_sign in (-1, 1):
            shutter_u = opening.u + side_sign * (opening.width * 0.75 + 0.12)
            b.box((shutter_u - opening.width / 4.0, front - 0.1, opening.bottom), (shutter_u + opening.width / 4.0, front - 0.04, opening.spring), "paint", house.accent)


def draw_door(b: Builder, house: House, u: float, width: float, height: float, top: str = "flat", double: bool = False, front: float = None) -> None:
    """Closed front door (houses are not enterable): frame, panelled leaf, threshold."""
    front = house.setback if front is None else front
    door = Opening(u, width, 0.0, height, top, kind="door")

    b.prism(door.outline(0.14), front - FRAME_DEPTH, front, "trim", house.trim_tint, uv=("band", *TRIM_BLOCK_BAND, 1.0))
    b.prism(door.outline(), front - 0.1, front - FRAME_DEPTH, "paint", house.accent)
    b.box((u - width / 2.0 - 0.1, front - 0.3, 0.0), (u + width / 2.0 + 0.1, front, 0.04), "trim", house.trim_tint)

    if double:
        b.box((u - 0.015, front - 0.12, 0.05), (u + 0.015, front - 0.1, door.spring), "paint", house.wood_tint)

    b.sphere((u + width * 0.3, front - 0.13, 1.05), 0.035, "metal", srgb("C9A24A"))
    house.doors.append({"x": round(u, 3), "width": width, "enterable": False})


def draw_cornice(b: Builder, house: House, height: float, projection: float = 0.25, thickness: float = 0.3) -> None:
    front = house.setback

    b.side_prism([(front, height), (front - projection, height + thickness * 0.4), (front - projection, height + thickness), (front, height + thickness)], -house.half, house.half, "trim", house.trim_tint, uv=("band", *TRIM_SMOOTH_BAND, 1.0))


def draw_quoins(b: Builder, house: House, bottom: float, top: float, material: str = "trim") -> None:
    """Alternating corner stones on both front corners."""
    course = 0.45
    courses = int((top - bottom) / course)
    stones = list(itertools.product((-1, 1), range(courses)))

    for side_sign, course_index in stones:
        long_stone = course_index % 2 == 0
        inner = house.half - (0.6 if long_stone else 0.35)
        u_from, u_to = sorted((side_sign * inner, side_sign * house.half))
        z = bottom + course_index * course
        b.box((u_from, house.setback - 0.05, z + 0.02), (u_to, house.setback, z + course - 0.02), material, house.trim_tint)


def draw_base_band(b: Builder, house: House, height: float, material: str = "stone", tint: tuple = None) -> None:
    b.box((-house.half, house.setback - 0.05, 0.0), (house.half, house.setback, height), material, tint or srgb(STONE["media"]))


def draw_chimney(b: Builder, house: House, u: float, d: float, top: float, size: tuple = (0.7, 0.6), material: str = "brick", pots: int = 1) -> None:
    half_u, half_d = size[0] / 2.0, size[1] / 2.0
    u = max(-house.limit + half_u, min(house.limit - half_u, u))

    b.box((u - half_u, d - half_d, house.top - 0.5), (u + half_u, d + half_d, top), material, srgb(BRICK["vermelho"]) if material == "brick" else WHITE)
    b.box((u - half_u - 0.05, d - half_d - 0.05, top), (u + half_u + 0.05, d + half_d + 0.05, top + 0.12), "trim", house.trim_tint)

    for pot_index in range(pots):
        pot_u = u + (pot_index - (pots - 1) / 2.0) * 0.3
        b.cylinder((pot_u, d, top + 0.12), 0.09, 0.35, 8, "brick", srgb(BRICK["escuro"]))


def draw_body(b: Builder, house: House, ground: str = "solid") -> None:
    """Wall mass storey by storey (each upper storey may hang forward by house.jetty, the ground storey may sit back
    behind an arcade), plus its collider. ground == "shop": the ground storey is built by shop_shell."""
    first = 1 if ground == "shop" else 0
    storeys = list(enumerate(zip(house.levels, house.levels[1:])))[first:]
    jetty = house.jetty

    for index, (bottom, top) in storeys:
        front = house.setback - jetty * index + (house.ground_recess if index == 0 else 0.0)
        b.box((-house.half, front, bottom), (house.half, house.depth, top), house.wall_material, house.wall_tint)
        b.collider((-house.half, front, bottom), (house.half, house.depth, top))

        if jetty > 0.0 and index > 0:
            b.box((-house.half, front, bottom - 0.12), (house.half, front + jetty, bottom), "wood", house.wood_tint, uv=("band", *WOOD_DARK_BAND, 1.5))


# ---------- roofs (dispatch by ROOF_BUILDERS) ----------

def gable_parallel_roof(b: Builder, house: House, pitch: float, eave_front: float = 0.4, eave_back: float = 0.4) -> float:
    """Ridge parallel to the street; eaves only front and back, ends flush with the lot. Returns the ridge height."""
    front, back = house.setback - eave_front, house.depth + eave_back
    rise = (back - front) / 2.0 * math.tan(math.radians(pitch))
    base = house.top - 0.12

    b.side_prism([(front, base), (back, base), ((front + back) / 2.0, base + rise)], -house.limit, house.limit, house.roof_material, house.roof_tint)

    return base + rise


def hip_roof(b: Builder, house: House, pitch: float, eave_front: float = 0.4, eave_back: float = 0.4) -> float:
    """Four slopes; sides end at the lot line (party walls), so only front and back eaves overhang."""
    front, back = house.setback - eave_front, house.depth + eave_back
    half_depth = (back - front) / 2.0
    rise = half_depth * math.tan(math.radians(pitch))
    base = house.top - 0.12
    ridge_half = max(0.05, house.limit - half_depth)
    middle = (front + back) / 2.0
    corners = [(side_sign * house.limit, edge, base) for side_sign, edge in itertools.product((-1, 1), (front, back))]

    b.hull(corners + [(-ridge_half, middle, base + rise), (ridge_half, middle, base + rise)], house.roof_material, house.roof_tint)

    return base + rise


def gable_street_roof(b: Builder, house: House, pitch: float, eave_back: float = 0.3, gable: str = "plain") -> float:
    """Gable toward the street (side eaves <= 0.13 m); the front triangle is a wall (plain, stepped, bell) dressed by
    GABLE_WALLS, with barge boards along the rake."""
    rise = house.limit * math.tan(math.radians(pitch))
    base = house.top - 0.12
    front = house.setback + 0.25

    b.prism([(-house.limit, base), (house.limit, base), (0.0, base + rise)], front, house.depth + eave_back, house.roof_material, house.roof_tint)
    GABLE_WALLS[gable](b, house, base, rise)

    return base + rise


def plain_gable_wall(b: Builder, house: House, base: float, rise: float) -> None:
    gable_rise = house.half * rise / house.limit
    front = house.setback

    b.prism([(-house.half, base), (house.half, base), (0.0, base + gable_rise)], front, front + 0.3, house.wall_material, house.wall_tint)

    for side_sign in (-1, 1):
        b.beam((side_sign * house.limit, front - 0.12, base), (0.0, front - 0.12, base + rise + 0.05), 0.22, 0.08, "wood", house.wood_tint)


def stepped_outline(half: float, base: float, top: float, steps: int) -> list:
    """Crow-stepped gable polygon in the facade plane, counter-clockwise from the bottom right corner."""
    widths = [max(0.45, half * (1.0 - step / steps)) for step in range(steps)]
    heights = [base + (top - base) * (step + 1) / steps for step in range(steps)]
    right = [(half, base)]

    for step in range(steps):
        right.append((widths[step], heights[step]))
        right += [(widths[step + 1], heights[step])] if step + 1 < steps else []

    return right + [(-u, z) for u, z in reversed(right)]


def stepped_gable_wall(b: Builder, house: House, base: float, rise: float) -> None:
    """Dutch crow-stepped gable, taller than the roof behind it, with a coping stone on every tread."""
    steps = 5
    front = house.setback
    gable_top = base + rise + 0.6
    widths = [max(0.45, house.half * (1.0 - step / steps)) for step in range(steps)] + [0.0]
    heights = [base + (gable_top - base) * (step + 1) / steps for step in range(steps)]
    treads = list(itertools.product(range(steps), (-1, 1)))

    b.prism(stepped_outline(house.half, base, gable_top, steps), front, front + 0.35, house.wall_material, house.wall_tint)

    for step, side_sign in treads:
        inner, outer = sorted((side_sign * widths[step + 1], side_sign * widths[step]))
        b.box((inner - 0.05, front - 0.05, heights[step]), (outer + 0.05, front + 0.4, heights[step] + 0.1), "trim", house.trim_tint)


def bell_gable_wall(b: Builder, house: House, base: float, rise: float) -> None:
    """Bell (or scroll) gable: concave shoulders rising to a narrow top with a small pediment."""
    front = house.setback
    gable_top = base + rise + 0.5
    neck = 0.8
    samples = 8
    shoulder = [(neck + (house.half - neck) * (1.0 - math.sin(math.pi / 2.0 * step / samples)), base + (gable_top - 0.9 - base) * step / samples) for step in range(samples + 1)]
    right = shoulder + [(neck, gable_top - 0.5), (neck * 0.6, gable_top)]
    outline = right + [(-u, z) for u, z in reversed(right)]

    b.prism(outline, front, front + 0.35, house.wall_material, house.wall_tint)
    b.prism([(-neck - 0.15, gable_top - 0.05), (neck + 0.15, gable_top - 0.05), (0.0, gable_top + 0.45)], front - 0.05, front + 0.4, "trim", house.trim_tint)

    for side_sign in (-1, 1):
        b.sphere((side_sign * (house.half - 0.1), front + 0.15, base + 0.25), 0.22, "trim", house.trim_tint)


def scroll_gable_wall(b: Builder, house: House, base: float, rise: float) -> None:
    """Hanseatic gable: bell outline with volutes at each shoulder and a sundial disc."""
    bell_gable_wall(b, house, base, rise)

    for side_sign in (-1, 1):
        b.cylinder((side_sign * 1.1, house.setback - 0.06, base + rise * 0.45), 0.28, 0.08, 12, "trim", house.trim_tint, axis="Y")

    b.cylinder((0.0, house.setback - 0.05, base + rise * 0.55), 0.4, 0.05, 16, "trim", house.trim_tint, axis="Y")
    b.box((-0.02, house.setback - 0.12, base + rise * 0.55), (0.02, house.setback - 0.05, base + rise * 0.55 + 0.35), "metal", house.iron_tint)


def half_hip_gable_wall(b: Builder, house: House, base: float, rise: float) -> None:
    """Gable cut short by a small hip at the top (Krüppelwalm): the wall stops at 3/4 of the rise."""
    front = house.setback
    cut = 0.75
    shoulder = house.half * (1.0 - cut)

    b.prism([(-house.half, base), (house.half, base), (shoulder, base + rise * cut), (-shoulder, base + rise * cut)], front, front + 0.3, house.wall_material, house.wall_tint)
    b.hull([(side_sign * house.limit * (1.0 - cut) + side_sign * 0.1, front - 0.15, base + rise * cut) for side_sign in (-1, 1)] + [(side_sign * house.limit * (1.0 - cut), front + 1.0, base + rise * cut) for side_sign in (-1, 1)] + [(0.0, front + 1.0, base + rise + 0.02)], house.roof_material, house.roof_tint)


GABLE_WALLS = {"plain": plain_gable_wall, "stepped": stepped_gable_wall, "bell": bell_gable_wall, "scroll": scroll_gable_wall, "half_hip": half_hip_gable_wall}


def flat_parapet_roof(b: Builder, house: House, pitch: float, steps: int = 3) -> float:
    """Flat roof behind a stepped art-deco parapet (front) and low parapets on the other sides."""
    front = house.setback
    slab_top = house.top + 0.15
    step_height = 0.45
    step_widths = [house.half * (1.0 - 0.28 * step) for step in range(steps)]

    b.box((-house.half, front, house.top), (house.half, house.depth, slab_top), "trim", house.trim_tint)
    b.box((-house.half, house.depth - 0.25, slab_top), (house.half, house.depth, slab_top + 0.6), house.wall_material, house.wall_tint)

    for step, step_half in enumerate(step_widths):
        b.box((-step_half, front, slab_top + step * step_height), (step_half, front + 0.3, slab_top + (step + 1) * step_height), house.wall_material, house.wall_tint)
        b.box((-step_half - 0.04, front - 0.06, slab_top + (step + 1) * step_height - 0.08), (step_half + 0.04, front + 0.34, slab_top + (step + 1) * step_height), "trim", house.trim_tint)

    return slab_top + steps * step_height


def pavilion_roof(b: Builder, house: House, pitch: float) -> float:
    """Steep pyramid with a weather vane: square tower house."""
    rise = house.limit * math.tan(math.radians(pitch))
    base = house.top - 0.1
    front = house.setback - 0.1
    corners = [(side_sign * house.limit, edge, base) for side_sign, edge in itertools.product((-1, 1), (front, house.depth + 0.1))]
    apex = (0.0, (front + house.depth + 0.1) / 2.0, base + rise)

    b.hull(corners + [apex], house.roof_material, house.roof_tint)
    b.cylinder(apex, 0.03, 1.2, 6, "metal", house.iron_tint)
    b.box((apex[0] - 0.25, apex[1] - 0.01, apex[2] + 0.9), (apex[0] + 0.25, apex[1] + 0.01, apex[2] + 1.05), "metal", house.iron_tint)

    return base + rise


ROOF_BUILDERS = {
    "gable_parallel": gable_parallel_roof,
    "hip": hip_roof,
    "gable_street": gable_street_roof,
    "flat_parapet": flat_parapet_roof,
    "pavilion": pavilion_roof,
}


# ---------- signature details (dispatch by FEATURES) ----------

def iron_balcony(b: Builder, house: House, storey: int = 1) -> None:
    """Continuous wrought-iron balcony on the given storey (sobrado)."""
    z = house.levels[storey]
    front = house.setback
    posts = int(2.0 * house.half / 0.14)

    b.box((-house.half + 0.1, front - 0.75, z - 0.12), (house.half - 0.1, front, z), "trim", house.trim_tint)
    b.box((-house.half + 0.1, front - 0.75, z + 0.95), (house.half - 0.1, front - 0.7, z + 1.0), "metal", house.iron_tint)

    for post in range(posts + 1):
        u = -house.half + 0.1 + (2.0 * house.half - 0.2) * post / posts
        b.box((u - 0.012, front - 0.74, z), (u + 0.012, front - 0.71, z + 0.95), "metal", house.iron_tint)


def roof_finials(b: Builder, house: House) -> None:
    """Glazed ceramic finials on the two front corners of the roof (luso-brazilian pinha)."""
    for side_sign in (-1, 1):
        u = side_sign * (house.half - 0.2)
        b.cylinder((u, house.setback - 0.2, house.top + 0.15), 0.08, 0.2, 8, "paint", house.accent)
        b.sphere((u, house.setback - 0.2, house.top + 0.45), 0.13, "paint", house.accent)


def wavy_parapet(b: Builder, house: House) -> None:
    """Low front parapet with a raised curve and a pinecone at the centre (casa térrea)."""
    front = house.setback
    samples = 12
    curve = [(-house.half + 2.0 * house.half * step / samples, house.top + 0.5 + 0.35 * math.sin(math.pi * step / samples) ** 2) for step in range(samples + 1)]

    b.prism([(house.half, house.top), (-house.half, house.top)] + curve, front - 0.05, front + 0.25, house.wall_material, house.wall_tint)
    b.cylinder((0.0, front + 0.1, house.top + 0.85), 0.07, 0.15, 8, "trim", house.trim_tint)
    b.sphere((0.0, front + 0.1, house.top + 1.08), 0.12, "trim", house.trim_tint, scale=(1.0, 1.0, 1.4))


def stone_bench(b: Builder, house: House) -> None:
    u = house.half - 0.9
    b.box((u - 0.6, house.setback - 0.45, 0.0), (u + 0.6, house.setback, 0.45), "stone", srgb(STONE["media"]))


def half_timber(b: Builder, house: House, first_storey: int = 1) -> None:
    """Dark timber frame on the upper storeys: posts, rails and St Andrew's crosses between window bays."""
    jetty = house.jetty
    storeys = list(enumerate(zip(house.levels, house.levels[1:])))[first_storey:]
    posts = house.bays(3, 0.0)
    panel_edges = [-house.half] + [(first + second) / 2.0 for first, second in zip(posts, posts[1:])] + [house.half]
    pieces = list(itertools.product(storeys, range(len(panel_edges) - 1)))

    for (index, (bottom, top)), panel in pieces:
        front = house.setback - jetty * index - 0.03
        left, right = panel_edges[panel], panel_edges[panel + 1]
        b.box((left, front - 0.05, bottom), (left + 0.16, front, top), "wood", house.wood_tint, uv=("band", *WOOD_DARK_BAND, 1.5))
        b.box((left, front - 0.05, bottom), (right, front, bottom + 0.16), "wood", house.wood_tint, uv=("band", *WOOD_DARK_BAND, 1.5))
        b.beam((left + 0.1, front - 0.06, bottom + 0.16), (left + 0.45, front - 0.06, top - 0.1), 0.12, 0.05, "wood", house.wood_tint)
        b.beam((right - 0.1, front - 0.06, bottom + 0.16), (right - 0.45, front - 0.06, top - 0.1), 0.12, 0.05, "wood", house.wood_tint)

    for index, (bottom, top) in storeys:
        front = house.setback - jetty * index - 0.03
        b.box((house.half - 0.16, front - 0.05, bottom), (house.half, front, top), "wood", house.wood_tint, uv=("band", *WOOD_DARK_BAND, 1.5))


def flower_boxes(b: Builder, house: House, storey: int = 1) -> None:
    """Window boxes with red flowers under the upper windows."""
    z = house.levels[storey] + 0.85
    front = house.setback - house.jetty * storey

    for u in house.bays(3):
        b.box((u - 0.45, front - 0.3, z - 0.18), (u + 0.45, front - 0.05, z), "wood", srgb(WOOD["media"]), uv=("band", *WOOD_LIGHT_BAND, 1.0))
        b.box((u - 0.42, front - 0.28, z), (u + 0.42, front - 0.07, z + 0.12), "paint", srgb("3F8A50"))
        b.sphere((u - 0.2, front - 0.18, z + 0.14), 0.09, "paint", srgb("D9483B"))
        b.sphere((u + 0.2, front - 0.18, z + 0.14), 0.09, "paint", srgb("D9483B"))


def bay_window(b: Builder, house: House) -> None:
    """Two-storey bay window on the left (tudor), diamond-paned glass."""
    u = -house.half + 1.8
    top = house.levels[2] - 0.2
    front = house.setback

    b.box((u - 0.95, front - 0.6, 0.4), (u + 0.95, front, top), house.wall_material, house.wall_tint)
    b.collider((u - 0.95, front - 0.6, 0.0), (u + 0.95, front, top))
    b.box((u - 1.0, front - 0.65, top), (u + 1.0, front, top + 0.15), "trim", house.trim_tint)

    for bottom in (0.9, house.levels[1] + 0.6):
        b.box((u - 0.75, front - 0.66, bottom), (u + 0.75, front - 0.6, bottom + 1.4), "glass")

        for bar in range(4):
            bar_u = u - 0.75 + 0.3 * (bar + 1)
            b.box((bar_u - 0.015, front - 0.68, bottom), (bar_u + 0.015, front - 0.66, bottom + 1.4), "metal", house.iron_tint)


def cross_gable(b: Builder, house: House) -> None:
    """Asymmetric front gable crossing the parallel roof (tudor), with vertical close studding."""
    u = house.half - 2.4
    half = 1.9
    rise = half * math.tan(math.radians(50.0))
    base = house.top - 0.12
    front = house.setback

    b.prism([(u - half - 0.1, base), (u + half + 0.1, base), (u, base + rise + 0.1)], front - 0.15, front + 3.5, house.roof_material, house.roof_tint)
    b.prism([(u - half, base), (u + half, base), (u, base + rise)], front - 0.18, front - 0.12, house.wall_material, house.wall_tint)

    for stud in range(7):
        stud_u = u - half + 0.3 + stud * (2.0 * half - 0.6) / 6.0
        stud_top = base + rise * (1.0 - abs(stud_u - u) / half) - 0.1
        b.box((stud_u - 0.05, front - 0.22, base), (stud_u + 0.05, front - 0.18, max(base + 0.2, stud_top)), "wood", house.wood_tint, uv=("band", *WOOD_DARK_BAND, 1.5))


def hoist_beam(b: Builder, house: House) -> None:
    """Hoisting beam with a hook under the gable top (Dutch canal house) and an attic oculus."""
    top = house.top + 2.2
    b.box((-0.1, house.setback - 0.8, top), (0.1, house.setback, top + 0.2), "wood", house.wood_tint, uv=("band", *WOOD_DARK_BAND, 1.5))
    b.cylinder((0.0, house.setback - 0.7, top - 0.5), 0.02, 0.5, 6, "metal", house.iron_tint)
    draw_window(b, house, Opening(0.0, 0.7, house.top + 0.9, 0.7, "circle"), bars=0)


def stone_bands(b: Builder, house: House) -> None:
    """Light stone string courses at every floor line and keystones over the windows (brick houses)."""
    for level in house.levels[1:-1]:
        b.box((-house.half, house.setback - 0.06, level - 0.08), (house.half, house.setback, level + 0.08), "trim", house.trim_tint)


def deep_eave_brackets(b: Builder, house: House) -> None:
    """Carved brackets under the deep front eave (alpine chalet) and stones holding the roof boards."""
    for u in house.bays(4, 0.2):
        b.beam((u, house.setback, house.top - 1.0), (u, house.setback - 1.1, house.top - 0.15), 0.14, 0.14, "wood", srgb(WOOD["mel"]))

    for stone_index in range(5):
        u = -house.half + 0.8 + (2.0 * house.half - 1.6) * stone_index / 4.0
        b.sphere((u, house.depth * 0.3, house.top + 0.8), 0.2, "stone", srgb(STONE["cinza"]), scale=(1.0, 1.0, 0.6))


def wooden_balcony(b: Builder, house: House) -> None:
    """Full-width wooden balcony on the first floor with cut-out balusters (chalet)."""
    z = house.levels[1]
    front = house.setback
    boards = int(2.0 * house.half / 0.22)
    honey = srgb(WOOD["mel"])

    b.box((-house.half, front - 1.0, z - 0.15), (house.half, front, z), "wood", honey, uv=("band", *WOOD_LIGHT_BAND, 1.5))
    b.box((-house.half, front - 1.0, z + 0.95), (house.half, front - 0.92, z + 1.05), "wood", honey, uv=("band", *WOOD_LIGHT_BAND, 1.5))

    for board in range(boards):
        u = -house.half + 0.11 + board * (2.0 * house.half - 0.22) / max(1, boards - 1)
        b.box((u - 0.07, front - 0.98, z), (u + 0.07, front - 0.94, z + 0.95), "wood", honey, uv=("band", *WOOD_LIGHT_BAND, 1.0))


def pergola_terrace(b: Builder, house: House) -> None:
    """Roof terrace over half the front with a pergola and a vine (mediterranean)."""
    left, right = 0.2, house.half
    z = house.top
    posts = [(u, d) for u, d in itertools.product((left + 0.1, right - 0.1), (house.setback + 0.2, house.setback + 3.0))]

    b.box((left, house.setback, z - 0.05), (right, house.setback + 3.2, z + 0.9), house.wall_material, house.wall_tint)

    for post_u, post_d in posts:
        b.box((post_u - 0.07, post_d - 0.07, z + 0.9), (post_u + 0.07, post_d + 0.07, z + 3.0), "wood", srgb(WOOD["media"]), uv=("band", *WOOD_LIGHT_BAND, 1.0))

    for beam in range(6):
        u = left + 0.1 + (right - left - 0.2) * beam / 5.0
        b.box((u - 0.05, house.setback + 0.1, z + 3.0), (u + 0.05, house.setback + 3.1, z + 3.12), "wood", srgb(WOOD["media"]), uv=("band", *WOOD_LIGHT_BAND, 1.0))

    b.sphere(((left + right) / 2.0, house.setback + 1.6, z + 3.15), 0.9, "paint", srgb("3F8A50"), scale=(1.6, 1.2, 0.35))


def clay_pots(b: Builder, house: House) -> None:
    for pot_index, u in enumerate((-house.half + 0.5, house.half - 0.5)):
        b.cylinder((u, house.setback - 0.35, 0.0), 0.22, 0.55, 10, "paint", srgb("C8693F"), top_radius=0.28)
        b.sphere((u, house.setback - 0.35, 0.7), 0.3, "paint", srgb("3F8A50" if pot_index else "7FC46A"))


def deco_fins(b: Builder, house: House) -> None:
    """Vertical fins between the upper windows, rising through the parapet (art deco)."""
    edges = house.bays(3)
    fins = [-house.half + 0.1] + [(first + second) / 2.0 for first, second in zip(edges, edges[1:])] + [house.half - 0.1]

    for u in fins:
        b.box((u - 0.09, house.setback - 0.18, house.levels[1]), (u + 0.09, house.setback, house.top + 1.2), "trim", WHITE)


def marquee(b: Builder, house: House) -> None:
    """Straight canopy over the shop window (art deco) and a granite base."""
    b.box((-house.half, house.setback - 1.1, 3.0), (house.half, house.setback, 3.15), "trim", WHITE)
    draw_base_band(b, house, 0.5, "stone", srgb(STONE["cinza"]))


def dormers(b: Builder, house: House) -> None:
    """Two gabled dormers on the front slope (Cotswold stone cottage)."""
    for u in (-house.half / 2.0, house.half / 2.0):
        z = house.top + 0.2
        b.box((u - 0.6, house.setback + 0.6, house.top - 0.1), (u + 0.6, house.setback + 1.8, z + 1.0), house.wall_material, house.wall_tint)
        b.prism([(u - 0.75, z + 1.0), (u + 0.75, z + 1.0), (u, z + 1.7)], house.setback + 0.5, house.setback + 2.4, house.roof_material, house.roof_tint)
        b.box((u - 0.35, house.setback + 0.54, z + 0.1), (u + 0.35, house.setback + 0.6, z + 0.9), "glass")


def front_garden(b: Builder, house: House) -> None:
    """Low dry-stone wall with a gate gap in front of a 1 m garden inside the lot (and a climbing rose)."""
    gate = 0.9

    for u_from, u_to in ((-house.half, -gate / 2.0), (gate / 2.0, house.half)):
        b.box((u_from, 0.0, 0.0), (u_to, 0.3, 0.6), "stone", srgb(STONE["dourada"]))
        b.collider((u_from, 0.0, 0.0), (u_to, 0.3, 0.6))

    b.box((-house.half + 0.1, 0.35, 0.0), (house.half - 0.1, house.setback - 0.05, 0.15), "paint", srgb("3F8A50"))
    b.sphere((house.half - 0.7, house.setback - 0.2, 1.4), 0.5, "paint", srgb("E9A6C0"), scale=(0.8, 0.5, 1.8))


def stone_porch(b: Builder, house: House) -> None:
    b.box((-0.9, house.setback - 1.0, 0.0), (0.9, house.setback, 0.12), "stone", srgb(STONE["dourada"]))
    b.prism([(-1.0, 2.5), (1.0, 2.5), (0.0, 3.3)], house.setback - 1.0, house.setback, house.roof_material, house.roof_tint)

    for side_sign in (-1, 1):
        b.box((side_sign * 0.85 - 0.08, house.setback - 0.95, 0.0), (side_sign * 0.85 + 0.08, house.setback - 0.8, 2.5), "stone", srgb(STONE["dourada"]))


def loggia(b: Builder, house: House) -> None:
    """Three dark arches on the top storey (italianate palazzo) behind a balustrade."""
    bottom = house.levels[-2] + 0.3
    height = house.storeys[-1] - 0.7

    for u in house.bays(3, 1.0):
        arch = Opening(u, 1.2, bottom, height, "round")
        b.prism(arch.outline(0.12), house.setback - 0.05, house.setback, "trim", house.trim_tint)
        b.prism(arch.outline(), house.setback - 0.06, house.setback - 0.05, "paint", srgb("2A2228"))

    for baluster in range(int(2.0 * house.half / 0.25)):
        u = -house.half + 0.125 + baluster * 0.25
        b.cylinder((u, house.setback - 0.2, bottom - 0.3), 0.05, 0.6, 6, "trim", house.trim_tint)


def eave_brackets(b: Builder, house: House) -> None:
    for u in house.bays(int(house.width / 1.2), 0.2):
        b.box((u - 0.07, house.setback - 0.55, house.top - 0.35), (u + 0.07, house.setback, house.top - 0.1), "trim", house.trim_tint)


def corner_turret(b: Builder, house: House) -> None:
    """Round stair turret in a front corner, inside the lot, with a conical slate roof."""
    radius = 1.0
    u = house.half - radius - 0.05
    d = house.setback + radius - 0.3
    top = house.top + 1.5

    b.cylinder((u, d, 0.0), radius, top, 14, house.wall_material, house.wall_tint)
    b.collider((u - radius, d - radius, 0.0), (u + radius, d + radius, top))
    b.cylinder((u, d, top), radius + 0.15, 2.4, 14, "slate", srgb("7E8AA6"), top_radius=0.02)

    for slit in range(3):
        b.box((u - 0.07, d - radius - 0.02, 1.5 + slit * 2.4), (u + 0.07, d - radius + 0.02, 2.3 + slit * 2.4), "glass")


def machicolations(b: Builder, house: House) -> None:
    for u in house.bays(int(house.width / 0.7), 0.1):
        b.box((u - 0.12, house.setback - 0.3, house.top - 0.6), (u + 0.12, house.setback, house.top - 0.1), "trim", house.trim_tint)

    b.box((-house.half, house.setback - 0.35, house.top - 0.1), (house.half, house.setback, house.top + 0.1), "trim", house.trim_tint)


def arcade(b: Builder, house: House) -> None:
    """Ground-floor arcade 2 m deep that people can walk under (hanseatic merchant house), with a lantern."""
    depth = 2.0
    count = 3 if house.width >= 10 else 2
    pier = 0.45
    span = (2.0 * house.half - pier * (count + 1)) / count
    spring = house.storeys[0] - span / 2.0 - 0.2

    for index in range(count + 1):
        u = -house.half + index * (span + pier)
        b.box((u, house.setback, 0.0), (u + pier, house.setback + 0.5, house.storeys[0]), house.wall_material, house.wall_tint)
        b.collider((u, house.setback, 0.0), (u + pier, house.setback + 0.5, house.storeys[0]))

    for index in range(count):
        u = -house.half + pier + index * (span + pier) + span / 2.0
        arch_band = Opening(u, span, 0.0, spring + span / 2.0, "round")
        crown = [(arch_u, z) for arch_u, z in arch_band.arc()]
        b.prism([(u + span / 2.0, house.storeys[0]), (u + span / 2.0, spring)] + crown[1:-1] + [(u - span / 2.0, spring), (u - span / 2.0, house.storeys[0])], house.setback, house.setback + 0.5, house.wall_material, house.wall_tint)

    b.box((-house.half, house.setback + depth, 0.0), (house.half, house.setback + depth + 0.02, 0.02), "stone", srgb(STONE["media"]))
    b.cylinder((0.0, house.setback + 1.0, house.storeys[0] - 0.8), 0.12, 0.35, 6, "glow_amber")


FEATURES = {
    "iron_balcony": iron_balcony,
    "finials": roof_finials,
    "wavy_parapet": wavy_parapet,
    "stone_bench": stone_bench,
    "half_timber": half_timber,
    "flower_boxes": flower_boxes,
    "bay_window": bay_window,
    "cross_gable": cross_gable,
    "hoist_beam": hoist_beam,
    "stone_bands": stone_bands,
    "deep_eave": deep_eave_brackets,
    "wooden_balcony": wooden_balcony,
    "pergola": pergola_terrace,
    "clay_pots": clay_pots,
    "deco_fins": deco_fins,
    "marquee": marquee,
    "dormers": dormers,
    "front_garden": front_garden,
    "stone_porch": stone_porch,
    "loggia": loggia,
    "eave_brackets": eave_brackets,
    "turret": corner_turret,
    "machicolations": machicolations,
    "arcade": arcade,
}


# ---------- archetypes (catálogo C.3) ----------

ARCHETYPE_SPECS = {  # arquétipo -> receita; janelas: (topo, largura, altura, peitoril, venezianas, travessas)
    "sobrado": dict(storeys=(3.6, 3.3), roof=("hip", dict(pitch=25.0, eave_front=0.6, eave_back=0.5)), roof_finish="terracota", bay=2.3, window=("segment", 1.1, 2.3, 0.3, False, 1), ground_window=("segment", 1.1, 2.6, 0.0, False, 1), door=("center", 1.3, 2.7, "segment"), base=None, cornice=True, quoins=True, features=("iron_balcony", "finials")),
    "terrea": dict(storeys=(3.4,), roof=("gable_parallel", dict(pitch=30.0, eave_front=0.1, eave_back=0.4)), roof_finish="terracota", bay=2.2, window=("flat", 1.0, 1.6, 0.9, True, 1), ground_window=("flat", 1.0, 1.6, 0.9, True, 1), door=("left", 1.1, 2.4, "flat"), base=("stone", 0.8), cornice=True, quoins=False, features=("wavy_parapet", "stone_bench")),
    "fachwerk": dict(storeys=(3.2, 2.9, 2.7), roof=("gable_street", dict(pitch=55.0, gable="half_hip")), roof_finish="velha", bay=1.8, window=("flat", 0.8, 1.2, 0.9, False, 1), ground_window=("flat", 0.9, 1.3, 0.9, False, 1), door=("left", 1.1, 2.3, "flat"), base=("stone", 3.2), cornice=False, quoins=False, jetty=0.35, features=("half_timber", "flower_boxes")),
    "tudor": dict(storeys=(3.3, 3.0), roof=("gable_parallel", dict(pitch=50.0, eave_front=0.35, eave_back=0.35)), roof_finish="ardosia", bay=2.2, window=("flat", 0.9, 1.4, 0.9, False, 2), ground_window=("flat", 0.9, 1.5, 0.9, False, 2), door=("right", 1.2, 2.4, "pointed"), base=("brick", 3.3), cornice=False, quoins=False, chimney=dict(u=-1.0, d=5.0, extra=1.2, pots=2), features=("bay_window", "cross_gable", "half_timber")),
    "holandesa": dict(storeys=(3.4, 3.1, 2.9), roof=("gable_street", dict(pitch=50.0, gable="stepped")), roof_finish="velha", bay=1.9, window=("segment", 0.85, 2.0, 0.7, False, 2), ground_window=("segment", 0.9, 2.2, 0.6, False, 2), door=("left", 1.0, 2.5, "round"), base=None, cornice=False, quoins=False, shrink=0.12, features=("hoist_beam", "stone_bands")),
    "chale": dict(storeys=(3.2, 3.0), roof=("gable_parallel", dict(pitch=22.0, eave_front=1.2, eave_back=0.6)), roof_finish="madeira", bay=2.4, window=("flat", 1.0, 1.4, 0.9, True, 1), ground_window=("flat", 1.0, 1.4, 0.9, True, 1), door=("center", 1.2, 2.3, "flat"), base=("stone", 3.2), cornice=False, quoins=False, upper_wall=("wood", WOOD["mel"]), features=("wooden_balcony", "deep_eave", "flower_boxes")),
    "mediterranea": dict(storeys=(3.3, 3.0), roof=("gable_parallel", dict(pitch=15.0, eave_front=0.3, eave_back=0.3)), roof_finish="clara", bay=2.8, window=("flat", 0.7, 1.0, 1.1, False, 0), ground_window=("flat", 0.7, 1.0, 1.2, False, 0), door=("center", 1.3, 2.5, "round"), base=None, cornice=False, quoins=False, chimney=dict(u=-2.0, d=6.0, extra=0.6, pots=0, material="plaster"), features=("pergola", "clay_pots")),
    "artdeco": dict(storeys=(3.6, 3.2), roof=("flat_parapet", dict(pitch=0.0, steps=3)), roof_finish="terracota", bay=2.4, window=("flat", 0.8, 2.0, 0.6, False, 2), ground_window=("flat", 3.0, 2.2, 0.6, False, 1), door=("right", 1.2, 2.6, "flat"), base=None, cornice=False, quoins=False, ground_bays=1, features=("deco_fins", "marquee")),
    "pedra": dict(storeys=(3.0,), roof=("gable_parallel", dict(pitch=50.0, eave_front=0.25, eave_back=0.25)), roof_finish="ardosia", bay=2.4, window=("flat", 1.0, 1.2, 0.9, False, 1), ground_window=("flat", 1.0, 1.2, 0.9, False, 1), door=("center", 1.0, 2.2, "flat"), base=None, cornice=False, quoins=False, setback=1.0, chimney=dict(u=2.6, d=4.0, extra=0.5, pots=2, material="stone"), features=("dormers", "front_garden", "stone_porch")),
    "palacete": dict(storeys=(3.4, 3.8, 3.2), roof=("hip", dict(pitch=22.0, eave_front=0.9, eave_back=0.6)), roof_finish="terracota", bay=2.4, window=("round", 1.1, 2.4, 0.5, False, 1), ground_window=("round", 1.1, 2.2, 0.6, False, 1), door=("center", 1.6, 3.0, "round"), base=("stone", 3.4), cornice=True, quoins=True, loggia_top=True, features=("loggia", "eave_brackets")),
    "torre": dict(storeys=(3.2, 3.0, 3.0, 2.8), roof=("pavilion", dict(pitch=60.0)), roof_finish="ardosia", bay=2.6, window=("round", 0.4, 1.2, 0.9, False, 0), ground_window=("flat", 0.25, 1.1, 1.2, False, 0), door=("left", 1.1, 2.4, "round"), upper_window=("round", 1.0, 1.6, 0.8, False, 1), base=None, cornice=False, quoins=True, features=("turret", "machicolations")),
    "hanseatica": dict(storeys=(3.6, 3.2, 3.0), roof=("gable_street", dict(pitch=50.0, gable="scroll")), roof_finish="terracota", bay=2.2, window=("segment", 0.9, 1.9, 0.7, False, 2), ground_window=None, door=("center", 1.2, 2.5, "round"), base=None, cornice=False, quoins=False, ground_recess=2.0, features=("arcade", "stone_bands")),
}


def window_shape(spec: dict, storey: int) -> tuple:
    """Window recipe of a storey: ground floor, the generic upper one, or the archetype's special upper one."""
    shapes = {0: spec["ground_window"]}

    return shapes.get(storey, spec.get("upper_window", spec["window"]))


def door_axis(house: House, spec: dict, bays: list) -> float:
    position = spec["door"][0]
    picks = {"center": lambda: bays[len(bays) // 2], "left": lambda: bays[0], "right": lambda: bays[-1]}

    return picks[position]()


def make_house(archetype: str, width: float, variant: int) -> House:
    widths, depth, plasters = HOUSE_ARCHETYPES[archetype]
    spec = ARCHETYPE_SPECS[archetype]
    accent = ACCENT_ORDER[(variant + len(archetype)) % len(ACCENT_ORDER)]
    house = House(width, depth, spec["storeys"], plasters[variant], spec["roof_finish"], accent, hash_seed(archetype, width, variant), spec.get("setback", 0.0))

    house.ground_recess = spec.get("ground_recess", 0.0)
    house.jetty = spec.get("jetty", 0.0)

    return house


def hash_seed(*parts) -> int:
    """Stable seed from text parts (Python's hash() of str changes between runs)."""
    return sum((index + 1) * ord(character) for index, character in enumerate("|".join(str(part) for part in parts)))


def build_house(b: Builder, house: House, spec: dict, ground: str = "solid") -> float:
    """Shell, windows, door, mouldings, roof and signature details of one archetype. Returns the roof top height."""
    bays = house.bays(max(1, int(round(2.0 * house.half / spec["bay"]))))
    door_u = door_axis(house, spec, bays)
    storeys = range(1 if ground == "shop" else 0, len(house.storeys) - (1 if spec.get("loggia_top") else 0))
    roof_name, roof_options = spec["roof"]

    draw_body(b, house, ground)
    paint_upper_wall(b, house, spec, ground)

    if spec.get("base") and ground != "shop":
        draw_base_band(b, house, min(spec["base"][1], house.storeys[0]), spec["base"][0], srgb(BRICK["tudor"]) if spec["base"][0] == "brick" else None)

    for storey in storeys:
        draw_storey_windows(b, house, spec, storey, bays, door_u)

    if ground != "shop":
        draw_door(b, house, door_u, spec["door"][1], spec["door"][2], spec["door"][3], front=house.setback + house.ground_recess)

    if spec.get("quoins"):
        draw_quoins(b, house, 0.0, house.top)

    if spec.get("cornice"):
        draw_cornice(b, house, house.top - 0.3)

    roof_top = ROOF_BUILDERS[roof_name](b, house, **roof_options)

    if spec.get("chimney"):
        chimney = spec["chimney"]
        draw_chimney(b, house, chimney["u"], min(chimney["d"], house.depth - 1.0), roof_top + chimney["extra"], material=chimney.get("material", "brick"), pots=chimney["pots"])

    for feature in spec["features"]:
        FEATURES[feature](b, house)

    return roof_top


def paint_upper_wall(b: Builder, house: House, spec: dict, ground: str) -> None:
    """Chalet: the upper storeys are clad in horizontal boards over the plaster."""
    if not spec.get("upper_wall"):
        return

    material, hex_value = spec["upper_wall"]
    b.box((-house.half, house.setback - 0.04, house.levels[1]), (house.half, house.setback, house.top), material, srgb(hex_value), uv=("band", *WOOD_LIGHT_BAND, 2.0))


def window_axes(house: House, spec: dict, storey: int, bays: list, door_u: float, width: float) -> list:
    """Window axes of a storey: every bay upstairs; downstairs the bays left free by the door (or the archetype's
    own ground rhythm, e.g. one wide shop window)."""
    if storey > 0:
        return bays

    if spec.get("ground_bays"):
        return [u for u in house.bays(spec["ground_bays"]) if abs(u - door_u) > width / 2.0]

    return [u for u in bays if abs(u - door_u) > 0.1]


def draw_storey_windows(b: Builder, house: House, spec: dict, storey: int, bays: list, door_u: float) -> None:
    shape = window_shape(spec, storey)

    if shape is None:
        return

    top, width, height, sill, shutters, bars = shape
    shrink = spec.get("shrink", 0.0) * storey
    bottom = house.levels[storey] + sill
    axes = window_axes(house, spec, storey, bays, door_u, width)
    front = house.setback - house.jetty * storey + (house.ground_recess if storey == 0 else 0.0)

    for u in axes:
        draw_window(b, house, Opening(u, width, bottom, max(0.6, height - shrink), top), shutters=shutters, bars=bars, front=front)


def build_archetype_model(archetype: str, width: float, variant: int) -> dict:
    """Build and export art/town/houses/<archetype>_w<width>_<variant>.gltf with its sidecar."""
    name = f"{archetype}_w{int(width)}_{variant}"
    b = Builder(name)
    house = make_house(archetype, width, variant)

    build_house(b, house, ARCHETYPE_SPECS[archetype])

    return b.finish(HOUSE_DIR / f"{name}.gltf", {"lot_width": width, "lot_depth": HOUSE_ARCHETYPES[archetype][1], "archetype": archetype, "variant": variant, "doors": house.doors})


def build_alley_gate() -> dict:
    """1 m wide alley closure (scaled across the alley in the scene): wall 2.2 m with a plank gate, one collider."""
    b = Builder("alley_gate")
    stone = srgb(STONE["media"])

    b.box((-0.5, 0.0, 0.0), (0.5, 0.35, ALLEY_WALL_HEIGHT), "stone", stone)
    b.box((-0.5, -0.04, 0.0), (0.5, 0.0, 1.9), "wood", srgb(WOOD["media"]), uv=("band", *WOOD_LIGHT_BAND, 1.0))
    b.box((-0.48, -0.05, ALLEY_WALL_HEIGHT), (0.48, 0.4, ALLEY_WALL_HEIGHT + 0.12), "trim", srgb(STONE["clara"]))
    b.collider((-0.5, 0.0, 0.0), (0.5, 0.35, ALLEY_WALL_HEIGHT))

    return b.finish(HOUSE_DIR / "alley_gate.gltf", {"lot_width": 1.0, "lot_depth": 0.4, "doors": []})


# ---------- enterable shops (seção D) ----------

def wall_piece(b: Builder, minimum: tuple, maximum: tuple, material: str, tint: tuple, frame: Matrix = None) -> None:
    """One wall slab, seen from both sides, with its own collider (doors and windows are real gaps)."""
    b.box(minimum, maximum, material, tint, frame=frame)
    b.collider(minimum, maximum, frame)


def open_frame(b: Builder, opening: Opening, expand: float, depth_from: float, depth_to: float, tint: tuple, band: tuple, frame: Matrix = None) -> None:
    """Moulding around an opening that stays open (shop door, vitrine): two jambs and a band over the top."""
    half = opening.width / 2.0
    outer_arc = opening.arc(expand)
    inner_arc = opening.arc()
    jamb_top = max(outer_arc[0][1], inner_arc[0][1])

    for jamb_left in (opening.u - half - expand, opening.u + half):
        b.box((jamb_left, depth_from, opening.bottom), (jamb_left + expand, depth_to, jamb_top), "trim", tint, frame=frame, uv=("band", *band, 1.0))

    b.prism(outer_arc + list(reversed(inner_arc)), depth_from, depth_to, "trim", tint, frame=frame, uv=("band", *band, 1.0))


# ---------- main ----------

def planned_models() -> dict:
    """Model name -> builder call, for every model the town plan uses (plus the alley gate)."""
    lots = town_lots()
    houses = {f"{lot['archetype']}_w{int(lot['width'])}_{lot['variant']}": (lot["archetype"], lot["width"], lot["variant"]) for lot in lots if lot["kind"] == "house"}
    models = {name: (lambda arguments=arguments: build_archetype_model(*arguments)) for name, arguments in houses.items()}
    models["alley_gate"] = build_alley_gate

    return models


def check_roof_families() -> None:
    """The town plan picks archetypes by ridge direction (build_hub_scene.STREET_GABLE_ARCHETYPES): keep it true."""
    street_gables = {name for name, spec in ARCHETYPE_SPECS.items() if spec["roof"][0] == "gable_street"}

    assert street_gables == set(STREET_GABLE_ARCHETYPES), f"empenas para a rua: {sorted(street_gables)} != {STREET_GABLE_ARCHETYPES}"


if __name__ == "__main__":
    check_roof_families()
    requested = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    models = planned_models()

    for model_name in requested or sorted(models):
        sidecar = models[model_name]()
        print(f"BUILT {model_name}: aabb {sidecar['aabb_min']} .. {sidecar['aabb_max']}, lot {sidecar['lot_width']}")
