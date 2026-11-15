"""Old square trees and royal palms for the plazas (Blender bmesh -> glTF).

README (numbers are measured from the generated meshes; "canopy_r" is the horizontal reach of the leaf mass,
"root_r" the horizontal reach of the buttress roots, trunk collider = `Trunk-colonly`, 3 m tall cylinder at the trunk radius):

  model (art/town/trees/)   trunk_r  root_r  canopy_r  canopy base z  height   note
  old_tree_1.gltf           @T1      @R1     @C1       @B1            @H1      broad umbrella
  old_tree_2.gltf           @T2      @R2     @C2       @B2            @H2      taller, narrower
  old_tree_3.gltf           @T3      @R3     @C3       @B3            @H3      asymmetric, leaning
  old_tree_4.gltf           @T4      @R4     @C4       @B4            @H4      widest
  old_tree_5.gltf           @T5      @R5     @C5       @B5            @H5      hanging vines
  old_tree_6.gltf           @T6      @R6     @C6       @B6            @H6      asymmetric, twisted trunk

  palm (art/town/)          trunk_r  height   fronds reach
  palm_9.gltf               0.36     @P9      ~4 m radius crown
  palm_11.gltf              0.36     @P11
  palm_14.gltf              0.36     @P14

Placement: keep the trunk >= root_r + 0.3 m from any path edge; the canopy may overhang paths (leaf mass starts
above "canopy base z"). Origin = trunk base center, +Y up in Godot. 3 materials per tree (bark, leaf mass, leaf cards),
2 per palm (trunk, frond card). Vertex colors carry all the tinting (linear, multiplied by the textures in Godot).

Textures generated here (numpy): art/town/trees/textures/T_OldBark.png, T_LeafCluster.png; art/town/textures/T_PalmFrond.png.

Usage:
  blender -b --factory-startup -P tools_src/build_trees.py [-- old_tree_1 palm_9 ...]
"""

import json
import math
import random
import sys
from pathlib import Path

import bmesh
import bpy
import numpy
from mathutils import Vector

PROJECT_DIR = Path(__file__).resolve().parent.parent
TOWN_DIR = PROJECT_DIR / "art" / "town"
TREE_DIR = TOWN_DIR / "trees"

# Palette (style bible): foliage #245A3A -> #3F8A50 -> #7FC46A, bark #8B5A3C darkened.
FOLIAGE_STOPS = ("#17402C", "#2F7442", "#6FB45C")
SUNLIT_LEAF = "#A9C25A"
BARK_COLOR = "#6E4A33"
MOSS_COLOR = "#3F8A50"
PALM_TRUNK_STOPS = ("#8F8068", "#B9A98F")

TREE_VARIANTS = {
    # trunk_r: radius at 1.3 m; fork: first fork height; lean: trunk offset at the fork; primaries / secondaries per primary: branch counts
    # leader: length of the near-vertical central limb; tops: extra loose clumps above the fork; clump: radius range of a leaf clump
    "old_tree_1": dict(seed=11, trunk_r=0.78, fork=3.4, lean=0.4, primaries=4, secondaries=2, leader=6.6, tops=1, length=(4.6, 5.4), elevation=(36, 52), bend=0.3, clump=(2.5, 3.1), flatten=0.79, roots=6),
    "old_tree_2": dict(seed=23, trunk_r=0.62, fork=3.8, lean=0.3, primaries=3, secondaries=2, leader=8.0, tops=2, length=(4.0, 4.8), elevation=(24, 38), bend=0.1, clump=(2.3, 2.9), flatten=0.92, roots=5),
    "old_tree_3": dict(seed=37, trunk_r=0.72, fork=3.0, lean=0.7, primaries=3, secondaries=2, leader=6.6, tops=1, length=(4.8, 6.0), elevation=(34, 56), bend=0.3, clump=(2.5, 3.2), flatten=0.82, roots=6, one_sided=True),
    "old_tree_4": dict(seed=41, trunk_r=0.84, fork=3.2, lean=0.35, primaries=5, secondaries=1, leader=5.8, tops=1, length=(5.4, 6.2), elevation=(44, 58), bend=0.4, clump=(2.7, 3.3), flatten=0.74, roots=7),
    "old_tree_5": dict(seed=59, trunk_r=0.7, fork=3.6, lean=0.45, primaries=4, secondaries=2, leader=7.2, tops=1, length=(4.8, 5.6), elevation=(36, 50), bend=0.3, clump=(2.5, 3.1), flatten=0.82, roots=6, vines=8),
    "old_tree_6": dict(seed=67, trunk_r=0.66, fork=3.2, lean=0.55, primaries=3, secondaries=2, leader=7.0, tops=2, length=(4.6, 5.8), elevation=(30, 50), bend=0.25, clump=(2.4, 3.0), flatten=0.87, roots=5, one_sided=True, twist=0.5),
}
PALM_VARIANTS = {
    "palm_9": dict(seed=3, height=9.0),
    "palm_11": dict(seed=5, height=11.5),
    "palm_14": dict(seed=8, height=14.0),
}

CANOPY_BASE_MIN = 4.6
CLUMP_ICOSPHERE_SUBDIVISIONS = 2
CARDS_PER_CLUMP = 72


# ---------------------------------------------------------------- colors


def srgb_to_linear(value: float) -> float:
    return value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4


