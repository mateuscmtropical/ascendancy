"""Rooms of the dormitory wing (upper floor, right wing of the orphanage: hall `reading`).

Two bands split by the long wall at d = 8.2. Front band (d = 0.3..8.05): the anteroom at the entry end (u = -14.55, by
the gallery) and dormitory A. Back band (d = 8.35..19.1): dormitory B for the small children, the washroom and the
linen room. The entry end of this wing is u = -14.55; the exposed end wall (u = 14.55) has the side windows.
"""

import itertools

import itertools

WALL_HALF = 0.15  # half the thickness of an inner wall (WALL = 0.3 in build_market_shops.py)

HALL_LEFT = -14.55
HALL_RIGHT = 14.55
HALL_FRONT = 0.3
HALL_BACK = 19.1
LONG_WALL = 8.2  # d of the wall between the front and the back band
ANTEROOM_WALL = -11.21  # u of the wall between the anteroom and dormitory A (a pier of the facade)
BABIES_WALL = 2.85  # u of the wall between dormitory B and the washroom (clear of the back windows)
WASH_WALL = 9.8  # u of the wall between the washroom and the linen room

FRONT_FACE = LONG_WALL - WALL_HALF  # the long wall seen from the front band
BACK_FACE = LONG_WALL + WALL_HALF  # the long wall seen from the back band
PIERS = (-8.17, -5.13, -1.805, 1.805, 5.13, 8.17, 11.21)  # u of the piers of the facade between its windows
BED_PITCH = 0.715  # a pair of beds stands this far either side of the night table between them
PAIR_PITCH = 2.9  # centres of the pairs of beds of dormitory B
BLANKET_A = "grey_blue"  # one blanket colour per ward; only the supervisor's and the older girl's beds differ
BLANKET_B = "green"
LIT_SCONCES = {(1, -5.13), (1, 5.13), (-1, -1.805)}  # (normal, u) of the sconces of dormitory A that really light
LAMPS_A = (-8.4, -2.8, 2.8, 8.4)  # pendant lamps down the aisle of dormitory A

DORM_DOOR = dict(at=4.2, width=1.5, height=2.1, leaf=("high", -1), lane=("high",))  # anteroom -> dormitory A
BABIES_DOOR = dict(at=-12.95, width=1.5, height=2.1)  # anteroom -> dormitory B (no leaf: the anteroom is too narrow)
WASH_DOOR_A = dict(at=7.6, width=1.5, height=2.1, leaf=("high", -1))  # dormitory A -> washroom
WASH_DOOR_B = dict(at=13.7, width=1.5, height=2.1, leaf=("high", 1))  # dormitory B -> washroom
LINEN_DOOR = dict(at=13.7, width=1.5, height=2.1, leaf=("high", 1))  # washroom -> linen room

NEW_WALL_FINISHES = {
    "washroom": dict(dado="FFFFFF", trim="5A3A26", material="azulejo", uv=("world", 1.2)),  # blue and white tiles
    "linen": dict(dado="8FA596", trim="5A3A26"),  # sage dado for the linen room
}


def bed_pair(f, blanket: str, u: float, wall_d: float, normal: int, trunks: bool = True) -> None:
    """Two iron beds with a night table between them and a trunk at each foot, heads to the wall face at d = wall_d
    (normal -1: the hall lies at smaller d, +1: at larger d)."""
    foot_d = wall_d + normal * 2.0
    trunk_d = foot_d + normal * 0.255

    f.on_face("d", wall_d, normal, "night_table", u)

    for side in (-1, 1):
        f.on_face("d", wall_d, normal, "iron_bed", u + side * BED_PITCH, variant=blanket)

        if trunks:
            f.put("bed_trunk", u + side * BED_PITCH, trunk_d, 0.0 if normal < 0 else 180.0)


def alcove(f, u: float, wall_d: float, normal: int, bed_variant: str = "dull_red") -> None:
    """A curtained alcove in a corner of a ward: a bed, a night table with a lamp and a washstand against the wall."""
    f.put("supervisor_alcove", u, wall_d + normal * 1.3)
    f.on_face("d", wall_d, normal, "iron_bed", u - 0.54, variant=bed_variant)
    f.on_face("d", wall_d, normal, "night_table", u + 0.21)
    f.on_face("d", wall_d, normal, "washstand", u + 0.81)
    f.put("oil_lamp_table", u + 0.21, wall_d + normal * 0.21, z=0.73)


