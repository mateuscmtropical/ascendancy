"""Model the hidden crypt and catacombs under the cathedral: art/town/cathedral_crypt.gltf (+ JSON sidecar) and the
stone reliquary monument that hides the stair, art/town/cathedral_crypt_monument.gltf.

At the back of the right aisle a saint stands on a long stone plinth against the wall. Pushed (E), plinth and
statue slide out into the aisle (features/hub/secret_passage.gd) and uncover a steep stair that runs down under the
pews to the rooms below the nave, laid out after real crypts, archives, cabinets of curiosities and quarry ossuaries:
  Crypt of the saints (back, vaulted on piers): the confessio altar on the axis with a saint behind its gilded
    grille; in the side bays incorrupt saints lying in state in gilded baroque glass urns, each with its candlestick,
    flowers and prie-dieu; stone tombs with recumbent effigies; walls of burial niches.
  Secret archive (front left): long rows of archive presses with aisles between them, as in a real archive; a
    reading room with tables, lamps and a lectern; scroll racks, document drawers, a safe.
  Cabinet of relics and curiosities (front right): every wall lined with cases and shelves, a dragon skull hung
    from the vault over a summoning circle, display tables, an alchemist's corner, old armour, crowns, reliquaries.
  Catacombs (through a low door in the archive, under the square): a rock-cut gallery that turns into an ossuary,
    bone walls of stacked femurs and skull bands on both sides, engraved plaques on posts, a chamber with a barrel
    of bones, a chapel of bones, and a loop back.
The saints and effigies are the game's own character models (art/characters), posed and dressed here.

Same coordinates as build_cathedral.py (x across, y along the nave from the facade, z up; Godot puts both models
at the cathedral's transform). Everything stays below the town ground (z < -0.15) except the stair shaft, which
lies inside the cathedral plinth; build_hub_scene.CRYPT_SHAFT_HOLE opens the ground there.

Usage (after build_cathedral.py):
  blender -b --factory-startup -P tools_src/build_cathedral_crypt.py
"""

import itertools
import json
import math
import sys
from pathlib import Path

import bmesh
import bpy
from mathutils import Matrix, Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))

from build_cathedral import BASE, CRYPT_OPENING_Y, CRYPT_SHAFT, CRYPT_SLAB, MARY_PARTS, MARY_SOURCE, OUTPUT_DIR, PRAYER_POSE, STATUE_PARTS, STATUE_SOURCE, import_posed_meshes, make_draped_cone  # noqa: E402
from build_market_shops import PROPS as SHOP_PROPS  # noqa: E402
from build_town_houses import Builder, srgb  # noqa: E402
from shop_props_crypt import CRYPT_STONE, DARK_STONE, GILT, LIMESTONE, MARBLE, OSSUARY_LENGTH, URN_BED  # noqa: E402
from shop_props_crypt import PROPS as CRYPT_PROPS  # noqa: E402

PROPS = {**SHOP_PROPS, **CRYPT_PROPS}

FLOOR = BASE - 29 * 0.2  # 29 degraus de 20 cm a partir do piso da nave
CEILING = -0.35  # abaixo do chão da cidade (-0.15), que não pode cortar as salas
SLAB_UNDERSIDE = BASE - CRYPT_SLAB  # piso da nave por cima do poço da escada
OUTER = (-12.4, 12.4, 10.0, 39.4)  # x min, x max, y min, y max por dentro das paredes
WALL = 0.5
CROSS_WALL_Y = 23.5  # entre a cripta dos santos (fundo) e as duas salas da frente
MIDDLE_WALL_X = 0.0  # entre o arquivo (esquerda) e o gabinete (direita)
SHAFT_X = CRYPT_SHAFT[0]  # poço da escada, encostado na parede lateral direita
SHAFT_INNER_WALL = (10.7, 10.95)
STAIR_TOP_Y = CRYPT_SHAFT[1][1]  # o primeiro degrau sai do piso da nave aqui, descendo para a fachada
STEP_TREAD = 0.28
STEP_RISE = 0.2
STEP_COUNT = 29
LANDING = (CRYPT_SHAFT[1][0], STAIR_TOP_Y - STEP_COUNT * STEP_TREAD)  # patamar no pé da escada
SHAFT_DOOR = (26.4, 27.8, 2.4)  # do patamar para a cripta dos santos (y de, y até, altura)
ROOM_DOORS = {"archive": (-6.8, -5.2), "cabinet": (4.2, 5.8)}  # vãos na parede CROSS_WALL_Y, x de, x até
ROOM_DOOR_HEIGHT = 2.6
CATACOMB_DOOR = (-3.0, -1.4, 2.1)  # porta baixa na parede sul do arquivo (x de, x até, altura)
PIER_X = (-6.0, 6.0)
PIER_Y = (27.0, 31.75, 36.5)
PIER_SIZE = 0.7
RIB = (0.4, 0.3)
LIGHTS_PER_ROOM = {"santos": 7, "arquivo": 5, "gabinete": 6, "catacumba": 12}
WALL_TINT = "A99C88"
FLOOR_TINT = "8E8478"
GRAVEL_TINT = "A39377"
ROCK_CEILING_TINT = "BBA984"
CATACOMB_CEILING = FLOOR + 2.4
CATACOMB_WALL = 0.6
# Galerias da catacumba (x de, x até, y de, y até) e as aberturas de cada lado: lado -> [(de, até)] ao longo dele;
# "all" abre o lado inteiro. Só a galeria de entrada (A) atravessa a parede do arquivo.
CATACOMB_SPACES = {
    "A": ((-3.4, -1.0, -14.0, OUTER[2] - WALL), {"north": "all", "south": "all", "east": [(-7.2, -4.8)]}),  # a parede do arquivo fecha o norte
    "B": ((-6.2, 1.8, -22.0, -14.0), {"north": [(-3.4, -1.0)], "east": [(-22.0, -19.6)]}),
    "C": ((-1.0, 9.0, -7.2, -4.8), {"west": "all", "east": "all"}),
    "D": ((9.0, 15.0, -10.0, -2.0), {"west": [(-7.2, -4.8)], "south": [(11.8, 14.2)]}),
    "E": ((11.8, 14.2, -19.6, -10.0), {"north": "all", "south": "all"}),
    "F": ((1.8, 14.2, -22.0, -19.6), {"west": "all", "north": [(11.8, 14.2)]}),
}
OSSUARY_START_Y = 1.6  # a galeria de entrada só tem rocha até aqui; dali para dentro, ossos dos dois lados
SAINT_SKIN = "D9C2A4"  # cera envelhecida das máscaras e das mãos
SAINT_MALE = STATUE_PARTS + ("Male_Peasant_Legs",)  # deitado, sem a túnica em cone das estátuas, as pernas aparecem
SAINT_FEMALE = MARY_PARTS + ("Female_Peasant_Legs",)
SAINT_VARIANTS = {  # (fonte, peças, cor do corpo, cor dos pés, cobertura)
    "bishop": (STATUE_SOURCE, SAINT_MALE, "8E2234", "B0263A", "mitre"),
    "monk": (STATUE_SOURCE, SAINT_MALE, "5E4330", "3A2A20", "hood"),
    "nun": (MARY_SOURCE, SAINT_FEMALE, "2C2522", "1E1A18", "veil"),
    "martyr": (MARY_SOURCE, SAINT_FEMALE, "DCE4EE", "C9A86A", "wreath"),
}
FIGURE_LENGTH = 1.8
FIGURE_DETAIL = 0.4  # fração dos triângulos que fica nas figuras (decimate): deitadas e à luz de vela não precisam mais
FIGURE_BACK = 0.13  # das costas ao eixo do corpo: quanto o corpo deitado sobe acima da cama
EFFIGY_TINT = "CDBFA6"
STAMPED_PROPS = ("ossuary_wall",)  # centenas de ossos por módulo: montados uma vez por variante e copiados
STAMP_SEEDS = 3
OSSUARY_CORNER = 0.45  # a fileira de ossos da parede que cruza ocupa o canto  # módulos lisos diferentes que se revezam ao longo das paredes
MONUMENT_ANCHOR = (12.4, sum(CRYPT_OPENING_Y) / 2.0, BASE)  # meio da face do pedestal encostada na parede
MONUMENT_SIZE = (SHAFT_X[1] - SHAFT_X[0], CRYPT_OPENING_Y[1] - CRYPT_OPENING_Y[0], 0.95)


