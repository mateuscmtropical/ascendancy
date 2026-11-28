"""Pre-fractured destructible scenery for the destruction system.

Outputs, each with a JSON sidecar beside it (sections, substance, piece count, bounds in Godot coords):
  art/destruction/cottage.gltf      half-timbered cottage, 5 x 4 m, gable roof, end chimney
  art/destruction/field_wall.gltf   old free-standing stone wall, 8 x 2.2 x 0.6 m

Node contract read by the game:
  (scene root made by the Godot importer; the sections are the top-level glTF nodes)
    Section_<SUBSTANCE>_<Name>         empty at the centre of the section bounds; SUBSTANCE in WOOD, PLASTER, STONE
      Whole_<Name>                     the intact section as one mesh
      Pieces_<Name>                    empty
        Piece_<Name>_<NNN>             closed convex chunk, origin at its bounds centre, sitting where it belongs

Blender coords: origin on the ground at the footprint centre, front toward -Y (Godot +Z after export).

Every section is a list of convex solids (boxes and prisms). Each solid is cut on its own into Voronoi cells:
a copy of the solid per seed, bisected by the planes halfway to every other seed, each cut capped with the
"inner" material of the substance. Seeds sit on a jittered grid, which keeps slivers away. UVs are set on the
solid before the cuts, so the pieces together look exactly like the whole.

Usage:
  blender -b --factory-startup -P tools_src/build_destructibles.py [-- --preview <folder>]
"""

import itertools
import json
import math
import random
import sys
import time
from pathlib import Path
from typing import Callable, NamedTuple

import bmesh
import bpy
from mathutils import Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))

from build_town_houses import PROJECT_DIR, TEXTURE_DIR, WOOD_DARK_BAND, WOOD_LIGHT_BAND, face_frame, load_image, srgb, stamp_buffer_hash  # noqa: E402

OUTPUT_DIR = PROJECT_DIR / "art" / "destruction"

# name: (texture, normal map, tint, roughness, uv mode). Slot order is the same on every mesh.
MATERIALS = {
    "plaster": ("T_TownPlaster_BaseColor", "T_Plaster_Normal", "F2E6CF", 0.95, ("world", 3.0)),
    "timber": ("T_WoodTrim_BaseColor", "T_WoodTrim_Normal", "D9CCC0", 0.8, ("band", *WOOD_DARK_BAND, 1.5)),
    "plank": ("T_WoodTrim_BaseColor", "T_WoodTrim_Normal", "C9B49A", 0.8, ("band", *WOOD_LIGHT_BAND, 1.5)),
    "stone": ("T_TownStone_BaseColor", "T_UnevenBrick_Normal", "D4C6AE", 0.9, ("world", 2.4)),
    "tiles": ("T_RoundTiles_BaseColor", "T_RoundTiles_Normal", "F0C8B4", 0.8, ("world", 1.8)),
    "stone_inner": ("T_TownStone_BaseColor", None, "8E8A92", 1.0, ("world", 1.1)),  # raw stone
    "plaster_inner": ("T_FarmHay_BaseColor", None, "B79C80", 1.0, ("world", 0.7)),  # daub and straw core
    "wood_inner": ("T_WoodTrim_BaseColor", None, "FFF0D8", 0.9, ("band", *WOOD_LIGHT_BAND, 0.6)),  # pale splinters
}
SLOT = {name: index for index, name in enumerate(MATERIALS)}
UV_MODES = [entry[4] for entry in MATERIALS.values()]
AXES = {"xz": (0, 2, 1), "yz": (1, 2, 0), "xy": (0, 1, 2)}  # plane -> axis of a, axis of b, axis of the extrusion

SEED_JITTER = 0.28  # fraction of a grid cell
FRACTURE_ATTEMPTS = 8  # the try whose smallest piece is biggest wins
PIECE_GUIDE = {"cottage": 220, "field_wall": 50}

