"""Sculpted body of the "Mula sem cabeça" (library of tools_src/build_mula_sem_cabeca.py).

The CC0 pack horse is too low-poly to read as flesh, so the body is rebuilt in separate parts (mula_parts.PARTS:
lofts of cross sections over the horse's skeleton, in pack units, ~3.4 per metre, Z up, head to -Y); a voxel remesh
fuses them into one skin whose creases between parts read as muscle separations; ribs, vertebrae and tatters go on
top; the neck is cut by a jagged solid that also digs the ember pit; skin weights are painted part by part.
"""

import math
import random

import bmesh
import bpy
import mula_parts
from mathutils import Vector, noise
from mathutils.bvhtree import BVHTree
from mathutils.interpolate import poly_3d_calc

VOXEL_SIZE = 0.045
HOOF_TOP = 0.42
MASS_RELAX = [(HOOF_TOP, 2)]  # (acima de Z, passadas): o tronco derrete mais que as patas
RELIEF_RELAX = [(HOOF_TOP, 2)]
SKIN_NOISE = 0.02  # ondulação orgânica da pele depois do remesh
STUMP_SEGMENTS = 40
STUMP_RADII = (0.64, 0.68)  # meia largura (X) e meia espessura da boca do toco
STUMP_WALL = 0.74  # fração do raio onde começa a parede do toco
STUMP_PIT_DEPTH = 0.42
STUMP_JAGS = (-0.13, -0.06, -0.02, 0.0, 0.05, 0.1, 0.18)  # lascas da borda, sorteadas por gomo
STUMP_SEED = 7
GIRTH_BOTTOM, GIRTH_TOP, TORSO_GIRTH = 2.2, 3.4, 1.0  # o tronco alarga acima das patas (ossos das patas não mudam)
GAME_VERTICES = 30000
CUT_TOLERANCE = 0.035
EMBER_RIM_HEAT = 0.3
GROUND_CLEARANCE = 0.03  # sola do casco chata

# Cada volume: (ponto inicial, ponto final, raio inicial, raio final, achatamento XYZ). X != 0 é espelhado.
# Os volumes grandes dão a massa; os músculos ficam por cima, saltando só um pouco, para a junção virar sulco.
# Eixo do toco: da base do pescoço esculpido até a boca do corte (o pescoço da mula é mais longo e mais em pé que o
# do cavalo do pacote; a pele continua seguindo o osso Neck pelos pesos).
NECK_BASE = (0.0, -2.5, 5.0)
NECK_MOUTH = (0.0, -3.87, 7.4)
RIB_STARTS = [-0.85, -0.45, -0.05, 0.35, 0.75, 1.15]  # Y do alto de cada costela aparente
RIB_HEIGHTS = [(5.0, 0.0), (4.4, 0.12), (3.8, 0.34)]  # (Z, recuo em Y) dos três pontos de cada costela
RIB_RADIUS = 0.1
RIB_RELIEF = -0.03  # quanto a costela salta do barril
# Vértebras saltadas ao longo da espinha (Y, Z, raio) e farrapos de carne pendurados (X, Y, Z do alto, comprimento).
# Vértebras saltadas ao longo da espinha (Y, raio) e farrapos de carne pendurados da barriga (X, Y, comprimento).
VERTEBRAE = [(-0.55, 0.14), (-0.1, 0.14), (0.35, 0.14), (0.8, 0.14), (1.25, 0.14), (1.7, 0.15), (2.15, 0.14), (2.55, 0.13)]
VERTEBRA_SINK = 0.06  # quanto do nó fica dentro do dorso
TATTERS = [(0.3, -2.3, 0.7), (-0.4, -2.0, 1.0), (0.1, -1.3, 0.6), (-0.15, -0.3, 0.85), (0.35, 0.5, 0.55), (-0.3, 1.2, 0.75),
           (0.5, -1.35, 0.5), (-0.5, -1.35, 0.7), (0.4, -2.6, 0.6), (-0.2, 0.1, 0.4), (0.3, 1.7, 0.6), (-0.45, -2.5, 0.45)]
TATTER_ROOT = 0.12  # quanto o farrapo nasce dentro da barriga


