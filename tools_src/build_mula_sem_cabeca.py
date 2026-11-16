"""Build the "Mula sem cabeça" mob (Brazilian folklore, public domain) from the CC0 Quaternius horse
(tools/vendor/animals/FBX/Horse.fbx) -> art/mobs/mula_sem_cabeca/mula_sem_cabeca.gltf (+ textures, + JSON sidecar).

Realistic on purpose (the mob is meant to look out of this world next to the rest of the game). Steps:
  1. import the horse; delete head, mane and tail; close the neck with a sunken ember stump; subdivide; jag the rim;
  2. lava veins (object MulaVeins): a shortest-path tree over the body's edge graph, rooted at the stump rim, with
     random edge costs so the paths meander and merge like blood vessels; each vessel is a raised tube whose radius
     follows how many branches it feeds (thick trunks at the neck, thin tips at the hooves). UV.x = distance from
     the stump (0..1), UV.y = thickness (0..1): art/shaders/lava_vein.gdshader pulses along it;
  3. broken iron chains (object MulaChains): link loops wrapped around neck, girth and flank by ray casting the
     body, plus hanging broken ends skinned to new Chain<n> bones that the game sways;
  4. bake charred hide (albedo, normal with muscle bulges/fibres, roughness) and the glow the veins cast on the
     hide (emission) from 3D procedural nodes, seamless over UV islands;
  5. rename the actions the mob plays; scale so the withers stand WITHERS_HEIGHT metres; export.
The fire itself (stump blaze, mane, hooves, tail, smoke, sparks) is particles in features/mobs/mula_sem_cabeca.tscn.

Usage:
  blender -b --factory-startup -P tools_src/build_mula_sem_cabeca.py
"""

import heapq
import json
import math
import random
import sys
from pathlib import Path

import bmesh
import bpy
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

sys.path.insert(0, str(Path(__file__).resolve().parent))
from convert_farm_animals import import_source, make_materials_opaque  # noqa: E402

PROJECT_DIR = Path(__file__).resolve().parent.parent
SOURCE = PROJECT_DIR / "tools" / "vendor" / "animals" / "FBX" / "Horse.fbx"
OUTPUT = PROJECT_DIR / "art" / "mobs" / "mula_sem_cabeca" / "mula_sem_cabeca.gltf"
WITHERS_HEIGHT = 1.7  # metros
ACTION_NAMES = {"idle": "Idle", "walk": "Walk", "run": "Run", "jump": "Attack", "death": "Death"}
HAIR_MATERIAL_INDEX = 1  # material escuro do pacote: crina, rabo e cascos
HOOF_TOP = 1.0  # unidades do FBX (~3 por metro); faces escuras acima disto são crina/rabo
EMBER_MATERIAL_INDEX = 2
STUMP_HEIGHT = 1.15  # unidades do FBX da base do osso do pescoço até a boca do toco (o corte é esticado até aqui)
TEXTURE_SIZE = 2048
HIDE_GLOW_STRENGTH = 1.5

VEIN_SEED = 11
VEIN_ROOTS = 7  # troncos que nascem na borda do toco
VEIN_TIPS = 230  # pontas espalhadas pelo corpo
VEIN_HOOF_TIPS = 40  # pontas extras nas canelas/cascos
VEIN_TIP_RADIUS = 0.011
VEIN_TRUNK_RADIUS = 0.05
VEIN_TRUNK_FLOW = 45.0  # ramos alimentados a partir dos quais o vaso já é tronco
VEIN_SIDES = 6

