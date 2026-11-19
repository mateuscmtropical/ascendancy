"""Rooms of the service wing (hall `library`, ground floor, beside the vestibule on its +u side; the entry end is
u = -14.55, the exposed end wall u = 14.55 has the side windows).

The corridor (orphanage_wing_common.py) runs from the vestibule to the end window. Front band, on the facade:
  - Library (u -14.55..-1.96): tall bookcases on the three solid walls, six reading tables for 24 readers, the
    librarian's desk at the middle window, card catalogue, lectern, globe, ladder.
  - Study hall (u -1.66..8.03): 24 double desks for 48 pupils in two blocks facing the supervisor's platform and the
    board on the library wall (daylight from the pupils' left), shelves of school books, stove.
  - Laundry (u 8.33..14.55): wash tubs and the copper on the study wall, mangle, ironing tables, airers overhead.
Back band, on the yard:
  - Refectory (u -14.55..2.70): six long tables with benches for the 72 children in two rows of three, the sisters'
    table across the entry end, reading pulpit on a pier of the back wall, crockery dressers, the serving hatch from
    the kitchen opening on the middle aisle.
  - Kitchen (u 3.00..9.65): masonry range against the scullery wall, bread oven on a back pier, two worktables under
    a pan rack, the serving counter at the hatch, pot shelf, chopping block, firewood, water filter.
  - Scullery (u 9.95..14.55, d 13.75..18.70): two stone sinks, plate rack, copper for hot water, vegetables.
  - Pantry (u 9.95..14.55, d 19.00..24.10): shelves on the walls, sacks, barrels, hams on the beam hooks.
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
    WIDE_DOOR,
    corridor_walls,
    cross_wall,
    door,
    hatch,
    spaced,
)

LIBRARY_WALL = -1.81  # u of the wall between the library and the study hall (a facade pier)
LAUNDRY_WALL = 8.175  # u of the wall between the study hall and the laundry (a facade pier)
KITCHEN_WALL = 2.85  # u of the wall between the refectory and the kitchen (clear of the back window at 3.01)
SCULLERY_WALL = 9.8  # u of the wall between the kitchen and the scullery and pantry (a back pier)
PANTRY_WALL = 18.85  # d of the wall between the scullery and the pantry

KITCHEN_FACE = KITCHEN_WALL + WALL_HALF  # the refectory wall seen from the kitchen
REFECTORY_EAST = KITCHEN_WALL - WALL_HALF  # the kitchen wall seen from the refectory
RANGE_FACE = SCULLERY_WALL - WALL_HALF  # the scullery wall seen from the kitchen
SCULLERY_WEST = SCULLERY_WALL + WALL_HALF
LIBRARY_EAST = LIBRARY_WALL - WALL_HALF
STUDY_WEST = LIBRARY_WALL + WALL_HALF
STUDY_EAST = LAUNDRY_WALL - WALL_HALF
LAUNDRY_WEST = LAUNDRY_WALL + WALL_HALF
FRONT_FACE = FRONT_BAND[1]  # the corridor wall seen from the front rooms
BACK_FACE = BACK_BAND[0]  # the corridor wall seen from the back rooms

HATCH_D = 19.0  # the serving hatch opens on the middle aisle of the refectory
REFECTORY_DOOR = door(-1.0, WIDE_DOOR)  # the children come in at the lower end, by the hatch
SISTERS_DOOR = door(-12.9)  # beside the sisters' table
KITCHEN_DOOR = door(7.5)
SERVICE_DOOR = door(15.0)  # kitchen -> refectory, by the corridor
SCULLERY_DOOR = door(14.8)
PANTRY_DOOR = door(22.3)
LIBRARY_DOOR = door(-3.4)
STUDY_DOOR = door(6.8)
LAUNDRY_DOOR = door(11.0)

NEW_WALL_FINISHES = {
    "corridor": CORRIDOR_FINISH,
    "library": dict(dado="2F4A3A", trim="4A2F20"),
    "study": dict(dado="6E7F5A", trim="4A2F20"),
    "laundry": dict(dado="FFFFFF", trim="5A7A8C", material="azulejo", uv=("world", 1.2)),
    "refectory": dict(dado="3D4D5C", trim="5A3A26"),
    "kitchen": dict(dado="FFFFFF", trim="3A5E8C", material="azulejo", uv=("world", 1.2)),
    "scullery": dict(dado="FFFFFF", trim="3A5E8C", material="azulejo", uv=("world", 1.2)),
    "pantry": dict(dado="A88B5E", trim="5A3A26"),
}

# Refectory (long_table_set 3.6 x 0.9 m; a long_bench 0.32 m deep tucks against each side, its edge under the top)
CHILD_TABLE_US = (-10.0, -5.15, -0.3)  # three tables a row, 1.25 m between them
CHILD_ROW_DS = (16.9, 21.0)  # two rows: 2.4 m aisles to the corridor wall and in the middle, 2.3 m to the back wall
BENCH_OFFSET = 0.62  # table centre -> bench centre
SISTERS_TABLE_U = -13.55  # the sisters' table runs along d with their chairs against the entry wall
SISTERS_TABLE_DS = (17.15, 20.75)
CHAIR_OFFSET = 0.71  # table centre -> chair centre (the front of the seat at the edge of the top)
SEAT_PITCH = 0.6

# Library (reading_table 2 x 1 m turned along d, two chairs a side)
READING_TABLE_US = (-11.555, -8.255, -4.955)
READING_TABLE_DS = (4.2, 7.4)
READING_CHAIR_OFFSET = 0.77  # table centre -> chair centre

# Study hall (double_desk 1.15 x 0.9 m, the pupils face -u toward the board)
DESK_ROW_US = (2.2, 3.45, 4.7, 5.95)
DESK_COLUMN_DS = (1.775, 2.925, 4.075, 6.425, 7.575, 8.725)


def furnish_refectory(f) -> None:
    """Refectory (u -14.55..2.70, d 13.75..24.10): 72 children at six tables, the sisters' table of twelve across the
    entry end under the crucifix, the reader's pulpit, two crockery dressers, a lamp over every table."""
    for table_u, row_d in itertools.product(CHILD_TABLE_US, CHILD_ROW_DS):
        f.put("long_table_set", table_u, row_d)
        f.put("long_bench", table_u, row_d - BENCH_OFFSET)
        f.put("long_bench", table_u, row_d + BENCH_OFFSET, 180.0)
        f.put("hanging_oil_lamp", table_u, row_d)

    for table_d in SISTERS_TABLE_DS:
        f.put("long_table_set", SISTERS_TABLE_U, table_d, 90.0)

        for seat_d in spaced(table_d - 1.5, SEAT_PITCH, 6):
            f.put("bentwood_chair", SISTERS_TABLE_U - CHAIR_OFFSET, seat_d, 90.0)

    f.put("hanging_oil_lamp", SISTERS_TABLE_U, sum(SISTERS_TABLE_DS) / 2.0)
    f.on_wall("left", "wall_crucifix", sum(SISTERS_TABLE_DS) / 2.0)
    f.hang_picture("u", HALL_LEFT, 1, 15.6, "portrait")
    f.hang_picture("u", HALL_LEFT, 1, 22.3, "lady")

    f.on_wall("back", "reading_pulpit", -5.8)
    f.on_wall("back", "crockery_dresser", -9.83)
    f.on_wall("back", "crockery_dresser", -13.6)
    f.on_wall("back", "water_filter", 1.6)
    f.on_wall("back", "wall_clock", 0.0)

    f.hang_picture("d", BACK_FACE, 1, -7.3, "landscape")
    f.on_face("d", BACK_FACE, 1, "wall_sconce", -10.0, lit=False)
    f.on_face("d", BACK_FACE, 1, "wall_sconce", -4.6, lit=False)


