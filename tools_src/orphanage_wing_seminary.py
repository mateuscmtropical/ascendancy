"""Rooms of the chapel wing (upper floor, left wing of the orphanage: hall `seminary`).

Two bands split by the long wall at d = 8.2. Front band (d = 0.3..8.05): the sacristy at the entry end (u = +14.55, by
the gallery) and the chapel, with its altar on the exposed end wall (u = -14.55) between the two side windows. Back
band (d = 8.35..19.1): the seminary room at the entry end and the infirmary at the far end.
"""

WALL_HALF = 0.15  # half the thickness of an inner wall (WALL = 0.3 in build_market_shops.py)

HALL_LEFT = -14.55
HALL_RIGHT = 14.55
HALL_FRONT = 0.3
HALL_BACK = 19.1
LONG_WALL = 8.2  # d of the wall between the front and the back band
SACRISTY_WALL = 11.21  # u of the wall between the sacristy and the chapel (a pier of the facade)
INFIRMARY_WALL = 0.0  # u of the wall between the seminary room and the infirmary (clear of the back windows)

FRONT_FACE = LONG_WALL - WALL_HALF  # the long wall seen from the front band
BACK_FACE = LONG_WALL + WALL_HALF  # the long wall seen from the back band
CHAPEL_END = SACRISTY_WALL - WALL_HALF  # u of the chapel's face of the sacristy wall
ALTAR_D = 5.2  # d of the altar: the middle of the pier between the side windows (4.1 and 6.9)
NAVE_D = 4.8  # d of the centre aisle; the pews of both blocks have to fit between the facade and the long wall
PEW_LENGTH = 2.56
AISLE_HALF = 0.65
FIRST_PEW_U = -6.6
PEW_PITCH = 1.05
PEW_ROWS = 12
RAIL_U = -10.9  # communion rail
CHAPEL_PIERS = (-8.17, -5.13, -1.805, 1.805, 5.13, 8.17)  # u of the piers of the facade the chapel uses
BED_PITCH = 1.6  # cubicles of the seminary room
BLANKET_SEMINARY = "grey_blue"
BLANKET_INFIRMARY = "ochre"

CHAPEL_DOOR = dict(at=4.2, width=1.5, height=2.1, leaf=("low", -1), lane=("low",))  # sacristy -> chapel
SACRISTY_DOOR = dict(at=12.95, width=1.5, height=2.1, leaf=("high", -1))  # sacristy -> seminary room
INFIRMARY_DOOR = dict(at=13.7, width=1.5, height=2.1, leaf=("high", 1))  # seminary room -> infirmary

NEW_WALL_FINISHES = {
    "chapel": dict(dado="5E6F82", trim="4A2D1C"),  # slate-blue dado for the chapel and sacristy
    "seminary": dict(dado="6B442D", trim="4A2D1C"),  # dark wood tone for the seminary room
    "infirmary": dict(dado="D6AE6C", trim="5A3A26"),  # light ochre for the sick ward
}


def furnish_sacristy(f) -> None:
    """Sacristy (u = 11.36..14.55, d = 0.3..8.05): a vestment press and a holy water font on the chapel wall, a table
    by the gallery wall, a prie-dieu under the window, a censer on its chain, a crucifix."""
    face = CHAPEL_END + 2 * WALL_HALF

    f.on_face("u", face, 1, "holy_water_font", 5.45)
    f.on_face("u", face, 1, "linen_press", 6.6)
    f.on_wall("right", "nurse_table", 6.4)
    f.on_face("d", f.front, 1, "prie_dieu", 13.9)
    f.on_face("d", FRONT_FACE, -1, "wall_crucifix", 11.7)
    f.put("censer_hanging", 13.0, 6.0)
    f.put("hanging_oil_lamp", 13.0, 4.0)
    f.on_face("d", FRONT_FACE, -1, "wall_sconce", 14.1, lit=False)