class Placer:
    """Props by name at (x, y) on the crypt floor, turned by degrees (front -Y), with colliders, light spots per
    room (lit=False keeps a prop dark) and footprints for the overlap report."""

    def __init__(self, b: Builder) -> None:
        self.b = b
        self.footprints = []
        self.lights = {}
        self.missing = set()
        self.stamps = {}

    def put(self, room: str, name: str, x: float, y: float, degrees: float = 0.0, z: float = None, lit: bool = True, **options) -> Matrix:
        entry = PROPS.get(name)

        if entry is None:
            self.missing.add(name)
            return Matrix.Identity(4)

        width, depth, height = entry["size"]
        floor = CATACOMB_FLOOR_OF.get(room, FLOOR)
        top = CATACOMB_CEILING if room == "catacumba" else CEILING
        origin_z = (top if entry.get("hang") else floor) if z is None else z
        frame = Matrix.Translation((x, y, origin_z)) @ Matrix.Rotation(math.radians(degrees), 4, "Z")
        cos_turn, sin_turn = abs(math.cos(math.radians(degrees))), abs(math.sin(math.radians(degrees)))
        half_x, half_y = (width * cos_turn + depth * sin_turn) / 2.0, (width * sin_turn + depth * cos_turn) / 2.0

        if name in STAMPED_PROPS:
            self.stamp(name, entry, frame, options)
        else:
            entry["build"](self.b, frame, **options)

        if entry.get("solid"):
            self.b.collider((-width / 2.0, -depth / 2.0, 0.0), (width / 2.0, depth / 2.0, min(height, 2.4)), frame)
            self.footprints.append((f"{room}:{name}", (x - half_x, x + half_x, y - half_y, y + half_y)))

        if entry.get("light") and lit:
            position, color, energy, light_range = entry["light"]
            self.lights.setdefault(room, []).append((frame @ Vector(position), color, energy, light_range))

        return frame

    def stamp(self, name: str, entry: dict, frame: Matrix, options: dict) -> None:
        """Copy of a baked module: one mesh per (material, tint, uv) instead of hundreds of small parts."""
        key = (name, options.get("variant", "plain"), options.get("seed", 0) % STAMP_SEEDS)

        if key not in self.stamps:
            self.stamps[key] = bake_module(self.b, entry, {**options, "seed": key[2]})

        for mesh, tint, uv in self.stamps[key]:
            part = bpy.data.objects.new(name, mesh.copy())
            bpy.context.scene.collection.objects.link(part)
            part.data.transform(frame)
            part["tint"], part["uv"] = tint, uv

    def against(self, room: str, side: str, name: str, along: float, wall: float, **options) -> Matrix:
        """Prop with its back to a wall: side is where the wall is (north +y, south -y, east +x, west -x)."""
        depth = PROPS.get(name, {"size": (1.0, 0.5, 1.0)})["size"][1] / 2.0 + 0.03
        spots = {"north": (along, wall - depth, 0.0), "south": (along, wall + depth, 180.0), "east": (wall - depth, along, -90.0), "west": (wall + depth, along, 90.0)}
        x, y, degrees = spots[side]

        return self.put(room, name, x, y, degrees, **options)

    def report(self) -> None:
        pairs = itertools.combinations(self.footprints, 2)
        overlapping = [(first[0], second[0]) for first, second in pairs if first[1][0] < second[1][1] - 0.02 and second[1][0] < first[1][1] - 0.02 and first[1][2] < second[1][3] - 0.02 and second[1][2] < first[1][3] - 0.02]

        for first, second in overlapping:
            print(f"AVISO cripta: {first} x {second}")

        if self.missing:
            print(f"AVISO cripta: props que não existem: {sorted(self.missing)}")


CATACOMB_FLOOR_OF = {}


