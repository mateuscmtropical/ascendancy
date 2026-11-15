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
CATHEDRAL_FACADE_X = 18.0
CATHEDRAL_FLOOR = 1.05
COREO_POSITION = (-50.0, -12.0)
PLAYER_SPAWN = (-42.4, -12.0)  # pé da escada do coreto, olhando para a catedral (+X)
PATH_WIDTH = 4.0
PLANTER_SOIL_HEIGHT = 0.42
SHADE_TREE_SCALE = 1.45
TREE_BED_CLEARANCE = 1.2  # tronco a pelo menos isto do meio-fio
GRASS_SEED = 77
GRASS_TUFTS_PER_SQUARE = 110

RING_RADII = (18.5, 21.5)  # passeio em anel ao redor do chafariz
PLAZA_RADIUS = 10.0
COREO_PLAZA_RADIUS = 7.5
RONDEL_RADIUS = 3.4
RONDEL_ALONG = 0.78  # fração do meio-diagonal onde fica cada rondel
STREET_DROP = 0.12  # asfalto fica abaixo das calçadas (meio-fio)
CURB_WIDTH = 0.22  # meio-fio de pedra dos canteiros
CURB_HEIGHT = 0.16
LAWN_EDGE_HEIGHT = 0.12  # a grama começa abaixo do topo do meio-fio e sobe para o meio do canteiro
LAWN_SWELL_HEIGHT = 0.26
LAWN_SWELL_DISTANCE = 4.5
ROUNDABOUT_RADIUS = 9.0
ROUNDABOUT_LAWN_RADII = (2.7, 6.0)  # canteiro em anel entre a fonte pequena e o passeio
MEDIAN_BEDS = [((CITY_MIN[0] + 4.0, MEDIAN_Z[0] + 0.7), (ROUNDABOUT[0] - 12.0, MEDIAN_Z[1] - 2.3)), ((ROUNDABOUT[0] + 12.0, MEDIAN_Z[0] + 0.7), (CITY_MAX[0] - 4.0, MEDIAN_Z[1] - 2.3))]
LAWN_RECTS = {  # canteiros = retângulo menos os caminhos de SQUARE_PATHS
    "GetulioVargas": ((GETULIO_VARGAS[0] - SQUARE_HALF[0] + PATH_WIDTH, -SQUARE_HALF[1] + PATH_WIDTH), (GETULIO_VARGAS[0] + SQUARE_HALF[0] - PATH_WIDTH, SQUARE_HALF[1] - PATH_WIDTH)),
    "SaoJose": ((SAO_JOSE[0] - SQUARE_HALF[0] + PATH_WIDTH, -SQUARE_HALF[1] + PATH_WIDTH), (SAO_JOSE[0] + SQUARE_HALF[0] - PATH_WIDTH, SQUARE_HALF[1] - PATH_WIDTH)),
}


def rondel_centers() -> list:
    """Small round widenings where each diagonal of Getúlio Vargas crosses the outer half of its run."""
    center_x, center_z = GETULIO_VARGAS
    reach = (SQUARE_HALF[0] - 2.0) * RONDEL_ALONG, (SQUARE_HALF[1] - 2.0) * RONDEL_ALONG

    return [(center_x + sign_x * reach[0], center_z + sign_z * reach[1]) for sign_x in (-1, 1) for sign_z in (-1, 1)]


