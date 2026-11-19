"""Rooms of the library wing (hall `library`, ground floor, right wing of the orphanage).

Five rooms split by the long wall at d = 8.2 m and three cross walls:
  - Passage (front, u -14.55..-11.36): vestibule entrance, lavabo, coat pegs, notice board, bench, holy water font.
  - Library (front, u -11.06..14.55): tall bookcases, two-tier book galleries with spiral stair, five reading tables
    with chairs, librarian's desk, card catalogues, scroll racks, globe, lectern, book cart, rolling ladders, clock.
  - Refectory (back, u -14.55..2.70): six long dining tables with benches (48 child seats), staff head table across the
    far end, reading pulpit, crockery dressers, serving counter, water filter, benches, wall crucifix and paintings.
  - Kitchen (back, u 3.00..10.00): masonry range, central worktable under hanging pan rack, dough table, stone sink,
    pot shelves, bread rack, water filter, firewood stack, flour sacks, hanging pots and garlic strings.
  - Pantry (back, u 10.30..14.55): pantry shelves on four walls, crates, flour and grain sacks, barrels, step ladder,
    hanging sausages and garlic strings.
"""

import itertools

WALL_HALF = 0.15  # half the thickness of an inner partition wall
LONG_WALL_D = 8.2  # splits the hall into a front band (d 0.3..8.05) and a back band (d 8.35..19.1)
PASSAGE_WALL_U = -11.21  # cross wall between Passage and Library (on a facade pier)
REFECTORY_WALL_U = 2.85  # cross wall between Refectory and Kitchen (clear of back window at u 3.01..4.61)
KITCHEN_WALL_U = 10.15  # cross wall between Kitchen and Pantry (on the solid pier at u 8.63..11.04)

PASSAGE_LIBRARY_DOOR = dict(at=3.0, width=1.5, height=2.1, leaf=("high", -1), lane=("low", "high"))
PASSAGE_REFECTORY_DOOR = dict(at=-12.95, width=1.5, height=2.1, leaf=("high", 1), lane=("low", "high"))
REFECTORY_KITCHEN_DOOR = dict(at=10.2, width=1.5, height=2.1, leaf=("high", 1), lane=("low", "high"))
KITCHEN_PANTRY_DOOR = dict(at=10.2, width=1.5, height=2.1, leaf=("low", 1), lane=("low", "high"))

NEW_WALL_FINISHES = {
    "library": dict(dado="2F4A3A", trim="4A2F20"),
    "refectory": dict(dado="3D4D5C", trim="5A3A26"),
    "kitchen": dict(dado="FFFFFF", trim="3A5E8C", material="azulejo", uv=("world", 1.2)),
}

# Library table rows (reading_table is 2.00 x 1.00 m, study_chair is 0.50 x 0.50 m): the front row spans the room, the
# second row stops short of the book galleries; chairs 0.85 m either side, 1.25 m aisle between the rows
LIBRARY_TABLE_US = (-3.60, 0.00, 3.60, 7.20, 10.80)  # pitch 3.60 m (1.60 m gap); -4.60..11.80 inside -11.06..14.55
LIBRARY_ROW_DS = (2.10, 5.55)
LIBRARY_SECOND_ROW_US = (-3.60, 0.00)
LIBRARY_BOOKCASE_US = (-9.60, -7.57, -5.54, -3.51, -1.48, 0.55, 2.58)  # 7 x 2.00 m, pitch 2.03 m; -10.60..3.58
LIBRARY_LAMPS = ((-7.80, 3.00, True), (-3.60, 3.80, True), (0.00, 3.80, True), (3.60, 2.10, True), (7.20, 2.10, False), (10.80, 2.10, True))  # (u, d, lit)

