"""Rooms of the school wing (ground floor, left wing of the orphanage: hall `school`).

Seven rooms arranged in two bands split by a long partition at d = 8.2:
  - Front band (d = 0.3..8.05): Cloakroom passage at the vestibule end, Classroom 1, Classroom 2, Science cabinet.
  - Back band (d = 8.35..19.1): Study hall at the vestibule end, Teachers' room, Headmaster's study.

All cross walls in the front band stand on facade piers so no window is cut; every room is reachable on foot from
the existing vestibule doorway on the right wall (u = 14.55, d = 3.0).
"""

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

CLASS_1_DOOR = dict(at=7.15, width=1.5, height=2.1, leaf=("low", -1))
CLASS_2_DOOR = dict(at=7.15, width=1.5, height=2.1, leaf=("low", -1))
SCIENCE_DOOR = dict(at=7.15, width=1.5, height=2.1, leaf=("low", -1))
STUDY_DOOR = dict(at=12.90, width=1.5, height=2.1, leaf=("high", -1))
TEACHERS_DOOR = dict(at=13.70, width=1.5, height=2.1, leaf=("low", 1))
DIRECTOR_DOOR = dict(at=13.70, width=1.5, height=2.1, leaf=("low", 1))

NEW_WALL_FINISHES = {
    "classroom": dict(dado="3D5060", trim="5A3A26"),  # dark blue-grey dado for classrooms, study hall, cloakroom
    "science": dict(dado="5A7082", trim="5A3A26"),    # cooler blue-grey dado for the science cabinet
    "teachers": dict(dado="6B442D", trim="4A2D1C"),   # dark wood panelling tone for teachers' room and study
}


def furnish_cloakroom(f) -> None:
    """Cloakroom passage (u = 11.36..14.55, d = 0.3..8.05): vestibule entry at d = 3.0, pegs, boot rack, benches,
    notice board, school bell, crucifix and hanging lamp."""
    west_face = CLOAKROOM_WALL + WALL_HALF  # 11.36

    # Under front window (u = 12.03..13.43, sill 0.9): bench_long is 1.8 x 0.4 x 0.5 (< 0.95 sill)
    f.on_wall("front", "bench_long", 12.73)
    f.put("plant_pot", 11.65, 1.25, variant="fern")  # u = 11.38..11.92, d = 1.00..1.50 (clear of 1.60 door lane)

    # Opposite vestibule doorway on u = 11.36 (leaves d = 6.20..8.05 clear for CLASS_1_DOOR)
    f.on_face("u", west_face, 1, "notice_board", 1.40)
    f.on_face("u", west_face, 1, "wall_crucifix", 3.00)
    f.on_face("u", west_face, 1, "clothes_pegs", 5.20)
    # boots_rack (1.24 x 0.4 x 0.96) at d = 5.20 -> d = 4.58..5.82, u = 11.36..11.76 (clear of 4.40 & 6.20 lanes)
    f.on_face("u", west_face, 1, "boots_rack", 5.20)

    # Right wall past vestibule door leaves (leaves fold back to d = 0.42..1.60 and 4.40..5.58)
    f.on_wall("right", "clothes_pegs", 6.70)
    # bench_long at d = 6.70 -> d = 5.80..7.60, u = 14.12..14.52 (clear of STUDY_DOOR lane u <= 13.85)
    f.on_wall("right", "bench_long", 6.70)

    f.put("hanging_oil_lamp", 13.00, 3.00, lit=True)
    f.put("school_bell", 12.95, 5.60)
    f.on_face("u", west_face, 1, "wall_sconce", 2.20, lit=False)
    f.on_face("u", west_face, 1, "wall_sconce", 6.10, lit=True)
    f.on_wall("right", "wall_sconce", 5.80, lit=False)