# cottage measurements
HALF_WIDTH, HALF_DEPTH = 2.5, 2.0
PLINTH_TOP = 0.45
EAVE = 2.65  # top of the walls
WALL = 0.22
TIMBER_PROUD = 0.02  # the frame stands out of the plaster
POST = 0.14
PLATE = 0.14
HEAD = 2.35  # top of door and windows; a lintel fills from here to the plate
SILL = 1.35
ROOF_SLOPE = 0.8
ROOF_THICKNESS = 0.16
EAVE_OVERHANG, GABLE_OVERHANG = 0.35, 0.3
PANEL_AREA = 0.45  # plaster m2 per piece
BRACE = 0.16
STACK_HALF = 0.33  # chimney stack half width; the roof is notched around it


class Solid(NamedTuple):
    mesh: object  # bmesh in model coords, materials and UVs set
    inner: str  # material of the cut faces
    count: int = 1  # wanted pieces
    flat: int = -1  # axis that gets a single row of seeds
    settle: Callable = None  # moves a seed onto the solid (sloped slabs)
    convex: bool = True


class Opening(NamedTuple):
    start: float
    end: float
    kind: str  # door, window or post (a post has no gap: start == end)


# ---------- materials ----------

def tinted_material(name: str, texture: str, normal: str, tint: str, roughness: float):
    """Texture times colour through a Multiply node: the exporter writes it as baseColorFactor, no vertex colours."""
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    material.use_backface_culling = True
    nodes, links = material.node_tree.nodes, material.node_tree.links
    shader = nodes["Principled BSDF"]
    image_node = nodes.new("ShaderNodeTexImage")
    mix = nodes.new("ShaderNodeMix")

    image_node.image = load_image(TEXTURE_DIR / f"{texture}.png", True)
    mix.data_type = "RGBA"
    mix.blend_type = "MULTIPLY"
    mix.inputs[0].default_value = 1.0
    mix.inputs[7].default_value = (*srgb(tint), 1.0)
    links.new(image_node.outputs["Color"], mix.inputs[6])
    links.new(mix.outputs[2], shader.inputs["Base Color"])
    shader.inputs["Roughness"].default_value = roughness

    if normal:
        normal_node = nodes.new("ShaderNodeTexImage")
        normal_map = nodes.new("ShaderNodeNormalMap")
        normal_node.image = load_image(TEXTURE_DIR / f"{normal}.png", False)
        links.new(normal_node.outputs["Color"], normal_map.inputs["Color"])
        links.new(normal_map.outputs["Normal"], shader.inputs["Normal"])

    return material


def build_materials() -> list:
    return [tinted_material(f"M_Break{name.title().replace('_', '')}", *entry[:4]) for name, entry in MATERIALS.items()]


# ---------- solids ----------

def map_face(face, uv_layer) -> None:
    """Same mapping as build_town_houses.map_uvs, chosen by the material of the face."""
    mode, *parameters = UV_MODES[face.material_index]
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


def prism(plane: str, outline: list, low: float, high: float, skin: str, sides: str = "", top: str = ""):
    """Outline (a, b) on the plane, extruded low..high along the third axis. sides: material of the faces around
    the outline (the joints of a plaster panel show its core). top: material of the faces looking up (tiles)."""
    first, second, third = AXES[plane]
    mesh = bmesh.new()
    uv_layer = mesh.loops.layers.uv.verify()

    def vertex(a: float, b: float, c: float):
        position = [0.0, 0.0, 0.0]
        position[first], position[second], position[third] = a, b, c

        return mesh.verts.new(position)

    lower = [vertex(a, b, low) for a, b in outline]
    upper = [vertex(a, b, high) for a, b in outline]
    count = len(outline)
    caps = [mesh.faces.new(lower), mesh.faces.new(upper)]
    around = [mesh.faces.new((lower[index], lower[(index + 1) % count], upper[(index + 1) % count], upper[index])) for index in range(count)]

    bmesh.ops.recalc_face_normals(mesh, faces=mesh.faces)
    mesh.normal_update()

    for face in caps:
        face.material_index = SLOT[skin]

    for face in around:
        face.material_index = SLOT[sides or skin]

    for face in [face for face in mesh.faces if top and face.normal.z > 0.3]:
        face.material_index = SLOT[top]

    for face in mesh.faces:
        map_face(face, uv_layer)

    return mesh


