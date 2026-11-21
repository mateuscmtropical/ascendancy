"""Model the big walk-in shops of the market squares (docs/research/shops.md): one third to one half of a block each.

Outputs per shop, each with a JSON sidecar (AABB, doors, lights, markers):
  art/town/shops/shop_<type>.gltf            shell: walls with real openings, floor, ceiling, posts, roof, awnings, colliders
  art/town/shops/shop_<type>_interior.gltf   furniture and goods fused in one mesh (hidden from afar by shop_interior.gd)

Same coords as build_town_houses.py: lot front on Y = 0, street toward -Y, u across, d into the lot, z up.
Furniture comes from the prop libraries tools_src/shop_props_*.py (PROPS contract in shop_props_common.py); the
plans of each shop live in shop_layouts.py. A prop named by a plan but not modelled yet is reported and skipped.

Usage:
  blender -b --factory-startup -P tools_src/build_market_shops.py -- [shop_type ...]
"""

import importlib
import itertools
import json
import math
import random
import sys
from pathlib import Path

from mathutils import Matrix

sys.path.insert(0, str(Path(__file__).resolve().parent))

import build_town_houses as town  # noqa: E402
import shop_layouts  # noqa: E402
from orphanage_wing_common import CORRIDOR  # noqa: E402
from build_hub_scene import CASARAO_UPPER_FLOOR, SHOP_LOTS, shop_lots, town_lots  # noqa: E402
from build_town_houses import STONE, WALL, WOOD, WOOD_DARK_BAND, WOOD_LIGHT_BAND, Builder, House, Opening, srgb  # noqa: E402

PROP_MODULES = ("shop_props_common", "shop_props_arms", "shop_props_food", "shop_props_arcane", "shop_props_manor", "shop_props_orphanage", "shop_props_orphanage_ground", "shop_props_convent")
PLAN_FOLDER = ""  # --plan=<pasta>: grava a planta (pegadas dos móveis) de cada salão mobiliado
CEILING_SLAB = 0.4
PIER = 0.6  # parede cheia entre vãos e nos cantos da fachada
VITRINE_PITCH = 3.0  # uma vitrine a cada tantos metros de fachada livre
VITRINE_SILL = 0.7
DOOR_CLEARANCE = 3.0  # faixa livre atrás da porta
BOARD_WIDTH = 0.6
JOIST_SPACING = 1.6
POST = 0.32
PLINTH_MARGIN = 0.06  # a sapata de pedra passa isso do pilar de cada lado
LIGHT_SPACING = 9.0
LIGHT_ROWS = (0.28, 0.72)  # frações da profundidade
AWNING_REACH = 1.7
AWNING_STRIPE = 0.5
SIDE_WINDOW_PITCH = 4.0
SIDE_WINDOW_SILL = 1.2
TALL_HALL = 6.0  # salões a partir desta altura de forro levam as janelas laterais no alto (clerestório)
HIGH_SIDE_WINDOW_DROP = 3.6  # peitoril dessas janelas altas: forro menos isto
BACK_WINDOW_PITCH = 4.0
BACK_AXIS_PIER = 1.8  # meia largura da parede cega no eixo do fundo (mapa, tapeçaria, estandarte atrás do balcão)
CHIMNEY_CLEARANCE = 1.0  # janela do fundo não abre a menos disto do eixo de uma chaminé encostada nele
WALL_PROP_REACH = 0.8  # móvel a menos disto de uma parede conta como encostado nela (checagem das janelas)
COLLIDER_MAX_HEIGHT = 2.4
PLINTH_HEIGHT = 0.5
BLIND_ARCH_MIN_SILL = 2.8  # janela com peitoril a partir disto ganha arco cego embaixo (a base da parede não fica nua)
BLIND_ARCH_BASE_GAP = 0.35  # do topo do embasamento ao pé do arco cego
BLIND_ARCH_TOP_GAP = 0.5  # do topo do arco cego ao peitoril da janela de cima
BLIND_ARCH_FRAME = 0.12
BLIND_ARCH_SHADE = 0.82  # painel do arco: a cor da parede um pouco mais escura
FLOOR_TOP = 0.05  # acima do calçamento da quadra, para o piso do salão não brigar com ele
FILL_PITCH = 2.5  # passo da grade de ilhas com que fill_floor enche o chão livre
FILL_AISLE = 0.55
FILL_LANE = 1.9  # meia largura do corredor que fica livre da porta ao balcão
FILL_BACK = 6.0  # fundo do salão que fica para o balcão e o lojista
ISLAND_AISLE = 0.9  # folga em volta de cada ilha que scatter() põe no meio do salão
FEATURE_LIGHT_LIMIT = 3  # luzes de móveis por andar nas lojas do comércio (a grade do forro faz o resto)
CONTACT_SHADOW_LAYERS = (0.0, 0.08, 0.16)  # quanto cada camada da sombra de contato passa da pegada do móvel
CONTACT_SHADOW_ALPHA = 0.13  # cada camada; no meio da pegada somam-se
CONTACT_SHADOW_LIFT = 0.004  # acima do piso, para não brigar com ele
DADO_HEIGHT = 1.2  # a barra pintada de baixo das paredes dos cômodos do orfanato
SKIRTING_HEIGHT = 0.14
SKIRTING_DEPTH = 0.04
DADO_DEPTH = 0.02
RAIL_HEIGHT = 0.06
RAIL_DEPTH = 0.05
DOOR_FRAME_WIDTH = 0.1  # batente e guarnição de uma porta de divisória
DOOR_FRAME_DEPTH = 0.03
DOOR_LEAF_THICKNESS = 0.05
DOOR_LEAF_OFFSET = 0.07  # a folha aberta fica a esta distância da parede, por fora do rodapé e do friso
PARTITION_DOOR_LANE = 1.0  # chão livre dos dois lados de uma porta de divisória
HATCH_LEDGE = 0.12  # quanto a tábua do peitoril de um passa-pratos sai de cada face da parede
PLANK_LENGTH_RANGE = (2.4, 5.2)  # comprimento das tábuas do piso, de junta a junta
PLANK_SHADE_RANGE = (0.84, 1.08)
CEILING_PLANK_WIDTH = 0.3
CEILING_PLANK_SHADE_RANGE = (0.88, 1.06)  # o forro de tábua é de uma estação só: pouca variação
GIRDER_WIDTH = 0.3
PICTURE_RAIL_HEIGHT = 2.5  # os quadros pendem deste friso
PICTURE_RAIL_DEPTH = 0.035
PICTURE_CORD = 0.18  # do friso ao topo do quadro
CORNICE_HEIGHT = 0.2
CORNICE_TINT = "EFE6D2"
STONE_PATCH_LIFT = 0.012  # o lajeado de um cômodo molhado fica este tanto acima do piso de tábua
WALL_FINISHES = {  # nome -> cor da barra pintada e do rodapé/friso (os planos escolhem por nome, ver shop_layouts.py)
    "dormitory": dict(dado="C9984F", trim="5A3A26"),
}  # material="azulejo" põe azulejo no lugar do reboco pintado (dado = tinta sobre a textura, uv opcional)
AZULEJO_TEXTURE = town.TEXTURE_DIR / "T_Azulejo_BaseColor.png"  # pintada por build_casarao.py, versionada

for wing_module in shop_layouts.WING_MODULES:
    WALL_FINISHES.update(wing_module.NEW_WALL_FINISHES)
INNER_PANE_DEPTH = 0.2  # o vidro de dentro das janelas do casarão, atrás do vidro aceso da fachada
AMBIENT_MARGIN = 0.1  # o volume de ambiência do casarão entra isto nas paredes, para o reboco ficar dentro dele

CASARAO_STOREYS = (CASARAO_UPPER_FLOOR, 5.6)  # o casarão em frente à catedral: térreo e andar nobre, os dois de salões andáveis
INNER_DOOR = (sum(CORRIDOR) / 2.0, 1.8, 3.0, "round")  # (d do eixo, largura, altura, topo): portas internas no eixo do corredor
CASARAO_HALL = dict(  # o casarão (build_casarao.py) veste a fachada e põe o telhado; cada salão faz só o seu andar
    casarao=True, axis_bay=3.0, sill=0.9, vitrine_top="round", vitrine_apex=4.0, vitrine_width=1.4, side_window=(1.4, 0.9, 3.1, "round"),
    archetype="palacete", wall="cal", roof="terracota", accent="verde", roof_shape=("hip", dict(pitch=25.0)), awning=None, door=(0.0, 3.0, 4.4, "round"),
    fixture_light=dict(share=0.7, energy=1.5, limit=24),  # à noite a luz sai dos lustres e arandelas (todos acesos, na cor da sala, mais fortes); a grade do forro é só a luz do dia
)
CASARAO_WING = dict(CASARAO_HALL, storeys=CASARAO_STOREYS[:1], street_door=False)  # salão do térreo: entra-se pelo vestíbulo
CASARAO_UPPER = dict(CASARAO_WING, storeys=CASARAO_STOREYS[1:], sill=0.12, vitrine_apex=3.12, vitrine_width=1.3)  # andar nobre: janelas de sacada

