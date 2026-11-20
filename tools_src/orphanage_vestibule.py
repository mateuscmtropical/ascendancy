"""Rooms of the vestibule of the orphanage (hall `vestibule`, both storeys; the shell is casarao_vestibule.py).

Ground floor, behind the street portal:
  - Entrance hall (u -4.99..4.99, d 0.30..10.65): urns, benches, a saint's niche and the holy water font, the
    porter's hatch on its +u wall.
  - Parlour (u -14.55..-5.29): split across by the grille wall at d = 5.0; the visitors sit on the window side
    (door from the entrance hall), the sisters on the enclosure side (door from the crossing). The grille has the
    turn for passing parcels.
  - Porter's lodge (u 5.29..8.03): the porteress's desk at the hatch, the key board, her bed, press and washstand.
  - Mother Superior's office (u 8.33..14.55): the desk facing the door with two chairs for visitors, bookcases,
    files, the safe, a sofa.
  - Crossing (d 10.95..16.20): from the school wing to the service wing in front of the stair, benches, clock.
  - Lavatory (back, u 5.10..14.55): six latrine stalls on the service wing wall and two troughs.
  - Teachers' room (back, u -14.55..-5.10): table for the lay masters, shelves, coat pegs, maps.
Upper floor (the gallery round the stair well): the children's recreation hall, with a reading corner, the games
tables, the little ones' toy corner, a drawing corner and the music corner with the piano.
"""

import itertools

from orphanage_wing_common import CORRIDOR, CORRIDOR_FINISH, HALL_BACK, HALL_FRONT, HALL_LEFT, HALL_RIGHT, WALL_HALF, door, hatch

HALL_WALL = 5.1375  # |u| of the walls between the entrance hall and the parlour or the lodge (facade piers)
OFFICE_WALL = 8.175  # u of the wall between the lodge and the office (a facade pier)
GRILLE_WALL = 5.0  # d of the grille wall across the parlour
FRONT_ROOMS = CORRIDOR[0]  # d of the wall closing the front rooms on the crossing
BACK_ROOMS = 16.9  # d of the wall closing the back corners on the crossing (behind the colonnade)
WELL = (-4.8, 4.8, 16.2, HALL_BACK)  # stair well (u from, u to, d from, d to): casarao_vestibule.WELL_HALF, WELL_FRONT
WELL_SIDE = 5.1  # |u| of the outer faces of the walls of the well
COLUMNS = (-9.7, 9.7)  # u of the colonnade columns outside the well, at d = WELL[2]
GRILLE_U = -9.85

FRONT_FACE = FRONT_ROOMS - WALL_HALF
CROSSING_FRONT = FRONT_ROOMS + WALL_HALF
CROSSING_BACK = BACK_ROOMS - WALL_HALF
BACK_FACE = BACK_ROOMS + WALL_HALF
PARLOUR_EAST = -HALL_WALL - WALL_HALF
HALL_EAST = HALL_WALL - WALL_HALF
LODGE_WEST = HALL_WALL + WALL_HALF
LODGE_EAST = OFFICE_WALL - WALL_HALF
OFFICE_WEST = OFFICE_WALL + WALL_HALF
GRILLE_FRONT = GRILLE_WALL - WALL_HALF
GRILLE_BACK = GRILLE_WALL + WALL_HALF

PARLOUR_DOOR = door(2.6)  # entrance hall -> visitors' side
ENCLOSURE_DOOR = door(-13.0)  # crossing -> sisters' side
LODGE_DOOR = door(6.6)
OFFICE_DOOR = door(11.4)
LAVATORY_DOOR = door(12.6)
TEACHERS_DOOR = door(-12.6)
PORTER_HATCH = hatch(4.5, 1.2)
GRILLE = dict(at=GRILLE_U, width=3.0, height=2.6, sill=0.9, lane=())

NEW_WALL_FINISHES = {
    "corridor": CORRIDOR_FINISH,  # every room of the vestibule keeps the azulejo dado of its outer walls
}


