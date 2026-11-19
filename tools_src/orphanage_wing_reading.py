"""Rooms of the children's wing (hall `reading`, upper floor over the service wing; the entry end u = -14.55 opens on
the gallery of the vestibule, the exposed end wall u = 14.55 has the side windows).

The corridor (orphanage_wing_common.py) runs from the gallery to the end window. Front band, behind the balcony
windows of the facade:
  - Boys' dormitory (u -14.55..1.66): 24 iron beds in three rows (one with the heads on the corridor wall, a
    head-to-head double row in the middle), a locker by every head, a trunk at the foot of the outer rows, the
    sister's curtained bed at the end of the double row; the strip by the windows stays free.
  - Boys' washroom (u 1.96..8.03): two stone troughs, four latrine stalls, two tubs behind a screen.
  - Nursery (u 8.33..14.55): 16 cots for the little ones in two lines, the sister's bed behind a screen, toys.
Back band, under the high windows:
  - Girls' dormitory (u -14.55..5.85): 32 beds in four rows (heads on the corridor wall, a head-to-head double row,
    heads on the back wall), a locker by every head, the sister's alcove in the corner by the door, presses, pegs
    and washstands at the far end.
  - Girls' washroom (u 6.15..10.15): troughs, a basin row, three latrine stalls, a tub behind a screen.
  - Linen room (u 10.45..14.55): presses and shelves of linen, the mending table.
"""

import itertools

from orphanage_wing_common import (
    BACK_BAND,
    CORRIDOR_CLEAR,
    CORRIDOR_FINISH,
    CORRIDOR_MIDDLE,
    FRONT_BAND,
    HALL_BACK,
    HALL_FRONT,
    HALL_LEFT,
    HALL_RIGHT,
    WALL_HALF,
    bed_row,
    corridor_walls,
    cross_wall,
    door,
    spaced,
)

BOYS_WALL = 1.81  # u of the wall between the boys' dormitory and their washroom (a facade pier)
NURSERY_WALL = 8.175  # u of the wall between the boys' washroom and the nursery (a facade pier)
GIRLS_WALL = 6.0  # u of the wall between the girls' dormitory and their washroom (a back pier)
LINEN_WALL = 10.3  # u of the wall between the girls' washroom and the linen room (a back pier)

FRONT_FACE = FRONT_BAND[1]  # the corridor wall seen from the front rooms
BACK_FACE = BACK_BAND[0]  # the corridor wall seen from the back rooms
BOYS_EAST = BOYS_WALL - WALL_HALF
BOYS_WASH_WEST = BOYS_WALL + WALL_HALF
BOYS_WASH_EAST = NURSERY_WALL - WALL_HALF
NURSERY_WEST = NURSERY_WALL + WALL_HALF
GIRLS_EAST = GIRLS_WALL - WALL_HALF
GIRLS_WASH_WEST = GIRLS_WALL + WALL_HALF
GIRLS_WASH_EAST = LINEN_WALL - WALL_HALF
LINEN_WEST = LINEN_WALL + WALL_HALF

BOYS_DOOR = door(-13.9)
NURSERY_DOOR = door(9.4)
GIRLS_DOOR = door(-13.2)
LINEN_DOOR = door(12.5)
BOYS_WASH_DOOR = door(9.3)
GIRLS_WASH_DOOR = door(16.3)

NEW_WALL_FINISHES = {
    "corridor": CORRIDOR_FINISH,
    "washroom": dict(dado="FFFFFF", trim="5A3A26", material="azulejo", uv=("world", 1.2)),
    "linen": dict(dado="8FA596", trim="5A3A26"),
    "nursery": dict(dado="9DB8C9", trim="5A3A26"),
}