def bake_module(b: Builder, entry: dict, options: dict) -> list:
    """Build a prop once at the origin and merge its parts by (material, tint, uv) into loose meshes (not in the
    scene): [(mesh, tint, uv)]. Its colliders stay out; the Placer adds the prop's box."""
    before = set(bpy.context.scene.objects)
    entry["build"](b, Matrix.Identity(4), **options)
    parts = [part for part in bpy.context.scene.objects if part not in before]
    groups = {}

    for part in parts:
        if part.type == "MESH" and not part.name.endswith("-colonly"):
            groups.setdefault((part.data.materials[0].name, tuple(part["tint"]), part["uv"]), []).append(part)

    baked = [(merge_parts(members), list(tint), uv) for (_material, tint, uv), members in groups.items()]

    for part in parts:
        bpy.data.objects.remove(part, do_unlink=True)

    return baked


def merge_parts(parts: list):
    """One mesh holding all the parts in their world placement, with the first part's material."""
    merged = bmesh.new()

    for part in parts:
        copy = part.data.copy()
        copy.transform(part.matrix_world)
        merged.from_mesh(copy)
        bpy.data.meshes.remove(copy)

    mesh = bpy.data.meshes.new("BakedModule")
    merged.to_mesh(mesh)
    merged.free()
    mesh.materials.append(parts[0].data.materials[0])

    return mesh


# ---------- figures: the game's character models, posed lying in state ----------

def tag_part(part, tint: str) -> None:
    part["tint"] = srgb(tint)
    part["uv"] = json.dumps(("world", 2.0))


def simplify(part) -> None:
    modifier = part.modifiers.new("Simplify", "DECIMATE")
    modifier.ratio = FIGURE_DETAIL

    with bpy.context.temp_override(object=part, active_object=part):
        bpy.ops.object.modifier_apply(modifier=modifier.name)


def lying_matrix(bed: Matrix) -> Matrix:
    """Standing figure (feet at the origin, facing -Y, up +Z) -> lying on its back along the bed's +X, head at +X,
    centred on the bed origin."""
    turn = Matrix(((0.0, 0.0, 1.0, 0.0), (-1.0, 0.0, 0.0, 0.0), (0.0, -1.0, 0.0, 0.0), (0.0, 0.0, 0.0, 1.0)))

    return bed @ Matrix.Translation((-FIGURE_LENGTH / 2.0, 0.0, FIGURE_BACK)) @ turn


def headwear_mitre(b: Builder, frame: Matrix, head_top: float) -> None:
    """Tall bishop's mitre, white with gold bands, two lappets down the back."""
    base = head_top - 0.07
    points = [(x, y, base) for x, y in itertools.product((-0.1, 0.1), (-0.08, 0.08))] + [(x, 0.0, base + 0.32) for x in (-0.05, 0.05)]

    b.hull(points, "paint", srgb("F4F0E6"), frame=frame)
    b.box((-0.012, -0.085, base), (0.012, 0.085, base + 0.3), "metal", srgb(GILT), frame)
    b.box((-0.105, -0.085, base), (0.105, 0.085, base + 0.04), "metal", srgb(GILT), frame)

    for side in (-1.0, 1.0):
        b.box((side * 0.05 - 0.025, 0.09, base - 0.3), (side * 0.05 + 0.025, 0.1, base), "metal", srgb(GILT), frame)


def headwear_hood(b: Builder, frame: Matrix, head_top: float) -> None:
    """Monk's cowl thrown back over the shoulders."""
    b.hull([(x, y, z) for x, y, z in itertools.product((-0.2, 0.2), (0.04, 0.2), (head_top - 0.42, head_top - 0.12))], "paint", srgb("4E3828"), frame=frame)


def headwear_veil(b: Builder, frame: Matrix, head_top: float) -> None:
    """Nun's black veil falling to the shoulders over a white wimple framing the face."""
    b.hull([(x, y, z) for x, y, z in itertools.product((-0.13, 0.13), (-0.02, 0.16), (head_top - 0.48, head_top + 0.03))], "paint", srgb("1C1818"), frame=frame)
    b.hull([(x, y, z) for x, y, z in itertools.product((-0.105, 0.105), (-0.1, 0.02), (head_top - 0.36, head_top - 0.27))], "paint", srgb("F2EEE6"), frame=frame)
    b.box((-0.105, -0.11, head_top - 0.05), (0.105, -0.06, head_top), "paint", srgb("F2EEE6"), frame)


def headwear_wreath(b: Builder, frame: Matrix, head_top: float) -> None:
    """Virgin martyr: a wreath of white and red flowers on the hair."""
    for step in range(10):
        angle = 2.0 * math.pi * step / 10.0
        b.sphere((0.1 * math.cos(angle), 0.1 * math.sin(angle), head_top - 0.06), 0.025, "paint", srgb("F4F0E8" if step % 2 else "C2283A"), frame=frame, segments=6)


HEADWEAR = {"mitre": headwear_mitre, "hood": headwear_hood, "veil": headwear_veil, "wreath": headwear_wreath}


def add_figure(b: Builder, bed: Matrix, variant: str, stone: bool = False) -> None:
    """One of the game's character models in the hands-joined prayer pose, dressed by variant, lying on the bed
    frame (its origin on the bed's top, length along its +X). stone=True carves the whole figure in one stone tint
    (tomb effigies)."""
    source, part_names, robe, slippers, headwear = SAINT_VARIANTS[variant]
    before = set(bpy.context.scene.objects)
    parts, bone_positions, _, _ = import_posed_meshes(source, part_names, PRAYER_POSE, f"Saint{variant}", b.materials["paint"])
    head = next(part for part in parts if "Head_Skin" in part.name)
    head_top = max(vertex.co.z for vertex in head.data.vertices)
    tints = {"Head_Skin": SAINT_SKIN, "Arms": SAINT_SKIN, "Eyebrows": "5A4A3E", "Hair": "8C8070", "Body": robe, "Feet": slippers}
    standing = Matrix.Identity(4)

    for part in parts:
        tag_part(part, next((tint for key, tint in tints.items() if key in part.name), robe))

    HEADWEAR[headwear](b, standing, head_top)

    if variant == "bishop":
        b.beam((0.34, 0.0, 0.2), (0.34, 0.0, 1.75), 0.025, 0.025, "metal", srgb(GILT))  # deitado, o báculo fica ao lado do corpo, não por cima

    if variant == "martyr":
        b.beam((0.0, -0.2, 0.8), (0.04, -0.24, 1.3), 0.04, 0.012, "paint", srgb("5E8B3D"))

    added = [scene_object for scene_object in bpy.context.scene.objects if scene_object not in before and scene_object.type == "MESH"]
    placement = lying_matrix(bed)

    for part in added:
        part.data.transform(part.matrix_world)
        part.matrix_world = Matrix.Identity(4)
        part.data.transform(placement)
        simplify(part)

        if stone:
            part["tint"] = srgb(EFFIGY_TINT)
            part.data.materials.clear()
            part.data.materials.append(b.materials["stone"])