def box(minimum: tuple, maximum: tuple, skin: str, top: str = ""):
    outline = [(minimum[0], minimum[1]), (maximum[0], minimum[1]), (maximum[0], maximum[1]), (minimum[0], maximum[1])]

    return prism("xy", outline, minimum[2], maximum[2], skin, top=top)


def rectangle(start: float, end: float, bottom: float, top: float) -> list:
    return [(start, bottom), (end, bottom), (end, top), (start, top)]


def outline_area(outline: list) -> float:
    return abs(sum(a * next_b - next_a * b for (a, b), (next_a, next_b) in zip(outline, outline[1:] + outline[:1]))) / 2.0


def bounds(mesh) -> tuple:
    coordinates = [vert.co for vert in mesh.verts]

    return Vector([min(co[axis] for co in coordinates) for axis in range(3)]), Vector([max(co[axis] for co in coordinates) for axis in range(3)])


# ---------- fracture ----------

def is_inside(mesh, point: Vector) -> bool:
    return all((point - face.verts[0].co).dot(face.normal) < -0.02 for face in mesh.faces)


def cell_seeds(solid: Solid, rng: random.Random) -> list:
    """Jittered grid over the bounds, with cells as cubic as the wanted count allows."""
    low, high = bounds(solid.mesh)
    size = high - low

    def rows(edge: float) -> list:
        return [1 if axis == solid.flat else max(1, round(size[axis] / edge)) for axis in range(3)]

    edge = max(size)

    while math.prod(rows(edge)) < solid.count:
        edge *= 0.99

    grid = rows(edge)
    jitter = [0.0 if axis == solid.flat else SEED_JITTER for axis in range(3)]
    seeds = [
        Vector([low[axis] + size[axis] * (index[axis] + 0.5 + rng.uniform(-jitter[axis], jitter[axis])) / grid[axis] for axis in range(3)])
        for index in itertools.product(*[range(count) for count in grid])
    ]
    seeds = [solid.settle(seed) for seed in seeds] if solid.settle else seeds
    seeds = [seed for seed in seeds if is_inside(solid.mesh, seed)] if solid.convex else seeds

    return seeds or [(low + high) / 2.0]


def cut(piece, plane: tuple, inner: str) -> None:
    """Keep the side of the plane behind its normal and close the wound with the inner material."""
    uv_layer = piece.loops.layers.uv.verify()

    bmesh.ops.bisect_plane(piece, geom=piece.verts[:] + piece.edges[:] + piece.faces[:], dist=1e-5, plane_co=plane[0], plane_no=plane[1], clear_outer=True)
    wound = [edge for edge in piece.edges if edge.is_boundary]
    caps = bmesh.ops.holes_fill(piece, edges=wound, sides=0)["faces"] if wound else []

    for face in caps:
        face.material_index = SLOT[inner]
        face.normal_update()
        map_face(face, uv_layer)


def voronoi_cell(solid: Solid, seed: Vector, seeds: list):
    piece = solid.mesh.copy()
    planes = [((seed + other) / 2.0, other - seed) for other in seeds if other is not seed]

    for plane in planes:
        cut(piece, plane, solid.inner)

    bmesh.ops.recalc_face_normals(piece, faces=piece.faces)

    return piece


def shatter(solid: Solid, rng: random.Random) -> list:
    seeds = cell_seeds(solid, rng)
    cells = [voronoi_cell(solid, seed, seeds) for seed in seeds]

    return [cell for cell in cells if cell.faces and cell.calc_volume() > 1e-6]


def fracture(solid: Solid, rng: random.Random) -> list:
    if solid.count <= 1:
        return [solid.mesh.copy()]

    attempts = [shatter(solid, rng) for _ in range(FRACTURE_ATTEMPTS)]

    return max(attempts, key=lambda pieces: min(piece.calc_volume() for piece in pieces))


def check_pieces(name: str, solid: Solid, pieces: list) -> None:
    """The check that fails when the fracture breaks: every piece closed, together the volume of the solid."""
    volume = solid.mesh.calc_volume()
    total = sum(piece.calc_volume() for piece in pieces)
    open_pieces = [piece for piece in pieces if not all(edge.is_manifold for edge in piece.edges)]

    assert not open_pieces, f"{name}: {len(open_pieces)} peça(s) aberta(s)"
    assert abs(total - volume) < 0.01 * volume + 1e-5, f"{name}: peças somam {total:.4f} m3, o sólido tem {volume:.4f} m3"