def furnish_classroom_1(f) -> None:
    """Classroom 1 (u = 1.955..11.06, d = 0.3..8.05): 14 double desks in 4 rows facing the blackboard and
    teacher's platform on the west wall, abacus, specimen cupboard, wall maps, crucifix and 4 hanging lamps."""
    west_face = CLASS_WALL + WALL_HALF       # 1.955
    east_face = CLOAKROOM_WALL - WALL_HALF   # 11.06
    inner_face = LONG_WALL - WALL_HALF       # 8.05

    # Teaching wall (u = 1.955, solid from d = 0.3..6.40; door at d = 6.40..7.90)
    f.on_face("u", west_face, 1, "wall_map", 1.15, variant="world")
    f.on_face("u", west_face, 1, "blackboard_big", 3.70)
    f.put("teacher_platform", 3.05, 3.70, 90.0)   # u = 2.15..3.95, d = 2.40..5.00
    f.put("abacus_stand", 2.20, 5.70, 90.0)       # u = 1.975..2.425, d = 5.375..6.325

    # Pupil desks (1.15 x 0.90, -90 deg faces -u toward board):
    # u rows: pitch 1.30 m, first 5.50 (5.05..5.95, 1.10 m from platform), last 9.40 (8.95..9.85, 1.21 m to 11.06)
    # d cols: front pair 1.275 (0.70..1.85), 2.475 (1.90..3.05); 1.20 m aisle 3.05..4.25;
    #         back pair 4.825 (4.25..5.40), 6.025 (5.45..6.60), leaving 1.45 m door corridor d = 6.60..8.05
    desk_us = (5.50, 6.80, 8.10, 9.40)
    desk_ds = (1.275, 2.475, 4.825, 6.025)
    for row_index, desk_u in enumerate(desk_us):
        cols = (2.475, 4.825) if row_index == 3 else desk_ds  # keep rear corners open for door & cupboard
        for desk_d in cols:
            f.put("double_desk", desk_u, desk_d, -90.0)

    # Rear wall u = 11.06 (clear of door leaf d = 4.84..6.30 and door d = 6.40..7.90)
    f.on_face("u", east_face, -1, "specimen_cupboard", 1.40)  # d = 0.75..2.05, u = 10.56..11.06
    f.on_face("u", east_face, -1, "clothes_pegs", 3.40)

    # Inner long wall d = 8.05 (maps, crucifix, sconces)
    f.on_face("d", inner_face, -1, "wall_map", 4.50, variant="country")
    f.on_face("d", inner_face, -1, "wall_crucifix", 6.50)
    f.on_face("d", inner_face, -1, "wall_map", 8.50, variant="botany")

    # Lighting: 4 hanging lamps over the two desk blocks (all lit) + 6 sconces (unlit to stay within wing budget)
    for lamp_u in (6.00, 8.80):
        for lamp_d in (2.50, 5.40):
            f.put("hanging_oil_lamp", lamp_u, lamp_d, lit=True)

    f.on_wall("front", "wall_sconce", 5.14, lit=False)
    f.on_wall("front", "wall_sconce", 8.17, lit=False)
    for sconce_u in (3.10, 5.75, 7.25, 9.90):
        f.on_face("d", inner_face, -1, "wall_sconce", sconce_u, lit=False)


def furnish_classroom_2(f) -> None:
    """Classroom 2 (u = -8.02..1.655, d = 0.3..8.05): 16 double desks in 4 rows facing the blackboard and
    teacher's platform on the west wall, abacus, cupboards, wall maps, crucifix and 4 hanging lamps."""
    west_face = SCIENCE_WALL + WALL_HALF   # -8.02
    east_face = CLASS_WALL - WALL_HALF     # 1.655
    inner_face = LONG_WALL - WALL_HALF     # 8.05

    # Teaching wall (u = -8.02, solid from d = 0.3..6.40; door at d = 6.40..7.90)
    f.on_face("u", west_face, 1, "wall_map", 1.15, variant="alphabet")
    f.on_face("u", west_face, 1, "blackboard_big", 3.70)
    f.put("teacher_platform", -6.92, 3.70, 90.0)  # u = -7.82..-6.02, d = 2.40..5.00
    f.put("abacus_stand", -7.75, 5.70, 90.0)      # u = -7.975..-7.525, d = 5.375..6.325

    # Pupil desks (4 x 4 = 16 double desks, pitch 1.30 m):
    # u rows: -4.45 (-4.90..-4.00, 1.12 m from platform), -3.15, -1.85, -0.55 (-1.00..-0.10, 1.755 m to 1.655)
    # d cols: 1.275, 2.475, 4.825, 6.025 (1.20 m centre aisle 3.05..4.25; 1.45 m door aisle 6.60..8.05)
    for desk_u in (-4.45, -3.15, -1.85, -0.55):
        for desk_d in (1.275, 2.475, 4.825, 6.025):
            f.put("double_desk", desk_u, desk_d, -90.0)

    # Rear wall u = 1.655 (d = 0.3..4.7, clear of door leaf d = 4.84..6.30)
    f.on_face("u", east_face, -1, "specimen_cupboard", 1.40)  # d = 0.75..2.05, u = 1.155..1.655
    f.on_face("u", east_face, -1, "filing_cabinet", 3.20)     # d = 2.65..3.75, u = 1.155..1.655

    # Inner long wall d = 8.05
    f.on_face("d", inner_face, -1, "wall_map", -5.20, variant="world")
    f.on_face("d", inner_face, -1, "wall_crucifix", -3.20)
    f.on_face("d", inner_face, -1, "wall_map", -1.20, variant="country")

    for lamp_u in (-3.80, -1.00):
        for lamp_d in (2.50, 5.40):
            f.put("hanging_oil_lamp", lamp_u, lamp_d, lit=True)

    f.on_wall("front", "wall_sconce", -5.13, lit=False)
    f.on_wall("front", "wall_sconce", -1.805, lit=False)
    for sconce_u in (-6.70, -3.95, -2.45, 0.30):
        f.on_face("d", inner_face, -1, "wall_sconce", sconce_u, lit=False)