def furnish_kitchen(f) -> None:
    """Kitchen (u 3.00..9.65, d 13.75..24.10): range against the scullery wall with the firewood beside it, the
    bread oven on the back pier with the flour sacks, two worktables under the pan rack, the serving counter at the
    hatch, pot shelf and plate rack on the corridor wall, chopping block, water filter."""
    f.on_face("u", RANGE_FACE, -1, "masonry_range", 17.6)
    f.on_face("u", RANGE_FACE, -1, "firewood_stack", 20.0)
    f.on_wall("back", "stone_oven", 5.8)
    f.on_wall("back", "flour_sacks", 3.75)

    for table_d in (16.6, 19.4):
        f.put("kitchen_worktable", 6.0, table_d, 90.0)

    f.put("hanging_pan_rack", 6.0, 18.0, 90.0)
    f.put("garlic_strings", 4.4, 22.0, 90.0)
    f.put("hanging_pots", 8.0, 15.4)
    f.on_face("u", KITCHEN_FACE, 1, "serving_counter", HATCH_D)
    f.on_face("u", KITCHEN_FACE, 1, "water_filter", 21.6)
    f.on_face("u", KITCHEN_FACE, 1, "wall_crucifix", 23.0)
    f.on_face("d", BACK_FACE, 1, "pot_shelf", 4.75)
    f.on_face("d", BACK_FACE, 1, "plate_rack", 9.0)
    f.put("chopping_block", 8.1, 21.4)

    f.put("hanging_oil_lamp", 6.0, 16.0)
    f.put("hanging_oil_lamp", 6.0, 20.6)


