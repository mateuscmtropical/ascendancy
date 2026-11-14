"""Write features/hub/hub.tscn: the fixed starting plaza (cathedral, fountains, avenues, houses, market, NPCs).

Layout in Godot coordinates (Y up). Plaza center = (0, 0, 0); cathedral to the north (-Z), main street to the south (+Z).
Every model's front faces +Z locally, so rotation_y turns it toward the plaza.

Usage: python tools_src/build_hub_scene.py
"""

import math
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
OUTPUT_PATH = PROJECT_DIR / "features" / "hub" / "hub.tscn"
NAVMESH_PATH = PROJECT_DIR / "features" / "hub" / "hub_navmesh.tres"
NAVIGATION_SOURCE_GROUP = "navigation_source"  # nós cujas malhas/colisões entram na navmesh (bake_hub_navmesh.gd)

HOUSE_SIZES = {  # name -> (width along facade, depth)
    "house_stone_tall": (6, 8),
    "house_narrow_three": (6, 8),
    "house_plaster_wide": (8, 8),
    "house_shop": (8, 10),
    "house_cottage": (6, 6),
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
        self.nodes = []

    def external_id(self, resource_type: str, path: str) -> str:
        if path not in self.external:
            self.external[path] = (resource_type, f"{len(self.external) + 1}_ext")

        return self.external[path][1]

    def add_sub_resource(self, text: str) -> None:
        self.sub_resources.append(text.strip() + "\n")

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


def place(scene: SceneWriter, name: str, parent: str, scene_path: str, position: tuple, rotation_y: float = 0.0, scale: float = 1.0) -> None:
    properties = {"position": vector(*position)}

    if rotation_y:
        properties["rotation"] = vector(0.0, rotation_y, 0.0)

    if scale != 1.0:
        properties["scale"] = vector(scale, scale, scale)

    scene.add_node(name, parent, instance=scene.external_id("PackedScene", scene_path), properties=properties)


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
        "rotation": vector(-0.78, 0.55, 0.0),
        "light_color": "Color(1, 0.902, 0.769, 1)",
        "light_energy": "1.35",
        "shadow_enabled": "true",
        "shadow_blur": "1.5",
        "directional_shadow_mode": "1",
        "directional_shadow_max_distance": "90.0",
    })


def add_ground(scene: SceneWriter) -> None:
    textures = {name: scene.external_id("Texture2D", f"res://art/town/textures/T_UnevenBrick_{name}.png") for name in ("BaseColor", "Normal", "Roughness")}
    scene.add_sub_resource(f'''
[sub_resource type="StandardMaterial3D" id="paving_material"]
albedo_color = Color(0.9, 0.86, 0.82, 1)
albedo_texture = ExtResource("{textures["BaseColor"]}")
roughness_texture = ExtResource("{textures["Roughness"]}")
normal_enabled = true
normal_scale = 0.8
normal_texture = ExtResource("{textures["Normal"]}")
uv1_scale = Vector3(0.38, 0.38, 0.38)
uv1_triplanar = true
uv1_world_triplanar = true''')
    scene.add_sub_resource('''
[sub_resource type="PlaneMesh" id="paving_mesh"]
material = SubResource("paving_material")
size = Vector2(96, 110)''')
    scene.add_sub_resource('''
[sub_resource type="FastNoiseLite" id="grass_noise"]
frequency = 0.05''')
    scene.add_sub_resource('''
[sub_resource type="NoiseTexture2D" id="grass_variation"]
seamless = true
noise = SubResource("grass_noise")''')
    scene.add_sub_resource('''
[sub_resource type="StandardMaterial3D" id="grass_material"]
albedo_color = Color(0.45, 0.66, 0.32, 1)
albedo_texture = SubResource("grass_variation")
roughness = 1.0
uv1_scale = Vector3(30, 30, 30)''')
    scene.add_sub_resource('''
[sub_resource type="PlaneMesh" id="grass_mesh"]
material = SubResource("grass_material")
size = Vector2(400, 400)''')
    scene.add_sub_resource('''
[sub_resource type="WorldBoundaryShape3D" id="ground_shape"]''')
    scene.add_node("Ground", ".", "StaticBody3D", groups=[NAVIGATION_SOURCE_GROUP])
    scene.add_node("Collision", "Ground", "CollisionShape3D", properties={"shape": 'SubResource("ground_shape")'})
    scene.add_node("Paving", "Ground", "MeshInstance3D", properties={"position": vector(0, 0.0, -8.0), "mesh": 'SubResource("paving_mesh")'})
    scene.add_node("Grass", "Ground", "MeshInstance3D", properties={"position": vector(0, -0.03, 0), "mesh": 'SubResource("grass_mesh")'})