# Refectory row geometry (long_table_set 3.60 x 0.90 m, long_bench 3.60 x 0.32 m)
REFECTORY_TABLE_US = (-11.55, -6.75, -1.95)  # 3 columns, pitch 4.80 m (1.20 m gap); -13.35..-0.15 inside -14.55..2.70
REFECTORY_ROW_DS = (11.95, 15.85)  # 2 rows, pitch 3.90 m; benches at row +- 0.81 (1.96 m central aisle)
REFECTORY_BENCH_OFFSET = 0.81  # 0.45 half-table + 0.20 leg clearance + 0.16 half-bench


def furnish_passage(f) -> None:
    """Entrance passage (u -14.55..-11.36, d 0.30..8.05): bench, holy water font, lavabo, coat pegs, notice board."""
    partition_u = PASSAGE_WALL_U - WALL_HALF  # -11.36
    back_d = LONG_WALL_D - WALL_HALF  # 8.05

    # Front window u = -12.73 (sill 0.90 m): bench_long (1.80 x 0.40 x 0.50 m) centred below sill; u -13.63..-11.83
    f.on_wall("front", "bench_long", -12.73)
    # Right partition front pier: holy_water_font (0.45 x 0.45 m) clear of vestibule lane (d >= 1.60) and door lane
    f.on_face("u", partition_u, -1, "holy_water_font", 1.25)

    # Left blind wall past vestibule lane (d 1.60..4.40): basin_row (2.60 x 0.60 m) at d = 5.75 (d 4.45..7.05)
    f.on_wall("left", "basin_row", 5.75)

    # Right partition past library door lane (d 2.05..3.95): clothes_pegs at 4.95 (4.15..5.75) and notice_board at 7.05
    f.on_face("u", partition_u, -1, "clothes_pegs", 4.95)
    f.on_face("u", partition_u, -1, "notice_board", 7.05)
    f.on_face("d", back_d, -1, "wall_crucifix", -11.78)

    # Clock above the basin row, the hand bell on the bench
    f.on_wall("left", "wall_clock", 6.20, z=0.65)
    f.put("brass_bell", -12.20, 0.55, z=0.56)

    # Lighting: 2 hanging oil lamps and 1 lit sconce (3 real lights), two more sconces for rhythm
    f.put("hanging_oil_lamp", -12.95, 3.00)
    f.put("hanging_oil_lamp", -12.95, 6.00)
    f.on_wall("left", "wall_sconce", 1.10, lit=False)
    f.on_wall("left", "wall_sconce", 5.75, lit=False)
    f.on_face("u", partition_u, -1, "wall_sconce", 6.05)


