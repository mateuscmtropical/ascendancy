"""Rooms of the school wing (ground floor, left wing of the orphanage: hall `school`).

Seven rooms arranged in two bands split by a long partition at d = 8.2:
  - Front band (d = 0.3..8.05): Cloakroom passage at the vestibule end, Classroom 1, Classroom 2, Science cabinet.
  - Back band (d = 8.35..19.1): Study hall at the vestibule end, Teachers' room, Headmaster's study.

All cross walls in the front band stand on facade piers so no window is cut; every room is reachable on foot from
the existing vestibule doorway on the right wall (u = 14.55, d = 3.0).
"""

import itertools

WALL_HALF = 0.15  # half the thickness of an inner partition (WALL = 0.3 in build_market_shops.py)

HALL_LEFT = -14.55
HALL_RIGHT = 14.55
HALL_FRONT = 0.3
HALL_BACK = 19.1
LONG_WALL = 8.2

CLOAKROOM_WALL = 11.21   # facade pier between cloakroom passage and classroom 1
CLASS_WALL = 1.805       # facade pier between classroom 1 and classroom 2
SCIENCE_WALL = -8.17     # facade pier between classroom 2 and science cabinet
STUDY_WALL = -2.85       # back-band cross wall between study hall and teachers' room (clear of back windows)
DIRECTOR_WALL = -9.40    # back-band cross wall between teachers' room and headmaster's study

INNER_FACE = LONG_WALL - WALL_HALF  # the long wall seen from the front band
BACK_FACE = LONG_WALL + WALL_HALF   # the long wall seen from the back band

CLASS_1_DOOR = dict(at=7.15, width=1.5, height=2.1, leaf=("low", -1))
CLASS_2_DOOR = dict(at=7.15, width=1.5, height=2.1, leaf=("low", -1))
SCIENCE_DOOR = dict(at=7.15, width=1.5, height=2.1, leaf=("low", -1))
STUDY_DOOR = dict(at=12.90, width=1.5, height=2.1, leaf=("high", -1))
TEACHERS_DOOR = dict(at=13.70, width=1.5, height=2.1, leaf=("low", 1))
DIRECTOR_DOOR = dict(at=13.70, width=1.5, height=2.1, leaf=("low", 1))

DESK_ROW_PITCH = 1.3
DESK_ROW_FIRST = 3.545  # from the board wall to the first row of double desks: 1.1 m clear of the teacher's platform
DESK_COLUMNS = (1.275, 2.475, 4.825, 6.025)  # two blocks of two columns with a 1.2 m aisle at d = 3.05..4.25
DESK_ROWS = 4
STUDY_TABLE_US = (0.70, 4.90, 9.10)  # three tables per row, pitch 4.2 m
STUDY_TABLE_DS = (11.40, 16.00)
STUDY_CHAIR_OFFSETS = (-1.00, -0.35, 0.35, 1.00)
STUDY_LIT_TABLES = {(0.70, 11.40), (9.10, 16.00)}  # tables whose lamp really lights

NEW_WALL_FINISHES = {
    "classroom": dict(dado="3D5060", trim="5A3A26"),  # dark blue-grey dado for classrooms, study hall, cloakroom
    "science": dict(dado="5A7082", trim="5A3A26"),    # cooler blue-grey dado for the science cabinet
    "teachers": dict(dado="6B442D", trim="4A2D1C"),   # dark wood panelling tone for teachers' room and study
}


def furnish_cloakroom(f) -> None:
    """Cloakroom passage (u = 11.36..14.55, d = 0.3..8.05): the vestibule doorway is at d = 3.0. Pegs, boot rack,
    two benches with the hand bell, notice board, crucifix, school bell, clock over the door to the study hall."""
    west_face = CLOAKROOM_WALL + WALL_HALF  # 11.36

    f.on_wall("front", "bench_long", 12.73)  # under the front window (sill 0.9)

    # West wall: only d = 0.3..1.6 and 4.4..6.2 are free (the doorway lane and the door to classroom 1)
    f.on_face("u", west_face, 1, "notice_board", 1.40)
    f.on_face("u", west_face, 1, "wall_crucifix", 3.00)
    f.on_face("u", west_face, 1, "clothes_pegs", 5.20)
    f.on_face("u", west_face, 1, "boots_rack", 5.20)

    # East wall past the folded leaves of the vestibule door
    f.on_wall("right", "clothes_pegs", 6.70)
    f.on_wall("right", "bench_long", 6.70)
    f.put("brass_bell", 14.33, 7.20, z=0.55)

    f.on_face("d", INNER_FACE, -1, "wall_clock", STUDY_DOOR["at"], z=0.45)

    f.put("school_bell", 12.95, 5.60)
    f.put("hanging_oil_lamp", 13.00, 3.00)
    f.put("hanging_oil_lamp", 12.60, 6.50)
    f.on_face("u", west_face, 1, "wall_sconce", 2.20, lit=False)
    f.on_face("u", west_face, 1, "wall_sconce", 6.10)
    f.on_wall("right", "wall_sconce", 5.80)