def add_boundary(scene: SceneWriter) -> None:
    walls = [("North", (0, 3, -84), (110, 6, 1)), ("South", (0, 3, 46), (110, 6, 1)), ("West", (-46, 3, -19), (1, 6, 130)), ("East", (46, 3, -19), (1, 6, 130))]

    scene.add_node("Boundary", ".", "StaticBody3D", groups=[NAVIGATION_SOURCE_GROUP])

    for wall_name, center, size in walls:
        shape_id = f"boundary_{wall_name.lower()}"
        scene.add_sub_resource(f'''
[sub_resource type="BoxShape3D" id="{shape_id}"]
size = {vector(*size)}''')
        scene.add_node(wall_name, "Boundary", "CollisionShape3D", properties={"position": vector(*center), "shape": f'SubResource("{shape_id}")'})


def house_row(names: list, start: float, axis: str, facade: float, rotation_y: float, outward_sign: float) -> list:
    """Lay houses side by side along an axis; returns (name, position, rotation)."""
    placements = []
    cursor = start

    for house_name in names:
        width, depth = HOUSE_SIZES[house_name]
        along = cursor + width / 2.0
        across = facade + outward_sign * depth / 2.0
        position = (across, 0.0, along) if axis == "z" else (along, 0.0, across)
        placements.append((house_name, position, rotation_y))
        cursor += width + 1.0

    return placements


def add_buildings(scene: SceneWriter) -> None:
    rows = [
        house_row(["house_narrow_three", "house_stone_tall", "house_plaster_wide", "house_cottage", "house_shop", "house_narrow_three", "house_stone_tall"], -26.0, "z", -30.0, math.pi / 2.0, -1.0),
        house_row(["house_stone_tall", "house_shop", "house_narrow_three", "house_cottage", "house_plaster_wide", "house_stone_tall", "house_narrow_three"], -26.0, "z", 30.0, -math.pi / 2.0, 1.0),
        house_row(["house_plaster_wide", "house_narrow_three", "house_stone_tall"], -28.5, "x", 36.0, math.pi, 1.0),
        house_row(["house_cottage", "house_shop", "house_narrow_three"], 5.5, "x", 36.0, math.pi, 1.0),
        house_row(["house_plaster_wide"], -29.0, "x", -31.0, 0.0, -1.0),
        house_row(["house_shop"], 20.0, "x", -31.0, 0.0, -1.0),
    ]
    placements = [placement for row in rows for placement in row]

    scene.add_node("Buildings", ".", "Node3D", groups=[NAVIGATION_SOURCE_GROUP])
    place(scene, "Cathedral", "Buildings", "res://art/town/cathedral.gltf", (0, 0, -34))

    for index, (house_name, position, rotation_y) in enumerate(placements):
        place(scene, f"House{index:02d}", "Buildings", f"res://art/town/{house_name}.gltf", position, rotation_y)