def furnish_library_room(f) -> None:
    """Library (u -11.06..14.55, d 0.30..8.05): bookcases, two-tier galleries, spiral stair, reading tables and desk."""
    partition_u = PASSAGE_WALL_U + WALL_HALF  # -11.06
    inner_d = LONG_WALL_D - WALL_HALF  # 8.05

    # Inner wall (d = 8.05): 7 tall_bookcases (u -10.60..3.58), 2 book_galleries (3.58..11.90) + gallery_stair (11.90..13.70)
    for bookcase_u in LIBRARY_BOOKCASE_US:
        f.on_face("d", inner_d, -1, "tall_bookcase", bookcase_u)

    f.put("rolling_ladder", -5.54, 7.28)
    f.put("rolling_ladder", 1.57, 7.28)

    f.on_face("d", inner_d, -1, "book_gallery", 5.66)
    f.on_face("d", inner_d, -1, "book_gallery", 9.82, open_end=1)
    f.put("gallery_stair", 12.80, 7.10, 0.0, winding=1)  # u 11.90..13.70 (< 13.75, clears right window 2 at d 6.9..8.3)

    # Exposed right wall (u = 14.55): tall_bookcase on each solid pier (windows at d 2.7..4.1 and 6.9..8.3)
    f.on_wall("right", "tall_bookcase", 1.50)  # d 0.50..2.50
    f.on_wall("right", "tall_bookcase", 5.50)  # d 4.50..6.50

    # Front wall (d = 0.30): card_catalogs and scroll_racks on piers, bench_longs under windows (sill 0.90 m)
    f.on_wall("front", "card_catalog", -8.175)   # Pier 1: u -8.90..-7.46
    f.on_wall("front", "scroll_rack", -5.1375)   # Pier 2: u -5.76..-4.52
    f.on_wall("front", "bench_long", 0.00)       # Axis window: u -0.90..0.90
    f.on_wall("front", "bench_long", 3.62)       # Window 5: u 2.72..4.52
    f.on_wall("front", "card_catalog", 8.175)    # Pier 6: u 7.46..8.90
    f.on_wall("front", "scroll_rack", 11.2125)   # Pier 7: u 10.59..11.83

    for pier_u, scene in ((-2.21, "portrait"), (2.21, "lady")):
        f.hang_picture("d", f.front, 1, pier_u, scene)

    # Left partition past door leaf (d 0.69..2.15) and door lane (d 2.05..3.95)
    f.on_face("u", partition_u, 1, "wall_crucifix", 4.30)
    f.on_face("u", partition_u, 1, "long_case_clock", 5.00)
    f.on_face("u", partition_u, 1, "wall_map", 6.40, variant="world")

    # Librarian's station facing the entrance (teacher_desk 2.06 x 0.94 m at -90 deg -> u -8.27..-7.33, d 1.97..4.03)
    f.put("teacher_desk", -7.80, 3.00, -90.0)
    f.put("study_chair", -6.95, 3.00, -90.0)
    f.put("book_cart", -7.80, 5.20, 0.0)
    f.put("globe_stand", -9.50, 5.50, 0.0)
    f.put("lectern", -5.65, 6.15, 0.0)

    # Reading tables: five in the front row, two behind them, four chairs each
    tables = [(table_u, LIBRARY_ROW_DS[0]) for table_u in LIBRARY_TABLE_US] + [(table_u, LIBRARY_ROW_DS[1]) for table_u in LIBRARY_SECOND_ROW_US]

    for table_u, table_d in tables:
        f.put("reading_table", table_u, table_d)

    for (table_u, table_d), chair_side in itertools.product(tables, (-0.55, 0.55)):
        f.put("study_chair", table_u + chair_side, table_d - 0.85, 180.0)
        f.put("study_chair", table_u + chair_side, table_d + 0.85, 0.0)

    # Lighting: 5 lit hanging lamps + 3 lit sconces (8 real lights; extra unlit fixtures for rhythm)
    for lamp_u, lamp_d, lit in LIBRARY_LAMPS:
        f.put("hanging_oil_lamp", lamp_u, lamp_d, lit=lit)

    for pier_u, lit in ((-8.175, True), (5.1375, False), (8.175, True)):
        f.on_wall("front", "wall_sconce", pier_u, lit=lit)

    f.on_face("u", partition_u, 1, "wall_sconce", 7.45)


