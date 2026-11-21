"""Plan of the adventurers' guild and its bank (references in the private refs repo, lojas/guild).

After guildhalls and livery halls kept from the guild era and banking halls of old banks: the great hall behind the
main door, panelled to the height of a man and a half under a coffered ceiling, the registry crystal on its dais in
the middle, the hearth on the side wall, long tables and the quest boards; at its far end the counter under the
gallery, the world map behind it and the doors to the back rooms. The guild bank on the right with its own street
door: the public floor before the teller screen, the clerks behind it, the strongroom at the back. Behind the hall
the guildmaster's office with the records and the trophy room.

guild_shell.py builds the walls, floors, ceilings, the gallery and the facade; build_market_shops.py reads PLAN
(keeper, partitions, furnish). Coordinates as in shop_layouts.py: u across the facade, d into the lot.
"""

HALF_WALL = 0.15
BANK_WALL = 5.3  # axis of the wall between the great hall and the bank, front to back
HALL_BACK = 13.2  # axis of the wall behind the gallery (great hall | office and trophy room)
BANK_BACK = 12.0  # axis of the wall between the banking hall and the strongroom
OFFICE_WALL = -2.1  # axis of the wall between the guildmaster's office and the trophy room
HALL_AXIS = -3.2  # middle of the great hall: main door, runner, dais, counter
ROOMS = {  # name -> (u from, u to, d from, d to) inside the walls
    "hall": (-11.55, BANK_WALL - HALF_WALL, 0.3, HALL_BACK - HALF_WALL),
    "bank": (BANK_WALL + HALF_WALL, 11.55, 0.3, BANK_BACK - HALF_WALL),
    "strongroom": (BANK_WALL + HALF_WALL, 11.55, BANK_BACK + HALF_WALL, 19.1),
    "office": (-11.55, OFFICE_WALL - HALF_WALL, HALL_BACK + HALF_WALL, 19.1),
    "trophies": (OFFICE_WALL + HALF_WALL, BANK_WALL - HALF_WALL, HALL_BACK + HALF_WALL, 19.1),
}
GALLERY = (10.65, 3.6)  # d of its front edge, z of its underside; it runs across the hall to the back wall
BANK_DOOR = (8.6, 1.6, 3.0)  # u, width, height of the bank's own street door (the guild's is SHOPS["guild"]["door"])
HALL_WINDOWS = (-9.4, -6.3, -0.1, 3.0)  # u of the tall arched windows of the hall front
BANK_WINDOWS = (6.55, 10.65)
HALL, BANK, STRONGROOM, OFFICE, TROPHIES = "guild_panel", "bank_marble", "strongroom_stone", "office_panel", "trophy_red"
PARTITIONS = (
    ("u", BANK_WALL, 0.3, BANK_BACK, dict(doors=[dict(at=4.6, width=1.8, height=3.0)], faces=(None, BANK))),
    ("u", BANK_WALL, BANK_BACK, HALL_BACK, dict(faces=(None, STRONGROOM))),
    ("u", BANK_WALL, HALL_BACK, 19.1, dict(doors=[dict(at=17.2, width=1.2, height=2.3, leaf=("high", 1))], faces=(TROPHIES, STRONGROOM))),
    ("d", HALL_BACK, -11.55, BANK_WALL - HALF_WALL, dict(doors=[dict(at=-9.0, width=1.3, height=2.5, leaf=("high", 1)), dict(at=2.6, width=1.6, height=2.7)], faces=(None, None))),
    ("u", OFFICE_WALL, HALL_BACK + HALF_WALL, 19.1, dict(faces=(OFFICE, TROPHIES))),
    ("d", BANK_BACK, BANK_WALL + HALF_WALL, 11.55, dict(doors=[dict(at=10.7, width=1.2, height=2.3, leaf=("high", -1))], faces=(BANK, STRONGROOM))),
)


