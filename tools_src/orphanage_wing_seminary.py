"""Rooms of the sisters' wing (hall `seminary`, upper floor over the school wing; the entry end u = 14.55 opens on the
gallery of the vestibule, the exposed end wall u = -14.55 has the side windows).

The corridor (orphanage_wing_common.py) runs from the gallery to the end window. Front band, behind the balcony
windows of the facade:
  - Cell dormitory (u -14.55..4.99): thirteen timber cells for the sisters and the novices, six on the facade (each
    with its own window) and seven on the corridor wall, a 3 m aisle between them. In every cell a bed, a chest at
    its foot, a washstand, a kneeler and a crucifix.
  - Sisters' washroom (u 5.29..8.03): trough, two latrine stalls, a tub behind a screen.
  - Community room (u 8.33..14.55): the long work table with its chairs, the mother's chair, bookcases, the
    spinning wheel and the mending baskets.
Back band, under the high windows:
  - Infirmary (u -14.55..-6.55): seven beds with lockers on the corridor wall and the back wall, the medicine
    cabinet between the end windows, the nurse's table, screens.
  - Sacristy (u -6.25..-0.65, d 13.75..18.80) and the isolation room behind it (d 19.10..24.10, two beds).
  - Chapel (u -0.35..14.55): nine rows of pews in two blocks with a middle aisle for the 72 children, the altar on the gallery
    wall, the sisters' stalls either side of the sanctuary, the communion rail, harmonium, confessional.
"""

import itertools
import math

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
    bed_row,
    corridor_walls,
    cross_wall,
    door,
    spaced,
)

WASH_WALL = 5.1375  # u of the wall between the cell dormitory and the sisters' washroom (a facade pier)
COMMUNITY_WALL = 8.175  # u of the wall between the washroom and the community room (a facade pier)
INFIRMARY_WALL = -6.4  # u of the wall between the infirmary and the sacristy (a back pier)
CHAPEL_WALL = -0.5  # u of the wall between the sacristy and the chapel (a back pier)
SACRISTY_WALL = 18.95  # d of the wall between the sacristy and the isolation room

FRONT_FACE = FRONT_BAND[1]  # the corridor wall seen from the front rooms
BACK_FACE = BACK_BAND[0]  # the corridor wall seen from the back rooms
CORRIDOR_STATION_US = (2.6, 4.2, 5.8, 7.4, 9.0, 10.6, 12.2)  # stations of the cross over the pews and stalls
BACK_STATION_US = (2.6, 4.4, 7.4, 8.8, 10.2, 11.6, 13.0)  # clear of the saint's niche at u 6.0
CELLS_EAST = WASH_WALL - WALL_HALF
WASH_WEST = WASH_WALL + WALL_HALF
WASH_EAST = COMMUNITY_WALL - WALL_HALF
COMMUNITY_WEST = COMMUNITY_WALL + WALL_HALF
INFIRMARY_EAST = INFIRMARY_WALL - WALL_HALF
SACRISTY_WEST = INFIRMARY_WALL + WALL_HALF
SACRISTY_EAST = CHAPEL_WALL - WALL_HALF
CHAPEL_WEST = CHAPEL_WALL + WALL_HALF

CELLS_DOOR = door(-14.0)  # the corner by the end windows stays free as the entry of the dormitory
WASH_DOOR = door(6.6)
COMMUNITY_DOOR = door(9.4)
INFIRMARY_DOOR = door(-14.0)
SACRISTY_DOOR = door(-3.5)
CHAPEL_DOOR = door(0.8, WIDE_DOOR)
VESTRY_DOOR = door(16.3)  # sacristy -> chapel
ISOLATION_DOOR = door(20.4)  # infirmary -> isolation room

NEW_WALL_FINISHES = {
    "corridor": CORRIDOR_FINISH,
    "cells": dict(dado="B8A27A", trim="5A3A26"),
    "community": dict(dado="7A5A6E", trim="4A2F20"),
    "infirmary": dict(dado="D8D4C4", trim="6E7F8C"),
    "chapel": dict(dado="6E2D38", trim="C89B45"),
    "sacristy": dict(dado="5A3A26", trim="2A2118"),
}

