"""Build the "Mula sem cabeça" mob (Brazilian folklore, public domain) over the skeleton and animations of the CC0
Quaternius horse (tools/vendor/animals/FBX/Horse.fbx) -> art/mobs/mula_v2/mula_v2.gltf (+ textures,
+ JSON sidecar).

Realistic on purpose (the mob is meant to look out of this world next to the rest of the game). Steps:
  1. import the horse and keep only its skeleton, actions and deform bone list; load the bull-proportioned, muscle-
     sculpted body from tools_src/mula_v2_base.py, cut the broad volcanic neck stump with an ember crater and add
     hanging flesh tatters under chest, belly and groin (tools_src/mula_v2_body.py);
  2. lava veins (object MulaVeins): a polygonal web of thick vessels across the neck, chest and upper shoulders
     plus a meandering shortest-path tree branching along the intermuscular grooves down to all four hooves.
     UV.x = distance from the stump (0..1), UV.y = thickness (0..1): art/shaders/lava_vein.gdshader pulses along it;
  3. broken iron chains (object MulaChains): four heavy link loops wrapped around neck, chest, girth and flank by
     ray casting the sculpted body, plus hanging broken ends skinned to Chain<n> bones that the game sways;
  4. fire: ribbons of flame (object MulaFlames) for the stump blaze, mane, wide flowing tail and climbing hoof flames,
     opened toward the camera by art/shaders/flame_ribbon.gdshader, and markers (FireStump, FireMane_<n>,
     FireTail_<n>, FireHoof_<leg>) where features/mobs/mula_v2.tscn hangs embers, dark smoke and light;
  5. bake dark wine-toned charred hide with muscle-fibre striations, 100k-vertex sculpted muscle relief + AO,
     3D-distance crimson halos around the veins (leaving muscle bellies dark and sculptural), glowing stump crater
     and dark charred hooves split by lava fissures;
  6. rename the actions the mob plays; scale so the withers stand WITHERS_HEIGHT metres; export.

Usage:
  blender -b --factory-startup -P tools_src/build_mula_v2.py -- [--source <Horse.fbx|.glb>]
"""

import hashlib
import heapq
import json
import math
import random
import sys
from pathlib import Path

import bmesh
import bpy
from mathutils import Matrix, Vector
from mathutils import noise as math_noise
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree

sys.path.insert(0, str(Path(__file__).resolve().parent))
import mula_v2_base  # noqa: E402
import mula_v2_body  # noqa: E402
from convert_farm_animals import import_source, make_materials_opaque  # noqa: E402

PROJECT_DIR = Path(__file__).resolve().parent.parent
SOURCE = PROJECT_DIR / "tools" / "vendor" / "animals" / "FBX" / "Horse.fbx"
OUTPUT = PROJECT_DIR / "art" / "mobs" / "mula_v2" / "mula_v2.gltf"
WITHERS_HEIGHT = 1.7  # metres
ACTION_NAMES = {"idle": "Idle", "walk": "Walk", "run": "Run", "jump": "Attack", "death": "Death"}
HAIR_MATERIAL_INDEX = 1
HAIR_FLOOR = 1.0
HOOF_BLEND = mula_v2_body.HOOF_TOP  # 0 at coronet top, 1 right at the ground sole so hoof wall stays dark cracked horn!
TEXTURE_SIZE = 2048

CRACK_PLATE_SCALE = 1.55
CRACK_FINE_SCALE = 4.2
CRACK_BEND = 0.36
CRACK_WIDTH, CRACK_FINE_WIDTH, CRACK_SCORCH_WIDTH = 0.026, 0.032, 0.18
CRACK_FINE_SHARE = 0.35
CRACK_LIT_SCALE, CRACK_LIT_THRESHOLD, CRACK_LIT_SHARPNESS = 1.4, 0.70, 8.0
CRACK_DEPTH = 0.065
CRACK_HEAT_BOOST = 0.65

RELIEF_CAGE = 0.06
RELIEF_REACH = 0.28
RELIEF_AMBIENT_SAMPLES = 32
RELIEF_STRENGTH = 2.8
RELIEF_SHADE = 0.85
WITHERS_Y = (-1.65, -0.95)
HEADLESS_BONES = ("Head",)
CHAIN_BONE_PREFIX = "Chain"
HIDE_GLOW_STRENGTH = 2.6
HIDE_HALO = 0.68
FIBRE_DENSITY = 8.0
NECK_FIBRE_TILT = math.radians(-30.0)

VEIN_SEED = 11
VEIN_ROOTS = 12  # thick trunks born around the volcanic neck rim
VEIN_TIPS = 56  # body & flank branch tips
VEIN_FRONT_DENSITY = 3.8
VEIN_FRONT_END = -0.7
VEIN_TIPS_PER_LEG = 5  # guaranteed tips descending down every cannon right into each hoof
VEIN_SHIN_TOP = 2.2
VEIN_BRIDGES = 14
VEIN_BRIDGE_REACH = 10
VEIN_GROOVE_PULL = 4.8
VEIN_MEANDER_SCALE = 2.2
VEIN_WEB_REACH = 3.85  # bold polygonal cells across the neck, chest and upper shoulders
VEIN_WEB_SPACING = 0.84  # ~20 cm cells so dark sculpted muscle bulges read clearly inside each cell!
VEIN_WEB_LINKS = 3
VEIN_WEB_DETOUR = 2.35
VEIN_WEB_THICKNESS = (1.0, 0.38)
VEIN_TIP_RADIUS = 0.006
VEIN_TRUNK_RADIUS = 0.066
VEIN_TRUNK_FLOW = 20.0
VEIN_SIDES = 6
VEIN_SINK = 0.35  # raised volcanic vessels sitting proudly in the muscle grooves
VEIN_HALO_MIN_REACH = 0.13  # ~3 cm around thin capillaries
VEIN_HALO_MAX_REACH = 0.38  # ~9.5 cm wide crimson halo around thick neck/chest trunks

LINK_RADIUS = 0.114
LINK_WIRE = 0.038
LINK_STRETCH = 1.48
LINK_SPACING = 0.268
LINK_SEGMENTS = 10
LINK_WIRE_SIDES = 5
HOT_LINK_SHARE = 0.36
CHAIN_LOOPS = [
    (Vector((0.0, -2.55, 6.65)), Vector((0.08, -0.68, 0.72)), "Shoulders"),
    (Vector((0.0, -2.15, 5.35)), Vector((0.28, -0.86, 0.42)), "Shoulders"),
    (Vector((0.0, -0.85, 5.15)), Vector((0.12, -0.96, 0.24)), "Torso"),
    (Vector((0.0, 1.15, 5.45)), Vector((-0.24, 0.92, 0.30)), "Hips"),
]
CHAIN_ENDS = [
    (0, 0, -1.0, 5, "Shoulders"),
    (1, 0, 1.0, 5, "Shoulders"),
    (1, 2, -1.0, 4, "Shoulders"),
    (3, 0, 1.0, 5, "Hips"),
    (3, 0, -1.0, 4, "Hips"),
]

STUMP_FIRE_DEPTH = 0.24
MANE_NECK_SHARES = [0.84, 0.64, 0.44, 0.24, 0.04]
WITHERS_FIRE = [-1.55, -1.00]
MANE_BONE_SPLIT = 0.30
HOOF_REACH = 0.85

FLAME_SEED = 5
FLAME_SEGMENTS = 10
FLAME_SLIVER = 0.002
FLAME_WIND = Vector((0.0, 1.0, 0.0))
STUMP_TONGUES, MANE_TONGUES, TAIL_TONGUES, HOOF_TONGUES = 22, 24, 40, 14
HOOF_FLAME_CLIMB = 1.95
TAIL_BONES = ["Tail1", "Tail2", "Tail3"]

AXIAL_LIFT_FLOOR, AXIAL_LIFT_TOP, AXIAL_LIFT = 0.75, 3.14, 0.96
AXIAL_TRUNK_STRETCH = 1.06
FOOT_FOLLOWS = {
    "FrontFoot.L": "FrontLowLeg.L_end",
    "FrontFoot.R": "FrontLowLeg.R_end",
    "BackFoot.L": "BackLowLeg.L_end",
    "BackFoot.R": "BackLowLeg.R_end",
}


def strip_hair(mesh_object) -> None:
    edit_mesh = bmesh.new()
    edit_mesh.from_mesh(mesh_object.data)
    bmesh.ops.remove_doubles(edit_mesh, verts=edit_mesh.verts[:], dist=0.0005)
    hair_faces = [
        face
        for face in edit_mesh.faces
        if face.material_index == HAIR_MATERIAL_INDEX and face.calc_center_median().z > HAIR_FLOOR
    ]
    bmesh.ops.delete(edit_mesh, geom=hair_faces, context="FACES")
    edit_mesh.to_mesh(mesh_object.data)
    edit_mesh.free()


def groove_depths(mesh, neighbours: dict) -> list:
    depths = []
    for vertex in mesh.vertices:
        around = [mesh.vertices[neighbour].co for neighbour in neighbours.get(vertex.index, [])]
        if not around:
            depths.append(0.0)
            continue
        middle = sum(around, Vector()) / len(around)
        reach = max(1e-5, sum((position - vertex.co).length for position in around) / len(around))
        depths.append((middle - vertex.co).dot(vertex.normal) / reach)
    return depths