# ---------- sections ----------

def mesh_object(name: str, mesh, origin: Vector, parent, parent_origin: Vector, materials: list):
    """Object with its origin at `origin` (model coords); the mesh is moved so it stays where it was built."""
    bmesh.ops.translate(mesh, vec=-origin, verts=mesh.verts)
    data = bpy.data.meshes.new(name)
    mesh.to_mesh(data)

    for material in materials:
        data.materials.append(material)

    mesh_node = bpy.data.objects.new(name, data)
    bpy.context.scene.collection.objects.link(mesh_node)
    mesh_node.parent = parent
    mesh_node.location = origin - parent_origin

    return mesh_node


def empty(name: str, parent=None, location: Vector = Vector()):
    node = bpy.data.objects.new(name, None)
    bpy.context.scene.collection.objects.link(node)
    node.parent = parent
    node.location = location

    return node


def joined(solids: list):
    whole = bmesh.new()
    whole.loops.layers.uv.verify()
    scratch = bpy.data.meshes.new("Scratch")

    for solid in solids:
        solid.mesh.to_mesh(scratch)
        whole.from_mesh(scratch)

    bpy.data.meshes.remove(scratch)

    return whole


def triangles(mesh) -> int:
    return sum(len(face.verts) - 2 for face in mesh.faces)


def godot_box(low: Vector, high: Vector) -> dict:
    return {"aabb_min": [round(low.x, 3), round(low.z, 3), round(-high.y, 3)], "aabb_max": [round(high.x, 3), round(high.z, 3), round(-low.y, 3)]}


def build_section(substance: str, name: str, solids: list, rng: random.Random, materials: list) -> dict:
    whole = joined(solids)
    low, high = bounds(whole)
    center = (low + high) / 2.0
    fractured = [fracture(solid, rng) for solid in solids]

    for solid, pieces in zip(solids, fractured):
        check_pieces(name, solid, pieces)

    pieces = list(itertools.chain.from_iterable(fractured))
    smallest = min(min(bounds(piece)[1] - bounds(piece)[0]) for piece in pieces)
    report = {
        "node": f"Section_{substance}_{name}", "name": name, "substance": substance, "pieces": len(pieces),
        "origin": godot_box(center, center)["aabb_min"], **godot_box(low, high),
        "triangles_whole": triangles(whole), "triangles_pieces": sum(triangles(piece) for piece in pieces),
    }
    section = empty(report["node"], None, center)
    holder = empty(f"Pieces_{name}", section)

    mesh_object(f"Whole_{name}", whole, center, section, center, materials)

    for index, piece in enumerate(pieces):
        piece_low, piece_high = bounds(piece)
        mesh_object(f"Piece_{name}_{index:03d}", piece, (piece_low + piece_high) / 2.0, holder, center, materials)

    print(f"  {report['node']}: {len(pieces)} peças, menor espessura {smallest:.3f} m, {report['triangles_pieces']} triângulos")

    return report


# ---------- cottage ----------

def roof_underside(across: float) -> float:
    return EAVE + ROOF_SLOPE * (HALF_DEPTH - abs(across))


def braced_panel(plaster: Callable, timber: Callable, start: float, end: float, lean: int) -> list:
    """Plaster panel between two posts; lean +1 / -1 crosses it with a brace rising to the right / left."""
    bottom, top = PLINTH_TOP, EAVE - PLATE

    if not lean:
        return [plaster(rectangle(start, end, bottom, top))]

    def side(u: float) -> float:
        return u if lean > 0 else start + end - u

    brace = [(side(start), bottom), (side(start + BRACE), bottom), (side(end), top), (side(end - BRACE), top)]
    under = [(side(start + BRACE), bottom), (side(end), bottom), (side(end), top)]
    over = [(side(start), bottom), (side(end - BRACE), top), (side(start), top)]

    return [timber(brace), plaster(under), plaster(over)]