def furnish_scullery(f) -> None:
    """Scullery (u 9.95..14.55, d 13.75..18.70): stone sinks on the pantry wall and the corridor wall, plate rack by
    the end window, the copper for hot water in the corner, baskets of vegetables waiting to be washed."""
    f.on_face("d", PANTRY_WALL - WALL_HALF, -1, "stone_sink", 11.9)
    f.on_face("d", BACK_FACE, 1, "stone_sink", 12.6)
    f.on_wall("right", "plate_rack", 14.8)
    f.put("copper_boiler", 14.1, 18.15)
    f.put("wicker_basket", 10.6, 17.8, 90.0, variant="fruit")
    f.put("crate_open", 13.9, 16.6, -90.0, variant="roots")
    f.put("hanging_oil_lamp", 12.2, 16.2)


def furnish_pantry(f) -> None:
    """Pantry (u 9.95..14.55, d 19.00..24.10): shelves of jars and crocks on the back and scullery walls, a jam shelf
    on the end wall, sacks under the end window, barrels, hams and sausages on the beam hooks."""
    pantry_front = PANTRY_WALL + WALL_HALF

    for shelf_u in (11.2, 13.3):
        f.on_wall("back", "pantry_shelf", shelf_u)
        f.on_face("d", pantry_front, 1, "pantry_shelf", shelf_u)

    f.on_wall("right", "jam_shelf", 22.6)
    f.on_wall("right", "sack_pile", 20.9)
    f.put("barrel_group", 12.3, 21.6)
    f.put("ceiling_beam_hooks", 12.3, 21.6, 90.0, variant="sausages")
    f.put("hanging_oil_lamp", 11.2, 21.6, lit=False)


def furnish_library(f) -> None:
    """Library (u -14.55..-1.96, d 0.30..10.65): tall bookcases on the vestibule wall, the corridor wall and the
    study wall, six reading tables along d with their chairs (daylight from the side), the librarian's desk at the
    middle window, card catalogue by the door, lectern and globe at the other windows, rolling ladder."""
    for case_d in spaced(1.35, 2.0, 5):
        f.on_wall("left", "tall_bookcase", case_d)

    for case_u in spaced(-13.15, 1.92, 4):
        f.on_face("d", FRONT_FACE, -1, "tall_bookcase_slim", case_u)

    for case_d in spaced(1.56, 1.92, 5):
        f.on_face("u", LIBRARY_EAST, -1, "tall_bookcase_slim", case_d)

    f.on_face("d", FRONT_FACE, -1, "card_catalog", -5.5)
    f.put("rolling_ladder", -12.6, 9.7, 180.0)

    for table_u, table_d in itertools.product(READING_TABLE_US, READING_TABLE_DS):
        f.put("reading_table", table_u, table_d, 90.0)

        for side, seat_d in itertools.product((-1, 1), (table_d - 0.5, table_d + 0.5)):
            f.put("study_chair", table_u + side * READING_CHAIR_OFFSET, seat_d, -90.0 * side)

    for lamp_u in READING_TABLE_US:
        f.put("hanging_oil_lamp", lamp_u, sum(READING_TABLE_DS) / 2.0)

    f.put("teacher_desk", -8.255, f.front + 0.95, 180.0)
    f.put("lectern", -11.2, f.front + 0.6, 180.0)
    f.put("globe_stand", -5.15, f.front + 0.75)
    f.put("book_cart", -3.3, 9.0, 180.0)