FACADE_WINDOW_US = (-12.731, -9.694, -6.656, -3.619, 0.0, 3.619)  # one cell on each balcony window
CELL_DEPTH = 3.6
WIDE_CELL, NARROW_CELL = 3.0, 2.4
CORRIDOR_CELL_US = spaced(-12.0, NARROW_CELL + 0.02, 7)
FIRST_CELL_SHIFT = 0.35  # the cell on the first window stands off the end wall, clear of its window
PEW_ROW_US = spaced(1.7, 0.95, 9)  # the sitters face +u, toward the altar
PEW_BLOCK_DS = (17.0, 20.85)  # one pew either side of the 1.3 m middle aisle
RAIL_U = 10.9  # the communion rail, 1.2 m in front of the first pews
STALL_US = (10.06, 12.66)  # the sisters' stalls along both side walls, facing each other
CHAPEL_AXIS = sum(BACK_BAND) / 2.0
INFIRMARY_CORRIDOR_BEDS = spaced(-12.6, 1.85, 3)
INFIRMARY_BACK_BEDS = spaced(-13.3, 1.85, 4)


def local(origin: tuple, degrees: float, x: float, y: float) -> tuple:
    """(u, d) of a point given in a prop's own frame (x across, y toward its back) placed at origin turned degrees."""
    cos_turn, sin_turn = math.cos(math.radians(degrees)), math.sin(math.radians(degrees))

    return (origin[0] + x * cos_turn - y * sin_turn, origin[1] + x * sin_turn + y * cos_turn)


def cell(f, u: float, wall_d: float, normal: int, width: float, blanket: str) -> None:
    """One sister's cell with its back to the wall face at wall_d (normal +1: the cell lies toward larger d): the
    bed along the side away from the curtained door, its chest at the foot, the washstand and the kneeler under the
    crucifix on the other side."""
    turn = 180.0 if normal > 0 else 0.0
    origin = (u, wall_d + normal * CELL_DEPTH / 2.0)
    half = width / 2.0
    items = (
        ("iron_bed", width / 2.0 - 0.52, 0.78, 0.0, dict(variant=blanket)),
        ("bed_trunk", half - 0.52, -0.5, 0.0, {}),
        ("washstand", -half + 0.48, 1.52, 0.0, {}),
        ("prie_dieu", -half + 0.4, 0.55, 0.0, {}),
        ("wall_crucifix", -half + 0.4, 1.74, 0.0, {}),
    )

    f.put("nun_cell" if width == WIDE_CELL else "nun_cell_narrow", *origin, turn)

    for name, x, y, extra_turn, options in items:
        f.put(name, *local(origin, turn, x, y), turn + extra_turn, **options)


def furnish_cells(f) -> None:
    """Cell dormitory (u -14.55..4.99, d 0.30..10.65): six cells on the facade windows, seven on the corridor wall,
    lamps down the aisle, a holy water font by the door."""
    for window_u in FACADE_WINDOW_US:
        narrow = window_u > 2.0 or window_u < -12.0
        cell(f, window_u + FIRST_CELL_SHIFT * (window_u < -12.0), f.front, 1, NARROW_CELL if narrow else WIDE_CELL, "grey_blue")

    for cell_u in CORRIDOR_CELL_US:
        cell(f, cell_u, FRONT_FACE, -1, NARROW_CELL, "grey_blue")

    for lamp_u in (-10.0, -4.0, 2.0):
        f.put("hanging_oil_lamp", lamp_u, 5.5)

    f.on_wall("left", "holy_water_font", 9.0)
    f.on_face("u", CELLS_EAST, -1, "wall_crucifix", 5.5)


def furnish_washroom(f) -> None:
    """Sisters' washroom (u 5.29..8.03, d 0.30..10.65): trough on the community room wall, two latrine stalls, a tub
    behind a screen, towel rack."""
    f.on_face("u", WASH_EAST, -1, "washroom_trough", 7.6)

    for stall_d in (3.0, 4.0):
        f.on_face("u", WASH_EAST, -1, "latrine_stall", stall_d)

    f.on_face("u", WASH_WEST, 1, "tin_bathtub", 5.0)
    f.put("folding_screen", 6.35, 5.0, 90.0)
    f.on_face("u", WASH_WEST, 1, "towel_rack", 7.9)
    f.put("hanging_oil_lamp", 6.65, 6.5)