def rib_point(top_y: float, height: float, lean: float) -> tuple:
    """Point of a rib on the trunk box, RIB_RELIEF proud of it."""
    y = top_y + lean
    center_z, half_width, half_depth = mula_parts.trunk_section(y)
    reach = half_width * math.sqrt(max(0.0, 1.0 - ((height - center_z) / half_depth) ** 2))

    return (reach + RIB_RELIEF - RIB_RADIUS, y, height)


def rib_volumes() -> list:
    points = [[rib_point(top_y, height, lean) for height, lean in RIB_HEIGHTS] for top_y in RIB_STARTS]

    return [(first, second, RIB_RADIUS, RIB_RADIUS, (1.0, 1.0, 1.0)) for rib in points for first, second in zip(rib, rib[1:])]


def mirrored(volume: tuple) -> list:
    """A volume and, when it sits off the middle plane, its mirror image."""
    start, end, start_radius, end_radius, squash = volume

    if start[0] == 0.0 and end[0] == 0.0:
        return [volume]

    return [volume, ((-start[0], start[1], start[2]), (-end[0], end[1], end[2]), start_radius, end_radius, squash)]


def relief_volumes() -> list:
    """Ribs, vertebrae and hanging tatters: the fine relief laid over the melted masses."""
    volumes = [copy for volume in rib_volumes() for copy in mirrored(volume)]
    backs = {y: mula_parts.trunk_section(y) for y in [y for y, _ in VERTEBRAE] + [y for _, y, _ in TATTERS]}
    spine = [(y, backs[y][0] + backs[y][2] - VERTEBRA_SINK, radius) for y, radius in VERTEBRAE]
    volumes += [((0.0, y, z), (0.0, y, z), radius, radius, (0.7, 1.0, 0.8)) for y, z, radius in spine]
    volumes += [((x, y, backs[y][0] - backs[y][2] + TATTER_ROOT), (x, y, backs[y][0] - backs[y][2] + TATTER_ROOT - length), 0.14, 0.03, (1.0, 1.0, 1.0))
                for x, y, length in TATTERS]

    return volumes


def add_volume(clay, volume: tuple) -> None:
    """Chain of squashed spheres from start to end, radius tapering."""
    start, end, start_radius, end_radius, squash = volume
    start, end = Vector(start), Vector(end)
    count = max(1, math.ceil((end - start).length / (min(start_radius, end_radius) * 0.4)))

    for step in range(count + 1):
        share = step / count
        radius = start_radius + (end_radius - start_radius) * share
        center = start.lerp(end, share)
        sphere = bmesh.ops.create_icosphere(clay, subdivisions=2, radius=radius)

        for vertex in sphere["verts"]:
            vertex.co = Vector((vertex.co.x * squash[0], vertex.co.y * squash[1], vertex.co.z * squash[2])) + center


def fuse(volumes: list, base=None, lofts: tuple = ()):
    """New mesh: the volumes (plus `base`, an already fused mesh) made one skin by a voxel remesh."""
    clay = bmesh.new()

    if base is not None:
        clay.from_mesh(base)
        bpy.data.meshes.remove(base)

    for volume in volumes:
        add_volume(clay, volume)

    for sections in lofts:
        mula_parts.add_loft(clay, sections)

    bmesh.ops.recalc_face_normals(clay, faces=clay.faces[:])

    rough_mesh = bpy.data.meshes.new("MulaClay")
    clay.to_mesh(rough_mesh)
    clay.free()
    rough = bpy.data.objects.new("MulaClay", rough_mesh)
    bpy.context.scene.collection.objects.link(rough)

    remesh = rough.modifiers.new("Remesh", "REMESH")
    remesh.mode = "VOXEL"
    remesh.voxel_size = VOXEL_SIZE
    remesh.adaptivity = 0.0
    fused = bpy.data.meshes.new_from_object(rough.evaluated_get(bpy.context.evaluated_depsgraph_get()))
    bpy.data.objects.remove(rough)
    bpy.data.meshes.remove(rough_mesh)

    return fused