def furnish_anteroom(f) -> None:
    """Anteroom (u = -14.55..-11.36, d = 0.3..8.05): a linen press, the children's clothes pegs with their bags and a
    boot rack on the wall to dormitory A, a sconce."""
    face = ANTEROOM_WALL - WALL_HALF

    f.on_wall("left", "linen_press", 5.9)
    f.on_face("u", face, -1, "clothes_pegs", 6.8)
    f.on_face("u", face, -1, "boots_rack", 6.8)
    f.on_face("u", face, -1, "wall_sconce", 5.6)


def furnish_dormitory_a(f) -> None:
    """Dormitory A (u = -11.06..14.55, d = 0.3..8.05): iron beds with their heads to the facade piers and to the long
    wall, in pairs round a night table, a trunk at every foot, a 2.7 m aisle from the door to the end wall, the
    supervisor's curtained bed by the door, a sconce over every bedside table, a crucifix and a kneeler on the end
    wall, the door to the washroom in the long wall."""
    facade_d = f.front

    for pier_u in PIERS:
        bed_pair(f, BLANKET_A, pier_u, facade_d, 1)
        f.on_face("d", facade_d, 1, "wall_sconce", pier_u, lit=(1, pier_u) in LIT_SCONCES)

    for pier_u in PIERS[1:5]:
        bed_pair(f, BLANKET_A, pier_u, FRONT_FACE, -1)
        f.on_face("d", FRONT_FACE, -1, "wall_sconce", pier_u, lit=(-1, pier_u) in LIT_SCONCES)

    alcove(f, -9.76, FRONT_FACE, -1)

    f.on_face("d", FRONT_FACE, -1, "clothes_pegs", -7.4)
    f.hang_picture("d", FRONT_FACE, -1, -3.47, "portrait")
    f.hang_picture("d", FRONT_FACE, -1, 9.1, "lady")

    for press_u in (10.4, 12.2):
        f.on_face("d", FRONT_FACE, -1, "linen_press", press_u)

    f.on_face("d", FRONT_FACE, -1, "wall_crucifix", 0.0)

    for lamp_u in LAMPS_A:
        f.put("hanging_oil_lamp", lamp_u, DORM_DOOR["at"])

    f.on_wall("right", "wall_crucifix", 5.35)
    f.on_wall("right", "prie_dieu", 5.35)

    for stand_d in (0.75, 1.7):
        f.on_wall("right", "washstand", stand_d)


def furnish_dormitory_b(f) -> None:
    """Dormitory B for the small children (u = -14.55..2.7, d = 8.35..19.1): three rows of iron beds, two with their heads
    to the long walls in pairs round a night table with a trunk at every foot and one down the middle with the heads
    to the end wall; the older girl's curtained bed in the corner; the toy corner against the washroom wall."""
    pair_us = tuple(-9.4 + PAIR_PITCH * index for index in range(4))

    for pair_u in pair_us:
        bed_pair(f, BLANKET_B, pair_u, BACK_FACE, 1)
        bed_pair(f, BLANKET_B, pair_u, f.back, -1)
        f.on_face("d", BACK_FACE, 1, "wall_sconce", pair_u, lit=pair_u in (-9.4, -3.6))
        f.on_face("d", f.back, -1, "wall_sconce", pair_u, lit=pair_u == -6.5)

    alcove(f, -13.15, f.back, -1, "ochre")

    f.on_wall("left", "clothes_pegs", 10.9)
    f.on_wall("left", "linen_press", 13.2)
    f.hang_picture("u", f.left, 1, 15.2, "portrait")

    for bed_u in (-11.0, -8.8, -6.6, -4.4, -2.2, 0.0):
        f.put("iron_bed", bed_u, WASH_DOOR_B["at"], 90.0, variant=BLANKET_B)

    for night_u in (-9.9, -5.5, -1.1):
        f.put("night_table", night_u, WASH_DOOR_B["at"] - 0.7, 0.0)

    for lamp_u, lamp_d in itertools.product((-8.2, -3.0), (11.9, 15.5)):
        f.put("hanging_oil_lamp", lamp_u, lamp_d)

    toy_wall = BABIES_WALL - WALL_HALF
    f.on_face("u", toy_wall, -1, "dollhouse", 10.4)
    f.on_face("u", toy_wall, -1, "toy_chest", 11.7)
    f.on_face("u", toy_wall, -1, "toy_chest", 16.2)
    f.on_face("u", toy_wall, -1, "wall_crucifix", 18.0)
    f.put("rocking_horse", 1.2, 17.3, 90.0)


