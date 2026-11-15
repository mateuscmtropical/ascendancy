"""Write features/hub/hub.tscn: the starting city, laid out after downtown Campo Mourão (PR).

Two squares side by side, separated by Rua Brasil (a market street here):
  - Praça Getúlio Vargas (west): union-jack paths, tiered chafariz in the middle, octagonal coreto.
  - Praça São José (east): the cathedral in the middle, facade toward Rua Brasil, dense shade trees.
Main avenue (Av. Capitão Índio Bandeira) with a tree-lined median and a roundabout runs along the north
side; Av. Irmãos Pereira along the south. A ring of ten half-blocks of row houses closes the city,
inside a town wall. Real grid scaled ~0.6 and built axis-aligned (Fable advisor): X runs along the
avenues (real NE), Z across them (real SE). Map data: OpenStreetMap contributors (ODbL).

Godot coordinates, Y up. Every model's front faces +Z locally, so rotation_y turns it toward the street.

Usage: python tools_src/build_hub_scene.py
"""

import math
import random
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
OUTPUT_PATH = PROJECT_DIR / "features" / "hub" / "hub.tscn"
NAVMESH_PATH = PROJECT_DIR / "features" / "hub" / "hub_navmesh.tres"
NAVIGATION_SOURCE_GROUP = "navigation_source"  # nós cujas malhas/colisões entram na navmesh (bake_hub_navmesh.gd)

CITY_MIN = (-102.0, -96.0)
CITY_MAX = (102.0, 88.0)
SIDEWALK = 3.0
HOUSE_ROW_DEPTH = 10.0
SQUARE_HALF = (30.0, 48.0)
GETULIO_VARGAS = (-34.0, 0.0)
SAO_JOSE = (34.0, 0.0)
AVENUE_Z = (-66.0, -48.0)
MEDIAN_Z = (-60.0, -54.0)
ROUNDABOUT = (0.0, -57.0)
CATHEDRAL_FACADE_X = 13.0  # catedral de 26 x 47,6 m (build_cathedral.py): fundo da abside em x = 60,6
CATHEDRAL_FLOOR = 1.05
CHANCEL_FLOOR = CATHEDRAL_FLOOR + 0.9
CATHEDRAL_CRUCIFIX = (CATHEDRAL_FACADE_X + 45.4, CHANCEL_FLOOR + 5.6, 0.0)  # peito do Cristo no retábulo
ADRO_WIDTH = 30.0  # cobre as estátuas da escadaria (z = ±12,2)
COREO_POSITION = (-46.0, -13.0)  # no gramado a noroeste do chafariz, como na foto aérea
COREO_APRON_RADIUS = 4.6
COREO_ACCESS_END = (-38.2, -13.0)  # o caminho do coreto encosta na diagonal do largo noroeste
COREO_ACCESS_WIDTH = 3.4  # cabe a escada com as muretas
PLAYER_SPAWN = (-38.4, -13.0)  # pé da escada do coreto, olhando para a catedral (+X)
PATH_WIDTH = 4.0
PLANTER_SOIL_HEIGHT = 0.42
GRASS_SEED = 77
GRASS_TUFTS_PER_SQUARE = 110

ESPLANADE_WIDTH = 8.0  # eixo oeste-leste que cruza a Getúlio Vargas e aponta para a fachada
PLAZA_RADIUS = 10.0
WEST_NODES = [(-43.0, -28.0), (-43.0, 28.0)]  # largos maiores a oeste, três ramos cada
EAST_RONDELS = [(-24.0, -16.0), (-24.0, 16.0)]  # rondéis do lado da catedral
NODE_RADIUS = 5.0
RONDEL_RADIUS = 4.0
MARCO = (0.0, 0.0)  # obelisco no calçadão, no eixo entre o chafariz e a catedral
MARCO_LAWN_RADII = (1.2, 2.6)
STREET_DROP = 0.12  # asfalto fica abaixo das calçadas (meio-fio)
CURB_WIDTH = 0.22  # meio-fio de pedra dos canteiros
CURB_HEIGHT = 0.16
LAWN_EDGE_HEIGHT = 0.12  # a grama começa abaixo do topo do meio-fio e sobe para o meio do canteiro
LAWN_SWELL_HEIGHT = 0.26
LAWN_SWELL_DISTANCE = 4.5
ROUNDABOUT_ISLAND_RADIUS = 5.0  # ilha elevada com a fonte pequena
ROUNDABOUT_OUTER_RADIUS = 10.5  # borda externa da pista em anel; as calçadas são recortadas em arco
ROUNDABOUT_LAWN_RADII = (2.4, 4.6)
MEDIAN_NOSE_X = 14.5  # o canteiro central termina com nariz redondo antes da rotatória
MEDIAN_HALF_WIDTH = (MEDIAN_Z[1] - MEDIAN_Z[0]) / 2.0
MEDIAN_BEDS = [((CITY_MIN[0] + 4.0, MEDIAN_Z[0] + 0.7), (-MEDIAN_NOSE_X - 1.0, MEDIAN_Z[1] - 2.3)), ((MEDIAN_NOSE_X + 1.0, MEDIAN_Z[0] + 0.7), (CITY_MAX[0] - 4.0, MEDIAN_Z[1] - 2.3))]
LAWN_RECTS = {  # canteiros = retângulo menos os caminhos de SQUARE_PATHS
    "GetulioVargas": ((GETULIO_VARGAS[0] - SQUARE_HALF[0] + PATH_WIDTH, -SQUARE_HALF[1] + PATH_WIDTH), (GETULIO_VARGAS[0] + SQUARE_HALF[0] - PATH_WIDTH, SQUARE_HALF[1] - PATH_WIDTH)),
    "SaoJose": ((SAO_JOSE[0] - SQUARE_HALF[0] + PATH_WIDTH, -SQUARE_HALF[1] + PATH_WIDTH), (SAO_JOSE[0] + SQUARE_HALF[0] - PATH_WIDTH, SQUARE_HALF[1] - PATH_WIDTH)),
}


def getulio_vargas_branches(sign: float) -> list:
    """Diagonals of one half of Getúlio Vargas (sign -1 = north, +1 = south): chafariz to the secondary plazas and their branches."""
    node = (WEST_NODES[0][0], sign * abs(WEST_NODES[0][1]))
    rondel = (EAST_RONDELS[0][0], sign * abs(EAST_RONDELS[0][1]))

    return [
        ("strip", GETULIO_VARGAS, node, 3.5),
        ("strip", node, (-60.0, sign * 44.0), 3.5),  # largo -> canto da praça
        ("strip", node, (-60.0, sign * 21.0), 3.0),  # largo -> borda oeste
        ("strip", node, (-23.0, sign * 39.5), 3.0),  # largo -> ramo norte/sul
        ("strip", GETULIO_VARGAS, rondel, 3.5),
        ("strip", rondel, (-23.0, sign * 44.0), 3.0),  # rondel -> borda norte/sul
        ("strip", rondel, (-8.0, sign * 27.0), 3.0),  # rondel -> borda leste
    ]


def sao_jose_walks(sign: float) -> list:
    """Walks of one half of São José: the cross walk, the one along Rua Brasil and the one along the back street."""
    half_x, half_z = SQUARE_HALF
    west, east = SAO_JOSE[0] - half_x, SAO_JOSE[0] + half_x

    return [
        ("strip", (west, sign * 30.0), (east, sign * 30.0), 3.0),
        ("strip", (west + 4.0, sign * 11.0), (west + 4.0, sign * half_z), 3.0),
        ("strip", (east - 3.0, sign * 16.0), (east - 3.0, sign * half_z), 3.0),
    ]


def square_paths() -> list:
    """Paved shapes cut out of the lawns, Godot (x, z): ("disc", center, radius) or ("strip", start, end, width)."""
    half_x = SQUARE_HALF[0]
    sao_jose_west, sao_jose_east = SAO_JOSE[0] - half_x, SAO_JOSE[0] + half_x
    plazas = [
        ("disc", GETULIO_VARGAS, PLAZA_RADIUS),
        ("strip", (GETULIO_VARGAS[0] - half_x, 0.0), (GETULIO_VARGAS[0] + half_x, 0.0), ESPLANADE_WIDTH),
        ("disc", COREO_POSITION, COREO_APRON_RADIUS),
        ("strip", COREO_POSITION, COREO_ACCESS_END, COREO_ACCESS_WIDTH),
        *[("disc", node, NODE_RADIUS) for node in WEST_NODES],
        *[("disc", rondel, RONDEL_RADIUS) for rondel in EAST_RONDELS],
        ("strip", (sao_jose_west, 0.0), (CATHEDRAL_FACADE_X, 0.0), ADRO_WIDTH),  # adro
        ("strip", (CATHEDRAL_FACADE_X, 0.0), (sao_jose_east, 0.0), 32.0),  # passeio em volta da catedral
    ]
    branches = [path for sign in (-1.0, 1.0) for path in getulio_vargas_branches(sign) + sao_jose_walks(sign)]

    return plazas + branches