def furnish_chapel(f) -> None:
    """Chapel (u = -14.55..11.06, d = 0.3..8.05): the altar and retable on the end wall between the two windows, a
    communion rail with a gate on the aisle, two side altars on the wall piers, the pulpit, twenty-four pews in two
    blocks either side of the centre aisle, the confessional and the harmonium by the door, the stations of the cross
    on the long wall and the piers, the sanctuary lamp."""
    f.on_wall("left", "retable_altar", ALTAR_D)
    f.put("sanctuary_lamp", HALL_LEFT + 1.4, ALTAR_D)

    for rail_d in (1.3, 3.3, 6.5):
        f.put("railing", RAIL_U, rail_d, 90.0)

    for stand_d in (NAVE_D - 1.25, NAVE_D + 1.25):
        f.put("candle_stand", RAIL_U + 0.5, stand_d)

    for wall_axis, wall_face, normal in (("d", f.front, 1), ("d", FRONT_FACE, -1)):
        f.on_face(wall_axis, wall_face, normal, "saint_niche", CHAPEL_PIERS[0])
        f.on_face(wall_axis, wall_face, normal, "prie_dieu", CHAPEL_PIERS[0])

        for stand_side in (-1, 1):
            f.on_face(wall_axis, wall_face, normal, "candle_stand", CHAPEL_PIERS[0] + stand_side * 0.75)

    f.on_face("d", FRONT_FACE, -1, "reading_pulpit", -10.0)
    f.on_face("d", FRONT_FACE, -1, "wall_crucifix", -12.5)

    block_ds = (NAVE_D - AISLE_HALF - PEW_LENGTH / 2.0, NAVE_D + AISLE_HALF + PEW_LENGTH / 2.0)

    for row in range(PEW_ROWS):
        for block_d in block_ds:
            f.put("pew", FIRST_PEW_U + row * PEW_PITCH, block_d, -90.0)

    f.on_face("d", FRONT_FACE, -1, "confessional", 7.6)
    f.on_face("d", FRONT_FACE, -1, "harmonium", 9.6)
    f.on_face("u", CHAPEL_END, -1, "prie_dieu", 6.6)
    f.on_face("u", CHAPEL_END, -1, "holy_water_font", 5.6)

    for station_u in (-6.0, -4.4, -2.8, -1.2, 0.4, 2.0, 3.6):
        f.hang_picture("d", FRONT_FACE, -1, station_u, "station")

    for pier_u in CHAPEL_PIERS[1:]:
        f.hang_picture("d", f.front, 1, pier_u, "station")

    for sconce_u, is_lit in ((-5.2, True), (-2.0, False), (1.2, False), (4.4, True)):
        f.on_face("d", FRONT_FACE, -1, "wall_sconce", sconce_u, lit=is_lit)

    for lamp_u in (-6.0, -1.5, 3.0):
        f.put("hanging_oil_lamp", lamp_u, NAVE_D)


def furnish_seminary_room(f) -> None:
    """Seminary room (u = 0.15..14.55, d = 8.35..19.1): a study side with a long table of three study tables, chairs
    both sides, a lectern at its head and bookcases along the long wall, the cross wall and the end wall; a sleeping side
    with eight curtained bed cubicles along the back wall."""
    cross_face = INFIRMARY_WALL + WALL_HALF
    table_d = 11.6

    for case_u in (1.4, 3.45, 5.5, 7.55, 9.6):
        f.on_face("d", BACK_FACE, 1, "tall_bookcase", case_u)

    f.on_face("u", cross_face, 1, "tall_bookcase", 10.0)
    f.on_face("u", cross_face, 1, "wall_crucifix", 17.0)

    for case_d in (10.9, 13.0, 15.1):
        f.on_wall("right", "tall_bookcase", case_d)

    for table_u in (3.5, 6.5, 9.5):
        f.put("study_table", table_u, table_d, lit=table_u != 6.5)

        for chair_offset in (-0.9, 0.0, 0.9):
            f.put("bentwood_chair", table_u + chair_offset, table_d - 0.85, 180.0)
            f.put("bentwood_chair", table_u + chair_offset, table_d + 0.85, 0.0)

    f.put("lectern", 1.3, table_d, 90.0)
    f.put("hanging_oil_lamp", 4.5, table_d + 2.0)
    f.put("hanging_oil_lamp", 8.5, table_d + 2.0)

    for cubicle in range(8):
        bed_u = 1.4 + BED_PITCH * cubicle

        f.on_face("d", f.back, -1, "iron_bed", bed_u, variant=BLANKET_SEMINARY)
        f.put("bed_trunk", bed_u, f.back - 2.255)

    for divider in range(9):
        f.put("cell_curtain", 0.6 + BED_PITCH * divider, f.back - 1.2, 90.0)

    f.on_wall("back", "wall_sconce", 2.2, lit=False)
    f.on_wall("back", "wall_sconce", 5.8, lit=False)
    f.on_wall("back", "wall_sconce", 9.8, lit=False)
    f.on_wall("back", "wall_sconce", 13.4, lit=False)


