"""Sculpted neck stump, hanging flesh tatters and mesh helpers for the Mula sem cabeça
(library of tools_src/build_mula_v2.py).

Works over the high-detail bull-horse body loaded by tools_src/mula_v2_base.py:
  - `Stump` + `cut_stump`: cuts the tall conical neck along a broad volcanic mouth (~24 deg forward tilt, matching
    the concept sheet), swells a thick irregular charred-flesh collar around the rim, and digs a deep concave ember
    crater in the middle (with an outer skirt on the cutter so zero jaw/chin fragments ever remain);
  - `add_tatters`: hangs wide-rooted, ragged, S-curved curtains and strips of charred hide/flesh under the bull chest,
    axillae, barrel and groin, weighed to the belly/chest bones where each strip roots.
"""

import math
import random

import bmesh
import bpy
import mula_parts
from mathutils import Vector, noise
from mathutils.bvhtree import BVHTree

VOXEL_SIZE = 0.045
HOOF_TOP = 0.54
MASS_RELAX = [(HOOF_TOP, 2)]
RELIEF_RELAX = [(HOOF_TOP, 2)]
SKIN_NOISE = 0.02
STUMP_SEGMENTS = 48
STUMP_RADII = (0.84, 1.04)  # half-width (X) and half-depth (front-to-back) matching the tall conical neck mouth
STUMP_WALL = 0.72
STUMP_PIT_DEPTH = 0.58
STUMP_COLLAR_BAND = 0.52
STUMP_COLLAR_SWELL = 0.090
STUMP_TILT_RADIANS = math.radians(33.0)  # open volcanic mouth visible in 3/4 view, cutting cleanly below jaw & ears
STUMP_SEED = 7
GIRTH_BOTTOM, GIRTH_TOP, TORSO_GIRTH = 2.2, 3.4, 1.0
GAME_VERTICES = 23500
CUT_TOLERANCE = 0.045
EMBER_RIM_HEAT = 0.16
GROUND_CLEARANCE = 0.02

NECK_BASE = (0.0, -2.2, 6.3)
NECK_MOUTH = (0.0, -3.4, 8.6)

# Hanging torn sheets & strips of charred flesh/hide:
# (x, y in pack units, length, base half-width, sideways sway, backward drift)
# Wide overlapping bases so they read as torn curtains of hide rather than thin comb teeth.
TATTER_SPECS = [
    # Deep chest & between forelegs (long ragged curtains, as in mula_gpt_folha_conceito.png)
    (0.00, -2.62, 1.28, 0.28, 0.03, 0.20),
    (0.18, -2.55, 1.05, 0.25, 0.06, 0.16),
    (-0.19, -2.52, 1.18, 0.26, -0.05, 0.18),
    (0.38, -2.42, 0.88, 0.22, 0.07, 0.14),
    (-0.40, -2.40, 0.94, 0.23, -0.06, 0.15),
    (0.10, -2.22, 1.32, 0.30, 0.02, 0.22),
    (-0.14, -2.18, 1.08, 0.26, -0.04, 0.17),
    (0.52, -2.15, 0.76, 0.20, 0.08, 0.12),
    (-0.50, -2.12, 0.82, 0.21, -0.07, 0.13),
    (0.26, -1.92, 0.96, 0.24, 0.05, 0.16),
    (-0.28, -1.88, 0.86, 0.23, -0.05, 0.14),
    # Sternum & barrel (broad ragged flaps of peeling hide breaking the belly line)
    (0.04, -1.55, 0.62, 0.28, 0.02, 0.12),
    (-0.20, -1.32, 0.48, 0.26, -0.03, 0.10),
    (0.24, -1.08, 0.42, 0.25, 0.04, 0.09),
    (-0.08, -0.80, 0.54, 0.28, -0.02, 0.11),
    (0.18, -0.48, 0.38, 0.24, 0.03, 0.08),
    (-0.22, -0.18, 0.44, 0.26, -0.03, 0.09),
    (0.10, 0.15, 0.36, 0.24, 0.02, 0.08),
    (-0.16, 0.48, 0.42, 0.25, -0.02, 0.09),
    # Flank fold, groin & inner thighs (visible in 3/4, side and rear views)
    (0.28, 0.82, 0.58, 0.24, 0.04, 0.12),
    (-0.28, 0.86, 0.62, 0.25, -0.04, 0.13),
    (0.14, 1.24, 0.82, 0.26, 0.02, 0.15),
    (-0.16, 1.30, 0.76, 0.25, -0.03, 0.14),
    (0.38, 1.48, 0.58, 0.21, 0.05, 0.11),
    (-0.36, 1.52, 0.64, 0.22, -0.05, 0.12),
]
TATTER_SEGMENTS = 7
TATTER_THICKNESS = 0.024
TATTER_ROOT_EMBED = 0.12