def furnish_refectory(f) -> None:
    """Refectory (u -14.55..2.70, d 8.35..19.10): 6 long tables (48 seats), staff head table, pulpit, dressers."""
    front_d = LONG_WALL_D + WALL_HALF  # 8.35
    right_u = REFECTORY_WALL_U - WALL_HALF  # 2.70

    # Two parallel rows of 3 long_table_sets (3.60 x 0.90 m) with 12 long_benches (3.60 x 0.32 m)
    # Row 1 d 10.98..12.92, Row 2 d 14.88..16.82 -> central aisle 1.96 m, front aisle 2.63 m, back aisle 2.28 m
    for row_d, (col_index, table_u) in itertools.product(REFECTORY_ROW_DS, enumerate(REFECTORY_TABLE_US)):
        f.put("long_table_set", table_u, row_d)
        f.put("long_bench", table_u, row_d - REFECTORY_BENCH_OFFSET, 180.0)
        f.put("long_bench", table_u, row_d + REFECTORY_BENCH_OFFSET, 0.0)
        f.put("hanging_oil_lamp", table_u, row_d, lit=(row_d < 13.0 and col_index != 1) or (row_d > 14.0 and col_index == 1))

    # Staff head table across the far end (long_table_set at -90 deg -> u 1.05..1.95, d 12.30..15.90; 1.20 m aisle)
    f.put("long_table_set", 1.50, 14.10, -90.0)
    f.put("hanging_oil_lamp", 1.50, 14.10)
    f.put("brass_bell", 1.50, 15.62, z=0.81)

    for chair_d in (12.90, 13.70, 14.50, 15.30):  # 4 bentwood_chairs (pitch 0.80 m; u 2.01..2.49)
        f.put("bentwood_chair", 2.25, chair_d, -90.0)

    # Kitchen serving counter against far wall past head table (u 1.95..2.70, d 16.50..18.90) and reading pulpit
    f.on_face("u", right_u, -1, "serving_counter", 17.70)
    f.on_face("u", right_u, -1, "wall_crucifix", 14.10)
    f.on_face("u", right_u, -1, "wall_clock", 17.70, z=0.5)
    f.on_wall("back", "reading_pulpit", 0.50)

    # Back wall (d = 19.10, high windows sill 3.30 m): 3 crockery_dressers (1.90 x 0.50 x 2.15 m)
    for dresser_u in (-11.55, -6.75, -2.25):
        f.on_wall("back", "crockery_dresser", dresser_u)

    # Front partition wall (d = 8.35) past folded door leaf (u -12.10..-10.64)
    f.on_face("d", front_d, 1, "water_filter", -10.20)
    f.on_face("d", front_d, 1, "bench_long", -8.55)
    f.on_face("d", front_d, 1, "crockery_dresser", -5.55)
    f.on_face("d", front_d, 1, "bench_long", -2.55)

    # Pictures and wall sconces (total real lights in Refectory: 4 hanging + 4 sconces = 8)
    f.hang_picture("u", f.left, 1, 13.90, "landscape")
    f.hang_picture("d", front_d, 1, -8.55, "portrait")
    f.hang_picture("d", front_d, 1, -2.55, "lady")
    f.hang_picture("d", f.back, -1, -9.15, "seascape")
    f.hang_picture("d", f.back, -1, -4.80, "portrait")

    f.on_face("d", front_d, 1, "wall_sconce", -7.05, lit=True)
    f.on_face("d", front_d, 1, "wall_sconce", -4.05, lit=False)
    f.on_wall("back", "wall_sconce", -13.50, lit=False)
    f.on_wall("back", "wall_sconce", -3.55, lit=True)
    f.on_wall("left", "wall_sconce", 11.95, lit=True)
    f.on_wall("left", "wall_sconce", 15.85, lit=False)
    f.on_face("u", right_u, -1, "wall_sconce", 12.60, lit=False)
    f.on_face("u", right_u, -1, "wall_sconce", 15.60, lit=True)