def furnish_classroom(f, west_face: float, east_face: float, wall_maps: tuple, stove_d: float, side_wall: tuple, front_sconce_us: tuple) -> None:
    """One classroom: 16 double desks in 4 rows facing the blackboard and the teacher's platform on the west wall, an
    abacus, a map by the board; on the long wall maps, a clock, a crucifix and sconces; on the east wall a cupboard,
    the stove and a cabinet or pegs; four hanging lamps over the desk blocks, a lit sconce on a facade pier and one on
    the long wall.
    wall_maps: (map beside the board, two maps of the long wall); side_wall: (name, d) of the east wall's cabinet."""
    desk_us = [west_face + DESK_ROW_FIRST + DESK_ROW_PITCH * row for row in range(DESK_ROWS)]
    board_map, long_maps = wall_maps[0], wall_maps[1:]
    long_wall_items = (  # (prop, distance from the board wall, options)
        ("wall_map", 1.45, dict(variant=long_maps[0])),
        ("wall_sconce", 2.60, dict(lit=False)),
        ("wall_clock", 3.55, {}),
        ("wall_crucifix", 4.55, {}),
        ("wall_sconce", 5.40, {}),
        ("wall_map", 6.65, dict(variant=long_maps[1])),
        ("wall_sconce", 8.00, dict(lit=False)),
    )

    f.on_face("u", west_face, 1, "wall_map", 1.15, variant=board_map)
    f.on_face("u", west_face, 1, "blackboard_big", 3.70)
    f.put("teacher_platform", west_face + 1.10, 3.70, 90.0)
    f.put("abacus_stand", west_face + 0.245, 5.70, 90.0)

    for desk_u, desk_d in itertools.product(desk_us, DESK_COLUMNS):
        f.put("double_desk", desk_u, desk_d, -90.0)

    for name, offset, options in long_wall_items:
        f.on_face("d", INNER_FACE, -1, name, west_face + offset, **options)

    f.on_face("u", east_face, -1, "specimen_cupboard", 1.40)
    f.on_face("u", east_face, -1, "cast_iron_stove", stove_d)
    f.on_face("u", east_face, -1, side_wall[0], side_wall[1])

    for lamp_u, lamp_d in itertools.product((west_face + 4.05, west_face + 6.85), (2.50, 5.40)):
        f.put("hanging_oil_lamp", lamp_u, lamp_d)

    for sconce_u in front_sconce_us:
        f.on_wall("front", "wall_sconce", sconce_u, lit=sconce_u == front_sconce_us[0])


def furnish_classroom_1(f) -> None:
    """Classroom 1 (u = 1.955..11.06): cupboard, stove and pegs on the rear wall by the door to the cloakroom."""
    west_face = CLASS_WALL + WALL_HALF
    east_face = CLOAKROOM_WALL - WALL_HALF

    furnish_classroom(f, west_face, east_face, ("world", "country", "botany"), 3.50, ("clothes_pegs", 4.30), (5.14, 8.17))


def furnish_classroom_2(f) -> None:
    """Classroom 2 (u = -8.02..1.655): cupboard, stove and filing cabinet on the rear wall by the door to classroom 1."""
    west_face = SCIENCE_WALL + WALL_HALF
    east_face = CLASS_WALL - WALL_HALF

    furnish_classroom(f, west_face, east_face, ("alphabet", "world", "country"), 2.90, ("filing_cabinet", 4.00), (-5.13, -1.805))