def square_paths() -> list:
    """Paved shapes cut out of the lawns, Godot (x, z): ("disc", center, radius), ("ring", center, inner, outer), ("strip", start, end, width)."""
    center_x, center_z = GETULIO_VARGAS
    half_x, half_z = SQUARE_HALF
    sao_jose_x = SAO_JOSE[0]

    return [
        ("disc", GETULIO_VARGAS, PLAZA_RADIUS),
        ("ring", GETULIO_VARGAS, *RING_RADII),
        ("disc", COREO_POSITION, COREO_PLAZA_RADIUS),
        ("strip", (center_x - half_x, center_z), (center_x + half_x, center_z), PATH_WIDTH),
        ("strip", (center_x, center_z - half_z), (center_x, center_z + half_z), PATH_WIDTH),
        ("strip", (center_x - half_x + 2, center_z - half_z + 2), (center_x + half_x - 2, center_z + half_z - 2), 3.5),
        ("strip", (center_x - half_x + 2, center_z + half_z - 2), (center_x + half_x - 2, center_z - half_z + 2), 3.5),
        ("strip", (sao_jose_x - half_x, 0.0), (CATHEDRAL_FACADE_X, 0.0), 34.0),  # adro
        ("strip", (CATHEDRAL_FACADE_X, 0.0), (sao_jose_x + half_x, 0.0), 29.0),  # volta da catedral
        ("strip", (sao_jose_x, -half_z), (sao_jose_x, half_z), 3.0),
        ("strip", (sao_jose_x - half_x, -31.0), (sao_jose_x + half_x, -31.0), 3.0),
        ("strip", (sao_jose_x - half_x, 31.0), (sao_jose_x + half_x, 31.0), 3.0),
        *[("disc", rondel, RONDEL_RADIUS) for rondel in rondel_centers()],
    ]


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

    return radial - rest[0] if kind == "disc" else abs(radial - (rest[0] + rest[1]) / 2.0) - (rest[1] - rest[0]) / 2.0


SQUARE_PATHS = square_paths()


def inside_distance(point: tuple, minimum: tuple, maximum: tuple) -> float:
    """Distance from a point to the nearest edge of a rectangle (negative outside)."""
    return min(point[0] - minimum[0], maximum[0] - point[0], point[1] - minimum[1], maximum[1] - point[1])


def square_edge_distance(point: tuple) -> float:
    """How far inside the lawn rectangle of a square the point is (negative outside both)."""
    return max(inside_distance(point, minimum, maximum) for minimum, maximum in LAWN_RECTS.values())


def bed_field(point: tuple) -> float:
    """Signed distance into the nearest planted bed (positive = on a bed, value = distance to its curb)."""
    square_bed = min(square_edge_distance(point), min(path_distance(point, path) for path in SQUARE_PATHS))
    roundabout_radial = math.hypot(point[0] - ROUNDABOUT[0], point[1] - ROUNDABOUT[1])
    roundabout_bed = min(ROUNDABOUT_LAWN_RADII[1] - roundabout_radial, roundabout_radial - ROUNDABOUT_LAWN_RADII[0])
    median_bed = max(inside_distance(point, minimum, maximum) for minimum, maximum in MEDIAN_BEDS)

    return max(square_bed, roundabout_bed, median_bed)


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
    "palm": ("cylinder", 0.32, 3.0),
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


def add_cathedral_lights(scene: SceneWriter) -> None:
    """Warm lamps along the nave and a spot on the altar (the stained glass glows on its own)."""
    nave_lights = [CATHEDRAL_FACADE_X + offset for offset in (6.0, 14.0, 22.0, 30.0)]
    altar = (CATHEDRAL_FACADE_X + 32.6, CATHEDRAL_FLOOR + 6.0, 0.0)

    scene.add_node("CathedralLights", ".", "Node3D")

    for index, light_x in enumerate(nave_lights):
        scene.add_node(f"NaveLight{index}", "CathedralLights", "OmniLight3D", properties={
            "position": vector(light_x, CATHEDRAL_FLOOR + 9.0, 0.0),
            "light_color": "Color(1, 0.85, 0.62, 1)",
            "light_energy": "1.6",
            "omni_range": "13.0",
            "distance_fade_enabled": "true",
            "distance_fade_begin": "60.0",
        })

    scene.add_node("AltarLight", "CathedralLights", "SpotLight3D", properties={
        "position": vector(*altar),
        "rotation": vector(-math.pi / 2.0, 0.0, 0.0),
        "light_color": "Color(1, 0.9, 0.7, 1)",
        "light_energy": "3.0",
        "spot_range": "9.0",
        "spot_angle": "35.0",
    })