def furnish_kitchen(f) -> None:
    """Kitchen (u 3.00..10.00, d 8.35..19.10): masonry range, central worktable, sink, pot shelves, dough table."""
    front_d = LONG_WALL_D + WALL_HALF  # 8.35
    left_u = REFECTORY_WALL_U + WALL_HALF  # 3.00
    right_u = KITCHEN_WALL_U - WALL_HALF  # 10.00

    # Back wall (d = 19.10, high windows sill 3.30 m): firewood_stack, masonry_range (2.80 x 1.05 x 2.70 m), flour_sacks
    f.on_wall("back", "firewood_stack", 4.10)  # u 3.45..4.75
    f.on_wall("back", "masonry_range", 6.50)   # u 5.10..7.90
    f.on_wall("back", "flour_sacks", 8.95)     # u 8.35..9.55

    # Front partition wall (d = 8.35): dough_table, crate_open, wicker_basket, jam_shelf, wall_crucifix
    f.on_face("d", front_d, 1, "dough_table", 6.50)  # u 5.50..7.50, d 8.35..9.35 (2.50 m from both doors)
    f.put("crate_open", 4.90, 8.65, 180.0, variant="roots")
    f.put("wicker_basket", 8.10, 8.65, 180.0, variant="fruit")
    f.on_face("d", front_d, 1, "wall_crucifix", 4.90)
    f.on_face("d", front_d, 1, "wall_clock", 6.50)
    f.on_face("d", front_d, 1, "jam_shelf", 8.10)

    # Left partition (u = 3.00) past folded door leaf (d 11.05..12.51): 2 pot_shelfs (pitch 2.40 m) + water_filter
    f.on_face("u", left_u, 1, "pot_shelf", 13.60)      # d 12.70..14.50
    f.on_face("u", left_u, 1, "pot_shelf", 16.00)      # d 15.10..16.90
    f.on_face("u", left_u, 1, "water_filter", 17.65)   # d 17.40..17.90

    # Right partition (u = 10.00) past door lane (d 9.25..11.15): stone_sink + bread_rack
    f.on_face("u", right_u, -1, "kitchen_stove", 17.55)  # d 16.95..18.15, past the bread rack and clear of the flour sacks
    f.on_face("u", right_u, -1, "stone_sink", 13.80)   # d 12.95..14.65
    f.on_face("u", right_u, -1, "bread_rack", 15.95)   # d 15.27..16.63

    # Central worktable (2.40 x 1.00 m) with overhead pan rack; aisles 1.88 m left, 1.60 m right, 3.22 m back
    f.put("kitchen_worktable", 6.50, 14.30)
    f.put("kitchen_worktable", 6.50, 11.60)
    f.put("hanging_pan_rack", 6.50, 14.30)

    for stool_u in (5.70, 6.50, 7.30):
        f.put("stool_round", stool_u, 10.85)
    f.put("hanging_pots", 6.50, 17.40)
    f.put("garlic_strings", 6.50, 8.85)

    # Lighting: 2 hanging oil lamps, the stove's fire and 2 lit wall sconces (5 real lights)
    f.put("hanging_oil_lamp", 6.50, 12.60)
    f.put("hanging_oil_lamp", 6.50, 16.00)
    f.on_face("u", left_u, 1, "wall_sconce", 14.80, lit=False)
    f.on_face("u", right_u, -1, "wall_sconce", 13.80)
    f.on_wall("back", "wall_sconce", 8.95)
    f.on_face("d", front_d, 1, "wall_sconce", 6.50, lit=False)