def furnish_community(f) -> None:
    """Community room (u 8.33..14.55, d 0.30..10.65): the long work table with eight chairs, the mother's armchair
    at its head, bookcases on the washroom wall, spinning wheel and baskets by the end wall, a crucifix."""
    for table_d in (3.6, 6.9):
        f.put("reading_table", 11.4, table_d, 90.0)

        for side, seat_d in itertools.product((-1, 1), (table_d - 0.5, table_d + 0.5)):
            f.put("bentwood_chair", 11.4 + side * 0.76, seat_d, -90.0 * side)

    f.put("armchair", 11.4, 9.0, 180.0)

    for case_d in (2.2, 4.3):
        f.on_face("u", COMMUNITY_WEST, 1, "floor_shelf", case_d, variant="books")

    f.on_wall("right", "spinning_wheel", 5.6)
    f.on_wall("right", "wall_crucifix", 5.6)
    f.put("yarn_basket", 13.9, 1.2)
    f.put("wicker_basket", 13.9, 9.8, variant="wool")
    f.hang_picture("d", FRONT_FACE, -1, 12.0, "portrait")

    for lamp_d in (3.6, 6.9):
        f.put("hanging_oil_lamp", 11.4, lamp_d)


def furnish_infirmary(f) -> None:
    """Infirmary (u -14.55..-6.55, d 13.75..24.10): three beds on the corridor wall and four on the back wall with a
    locker by every head, the medicine cabinet between the end windows, the nurse's table in the middle, screens."""
    bed_row(f, "iron_bed", INFIRMARY_CORRIDOR_BEDS, BACK_FACE, 1, variant="green")
    bed_row(f, "iron_bed", INFIRMARY_BACK_BEDS, HALL_BACK, -1, variant="green")

    f.on_wall("left", "medicine_cabinet", 18.74)
    f.on_wall("left", "washstand", 22.8)
    f.put("nurse_table", -10.4, 18.9)
    f.put("bentwood_chair", -10.4, 19.55, 180.0)
    f.put("folding_screen", -12.4, 17.2)
    f.on_face("u", INFIRMARY_EAST, -1, "wall_crucifix", 18.9)

    for lamp_u in (-12.0, -8.4):
        f.put("hanging_oil_lamp", lamp_u, 18.9)


def furnish_sacristy(f) -> None:
    """Sacristy (u -6.25..-0.65, d 13.75..18.80): vestment press and linen press, a vesting table, the lavabo, a
    crucifix; isolation room (d 19.10..24.10): two beds behind a screen, a washstand and a chair."""
    f.on_face("d", SACRISTY_WALL - WALL_HALF, -1, "wardrobe", -5.0)
    f.on_face("d", SACRISTY_WALL - WALL_HALF, -1, "linen_press", -2.6)
    f.put("side_table", -3.4, 16.0)
    f.on_face("u", SACRISTY_WEST, 1, "washstand", 15.0)
    f.on_face("u", SACRISTY_WEST, 1, "wall_crucifix", 16.6)
    f.put("hanging_oil_lamp", -3.4, 16.2)

    for bed_u in (-4.8, -2.1):
        f.on_wall("back", "iron_bed", bed_u, variant="dull_red")

    f.put("folding_screen", -3.45, 22.3, 90.0)
    f.on_face("u", SACRISTY_EAST, -1, "washstand", 20.0)
    f.put("bentwood_chair", -1.4, 20.6, -90.0)
    f.put("hanging_oil_lamp", -3.4, 21.6, lit=False)


def furnish_chapel(f) -> None:
    """Chapel (u -0.35..14.55, d 13.75..24.10): nine rows of pews either side of the middle aisle, the altar against
    the gallery wall with candlesticks and the sanctuary lamp, the sisters' stalls along the sanctuary, the
    communion rail, harmonium, confessional, holy water font at the door, saints in niches, the stations of the cross."""
    for row_u, block_d in itertools.product(PEW_ROW_US, PEW_BLOCK_DS):
        f.put("pew", row_u, block_d, 90.0)

    f.on_wall("right", "chancel_altar", CHAPEL_AXIS)

    for side in (-1, 1):
        f.put("candle_stand", 13.6, CHAPEL_AXIS + side * 2.2)
        f.put("railing", RAIL_U, CHAPEL_AXIS + side * 1.9, 90.0)

    for stall_u in STALL_US:
        f.on_face("d", BACK_FACE, 1, "pew", stall_u)
        f.on_wall("back", "pew", stall_u)

    f.put("sanctuary_lamp", 12.4, CHAPEL_AXIS + 1.2)
    f.on_wall("back", "harmonium", 3.4)
    f.on_wall("back", "confessional", 1.4)
    f.on_wall("back", "saint_niche", 6.0)
    f.on_face("d", BACK_FACE, 1, "holy_water_font", 2.2)

    for lamp_u in (3.5, 7.0):
        f.put("wheel_chandelier", lamp_u, CHAPEL_AXIS)

    for station_u in CORRIDOR_STATION_US:  # the fourteen stations of the cross, seven on each side wall
        f.hang_picture("d", BACK_FACE, 1, station_u, "station")

    for station_u in BACK_STATION_US:
        f.hang_picture("d", HALL_BACK, -1, station_u, "station")


