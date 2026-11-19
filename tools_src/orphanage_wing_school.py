"""Rooms of the school wing (hall `school`, ground floor, beside the vestibule on its -u side; the entry end is
u = 14.55, the exposed end wall u = -14.55 has the side windows).

The corridor (orphanage_wing_common.py) runs from the vestibule to the end window. Front band, on the facade, three
classrooms of 16 double desks (32 pupils) each, the daylight always on the pupils' left:
  - First class (u 5.29..14.55) and second class (u -4.99..4.99): the board and the teacher's platform on the wall
    toward the end of the wing, the pupils facing -u with the facade windows on their left.
  - Third class (u -14.55..-5.29): the board on the corridor wall, the pupils facing it with the end windows on
    their left.
Back band, under the high windows:
  - Fencing hall (u -14.55..4.65): two 14 m pistes along the hall with their run-backs, racks of foils and masks
    and a trophy of arms on the back wall, plastrons and pells, mirror, the spectators' benches on the corridor wall.
  - Magic practice room (u 4.95..14.55): a casting range across the room, the warded line where the pupils stand,
    three straw targets against the back wall, rune pillars in its corners, lecterns, the master's demonstration
    table, staffs, scrolls and grimoires.
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
    spaced,
)

FIRST_WALL = 5.1375  # u of the wall between the first and the second class (a facade pier)
THIRD_WALL = -5.1375  # u of the wall between the second and the third class (a facade pier)
SALLE_WALL = 4.8  # u of the wall between the fencing hall and the magic room (a back pier)

FRONT_FACE = FRONT_BAND[1]  # the corridor wall seen from the front rooms
BACK_FACE = BACK_BAND[0]  # the corridor wall seen from the back rooms
FIRST_WEST = FIRST_WALL + WALL_HALF
SECOND_WEST = THIRD_WALL + WALL_HALF
SECOND_EAST = FIRST_WALL - WALL_HALF
THIRD_EAST = THIRD_WALL - WALL_HALF
SALLE_EAST = SALLE_WALL - WALL_HALF
MAGIC_WEST = SALLE_WALL + WALL_HALF

FIRST_DOOR = door(13.4)
SECOND_DOOR = door(4.0)
THIRD_DOOR = door(-13.6)
SALLE_DOOR = door(-2.0, WIDE_DOOR)
MAGIC_DOOR = door(6.2)

NEW_WALL_FINISHES = {
    "corridor": CORRIDOR_FINISH,
    "classroom": dict(dado="3D5060", trim="5A3A26"),
    "salle": dict(dado="6B4A2E", trim="3A2618"),  # dark oak panelling of the fencing hall
    "arcane": dict(dado="2E3A5C", trim="2A2118"),
}

DESK = "double_desk"  # 1.15 x 0.9 m, two pupils on the bench behind the sloped lid
DESK_PITCH = 1.2
BLOCK_DS = (3.15, 4.3, 6.65, 7.8)  # two blocks of two columns, 1.2 m aisle between them
FIRST_ROW_US = spaced(9.04, DESK_PITCH, 4)  # pupils face -u
SECOND_ROW_US = spaced(-1.24, DESK_PITCH, 4)
THIRD_ROW_DS = spaced(6.9, -DESK_PITCH, 4)  # pupils face +d
THIRD_BLOCK_US = (-12.43, -11.28, -8.93, -7.78)
BOARD_D = sum(BLOCK_DS) / len(BLOCK_DS)

PISTE_U = -5.0  # centre of both pistes (14 m, with 1.5 m run-backs to -13.5 and 3.5)
PISTE_DS = (16.6, 21.3)
GANGWAY_D = sum(PISTE_DS) / 2.0  # the floor between the pistes
TARGET_US = (7.0, 9.75, 12.5)
WARD_D = 17.6


def classroom_walls(f, board_axis: str, board_face: float, board_normal: int, board_along: float, back_items: list) -> None:
    """Board, platform, crucifix, maps and clock of a classroom; back_items are (axis, face, normal, name, along,
    options) on the other walls."""
    f.on_face(board_axis, board_face, board_normal, "teacher_platform", board_along)
    f.on_face(board_axis, board_face, board_normal, "blackboard_big", board_along)

    for axis, face, normal, name, along, options in back_items:
        f.on_face(axis, face, normal, name, along, **options)


def furnish_first(f) -> None:
    """First class (u 5.29..14.55, d 0.30..10.65): board and platform on the second class's wall, four rows of four
    double desks facing them, cupboard, abacus, maps, stove, the coat pegs by the door."""
    classroom_walls(f, "u", FIRST_WEST, 1, BOARD_D, [
        ("u", FIRST_WEST, 1, "wall_map", 1.6, dict(variant="alphabet")),
        ("u", FIRST_WEST, 1, "wall_map", 9.4, dict(variant="world")),
        ("d", FRONT_FACE, -1, "specimen_cupboard", 7.0, {}),
        ("d", FRONT_FACE, -1, "clothes_pegs", 10.6, {}),
        ("d", FRONT_FACE, -1, "wall_clock", 9.0, {}),
    ])

    for row_u, column_d in itertools.product(FIRST_ROW_US, BLOCK_DS):
        f.put(DESK, row_u, column_d, -90.0)

    f.on_wall("right", "abacus_stand", 1.2)
    f.on_wall("right", "cast_iron_stove", 5.5)
    f.put("hanging_oil_lamp", 10.2, 3.7)
    f.put("hanging_oil_lamp", 10.2, 7.2)


def furnish_second(f) -> None:
    """Second class (u -4.99..4.99, d 0.30..10.65): board and platform on the third class's wall, four rows of four
    double desks, the bookcase of readers and the stove on the first class's wall, maps, clock, pegs."""
    classroom_walls(f, "u", SECOND_WEST, 1, BOARD_D, [
        ("u", SECOND_WEST, 1, "wall_map", 1.6, dict(variant="country")),
        ("u", SECOND_WEST, 1, "wall_map", 9.4, dict(variant="botany")),
        ("u", SECOND_EAST, -1, "wall_shelf", 2.0, dict(variant="books")),
        ("u", SECOND_EAST, -1, "cast_iron_stove", 5.5, {}),
        ("u", SECOND_EAST, -1, "specimen_cupboard", 8.2, {}),
        ("d", FRONT_FACE, -1, "clothes_pegs", -1.0, {}),
        ("d", FRONT_FACE, -1, "wall_clock", 1.5, {}),
    ])

    for row_u, column_d in itertools.product(SECOND_ROW_US, BLOCK_DS):
        f.put(DESK, row_u, column_d, -90.0)

    f.put("hanging_oil_lamp", 0.6, 3.7)
    f.put("hanging_oil_lamp", 0.6, 7.2)