def path_distance(point: tuple, path: tuple) -> float:
    """Signed distance from a point to one paved shape (negative = on the paving)."""
    kind, first, *rest = path

    if kind == "strip":
        end, width = rest
        length = math.hypot(end[0] - first[0], end[1] - first[1])
        along = ((point[0] - first[0]) * (end[0] - first[0]) + (point[1] - first[1]) * (end[1] - first[1])) / length
        across = abs((point[0] - first[0]) * (end[1] - first[1]) - (point[1] - first[1]) * (end[0] - first[0])) / length

        return max(across - width / 2.0, -along, along - length)

    radial = math.hypot(point[0] - first[0], point[1] - first[1])

    return radial - rest[0]


SQUARE_PATHS = square_paths()


def inside_distance(point: tuple, minimum: tuple, maximum: tuple) -> float:
    """Distance from a point to the nearest edge of a rectangle (negative outside)."""
    return min(point[0] - minimum[0], maximum[0] - point[0], point[1] - minimum[1], maximum[1] - point[1])


def square_edge_distance(point: tuple) -> float:
    """How far inside the lawn rectangle of a square the point is (negative outside both)."""
    return max(inside_distance(point, minimum, maximum) for minimum, maximum in LAWN_RECTS.values())


def ring_bed_distance(point: tuple, center: tuple, radii: tuple) -> float:
    """Signed distance into a round bed between two radii (positive = on the bed)."""
    radial = math.hypot(point[0] - center[0], point[1] - center[1])

    return min(radii[1] - radial, radial - radii[0])


def bed_field(point: tuple) -> float:
    """Signed distance into the nearest planted bed (positive = on a bed, value = distance to its curb)."""
    square_bed = min(square_edge_distance(point), min(path_distance(point, path) for path in SQUARE_PATHS))
    roundabout_bed = ring_bed_distance(point, ROUNDABOUT, ROUNDABOUT_LAWN_RADII)
    marco_bed = ring_bed_distance(point, MARCO, MARCO_LAWN_RADII)
    median_bed = max(inside_distance(point, minimum, maximum) for minimum, maximum in MEDIAN_BEDS)

    return max(square_bed, roundabout_bed, marco_bed, median_bed)


def bed_height(field: float) -> float:
    """Ground height on a bed: stone curb at the edge, then a lawn that swells gently toward the middle."""
    if field <= 0.0:
        return 0.0

    if field < CURB_WIDTH:
        return CURB_HEIGHT

    swell = min(1.0, (field - CURB_WIDTH) / LAWN_SWELL_DISTANCE)

    return LAWN_EDGE_HEIGHT + LAWN_SWELL_HEIGHT * swell * swell * (3.0 - 2.0 * swell)


def ground_height(point: tuple) -> float:
    """Height of the walkable ground at a point of the squares, blocks or median (streets are STREET_DROP lower)."""
    return bed_height(bed_field(point))


def on_lawn(point: tuple, margin: float = 0.0) -> bool:
    """True when the point is on a planted bed, at least margin away from its curb."""
    return bed_field(point) > margin


TRUNK_RADIUS = {"tree_old": 0.85, "tree_bloom": 0.3, "palm": 0.36, "bush": 0.5, "flowers": 0.0}
PLANT_CLEARANCE = 1.2  # do meio-fio do canteiro até a casca: tronco fica por dentro da sebe
ROOT_CLEARANCE = {"tree_old": 3.0}  # raízes tabulares medidas em old_tree_*.gltf chegam a 3,0 m do eixo
PAVED_CLEARANCE = 0.4  # postes e bancos ficam no piso, longe da grama


def can_plant(point: tuple, kind: str) -> bool:
    """Single planting rule for trees, palms, bushes and flowers: the trunk stays inside a bed, clear of curb and hedge."""
    return bed_field(point) >= ROOT_CLEARANCE.get(kind, PLANT_CLEARANCE + TRUNK_RADIUS[kind])


def is_paved(point: tuple) -> bool:
    return bed_field(point) <= -PAVED_CLEARANCE


HEDGE_BAND = (0.30, 0.85)  # sebe baixa entre estas distâncias da borda do canteiro
HEDGE_GAP_SEED = 53
HEDGE_GAP_SPACING = 22.0
HEDGE_GAP_HALF_WIDTH = 0.8
HEDGE_GAP_STRAIGHT_REACH = 4.0  # vão só em trecho reto: a borda não vira mais de 40° nesta distância


def bed_domains() -> list:
    """Godot (x, z) rectangles that contain every planted bed."""
    roundabout_reach = ROUNDABOUT_LAWN_RADII[1] + 1.0
    marco_reach = MARCO_LAWN_RADII[1] + 1.0
    roundabout = ((ROUNDABOUT[0] - roundabout_reach, ROUNDABOUT[1] - roundabout_reach), (ROUNDABOUT[0] + roundabout_reach, ROUNDABOUT[1] + roundabout_reach))
    marco = ((MARCO[0] - marco_reach, MARCO[1] - marco_reach), (MARCO[0] + marco_reach, MARCO[1] + marco_reach))
    padded_medians = [((minimum[0] - 1.0, minimum[1] - 1.0), (maximum[0] + 1.0, maximum[1] + 1.0)) for minimum, maximum in MEDIAN_BEDS]

    return list(LAWN_RECTS.values()) + [roundabout, marco] + padded_medians


def bed_gradient(point: tuple) -> tuple:
    """Unit direction in which bed_field grows (into the bed)."""
    step = 0.05
    gradient_x = bed_field((point[0] + step, point[1])) - bed_field((point[0] - step, point[1]))
    gradient_z = bed_field((point[0], point[1] + step)) - bed_field((point[0], point[1] - step))
    length = math.hypot(gradient_x, gradient_z) or 1.0

    return gradient_x / length, gradient_z / length


def hedge_tangent(point: tuple) -> tuple:
    gradient = bed_gradient(point)

    return -gradient[1], gradient[0]


def is_straight_hedge(point: tuple) -> bool:
    """True when the bed edge runs straight for HEDGE_GAP_STRAIGHT_REACH on both sides of the point."""
    gradient = bed_gradient(point)
    tangent = hedge_tangent(point)
    reach = HEDGE_GAP_STRAIGHT_REACH
    neighbours = [(point[0] + side * reach * tangent[0], point[1] + side * reach * tangent[1]) for side in (-1.0, 1.0)]
    alignments = [bed_gradient(neighbour)[0] * gradient[0] + bed_gradient(neighbour)[1] * gradient[1] for neighbour in neighbours]
    hedge_middle = sum(HEDGE_BAND) / 2.0

    return all(alignment > math.cos(math.radians(40.0)) for alignment in alignments) and all(abs(bed_field(neighbour) - hedge_middle) < 0.3 for neighbour in neighbours)


def hedge_gaps() -> list:
    """Openings in the hedges to step onto the lawns: seeded greedy pick on straight edges, HEDGE_GAP_SPACING apart."""
    hedge_middle = sum(HEDGE_BAND) / 2.0
    grid = [(minimum[0] + column, minimum[1] + row) for minimum, maximum in bed_domains() for column in range(int(maximum[0] - minimum[0]) + 1) for row in range(int(maximum[1] - minimum[1]) + 1)]
    candidates = [point for point in grid if abs(bed_field(point) - hedge_middle) < 0.5]
    centred = [(point[0] + (hedge_middle - bed_field(point)) * bed_gradient(point)[0], point[1] + (hedge_middle - bed_field(point)) * bed_gradient(point)[1]) for point in candidates]
    straight = [point for point in centred if is_straight_hedge(point)]
    gaps = []

    random.Random(HEDGE_GAP_SEED).shuffle(straight)

    for point in straight:
        if all(math.hypot(point[0] - gap[0], point[1] - gap[1]) >= HEDGE_GAP_SPACING for gap in gaps):
            gaps.append(point)

    return gaps