WING_FIXTURE_LIGHT = dict(share=0.7, energy=0.8, limit=40, night_only=True)  # the rooms of a wing light only at night, about 8 real lamps a room
WING_NIGHT_AMBIENT = 0.08  # ambient of a wing hall at night (the shared interior level is for the big halls)
SHOPS = {  # tipo -> casca; door = (u, largura, altura, topo); roof_shape como ARCHETYPE_SPECS; awning = (cor, cor)
    "smith": dict(archetype="pedra", wall="cinza", roof="ardosia", accent="oxido", storeys=(5.2,), roof_shape=("gable_parallel", dict(pitch=30.0, eave_front=0.5, eave_back=0.4)), features=("dormers",), floor="stone", awning=("B5533F", "F2E6CF"), door=(-5.0, 2.6, 3.2, "segment"), open_bays=((7.4, 7.2),), chimney=dict(u=8.2, d=18.3, extra=1.5, pots=0, material="stone"), light="FFC890"),
    "guild": dict(archetype="palacete", wall="clara", roof="ardosia", accent="vinho", storeys=(7.4, 3.4), roof_shape=("hip", dict(pitch=24.0, eave_front=0.9, eave_back=0.5)), floor="stone", awning=("7A2F3A", "D9A441"), door=(0.0, 3.2, 4.2, "round"), features=("eave_brackets",), quoins=True, cornice=True, light="FFD9A0"),
    "tavern": dict(archetype="tudor", wall="creme", roof="velha", accent="vinho", storeys=(5.0, 3.0), roof_shape=("gable_parallel", dict(pitch=38.0, eave_front=0.5, eave_back=0.4)), floor="wood", awning=("7A2F3A", "F2E6CF"), door=(0.0, 2.6, 3.0, "pointed"), features=("half_timber",), jetty=0.35, chimney=dict(u=-7.4, d=9.7, extra=1.2, pots=2), light="FFC27A"),
    "armor": dict(archetype="hanseatica", wall="tijolo", roof="terracota", accent="vinho", storeys=(4.6, 3.2), roof_shape=("gable_street", dict(pitch=36.0, gable="stepped")), floor="stone", awning=("7A2F3A", "D8DCE4"), door=(0.0, 2.4, 3.0, "round"), features=("stone_bands",), light="FFD9A0"),
    "general": dict(archetype="sobrado", wall="creme", roof="terracota", accent="verde", storeys=(4.4, 3.2), roof_shape=("hip", dict(pitch=26.0, eave_front=0.6, eave_back=0.5)), floor="wood", awning=("B5533F", "F4EFE6"), door=(0.0, 2.4, 2.9, "segment"), features=("iron_balcony", "finials"), quoins=True, cornice=True, light="FFD9A0"),
    "magic": dict(archetype="torre", wall="lilas", roof="ardosia", accent="azul", storeys=(5.6, 3.0), roof_shape=("gable_street", dict(pitch=42.0, gable="bell")), floor="wood", awning=("4A3A8E", "C9B6D9"), door=(0.0, 2.2, 3.2, "pointed"), light="C9B0FF"),
    "alchemy": dict(archetype="fachwerk", wall="salvia", roof="velha", accent="verde", storeys=(4.6, 2.9), roof_shape=("gable_parallel", dict(pitch=40.0, eave_front=0.5, eave_back=0.4)), floor="wood", awning=("2F6B4F", "D9E8B0"), door=(0.0, 2.2, 2.9, "round"), features=("half_timber",), jetty=0.3, chimney=dict(u=-6.0, d=15.0, extra=1.2, pots=2), light="C8F0B0"),
    "tailor": dict(archetype="mediterranea", wall="rosa", roof="clara", accent="vinho", storeys=(4.4, 3.0), roof_shape=("gable_street", dict(pitch=32.0, gable="scroll")), floor="wood", awning=("C0517A", "F4EFE6"), door=(0.0, 2.2, 2.9, "round"), features=("flower_boxes",), light="FFDCC0"),
    "library": dict(CASARAO_WING, floor="wood", light="FFF3E6", day_light="FFDFA8", inner_doors={"left": INNER_DOOR}, fixture_light=WING_FIXTURE_LIGHT, night_ambient=WING_NIGHT_AMBIENT),
    "school": dict(CASARAO_WING, floor="wood", light="FFF4E8", day_light="FFE2B0", inner_doors={"right": INNER_DOOR}, fixture_light=WING_FIXTURE_LIGHT, night_ambient=WING_NIGHT_AMBIENT),
    "reading": dict(CASARAO_UPPER, floor="wood", light="FFFAF4", day_light="FFE2B8", inner_doors={"left": INNER_DOOR}, fixture_light=WING_FIXTURE_LIGHT, night_ambient=WING_NIGHT_AMBIENT),
    "seminary": dict(CASARAO_UPPER, floor="wood", light="FFFAF4", day_light="FFDCB0", inner_doors={"right": INNER_DOOR}, fixture_light=WING_FIXTURE_LIGHT, night_ambient=WING_NIGHT_AMBIENT),
    "vestibule": dict(CASARAO_HALL, storeys=CASARAO_STOREYS, floor="stone", light="FFF5EA", day_light="FFE4BC", door=(0.0, 3.4, 4.6, "round"), inner_doors={"left": INNER_DOOR, "right": INNER_DOOR}, door_leaves=False, shell="casarao_vestibule", fixture_light=WING_FIXTURE_LIGHT, night_ambient=WING_NIGHT_AMBIENT),  # lamps lit only at night, as in the wings
}


def load_props() -> dict:
    """PROPS of every prop library already written (the libraries land one by one)."""
    props = {}

    for module_name in PROP_MODULES:
        if (Path(__file__).resolve().parent / f"{module_name}.py").exists():
            props.update(importlib.import_module(module_name).PROPS)

    return props


PROPS = load_props()
SCENES = importlib.import_module("shop_props_manor").SCENES
PICTURE_CENTRE = importlib.import_module("shop_props_manor").PAINTING_CENTRE


class Room:
    """Measurements of one shop: body, inner hall bounds and heights (facade coords)."""

    def __init__(self, shop_type: str) -> None:
        spec = SHOPS[shop_type]
        width, depth = SHOP_LOTS[shop_type]

        self.shop_type = shop_type
        self.spec = spec
        self.house = House(width, depth, spec["storeys"], spec["wall"], spec["roof"], spec["accent"], town.hash_seed(shop_type))
        self.house.jetty = spec.get("jetty", 0.0)
        self.half = self.house.half
        self.depth = self.house.depth
        self.storey = spec["storeys"][0]
        self.ceiling = self.storey - CEILING_SLAB
        self.left, self.right = -self.half + WALL, self.half - WALL
        self.front, self.back = WALL, self.depth - WALL
        self.exposed = next(lot["exposed"] for lot in shop_lots(town_lots()) if lot["shop"] == shop_type)
        self.door = spec["door"]
        self.has_street_door = spec.get("street_door", True)
        self.inner_doors = spec.get("inner_doors", {})  # lado -> INNER_DOOR: passagem para o salão vizinho do casarão
        self.plan = shop_layouts.PLANS.get(shop_type, {})
        self.keeper = self.plan.get("keeper", (spec["door"][0], self.back - 2.4))
        self.posts = self.plan.get("posts", self.default_posts())
        self.partitions = self.plan.get("partitions", ())

    def default_posts(self) -> list:
        """Posts on an odd number of ~6 m bays (the door axis stays free), two rows deep."""
        bays = max(3, 2 * round((2.0 * self.half / 6.0 - 1.0) / 2.0) + 1)
        post_us = [-self.half + 2.0 * self.half * index / bays for index in range(1, bays)]

        return list(itertools.product(post_us, (self.depth / 3.0, 2.0 * self.depth / 3.0)))


# ---------- walls ----------

def close_opening_top(b: Builder, room: Room, frame: Matrix, opening: Opening) -> None:
    house = room.house
    half = opening.width / 2.0

    town.wall_piece(b, (opening.u - half, 0.0, opening.apex), (opening.u + half, WALL, room.storey), house.wall_material, house.wall_tint, frame)

    if opening.top != "flat":
        b.prism(opening.arc() + [(opening.u - half, opening.apex), (opening.u + half, opening.apex)], 0.0, WALL, house.wall_material, house.wall_tint, frame=frame)


def dress_door(b: Builder, room: Room, frame: Matrix, opening: Opening) -> None:
    """Flush stone threshold, moulding and two leaves fixed open into the hall."""
    house = room.house
    half = opening.width / 2.0
    leaf = half - 0.02
    leaf_height = opening.spring - 0.05
    swing = math.radians(100.0)

    b.box((opening.u - half, -0.3, 0.0), (opening.u + half, WALL, FLOOR_TOP + 0.005), "trim", house.trim_tint, frame=frame)
    town.open_frame(b, opening, 0.18, -0.06, 0.0, house.trim_tint, town.TRIM_BLOCK_BAND, frame)

    for side_sign in (-1, 1):
        hinge_u = opening.u + side_sign * half
        tip = (hinge_u - side_sign * leaf * math.cos(swing), WALL + leaf * math.sin(swing))
        b.beam((hinge_u, WALL + 0.03, 0.02 + leaf_height / 2.0), (tip[0], tip[1], 0.02 + leaf_height / 2.0), leaf_height, 0.07, "paint", house.accent, frame=frame)

    house.doors.append({"x": round(opening.u - room.half, 3), "width": opening.width, "enterable": True})


def dress_vitrine(b: Builder, room: Room, frame: Matrix, opening: Opening) -> None:
    """Shop window: low sill wall, glass pane with glazing bars, moulded frame."""
    house = room.house
    half = opening.width / 2.0
    bar_count = max(1, round(opening.width / 0.9)) - 1
    bar_tint = srgb(WOOD["escura"])

    town.wall_piece(b, (opening.u - half, 0.0, 0.0), (opening.u + half, WALL, opening.bottom), house.wall_material, house.wall_tint, frame)
    b.prism(opening.outline(), 0.12, 0.14, "shopfront", frame=frame)

    if room.spec.get("casarao"):
        b.pane(opening.outline(), INNER_PANE_DEPTH, "inner_glass", frame=frame)

    b.collider((opening.u - half, 0.08, opening.bottom), (opening.u + half, 0.2, opening.apex), frame)
    town.open_frame(b, opening, 0.12, -0.05, 0.0, house.trim_tint, town.TRIM_SMOOTH_BAND, frame)
    b.box((opening.u - half - 0.1, -0.12, opening.bottom - 0.08), (opening.u + half + 0.1, WALL + 0.12, opening.bottom), "trim", house.trim_tint, frame=frame)
    b.box((opening.u - half, 0.1, opening.spring - 0.03), (opening.u + half, 0.16, opening.spring + 0.03), "paint", bar_tint, frame=frame)

    for bar_index in range(bar_count):
        bar_u = opening.u - half + opening.width * (bar_index + 1) / (bar_count + 1)
        b.box((bar_u - 0.025, 0.1, opening.bottom), (bar_u + 0.025, 0.16, opening.spring), "paint", bar_tint, frame=frame)


