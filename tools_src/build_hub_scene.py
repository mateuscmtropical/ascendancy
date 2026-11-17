"""Write features/hub/hub.tscn: the starting city.

Two squares side by side, separated by the market promenade:
  - West square: union-jack paths, tiered chafariz in the middle, octagonal coreto.
  - East square: the cathedral in the middle, facade toward the promenade, dense shade trees.
The main avenue, with a tree-lined median and a roundabout, runs along the north side; a second avenue
runs along the south. A ring of ten half-blocks of row houses closes the city, inside a town wall.
X runs along the avenues, Z across them.

Godot coordinates, Y up. Every model's front faces +Z locally, so rotation_y turns it toward the street.

Usage: python tools_src/build_hub_scene.py
"""

import itertools
import json
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
HOUSE_ROW_DEPTH = 12.5  # recorte de esquina: lotes têm até 12 m de fundo
SQUARE_HALF = (30.0, 48.0)
WEST_SQUARE = (-34.0, 0.0)
EAST_SQUARE = (34.0, 0.0)
AVENUE_Z = (-66.0, -48.0)
MEDIAN_Z = (-60.0, -54.0)
ROUNDABOUT = (0.0, -57.0)
CATHEDRAL_FACADE_X = 13.0  # catedral de 26 x 47,6 m (build_cathedral.py): fundo da abside em x = 60,6
CATHEDRAL_FLOOR = 1.05
CHANCEL_FLOOR = CATHEDRAL_FLOOR + 0.9
CATHEDRAL_CRUCIFIX = (CATHEDRAL_FACADE_X + 45.4, CHANCEL_FLOOR + 5.6, 0.0)  # peito do Cristo no retábulo
ADRO_WIDTH = 30.0  # cobre as estátuas da escadaria (z = ±12,2)
COREO_POSITION = (-46.0, -13.0)  # no gramado a noroeste do chafariz
COREO_APRON_RADIUS = 4.6
COREO_ACCESS_END = (-38.2, -13.0)  # o caminho do coreto encosta na diagonal do largo noroeste
COREO_ACCESS_WIDTH = 3.4  # cabe a escada com as muretas
PLAYER_SPAWN = (-38.4, -13.0)  # pé da escada do coreto, olhando para a catedral (+X)
PATH_WIDTH = 4.0
BRANCH_OVERRUN = 4.0  # ramo que chega na borda do gramado passa reto até a calçada (sem quina de grama)
PLANTER_SOIL_HEIGHT = 0.42
GRASS_SEED = 77
GRASS_TUFTS_PER_SQUARE = 110

ESPLANADE_WIDTH = 8.0  # eixo oeste-leste que cruza a praça oeste e aponta para a fachada
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
    "WestSquare": ((WEST_SQUARE[0] - SQUARE_HALF[0] + PATH_WIDTH, -SQUARE_HALF[1] + PATH_WIDTH), (WEST_SQUARE[0] + SQUARE_HALF[0] - PATH_WIDTH, SQUARE_HALF[1] - PATH_WIDTH)),
    "EastSquare": ((EAST_SQUARE[0] - SQUARE_HALF[0] + PATH_WIDTH, -SQUARE_HALF[1] + PATH_WIDTH), (EAST_SQUARE[0] + SQUARE_HALF[0] - PATH_WIDTH, SQUARE_HALF[1] - PATH_WIDTH)),
}


def run_past(start: tuple, end: tuple, extra: float) -> tuple:
    """End point pushed further along the strip, so its square end lands on paving instead of leaving a lawn notch."""
    length = math.hypot(end[0] - start[0], end[1] - start[1])

    return (end[0] + (end[0] - start[0]) / length * extra, end[1] + (end[1] - start[1]) / length * extra)


def west_square_branches(sign: float) -> list:
    """Diagonals of one half of the west square (sign -1 = north, +1 = south): chafariz to the secondary plazas and their branches."""
    node = (WEST_NODES[0][0], sign * abs(WEST_NODES[0][1]))
    rondel = (EAST_RONDELS[0][0], sign * abs(EAST_RONDELS[0][1]))

    return [
        ("strip", WEST_SQUARE, node, 3.5),
        ("strip", node, run_past(node, (-60.0, sign * 44.0), BRANCH_OVERRUN), 3.5),  # largo -> canto da praça
        ("strip", node, run_past(node, (-60.0, sign * 21.0), BRANCH_OVERRUN), 3.0),  # largo -> borda oeste
        ("strip", node, run_past(node, (-23.0, sign * 39.5), 1.5), 3.0),  # largo -> ramo norte/sul (entra até o meio dele)
        ("strip", WEST_SQUARE, rondel, 3.5),
        ("strip", rondel, run_past(rondel, (-23.0, sign * 44.0), BRANCH_OVERRUN), 3.0),  # rondel -> borda norte/sul
        ("strip", rondel, run_past(rondel, (-8.0, sign * 27.0), BRANCH_OVERRUN), 3.0),  # rondel -> borda leste
    ]


def east_square_walks(sign: float) -> list:
    """Walks of one half of the east square: the cross walk, the one along the promenade and the one along the back street."""
    half_x, half_z = SQUARE_HALF
    west, east = EAST_SQUARE[0] - half_x, EAST_SQUARE[0] + half_x

    return [
        ("strip", (west, sign * 30.0), (east, sign * 30.0), 3.0),
        ("strip", (west + 4.0, sign * 11.0), (west + 4.0, sign * half_z), 3.0),
        ("strip", (east - 3.0, sign * 16.0), (east - 3.0, sign * half_z), 3.0),
    ]


def square_paths() -> list:
    """Paved shapes cut out of the lawns, Godot (x, z): ("disc", center, radius) or ("strip", start, end, width)."""
    half_x = SQUARE_HALF[0]
    east_square_west, east_square_east = EAST_SQUARE[0] - half_x, EAST_SQUARE[0] + half_x
    plazas = [
        ("disc", WEST_SQUARE, PLAZA_RADIUS),
        ("strip", (WEST_SQUARE[0] - half_x, 0.0), (WEST_SQUARE[0] + half_x, 0.0), ESPLANADE_WIDTH),
        ("disc", COREO_POSITION, COREO_APRON_RADIUS),
        ("strip", COREO_POSITION, COREO_ACCESS_END, COREO_ACCESS_WIDTH),
        *[("disc", node, NODE_RADIUS) for node in WEST_NODES],
        *[("disc", rondel, RONDEL_RADIUS) for rondel in EAST_RONDELS],
        ("strip", (east_square_west, 0.0), (CATHEDRAL_FACADE_X, 0.0), ADRO_WIDTH),  # adro
        ("strip", (CATHEDRAL_FACADE_X, 0.0), (east_square_east, 0.0), 32.0),  # passeio em volta da catedral
    ]
    branches = [path for sign in (-1.0, 1.0) for path in west_square_branches(sign) + east_square_walks(sign)]

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