def furnish_third(f) -> None:
    """Third class of the older pupils (u -14.55..-5.29, d 0.30..10.65): board and platform on the corridor wall,
    four rows of four double desks facing +d with the end windows on their left, globe, cupboard, stove, pegs."""
    classroom_walls(f, "d", FRONT_FACE, -1, -9.92, [
        ("d", FRONT_FACE, -1, "wall_map", -6.6, dict(variant="world")),
        ("u", THIRD_EAST, -1, "specimen_cupboard", 3.0, {}),
        ("u", THIRD_EAST, -1, "cast_iron_stove", 6.2, {}),
        ("u", THIRD_EAST, -1, "clothes_pegs", 8.6, {}),
    ])

    for row_d, column_u in itertools.product(THIRD_ROW_DS, THIRD_BLOCK_US):
        f.put(DESK, column_u, row_d, 180.0)

    f.put("globe_stand", -13.9, 1.0)
    f.put("hanging_oil_lamp", -10.1, 3.4)
    f.put("hanging_oil_lamp", -10.1, 6.6)


def furnish_salle(f) -> None:
    """Fencing hall (u -14.55..4.65, d 13.75..24.10): two pistes along the hall, racks of foils and masks, a trophy of
    arms and a mirror on the back wall, plastrons on the end wall between its windows, two pells in the gangway,
    benches, boots and the bout board on the corridor wall, lamps over the pistes."""
    for piste_d in PISTE_DS:
        f.put("fencing_piste", PISTE_U, piste_d)

    for rack_u in (-11.9, -1.2, 2.8):
        f.on_wall("back", "fencing_rack", rack_u)

    f.on_wall("back", "sword_wall", -6.0)
    f.on_wall("back", "standing_mirror", -9.6)
    f.on_wall("back", "armor_stand_a", 0.7)

    for target_d in (18.4, 19.5):
        f.on_wall("left", "plastron_target", target_d)

    f.put("pell_post", 3.6, GANGWAY_D)
    f.put("pell_post", -12.6, GANGWAY_D)

    for bench_u in (-11.0, -6.5, 1.5):
        f.on_face("d", BACK_FACE, 1, "bench_long", bench_u)

    f.on_face("d", BACK_FACE, 1, "boots_rack", -8.6)
    f.on_face("d", BACK_FACE, 1, "rank_board", -4.4)
    f.on_face("d", BACK_FACE, 1, "clothes_pegs", 3.6)

    for lamp_u, lamp_d in itertools.product((-9.0, -1.0), PISTE_DS):
        f.put("hanging_oil_lamp", lamp_u, lamp_d)