def furnish_science_cabinet(f) -> None:
    """Science cabinet (u = -14.55..-8.32, d = 0.3..8.05): glazed specimen cupboards on solid piers and the inner wall,
    skeleton, two lab benches with stools, globes, astrolabe, a chalk diagram and the planet mobile."""
    east_face = SCIENCE_WALL - WALL_HALF  # -8.32

    # Specimen cupboards clear of the front windows (-13.43..-12.03, -10.39..-8.99) and the left ones (2.70..4.10, 6.90..8.30)
    f.on_wall("front", "specimen_cupboard", -11.21)
    f.on_wall("left", "specimen_cupboard", 5.50)
    f.on_face("d", INNER_FACE, -1, "specimen_cupboard", -12.95)
    f.on_face("d", INNER_FACE, -1, "specimen_cupboard", -11.00)

    f.on_face("u", east_face, -1, "wall_map", 1.60, variant="botany")
    f.on_face("u", east_face, -1, "recipe_board", 3.60)
    f.on_face("u", east_face, -1, "skeleton_stand", 4.45)
    f.on_face("d", INNER_FACE, -1, "wall_crucifix", -9.90)
    f.on_face("d", INNER_FACE, -1, "wall_clock", -8.85, z=0.0)

    f.put("lab_bench", -11.20, 2.55, 0.0)
    f.put("lab_bench", -11.20, 5.25, 180.0)

    for stool_u in (-11.80, -10.60):
        f.put("stool_round", stool_u, 1.75)

    f.put("bentwood_chair", -11.20, 6.00, 0.0)

    f.put("celestial_globe", -13.60, 1.65)
    f.put("globe_stand", -9.15, 1.65)
    f.put("astrolabe", -9.15, 3.30)
    f.put("planet_mobile", -11.20, 3.90)

    f.put("hanging_oil_lamp", -11.20, 2.30)
    f.put("hanging_oil_lamp", -11.20, 5.50)
    f.on_face("d", INNER_FACE, -1, "wall_sconce", -11.975)
    f.on_face("u", east_face, -1, "wall_sconce", 2.65)
    f.on_wall("left", "wall_sconce", 4.45)
    f.on_wall("left", "wall_sconce", 1.60, lit=False)


def furnish_study_hall(f) -> None:
    """Study hall (u = -2.70..14.55, d = 8.35..19.1): two rows of three long study tables with 48 chairs between
    bookcases on both long walls, the supervisor's platform at the east end under a crucifix, a stove, clocks, maps."""
    west_face = STUDY_WALL + WALL_HALF  # -2.70

    f.put("teacher_platform", 13.65, 13.70, -90.0)
    f.on_wall("right", "wall_clock", 9.40)
    f.on_wall("right", "wall_map", 11.20, variant="world")
    f.on_wall("right", "wall_crucifix", 13.70)
    f.on_wall("right", "wall_map", 16.20, variant="country")
    f.hang_picture("u", f.right, -1, 17.95, "portrait")

    # Inner long wall d = 8.35: bookcases and the card catalogue; u = 10.59..13.65 stays free for the door and its leaf
    for case_u in (-0.80, 2.40, 6.80, 9.45):
        f.on_face("d", BACK_FACE, 1, "tall_bookcase", case_u)

    f.on_face("d", BACK_FACE, 1, "card_catalog", 4.60)

    # Back wall d = 19.1 (high windows at u = 3.81, 7.83, 11.84, sill 3.3): tall cases on the piers, shorter ones under the windows
    for case_u in (0.50, 5.80, 9.80):
        f.on_wall("back", "tall_bookcase", case_u)

    f.on_wall("back", "linen_press", 3.80)
    f.on_wall("back", "specimen_cupboard", 7.80)
    f.on_wall("back", "filing_cabinet", 12.20)
    f.on_wall("back", "cast_iron_stove", 13.60)

    f.on_face("u", west_face, 1, "long_case_clock", 11.40)
    f.hang_picture("u", west_face, 1, 16.50, "seascape")

    for (table_u, table_d), offset in itertools.product(itertools.product(STUDY_TABLE_US, STUDY_TABLE_DS), STUDY_CHAIR_OFFSETS):
        near_chair_d, far_chair_d = table_d - 0.85, table_d + 0.85

        f.put("bentwood_chair", table_u + offset, near_chair_d, 180.0)
        f.put("bentwood_chair", table_u + offset, far_chair_d, 0.0)

    for table_u, table_d in itertools.product(STUDY_TABLE_US, STUDY_TABLE_DS):
        f.put("study_table", table_u, table_d, 0.0, lit=(table_u, table_d) in STUDY_LIT_TABLES)

    for lamp_u in (0.70, 4.90, 9.10):
        f.put("hanging_oil_lamp", lamp_u, 13.70)

    for sconce_u, lit in ((-1.60, False), (2.25, False), (12.20, True), (14.05, False)):
        f.on_wall("back", "wall_sconce", sconce_u, lit=lit)

    for sconce_u, lit in ((0.80, False), (4.60, False), (8.125, True), (14.05, False)):
        f.on_face("d", BACK_FACE, 1, "wall_sconce", sconce_u, lit=lit)

    f.on_wall("right", "wall_sconce", 12.10, lit=False)
    f.on_wall("right", "wall_sconce", 15.25, lit=False)
    f.on_face("u", west_face, 1, "wall_sconce", 10.50, lit=False)
    f.on_face("u", west_face, 1, "wall_sconce", 17.60, lit=False)