class Stump:
    """Frame of the neck cut: broad volcanic rim tilted ~24 deg forward with an organic ragged lip
    and a deep concave ember crater."""

    def __init__(self):
        randomizer = random.Random(STUMP_SEED)
        mouth = Vector(NECK_MOUTH)
        base = Vector(NECK_BASE)

        self.neck_base = base
        self.neck_mouth = mouth
        self.neck_axis = (mouth - base).normalized()
        self.neck_length = (mouth - base).length

        self.axis = Vector((0.0, -math.sin(STUMP_TILT_RADIANS), math.cos(STUMP_TILT_RADIANS))).normalized()
        self.height = 2.2
        self.origin = mouth - self.axis * self.height
        self.side = Vector((1.0, 0.0, 0.0))
        self.crest = self.axis.cross(self.side).normalized()

        phases = [randomizer.uniform(0.0, math.tau) for _ in range(4)]
        self.jags = []
        for segment in range(STUMP_SEGMENTS):
            angle = math.tau * segment / STUMP_SEGMENTS
            throat_notch = -0.09 * max(0.0, -math.sin(angle + 0.2)) ** 2
            broad_waves = (
                0.065 * math.sin(2.0 * angle + phases[0])
                + 0.050 * math.sin(3.0 * angle + phases[1])
                + 0.036 * math.sin(5.0 * angle + phases[2])
                + 0.020 * math.sin(8.0 * angle + phases[3])
            )
            chip = randomizer.uniform(-0.015, 0.015)
            self.jags.append(throat_notch + broad_waves + chip)

    def point(self, rho: float, segment: float, height: float) -> Vector:
        angle = math.tau * segment / STUMP_SEGMENTS
        across = self.side * (math.cos(angle) * STUMP_RADII[0] * rho) + self.crest * (math.sin(angle) * STUMP_RADII[1] * rho)
        return self.origin + self.axis * height + across

    def polar(self, position: Vector) -> tuple:
        offset = position - self.origin
        across_side = offset.dot(self.side) / STUMP_RADII[0]
        across_crest = offset.dot(self.crest) / STUMP_RADII[1]
        turn = (math.atan2(across_crest, across_side) / math.tau * STUMP_SEGMENTS) % STUMP_SEGMENTS
        return math.hypot(across_side, across_crest), turn, offset.dot(self.axis)

    def rim_height(self, turn: float) -> float:
        below = int(turn) % STUMP_SEGMENTS
        share = turn - int(turn)
        return self.height + self.jags[below] * (1.0 - share) + self.jags[(below + 1) % STUMP_SEGMENTS] * share

    def cut_height(self, rho: float, turn: float) -> float:
        """Height of the cut: raised fleshy lip on the rim wall, deep concave ember pit inside,
        and a downward outer skirt well outside the neck (rho > 1.35) so no chin/muzzle tip can survive."""
        wall_share = min(1.0, max(0.0, (rho - STUMP_WALL * 0.42) / (STUMP_WALL * 0.58)))
        smooth_wall = wall_share * wall_share * (3.0 - 2.0 * wall_share)
        lip_arch = 0.070 * math.exp(-((rho - 0.85) / 0.16) ** 2)
        pit = STUMP_PIT_DEPTH * (1.0 - smooth_wall)
        angle = turn / STUMP_SEGMENTS * math.tau
        crater_lumps = 0.085 * noise.noise(Vector((rho * 3.4 * math.cos(angle) + 1.7, rho * 3.4 * math.sin(angle) - 0.9, 0.4)))
        # Outside the neck cylinder (rho > 1.25), drop the cutter floor sharply in front so the entire head/jaw/muzzle
        # lies strictly above the cutter floor and is 100% removed.
        front_skirt = max(0.0, rho - 1.25) * (0.45 + 1.15 * max(0.0, -math.sin(angle)))
        return (
            self.rim_height(turn) * (0.18 + 0.82 * smooth_wall)
            + self.height * 0.82 * (1.0 - smooth_wall)
            + lip_arch
            - pit
            + crater_lumps * (1.0 - smooth_wall * 0.7)
            - front_skirt
        )