def dress_open_bay(b: Builder, room: Room, frame: Matrix, opening: Opening) -> None:
    """Open bay (forge yard): a timber lintel on the facade, nothing in the gap."""
    half = opening.width / 2.0

    b.box((opening.u - half - 0.2, -0.1, opening.apex - 0.05), (opening.u + half + 0.2, 0.0, opening.apex + 0.35), "wood", room.house.wood_tint, frame=frame, uv=("band", *WOOD_DARK_BAND, 1.5))


def dress_inner_door(b: Builder, room: Room, frame: Matrix, opening: Opening) -> None:
    """Doorway to the next hall of the casarão: threshold through the wall, a moulding on the hall side and two
    leaves folded back against it (the vestibule keeps its side bare: one pair of leaves per doorway)."""
    house = room.house
    half = opening.width / 2.0
    leaf = half - 0.02
    leaf_height = opening.spring - 0.05
    swing = math.radians(165.0)

    b.box((opening.u - half, 0.0, 0.0), (opening.u + half, WALL, FLOOR_TOP + 0.005), "trim", house.trim_tint, frame=frame)
    b.collider((opening.u - half, 0.0, 0.0), (opening.u + half, WALL, FLOOR_TOP), frame)
    town.open_frame(b, opening, 0.2, WALL, WALL + 0.07, house.trim_tint, town.TRIM_SMOOTH_BAND, frame)

    if not room.spec.get("door_leaves", True):
        return

    for side_sign in (-1, 1):
        hinge_u = opening.u + side_sign * (half + 0.2)
        tip = (hinge_u - side_sign * leaf * math.cos(swing), WALL + 0.1 + leaf * math.sin(swing))
        b.beam((hinge_u, WALL + 0.1, FLOOR_TOP + leaf_height / 2.0), (tip[0], tip[1], FLOOR_TOP + leaf_height / 2.0), leaf_height, 0.07, "paint", house.accent, frame=frame)


def dress_balcony_door(b: Builder, room: Room, frame: Matrix, opening: Opening) -> None:
    """Door of the upper floor to a balcony the casarão hangs outside: threshold and two glazed leaves open inward."""
    house = room.house
    half = opening.width / 2.0
    leaf = half - 0.02
    leaf_height = opening.spring - 0.05
    swing = math.radians(105.0)

    b.box((opening.u - half, 0.0, 0.0), (opening.u + half, WALL, FLOOR_TOP + 0.005), "trim", house.trim_tint, frame=frame)
    b.collider((opening.u - half, 0.0, 0.0), (opening.u + half, WALL, FLOOR_TOP), frame)

    for side_sign in (-1, 1):
        hinge_u = opening.u + side_sign * half
        tip = (hinge_u - side_sign * leaf * math.cos(swing), WALL + leaf * math.sin(swing))
        b.beam((hinge_u, WALL + 0.03, FLOOR_TOP + leaf_height / 2.0), (tip[0], tip[1], FLOOR_TOP + leaf_height / 2.0), leaf_height, 0.06, "paint", house.accent, frame=frame)


def dress_arch(b: Builder, room: Room, frame: Matrix, opening: Opening) -> None:
    """Open archway in an inner wall: a moulding on its outer face."""
    town.open_frame(b, opening, 0.18, -0.06, 0.0, room.house.trim_tint, town.TRIM_SMOOTH_BAND, frame)


OPENING_DRESSING = {"door": dress_door, "vitrine": dress_vitrine, "open": dress_open_bay, "inner": dress_inner_door, "balcony": dress_balcony_door, "arch": dress_arch}


def pierced_wall(b: Builder, room: Room, frame: Matrix, length: float, openings: list) -> None:
    """Wall in its own frame: u from 0 to length seen from outside, outer face on d = 0, WALL thick toward +d."""
    house = room.house
    edges = sorted((opening.u - opening.width / 2.0, opening.u + opening.width / 2.0) for opening in openings)
    solid_from = [0.0] + [right for _, right in edges]
    solid_to = [left for left, _ in edges] + [length]

    for u_from, u_to in zip(solid_from, solid_to):
        if u_to - u_from > 1e-3:
            town.wall_piece(b, (u_from, 0.0, 0.0), (u_to, WALL, room.storey), house.wall_material, house.wall_tint, frame)

    for opening in openings:
        close_opening_top(b, room, frame, opening)
        OPENING_DRESSING[opening.kind](b, room, frame, opening)