def weighted_sample(randomizer, population: list, weights: list, count: int) -> list:
    if not population or count <= 0:
        return []
    count = min(count, len(population))
    keys = [randomizer.random() ** (1.0 / max(1e-4, weight)) for weight in weights]
    order = sorted(range(len(population)), key=keys.__getitem__, reverse=True)
    return [population[index] for index in order[:count]]


def sample_leg_tips(randomizer, reachable: list, positions: list) -> list:
    chosen = []
    for x_sign in (-1.0, 1.0):
        for y_front in (True, False):
            quadrant = [
                v
                for v in reachable
                if (positions[v].x * x_sign > 0.25)
                and ((positions[v].y < -0.5) == y_front)
                and positions[v].z < VEIN_SHIN_TOP
            ]
            hoof_zone = [v for v in quadrant if positions[v].z < 0.62]
            cannon_zone = [v for v in quadrant if 0.62 <= positions[v].z < VEIN_SHIN_TOP]
            chosen += randomizer.sample(hoof_zone, min(3, len(hoof_zone)))
            chosen += randomizer.sample(cannon_zone, min(max(0, VEIN_TIPS_PER_LEG - 3), len(cannon_zone)))
    return chosen


def grow_vein_tree(mesh, rim: list, blocked: set) -> dict:
    """Polygonal lava web over neck/chest/shoulders + meandering vascular branches down to all four hooves."""
    randomizer = random.Random(VEIN_SEED)
    positions = [vertex.co.copy() for vertex in mesh.vertices]
    open_edges = [
        edge.vertices[:]
        for edge in mesh.edges
        if edge.vertices[0] not in blocked and edge.vertices[1] not in blocked
    ]
    adjacent = {}
    for first, second in open_edges:
        adjacent.setdefault(first, []).append(second)
        adjacent.setdefault(second, []).append(first)

    depths = groove_depths(mesh, adjacent)
    neighbours = {}
    seed_offset = Vector((3.1, -1.7, 2.3))

    for first, second in open_edges:
        midpoint = (positions[first] + positions[second]) * 0.5
        groove = min(2.6, max(0.22, 1.0 - VEIN_GROOVE_PULL * (depths[first] + depths[second]) * 0.5))
        meander = 0.50 + 1.65 * (0.5 + 0.5 * math_noise.noise(midpoint * VEIN_MEANDER_SCALE + seed_offset))
        # Break up the mirror-seam straight line at x = 0 so central neck/chest vessels zig-zag into polygonal cells
        midline_zig = 1.0 + 1.45 * max(0.0, 1.0 - abs(midpoint.x) / 0.18) * (
            0.5 + 0.5 * math.sin(midpoint.z * 4.4 + midpoint.y * 2.7)
        )
        jitter = randomizer.uniform(0.72, 1.38)
        length = (positions[first] - positions[second]).length
        cost = length * meander * midline_zig * jitter * groove
        neighbours.setdefault(first, []).append((second, cost, length))
        neighbours.setdefault(second, []).append((first, cost, length))

    roots = rim[:: max(1, len(rim) // VEIN_ROOTS)][:VEIN_ROOTS]
    cost_to = {root: 0.0 for root in roots}
    distance = {root: 0.0 for root in roots}
    parent = {root: None for root in roots}
    queue = [(0.0, root) for root in roots]

    while queue:
        cost, vertex = heapq.heappop(queue)
        if cost > cost_to[vertex]:
            continue
        for neighbour, edge_cost, length in neighbours.get(vertex, []):
            if cost + edge_cost < cost_to.get(neighbour, math.inf):
                cost_to[neighbour] = cost + edge_cost
                distance[neighbour] = distance[vertex] + length
                parent[neighbour] = vertex
                heapq.heappush(queue, (cost + edge_cost, neighbour))

    reachable = sorted(set(parent) - set(rim))
    density = [VEIN_FRONT_DENSITY if positions[vertex].y < VEIN_FRONT_END else 1.0 for vertex in reachable]
    tips = weighted_sample(randomizer, reachable, density, VEIN_TIPS) + sample_leg_tips(randomizer, reachable, positions)
    tips = list(dict.fromkeys(tips))
    flow = {}

    for tip in tips:
        vertex = tip
        while vertex is not None:
            flow[vertex] = flow.get(vertex, 0) + 1
            vertex = parent[vertex]

    kept = {vertex: parent[vertex] for vertex in flow}
    bridge_picks = randomizer.sample(tips, min(VEIN_BRIDGES, len(tips)))
    bridges = [bridge for bridge in (bridge_from(tip, kept, flow, adjacent) for tip in bridge_picks) if bridge]
    web_segments, web_thickness = weave_vein_web(randomizer, positions, neighbours, distance, roots)
    branches = [(vertex, above) for vertex, above in kept.items() if above is not None]
    segments = list({frozenset(pair): pair for pair in branches + bridges + web_segments}.values())
    thickness = {vertex: vein_thickness(count) for vertex, count in flow.items()}

    for vertex, web_share in web_thickness.items():
        thickness[vertex] = max(thickness.get(vertex, 0.0), web_share)

    return {"segments": segments, "thickness": thickness, "distance": distance}


def spread_web_nodes(randomizer, positions: list, candidates: list, pinned: list) -> list:
    cells = {}
    nodes = []

    def try_insert(vertex: int, min_dist: float) -> None:
        position = positions[vertex]
        cell = (
            round(position.x / VEIN_WEB_SPACING),
            round(position.y / VEIN_WEB_SPACING),
            round(position.z / VEIN_WEB_SPACING),
        )
        around = [
            other
            for dx in (-1, 0, 1)
            for dy in (-1, 0, 1)
            for dz in (-1, 0, 1)
            for other in cells.get((cell[0] + dx, cell[1] + dy, cell[2] + dz), [])
        ]
        if all((positions[other] - position).length >= min_dist for other in around):
            cells.setdefault(cell, []).append(vertex)
            nodes.append(vertex)

    for root in pinned[::2]:
        try_insert(root, VEIN_WEB_SPACING * 0.72)

    shuffled = list(candidates)
    randomizer.shuffle(shuffled)
    for vertex in shuffled:
        try_insert(vertex, VEIN_WEB_SPACING)

    return nodes


def cheapest_path(neighbours: dict, start: int, goal: int, longest: float) -> list:
    cost_to = {start: 0.0}
    length_to = {start: 0.0}
    came_from = {start: None}
    queue = [(0.0, start)]

    while queue:
        cost, vertex = heapq.heappop(queue)
        if vertex == goal:
            break
        if cost > cost_to[vertex]:
            continue
        for neighbour, edge_cost, length in neighbours.get(vertex, []):
            if cost + edge_cost < cost_to.get(neighbour, math.inf) and length_to[vertex] + length <= longest:
                cost_to[neighbour] = cost + edge_cost
                length_to[neighbour] = length_to[vertex] + length
                came_from[neighbour] = vertex
                heapq.heappush(queue, (cost + edge_cost, neighbour))

    if goal not in came_from:
        return []

    path = [goal]
    while came_from[path[-1]] is not None:
        path.append(came_from[path[-1]])
    return path


def weave_vein_web(randomizer, positions: list, neighbours: dict, distance: dict, roots: list) -> tuple:
    candidates = sorted(
        vertex
        for vertex, length in distance.items()
        if length < VEIN_WEB_REACH and positions[vertex].z > 3.55
    )
    nodes = spread_web_nodes(randomizer, positions, candidates, roots)
    pairs = set()

    for node in nodes:
        nearest = sorted(nodes, key=lambda other: (positions[other] - positions[node]).length_squared)[
            1 : VEIN_WEB_LINKS + 1
        ]
        for other in nearest:
            if (positions[other] - positions[node]).length <= VEIN_WEB_SPACING * 2.1:
                pairs.add(frozenset((node, other)))

    segments = []
    thickness = {}
    near, far = VEIN_WEB_THICKNESS

    for first, second in sorted(tuple(sorted(pair)) for pair in pairs):
        path = cheapest_path(
            neighbours, first, second, (positions[first] - positions[second]).length * VEIN_WEB_DETOUR
        )
        vessel = randomizer.uniform(0.78, 1.0)
        segments += list(zip(path, path[1:]))

        for vertex in path:
            share = min(1.0, distance[vertex] / VEIN_WEB_REACH)
            thickness[vertex] = max(thickness.get(vertex, 0.0), (near + (far - near) * (share ** 0.72)) * vessel)

    return segments, thickness


def bridge_from(tip: int, kept: dict, flow: dict, adjacent: dict):
    own_branch = set()
    vertex = tip
    while vertex is not None and len(own_branch) < VEIN_BRIDGE_REACH * 2:
        own_branch.add(vertex)
        vertex = kept[vertex]

    came_from = {tip: None}
    frontier = [tip]
    for _ in range(VEIN_BRIDGE_REACH):
        following = []
        for vertex in frontier:
            for neighbour in adjacent.get(vertex, []):
                if neighbour in came_from or neighbour in own_branch:
                    continue
                came_from[neighbour] = vertex
                if neighbour in kept:
                    return lay_bridge(vertex, neighbour, came_from, kept, flow)
                following.append(neighbour)
        frontier = following
    return None


def lay_bridge(last: int, landing: int, came_from: dict, kept: dict, flow: dict) -> tuple:
    path = []
    vertex = last
    while came_from[vertex] is not None:
        path.append(vertex)
        vertex = came_from[vertex]
    for vertex in path:
        kept[vertex] = came_from[vertex]
        flow[vertex] = 1
    return (last, landing)


def vein_thickness(flow: int) -> float:
    return min(1.0, (flow / VEIN_TRUNK_FLOW) ** 0.50)


def finish_skinned_object(name: str, edit_mesh, body_object, armature, materials: list):
    mesh = bpy.data.meshes.new(name)
    skinned = bpy.data.objects.new(name, mesh)

    for group in body_object.vertex_groups:
        skinned.vertex_groups.new(name=group.name)

    edit_mesh.to_mesh(mesh)
    edit_mesh.free()

    for material in materials:
        mesh.materials.append(material)

    bpy.context.scene.collection.objects.link(skinned)
    skinned.parent = armature
    skinned.modifiers.new("Armature", "ARMATURE").object = armature

    return skinned


def build_veins(mesh_object, armature, tree: dict):
    """Raised tubes along the vessels, smoothed into natural curves and laid onto the sculpted hide."""
    mesh = mesh_object.data
    surface = BVHTree.FromObject(mesh_object, bpy.context.evaluated_depsgraph_get())
    segments, thickness, distance = tree["segments"], tree["thickness"], tree["distance"]
    longest = max(1e-4, max(distance[vertex] for vertex in thickness))
    links = {vertex: [] for vertex in thickness}

    for vertex, above in segments:
        links[vertex].append(above)
        links[above].append(vertex)

    positions = {vertex: mesh.vertices[vertex].co.copy() for vertex in links}
    for _ in range(4):
        positions = {
            vertex: positions[vertex].lerp(
                sum((positions[link] for link in links[vertex]), Vector()) / len(links[vertex]),
                0.46 if len(links[vertex]) == 2 else (0.20 if len(links[vertex]) > 2 else 0.0),
            )
            for vertex in positions
        }

    tube = bmesh.new()
    deform_layer = tube.verts.layers.deform.verify()
    uv_layer = tube.loops.layers.uv.new("UVMap")
    rings, ring_uv, ring_sides = {}, {}, {}

    for vertex, position in positions.items():
        if not links[vertex]:
            continue
        is_tip = len(links[vertex]) == 1 and distance[vertex] > 0.0
        radius = (VEIN_TIP_RADIUS + (VEIN_TRUNK_RADIUS - VEIN_TIP_RADIUS) * thickness[vertex]) * (0.35 if is_tip else 1.0)
        location, normal, _, _ = surface.find_nearest(position)
        tangent_vec = positions[links[vertex][0]] - position
        tangent = tangent_vec.normalized() if tangent_vec.length > 1e-6 else Vector((0.0, 0.0, 1.0))
        side = tangent.cross(normal)
        side = side.normalized() if side.length > 1e-6 else tangent.orthogonal().normalized()
        up = side.cross(tangent).normalized()
        center = location - normal * radius * VEIN_SINK
        weights = {element.group: element.weight for element in mesh.vertices[vertex].groups}
        ring = []

        for step in range(VEIN_SIDES):
            angle = math.tau * step / VEIN_SIDES
            corner = tube.verts.new(center + (side * math.cos(angle) + up * math.sin(angle)) * radius)
            for group, weight in weights.items():
                corner[deform_layer][group] = weight
            ring.append(corner)

        rings[vertex] = ring
        ring_sides[vertex] = side
        ring_uv[vertex] = (distance[vertex] / longest, 1.0 - thickness[vertex])

    for vertex, above in segments:
        if vertex not in rings or above not in rings:
            continue
        is_mirrored = ring_sides[vertex].dot(ring_sides[above]) < 0.0
        matching = [(VEIN_SIDES // 2 - step) % VEIN_SIDES if is_mirrored else step for step in range(VEIN_SIDES)]

        for step in range(VEIN_SIDES):
            following = (step + 1) % VEIN_SIDES
            verts = (
                rings[vertex][step],
                rings[vertex][following],
                rings[above][matching[following]],
                rings[above][matching[step]],
            )
            if len(set(verts)) == 4:
                face = tube.faces.new(verts)
                face.smooth = True
                for loop, owner in zip(face.loops, (vertex, vertex, above, above)):
                    loop[uv_layer].uv = ring_uv[owner]

    bmesh.ops.recalc_face_normals(tube, faces=tube.faces[:])

    material = bpy.data.materials.new("M_MulaVein")
    material.use_nodes = True
    shader = material.node_tree.nodes["Principled BSDF"]
    shader.inputs["Base Color"].default_value = (0.65, 0.12, 0.02, 1.0)
    shader.inputs["Emission Color"].default_value = (1.0, 0.42, 0.06, 1.0)
    shader.inputs["Emission Strength"].default_value = 5.5

    return finish_skinned_object("MulaVeins", tube, mesh_object, armature, [material])


def compute_vein_halo(mesh, tree: dict, tatter_vertices: set) -> dict:
    """Exact 3D distance-based crimson halo around each lava vessel: wide (~9.5 cm) around thick neck/chest
    trunks and narrow (~3 cm) around thin shin capillaries, falling cleanly to 0 in the middle of muscle bellies
    so dark wine-charred muscles keep full 3D contrast inside every polygonal cell!"""
    segments = tree["segments"]
    thickness = tree["thickness"]
    samples = []

    for first, second in segments:
        p0 = mesh.vertices[first].co
        p1 = mesh.vertices[second].co
        t0 = thickness.get(first, 0.0)
        t1 = thickness.get(second, 0.0)
        for step in range(3):
            share = step / 2.0
            samples.append((p0.lerp(p1, share), t0 + (t1 - t0) * share))

    kd = KDTree(len(samples))
    for index, (pos, _) in enumerate(samples):
        kd.insert(pos, index)
    kd.balance()

    halo = {}
    for vertex in mesh.vertices:
        if vertex.index in tatter_vertices:
            continue
        best = 0.0
        for _, sample_idx, dist in kd.find_range(vertex.co, VEIN_HALO_MAX_REACH):
            thick = samples[sample_idx][1]
            reach = VEIN_HALO_MIN_REACH + (VEIN_HALO_MAX_REACH - VEIN_HALO_MIN_REACH) * (thick ** 0.75)
            if dist < reach:
                falloff = (1.0 - dist / reach) ** 1.85
                strength = (0.32 + 0.68 * thick) * falloff
                if strength > best:
                    best = strength
        if best > 0.001:
            halo[vertex.index] = best

    return halo


def paint_bake_mask(mesh_object, tree: dict, ember_heat: dict, tatter_vertices: set) -> None:
    """Corner colours for the bake:
    `mask`: R = 3D vein halo, G = ember of the neck crater, B = hoof, A = leg (fibres run vertically).
    `neck`: R = neck (fibres run up the neck), G = tatter darkening."""
    mesh = mesh_object.data
    group_names = {group.index: group.name for group in mesh_object.vertex_groups}
    spill = compute_vein_halo(mesh, tree, tatter_vertices)

    leg = [
        sum(
            element.weight
            for element in vertex.groups
            if "Leg" in group_names[element.group] or "Foot" in group_names[element.group]
        )
        for vertex in mesh.vertices
    ]
    neck = [
        sum(element.weight for element in vertex.groups if group_names[element.group] == "Neck")
        for vertex in mesh.vertices
    ]
    mask = mesh.color_attributes.new("mask", "FLOAT_COLOR", "CORNER")
    neck_mask = mesh.color_attributes.new("neck", "FLOAT_COLOR", "CORNER")

    for loop in mesh.loops:
        vertex = loop.vertex_index
        ember = ember_heat.get(vertex, 0.0)
        is_tatter = 1.0 if vertex in tatter_vertices else 0.0
        hoof = 0.0 if is_tatter else min(1.0, max(0.0, (mula_v2_body.HOOF_TOP - mesh.vertices[vertex].co.z) / HOOF_BLEND))
        mask.data[loop.index].color = (spill.get(vertex, 0.0), ember, hoof, min(1.0, leg[vertex]))
        neck_mask.data[loop.index].color = (min(1.0, neck[vertex]), is_tatter, 0.0, 1.0)


def add_marker(armature, name: str, bone: str, position: Vector) -> str:
    marker = bpy.data.objects.new(name, None)
    bpy.context.scene.collection.objects.link(marker)
    marker.parent = armature
    marker.parent_type = "BONE"
    marker.parent_bone = bone
    bpy.context.view_layer.update()
    marker.matrix_world = armature.matrix_world @ Matrix.Translation(position)
    return name


def strongest_bone(mesh_object, position: Vector, reach: float) -> str:
    group_names = [group.name for group in mesh_object.vertex_groups]
    totals = {}
    for vertex in mesh_object.data.vertices:
        if (vertex.co - position).length > reach:
            continue
        for element in vertex.groups:
            totals[element.group] = totals.get(element.group, 0.0) + element.weight
    return group_names[max(totals, key=totals.get)]


def crest_points(surface, stump) -> list:
    points = []
    ray_dir = Vector((0.0, -0.55, -0.83)).normalized()

    for share in MANE_NECK_SHARES:
        along_pt = stump.neck_base.lerp(stump.neck_mouth, share)
        location, _, _, _ = surface.ray_cast(along_pt - ray_dir * 3.5, ray_dir, 5.0)
        bone = "Neck" if share > MANE_BONE_SPLIT else "Shoulders"
        points.append((bone, location))

    for y in WITHERS_FIRE:
        location, _, _, _ = surface.ray_cast(Vector((0.0, y, 10.0)), Vector((0.0, 0.0, -1.0)), 6.0)
        points.append(("Shoulders", location))

    return [(bone, location) for bone, location in points if location is not None]


def tail_fire_markers() -> list:
    dock = mula_v2_base.tail_dock()
    return [
        ("Tail1", dock + Vector((0.0, 0.25, -0.02))),
        ("Tail1", dock + Vector((0.0, 0.95, -0.10))),
        ("Tail2", dock + Vector((0.0, 1.75, -0.45))),
        ("Tail3", dock + Vector((0.0, 2.55, -1.05))),
    ]


def add_fire_markers(mesh_object, armature, stump, crest: list) -> list:
    mouth = stump.origin + stump.axis * (stump.height - STUMP_FIRE_DEPTH)
    hooves = mula_v2_base.hoof_fires()
    names = [add_marker(armature, "FireStump", "Neck", mouth)]
    names += [add_marker(armature, f"FireMane_{index + 1}", bone, position) for index, (bone, position) in enumerate(crest)]
    names += [add_marker(armature, f"FireTail_{index + 1}", bone, position) for index, (bone, position) in enumerate(tail_fire_markers())]
    names += [
        add_marker(armature, f"FireHoof_{leg}", strongest_bone(mesh_object, position, HOOF_REACH), position)
        for leg, position in hooves.items()
    ]
    return names


def scatter(randomizer, reach: float) -> Vector:
    return Vector((randomizer.uniform(-reach, reach), randomizer.uniform(-reach, reach), randomizer.uniform(-reach, reach)))


def stump_tongues(randomizer, stump) -> list:
    """Fierce, broad blaze tongues erupting from the volcanic crater and sweeping backward."""
    tongues = []
    for index in range(STUMP_TONGUES):
        length = randomizer.uniform(1.5, 3.2)
        turn = index * mula_v2_body.STUMP_SEGMENTS / STUMP_TONGUES + randomizer.uniform(-1.2, 1.2)
        root = stump.point(randomizer.uniform(0.08, 0.74), turn, stump.height - STUMP_FIRE_DEPTH)
        rise = Vector((randomizer.uniform(-0.22, 0.22), 0.48, 0.80)).normalized()
        middle = root + rise * length * 0.54 + scatter(randomizer, 0.22)
        tip = root + rise * length + FLAME_WIND * length * randomizer.uniform(0.42, 0.85) + scatter(randomizer, 0.28)
        tongues.append({"curve": (root, middle, tip), "bones": ["Neck"], "width": randomizer.uniform(1.0, 1.65)})
    return tongues


def mane_tongues(randomizer, crest: list) -> list:
    tongues = []
    if len(crest) < 2:
        return tongues
    for index in range(MANE_TONGUES):
        share = index / (MANE_TONGUES - 1) * (len(crest) - 1)
        below = min(int(share), len(crest) - 2)
        bone = crest[below][0]
        root = crest[below][1].lerp(crest[below + 1][1], share - below) + Vector((randomizer.uniform(-0.18, 0.18), 0.0, -0.05))
        length = randomizer.uniform(1.30, 2.35) * (1.0 - 0.36 * index / MANE_TONGUES)
        middle = root + Vector((randomizer.uniform(-0.12, 0.12), 0.40, 0.68)) * length * 0.52 + scatter(randomizer, 0.14)
        tip = root + Vector((0.0, 0.45, 0.64)) * length + FLAME_WIND * length * randomizer.uniform(0.45, 0.85) + scatter(randomizer, 0.20)
        tongues.append({"curve": (root, middle, tip), "bones": [bone], "width": randomizer.uniform(0.68, 1.12)})
    return tongues


def tail_tongues(randomizer) -> list:
    """Wide, voluminous flowing mane-of-fire tail streaming back and downward in a broad vertical & lateral S-fan."""
    tongues = []
    dock = mula_v2_base.tail_dock()
    for index in range(TAIL_TONGUES):
        fan = (index / max(1, TAIL_TONGUES - 1) - 0.5) * 2.0
        length = randomizer.uniform(3.6, 6.6)
        # Wide vertical spread from high wind-blown locks (drop=0.20) down to low cascading locks (drop=1.08)
        drop = 0.20 + 0.88 * ((index * 7) % TAIL_TONGUES) / max(1, TAIL_TONGUES - 1) + randomizer.uniform(-0.06, 0.06)
        spread_x = fan * randomizer.uniform(0.18, 0.48) + randomizer.uniform(-0.10, 0.10)
        along_dock = randomizer.uniform(0.0, 0.52)
        root = dock + Vector((fan * 0.14, along_dock, -along_dock * 0.14 + randomizer.uniform(-0.08, 0.08)))
        middle = root + Vector((spread_x * 0.55, 0.65, 0.24 - drop * 0.36)) * length * 0.50
        tip = root + Vector((spread_x, 0.94 - drop * 0.20, -drop * 0.72 + 0.10)) * length + scatter(randomizer, 0.15)
        tongues.append({"curve": (root, middle, tip), "bones": TAIL_BONES, "width": randomizer.uniform(0.92, 1.58)})
    return tongues


def hoof_tongues(randomizer, mesh_object) -> list:
    """Crisp, dense flames hugging each cracked dark hoof and climbing boldly up the pastern and cannon."""
    tongues = []
    for position in mula_v2_base.hoof_fires().values():
        bone = strongest_bone(mesh_object, position, HOOF_REACH)
        for index in range(HOOF_TONGUES):
            angle = math.tau * index / HOOF_TONGUES + randomizer.uniform(-0.28, 0.28)
            tier = index % 3
            climb = 0.0 if tier == 0 else (HOOF_FLAME_CLIMB * (0.35 if tier == 1 else 0.88) * randomizer.uniform(0.75, 1.1))
            reach = 0.34 if tier == 0 else (0.22 if tier == 1 else 0.17)
            length = randomizer.uniform(1.25, 2.35) if tier < 2 else randomizer.uniform(1.05, 1.85)
            root = position + Vector((math.cos(angle) * reach, math.sin(angle) * reach, climb - 0.08))
            middle = root + Vector((math.cos(angle) * 0.06, math.sin(angle) * 0.06 + 0.08, length * 0.52))
            tip = position + Vector((math.cos(angle) * 0.10, math.sin(angle) * 0.10, climb + length)) + FLAME_WIND * length * randomizer.uniform(0.15, 0.40) + scatter(randomizer, 0.09)
            tongues.append({"curve": (root, middle, tip), "bones": [bone], "width": randomizer.uniform(0.56, 0.92)})
    return tongues


def add_tongue(flames, layers: dict, groups: dict, tongue: dict, seed: float) -> list:
    root, middle, tip = tongue["curve"]
    bones = tongue["bones"]
    directions = []
    rows = []

    for step in range(FLAME_SEGMENTS + 1):
        share = step / FLAME_SEGMENTS
        point = root.lerp(middle, share).lerp(middle.lerp(tip, share), share)
        direction = (middle - root).lerp(tip - middle, share).normalized()
        sliver = direction.orthogonal().normalized() * FLAME_SLIVER
        along_bones = share * (len(bones) - 1)
        lower = min(int(along_bones), max(0, len(bones) - 2))
        weights = (
            {bones[lower]: 1.0}
            if len(bones) == 1
            else {bones[lower]: 1.0 - (along_bones - lower), bones[lower + 1]: along_bones - lower}
        )
        row = [flames.verts.new(point - sliver), flames.verts.new(point + sliver)]

        for corner in row:
            for bone, weight in weights.items():
                corner[layers["deform"]][groups[bone]] = weight

        rows.append((row, share))
        directions += [direction, direction]

    for (lower_row, lower_share), (upper_row, upper_share) in zip(rows, rows[1:]):
        face = flames.faces.new((lower_row[0], lower_row[1], upper_row[1], upper_row[0]))
        face.smooth = True
        for loop, (across, along) in zip(
            face.loops, ((0.0, lower_share), (1.0, lower_share), (1.0, upper_share), (0.0, upper_share))
        ):
            loop[layers["uv"]].uv = (across, 1.0 - along)
            loop[layers["seed"]].uv = (seed, 1.0 - tongue["width"])

    return directions


def build_flames(mesh_object, armature, stump, crest: list):
    randomizer = random.Random(FLAME_SEED)
    tongues = (
        stump_tongues(randomizer, stump)
        + mane_tongues(randomizer, crest)
        + tail_tongues(randomizer)
        + hoof_tongues(randomizer, mesh_object)
    )

    for bone in TAIL_BONES:
        if bone not in mesh_object.vertex_groups:
            mesh_object.vertex_groups.new(name=bone)

    groups = {group.name: group.index for group in mesh_object.vertex_groups}
    flames = bmesh.new()
    layers = {
        "deform": flames.verts.layers.deform.verify(),
        "uv": flames.loops.layers.uv.new("UVMap"),
        "seed": flames.loops.layers.uv.new("Seed"),
    }
    directions = [direction for tongue in tongues for direction in add_tongue(flames, layers, groups, tongue, randomizer.random())]

    material = bpy.data.materials.new("M_MulaFlame")
    material.use_nodes = True
    shader = material.node_tree.nodes["Principled BSDF"]
    shader.inputs["Emission Color"].default_value = (1.0, 0.35, 0.04, 1.0)
    shader.inputs["Emission Strength"].default_value = 4.0
    flame_object = finish_skinned_object("MulaFlames", flames, mesh_object, armature, [material])
    flame_object.data.normals_split_custom_set_from_vertices(directions)

    return flame_object


def chain_loop_points(surface, center: Vector, normal: Vector) -> list:
    normal = normal.normalized()
    first_axis = normal.orthogonal().normalized()
    second_axis = normal.cross(first_axis)
    hits = []

    for step in range(96):
        angle = math.tau * step / 96
        direction = first_axis * math.cos(angle) + second_axis * math.sin(angle)
        location, hit_normal, _, _ = surface.ray_cast(center, direction, 4.0)
        if location is not None:
            outward = hit_normal if hit_normal.dot(direction) > 0.0 else direction
            hits.append((location + outward.normalized() * (LINK_WIRE + 0.018), outward.normalized()))

    resampled = [hits[0]]
    for point, direction in hits[1:]:
        if (point - resampled[-1][0]).length >= LINK_SPACING:
            resampled.append((point, direction))
    return resampled


def add_link(chain, deform_layer, group: int, matrix: Matrix, body_side: Vector, is_hot: bool, arc: float = 1.0) -> None:
    ring_count = LINK_SEGMENTS if arc >= 1.0 else int(LINK_SEGMENTS * arc) + 1
    rings = []

    for ring_index in range(ring_count):
        around = math.tau * ring_index / LINK_SEGMENTS
        spoke = Vector((math.cos(around), math.sin(around), 0.0))
        core = Vector((spoke.x * LINK_RADIUS * LINK_STRETCH, spoke.y * LINK_RADIUS, 0.0))
        ring = []

        for side_index in range(LINK_WIRE_SIDES):
            turn = math.tau * side_index / LINK_WIRE_SIDES
            corner = chain.verts.new(
                matrix @ (core + (spoke * math.cos(turn) + Vector((0.0, 0.0, math.sin(turn)))) * LINK_WIRE)
            )
            corner[deform_layer][group] = 1.0
            ring.append(corner)

        rings.append(ring)

    for ring_index in range(ring_count if arc >= 1.0 else ring_count - 1):
        following_ring = rings[(ring_index + 1) % ring_count]
        for side_index in range(LINK_WIRE_SIDES):
            following_side = (side_index + 1) % LINK_WIRE_SIDES
            face = chain.faces.new(
                (
                    rings[ring_index][side_index],
                    rings[ring_index][following_side],
                    following_ring[following_side],
                    following_ring[side_index],
                )
            )
            face.smooth = True
            face.normal_update()
            face.material_index = (
                1
                if is_hot
                and abs(face.normal.dot(body_side)) > 0.2
                and (face.calc_center_median() - matrix.translation).dot(body_side) > 0.0
                else 0
            )


def link_matrix(point: Vector, tangent: Vector, outward: Vector, lies_flat: bool) -> Matrix:
    side = outward.cross(tangent)
    side = side.normalized() if side.length > 1e-6 else tangent.orthogonal().normalized()
    outward = tangent.cross(side).normalized()
    columns = (tangent, side, outward) if lies_flat else (tangent, outward, -side)
    frame = Matrix(columns).transposed().to_4x4()
    frame.translation = point
    return frame


def build_chains(mesh_object, armature) -> tuple:
    surface = BVHTree.FromObject(mesh_object, bpy.context.evaluated_depsgraph_get())
    randomizer = random.Random(3)
    loops = [chain_loop_points(surface, center, normal) for center, normal, _ in CHAIN_LOOPS]
    anchors = [max(loops[loop], key=lambda item: item[0][axis] * sign) for loop, axis, sign, _, _ in CHAIN_ENDS]
    chain_bones = [f"{CHAIN_BONE_PREFIX}{index + 1}" for index in range(len(CHAIN_ENDS))]

    bpy.ops.object.select_all(action="DESELECT")
    bpy.context.view_layer.objects.active = armature
    armature.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")

    for name, (point, _), end in zip(chain_bones, anchors, CHAIN_ENDS):
        bone = armature.data.edit_bones.new(name)
        bone.head = point
        bone.tail = point + Vector((0.0, 0.0, -0.5))
        bone.parent = armature.data.edit_bones[end[4]]

    bpy.ops.object.mode_set(mode="OBJECT")

    for name in chain_bones:
        mesh_object.vertex_groups.new(name=name)

    group_indices = {group.name: group.index for group in mesh_object.vertex_groups}
    chain = bmesh.new()
    deform_layer = chain.verts.layers.deform.verify()

    for points, (_, _, bone) in zip(loops, CHAIN_LOOPS):
        for index, (point, outward) in enumerate(points):
            tangent = (points[(index + 1) % len(points)][0] - points[index - 1][0]).normalized()
            lies_flat = index % 2 == 0
            lifted = point + outward * (0.0 if lies_flat else LINK_RADIUS * 0.42)
            add_link(
                chain,
                deform_layer,
                group_indices[bone],
                link_matrix(lifted, tangent, outward, lies_flat),
                -outward,
                randomizer.random() < HOT_LINK_SHARE,
            )

    down = Vector((0.0, 0.0, -1.0))
    for name, (point, outward), end in zip(chain_bones, anchors, CHAIN_ENDS):
        flat_outward = Vector((outward.x, outward.y, 0.0))
        flat_outward = flat_outward.normalized() if flat_outward.length > 1e-4 else Vector((1.0, 0.0, 0.0))
        for index in range(end[3]):
            is_last = index == end[3] - 1
            hanging = point + flat_outward * 0.05 + down * LINK_SPACING * (index + 0.6)
            add_link(
                chain,
                deform_layer,
                group_indices[name],
                link_matrix(hanging, down, flat_outward, index % 2 == 0),
                -flat_outward,
                index < 2,
                0.72 if is_last else 1.0,
            )

    iron = bpy.data.materials.new("M_MulaChain")
    hot_iron = bpy.data.materials.new("M_MulaChainHot")

    for material in (iron, hot_iron):
        material.use_nodes = True
        shader = material.node_tree.nodes["Principled BSDF"]
        shader.inputs["Base Color"].default_value = (0.045, 0.04, 0.04, 1.0)
        shader.inputs["Metallic"].default_value = 1.0
        shader.inputs["Roughness"].default_value = 0.48

    hot_shader = hot_iron.node_tree.nodes["Principled BSDF"]
    hot_shader.inputs["Emission Color"].default_value = (1.0, 0.18, 0.02, 1.0)
    hot_shader.inputs["Emission Strength"].default_value = 1.35

    return finish_skinned_object("MulaChains", chain, mesh_object, armature, [iron, hot_iron]), chain_bones


def unwrap(mesh_object) -> None:
    bpy.ops.object.select_all(action="DESELECT")
    bpy.context.view_layer.objects.active = mesh_object
    mesh_object.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=math.radians(70.0), island_margin=0.008)
    bpy.ops.object.mode_set(mode="OBJECT")


def math_node(nodes, links, operation: str, first, second, clamp: bool = False):
    node = nodes.new("ShaderNodeMath")
    node.operation = operation
    node.use_clamp = clamp
    for slot, value in enumerate((first, second)):
        if isinstance(value, (int, float)):
            node.inputs[slot].default_value = value
        else:
            links.new(value, node.inputs[slot])
    return node.outputs[0]


def noise(nodes, links, coordinates, scale: float, detail: float, stretch=(1.0, 1.0, 1.0), tilt: float = 0.0):
    mapping = nodes.new("ShaderNodeMapping")
    texture = nodes.new("ShaderNodeTexNoise")
    mapping.inputs["Rotation"].default_value = (tilt, 0.0, 0.0)
    mapping.inputs["Scale"].default_value = stretch
    texture.inputs["Scale"].default_value = scale
    texture.inputs["Detail"].default_value = detail
    links.new(coordinates, mapping.inputs["Vector"])
    links.new(mapping.outputs[0], texture.inputs["Vector"])
    return texture.outputs[0]


def voronoi(nodes, links, coordinates, scale: float, feature: str):
    texture = nodes.new("ShaderNodeTexVoronoi")
    texture.feature = feature
    texture.inputs["Scale"].default_value = scale
    links.new(coordinates, texture.inputs["Vector"])
    return texture.outputs["Distance"]


def mix(nodes, links, factor, first, second):
    node = nodes.new("ShaderNodeMixRGB")
    for slot, value in enumerate((factor, first, second)):
        if isinstance(value, (int, float)):
            node.inputs[slot].default_value = value
        elif isinstance(value, tuple):
            node.inputs[slot].default_value = (*value, 1.0)
        else:
            links.new(value, node.inputs[slot])
    return node.outputs[0]


def color_ramp(nodes, links, factor, stops: list):
    node = nodes.new("ShaderNodeValToRGB")
    elements = node.color_ramp.elements
    while len(elements) < len(stops):
        elements.new(0.5)
    for element, (position, color) in zip(elements, stops):
        element.position = position
        element.color = (*color, 1.0)
    links.new(factor, node.inputs[0])
    return node.outputs[0]


def vector_math(nodes, links, operation: str, first, second=None):
    node = nodes.new("ShaderNodeVectorMath")
    node.operation = operation
    links.new(first, node.inputs[0])
    if isinstance(second, float):
        node.inputs[3].default_value = second
    elif isinstance(second, tuple):
        node.inputs[1].default_value = second
    elif second is not None:
        links.new(second, node.inputs[1])
    return node.outputs[0]


def crack_network(nodes, links, coordinates, heat):
    bend_vector = nodes.new("ShaderNodeTexNoise")
    bend_vector.inputs["Scale"].default_value = 1.8
    bend_vector.inputs["Detail"].default_value = 2.0
    links.new(coordinates, bend_vector.inputs["Vector"])
    offset = vector_math(nodes, links, "SUBTRACT", bend_vector.outputs["Color"], (0.5, 0.5, 0.5))
    bent = vector_math(nodes, links, "ADD", coordinates, vector_math(nodes, links, "SCALE", offset, CRACK_BEND))
    plate_edge = voronoi(nodes, links, bent, CRACK_PLATE_SCALE, "DISTANCE_TO_EDGE")
    fine_edge = voronoi(nodes, links, bent, CRACK_FINE_SCALE, "DISTANCE_TO_EDGE")
    wide = math_node(nodes, links, "SUBTRACT", 1.0, math_node(nodes, links, "MULTIPLY", plate_edge, 1.0 / CRACK_WIDTH, clamp=True))
    thin = math_node(
        nodes,
        links,
        "MULTIPLY",
        math_node(nodes, links, "SUBTRACT", 1.0, math_node(nodes, links, "MULTIPLY", fine_edge, 1.0 / CRACK_FINE_WIDTH, clamp=True)),
        CRACK_FINE_SHARE,
    )
    cracks = math_node(nodes, links, "MAXIMUM", wide, thin)
    heat_mask = math_node(nodes, links, "MULTIPLY", heat, 1.25, clamp=True)
    local_groove = math_node(nodes, links, "MULTIPLY", cracks, heat_mask)

    lit_noise = noise(nodes, links, coordinates, CRACK_LIT_SCALE, 2.0)
    lit = math_node(nodes, links, "MULTIPLY", math_node(nodes, links, "SUBTRACT", lit_noise, CRACK_LIT_THRESHOLD), CRACK_LIT_SHARPNESS)
    lit = math_node(nodes, links, "ADD", lit, math_node(nodes, links, "MULTIPLY", heat, CRACK_HEAT_BOOST), clamp=True)
    lit = math_node(nodes, links, "MULTIPLY", lit, heat_mask, clamp=True)
    scorch = math_node(nodes, links, "SUBTRACT", 1.0, math_node(nodes, links, "MULTIPLY", plate_edge, 1.0 / CRACK_SCORCH_WIDTH, clamp=True))
    scorch = math_node(nodes, links, "MULTIPLY", scorch, heat_mask)

    return math_node(nodes, links, "MULTIPLY", cracks, lit), local_groove, scorch


def build_bake_material(mesh_object) -> dict:
    """Dark wine-toned charred muscle hide: rich contrast inside polygonal cells, wide crimson halo only around
    vessels, glowing volcanic crater pit, and dark charred horn hooves split by narrow lava fissures."""
    material = bpy.data.materials.new("M_MulaHide")
    material.use_nodes = True
    nodes, links = material.node_tree.nodes, material.node_tree.links
    nodes.clear()

    coordinates = nodes.new("ShaderNodeTexCoord").outputs["Object"]
    mask = nodes.new("ShaderNodeAttribute")
    mask.attribute_name = "mask"
    channels = nodes.new("ShaderNodeSeparateColor")
    links.new(mask.outputs["Color"], channels.inputs[0])
    vein_glow, ember, hoof, leg = channels.outputs[0], channels.outputs[1], channels.outputs[2], mask.outputs["Alpha"]

    neck_mask = nodes.new("ShaderNodeAttribute")
    neck_mask.attribute_name = "neck"
    neck_channels = nodes.new("ShaderNodeSeparateColor")
    links.new(neck_mask.outputs["Color"], neck_channels.inputs[0])
    is_neck, is_tatter = neck_channels.outputs[0], neck_channels.outputs[1]

    grain = noise(nodes, links, coordinates, 2.8, 2.0)
    blotch = noise(nodes, links, coordinates, 1.2, 2.5)

    body_fibres = noise(nodes, links, coordinates, 1.0, 5.0, (FIBRE_DENSITY, 0.70, FIBRE_DENSITY * 1.15))
    leg_fibres = noise(nodes, links, coordinates, 1.0, 5.0, (FIBRE_DENSITY * 1.1, FIBRE_DENSITY * 1.1, 0.65))
    neck_fibres = noise(nodes, links, coordinates, 1.0, 5.0, (FIBRE_DENSITY * 1.1, FIBRE_DENSITY, 0.65), NECK_FIBRE_TILT)
    fibres = mix(nodes, links, is_neck, mix(nodes, links, leg, body_fibres, leg_fibres), neck_fibres)
    ridges = math_node(
        nodes,
        links,
        "MULTIPLY",
        math_node(nodes, links, "ABSOLUTE", math_node(nodes, links, "SUBTRACT", fibres, 0.5), 0.0),
        4.6,
        clamp=True,
    )
    crack_glow, groove, scorch = crack_network(nodes, links, coordinates, vein_glow)

    height = math_node(nodes, links, "MULTIPLY", ridges, 0.105)
    height = math_node(nodes, links, "SUBTRACT", height, math_node(nodes, links, "MULTIPLY", groove, CRACK_DEPTH))

    relief_image = nodes.new("ShaderNodeTexImage")
    relief = nodes.new("ShaderNodeNormalMap")
    relief.inputs["Strength"].default_value = RELIEF_STRENGTH
    links.new(relief_image.outputs["Color"], relief.inputs["Color"])
    ambient = nodes.new("ShaderNodeTexImage")
    bump = nodes.new("ShaderNodeBump")
    links.new(relief.outputs[0], bump.inputs["Normal"])
    bump.inputs["Strength"].default_value = 1.0
    bump.inputs["Distance"].default_value = 0.28
    links.new(height, bump.inputs["Height"])
    diffuse = nodes.new("ShaderNodeBsdfDiffuse")
    links.new(bump.outputs[0], diffuse.inputs["Normal"])

    # Deep charred wine / burgundy smoked muscle tone
    tone = math_node(
        nodes,
        links,
        "ADD",
        math_node(nodes, links, "MULTIPLY", grain, 0.26),
        math_node(nodes, links, "MULTIPLY", ridges, 0.74),
    )
    hide = color_ramp(
        nodes,
        links,
        tone,
        [
            (0.14, (0.011, 0.003, 0.004)),  # near-black burgundy crease
            (0.48, (0.055, 0.012, 0.014)),  # dark smoked wine muscle
            (0.84, (0.145, 0.030, 0.028)),  # crimson-wine muscle fibre ridge
        ],
    )
    hide = mix(nodes, links, math_node(nodes, links, "MULTIPLY", blotch, 0.30), hide, (0.022, 0.005, 0.006))
    hide = mix(nodes, links, math_node(nodes, links, "MULTIPLY", scorch, 0.65), hide, (0.009, 0.003, 0.003))
    # Crimson subsurface flush around lava vessels
    hide = mix(nodes, links, math_node(nodes, links, "MULTIPLY", vein_glow, 0.50, clamp=True), hide, (0.28, 0.016, 0.008))
    hide = mix(nodes, links, math_node(nodes, links, "MULTIPLY", is_tatter, 0.60), hide, (0.012, 0.004, 0.004))
    # Dark charred horn for the hooves so lava cracks stand out dramatically!
    is_hoof = math_node(nodes, links, "GREATER_THAN", hoof, 0.05)
    hide = mix(nodes, links, math_node(nodes, links, "MULTIPLY", hoof, 0.88, clamp=True), hide, (0.010, 0.005, 0.004))

    shaded = nodes.new("ShaderNodeMix")
    shaded.data_type = "RGBA"
    shaded.blend_type = "MULTIPLY"
    shaded.inputs["Factor"].default_value = RELIEF_SHADE
    links.new(hide, shaded.inputs["A"])
    links.new(ambient.outputs["Color"], shaded.inputs["B"])
    hide = shaded.outputs["Result"]

    is_ember = math_node(nodes, links, "GREATER_THAN", ember, 0.05)
    hide = mix(nodes, links, is_ember, hide, (0.028, 0.006, 0.003))

    roughness_value = math_node(nodes, links, "MULTIPLY_ADD", ridges, -0.25, clamp=True)
    roughness_value.node.inputs[2].default_value = 0.48
    combine = nodes.new("ShaderNodeCombineColor")
    links.new(roughness_value, combine.inputs[1])

    # Distance-controlled crimson halo: glows crimson right beside the vessel and drops to 0 inside muscle cells
    halo_glow = math_node(nodes, links, "MULTIPLY", vein_glow, HIDE_HALO)
    hide_glow = math_node(nodes, links, "MAXIMUM", halo_glow, crack_glow)

    ember_cracks = math_node(
        nodes,
        links,
        "SUBTRACT",
        1.0,
        math_node(nodes, links, "MULTIPLY", voronoi(nodes, links, coordinates, 5.5, "DISTANCE_TO_EDGE"), 6.0, clamp=True),
    )
    ember_glow = math_node(
        nodes,
        links,
        "ADD",
        math_node(nodes, links, "MULTIPLY", ember, 0.72),
        math_node(nodes, links, "MULTIPLY", ember_cracks, 0.42),
        clamp=True,
    )

    # Hooves: large dark charred horn plates split by 4-6 bold vertical lava fissures + glowing coronet & sole rim
    hoof_fissure = math_node(
        nodes,
        links,
        "SUBTRACT",
        1.0,
        math_node(
            nodes,
            links,
            "MULTIPLY",
            voronoi(nodes, links, vector_math(nodes, links, "MULTIPLY", coordinates, (1.15, 1.15, 0.24)), 3.4, "DISTANCE_TO_EDGE"),
            9.5,
            clamp=True,
        ),
    )
    coronet_band = math_node(
        nodes,
        links,
        "MULTIPLY",
        math_node(nodes, links, "SUBTRACT", 1.0, math_node(nodes, links, "MULTIPLY", math_node(nodes, links, "ABSOLUTE", math_node(nodes, links, "SUBTRACT", hoof, 0.14), 0.0), 6.5, clamp=True)),
        0.85,
    )
    sole_rim = math_node(nodes, links, "MULTIPLY", math_node(nodes, links, "SUBTRACT", hoof, 0.88, clamp=True), 6.5, clamp=True)
    hoof_cracks_and_rims = math_node(nodes, links, "MAXIMUM", hoof_fissure, math_node(nodes, links, "MAXIMUM", coronet_band, sole_rim))
    hoof_glow = math_node(nodes, links, "MULTIPLY", is_hoof, hoof_cracks_and_rims, clamp=True)
    # Replace general hide_glow on the hoof so the dark horn plates themselves stay unlit dark charcoal!
    body_or_hoof_glow = mix(nodes, links, is_hoof, hide_glow, hoof_glow)

    glow = color_ramp(
        nodes,
        links,
        mix(nodes, links, is_ember, body_or_hoof_glow, ember_glow),
        [
            (0.0, (0.0, 0.0, 0.0)),
            (0.18, (0.045, 0.001, 0.0)),   # soft outer crimson halo edge
            (0.48, (0.28, 0.012, 0.001)),  # deep blood-red lava halo
            (0.76, (0.82, 0.14, 0.010)),   # hot orange fissure / crater wall
            (1.0, (1.0, 0.68, 0.18)),      # white-yellow molten pit & hoof crack core
        ],
    )

    emission = nodes.new("ShaderNodeEmission")
    nodes.new("ShaderNodeOutputMaterial")
    mesh_object.data.materials.clear()
    mesh_object.data.materials.append(material)

    return {
        "material": material,
        "emission": emission,
        "diffuse": diffuse,
        "relief": relief_image,
        "ambient": ambient,
        "hide": hide,
        "roughness": combine.outputs[0],
        "glow": glow,
    }


def axial_bone_place(point: Vector) -> Vector:
    lifted_z = point.z + max(0.0, min(AXIAL_LIFT_TOP, point.z) - AXIAL_LIFT_FLOOR) / (AXIAL_LIFT_TOP - AXIAL_LIFT_FLOOR) * AXIAL_LIFT
    tail_boost = 0.42 * min(1.0, max(0.0, (point.y - 2.2) / 0.8))
    return Vector((point.x, point.y * AXIAL_TRUNK_STRETCH, lifted_z + tail_boost))


def move_bones(armature) -> None:
    bpy.ops.object.select_all(action="DESELECT")
    bpy.context.view_layer.objects.active = armature
    armature.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")

    leg_places = mula_v2_base.leg_bones()
    neck_base, neck_mouth = mula_v2_base.neck_axis()

    for bone in armature.data.edit_bones:
        if bone.name == "root":
            bone.head = Vector((0.0, 0.0, 0.0))
            bone.tail = Vector((0.0, 0.0, 2.402))
        elif bone.name in leg_places:
            bone.head, bone.tail = leg_places[bone.name]
        elif bone.name == "Neck":
            bone.head = axial_bone_place(bone.head)
            bone.tail = neck_base.lerp(neck_mouth, 0.85)
        elif bone.name == "Shoulders":
            bone.head = axial_bone_place(bone.head)
            bone.tail = neck_base.copy()
        else:
            bone.head = axial_bone_place(bone.head)
            bone.tail = axial_bone_place(bone.tail)

    bpy.ops.object.mode_set(mode="OBJECT")


def skin_to_skeleton(mesh_object, armature, pack_horse) -> None:
    skinning = {group.name for group in pack_horse.vertex_groups}

    for bone in armature.data.bones:
        bone.use_deform = bone.name in skinning and bone.name not in HEADLESS_BONES

    move_bones(armature)

    bpy.ops.object.select_all(action="DESELECT")
    mesh_object.select_set(True)
    armature.select_set(True)
    bpy.context.view_layer.objects.active = armature
    bpy.ops.object.parent_set(type="ARMATURE_AUTO")

    loose = sum(1 for vertex in mesh_object.data.vertices if not vertex.groups)
    if loose:
        raise RuntimeError(f"automatic weights left {loose} vertices without a bone")


def attach_foot_constraints(armature) -> None:
    for foot, leg_tip in FOOT_FOLLOWS.items():
        follow = armature.pose.bones[foot].constraints.new("COPY_LOCATION")
        follow.target = armature
        follow.subtarget = leg_tip
    bpy.context.view_layer.update()


def bake_relief(mesh_object, setup: dict, stump: mula_v2_body.Stump) -> None:
    high = mula_v2_base.load_body(light=False)
    mula_v2_body.swell_stump_collar(high, stump)
    nodes = setup["material"].node_tree.nodes
    bake_settings = bpy.context.scene.render.bake
    passes = {
        "NORMAL": ("relief", (0.5, 0.5, 1.0, 1.0), 1),
        "AO": ("ambient", (1.0, 1.0, 1.0, 1.0), RELIEF_AMBIENT_SAMPLES),
    }

    for polygon in high.data.polygons:
        polygon.use_smooth = True

    bpy.ops.object.select_all(action="DESELECT")
    high.select_set(True)
    mesh_object.select_set(True)
    bpy.context.view_layer.objects.active = mesh_object
    bake_settings.use_selected_to_active = True
    bake_settings.use_clear = False
    bake_settings.cage_extrusion = RELIEF_CAGE
    bake_settings.max_ray_distance = RELIEF_REACH

    for bake_type, (key, fill, samples) in passes.items():
        image = bpy.data.images.new(f"mula_relief_{key}", TEXTURE_SIZE, TEXTURE_SIZE, alpha=False)
        image.colorspace_settings.name = "Non-Color"
        image.generated_color = fill
        target = nodes.new("ShaderNodeTexImage")
        target.image = image
        nodes.active = target
        bpy.context.scene.cycles.samples = samples
        bpy.ops.object.bake(type=bake_type, margin=8)
        nodes.remove(target)
        setup[key].image = image

    bake_settings.use_selected_to_active = False
    high_mesh = high.data
    bpy.data.objects.remove(high)
    bpy.data.meshes.remove(high_mesh)


def bake(setup: dict, name: str, source, color_space: str = "sRGB"):
    material = setup["material"]
    nodes, links = material.node_tree.nodes, material.node_tree.links
    output = next(node for node in nodes if node.type == "OUTPUT_MATERIAL")
    image = bpy.data.images.new(name, TEXTURE_SIZE, TEXTURE_SIZE, alpha=False)
    target = nodes.new("ShaderNodeTexImage")

    image.colorspace_settings.name = color_space
    target.image = image
    nodes.active = target

    if source is None:
        links.new(setup["diffuse"].outputs[0], output.inputs["Surface"])
        bpy.ops.object.bake(type="NORMAL", margin=8)
    else:
        links.new(source, setup["emission"].inputs["Color"])
        links.new(setup["emission"].outputs[0], output.inputs["Surface"])
        bpy.ops.object.bake(type="EMIT", margin=8)

    image.pack()
    nodes.remove(target)

    return image


def build_game_material(material, images: dict) -> None:
    nodes, links = material.node_tree.nodes, material.node_tree.links
    nodes.clear()

    shader = nodes.new("ShaderNodeBsdfPrincipled")
    output = nodes.new("ShaderNodeOutputMaterial")
    textures = {}

    for name, image in images.items():
        textures[name] = nodes.new("ShaderNodeTexImage")
        textures[name].image = image

    normal_map = nodes.new("ShaderNodeNormalMap")
    channels = nodes.new("ShaderNodeSeparateColor")
    shader.inputs["Emission Strength"].default_value = HIDE_GLOW_STRENGTH
    links.new(textures["hide"].outputs["Color"], shader.inputs["Base Color"])
    links.new(textures["glow"].outputs["Color"], shader.inputs["Emission Color"])
    links.new(textures["normal"].outputs["Color"], normal_map.inputs["Color"])
    links.new(normal_map.outputs[0], shader.inputs["Normal"])
    links.new(textures["roughness"].outputs["Color"], channels.inputs[0])
    links.new(channels.outputs[1], shader.inputs["Roughness"])
    links.new(shader.outputs[0], output.inputs["Surface"])


def rename_actions() -> dict:
    kept = {}
    for action in list(bpy.data.actions):
        game_name = ACTION_NAMES.get(action.name.rsplit("|", 1)[-1].lower())
        if game_name is None:
            bpy.data.actions.remove(action)
            continue
        kept[game_name] = action.name
        action.name = game_name
    return kept


def withers_of(mesh_object) -> float:
    return max(vertex.co.z for vertex in mesh_object.data.vertices if WITHERS_Y[0] < vertex.co.y < WITHERS_Y[1])


def measure_proportions(mesh_object, tatter_vertices: set) -> dict:
    vertices = [vertex.co for index, vertex in enumerate(mesh_object.data.vertices) if index not in tatter_vertices]
    withers = withers_of(mesh_object)
    neck_base, neck_mouth = Vector(mula_v2_body.NECK_BASE), Vector(mula_v2_body.NECK_MOUTH)
    neck_axis = (neck_mouth - neck_base).normalized()
    neck_length = (neck_mouth - neck_base).length
    trunk = [position.y for position in vertices if 0.55 * withers < position.z < 0.82 * withers and abs(position.x) > 0.2]
    girth = [position.z for position in vertices if abs(position.x) < 0.25 and -1.85 < position.y < -1.45]

    def neck_width(share: float) -> float:
        slab = [
            abs(position.x)
            for position in vertices
            if abs((position - neck_base).dot(neck_axis) - share * neck_length) < 0.18 and position.y < neck_base.y + 1.0
        ]
        return 2.0 * max(slab) if slab else 1.0

    body_length = max(trunk) - min(trunk)

    def leg_width(is_front: bool, height_share: float) -> float:
        slab = [
            position.y
            for position in vertices
            if position.x > 0.35 and (position.y < -0.5) == is_front and abs(position.z - height_share * withers) < 0.12
        ]
        return round((max(slab) - min(slab)) / withers, 3) if slab else 0.0

    return {
        "body_per_withers": round(body_length / withers, 3),
        "chest_depth_per_withers": round((max(girth) - min(girth)) / withers, 3),
        "ground_to_elbow_per_withers": round(min(girth) / withers, 3),
        "croup_per_withers": round(max(position.z for position in vertices if position.y > 1.5) / withers, 3),
        "neck_degrees": round(math.degrees(math.atan2(neck_axis.z, -neck_axis.y)), 1),
        "neck_taper": round(neck_width(0.85) / neck_width(0.25), 3),
        "neck_per_body": round(neck_length / body_length, 3),
        "forearm_width_per_withers": leg_width(True, 0.42),
        "front_cannon_width_per_withers": leg_width(True, 0.16),
        "gaskin_width_per_withers": leg_width(False, 0.42),
        "hind_cannon_width_per_withers": leg_width(False, 0.16),
    }


def write_silhouette(mesh_object, path: Path) -> None:
    vertices = mesh_object.data.vertices
    withers = withers_of(mesh_object)
    polygons = [
        [(round(vertices[index].co.y / withers, 4), round(vertices[index].co.z / withers, 4)) for index in polygon.vertices]
        for polygon in mesh_object.data.polygons
    ]
    path.write_text(json.dumps(polygons), encoding="utf-8")


def scale_to_withers(mesh_object) -> float:
    factor = WITHERS_HEIGHT / withers_of(mesh_object)
    root = bpy.data.objects.new("MulaSemCabeca", None)
    bpy.context.scene.collection.objects.link(root)

    for scene_object in [
        scene_object for scene_object in bpy.context.scene.objects if scene_object.parent is None and scene_object != root
    ]:
        scene_object.parent = root

    root.matrix_world = Matrix.Scale(factor, 4)
    return factor


def stamp_buffer_hash(gltf_path: Path) -> None:
    document = json.loads(gltf_path.read_text(encoding="utf-8"))
    buffer_hash = hashlib.md5(gltf_path.with_suffix(".bin").read_bytes()).hexdigest()
    document["asset"]["extras"] = {"buffer_md5": buffer_hash}
    gltf_path.write_text(json.dumps(document, indent="\t"), encoding="utf-8", newline="\n")


def build(source: Path, silhouette: Path | None = None) -> dict:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    import_source(source)
    make_materials_opaque()

    pack_horse = next(scene_object for scene_object in bpy.context.scene.objects if scene_object.type == "MESH")
    armature = next(scene_object for scene_object in bpy.context.scene.objects if scene_object.type == "ARMATURE")
    armature.data.pose_position = "REST"
    bpy.context.view_layer.update()

    mula_v2_body.NECK_BASE, mula_v2_body.NECK_MOUTH = mula_v2_base.neck_axis()
    stump = mula_v2_body.Stump()

    strip_hair(pack_horse)
    mesh_object = mula_v2_base.load_body(light=True)
    rim, ember_heat = mula_v2_body.cut_stump(mesh_object, stump)
    skin_to_skeleton(mesh_object, armature, pack_horse)
    bpy.data.objects.remove(pack_horse)

    tree = grow_vein_tree(mesh_object.data, rim, set(ember_heat))
    veins = build_veins(mesh_object, armature, tree)
    chains, chain_bones = build_chains(mesh_object, armature)
    crest = crest_points(BVHTree.FromObject(mesh_object, bpy.context.evaluated_depsgraph_get()), stump)
    fire_markers = add_fire_markers(mesh_object, armature, stump, crest)
    flames = build_flames(mesh_object, armature, stump, crest)

    tatter_vertices = mula_v2_body.add_tatters(mesh_object)
    paint_bake_mask(mesh_object, tree, ember_heat, tatter_vertices)
    actions = rename_actions()
    unwrap(mesh_object)

    bpy.context.scene.render.engine = "CYCLES"
    setup = build_bake_material(mesh_object)
    bake_relief(mesh_object, setup, stump)
    bpy.context.scene.cycles.samples = 1

    bpy.ops.object.select_all(action="DESELECT")
    mesh_object.select_set(True)
    bpy.context.view_layer.objects.active = mesh_object

    images = {
        "hide": bake(setup, "mula_v2_hide", setup["hide"]),
        "glow": bake(setup, "mula_v2_glow", setup["glow"]),
        "roughness": bake(setup, "mula_v2_roughness", setup["roughness"], "Non-Color"),
        "normal": bake(setup, "mula_v2_normal", None, "Non-Color"),
    }
    build_game_material(setup["material"], images)
    mesh_object.data.color_attributes.remove(mesh_object.data.color_attributes["mask"])
    mesh_object.data.color_attributes.remove(mesh_object.data.color_attributes["neck"])
    mesh_object.name = "Mula"

    proportions = measure_proportions(mesh_object, tatter_vertices)
    if silhouette is not None:
        write_silhouette(mesh_object, silhouette)

    armature.data.pose_position = "POSE"
    attach_foot_constraints(armature)
    factor = scale_to_withers(mesh_object)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.export_scene.gltf(
        filepath=str(OUTPUT),
        export_format="GLTF_SEPARATE",
        export_texture_dir="textures",
        export_yup=True,
        export_animation_mode="ACTIONS",
        export_force_sampling=True,
        export_vertex_color="NONE",
    )
    stamp_buffer_hash(OUTPUT)

    vertex_counts = {scene_object.name: len(scene_object.data.vertices) for scene_object in (mesh_object, veins, chains, flames)}
    vertex_counts["total"] = sum(vertex_counts.values())
    sidecar = {
        "source": source.name,
        "withers_height": WITHERS_HEIGHT,
        "scale": round(factor, 5),
        "animations": actions,
        "proportions": proportions,
        "fire_markers": fire_markers,
        "hanging_chains": chain_bones,
        "vertices": vertex_counts,
    }
    OUTPUT.with_suffix(".json").write_text(json.dumps(sidecar, indent=1), encoding="utf-8", newline="\n")

    return sidecar


if __name__ == "__main__":
    arguments = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    source_path = Path(arguments[arguments.index("--source") + 1]) if "--source" in arguments else SOURCE
    silhouette_path = Path(arguments[arguments.index("--silhouette") + 1]) if "--silhouette" in arguments else None

    print(f"BUILT mula_v2: {build(source_path, silhouette_path)}")