def swell_stump_collar(body, stump: Stump) -> None:
    """Thicken the outer neck skin just below the cut into a heavy, irregular charred-flesh rim."""
    for vertex in body.data.vertices:
        if vertex.co.y > -1.2 or vertex.co.z < 5.6:
            continue
        rho, turn, height = stump.polar(vertex.co)
        below_rim = stump.rim_height(turn) - height
        if -0.15 < below_rim < STUMP_COLLAR_BAND and 0.40 < rho < 1.32:
            band = math.exp(-((below_rim - 0.10) / 0.24) ** 2)
            radial = vertex.co - (stump.origin + stump.axis * height)
            radial -= stump.axis * radial.dot(stump.axis)
            if radial.length > 1e-4:
                irregular = 0.82 + 0.40 * noise.noise(vertex.co * 2.5)
                vertex.co += radial * (STUMP_COLLAR_SWELL * band * irregular)


def build_stump_cutter(stump: Stump):
    """Solid above the cut surface (out to 6 mouth radii, 6.5 units tall) removing the entire head & ears cleanly."""
    rhos = [0.0, 0.14, 0.28, 0.40, 0.50, 0.58, 0.65, 0.72, 0.78, 0.84, 0.91, 1.00, 1.12, 1.25, 1.8, 3.2, 6.0]
    cutter = bmesh.new()
    floor_rings = [
        [cutter.verts.new(stump.point(rho, segment, stump.cut_height(rho, segment))) for segment in range(STUMP_SEGMENTS)]
        for rho in rhos[1:]
    ]
    roof_ring = [cutter.verts.new(stump.point(rhos[-1], segment, stump.height + 6.5)) for segment in range(STUMP_SEGMENTS)]
    floor_center = cutter.verts.new(stump.point(0.0, 0, stump.cut_height(0.0, 0.0)))
    roof_center = cutter.verts.new(stump.point(0.0, 0, stump.height + 6.5))
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
    """Swell the collar, cut the neck with the crater solid and lighten the mesh.
    Returns (hide vertices around the cut ordered by turn, {vertex of the cut: ember heat, hottest in the pit})."""
    swell_stump_collar(body, stump)
    cutter = build_stump_cutter(stump)
    cutter_data = cutter.data
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
    bpy.data.objects.remove(cutter)
    bpy.data.meshes.remove(cutter_data)

    drop_loose_pieces(cut_mesh)
    lighten(body)
    cut_mesh = body.data
    on_cut = {}

    for vertex in cut_mesh.vertices:
        if vertex.co.z < 5.5:
            continue
        rho, turn, height = stump.polar(vertex.co)
        if rho < 1.32 and abs(height - stump.cut_height(rho, turn)) < CUT_TOLERANCE:
            # Outer lip (rho ~ 0.78..1.05) stays dark charred crimson; deep crater pit glows white-orange
            pit_heat = min(1.0, max(0.0, (0.82 - rho) / 0.62))
            on_cut[vertex.index] = EMBER_RIM_HEAT + (1.0 - EMBER_RIM_HEAT) * (pit_heat ** 0.85)

    outside = set()
    for edge in cut_mesh.edges:
        first, second = edge.vertices
        if (first in on_cut) != (second in on_cut):
            outside.add(second if first in on_cut else first)

    return sorted(outside, key=lambda index: stump.polar(cut_mesh.vertices[index].co)[1]), on_cut