def furnish_entrance(f) -> None:
    """Entrance hall and crossing: urns on the piers of the portal, benches and the saint on the side walls, the
    holy water font by the parlour door, the long-case clock and benches on the crossing, the chandelier."""
    for pier_u in (-2.2, 2.2):
        f.put("pedestal_urn", pier_u, f.front + 0.36)

    f.on_face("u", -HALL_EAST, 1, "holy_water_font", 4.0)
    f.on_face("u", -HALL_EAST, 1, "bench_long", 6.6)
    f.on_face("u", -HALL_EAST, 1, "saint_niche", 9.0)
    f.on_face("u", HALL_EAST, -1, "bench_long", 7.4)
    f.on_face("u", HALL_EAST, -1, "wall_lantern", 2.4)
    f.hang_picture("u", -HALL_EAST, 1, 6.6, "portrait")
    f.hang_picture("u", HALL_EAST, -1, 7.4, "lady")
    f.put("grand_chandelier", 0.0, 5.5, drop=0.5)

    for plant_u in (-4.4, 4.4):
        f.put("plant_pot", plant_u, FRONT_FACE - 0.4)

    f.on_face("d", CROSSING_FRONT, 1, "long_case_clock", -7.5)
    f.on_face("d", CROSSING_FRONT, 1, "bench_long", 9.0)
    f.on_face("d", CROSSING_BACK, -1, "bench_long", -8.0)
    f.on_face("d", CROSSING_BACK, -1, "bench_long", 7.6)
    f.hang_picture("d", CROSSING_BACK, -1, -11.6, "portrait")
    f.hang_picture("d", CROSSING_BACK, -1, 11.0, "lady")

    for column_u in COLUMNS:
        f.block("coluna", (column_u - 0.35, column_u + 0.35, WELL[2] - 0.35, WELL[2] + 0.35))


def furnish_parlour(f) -> None:
    """Parlour (u -14.55..-5.29): the grille with its turn in the middle of the wall at d = 5.0, four chairs for the
    visitors before it, a bench, a side table and a picture on their side; two chairs, a table and the crucifix on
    the sisters' side."""
    f.put("parlour_grille", GRILLE_U, GRILLE_WALL, 0.0, variant="turn")

    for chair_u in (-11.0, -10.3, -9.4, -8.7):
        f.put("bentwood_chair", chair_u, GRILLE_FRONT - 0.9, 180.0)

    f.put("rug_ornate", GRILLE_U, 3.2, variant="red")
    f.on_wall("left", "bench_long", 2.6)
    f.hang_picture("u", HALL_LEFT, 1, 2.6, "portrait")
    f.put("side_table", -6.2, 1.2)
    f.put("plant_pot", -14.0, 0.8)
    f.hang_picture("u", PARLOUR_EAST, -1, 1.2, "landscape")
    f.on_face("u", PARLOUR_EAST, -1, "wall_sconce", 4.0, lit=False)

    for chair_u in (-10.4, -9.3):
        f.put("bentwood_chair", chair_u, GRILLE_BACK + 0.9)

    f.put("side_table", -7.2, 8.4)
    f.put("rug_ornate", GRILLE_U, 6.8, variant="green")
    f.on_face("u", PARLOUR_EAST, -1, "floor_shelf", 7.0, variant="books")
    f.on_wall("left", "saint_niche", 6.4)
    f.on_face("d", FRONT_FACE, -1, "wall_crucifix", GRILLE_U)
    f.on_wall("left", "prie_dieu", 8.0)
    f.put("hanging_oil_lamp", GRILLE_U, 2.6)
    f.put("hanging_oil_lamp", GRILLE_U, 7.8)


def furnish_lodge(f) -> None:
    """Porter's lodge (u 5.29..8.03): the desk under the hatch with the register and the hand bell, her chair, the
    key board, her bed along the hall wall, a press and a washstand."""
    f.on_face("u", LODGE_WEST, 1, "porter_desk", PORTER_HATCH["at"])
    f.put("bentwood_chair", 6.5, PORTER_HATCH["at"], -90.0)
    f.on_face("u", LODGE_EAST, -1, "key_board", 4.5)
    f.on_face("u", LODGE_EAST, -1, "washstand", 1.6)
    f.on_face("u", LODGE_EAST, -1, "wardrobe", 8.5)
    f.put("iron_bed", LODGE_WEST + 0.48, 8.4, 0.0, variant="ochre")
    f.on_face("u", LODGE_EAST, -1, "wall_crucifix", 6.6)
    f.put("hanging_oil_lamp", 6.65, 4.5)