def furnish_science_cabinet(f) -> None:
    """Science cabinet (u = -14.55..-8.32, d = 0.3..8.05): glazed specimen cupboards on solid piers and inner wall,
    skeleton stand, student and demonstration lab benches, globes, astrolabe, chalk diagram and planet mobile."""
    east_face = SCIENCE_WALL - WALL_HALF  # -8.32
    inner_face = LONG_WALL - WALL_HALF    # 8.05

    # Specimen cupboards clear of front windows (-13.43..-12.03, -10.39..-8.99) and left windows (2.70..4.10, 6.90..8.30)
    f.on_wall("front", "specimen_cupboard", -11.21)               # pier -12.03..-10.39, d = 0.33..0.83
    f.on_wall("left", "specimen_cupboard", 5.50)                  # pier d = 4.10..6.90, u = -14.52..-14.02
    f.on_face("d", inner_face, -1, "specimen_cupboard", -12.95)   # u = -13.60..-12.30 (> -13.75 left window zone)
    f.on_face("d", inner_face, -1, "specimen_cupboard", -11.00)   # u = -11.65..-10.35 (0.65 m sconce gap between)

    # East cross wall u = -8.32 (d = 0.3..4.7, clear of door leaf 4.84..6.30 and door 6.40..7.90)
    f.on_face("u", east_face, -1, "wall_map", 1.60, variant="botany")
    f.on_face("u", east_face, -1, "recipe_board", 3.60)
    f.on_face("u", east_face, -1, "skeleton_stand", 4.45)         # d = 4.21..4.69, u = -8.88..-8.32
    f.on_face("d", inner_face, -1, "wall_crucifix", -9.90)

    # Lab benches in the middle: student bench at d = 2.55 (2.09..3.01), demo bench at d = 5.25 (4.79..5.71)
    f.put("lab_bench", -11.20, 2.55, 0.0)
    f.put("stool_round", -11.80, 1.75)
    f.put("stool_round", -10.60, 1.75)
    f.put("lab_bench", -11.20, 5.25, 180.0)
    f.put("bentwood_chair", -11.20, 6.00, 0.0)

    # Scientific instruments clear of left/front window zones and bench aisles
    f.put("celestial_globe", -13.60, 1.65)  # u = -14.065..-13.135, d = 1.195..2.105 (below d = 2.70 window)
    f.put("globe_stand", -9.15, 1.65)       # u = -9.555..-8.745, d = 1.245..2.055
    f.put("astrolabe", -9.15, 3.30)         # u = -9.45..-8.85, d = 3.04..3.56

    f.put("planet_mobile", -11.20, 3.90)
    f.put("hanging_oil_lamp", -11.20, 2.30, lit=True)
    f.put("hanging_oil_lamp", -11.20, 5.50, lit=True)
    f.on_face("d", inner_face, -1, "wall_sconce", -11.975, lit=True)
    f.on_face("u", east_face, -1, "wall_sconce", 2.65, lit=False)
    f.on_wall("left", "wall_sconce", 4.45, lit=False)