def add_tatters(body) -> set:
    """Append wide-rooted, ragged curtains and strips of charred hide/flesh under chest, belly and groin."""
    depsgraph = bpy.context.evaluated_depsgraph_get()
    surface = BVHTree.FromObject(body, depsgraph)
    mesh = body.data

    source_weights = [
        {element.group: element.weight for element in vertex.groups}
        for vertex in mesh.vertices
    ]
    polygons_verts = [list(poly.vertices) for poly in mesh.polygons]

    bm = bmesh.new()
    bm.from_mesh(mesh)
    deform_layer = bm.verts.layers.deform.verify()
    randomizer = random.Random(19)
    initial_count = len(bm.verts)

    for index, (rx, ry, length, base_width, sway_x, drift_y) in enumerate(TATTER_SPECS):
        origin = Vector((rx, ry, 2.2))
        location, _, face_index, _ = surface.ray_cast(origin, Vector((0.0, 0.0, 1.0)), 4.8)
        if location is None or face_index is None or location.z < 3.20:
            continue

        face_vids = polygons_verts[face_index]
        weights = {}
        for vid in face_vids:
            for group, weight in source_weights[vid].items():
                weights[group] = weights.get(group, 0.0) + weight / len(face_vids)

        root = location + Vector((0.0, 0.0, TATTER_ROOT_EMBED))
        # Orient wide face of the ragged sheet primarily along the body side/profile (Y-X diagonal) so it reads
        # broadly in both 3/4 and side views instead of looking like thin comb needles!
        yaw = math.radians(28.0 if rx >= 0.0 else -28.0) + randomizer.uniform(-0.35, 0.35)
        flutter_seed = randomizer.uniform(0.0, math.tau)
        rings = []

        for step in range(TATTER_SEGMENTS):
            share = step / TATTER_SEGMENTS
            ragged = 1.0 + 0.26 * math.sin(share * 7.5 + flutter_seed)
            # Broad triangular/curtain taper
            width = base_width * ((1.0 - 0.88 * share) ** 0.85) * ragged
            thick = TATTER_THICKNESS * (1.0 - 0.70 * share)
            twist = yaw + 0.45 * share * (1.0 if index % 2 == 0 else -1.0)

            # Width axis mostly longitudinal (Y) + slight X so side & 3/4 views see torn flaps, not needles
            side_dir = Vector((math.sin(twist) * 0.55, math.cos(twist), 0.0)).normalized()
            thick_dir = Vector((-side_dir.y, side_dir.x, 0.12)).normalized()

            s_curve_y = drift_y * (share ** 1.35) + 0.055 * math.sin(share * 4.6 + flutter_seed)
            s_curve_x = sway_x * (share ** 1.4) + 0.035 * math.cos(share * 5.2 + flutter_seed)
            center = root + Vector((s_curve_x, s_curve_y, -length * share))

            ring = [
                bm.verts.new(center + side_dir * width),
                bm.verts.new(center + thick_dir * thick),
                bm.verts.new(center - side_dir * width),
                bm.verts.new(center - thick_dir * thick),
            ]
            for vert in ring:
                for group, weight in weights.items():
                    vert[deform_layer][group] = weight
            rings.append(ring)

        tip_pos = root + Vector((sway_x * 1.15, drift_y * 1.20, -length * 1.04))
        tip_vert = bm.verts.new(tip_pos)
        for group, weight in weights.items():
            tip_vert[deform_layer][group] = weight

        bm.faces.new(rings[0][::-1])
        for upper, lower in zip(rings, rings[1:]):
            for corner in range(4):
                nxt = (corner + 1) % 4
                face = bm.faces.new((upper[corner], upper[nxt], lower[nxt], lower[corner]))
                face.smooth = True

        last_ring = rings[-1]
        for corner in range(4):
            nxt = (corner + 1) % 4
            face = bm.faces.new((last_ring[corner], last_ring[nxt], tip_vert))
            face.smooth = True

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bm.to_mesh(mesh)
    bm.free()
    mesh.validate()

    for polygon in mesh.polygons:
        polygon.use_smooth = True

    return set(range(initial_count, len(mesh.vertices)))


def drop_loose_pieces(mesh) -> None:
    """Keep only the largest connected piece (what the cut leaves of the head goes away)."""
    skin = bmesh.new()
    skin.from_mesh(mesh)
    unseen = set(skin.verts)
    pieces = []

    while unseen:
        piece, front = set(), [unseen.pop()]
        while front:
            vertex = front.pop()
            piece.add(vertex)
            neighbours = [edge.other_vert(vertex) for edge in vertex.link_edges if edge.other_vert(vertex) in unseen]
            unseen.difference_update(neighbours)
            front.extend(neighbours)
        pieces.append(piece)

    largest = max(pieces, key=len)
    bmesh.ops.delete(skin, geom=[vertex for vertex in skin.verts if vertex not in largest], context="VERTS")
    skin.to_mesh(mesh)
    skin.free()


def lighten(body) -> None:
    """Collapse the mesh down to GAME_VERTICES."""
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
    """Vertex groups named after the pack horse's, weighed part by part (legacy helper)."""
    mula_parts.paint_weights(body, [group.name for group in source_object.vertex_groups])