HOUSE_SIZES = {  # name -> (width along facade, depth)
    "house_stone_tall": (6, 8),
    "house_narrow_three": (6, 8),
    "house_plaster_wide": (8, 8),
    "house_shop": (8, 10),
    "house_cottage": (6, 6),
}
SHOP_HOUSES = {  # casa da fileira -> variantes de loja com a mesma planta (build_shop_houses.py)
    "house_stone_tall": [f"shops/house_shop_narrow_{index}" for index in range(1, 9)],
    "house_narrow_three": [f"shops/house_shop_narrow_{index}" for index in range(1, 9)],
}
HOUSES_BY_WIDTH = {6: ["house_stone_tall", "house_narrow_three", "house_cottage"], 8: ["house_plaster_wide", "house_shop"]}
SIDE_ROTATION = {"N": math.pi, "S": 0.0, "W": -math.pi / 2.0, "E": math.pi / 2.0}  # house front faces the street
BLOCKS = [  # (min x, max x, min z, max z, street sides by priority)
    (-102, -72, -96, -66, "SE"),
    (-64, -4, -96, -66, "SWE"),
    (4, 64, -96, -66, "SWE"),
    (72, 102, -96, -66, "SW"),
    (-102, -72, -48, 48, "ENS"),
    (72, 102, -48, 48, "WNS"),
    (-102, -72, 58, 88, "NE"),
    (-64, -4, 58, 88, "NWE"),
    (4, 64, 58, 88, "NWE"),
    (72, 102, 58, 88, "NW"),
]
SHOP_FRONTAGES = {(1, "S"), (2, "S"), (4, "E"), (5, "W"), (7, "N"), (8, "N")}  # (bloco, lado) virados para as praças e a avenida
SHOP_TYPES = ["smith", "armor", "magic", "alchemy", "tavern", "inn", "guild", "bakery", "tailor", "jeweler"]
SHOP_SEED = 2207
SHOP_WALL_GAP = 0.06
KIT_COLLIDERS = {  # kit model name prefix -> simple solid in model space: ("cylinder", radius, height) or ("box", size, center)
    "CommonTree": ("cylinder", 0.35, 3.0),
    "old_tree": ("cylinder", 0.85, 3.0),
    "tree_bloom": ("cylinder", 0.3, 3.0),
    "palm_": ("cylinder", 0.36, 3.0),
    "Bush_Common": ("cylinder", 0.8, 1.2),
    "Flower_3_Group": ("cylinder", 0.5, 1.6),
    "Flower_4_Group": ("cylinder", 0.5, 1.6),
    "Bench": ("box", (2.78, 0.54, 0.53), (0.0, 0.27, 0.0)),
    "Stall_Empty": ("box", (1.84, 2.62, 0.93), (0.0, 1.31, 0.0)),
    "Stall_Cart_Empty": ("box", (3.02, 2.63, 1.06), (-0.6, 1.31, 0.0)),
    "Barrel": ("cylinder", 0.35, 0.9),
    "Crate_Wooden": ("box", (0.86, 0.88, 0.9), (0.0, 0.41, 0.0)),
    "Table_Large": ("box", (2.84, 0.81, 1.09), (0.0, 0.4, 0.0)),
    "Stool": ("cylinder", 0.24, 0.58),
}
HAIR_COLORS = {
    "dark": (0.16, 0.12, 0.1),
    "brown": (0.32, 0.21, 0.14),
    "auburn": (0.55, 0.27, 0.15),
    "blond": (0.85, 0.7, 0.45),
    "grey": (0.62, 0.6, 0.58),
    "black": (0.08, 0.07, 0.07),
}


class SceneWriter:
    def __init__(self) -> None:
        self.external = {}
        self.sub_resources = []
        self.sub_resource_ids = set()
        self.nodes = []

    def external_id(self, resource_type: str, path: str) -> str:
        if path not in self.external:
            self.external[path] = (resource_type, f"{len(self.external) + 1}_ext")

        return self.external[path][1]

    def add_sub_resource(self, text: str) -> None:
        self.sub_resources.append(text.strip() + "\n")

    def add_sub_resource_once(self, resource_id: str, text: str) -> str:
        if resource_id not in self.sub_resource_ids:
            self.sub_resource_ids.add(resource_id)
            self.add_sub_resource(text)

        return resource_id

    def add_node(self, name: str, parent: str, node_type: str = "", instance: str = "", properties: dict = None, groups: list = None) -> None:
        header = f'[node name="{name}"'
        header += f' type="{node_type}"' if node_type else ""
        header += f' parent="{parent}"' if parent is not None else ""
        header += f' instance=ExtResource("{instance}")' if instance else ""
        header += " groups=[" + ", ".join(f'"{group}"' for group in groups) + "]" if groups else ""
        lines = [header + "]"] + [f"{key} = {value}" for key, value in (properties or {}).items()]
        self.nodes.append("\n".join(lines) + "\n")

    def render(self) -> str:
        load_steps = len(self.external) + len(self.sub_resources) + 1
        external_lines = [f'[ext_resource type="{resource_type}" path="{path}" id="{resource_id}"]' for path, (resource_type, resource_id) in self.external.items()]

        return "\n".join([f"[gd_scene load_steps={load_steps} format=3]", "", *external_lines, "", *self.sub_resources, *self.nodes])


def vector(x: float, y: float, z: float) -> str:
    return f"Vector3({x:.3f}, {y:.3f}, {z:.3f})"


def color(rgb: tuple) -> str:
    return f"Color({rgb[0]:.3f}, {rgb[1]:.3f}, {rgb[2]:.3f}, 1)"


def look_rotation(eye: tuple, target: tuple) -> str:
    delta_x, delta_y, delta_z = (target[index] - eye[index] for index in range(3))
    yaw = math.atan2(-delta_x, -delta_z)
    pitch = math.atan2(delta_y, math.hypot(delta_x, delta_z))

    return vector(pitch, yaw, 0.0)


def facing_yaw(origin: tuple, target: tuple) -> float:
    """Yaw that turns a model's +Z front from origin toward target (both (x, z))."""
    return math.atan2(target[0] - origin[0], target[1] - origin[1])


def place(scene: SceneWriter, name: str, parent: str, scene_path: str, position: tuple, rotation_y: float = 0.0, scale: float = 1.0) -> None:
    properties = {"position": vector(*position)}

    if rotation_y:
        properties["rotation"] = vector(0.0, rotation_y, 0.0)

    if scale != 1.0:
        properties["scale"] = vector(scale, scale, scale)

    scene.add_node(name, parent, instance=scene.external_id("PackedScene", scene_path), properties=properties)
    add_kit_collider(scene, f"{parent}/{name}", Path(scene_path).stem)


def add_kit_collider(scene: SceneWriter, node_path: str, model_name: str) -> None:
    """Kit models ship without collision: give the ones people would bump into a simple solid (also cut from the navmesh)."""
    prefix = next((prefix for prefix in KIT_COLLIDERS if model_name.startswith(prefix)), None)

    if prefix is None:
        return

    kind, *dimensions = KIT_COLLIDERS[prefix]
    shape_id = f"collider_{prefix}"

    if kind == "cylinder":
        radius, height = dimensions
        shape_text = f'[sub_resource type="CylinderShape3D" id="{shape_id}"]\nradius = {radius}\nheight = {height}'
        center = (0.0, height / 2.0, 0.0)
    else:
        size, center = dimensions
        shape_text = f'[sub_resource type="BoxShape3D" id="{shape_id}"]\nsize = {vector(*size)}'

    scene.add_sub_resource_once(shape_id, shape_text)

    scene.add_node("Collider", node_path, "StaticBody3D", groups=[NAVIGATION_SOURCE_GROUP])
    scene.add_node("Shape", f"{node_path}/Collider", "CollisionShape3D", properties={"position": vector(*center), "shape": f'SubResource("{shape_id}")'})


# ---------- ground ----------

def add_materials(scene: SceneWriter) -> None:
    rock = scene.external_id("Texture2D", "res://art/town/textures/T_RockTrim_BaseColor.png")
    lawn = scene.external_id("Texture2D", "res://art/town/textures/T_Lawn_BaseColor.png")

    scene.add_sub_resource(f'''
[sub_resource type="StandardMaterial3D" id="wall_material"]
albedo_color = Color(0.85, 0.82, 0.76, 1)
albedo_texture = ExtResource("{rock}")
uv1_scale = Vector3(0.25, 0.25, 0.25)
uv1_triplanar = true
uv1_world_triplanar = true''')
    scene.add_sub_resource(f'''
[sub_resource type="StandardMaterial3D" id="countryside_material"]
albedo_color = Color(0.9, 0.95, 0.85, 1)
albedo_texture = ExtResource("{lawn}")
roughness = 1.0
uv1_scale = Vector3(0.05, 0.05, 0.05)
uv1_triplanar = true
uv1_world_triplanar = true''')


def add_ground(scene: SceneWriter) -> None:
    """Streets, curbed pavements and raised beds come modelled from build_ground.py; here only the endless floor under them."""
    scene.add_sub_resource('''
[sub_resource type="WorldBoundaryShape3D" id="ground_shape"]''')
    scene.add_sub_resource('''
[sub_resource type="PlaneMesh" id="countryside_mesh"]
material = SubResource("countryside_material")
size = Vector2(500, 500)''')
    scene.add_node("Ground", ".", "StaticBody3D", groups=[NAVIGATION_SOURCE_GROUP])
    scene.add_node("Collision", "Ground", "CollisionShape3D", properties={"position": vector(0, -STREET_DROP, 0), "shape": 'SubResource("ground_shape")'})
    scene.add_node("Countryside", "Ground", "MeshInstance3D", properties={"position": vector(0, -STREET_DROP - 0.03, 0), "mesh": 'SubResource("countryside_mesh")'})
    place(scene, "City", "Ground", "res://art/town/ground.gltf", (0, 0, 0))