LINK_RADIUS = 0.105
LINK_WIRE = 0.03
LINK_STRETCH = 1.5
LINK_SPACING = 0.25
LINK_SEGMENTS = 10
LINK_WIRE_SIDES = 5
# (centro, normal do plano, osso) em unidades do FBX: colar na base do pescoço, colar torto, barrigueira, flanco
CHAIN_LOOPS = [
    (Vector((0.0, -2.75, 5.3)), Vector((0.0, -0.68, 0.74)), "Shoulders"),
    (Vector((0.0, -2.55, 4.9)), Vector((0.25, -0.9, 0.35)), "Shoulders"),
    (Vector((0.0, -0.75, 3.9)), Vector((0.18, 1.0, 0.12)), "Torso"),
    (Vector((0.0, 1.15, 3.9)), Vector((-0.22, 1.0, -0.15)), "Hips"),
]
# (laço, eixo, sentido, elos pendurados, osso pai): o pedaço partido pende do ponto do laço mais extremo no eixo
CHAIN_ENDS = [(0, 2, -1.0, 7, "Shoulders"), (1, 0, 1.0, 4, "Shoulders"), (2, 0, -1.0, 6, "Torso"), (3, 0, 1.0, 5, "Hips"), (2, 0, 1.0, 3, "Torso")]
ATTACHMENT_BONES = {"neck_stump": "Head", "mane": ["Neck", "Shoulders"], "tail": ["Tail1", "Tail2", "Tail3", "Tail4"],
                    "hooves": ["FrontFoot.L", "FrontFoot.R", "BackFoot.L", "BackFoot.R"]}


def group_weight(vertex, deform_layer, group_indices: dict, names) -> float:
    return sum(vertex[deform_layer].get(group_indices[name], 0.0) for name in names if name in group_indices)


def behead(mesh_object, neck_base: Vector, neck_direction: Vector) -> None:
    """Delete head, mane and tail; cut the neck straight across; fill stray holes; stretch the stump and close it
    with a sunken cap (EMBER_MATERIAL_INDEX)."""
    mesh = mesh_object.data
    group_indices = {group.name: group.index for group in mesh_object.vertex_groups}
    edit_mesh = bmesh.new()

    edit_mesh.from_mesh(mesh)
    deform_layer = edit_mesh.verts.layers.deform.verify()

    hair_faces = [face for face in edit_mesh.faces if face.material_index == HAIR_MATERIAL_INDEX and face.calc_center_median().z > HOOF_TOP]
    bmesh.ops.delete(edit_mesh, geom=hair_faces, context="FACES")
    head_vertices = [vertex for vertex in edit_mesh.verts if group_weight(vertex, deform_layer, group_indices, ["Head"]) > 0.5]
    bmesh.ops.delete(edit_mesh, geom=head_vertices, context="VERTS")
    bmesh.ops.delete(edit_mesh, geom=[vertex for vertex in edit_mesh.verts if not vertex.link_faces], context="VERTS")

    hole = [vertex for edge in edit_mesh.edges if edge.is_boundary for vertex in edge.verts if group_weight(vertex, deform_layer, group_indices, ["Neck", "Shoulders"]) > 0.5]
    cut_height = min((vertex.co - neck_base).dot(neck_direction) for vertex in hole) - 0.05
    cut = bmesh.ops.bisect_plane(edit_mesh, geom=edit_mesh.verts[:] + edit_mesh.edges[:] + edit_mesh.faces[:], dist=0.0001,
                                 plane_co=neck_base + neck_direction * cut_height, plane_no=neck_direction, clear_outer=True)
    neck_edges = [element for element in cut["geom_cut"] if isinstance(element, bmesh.types.BMEdge)]
    other_edges = [edge for edge in edit_mesh.edges if edge.is_boundary and edge not in neck_edges]
    print(f"MULA cut height {cut_height:.2f}, hair faces {len(hair_faces)}, head verts {len(head_vertices)}, neck rim edges {len(neck_edges)}, other hole edges {len(other_edges)}")
    bmesh.ops.holes_fill(edit_mesh, edges=other_edges, sides=0)

    rim_vertices = list({vertex for edge in neck_edges for vertex in edge.verts})

    for vertex in rim_vertices:
        vertex.co += neck_direction * (STUMP_HEIGHT - cut_height)

    center = sum((vertex.co for vertex in rim_vertices), Vector()) / len(rim_vertices)
    inner = {}

    for vertex in rim_vertices:
        inner[vertex] = edit_mesh.verts.new(vertex.co.lerp(center, 0.3) - neck_direction * 0.25)
        inner[vertex][deform_layer][group_indices["Neck"]] = 1.0

    pit = edit_mesh.verts.new(center - neck_direction * 0.55)
    pit[deform_layer][group_indices["Neck"]] = 1.0

    for edge in neck_edges:
        first, second = edge.verts
        wall = edit_mesh.faces.new((first, second, inner[second], inner[first]))
        floor = edit_mesh.faces.new((inner[first], inner[second], pit))
        wall.material_index = EMBER_MATERIAL_INDEX
        floor.material_index = EMBER_MATERIAL_INDEX

    bmesh.ops.recalc_face_normals(edit_mesh, faces=edit_mesh.faces[:])
    edit_mesh.to_mesh(mesh)
    edit_mesh.free()