def relax(mesh, passes_by_height: list) -> None:
    """Smooth the skin; each (lowest Z, passes) entry relaxes only what stands above that height."""
    skin = bmesh.new()
    skin.from_mesh(mesh)

    for lowest, passes in passes_by_height:
        above = [vertex for vertex in skin.verts if vertex.co.z > lowest]

        for _ in range(passes):
            bmesh.ops.smooth_vert(skin, verts=above, factor=0.5, use_axis_x=True, use_axis_y=True, use_axis_z=True)

    skin.to_mesh(mesh)
    skin.free()


def sculpt_clay():
    """Object with the masses fused and melted together, then the fine relief on top; still whole (neck not cut)."""
    masses = fuse([], lofts=mula_parts.all_parts())
    relax(masses, MASS_RELAX)
    skin_mesh = fuse(relief_volumes(), masses)
    relax(skin_mesh, RELIEF_RELAX)

    skin = bmesh.new()
    skin.from_mesh(skin_mesh)
    skin.normal_update()

    for vertex in skin.verts:
        girth_share = min(1.0, max(0.0, (vertex.co.z - GIRTH_BOTTOM) / (GIRTH_TOP - GIRTH_BOTTOM)))

        vertex.co += vertex.normal * noise.noise(vertex.co * 2.2) * SKIN_NOISE * min(1.0, vertex.co.z)
        vertex.co.x *= 1.0 + (TORSO_GIRTH - 1.0) * girth_share
        vertex.co.z = max(vertex.co.z, GROUND_CLEARANCE)

    skin.to_mesh(skin_mesh)
    skin.free()
    skin_mesh.name = "Mula"
    body = bpy.data.objects.new("Mula", skin_mesh)
    bpy.context.scene.collection.objects.link(body)

    return body


class Stump:
    """Frame of the neck cut: polar coordinates around the neck bone and the height of the cut at each of them."""

    def __init__(self):
        randomizer = random.Random(STUMP_SEED)

        self.origin = Vector(NECK_BASE)
        self.height = (Vector(NECK_MOUTH) - self.origin).length  # da base até a boca do toco, ao longo do eixo
        self.axis = (Vector(NECK_MOUTH) - self.origin).normalized()
        self.side = Vector((1.0, 0.0, 0.0))
        self.crest = self.axis.cross(self.side).normalized()  # para trás e para cima: lado da crina
        self.jags = [randomizer.choice(STUMP_JAGS) for _ in range(STUMP_SEGMENTS)]

    def point(self, rho: float, segment: int, height: float) -> Vector:
        angle = 2.0 * math.pi * segment / STUMP_SEGMENTS
        across = self.side * (math.cos(angle) * STUMP_RADII[0] * rho) + self.crest * (math.sin(angle) * STUMP_RADII[1] * rho)

        return self.origin + self.axis * height + across

    def polar(self, position: Vector) -> tuple:
        """(rho, turn 0..STUMP_SEGMENTS, height along the neck) of a point."""
        offset = position - self.origin
        across_side = offset.dot(self.side) / STUMP_RADII[0]
        across_crest = offset.dot(self.crest) / STUMP_RADII[1]
        turn = (math.atan2(across_crest, across_side) / (2.0 * math.pi) * STUMP_SEGMENTS) % STUMP_SEGMENTS

        return math.hypot(across_side, across_crest), turn, offset.dot(self.axis)

    def rim_height(self, turn: float) -> float:
        below = int(turn) % STUMP_SEGMENTS
        share = turn - int(turn)

        return self.height + self.jags[below] * (1.0 - share) + self.jags[(below + 1) % STUMP_SEGMENTS] * share

    def cut_height(self, rho: float, turn: float) -> float:
        """Height of the cut: the jagged rim on the wall, sinking into the ember pit toward the middle."""
        wall_share = min(1.0, max(0.0, (rho - STUMP_WALL * 0.55) / (STUMP_WALL * 0.45)))
        pit = STUMP_PIT_DEPTH * (1.0 - wall_share * wall_share * (3.0 - 2.0 * wall_share))
        dent = 0.08 * noise.noise(Vector((rho * 3.0 * math.cos(turn), rho * 3.0 * math.sin(turn), 0.0)))

        return self.rim_height(turn) * (0.1 + 0.9 * wall_share) + self.height * 0.9 * (1.0 - wall_share) - pit + dent * (1.0 - wall_share)