# ---------- squares ----------

def ring_points(center: tuple, radius: float, count: int, start_degrees: float = 0.0) -> list:
    return [(center[0] + radius * math.cos(math.radians(start_degrees + 360.0 * index / count)), center[1] + radius * math.sin(math.radians(start_degrees + 360.0 * index / count))) for index in range(count)]


def add_lamps(scene: SceneWriter) -> list:
    center_x, center_z = GETULIO_VARGAS
    perimeter_offsets = [-36.0, -18.0, 0.0, 18.0, 36.0]
    fountain_ring = ring_points(GETULIO_VARGAS, 9.0, 8, 22.5)
    getulio_vargas_edges = [(center_x + side * (SQUARE_HALF[0] - 0.6), center_z + offset) for side in (-1, 1) for offset in perimeter_offsets]
    getulio_vargas_ends = [(center_x + offset, center_z + side * (SQUARE_HALF[1] - 0.6)) for side in (-1, 1) for offset in (-18.0, 0.0, 18.0)]
    forecourt = [(6.0, -15.0), (6.0, 15.0), (CATHEDRAL_FACADE_X - 4.5, -12.0), (CATHEDRAL_FACADE_X - 4.5, 12.0)]
    sao_jose_ring = [(x, side * 14.0) for side in (-1, 1) for x in (26.0, 38.0, 50.0, 62.0)]
    median = [(x, sum(MEDIAN_Z) / 2.0) for x in range(-96, 97, 16) if abs(x) > 14]
    roundabout = ring_points(ROUNDABOUT, 7.5, 6, 30.0)
    positions = fountain_ring + getulio_vargas_edges + getulio_vargas_ends + forecourt + sao_jose_ring + median + roundabout

    scene.add_node("Lamps", ".", "Node3D", groups=[NAVIGATION_SOURCE_GROUP])

    for index, (x, z) in enumerate(positions):
        place(scene, f"Lamp{index:02d}", "Lamps", "res://features/hub/props/lamp_post.tscn", grounded(x, z))

    return positions


def mirrored_in_quadrants(center: tuple, offsets: list) -> list:
    signs = [(1, 1), (1, -1), (-1, 1), (-1, -1)]

    return [(center[0] + sign_x * dx, center[1] + sign_z * dz) for sign_x, sign_z in signs for dx, dz in offsets]


def clear_of_coreto(spot: tuple) -> bool:
    return math.hypot(spot[0] - COREO_POSITION[0], spot[1] - COREO_POSITION[1]) > 9.5


def grass_tuft_spots() -> list:
    """Seeded scatter of grass tufts over the lawns of both squares, clear of curbs and hedges."""
    generator = random.Random(GRASS_SEED)
    spots = []

    for minimum, maximum in LAWN_RECTS.values():
        candidates = [(generator.uniform(minimum[0], maximum[0]), generator.uniform(minimum[1], maximum[1])) for _ in range(GRASS_TUFTS_PER_SQUARE * 3)]
        spots += [spot for spot in candidates if on_lawn(spot, 0.6) and square_edge_distance(spot) > 2.0][:GRASS_TUFTS_PER_SQUARE]

    return spots


def palm_spots() -> list:
    """Royal palms: a ring around the chafariz plaza, pairs along the long axis of Getúlio Vargas and the edge of the forecourt."""
    center_x, center_z = GETULIO_VARGAS
    around_chafariz = ring_points(GETULIO_VARGAS, 14.6, 8, 22.5)
    along_axis = [(center_x + side * 4.6, center_z + sign * offset) for side in (-1, 1) for sign in (-1, 1) for offset in (26.0, 34.0, 42.0)]
    forecourt = [(8.5, sign * offset) for sign in (-1, 1) for offset in (20.0, 26.0)]

    return [spot for spot in around_chafariz + along_axis + forecourt if on_lawn(spot, 0.7)]