def furnish_corridor(f) -> None:
    """Corridor (d 10.95..13.45): benches, a saint's niche by the chapel door, pictures, lamps."""
    front, back = CORRIDOR_CLEAR

    f.on_face("d", front, 1, "bench_long", -6.0)
    f.on_face("d", back, -1, "saint_niche", 3.0)
    f.hang_picture("d", front, 1, -0.5, "landscape")
    f.on_face("d", back, -1, "bench_long", 7.0)

    for lamp_u in (-9.5, 0.5, 9.5):
        f.put("hanging_oil_lamp", lamp_u, CORRIDOR_MIDDLE)


def furnish_seminary(f) -> None:
    """Upper floor of the sisters' wing; the rooms that need their night lamps most come first."""
    furnish_chapel(f)
    furnish_cells(f)
    furnish_infirmary(f)
    furnish_corridor(f)
    furnish_community(f)
    furnish_washroom(f)
    furnish_sacristy(f)


PLAN = dict(
    keeper=(6.0, CHAPEL_AXIS),  # the sacristan, in the middle aisle of the chapel
    posts=(),
    girder_pitch=2.4,
    partitions=(
        *corridor_walls(
            [(HALL_LEFT, WASH_WALL, "cells", [CELLS_DOOR]), (WASH_WALL, COMMUNITY_WALL, "washroom", [WASH_DOOR]), (COMMUNITY_WALL, HALL_RIGHT, "community", [COMMUNITY_DOOR])],
            [(HALL_LEFT, INFIRMARY_WALL, "infirmary", [INFIRMARY_DOOR]), (INFIRMARY_WALL, CHAPEL_WALL, "sacristy", [SACRISTY_DOOR]), (CHAPEL_WALL, HALL_RIGHT, "chapel", [CHAPEL_DOOR])],
            "corridor",
        ),
        cross_wall(WASH_WALL, FRONT_BAND, "cells", "washroom"),
        cross_wall(COMMUNITY_WALL, FRONT_BAND, "washroom", "community"),
        cross_wall(INFIRMARY_WALL, BACK_BAND, "infirmary", "sacristy", [ISOLATION_DOOR]),
        cross_wall(CHAPEL_WALL, BACK_BAND, "sacristy", "chapel", [VESTRY_DOOR]),
        ("d", SACRISTY_WALL, SACRISTY_WEST, SACRISTY_EAST, dict(faces=("sacristy", "infirmary"))),
    ),
    finishes=(
        ("front", HALL_LEFT, CELLS_EAST, "cells"),
        ("front", WASH_WEST, WASH_EAST, "washroom"),
        ("front", COMMUNITY_WEST, HALL_RIGHT, "community"),
        ("left", HALL_FRONT, FRONT_FACE, "cells"),
        ("left", CORRIDOR_CLEAR[0], CORRIDOR_CLEAR[1], "corridor"),
        ("left", BACK_FACE, HALL_BACK, "infirmary"),
        ("right", HALL_FRONT, FRONT_FACE, "community"),
        ("right", CORRIDOR_CLEAR[0], CORRIDOR_CLEAR[1], "corridor"),
        ("right", BACK_FACE, HALL_BACK, "chapel"),
        ("back", HALL_LEFT, INFIRMARY_EAST, "infirmary"),
        ("back", SACRISTY_WEST, SACRISTY_EAST, "infirmary"),
        ("back", CHAPEL_WEST, HALL_RIGHT, "chapel"),
    ),
    stone_floors=((WASH_WEST, WASH_EAST, HALL_FRONT, FRONT_FACE),),
    furnish=furnish_seminary,
)