def add_standing_statue(b: Builder, placement: Matrix) -> None:
    """Stone statue of a praying monk-saint (the game's male model), standing on placement's origin facing -Y."""
    before = set(bpy.context.scene.objects)
    import_posed_meshes(STATUE_SOURCE, STATUE_PARTS, PRAYER_POSE, "MonumentSaint", b.materials["stone"])
    make_draped_cone("MonumentSaintRobe", 0.03, 1.35, 0.34, 0.18, 9, 0.035, b.materials["stone"])
    added = [scene_object for scene_object in bpy.context.scene.objects if scene_object not in before and scene_object.type == "MESH"]

    for part in added:
        part["tint"] = srgb("E2D8C4")
        part["uv"] = json.dumps(("world", 2.0))
        part.data.transform(part.matrix_world)
        part.matrix_world = Matrix.Identity(4)
        part.data.transform(placement)
        simplify(part)


# ---------- shell of the crypt ----------

def stone_box(b: Builder, minimum: tuple, maximum: tuple, tint: str = WALL_TINT, collide: bool = True) -> None:
    b.box(minimum, maximum, "stone", srgb(tint))

    if collide:
        b.collider(minimum, maximum)


def build_floor_and_ceiling(b: Builder) -> None:
    """Flagstone floor everywhere; the ceiling slab leaves the stair shaft open to the plinth above."""
    x_min, x_max, y_min, y_max = OUTER
    shaft_column = (SHAFT_INNER_WALL[0], x_max + WALL)

    stone_box(b, (x_min - WALL, y_min - WALL, FLOOR - 0.3), (x_max + WALL, y_max + WALL, FLOOR), FLOOR_TINT)
    stone_box(b, (x_min - WALL, y_min - WALL, CEILING), (shaft_column[0], y_max + WALL, CEILING + 0.15), DARK_STONE, collide=False)
    stone_box(b, (shaft_column[0], y_min - WALL, CEILING), (shaft_column[1], LANDING[0], CEILING + 0.15), DARK_STONE, collide=False)
    stone_box(b, (shaft_column[0], STAIR_TOP_Y + 0.3, CEILING), (shaft_column[1], y_max + WALL, CEILING + 0.15), DARK_STONE, collide=False)


def build_outer_walls(b: Builder) -> None:
    """Outer walls; the south wall of the archive keeps the low door to the catacombs."""
    x_min, x_max, y_min, y_max = OUTER
    door_from, door_to, door_height = CATACOMB_DOOR

    stone_box(b, (x_min - WALL, y_min - WALL, FLOOR), (door_from, y_min, CEILING))
    stone_box(b, (door_to, y_min - WALL, FLOOR), (x_max + WALL, y_min, CEILING))
    stone_box(b, (door_from, y_min - WALL, FLOOR + door_height), (door_to, y_min, CEILING))
    stone_box(b, (x_min - WALL, y_max, FLOOR), (x_max + WALL, y_max + WALL, CEILING))
    stone_box(b, (x_min - WALL, y_min, FLOOR), (x_min, y_max, CEILING))
    stone_box(b, (x_max, y_min, FLOOR), (x_max + WALL, y_max, SLAB_UNDERSIDE))


def build_inner_walls(b: Builder) -> None:
    """Cross wall with the two room doors, middle wall between archive and cabinet, wall between the shaft and the
    crypt of the saints with its door off the landing."""
    x_min, x_max, y_min, _ = OUTER
    door_edges = [x_min] + [edge for door in sorted(ROOM_DOORS.values()) for edge in door] + [SHAFT_INNER_WALL[1]]
    solid_runs = list(zip(door_edges[0::2], door_edges[1::2]))
    half = 0.25

    for run_from, run_to in solid_runs:
        stone_box(b, (run_from, CROSS_WALL_Y - half, FLOOR), (run_to, CROSS_WALL_Y + half, CEILING))

    for door_from, door_to in ROOM_DOORS.values():
        stone_box(b, (door_from, CROSS_WALL_Y - half, FLOOR + ROOM_DOOR_HEIGHT), (door_to, CROSS_WALL_Y + half, CEILING))
        stone_box(b, (door_from - 0.12, CROSS_WALL_Y - half - 0.06, FLOOR), (door_from, CROSS_WALL_Y + half + 0.06, FLOOR + ROOM_DOOR_HEIGHT + 0.12), MARBLE, collide=False)
        stone_box(b, (door_to, CROSS_WALL_Y - half - 0.06, FLOOR), (door_to + 0.12, CROSS_WALL_Y + half + 0.06, FLOOR + ROOM_DOOR_HEIGHT + 0.12), MARBLE, collide=False)
        stone_box(b, (door_from - 0.12, CROSS_WALL_Y - half - 0.06, FLOOR + ROOM_DOOR_HEIGHT), (door_to + 0.12, CROSS_WALL_Y + half + 0.06, FLOOR + ROOM_DOOR_HEIGHT + 0.18), MARBLE, collide=False)

    stone_box(b, (MIDDLE_WALL_X - half, y_min, FLOOR), (MIDDLE_WALL_X + half, CROSS_WALL_Y - half, CEILING))

    inner_from, inner_to = SHAFT_INNER_WALL
    door_from, door_to, door_height = SHAFT_DOOR
    stone_box(b, (inner_from, CROSS_WALL_Y + half, FLOOR), (inner_to, door_from, SLAB_UNDERSIDE))
    stone_box(b, (inner_from, door_to, FLOOR), (inner_to, OUTER[3], SLAB_UNDERSIDE))
    stone_box(b, (inner_from, door_from, FLOOR + door_height), (inner_to, door_to, SLAB_UNDERSIDE))
    stone_box(b, (inner_to, CROSS_WALL_Y + half, FLOOR), (x_max, LANDING[0], SLAB_UNDERSIDE))
    stone_box(b, (inner_to, STAIR_TOP_Y, FLOOR), (x_max, STAIR_TOP_Y + 0.3, SLAB_UNDERSIDE))