def hex_color(text: str, scale: float = 1.0) -> tuple:
    red, green, blue = (int(text[index:index + 2], 16) / 255.0 for index in (1, 3, 5))

    return (srgb_to_linear(red) * scale, srgb_to_linear(green) * scale, srgb_to_linear(blue) * scale, 1.0)


def mix_colors(first: tuple, second: tuple, amount: float) -> tuple:
    return tuple(first[index] + (second[index] - first[index]) * amount for index in range(4))


def ramp_color(stops: tuple, amount: float) -> tuple:
    amount = min(1.0, max(0.0, amount)) * (len(stops) - 1)
    index = min(int(amount), len(stops) - 2)

    return mix_colors(hex_color(stops[index]), hex_color(stops[index + 1]), amount - index)


# ---------------------------------------------------------------- textures and materials


def new_image(name: str, pixels: numpy.ndarray) -> bpy.types.Image:
    height, width = pixels.shape[:2]
    image = bpy.data.images.new(name, width, height, alpha=True)

    linear = pixels.copy()
    linear[..., :3] = numpy.where(linear[..., :3] <= 0.04045, linear[..., :3] / 12.92, ((linear[..., :3] + 0.055) / 1.055) ** 2.4)  # pixels are sRGB-authored; Blender wants linear
    image.pixels.foreach_set(linear.astype(numpy.float32).ravel())
    image.filepath_raw = str(Path(bpy.app.tempdir) / f"{name}.png")
    image.file_format = "PNG"
    image.save()

    # The exporter re-encodes generated images as black; a file-backed copy is copied byte for byte.
    saved_path = image.filepath_raw
    bpy.data.images.remove(image)

    return bpy.data.images.load(saved_path)