def opening_frame(plaster: Callable, timber: Callable, bar: Callable, opening: Opening) -> list:
    """Posts on both sides, lintel up to the plate; a window also gets sill, parapet and a cross of glazing bars."""
    start, end = opening.start, opening.end
    top = EAVE - PLATE
    middle, cross = (start + end) / 2.0, (SILL + HEAD) / 2.0
    frames = {
        "post": [timber(rectangle(start - POST / 2.0, start + POST / 2.0, PLINTH_TOP, top))],
        "door": [timber(rectangle(start - POST, start, PLINTH_TOP, top)), timber(rectangle(end, end + POST, PLINTH_TOP, top)), timber(rectangle(start, end, HEAD, top))],
    }
    frames["window"] = frames["door"] + [
        timber(rectangle(start, end, SILL - 0.1, SILL)),
        plaster(rectangle(start, end, PLINTH_TOP, SILL - 0.1)),
        bar(rectangle(middle - 0.02, middle + 0.02, SILL, HEAD)),
        bar(rectangle(start, middle - 0.02, cross - 0.02, cross + 0.02)),
        bar(rectangle(middle + 0.02, end, cross - 0.02, cross + 0.02)),
    ]

    return frames[opening.kind]


def wall(plane: str, outer: float, inward: int, span: tuple, openings: list, leans: dict, corner_posts: bool, gable: bool) -> list:
    """Timber frame with plaster infill on the plane, u running along the wall. outer: coordinate of the outside face;
    inward: +1 / -1, the direction of the room."""
    plaster_depth = sorted((outer, outer + inward * WALL))
    timber_depth = sorted((outer - inward * TIMBER_PROUD, outer + inward * WALL))
    bar_depth = sorted((outer + inward * 0.08, outer + inward * 0.12))
    flat = AXES[plane][2]

    def plaster(outline: list) -> Solid:
        return Solid(prism(plane, outline, *plaster_depth, "plaster", sides="plaster_inner"), "plaster_inner", max(1, round(outline_area(outline) / PANEL_AREA)))

    def timber(outline: list) -> Solid:
        return Solid(prism(plane, outline, *timber_depth, "timber"), "wood_inner")

    def bar(outline: list) -> Solid:
        return Solid(prism(plane, outline, *bar_depth, "timber"), "wood_inner")

    start, end = span
    corners = [Opening(start + POST / 2.0, start + POST / 2.0, "post"), Opening(end - POST / 2.0, end - POST / 2.0, "post")] if corner_posts else []
    framed = sorted(openings + corners)
    margins = {"post": POST / 2.0, "door": POST, "window": POST}
    panel_starts = [start] + [opening.end + margins[opening.kind] for opening in framed]
    panel_ends = [opening.start - margins[opening.kind] for opening in framed] + [end]
    panels = [(panel_start, panel_end) for panel_start, panel_end in zip(panel_starts, panel_ends) if panel_end - panel_start > 0.01]
    plate = Solid(prism(plane, rectangle(start, end, EAVE - PLATE, EAVE), *timber_depth, "timber"), "wood_inner", 2, flat)
    solids = [plate]

    solids += itertools.chain.from_iterable(opening_frame(plaster, timber, bar, opening) for opening in framed)
    solids += itertools.chain.from_iterable(braced_panel(plaster, timber, *panel, leans.get(index, 0)) for index, panel in enumerate(panels))

    if gable:
        apex, king = roof_underside(0.0), roof_underside(POST / 2.0)
        solids += [
            timber([(-POST / 2.0, EAVE), (POST / 2.0, EAVE), (POST / 2.0, king), (0.0, apex), (-POST / 2.0, king)]),
            plaster([(start, EAVE), (-POST / 2.0, EAVE), (-POST / 2.0, king)]),
            plaster([(POST / 2.0, EAVE), (end, EAVE), (POST / 2.0, king)]),
        ]

    return solids


def roof_slab(side: int, x_from: float, x_to: float, near: float, count: int) -> Solid:
    """One slope: side -1 front, +1 back; `near` is how close to the ridge line it starts (the chimney notch)."""
    edges = (side * near, side * (HALF_DEPTH + EAVE_OVERHANG))
    outline = [(across, roof_underside(across) + lift) for across, lift in zip(edges + edges[::-1], (0.0, 0.0, ROOF_THICKNESS, ROOF_THICKNESS))]

    def settle(seed: Vector) -> Vector:
        return Vector((seed.x, seed.y, roof_underside(seed.y) + ROOF_THICKNESS / 2.0))

    return Solid(prism("yz", outline, x_from, x_to, "timber", top="tiles"), "wood_inner", count, 2, settle)