def build_stair(b: Builder) -> None:
    """Steep stone stair from the nave floor down the shaft, with one ramp collider over the steps and an iron
    hand rail on the open side."""
    x_from, x_to = SHAFT_X
    run = STEP_COUNT * STEP_TREAD
    drop = STEP_COUNT * STEP_RISE
    slope = math.atan2(drop, run)
    length = math.hypot(run, drop) + 0.4
    # o colisor passa 0,4 m do pé da escada para dentro do patamar, nunca acima do piso da nave
    middle = Vector(((x_from + x_to) / 2.0, STAIR_TOP_Y - run / 2.0, BASE - drop / 2.0)) - 0.2 * Vector((0.0, math.cos(slope), math.sin(slope)))
    rail_start_step = BASE - (STAIR_TOP_Y - CRYPT_OPENING_Y[0]) / STEP_TREAD * STEP_RISE

    for step in range(STEP_COUNT - 1):
        front = STAIR_TOP_Y - (step + 1) * STEP_TREAD
        top = BASE - (step + 1) * STEP_RISE
        b.box((x_from, front, FLOOR), (x_to, front + STEP_TREAD, top), "stone", srgb(CRYPT_STONE))
        b.box((x_from, front - 0.03, top - 0.04), (x_to, front + 0.02, top), "stone", srgb(MARBLE))

    b.collider((-(x_to - x_from) / 2.0, -length / 2.0, -0.4), ((x_to - x_from) / 2.0, length / 2.0, 0.0), Matrix.Translation(middle) @ Matrix.Rotation(slope, 4, "X"))
    rail_from = Vector((SHAFT_INNER_WALL[1] + 0.06, CRYPT_OPENING_Y[0], rail_start_step + 0.9))
    rail_to = Vector((SHAFT_INNER_WALL[1] + 0.06, LANDING[1] + 0.2, FLOOR + 0.95))
    b.beam(tuple(rail_from), tuple(rail_to), 0.05, 0.05, "metal", srgb("3A3B5E"))


def build_piers_and_ribs(b: Builder) -> None:
    """Square piers with base and capital under the vault of the crypt of the saints, ribs across and along."""
    half = PIER_SIZE / 2.0
    crypt_x = (OUTER[0], SHAFT_INNER_WALL[0])
    crypt_y = (CROSS_WALL_Y + 0.25, OUTER[3])

    for pier_x, pier_y in itertools.product(PIER_X, PIER_Y):
        stone_box(b, (pier_x - half, pier_y - half, FLOOR), (pier_x + half, pier_y + half, CEILING), CRYPT_STONE)
        stone_box(b, (pier_x - half - 0.1, pier_y - half - 0.1, FLOOR), (pier_x + half + 0.1, pier_y + half + 0.1, FLOOR + 0.3), DARK_STONE, collide=False)
        stone_box(b, (pier_x - half - 0.12, pier_y - half - 0.12, CEILING - 0.6), (pier_x + half + 0.12, pier_y + half + 0.12, CEILING - 0.4), MARBLE, collide=False)

    for pier_y in PIER_Y:
        stone_box(b, (crypt_x[0], pier_y - RIB[0] / 2.0, CEILING - RIB[1]), (crypt_x[1], pier_y + RIB[0] / 2.0, CEILING), CRYPT_STONE, collide=False)

    for pier_x in PIER_X:
        stone_box(b, (pier_x - RIB[0] / 2.0, crypt_y[0], CEILING - RIB[1]), (pier_x + RIB[0] / 2.0, crypt_y[1], CEILING), CRYPT_STONE, collide=False)

    for rib_x in (-6.3, -3.0, 3.0, 6.3):
        stone_box(b, (rib_x - 0.15, OUTER[2], CEILING - 0.2), (rib_x + 0.15, CROSS_WALL_Y - 0.25, CEILING), CRYPT_STONE, collide=False)


# ---------- catacombs ----------

def side_runs(span: tuple, openings) -> list:
    """Solid stretches along one side of a space, between its openings ("all" = no wall)."""
    if openings == "all":
        return []

    edges = [span[0]] + [edge for opening in sorted(openings or []) for edge in opening] + [span[1]]

    return [(start, end) for start, end in zip(edges[0::2], edges[1::2]) if end - start > 0.01]


def build_catacomb_shell(b: Builder) -> None:
    """Rock-cut galleries: gravel floor, rough limestone walls left solid except at the openings, a low rock
    ceiling. Walls stand outside each space so neighbouring spaces share them."""
    thick = CATACOMB_WALL

    for name, ((x_from, x_to, y_from, y_to), openings) in CATACOMB_SPACES.items():
        stone_box(b, (x_from, y_from, FLOOR - 0.3), (x_to, y_to, FLOOR), GRAVEL_TINT)
        stone_box(b, (x_from, y_from, CATACOMB_CEILING), (x_to, y_to, CATACOMB_CEILING + 0.4), ROCK_CEILING_TINT, collide=False)
        # as paredes leste e oeste fecham os cantos, salvo onde o lado vizinho é todo aberto (entra noutra galeria)
        y_span = (y_from - (0.0 if openings.get("south") == "all" else thick), y_to + (0.0 if openings.get("north") == "all" else thick))
        sides = {
            "north": [((start, y_to, FLOOR), (end, y_to + thick, CATACOMB_CEILING)) for start, end in side_runs((x_from, x_to), openings.get("north"))],
            "south": [((start, y_from - thick, FLOOR), (end, y_from, CATACOMB_CEILING)) for start, end in side_runs((x_from, x_to), openings.get("south"))],
            "west": [((x_from - thick, start, FLOOR), (x_from, end, CATACOMB_CEILING)) for start, end in side_runs(y_span, openings.get("west"))],
            "east": [((x_to, start, FLOOR), (x_to + thick, end, CATACOMB_CEILING)) for start, end in side_runs(y_span, openings.get("east"))],
        }

        for minimum, maximum in [wall for walls in sides.values() for wall in walls]:
            stone_box(b, minimum, maximum, LIMESTONE)

    build_ossuary_portal(b)