def add_plaza_props(scene: SceneWriter) -> None:
    lamp_ring = [(9.0 * math.cos(math.radians(22.5 + 45 * index)), 0, 9.0 * math.sin(math.radians(22.5 + 45 * index))) for index in range(8)]
    lamp_avenue = [(side * 17.0, 0, z) for side in (-1, 1) for z in (-22, -6, 10, 26)]
    lamp_steps = [(-10, 0, -28), (10, 0, -28)]
    tree_avenue = [(side * 21.0, 0, z) for side in (-1, 1) for z in (-20, -12, -4, 4, 12, 20, 28)]
    benches = [(side * 19.2, 0, z) for side in (-1, 1) for z in (-16, -8, 0, 8, 16, 24)]
    flower_ring = [(6.9 * math.cos(math.radians(45 * index)), 0, 6.9 * math.sin(math.radians(45 * index))) for index in range(8) if index not in (2, 6)]

    scene.add_node("Plaza", ".", "Node3D", groups=[NAVIGATION_SOURCE_GROUP])
    place(scene, "FountainLarge", "Plaza", "res://features/hub/props/fountain_large.tscn", (0, 0, 0))
    place(scene, "FountainWest", "Plaza", "res://features/hub/props/fountain_small.tscn", (-12, 0, 17))
    place(scene, "FountainEast", "Plaza", "res://features/hub/props/fountain_small.tscn", (12, 0, 17))

    for index, position in enumerate(lamp_ring + lamp_avenue + lamp_steps):
        place(scene, f"Lamp{index:02d}", "Plaza", "res://features/hub/props/lamp_post.tscn", position)

    for index, position in enumerate(tree_avenue):
        tree_model = f"res://art/nature/CommonTree_{index % 5 + 1}.gltf"
        place(scene, f"Planter{index:02d}", "Plaza", "res://art/town/planter.gltf", position)
        place(scene, f"Tree{index:02d}", "Plaza", tree_model, (position[0], 0.35, position[2]), rotation_y=index * 1.3, scale=0.75 + 0.06 * (index % 3))

    for index, position in enumerate(benches):
        place(scene, f"Bench{index:02d}", "Plaza", "res://art/props/Bench.gltf", position, rotation_y=math.pi / 2.0)

    for index, position in enumerate(flower_ring):
        place(scene, f"FlowerBush{index:02d}", "Plaza", "res://art/nature/Bush_Common_Flowers.gltf", position, rotation_y=index * 0.9, scale=0.9)

    flower_patches = [(-11.5, -29.5), (11.5, -29.5), (-14.5, -29.0), (14.5, -29.0), (-6.5, -30.8), (6.5, -30.8)]

    for index, (x, z) in enumerate(flower_patches):
        place(scene, f"Flowers{index:02d}", "Plaza", f"res://art/nature/Flower_{3 + index % 2}_Group.gltf", (x, 0, z), rotation_y=index * 1.1)


def add_market(scene: SceneWriter) -> None:
    market_items = [
        ("Stall_Empty", (10.0, 0, 27.0), 0.0),
        ("Stall_Empty", (14.2, 0, 27.0), 0.0),
        ("Stall_Cart_Empty", (18.5, 0, 24.0), -0.6),
        ("Barrel", (8.4, 0, 25.2), 0.0),
        ("Barrel_Apples", (11.9, 0, 25.4), 0.4),
        ("FarmCrate_Apple", (9.2, 0, 25.6), 0.2),
        ("FarmCrate_Carrot", (13.3, 0, 25.6), -0.2),
        ("Crate_Wooden", (16.2, 0, 27.6), 0.3),
        ("Bucket_Wooden_1", (16.6, 0, 26.2), 0.0),
        ("Table_Large", (-12.0, 0, 27.0), 0.0),
        ("Stool", (-13.6, 0, 27.0), 0.0),
        ("Stool", (-10.4, 0, 27.0), 0.0),
        ("Stool", (-12.0, 0, 25.75), 0.0),
        ("Barrel", (-15.0, 0, 28.5), 0.0),
        ("Barrel", (-15.6, 0, 27.6), 0.7),
        ("Banner_1", (-29.7, 3.6, -13.0), math.pi / 2.0),
        ("Banner_2", (29.7, 3.6, -5.0), -math.pi / 2.0),
    ]

    scene.add_node("Market", ".", "Node3D", groups=[NAVIGATION_SOURCE_GROUP])

    for index, (model_name, position, rotation_y) in enumerate(market_items):
        place(scene, f"{model_name}{index:02d}", "Market", f"res://art/props/{model_name}.gltf", position, rotation_y)