def furnish_magic(f) -> None:
    """Magic practice room (u 4.95..14.55, d 13.75..24.10): the warded line across the room where the pupils stand,
    three straw targets against the back wall, rune pillars in the back corners, four lecterns behind the line, the
    master's demonstration table, staffs on the fencing hall's wall, grimoires and scrolls on the vestibule wall."""
    f.put("ward_line", sum(TARGET_US) / 2.0, WARD_D)

    for target_u in TARGET_US:
        f.on_wall("back", "practice_dummy", target_u)

    f.put("rune_pillar", MAGIC_WEST + 0.5, HALL_BACK - 0.5)
    f.put("rune_pillar", HALL_RIGHT - 0.5, HALL_BACK - 0.5)

    for lectern_u in (6.8, 8.8, 10.8, 12.8):
        f.put("lectern", lectern_u, 16.2, 180.0)

    f.on_face("d", BACK_FACE, 1, "enchant_table", 10.0)
    f.on_face("u", MAGIC_WEST, 1, "staff_rack", 18.0)
    f.on_face("u", MAGIC_WEST, 1, "scroll_rack", 21.0)
    f.on_wall("right", "tall_bookcase", 16.5)
    f.on_wall("right", "crystal_ball_pedestal", 19.5)
    f.on_wall("right", "star_tapestry", 21.6)
    f.put("hanging_oil_lamp", 9.75, 15.4)


def furnish_corridor(f) -> None:
    """Corridor (d 10.95..13.45): benches, the notice board, the school bell, pictures and lamps."""
    front, back = CORRIDOR_CLEAR

    f.on_face("d", front, 1, "notice_board", 8.0)
    f.on_face("d", front, 1, "bench_long", -1.0)
    f.on_face("d", back, -1, "bench_long", -9.0)
    f.hang_picture("d", back, -1, -9.0, "portrait")
    f.on_face("d", back, -1, "wall_crucifix", 10.5)
    f.put("school_bell", 10.0, CORRIDOR_MIDDLE)

    for lamp_u in (-9.5, 0.5, 9.5):
        f.put("hanging_oil_lamp", lamp_u, CORRIDOR_MIDDLE)


def furnish_school(f) -> None:
    """Ground floor of the school wing; the rooms that need their night lamps most come first."""
    furnish_salle(f)
    furnish_magic(f)
    furnish_corridor(f)
    furnish_first(f)
    furnish_second(f)
    furnish_third(f)


PLAN = dict(
    keeper=(-5.0, GANGWAY_D),  # the fencing master, between the pistes
    posts=(),
    girder_pitch=2.4,
    partitions=(
        *corridor_walls(
            [(HALL_LEFT, THIRD_WALL, "classroom", [THIRD_DOOR]), (THIRD_WALL, FIRST_WALL, "classroom", [SECOND_DOOR]), (FIRST_WALL, HALL_RIGHT, "classroom", [FIRST_DOOR])],
            [(HALL_LEFT, SALLE_WALL, "salle", [SALLE_DOOR]), (SALLE_WALL, HALL_RIGHT, "arcane", [MAGIC_DOOR])],
            "corridor",
        ),
        cross_wall(THIRD_WALL, FRONT_BAND, "classroom", "classroom"),
        cross_wall(FIRST_WALL, FRONT_BAND, "classroom", "classroom"),
        cross_wall(SALLE_WALL, BACK_BAND, "salle", "arcane"),
    ),
    finishes=(
        ("front", HALL_LEFT, HALL_RIGHT, "classroom"),
        ("left", HALL_FRONT, FRONT_FACE, "classroom"),
        ("left", CORRIDOR_CLEAR[0], CORRIDOR_CLEAR[1], "corridor"),
        ("left", BACK_FACE, HALL_BACK, "salle"),
        ("right", HALL_FRONT, FRONT_FACE, "classroom"),
        ("right", CORRIDOR_CLEAR[0], CORRIDOR_CLEAR[1], "corridor"),
        ("right", BACK_FACE, HALL_BACK, "arcane"),
        ("back", HALL_LEFT, SALLE_EAST, "salle"),
        ("back", MAGIC_WEST, HALL_RIGHT, "arcane"),
    ),
    furnish=furnish_school,
)