def furnish_pantry(f) -> None:
    """Pantry (u 10.30..14.55, d 8.35..19.10): pantry shelves on all four sides, sacks, barrels, crates, ladder."""
    front_d = LONG_WALL_D + WALL_HALF  # 8.35
    left_u = KITCHEN_WALL_U + WALL_HALF  # 10.30

    # Left partition past door lane (d 9.25..11.15): 3 pantry_shelfs (1.90 x 0.55 m), pitch 2.50 m (0.60 m gap)
    for shelf_d in (12.40, 14.90, 17.40):  # d 11.45..13.35, 13.95..15.85, 16.45..18.35
        f.on_face("u", left_u, 1, "pantry_shelf", shelf_d)

    # Back wall (u 11.45..13.35) and front wall clear of door (u 12.15..14.05)
    f.on_wall("back", "pantry_shelf", 12.40)
    f.on_face("d", front_d, 1, "pantry_shelf", 13.10)

    # Exposed right wall (u = 14.55; windows at d 11.10..12.50 and 15.30..16.70, sill 0.90 m)
    f.on_wall("right", "pantry_shelf", 13.90)  # middle pier: d 12.95..14.85
    f.put("crate_stack", 14.00, 10.10, -90.0)  # front pier: d 9.40..10.80
    f.put("flour_sacks", 14.00, 11.80, -90.0)  # under window 3 (0.70 < 0.90 sill): d 11.20..12.40
    f.put("sack_pile", 14.00, 16.00, -90.0)    # under window 4 (0.78 < 0.90 sill): d 15.40..16.60
    f.put("barrel_group", 13.95, 17.85, -90.0) # back pier: d 17.20..18.50

    # Floor crates/baskets and step ladder along shelves (central aisle 1.70..1.82 m)
    f.put("crate_open", 11.25, 13.70, 90.0, variant="apples")
    f.put("wicker_basket", 13.45, 13.60, -90.0, variant="mushrooms")
    f.put("step_ladder", 11.35, 16.20, 90.0)

    # Overhead hanging goods and lighting (2 hanging oil lamps + 1 lit sconce = 3 real lights)
    f.put("ceiling_beam_hooks", 12.40, 12.40, 90.0, variant="sausages")
    f.put("garlic_strings", 12.40, 14.50, 90.0)
    f.put("ceiling_beam_hooks", 12.40, 17.40, 90.0, variant="sausages")
    f.put("hanging_oil_lamp", 12.40, 10.60)
    f.put("hanging_oil_lamp", 12.40, 15.60)
    f.on_face("u", left_u, 1, "wall_sconce", 13.65)
    f.on_face("u", left_u, 1, "wall_sconce", 16.15, lit=False)


def furnish_library(f) -> None:
    """Furnish all five rooms of the library wing (ground floor, right wing)."""
    furnish_passage(f)
    furnish_library_room(f)
    furnish_refectory(f)
    furnish_kitchen(f)
    furnish_pantry(f)


PLAN = dict(
    keeper=(-6.85, 3.90),
    posts=(),
    girder_pitch=2.4,
    stone_floors=((3.00, 10.00, 8.35, 19.10), (10.30, 14.55, 8.35, 19.10)),
    partitions=(
        ("u", PASSAGE_WALL_U, 0.3, LONG_WALL_D - WALL_HALF, dict(doors=[PASSAGE_LIBRARY_DOOR], faces=("library", "library"))),
        ("d", LONG_WALL_D, -14.55, REFECTORY_WALL_U, dict(doors=[PASSAGE_REFECTORY_DOOR], faces=("library", "refectory"))),
        ("d", LONG_WALL_D, REFECTORY_WALL_U, KITCHEN_WALL_U, dict(faces=("library", "kitchen"))),
        ("d", LONG_WALL_D, KITCHEN_WALL_U, 14.55, dict(faces=("library", "kitchen"))),
        ("u", REFECTORY_WALL_U, LONG_WALL_D + WALL_HALF, 19.1, dict(doors=[REFECTORY_KITCHEN_DOOR], faces=("refectory", "kitchen"))),
        ("u", KITCHEN_WALL_U, LONG_WALL_D + WALL_HALF, 19.1, dict(doors=[KITCHEN_PANTRY_DOOR], faces=("kitchen", "kitchen"))),
    ),
    finishes=(
        ("front", -14.55, 14.55, "library"),
        ("left", 0.3, LONG_WALL_D - WALL_HALF, "library"),
        ("right", 0.3, LONG_WALL_D - WALL_HALF, "library"),
        ("left", LONG_WALL_D + WALL_HALF, 19.1, "refectory"),
        ("back", -14.55, REFECTORY_WALL_U - WALL_HALF, "refectory"),
        ("back", REFECTORY_WALL_U + WALL_HALF, KITCHEN_WALL_U - WALL_HALF, "kitchen"),
        ("back", KITCHEN_WALL_U + WALL_HALF, 14.55, "kitchen"),
        ("right", LONG_WALL_D + WALL_HALF, 19.1, "kitchen"),
    ),
    furnish=furnish_library,
)