def add_backdrop(scene: SceneWriter) -> None:
    corner_trees = [(-22, -32), (-18.5, -36), (22, -33), (18, -37), (-27, 31), (27, 31), (-3.5, 41), (3.5, 41)]
    far_ring = [(66 * math.cos(math.radians(angle)), 66 * math.sin(math.radians(angle))) for angle in range(0, 360, 15)]
    back_rows = [(side * 42, z) for side in (-1, 1) for z in range(-60, 40, 9)]

    scene.add_node("Backdrop", ".", "Node3D")

    for index, (x, z) in enumerate(corner_trees + back_rows):
        place(scene, f"Tree{index:02d}", "Backdrop", f"res://art/nature/CommonTree_{index % 5 + 1}.gltf", (x, 0, z), rotation_y=index * 0.7, scale=0.85 + 0.1 * (index % 4))

    for index, (x, z) in enumerate(far_ring):
        place(scene, f"Pine{index:02d}", "Backdrop", f"res://art/nature/Pine_{index % 3 + 1}.gltf", (x, 0, z - 15), rotation_y=index * 0.5, scale=1.6 + 0.2 * (index % 3))


def npc(scene: SceneWriter, name: str, body: str, hair: str, properties: dict) -> None:
    body_id = scene.external_id("PackedScene", f"res://art/characters/{body}.gltf")
    all_properties = {"body_scene": f'ExtResource("{body_id}")', "hair_color": color(HAIR_COLORS[hair])}

    all_properties.update(properties)
    scene.add_node(name, "Townsfolk", instance=scene.external_id("PackedScene", "res://features/hub/walking_npc.tscn"), properties=all_properties)


def patrol(points: list, speed: float, pause: float, idle: str) -> dict:
    point_list = ", ".join(f"{x:.2f}, 0, {z:.2f}" for x, z in points)

    return {"route": f"PackedVector3Array({point_list})", "walk_speed": f"{speed}", "pause_seconds": f"{pause}", "idle_animation": f'&"{idle}"'}


def stand(position: tuple, facing: float, animation: str, offset: float) -> dict:
    return {
        "position": vector(position[0], 0.0, position[1]),
        "rotation": vector(0, facing, 0),
        "activity": "1",
        "idle_animation": f'&"{animation}"',
        "animation_offset_seconds": f"{offset}",
    }