def grounded(x: float, z: float) -> tuple:
    """Position standing on the ground at (x, z): raised on the planted beds."""
    return x, ground_height((x, z)), z


def add_town_wall(scene: SceneWriter) -> None:
    """Stone wall around the city: closes the street ends and keeps the player inside."""
    thickness = 1.2
    height = 4.5
    walls = [
        ("North", ((CITY_MIN[0] + CITY_MAX[0]) / 2.0, CITY_MIN[1] - thickness / 2.0), (CITY_MAX[0] - CITY_MIN[0] + 2 * thickness, thickness)),
        ("South", ((CITY_MIN[0] + CITY_MAX[0]) / 2.0, CITY_MAX[1] + thickness / 2.0), (CITY_MAX[0] - CITY_MIN[0] + 2 * thickness, thickness)),
        ("West", (CITY_MIN[0] - thickness / 2.0, (CITY_MIN[1] + CITY_MAX[1]) / 2.0), (thickness, CITY_MAX[1] - CITY_MIN[1])),
        ("East", (CITY_MAX[0] + thickness / 2.0, (CITY_MIN[1] + CITY_MAX[1]) / 2.0), (thickness, CITY_MAX[1] - CITY_MIN[1])),
    ]

    scene.add_node("TownWall", ".", "StaticBody3D", groups=[NAVIGATION_SOURCE_GROUP])

    for wall_name, (x, z), (size_x, size_z) in walls:
        shape_id = f"town_wall_{wall_name.lower()}"
        scene.add_sub_resource(f'''
[sub_resource type="BoxShape3D" id="{shape_id}_shape"]
size = {vector(size_x, height, size_z)}''')
        scene.add_sub_resource(f'''
[sub_resource type="BoxMesh" id="{shape_id}_mesh"]
material = SubResource("wall_material")
size = {vector(size_x, height, size_z)}''')
        scene.add_node(f"{wall_name}Collision", "TownWall", "CollisionShape3D", properties={"position": vector(x, height / 2.0, z), "shape": f'SubResource("{shape_id}_shape")'})
        scene.add_node(f"{wall_name}Mesh", "TownWall", "MeshInstance3D", properties={"position": vector(x, height / 2.0, z), "mesh": f'SubResource("{shape_id}_mesh")'})


# ---------- buildings ----------

def side_frontage(block: tuple, side: str) -> tuple:
    """Facade line and run of a block side: (fixed coordinate, run start, run end, along axis)."""
    min_x, max_x, min_z, max_z = block[:4]
    frontages = {
        "N": (min_z + SIDEWALK, min_x + SIDEWALK, max_x - SIDEWALK, "x"),
        "S": (max_z - SIDEWALK, min_x + SIDEWALK, max_x - SIDEWALK, "x"),
        "W": (min_x + SIDEWALK, min_z + SIDEWALK, max_z - SIDEWALK, "z"),
        "E": (max_x - SIDEWALK, min_z + SIDEWALK, max_z - SIDEWALK, "z"),
    }

    return frontages[side]


def trimmed_run(block: tuple, side: str, earlier_sides: str) -> tuple:
    """Shorten a side's run where an earlier perpendicular row already fills the corner."""
    facade, run_start, run_end, axis = side_frontage(block, side)
    start_corner = {"x": "W", "z": "N"}[axis]
    end_corner = {"x": "E", "z": "S"}[axis]

    run_start += HOUSE_ROW_DEPTH if start_corner in earlier_sides else 0.0
    run_end -= HOUSE_ROW_DEPTH if end_corner in earlier_sides else 0.0

    return facade, run_start, run_end, axis