def furnish_infirmary(f) -> None:
    """Infirmary (u = -14.55..-0.15, d = 8.35..19.1): six iron beds with their heads to the long walls, a night table
    by each, folding screens between some, the medicine cabinet, the nurse's table and a washstand on the wall to the
    seminary room, a linen press, the stove on the end wall between the windows with two armchairs before it."""
    cross_face = INFIRMARY_WALL - WALL_HALF

    for bed_u in (-12.0, -8.0, -4.0):
        for wall_d, normal in ((BACK_FACE, 1), (f.back, -1)):
            f.on_face("d", wall_d, normal, "iron_bed", bed_u, variant=BLANKET_INFIRMARY)
            f.on_face("d", wall_d, normal, "night_table", bed_u + 0.75)
            f.on_face("d", wall_d, normal, "wall_sconce", bed_u + 0.75, lit=bed_u == -8.0)

    f.put("folding_screen", -10.0, BACK_FACE + 1.4, 90.0)
    f.put("folding_screen", -6.0, f.back - 1.4, 90.0)

    f.on_face("u", cross_face, -1, "medicine_cabinet", 10.2)
    f.on_face("u", cross_face, -1, "nurse_table", 17.2)
    f.on_face("u", cross_face, -1, "washstand", 18.5)
    f.on_face("d", BACK_FACE, 1, "linen_press", -1.8)

    f.on_wall("left", "fireplace", 13.9)
    f.put("armchair", HALL_LEFT + 1.8, 13.2, -90.0)
    f.put("armchair", HALL_LEFT + 1.8, 14.6, -90.0)
    f.on_wall("left", "curtain_pair", 11.8, width=1.8, height=3.4, variant="cream")
    f.on_wall("left", "curtain_pair", 16.0, width=1.8, height=3.4, variant="cream")

    f.on_face("d", BACK_FACE, 1, "wall_crucifix", -10.0)
    f.on_face("d", f.back, -1, "wall_crucifix", -10.0)

    f.put("reading_table", -7.0, 13.7)

    for chair_u in (-7.6, -6.4):
        f.put("bentwood_chair", chair_u, 13.7 - 0.85, 180.0)
        f.put("bentwood_chair", chair_u, 13.7 + 0.85, 0.0)

    f.on_wall("left", "clothes_pegs", 9.5)

    for lamp_u in (-10.0, -6.0, -2.5):
        f.put("hanging_oil_lamp", lamp_u, 13.7)


def furnish_seminary(f) -> None:
    """Upper floor of the left wing: the sacristy, the chapel, the seminary room and the infirmary."""
    furnish_sacristy(f)
    furnish_chapel(f)
    furnish_seminary_room(f)
    furnish_infirmary(f)


PLAN = dict(
    keeper=(7.0, 14.4),  # the prefect between the study table and the cubicles
    posts=(),
    girder_pitch=2.4,
    partitions=(
        ("u", SACRISTY_WALL, HALL_FRONT, FRONT_FACE, dict(doors=[CHAPEL_DOOR], faces=("chapel", "chapel"))),
        ("d", LONG_WALL, HALL_LEFT, INFIRMARY_WALL, dict(faces=("chapel", "infirmary"))),
        ("d", LONG_WALL, INFIRMARY_WALL, HALL_RIGHT, dict(doors=[SACRISTY_DOOR], faces=("chapel", "seminary"))),
        ("u", INFIRMARY_WALL, BACK_FACE, HALL_BACK, dict(doors=[INFIRMARY_DOOR], faces=("infirmary", "seminary"))),
    ),
    finishes=(
        ("front", HALL_LEFT, HALL_RIGHT, "chapel"),
        ("left", HALL_FRONT, FRONT_FACE, "chapel"),
        ("right", HALL_FRONT, FRONT_FACE, "chapel"),
        ("left", BACK_FACE, HALL_BACK, "infirmary"),
        ("right", BACK_FACE, HALL_BACK, "seminary"),
        ("back", HALL_LEFT, INFIRMARY_WALL - WALL_HALF, "infirmary"),
        ("back", INFIRMARY_WALL + WALL_HALF, HALL_RIGHT, "seminary"),
    ),
    furnish=furnish_seminary,
)