def add_trees(scene: SceneWriter) -> None:
    """Shade trees on the lawns (dense in São José, as in the real square), the median and behind the houses."""
    center_x, center_z = GETULIO_VARGAS
    quadrant_spots = [(6.0, 30.0), (8.0, 41.0), (16.0, 38.0), (20.0, 14.0), (24.0, 24.0), (24.0, 8.0)]
    getulio_vargas = [spot for spot in mirrored_in_quadrants(GETULIO_VARGAS, quadrant_spots) if clear_of_coreto(spot)]
    sao_jose = [(x, side * dz) for side in (-1, 1) for x in (12.0, 21.0, 30.0, 39.0, 48.0, 57.0) for dz in (21.0, 39.0)]
    sao_jose_extra = [(x, side * 30.0) for side in (-1, 1) for x in (16.5, 34.5, 52.5)]
    median = [(x, sum(MEDIAN_Z) / 2.0) for x in range(-88, 89, 16) if abs(x) > 14]
    backyards = [((block[0] + block[1]) / 2.0, (block[2] + block[3]) / 2.0) for block in BLOCKS]
    # Troncos e raízes só dentro dos canteiros, nunca na calçada.
    getulio_vargas = [spot for spot in getulio_vargas if on_lawn(spot, TREE_BED_CLEARANCE)]
    sao_jose = [spot for spot in sao_jose + sao_jose_extra if on_lawn(spot, TREE_BED_CLEARANCE)]
    lawn_trees = getulio_vargas + sao_jose

    scene.add_node("Trees", ".", "Node3D")

    for index, (x, z) in enumerate(lawn_trees + median):
        is_shade_tree = len(getulio_vargas) <= index < len(lawn_trees)  # São José: copas grandes e fechadas
        scale = (0.85 + 0.08 * (index % 4)) * (SHADE_TREE_SCALE if is_shade_tree else 1.0)
        place(scene, f"Tree{index:03d}", "Trees", f"res://art/nature/CommonTree_{index % 5 + 1}.gltf", grounded(x, z), rotation_y=index * 1.3, scale=scale)

    for index, (x, z) in enumerate(grass_tuft_spots()):
        place(scene, f"Grass{index:03d}", "Trees", "res://art/nature/Grass_Common_Short.gltf", grounded(x, z), rotation_y=index * 0.7, scale=0.4 + 0.08 * (index % 3))

    for index, (x, z) in enumerate(palm_spots()):
        place(scene, f"Palm{index:02d}", "Trees", "res://art/town/palm.gltf", grounded(x, z), rotation_y=index * 2.1, scale=0.9 + 0.07 * (index % 3))

    for index, (x, z) in enumerate(backyards):
        place(scene, f"BackyardTree{index:02d}", "Trees", f"res://art/nature/CommonTree_{index % 5 + 1}.gltf", (x, 0, z), rotation_y=index * 0.9, scale=1.1)