def evenly(span_from: float, span_to: float, pitch: float) -> list:
    """(centre, room) of the openings that fit a wall span, one every pitch metres."""
    count = int((span_to - span_from) // pitch)

    return [(span_from + (span_to - span_from) * (index + 0.5) / count, (span_to - span_from) / count) for index in range(count)]


def front_openings(room: Room) -> list:
    """Door, open bays and as many shop windows as fit the free stretches of the facade (wall-local u = facade u + half)."""
    door_u, door_width, door_height, door_top = room.door
    axis_bay = room.spec.get("axis_bay", door_width)  # casarão: o mesmo ritmo de vãos em todos os salões, com ou sem porta
    vitrine_top = room.spec.get("vitrine_apex", min(room.ceiling - 0.6, 3.4))
    bays = [(u, width, "open") for u, width in room.spec.get("open_bays", ())]
    taken = sorted([(door_u - axis_bay / 2.0, door_u + axis_bay / 2.0)] + [(u - width / 2.0, u + width / 2.0) for u, width, _ in bays])
    free_from = [-room.half] + [right for _, right in taken]
    free_to = [left for left, _ in taken] + [room.half]
    spots = [spot for span_from, span_to in zip(free_from, free_to) for spot in evenly(span_from + PIER, span_to - PIER, VITRINE_PITCH)]
    spots += [] if room.has_street_door else [(door_u, axis_bay)]  # sem porta de rua, o vão do eixo é mais uma janela
    sill = room.spec.get("sill", VITRINE_SILL)
    vitrines = [Opening(u + room.half, room.spec.get("vitrine_width", space - 0.9), sill, vitrine_top - sill, room.spec.get("vitrine_top", "segment"), kind="vitrine") for u, space in spots]
    door = Opening(door_u + room.half, door_width, 0.0, door_height, door_top, kind="door")
    open_bays = [Opening(u + room.half, width, 0.0, min(room.ceiling - 0.5, 3.8), "flat", kind="open") for u, width, _ in bays]

    return ([door] if room.has_street_door else []) + open_bays + vitrines


def inner_door_openings(room: Room) -> dict:
    """Doorways to the neighbour halls, side -> [Opening] in wall-local coords (the walls run as in wall_frames)."""
    along = {"right": lambda d: d - WALL, "left": lambda d: room.depth - WALL - d}

    return {side: [Opening(along[side](d), width, 0.0, height, top, kind="inner")] for side, (d, width, height, top) in room.inner_doors.items()}


def room_openings(room: Room) -> dict:
    """Every opening of the four walls of a hall, side -> [Opening] in wall-local coords."""
    openings = {"front": front_openings(room), **wall_windows(room)}
    inner = inner_door_openings(room)

    return {side: found + inner.get(side, []) for side, found in openings.items()}


def entry_point(room: Room) -> list:
    """Godot model coords (x, z) of the first inner doorway, on the hall side of the wall."""
    side, (d, _, _, _) = next(iter(room.inner_doors.items()))

    return [round({"left": room.left, "right": room.right}[side], 3), round(-d, 3)]


def side_windows(room: Room, length: float) -> list:
    """Windows of an exposed side wall; halls taller than TALL_HALL get them high, over the wall furniture."""
    is_tall = room.ceiling >= TALL_HALL
    sill = room.ceiling - HIGH_SIDE_WINDOW_DROP if is_tall else SIDE_WINDOW_SILL
    width, sill, height, top = room.spec.get("side_window", (1.5, sill, min(2.2, room.ceiling - 1.8), "segment"))

    return [Opening(u, width, sill, height, top, kind="vitrine") for u, _ in evenly(1.0, length - 1.0, SIDE_WINDOW_PITCH)]


def back_windows(room: Room) -> list:
    """High windows of the back wall in pairs around the axis (the wall behind the counter stays blind for the
    centrepiece), none in front of a chimney stack set against that wall. Wall-local u = half - facade u."""
    high_sill = room.ceiling - 1.9
    chimney = room.spec.get("chimney")
    chimney_us = [chimney["u"]] if chimney and chimney["d"] > room.depth - 2.0 else []
    offsets = [offset for offset, _ in evenly(BACK_AXIS_PIER, room.half - 1.0, BACK_WINDOW_PITCH)]
    facade_us = sorted([-offset for offset in offsets] + offsets)
    clear_us = [u for u in facade_us if all(abs(u - chimney_u) > 0.8 + CHIMNEY_CLEARANCE for chimney_u in chimney_us)]

    return [Opening(room.half - u, 1.6, high_sill, 1.4, "segment", kind="vitrine") for u in clear_us]


def wall_windows(room: Room) -> dict:
    """Openings of the back wall and of the sides that face a street, in wall-local coords (shell and furniture
    check read the same list)."""
    side_length = room.depth - 2.0 * WALL
    side = side_windows(room, side_length)

    return {"back": back_windows(room), "left": side if "left" in room.exposed else [], "right": side if "right" in room.exposed else []}


def window_spans(room: Room) -> dict:
    """The same windows in hall coords: side -> [(from, to, sill)] along the wall (u on the back, d on the sides),
    sorted from the start of the wall (left corner on the back, the facade on the sides)."""
    to_hall = {
        "back": lambda opening: (room.half - opening.u - opening.width / 2.0, room.half - opening.u + opening.width / 2.0),
        "right": lambda opening: (WALL + opening.u - opening.width / 2.0, WALL + opening.u + opening.width / 2.0),
        "left": lambda opening: (room.depth - WALL - opening.u - opening.width / 2.0, room.depth - WALL - opening.u + opening.width / 2.0),
    }

    return {side: sorted((*to_hall[side](opening), opening.bottom) for opening in openings) for side, openings in wall_windows(room).items()}


def flat_window(b: Builder, room: Room, frame: Matrix, opening: Opening) -> None:
    """Window painted on a solid wall (upper storeys of the exposed sides)."""
    b.prism(opening.outline(0.1), -0.05, 0.0, "trim", room.house.trim_tint, frame=frame, uv=("band", *town.TRIM_SMOOTH_BAND, 1.0))
    b.prism(opening.outline(), -0.07, -0.05, "glass", frame=frame)
    b.box((opening.u - 0.02, -0.085, opening.bottom), (opening.u + 0.02, -0.07, opening.spring), "paint", town.WHITE, frame=frame)


def blind_arch(b: Builder, room: Room, frame: Matrix, window: Opening) -> None:
    """Round-headed blind arch under a high window: a moulded frame and a darker panel standing proud of it."""
    house = room.house
    bottom = PLINTH_HEIGHT + BLIND_ARCH_BASE_GAP
    arch = Opening(window.u, window.width, bottom, window.bottom - BLIND_ARCH_TOP_GAP - bottom, "round")
    panel_tint = tuple(channel * BLIND_ARCH_SHADE for channel in house.wall_tint)

    b.prism(arch.outline(BLIND_ARCH_FRAME), -0.08, 0.0, "trim", house.trim_tint, frame=frame, uv=("band", *town.TRIM_SMOOTH_BAND, 1.0))
    b.prism(arch.outline(), -0.1, -0.08, house.wall_material, panel_tint, frame=frame)


def dress_street_wall(b: Builder, room: Room, frame: Matrix, length: float, openings: list) -> None:
    """What makes a street wall read as a facade: stone plinth between the doors, a string course under the upper
    storey, and on tall halls a second tier of arched windows over the shop windows."""
    house = room.house
    gaps = sorted((opening.u - opening.width / 2.0 - 0.18, opening.u + opening.width / 2.0 + 0.18) for opening in openings if opening.kind != "vitrine")
    plinth_from = [0.0] + [right for _, right in gaps]
    plinth_to = [left for left, _ in gaps] + [length]
    vitrines = [opening for opening in openings if opening.kind == "vitrine"]
    tier_bottom = max((opening.apex for opening in vitrines), default=0.0) + 1.3
    tier_height = room.storey - 0.7 - tier_bottom

    for u_from, u_to in zip(plinth_from, plinth_to):
        b.box((u_from, -0.07, 0.0), (u_to, 0.0, PLINTH_HEIGHT), "trim", house.trim_tint, frame=frame, uv=("band", *town.TRIM_BLOCK_BAND, 1.0))

    if len(house.storeys) > 1:
        b.box((0.0, -0.1, room.storey - 0.22), (length, 0.0, room.storey), "trim", house.trim_tint, frame=frame, uv=("band", *town.TRIM_SMOOTH_BAND, 1.0))

    for window in vitrines:
        if window.bottom >= BLIND_ARCH_MIN_SILL:
            blind_arch(b, room, frame, window)

    if tier_height < 1.2:
        return

    for opening in vitrines:
        flat_window(b, room, frame, Opening(opening.u, min(1.5, opening.width * 0.6), tier_bottom, tier_height, "round"))


def wall_frames(room: Room, lift: float = 0.0) -> dict:
    """Frame of each wall of a hall (outer face on local d = 0, u from 0 along it seen from outside), lift up."""
    return {
        "front": Matrix.Translation((-room.half, 0.0, lift)),
        "back": Matrix.Translation((room.half, room.depth, lift)) @ Matrix.Rotation(math.pi, 4, "Z"),
        "right": Matrix.Translation((room.half, WALL, lift)) @ Matrix.Rotation(math.pi / 2.0, 4, "Z"),
        "left": Matrix.Translation((-room.half, room.depth - WALL, lift)) @ Matrix.Rotation(-math.pi / 2.0, 4, "Z"),
    }


def wall_lengths(room: Room) -> dict:
    side_length = room.depth - 2.0 * WALL

    return {"front": 2.0 * room.half, "back": 2.0 * room.half, "left": side_length, "right": side_length}


def build_walls(b: Builder, room: Room, openings: dict = None, lift: float = 0.0) -> list:
    """Four walls of one storey; the sides that face a street get real windows. Returns the front openings."""
    side_length = room.depth - 2.0 * WALL
    frames = wall_frames(room, lift)
    openings = openings or room_openings(room)
    front = openings["front"]
    lengths = wall_lengths(room)

    for side, frame in frames.items():
        pierced_wall(b, room, frame, lengths[side], openings[side])

    if room.spec.get("casarao"):
        return front

    for side in ("front", *room.exposed):
        dress_street_wall(b, room, frames[side], lengths[side], openings[side])

    for side, storey in itertools.product(room.exposed, range(1, len(room.house.storeys))):
        upper_frame = frames[side] @ Matrix.Translation((0.0, 0.0, room.house.levels[storey]))

        for u, _ in evenly(1.0, side_length - 1.0, SIDE_WINDOW_PITCH):
            flat_window(b, room, upper_frame, Opening(u, 1.1, 0.8, 1.7, "segment"))

    return front


# ---------- shell ----------

def build_floor(b: Builder, room: Room) -> None:
    """Planked or flagged floor flush with the pavement."""
    if room.spec["floor"] == "stone":
        b.box((room.left, room.front, 0.0), (room.right, room.back, FLOOR_TOP), "stone", srgb(STONE["dourada"]), uv=("world", 1.2))
        return

    board_count = round((room.right - room.left) / BOARD_WIDTH)
    board_width = (room.right - room.left) / board_count

    if room.spec.get("casarao"):
        build_plank_floor(b, room, board_count, board_width)
    else:
        for board_index in range(board_count):
            board_left = room.left + board_index * board_width
            shade = 1.0 if board_index % 3 else 0.9
            b.box((board_left, room.front, 0.0), (board_left + board_width, room.back, FLOOR_TOP), "wood", tuple(shade * channel for channel in srgb(WOOD["mel"])), uv=("band", *WOOD_LIGHT_BAND, 2.0))

    b.collider((room.left, room.front, 0.0), (room.right, room.back, FLOOR_TOP), name="WoodFloor")  # passos com som de madeira

    for u_from, u_to, d_from, d_to in room.plan.get("stone_floors", ()):
        b.box((u_from, d_from, FLOOR_TOP), (u_to, d_to, FLOOR_TOP + STONE_PATCH_LIFT), "stone", srgb(STONE["dourada"]), uv=("world", 1.2))
        b.collider((u_from, d_from, FLOOR_TOP), (u_to, d_to, FLOOR_TOP + STONE_PATCH_LIFT), name="StoneFloor")


def plank_joints(rng: random.Random, room: Room) -> list:
    """d of the end-to-end joints of one board, front to back: boards of PLANK_LENGTH_RANGE, the first one cut short at random."""
    joints = [room.front]
    reach = room.front + rng.uniform(0.3, PLANK_LENGTH_RANGE[1])

    while reach < room.back - PLANK_LENGTH_RANGE[0] / 2.0:
        joints.append(reach)
        reach += rng.uniform(*PLANK_LENGTH_RANGE)

    return joints + [room.back]


def build_plank_floor(b: Builder, room: Room, board_count: int, board_width: float) -> None:
    """Wide boards laid front to back, each cut into planks with its own shade and staggered end joints: the floor of
    a lived-in hall is never one flat colour."""
    rng = random.Random(town.hash_seed(room.shop_type))
    base = srgb(WOOD["mel"])

    for board_index in range(board_count):
        board_left = room.left + board_index * board_width
        joints = plank_joints(rng, room)

        for plank_from, plank_to in zip(joints, joints[1:]):
            shade = rng.uniform(*PLANK_SHADE_RANGE)
            b.box((board_left, plank_from, 0.0), (board_left + board_width, plank_to, FLOOR_TOP), "wood", tuple(shade * channel for channel in base), uv=("band", *WOOD_LIGHT_BAND, 2.0))


def girder_us(room: Room) -> list:
    """u of the cross beams of the plan's girder_pitch (every so many metres, evenly over the hall), none by default."""
    pitch = room.plan.get("girder_pitch")

    if not pitch:
        return []

    count = int((room.right - room.left) / pitch)

    return [room.left + (room.right - room.left) * (index + 0.5) / count for index in range(count)]


def build_plank_ceiling(b: Builder, room: Room) -> None:
    """The underside of the ceiling as one dark-stained board ceiling, a little shade between boards."""
    rng = random.Random(town.hash_seed(room.shop_type) + 7)
    board_count = round((room.right - room.left) / CEILING_PLANK_WIDTH)
    board_width = (room.right - room.left) / board_count
    base = srgb(WOOD["media"])

    for board_index in range(board_count):
        board_left = room.left + board_index * board_width
        shade = rng.uniform(*CEILING_PLANK_SHADE_RANGE)

        b.box((board_left, room.front, room.ceiling - 0.03), (board_left + board_width, room.back, room.ceiling + 0.05), "wood", tuple(shade * channel for channel in base), uv=("band", *WOOD_DARK_BAND, 2.0))


def build_ceiling(b: Builder, room: Room) -> None:
    """Board ceiling (its collider, down to the beams, stops the camera arm), joists, and a girder over each row of posts."""
    house = room.house
    joist_count = int((room.back - room.front) / JOIST_SPACING)
    post_us = sorted({u for u, _ in room.posts} | set(girder_us(room)))

    beam_depth = 0.42 if post_us else 0.2

    # o colisor do forro desce até a face de baixo das vigas: o braço da câmera para embaixo delas, não dentro
    b.box((room.left, room.front, room.ceiling), (room.right, room.back, room.storey), "wood", srgb(WOOD["mel"]))
    b.collider((room.left, room.front, room.ceiling - beam_depth), (room.right, room.back, room.storey))

    if room.spec.get("casarao"):
        build_plank_ceiling(b, room)

    for joist_index in range(joist_count):
        d = room.front + (room.back - room.front) * (joist_index + 0.5) / joist_count
        b.box((room.left, d - 0.08, room.ceiling - 0.2), (room.right, d + 0.08, room.ceiling), "wood", house.wood_tint, uv=("band", *WOOD_DARK_BAND, 1.5))

    for u in post_us:
        b.box((u - GIRDER_WIDTH / 2.0, room.front, room.ceiling - 0.42), (u + GIRDER_WIDTH / 2.0, room.back, room.ceiling - 0.2), "wood", house.wood_tint, uv=("band", *WOOD_DARK_BAND, 1.5))

    for u, d in room.posts:
        town.wall_piece(b, (u - POST / 2.0, d - POST / 2.0, 0.0), (u + POST / 2.0, d + POST / 2.0, room.ceiling - 0.42), "wood", house.wood_tint)
        b.box((u - POST / 2.0 - PLINTH_MARGIN, d - POST / 2.0 - PLINTH_MARGIN, 0.0), (u + POST / 2.0 + PLINTH_MARGIN, d + POST / 2.0 + PLINTH_MARGIN, 0.35), "stone", srgb(STONE["media"]))

        for brace_sign in (-1, 1):
            b.beam((u, d + brace_sign * 0.1, room.ceiling - 1.4), (u, d + brace_sign * 1.0, room.ceiling - 0.42), 0.14, 0.14, "wood", house.wood_tint)


def partition_options(partition: tuple) -> dict:
    """Optional fifth item of a partition: doors=[dict(at, width, height, leaf=(face, direction), lane=(faces kept free))] and faces=(low finish, high finish)."""
    return partition[4] if len(partition) > 4 else {}


def partition_doors(partition: tuple) -> list:
    """Doors of a partition as (from, to, door) along its span, in order."""
    doors = sorted(partition_options(partition).get("doors", ()), key=lambda door: door["at"])

    return [(door["at"] - door["width"] / 2.0, door["at"] + door["width"] / 2.0, door) for door in doors]


def partition_piece(room: Room, partition: tuple, span_from: float, span_to: float, z_from: float = 0.0, z_to: float = None) -> tuple:
    """Box (low, high corners, facade coords) of a stretch of an inner wall, from z_from up to the ceiling by default."""
    axis, fixed = partition[0], partition[1]
    top = room.ceiling if z_to is None else z_to
    boxes = {
        "u": ((fixed - WALL / 2.0, span_from, z_from), (fixed + WALL / 2.0, span_to, top)),
        "d": ((span_from, fixed - WALL / 2.0, z_from), (span_to, fixed + WALL / 2.0, top)),
    }

    return boxes[axis]


def free_spans(span_from: float, span_to: float, cuts: list) -> list:
    """(from, to) pieces of a span left once the cuts (not overlapping) are taken out of it."""
    inside = sorted((max(cut_from, span_from), min(cut_to, span_to)) for cut_from, cut_to in cuts if cut_to > span_from and cut_from < span_to)
    starts = [span_from] + [cut_to for _, cut_to in inside]
    ends = [cut_from for cut_from, _ in inside] + [span_to]

    return [(start, end) for start, end in zip(starts, ends) if end - start > 0.05]


def face_reach(fixed: float, side: str) -> tuple:
    """(from, to) across an inner wall on its low or high side, PARTITION_DOOR_LANE deep from the wall face."""
    return {"low": (fixed - WALL / 2.0 - PARTITION_DOOR_LANE, fixed - WALL / 2.0), "high": (fixed + WALL / 2.0, fixed + WALL / 2.0 + PARTITION_DOOR_LANE)}[side]


def partition_segments(partition: tuple) -> list:
    """(from, to) of the solid stretches of a partition, the door gaps left out."""
    return free_spans(partition[2], partition[3], [(door_from, door_to) for door_from, door_to, _ in partition_doors(partition)])


def wall_slab(axis: str, face_at: float, normal: int, span: tuple, offset: float, thickness: float, z_range: tuple) -> tuple:
    """Box standing on a wall face: axis is the wall's fixed coordinate (u | d), normal points into the room."""
    near, far = sorted((face_at + normal * offset, face_at + normal * (offset + thickness)))
    boxes = {"u": ((near, span[0], z_range[0]), (far, span[1], z_range[1])), "d": ((span[0], near, z_range[0]), (span[1], far, z_range[1]))}

    return boxes[axis]


def dress_wall_face(b: Builder, room: Room, axis: str, face_at: float, normal: int, span: tuple, finish_name: str, cuts: list, rail_cuts: list) -> None:
    """Finished wall: painted (or tiled) dado with skirting and a thin rail, a picture rail higher up and a cornice at
    the ceiling. The dado skips `cuts` (doors, low windows), the picture rail `rail_cuts`; the wall between the rails
    keeps the hall plaster."""
    finish = WALL_FINISHES[finish_name]
    dado_tint, trim_tint = srgb(finish["dado"]), srgb(finish["trim"])
    wood_uv = ("band", *WOOD_DARK_BAND, 1.5)
    cornice_tint = srgb(CORNICE_TINT)
    cornice_from = room.ceiling - CORNICE_HEIGHT

    for piece in free_spans(span[0], span[1], cuts):
        b.box(*wall_slab(axis, face_at, normal, piece, 0.0, DADO_DEPTH, (SKIRTING_HEIGHT, DADO_HEIGHT)), finish.get("material", "plaster"), dado_tint, uv=finish.get("uv"))
        b.box(*wall_slab(axis, face_at, normal, piece, 0.0, SKIRTING_DEPTH, (0.0, SKIRTING_HEIGHT)), "wood", trim_tint, uv=wood_uv)
        b.box(*wall_slab(axis, face_at, normal, piece, 0.0, RAIL_DEPTH, (DADO_HEIGHT, DADO_HEIGHT + RAIL_HEIGHT)), "wood", trim_tint, uv=wood_uv)

    for piece in free_spans(span[0], span[1], rail_cuts):
        b.box(*wall_slab(axis, face_at, normal, piece, 0.0, PICTURE_RAIL_DEPTH, (PICTURE_RAIL_HEIGHT, PICTURE_RAIL_HEIGHT + RAIL_HEIGHT)), "wood", trim_tint, uv=wood_uv)

    b.box(*wall_slab(axis, face_at, normal, span, 0.0, 0.05, (cornice_from, cornice_from + CORNICE_HEIGHT * 0.4)), "plaster", cornice_tint)
    b.box(*wall_slab(axis, face_at, normal, span, 0.0, 0.1, (cornice_from + CORNICE_HEIGHT * 0.4, room.ceiling)), "plaster", cornice_tint)


def hall_wall_faces(room: Room) -> dict:
    """side -> (fixed axis, coordinate of the inner face, normal into the hall) of the four walls of a hall."""
    return {"front": ("d", room.front, 1), "back": ("d", room.back, -1), "left": ("u", room.left, 1), "right": ("u", room.right, -1)}


def hall_wall_cuts(room: Room, side: str, height: float) -> list:
    """Stretches of an inner wall face (hall coords along it) a band at this height must skip: windows that start below
    it, doorways."""
    front = [(opening.u - room.half - opening.width / 2.0, opening.u - room.half + opening.width / 2.0) for opening in front_openings(room) if opening.bottom < height] if side == "front" else []
    windows = [(span_from, span_to) for span_from, span_to, sill in window_spans(room).get(side, ()) if sill < height]
    doorway = room.inner_doors.get(side)
    doorways = [(doorway[0] - doorway[1] / 2.0 - 0.2, doorway[0] + doorway[1] / 2.0 + 0.2)] if doorway else []

    return sorted(front + windows + doorways)


def used_finishes(room: Room) -> set:
    """Names of the wall finishes a room's plan uses, on its hall walls and partition faces."""
    on_halls = {finish for _, _, _, finish in room.plan.get("finishes", ())}
    on_partitions = {finish for partition in room.partitions for finish in partition_options(partition).get("faces", ()) if finish}

    return on_halls | on_partitions


def build_wall_finishes(b: Builder, room: Room) -> None:
    """Dado of the plan's `finishes`: (side, from, to, finish) along the inner face of the hall walls."""
    faces = hall_wall_faces(room)

    for side, span_from, span_to, finish_name in room.plan.get("finishes", ()):
        axis, face_at, normal = faces[side]

        dress_wall_face(b, room, axis, face_at, normal, (span_from, span_to), finish_name, hall_wall_cuts(room, side, DADO_HEIGHT), hall_wall_cuts(room, side, PICTURE_RAIL_HEIGHT))


def dress_partition_door(b: Builder, room: Room, partition: tuple, door: dict) -> None:
    """Framed doorway of an inner wall: wall over the door to the ceiling, a frame (jambs and head) on both faces and,
    when the plan asks for it, one leaf folded back against the wall."""
    axis, fixed = partition[0], partition[1]
    door_from, door_to = door["at"] - door["width"] / 2.0, door["at"] + door["width"] / 2.0
    wood_uv = ("band", *WOOD_DARK_BAND, 1.5)
    frame_tint = srgb(WOOD["escura"])

    sill = door.get("sill", 0.0)  # a hatch (passa-pratos, guichê, grade do locutório) is a doorway with a sill
    sill_tint = srgb(WOOD["media"])

    town.wall_piece(b, *partition_piece(room, partition, door_from, door_to, door["height"]), room.house.wall_material, room.house.wall_tint)

    if sill > 0.0:
        town.wall_piece(b, *partition_piece(room, partition, door_from, door_to, 0.0, sill), room.house.wall_material, room.house.wall_tint)
        b.box(*wall_slab(axis, fixed - WALL / 2.0 - HATCH_LEDGE, 1, (door_from, door_to), 0.0, WALL + 2.0 * HATCH_LEDGE, (sill - 0.05, sill)), "wood", sill_tint, uv=wood_uv)

    for normal in (-1, 1):
        face_at = fixed + normal * WALL / 2.0

        for jamb in ((door_from - DOOR_FRAME_WIDTH, door_from), (door_to, door_to + DOOR_FRAME_WIDTH)):
            b.box(*wall_slab(axis, face_at, normal, jamb, 0.0, DOOR_FRAME_DEPTH, (sill, door["height"] + DOOR_FRAME_WIDTH)), "wood", frame_tint, uv=wood_uv)

        head = (door_from - DOOR_FRAME_WIDTH, door_to + DOOR_FRAME_WIDTH)

        b.box(*wall_slab(axis, face_at, normal, head, 0.0, DOOR_FRAME_DEPTH, (door["height"], door["height"] + DOOR_FRAME_WIDTH)), "wood", frame_tint, uv=wood_uv)

    if door.get("leaf"):
        dress_door_leaf(b, partition, door)


def dress_door_leaf(b: Builder, partition: tuple, door: dict) -> None:
    """The leaf of door['leaf'] = (face, direction) folded flat against that face of the wall: face 'low' | 'high',
    direction -1 | +1 along the span from the hinge jamb (the stretch of wall it covers must be free)."""
    axis, fixed = partition[0], partition[1]
    face, direction = door["leaf"]
    normal = {"low": -1, "high": 1}[face]
    hinge = door["at"] + direction * (door["width"] / 2.0 + DOOR_FRAME_WIDTH)
    span = tuple(sorted((hinge, hinge + direction * (door["width"] - 0.04))))
    inset = (span[0] + 0.1, span[1] - 0.1)
    leaf_tint, panel_tint = srgb(WOOD["media"]), srgb(WOOD["mel"])
    wood_uv = ("band", *WOOD_DARK_BAND, 1.5)
    face_at = fixed + normal * WALL / 2.0
    panels = ((0.15, door["height"] * 0.45), (door["height"] * 0.52, door["height"] - 0.2))

    b.box(*wall_slab(axis, face_at, normal, span, DOOR_LEAF_OFFSET, DOOR_LEAF_THICKNESS, (0.02, door["height"] - 0.03)), "wood", leaf_tint, uv=wood_uv)

    for panel in panels:
        b.box(*wall_slab(axis, face_at, normal, inset, DOOR_LEAF_OFFSET + DOOR_LEAF_THICKNESS, 0.012, panel), "wood", panel_tint, uv=("band", *WOOD_LIGHT_BAND, 1.0))


def build_partition(b: Builder, room: Room, partition: tuple) -> None:
    """Inner wall to the ceiling with its doorways (framed, lintel wall above), both faces finished as the plan says."""
    axis, fixed = partition[0], partition[1]
    faces = partition_options(partition).get("faces", (None, None))
    door_cuts = [(door_from - DOOR_FRAME_WIDTH, door_to + DOOR_FRAME_WIDTH) for door_from, door_to, _ in partition_doors(partition)]

    for span_from, span_to in partition_segments(partition):
        town.wall_piece(b, *partition_piece(room, partition, span_from, span_to), room.house.wall_material, room.house.wall_tint)

    for _, _, door in partition_doors(partition):
        dress_partition_door(b, room, partition, door)

    for normal, finish_name in zip((-1, 1), faces):
        if finish_name:
            dress_wall_face(b, room, axis, fixed + normal * WALL / 2.0, normal, partition[2:4], finish_name, door_cuts, [])


def build_awnings(b: Builder, room: Room, front: list) -> None:
    """Striped cloth awning over every shop window of the facade."""
    colors = [srgb(hex_value) for hex_value in room.spec["awning"] or ()]
    vitrines = [opening for opening in front if opening.kind == "vitrine" and colors]

    for opening in vitrines:
        left = opening.u - room.half - opening.width / 2.0 - 0.25
        stripe_count = max(2, round((opening.width + 0.5) / AWNING_STRIPE))
        stripe_width = (opening.width + 0.5) / stripe_count
        top = opening.apex + 0.45
        slab = [(0.0, top), (-AWNING_REACH, top - 0.6), (-AWNING_REACH, top - 0.55), (0.0, top + 0.05)]
        valance = [(-AWNING_REACH, top - 0.58), (-AWNING_REACH, top - 0.85), (-AWNING_REACH + 0.03, top - 0.85), (-AWNING_REACH + 0.03, top - 0.58)]

        for stripe_index in range(stripe_count):
            stripe_left = left + stripe_index * stripe_width
            b.side_prism(slab, stripe_left, stripe_left + stripe_width, "paint", colors[stripe_index % 2])
            b.side_prism(valance, stripe_left, stripe_left + stripe_width, "paint", colors[(stripe_index + 1) % 2])

        for arm_u in (left + 0.05, left + opening.width + 0.45):
            b.beam((arm_u, 0.0, top - 0.75), (arm_u, -AWNING_REACH, top - 0.6), 0.04, 0.04, "metal", room.house.iron_tint)

        slab_frame = Matrix.Translation((0.0, 0.0, top)) @ Matrix.Rotation(math.atan2(0.6, AWNING_REACH), 4, "X")
        b.collider((left, -math.hypot(AWNING_REACH, 0.6), -0.05), (left + opening.width + 0.5, 0.0, 0.0), slab_frame, name=town.CAMERA_STOP)
        b.collider((left, -AWNING_REACH, top - 0.85), (left + opening.width + 0.5, -AWNING_REACH + 0.03, top - 0.58), name=town.CAMERA_STOP)


def build_roof(b: Builder, room: Room) -> None:
    """Upper storeys, roof and signature details of the archetype the shop is dressed after."""
    spec = dict(town.ARCHETYPE_SPECS[room.spec["archetype"]])
    house = room.house

    spec.update(storeys=room.spec["storeys"], roof=room.spec["roof_shape"], features=room.spec.get("features", ()), chimney=room.spec.get("chimney"), loggia_top=False, quoins=room.spec.get("quoins", False), cornice=room.spec.get("cornice", False))
    town.build_house(b, house, spec, ground="shop")

    if room.spec["roof_shape"][0] != "gable_parallel":
        return

    options = room.spec["roof_shape"][1]
    eave_front, eave_back = -options["eave_front"], house.depth + options["eave_back"]
    rise = (eave_back - eave_front) / 2.0 * math.tan(math.radians(options["pitch"]))
    gable = [(eave_front + 0.3, house.top - 0.12), (eave_back - 0.3, house.top - 0.12), ((eave_front + eave_back) / 2.0, house.top - 0.12 + rise - 0.3 * rise / ((eave_back - eave_front) / 2.0))]

    for side in room.exposed:
        side_sign = {"left": -1.0, "right": 1.0}[side]
        b.side_prism(gable, side_sign * house.limit, side_sign * (house.limit + 0.01), house.wall_material, house.wall_tint)


def build_shell(shop_type: str) -> dict:
    room = Room(shop_type)

    if "shell" in room.spec:  # casca própria (o vestíbulo do casarão tem dois andares e a escadaria)
        return importlib.import_module(room.spec["shell"]).build_shell(room)

    b = Builder(f"shop_{shop_type}")
    house = room.house
    light_columns = max(2, round(2.0 * room.half / LIGHT_SPACING))
    light_us = [room.left + (room.right - room.left) * (index + 0.5) / light_columns for index in range(light_columns)]

    if any(WALL_FINISHES[finish]["material"] == "azulejo" for finish in used_finishes(room) if "material" in WALL_FINISHES[finish]):
        b.materials["azulejo"] = town.textured_material("M_TownAzulejo", AZULEJO_TEXTURE, roughness=0.35)

    front = build_walls(b, room)
    build_floor(b, room)
    build_ceiling(b, room)
    build_awnings(b, room, front)

    if not room.spec.get("casarao"):
        build_roof(b, room)

    for partition in room.partitions:
        build_partition(b, room, partition)

    build_wall_finishes(b, room)

    for u, row in itertools.product(light_us, LIGHT_ROWS):
        b.light((u, room.front + (room.back - room.front) * row, room.ceiling - 0.9), *day_lamp(room))

    b.marker("shopkeeper", (*room.keeper, 0.0 if room.has_street_door else FLOOR_TOP))

    return b.finish(town.SHOP_DIR / f"shop_{shop_type}.gltf", shell_sidecar(room))


def day_lamp(room: Room) -> tuple:
    """(color, energy, range, frame, group) of the ceiling grid lamps. In the casarão they are the light of the day
    (daylight bouncing round the hall: warm, on only while the sun is up); at night its lamps are the chandeliers."""
    if room.spec.get("casarao"):
        return room.spec["day_light"], 1.3, 10.0, None, "day_lights"

    return room.spec["light"], 1.3, 10.0


def shell_sidecar(room: Room) -> dict:
    """What the scene reads of a shell; a hall with no street door tells where its inner doorway is."""
    sidecar = {"lot_width": SHOP_LOTS[room.shop_type][0], "lot_depth": SHOP_LOTS[room.shop_type][1], "shop": room.shop_type, "doors": room.house.doors}

    if not room.has_street_door:
        sidecar["entry"] = entry_point(room)

    if room.spec.get("casarao"):
        sidecar["ambient_volume"] = ambient_volume(room)

    if "night_ambient" in room.spec:
        sidecar["night_ambient"] = room.spec["night_ambient"]

    return sidecar


def ambient_volume(room: Room) -> dict:
    """Box (model-local Godot coords) of the air inside a casarão hall, for the interior ambient probe: from the floor
    to the underside of the topmost ceiling, walls to their inner face plus a hair."""
    top = sum(room.spec["storeys"][:-1]) + room.spec["storeys"][-1] - CEILING_SLAB
    corner_low = town.blender_to_godot((room.left - AMBIENT_MARGIN, room.back + AMBIENT_MARGIN, 0.0))
    corner_high = town.blender_to_godot((room.right + AMBIENT_MARGIN, room.front - AMBIENT_MARGIN, top))

    return {"min": corner_low, "max": corner_high}


# ---------- furniture ----------

class Furnisher:
    """Places props of the libraries in a room and keeps their footprints to report overlaps."""

    def __init__(self, b: Builder, room: Room, base: float = 0.0) -> None:
        door_u, door_width, _, _ = room.door

        self.b = b
        self.room = room
        self.base = base  # altura do piso deste andar (o vestíbulo do casarão mobília dois)
        self.floors = [self]
        self.left, self.right, self.front, self.back, self.ceiling = room.left, room.right, room.front, room.back, base + room.ceiling
        self.door_u = door_u
        self.keeper = room.keeper
        self.placed = 0
        self.missing = set()
        self.lights = []
        self.windows = window_spans(room)
        self.window_list = [(side, window) for side, windows in self.windows.items() for window in windows]
        self.window_blockers = []
        self.rugs = []
        self.footprints = [("lojista", (self.keeper[0] - 0.35, self.keeper[0] + 0.35, self.keeper[1] - 0.35, self.keeper[1] + 0.35))] if base == 0.0 else []
        self.footprints += [("porta", (door_u - door_width / 2.0 - 0.2, door_u + door_width / 2.0 + 0.2, room.front, room.front + DOOR_CLEARANCE))] if room.has_street_door and base == 0.0 else []
        self.footprints += [("porta", self.inner_door_lane(side, d, width)) for side, (d, width, _, _) in room.inner_doors.items()]
        self.footprints += [("pilar", (u - POST / 2.0, u + POST / 2.0, d - POST / 2.0, d + POST / 2.0)) for u, d in room.posts]
        self.footprints += [("parede", (box[0][0], box[1][0], box[0][1], box[1][1])) for box in self.partition_boxes()] if base == 0.0 else []  # as divisórias são do térreo
        self.footprints += [("porta", lane) for lane in self.partition_door_lanes()] if base == 0.0 else []

    def partition_boxes(self) -> list:
        """Solid stretches of every partition (door gaps left out) as (low, high) corners."""
        return [partition_piece(self.room, partition, span_from, span_to) for partition in self.room.partitions for span_from, span_to in partition_segments(partition)]

    def partition_door_lanes(self) -> list:
        """Floor kept free beside every partition door, (u from, u to, d from, d to): on the faces its `lane` lists
        (both by default)."""
        lanes = {
            "u": lambda reach, door_from, door_to: (*reach, door_from, door_to),
            "d": lambda reach, door_from, door_to: (door_from, door_to, *reach),
        }
        found = []

        for partition in self.room.partitions:
            for door_from, door_to, door in partition_doors(partition):
                along = (max(door_from - 0.2, partition[2]), min(door_to + 0.2, partition[3]))
                found += [lanes[partition[0]](face_reach(partition[1], side), *along) for side in door.get("lane", ("low", "high"))]

        return found

    def inner_door_lane(self, side: str, d: float, width: float) -> tuple:
        """Floor kept free behind an inner doorway."""
        reach = {"left": (self.left, self.left + DOOR_CLEARANCE), "right": (self.right - DOOR_CLEARANCE, self.right)}[side]

        return (*reach, d - width / 2.0 - 0.2, d + width / 2.0 + 0.2)

    def prop_size(self, name: str) -> tuple:
        """(width, depth, height) of a prop of the libraries (a 1 m cube while it is not modelled yet)."""
        return PROPS.get(name, {"size": (1.0, 1.0, 1.0)})["size"]

    def upstairs(self, base: float) -> "Furnisher":
        """Furnisher of another storey of the same hall, reported and counted with this one."""
        upper = Furnisher(self.b, self.room, base)

        self.floors.append(upper)

        return upper

    def block(self, name: str, box: tuple) -> None:
        """Floor (u from, u to, d from, d to) that is not free for furniture: a stair, a void."""
        self.footprints.append((name, box))

    def put(self, name: str, u: float, d: float, degrees: float = 0.0, z: float = None, **options) -> None:
        """One prop with its local origin at (u, d); degrees turns its front (-Y) counter-clockwise seen from above.
        Hanging props go to the ceiling unless z is given."""
        entry = PROPS.get(name)
        lit = options.pop("lit", True)

        if entry is None:
            self.missing.add(name)
            return

        width, depth, height = entry["size"]
        height_origin = (self.ceiling if entry.get("hang") else self.base + FLOOR_TOP) if z is None else z
        frame = Matrix.Translation((u, d, height_origin)) @ Matrix.Rotation(math.radians(degrees), 4, "Z")
        cos_turn, sin_turn = abs(math.cos(math.radians(degrees))), abs(math.sin(math.radians(degrees)))
        half_u, half_d = (width * cos_turn + depth * sin_turn) / 2.0, (width * sin_turn + depth * cos_turn) / 2.0

        entry["build"](self.b, frame, **options)
        self.placed += 1

        if not entry.get("hang") and not entry.get("beside_window"):
            self.note_window_blocker(name, (u - half_u, u + half_u, d - half_d, d + half_d), height_origin - self.base + height)  # altura sobre o piso deste andar

        if name.startswith("rug") and not entry.get("hang"):
            self.rugs.append((name, (u - half_u, u + half_u, d - half_d, d + half_d)))

        if entry.get("solid"):
            self.b.collider((-width / 2.0, -depth / 2.0, 0.0), (width / 2.0, depth / 2.0, min(height, COLLIDER_MAX_HEIGHT)), frame)
            self.footprints.append((name, (u - half_u, u + half_u, d - half_d, d + half_d)))

        if entry.get("light") and lit:
            position, color, energy, light_range = entry["light"]
            self.lights.append((frame, position, color, energy, light_range))

    def wall(self, side: str, items: list, start: float = None, gap: float = 0.25) -> None:
        """Props in a row with their backs to a wall, from start along it (u for back/front, d for left/right).
        items: prop name, (name, options) or a number of metres to skip."""
        cursor = start if start is not None else {"back": self.left, "front": self.left, "left": self.front, "right": self.front}[side] + 0.4

        for item in items:
            if isinstance(item, (int, float)):
                cursor += item
                continue

            name, options = (item, {}) if isinstance(item, str) else item
            width = PROPS.get(name, {"size": (1.0, 0.5, 1.0)})["size"][0]

            self.on_wall(side, name, cursor + width / 2.0, **options)
            cursor += width + gap

    def on_wall(self, side: str, name: str, along: float, z: float = None, **options) -> None:
        """One prop with its back to a wall, centred at along (u for back/front, d for left/right)."""
        turns = {"back": 0.0, "front": 180.0, "left": 90.0, "right": -90.0}
        across = PROPS.get(name, {"size": (1.0, 0.5, 1.0)})["size"][1] / 2.0 + 0.03
        spots = {"back": (along, self.back - across), "front": (along, self.front + across), "left": (self.left + across, along), "right": (self.right - across, along)}

        self.put(name, *spots[side], turns[side], z, **options)

    def on_face(self, axis: str, face_at: float, normal: int, name: str, along: float, z: float = None, **options) -> None:
        """One prop with its back to an inner wall (a partition), centred at along. axis is the wall's fixed coordinate
        (u | d), face_at the coordinate of the face the prop stands on, normal points from the face into the room."""
        depth = PROPS.get(name, {"size": (1.0, 0.5, 1.0)})["size"][1]
        turns = {("d", -1): 0.0, ("d", 1): 180.0, ("u", -1): -90.0, ("u", 1): 90.0}
        centre = face_at + normal * depth / 2.0
        spots = {"d": (along, centre), "u": (centre, along)}

        self.put(name, *spots[axis], turns[(axis, normal)], z, **options)

    def hang_picture(self, axis: str, face_at: float, normal: int, along: float, variant: str, name: str = "painting") -> None:
        """A framed picture hung by two cords from the picture rail of an inner wall (same arguments as on_face)."""
        width, height = SCENES[variant][:2]
        origin = PICTURE_RAIL_HEIGHT - PICTURE_CORD - height / 2.0 - PICTURE_CENTRE
        top = PICTURE_RAIL_HEIGHT - PICTURE_CORD

        self.on_face(axis, face_at, normal, name, along, z=origin, variant=variant)

        for cord_along in (along - width * 0.3, along + width * 0.3):
            self.b.box(*wall_slab(axis, face_at, normal, (cord_along - 0.004, cord_along + 0.004), 0.04, 0.008, (top, PICTURE_RAIL_HEIGHT)), "paint", srgb("2A2118"))

    def note_window_blocker(self, name: str, box: tuple, top: float) -> None:
        """Remember a prop that stands against a wall in front of one of its windows, above the sill."""
        u_from, u_to, d_from, d_to = box
        against = {"back": d_to > self.back - WALL_PROP_REACH, "left": u_from < self.left + WALL_PROP_REACH, "right": u_to > self.right - WALL_PROP_REACH}
        along = {"back": (u_from, u_to), "left": (d_from, d_to), "right": (d_from, d_to)}
        covered = [(side, window) for side, window in self.window_list if against[side] and along[side][0] < window[1] - 0.05 and window[0] + 0.05 < along[side][1] and top > window[2] + 0.05]

        self.window_blockers += [(name, side, round(window[0], 1), round(window[1], 1)) for side, window in covered]

    def piers(self, side: str) -> list:
        """Stretches of solid wall between the windows of a side, (from, to) along it, from the start of the wall."""
        wall_start, wall_end = (self.left, self.right) if side == "back" else (self.front, self.back)
        window_edges = [(window_from, window_to) for window_from, window_to, _ in self.windows[side]]
        pier_from = [wall_start] + [window_to for _, window_to in window_edges]
        pier_to = [window_from for window_from, _ in window_edges] + [wall_end]

        return list(zip(pier_from, pier_to))

    def row_length(self, items: list, gap: float) -> float:
        """Length along a wall of a row of props as wall() would place it."""
        names = [item if isinstance(item, str) else item[0] for item in items if not isinstance(item, (int, float))]
        skips = [item for item in items if isinstance(item, (int, float))]

        return sum(PROPS.get(name, {"size": (1.0, 0.5, 1.0)})["size"][0] for name in names) + gap * max(0, len(names) - 1) + sum(skips)

    def is_free(self, name: str, u: float, d: float, degrees: float, aisle: float) -> bool:
        """True when the prop would stand inside the hall with an aisle to everything already placed."""
        width, depth, _ = PROPS.get(name, {"size": (1.0, 1.0, 1.0)})["size"]
        cos_turn, sin_turn = abs(math.cos(math.radians(degrees))), abs(math.sin(math.radians(degrees)))
        half_u, half_d = (width * cos_turn + depth * sin_turn) / 2.0 + aisle, (width * sin_turn + depth * cos_turn) / 2.0 + aisle
        inside = self.left < u - half_u and u + half_u < self.right and self.front < d - half_d and d + half_d < self.back

        return inside and not any(u - half_u < taken[1] and taken[0] < u + half_u and d - half_d < taken[3] and taken[2] < d + half_d for _, taken in self.footprints)

    def scatter(self, items: list, u_range: tuple, d_range: tuple, columns: int, rows: int, aisle: float = ISLAND_AISLE) -> None:
        """Islands for the open floor: walks a columns x rows grid and stands the next item of the cycle on every
        cell that is still free (aisle kept to walls, posts, the door lane and earlier props).
        items: prop name or (name, degrees, options)."""
        cycle = itertools.cycle(items)

        for row, column in itertools.product(range(rows), range(columns)):
            u = u_range[0] + (u_range[1] - u_range[0]) * column / max(1, columns - 1)
            d = d_range[0] + (d_range[1] - d_range[0]) * row / max(1, rows - 1)
            name, degrees, options = next(cycle)

            if self.is_free(name, u, d, degrees, aisle):
                self.put(name, u, d, degrees, **options)

    def grid(self, name: str, u_range: tuple, d_range: tuple, columns: int, rows: int, degrees: float = 0.0, **options) -> None:
        """columns x rows copies spread over a rectangle (ranges are the centres of the outer ones)."""
        for column, row in itertools.product(range(columns), range(rows)):
            u = u_range[0] + (u_range[1] - u_range[0]) * column / max(1, columns - 1)
            d = d_range[0] + (d_range[1] - d_range[0]) * row / max(1, rows - 1)
            self.put(name, u, d, degrees, **options)

    def report(self) -> None:
        """Print solid props that overlap each other, a post, a partition, the door lane, leave the room, or stand
        against a wall in front of one of its windows."""
        pairs = itertools.combinations(self.footprints, 2)
        overlapping = [(first[0], second[0], tuple(round(value, 1) for value in second[1])) for first, second in pairs if (first[0], second[0]) != ("porta", "porta") and first[1][0] < second[1][1] - 0.02 and second[1][0] < first[1][1] - 0.02 and first[1][2] < second[1][3] - 0.02 and second[1][2] < first[1][3] - 0.02]
        fixed = [(name, box) for name, box in self.footprints if name in ("pilar", "parede")]
        rugs_under = [(rug, name, tuple(round(value, 1) for value in box)) for (rug, rug_box), (name, box) in itertools.product(self.rugs, fixed) if boxes_overlap(rug_box, box, -PLINTH_MARGIN)]
        outside = [name for name, (u_from, u_to, d_from, d_to) in self.footprints if u_from < self.left - 0.02 or u_to > self.right + 0.02 or d_from < self.front - 0.02 or d_to > self.back + 0.02]

        for first, second, where in overlapping:
            print(f"AVISO {self.room.shop_type}: {first} x {second} em {where}")

        for rug, name, where in rugs_under:
            print(f"AVISO {self.room.shop_type}: {rug} entra embaixo de {name} em {where}")

        for name in outside:
            print(f"AVISO {self.room.shop_type}: {name} fora do salão")

        for name, side, window_from, window_to in self.window_blockers:
            print(f"AVISO {self.room.shop_type}: {name} tapa a janela {side} em {window_from}..{window_to}")

        if self.missing:
            print(f"AVISO {self.room.shop_type}: props ainda não modelados: {sorted(self.missing)}")


def mix_hex(color: str, target: str, share: float) -> str:
    """'RRGGBB' blended toward another by share (0 keeps color)."""
    channels = [round(int(color[offset:offset + 2], 16) * (1.0 - share) + int(target[offset:offset + 2], 16) * share) for offset in (0, 2, 4)]

    return "".join(f"{channel:02X}" for channel in channels)


def boxes_overlap(first: tuple, second: tuple, margin: float = 0.0) -> bool:
    """True when two (u from, u to, d from, d to) boxes overlap; a negative margin grows them (a post's plinth)."""
    return first[0] < second[1] - margin and second[0] < first[1] - margin and first[2] < second[3] - margin and second[2] < first[3] - margin


def fill_floor(furnisher: Furnisher, items: list) -> None:
    """Loose islands of goods on whatever floor the plan left free, on both sides of the lane from the door."""
    if not items:
        return

    d_range = (furnisher.front + 2.2, furnisher.back - FILL_BACK)
    rows = round((d_range[1] - d_range[0]) / FILL_PITCH) + 1

    for u_range in ((furnisher.left + 1.2, furnisher.door_u - FILL_LANE), (furnisher.door_u + FILL_LANE, furnisher.right - 1.2)):
        columns = max(1, round((u_range[1] - u_range[0]) / FILL_PITCH) + 1)
        furnisher.scatter(items, u_range, d_range, columns, rows, aisle=FILL_AISLE)


def write_plan(furnisher: Furnisher, path: Path) -> None:
    """Footprints of a furnished hall, floor by floor, for a plan drawing (--plan=<folder>)."""
    room = furnisher.room
    floors = [{"base": floor.base, "footprints": [[name, *box] for name, box in floor.footprints], "rugs": [[name, *box] for name, box in floor.rugs]} for floor in furnisher.floors]
    record = {"shop": room.shop_type, "bounds": [room.left, room.right, room.front, room.back], "inner_doors": room.inner_doors, "windows": furnisher.windows, "floors": floors}

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record), encoding="utf-8")