def furnish_study_hall(f) -> None:
    """Study hall (u = -2.70..14.55, d = 8.35..19.1): two parallel rows of 3 long study tables with 48 chairs,
    bookcases and cupboards along both long walls, supervisor's platform at the east end, clock and crucifix."""
    west_face = STUDY_WALL + WALL_HALF  # -2.70
    inner_face = LONG_WALL + WALL_HALF  # 8.35

    # Supervisor's raised desk at the east end facing west down the 2.42 m central aisle
    f.put("teacher_platform", 13.65, 13.70, -90.0)  # u = 12.75..14.55, d = 12.40..15.00
    f.on_wall("right", "wall_map", 11.20, variant="world")
    f.on_wall("right", "wall_crucifix", 13.70)
    f.on_wall("right", "wall_map", 16.20, variant="country")
    f.hang_picture("u", f.right, -1, 9.50, "landscape")
    f.hang_picture("u", f.right, -1, 17.75, "portrait")

    # Inner long wall d = 8.35 (bookcases + card catalog; u = 10.59..13.65 left free for STUDY_DOOR & leaf)
    for case_u in (-0.80, 2.40, 6.80, 9.45):
        f.on_face("d", inner_face, 1, "tall_bookcase", case_u)
    f.on_face("d", inner_face, 1, "card_catalog", 4.60)  # u = 3.88..5.32, d = 8.35..8.97, height 1.40

    # Back wall d = 19.1 (high windows at u = 3.81, 7.83, 11.84, sill 3.3 m):
    # tall_bookcase (4.0 m) only on piers; shorter storage (< 3.35 m) under windows
    for case_u in (0.50, 5.80, 9.80):
        f.on_wall("back", "tall_bookcase", case_u)
    f.on_wall("back", "linen_press", 3.80)
    f.on_wall("back", "specimen_cupboard", 7.80)
    f.on_wall("back", "filing_cabinet", 12.20)

    # West cross wall u = -2.70 (TEACHERS_DOOR at d = 12.95..14.45)
    f.on_face("u", west_face, 1, "long_case_clock", 11.40)
    f.hang_picture("u", west_face, 1, 16.50, "seascape")

    # Two rows of 3 study_tables (3.0 x 1.0):
    # u centres: 0.70 (-0.80..2.20), 4.90 (3.40..6.40), 9.10 (7.60..10.60); pitch 4.20 m (1.20 m cross-gaps)
    # d centres: 11.40 and 16.00; 4 chairs per side (offsets -1.00, -0.35, 0.35, 1.00) = 48 seats
    table_us = (0.70, 4.90, 9.10)
    chair_offsets = (-1.00, -0.35, 0.35, 1.00)
    for row_index, table_u in enumerate(table_us):
        f.put("study_table", table_u, 11.40, 0.0, lit=(row_index == 0))
        f.put("study_table", table_u, 16.00, 0.0, lit=(row_index == 1))
        for offset in chair_offsets:
            f.put("bentwood_chair", table_u + offset, 10.55, 180.0)
            f.put("bentwood_chair", table_u + offset, 12.25, 0.0)
            f.put("bentwood_chair", table_u + offset, 15.15, 180.0)
            f.put("bentwood_chair", table_u + offset, 16.85, 0.0)

    # Central aisle lamps (d = 13.70) and perimeter sconces (clear of tall bookcases and pictures)
    for lamp_u, is_lit in ((0.70, True), (4.90, True), (9.10, True), (12.20, False)):
        f.put("hanging_oil_lamp", lamp_u, 13.70, lit=is_lit)

    for sconce_u in (-1.60, 2.25, 12.20, 13.70):
        f.on_wall("back", "wall_sconce", sconce_u, lit=False)
    for sconce_u in (0.80, 4.60, 8.125, 14.05):
        f.on_face("d", inner_face, 1, "wall_sconce", sconce_u, lit=False)
    f.on_wall("right", "wall_sconce", 12.10, lit=False)
    f.on_wall("right", "wall_sconce", 15.25, lit=False)
    f.on_face("u", west_face, 1, "wall_sconce", 10.50, lit=False)
    f.on_face("u", west_face, 1, "wall_sconce", 17.60, lit=False)