def furnish_hall(f) -> None:
    """Dais and crystal in the middle, counter and map under the gallery, hearth corner, tables and quest boards."""
    hall_side = BANK_WALL - HALF_WALL

    f.put("dais_a", HALL_AXIS, 6.8, width=3.6, depth=2.4)
    f.put("registry_crystal", HALL_AXIS, 7.0, 0.0, z=0.35)
    f.put("dragon_skull_hanging", HALL_AXIS, 3.6)
    f.put("guild_counter", HALL_AXIS, 11.4)
    f.on_face("d", HALL_BACK - HALF_WALL, -1, "world_map_wall", HALL_AXIS)
    f.on_wall("left", "guild_hearth_a", 6.4)
    f.put("armchair", -8.3, 4.3, -120.0)
    f.put("armchair", -8.3, 8.5, -60.0)
    f.put("rug", -8.4, 6.4, 90.0, variant="gold")
    f.on_wall("left", "monster_trophy", 11.6, variant="claw")
    f.put("group_table", 1.4, 3.4)
    f.put("group_table", 1.4, 7.0)
    f.on_face("u", hall_side, -1, "notice_board", 1.9)
    f.on_face("u", hall_side, -1, "quest_board", 8.2)
    f.on_wall("front", "armor_stand_a", -7.85, variant="knight_gold")
    f.on_wall("front", "armor_stand_a", 1.45, variant="plate")
    f.on_wall("front", "plant_pot", -11.0, variant="bush")
    f.on_wall("front", "plant_pot", 4.6, variant="bush")


def furnish_bank(f) -> None:
    """Public floor with the writing desk and the bench, the teller screen across, clerks and deposit boxes behind."""
    bank_side = BANK_WALL + HALF_WALL

    f.put("teller_counter", 8.5, 6.4)
    f.put("check_desk", 8.6, 3.2)
    f.on_face("u", bank_side, 1, "bench_long", 1.6)
    f.on_wall("right", "deposit_boxes", 7.9)
    f.put("coin_table", 8.0, 10.9)
    f.put("money_sacks", 6.3, 10.9)
    f.on_face("d", BANK_BACK - HALF_WALL, -1, "wall_clock", 7.6)
    f.on_wall("front", "plant_pot", 7.3, variant="bush")
    f.on_wall("front", "plant_pot", 9.9, variant="bush")


def furnish_strongroom(f) -> None:
    """The safe door on the back wall, deposit boxes round the walls, chests and sacks of coin."""
    f.on_wall("back", "vault_door", 8.6)
    f.on_wall("right", "deposit_boxes", 14.2)
    f.on_wall("right", "deposit_boxes", 16.0)
    f.on_face("u", BANK_WALL + HALF_WALL, 1, "deposit_boxes", 14.0)
    f.put("chest_gold", 10.7, 18.2, 90.0)
    f.put("money_sacks", 6.6, 18.6)


def furnish_office(f) -> None:
    """The guildmaster's desk facing the door, records on the walls, the table with the charts."""
    f.put("director_desk", -6.9, 17.4, 180.0)
    f.on_wall("left", "tall_bookcase", 15.0)
    f.on_wall("left", "tall_bookcase", 17.6)
    f.on_wall("back", "filing_cabinet", -10.4)
    f.on_face("u", OFFICE_WALL - HALF_WALL, -1, "tall_bookcase", 17.3)
    f.put("group_table", -4.6, 14.9)
    f.put("armchair", -7.6, 15.0, 200.0)
    f.put("rug", -6.9, 16.6, variant="red")


def furnish_trophies(f) -> None:
    """Trophy cases and the rank board on the walls, heads and claws over them, the rental rack, two suits of armour."""
    f.on_wall("back", "trophy_case", 0.0)
    f.on_wall("back", "trophy_case", 2.9)
    f.on_face("u", OFFICE_WALL + HALF_WALL, 1, "rank_board", 15.0)
    f.on_face("u", OFFICE_WALL + HALF_WALL, 1, "monster_trophy", 17.6, variant="horns")
    f.on_face("u", BANK_WALL - HALF_WALL, -1, "weapon_rental_rack", 15.0)
    f.on_face("u", BANK_WALL - HALF_WALL, -1, "monster_trophy", 18.7, variant="skull")
    f.put("armor_stand_a", 1.4, 16.6, variant="mail")


def furnish_guild(f) -> None:
    furnish_hall(f)
    furnish_bank(f)
    furnish_strongroom(f)
    furnish_office(f)
    furnish_trophies(f)


PLAN = dict(keeper=(HALL_AXIS, 12.45), posts=(), partitions=PARTITIONS, furnish=furnish_guild)