def add_square_props(scene: SceneWriter) -> list:
    """Chafariz, roundabout fountain, benches (returned for the sitters) and red flower beds."""
    center_x, center_z = GETULIO_VARGAS
    circle_benches = [((center_x + 8.6 * math.cos(math.radians(angle)), center_z + 8.6 * math.sin(math.radians(angle))), facing_yaw((math.cos(math.radians(angle)), math.sin(math.radians(angle))), (0.0, 0.0))) for angle in (45, 135, 225, 315)]
    axis_benches = [((center_x + offset, center_z + side * 2.6), math.pi if side > 0 else 0.0) for side in (-1, 1) for offset in (-20.0, -14.0, 14.0, 20.0)]
    cathedral_benches = [((x, side * 15.4), 0.0 if side < 0 else math.pi) for side in (-1, 1) for x in (32.0, 44.0)]
    benches = circle_benches + axis_benches + cathedral_benches
    getulio_vargas_beds = [spot for spot in mirrored_in_quadrants(GETULIO_VARGAS, [(8.0, 24.0), (17.0, 8.0)]) if clear_of_coreto(spot)]
    flower_beds = getulio_vargas_beds
    forecourt_planters = [(10.5, -12.0), (10.5, 12.0), (10.5, -6.0), (10.5, 6.0)]
    getulio_vargas_bushes = ring_points(GETULIO_VARGAS, 11.5, 8, 22.5)

    scene.add_node("SquareProps", ".", "Node3D", groups=[NAVIGATION_SOURCE_GROUP])
    place(scene, "Chafariz", "SquareProps", "res://features/hub/props/fountain_large.tscn", (center_x, 0, center_z))
    place(scene, "RoundaboutFountain", "SquareProps", "res://features/hub/props/fountain_small.tscn", (ROUNDABOUT[0], 0, ROUNDABOUT[1]))

    for index, ((x, z), rotation_y) in enumerate(benches):
        place(scene, f"Bench{index:02d}", "SquareProps", "res://art/props/Bench.gltf", grounded(x, z), rotation_y)

    for index, (x, z) in enumerate(flower_beds):
        place(scene, f"Flowers{index:02d}", "SquareProps", f"res://art/nature/Flower_{3 + index % 2}_Group.gltf", grounded(x, z), rotation_y=index * 1.1, scale=1.3)

    for index, (x, z) in enumerate(forecourt_planters):
        place(scene, f"Planter{index:02d}", "SquareProps", "res://art/town/planter.gltf", (x, 0, z))
        place(scene, f"PlanterFlowers{index:02d}", "SquareProps", f"res://art/nature/Flower_{3 + index % 2}_Group.gltf", (x, PLANTER_SOIL_HEIGHT, z), rotation_y=index * 1.7)

    for index, (x, z) in enumerate(getulio_vargas_bushes):
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


