"""Build the "Mula sem cabeça" mob (Brazilian folklore, public domain) over the skeleton and animations of the CC0
Quaternius horse (tools/vendor/animals/FBX/Horse.fbx) -> art/mobs/mula_sem_cabeca/mula_sem_cabeca.gltf (+ textures,
+ JSON sidecar).

Realistic on purpose (the mob is meant to look out of this world next to the rest of the game). Steps:
  1. import the horse and keep only its skeleton, actions and skin weights; the body itself is sculpted by
     tools_src/mula_body.py (muscle volumes fused by voxel remesh, neck cut by a jagged solid with an ember pit);
  2. lava veins (object MulaVeins): a shortest-path tree over the body's edge graph, rooted around the neck cut,
     with random edge costs that are cheaper along the grooves between muscles, so the vessels meander, merge and
     run where real ones would; some tips bridge to a neighbouring vessel and, near the stump, the vessels close
     into a web of polygonal cells. Each vessel is a raised tube whose
     radius follows how many branches it feeds (thick trunks at the neck, thin tips at the hooves). UV.x =
     distance from the stump (0..1), UV.y = thickness (0..1): art/shaders/lava_vein.gdshader pulses along it;
  3. broken iron chains (object MulaChains): link loops wrapped around neck, girth and flank by ray casting the
     body, plus hanging broken ends skinned to new Chain<n> bones that the game sways;
  4. fire: ribbons of flame (object MulaFlames) for the stump blaze, mane, tail and hooves, opened toward the
     camera by art/shaders/flame_ribbon.gdshader, and markers (empties parented to bones: FireStump,
     FireMane_<n>, FireTail_<n>, FireHoof_<leg>) where features/mobs/mula_sem_cabeca.tscn hangs embers, smoke
     and light;
  5. bake charred hide (albedo, normal with muscle bulges/fibres, roughness) and the glow of veins, neck embers
     and hooves on the hide (emission) from 3D procedural nodes, seamless over UV islands;
  6. rename the actions the mob plays; scale so the withers stand WITHERS_HEIGHT metres; export.

Usage:
  blender -b --factory-startup -P tools_src/build_mula_sem_cabeca.py -- [--source <Horse.fbx|.glb>]
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
from mathutils.bvhtree import BVHTree

sys.path.insert(0, str(Path(__file__).resolve().parent))
import mula_body  # noqa: E402
from convert_farm_animals import import_source, make_materials_opaque  # noqa: E402

PROJECT_DIR = Path(__file__).resolve().parent.parent
SOURCE = PROJECT_DIR / "tools" / "vendor" / "animals" / "FBX" / "Horse.fbx"
OUTPUT = PROJECT_DIR / "art" / "mobs" / "mula_sem_cabeca" / "mula_sem_cabeca.gltf"
WITHERS_HEIGHT = 1.7  # metros
ACTION_NAMES = {"idle": "Idle", "walk": "Walk", "run": "Run", "jump": "Attack", "death": "Death"}
HAIR_MATERIAL_INDEX = 1  # material escuro do pacote: crina, rabo e cascos
HAIR_FLOOR = 1.0  # unidades do pacote (~3,4 por metro); faces escuras acima disto são crina/rabo
HOOF_BLEND = 0.25  # faixa em que o casco em brasa vira couro
TEXTURE_SIZE = 2048
HIDE_GLOW_STRENGTH = 2.0
HIDE_HALO = 0.3  # quanto do brilho das veias vaza para o couro em volta
FIBRE_DENSITY = 6.0  # fibras de músculo por unidade, atravessando a fibra
NECK_FIBRE_TILT = math.radians(-23.0)  # o pescoço sobe inclinado para a frente: as fibras acompanham

VEIN_SEED = 11
VEIN_ROOTS = 9  # troncos que nascem na borda do toco
VEIN_TIPS = 60  # pontas espalhadas pelo corpo
VEIN_FRONT_DENSITY = 6.0  # pescoço, peito e ombros (Y < VEIN_FRONT_END) têm mais pontas que o resto
VEIN_FRONT_END = -0.9
VEIN_SHIN_TIPS = 8  # pontas extras nas canelas e cascos
VEIN_SHIN_TOP = 1.6
VEIN_BRIDGES = 12  # pontas que alcançam um vaso vizinho e fecham a teia
VEIN_BRIDGE_REACH = 9  # arestas que uma ponte pode atravessar
VEIN_GROOVE_PULL = 4.0  # quanto o sulco entre músculos barateia o caminho
VEIN_WEB_REACH = 4.0  # até esta distância do toco (pela pele) os vasos fecham células poligonais
VEIN_WEB_SPACING = 1.0  # distância entre os nós da teia
VEIN_WEB_LINKS = 3  # vizinhos a que cada nó se liga
VEIN_WEB_DETOUR = 2.4  # caminho mais longo que isto vezes a reta entre dois nós não vira vaso
VEIN_WEB_THICKNESS = (1.0, 0.4)  # grossura dos vasos da teia: junto ao toco, no fim do alcance
VEIN_TIP_RADIUS = 0.008
VEIN_TRUNK_RADIUS = 0.078
VEIN_TRUNK_FLOW = 30.0  # ramos alimentados a partir dos quais o vaso já é tronco
VEIN_SIDES = 6
VEIN_SINK = 0.3  # fração do raio que o vaso afunda no couro: fica rente, como fenda de lava, não como cano

LINK_RADIUS = 0.15
LINK_WIRE = 0.05
LINK_STRETCH = 1.5
LINK_SPACING = 0.35
LINK_SEGMENTS = 10
LINK_WIRE_SIDES = 5
HOT_LINK_SHARE = 0.35  # elos dos laços que encostam em veia e ficam em brasa
# (centro, normal do plano, osso) em unidades do FBX: colar na base do pescoço, colar torto, barrigueira, flanco
CHAIN_LOOPS = [
    (Vector((0.0, -2.75, 5.3)), Vector((0.0, -0.68, 0.74)), "Shoulders"),
    (Vector((0.0, -2.55, 4.9)), Vector((0.25, -0.9, 0.35)), "Shoulders"),
]
# (laço, eixo, sentido, elos pendurados, osso pai): o pedaço partido pende do ponto do laço mais extremo no eixo
CHAIN_ENDS = [(0, 2, -1.0, 5, "Shoulders"), (1, 0, 1.0, 4, "Shoulders")]
# Marcadores de fogo: vazios presos aos ossos, que o jogo troca pelas partículas (prefixo do nome = tipo de fogo).
STUMP_FIRE_DEPTH = 0.22  # a labareda nasce dentro da cratera do toco
MANE_HEIGHTS = [1.9, 1.35, 0.8, 0.25, -0.3]  # alturas no eixo do toco onde a crina de fogo pega na crista
WITHERS_FIRE = [-1.55, -1.05]  # Y dos pontos da cernelha
MANE_BONE_SPLIT = 0.0  # abaixo desta altura do eixo a crista segue o osso Shoulders
# Rabo de fogo: arco que sai do sabugo para trás e cai; cada ponto segue um osso do rabo (balança na animação).
TAIL_FIRE = [("Tail1", Vector((0.0, 3.1, 4.9))), ("Tail1", Vector((0.0, 3.8, 4.7))), ("Tail2", Vector((0.0, 4.5, 4.2))), ("Tail3", Vector((0.0, 5.1, 3.5)))]
TAIL_DOCK = Vector((0.0, 3.0, 4.9))
HOOF_FIRE = {"FrontL": Vector((0.87, -2.13, 0.2)), "FrontR": Vector((-0.87, -2.13, 0.2)), "BackL": Vector((0.75, 2.5, 0.2)), "BackR": Vector((-0.75, 2.5, 0.2))}
HOOF_REACH = 0.6  # raio em volta do marcador que decide qual osso carrega o casco

# Labaredas em fita (objeto MulaFlames): cada língua de fogo é uma tira quase sem largura ao longo de uma curva;
# art/shaders/flame_ribbon.gdshader abre a tira de frente para a câmera. Normal = direção da curva, UV.x = lado,
# UV.y = raiz (0) à ponta (1), UV2 = (semente, largura em unidades do pacote).
FLAME_SEED = 5
FLAME_SEGMENTS = 10
FLAME_SLIVER = 0.002  # meia largura real da tira (só para o triângulo não ser degenerado)
FLAME_WIND = Vector((0.0, 1.0, 0.0))  # as línguas deitam para trás, como num bicho que avança
STUMP_TONGUES, MANE_TONGUES, TAIL_TONGUES, HOOF_TONGUES = 12, 18, 22, 9
HOOF_FLAME_CLIMB = 1.3  # até onde, acima do casco, nascem línguas subindo pela canela
TAIL_BONES = ["Tail1", "Tail2", "Tail3"]

# Proporção esticada no fim (stretch_proportions): patas alongadas entre o boleto e a articulação do ombro/anca,
# tronco alongado entre os dois pares de patas.
LEG_STRETCH = 1.35
LEG_STRETCH_FLOOR, LEG_STRETCH_TOP = 0.75, 3.14
TRUNK_STRETCH = 1.2
TRUNK_STRETCH_REACH = 1.5
FOOT_FOLLOWS = {"FrontFoot.L": "FrontLowLeg.L_end", "FrontFoot.R": "FrontLowLeg.R_end", "BackFoot.L": "BackLowLeg.L_end", "BackFoot.R": "BackLowLeg.R_end"}


def strip_hair(mesh_object) -> None:
    """Weld the pack horse and drop mane and tail: what is left only lends its skin weights to the sculpted body."""
    edit_mesh = bmesh.new()

    edit_mesh.from_mesh(mesh_object.data)
    bmesh.ops.remove_doubles(edit_mesh, verts=edit_mesh.verts[:], dist=0.0005)
    hair_faces = [face for face in edit_mesh.faces if face.material_index == HAIR_MATERIAL_INDEX and face.calc_center_median().z > HAIR_FLOOR]
    bmesh.ops.delete(edit_mesh, geom=hair_faces, context="FACES")
    edit_mesh.to_mesh(mesh_object.data)
    edit_mesh.free()


def groove_depths(mesh, neighbours: dict) -> list:
    """Per vertex: how far its neighbours rise above it along its normal, in edge lengths (> 0 in a groove)."""
    depths = []

    for vertex in mesh.vertices:
        around = [mesh.vertices[neighbour].co for neighbour in neighbours.get(vertex.index, [])]

        if not around:
            depths.append(0.0)
            continue

        middle = sum(around, Vector()) / len(around)
        reach = sum((position - vertex.co).length for position in around) / len(around)
        depths.append((middle - vertex.co).dot(vertex.normal) / reach)

    return depths


def weighted_sample(randomizer, population: list, weights: list, count: int) -> list:
    """`count` different items, likelier the heavier (Efraimidis-Spirakis keys)."""
    keys = [randomizer.random() ** (1.0 / weight) for weight in weights]
    order = sorted(range(len(population)), key=keys.__getitem__, reverse=True)

    return [population[index] for index in order[:count]]


def grow_vein_tree(mesh, rim: list, blocked: set) -> dict:
    """Shortest-path tree from VEIN_ROOTS rim vertices over the edge graph, kept only where it leads to a sampled
    tip. Edge costs are random (the paths meander and merge like blood vessels) and cheaper along grooves (the
    vessels run between the muscles). Some tips then reach across to a neighbouring vessel, and near the stump
    the vessels close into a web of polygonal cells (weave_vein_web).
    Returns {"segments": [(vertex, vertex)], "thickness": {vertex: 0 tip .. 1 trunk}, "distance": {vertex: path
    length from the stump}}."""
    randomizer = random.Random(VEIN_SEED)
    positions = [vertex.co.copy() for vertex in mesh.vertices]
    open_edges = [edge.vertices[:] for edge in mesh.edges if edge.vertices[0] not in blocked and edge.vertices[1] not in blocked]
    adjacent = {}

    for first, second in open_edges:
        adjacent.setdefault(first, []).append(second)
        adjacent.setdefault(second, []).append(first)

    depths = groove_depths(mesh, adjacent)
    neighbours = {}

    for first, second in open_edges:
        groove = min(2.5, max(0.3, 1.0 - VEIN_GROOVE_PULL * (depths[first] + depths[second]) * 0.5))
        length = (positions[first] - positions[second]).length
        cost = length * randomizer.uniform(0.5, 2.4) * groove
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
    low = [vertex for vertex in reachable if positions[vertex].z < VEIN_SHIN_TOP]
    tips = weighted_sample(randomizer, reachable, density, VEIN_TIPS) + randomizer.sample(low, min(VEIN_SHIN_TIPS, len(low)))
    flow = {}

    for tip in tips:
        vertex = tip

        while vertex is not None:
            flow[vertex] = flow.get(vertex, 0) + 1
            vertex = parent[vertex]

    kept = {vertex: parent[vertex] for vertex in flow}
    bridges = [bridge for bridge in (bridge_from(tip, kept, flow, adjacent) for tip in randomizer.sample(tips, VEIN_BRIDGES)) if bridge]
    web_segments, web_thickness = weave_vein_web(randomizer, positions, neighbours, distance)
    branches = [(vertex, above) for vertex, above in kept.items() if above is not None]
    segments = list({frozenset(pair): pair for pair in branches + bridges + web_segments}.values())
    thickness = {vertex: vein_thickness(count) for vertex, count in flow.items()}

    for vertex, web_share in web_thickness.items():
        thickness[vertex] = max(thickness.get(vertex, 0.0), web_share)

    return {"segments": segments, "thickness": thickness, "distance": distance}


def spread_web_nodes(randomizer, positions: list, candidates: list) -> list:
    """Candidates kept so that no two stand closer than VEIN_WEB_SPACING (dart throwing over a grid of cells)."""
    cells = {}
    nodes = []

    randomizer.shuffle(candidates)

    for vertex in candidates:
        position = positions[vertex]
        cell = (round(position.x / VEIN_WEB_SPACING), round(position.y / VEIN_WEB_SPACING), round(position.z / VEIN_WEB_SPACING))
        around = [other for dx in (-1, 0, 1) for dy in (-1, 0, 1) for dz in (-1, 0, 1) for other in cells.get((cell[0] + dx, cell[1] + dy, cell[2] + dz), [])]

        if all((positions[other] - position).length >= VEIN_WEB_SPACING for other in around):
            cells.setdefault(cell, []).append(vertex)
            nodes.append(vertex)

    return nodes


def cheapest_path(neighbours: dict, start: int, goal: int, longest: float) -> list:
    """Vertices of the cheapest path from start to goal, or [] when it would run longer than `longest`."""
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


def weave_vein_web(randomizer, positions: list, neighbours: dict, distance: dict) -> tuple:
    """Near the stump the lava vessels close into polygonal cells: nodes spread over the hide, each joined to its
    nearest nodes by the cheapest path. Returns (segments, {vertex: thickness, thicker toward the stump})."""
    candidates = sorted(vertex for vertex, length in distance.items() if length < VEIN_WEB_REACH)
    nodes = spread_web_nodes(randomizer, positions, candidates)
    pairs = set()

    for node in nodes:
        nearest = sorted(nodes, key=lambda other: (positions[other] - positions[node]).length_squared)[1:VEIN_WEB_LINKS + 1]
        pairs.update(frozenset((node, other)) for other in nearest)

    segments = []
    thickness = {}
    near, far = VEIN_WEB_THICKNESS

    for first, second in sorted(tuple(sorted(pair)) for pair in pairs):
        path = cheapest_path(neighbours, first, second, (positions[first] - positions[second]).length * VEIN_WEB_DETOUR)
        vessel = randomizer.uniform(0.7, 1.0)
        segments += list(zip(path, path[1:]))

        for vertex in path:
            share = min(1.0, distance[vertex] / VEIN_WEB_REACH)
            thickness[vertex] = max(thickness.get(vertex, 0.0), (near + (far - near) * share ** 0.7) * vessel)

    return segments, thickness


def bridge_from(tip: int, kept: dict, flow: dict, adjacent: dict):
    """Grow a thin vessel from a tip over bare hide to the nearest vessel that is not its own branch; the new
    vertices join `kept`/`flow` and the pair that closes the loop is returned (None when nothing is in reach)."""
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
    """0 at a tip, 1 at a trunk."""
    return min(1.0, (flow / VEIN_TRUNK_FLOW) ** 0.55)


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
    """Raised tubes along the vessels, smoothed and laid back on the hide; skin weights copied from the body."""
    mesh = mesh_object.data
    surface = BVHTree.FromObject(mesh_object, bpy.context.evaluated_depsgraph_get())
    segments, thickness, distance = tree["segments"], tree["thickness"], tree["distance"]
    longest = max(distance[vertex] for vertex in thickness)
    links = {vertex: [] for vertex in thickness}

    for vertex, above in segments:
        links[vertex].append(above)
        links[above].append(vertex)

    positions = {vertex: mesh.vertices[vertex].co.copy() for vertex in links}

    for _ in range(4):
        positions = {vertex: positions[vertex].lerp(sum((positions[link] for link in links[vertex]), Vector()) / len(links[vertex]), 0.5 if len(links[vertex]) > 1 else 0.0)
                     for vertex in positions}

    tube = bmesh.new()
    deform_layer = tube.verts.layers.deform.verify()
    uv_layer = tube.loops.layers.uv.new("UVMap")
    rings, ring_uv, ring_sides = {}, {}, {}

    for vertex, position in positions.items():
        is_tip = len(links[vertex]) == 1 and distance[vertex] > 0.0
        radius = (VEIN_TIP_RADIUS + (VEIN_TRUNK_RADIUS - VEIN_TIP_RADIUS) * thickness[vertex]) * (0.35 if is_tip else 1.0)
        location, normal, _, _ = surface.find_nearest(position)
        tangent = (positions[links[vertex][0]] - position).normalized()
        side = tangent.cross(normal).normalized()
        up = side.cross(tangent)
        center = location - normal * radius * VEIN_SINK
        weights = {element.group: element.weight for element in mesh.vertices[vertex].groups}
        ring = []

        for step in range(VEIN_SIDES):
            angle = 2.0 * math.pi * step / VEIN_SIDES
            corner = tube.verts.new(center + (side * math.cos(angle) + up * math.sin(angle)) * radius)

            for group, weight in weights.items():
                corner[deform_layer][group] = weight

            ring.append(corner)

        rings[vertex] = ring
        ring_sides[vertex] = side
        ring_uv[vertex] = (distance[vertex] / longest, 1.0 - thickness[vertex])  # o glTF inverte o V: o jogo lê a grossura

    for vertex, above in segments:
        # o anel vizinho pode ter sido montado no sentido contrário: aí os cantos casam espelhados
        is_mirrored = ring_sides[vertex].dot(ring_sides[above]) < 0.0
        matching = [(VEIN_SIDES // 2 - step) % VEIN_SIDES if is_mirrored else step for step in range(VEIN_SIDES)]

        for step in range(VEIN_SIDES):
            following = (step + 1) % VEIN_SIDES
            face = tube.faces.new((rings[vertex][step], rings[vertex][following], rings[above][matching[following]], rings[above][matching[step]]))
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


def paint_bake_mask(mesh_object, tree: dict, ember_heat: dict) -> None:
    """Corner colours for the bake. `mask`: R = glow the veins cast on the hide, G = ember of the neck cut, B = hoof,
    A = leg (fibres run down). `neck`: R = neck (fibres run up the neck)."""
    mesh = mesh_object.data
    group_names = {group.index: group.name for group in mesh_object.vertex_groups}
    glow = {vertex: 0.25 + 0.75 * thickness for vertex, thickness in tree["thickness"].items()}
    spill = dict(glow)

    for edge in mesh.edges:
        first, second = edge.vertices
        spill[first] = max(spill.get(first, 0.0), glow.get(second, 0.0) ** 2 * 0.45)
        spill[second] = max(spill.get(second, 0.0), glow.get(first, 0.0) ** 2 * 0.45)

    leg = [sum(element.weight for element in vertex.groups if "Leg" in group_names[element.group] or "Foot" in group_names[element.group]) for vertex in mesh.vertices]
    neck = [sum(element.weight for element in vertex.groups if group_names[element.group] == "Neck") for vertex in mesh.vertices]
    mask = mesh.color_attributes.new("mask", "FLOAT_COLOR", "CORNER")
    neck_mask = mesh.color_attributes.new("neck", "FLOAT_COLOR", "CORNER")

    for loop in mesh.loops:
        vertex = loop.vertex_index
        ember = ember_heat.get(vertex, 0.0)
        hoof = min(1.0, max(0.0, (mula_body.HOOF_TOP - mesh.vertices[vertex].co.z) / HOOF_BLEND))
        mask.data[loop.index].color = (spill.get(vertex, 0.0), ember, hoof, min(1.0, leg[vertex]))
        neck_mask.data[loop.index].color = (min(1.0, neck[vertex]), 0.0, 0.0, 1.0)


def add_marker(armature, name: str, bone: str, position: Vector) -> str:
    """Empty at `position` (armature space) that follows `bone`; the game hangs fire on it."""
    marker = bpy.data.objects.new(name, None)

    bpy.context.scene.collection.objects.link(marker)
    marker.parent = armature
    marker.parent_type = "BONE"
    marker.parent_bone = bone
    bpy.context.view_layer.update()
    marker.matrix_world = armature.matrix_world @ Matrix.Translation(position)

    return name


def strongest_bone(mesh_object, position: Vector, reach: float) -> str:
    """Bone that carries most of the skin within `reach` of a point."""
    group_names = [group.name for group in mesh_object.vertex_groups]
    totals = {}

    for vertex in mesh_object.data.vertices:
        if (vertex.co - position).length > reach:
            continue

        for element in vertex.groups:
            totals[element.group] = totals.get(element.group, 0.0) + element.weight

    return group_names[max(totals, key=totals.get)]


def crest_points(surface, stump) -> list:
    """(bone, point on the hide) down the crest of the neck (MANE_HEIGHTS along the stump axis) and over the withers."""
    points = []

    for height in MANE_HEIGHTS:
        location, _, _, _ = surface.ray_cast(stump.origin + stump.axis * height + stump.crest * 4.0, -stump.crest)
        points.append(("Neck" if height > MANE_BONE_SPLIT else "Shoulders", location))

    for y in WITHERS_FIRE:
        location, _, _, _ = surface.ray_cast(Vector((0.0, y, 9.0)), Vector((0.0, 0.0, -1.0)))
        points.append(("Shoulders", location))

    return points


def add_fire_markers(mesh_object, armature, stump, crest: list) -> list:
    """FireStump in the neck pit, FireMane_<n> down the crest to the withers, FireTail_<n> along the arc of the
    tail, FireHoof_<leg> on each hoof (on whichever bone moves that hoof)."""
    mouth = stump.origin + stump.axis * (stump.height - STUMP_FIRE_DEPTH)
    names = [add_marker(armature, "FireStump", "Neck", mouth)]

    names += [add_marker(armature, f"FireMane_{index + 1}", bone, position) for index, (bone, position) in enumerate(crest)]
    names += [add_marker(armature, f"FireTail_{index + 1}", bone, position) for index, (bone, position) in enumerate(TAIL_FIRE)]
    names += [add_marker(armature, f"FireHoof_{leg}", strongest_bone(mesh_object, position, HOOF_REACH), position) for leg, position in HOOF_FIRE.items()]

    return names


def scatter(randomizer, reach: float) -> Vector:
    return Vector((randomizer.uniform(-reach, reach), randomizer.uniform(-reach, reach), randomizer.uniform(-reach, reach)))


def stump_tongues(randomizer, stump) -> list:
    """Tongues of the blaze: born inside the pit, rising along the neck and bending back."""
    tongues = []

    for index in range(STUMP_TONGUES):
        length = randomizer.uniform(1.5, 3.2)
        root = stump.point(randomizer.uniform(0.1, 0.62), index * mula_body.STUMP_SEGMENTS // STUMP_TONGUES, stump.height - STUMP_FIRE_DEPTH)
        rise = (stump.axis * 0.5 + Vector((0.0, 0.0, 0.6))).normalized()
        middle = root + rise * length * 0.55 + scatter(randomizer, 0.25)
        tip = root + rise * length + FLAME_WIND * length * randomizer.uniform(0.2, 0.55) + scatter(randomizer, 0.3)
        tongues.append({"curve": (root, middle, tip), "bones": ["Neck"], "width": randomizer.uniform(0.9, 1.5)})

    return tongues


def mane_tongues(randomizer, crest: list) -> list:
    """Mane of fire: tongues along the crest from the stump to the withers, shorter toward the back."""
    tongues = []

    for index in range(MANE_TONGUES):
        share = index / (MANE_TONGUES - 1) * (len(crest) - 1)
        below = min(int(share), len(crest) - 2)
        bone = crest[below][0]
        root = crest[below][1].lerp(crest[below + 1][1], share - below) + Vector((randomizer.uniform(-0.12, 0.12), 0.0, -0.05))
        length = randomizer.uniform(1.3, 2.3) * (1.0 - 0.4 * index / MANE_TONGUES)
        middle = root + Vector((0.0, 0.25, 0.75)) * length * 0.5 + scatter(randomizer, 0.15)
        tip = root + Vector((0.0, 0.25, 0.75)) * length + FLAME_WIND * length * randomizer.uniform(0.3, 0.7) + scatter(randomizer, 0.2)
        tongues.append({"curve": (root, middle, tip), "bones": [bone], "width": randomizer.uniform(0.6, 1.0)})

    return tongues


def tail_tongues(randomizer) -> list:
    """Tail of fire: a wide head of hair streaming back from the dock and falling, each lock ending somewhere else."""
    tongues = []

    for _ in range(TAIL_TONGUES):
        length = randomizer.uniform(3.0, 5.6)
        fall = randomizer.uniform(0.45, 1.15)
        root = TAIL_DOCK + scatter(randomizer, 0.1)
        middle = root + Vector((randomizer.uniform(-0.3, 0.3), 0.8, 0.2 - fall * 0.15)) * length * 0.5
        tip = root + Vector((randomizer.uniform(-0.3, 0.3), 1.0 - fall * 0.45, -fall * 0.85)) * length
        tongues.append({"curve": (root, middle, tip), "bones": TAIL_BONES, "width": randomizer.uniform(0.7, 1.25)})

    return tongues


def hoof_tongues(randomizer, mesh_object) -> list:
    """Each hoof wrapped in short tongues that climb the pastern."""
    tongues = []

    for position in HOOF_FIRE.values():
        bone = strongest_bone(mesh_object, position, HOOF_REACH)

        for index in range(HOOF_TONGUES):
            angle = 2.0 * math.pi * index / HOOF_TONGUES + randomizer.uniform(-0.4, 0.4)
            climb = HOOF_FLAME_CLIMB * randomizer.random() * (index % 2)  # metade nasce no casco, metade canela acima
            reach = 0.3 if climb == 0.0 else 0.17
            length = randomizer.uniform(1.0, 2.0)
            root = position + Vector((math.cos(angle) * reach, math.sin(angle) * reach, climb - 0.08))
            middle = root + Vector((math.cos(angle) * 0.1, math.sin(angle) * 0.1, length * 0.5))
            tip = position + Vector((0.0, 0.0, climb + length)) + FLAME_WIND * length * randomizer.uniform(0.1, 0.4) + scatter(randomizer, 0.12)
            tongues.append({"curve": (root, middle, tip), "bones": [bone], "width": randomizer.uniform(0.4, 0.62)})

    return tongues


def add_tongue(flames, layers: dict, groups: dict, tongue: dict, seed: float) -> list:
    """One ribbon along the quadratic curve of the tongue; returns the curve direction of each new vertex."""
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
        weights = {bones[lower]: 1.0} if len(bones) == 1 else {bones[lower]: 1.0 - (along_bones - lower), bones[lower + 1]: along_bones - lower}
        row = [flames.verts.new(point - sliver), flames.verts.new(point + sliver)]

        for corner in row:
            for bone, weight in weights.items():
                corner[layers["deform"]][groups[bone]] = weight

        rows.append((row, share))
        directions += [direction, direction]

    for (lower_row, lower_share), (upper_row, upper_share) in zip(rows, rows[1:]):
        face = flames.faces.new((lower_row[0], lower_row[1], upper_row[1], upper_row[0]))
        face.smooth = True

        for loop, (across, along) in zip(face.loops, ((0.0, lower_share), (1.0, lower_share), (1.0, upper_share), (0.0, upper_share))):
            loop[layers["uv"]].uv = (across, 1.0 - along)  # o glTF inverte o V: o jogo lê `along` e a largura
            loop[layers["seed"]].uv = (seed, 1.0 - tongue["width"])

    return directions


def build_flames(mesh_object, armature, stump, crest: list):
    """Object MulaFlames: every tongue of the stump blaze, mane, tail and hooves as a ribbon skinned to its bone."""
    randomizer = random.Random(FLAME_SEED)
    tongues = stump_tongues(randomizer, stump) + mane_tongues(randomizer, crest) + tail_tongues(randomizer) + hoof_tongues(randomizer, mesh_object)

    for bone in TAIL_BONES:  # o cavalo do pacote não pinta todos os ossos do rabo
        if bone not in mesh_object.vertex_groups:
            mesh_object.vertex_groups.new(name=bone)

    groups = {group.name: group.index for group in mesh_object.vertex_groups}
    flames = bmesh.new()
    layers = {"deform": flames.verts.layers.deform.verify(), "uv": flames.loops.layers.uv.new("UVMap"), "seed": flames.loops.layers.uv.new("Seed")}
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
            add_link(chain, deform_layer, group_indices[bone], link_matrix(lifted, tangent, outward, lies_flat), -outward, randomizer.random() < HOT_LINK_SHARE)

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
    hot_shader.inputs["Emission Color"].default_value = (1.0, 0.16, 0.02, 1.0)
    hot_shader.inputs["Emission Strength"].default_value = 1.1

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


def noise(nodes, links, coordinates, scale: float, detail: float, stretch=(1.0, 1.0, 1.0), tilt: float = 0.0):
    """Noise over the coordinates turned `tilt` radians around X and then stretched."""
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
    vein_glow, ember, hoof, leg = channels.outputs[0], channels.outputs[1], channels.outputs[2], mask.outputs["Alpha"]

    neck_mask = nodes.new("ShaderNodeAttribute")
    neck_mask.attribute_name = "neck"
    neck_channels = nodes.new("ShaderNodeSeparateColor")
    links.new(neck_mask.outputs["Color"], neck_channels.inputs[0])

    grain = noise(nodes, links, coordinates, 2.2, 1.0)
    blotch = noise(nodes, links, coordinates, 1.4, 2.0)
    # fibras de músculo: ruído esticado ao longo do corpo, das patas e do pescoço, dobrado em cristas finas
    body_fibres = noise(nodes, links, coordinates, 1.0, 4.0, (FIBRE_DENSITY, 0.9, FIBRE_DENSITY))
    leg_fibres = noise(nodes, links, coordinates, 1.0, 4.0, (FIBRE_DENSITY, FIBRE_DENSITY, 0.9))
    neck_fibres = noise(nodes, links, coordinates, 1.0, 4.0, (FIBRE_DENSITY, FIBRE_DENSITY, 0.9), NECK_FIBRE_TILT)
    fibres = mix(nodes, links, neck_channels.outputs[0], mix(nodes, links, leg, body_fibres, leg_fibres), neck_fibres)
    ridges = math_node(nodes, links, "MULTIPLY", math_node(nodes, links, "ABSOLUTE", math_node(nodes, links, "SUBTRACT", fibres, 0.5), 0.0), 4.0, clamp=True)
    bulges = math_node(nodes, links, "SUBTRACT", 1.0, voronoi(nodes, links, coordinates, 1.1, "SMOOTH_F1"), clamp=True)
    crackle = math_node(nodes, links, "MULTIPLY", voronoi(nodes, links, coordinates, 11.0, "DISTANCE_TO_EDGE"), 14.0, clamp=True)

    height = math_node(nodes, links, "MULTIPLY", bulges, 0.3)
    height = math_node(nodes, links, "ADD", height, math_node(nodes, links, "MULTIPLY", ridges, 0.07))
    height = math_node(nodes, links, "ADD", height, math_node(nodes, links, "MULTIPLY", crackle, 0.0))
    height = math_node(nodes, links, "ADD", height, math_node(nodes, links, "MULTIPLY", grain, 0.0))

    bump = nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 1.0
    bump.inputs["Distance"].default_value = 0.3
    links.new(height, bump.inputs["Height"])
    diffuse = nodes.new("ShaderNodeBsdfDiffuse")
    links.new(bump.outputs[0], diffuse.inputs["Normal"])

    # couro cor de vinho queimado: fundo do sulco quase preto, crista da fibra em carne escura
    tone = math_node(nodes, links, "ADD", math_node(nodes, links, "MULTIPLY", grain, 0.35), math_node(nodes, links, "MULTIPLY", ridges, 0.65))
    hide = color_ramp(nodes, links, tone, [(0.15, (0.012, 0.006, 0.006)), (0.45, (0.05, 0.018, 0.016)), (0.8, (0.13, 0.04, 0.032))])
    hide = mix(nodes, links, math_node(nodes, links, "MULTIPLY", blotch, 0.3), hide, (0.03, 0.014, 0.014))
    hide = mix(nodes, links, math_node(nodes, links, "MULTIPLY", math_node(nodes, links, "SUBTRACT", 1.0, crackle), 0.0), hide, (0.01, 0.006, 0.006))
    hide = mix(nodes, links, math_node(nodes, links, "MULTIPLY", vein_glow, 0.2), hide, (0.32, 0.02, 0.008))
    is_ember = math_node(nodes, links, "GREATER_THAN", ember, 0.05)
    hide = mix(nodes, links, is_ember, hide, (0.05, 0.012, 0.006))

    # carne úmida: brilha mais na crista da fibra, fosca no sulco carbonizado
    roughness_value = math_node(nodes, links, "MULTIPLY_ADD", ridges, -0.2, clamp=True)
    roughness_value.node.inputs[2].default_value = 0.42
    combine = nodes.new("ShaderNodeCombineColor")
    links.new(roughness_value, combine.inputs[1])

    hide_glow = math_node(nodes, links, "MULTIPLY", vein_glow, HIDE_HALO)  # só as veias brilham: o couro guarda um halo fraco
    ember_cracks = math_node(nodes, links, "SUBTRACT", 1.0, math_node(nodes, links, "MULTIPLY", voronoi(nodes, links, coordinates, 6.0, "DISTANCE_TO_EDGE"), 7.0, clamp=True))
    ember_glow = math_node(nodes, links, "ADD", math_node(nodes, links, "MULTIPLY", ember, 0.45), math_node(nodes, links, "MULTIPLY", ember_cracks, 0.55), clamp=True)
    hoof_cracks = math_node(nodes, links, "MULTIPLY", voronoi(nodes, links, coordinates, 5.0, "DISTANCE_TO_EDGE"), 9.0, clamp=True)
    # casco de lava: todo derretido e claro, com placas de crosta um pouco mais escuras entre as fendas
    hoof_glow = math_node(nodes, links, "MULTIPLY", hoof, math_node(nodes, links, "MULTIPLY_ADD", math_node(nodes, links, "SUBTRACT", 1.0, hoof_cracks), 0.12))
    hoof_glow.node.inputs[2].default_value = 0.88
    hide_glow = math_node(nodes, links, "MAXIMUM", hide_glow, hoof_glow)
    glow = color_ramp(nodes, links, mix(nodes, links, is_ember, hide_glow, ember_glow),
                      [(0.0, (0.0, 0.0, 0.0)), (0.45, (0.1, 0.003, 0.0)), (0.8, (0.5, 0.05, 0.004)), (1.0, (1.0, 0.4, 0.07))])

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


def stretched(position: Vector) -> Vector:
    """Where a point of the pack-proportioned mula lands once it is stretched: the legs lengthen between fetlock and
    shoulder/hip joint (hooves stay, everything above rides up) and the trunk lengthens between the leg pairs."""
    trunk = min(TRUNK_STRETCH_REACH, max(-TRUNK_STRETCH_REACH, position.y))
    leg = min(LEG_STRETCH_TOP, max(LEG_STRETCH_FLOOR, position.z))

    return Vector((position.x, position.y + trunk * (TRUNK_STRETCH - 1.0), position.z + (leg - LEG_STRETCH_FLOOR) * (LEG_STRETCH - 1.0)))


def stretch_proportions(armature, mesh_objects: list, marker_names: list) -> None:
    """The pack horse is short in the leg and in the back; the mula stands tall. Stretch skin, bones and fire
    markers. The leg bones keep their animated rotations, so the longer legs reach further than the pack's foot
    bones were keyed for: each foot bone now follows the tip of its leg."""
    markers = {name: bpy.data.objects[name].matrix_world.translation.copy() for name in marker_names}

    for mesh_object in mesh_objects:
        for vertex in mesh_object.data.vertices:
            vertex.co = stretched(vertex.co)

    bpy.ops.object.select_all(action="DESELECT")
    bpy.context.view_layer.objects.active = armature
    armature.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")

    for bone in armature.data.edit_bones:
        bone.head = stretched(bone.head)
        bone.tail = stretched(bone.tail)

    bpy.ops.object.mode_set(mode="OBJECT")

    for foot, leg_tip in FOOT_FOLLOWS.items():
        follow = armature.pose.bones[foot].constraints.new("COPY_LOCATION")
        follow.target = armature
        follow.subtarget = leg_tip

    bpy.context.view_layer.update()

    for name, position in markers.items():
        bpy.data.objects[name].matrix_world = armature.matrix_world @ Matrix.Translation(stretched(position))


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


def stamp_buffer_hash(gltf_path: Path) -> None:
    """Godot only reimports when the .gltf text changes, and a rebuild often changes nothing but the .bin (same
    counts, other positions): write the hash of the buffer into the .gltf so every rebuild is seen."""
    document = json.loads(gltf_path.read_text(encoding="utf-8"))
    buffer_hash = hashlib.md5(gltf_path.with_suffix(".bin").read_bytes()).hexdigest()

    document["asset"]["extras"] = {"buffer_md5": buffer_hash}
    gltf_path.write_text(json.dumps(document, indent="\t"), encoding="utf-8", newline="\n")


def build(source: Path) -> dict:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    import_source(source)
    make_materials_opaque()

    pack_horse = next(scene_object for scene_object in bpy.context.scene.objects if scene_object.type == "MESH")
    armature = next(scene_object for scene_object in bpy.context.scene.objects if scene_object.type == "ARMATURE")
    stump = mula_body.Stump()

    strip_hair(pack_horse)
    mesh_object = mula_body.sculpt_clay()
    rim, ember_heat = mula_body.cut_stump(mesh_object, stump)
    mula_body.transfer_weights(mesh_object, pack_horse)
    bpy.data.objects.remove(pack_horse)
    mesh_object.parent = armature
    mesh_object.modifiers.new("Armature", "ARMATURE").object = armature

    tree = grow_vein_tree(mesh_object.data, rim, set(ember_heat))
    veins = build_veins(mesh_object, armature, tree)
    chains, chain_bones = build_chains(mesh_object, armature)
    paint_bake_mask(mesh_object, tree, ember_heat)
    crest = crest_points(BVHTree.FromObject(mesh_object, bpy.context.evaluated_depsgraph_get()), stump)
    fire_markers = add_fire_markers(mesh_object, armature, stump, crest)
    flames = build_flames(mesh_object, armature, stump, crest)
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
    mesh_object.data.color_attributes.remove(mesh_object.data.color_attributes["neck"])
    mesh_object.name = "Mula"

    actions = rename_actions()
    stretch_proportions(armature, [mesh_object, veins, chains, flames], fire_markers)
    factor = scale_to_withers(mesh_object)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.export_scene.gltf(filepath=str(OUTPUT), export_format="GLTF_SEPARATE", export_texture_dir="textures", export_yup=True,
                              export_animation_mode="ACTIONS", export_force_sampling=True, export_vertex_color="NONE")
    stamp_buffer_hash(OUTPUT)

    sidecar = {"source": source.name, "withers_height": WITHERS_HEIGHT, "scale": round(factor, 5), "animations": actions,
               "fire_markers": fire_markers, "hanging_chains": chain_bones,
               "vertices": {scene_object.name: len(scene_object.data.vertices) for scene_object in (mesh_object, veins, chains, flames)}}
    OUTPUT.with_suffix(".json").write_text(json.dumps(sidecar, indent=1), encoding="utf-8", newline="\n")

    return sidecar


if __name__ == "__main__":
    arguments = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    source_path = Path(arguments[arguments.index("--source") + 1]) if "--source" in arguments else SOURCE

    print(f"BUILT mula_sem_cabeca: {build(source_path)}")