def subdivide(mesh_object) -> None:
    bpy.context.view_layer.objects.active = mesh_object
    mesh_object.select_set(True)
    modifier = mesh_object.modifiers.new("Smooth", "SUBSURF")
    modifier.levels = 2
    bpy.ops.object.modifier_move_to_index(modifier=modifier.name, index=0)
    bpy.ops.object.modifier_apply(modifier=modifier.name)
    bpy.ops.object.shade_smooth()


def roughen_rim(mesh, neck_direction: Vector) -> tuple:
    """Jag the stump rim; returns (rim vertex indices, vertex indices inside the ember cap)."""
    ember_vertices = {index for polygon in mesh.polygons if polygon.material_index == EMBER_MATERIAL_INDEX for index in polygon.vertices}
    hide_vertices = {index for polygon in mesh.polygons if polygon.material_index != EMBER_MATERIAL_INDEX for index in polygon.vertices}
    rim = sorted(ember_vertices & hide_vertices)
    randomizer = random.Random(7)

    for index in rim:
        mesh.vertices[index].co += neck_direction * randomizer.choice((-0.1, 0.0, 0.12, 0.3))

    mesh.update()

    return rim, ember_vertices - set(rim)


def grow_vein_tree(mesh, rim: list, blocked: set) -> dict:
    """Shortest-path tree from VEIN_ROOTS rim vertices over the edge graph with random edge costs, kept only where
    it leads to a sampled tip. Returns {"parent": {vertex: parent or None}, "flow": {vertex: tips fed},
    "distance": {vertex: path length from the stump}}."""
    randomizer = random.Random(VEIN_SEED)
    positions = [vertex.co.copy() for vertex in mesh.vertices]
    neighbours = {}

    for edge in mesh.edges:
        first, second = edge.vertices

        if first in blocked or second in blocked:
            continue

        cost = (positions[first] - positions[second]).length * randomizer.uniform(0.5, 2.2)
        neighbours.setdefault(first, []).append((second, cost))
        neighbours.setdefault(second, []).append((first, cost))

    roots = rim[:: max(1, len(rim) // VEIN_ROOTS)][:VEIN_ROOTS]
    cost_to = {root: 0.0 for root in roots}
    parent = {root: None for root in roots}
    queue = [(0.0, root) for root in roots]

    while queue:
        cost, vertex = heapq.heappop(queue)

        if cost > cost_to[vertex]:
            continue

        for neighbour, edge_cost in neighbours.get(vertex, []):
            if cost + edge_cost < cost_to.get(neighbour, math.inf):
                cost_to[neighbour] = cost + edge_cost
                parent[neighbour] = vertex
                heapq.heappush(queue, (cost + edge_cost, neighbour))

    reachable = sorted(set(parent) - set(rim))
    low = [vertex for vertex in reachable if positions[vertex].z < 1.6]
    tips = randomizer.sample(reachable, VEIN_TIPS) + randomizer.sample(low, min(VEIN_HOOF_TIPS, len(low)))
    flow = {}

    for tip in tips:
        vertex = tip

        while vertex is not None:
            flow[vertex] = flow.get(vertex, 0) + 1
            vertex = parent[vertex]

    distance = {}

    for vertex in sorted(flow, key=cost_to.get):
        distance[vertex] = 0.0 if parent[vertex] is None else distance[parent[vertex]] + (positions[vertex] - positions[parent[vertex]]).length

    return {"parent": {vertex: parent[vertex] for vertex in flow}, "flow": flow, "distance": distance}


def vein_thickness(flow: int) -> float:
    """0 at a tip, 1 at a trunk."""
    return min(1.0, math.sqrt(flow / VEIN_TRUNK_FLOW))


def finish_skinned_object(name: str, edit_mesh, body_object, armature, materials: list):
    """bmesh -> object with the body's vertex groups (same order, so deform indices match) bound to the armature."""
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
    """Raised tubes along the tree, smoothed and laid back on the hide; skin weights copied from the body."""
    mesh = mesh_object.data
    surface = BVHTree.FromObject(mesh_object, bpy.context.evaluated_depsgraph_get())
    parent, flow, distance = tree["parent"], tree["flow"], tree["distance"]
    longest = max(distance.values())
    links = {vertex: [] for vertex in parent}

    for vertex, above in parent.items():
        if above is not None:
            links[vertex].append(above)
            links[above].append(vertex)

    positions = {vertex: mesh.vertices[vertex].co.copy() for vertex in parent}

    for _ in range(4):
        positions = {vertex: positions[vertex].lerp(sum((positions[link] for link in links[vertex]), Vector()) / len(links[vertex]), 0.5 if len(links[vertex]) > 1 else 0.0)
                     for vertex in positions}

    tube = bmesh.new()
    deform_layer = tube.verts.layers.deform.verify()
    uv_layer = tube.loops.layers.uv.new("UVMap")
    rings, ring_uv = {}, {}

    for vertex, position in positions.items():
        is_tip = len(links[vertex]) == 1 and parent[vertex] is not None
        thickness = vein_thickness(flow[vertex])
        radius = (VEIN_TIP_RADIUS + (VEIN_TRUNK_RADIUS - VEIN_TIP_RADIUS) * thickness) * (0.35 if is_tip else 1.0)
        location, normal, _, _ = surface.find_nearest(position)
        toward = parent[vertex] if parent[vertex] is not None else links[vertex][0]
        tangent = (positions[toward] - position).normalized() * (1.0 if parent[vertex] is not None else -1.0)
        side = tangent.cross(normal).normalized()
        up = side.cross(tangent)
        center = location + normal * radius * 0.3
        weights = {element.group: element.weight for element in mesh.vertices[vertex].groups}
        ring = []

        for step in range(VEIN_SIDES):
            angle = 2.0 * math.pi * step / VEIN_SIDES
            corner = tube.verts.new(center + (side * math.cos(angle) + up * math.sin(angle)) * radius)

            for group, weight in weights.items():
                corner[deform_layer][group] = weight

            ring.append(corner)

        rings[vertex] = ring
        ring_uv[vertex] = (distance[vertex] / longest, thickness)

    for vertex, above in parent.items():
        if above is None:
            continue

        for step in range(VEIN_SIDES):
            following = (step + 1) % VEIN_SIDES
            face = tube.faces.new((rings[vertex][step], rings[vertex][following], rings[above][following], rings[above][step]))
            face.smooth = True

            for loop, owner in zip(face.loops, (vertex, vertex, above, above)):
                loop[uv_layer].uv = ring_uv[owner]

    bmesh.ops.recalc_face_normals(tube, faces=tube.faces[:])

    material = bpy.data.materials.new("M_MulaVein")
    material.use_nodes = True
    shader = material.node_tree.nodes["Principled BSDF"]
    shader.inputs["Base Color"].default_value = (0.6, 0.12, 0.02, 1.0)
    shader.inputs["Emission Color"].default_value = (1.0, 0.4, 0.05, 1.0)
    shader.inputs["Emission Strength"].default_value = 5.0

    return finish_skinned_object("MulaVeins", tube, mesh_object, armature, [material])


def paint_bake_mask(mesh_object, tree: dict) -> None:
    """Corner colour for the bake: R = glow the veins cast on the hide, G = ember cap, A = leg (fibres run down)."""
    mesh = mesh_object.data
    group_names = {group.index: group.name for group in mesh_object.vertex_groups}
    glow = {vertex: 0.35 + 0.65 * vein_thickness(flow) for vertex, flow in tree["flow"].items()}
    spill = dict(glow)

    for edge in mesh.edges:
        first, second = edge.vertices
        spill[first] = max(spill.get(first, 0.0), glow.get(second, 0.0) * 0.45)
        spill[second] = max(spill.get(second, 0.0), glow.get(first, 0.0) * 0.45)

    leg = [sum(element.weight for element in vertex.groups if "Leg" in group_names[element.group] or "Foot" in group_names[element.group]) for vertex in mesh.vertices]
    mask = mesh.color_attributes.new("mask", "FLOAT_COLOR", "CORNER")

    for polygon in mesh.polygons:
        ember = 1.0 if polygon.material_index == EMBER_MATERIAL_INDEX else 0.0

        for loop_index in polygon.loop_indices:
            vertex = mesh.loops[loop_index].vertex_index
            mask.data[loop_index].color = (spill.get(vertex, 0.0), ember, 0.0, min(1.0, leg[vertex]))

        polygon.material_index = 0


def chain_loop_points(surface, center: Vector, normal: Vector) -> list:
    """Closed polyline hugging the body where the plane (center, normal) cuts it, resampled every LINK_SPACING.
    Each item is (point, outward direction)."""
    normal = normal.normalized()
    first_axis = normal.orthogonal().normalized()
    second_axis = normal.cross(first_axis)
    hits = []

    for step in range(72):
        angle = 2.0 * math.pi * step / 72
        direction = first_axis * math.cos(angle) + second_axis * math.sin(angle)
        location, _, _, _ = surface.ray_cast(center, direction)

        if location is not None:
            hits.append((location + direction * (LINK_WIRE + 0.02), direction))

    resampled = [hits[0]]

    for point, direction in hits[1:]:
        if (point - resampled[-1][0]).length >= LINK_SPACING:
            resampled.append((point, direction))

    return resampled


def add_link(chain, deform_layer, group: int, matrix: Matrix, body_side: Vector, is_hot: bool, arc: float = 1.0) -> None:
    """One chain link (stretched torus) placed by `matrix`; faces turned to the body glow when the link is hot."""
    ring_count = LINK_SEGMENTS if arc >= 1.0 else int(LINK_SEGMENTS * arc) + 1
    rings = []

    for ring_index in range(ring_count):
        around = 2.0 * math.pi * ring_index / LINK_SEGMENTS
        spoke = Vector((math.cos(around), math.sin(around), 0.0))
        core = Vector((spoke.x * LINK_RADIUS * LINK_STRETCH, spoke.y * LINK_RADIUS, 0.0))
        ring = []

        for side_index in range(LINK_WIRE_SIDES):
            turn = 2.0 * math.pi * side_index / LINK_WIRE_SIDES
            corner = chain.verts.new(matrix @ (core + (spoke * math.cos(turn) + Vector((0.0, 0.0, math.sin(turn)))) * LINK_WIRE))
            corner[deform_layer][group] = 1.0
            ring.append(corner)

        rings.append(ring)

    for ring_index in range(ring_count if arc >= 1.0 else ring_count - 1):
        following_ring = rings[(ring_index + 1) % ring_count]

        for side_index in range(LINK_WIRE_SIDES):
            following_side = (side_index + 1) % LINK_WIRE_SIDES
            face = chain.faces.new((rings[ring_index][side_index], rings[ring_index][following_side], following_ring[following_side], following_ring[side_index]))
            face.smooth = True
            face.normal_update()
            face.material_index = 1 if is_hot and abs(face.normal.dot(body_side)) > 0.2 and (face.calc_center_median() - matrix.translation).dot(body_side) > 0.0 else 0


def link_matrix(point: Vector, tangent: Vector, outward: Vector, lies_flat: bool) -> Matrix:
    """Link frame: X along the chain; a flat link shows its hole to the outside, the next one stands on edge."""
    side = outward.cross(tangent).normalized()
    outward = tangent.cross(side)
    columns = (tangent, side, outward) if lies_flat else (tangent, outward, -side)
    frame = Matrix(columns).transposed().to_4x4()

    frame.translation = point

    return frame


def build_chains(mesh_object, armature) -> tuple:
    """Wrapped loops (rigid on one bone each) and hanging broken ends on new Chain<n> bones. Returns (object, bones)."""
    surface = BVHTree.FromObject(mesh_object, bpy.context.evaluated_depsgraph_get())
    randomizer = random.Random(3)
    loops = [chain_loop_points(surface, center, normal) for center, normal, _ in CHAIN_LOOPS]
    anchors = [max(loops[loop], key=lambda item: item[0][axis] * sign) for loop, axis, sign, _, _ in CHAIN_ENDS]
    chain_bones = [f"Chain{index + 1}" for index in range(len(CHAIN_ENDS))]

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
            lifted = point + outward * (0.0 if lies_flat else LINK_RADIUS * 0.45)
            add_link(chain, deform_layer, group_indices[bone], link_matrix(lifted, tangent, outward, lies_flat), -outward, randomizer.random() < 0.6)

    down = Vector((0.0, 0.0, -1.0))

    for name, (point, outward), end in zip(chain_bones, anchors, CHAIN_ENDS):
        flat_outward = Vector((outward.x, outward.y, 0.0)).normalized()

        for index in range(end[3]):
            is_last = index == end[3] - 1
            hanging = point + flat_outward * 0.05 + down * LINK_SPACING * (index + 0.6)
            add_link(chain, deform_layer, group_indices[name], link_matrix(hanging, down, flat_outward, index % 2 == 0), -flat_outward, index < 2, 0.72 if is_last else 1.0)

    iron = bpy.data.materials.new("M_MulaChain")
    hot_iron = bpy.data.materials.new("M_MulaChainHot")

    for material in (iron, hot_iron):
        material.use_nodes = True
        shader = material.node_tree.nodes["Principled BSDF"]
        shader.inputs["Base Color"].default_value = (0.045, 0.04, 0.04, 1.0)
        shader.inputs["Metallic"].default_value = 1.0
        shader.inputs["Roughness"].default_value = 0.5

    hot_shader = hot_iron.node_tree.nodes["Principled BSDF"]
    hot_shader.inputs["Emission Color"].default_value = (1.0, 0.22, 0.03, 1.0)
    hot_shader.inputs["Emission Strength"].default_value = 2.0

    return finish_skinned_object("MulaChains", chain, mesh_object, armature, [iron, hot_iron]), chain_bones


def unwrap(mesh_object) -> None:
    bpy.ops.object.select_all(action="DESELECT")
    bpy.context.view_layer.objects.active = mesh_object
    mesh_object.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=math.radians(70.0), island_margin=0.01)
    bpy.ops.object.mode_set(mode="OBJECT")


def math_node(nodes, links, operation: str, first, second, clamp: bool = False):
    """Math node over sockets or plain numbers; returns the output socket."""
    node = nodes.new("ShaderNodeMath")
    node.operation = operation
    node.use_clamp = clamp

    for slot, value in enumerate((first, second)):
        if isinstance(value, (int, float)):
            node.inputs[slot].default_value = value
        else:
            links.new(value, node.inputs[slot])

    return node.outputs[0]


def noise(nodes, links, coordinates, scale: float, detail: float, stretch=(1.0, 1.0, 1.0)):
    mapping = nodes.new("ShaderNodeMapping")
    texture = nodes.new("ShaderNodeTexNoise")

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
    """Mix node over sockets, numbers (factor) or RGB tuples; returns the output socket."""
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


def build_bake_material(mesh_object) -> dict:
    """Procedural charred hide. Returns the material, the two shaders to bake through (emission for colour data,
    diffuse with bump for the normal map) and the colour sockets for hide, roughness and glow."""
    material = bpy.data.materials.new("M_MulaHide")
    material.use_nodes = True
    nodes, links = material.node_tree.nodes, material.node_tree.links
    nodes.clear()

    coordinates = nodes.new("ShaderNodeTexCoord").outputs["Object"]
    mask = nodes.new("ShaderNodeAttribute")
    mask.attribute_name = "mask"
    channels = nodes.new("ShaderNodeSeparateColor")
    links.new(mask.outputs["Color"], channels.inputs[0])
    vein_glow, ember, leg = channels.outputs[0], channels.outputs[1], mask.outputs["Alpha"]

    grain = noise(nodes, links, coordinates, 5.0, 5.0)
    blotch = noise(nodes, links, coordinates, 1.4, 2.0)
    body_fibres = noise(nodes, links, coordinates, 1.0, 3.0, (9.0, 1.1, 9.0))
    leg_fibres = noise(nodes, links, coordinates, 1.0, 3.0, (11.0, 11.0, 1.2))
    fibres = mix(nodes, links, leg, body_fibres, leg_fibres)
    bulges = math_node(nodes, links, "SUBTRACT", 1.0, voronoi(nodes, links, coordinates, 1.1, "SMOOTH_F1"), clamp=True)
    crackle = math_node(nodes, links, "MULTIPLY", voronoi(nodes, links, coordinates, 11.0, "DISTANCE_TO_EDGE"), 14.0, clamp=True)

    height = math_node(nodes, links, "MULTIPLY", bulges, 0.55)
    height = math_node(nodes, links, "ADD", height, math_node(nodes, links, "MULTIPLY", fibres, 0.45))
    height = math_node(nodes, links, "ADD", height, math_node(nodes, links, "MULTIPLY", crackle, 0.12))
    height = math_node(nodes, links, "ADD", height, math_node(nodes, links, "MULTIPLY", grain, 0.12))

    bump = nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 1.0
    bump.inputs["Distance"].default_value = 0.22
    links.new(height, bump.inputs["Height"])
    diffuse = nodes.new("ShaderNodeBsdfDiffuse")
    links.new(bump.outputs[0], diffuse.inputs["Normal"])

    tone = math_node(nodes, links, "ADD", math_node(nodes, links, "MULTIPLY", grain, 0.5), math_node(nodes, links, "MULTIPLY", fibres, 0.5))
    hide = color_ramp(nodes, links, tone, [(0.3, (0.022, 0.013, 0.013)), (0.5, (0.07, 0.03, 0.026)), (0.72, (0.17, 0.075, 0.055))])
    hide = mix(nodes, links, math_node(nodes, links, "MULTIPLY", blotch, 0.55), hide, (0.012, 0.01, 0.011))
    hide = mix(nodes, links, math_node(nodes, links, "SUBTRACT", 1.0, crackle), hide, (0.01, 0.006, 0.006))
    hide = mix(nodes, links, math_node(nodes, links, "MULTIPLY", vein_glow, 0.4), hide, (0.3, 0.03, 0.01))
    hide = mix(nodes, links, ember, hide, (0.25, 0.04, 0.01))

    roughness_value = math_node(nodes, links, "MULTIPLY_ADD", grain, 0.4, clamp=True)
    roughness_value.node.inputs[2].default_value = 0.42
    combine = nodes.new("ShaderNodeCombineColor")
    links.new(roughness_value, combine.inputs[1])

    hide_glow = math_node(nodes, links, "MULTIPLY", vein_glow, math_node(nodes, links, "ADD", math_node(nodes, links, "MULTIPLY", grain, 0.6), 0.5))
    ember_glow = math_node(nodes, links, "ADD", math_node(nodes, links, "MULTIPLY", grain, 0.9), 0.3, clamp=True)
    glow = color_ramp(nodes, links, mix(nodes, links, ember, hide_glow, ember_glow),
                      [(0.0, (0.0, 0.0, 0.0)), (0.45, (0.1, 0.005, 0.0)), (0.8, (0.5, 0.07, 0.005)), (1.0, (1.0, 0.45, 0.08))])

    emission = nodes.new("ShaderNodeEmission")
    nodes.new("ShaderNodeOutputMaterial")
    mesh_object.data.materials.clear()
    mesh_object.data.materials.append(material)

    return {"material": material, "emission": emission, "diffuse": diffuse, "hide": hide, "roughness": combine.outputs[0], "glow": glow}


def bake(setup: dict, name: str, source, color_space: str = "sRGB"):
    """Bake a colour socket through the emission shader, or the tangent normal map when `source` is None."""
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


def scale_to_withers(mesh_object) -> float:
    """Hang everything under a scaled root (the FBX actions animate the armature object, so it cannot be scaled)."""
    group_names = {group.index: group.name for group in mesh_object.vertex_groups}
    back = [vertex.co.z for vertex in mesh_object.data.vertices if any(group_names[element.group] in ("Torso", "Hips") and element.weight > 0.5 for element in vertex.groups)]
    factor = WITHERS_HEIGHT / max(back)
    root = bpy.data.objects.new("MulaSemCabeca", None)

    bpy.context.scene.collection.objects.link(root)

    for scene_object in [scene_object for scene_object in bpy.context.scene.objects if scene_object.parent is None and scene_object != root]:
        scene_object.parent = root

    root.matrix_world = Matrix.Scale(factor, 4)

    return factor


def build() -> dict:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    import_source(SOURCE)
    make_materials_opaque()

    mesh_object = next(scene_object for scene_object in bpy.context.scene.objects if scene_object.type == "MESH")
    armature = next(scene_object for scene_object in bpy.context.scene.objects if scene_object.type == "ARMATURE")
    neck_bone = armature.data.bones["Neck"]
    neck_direction = (neck_bone.tail_local - neck_bone.head_local).normalized()

    mesh_object.data.color_attributes.remove(mesh_object.data.color_attributes[0])
    behead(mesh_object, neck_bone.head_local.copy(), neck_direction)
    subdivide(mesh_object)
    rim, ember_vertices = roughen_rim(mesh_object.data, neck_direction)
    tree = grow_vein_tree(mesh_object.data, rim, ember_vertices)
    veins = build_veins(mesh_object, armature, tree)
    chains, chain_bones = build_chains(mesh_object, armature)
    paint_bake_mask(mesh_object, tree)
    unwrap(mesh_object)

    bpy.context.scene.render.engine = "CYCLES"
    bpy.context.scene.cycles.samples = 1
    setup = build_bake_material(mesh_object)
    images = {
        "hide": bake(setup, "mula_sem_cabeca_hide", setup["hide"]),
        "glow": bake(setup, "mula_sem_cabeca_glow", setup["glow"]),
        "roughness": bake(setup, "mula_sem_cabeca_roughness", setup["roughness"], "Non-Color"),
        "normal": bake(setup, "mula_sem_cabeca_normal", None, "Non-Color"),
    }
    build_game_material(setup["material"], images)
    mesh_object.data.color_attributes.remove(mesh_object.data.color_attributes["mask"])
    mesh_object.name = "Mula"

    actions = rename_actions()
    factor = scale_to_withers(mesh_object)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.export_scene.gltf(filepath=str(OUTPUT), export_format="GLTF_SEPARATE", export_texture_dir="textures", export_yup=True,
                              export_animation_mode="ACTIONS", export_force_sampling=True, export_vertex_color="NONE")

    sidecar = {"source": SOURCE.name, "withers_height": WITHERS_HEIGHT, "scale": round(factor, 5), "animations": actions,
               "attachment_bones": {**ATTACHMENT_BONES, "hanging_chains": chain_bones},
               "vertices": {scene_object.name: len(scene_object.data.vertices) for scene_object in (mesh_object, veins, chains)}}
    OUTPUT.with_suffix(".json").write_text(json.dumps(sidecar, indent=1), encoding="utf-8", newline="\n")

    return sidecar


if __name__ == "__main__":
    print(f"BUILT mula_sem_cabeca: {build()}")