def add_townsfolk(scene: SceneWriter, benches: list) -> None:
    center_x, center_z = GETULIO_VARGAS
    half_x, half_z = SQUARE_HALF
    # Entre o chafariz (colisão r=5.1) e o anel de postes (r=9).
    fountain_loop = ring_points(GETULIO_VARGAS, 7.2, 12)
    perimeter_loop = [(center_x - half_x + 2.6, center_z - half_z + 2.6), (center_x + half_x - 2.6, center_z - half_z + 2.6), (center_x + half_x - 2.6, center_z + half_z - 2.6), (center_x - half_x + 2.6, center_z + half_z - 2.6)]
    sao_jose_loop = [(8.0, -16.5), (63.0, -16.5), (63.0, 16.5), (8.0, 16.5)]
    worshipper_route = [(8.0, 5.0), (CATHEDRAL_FACADE_X - 4.0, 0.0), (CATHEDRAL_FACADE_X + 26.0, 0.0)]
    west_bench_seat, west_bench_facing = sitter(benches[0])
    east_bench_seat, east_bench_facing = sitter(benches[2])
    cathedral_bench_seat, cathedral_bench_facing = sitter(benches[12])
    median_z = sum(MEDIAN_Z) / 2.0

    scene.add_node("Navigation", ".", "NavigationRegion3D", properties={"navigation_mesh": f'ExtResource("{scene.external_id("NavigationMesh", "res://features/hub/hub_navmesh.tres")}")'})
    scene.add_node("Townsfolk", ".", "Node3D")
    npc(scene, "FountainWalker", "villager_male", "dark", patrol(fountain_loop, 1.2, 0.0, "ual1/Idle"))
    npc(scene, "FountainWalkerReverse", "villager_female", "auburn", patrol(list(reversed(fountain_loop[6:] + fountain_loop[:6])), 1.1, 0.0, "ual1/Idle"))
    npc(scene, "SquareWalker", "adventurer_female", "blond", patrol(perimeter_loop, 1.4, 0.0, "ual1/Idle"))
    npc(scene, "SquareWalkerReverse", "villager_male", "grey", patrol(list(reversed(perimeter_loop[2:] + perimeter_loop[:2])), 1.2, 0.0, "ual1/Idle"))
    npc(scene, "CalcadaoWalker", "villager_female", "brown", patrol([(0.8, -22.0), (0.8, 22.0)], 1.1, 4.0, "ual1/Idle_Talking"))
    npc(scene, "Worshipper", "villager_female", "black", patrol(worshipper_route, 1.0, 6.0, "ual1/Idle"))
    npc(scene, "CathedralStroller", "villager_male", "brown", patrol(sao_jose_loop, 1.2, 2.0, "ual2/Idle_FoldArms"))
    npc(scene, "MedianWalkerWest", "adventurer_male", "black", patrol([(-92.0, median_z + 2.0), (-14.0, median_z + 2.0)], 1.4, 3.0, "ual2/Idle_FoldArms"))
    npc(scene, "MedianWalkerEast", "villager_female", "grey", patrol([(14.0, median_z + 2.0), (92.0, median_z + 2.0)], 1.2, 3.0, "ual1/Idle"))
    npc(scene, "SidewalkWalker", "villager_male", "auburn", patrol([(-60.0, -67.5), (60.0, -67.5)], 1.3, 5.0, "ual1/Idle"))
    npc(scene, "Merchant", "villager_male", "auburn", stand((-1.1, -36.0), math.pi / 2.0, "ual1/Idle_Talking", 1.1))
    npc(scene, "Shopper", "villager_female", "blond", stand((0.4, -35.4), -math.pi / 2.0 - 0.3, "ual2/Idle_FoldArms", 0.4))
    npc(scene, "TalkerA", "villager_male", "brown", stand((center_x + 12.0, center_z + 9.0), 2.28, "ual1/Idle_Talking", 0.0))
    npc(scene, "TalkerB", "villager_female", "blond", stand((center_x + 13.4, center_z + 7.8), -0.86, "ual2/Idle_FoldArms", 0.7))
    npc(scene, "SittingWest", "villager_female", "grey", stand(west_bench_seat, west_bench_facing, "ual1/Sitting_Idle", 0.3))
    npc(scene, "SittingEast", "villager_male", "black", stand(east_bench_seat, east_bench_facing, "ual1/Sitting_Talking", 0.0))
    npc(scene, "SittingCathedral", "adventurer_male", "brown", stand(cathedral_bench_seat, cathedral_bench_facing, "ual1/Sitting_Talking", 0.5))
    npc(scene, "Bard", "adventurer_female", "auburn", stand((COREO_POSITION[0], COREO_POSITION[1]), math.pi / 2.0, "ual1/Idle_Talking", 0.2, height=1.2))
    npc(scene, "Guard", "adventurer_female", "dark", stand((CATHEDRAL_FACADE_X - 4.2, -6.5), -math.pi / 2.0, "ual2/Idle_FoldArms", 0.0))
    npc(scene, "Priest", "villager_male", "grey", stand((CATHEDRAL_FACADE_X + 33.6, 0.0), -math.pi / 2.0, "ual1/Idle", 0.0, height=CATHEDRAL_FLOOR + 0.9))


# ---------- player and cameras ----------

def add_player_and_cameras(scene: SceneWriter) -> None:
    spawn_x, spawn_z = PLAYER_SPAWN
    select_eye = (spawn_x + 4.4, 1.35, spawn_z - 1.2)
    tour = [
        ((-90, 28, -30), (18, 8, 0)),
        ((-24, 2.6, 9), (-34, 2.2, 0)),
        ((-40, 3.2, -22), (-50, 2.6, -12)),
        ((0, 2.2, 44), (0, 2.0, -20)),
        ((2, 1.8, 7), (18, 18, 0)),
        ((CATHEDRAL_FACADE_X + 4, 2.8, 0), (CATHEDRAL_FACADE_X + 34, 5.0, 0)),
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