def build_ossuary_portal(b: Builder) -> None:
    """Stone door frame where the entrance gallery turns into the ossuary: two jambs and a deep lintel that
    carries the carved warning."""
    a_from, a_to = CATACOMB_SPACES["A"][0][:2]
    front, back = OSSUARY_START_Y - 0.2, OSSUARY_START_Y

    stone_box(b, (a_from, front, FLOOR), (a_from + 0.4, back, CATACOMB_CEILING), CRYPT_STONE)
    stone_box(b, (a_to - 0.4, front, FLOOR), (a_to, back, CATACOMB_CEILING), CRYPT_STONE)
    stone_box(b, (a_from + 0.4, front, FLOOR + 1.9), (a_to - 0.4, back, CATACOMB_CEILING), CRYPT_STONE)


def line_of_bones(place: Placer, side: str, along: tuple, wall: float, skip: list, patterns: dict, seed: int) -> None:
    """Ossuary modules side by side along one wall face, leaving the openings (skip) free and the corners to the
    crossing wall's line; patterns maps a module index to its variant (cross, heart)."""
    along = (along[0] + OSSUARY_CORNER, along[1] - OSSUARY_CORNER)
    count = int((along[1] - along[0]) / OSSUARY_LENGTH)
    start = along[0] + ((along[1] - along[0]) - count * OSSUARY_LENGTH) / 2.0 + OSSUARY_LENGTH / 2.0
    centers = [start + index * OSSUARY_LENGTH for index in range(count)]
    free = [center for center in centers if all(center + OSSUARY_LENGTH / 2.0 <= low + 0.05 or center - OSSUARY_LENGTH / 2.0 >= high - 0.05 for low, high in skip)]

    for index, center in enumerate(free):
        place.against("catacumba", side, "ossuary_wall", center, wall, seed=seed + index, variant=patterns.get(index, "plain"))


def furnish_catacombs(place: Placer) -> None:
    """Bones on both walls from the first plaque inward, plaques on posts, wall lanterns, the barrel of bones in the
    chamber at the end of the entrance gallery, an altar of skulls in the chapel of bones."""
    lantern_z = FLOOR + 2.15
    a_x, b_x = (-3.4, -1.0), (-6.2, 1.8)

    line_of_bones(place, "west", (-14.0, OSSUARY_START_Y), a_x[0], [], {3: "cross"}, 100)
    line_of_bones(place, "east", (-14.0, OSSUARY_START_Y), a_x[1], [(-7.2, -4.8)], {1: "heart"}, 120)
    line_of_bones(place, "north", b_x, -14.0, [(-3.4, -1.0)], {}, 140)
    line_of_bones(place, "south", b_x, -22.0, [], {2: "cross"}, 150)
    line_of_bones(place, "west", (-22.0, -14.0), b_x[0], [], {1: "heart"}, 160)
    line_of_bones(place, "east", (-22.0, -14.0), b_x[1], [(-22.0, -19.6)], {}, 170)
    line_of_bones(place, "north", (-1.0, 9.0), -4.8, [], {2: "cross"}, 180)
    line_of_bones(place, "south", (-1.0, 9.0), -7.2, [], {}, 190)
    line_of_bones(place, "north", (9.0, 15.0), -2.0, [], {1: "heart"}, 200)
    line_of_bones(place, "south", (9.0, 15.0), -10.0, [(11.8, 14.2)], {}, 210)
    line_of_bones(place, "west", (-10.0, -2.0), 9.0, [(-7.2, -4.8)], {}, 220)
    line_of_bones(place, "west", (-19.6, -10.0), 11.8, [], {2: "cross"}, 230)
    line_of_bones(place, "east", (-22.0, -10.0), 14.2, [], {}, 240)
    line_of_bones(place, "north", (1.8, 11.8), -19.6, [], {}, 250)
    line_of_bones(place, "south", (1.8, 14.2), -22.0, [], {3: "heart"}, 260)

    place.put("catacumba", "lintel_inscription", sum(a_x) / 2.0, OSSUARY_START_Y, 180.0, z=FLOOR + 1.95)
    place.put("catacumba", "lintel_inscription", sum(CATACOMB_DOOR[:2]) / 2.0, OUTER[2], 180.0, z=FLOOR + CATACOMB_DOOR[2] + 0.1)

    for side, x, y in (("west", a_x[0] + 0.55, -3.0), ("east", a_x[1] - 0.55, -11.0), ("north", -4.6, -14.55), ("west", 12.35, -15.0), ("south", 7.0, -21.45)):
        place.put("catacumba", "catacomb_plaque", x, y, {"west": 90.0, "east": -90.0, "north": 0.0, "south": 180.0}[side])

    for x, y, degrees in ((a_x[0] + 0.05, 6.0, 90.0), (a_x[1] - 0.05, -1.0, -90.0), (a_x[0] + 0.05, -9.0, 90.0), (b_x[0] + 0.05, -18.0, 90.0), (b_x[1] - 0.05, -16.0, -90.0), (4.0, -4.85, 0.0), (14.15, -15.0, -90.0), (7.0, -19.65, 0.0)):
        place.put("catacumba", "wall_lantern", x, y, degrees, z=lantern_z)

    place.put("catacumba", "bone_barrel", sum(b_x) / 2.0, -18.0)
    place.against("catacumba", "east", "sarcophagus", -6.0, 15.0)
    place.put("catacumba", "candle_stand", 13.6, -7.6)
    place.put("catacumba", "candle_stand", 13.6, -4.4)

    for x, y, degrees in ((12.0, -2.05, 180.0), (12.0, -9.95, 0.0)):
        place.put("catacumba", "wall_lantern", x, y, degrees, z=lantern_z)


# ---------- rooms ----------