def furnish_teachers_room(f) -> None:
    """Teachers' room (u = -9.25..-3.00, d = 8.35..19.1): hearth with fireside armchairs on the inner wall,
    long meeting table with 8 chairs in the back half, bookcase, cabinets, clock and coat rack."""
    west_face = DIRECTOR_WALL + WALL_HALF  # -9.25
    east_face = STUDY_WALL - WALL_HALF     # -3.00
    inner_face = LONG_WALL + WALL_HALF     # 8.35

    # Fireside lounge against d = 8.35
    f.on_face("d", inner_face, 1, "fireplace_tall", -6.125, height=5.0, lit=True)
    f.put("rug_ornate", -6.125, 10.60, variant="red")
    f.put("armchair", -7.65, 10.45, 45.0)
    f.put("armchair", -4.60, 10.45, -45.0)
    f.put("plant_pot", -8.70, 8.80, variant="fern")
    f.put("plant_pot", -3.55, 8.80, variant="bush")

    # Faculty meeting table (study_table 3.0 x 1.0) + 8 chairs in back half (d = 16.25, clear of door corridor)
    f.put("rug_ornate", -6.125, 16.25, variant="green")
    f.put("study_table", -6.125, 16.25, 0.0, lit=True)
    for chair_u in (-7.125, -6.125, -5.125):
        f.put("bentwood_chair", chair_u, 15.40, 180.0)
        f.put("bentwood_chair", chair_u, 17.10, 0.0)
    f.put("bentwood_chair", -7.95, 16.25, 90.0)
    f.put("bentwood_chair", -4.30, 16.25, -90.0)

    # Back wall d = 19.1 (tall_bookcase on pier -5.82; shorter cabinets under high windows -7.83 and -3.81)
    f.on_wall("back", "filing_cabinet", -7.83)
    f.on_wall("back", "tall_bookcase", -5.82)
    f.on_wall("back", "specimen_cupboard", -3.90)

    # Side walls (east u = -3.00 south of door; west u = -9.25)
    f.on_face("u", east_face, -1, "coat_rack_wall", 9.95)
    f.on_face("u", east_face, -1, "bench_long", 9.95)
    f.on_face("u", east_face, -1, "long_case_clock", 12.15)
    f.on_face("u", east_face, -1, "wall_crucifix", 17.50)

    f.on_face("u", west_face, 1, "card_catalog", 10.60)
    f.hang_picture("u", west_face, 1, 16.00, "portrait")
    f.on_face("u", west_face, 1, "notice_board", 17.60)

    f.put("hanging_oil_lamp", -6.125, 13.70, lit=True)
    f.put("hanging_oil_lamp", -6.125, 16.25, lit=False)
    f.on_face("u", east_face, -1, "wall_sconce", 11.40, lit=False)
    f.on_face("u", west_face, 1, "wall_sconce", 12.10, lit=False)
    f.on_face("u", west_face, 1, "wall_sconce", 15.10, lit=False)


def furnish_headmaster_study(f) -> None:
    """Headmaster's study (u = -14.55..-9.55, d = 8.35..19.1): director's pedestal desk, visitor chairs,
    filing cabinets, linen press, tall bookcases, reading table with sofa and armchair, globe and curtains."""
    east_face = DIRECTOR_WALL - WALL_HALF  # -9.55
    inner_face = LONG_WALL + WALL_HALF     # 8.35

    # Director's desk zone at the back (d = 16.40: 1.30 m behind chair to 18.50 back cabinets)
    f.put("rug_ornate", -12.05, 16.40, variant="plum")
    f.put("director_desk", -12.05, 16.40, 0.0, lit=True)
    f.put("study_chair", -12.55, 15.10, 180.0)
    f.put("study_chair", -11.55, 15.10, 180.0)

    # Back wall d = 19.1 (all < 3.35 m under high window u = -11.84; centre kept clear for landscape)
    f.on_wall("back", "filing_cabinet", -13.60)
    f.on_wall("back", "linen_press", -10.45)
    f.hang_picture("d", f.back, -1, -12.15, "landscape")
    f.put("plant_pot", -9.95, 17.50, variant="fern")

    # Inner wall d = 8.35 (no windows) and waiting/reading corner (d = 9.0..12.2)
    f.on_face("d", inner_face, 1, "tall_bookcase", -13.30)
    f.on_face("d", inner_face, 1, "tall_bookcase", -10.90)
    f.put("rug_ornate", -12.05, 10.80, variant="blue")
    f.on_wall("left", "sofa", 10.00)                    # pier d = 8.35..11.1, height 0.90 (< 0.95)
    f.put("reading_table", -12.35, 10.90, 90.0)         # u = -12.85..-11.85, d = 9.90..11.90
    f.put("armchair", -11.00, 10.90, -90.0)
    f.put("globe_stand", -10.10, 9.50)

    # Exposed left wall (windows at d = 11.8 and 16.0; solid pier d = 12.5..15.3)
    f.on_wall("left", "curtain_pair", 11.80, width=1.8, height=4.1, variant="wine")
    f.on_wall("left", "long_case_clock", 13.90)
    f.on_wall("left", "curtain_pair", 16.00, width=1.8, height=4.1, variant="wine")

    # East partition wall u = -9.55 (door leaf at d = 14.55..16.01)
    f.hang_picture("u", east_face, -1, 10.90, "portrait")
    f.on_face("u", east_face, -1, "wall_crucifix", 17.50)

    f.put("hanging_oil_lamp", -12.05, 11.00, lit=True)
    f.put("hanging_oil_lamp", -12.05, 14.30, lit=True)
    f.on_wall("left", "wall_sconce", 13.10, lit=False)
    f.on_face("u", east_face, -1, "wall_sconce", 12.20, lit=False)
    f.on_face("u", east_face, -1, "wall_sconce", 16.60, lit=False)
    f.on_wall("back", "wall_sconce", -13.60, lit=False)


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