def furnish_teachers_room(f) -> None:
    """Teachers' room (u = -9.25..-3.00, d = 8.35..19.1): hearth with two armchairs and a side table on the front wall,
    bookcases and a card catalogue on the west wall, the coat rack and bench on the east wall, a long meeting table
    with eight chairs in the back half, cabinets under the high windows, a clock over the door. The doors face each
    other at d = 13.7, so that stretch stays open."""
    west_face = DIRECTOR_WALL + WALL_HALF  # -9.25
    east_face = STUDY_WALL - WALL_HALF     # -3.00

    f.on_face("d", BACK_FACE, 1, "fireplace_tall", -6.125, height=5.0)
    f.on_face("d", BACK_FACE, 1, "long_case_clock", -8.45)
    f.on_face("d", BACK_FACE, 1, "filing_cabinet", -3.60)
    f.put("armchair", -7.55, 10.15, 30.0)
    f.put("armchair", -4.70, 10.15, -30.0)
    f.put("side_table", -6.125, 10.20)
    f.put("oil_lamp_table", -6.125, 10.20, z=0.67, lit=False)

    f.put("study_table", -6.125, 16.70, 0.0)

    for chair_u in (-7.125, -6.125, -5.125):
        f.put("bentwood_chair", chair_u, 15.85, 180.0)
        f.put("bentwood_chair", chair_u, 17.55, 0.0)

    f.put("bentwood_chair", -8.10, 16.70, 90.0)
    f.put("bentwood_chair", -4.15, 16.70, -90.0)

    f.on_wall("back", "filing_cabinet", -7.83)
    f.on_wall("back", "tall_bookcase", -5.82)
    f.on_wall("back", "specimen_cupboard", -3.90)

    f.on_face("u", east_face, -1, "coat_rack_wall", 9.95)
    f.on_face("u", east_face, -1, "bench_long", 9.95)
    f.on_face("u", east_face, -1, "wall_clock", TEACHERS_DOOR["at"], z=0.45)
    f.on_face("u", east_face, -1, "tall_bookcase_slim", 16.10)
    f.on_face("u", east_face, -1, "filing_cabinet", 17.65)

    f.on_face("u", west_face, 1, "card_catalog", 9.62)
    f.on_face("u", west_face, 1, "tall_bookcase", 11.40)
    f.on_face("u", west_face, 1, "tall_bookcase", 15.90)
    f.on_face("u", west_face, 1, "notice_board", 18.05)
    f.on_face("u", west_face, 1, "wall_crucifix", DIRECTOR_DOOR["at"], z=0.7)

    for lamp_d in (10.60, 16.70):
        f.put("hanging_oil_lamp", -6.125, lamp_d)

    f.on_face("u", east_face, -1, "wall_sconce", 11.60)
    f.on_face("u", east_face, -1, "wall_sconce", 14.90, lit=False)
    f.on_face("u", west_face, 1, "wall_sconce", 12.10, lit=False)