def cottage_sections() -> list:
    inner_half = HALF_WIDTH - WALL
    door = Opening(-1.45, -0.55, "door")
    plinth = [
        Solid(box((-HALF_WIDTH - 0.02, -HALF_DEPTH - 0.02, 0.0), (HALF_WIDTH + 0.02, HALF_DEPTH + 0.02, PLINTH_TOP), "stone"), "stone_inner", 20, 2),
        Solid(box((door.start - 0.1, -HALF_DEPTH - 0.45, 0.0), (door.end + 0.1, -HALF_DEPTH - 0.02, 0.24), "stone"), "stone_inner"),
    ]
    front = wall("xz", -HALF_DEPTH, 1, (-inner_half, inner_half), [door, Opening(0.55, 1.45, "window")], {}, False, False)
    back = wall("xz", HALF_DEPTH, -1, (-inner_half, inner_half), [Opening(-0.8, -0.8, "post"), Opening(0.8, 0.8, "post")], {0: -1, 2: 1}, False, False)
    left = wall("yz", -HALF_WIDTH, 1, (-HALF_DEPTH, HALF_DEPTH), [Opening(-0.45, 0.45, "window")], {0: -1, 1: 1}, True, True)
    right = wall("yz", HALF_WIDTH, -1, (-HALF_DEPTH, HALF_DEPTH), [Opening(-0.7, -0.7, "post"), Opening(0.7, 0.7, "post")], {0: -1, 2: 1}, True, True)
    plank = (door.end - door.start) / 5.0
    door_leaf = [
        Solid(box((door.start + plank * index, -HALF_DEPTH + 0.07, PLINTH_TOP), (door.start + plank * (index + 1), -HALF_DEPTH + 0.13, HEAD), "plank"), "wood_inner")
        for index in range(5)
    ]
    roof_edge = HALF_WIDTH + GABLE_OVERHANG
    roof = [roof_slab(side, -roof_edge, HALF_WIDTH, 0.0, 9) for side in (-1, 1)] + [roof_slab(side, HALF_WIDTH, roof_edge, STACK_HALF + 0.02, 1) for side in (-1, 1)]
    stack_from, stack_to = HALF_WIDTH + TIMBER_PROUD, HALF_WIDTH + TIMBER_PROUD + 0.6
    chimney = [
        Solid(box((stack_from, -0.5, 0.0), (stack_to, 0.5, 2.4), "stone"), "stone_inner", 4),
        Solid(box((stack_from, -STACK_HALF, 2.4), (stack_to, STACK_HALF, 4.9), "stone"), "stone_inner", 4),
        Solid(box((stack_from - 0.05, -STACK_HALF - 0.05, 4.9), (stack_to + 0.05, STACK_HALF + 0.05, 5.02), "stone"), "stone_inner"),
    ]

    return [
        ("STONE", "Plinth", plinth), ("PLASTER", "FrontWall", front), ("PLASTER", "BackWall", back), ("PLASTER", "LeftWall", left),
        ("PLASTER", "RightWall", right), ("WOOD", "Door", door_leaf), ("WOOD", "Roof", roof), ("STONE", "Chimney", chimney),
    ]


# ---------- field wall ----------

def field_wall_sections() -> list:
    rng = random.Random(7)
    stations = [-4.0 + 0.5 * index for index in range(17)]
    crest = [(station, 2.2 + rng.uniform(-0.18, 0.08)) for station in reversed(stations)]
    body = prism("xz", [(-4.0, 0.0), (4.0, 0.0)] + crest, -0.3, 0.3, "stone")

    return [("STONE", "Wall", [Solid(body, "stone_inner", 36, convex=False)])]


# ---------- export and preview ----------