BED = "child_bed"  # 0.86 x 1.85 m
BED_LENGTH = 1.85
GIRLS_BLANKET = "dull_red"
BOYS_BLANKET = "grey_blue"
GIRLS_BED_US = spaced(-11.5, 1.75, 8)  # a locker beside every head, 0.9 m between neighbours
GIRLS_HEADS = ((BACK_FACE, 1), (18.85, -1), (18.95, 1), (HALL_BACK, -1))  # (d of the heads, side the beds lie on)
BOYS_OUTER_US = spaced(-12.6, 1.55, 8)
BOYS_MIDDLE_US = spaced(-12.9, 1.55, 8)
BOYS_HEADS_MIDDLE = ((5.1, 1), (5.0, -1))
TRUNK_DEPTH = 0.45
COT_DS = spaced(0.9, 0.95, 9)  # cots along the nursery's west wall
COT_END_DS = (0.9, 1.9, 4.7, 5.65, 6.6, 9.1, 10.05)  # cots along the end wall, between its windows


def furnish_girls(f) -> None:
    """Girls' dormitory (u -14.55..5.85, d 13.75..24.10): four rows of eight beds with a locker by every head, the
    sister's curtained alcove in the corner by the door, washstands on the entry wall, presses, pegs and the
    crucifix with a kneeler at the far end, lamps down the two aisles."""
    for head_d, normal in GIRLS_HEADS:
        bed_row(f, BED, GIRLS_BED_US, head_d, normal, variant=GIRLS_BLANKET)

    f.put("supervisor_alcove", -13.25, HALL_BACK - 1.3)
    f.put("iron_bed", -13.79, HALL_BACK - 1.0, 0.0, variant="ochre")
    f.put("night_table", -13.04, HALL_BACK - 0.19)
    f.put("oil_lamp_table", -13.04, HALL_BACK - 0.19, z=f.base + 0.73)

    for stand_d in (16.3, 17.3, 18.3, 19.3):
        f.on_wall("left", "washstand", stand_d)

    for press_d in (14.6, 21.3):
        f.on_face("u", GIRLS_EAST, -1, "linen_press", press_d)

    f.on_face("u", GIRLS_EAST, -1, "clothes_pegs", 19.0)
    f.on_face("u", GIRLS_EAST, -1, "wall_crucifix", 23.2)
    f.on_face("u", GIRLS_EAST, -1, "prie_dieu", 23.2)

    for lamp_u, lamp_d in itertools.product((-7.5, -1.0), (16.3, 21.5)):
        f.put("hanging_oil_lamp", lamp_u, lamp_d, lit=lamp_d < 20.0 or lamp_u < -5.0)


def furnish_girls_washroom(f) -> None:
    """Girls' washroom (u 6.15..10.15, d 13.75..24.10): two troughs on the linen room wall, a basin row under the back
    window, three latrine stalls in the corner, a tub behind a folding screen, towel rack and bench."""
    for trough_d in (15.6, 18.9):
        f.on_face("u", GIRLS_WASH_EAST, -1, "washroom_trough", trough_d)

    f.on_wall("back", "basin_row", 8.4)

    for stall_d in (20.6, 21.6, 22.6):
        f.on_face("u", GIRLS_WASH_WEST, 1, "latrine_stall", stall_d)

    f.on_face("d", BACK_FACE, 1, "tin_bathtub", 8.6)
    f.put("folding_screen", 8.6, 15.4)
    f.on_face("u", GIRLS_WASH_WEST, 1, "towel_rack", 18.6)
    f.put("hanging_oil_lamp", 8.15, 19.0)


def furnish_linen(f) -> None:
    """Linen room (u 10.45..14.55, d 13.75..24.10): presses along the washroom wall and on the back wall, a shelf of
    folded linen on the end wall pier, the mending table with two chairs, baskets of mending."""
    for press_d in (16.0, 17.8, 19.6, 21.4, 23.2):
        f.on_face("u", LINEN_WEST, 1, "linen_press", press_d)

    f.on_wall("back", "linen_press", 13.3)
    f.on_wall("right", "wall_shelf", 18.74, variant="linen")
    f.put("cutting_table", 12.9, 20.3, 90.0)
    f.put("bentwood_chair", 12.0, 19.6, -90.0)
    f.put("bentwood_chair", 13.8, 21.0, 90.0)
    f.put("yarn_basket", 13.95, 22.5)
    f.put("wicker_basket", 12.0, 15.5, variant="wool")
    f.put("hanging_oil_lamp", 12.9, 20.3)