def add_townsfolk(scene: SceneWriter) -> None:
    # Fora do anel de postes (r=9) e dos canteiros de flores (r=6.9); a navmesh contorna o resto.
    fountain_loop = [(10.5 * math.cos(math.radians(angle)), 10.5 * math.sin(math.radians(angle))) for angle in range(0, 360, 30)]

    scene.add_node("Navigation", ".", "NavigationRegion3D", properties={"navigation_mesh": f'ExtResource("{scene.external_id("NavigationMesh", "res://features/hub/hub_navmesh.tres")}")'})
    scene.add_node("Townsfolk", ".", "Node3D")
    npc(scene, "FountainWalker", "villager_male", "dark", patrol(fountain_loop, 1.2, 0.0, "ual1/Idle"))
    npc(scene, "FountainWalkerReverse", "villager_female", "auburn", patrol(list(reversed(fountain_loop[6:] + fountain_loop[:6])), 1.1, 0.0, "ual1/Idle"))
    npc(scene, "StreetWalker", "villager_male", "grey", patrol([(-2.5, 34), (-2.5, -27), (2.5, -27), (2.5, 34)], 1.3, 4.0, "ual2/Idle_FoldArms"))
    npc(scene, "WestAvenueWalker", "adventurer_female", "blond", patrol([(-15.5, -22), (-15.5, 20)], 1.5, 3.0, "ual1/Idle"))
    npc(scene, "EastAvenueWalker", "adventurer_male", "black", patrol([(15.5, 20), (15.5, -22)], 1.4, 5.0, "ual2/Idle_FoldArms"))
    npc(scene, "MarketShopper", "villager_female", "brown", patrol([(8.0, 23.5), (14.5, 22.5), (12.0, 21.0)], 1.0, 4.5, "ual1/Idle_Talking"))
    npc(scene, "CathedralVisitor", "villager_female", "black", patrol([(-9.0, -26.0), (9.0, -26.0)], 1.1, 6.0, "ual1/Idle"))
    npc(scene, "TalkerA", "villager_male", "brown", stand((7.6, 11.8), 2.28, "ual1/Idle_Talking", 0.0))
    npc(scene, "TalkerB", "villager_female", "blond", stand((9.0, 10.6), -0.86, "ual2/Idle_FoldArms", 0.7))
    npc(scene, "Merchant", "villager_male", "auburn", stand((10.0, 28.0), math.pi, "ual1/Idle_Talking", 1.1))
    npc(scene, "SittingWest", "villager_female", "grey", stand((-19.05, -8.0), math.pi / 2.0, "ual1/Sitting_Idle", 0.3))
    npc(scene, "SittingEast", "villager_male", "black", stand((19.05, 8.0), -math.pi / 2.0, "ual1/Sitting_Talking", 0.0))
    npc(scene, "TavernGuest", "adventurer_male", "brown", stand((-12.0, 25.6), 0.0, "ual1/Sitting_Talking", 0.5))
    npc(scene, "Guard", "adventurer_female", "dark", stand((-7.0, -28.4), 0.25, "ual2/Idle_FoldArms", 0.0))


def add_player_and_cameras(scene: SceneWriter) -> None:
    select_eye = (0.8, 1.35, 31.4)
    tour = [
        ((0, 15, 50), (0, 12, -40)),
        ((12, 2.4, 12), (0, 2.2, 0)),
        ((22, 3.2, 35), (10, 1.6, 24)),
        ((-19.5, 1.9, 30), (-19.5, 2.5, -20)),
        ((9, 1.3, -21), (0, 24, -38)),
        ((-42, 32, -6), (0, 4, -6)),
    ]

    place(scene, "Player", ".", "res://features/player/player.tscn", (0, 0, 27))
    scene.add_node("SelectCamera", ".", "Camera3D", properties={"position": vector(*select_eye), "rotation": look_rotation(select_eye, (0, 0.8, 27)), "fov": "42.0"})
    scene.add_node("CinematicTour", ".", "Node3D", properties={"script": f'ExtResource("{scene.external_id("Script", "res://features/hub/cinematic_tour.gd")}")'})

    for index, (eye, target) in enumerate(tour):
        scene.add_node(f"Key{index}", "CinematicTour", "Marker3D", properties={"position": vector(*eye), "rotation": look_rotation(eye, target)})

    scene.add_node("CharacterSelect", ".", instance=scene.external_id("PackedScene", "res://features/hub/character_select.tscn"))


def build_hub_scene() -> str:
    scene = SceneWriter()
    script_id = scene.external_id("Script", "res://features/hub/hub.gd")

    scene.add_node("Hub", None, "Node3D", properties={"script": f'ExtResource("{script_id}")'})
    add_environment(scene)
    add_ground(scene)
    add_boundary(scene)
    add_buildings(scene)
    add_plaza_props(scene)
    add_market(scene)
    add_backdrop(scene)
    add_townsfolk(scene)
    add_player_and_cameras(scene)

    return scene.render()


if __name__ == "__main__":
    if not NAVMESH_PATH.exists():  # placeholder until tools_src/bake_hub_navmesh.gd bakes the real one
        NAVMESH_PATH.write_text('[gd_resource type="NavigationMesh" format=3]\n\n[resource]\n', encoding="utf-8", newline="\n")

    OUTPUT_PATH.write_text(build_hub_scene(), encoding="utf-8", newline="\n")
    print(f"WROTE {OUTPUT_PATH}")