def render_previews(model: str, folder: Path, low: Vector, high: Vector) -> None:
    """Stills from the front and from behind: intact, the pieces in place (gaps and flipped faces show), the pieces pushed apart."""
    scene = bpy.context.scene
    center = (low + high) / 2.0
    wholes = [node for node in scene.objects if node.name.startswith("Whole_")]
    pieces = [node for node in scene.objects if node.name.startswith("Piece_")]
    sections = [node for node in scene.objects if node.name.startswith("Section_")]
    front, behind = Vector((0.8, -1.0, 0.5)).normalized(), Vector((-0.9, 1.0, 0.45)).normalized()
    camera = bpy.data.objects.new("PreviewCamera", bpy.data.cameras.new("PreviewCamera"))
    sun = bpy.data.objects.new("PreviewSun", bpy.data.lights.new("PreviewSun", "SUN"))
    world = bpy.data.worlds.new("PreviewWorld")
    engines = [item.identifier for item in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items]

    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.66, 0.78, 0.92, 1.0)
    scene.world = world
    sun.data.energy = 3.5
    sun.rotation_euler = (math.radians(55.0), 0.0, math.radians(25.0))
    scene.collection.objects.link(camera)
    scene.collection.objects.link(sun)
    scene.camera = camera
    scene.render.engine = next(engine for engine in ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT") if engine in engines)
    scene.render.resolution_x, scene.render.resolution_y = 1600, 1200
    scene.view_settings.view_transform = "Standard"

    def shoot(view: str, shown: list, hidden: list, distance: float, direction: Vector = front) -> None:
        for node in shown:
            node.hide_render = False

        for node in hidden:
            node.hide_render = True

        camera.location = center + direction * distance
        camera.rotation_euler = (-direction).to_track_quat("-Z", "Y").to_euler()
        scene.render.filepath = str(folder / f"destructible_{model}_{view}.png")
        bpy.ops.render.render(write_still=True)

    reach = (high - low).length
    shoot("whole", wholes, pieces, reach * 1.5)
    shoot("pieces", pieces, wholes, reach * 1.5)
    shoot("pieces_back", pieces, wholes, reach * 1.5, behind)

    for node in sections:
        node.location = center + (node.location - center) * 1.5

    for node in pieces:
        node.location = node.location * 1.45

    shoot("exploded", pieces, wholes, reach * 2.3)
    shoot("exploded_back", pieces, wholes, reach * 2.3, behind)


def build_model(model: str, sections: list, preview: Path) -> None:
    started = time.perf_counter()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    materials = build_materials()
    rng = random.Random(model)
    output_path = OUTPUT_DIR / f"{model}.gltf"

    print(f"{model}:")
    reports = [build_section(substance, name, solids, rng, materials) for substance, name, solids in sections]
    low = Vector([min(report["aabb_min"][axis] for report in reports) for axis in range(3)])
    high = Vector([max(report["aabb_max"][axis] for report in reports) for axis in range(3)])
    total = sum(report["pieces"] for report in reports)

    assert total <= PIECE_GUIDE[model], f"{model}: {total} peças, o teto é {PIECE_GUIDE[model]}"

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    bpy.ops.export_scene.gltf(filepath=str(output_path), export_format="GLTF_SEPARATE", export_yup=True, export_keep_originals=True, export_vertex_color="NONE", use_visible=True)
    stamp_buffer_hash(output_path)

    sidecar = {
        "aabb_min": [round(value, 3) for value in low], "aabb_max": [round(value, 3) for value in high],
        "pieces": total, "triangles_whole": sum(report["triangles_whole"] for report in reports),
        "triangles_pieces": sum(report["triangles_pieces"] for report in reports), "sections": reports,
    }
    output_path.with_suffix(".json").write_text(json.dumps(sidecar, indent=1), encoding="utf-8", newline="\n")

    if preview:
        render_previews(model, preview, Vector((low.x, -high.z, low.y)), Vector((high.x, -low.z, high.y)))

    print(f"BUILT {model}: {total} peças, {sidecar['triangles_whole']} triângulos inteiro, {sidecar['triangles_pieces']} em peças, {time.perf_counter() - started:.1f} s")


if __name__ == "__main__":
    arguments = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    preview_folder = Path(arguments[arguments.index("--preview") + 1]) if "--preview" in arguments else None

    build_model("cottage", cottage_sections(), preview_folder)
    build_model("field_wall", field_wall_sections(), preview_folder)