SIDE_ROTATION = {"N": math.pi, "S": 0.0, "W": -math.pi / 2.0, "E": math.pi / 2.0}  # house front faces the street
BLOCKS = [  # (min x, max x, min z, max z, street sides by priority)
    (-102, -72, -96, -66, "S"),  # fileira norte = comércio e ofícios: as lojas grandes ocupam a quadra de ponta a ponta
    (-64, -4, -96, -66, "S"),
    (4, 64, -96, -66, "S"),
    (72, 102, -96, -66, "S"),
    (-102, -72, -48, 48, "E"),  # quadra oeste = biblioteca, escola e seminário, de frente para a catedral
    (72, 102, -48, 48, ""),  # quadra leste, atrás da abside = fazenda (FARM_*): sem fileira de casas
    (-102, -72, 58, 88, "NE"),
    (-64, -4, 58, 88, "NWE"),  # fileira sul = residencial
    (4, 64, 58, 88, "NWE"),
    (72, 102, 58, 88, "NW"),
]
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
        node_paths = [key for key, value in (properties or {}).items() if value.startswith("NodePath(")]
        header += " node_paths=PackedStringArray(" + ", ".join(f'"{key}"' for key in node_paths) + ")" if node_paths else ""  # exports de nó: o Godot só resolve os listados
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
    """Stone wall around the city: closes the street ends and keeps the player inside; the farm lane leaves through
    a gap in the east wall into the fenced fields."""
    thickness = TOWN_WALL_THICKNESS
    height = 4.5
    walls = [
        ("North", ((CITY_MIN[0] + CITY_MAX[0]) / 2.0, CITY_MIN[1] - thickness / 2.0), (CITY_MAX[0] - CITY_MIN[0] + 2 * thickness, thickness)),
        ("South", ((CITY_MIN[0] + CITY_MAX[0]) / 2.0, CITY_MAX[1] + thickness / 2.0), (CITY_MAX[0] - CITY_MIN[0] + 2 * thickness, thickness)),
        ("West", (CITY_MIN[0] - thickness / 2.0, (CITY_MIN[1] + CITY_MAX[1]) / 2.0), (thickness, CITY_MAX[1] - CITY_MIN[1])),
        ("EastNorth", (CITY_MAX[0] + thickness / 2.0, (CITY_MIN[1] + FARM_GATE_Z[0]) / 2.0), (thickness, FARM_GATE_Z[0] - CITY_MIN[1])),
        ("EastSouth", (CITY_MAX[0] + thickness / 2.0, (FARM_GATE_Z[1] + CITY_MAX[1]) / 2.0), (thickness, CITY_MAX[1] - FARM_GATE_Z[1])),
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


def add_buildings(scene: SceneWriter) -> None:
    """Cathedral, coreto and the modelled lots of town_lots() (build_town_houses.py and build_market_shops.py)."""
    lots = town_lots()
    missing = missing_town_models(lots)

    assert not missing, f"rode build_town_houses.py / build_market_shops.py antes; faltam: {missing[:4]}"

    check_town_plan(lots)
    scene.add_node("Buildings", ".", "Node3D", groups=[NAVIGATION_SOURCE_GROUP])
    place(scene, "Cathedral", "Buildings", "res://art/town/cathedral.gltf", (CATHEDRAL_FACADE_X, 0, EAST_SQUARE[1]), -math.pi / 2.0)
    place(scene, "Coreto", "Buildings", "res://art/town/coreto.gltf", (COREO_POSITION[0], 0, COREO_POSITION[1]), math.pi / 2.0)

    add_town_lots(scene, lots)


# ---------- farm: block 5 behind the apse and the fields beyond the east wall ----------

FARM_BLOCK = 5
FARM_YARD = (75.0, CITY_MAX[0], -45.0, 45.0)  # x e z: a quadra menos as calçadas oeste, norte e sul
TOWN_WALL_THICKNESS = 1.2
FARM_FIELDS = (CITY_MAX[0] + TOWN_WALL_THICKNESS, 150.0, -46.0, 46.0)  # campo aberto além do muro leste
FARM_GATE_Z = (-3.0, 3.0)  # vão no muro leste por onde a estradinha da fazenda sai para o campo
FARM_LANE_HALF_WIDTH = 2.0
FARMHOUSE = {"position": (FARM_YARD[0] + 1.5, 0.0, -37.0), "rotation": SIDE_ROTATION["W"], "width": 12.0, "depth": 10.0}  # de frente para a abside
BARN = {"position": (94.5, 0.0, -27.0), "rotation": 0.0, "width": 13.0, "depth": 15.0}  # portões para o terreiro (+z)
FARM_PENS = {  # cercado -> (min x, max x, min z, max z) por dentro da cerca
    "cows": (77.0, 100.5, 4.0, 28.0),
    "pigs": (85.0, 100.5, 31.0, 43.5),
}
FARM_ANIMAL_MARGIN = 1.5  # bicho anda num retângulo afastado da cerca
FARM_ANIMALS = {  # cercado -> (modelo convertido por convert_farm_animals.py, quantos, velocidade em m/s)
    "cows": ("res://art/town/farm/animals/cow.gltf", 4, 0.55),
    "pigs": ("res://art/town/farm/animals/pig.gltf", 5, 0.5),
}
FARM_ANIMAL_SEED = 5150
FARM_ANIMAL_GAP = 1.6  # distância mínima entre bichos ao nascer, em comprimentos do corpo
FARM_ANIMAL_TRIES = 60
FARM_FIELD_PLOTS = {  # canteiro -> (cultura, min x, max x, min z, max z): fileiras correm ao longo de x
    # Uma faixa por cultura: horta (repolho, cenoura) junto do portão, grãos adiante, trigo na faixa do fundo,
    # feno ao sul. A estradinha (z = 0) fica com 1,8 m de margem de cada lado e as trilhas com 1,4 m.
    "Wheat": ("wheat", 108.0, 147.0, -44.0, -24.0),
    "Cabbage": ("cabbage", 108.0, 124.0, -19.0, -5.0),
    "Corn": ("corn", 127.0, 147.0, -19.0, -5.0),
    "Carrot": ("carrot", 108.0, 124.0, 5.0, 19.0),
    "HayField": ("hayfield", 127.0, 147.0, 5.0, 19.0),
    "Meadow": ("meadow", 108.0, 147.0, 23.0, 44.0),
}
FARM_SHADE_TREES = {  # nome -> (tipo em PLANT_MODELS, variante, x, z, escala): sombra nos pastos, copa inteira dentro da cerca
    "CowOak": ("tree_old", 2, 83.0, 12.0, 0.6),
    "CowBloom": ("tree_bloom", 0, 94.5, 12.5, 0.8),
    "PigBloom": ("tree_bloom", 1, 89.0, 35.2, 0.7),
}
CANOPY_RADIUS = {"tree_old": 8.0, "tree_bloom": 4.9}  # maior alcance da copa em escala 1 (medido nos glTF de build_trees.py)
KITCHEN_GARDEN = ("garden", 77.0, 86.0, -28.5, -20.0)  # horta ao lado da casa do fazendeiro
MULA = {"position": (112.5, 32.0), "rotation": math.pi}  # x, z no pasto além do muro, de frente para a estradinha


# ---------- town plan: lots, archetypes and shops (seções C e D) ----------

HOUSE_ARCHETYPES = {  # arquétipo -> (larguras de lote, profundidade, cores de reboco das 3 variantes) — catálogo C.3
    "sobrado": ((8, 10, 12), 10.0, ("cal", "creme", "cal")),
    "terrea": ((6, 8), 9.0, ("ocre", "rosa", "salvia")),
    "fachwerk": ((6, 8), 10.0, ("creme", "cal", "amarelo")),
    "tudor": ((10, 12), 10.0, ("creme", "cal", "creme")),
    "holandesa": ((6,), 12.0, ("tijolo", "tijolo_escuro", "tijolo_claro")),
    "chale": ((10, 12), 10.0, ("caiada", "creme", "cal")),
    "mediterranea": ((8, 10), 10.0, ("cal", "ocre", "rosa")),
    "artdeco": ((8, 10), 10.0, ("creme", "rosa", "azul")),
    "pedra": ((8,), 9.0, ("dourada", "clara", "dourada")),
    "palacete": ((10, 12), 10.0, ("ocre", "rosa", "terra")),
    "torre": ((8,), 8.0, ("cinza", "media", "cinza")),
    "hanseatica": ((8, 10), 12.0, ("tijolo_claro", "tijolo", "tijolo_claro")),
}
HOUSE_VARIANTS = 3
BACK_STREET_ARCHETYPES = ("terrea", "fachwerk", "chale", "mediterranea", "pedra")
CORNER_ARCHETYPES = ("torre", "artdeco", "sobrado")
STREET_GABLE_ARCHETYPES = ("fachwerk", "holandesa", "hanseatica")  # cumeeira perpendicular à rua (empena para a rua)
FLAT_ROOF_ARCHETYPES = ("artdeco", "torre")  # platibanda e pavilhão: sem cumeeira, servem em qualquer quadra
BLOCK_RIDGE_AXIS = {  # quadra -> eixo do mundo de todas as cumeeiras dela (o das lojas fixas manda; senão o da fileira principal)
    0: "x", 1: "z", 2: "x", 3: "x", 6: "x", 7: "x", 8: "x", 9: "x",
}
ARCHETYPE_REPEAT_DISTANCE = 3  # mesmo arquétipo proibido a menos de 3 lotes
LOT_WIDTHS = (6, 8, 10, 12)
LOT_FRONT_OVERHANG = 1.2  # beiral, sacada e placa podem avançar sobre a calçada
LOT_EDGE_CLEARANCE = 0.02
TOWN_SEED = 4421
SHOP_LOTS = {  # tipo -> (largura, profundidade) do prédio: 1/3 de quadra ou mais (docs/research/shops.md)
    "smith": (24, 20.0),
    "armor": (18, 20.0),
    "magic": (18, 20.0),
    "tailor": (18, 20.0),
    "tavern": (18, 20.0),
    "alchemy": (18, 20.0),
    "general": (18, 20.0),
    "guild": (24, 20.0),
    "library": (30, 20.0),
    "school": (30, 20.0),
    "seminary": (30, 20.0),
}
FIXED_LOTS = {  # (bloco, lado) -> [(início, fim, prédio ou None)] ao longo da fileira; trechos sem lote fixo são preenchidos
    (0, "S"): [(-99.0, -75.0, "smith")],
    (1, "S"): [(-61.0, -43.0, "armor"), (-43.0, -25.0, "magic"), (-25.0, -7.0, "tailor")],
    (2, "S"): [(7.0, 25.0, "tavern"), (25.0, 43.0, "alchemy"), (43.0, 61.0, "general")],
    (3, "S"): [(75.0, 99.0, "guild")],
    (4, "E"): [(-45.0, -15.0, "library"), (-15.0, 15.0, "school"), (15.0, 45.0, "seminary")],
}
SHOP_SIGNS = {  # prédio -> placas penduradas (build_shops.py): o ofício principal e o da ala
    "smith": ("smith",), "armor": ("armor",), "magic": ("magic",), "tailor": ("tailor", "jeweler"), "tavern": ("tavern", "inn"),
    "alchemy": ("alchemy", "herbalist"), "general": ("general", "bakery"), "guild": ("guild", "bank"), "library": ("bookshop",),
}
SHOP_FRONT_OVERHANG = 2.6  # toldos e mercadoria na calçada
ROW_START_SIDE = {"S": "left", "N": "right", "E": "right", "W": "left"}  # lado do modelo (u < 0 = left) na ponta inicial da fileira
INTERIOR_VISIBLE_DISTANCE = 60.0  # o recheio das lojas some além disto (features/hub/shop_interior.gd)
# Luzes locais somem com a distância (o Forward+ paga cada luz por pixel que ela toca): de dentro das lojas e da
# catedral só se vê a luz pela porta e pelas janelas, e de longe ela não faz diferença.
LIGHT_FADE_BEGIN = {"shop": 30.0, "cathedral": 45.0}
LIGHT_FADE_LENGTH = 10.0
ALLEY_WALL_HEIGHT = 2.2


def lot_widths(length: float, generator: random.Random, allowed_widths: tuple = LOT_WIDTHS) -> tuple:
    """Lot widths that fill length exactly; the odd remainder (< 2 m) becomes an alley (C.1 item 4)."""
    alley = length % 2.0
    remaining = length - alley
    lots = []

    while remaining > 0.0:
        options = [width for width in allowed_widths if remaining - width == 0.0 or remaining - width >= min(allowed_widths)]
        lots.append(generator.choice(options))
        remaining -= lots[-1]

    return lots, alley


def row_segments(run_start: float, run_end: float, fixed: list) -> list:
    """Fixed lots in order plus the free stretches between them: (start, end, shop or "fixed" or "free")."""
    segments = []
    cursor = run_start

    for start, end, shop in sorted(fixed):
        segments += [(cursor, start, "free")] if start - cursor > 1e-6 else []
        segments.append((start, end, shop or "fixed"))
        cursor = end

    segments += [(cursor, run_end, "free")] if run_end - cursor > 1e-6 else []

    return segments


def segment_lots(segment: tuple, generator: random.Random, allowed_widths: tuple) -> list:
    """(start, width, shop) lots of one segment; a free stretch may end with an alley ("alley" lot)."""
    start, end, kind = segment
    lots_by_kind = {"free": lambda: free_lots(start, end, generator, allowed_widths), "fixed": lambda: [(start, end - start, None)]}

    return lots_by_kind.get(kind, lambda: [(start, end - start, kind)])()


def free_lots(start: float, end: float, generator: random.Random, allowed_widths: tuple) -> list:
    widths, alley = lot_widths(end - start, generator, allowed_widths)
    lots = []
    cursor = start
    alley_index = len(widths) // 2 if alley > 1e-6 else -1

    for index, width in enumerate(widths):
        lots += [(cursor, alley, "alley")] if index == alley_index else []
        cursor += alley if index == alley_index else 0.0
        lots.append((cursor, float(width), None))
        cursor += width

    lots += [(cursor, alley, "alley")] if alley > 1e-6 and not widths else []

    return lots


def roof_archetypes(gable_to_street: bool) -> tuple:
    """Archetypes whose ridge runs the way the block asks: across the street (gable to the street) or along it."""
    along_street = tuple(name for name in HOUSE_ARCHETYPES if name not in STREET_GABLE_ARCHETYPES + FLAT_ROOF_ARCHETYPES)

    return (STREET_GABLE_ARCHETYPES if gable_to_street else along_street) + FLAT_ROOF_ARCHETYPES


def row_widths(archetypes: tuple) -> tuple:
    """Lot widths some archetype of the row can fill."""
    return tuple(width for width in LOT_WIDTHS if any(width in HOUSE_ARCHETYPES[name][0] for name in archetypes))


def pick_archetype(width: float, history: list, usage: dict, is_corner: bool, is_main: bool, archetypes: tuple, generator: random.Random) -> str:
    """Archetype for a residence lot: one of the block's roof family, fits the width, never repeats within
    ARCHETYPE_REPEAT_DISTANCE lots (relaxed to the last lot when the family is too small), corners of the main rows
    prefer the two-fronted types, back streets the simple ones; among those, the least used so far in town wins
    (ties drawn by seed)."""
    fitting = []

    for repeat_distance in (ARCHETYPE_REPEAT_DISTANCE, 2):
        recent = history[-(repeat_distance - 1):]
        fitting = fitting or [name for name in archetypes if int(width) in HOUSE_ARCHETYPES[name][0] and name not in recent]

    assert fitting, f"nenhum arquétipo de {width} m entre {archetypes}"
    preferred_by_place = {(True, True): CORNER_ARCHETYPES, (True, False): BACK_STREET_ARCHETYPES + ("torre",), (False, False): BACK_STREET_ARCHETYPES, (False, True): tuple(HOUSE_ARCHETYPES)}
    preferred = [name for name in fitting if name in preferred_by_place[(is_corner, is_main)]] or fitting
    fewest = min(usage.get(name, 0) for name in preferred)
    chosen = generator.choice([name for name in preferred if usage.get(name, 0) == fewest])
    usage[chosen] = usage.get(chosen, 0) + 1

    return chosen


def pick_variant(archetype: str, previous_plaster: str, generator: random.Random) -> int:
    """Colour variant whose plaster differs from the neighbour's."""
    plasters = HOUSE_ARCHETYPES[archetype][2]
    options = [variant for variant in range(HOUSE_VARIANTS) if plasters[variant] != previous_plaster]

    return generator.choice(options)


def lot_frame(facade: float, along: float, axis: str, side: str) -> tuple:
    """Position of the lot front centre and the yaw that turns the model's +Z front to the street."""
    position = (along, 0.0, facade) if axis == "x" else (facade, 0.0, along)

    return position, SIDE_ROTATION[side]


def town_lots() -> list:
    """Every lot of the town rows: dicts with model, kind, width, depth, position, rotation, side and corner flag."""
    usage = {}
    lots = []

    for block_index, block in enumerate(BLOCKS):
        street_sides = block[4]
        generator = random.Random(TOWN_SEED * 100 + block_index)  # sub-seed por quadra: mudar uma não embaralha as outras

        for side_index, side in enumerate(street_sides):
            facade, run_start, run_end, axis = trimmed_run(block, side, street_sides[:side_index])
            archetypes = roof_archetypes(axis != BLOCK_RIDGE_AXIS.get(block_index, axis))
            segments = row_segments(run_start, run_end, FIXED_LOTS.get((block_index, side), []))
            row = [lot for segment in segments for lot in segment_lots(segment, generator, row_widths(archetypes))]
            lots += dress_row(row, facade, axis, side, side_index == 0, usage, archetypes, generator)

    return lots


def dress_row(row: list, facade: float, axis: str, side: str, is_main: bool, usage: dict, archetypes: tuple, generator: random.Random) -> list:
    """Give each lot of a row its model (shop building, house archetype and variant, or alley gate)."""
    history = []
    previous_plaster = ""
    building_indices = [index for index, (_, _, kind) in enumerate(row) if kind != "alley"]
    corners = {building_indices[0], building_indices[-1]} if building_indices else set()
    dressed = []

    for index, (start, width, kind) in enumerate(row):
        position, rotation = lot_frame(facade, start + width / 2.0, axis, side)
        lot = {"width": width, "position": position, "rotation": rotation, "side": side, "kind": kind or "house"}

        if kind == "alley":
            lot.update(model="res://art/town/houses/alley_gate.gltf", depth=0.4)
        elif kind:
            row_ends = [(building_indices[0], ROW_START_SIDE[side]), (building_indices[-1], {"left": "right", "right": "left"}[ROW_START_SIDE[side]])]
            exposed = tuple(sorted(end_side for end_index, end_side in row_ends if end_index == index))
            lot.update(model=f"res://art/town/shops/shop_{kind}.gltf", depth=SHOP_LOTS[kind][1], shop=kind, exposed=exposed)
            history.append(kind)
        else:
            archetype = pick_archetype(width, history, usage, index in corners, is_main, archetypes, generator)
            variant = pick_variant(archetype, previous_plaster, generator)
            previous_plaster = HOUSE_ARCHETYPES[archetype][2][variant]
            history.append(archetype)
            lot.update(model=f"res://art/town/houses/{archetype}_w{int(width)}_{variant}.gltf", depth=HOUSE_ARCHETYPES[archetype][1], archetype=archetype, variant=variant)

        dressed.append(lot)

    return dressed


def lot_rectangle(lot: dict, front_overhang: float = 0.0) -> tuple:
    """World (min x, max x, min z, max z) of a lot, inset by LOT_EDGE_CLEARANCE at the sides."""
    half = lot["width"] / 2.0 - LOT_EDGE_CLEARANCE
    inward = {"N": 1.0, "S": -1.0, "W": 1.0, "E": -1.0}[lot["side"]]
    x, _, z = lot["position"]
    near, far = -inward * front_overhang, inward * lot["depth"]
    rectangles = {
        "x": (x - half, x + half, z + min(near, far), z + max(near, far)),
        "z": (x + min(near, far), x + max(near, far), z - half, z + half),
    }

    return rectangles["x" if lot["side"] in ("N", "S") else "z"]


def rectangles_overlap(first: tuple, second: tuple) -> bool:
    return first[0] < second[1] and second[0] < first[1] and first[2] < second[3] and second[2] < first[3]


def model_rectangle(lot: dict, sidecar: dict) -> tuple:
    """World rectangle of a placed model from its sidecar AABB (yaw is a multiple of 90°)."""
    x, _, z = lot["position"]
    minimum, maximum = sidecar["aabb_min"], sidecar["aabb_max"]
    corners = [(corner_x, corner_z) for corner_x in (minimum[0], maximum[0]) for corner_z in (minimum[2], maximum[2])]
    cos_yaw, sin_yaw = round(math.cos(lot["rotation"])), round(math.sin(lot["rotation"]))
    turned = [(x + corner_x * cos_yaw + corner_z * sin_yaw, z - corner_x * sin_yaw + corner_z * cos_yaw) for corner_x, corner_z in corners]

    return min(point[0] for point in turned), max(point[0] for point in turned), min(point[1] for point in turned), max(point[1] for point in turned)


def model_sidecar(model: str) -> dict:
    sidecar_path = PROJECT_DIR / model.removeprefix("res://").replace(".gltf", ".json")

    return json.loads(sidecar_path.read_text(encoding="utf-8")) if sidecar_path.exists() else {}


def check_town_plan(lots: list) -> None:
    """C.1 item 8: lots never overlap, stay out of the roundabout, and (once modelled) each model fits its lot."""
    rectangles = [lot_rectangle(lot) for lot in lots]
    pairs = itertools.combinations(range(len(lots)), 2)
    overlapping = [(first, second) for first, second in pairs if rectangles_overlap(rectangles[first], rectangles[second])]
    in_roundabout = [index for index, rectangle in enumerate(rectangles) if rectangle_distance(rectangle, ROUNDABOUT) < ROUNDABOUT_OUTER_RADIUS + 0.5]
    sidecars = [(lot, model_sidecar(lot["model"])) for lot in lots]
    outside_lot = [lot["model"] for lot, sidecar in sidecars if sidecar and not rectangle_inside(model_rectangle(lot, sidecar), lot_rectangle(lot, SHOP_FRONT_OVERHANG if lot.get("shop") else LOT_FRONT_OVERHANG), 0.01)]
    models = [model_rectangle(lot, sidecar) for lot, sidecar in sidecars if sidecar]
    touching_models = [(first, second) for first, second in itertools.combinations(range(len(models)), 2) if rectangles_overlap(models[first], models[second])]

    assert not overlapping, f"lotes sobrepostos: {overlapping[:4]}"
    assert not in_roundabout, f"lote dentro da rotatória: {in_roundabout}"
    assert not outside_lot, f"modelo maior que o lote: {outside_lot[:4]}"
    assert not touching_models, f"prédios se atravessam: {touching_models[:4]}"


def rectangle_distance(rectangle: tuple, point: tuple) -> float:
    dx = max(rectangle[0] - point[0], 0.0, point[0] - rectangle[1])
    dz = max(rectangle[2] - point[1], 0.0, point[1] - rectangle[3])

    return math.hypot(dx, dz)


def rectangle_inside(inner: tuple, outer: tuple, tolerance: float) -> bool:
    return inner[0] >= outer[0] - tolerance and inner[1] <= outer[1] + tolerance and inner[2] >= outer[2] - tolerance and inner[3] <= outer[3] + tolerance


def missing_town_models(lots: list) -> list:
    """Models the plan uses that build_town_houses.py / build_market_shops.py have not written yet."""
    return [lot["model"] for lot in lots if not (PROJECT_DIR / lot["model"].removeprefix("res://")).exists()]


SHOPKEEPERS = {  # prédio -> (corpo, cabelo, animação) de quem atende atrás do balcão
    "smith": ("villager_male", "black", "ual2/Idle_FoldArms"),
    "armor": ("adventurer_male", "brown", "ual1/Idle"),
    "magic": ("villager_female", "grey", "ual1/Idle_Talking"),
    "tailor": ("villager_male", "grey", "ual1/Idle"),
    "tavern": ("villager_female", "auburn", "ual1/Idle_Talking"),
    "alchemy": ("villager_male", "auburn", "ual1/Idle"),
    "general": ("villager_female", "brown", "ual1/Idle_Talking"),
    "guild": ("adventurer_female", "dark", "ual2/Idle_FoldArms"),
    "library": ("villager_female", "dark", "ual1/Idle"),
    "school": ("villager_male", "brown", "ual1/Idle_Talking"),
    "seminary": ("villager_male", "grey", "ual1/Idle"),
}
SHOP_SIGN_SCALE = 1.6  # as placas foram feitas para fachadas de 8 m
SHOP_SIGN_OFFSET = 0.45  # da borda da porta até o braço da placa, no pilar entre a porta e a primeira vitrine


def lot_to_world(lot: dict, point: tuple) -> tuple:
    """Model-local Godot point of a lot (x, y, z) to world coordinates."""
    x, _, z = lot["position"]
    cos_yaw, sin_yaw = math.cos(lot["rotation"]), math.sin(lot["rotation"])

    return x + point[0] * cos_yaw + point[2] * sin_yaw, point[1], z - point[0] * sin_yaw + point[2] * cos_yaw


def add_town_lots(scene: SceneWriter, lots: list) -> None:
    """Place the modelled houses, alley gates and enterable shops of the plan."""
    houses = [lot for lot in lots if lot["kind"] == "house"]
    alleys = [lot for lot in lots if lot["kind"] == "alley"]
    shops = [lot for lot in lots if lot.get("shop")]

    for index, lot in enumerate(houses):
        place(scene, f"House{index:03d}", "Buildings", lot["model"], lot["position"], lot["rotation"])

    for index, lot in enumerate(alleys):
        properties = {"position": vector(*lot["position"]), "rotation": vector(0.0, lot["rotation"], 0.0), "scale": vector(lot["width"], 1.0, 1.0)}
        scene.add_node(f"AlleyGate{index:02d}", "Buildings", instance=scene.external_id("PackedScene", lot["model"]), properties=properties)

    scene.add_node("Shops", ".", "Node3D", groups=[NAVIGATION_SOURCE_GROUP])

    for index, lot in enumerate(shops):
        add_shop_building(scene, index, lot)


def add_shop_building(scene: SceneWriter, index: int, lot: dict) -> None:
    """Shop building with its hanging sign, the furnished interior (own model, hidden from afar), the lights of both
    sidecars and the shopkeeper behind the counter."""
    shop_type = lot["shop"]
    sidecar = model_sidecar(lot["model"])
    interior_model = lot["model"].replace(".gltf", "_interior.gltf")
    interior_sidecar = model_sidecar(interior_model)
    shop_name = f"Shop{index:02d}{shop_type.title()}"
    door = sidecar["doors"][0]
    sign_reach = door["width"] / 2.0 + SHOP_SIGN_OFFSET
    interior_script = scene.external_id("Script", "res://features/hub/shop_interior.gd")

    scene.add_node(shop_name, "Shops", "Node3D", properties={"position": vector(*lot["position"]), "rotation": vector(0.0, lot["rotation"], 0.0)}, groups=[f"shop_{shop_type}"])
    place(scene, "Building", f"Shops/{shop_name}", lot["model"], (0.0, 0.0, 0.0))

    for sign_index, sign in enumerate(SHOP_SIGNS.get(shop_type, ())):
        sign_x = door["x"] + (1.0 - 2.0 * sign_index) * sign_reach
        place(scene, f"Sign{sign_index}", f"Shops/{shop_name}", f"res://art/town/shops/shop_{sign}_sign.gltf", (sign_x, 0.0, 0.0), scale=SHOP_SIGN_SCALE)

    if interior_sidecar:
        scene.add_node("Interior", f"Shops/{shop_name}", "Node3D", properties={"script": f'ExtResource("{interior_script}")', "visible_distance": f"{INTERIOR_VISIBLE_DISTANCE}"})
        place(scene, "Props", f"Shops/{shop_name}/Interior", interior_model, (0.0, 0.0, 0.0))

    for light_index, light in enumerate(sidecar["lights"] + interior_sidecar.get("lights", [])):
        scene.add_node(f"Light{light_index}", f"Shops/{shop_name}", "OmniLight3D", properties={
            "position": vector(*light["position"]),
            "light_color": hex_color(light["color"]),
            "light_energy": f"{light['energy']}",
            "omni_range": f"{light['range']}",
            **light_fade("shop"),
        })


def light_fade(place_kind: str) -> dict:
    """Distance fade properties of a local light (LIGHT_FADE_BEGIN by where it shines)."""
    return {"distance_fade_enabled": "true", "distance_fade_begin": f"{LIGHT_FADE_BEGIN[place_kind]}", "distance_fade_length": f"{LIGHT_FADE_LENGTH}"}


def add_shopkeepers(scene: SceneWriter, lots: list) -> None:
    """One shopkeeper standing behind each shop counter, turned toward the door."""
    shops = [lot for lot in lots if lot.get("shop")]

    for index, lot in enumerate(shops):
        sidecar = model_sidecar(lot["model"])
        keeper_body, keeper_hair, keeper_animation = SHOPKEEPERS[lot["shop"]]
        keeper = lot_to_world(lot, sidecar["markers"]["shopkeeper"])
        door = sidecar["doors"][0]
        door_world = lot_to_world(lot, (door["x"], 0.0, 1.0))
        facing = facing_yaw((keeper[0], keeper[2]), (door_world[0], door_world[2]))
        npc(scene, f"Shopkeeper{index:02d}", keeper_body, keeper_hair, stand((keeper[0], keeper[2]), facing, keeper_animation, 0.0))


SIDEWALK_DOOR_REACH = 1.6  # do pé da fachada até onde quem olha a vitrine para, no meio da calçada de 3 m
WINDOW_SHOPPERS = {  # nome -> (lado da fileira, faixa de x ou z das portas, corpo, cabelo, velocidade, pausa)
    "WindowShopperWest": ("S", (-102.0, -4.0), "villager_female", "auburn", 1.1, 5.0),
    "WindowShopperEast": ("S", (4.0, 102.0), "villager_male", "blond", 1.2, 4.0),
    "Scholar": ("E", (-48.0, 48.0), "villager_male", "grey", 1.0, 6.0),
}


def shop_door_fronts(lots: list, side: str, span: tuple) -> list:
    """Sidewalk spots in front of each shop door of a row, in walking order along the row."""
    shops = [lot for lot in lots if lot.get("shop") and lot["side"] == side]
    fronts = [lot_to_world(lot, (model_sidecar(lot["model"])["doors"][0]["x"], 0.0, SIDEWALK_DOOR_REACH)) for lot in shops]
    along_axis = 0 if side in ("N", "S") else 2
    inside = [front for front in fronts if span[0] <= front[along_axis] <= span[1]]

    return sorted(((front[0], front[2]) for front in inside), key=lambda front: front[0 if along_axis == 0 else 1])


def add_window_shoppers(scene: SceneWriter, lots: list) -> None:
    """Townsfolk who stroll a shop row and stop at every door (sidewalk north of the avenue, civic block)."""
    for name, (side, span, body, hair, speed, pause) in WINDOW_SHOPPERS.items():
        npc(scene, name, body, hair, patrol(shop_door_fronts(lots, side, span), speed, pause, "ual1/Idle"))


def hex_color(text: str) -> str:
    """'FFD9A0' (sRGB) -> Godot Color literal."""
    return color(tuple(int(text[offset:offset + 2], 16) / 255.0 for offset in (0, 2, 4)))


APSE_CENTER_X = CATHEDRAL_FACADE_X + 40.0  # centro do semicírculo da abside (build_cathedral.py: BODY_LENGTH)
APSE_GLASS_RADIUS = 6.6  # um pouco para dentro da face interna da parede (raio 7)
LANCET_ANGLES = (30.0, 55.0, 78.0)  # graus do eixo da abside, de cada lado (build_cathedral.py)
LANCET_CENTER_Y = CHANCEL_FLOOR + 7.0
OCULUS_CENTER_Y = CHANCEL_FLOOR + 11.3
AISLE_BAYS = (7.8, 13.4, 19.0, 24.6, 30.2)  # build_cathedral.py: BAY_CENTERS, ao longo da nave a partir da fachada
AISLE_GLASS_Z = 12.3  # face interna da parede sul (meia largura 13, parede 0,6)
AISLE_GLASS_Y = 10.45  # meio do vitral alto do tramo
GLASS_TEXTURES = "res://art/town/textures/"


def cathedral_glass_spots() -> list:
    """(name, position, inward normal, projector texture, half angle) for every window the sun can shine through:
    the six apse lancets and the oculus get the morning sun from the east, the south aisle windows the rest of the day
    (the sun crosses the sky on the +z side; the north windows never see it)."""
    lancets = [
        (f"LancetSun{variant}{'N' if side < 0 else 'S'}",
         (APSE_CENTER_X + APSE_GLASS_RADIUS * math.cos(math.radians(angle)), LANCET_CENTER_Y, side * APSE_GLASS_RADIUS * math.sin(math.radians(angle))),
         (-math.cos(math.radians(angle)), 0.0, -side * math.sin(math.radians(angle))),
         f"{GLASS_TEXTURES}T_DoveGlass{variant}.png", 5.0)
        for (variant, angle), side in itertools.product(enumerate(LANCET_ANGLES), (-1.0, 1.0))
    ]
    oculus = [("OculusSun", (APSE_CENTER_X + APSE_GLASS_RADIUS, OCULUS_CENTER_Y, 0.0), (-1.0, 0.0, 0.0), f"{GLASS_TEXTURES}T_OculusGlass.png", 6.0)]
    aisle = [(f"AisleSun{index}", (CATHEDRAL_FACADE_X + bay, AISLE_GLASS_Y, AISLE_GLASS_Z), (0.0, 0.0, -1.0), f"{GLASS_TEXTURES}T_StainedGlassFigure.png", 6.0) for index, bay in enumerate(AISLE_BAYS)]

    return lancets + oculus + aisle


def add_cathedral_lights(scene: SceneWriter) -> None:
    """Warm lamps along the nave, a spot on the crucifix, gold backlight in the retable, coloured light from the apse
    windows and a small lamp at each side altar (the stained glass glows on its own)."""
    nave_lights = [CATHEDRAL_FACADE_X + offset for offset in (8.0, 15.0, 22.0, 29.0)]
    altar_light = (CATHEDRAL_FACADE_X + 39.7, CHANCEL_FLOOR + 9.0, 0.0)
    retable_backlights = [(CATHEDRAL_FACADE_X + 45.0, CHANCEL_FLOOR + 8.0, side * 2.0) for side in (-1.0, 1.0)]
    side_altar_lights = [(CATHEDRAL_FACADE_X + 38.5, CATHEDRAL_FLOOR + 3.0, side * 10.0) for side in (-1.0, 1.0)]
    warm_omni = {"light_color": "Color(1, 0.85, 0.62, 1)", **light_fade("cathedral")}

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
        **light_fade("cathedral"),
    })

    for index, position in enumerate(retable_backlights):
        scene.add_node(f"RetableBacklight{index}", "CathedralLights", "OmniLight3D", properties={**warm_omni, "position": vector(*position), "light_color": "Color(1, 0.8, 0.45, 1)", "light_energy": "0.6", "omni_range": "4.0"})

    for index, position in enumerate(side_altar_lights):
        scene.add_node(f"SideAltarLight{index}", "CathedralLights", "OmniLight3D", properties={**warm_omni, "position": vector(*position), "light_energy": "0.8", "omni_range": "4.0"})

    sun_script = scene.external_id("Script", "res://features/sky/sun_through_glass.gd")

    for name, position, inward, texture, half_angle in cathedral_glass_spots():
        scene.add_node(name, "CathedralLights", "SpotLight3D", properties={
            "position": vector(*position),
            "visible": "false",
            "light_projector": f'ExtResource("{scene.external_id("Texture2D", texture)}")',
            "light_energy": "0.0",
            "spot_range": "32.0",
            "spot_angle": f"{half_angle}",
            "spot_attenuation": "0.2",
            "light_volumetric_fog_energy": "0.2",  # só um véu de poeira no feixe; 1.0 lava a nave
            "script": f'ExtResource("{sun_script}")',
            "day_night": 'NodePath("../../DayNight")',
            "inward_normal": vector(*inward),
            "base_energy": "1.6",
            **light_fade("cathedral"),
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
OLD_TREES_WEST_SQUARE = [  # metade norte, espelhada em z: faixa da avenida e o "V" que se fecha na direção da catedral
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
    center_x, center_z = WEST_SQUARE
    perimeter_offsets = [-36.0, -18.0, 0.0, 18.0, 36.0]
    fountain_ring = ring_points(WEST_SQUARE, 9.0, 8, 22.5)
    esplanade = mirrored_in_z([(x, -ESPLANADE_WIDTH / 2.0 + 0.4) for x in ESPLANADE_STATIONS])
    plazas = [point_at(center, radius - 0.8, angle) for center, radius, angle in plaza_lamp_directions()]
    west_square_edges = [(center_x + side * (SQUARE_HALF[0] - 0.6), center_z + offset) for side in (-1, 1) for offset in perimeter_offsets]
    west_square_ends = [(center_x + offset, center_z + side * (SQUARE_HALF[1] - 0.6)) for side in (-1, 1) for offset in (-18.0, 0.0, 18.0)]
    forecourt = [(6.0, -15.0), (6.0, 15.0), (CATHEDRAL_FACADE_X - 4.5, -9.0), (CATHEDRAL_FACADE_X - 4.5, 9.0)]
    east_square_ring = [(x, side * 14.0) for side in (-1, 1) for x in (26.0, 38.0, 50.0, 62.0)]
    square_candidates = fountain_ring + esplanade + plazas + west_square_edges + west_square_ends + forecourt + east_square_ring
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
    """Big old trees: the explicit west square bands plus a seeded Poisson grove that fills the east square."""
    west_square = [spot for spot in mirrored_in_z(OLD_TREES_WEST_SQUARE) if can_plant(spot, "tree_old")]
    grove = [spot for spot in mirrored_in_z(GROVE_FORCED) if can_plant(spot, "tree_old")]
    generator = random.Random(GROVE_SEED)
    minimum, maximum = LAWN_RECTS["EastSquare"]

    for _ in range(GROVE_ATTEMPTS):
        spot = (generator.uniform(minimum[0], maximum[0]), generator.uniform(minimum[1], maximum[1]))

        if can_plant(spot, "tree_old") and far_from_all(spot, grove, GROVE_SPACING):
            grove.append(spot)

    return west_square + grove


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


FLOWER_COLORS = {"vermelho": "D9483B", "amarelo": "F2C544", "laranja": "E8962E", "branco": "F4EFE6", "rosa": "E9A6C0", "lilas": "B79AD6"}  # L.1
FLOWER_DENSITY = 7.0  # tufos por m² (spec 9; 7 segura o orçamento de triângulos)
FLOWER_SEED = 61
FLOWER_HEIGHTS = (0.22, 0.38)
FLOWER_TRUNK_CLEARANCE = 1.5
FLOWER_BED_MIN = 1.0  # por dentro da sebe
FLOWER_DOMINANT_SHARE = 0.8  # cada mancha: 1 cor dominante + branco ou amarelo
ROUND_BED_LIMIT = 8
ROUND_BED_SPACING = 14.0


class FlowerZone:
    """A kind of flower patch (L.2): where it grows (bounds + test on the point and its bed field) and its two colours."""

    def __init__(self, name: str, bounds: tuple, test, colors, field_band: tuple = (FLOWER_BED_MIN, math.inf), trunk_clearance: float = FLOWER_TRUNK_CLEARANCE) -> None:
        self.name = name
        self.bounds = bounds
        self.test = test
        self.colors = colors
        self.field_band = field_band
        self.trunk_clearance = trunk_clearance


def around(center: tuple, reach: float) -> tuple:
    return center[0] - reach, center[1] - reach, center[0] + reach, center[1] + reach


def round_bed_centers(trunks: list) -> list:
    """Centres of the round flower beds: deepest lawn points of the west square, far from trunks and from each other."""
    minimum, maximum = LAWN_RECTS["WestSquare"]
    grid = itertools.product(range(int(minimum[0]), int(maximum[0]) + 1), range(int(minimum[1]), int(maximum[1]) + 1))
    candidates = sorted(((bed_field((x, z)), (float(x), float(z))) for x, z in grid), reverse=True)
    centers = []

    for field, point in candidates:
        is_free = field >= 4.0 and far_from_all(point, centers, ROUND_BED_SPACING) and far_from_all(point, trunks, 4.0)
        centers += [point] if is_free and len(centers) < ROUND_BED_LIMIT else []

    return centers


def flower_zones(trunks: list, palms: list) -> list:
    """The patches of L.2: esplanade border, fountain crown, half-moons of the plazas, round beds, coreto ring, palm
    feet, forecourt strips, roundabout and marco rings, median patches."""
    gv_min, gv_max = LAWN_RECTS["WestSquare"]
    esplanade_edge = ESPLANADE_WIDTH / 2.0
    coreto_mouth = math.degrees(math.atan2(COREO_ACCESS_END[1] - COREO_POSITION[1], COREO_ACCESS_END[0] - COREO_POSITION[0]))
    round_beds = round_bed_centers(trunks)
    adro_edge = ADRO_WIDTH / 2.0
    median_z = (MEDIAN_BEDS[0][0][1] + MEDIAN_BEDS[0][1][1]) / 2.0
    zones = [
        FlowerZone("esplanada", (gv_min[0], -esplanade_edge - 3.0, gv_max[0], esplanade_edge + 3.0), lambda p: (-60.0 <= p[0] <= -46.0 or -22.0 <= p[0] <= -8.0) and abs(p[1]) <= esplanade_edge + 2.5, lambda p: ("vermelho", "branco") if int((p[0] + 100.0) / 6.0) % 2 else ("amarelo", "branco"), (FLOWER_BED_MIN, 1.8)),
        FlowerZone("coroa", around(WEST_SQUARE, 13.5), lambda p: 11.0 <= distance(p, WEST_SQUARE) <= 13.5, lambda p: ("vermelho", "branco"), (FLOWER_BED_MIN, 2.0)),
        *[FlowerZone(f"meia_lua{index}", around(center, radius + 2.0), lambda p, center=center, radius=radius: radius + 1.0 <= distance(p, center) <= radius + 1.9, lambda p, center=center: ("rosa", "branco") if center[0] < WEST_SQUARE[0] else ("lilas", "branco")) for index, (center, radius) in enumerate(secondary_plazas())],
        *[FlowerZone(f"redondo{index}", around(center, 2.4), lambda p, center=center, index=index: distance(p, center) <= 1.8 + 0.2 * (index % 4), lambda p: ("laranja", "amarelo")) for index, center in enumerate(round_beds)],
        FlowerZone("coreto", around(COREO_POSITION, 6.5), lambda p: 5.6 <= distance(p, COREO_POSITION) <= 6.4 and angle_gap(math.degrees(math.atan2(p[1] - COREO_POSITION[1], p[0] - COREO_POSITION[0])), coreto_mouth) > 30.0, lambda p: ("branco", "rosa")),
        *[FlowerZone(f"palmeira{index}", around(palm, 0.7), lambda p, palm=palm: TRUNK_RADIUS["palm"] + 0.15 <= distance(p, palm) <= 0.7, lambda p: ("amarelo", "branco"), (FLOWER_BED_MIN, math.inf), 0.0) for index, palm in enumerate(palms[::3]) if palm[0] < 0.0],
        FlowerZone("adro", (CATHEDRAL_FACADE_X - 11.0, -adro_edge - 3.0, CATHEDRAL_FACADE_X - 2.0, adro_edge + 3.0), lambda p: CATHEDRAL_FACADE_X - 10.0 <= p[0] <= CATHEDRAL_FACADE_X - 2.0 and abs(p[1]) >= adro_edge, lambda p: ("branco", "vermelho"), (FLOWER_BED_MIN, 2.0)),
        FlowerZone("rotatoria", around(ROUNDABOUT, ROUNDABOUT_LAWN_RADII[1]), lambda p: True, lambda p: ("vermelho", "branco"), (0.9, math.inf)),
        FlowerZone("marco", around(MARCO, MARCO_LAWN_RADII[1]), lambda p: True, lambda p: ("amarelo", "branco"), (0.45, math.inf)),
        FlowerZone("canteiro_central", (CITY_MIN[0], median_z - 1.0, CITY_MAX[0], median_z + 1.0), lambda p: abs(p[0]) > MEDIAN_NOSE_X + 2.0 and abs((p[0] - 8.0) % 16.0 - 8.0) >= 6.5, lambda p: ("rosa", "branco") if int((p[0] + 200.0) / 16.0) % 2 else ("laranja", "amarelo"), (0.6, math.inf)),
    ]

    return zones


def flower_tufts() -> list:
    """(x, z, colour name, height, yaw) of every flower tuft, by zone; seeded and independent of the scene writer."""
    generator = random.Random(FLOWER_SEED)
    old_trees = old_tree_spots()
    palms = palm_spots(old_trees)
    bloom_trees = [spot for spot in mirrored_in_z(BLOOM_TREES_WEST_EDGE) if can_plant(spot, "tree_bloom")]
    trunks = old_trees + palms + bloom_trees
    step = 1.0 / math.sqrt(FLOWER_DENSITY)
    tufts = []

    for zone in flower_zones(old_trees + bloom_trees, palms):
        min_x, min_z, max_x, max_z = zone.bounds
        cells = itertools.product(range(int((max_x - min_x) / step) + 1), range(int((max_z - min_z) / step) + 1))

        for column, row in cells:
            point = (min_x + (column + generator.uniform(0.1, 0.9)) * step, min_z + (row + generator.uniform(0.1, 0.9)) * step)
            dominant, accent = zone.colors(point)
            color = dominant if generator.random() < FLOWER_DOMINANT_SHARE else accent
            height = generator.uniform(*FLOWER_HEIGHTS)
            yaw = generator.uniform(0.0, math.pi)

            if zone.test(point) and zone.field_band[0] <= bed_field(point) <= zone.field_band[1] and far_from_all(point, trunks, zone.trunk_clearance):
                tufts.append((point[0], point[1], color, height, yaw))

    return tufts


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


BACKYARD_SHIFT = 4.5  # do centro da quadra para longe da fileira principal (lotes de 12 m chegam ao centro)


def house_blocks() -> list:
    """Blocks with rows of buildings (the farm block has none)."""
    return [block for block in BLOCKS if block[4]]


def backyard_spot(block: tuple) -> tuple:
    """Old tree in the middle of a block's back yards, clear of the 12 m lots: pushed away from the main row,
    and on corner blocks (two rows) away from both."""
    shifts = {"N": (0.0, BACKYARD_SHIFT), "S": (0.0, -BACKYARD_SHIFT), "W": (BACKYARD_SHIFT, 0.0), "E": (-BACKYARD_SHIFT, 0.0)}
    pushing_sides = block[4] if len(block[4]) == 2 else block[4][0]
    shift_x = sum(shifts[side][0] for side in pushing_sides)
    shift_z = sum(shifts[side][1] for side in pushing_sides)

    return (block[0] + block[1]) / 2.0 + shift_x, (block[2] + block[3]) / 2.0 + shift_z


def add_trees(scene: SceneWriter) -> None:
    """Old trees in bands and the east square grove, blooming trees on the west edge and the median, royal palms in rows."""
    old_trees = old_tree_spots()
    bloom_trees = [spot for spot in mirrored_in_z(BLOOM_TREES_WEST_EDGE) if can_plant(spot, "tree_bloom")]
    palms = palm_spots(old_trees)
    median = [(x, MEDIAN_BEDS[0][0][1] + 1.5) for x in range(-88, 89, 16) if abs(x) > MEDIAN_NOSE_X + 2.0]
    shop_rectangles = [lot_rectangle(lot) for lot in town_lots() if lot.get("shop")]
    backyards = [spot for spot in map(backyard_spot, house_blocks()) if all(rectangle_distance(rectangle, spot) > 5.0 for rectangle in shop_rectangles)]

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
    fountain_spots = [point_at(WEST_SQUARE, 8.6, angle) for angle in FOUNTAIN_BENCH_ANGLES + tuple(-angle for angle in FOUNTAIN_BENCH_ANGLES)]
    esplanade = [((x, side * (ESPLANADE_WIDTH / 2.0 - 0.6)), math.pi if side > 0 else 0.0) for side in (-1, 1) for x in (-56.0, -50.0, -18.0, -12.0)]
    cathedral = [((x, side * 15.4), 0.0 if side < 0 else math.pi) for side in (-1, 1) for x in (32.0, 44.0)]

    return {
        "fountain": [(spot, facing_yaw(spot, WEST_SQUARE)) for spot in fountain_spots],
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
    bushes = [spot for spot in ring_points(WEST_SQUARE, 12.4, 8, 22.5) + plaza_bush_spots if can_plant(spot, "bush")]

    scene.add_node("SquareProps", ".", "Node3D", groups=[NAVIGATION_SOURCE_GROUP])
    place(scene, "Chafariz", "SquareProps", "res://features/hub/props/fountain_large.tscn", (WEST_SQUARE[0], 0, WEST_SQUARE[1]))
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
    """Calçadão market on the promenade between the squares; the middle stays open toward the cathedral."""
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
    """Pine belt around the town wall and around the farm fields beyond it."""
    margin = 14.0
    far_east = FARM_FIELDS[1] + margin - 2.0
    north_south = [(x, z) for x in range(int(CITY_MIN[0]) - 10, int(far_east) + 1, 14) for z in (CITY_MIN[1] - margin, CITY_MAX[1] + margin)]
    west_east = [(x, z) for z in range(int(CITY_MIN[1]), int(CITY_MAX[1]) + 1, 14) for x in (CITY_MIN[0] - margin, CITY_MAX[0] + margin, far_east)]
    fields_clearance = (FARM_FIELDS[0] - 4.0, FARM_FIELDS[1] + 6.0, FARM_FIELDS[2] - 6.0, FARM_FIELDS[3] + 6.0)
    pines = [spot for spot in north_south + west_east if rectangle_distance(fields_clearance, spot) > 0.0]

    shadowless_script = scene.external_id("Script", "res://features/hub/shadowless_group.gd")

    scene.add_node("Backdrop", ".", "Node3D", properties={"script": f'ExtResource("{shadowless_script}")'})

    for index, (x, z) in enumerate(pines):
        place(scene, f"Pine{index:02d}", "Backdrop", f"res://art/nature/Pine_{index % 3 + 1}.gltf", (x, 0, z), rotation_y=index * 0.5, scale=1.6 + 0.2 * (index % 3))


# ---------- farm ----------

FARM_MODELS = ("farm_yard", "farm_fields")
FARMHANDS = {  # nome -> (corpo, cabelo, posição, para onde olha, animação)
    "Farmer": ("villager_male", "brown", (86.4, -15.0), (88.0, -15.0), "ual1/Idle"),
    "Milkmaid": ("villager_female", "blond", (88.0, 3.2), (88.0, 8.0), "ual1/Idle_Talking"),
    "Swineherd": ("villager_male", "grey", (90.0, 30.2), (93.0, 36.0), "ual2/Idle_FoldArms"),
}
FARM_ANIMAL_BODY = {"cows": (0.9, 1.4, 2.2), "pigs": (0.6, 0.8, 1.2)}
FARM_PEN_PROPS = {  # cercado -> (x, z, raio) de abrigo, cochos e comedouro de feno (posições de build_farm.py): o bicho não anda por cima deles
    "cows": ((90.5, 23.7, 2.5), (93.5, 23.7, 2.5), (96.5, 23.7, 2.5), (88.0, 5.6, 1.5), (85.5, 24.8, 1.6)),
    "pigs": ((94.5, 39.9, 2.0), (97.5, 39.9, 2.0), (94.0, 32.2, 1.2), (88.0, 42.2, 1.4)),
}
CARRIAGE_HORSE = "res://art/town/farm/animals/horse.gltf"
CARRIAGE_HARNESSED_HORSE = "res://art/town/farm/animals/horse_harness.gltf"  # coelheira, selim e argolas dos varais
CARRIAGE_DRIVERS = (("villager_male", "brown"), ("villager_female", "black"))  # (corpo, cabelo) de cada condutor
CARRIAGE_DRIVER_SEAT = (0.0, 0.72, 1.45)  # sem o marcador driver_seat no sidecar: borda da frente da caixa
CARRIAGE_HIP_HEIGHT = 0.45  # do quadril do condutor sentado até a origem do modelo dele
CARRIAGE_WAGONS = ("res://art/town/farm/farm_wagon.gltf", "res://art/town/farm/hay_cart.gltf")
CARRIAGE_SPEED = 1.3
CARRIAGE_CORNER_RADIUS = 6.0
# Pista das carroças pelas ruas rebaixadas, mão direita: oeste pela rua sul, norte pela rua x = -68, leste
# pela pista sul da avenida (o canteiro central não tem vão nas ruas transversais, então o laço nunca troca
# de pista), anti-horário pelo sul da ilha da rotatória e sul pela rua x = 68. Conferido com a caixa da
# carroça (2 x 7,6 m, Carriage.body_size) varrendo a rota: folga mínima 0,74 m na rotatória e 0,44 m na
# curva da esquina noroeste.
STREET_LOOP = [
    (68.0, 53.0), (-68.0, 53.0), (-68.0, -51.0), (-16.0, -51.0), (-8.0, -50.2), (0.0, -49.5), (8.0, -50.2), (16.0, -51.0), (68.0, -51.0),
]


def model_exists(model: str) -> bool:
    return (PROJECT_DIR / model.removeprefix("res://")).exists()


def add_farm(scene: SceneWriter) -> None:
    """Farmhouse, barn, the yard and the fields (build_farm.py), the people who work there and, once
    convert_farm_animals.py has run, the cows and pigs wandering in their pens."""
    scene.add_node("Farm", ".", "Node3D", groups=[NAVIGATION_SOURCE_GROUP])
    place(scene, "Farmhouse", "Farm", "res://art/town/farm/farmhouse.gltf", FARMHOUSE["position"], FARMHOUSE["rotation"])
    place(scene, "Barn", "Farm", "res://art/town/farm/barn.gltf", BARN["position"], BARN["rotation"])

    for model in FARM_MODELS:
        place(scene, model.title().replace("_", ""), "Farm", f"res://art/town/farm/{model}.gltf", (0.0, 0.0, 0.0))

    for name, (body, hair, position, target, animation) in FARMHANDS.items():
        npc(scene, name, body, hair, stand(position, facing_yaw(position, target), animation, 0.0, height=0.03))

    check_shade_trees()

    for name, (kind, variant, x, z, scale) in FARM_SHADE_TREES.items():
        place(scene, name, "Farm", plant_models(kind)[variant], (x, 0.03, z), rotation_y=x * 0.7, scale=scale)

    add_farm_animals(scene)


def spread_points(generator: random.Random, area: tuple, count: int, gap: float, trunks: tuple = ()) -> list:
    """Points inside area (x, z, width, depth) at least gap apart and half a gap off every trunk (x, z, radius)
    (rejection sampling; gives up spacing after a few tries, never the trunks)."""
    points = []

    for _ in range(count):
        candidates = [(generator.uniform(area[0], area[0] + area[2]), generator.uniform(area[1], area[1] + area[3])) for _ in range(FARM_ANIMAL_TRIES)]
        free = [point for point in candidates if all(distance(point, trunk[:2]) >= trunk[2] + gap / 2.0 for trunk in trunks)]
        spaced = [point for point in free if all(distance(point, taken) >= gap for taken in points)]
        points.append((spaced or free)[0])

    return points


def pen_trunks(pen: str) -> tuple:
    """(x, z, radius) of what the animals of a pen must walk around: the shade trees and FARM_PEN_PROPS."""
    min_x, max_x, min_z, max_z = FARM_PENS[pen]
    trunks = tuple(
        (x, z, TRUNK_RADIUS[kind] * scale)
        for kind, _variant, x, z, scale in FARM_SHADE_TREES.values()
        if min_x < x < max_x and min_z < z < max_z
    )

    return trunks + FARM_PEN_PROPS[pen]


def check_shade_trees() -> None:
    """Every shade tree stands inside a pen with its roots and its whole canopy inside the fence."""
    pens = {pen: rectangle for pen, rectangle in FARM_PENS.items()}
    problems = []

    for name, (kind, _variant, x, z, scale) in FARM_SHADE_TREES.items():
        reach = max(ROOT_CLEARANCE.get(kind, TRUNK_RADIUS[kind]), CANOPY_RADIUS[kind]) * scale
        inside = [pen for pen, (min_x, max_x, min_z, max_z) in pens.items() if min_x + reach <= x <= max_x - reach and min_z + reach <= z <= max_z - reach]

        if not inside:
            problems.append(name)

    if problems:
        raise SystemExit(f"árvores de sombra com a copa sobre a cerca ou fora dos pastos: {problems}")


def add_farm_animals(scene: SceneWriter) -> None:
    script = scene.external_id("Script", "res://features/hub/farm_animal.gd")
    generator = random.Random(FARM_ANIMAL_SEED)
    herds = [(pen, model, count, speed) for pen, (model, count, speed) in FARM_ANIMALS.items() if model_exists(model)]

    if len(herds) < len(FARM_ANIMALS):
        print("AVISO: bichos da fazenda ausentes; rode tools_src/convert_farm_animals.py no Blender")

    if herds:
        scene.add_node("FarmAnimals", ".", "Node3D")  # fora do grupo da navmesh: bicho anda, não é obstáculo fixo

    for pen, model, count, speed in herds:
        min_x, max_x, min_z, max_z = FARM_PENS[pen]
        area = (min_x + FARM_ANIMAL_MARGIN, min_z + FARM_ANIMAL_MARGIN, max_x - min_x - 2.0 * FARM_ANIMAL_MARGIN, max_z - min_z - 2.0 * FARM_ANIMAL_MARGIN)
        model_id = scene.external_id("PackedScene", model)
        trunks = pen_trunks(pen)
        spawn_points = spread_points(generator, area, count, FARM_ANIMAL_BODY[pen][2] * FARM_ANIMAL_GAP, trunks)
        trunk_text = ", ".join(f"{x:.2f}, {z:.2f}, {radius:.2f}" for x, z, radius in trunks)

        for index, (x, z) in enumerate(spawn_points):
            scene.add_node(f"{pen.title()}{index}", "FarmAnimals", "AnimatableBody3D", properties={
                "position": vector(x, 0.03, z),
                "rotation": vector(0.0, generator.uniform(-math.pi, math.pi), 0.0),
                "collision_layer": "4",
                "collision_mask": "0",
                "sync_to_physics": "false",  # o script move o corpo direto a cada quadro de física
                "script": f'ExtResource("{script}")',
                "model_scene": f'ExtResource("{model_id}")',
                "pen": f"Rect2({area[0]:.2f}, {area[1]:.2f}, {area[2]:.2f}, {area[3]:.2f})",
                "walk_speed": f"{speed}",
                "wander_seed": f"{generator.randrange(1, 1 << 30)}",
                "body_size": vector(*FARM_ANIMAL_BODY[pen]),
                "obstacles": f"PackedVector3Array({trunk_text})",
            })


def rounded_loop(corners: list, radius: float, steps: int = 4) -> list:
    """Closed polyline with every corner replaced by a short arc (quadratic curve between the two tangent points)."""
    points = []

    for index, corner in enumerate(corners):
        before, after = corners[index - 1], corners[(index + 1) % len(corners)]
        reach = min(radius, distance(before, corner) / 2.0, distance(corner, after) / 2.0)
        entry = toward(corner, before, reach)
        leave = toward(corner, after, reach)
        points += [quadratic_point(entry, corner, leave, step / steps) for step in range(steps + 1)]

    return points


def toward(origin: tuple, target: tuple, reach: float) -> tuple:
    length = max(distance(origin, target), 1e-6)

    return origin[0] + (target[0] - origin[0]) * reach / length, origin[1] + (target[1] - origin[1]) * reach / length


def quadratic_point(start: tuple, control: tuple, end: tuple, amount: float) -> tuple:
    rest = 1.0 - amount

    return tuple(rest * rest * start[axis] + 2.0 * rest * amount * control[axis] + amount * amount * end[axis] for axis in range(2))


def driver_seat(wagon: str) -> tuple:
    """Origin of the seated driver: the wagon's driver_seat marker (top of the bench) lowered to the hips."""
    seat = model_sidecar(wagon).get("markers", {}).get("driver_seat")

    if not seat:
        return CARRIAGE_DRIVER_SEAT

    return seat[0], round(seat[1] - CARRIAGE_HIP_HEIGHT, 3), seat[2]


def add_carriages(scene: SceneWriter) -> None:
    """Horse-drawn wagons rolling slowly round the street loop, half a lap apart."""
    script = scene.external_id("Script", "res://features/hub/carriage.gd")
    route = rounded_loop(STREET_LOOP, CARRIAGE_CORNER_RADIUS)
    route_text = ", ".join(f"{x:.2f}, {-STREET_DROP}, {z:.2f}" for x, z in route)
    lap = sum(distance(route[index - 1], route[index]) for index in range(len(route)))
    horse = CARRIAGE_HARNESSED_HORSE if model_exists(CARRIAGE_HARNESSED_HORSE) else CARRIAGE_HORSE
    models = [horse, *CARRIAGE_WAGONS]

    if not all(model_exists(model) for model in models):
        print("AVISO: carroças fora da cena até existirem o cavalo (convert_farm_animals.py) e as carroças (build_farm.py)")
        return

    scene.add_node("Carriages", ".", "Node3D")

    for index, (wagon, (driver_body, driver_hair)) in enumerate(zip(CARRIAGE_WAGONS, CARRIAGE_DRIVERS)):
        scene.add_node(f"Carriage{index}", "Carriages", "AnimatableBody3D", properties={
            "collision_layer": "4",
            "collision_mask": "0",
            "sync_to_physics": "false",  # o script move o corpo direto a cada quadro de física
            "script": f'ExtResource("{script}")',
            "wagon_scene": f'ExtResource("{scene.external_id("PackedScene", wagon)}")',
            "horse_scene": f'ExtResource("{scene.external_id("PackedScene", horse)}")',
            "driver_body": f'ExtResource("{scene.external_id("PackedScene", f"res://art/characters/{driver_body}.gltf")}")',
            "driver_hair_color": color(HAIR_COLORS[driver_hair]),
            "driver_seat": vector(*driver_seat(wagon)),
            "route": f"PackedVector3Array({route_text})",
            "speed": f"{CARRIAGE_SPEED}",
            "start_distance": f"{lap * index / len(CARRIAGE_WAGONS):.2f}",
        })


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
    center_x, center_z = WEST_SQUARE
    half_x, half_z = SQUARE_HALF
    # Entre o chafariz (colisão r=5.1) e o anel de postes (r=9).
    fountain_loop = ring_points(WEST_SQUARE, 7.2, 12)
    perimeter_loop = [(center_x - half_x + 2.6, center_z - half_z + 2.6), (center_x + half_x - 2.6, center_z - half_z + 2.6), (center_x + half_x - 2.6, center_z + half_z - 2.6), (center_x - half_x + 2.6, center_z + half_z - 2.6)]
    east_square_loop = [(8.0, -16.5), (63.0, -16.5), (63.0, 16.5), (8.0, 16.5)]
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
    npc(scene, "CathedralStroller", "villager_male", "brown", patrol(east_square_loop, 1.2, 2.0, "ual2/Idle_FoldArms"))
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
    add_shopkeepers(scene, town_lots())
    add_window_shoppers(scene, town_lots())
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
    scene.add_node("SettingsMenu", ".", instance=scene.external_id("PackedScene", "res://features/ui/settings_menu.tscn"))
    scene.add_node("HubAudio", ".", instance=scene.external_id("PackedScene", "res://features/hub/hub_audio.tscn"))


DAY_NIGHT_CYCLE_MINUTES = 24.0  # 12 min de dia claro + 12 de noite
START_TIME_OF_DAY = 0.18  # manhã: o sol a uns 40° a leste-sudeste, a luz dos prints de antes
SUN_SHADOW_DISTANCE = 60.0  # style bible: sombra do sol até ~60 m (era 110 m: o dobro de mapa no passe de sombra)
SUN_SHADOW_NEAR_SPLIT = 0.25  # primeira cascata nos 15 m mais perto da câmera
WORLD_SEED = 1  # semente do mundo da cidade inicial (eventos do céu); o servidor mandará a dele


def add_environment(scene: SceneWriter) -> None:
    sky_shader = scene.external_id("Shader", "res://art/shaders/sky.gdshader")
    day_night_script = scene.external_id("Script", "res://features/sky/day_night_cycle.gd")

    scene.add_sub_resource(f'''
[sub_resource type="ShaderMaterial" id="sky_material"]
shader = ExtResource("{sky_shader}")''')
    scene.add_sub_resource('''
[sub_resource type="Sky" id="sky"]
sky_material = SubResource("sky_material")
process_mode = 2
radiance_size = 2''')
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
fog_sky_affect = 0.2
adjustment_enabled = true
adjustment_saturation = 1.08''')
    scene.add_node("WorldEnvironment", ".", "WorldEnvironment", properties={"environment": 'SubResource("environment")'})
    scene.add_node("Sun", ".", "DirectionalLight3D", properties={
        "rotation": vector(-0.78, 0.55 + math.radians(40.0), 0.0),
        "light_color": "Color(1, 0.902, 0.769, 1)",
        "light_energy": "1.35",
        "shadow_enabled": "true",
        "shadow_blur": "1.5",
        "directional_shadow_mode": "1",  # 2 cascatas (style bible: 2–3; o Godot só tem 2 ou 4)
        "directional_shadow_split_1": f"{SUN_SHADOW_NEAR_SPLIT}",
        "directional_shadow_max_distance": f"{SUN_SHADOW_DISTANCE}",
        "directional_shadow_fade_start": "0.85",
    })
    scene.add_node("DayNight", ".", "Node", properties={
        "script": f'ExtResource("{day_night_script}")',
        "sun": 'NodePath("../Sun")',
        "world_environment": 'NodePath("../WorldEnvironment")',
        "cycle_minutes": f"{DAY_NIGHT_CYCLE_MINUTES}",
        "start_time_of_day": f"{START_TIME_OF_DAY}",
        "world_seed": f"{WORLD_SEED}",
    })


def add_mula(scene: SceneWriter) -> None:
    """The Mula sem cabeça (features/mobs/mula_sem_cabeca.tscn) standing in the meadow beyond the farm gate."""
    place(scene, "MulaSemCabeca", ".", "res://features/mobs/mula_sem_cabeca.tscn", grounded(*MULA["position"]), MULA["rotation"])


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
    add_farm(scene)
    add_mula(scene)
    add_carriages(scene)
    add_distance_fades(scene)
    add_player_and_cameras(scene)

    return scene.render()


DISTANCE_FADES = {  # nó -> (grupo da cena, prefixos dos filhos, alcance em m): peças pequenas somem de longe com fade
    "GrassTufts": ("Trees", ("Grass",), 45.0),
    "SquareSmallProps": ("SquareProps", ("Bench", "FlowerBush", "Planter"), 70.0),
    "MarketProps": ("Market", (), 70.0),
    "FarmFieldCrops": ("Farm/FarmFields", ("Crops",), 80.0),
}


def add_distance_fades(scene: SceneWriter) -> None:
    """One DistanceFade (features/hub/distance_fade.gd) per group of small pieces: grass tufts, benches and pots,
    market props and the crops of each farm plot (build_farm.py keeps each plot's plants as Crops<n> meshes)."""
    script = scene.external_id("Script", "res://features/hub/distance_fade.gd")

    scene.add_node("DistanceFades", ".", "Node")

    for name, (group, prefixes, range_end) in DISTANCE_FADES.items():
        prefix_text = ", ".join(f'"{prefix}"' for prefix in prefixes)
        scene.add_node(name, "DistanceFades", "Node", properties={
            "script": f'ExtResource("{script}")',
            "target": f'NodePath("../../{group}")',
            "child_prefixes": f"PackedStringArray({prefix_text})",
            "range_end": f"{range_end}",
        })


SHOP_SHOTS_PATH = PROJECT_DIR / "tests" / "shots" / "shop_shots.tscn"
SHOP_SHOT_VIEWS = {  # sufixo -> (olho, alvo) em coordenadas do lote: x ao longo da fachada, z > 0 = rua, z < 0 = dentro
    "Front": ((6.0, 1.6, 16.0), (0.0, 4.0, 0.0)),
    "Door": ((0.0, 1.6, 4.0), (0.0, 1.8, -10.0)),
    "Inside": ((0.0, 1.6, -1.2), (0.0, 1.4, -12.0)),
    "Left": ((2.0, 1.6, -9.0), (-12.0, 1.4, -11.0)),
    "Right": ((-2.0, 1.6, -9.0), (12.0, 1.4, -11.0)),
    "Back": ((0.0, 1.6, -9.0), (0.0, 1.5, -19.0)),
    "Out": ((0.0, 1.6, -15.0), (0.0, 1.6, 0.0)),
    "Top": ((0.0, 30.0, -9.5), (0.0, 0.0, -9.6)),
}


def build_shop_shots() -> str:
    """Shot scene with the same views of every shop, at the player's eye height (tools_src/shot.sh <Type><View>)."""
    scene = SceneWriter()
    capture = scene.external_id("Script", "res://tests/shots/shot_capture.gd")
    shops = [lot for lot in town_lots() if lot.get("shop")]

    scene.add_node("ShopShots", None, "Node3D")
    scene.add_node("Hub", ".", instance=scene.external_id("PackedScene", "res://features/hub/hub.tscn"))
    scene.add_node("ShotCapture", ".", "Node", properties={"script": f'ExtResource("{capture}")', "seconds_before_capture": "3.0"})

    for lot, (view, (eye, target)) in itertools.product(shops, SHOP_SHOT_VIEWS.items()):
        door_x = model_sidecar(lot["model"]).get("doors", [{"x": 0.0}])[0]["x"] if view in ("Door", "Inside") else 0.0
        world_eye = lot_to_world(lot, (eye[0] + door_x, eye[1], eye[2]))
        world_target = lot_to_world(lot, (target[0] + door_x, target[1], target[2]))
        scene.add_node(f"{lot['shop'].title()}{view}", ".", "Camera3D", properties={"position": vector(*world_eye), "rotation": look_rotation(world_eye, world_target), "fov": "75.0", "far": "400.0"})

    return scene.render()


if __name__ == "__main__":
    SHOP_SHOTS_PATH.write_text(build_shop_shots(), encoding="utf-8", newline="\n")
    if not NAVMESH_PATH.exists():  # placeholder until tools_src/bake_hub_navmesh.gd bakes the real one
        NAVMESH_PATH.write_text('[gd_resource type="NavigationMesh" format=3]\n\n[resource]\n', encoding="utf-8", newline="\n")

    OUTPUT_PATH.write_text(build_hub_scene(), encoding="utf-8", newline="\n")
    print(f"WROTE {OUTPUT_PATH}")