def furnish_washroom(f) -> None:
    """Washroom (u = 3.0..9.65, d = 8.35..19.1): two tin bathtubs behind folding screens and the copper boiler on the
    washroom side of dormitory B's wall, basin rows on the back wall and on the linen room's wall, towel racks, a
    bench and pegs under the long wall; stone floor, tiled dado."""
    west_face = BABIES_WALL + WALL_HALF
    east_face = WASH_WALL - WALL_HALF

    for tub_d in (10.4, 16.9):
        f.on_face("u", west_face, 1, "tin_bathtub", tub_d)
        f.put("folding_screen", west_face + 1.15, tub_d, 90.0)

    f.put("copper_boiler", west_face + 0.55, f.back - 0.45)

    f.on_wall("back", "basin_row", 5.4)
    f.on_wall("back", "basin_row", 8.1)
    f.on_face("u", east_face, -1, "basin_row", 11.0)
    f.on_face("u", east_face, -1, "basin_row", 16.9)

    f.on_face("d", BACK_FACE, 1, "bench_long", 4.6)
    f.on_face("d", BACK_FACE, 1, "clothes_pegs", 4.6)

    f.put("long_bench", 6.3, 13.0, 90.0)
    f.put("towel_rack", 4.6, 14.5, 90.0)

    f.put("hanging_oil_lamp", 6.3, 11.5)
    f.put("hanging_oil_lamp", 6.3, 16.0)
    f.on_face("u", west_face, 1, "wall_sconce", 13.7, lit=False)
    f.on_face("u", east_face, -1, "wall_sconce", 13.0, lit=False)


def furnish_linen_room(f) -> None:
    """Linen room (u = 9.95..14.55, d = 8.35..19.1): linen presses on three walls, shelves of folded linen, the ironing
    table in the middle and the laundry tubs against the washroom wall."""
    west_face = WASH_WALL + WALL_HALF

    for press_u in (10.85, 12.55):
        f.on_face("d", BACK_FACE, 1, "linen_press", press_u)

    f.on_wall("back", "linen_press", 10.85)
    f.on_wall("back", "linen_press", 13.55)
    f.on_wall("right", "linen_press", 13.9)
    f.on_wall("right", "wall_shelf", 9.9, variant="linen")
    f.on_face("u", west_face, 1, "wall_shelf", 10.6, variant="linen")
    f.on_face("u", west_face, 1, "laundry_tubs", 17.2)
    f.put("ironing_table", 12.6, 13.6, 90.0)
    f.put("hanging_oil_lamp", 12.6, 13.6)
    f.on_wall("right", "wall_sconce", 14.0, lit=False)


def furnish_reading(f) -> None:
    """Upper floor of the right wing: the anteroom, dormitory A, dormitory B, the washroom and the linen room."""
    furnish_anteroom(f)
    furnish_dormitory_a(f)
    furnish_dormitory_b(f)
    furnish_washroom(f)
    furnish_linen_room(f)


PLAN = dict(
    keeper=(0.0, 16.0),
    posts=(),
    girder_pitch=2.4,
    partitions=(
        ("u", ANTEROOM_WALL, HALL_FRONT, FRONT_FACE, dict(doors=[DORM_DOOR], faces=("dormitory", "dormitory"))),
        ("d", LONG_WALL, HALL_LEFT, BABIES_WALL, dict(doors=[BABIES_DOOR], faces=("dormitory", "dormitory"))),
        ("d", LONG_WALL, BABIES_WALL, WASH_WALL, dict(doors=[WASH_DOOR_A], faces=("dormitory", "washroom"))),
        ("d", LONG_WALL, WASH_WALL, HALL_RIGHT, dict(faces=("dormitory", "linen"))),
        ("u", BABIES_WALL, BACK_FACE, HALL_BACK, dict(doors=[WASH_DOOR_B], faces=("dormitory", "washroom"))),
        ("u", WASH_WALL, BACK_FACE, HALL_BACK, dict(doors=[LINEN_DOOR], faces=("washroom", "linen"))),
    ),
    finishes=(
        ("front", HALL_LEFT, HALL_RIGHT, "dormitory"),
        ("left", HALL_FRONT, FRONT_FACE, "dormitory"),
        ("right", HALL_FRONT, FRONT_FACE, "dormitory"),
        ("left", BACK_FACE, HALL_BACK, "dormitory"),
        ("right", BACK_FACE, HALL_BACK, "linen"),
        ("back", HALL_LEFT, BABIES_WALL - WALL_HALF, "dormitory"),
        ("back", BABIES_WALL + WALL_HALF, WASH_WALL - WALL_HALF, "washroom"),
        ("back", WASH_WALL + WALL_HALF, HALL_RIGHT, "linen"),
    ),
    stone_floors=((BABIES_WALL + WALL_HALF, WASH_WALL - WALL_HALF, BACK_FACE, HALL_BACK),),
    furnish=furnish_reading,
)