def paint_bark_image() -> numpy.ndarray:
    """Vertical bark ridges with horizontal cracks; neutral grey so vertex colors give the hue. Tiles in both axes."""
    size = 256
    generator = numpy.random.default_rng(4)
    columns = generator.random(size // 4 + 1)
    ridge = numpy.interp(numpy.arange(size) / 4.0, numpy.arange(len(columns)), numpy.concatenate([columns[:-1], columns[:1]]))
    rows = numpy.arange(size)[:, None]
    wobble = numpy.sin(rows / size * 2 * math.pi * 3 + ridge[None, :] * 6.0) * 0.5 + 0.5
    cracks = (generator.random((size // 8, size)) > 0.93).astype(float)
    cracks = numpy.repeat(cracks, 8, axis=0) * 0.25
    value = 0.62 + 0.28 * ridge[None, :] * wobble + 0.1 * generator.random((size, size)) - cracks
    value = numpy.clip(value, 0.25, 1.0)
    rgba = numpy.dstack([value, value * 0.97, value * 0.93, numpy.ones_like(value)])

    return rgba


def paint_leaf_cluster_image() -> numpy.ndarray:
    """A painterly clump of leaves with alpha: lighter on top, darker toward the middle."""
    size = 256
    generator = numpy.random.default_rng(5)
    grid_y, grid_x = numpy.mgrid[0:size, 0:size]
    grid_x = (grid_x + 0.5) / size
    grid_y = (grid_y + 0.5) / size
    rgba = numpy.zeros((size, size, 4))
    rgba[..., :3] = 0.7

    for _ in range(150):
        angle_around = generator.uniform(0, 2 * math.pi)
        distance = 0.36 * math.sqrt(generator.random())
        center_x, center_y = 0.5 + distance * math.cos(angle_around), 0.5 + distance * math.sin(angle_around)
        angle = angle_around + generator.normal(0, 0.8)
        half_length = generator.uniform(0.06, 0.1)
        half_width = generator.uniform(0.028, 0.045)
        along = (grid_x - center_x) * math.cos(angle) + (grid_y - center_y) * math.sin(angle)
        across = -(grid_x - center_x) * math.sin(angle) + (grid_y - center_y) * math.cos(angle)
        profile = half_width * (1.0 - (along / half_length) ** 2)
        inside = (numpy.abs(along) < half_length) & (numpy.abs(across) < profile)
        brightness = 0.58 + 0.42 * numpy.clip((center_y - 0.15) / 0.7, 0, 1) + generator.normal(0, 0.06)
        brightness *= 0.92 + 0.14 * distance / 0.36
        shade = brightness + 0.1 * numpy.clip(across / half_width, -1, 1) - 0.12 * (numpy.abs(across) > 0.8 * profile)
        shade = numpy.where(numpy.abs(across) < 0.1 * half_width, shade * 0.85, shade)
        rgba[inside, :3] = numpy.clip(shade[inside], 0.2, 1.0)[:, None] * numpy.array([0.97, 1.0, 0.9])
        rgba[inside, 3] = 1.0

    return rgba


def paint_palm_frond_image() -> numpy.ndarray:
    """One side of a pinnate frond: u along the rib (0 = base), v from the rib (bottom row) to the leaflet tips (top row)."""
    width, height = 512, 128
    rgba = numpy.zeros((height, width, 4))
    rgba[..., :3] = 0.7
    leaflet_count = 58

    for leaflet in range(leaflet_count):
        along = (leaflet + 0.5) / leaflet_count
        reach = 0.97 * max(0.12, math.sin(math.pi * (0.05 + 0.9 * along))) ** 0.45
        steps = numpy.linspace(0.05, reach, 110)
        columns = ((along + 0.07 * steps) * width).astype(int)
        rows = (steps * (height - 1)).astype(int)
        shade = 0.55 + 0.45 * steps
        for thickness in (0, 1, 2):
            valid = (columns + thickness < width) & (thickness < 3 - 2 * steps)
            rgba[rows[valid], (columns + thickness)[valid], :3] = shade[valid, None] * numpy.array([0.95, 1.0, 0.88])
            rgba[rows[valid], (columns + thickness)[valid], 3] = 1.0

    rgba[:6, :, :3] = 0.95
    rgba[:6, :, 3] = 1.0

    return rgba


def make_material(name: str, image=None, use_alpha: bool = False, roughness: float = 0.9) -> bpy.types.Material:
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    shader = material.node_tree.nodes["Principled BSDF"]

    shader.inputs["Base Color"].default_value = (1.0, 1.0, 1.0, 1.0)
    shader.inputs["Roughness"].default_value = roughness

    if image is not None:
        texture = material.node_tree.nodes.new("ShaderNodeTexImage")
        texture.image = image
        material.node_tree.links.new(texture.outputs["Color"], shader.inputs["Base Color"])

        if use_alpha:
            material.node_tree.links.new(texture.outputs["Alpha"], shader.inputs["Alpha"])
            material.use_backface_culling = False

    return material


# ---------------------------------------------------------------- mesh building blocks


class Part:
    """One output mesh: a bmesh with a UV layer and a float color layer, tagged with its material."""

    def __init__(self, name: str, material) -> None:
        self.name = name
        self.material = material
        self.mesh = bmesh.new()
        self.uv_layer = self.mesh.loops.layers.uv.new("UVMap")
        self.color_layer = self.mesh.loops.layers.float_color.new("Color")

    def add_face(self, vertices: list, colors: list, uvs: list = None, smooth: bool = True):
        face = self.mesh.faces.new(vertices)
        face.smooth = smooth

        for index, loop in enumerate(face.loops):
            loop[self.color_layer] = colors[index]

            if uvs is not None:
                loop[self.uv_layer].uv = uvs[index]

        return face

    def to_object(self) -> bpy.types.Object:
        mesh_data = bpy.data.meshes.new(self.name)

        self.mesh.to_mesh(mesh_data)
        mesh_data.materials.append(self.material)
        mesh_data.color_attributes.active_color = mesh_data.color_attributes["Color"]
        mesh_data.color_attributes.render_color_index = 0
        mesh_object = bpy.data.objects.new(self.name, mesh_data)
        bpy.context.scene.collection.objects.link(mesh_object)

        return mesh_object


def tube(part: Part, points: list, radii: list, sides: int, color_function, flute: float = 0.0, twist: float = 0.0, cap_top: bool = False, uv_scale: float = 0.5) -> None:
    """Round tube along a path. color_function(position, ring_index, angle_index) -> rgba. flute = radius ripple (old bark)."""
    rings = []
    normal = None
    travelled = 0.0

    for index, center in enumerate(points):
        tangent = (points[min(index + 1, len(points) - 1)] - points[max(index - 1, 0)]).normalized()

        if normal is None:
            reference = Vector((1, 0, 0)) if abs(tangent.x) < 0.9 else Vector((0, 1, 0))
            normal = tangent.cross(reference).normalized()
        else:
            normal = (normal - tangent * normal.dot(tangent)).normalized()

        binormal = tangent.cross(normal)

        if index:
            travelled += (center - points[index - 1]).length

        ring = []

        for side in range(sides):
            angle = 2 * math.pi * side / sides + twist * index
            radius = radii[index] * (1.0 + flute * math.sin(3 * angle + index * 1.1))
            ring.append(part.mesh.verts.new(center + (normal * math.cos(angle) + binormal * math.sin(angle)) * radius))

        rings.append((ring, center, travelled))

    for index in range(len(rings) - 1):
        lower, lower_center, lower_distance = rings[index]
        upper, upper_center, upper_distance = rings[index + 1]

        for side in range(sides):
            following = (side + 1) % sides
            corners = [lower[side], lower[following], upper[following], upper[side]]
            colors = [color_function(corner.co, ring_index, side_index) for corner, ring_index, side_index in zip(corners, (index, index, index + 1, index + 1), (side, side + 1, side + 1, side))]
            uvs = [(side / sides * 2.0, lower_distance * uv_scale), ((side + 1) / sides * 2.0, lower_distance * uv_scale), ((side + 1) / sides * 2.0, upper_distance * uv_scale), (side / sides * 2.0, upper_distance * uv_scale)]
            part.add_face(corners, colors, uvs)

    if cap_top:
        top, top_center, top_distance = rings[-1]
        part.add_face(list(reversed(top)), [color_function(vertex.co, len(rings) - 1, 0) for vertex in reversed(top)], [(0.5, 0.5)] * len(top), smooth=False)


def radial_basis(direction: Vector) -> tuple:
    reference = Vector((0, 0, 1)) if abs(direction.z) < 0.95 else Vector((1, 0, 0))
    first = direction.cross(reference).normalized()

    return first, direction.cross(first)


# ---------------------------------------------------------------- old tree


def trunk_radius_at(height: float, base_radius: float, fork: float) -> float:
    taper = 1.0 - 0.2 * height / fork
    flare = 1.0 + 0.8 * max(0.0, 1.0 - height / 0.8) ** 2

    return base_radius * taper * flare


def bark_color_function(base_scale: float, moss_height: float = 0.7):
    def color(position: Vector, ring_index: int, side_index: int):
        height_fade = min(1.0, position.z / 4.0)
        crevice = 0.82 + 0.18 * (side_index % 2)
        tint = hex_color(BARK_COLOR, base_scale * crevice * (0.8 + 0.3 * height_fade))

        return mix_colors(tint, hex_color(MOSS_COLOR, 0.55), 0.35 * max(0.0, 1.0 - position.z / max(moss_height, 0.001)) * (side_index % 3 == 0))

    return color


def build_roots(part: Part, rng: random.Random, params: dict, base_radius: float) -> float:
    """Tabular buttress roots: thin triangular fins around the base. Returns the horizontal reach."""
    count = params["roots"]
    offset = rng.uniform(0, 2 * math.pi)
    reach_max = 0.0

    for root_index in range(count):
        angle = offset + 2 * math.pi * root_index / count + rng.uniform(-0.28, 0.28)
        length = rng.uniform(1.2, 2.0)
        top_height = rng.uniform(0.5, 0.9)
        flare_radius = trunk_radius_at(0.4, base_radius, params["fork"])
        inner = flare_radius * 0.85
        tip = flare_radius + length
        reach_max = max(reach_max, tip)
        steps = 5
        top_line, bottom_line = [], []
        direction = Vector((math.cos(angle), math.sin(angle), 0))
        side = Vector((-direction.y, direction.x, 0))
        bend = rng.uniform(-0.25, 0.25)

        for step in range(steps + 1):
            amount = step / steps
            distance = inner + (tip - inner) * amount
            lateral = bend * amount * amount * length
            thickness = 0.1 * (1.0 - 0.55 * amount)
            top = top_height * (1.0 - amount) ** 1.7 + 0.04 * (1.0 - amount)
            base_point = direction * distance + side * lateral
            top_line.append((base_point + side * thickness + Vector((0, 0, top)), base_point - side * thickness + Vector((0, 0, top))))
            bottom_line.append((base_point + side * thickness + Vector((0, 0, -0.12)), base_point - side * thickness + Vector((0, 0, -0.12))))

        moss_top = mix_colors(hex_color(BARK_COLOR, 0.8), hex_color(MOSS_COLOR, 0.6), 0.5)
        dark = hex_color(BARK_COLOR, 0.55)
        verts_top = [(part.mesh.verts.new(left), part.mesh.verts.new(right)) for left, right in top_line]
        verts_bottom = [(part.mesh.verts.new(left), part.mesh.verts.new(right)) for left, right in bottom_line]

        for step in range(steps):
            left_quad = [verts_top[step][0], verts_top[step + 1][0], verts_bottom[step + 1][0], verts_bottom[step][0]]
            right_quad = [verts_top[step + 1][1], verts_top[step][1], verts_bottom[step][1], verts_bottom[step + 1][1]]
            top_quad = [verts_top[step][1], verts_top[step + 1][1], verts_top[step + 1][0], verts_top[step][0]]
            uv_a, uv_b = (0.0, step * 0.4), (1.0, (step + 1) * 0.4)
            part.add_face(left_quad, [moss_top, moss_top, dark, dark], [(0, uv_a[1]), (0, uv_b[1]), (0.3, uv_b[1]), (0.3, uv_a[1])], smooth=False)
            part.add_face(right_quad, [moss_top, moss_top, dark, dark], [(0, uv_b[1]), (0, uv_a[1]), (0.3, uv_a[1]), (0.3, uv_b[1])], smooth=False)
            part.add_face(top_quad, [moss_top] * 4, [(0.4, uv_a[1]), (0.4, uv_b[1]), (0.6, uv_b[1]), (0.6, uv_a[1])], smooth=False)

        part.add_face([verts_top[-1][0], verts_top[-1][1], verts_bottom[-1][1], verts_bottom[-1][0]], [dark] * 4, [(0, 0)] * 4, smooth=False)

    return reach_max


def build_branch(part: Part, rng: random.Random, start: Vector, azimuth: float, elevation: float, bend: float, length: float, radius_start: float, radius_end: float, sides: int, points_count: int) -> list:
    """Curved branch; returns the path points."""
    points = [start]
    position = start.copy()
    radii = []

    for step in range(1, points_count):
        amount = step / (points_count - 1)
        polar = elevation + bend * amount
        direction = Vector((math.sin(polar) * math.cos(azimuth), math.sin(polar) * math.sin(azimuth), math.cos(polar)))
        position = position + direction * (length / (points_count - 1)) + Vector((rng.uniform(-0.18, 0.18), rng.uniform(-0.18, 0.18), rng.uniform(-0.08, 0.08)))
        points.append(position.copy())

    for step in range(points_count):
        radii.append(radius_start + (radius_end - radius_start) * step / (points_count - 1))

    tube(part, points, radii, sides, bark_color_function(1.0, 0.0), flute=0.06)

    return points


def clump_color(unit: Vector, height_fraction: float, jitter: float, brighten: float = 0.0) -> tuple:
    """Foliage ramp: dark underneath/inside, light on top (painted shading; Godot adds the real light)."""
    amount = 0.0 + 0.34 * (unit.z * 0.5 + 0.5) + 0.3 * height_fraction + jitter + brighten
    color = ramp_color(FOLIAGE_STOPS, amount)

    return mix_colors(color, hex_color(SUNLIT_LEAF, 0.6), max(0.0, amount - 0.75) * 0.9)


def add_clump(leaf_part: Part, card_part: Part, rng: random.Random, center: Vector, radius: float, flatten: float, height_range: tuple) -> None:
    """Leaf mass: a flattened, lumpy icosphere with a flat-ish underside, plus leaf cards on its skin for a ragged silhouette."""
    result = bmesh.ops.create_icosphere(leaf_part.mesh, subdivisions=CLUMP_ICOSPHERE_SUBDIVISIONS, radius=1.0)
    verts = result["verts"]
    jitter = rng.uniform(-0.05, 0.05)
    phase = [rng.uniform(0, 6.28) for _ in range(3)]
    radius_z = radius * flatten

    for vertex in verts:
        unit = vertex.co.copy()
        lump = 1.0 + 0.1 * math.sin(unit.x * 4.1 + phase[0]) + 0.1 * math.sin(unit.y * 4.7 + phase[1]) + 0.08 * math.sin(unit.z * 5.3 + phase[2]) + rng.uniform(-0.04, 0.04)
        squash = 1.0 if unit.z > 0 else 0.55
        vertex.co = center + Vector((unit.x * radius * lump, unit.y * radius * lump, unit.z * radius_z * lump * squash))
        vertex.normal_update()

    faces = {face for vertex in verts for face in vertex.link_faces}
    bottom, top = height_range

    for face in faces:
        face.smooth = True

        for loop in face.loops:
            unit = (loop.vert.co - center)
            unit = Vector((unit.x / radius, unit.y / radius, unit.z / radius_z)).normalized()
            height_fraction = (loop.vert.co.z - bottom) / max(top - bottom, 1.0)
            loop[leaf_part.color_layer] = clump_color(unit, height_fraction, jitter)

    for _ in range(CARDS_PER_CLUMP):
        unit = Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-0.15, 1.0))).normalized()
        surface = center + Vector((unit.x * radius, unit.y * radius, unit.z * radius_z * (1.0 if unit.z > 0 else 0.55)))
        surface += unit * radius * 0.08
        first, second = radial_basis(unit)
        roll = rng.uniform(0, math.pi)
        axis_a = first * math.cos(roll) + second * math.sin(roll)
        axis_b = unit.cross(axis_a)
        half = rng.uniform(0.7, 1.1)
        corners = [surface + axis_a * (-half) + axis_b * (-half), surface + axis_a * half + axis_b * (-half), surface + axis_a * half + axis_b * half, surface + axis_a * (-half) + axis_b * half]
        verts_card = [card_part.mesh.verts.new(corner) for corner in corners]
        height_fraction = (surface.z - bottom) / max(top - bottom, 1.0)
        color = clump_color(unit, height_fraction, jitter, brighten=0.16)
        card_part.add_face(verts_card, [color] * 4, [(0, 0), (1, 0), (1, 1), (0, 1)], smooth=False)


def build_vines(part: Part, rng: random.Random, anchors: list, count: int) -> None:
    for _ in range(count):
        anchor = rng.choice(anchors)
        length = rng.uniform(1.6, 3.0)
        sway = Vector((rng.uniform(-0.2, 0.2), rng.uniform(-0.2, 0.2), 0))
        points = [anchor + sway * (step / 5.0) + Vector((0, 0, -length * step / 5.0)) for step in range(6)]
        radii = [0.045 - 0.025 * step / 5.0 for step in range(6)]
        tube(part, points, radii, 4, lambda position, ring, side: hex_color("#2F6B45", 0.9))


def build_old_tree(name: str, params: dict) -> dict:
    rng = random.Random(params["seed"])
    bark_image = bpy.data.images.get("T_OldBark") or new_image("T_OldBark", paint_bark_image())
    card_image = bpy.data.images.get("T_LeafCluster") or new_image("T_LeafCluster", paint_leaf_cluster_image())
    bark = Part("Bark", make_material("M_OldBark", bark_image, roughness=0.95))
    leaf = Part("LeafMass", make_material("M_OldLeaf", None, roughness=0.9))
    cards = Part("LeafCards", make_material("M_OldLeafCard", card_image, use_alpha=True, roughness=0.9))
    fork = params["fork"]
    base_radius = params["trunk_r"] / (1.0 - 0.2 * 1.3 / fork)
    lean_azimuth = rng.uniform(0, 2 * math.pi)
    lean_vector = Vector((math.cos(lean_azimuth), math.sin(lean_azimuth), 0))
    heights = [0.0, 0.35, 0.8, 1.3] + [1.3 + (fork - 1.3) * step / 3.0 for step in range(1, 4)]
    trunk_points = [Vector((0, 0, height)) + lean_vector * params["lean"] * (height / fork) ** 1.6 for height in heights]
    trunk_radii = [trunk_radius_at(height, base_radius, fork) for height in heights]

    tube(bark, trunk_points, trunk_radii, 10, bark_color_function(1.0), flute=0.09, twist=params.get("twist", 0.12), cap_top=True)
    root_reach = build_roots(bark, rng, params, base_radius)

    fork_point = trunk_points[-1]
    clump_specs = []
    branch_anchors = []
    primary_count = params["primaries"]
    azimuth_start = rng.uniform(0, 2 * math.pi)
    span = math.pi if params.get("one_sided") else 2 * math.pi
    top_radius = trunk_radii[-1]

    for index in range(primary_count):
        azimuth = azimuth_start + span * index / primary_count + rng.uniform(-0.3, 0.3)
        elevation = math.radians(rng.uniform(*params["elevation"]))
        length = rng.uniform(*params["length"])
        start = fork_point + Vector((math.cos(azimuth), math.sin(azimuth), 0)) * top_radius * 0.3
        points = build_branch(bark, rng, start, azimuth, elevation, params["bend"], length, top_radius * 0.62, 0.11, 7, 6)
        tip = points[-1]
        branch_anchors.extend(points[2:5])
        clump_specs.append((tip + Vector((0, 0, 0.6)), rng.uniform(*params["clump"])))
        clump_specs.append((points[3] + Vector((0, 0, 0.9)), rng.uniform(*params["clump"]) * 0.82))

        for secondary in range(params["secondaries"]):
            amount = 0.5 + 0.2 * secondary
            origin = points[min(len(points) - 1, int(amount * (len(points) - 1)) + 1)]
            side = 1.0 if secondary % 2 == 0 else -1.0
            sub_azimuth = azimuth + side * rng.uniform(0.6, 0.95)
            sub_points = build_branch(bark, rng, origin, sub_azimuth, math.radians(rng.uniform(52, 72)), -0.45, rng.uniform(2.2, 3.2), 0.12, 0.05, 5, 4)
            branch_anchors.extend(sub_points[1:])
            clump_specs.append((sub_points[-1] + Vector((0, 0, 0.5)), rng.uniform(params["clump"][0] * 0.8, params["clump"][1] * 0.92)))

    leader_azimuth = rng.uniform(0, 2 * math.pi)
    leader_points = build_branch(bark, rng, fork_point, leader_azimuth, math.radians(rng.uniform(8, 18)), 0.1, params["leader"], top_radius * 0.6, 0.12, 6, 5)
    branch_anchors.extend(leader_points[2:])
    clump_specs.append((leader_points[-1] + Vector((0, 0, 0.9)), rng.uniform(*params["clump"])))
    clump_specs.append((leader_points[2] + Vector((0, 0, 0.8)), rng.uniform(*params["clump"]) * 0.85))

    for _ in range(params["tops"]):
        offset = Vector((rng.uniform(-3.0, 3.0), rng.uniform(-3.0, 3.0), 0))
        clump_specs.append((leader_points[-1] + offset + Vector((0, 0, rng.uniform(-0.2, 0.9))), rng.uniform(*params["clump"]) * 0.85))

    lowest = []

    for center, radius in clump_specs:
        center.z = max(center.z, CANOPY_BASE_MIN + radius * params["flatten"] * 0.55)
        lowest.append(center.z - radius * params["flatten"] * 0.55)

    top_of_canopy = max(center.z + radius * params["flatten"] for center, radius in clump_specs)
    bottom_of_canopy = min(lowest)

    for center, radius in clump_specs:
        add_clump(leaf, cards, rng, center, radius, params["flatten"], (bottom_of_canopy, top_of_canopy))

    if params.get("vines"):
        build_vines(leaf, rng, [anchor for anchor in branch_anchors if Vector((anchor.x, anchor.y, 0)).length > 1.5], params["vines"])

    collider = add_trunk_collider(params["trunk_r"] * 1.02)

    return {"objects": [bark.to_object(), leaf.to_object(), cards.to_object(), collider], "trunk_r": params["trunk_r"], "root_r": root_reach}


def add_trunk_collider(radius: float) -> bpy.types.Object:
    collider_mesh = bmesh.new()

    bmesh.ops.create_cone(collider_mesh, cap_ends=True, segments=10, radius1=radius, radius2=radius, depth=3.0)
    bmesh.ops.translate(collider_mesh, vec=(0, 0, 1.5), verts=collider_mesh.verts)
    mesh_data = bpy.data.meshes.new("Trunk-colonly")
    collider_mesh.to_mesh(mesh_data)
    collider = bpy.data.objects.new("Trunk-colonly", mesh_data)
    bpy.context.scene.collection.objects.link(collider)

    return collider


# ---------------------------------------------------------------- royal palm


def palm_trunk_radius(height: float, trunk_height: float) -> float:
    belly = 0.05 * math.exp(-(((height - trunk_height / 3.0) / (trunk_height * 0.22)) ** 2))
    flare = 0.05 * max(0.0, 1.0 - height / 0.5)

    return 0.31 * (1.0 - 0.16 * height / trunk_height) + belly + flare


def build_frond(part: Part, yaw: float, pitch: float, length: float, droop: float, tint: float, origin: Vector) -> None:
    """Arching pinnate frond as two folded strips (V section) sharing the rib; leaflets come from the alpha texture."""
    steps = 8
    rib, left, right = [], [], []
    cos_yaw, sin_yaw = math.cos(yaw), math.sin(yaw)

    def place(local: Vector) -> Vector:
        return origin + Vector((local.x * cos_yaw - local.y * sin_yaw, local.x * sin_yaw + local.y * cos_yaw, local.z))

    for step in range(steps + 1):
        amount = step / steps
        out = math.cos(pitch) * length * amount
        rise = math.sin(pitch) * length * amount - droop * length * amount * amount
        half_width = 0.62 * max(0.0, math.sin(math.pi * (0.04 + 0.92 * amount))) ** 0.7 + 0.03
        edge_drop = 0.5 * half_width + 0.25 * half_width * amount
        rib.append(part.mesh.verts.new(place(Vector((out, 0.0, rise)))))
        left.append(part.mesh.verts.new(place(Vector((out - 0.1 * half_width, half_width, rise - edge_drop)))))
        right.append(part.mesh.verts.new(place(Vector((out - 0.1 * half_width, -half_width, rise - edge_drop)))))

    for step in range(steps):
        amount_a, amount_b = step / steps, (step + 1) / steps
        base = ramp_color(FOLIAGE_STOPS, 0.45 + 0.4 * tint)
        tip = ramp_color(FOLIAGE_STOPS, 0.58 + 0.4 * tint)
        part.add_face([rib[step], rib[step + 1], left[step + 1], left[step]], [base, base, tip, tip], [(amount_a, 0), (amount_b, 0), (amount_b, 1), (amount_a, 1)], smooth=False)
        part.add_face([rib[step + 1], rib[step], right[step], right[step + 1]], [base, base, tip, tip], [(amount_b, 0), (amount_a, 0), (amount_a, 1), (amount_b, 1)], smooth=False)


def build_palm(name: str, params: dict) -> dict:
    rng = random.Random(params["seed"])
    frond_image = bpy.data.images.get("T_PalmFrond") or new_image("T_PalmFrond", paint_palm_frond_image())
    trunk = Part("PalmTrunk", make_material("M_PalmTrunk", None, roughness=0.9))
    fronds = Part("PalmFronds", make_material("M_PalmFrond", frond_image, use_alpha=True, roughness=0.85))
    trunk_height = params["height"] - 2.4
    lean = lambda height: Vector((0.3 * (height / trunk_height) ** 2, 0.1 * math.sin(height / trunk_height * 2.4), height))
    heights = [step * 0.3 for step in range(int(trunk_height / 0.3) + 1)]
    ring_scale = lambda index: 0.935 if index % 2 == 0 else 1.015
    radii = [palm_trunk_radius(height, trunk_height) * ring_scale(index) for index, height in enumerate(heights)]

    def trunk_color(position: Vector, ring_index: int, side_index: int):
        ring = ring_index % 2
        base = ramp_color(PALM_TRUNK_STOPS, position.z / trunk_height + 0.25 * ring)
        moss = max(0.0, 1.0 - position.z / 1.2)

        return mix_colors(mix_colors(base, hex_color("#8F8068", 0.75), 0.45 * (1 - ring)), hex_color("#4E7A4A", 0.7), 0.3 * moss)

    tube(trunk, [lean(height) for height in heights], radii, 10, trunk_color, cap_top=False, uv_scale=0.4)

    crown = lean(trunk_height)
    shaft_points = [crown + Vector((0, 0, 1.4 * step / 3.0)) for step in range(4)]
    shaft_radii = [0.27, 0.25, 0.2, 0.13]
    tube(trunk, shaft_points, shaft_radii, 10, lambda position, ring, side: ramp_color(("#3F8A50", "#7FC46A"), 0.3 + 0.4 * ring / 3.0 - 0.1), cap_top=True)

    layers = [(54.0, 3.5, 0.52, 1.0), (16.0, 3.9, 0.6, 0.6), (-22.0, 4.1, 0.55, 0.3)]
    yaw_offset = rng.uniform(0, math.tau)

    for layer_index, (pitch, length, droop, tint) in enumerate(layers):
        for frond_index in range(6):
            yaw = yaw_offset + math.tau * frond_index / 6.0 + layer_index * 0.55 + rng.uniform(-0.18, 0.18)
            attach = crown + Vector((0, 0, 1.15 - 0.22 * layer_index))
            build_frond(fronds, yaw, math.radians(pitch + rng.uniform(-5, 5)), length * rng.uniform(0.92, 1.08), droop, tint * rng.uniform(0.85, 1.0), attach)

    collider = add_trunk_collider(0.36)

    return {"objects": [trunk.to_object(), fronds.to_object(), collider], "trunk_r": 0.36, "root_r": 0.0}


# ---------------------------------------------------------------- export


def patch_gltf_materials(path: Path, card_material_names: tuple) -> None:
    """Cards need alpha-scissor + double sided in Godot; Blender writes them as BLEND."""
    document = json.loads(path.read_text(encoding="utf-8"))

    for material in document["materials"]:
        if material["name"] in card_material_names:
            material["alphaMode"] = "MASK"
            material["alphaCutoff"] = 0.5
            material["doubleSided"] = True

    path.write_text(json.dumps(document, indent=2), encoding="utf-8")


IMPORT_TEMPLATE = """[remap]

importer="scene"
importer_version=1
type="PackedScene"

[params]

nodes/root_type=""
nodes/root_name=""
nodes/root_script=null
mesh_library/use_node_names_as_mesh_names=false
array_mesh/deduplicate_surfaces=true
nodes/apply_root_scale=true
nodes/root_scale=1.0
nodes/import_as_skeleton_bones=false
nodes/use_name_suffixes=true
nodes/use_node_type_suffixes=true
meshes/ensure_tangents=true
meshes/generate_lods=true
meshes/create_shadow_meshes=true
meshes/light_baking=1
meshes/lightmap_texel_size=0.2
meshes/force_disable_compression=false
skins/use_named_skins=true
animation/import=true
animation/fps=30
animation/trimming=false
animation/remove_immutable_tracks=true
animation/import_rest_as_RESET=false
import_script/path=""
materials/extract=0
materials/extract_format=0
materials/extract_path=""
_subresources={}
gltf/naming_version=2
gltf/embedded_image_handling=1
gltf/texture_map_mode=1
"""

# Godot does not turn COLOR_0 into albedo on import, so every glTF material is swapped (via the .import) for a .tres with vertex colors on.
GODOT_MATERIALS = {
    "M_OldBark": ("tree_bark", "res://art/town/trees/textures/T_OldBark.png", False, 0.95),
    "M_OldLeaf": ("tree_leaf", None, False, 0.9),
    "M_OldLeafCard": ("tree_leaf_card", "res://art/town/trees/textures/T_LeafCluster.png", True, 0.9),
    "M_PalmTrunk": ("palm_trunk", None, False, 0.9),
    "M_PalmFrond": ("palm_frond", "res://art/town/textures/T_PalmFrond.png", True, 0.85),
}


def write_godot_material(material_name: str) -> str:
    file_name, texture_path, scissor, roughness = GODOT_MATERIALS[material_name]
    materials_dir = PROJECT_DIR / "art" / "materials"
    lines = ['[gd_resource type="StandardMaterial3D" format=3]', ""]

    if texture_path:
        lines = ['[gd_resource type="StandardMaterial3D" load_steps=2 format=3]', "", f'[ext_resource type="Texture2D" path="{texture_path}" id="1_texture"]', ""]

    lines += ["[resource]", f'resource_name = "{material_name}"']

    if scissor:
        lines += ["transparency = 2", "alpha_scissor_threshold = 0.5", "cull_mode = 2"]

    lines += ["vertex_color_use_as_albedo = true", f"roughness = {roughness}"]

    if texture_path:
        lines += ['albedo_texture = ExtResource("1_texture")']

    materials_dir.mkdir(exist_ok=True)
    (materials_dir / f"{file_name}.tres").write_text("\n".join(lines) + "\n", encoding="utf-8")

    return f"res://art/materials/{file_name}.tres"


def link_godot_materials(gltf_path: Path) -> None:
    """Point each glTF material of the model at its .tres through the sibling .import file."""
    document = json.loads(gltf_path.read_text(encoding="utf-8"))
    entries = []

    for material in document["materials"]:
        resource_path = write_godot_material(material["name"])
        entries.append(f'"{material["name"]}": {{\n"use_external/enabled": true,\n"use_external/fallback_path": "{resource_path}",\n"use_external/path": "{resource_path}"\n}}')

    block = '_subresources={\n"materials": {\n' + ",\n".join(entries) + "\n}\n}"
    import_path = gltf_path.with_suffix(".gltf.import")
    import_text = import_path.read_text(encoding="utf-8") if import_path.exists() else IMPORT_TEMPLATE
    start = import_text.index("_subresources=")
    end = import_text.index("\ngltf/naming_version")
    import_path.write_text(import_text[:start] + block + import_text[end:], encoding="utf-8")


def measure(objects: list) -> dict:
    """Horizontal canopy reach, canopy base and total height from the leaf meshes (Blender Z = up)."""
    leaf_vertices = [vertex.co for scene_object in objects if scene_object.name in ("LeafMass", "LeafCards", "PalmFronds") for vertex in scene_object.data.vertices]
    all_vertices = [vertex.co for scene_object in objects for vertex in scene_object.data.vertices]

    return {
        "canopy_r": max(math.hypot(co.x, co.y) for co in leaf_vertices),
        "canopy_base": min(co.z for co in leaf_vertices),
        "height": max(co.z for co in all_vertices),
        "tris": sum(len(scene_object.data.polygons) and sum(len(polygon.vertices) - 2 for polygon in scene_object.data.polygons) for scene_object in objects if "colonly" not in scene_object.name),
    }


def build_model(name: str) -> Path:
    bpy.ops.wm.read_factory_settings(use_empty=True)

    is_palm = name in PALM_VARIANTS
    result = build_palm(name, PALM_VARIANTS[name]) if is_palm else build_old_tree(name, TREE_VARIANTS[name])
    output_dir = TOWN_DIR if is_palm else TREE_DIR
    texture_dir = "textures"
    output_path = output_dir / f"{name}.gltf"
    stats = measure(result["objects"])

    output_dir.mkdir(parents=True, exist_ok=True)
    bpy.ops.export_scene.gltf(filepath=str(output_path), export_format="GLTF_SEPARATE", export_texture_dir=texture_dir, export_yup=True, export_vertex_color="ACTIVE", export_apply=False)
    patch_gltf_materials(output_path, ("M_OldLeafCard", "M_PalmFrond"))
    link_godot_materials(output_path)
    print(f"BUILT {name}: trunk_r={result['trunk_r']:.2f} root_r={result['root_r']:.2f} canopy_r={stats['canopy_r']:.2f} base_z={stats['canopy_base']:.2f} height={stats['height']:.2f} tris={stats['tris']} -> {output_path}")

    return output_path


if __name__ == "__main__":
    script_arguments = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []

    for requested_model in script_arguments or [*TREE_VARIANTS, *PALM_VARIANTS]:
        build_model(requested_model)