def furnish_boys(f) -> None:
    """Boys' dormitory (u -14.55..1.66, d 0.30..10.65): a row of beds with their heads on the corridor wall and a
    head-to-head double row in the middle, a locker by every head, a trunk at the foot of the outer rows, the
    sister's alcove closing the end of the double row; the strip by the balcony windows stays free."""
    bed_row(f, BED, BOYS_OUTER_US, FRONT_FACE, -1, variant=BOYS_BLANKET)

    for head_d, normal in BOYS_HEADS_MIDDLE:
        bed_row(f, BED, BOYS_MIDDLE_US, head_d, normal, variant=BOYS_BLANKET)

    outer_trunk_d = FRONT_FACE - BED_LENGTH - TRUNK_DEPTH / 2.0
    window_trunk_d = BOYS_HEADS_MIDDLE[1][0] - BED_LENGTH - TRUNK_DEPTH / 2.0

    for bed_u in BOYS_OUTER_US:
        f.put("bed_trunk", bed_u, outer_trunk_d)

    for bed_u in BOYS_MIDDLE_US:
        f.put("bed_trunk", bed_u, window_trunk_d)

    f.put("supervisor_alcove", 0.36, 5.05, 180.0)  # opens on the aisle behind the double row
    f.put("iron_bed", -0.2, 4.85, 180.0, variant="ochre")
    f.put("night_table", 0.9, 3.95, 180.0)
    f.put("oil_lamp_table", 0.9, 3.95, z=f.base + 0.73)

    f.on_face("u", BOYS_EAST, -1, "linen_press", 1.2)
    f.on_face("u", BOYS_EAST, -1, "clothes_pegs", 7.6)
    f.on_wall("left", "wall_crucifix", 5.05)
    f.on_wall("left", "prie_dieu", 5.05)

    for lamp_u, lamp_d in itertools.product((-9.5, -3.5), (2.9, 7.65)):
        f.put("hanging_oil_lamp", lamp_u, lamp_d, lit=lamp_d > 5.0)


def furnish_boys_washroom(f) -> None:
    """Boys' washroom (u 1.96..8.03, d 0.30..10.65): a trough on the corridor wall and one on the nursery wall, four
    latrine stalls along the nursery wall by the facade, two tubs behind a screen, bench and pegs."""
    f.on_face("d", FRONT_FACE, -1, "washroom_trough", 4.6)
    f.on_face("u", BOYS_WASH_EAST, -1, "washroom_trough", 7.9)

    for stall_d in (1.0, 2.0, 3.0, 4.0):
        f.on_face("u", BOYS_WASH_EAST, -1, "latrine_stall", stall_d)

    for tub_d in (4.6, 6.4):
        f.put("tin_bathtub", 3.1, tub_d, 90.0)

    f.put("folding_screen", 4.3, 5.5, 90.0)
    f.on_face("u", BOYS_WASH_WEST, 1, "towel_rack", 2.0)
    f.on_face("u", BOYS_WASH_WEST, 1, "bench_long", 7.6)
    f.put("hanging_oil_lamp", 5.0, 5.5)


def furnish_nursery(f) -> None:
    """Nursery (u 8.33..14.55, d 0.30..10.65): 16 cots in two lines (heads to the washroom wall, heads to the end
    wall between its windows), the sister's bed behind a screen by the door, a low table, toys, a rocking chair."""
    for cot_d in COT_DS:
        f.on_face("u", NURSERY_WEST, 1, "cot", cot_d, variant="green")

    for cot_d in COT_END_DS:
        f.on_wall("right", "cot", cot_d, variant="ochre")

    f.put("iron_bed", 11.4, 9.3, 0.0, variant="grey_blue")
    f.put("folding_screen", 11.4, 7.95)
    f.put("toy_chest", 11.5, 1.0, 180.0)
    f.put("rocking_horse", 11.5, 3.5, 90.0)
    f.put("dollhouse", 11.5, 5.5, 90.0)
    f.put("armchair", 12.2, 6.8, -60.0)
    f.on_face("d", FRONT_FACE, -1, "wall_crucifix", 12.6)
    f.put("hanging_oil_lamp", 11.4, 4.2)