def urn_bay(place: Placer, side: str, y: float, variant: str, seed: int) -> None:
    """One side bay with a saint in state: the urn lengthwise against the wall, a candlestick at each end (one lit),
    flowers on the floor before it and a prie-dieu facing it."""
    wall_x = OUTER[0] if side == "west" else SHAFT_INNER_WALL[0]
    sign = 1.0 if side == "west" else -1.0
    urn_x = wall_x + sign * 0.8
    turn = 90.0 if side == "west" else -90.0
    urn = place.put("santos", "baroque_urn", urn_x, y, turn)

    add_figure(place.b, urn @ Matrix.Translation((0.0, 0.0, URN_BED)), variant)
    place.put("santos", "candle_stand", urn_x, y - 1.55)
    place.put("santos", "candle_stand", urn_x, y + 1.55, lit=False)
    place.put("santos", "flower_vase", urn_x + sign * 0.95, y - 0.75, seed=seed)
    place.put("santos", "flower_vase", urn_x + sign * 0.95, y + 0.75, seed=seed + 1)
    place.put("santos", "kneeler", urn_x + sign * 1.95, y, turn)


def tomb(place: Placer, x: float, y: float, degrees: float, variant: str) -> None:
    frame = place.put("santos", "sarcophagus", x, y, degrees)

    add_figure(place.b, frame @ Matrix.Translation((0.0, 0.0, 1.0)), variant, stone=True)


def furnish_saints(place: Placer) -> None:
    """Confessio altar on the axis under the high altar, four saints in state in the side bays, three tombs with
    recumbent effigies, burial niches on the end walls, iron lanterns over the aisle."""
    room = "santos"
    west, east, north, south = OUTER[0], SHAFT_INNER_WALL[0], OUTER[3], CROSS_WALL_Y + 0.25

    for lantern_y in (27.0, 31.75, 36.5):
        place.put(room, "hanging_lantern", 0.0, lantern_y)

    altar = place.against(room, "north", "confessio_altar", 0.0, north)
    add_figure(place.b, altar @ Matrix.Translation((0.0, 0.05, 0.42)), "bishop")
    place.put(room, "candle_stand", -2.1, north - 1.2)
    place.put(room, "candle_stand", 2.1, north - 1.2)
    place.put(room, "kneeler", -0.75, north - 2.6, 0.0)
    place.put(room, "kneeler", 0.75, north - 2.6, 0.0)

    urn_bay(place, "west", 30.0, "bishop", 10)
    urn_bay(place, "west", 34.4, "nun", 20)
    urn_bay(place, "east", 30.0, "martyr", 30)
    urn_bay(place, "east", 34.4, "monk", 40)
    tomb(place, west + 0.75, 25.6, 90.0, "bishop")
    tomb(place, -9.3, 37.55, 0.0, "monk")
    tomb(place, 8.55, 37.55, 0.0, "bishop")

    for index, wall_x in enumerate((-11.3, -9.3, -4.3, 4.3, 7.65, 9.65)):
        place.against(room, "north", "loculi_wall", wall_x, north, seed=index)

    for index, wall_x in enumerate((-10.0, -3.3, -1.2, 0.9, 7.6, 9.65)):
        place.against(room, "south", "loculi_wall", wall_x, south, seed=10 + index)

    place.put(room, "iron_gate", east - 0.06, SHAFT_DOOR[0] - 0.45, 90.0)  # aberto, rente à parede ao lado da porta


def reading_table_with_chairs(place: Placer, room: str, x: float, y: float) -> None:
    place.put(room, "reading_table", x, y, 0.0)

    for chair_x, side in itertools.product((x - 0.5, x + 0.5), (-1.0, 1.0)):
        place.put(room, "study_chair", chair_x, y + side * 0.78, 0.0 if side < 0 else 180.0)


def furnish_archive(place: Placer) -> None:
    """Secret archive after real archive stacks: a row of presses on the west wall and three double rows back to
    back, 1.4 m aisles between them, running toward the reading room by the door; scroll racks, drawers and a
    safe on the middle wall; the low door to the catacombs kept clear at the south."""
    room = "arquivo"
    west, east, north, south = OUTER[0], MIDDLE_WALL_X - 0.25, CROSS_WALL_Y - 0.25, OUTER[2]
    stack_y = (12.05, 14.15, 16.25)

    for index, case_y in enumerate((*stack_y, 18.35, 20.45)):
        place.against(room, "west", "archive_cabinet", case_y, west, seed=index)

    for row_index, (left, right) in enumerate(((-10.04, -9.42), (-7.4, -6.78), (-4.76, -4.14))):
        for case_index, case_y in enumerate(stack_y):
            place.put(room, "archive_cabinet", left, case_y, -90.0, seed=20 + row_index * 7 + case_index)
            place.put(room, "archive_cabinet", right, case_y, 90.0, seed=40 + row_index * 7 + case_index)

    place.put(room, "rolling_ladder", -11.4, 16.25, 90.0)
    place.put(room, "rolling_ladder", -8.4, 14.15, 90.0)
    place.put(room, "book_cart", -11.0, 18.8, 90.0)

    for index, case_y in enumerate((12.1, 13.7)):
        place.against(room, "east", "scroll_rack", case_y, east, seed=60 + index)

    place.against(room, "east", "deposit_boxes", 15.6, east)
    place.against(room, "east", "card_catalog", 17.4, east)
    place.against(room, "east", "iron_safe", 18.9, east)
    place.against(room, "north", "scroll_rack", -11.0, north, seed=70)
    place.against(room, "north", "long_case_clock", -2.6, north)
    reading_table_with_chairs(place, room, -8.6, 20.6)
    reading_table_with_chairs(place, room, -3.4, 20.6)
    place.put(room, "lectern", -1.0, 21.8, -90.0)
    place.put(room, "globe_stand", -11.4, 22.4)

    for lantern_x, lantern_y in ((-8.6, 20.6), (-3.4, 20.6), (-8.4, 14.15), (-5.77, 14.15), (-2.9, 12.0)):
        place.put(room, "hanging_lantern", lantern_x, lantern_y)

    place.put(room, "iron_gate", CATACOMB_DOOR[0] - 0.45, south + 0.08, 0.0)