def build_stump_cutter(stump: Stump):
    """Solid above the cut surface (out to 4 mouth radii, 3 units tall)."""
    rhos = [0.0, 0.15, 0.3, 0.42, 0.52, 0.6, 0.67, 0.72, 0.76, 0.8, 0.86, 0.95, 1.2, 2.0, 4.0]
    cutter = bmesh.new()
    floor_rings = [[cutter.verts.new(stump.point(rho, segment, stump.cut_height(rho, segment))) for segment in range(STUMP_SEGMENTS)] for rho in rhos[1:]]
    roof_ring = [cutter.verts.new(stump.point(rhos[-1], segment, stump.height + 3.0)) for segment in range(STUMP_SEGMENTS)]
    floor_center = cutter.verts.new(stump.point(0.0, 0, stump.cut_height(0.0, 0.0)))
    roof_center = cutter.verts.new(stump.point(0.0, 0, stump.height + 3.0))
    rings = floor_rings + [roof_ring]

    for segment in range(STUMP_SEGMENTS):
        following = (segment + 1) % STUMP_SEGMENTS
        cutter.faces.new((floor_center, floor_rings[0][segment], floor_rings[0][following]))
        cutter.faces.new((roof_center, roof_ring[following], roof_ring[segment]))

        for inner, outer in zip(rings, rings[1:]):
            cutter.faces.new((inner[segment], outer[segment], outer[following], inner[following]))

    bmesh.ops.recalc_face_normals(cutter, faces=cutter.faces[:])
    cutter_mesh = bpy.data.meshes.new("StumpCutter")
    cutter.to_mesh(cutter_mesh)
    cutter.free()
    cutter_object = bpy.data.objects.new("StumpCutter", cutter_mesh)
    bpy.context.scene.collection.objects.link(cutter_object)

    return cutter_object


def cut_stump(body, stump: Stump) -> tuple:
    """Cut the neck with the jagged solid and lighten the mesh. Returns (hide vertices around the cut, ordered by turn; {vertex of the cut: ember heat, hottest in the middle})."""
    cutter = build_stump_cutter(stump)
    boolean = body.modifiers.new("Cut", "BOOLEAN")

    boolean.operation = "DIFFERENCE"
    boolean.solver = "EXACT"
    boolean.object = cutter
    cut_mesh = bpy.data.meshes.new_from_object(body.evaluated_get(bpy.context.evaluated_depsgraph_get()))
    body.modifiers.remove(boolean)
    old_mesh = body.data
    body.data = cut_mesh
    cut_mesh.name = "Mula"
    bpy.data.meshes.remove(old_mesh)
    bpy.data.meshes.remove(cutter.data)

    lighten(body)
    cut_mesh = body.data
    on_cut = {}

    for vertex in cut_mesh.vertices:
        rho, turn, height = stump.polar(vertex.co)

        if rho < 1.6 and abs(height - stump.cut_height(rho, turn)) < CUT_TOLERANCE:
            on_cut[vertex.index] = max(EMBER_RIM_HEAT, 1.0 - rho)

    outside = set()

    for edge in cut_mesh.edges:
        first, second = edge.vertices

        if (first in on_cut) != (second in on_cut):
            outside.add(second if first in on_cut else first)

    return sorted(outside, key=lambda index: stump.polar(cut_mesh.vertices[index].co)[1]), on_cut


def lighten(body) -> None:
    """Collapse the voxel grid down to GAME_VERTICES (irregular triangles, which also lets the veins wander)."""
    decimate = body.modifiers.new("Decimate", "DECIMATE")
    decimate.ratio = min(1.0, GAME_VERTICES / len(body.data.vertices))
    light_mesh = bpy.data.meshes.new_from_object(body.evaluated_get(bpy.context.evaluated_depsgraph_get()))
    body.modifiers.remove(decimate)
    heavy_mesh = body.data
    body.data = light_mesh
    light_mesh.name = "Mula"
    bpy.data.meshes.remove(heavy_mesh)

    for polygon in light_mesh.polygons:
        polygon.use_smooth = True


def transfer_weights(body, source_object) -> None:
    """Vertex groups named after the pack horse's, weighed part by part (see mula_parts.paint_weights)."""
    mula_parts.paint_weights(body, [group.name for group in source_object.vertex_groups])