def furnish_study(f) -> None:
    """Study hall (u -1.66..8.03, d 0.30..10.65): the supervisor's platform and the board on the library wall, 24
    double desks in two blocks of three columns facing them, shelves of school books and the stove on the laundry
    wall, maps and the clock."""
    f.on_face("u", STUDY_WEST, 1, "teacher_platform", 5.25)
    f.on_face("u", STUDY_WEST, 1, "blackboard_big", 5.25)
    f.on_face("u", STUDY_WEST, 1, "wall_map", 2.4, variant="world")
    f.on_face("u", STUDY_WEST, 1, "wall_map", 8.1, variant="country")

    for row_u, column_d in itertools.product(DESK_ROW_US, DESK_COLUMN_DS):
        f.put("double_desk", row_u, column_d, -90.0)

    for lamp_u, lamp_d in itertools.product((2.8, 5.4), (3.0, 7.6)):
        f.put("hanging_oil_lamp", lamp_u, lamp_d)

    f.on_face("u", STUDY_EAST, -1, "wall_shelf", 1.6, variant="books")
    f.on_face("u", STUDY_EAST, -1, "cast_iron_stove", 5.25)
    f.on_face("u", STUDY_EAST, -1, "wall_shelf", 8.2, variant="books")
    f.on_face("d", FRONT_FACE, -1, "wall_clock", 2.0)


def furnish_laundry(f) -> None:
    """Laundry (u 8.33..14.55, d 0.30..10.65): wash tubs and the copper along the study wall, the mangle and two
    ironing tables in the middle, airers of drying sheets overhead, a linen shelf on the end wall pier, baskets."""
    f.on_face("u", LAUNDRY_WEST, 1, "laundry_tubs", 2.4)
    f.on_face("u", LAUNDRY_WEST, 1, "laundry_tubs", 4.5)
    f.on_face("u", LAUNDRY_WEST, 1, "copper_boiler", 6.6)
    f.put("laundry_mangle", 11.6, 3.4)
    f.put("ironing_table", 11.6, 6.6)
    f.put("ironing_table", 11.6, 8.4)

    for airer_d in (3.0, 7.4):
        f.put("laundry_airer", 11.6, airer_d, 90.0)

    f.on_wall("right", "wall_shelf", 5.66, variant="linen")
    f.on_face("d", FRONT_FACE, -1, "wicker_basket", 9.2, variant="wool")
    f.on_face("d", FRONT_FACE, -1, "wicker_basket", 13.4, variant="wool")
    f.put("hanging_oil_lamp", 10.2, 5.2)
    f.put("hanging_oil_lamp", 13.0, 5.2)


def furnish_corridor(f) -> None:
    """Corridor (d 10.95..13.45): benches, pictures, the notice board and the sconces on its walls, lamps overhead."""
    front, back = CORRIDOR_CLEAR

    f.on_face("d", front, 1, "bench_long", -8.5)
    f.hang_picture("d", front, 1, -8.5, "landscape")
    f.on_face("d", front, 1, "notice_board", 1.2)
    f.on_face("d", back, -1, "bench_long", 4.0)
    f.hang_picture("d", back, -1, -7.0, "seascape")
    f.on_face("d", back, -1, "wall_crucifix", 11.5)

    for sconce_u in (-11.0, -5.0, 4.0, 9.0):
        f.on_face("d", front, 1, "wall_sconce", sconce_u, lit=sconce_u in (-5.0, 9.0))

    for lamp_u in (-9.0, 1.0, 10.5):
        f.put("hanging_oil_lamp", lamp_u, CORRIDOR_MIDDLE)