def furnish_office(f) -> None:
    """Mother Superior's office (u 8.33..14.55): the desk with its lamp facing the door, two visitors' chairs, the
    bookcases on the service wing wall, files and the safe on the lodge wall, a sofa, a rug, the crucifix."""
    f.put("rug_ornate", 11.4, 4.6, 90.0, variant="red")
    f.put("director_desk", 11.4, 3.9, 180.0)

    for chair_u in (10.8, 12.0):
        f.put("bentwood_chair", chair_u, 5.6)

    f.on_wall("right", "tall_bookcase", 2.4)
    f.on_wall("right", "tall_bookcase", 4.6)
    f.on_wall("right", "sofa", 7.6)
    f.on_face("u", OFFICE_WEST, 1, "filing_cabinet", 2.0)
    f.on_face("u", OFFICE_WEST, 1, "iron_safe", 7.0)
    f.on_face("u", OFFICE_WEST, 1, "wall_crucifix", 4.5)
    f.hang_picture("d", FRONT_FACE, -1, 13.4, "portrait")
    f.put("hanging_oil_lamp", 11.4, 6.0)


def furnish_lavatory(f) -> None:
    """Lavatory (u 5.10..14.55, d 17.05..24.10): six stalls on the service wing wall, two troughs on the back wall,
    towel racks on the wall of the well."""
    for stall_d in (18.6, 19.6, 20.6, 21.6, 22.6, 23.6):
        f.on_wall("right", "latrine_stall", stall_d)

    for trough_u in (7.4, 10.6):
        f.on_wall("back", "washroom_trough", trough_u)

    f.on_face("u", WELL_SIDE, 1, "towel_rack", 19.0)
    f.put("hanging_oil_lamp", 9.8, 20.6)


def furnish_teachers(f) -> None:
    """Teachers' room (u -14.55..-5.10, d 17.05..24.10): the lay masters' table with six chairs, book shelves on the
    back wall, coat pegs by the door, the map, a cupboard."""
    for table_u in (-10.9, -8.7):
        f.put("reading_table", table_u, 20.6)

    for table_u, offset, side in itertools.product((-10.9, -8.7), (-0.5, 0.5), (-1, 1)):
        f.put("bentwood_chair", table_u + offset, 20.6 + side * 0.76, 0.0 if side > 0 else 180.0)

    for shelf_u in (-12.6, -7.0):
        f.on_wall("back", "floor_shelf", shelf_u, variant="books")

    f.on_face("d", BACK_FACE, 1, "clothes_pegs", -9.5)
    f.on_wall("left", "wall_map", 20.6, variant="world")
    f.on_face("u", -WELL_SIDE, -1, "specimen_cupboard", 21.0)
    f.put("hanging_oil_lamp", -9.8, 20.6)