def house_widths_for(length: float) -> list:
    """Mix of 8 m and 6 m houses that fills length with the least slack (slack becomes small gaps)."""
    candidates = [(length - 8 * wide_count - 6 * int((length - 8 * wide_count) // 6), wide_count) for wide_count in range(int(length // 8) + 1)]
    slack, wide_count = min(candidates)
    narrow_count = int((length - 8 * wide_count) // 6)
    widths = [8] * wide_count + [6] * narrow_count

    return widths


def pick_house_types(widths: list, generator: random.Random, allow_cottage: bool) -> list:
    """One house type per width, never the same type twice in a row."""
    chosen = []

    for width in widths:
        options = [name for name in HOUSES_BY_WIDTH[width] if name != (chosen[-1] if chosen else "") and (allow_cottage or name != "house_cottage")]
        chosen.append(generator.choice(options))

    return chosen


def house_row(block: tuple, side: str, earlier_sides: str, generator: random.Random) -> list:
    """Row houses along one block side; returns (model, position, rotation)."""
    facade, run_start, run_end, axis = trimmed_run(block, side, earlier_sides)
    length = run_end - run_start
    widths = house_widths_for(length)
    generator.shuffle(widths)
    is_main_front = earlier_sides == ""
    names = pick_house_types(widths, generator, allow_cottage=not is_main_front)
    gap = (length - sum(widths)) / max(1, len(widths))
    inward = {"N": 1.0, "S": -1.0, "W": 1.0, "E": -1.0}[side]
    placements = []
    cursor = run_start + gap / 2.0

    for house_name, width in zip(names, widths):
        depth = HOUSE_SIZES[house_name][1]
        along = cursor + width / 2.0
        across = facade + inward * depth / 2.0
        position = (along, 0.0, across) if axis == "x" else (across, 0.0, along)
        placements.append((house_name, position, SIDE_ROTATION[side], side))
        cursor += width + gap

    return placements


def shop_houses_for(shop_fronts: list) -> dict:
    """Position -> shop house variant that replaces the row house there; neighbours never get the same variant."""
    generator = random.Random(SHOP_SEED)
    chosen = {}
    previous = ""

    for house_name, position, _rotation_y, _side in shop_fronts:
        previous = generator.choice([variant for variant in SHOP_HOUSES.get(house_name, [house_name]) if variant != previous])
        chosen[position] = previous

    return chosen


def add_buildings(scene: SceneWriter) -> None:
    generator = random.Random(1942)
    placements = []
    shop_fronts = []

    for block_index, block in enumerate(BLOCKS):
        street_sides = block[4]

        for side_index, side in enumerate(street_sides):
            row = house_row(block, side, street_sides[:side_index], generator)
            placements += row
            shop_fronts += row if (block_index, side) in SHOP_FRONTAGES else []

    scene.add_node("Buildings", ".", "Node3D", groups=[NAVIGATION_SOURCE_GROUP])
    place(scene, "Cathedral", "Buildings", "res://art/town/cathedral.gltf", (CATHEDRAL_FACADE_X, 0, SAO_JOSE[1]), -math.pi / 2.0)
    place(scene, "Coreto", "Buildings", "res://art/town/coreto.gltf", (COREO_POSITION[0], 0, COREO_POSITION[1]), math.pi / 2.0)

    shop_houses = shop_houses_for(shop_fronts)

    for index, (house_name, position, rotation_y, _side) in enumerate(placements):
        place(scene, f"House{index:03d}", "Buildings", f"res://art/town/{shop_houses.get(position, house_name)}.gltf", position, rotation_y)

    add_shops(scene, shop_fronts)


def shop_types_for(count: int) -> list:
    """One trade per shop front: every trade appears before any repeats, and neighbours never match."""
    generator = random.Random(SHOP_SEED)
    chosen = []

    while len(chosen) < count:
        round_of_types = [shop_type for shop_type in SHOP_TYPES]
        generator.shuffle(round_of_types)

        if chosen and round_of_types[0] == chosen[-1]:
            round_of_types.append(round_of_types.pop(0))

        chosen += round_of_types

    return chosen[:count]


def add_shops(scene: SceneWriter, shop_fronts: list) -> None:
    """Dress the houses that face the squares and the avenue as RPG shops: hanging sign at the corner,
    awning stall under the first window and the trade's big props under the last one (build_shops.py)."""
    shop_types = shop_types_for(len(shop_fronts))

    scene.add_node("Shops", ".", "Node3D", groups=[NAVIGATION_SOURCE_GROUP])

    for index, ((house_name, position, rotation_y, _side), shop_type) in enumerate(zip(shop_fronts, shop_types)):
        width, depth = HOUSE_SIZES[house_name]
        facade_offset = depth / 2.0 + SHOP_WALL_GAP
        facade = (position[0] + facade_offset * math.sin(rotation_y), 0.0, position[2] + facade_offset * math.cos(rotation_y))
        shop_name = f"Shop{index:02d}{shop_type.title()}"
        pieces = {"stall": -(width / 2.0 - 1.1), "yard": width / 2.0 - 1.2, "sign": width / 2.0 - 0.15}

        scene.add_node(shop_name, "Shops", "Node3D", properties={"position": vector(*facade), "rotation": vector(0.0, rotation_y, 0.0)}, groups=[f"shop_{shop_type}"])

        for piece, offset_x in pieces.items():
            place(scene, piece.title(), f"Shops/{shop_name}", f"res://art/town/shops/shop_{shop_type}_{piece}.gltf", (offset_x, 0, 0))


CATHEDRAL_GLASS_SPOTS = [  # (nome, posição, alvo, cor): luz colorida das lancetas e do óculo no piso do presbitério
    ("LancetSpotA", (CATHEDRAL_FACADE_X + 45.6, CHANCEL_FLOOR + 7.0, 3.25), (CATHEDRAL_FACADE_X + 38.0, CHANCEL_FLOOR, -1.0), "Color(0.5, 0.69, 1, 1)"),
    ("LancetSpotB", (CATHEDRAL_FACADE_X + 45.6, CHANCEL_FLOOR + 7.0, -3.25), (CATHEDRAL_FACADE_X + 38.0, CHANCEL_FLOOR, 1.0), "Color(0.5, 0.69, 1, 1)"),
    ("OculusSpot", (CATHEDRAL_FACADE_X + 46.5, CHANCEL_FLOOR + 11.3, 0.0), (CATHEDRAL_FACADE_X + 37.0, CHANCEL_FLOOR, 0.0), "Color(1, 0.78, 0.4, 1)"),
]


def add_cathedral_lights(scene: SceneWriter) -> None:
    """Warm lamps along the nave, a spot on the crucifix, gold backlight in the retable, coloured light from the apse
    windows and a small lamp at each side altar (the stained glass glows on its own)."""
    nave_lights = [CATHEDRAL_FACADE_X + offset for offset in (8.0, 15.0, 22.0, 29.0)]
    altar_light = (CATHEDRAL_FACADE_X + 39.7, CHANCEL_FLOOR + 9.0, 0.0)
    retable_backlights = [(CATHEDRAL_FACADE_X + 45.0, CHANCEL_FLOOR + 8.0, side * 2.0) for side in (-1.0, 1.0)]
    side_altar_lights = [(CATHEDRAL_FACADE_X + 38.5, CATHEDRAL_FLOOR + 3.0, side * 10.0) for side in (-1.0, 1.0)]
    warm_omni = {"light_color": "Color(1, 0.85, 0.62, 1)", "distance_fade_enabled": "true", "distance_fade_begin": "60.0"}

    scene.add_node("CathedralLights", ".", "Node3D")

    for index, light_x in enumerate(nave_lights):
        scene.add_node(f"NaveLight{index}", "CathedralLights", "OmniLight3D", properties={**warm_omni, "position": vector(light_x, CATHEDRAL_FLOOR + 9.0, 0.0), "light_energy": "1.6", "omni_range": "13.0"})

    scene.add_node("AltarLight", "CathedralLights", "SpotLight3D", properties={
        "position": vector(*altar_light),
        "rotation": look_rotation(altar_light, CATHEDRAL_CRUCIFIX),
        "light_color": "Color(1, 0.914, 0.769, 1)",
        "light_energy": "4.0",
        "spot_range": "14.0",
        "spot_angle": "28.0",
    })

    for index, position in enumerate(retable_backlights):
        scene.add_node(f"RetableBacklight{index}", "CathedralLights", "OmniLight3D", properties={**warm_omni, "position": vector(*position), "light_color": "Color(1, 0.8, 0.45, 1)", "light_energy": "0.6", "omni_range": "4.0"})

    for index, position in enumerate(side_altar_lights):
        scene.add_node(f"SideAltarLight{index}", "CathedralLights", "OmniLight3D", properties={**warm_omni, "position": vector(*position), "light_energy": "0.8", "omni_range": "4.0"})

    for name, position, target, color in CATHEDRAL_GLASS_SPOTS:
        scene.add_node(name, "CathedralLights", "SpotLight3D", properties={
            "position": vector(*position),
            "rotation": look_rotation(position, target),
            "light_color": color,
            "light_energy": "1.2",
            "spot_range": "16.0",
            "spot_angle": "30.0",
        })


# ---------- squares ----------

PLANT_MODELS = {  # tipo -> modelos de build_trees.py
    "tree_old": [f"res://art/town/trees/old_tree_{index}.gltf" for index in range(1, 7)],
    "tree_bloom": [f"res://art/town/trees/tree_bloom_{index}.gltf" for index in range(1, 3)],
    "palm": ["res://art/town/palm_9.gltf", "res://art/town/palm_11.gltf", "res://art/town/palm_14.gltf"],
}
PLANT_FALLBACK_MODELS = {"tree_bloom": [f"res://art/nature/CommonTree_{index}.gltf" for index in range(1, 6)]}  # até rodar build_trees.py
PLANT_SCALES = {"tree_old": (0.92, 1.08), "tree_bloom": (0.85, 1.0), "palm": (0.94, 1.06)}
PALM_WEIGHTS = (0.2, 0.5, 0.3)  # palm_9, palm_11, palm_14 (seção B)
PALM_SEED = 311
PALM_LIMIT = 52
PALM_SPACING = 6.0
PALM_ROW_OFFSET = 2.0  # do eixo do caminho: largura/2 + isto, por dentro da sebe
GROVE_SEED = 907
GROVE_SPACING = 8.5
GROVE_ATTEMPTS = 3000
OLD_TREES_GETULIO_VARGAS = [  # metade norte, espelhada em z: faixa da avenida e o "V" que se fecha na direção da catedral
    (-48.0, -41.0), (-39.0, -41.0), (-30.0, -41.0),
    (-28.5, -30.5), (-18.5, -27.0), (-12.0, -18.5),
    (-18.0, -38.0), (-11.0, -32.0),
    (-11.5, -40.0), (-11.5, -12.0),
]  # todos com bed_field >= ROOT_CLEARANCE (pontos medidos nos gramados do traçado A.4)
BLOOM_TREES_WEST_EDGE = [(-58.5, -38.0), (-58.5, -30.0), (-58.5, -10.0)]
GROVE_FORCED = [(13.5, -19.5), (13.5, -24.5), (20.0, -21.0), (16.0, -40.0)]  # as gigantes que emolduram a fachada
FOUNTAIN_BENCH_ANGLES = (33.0, 85.0, 140.0)  # graus, espelhados em z: fora das bocas dos caminhos e dos postes
ROUNDABOUT_LAMP_ANGLES = (57.0, 66.0, 114.0, 123.0, -57.0, -66.0, -114.0, -123.0)  # dois em cada canto de calçada recortado
PLAZA_LAMP_COUNT = {NODE_RADIUS: 2, RONDEL_RADIUS: 4}  # largos oeste têm quatro bocas de caminho, sobra menos espaço
ESPLANADE_STATIONS = (-60.0, -53.0, -46.0, -22.0, -15.0, -8.0)


def point_at(center: tuple, radius: float, degrees: float) -> tuple:
    return center[0] + radius * math.cos(math.radians(degrees)), center[1] + radius * math.sin(math.radians(degrees))


def ring_points(center: tuple, radius: float, count: int, start_degrees: float = 0.0) -> list:
    return [point_at(center, radius, start_degrees + 360.0 * index / count) for index in range(count)]


def mirrored_in_z(spots: list) -> list:
    return spots + [(x, -z) for x, z in spots]


def distance(first: tuple, second: tuple) -> float:
    return math.hypot(first[0] - second[0], first[1] - second[1])


def far_from_all(spot: tuple, others: list, minimum: float) -> bool:
    return all(distance(spot, other) >= minimum for other in others)


def path_mouth_angles(center: tuple) -> list:
    """Directions (degrees) of the strips that leave a plaza centred at center."""
    far_ends = [path[2] if path[1] == center else path[1] for path in SQUARE_PATHS if path[0] == "strip" and center in (path[1], path[2])]

    return [math.degrees(math.atan2(end[1] - center[1], end[0] - center[0])) for end in far_ends]


def angle_gap(first: float, second: float) -> float:
    return abs((first - second + 180.0) % 360.0 - 180.0)


def free_angles(center: tuple, count: int, taken: list) -> list:
    """count spread-out directions around a plaza, at least 30° away from its paths and 20° from the taken directions."""
    mouths = path_mouth_angles(center)
    candidates = [float(angle) for angle in range(0, 360, 15) if all(angle_gap(angle, mouth) >= 30.0 for mouth in mouths) and all(angle_gap(angle, other) >= 20.0 for other in taken)]
    stride = max(1, len(candidates) // count)

    return candidates[::stride][:count]


def secondary_plazas() -> list:
    return [(node, NODE_RADIUS) for node in WEST_NODES] + [(rondel, RONDEL_RADIUS) for rondel in EAST_RONDELS]


def plaza_lamp_directions() -> list:
    """(center, radius, degrees) of the lamps standing in each secondary plaza."""
    return [(center, radius, angle) for center, radius in secondary_plazas() for angle in free_angles(center, PLAZA_LAMP_COUNT[radius], [])]


def add_lamps(scene: SceneWriter) -> list:
    center_x, center_z = GETULIO_VARGAS
    perimeter_offsets = [-36.0, -18.0, 0.0, 18.0, 36.0]
    fountain_ring = ring_points(GETULIO_VARGAS, 9.0, 8, 22.5)
    esplanade = mirrored_in_z([(x, -ESPLANADE_WIDTH / 2.0 + 0.4) for x in ESPLANADE_STATIONS])
    plazas = [point_at(center, radius - 0.8, angle) for center, radius, angle in plaza_lamp_directions()]
    getulio_vargas_edges = [(center_x + side * (SQUARE_HALF[0] - 0.6), center_z + offset) for side in (-1, 1) for offset in perimeter_offsets]
    getulio_vargas_ends = [(center_x + offset, center_z + side * (SQUARE_HALF[1] - 0.6)) for side in (-1, 1) for offset in (-18.0, 0.0, 18.0)]
    forecourt = [(6.0, -15.0), (6.0, 15.0), (CATHEDRAL_FACADE_X - 4.5, -9.0), (CATHEDRAL_FACADE_X - 4.5, 9.0)]
    sao_jose_ring = [(x, side * 14.0) for side in (-1, 1) for x in (26.0, 38.0, 50.0, 62.0)]
    square_candidates = fountain_ring + esplanade + plazas + getulio_vargas_edges + getulio_vargas_ends + forecourt + sao_jose_ring
    median = [(x, sum(MEDIAN_Z) / 2.0) for x in range(-96, 97, 16) if abs(x) > MEDIAN_NOSE_X + 2.0]
    roundabout = [point_at(ROUNDABOUT, ROUNDABOUT_OUTER_RADIUS + 0.8, angle) for angle in ROUNDABOUT_LAMP_ANGLES]
    positions = [spot for spot in square_candidates if is_paved(spot)] + median + roundabout

    scene.add_node("Lamps", ".", "Node3D", groups=[NAVIGATION_SOURCE_GROUP])

    for index, (x, z) in enumerate(positions):
        place(scene, f"Lamp{index:02d}", "Lamps", "res://features/hub/props/lamp_post.tscn", grounded(x, z))

    return positions


def strip_side_rows(path: tuple, generator: random.Random) -> list:
    """Palm candidates in rows on both sides of a strip, every PALM_SPACING metres, jittered along it."""
    _, start, end, width = path
    length = distance(start, end)
    along = ((end[0] - start[0]) / length, (end[1] - start[1]) / length)
    offset = width / 2.0 + PALM_ROW_OFFSET
    stations = [PALM_SPACING * (index + 0.5) + generator.uniform(-0.6, 0.6) for index in range(int(length / PALM_SPACING))]

    return [(start[0] + along[0] * station - side * along[1] * offset, start[1] + along[1] * station + side * along[0] * offset) for station in stations for side in (-1.0, 1.0)]


def old_tree_spots() -> list:
    """Big old trees: the explicit Getúlio Vargas bands plus a seeded Poisson grove that fills São José."""
    getulio_vargas = [spot for spot in mirrored_in_z(OLD_TREES_GETULIO_VARGAS) if can_plant(spot, "tree_old")]
    grove = [spot for spot in mirrored_in_z(GROVE_FORCED) if can_plant(spot, "tree_old")]
    generator = random.Random(GROVE_SEED)
    minimum, maximum = LAWN_RECTS["SaoJose"]

    for _ in range(GROVE_ATTEMPTS):
        spot = (generator.uniform(minimum[0], maximum[0]), generator.uniform(minimum[1], maximum[1]))

        if can_plant(spot, "tree_old") and far_from_all(spot, grove, GROVE_SPACING):
            grove.append(spot)

    return getulio_vargas + grove


def palm_spots(old_trees: list) -> list:
    """Royal palms in rows along the diagonals and the esplanade, around the plazas and at the forecourt (seeded, at most PALM_LIMIT)."""
    generator = random.Random(PALM_SEED)
    diagonals = [path for path in SQUARE_PATHS if path[0] == "strip" and path[1][0] < 0.0 and path[3] < ESPLANADE_WIDTH]
    along_diagonals = [spot for path in diagonals for spot in strip_side_rows(path, generator)]
    esplanade = mirrored_in_z([(x, -ESPLANADE_WIDTH / 2.0 - PALM_ROW_OFFSET) for x in ESPLANADE_STATIONS])
    around_plazas = [point_at(center, radius + PALM_ROW_OFFSET, 72.0 * index + generator.uniform(-12.0, 12.0)) for center, radius in secondary_plazas() for index in range(5)]
    forecourt = mirrored_in_z([(11.3, -14.0)])
    palms = []

    for spot in esplanade + forecourt + around_plazas + along_diagonals:
        is_clear = distance(spot, COREO_POSITION) >= 6.5 and far_from_all(spot, palms, 3.2) and far_from_all(spot, old_trees, 4.0)

        if can_plant(spot, "palm") and is_clear:
            palms.append(spot)

    while len(palms) > PALM_LIMIT:
        palms.pop(generator.randrange(len(palms)))

    return palms


def grass_tuft_spots() -> list:
    """Seeded scatter of grass tufts over the lawns of both squares, inside the hedges."""
    generator = random.Random(GRASS_SEED)
    spots = []

    for minimum, maximum in LAWN_RECTS.values():
        candidates = [(generator.uniform(minimum[0], maximum[0]), generator.uniform(minimum[1], maximum[1])) for _ in range(GRASS_TUFTS_PER_SQUARE * 3)]
        spots += [spot for spot in candidates if can_plant(spot, "bush")][:GRASS_TUFTS_PER_SQUARE]

    return spots


def plant_models(kind: str) -> list:
    """Models of a plant kind; the fallback only while the generated glTFs are missing."""
    models = PLANT_MODELS[kind]
    is_generated = all((PROJECT_DIR / model.removeprefix("res://")).exists() for model in models)

    return models if is_generated else PLANT_FALLBACK_MODELS[kind]


def spot_variant(spot: tuple, count: int) -> int:
    """Stable variant index from the position, so moving one tree does not reshuffle the others."""
    return int(abs(spot[0] * 31.0 + spot[1] * 17.0)) % count


def palm_variants(spots: list) -> list:
    """Palm heights by PALM_WEIGHTS, never the same height twice in a row (rows are listed in order)."""
    generator = random.Random(PALM_SEED)
    choices = []

    for _ in spots:
        options = [index for index in range(len(PALM_WEIGHTS)) if not choices or index != choices[-1]]
        weights = [PALM_WEIGHTS[index] for index in options]
        choices.append(generator.choices(options, weights)[0])

    return choices


def place_plants(scene: SceneWriter, kind: str, spots: list, name: str) -> None:
    models = plant_models(kind)
    smallest, largest = PLANT_SCALES[kind]
    variant_by_kind = {
        "palm": lambda: palm_variants(spots),
        "tree_old": lambda: [spot_variant(spot, len(models)) for spot in spots],
        "tree_bloom": lambda: [spot_variant(spot, len(models)) for spot in spots],
    }
    variants = variant_by_kind[kind]()

    for index, (x, z) in enumerate(spots):
        scale = smallest + (largest - smallest) * (index * 0.618 % 1.0)
        place(scene, f"{name}{index:03d}", "Trees", models[variants[index]], grounded(x, z), rotation_y=index * 1.3, scale=scale)


def add_trees(scene: SceneWriter) -> None:
    """Old trees in bands and the São José grove, blooming trees on the west edge and the median, royal palms in rows."""
    old_trees = old_tree_spots()
    bloom_trees = [spot for spot in mirrored_in_z(BLOOM_TREES_WEST_EDGE) if can_plant(spot, "tree_bloom")]
    palms = palm_spots(old_trees)
    median = [(x, MEDIAN_BEDS[0][0][1] + 1.5) for x in range(-88, 89, 16) if abs(x) > MEDIAN_NOSE_X + 2.0]
    backyards = [((block[0] + block[1]) / 2.0, (block[2] + block[3]) / 2.0) for block in BLOCKS]

    assert all(bed_field(spot) >= PLANT_CLEARANCE for spot in old_trees + bloom_trees + palms), "tronco fora do canteiro"

    scene.add_node("Trees", ".", "Node3D")
    place_plants(scene, "tree_old", old_trees, "OldTree")
    place_plants(scene, "tree_bloom", bloom_trees + median, "BloomTree")
    place_plants(scene, "palm", palms, "Palm")
    place_plants(scene, "tree_old", backyards, "BackyardTree")

    for index, (x, z) in enumerate(grass_tuft_spots()):
        place(scene, f"Grass{index:03d}", "Trees", "res://art/nature/Grass_Common_Short.gltf", grounded(x, z), rotation_y=index * 0.7, scale=0.4 + 0.08 * (index % 3))


def plaza_benches() -> list:
    """Two benches inside each secondary plaza, between paths and lamps, facing the middle."""
    lamp_angles = {}
    benches = []

    for center, _, angle in plaza_lamp_directions():
        lamp_angles.setdefault(center, []).append(angle)

    for center, radius in secondary_plazas():
        benches += [(point_at(center, radius - 1.2, angle), facing_yaw(point_at(center, radius - 1.2, angle), center)) for angle in free_angles(center, 2, lamp_angles[center])]

    return benches


def bench_layout() -> dict:
    """Benches by group, each (spot, yaw): around the chafariz, along the esplanade, in the plazas and beside the cathedral."""
    fountain_spots = [point_at(GETULIO_VARGAS, 8.6, angle) for angle in FOUNTAIN_BENCH_ANGLES + tuple(-angle for angle in FOUNTAIN_BENCH_ANGLES)]
    esplanade = [((x, side * (ESPLANADE_WIDTH / 2.0 - 0.6)), math.pi if side > 0 else 0.0) for side in (-1, 1) for x in (-56.0, -50.0, -18.0, -12.0)]
    cathedral = [((x, side * 15.4), 0.0 if side < 0 else math.pi) for side in (-1, 1) for x in (32.0, 44.0)]

    return {
        "fountain": [(spot, facing_yaw(spot, GETULIO_VARGAS)) for spot in fountain_spots],
        "esplanade": esplanade,
        "plazas": plaza_benches(),
        "cathedral": cathedral,
    }


def add_square_props(scene: SceneWriter) -> dict:
    """Chafariz, roundabout fountain, benches (returned for the sitters), forecourt planters and flowering bushes."""
    benches = bench_layout()
    all_benches = [bench for group in benches.values() for bench in group]
    forecourt_planters = [(10.5, -12.0), (10.5, 12.0), (10.5, -6.0), (10.5, 6.0)]
    plaza_bush_spots = [point_at(center, radius + 2.2, angle) for center, radius in secondary_plazas() for angle in free_angles(center, 2, [])]
    bushes = [spot for spot in ring_points(GETULIO_VARGAS, 12.4, 8, 22.5) + plaza_bush_spots if can_plant(spot, "bush")]

    scene.add_node("SquareProps", ".", "Node3D", groups=[NAVIGATION_SOURCE_GROUP])
    place(scene, "Chafariz", "SquareProps", "res://features/hub/props/fountain_large.tscn", (GETULIO_VARGAS[0], 0, GETULIO_VARGAS[1]))
    place(scene, "RoundaboutFountain", "SquareProps", "res://features/hub/props/fountain_small.tscn", (ROUNDABOUT[0], 0, ROUNDABOUT[1]))

    for index, ((x, z), rotation_y) in enumerate(all_benches):
        place(scene, f"Bench{index:02d}", "SquareProps", "res://art/props/Bench.gltf", grounded(x, z), rotation_y)

    for index, (x, z) in enumerate(forecourt_planters):
        place(scene, f"Planter{index:02d}", "SquareProps", "res://art/town/planter.gltf", (x, 0, z))
        place(scene, f"PlanterFlowers{index:02d}", "SquareProps", f"res://art/nature/Flower_{3 + index % 2}_Group.gltf", (x, PLANTER_SOIL_HEIGHT, z), rotation_y=index * 1.7, scale=0.6)

    for index, (x, z) in enumerate(bushes):
        place(scene, f"FlowerBush{index:02d}", "SquareProps", "res://art/nature/Bush_Common_Flowers.gltf", grounded(x, z), rotation_y=index * 0.9)

    return benches


def add_market(scene: SceneWriter) -> None:
    """Calçadão market on Rua Brasil between the squares; the middle stays open toward the cathedral."""
    market_items = [
        ("Stall_Empty", (-2.4, 0, -38.0), math.pi / 2.0),
        ("Stall_Empty", (-2.4, 0, -33.6), math.pi / 2.0),
        ("Stall_Cart_Empty", (-2.2, 0, -27.0), math.pi / 2.0 + 0.3),
        ("Stall_Empty", (-2.4, 0, 27.0), math.pi / 2.0),
        ("Stall_Empty", (-2.4, 0, 31.4), math.pi / 2.0),
        ("Stall_Cart_Empty", (-2.2, 0, 38.0), math.pi / 2.0 - 0.3),
        ("Barrel", (-3.2, 0, -30.5), 0.0),
        ("Barrel_Apples", (-3.1, 0, -24.6), 0.4),
        ("FarmCrate_Apple", (-3.0, 0, 34.6), 0.2),
        ("FarmCrate_Carrot", (-3.0, 0, 24.3), -0.2),
        ("Crate_Wooden", (3.0, 0, -36.0), 0.3),
        ("Bucket_Wooden_1", (3.1, 0, -34.9), 0.0),
        ("Table_Large", (2.6, 0, 34.0), math.pi / 2.0),
        ("Stool", (2.6, 0, 32.4), 0.0),
        ("Stool", (2.6, 0, 35.6), 0.0),
    ]

    scene.add_node("Market", ".", "Node3D", groups=[NAVIGATION_SOURCE_GROUP])

    for index, (model_name, position, rotation_y) in enumerate(market_items):
        place(scene, f"{model_name}{index:02d}", "Market", f"res://art/props/{model_name}.gltf", position, rotation_y)


def add_backdrop(scene: SceneWriter) -> None:
    margin = 14.0
    north_south = [(x, z) for x in range(int(CITY_MIN[0]) - 10, int(CITY_MAX[0]) + 11, 14) for z in (CITY_MIN[1] - margin, CITY_MAX[1] + margin)]
    west_east = [(x, z) for z in range(int(CITY_MIN[1]), int(CITY_MAX[1]) + 1, 14) for x in (CITY_MIN[0] - margin, CITY_MAX[0] + margin)]

    scene.add_node("Backdrop", ".", "Node3D")

    for index, (x, z) in enumerate(north_south + west_east):
        place(scene, f"Pine{index:02d}", "Backdrop", f"res://art/nature/Pine_{index % 3 + 1}.gltf", (x, 0, z), rotation_y=index * 0.5, scale=1.6 + 0.2 * (index % 3))


# ---------- townsfolk ----------

def npc(scene: SceneWriter, name: str, body: str, hair: str, properties: dict) -> None:
    body_id = scene.external_id("PackedScene", f"res://art/characters/{body}.gltf")
    all_properties = {"body_scene": f'ExtResource("{body_id}")', "hair_color": color(HAIR_COLORS[hair])}

    all_properties.update(properties)
    scene.add_node(name, "Townsfolk", instance=scene.external_id("PackedScene", "res://features/hub/walking_npc.tscn"), properties=all_properties)


def patrol(points: list, speed: float, pause: float, idle: str) -> dict:
    point_list = ", ".join(f"{x:.2f}, 0, {z:.2f}" for x, z in points)

    return {"route": f"PackedVector3Array({point_list})", "walk_speed": f"{speed}", "pause_seconds": f"{pause}", "idle_animation": f'&"{idle}"'}


def stand(position: tuple, facing: float, animation: str, offset: float, height: float = 0.0) -> dict:
    return {
        "position": vector(position[0], height or ground_height(position), position[1]),
        "rotation": vector(0, facing, 0),
        "activity": "1",
        "idle_animation": f'&"{animation}"',
        "animation_offset_seconds": f"{offset}",
    }


def sitter(bench: tuple) -> tuple:
    (x, z), rotation_y = bench

    return (x + 0.15 * math.sin(rotation_y), z + 0.15 * math.cos(rotation_y)), rotation_y


def add_townsfolk(scene: SceneWriter, benches: dict) -> None:
    center_x, center_z = GETULIO_VARGAS
    half_x, half_z = SQUARE_HALF
    # Entre o chafariz (colisão r=5.1) e o anel de postes (r=9).
    fountain_loop = ring_points(GETULIO_VARGAS, 7.2, 12)
    perimeter_loop = [(center_x - half_x + 2.6, center_z - half_z + 2.6), (center_x + half_x - 2.6, center_z - half_z + 2.6), (center_x + half_x - 2.6, center_z + half_z - 2.6), (center_x - half_x + 2.6, center_z + half_z - 2.6)]
    sao_jose_loop = [(8.0, -16.5), (63.0, -16.5), (63.0, 16.5), (8.0, 16.5)]
    worshipper_route = [(8.0, 5.0), (CATHEDRAL_FACADE_X - 4.0, 0.0), (CATHEDRAL_FACADE_X + 26.0, 0.0)]
    west_bench_seat, west_bench_facing = sitter(benches["fountain"][3])
    east_bench_seat, east_bench_facing = sitter(benches["esplanade"][3])
    cathedral_bench_seat, cathedral_bench_facing = sitter(benches["cathedral"][0])
    median_z = sum(MEDIAN_Z) / 2.0
    talker_a = (EAST_RONDELS[1][0] - 0.9, EAST_RONDELS[1][1] - 0.4)  # conversa no rondel sudeste
    talker_b = (EAST_RONDELS[1][0] + 0.5, EAST_RONDELS[1][1] + 0.5)

    scene.add_node("Navigation", ".", "NavigationRegion3D", properties={"navigation_mesh": f'ExtResource("{scene.external_id("NavigationMesh", "res://features/hub/hub_navmesh.tres")}")'})
    scene.add_node("Townsfolk", ".", "Node3D")
    npc(scene, "FountainWalker", "villager_male", "dark", patrol(fountain_loop, 1.2, 0.0, "ual1/Idle"))
    npc(scene, "FountainWalkerReverse", "villager_female", "auburn", patrol(list(reversed(fountain_loop[6:] + fountain_loop[:6])), 1.1, 0.0, "ual1/Idle"))
    npc(scene, "SquareWalker", "adventurer_female", "blond", patrol(perimeter_loop, 1.4, 0.0, "ual1/Idle"))
    npc(scene, "SquareWalkerReverse", "villager_male", "grey", patrol(list(reversed(perimeter_loop[2:] + perimeter_loop[:2])), 1.2, 0.0, "ual1/Idle"))
    npc(scene, "CalcadaoWalker", "villager_female", "brown", patrol([(0.8, -22.0), (0.8, 22.0)], 1.1, 4.0, "ual1/Idle_Talking"))
    npc(scene, "Worshipper", "villager_female", "black", patrol(worshipper_route, 1.0, 6.0, "ual1/Idle"))
    npc(scene, "CathedralStroller", "villager_male", "brown", patrol(sao_jose_loop, 1.2, 2.0, "ual2/Idle_FoldArms"))
    npc(scene, "MedianWalkerWest", "adventurer_male", "black", patrol([(-92.0, median_z + 2.0), (-MEDIAN_NOSE_X - 1.5, median_z + 2.0)], 1.4, 3.0, "ual2/Idle_FoldArms"))
    npc(scene, "MedianWalkerEast", "villager_female", "grey", patrol([(MEDIAN_NOSE_X + 1.5, median_z + 2.0), (92.0, median_z + 2.0)], 1.2, 3.0, "ual1/Idle"))
    npc(scene, "SidewalkWalker", "villager_male", "auburn", patrol([(-60.0, -67.5), (60.0, -67.5)], 1.3, 5.0, "ual1/Idle"))
    npc(scene, "Merchant", "villager_male", "auburn", stand((-1.1, -36.0), math.pi / 2.0, "ual1/Idle_Talking", 1.1))
    npc(scene, "Shopper", "villager_female", "blond", stand((0.4, -35.4), -math.pi / 2.0 - 0.3, "ual2/Idle_FoldArms", 0.4))
    npc(scene, "TalkerA", "villager_male", "brown", stand(talker_a, facing_yaw(talker_a, talker_b), "ual1/Idle_Talking", 0.0))
    npc(scene, "TalkerB", "villager_female", "blond", stand(talker_b, facing_yaw(talker_b, talker_a), "ual2/Idle_FoldArms", 0.7))
    npc(scene, "SittingWest", "villager_female", "grey", stand(west_bench_seat, west_bench_facing, "ual1/Sitting_Idle", 0.3))
    npc(scene, "SittingEast", "villager_male", "black", stand(east_bench_seat, east_bench_facing, "ual1/Sitting_Talking", 0.0))
    npc(scene, "SittingCathedral", "adventurer_male", "brown", stand(cathedral_bench_seat, cathedral_bench_facing, "ual1/Sitting_Talking", 0.5))
    npc(scene, "Bard", "adventurer_female", "auburn", stand((COREO_POSITION[0], COREO_POSITION[1]), math.pi / 2.0, "ual1/Idle_Talking", 0.2, height=1.2))
    npc(scene, "Guard", "adventurer_female", "dark", stand((CATHEDRAL_FACADE_X - 4.2, -6.5), -math.pi / 2.0, "ual2/Idle_FoldArms", 0.0))
    npc(scene, "Priest", "villager_male", "grey", stand((CATHEDRAL_FACADE_X + 40.4, 0.0), -math.pi / 2.0, "ual1/Idle", 0.0, height=CHANCEL_FLOOR + 0.3))


# ---------- player and cameras ----------

def add_player_and_cameras(scene: SceneWriter) -> None:
    spawn_x, spawn_z = PLAYER_SPAWN
    select_eye = (spawn_x + 4.4, 1.35, spawn_z - 1.2)
    tour = [
        ((-90, 28, -30), (18, 8, 0)),
        ((-24, 2.6, 9), (-34, 2.2, 0)),
        ((-37, 3.2, -23), (COREO_POSITION[0], 2.6, COREO_POSITION[1])),
        ((0, 2.2, 44), (0, 2.0, -20)),
        ((2, 1.8, 7), (18, 18, 0)),
        ((CATHEDRAL_FACADE_X + 4, 2.8, 0), CATHEDRAL_CRUCIFIX),
        ((-90, 4, -57), (0, 3, -57)),
    ]

    place(scene, "Player", ".", "res://features/player/player.tscn", (spawn_x, 0, spawn_z), -math.pi / 2.0)
    scene.add_node("SelectCamera", ".", "Camera3D", properties={"position": vector(*select_eye), "rotation": look_rotation(select_eye, (spawn_x, 0.8, spawn_z)), "fov": "42.0"})
    scene.add_node("CinematicTour", ".", "Node3D", properties={"script": f'ExtResource("{scene.external_id("Script", "res://features/hub/cinematic_tour.gd")}")'})

    for index, (eye, target) in enumerate(tour):
        scene.add_node(f"Key{index}", "CinematicTour", "Marker3D", properties={"position": vector(*eye), "rotation": look_rotation(eye, target)})

    scene.add_node("CharacterSelect", ".", instance=scene.external_id("PackedScene", "res://features/hub/character_select.tscn"))
    scene.add_node("FpsCounter", ".", instance=scene.external_id("PackedScene", "res://features/hub/fps_counter.tscn"))


def add_environment(scene: SceneWriter) -> None:
    scene.add_sub_resource('''
[sub_resource type="ProceduralSkyMaterial" id="sky_material"]
sky_top_color = Color(0.361, 0.561, 0.82, 1)
sky_horizon_color = Color(0.78, 0.89, 0.95, 1)
sky_curve = 0.12
ground_horizon_color = Color(0.78, 0.89, 0.95, 1)
ground_bottom_color = Color(0.35, 0.42, 0.33, 1)
sun_angle_max = 20.0''')
    scene.add_sub_resource('''
[sub_resource type="Sky" id="sky"]
sky_material = SubResource("sky_material")''')
    scene.add_sub_resource('''
[sub_resource type="Environment" id="environment"]
background_mode = 2
sky = SubResource("sky")
ambient_light_source = 3
ambient_light_color = Color(0.663, 0.784, 0.941, 1)
ambient_light_sky_contribution = 0.75
tonemap_mode = 2
tonemap_exposure = 0.95
tonemap_white = 1.4
ssao_enabled = true
ssao_radius = 1.4
ssao_intensity = 1.6
ssil_enabled = true
glow_enabled = true
glow_intensity = 0.35
glow_bloom = 0.05
glow_blend_mode = 1
glow_hdr_threshold = 1.0
fog_enabled = true
fog_light_color = Color(0.78, 0.87, 0.95, 1)
fog_density = 0.0016
fog_sun_scatter = 0.25
fog_aerial_perspective = 0.35
adjustment_enabled = true
adjustment_saturation = 1.08''')
    scene.add_node("WorldEnvironment", ".", "WorldEnvironment", properties={"environment": 'SubResource("environment")'})
    scene.add_node("Sun", ".", "DirectionalLight3D", properties={
        "rotation": vector(-0.78, 0.55 + math.radians(40.0), 0.0),
        "light_color": "Color(1, 0.902, 0.769, 1)",
        "light_energy": "1.35",
        "shadow_enabled": "true",
        "shadow_blur": "1.5",
        "directional_shadow_mode": "1",
        "directional_shadow_max_distance": "110.0",
    })


def build_hub_scene() -> str:
    scene = SceneWriter()
    script_id = scene.external_id("Script", "res://features/hub/hub.gd")

    scene.add_node("Hub", None, "Node3D", properties={"script": f'ExtResource("{script_id}")'})
    add_materials(scene)
    add_environment(scene)
    add_ground(scene)
    add_town_wall(scene)
    add_buildings(scene)
    add_cathedral_lights(scene)
    add_lamps(scene)
    add_trees(scene)
    benches = add_square_props(scene)
    add_market(scene)
    add_backdrop(scene)
    add_townsfolk(scene, benches)
    add_player_and_cameras(scene)

    return scene.render()


if __name__ == "__main__":
    if not NAVMESH_PATH.exists():  # placeholder until tools_src/bake_hub_navmesh.gd bakes the real one
        NAVMESH_PATH.write_text('[gd_resource type="NavigationMesh" format=3]\n\n[resource]\n', encoding="utf-8", newline="\n")

    OUTPUT_PATH.write_text(build_hub_scene(), encoding="utf-8", newline="\n")
    print(f"WROTE {OUTPUT_PATH}")