def furnish_library_wing(f) -> None:
    """Ground floor of the service wing. The rooms that need their night lamps most come first (the hall keeps only
    the first WING_FIXTURE_LIGHT['limit'] lights)."""
    furnish_refectory(f)
    furnish_kitchen(f)
    furnish_library(f)
    furnish_study(f)
    furnish_scullery(f)
    furnish_laundry(f)
    furnish_corridor(f)
    furnish_pantry(f)


PLAN = dict(
    keeper=(7.6, 18.0),  # the cook, between the worktables and the range
    posts=(),
    girder_pitch=2.4,
    partitions=(
        *corridor_walls(
            [(HALL_LEFT, LIBRARY_WALL, "library", [LIBRARY_DOOR]), (LIBRARY_WALL, LAUNDRY_WALL, "study", [STUDY_DOOR]), (LAUNDRY_WALL, HALL_RIGHT, "laundry", [LAUNDRY_DOOR])],
            [(HALL_LEFT, KITCHEN_WALL, "refectory", [SISTERS_DOOR, REFECTORY_DOOR]), (KITCHEN_WALL, SCULLERY_WALL, "kitchen", [KITCHEN_DOOR]), (SCULLERY_WALL, HALL_RIGHT, "scullery", [])],
            "corridor",
        ),
        cross_wall(LIBRARY_WALL, FRONT_BAND, "library", "study"),
        cross_wall(LAUNDRY_WALL, FRONT_BAND, "study", "laundry"),
        cross_wall(KITCHEN_WALL, BACK_BAND, "refectory", "kitchen", [SERVICE_DOOR, hatch(HATCH_D, 1.6)]),
        cross_wall(SCULLERY_WALL, (BACK_BAND[0], PANTRY_WALL - WALL_HALF), "kitchen", "scullery", [SCULLERY_DOOR]),
        cross_wall(SCULLERY_WALL, (PANTRY_WALL - WALL_HALF, HALL_BACK), "kitchen", "pantry", [PANTRY_DOOR]),
        ("d", PANTRY_WALL, SCULLERY_WEST, HALL_RIGHT, dict(faces=("scullery", "pantry"))),
    ),
    finishes=(
        ("front", HALL_LEFT, LIBRARY_EAST, "library"),
        ("front", STUDY_WEST, STUDY_EAST, "study"),
        ("front", LAUNDRY_WEST, HALL_RIGHT, "laundry"),
        ("left", HALL_FRONT, FRONT_FACE, "library"),
        ("left", CORRIDOR_CLEAR[0], CORRIDOR_CLEAR[1], "corridor"),
        ("left", BACK_FACE, HALL_BACK, "refectory"),
        ("right", HALL_FRONT, FRONT_FACE, "laundry"),
        ("right", CORRIDOR_CLEAR[0], CORRIDOR_CLEAR[1], "corridor"),
        ("right", BACK_FACE, PANTRY_WALL - WALL_HALF, "scullery"),
        ("right", PANTRY_WALL + WALL_HALF, HALL_BACK, "pantry"),
        ("back", HALL_LEFT, REFECTORY_EAST, "refectory"),
        ("back", KITCHEN_FACE, RANGE_FACE, "kitchen"),
        ("back", SCULLERY_WEST, HALL_RIGHT, "pantry"),
    ),
    stone_floors=(
        (KITCHEN_FACE, RANGE_FACE, BACK_FACE, HALL_BACK),
        (SCULLERY_WEST, HALL_RIGHT, BACK_FACE, HALL_BACK),
        (LAUNDRY_WEST, HALL_RIGHT, HALL_FRONT, FRONT_FACE),
    ),
    furnish=furnish_library_wing,
)