def furnish_gallery(gallery) -> None:
    """The children's recreation hall on the gallery: reading corner by the sisters' wing, eight games tables in the
    middle, the toy corner by the children's wing, the drawing corner and the music corner in the back."""
    gallery.block("vão", WELL)
    gallery.block("chegada", (WELL[0], WELL[1], WELL[2] - 1.6, WELL[2]))
    gallery.put("grand_chandelier", 0.0, (WELL[2] + WELL[3]) / 2.0, drop=2.4)

    gallery.put("rug_ornate", -10.0, 5.6, 90.0, variant="green")
    gallery.on_wall("left", "floor_shelf", 3.4, variant="books")
    gallery.on_wall("left", "floor_shelf", 5.2, variant="books")
    gallery.on_wall("left", "floor_shelf", 7.0, variant="books")
    gallery.put("sofa", -10.6, 8.2, 180.0)
    gallery.put("armchair", -8.6, 4.6, 120.0)
    gallery.put("armchair", -11.4, 4.2, 200.0)
    gallery.put("side_table", -9.8, 6.0)

    gallery.put("rug_ornate", 0.0, 7.4, variant="red")

    for table_u in (-6.6, -2.4, 2.4, 6.6):
        gallery.put("round_table_set", table_u, 7.4)

    for table_u in (-7.0, -3.0, 3.0, 7.0):  # draughts and cards by the stair, a 2.75 m lane kept from the balcony to the stair
        gallery.put("cafe_table_set", table_u, 11.4)

    gallery.put("rug_ornate", 10.0, 5.6, 90.0, variant="blue")
    gallery.put("rocking_horse", 9.0, 4.4, 30.0)
    gallery.on_wall("right", "dollhouse", 3.0)
    gallery.on_wall("right", "toy_chest", 5.0)
    gallery.on_wall("right", "toy_chest", 7.0)
    gallery.put("cafe_table_set", 11.0, 7.6)
    gallery.on_wall("right", "floor_shelf", 9.0, variant="books")

    for easel_u in (-12.2, -9.8):
        gallery.put("easel", easel_u, 19.0, 180.0)

    for table_u, offset, side in itertools.product((-12.0, -9.6), (-0.5, 0.5), (-1, 1)):
        gallery.put("bentwood_chair", table_u + offset, 22.4 + side * 0.76, 0.0 if side > 0 else 180.0)

    for table_u in (-12.0, -9.6):
        gallery.put("reading_table", table_u, 22.4)
    gallery.on_wall("left", "wall_shelf", 22.0, variant="jars")

    gallery.on_wall("back", "piano", 9.8)
    gallery.grid("bentwood_chair", (8.4, 11.2), (19.4, 20.6), 3, 2, 180.0)
    gallery.on_wall("right", "wall_shelf", 21.6, variant="books")
    gallery.on_wall("right", "harmonium", 18.4)

    for lantern_d in (3.0, 8.0):
        gallery.on_wall("left", "wall_lantern", lantern_d + 1.0)
        gallery.on_wall("right", "wall_lantern", lantern_d + 1.0)

    gallery.grid("grand_chandelier", (-8.2, 8.2), (6.0, 6.0), 2, 1, drop=0.5)


def furnish_vestibule(f) -> None:
    """Both storeys of the vestibule."""
    gallery = f.upstairs(f.room.spec["storeys"][0])

    f.block("escada", (WELL[0], WELL[1], WELL[2] - 0.4, WELL[3]))
    furnish_entrance(f)
    furnish_parlour(f)
    furnish_lodge(f)
    furnish_office(f)
    furnish_lavatory(f)
    furnish_teachers(f)
    furnish_gallery(gallery)


PLAN = dict(
    keeper=(6.5, 5.6),  # the porteress, behind her desk at the hatch
    posts=(),
    partitions=(
        ("u", -HALL_WALL, HALL_FRONT, FRONT_FACE, dict(doors=[PARLOUR_DOOR], faces=("corridor", "corridor"))),
        ("u", HALL_WALL, HALL_FRONT, FRONT_FACE, dict(doors=[PORTER_HATCH], faces=("corridor", "corridor"))),
        ("u", OFFICE_WALL, HALL_FRONT, FRONT_FACE, dict(faces=("corridor", "corridor"))),
        ("d", GRILLE_WALL, HALL_LEFT, PARLOUR_EAST, dict(doors=[GRILLE], faces=("corridor", "corridor"))),
        ("d", FRONT_ROOMS, HALL_LEFT, -HALL_WALL, dict(doors=[ENCLOSURE_DOOR], faces=("corridor", "corridor"))),
        ("d", FRONT_ROOMS, HALL_WALL, OFFICE_WALL, dict(doors=[LODGE_DOOR], faces=("corridor", "corridor"))),
        ("d", FRONT_ROOMS, OFFICE_WALL, HALL_RIGHT, dict(doors=[OFFICE_DOOR], faces=("corridor", "corridor"))),
        ("d", BACK_ROOMS, WELL_SIDE, HALL_RIGHT, dict(doors=[LAVATORY_DOOR], faces=("corridor", "corridor"))),
        ("d", BACK_ROOMS, HALL_LEFT, -WELL_SIDE, dict(doors=[TEACHERS_DOOR], faces=("corridor", "corridor"))),
    ),
    furnish=furnish_vestibule,
)