def add_contact_shadows(b: Builder, furnisher: Furnisher) -> None:
    """Soft dark patch on the floor under every solid prop (stacked translucent rectangles), so furniture sits on the
    floor instead of floating: the town's ambient occlusion is too weak to show indoors."""
    b.materials["contact_shadow"] = town.plain_material("M_ContactShadow", (0.0, 0.0, 0.0), 1.0, alpha=CONTACT_SHADOW_ALPHA)

    for floor in furnisher.floors:
        for name, (u_from, u_to, d_from, d_to) in floor.footprints:
            if name not in PROPS:
                continue

            for layer, margin in enumerate(CONTACT_SHADOW_LAYERS):
                height = floor.base + FLOOR_TOP + CONTACT_SHADOW_LIFT * (layer + 1)

                b.box((u_from - margin, d_from - margin, height), (u_to + margin, d_to + margin, height + 0.001), "contact_shadow")


def build_interior(shop_type: str) -> dict:
    """Furniture model of one shop; nothing is written while its plan or its props do not exist yet."""
    room = Room(shop_type)
    b = Builder(f"shop_{shop_type}_interior")
    furnisher = Furnisher(b, room)
    output_path = town.SHOP_DIR / f"shop_{shop_type}_interior.gltf"
    fixture_light = room.spec.get("fixture_light", dict(share=0.0, energy=1.0, limit=FEATURE_LIGHT_LIMIT))

    room.plan.get("furnish", shop_layouts.furnish_generic)(furnisher)
    fill_floor(furnisher, shop_layouts.FILL.get(shop_type, []))
    placed = sum(floor.placed for floor in furnisher.floors)

    if PLAN_FOLDER:
        write_plan(furnisher, Path(PLAN_FOLDER) / f"{shop_type}.json")

    for floor in furnisher.floors:
        floor.report()

    if placed == 0:
        return {}

    if room.spec.get("casarao"):
        add_contact_shadows(b, furnisher)

    for floor in furnisher.floors:
        for frame, position, color, energy, light_range in floor.lights[:fixture_light["limit"]]:
            tinted = mix_hex(color, room.spec["light"], fixture_light["share"])

            b.light(position, tinted, energy * fixture_light["energy"], light_range, frame, "night_lights" if fixture_light.get("night_only") else "")

    return b.finish(output_path, {"shop": shop_type, "props": placed})


if __name__ == "__main__":
    requested = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    PLAN_FOLDER = next((argument.removeprefix("--plan=") for argument in requested if argument.startswith("--plan=")), "")
    only_interiors = "--interiors" in requested
    shop_types = [name for name in requested if not name.startswith("--")] or sorted(SHOPS)

    for shop_type in shop_types:
        sidecar = {} if only_interiors else build_shell(shop_type)
        interior = build_interior(shop_type)
        print(f"BUILT shop_{shop_type}: aabb {sidecar.get('aabb_min')} .. {sidecar.get('aabb_max')}, interior props {interior.get('props', 0)}")