def furnish_headmaster_study(f) -> None:
    """Headmaster's study (u = -14.55..-9.55, d = 8.35..19.1): pedestal desk and two visitor chairs at the back, two
    tall bookcases and a clock on the front wall, a sofa, reading table and armchair in the front half, narrow
    curtains at the two windows, a bookcase, crucifix and clock on the east wall."""
    east_face = DIRECTOR_WALL - WALL_HALF  # -9.55

    f.put("director_desk", -12.05, 16.40, 0.0)
    f.put("study_chair", -12.55, 15.10, 180.0)
    f.put("study_chair", -11.55, 15.10, 180.0)

    # Back wall d = 19.1 (high window at u = -11.84, sill 3.3): low cabinets on both piers, a picture between
    f.on_wall("back", "filing_cabinet", -13.60)
    f.on_wall("back", "specimen_cupboard", -10.20)
    f.hang_picture("d", f.back, -1, -12.15, "landscape")

    f.on_face("d", BACK_FACE, 1, "tall_bookcase", -13.40)
    f.on_face("d", BACK_FACE, 1, "tall_bookcase", -11.40)
    f.on_face("d", BACK_FACE, 1, "long_case_clock", -10.00)

    f.on_wall("left", "sofa", 9.80)
    f.put("reading_table", -12.35, 10.90, 90.0)
    f.put("armchair", -11.00, 10.90, -90.0)
    f.put("globe_stand", -10.40, 9.30)
    f.put("side_table", -10.60, 12.30)

    # Exposed west wall: windows at d = 11.8 and 16.0 with a solid pier between
    f.on_wall("left", "curtain_pair", 11.80, width=1.7, height=3.2, variant="wine")
    f.on_wall("left", "long_case_clock", 13.90)
    f.on_wall("left", "curtain_pair", 16.00, width=1.7, height=3.2, variant="wine")

    f.hang_picture("u", east_face, -1, 10.90, "portrait")
    f.on_face("u", east_face, -1, "wall_clock", DIRECTOR_DOOR["at"], z=0.45)
    f.on_face("u", east_face, -1, "tall_bookcase_slim", 16.30)
    f.on_face("u", east_face, -1, "wall_crucifix", 18.30)

    f.put("hanging_oil_lamp", -12.05, 11.00)
    f.put("hanging_oil_lamp", -12.05, 14.30)
    f.on_wall("left", "wall_sconce", 13.10, lit=False)
    f.on_face("u", east_face, -1, "wall_sconce", 12.20)
    f.on_wall("back", "wall_sconce", -13.60)


def furnish_school(f) -> None:
    """Ground floor of the left wing (`school`): cloakroom passage, two classrooms, science cabinet, study hall,
    teachers' room and headmaster's study."""
    furnish_cloakroom(f)
    furnish_classroom_1(f)
    furnish_classroom_2(f)
    furnish_science_cabinet(f)
    furnish_study_hall(f)
    furnish_teachers_room(f)
    furnish_headmaster_study(f)


PLAN = dict(
    keeper=(12.20, 13.70),  # supervisor standing by the study hall dais, facing the entry
    posts=(),
    girder_pitch=2.4,
    partitions=(
        ("d", LONG_WALL, HALL_LEFT, SCIENCE_WALL, dict(faces=("science", "teachers"))),
        ("d", LONG_WALL, SCIENCE_WALL, STUDY_WALL, dict(faces=("classroom", "teachers"))),
        ("d", LONG_WALL, STUDY_WALL, HALL_RIGHT, dict(doors=[STUDY_DOOR], faces=("classroom", "classroom"))),
        ("u", CLOAKROOM_WALL, HALL_FRONT, LONG_WALL - WALL_HALF, dict(doors=[CLASS_1_DOOR], faces=("classroom", "classroom"))),
        ("u", CLASS_WALL, HALL_FRONT, LONG_WALL - WALL_HALF, dict(doors=[CLASS_2_DOOR], faces=("classroom", "classroom"))),
        ("u", SCIENCE_WALL, HALL_FRONT, LONG_WALL - WALL_HALF, dict(doors=[SCIENCE_DOOR], faces=("science", "classroom"))),
        ("u", STUDY_WALL, LONG_WALL + WALL_HALF, HALL_BACK, dict(doors=[TEACHERS_DOOR], faces=("teachers", "classroom"))),
        ("u", DIRECTOR_WALL, LONG_WALL + WALL_HALF, HALL_BACK, dict(doors=[DIRECTOR_DOOR], faces=("teachers", "teachers"))),
    ),
    finishes=(
        ("front", HALL_LEFT, SCIENCE_WALL - WALL_HALF, "science"),
        ("front", SCIENCE_WALL + WALL_HALF, HALL_RIGHT, "classroom"),
        ("left", HALL_FRONT, LONG_WALL - WALL_HALF, "science"),
        ("left", LONG_WALL + WALL_HALF, HALL_BACK, "teachers"),
        ("right", HALL_FRONT, LONG_WALL - WALL_HALF, "classroom"),
        ("right", LONG_WALL + WALL_HALF, HALL_BACK, "classroom"),
        ("back", HALL_LEFT, STUDY_WALL - WALL_HALF, "teachers"),
        ("back", STUDY_WALL + WALL_HALF, HALL_RIGHT, "classroom"),
    ),
    furnish=furnish_school,
)