def furnish_cabinet(place: Placer) -> None:
    """Cabinet of curiosities after the old engraved collections: every wall lined with cases and shelves, a dragon
    skull hung over a summoning circle in the middle, display tables, an alchemist's corner, armour and crowns."""
    room = "gabinete"
    west, east, north, south = MIDDLE_WALL_X + 0.25, OUTER[1], CROSS_WALL_Y - 0.25, OUTER[2]
    circle = (6.3, 15.0)

    place.put(room, "summoning_circle", *circle)
    place.put(room, "dragon_skull_hanging", circle[0], circle[1])

    for index, (corner_x, corner_y) in enumerate(itertools.product((-1.0, 1.0), (-1.0, 1.0))):
        place.put(room, "candle_stand", circle[0] + corner_x * 1.6, circle[1] + corner_y * 1.6, lit=index % 3 == 0)

    place.put(room, "rune_pillar", circle[0] - 2.5, circle[1])
    place.put(room, "rune_pillar", circle[0] + 2.5, circle[1], lit=False)
    place.put(room, "crystal_ball_pedestal", circle[0], circle[1] + 2.3, 180.0)

    for index, (wall_y, name) in enumerate(((11.4, "relic_shelf"), (13.3, "trophy_case"), (15.2, "relic_shelf"), (17.6, "bottle_shelf"), (19.8, "alembic_table"), (22.0, "potion_wall"))):
        place.against(room, "east", name, wall_y, east, seed=80 + index)

    for index, (wall_x, name) in enumerate(((1.6, "world_map_wall"), (4.2, "relic_shelf"), (6.3, "star_tapestry"), (8.4, "trophy_case"), (10.3, "relic_shelf"))):  # o canto leste fica com a estante da parede leste
        place.against(room, "south", name, wall_x, south, seed=90 + index)

    for index, (wall_y, name) in enumerate(((12.0, "tall_bookcase"), (14.1, "tall_bookcase_slim"), (16.2, "jewel_case"), (17.9, "armor_stand_a"), (19.0, "armor_stand_a"), (20.6, "enchant_table"), (22.3, "skeleton_stand"))):
        place.against(room, "west", name, wall_y, west, seed=100 + index)

    for index, (wall_x, name) in enumerate(((1.4, "relic_shelf"), (8.4, "relic_shelf"), (10.5, "deposit_boxes"))):
        place.against(room, "north", name, wall_x, north, seed=110 + index)

    place.put(room, "display_table", 3.3, 19.6, 0.0)
    place.put(room, "display_table", 8.8, 19.6, 0.0)
    place.put(room, "celestial_globe", 3.3, 21.4)
    place.put(room, "astrolabe", 8.8, 21.4)
    place.put(room, "giant_hourglass", 11.6, 18.7)
    place.put(room, "masterwork_plinth_a", 2.4, 13.2)
    place.put(room, "hanging_lantern", 3.3, 19.6)
    place.put(room, "hanging_lantern", 8.8, 19.6)


def add_lights(b: Builder, place: Placer) -> int:
    """At most LIGHTS_PER_ROOM real lights per room, in placement order; the other candles only glow."""
    kept = [light for room, room_lights in place.lights.items() for light in room_lights[:LIGHTS_PER_ROOM.get(room, 6)]]

    for position, color, energy, light_range in kept:
        b.light(tuple(position), color, energy, light_range)

    return len(kept)


def build_crypt() -> dict:
    b = Builder("cathedral_crypt")
    place = Placer(b)

    build_floor_and_ceiling(b)
    build_outer_walls(b)
    build_inner_walls(b)
    build_stair(b)
    build_piers_and_ribs(b)
    build_catacomb_shell(b)
    furnish_saints(place)
    furnish_archive(place)
    furnish_cabinet(place)
    furnish_catacombs(place)
    light_count = add_lights(b, place)
    place.report()

    return b.finish(OUTPUT_DIR / "cathedral_crypt.gltf", {"lights_kept": light_count})


# ---------- the monument over the stair ----------

def build_monument() -> dict:
    """Long stone plinth (it covers the opening in the nave floor) with panels and a carved tablet, a praying saint
    on top, candlesticks and flowers at its feet. Origin: middle of the face against the wall, on the nave floor;
    the plinth reaches -X into the aisle."""
    b = Builder("cathedral_crypt_monument")
    depth, length, height = MONUMENT_SIZE

    b.box((-depth, -length / 2.0, 0.0), (0.0, length / 2.0, 0.14), "stone", srgb(DARK_STONE))
    b.box((-depth + 0.06, -length / 2.0 + 0.06, 0.14), (0.0, length / 2.0 - 0.06, height - 0.12), "stone", srgb(CRYPT_STONE))
    b.box((-depth - 0.03, -length / 2.0 - 0.03, height - 0.12), (0.0, length / 2.0 + 0.03, height), "stone", srgb(MARBLE))

    for panel_y in (-1.05, 1.05):
        b.box((-depth + 0.04, panel_y - 0.45, 0.26), (-depth + 0.06, panel_y + 0.45, height - 0.24), "stone", srgb("A89A82"))

    b.box((-depth + 0.03, -0.5, 0.3), (-depth + 0.06, 0.5, height - 0.28), "stone", srgb(MARBLE))

    for line in range(4):
        half = 0.38 if line == 0 else 0.3
        b.box((-depth + 0.025, -half, height - 0.38 - line * 0.08), (-depth + 0.03, half, height - 0.36 - line * 0.08), "paint", srgb("4A4038"))

    add_standing_statue(b, Matrix.Translation((-depth / 2.0, 0.0, height)) @ Matrix.Rotation(math.radians(-90.0), 4, "Z"))

    for candle_y in (-1.35, 1.35):
        frame = Matrix.Translation((-depth / 2.0, candle_y, height)) @ Matrix.Rotation(math.radians(-90.0), 4, "Z")
        PROPS["flower_vase"]["build"](b, frame, seed=int(candle_y * 10))

    return b.finish(OUTPUT_DIR / "cathedral_crypt_monument.gltf", {"size": MONUMENT_SIZE})


if __name__ == "__main__":
    sidecar = build_crypt()
    print(f"BUILT cathedral_crypt: aabb {sidecar['aabb_min']} .. {sidecar['aabb_max']}, lights {len(sidecar['lights'])}")
    sidecar = build_monument()
    print(f"BUILT cathedral_crypt_monument: aabb {sidecar['aabb_min']} .. {sidecar['aabb_max']}")