def furnish_corridor(f) -> None:
    """Corridor (d 10.95..13.45): pegs and benches by the dormitory doors, pictures, a saint's niche, lamps."""
    front, back = CORRIDOR_CLEAR

    f.on_face("d", front, 1, "bench_long", -9.0)
    f.on_face("d", front, 1, "clothes_pegs", -9.0)
    f.on_face("d", back, -1, "bench_long", -8.0)
    f.hang_picture("d", back, -1, -3.0, "portrait")
    f.on_face("d", front, 1, "saint_niche", 4.5)
    f.on_face("d", back, -1, "wall_clock", 4.0)

    for lamp_u in (-9.0, 1.0, 10.5):
        f.put("hanging_oil_lamp", lamp_u, CORRIDOR_MIDDLE)


def furnish_reading(f) -> None:
    """Upper floor of the children's wing; the rooms that need their night lamps most come first."""
    furnish_girls(f)
    furnish_boys(f)
    furnish_nursery(f)
    furnish_corridor(f)
    furnish_girls_washroom(f)
    furnish_boys_washroom(f)
    furnish_linen(f)


PLAN = dict(
    keeper=(-10.0, 16.3),  # the girls' sister, in the aisle of their dormitory
    posts=(),
    girder_pitch=2.4,
    partitions=(
        *corridor_walls(
            [(HALL_LEFT, BOYS_WALL, "dormitory", [BOYS_DOOR]), (BOYS_WALL, NURSERY_WALL, "washroom", []), (NURSERY_WALL, HALL_RIGHT, "nursery", [NURSERY_DOOR])],
            [(HALL_LEFT, GIRLS_WALL, "dormitory", [GIRLS_DOOR]), (GIRLS_WALL, LINEN_WALL, "washroom", []), (LINEN_WALL, HALL_RIGHT, "linen", [LINEN_DOOR])],
            "corridor",
        ),
        cross_wall(BOYS_WALL, FRONT_BAND, "dormitory", "washroom", [BOYS_WASH_DOOR]),
        cross_wall(NURSERY_WALL, FRONT_BAND, "washroom", "nursery"),
        cross_wall(GIRLS_WALL, BACK_BAND, "dormitory", "washroom", [GIRLS_WASH_DOOR]),
        cross_wall(LINEN_WALL, BACK_BAND, "washroom", "linen"),
    ),
    finishes=(
        ("front", HALL_LEFT, BOYS_EAST, "dormitory"),
        ("front", BOYS_WASH_WEST, BOYS_WASH_EAST, "washroom"),
        ("front", NURSERY_WEST, HALL_RIGHT, "nursery"),
        ("left", HALL_FRONT, FRONT_FACE, "dormitory"),
        ("left", CORRIDOR_CLEAR[0], CORRIDOR_CLEAR[1], "corridor"),
        ("left", BACK_FACE, HALL_BACK, "dormitory"),
        ("right", HALL_FRONT, FRONT_FACE, "nursery"),
        ("right", CORRIDOR_CLEAR[0], CORRIDOR_CLEAR[1], "corridor"),
        ("right", BACK_FACE, HALL_BACK, "linen"),
        ("back", HALL_LEFT, GIRLS_EAST, "dormitory"),
        ("back", GIRLS_WASH_WEST, GIRLS_WASH_EAST, "washroom"),
        ("back", LINEN_WEST, HALL_RIGHT, "linen"),
    ),
    stone_floors=(
        (BOYS_WASH_WEST, BOYS_WASH_EAST, HALL_FRONT, FRONT_FACE),
        (GIRLS_WASH_WEST, GIRLS_WASH_EAST, BACK_FACE, HALL_BACK),
    ),
    furnish=furnish_reading,
)
