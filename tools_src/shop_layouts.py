"""Floor plans of the market shops: what stands where in each hall (docs/research/shops.md).

Each plan is a function of a Furnisher (build_market_shops.py): f.put(prop, u, d, degrees), f.on_wall(side, prop,
along), f.wall(side, [props]), f.grid(prop, u range, d range, columns, rows). Coordinates in metres: u across the
facade (0 = middle of the lot, the hall goes from f.left to f.right), d into the lot (f.front at the door wall,
f.back at the far wall). Props turn their front to the street at 0 degrees; the wall helpers turn their backs to
the wall. PLANS also says where the shopkeeper stands and, when the default grid does not fit, the posts and the
inner walls ("u" | "d", fixed coordinate, from, to). The back wall and the sides facing a street have windows
(f.windows, f.piers(side)): tall furniture goes on the piers between them (window_wall), the report flags any
prop that covers one.
"""


def furnish_generic(f) -> None:
    """Stand-in plan: counter at the back, shelves on the walls, tables of goods and rugs down the hall."""
    keeper_u, keeper_d = f.keeper

    f.put("counter_till", keeper_u, keeper_d - 1.3)
    f.put("rug", f.door_u, f.front + 4.5)
    f.wall("back", ["wall_shelf"] * 5, gap=0.6)
    f.wall("left", ["wall_shelf", "crate_stack", "wall_shelf", "barrel_group", "wall_shelf"], start=f.front + 2.0, gap=0.8)
    f.wall("right", ["wall_shelf", "sack_pile", "wall_shelf", "crate_stack", "wall_shelf"], start=f.front + 2.0, gap=0.8)
    f.grid("display_table", (f.left + 4.5, f.right - 4.5), (f.front + 5.0, f.back - 6.5), 2, 2)
    f.grid("wheel_chandelier", (f.left + 5.0, f.right - 5.0), (f.front + 5.0, f.back - 5.0), 2, 2)


def furnish_guild(f) -> None:
    """Adventurers' guild (24 m): nave from the portal to the three-wicket counter under the world map, quest board
    on the right wall, fireplace lounge on the left, party tables by the columns, a dragon skull overhead and the
    guild bank (tellers, deposit boxes, vault) in the back right corner."""
    f.put("rug", 0.0, 6.2, variant="red")
    f.put("registry_crystal", 0.0, 11.2)
    f.put("dragon_skull_hanging", 0.0, 8.0)
    f.put("guild_counter", 0.0, 15.7)
    f.on_wall("back", "world_map_wall", 0.0)
    f.on_wall("back", "guild_banner", -3.4)
    f.on_wall("back", "guild_banner", 3.4)
    f.on_wall("back", "monster_trophy", -5.6, variant="horns")
    f.on_wall("back", "trophy_case", -8.0)
    f.on_wall("back", "rank_board", 5.4)

    f.on_wall("right", "notice_board", 3.6)
    f.on_wall("right", "quest_board", 6.6)
    f.on_wall("right", "wanted_posters", 9.6)
    f.put("bench_long", 5.4, 7.6, 90.0)
    f.put("teller_counter", 7.6, 14.6, -90.0)
    f.on_wall("back", "vault_door", 9.6)
    f.on_wall("right", "deposit_boxes", 14.6)
    f.put("money_sacks", 10.6, 12.2)
    f.put("coin_table", 10.0, 16.6, -90.0)
    f.put("chest_gold", 10.8, 16.2)

    f.on_wall("left", "fireplace", 9.7)
    f.on_wall("left", "monster_trophy", 5.6, variant="claw")
    f.on_wall("left", "monster_trophy", 13.6, variant="skull")
    f.put("armchair", -8.4, 7.8, -60.0)
    f.put("armchair", -8.4, 11.6, -120.0)
    f.put("rug", -8.8, 9.7, 90.0, variant="gold")
    f.on_wall("left", "weapon_rental_rack", 16.6)
    f.put("group_table", -7.4, 3.9)
    f.put("group_table", 7.4, 3.6)
    f.put("group_table", -6.4, 15.2)
    f.on_wall("front", "armor_stand", -3.4, variant="knight_gold")
    f.on_wall("front", "armor_stand", 3.4, variant="plate")
    f.on_wall("front", "plant_pot", -10.8, variant="bush")
    f.on_wall("front", "plant_pot", 10.8, variant="bush")
    f.grid("wheel_chandelier", (-7.2, 7.2), (4.5, 13.5), 2, 2)
    f.scatter([("group_table", 0.0, {}), ("armor_stand", 0.0, {"variant": "mail"}), ("barrel_group", 0.0, {}), ("group_table", 90.0, {}), ("crate_stack", 0.0, {}), ("plant_pot", 0.0, {"variant": "fern"})], (-9.6, -2.6), (3.4, 13.4), 3, 4)
    f.scatter([("group_table", 0.0, {}), ("armor_stand", 0.0, {"variant": "mail"}), ("barrel_group", 0.0, {}), ("group_table", 90.0, {}), ("crate_stack", 0.0, {}), ("plant_pot", 0.0, {"variant": "fern"})], (2.6, 9.6), (3.4, 13.4), 3, 4)
    f.scatter([("group_table", 0.0, {}), ("bench_long", 90.0, {}), ("armor_stand", 0.0, {"variant": "leather"}), ("crate_open", 0.0, {"variant": "apples"}), ("barrel_group", 0.0, {})], (-10.4, -2.4), (3.0, 13.8), 4, 6, aisle=0.6)
    f.scatter([("group_table", 0.0, {}), ("bench_long", 90.0, {}), ("armor_stand", 0.0, {"variant": "leather"}), ("crate_open", 0.0, {"variant": "apples"}), ("barrel_group", 0.0, {})], (2.4, 10.4), (3.0, 13.8), 4, 6, aisle=0.6)


def furnish_smith(f) -> None:
    """Blacksmith (24 m): sales hall on the left (weapons on every wall, counter at the back), forge yard on the
    right, open to the street: forge and bellows at the back wall, anvil, quench barrel and grindstone around it."""
    f.put("counter_till", -5.0, 14.0)
    f.put("rug", -5.0, 11.4, variant="gold")
    f.wall("back", ["shield_wall", "axe_mace_rack", ("sword_wall", {"seed": 2}), "spear_rack", "helmet_shelf", "giant_sword"], start=-11.3, gap=0.4)
    window_wall(f, "left", [[], [("armor_stand", {"variant": "plate"}), ("armor_stand", {"variant": "mail"})], [("wall_shelf", {"variant": "helmets"})], ["spear_rack", ("armor_stand", {"variant": "leather"})]], ["boots_rack", "crate_stack", "gauntlet_basket", None], gap=0.5)
    f.put("floor_shelf", -8.4, 9.6, 90.0, variant="tools")
    f.put("floor_shelf", -1.6, 9.6, 90.0, variant="helmets")
    f.put("ingot_crates", 0.8, 4.2)
    f.put("blade_shelf", 2.6, 11.4, -90.0)
    f.put("spear_rack", 2.7, 14.4, -90.0)
    f.put("plans_table", 1.6, 17.2, -90.0)
    f.grid("wheel_chandelier", (-8.4, -1.6), (5.0, 12.0), 2, 2)
    f.scatter([("armor_stand", 0.0, {"variant": "plate"}), ("floor_shelf", 90.0, {"variant": "tools"}), ("crate_open", 0.0, {"variant": "ingots"}), ("axe_mace_rack", 0.0, {}), ("floor_shelf", 90.0, {"variant": "helmets"}), ("barrel_group", 0.0, {}), ("armor_stand", 0.0, {"variant": "leather"})], (-9.8, 1.2), (4.2, 11.4), 5, 3)

    f.on_wall("back", "forge", 8.2)
    f.put("bellows", 6.0, 17.5, -20.0)
    f.put("anvil_block", 6.8, 14.0, 30.0)
    f.put("quench_barrel", 9.4, 13.4)
    f.put("grindstone", 5.2, 10.8, 90.0)
    f.on_wall("right", "coal_pile", 16.8)
    f.on_wall("right", "tool_wall_rack", 13.9)
    f.on_wall("right", "ingot_crates", 8.4)
    f.put("plans_table", 3.9, 15.6, 90.0)
    f.put("blade_shelf", 3.6, 12.2, 90.0)
    f.put("barrel_group", 10.4, 4.6)
    f.put("crate_stack", 10.6, 6.6)
    f.put("ceiling_beam_hooks", 7.4, 11.8)
    f.put("hanging_lantern", 7.4, 6.5)
    f.scatter([("crate_open", 0.0, {"variant": "ingots"}), ("sack_pile", 0.0, {}), ("barrel_group", 0.0, {})], (5.0, 9.8), (3.0, 9.0), 3, 3)


def furnish_armor(f) -> None:
    """Armourer: showroom of mannequins along both walls and on the floor, a fitting platform with a mirror in the
    middle, shields and helmets behind the counter, a small plate workshop in the back corner."""
    f.put("counter_straight", 0.0, 14.7)
    f.put("rug", 0.0, 5.6, variant="red")
    f.put("fitting_platform", 0.0, 9.6)
    f.put("standing_mirror", 1.7, 11.2, 30.0)
    f.on_wall("back", "shield_wall", 0.0)
    f.on_wall("back", "helmet_shelf", -3.6)
    f.on_wall("back", "helmet_shelf", 3.6)
    f.on_wall("back", "guild_banner", 6.6, tint="7A2F3A")
    window_wall(f, "left", [[], [("armor_stand", {"variant": "plate"}), ("armor_stand", {"variant": "knight_gold"})], [("armor_stand", {"variant": "mail"}), ("armor_stand", {"variant": "leather"})], ["chainmail_stand", ("armor_stand", {"variant": "plate"})]], ["boots_rack", "gauntlet_basket", "boots_rack", None], gap=0.5)
    f.wall("right", [("wall_shelf", {"variant": "helmets"}), ("armor_stand", {"variant": "leather"}), "shield_wall", "gauntlet_basket", ("armor_stand", {"variant": "plate"}), "plate_pile", "crate_stack"], start=3.4, gap=0.6)
    f.grid("armor_stand", (-5.6, 5.6), (5.6, 11.6), 2, 2, variant="knight_gold")
    f.put("floor_shelf", -5.6, 8.6, 90.0, variant="helmets")
    f.put("floor_shelf", 5.6, 8.6, 90.0, variant="shoes")
    f.put("anvil_block", -6.4, 17.2, 20.0)
    f.put("plans_table", -6.8, 14.8, 90.0)
    f.grid("wheel_chandelier", (0.0, 0.0), (5.0, 12.5), 1, 2)
    f.scatter([("armor_stand", 0.0, {"variant": "mail"}), ("gauntlet_basket", 0.0, {}), ("chainmail_stand", 0.0, {}), ("armor_stand", 0.0, {"variant": "leather"}), ("plate_pile", 0.0, {}), ("boots_rack", 90.0, {})], (-6.6, 6.6), (3.4, 13.0), 6, 4)


def furnish_tavern(f) -> None:
    """Tavern and inn (18 m): inn reception by the door on the left and the stairs to the rooms at the back, big
    fireplace with a mounted head over the mantel on the left wall, L bar with kegs and bottles in the back right,
    a small stage on the right wall, long tables down the middle."""
    f.put("bar_counter_l", 4.6, 15.9)
    f.on_wall("back", "bottle_shelf", 5.4)
    f.on_wall("back", "keg_rack", 1.6)
    f.grid("bar_stool", (2.4, 6.6), (14.2, 14.2), 4, 1)
    f.put("mug_rail", 4.6, 15.9)
    f.on_wall("back", "kitchen_stove", -2.0)
    f.put("hanging_pots", -2.0, 18.0)
    f.put("garlic_strings", 0.2, 18.2)

    f.on_wall("left", "reception_desk", 5.5)
    f.on_wall("left", "luggage_pile", 7.6)
    f.on_wall("left", "fireplace", 9.7)
    f.on_wall("left", "mounted_head", 9.7, z=0.7)
    f.put("spit_roast", -6.6, 9.7, 90.0)
    f.put("armchair", -5.6, 8.0, -50.0)
    f.put("armchair", -5.6, 11.4, -130.0)
    f.put("stairs_straight", -7.75, 15.6)

    f.put("stage", 6.9, 9.7, -90.0)
    f.on_wall("right", "dart_board", 4.6)
    f.on_wall("right", "menu_board", 12.6)
    f.put("tavern_table_set", 0.0, 5.6)
    f.put("tavern_table_set", 0.0, 9.7)
    f.put("round_table_set", 5.6, 4.4)
    f.put("round_table_set", -4.6, 13.8)
    f.put("barrel_table", 0.4, 13.2)
    f.grid("wheel_chandelier", (-4.6, 4.6), (5.0, 11.6), 2, 2)
    f.scatter([("tavern_table_set", 0.0, {}), ("round_table_set", 0.0, {}), ("barrel_table", 0.0, {}), ("tavern_table_set", 90.0, {})], (-6.4, 6.4), (3.6, 12.6), 5, 4)
    f.scatter([("barrel_table", 0.0, {}), ("round_table_set", 0.0, {}), ("barrel_group", 0.0, {}), ("plant_pot", 0.0, {"variant": "fern"})], (-7.2, 7.2), (3.0, 13.4), 7, 6, aisle=0.55)


def furnish_school(f) -> None:
    """School (30 m): the master's desk and boards at the back, rows of long desks with benches facing them, maps,
    globes and bookshelves on the walls, a reading corner by the windows."""
    f.put("lectern", 0.0, 15.2)
    f.on_wall("back", "world_map_wall", 0.0)
    f.wall("back", ["recipe_board", "recipe_board", 4.4, "recipe_board", "recipe_board"], start=-4.6, gap=0.5)
    f.on_wall("back", "tall_bookcase", -9.7)
    f.on_wall("back", "tall_bookcase", 9.7)
    f.on_wall("back", "scroll_rack", -12.6)
    f.on_wall("back", "scroll_rack", 12.6)
    f.put("globe_stand", -3.2, 15.6)
    f.put("celestial_globe", 3.2, 15.6)
    f.wall("left", [("wall_shelf", {"variant": "books"}), "notice_board", ("wall_shelf", {"variant": "scrolls"}), "map_table", ("wall_shelf", {"variant": "books"})], start=3.0, gap=0.9)
    f.wall("right", [("wall_shelf", {"variant": "books"}), "astrolabe", ("wall_shelf", {"variant": "boxes"}), "book_cart", ("wall_shelf", {"variant": "scrolls"})], start=3.0, gap=0.9)
    f.scatter([("reading_table", 0.0, {})], (-11.6, 11.6), (5.4, 11.8), 7, 3, aisle=0.7)
    f.scatter([("bench_long", 0.0, {})], (-11.6, 11.6), (4.5, 10.9), 7, 3, aisle=0.02)
    f.grid("wheel_chandelier", (-9.0, 9.0), (5.0, 13.0), 3, 2)


def furnish_seminary(f) -> None:
    """Seminary (30 m): a study chapel in the middle (lectern, rows of benches), the refectory on the left, the
    dormitory on the right, books and candles along the walls."""
    f.put("lectern", 0.0, 15.4)
    f.on_wall("back", "star_tapestry", 0.0)
    f.on_wall("back", "tall_bookcase", -1.95)
    f.on_wall("back", "tall_bookcase", 1.95)
    f.grid("bench_long", (-1.2, 1.2), (5.0, 12.2), 2, 5)
    f.put("rug", 0.0, 13.8, variant="red")

    f.grid("tavern_table_set", (-11.4, -6.6), (5.0, 12.4), 2, 3, 90.0)
    f.on_wall("left", "fireplace", 9.7)
    f.on_wall("back", "kitchen_stove", -11.6)
    f.on_wall("back", "plate_rack", -9.4)
    f.on_wall("back", "bread_rack", -7.2)
    f.put("barrel_group", -13.4, 16.6)

    f.grid("bed_single", (6.2, 12.2), (16.6, 16.6), 4, 1)
    f.grid("bed_single", (6.2, 12.2), (5.6, 5.6), 4, 1, 180.0)
    f.grid("nightstand", (7.2, 11.2), (17.8, 17.8), 3, 1)
    f.wall("right", ["wardrobe", "washstand", "wardrobe", ("wall_shelf", {"variant": "books"}), "wardrobe"], start=7.6, gap=0.7)
    f.put("reading_table", 8.6, 11.0)
    f.put("chest_gold", 13.4, 4.0)
    f.grid("wheel_chandelier", (-9.0, 9.0), (5.0, 13.0), 3, 2)


SHELF_PAIR_OFFSET = 0.25  # half the depth of a floor_shelf: two of them stand back to back


def side_wall(f, side: str, tall: list, low: list, start: float = None, gap: float = 0.35) -> None:
    """Tall furniture against a blind side wall, low goods under the windows of an exposed one."""
    items = low if side in f.room.exposed else tall

    f.wall(side, items, start=start, gap=gap)


def window_wall(f, side: str, pier_rows: list, sill_items: list, gap: float = 0.3) -> None:
    """A wall with windows: each row of tall props centred on the next pier between windows (an empty row skips
    that pier), each low prop centred under the next window (None skips that window)."""
    for (pier_from, pier_to), row in zip(f.piers(side), pier_rows):
        f.wall(side, row, start=(pier_from + pier_to - f.row_length(row, gap)) / 2.0, gap=gap)

    for (window_from, window_to, _), item in zip(f.windows[side], sill_items):
        if item is None:
            continue

        name, options = (item, {}) if isinstance(item, str) else item
        f.on_wall(side, name, (window_from + window_to) / 2.0, **options)


def shelf_island(f, u: float, d: float, variants: tuple) -> None:
    """Two floor shelves back to back across the aisle, one facing each side."""
    f.put("floor_shelf", u - SHELF_PAIR_OFFSET, d, -90.0, variant=variants[0])
    f.put("floor_shelf", u + SHELF_PAIR_OFFSET, d, 90.0, variant=variants[1])


def furnish_magic(f) -> None:
    """Magic shop: a summoning circle under floating books in the middle of the nave, bookcases with a rolling
    ladder and staff racks on the walls, wands and crystal balls in the windows, a glass counter, and the
    enchanter's corner (enchanting table between rune pillars) at the back right."""
    f.put("rug", 0.0, 5.0, variant="blue")
    f.put("crystal_ball_pedestal", 0.0, 5.4)
    f.put("summoning_circle", 0.0, 9.7)
    f.put("floating_books", 0.0, 9.7)
    f.put("counter_glass", 0.0, 14.2)
    f.put("price_board", 1.9, 14.2)
    f.put("stool_round", 0.9, 16.0)

    f.on_wall("back", "tall_bookcase", -7.4)
    f.on_wall("back", "staff_rack", -4.6)
    f.on_wall("back", "wand_case", -2.3)
    f.on_wall("back", "star_tapestry", 0.0)
    f.on_wall("back", "mage_hat_stand", 2.0)
    f.on_wall("back", "tall_bookcase", 7.4)
    f.put("lectern", -5.6, 16.6)
    f.put("chest_gold", -2.6, 17.4)

    f.put("rug", 5.8, 16.0, variant="blue")
    f.put("enchant_table", 5.8, 16.0)
    f.put("rune_pillar", 3.6, 16.8)
    f.put("rune_pillar", 7.6, 14.6)
    f.put("giant_hourglass", 3.8, 14.9)

    side_wall(f, "left", ["tall_bookcase", "staff_rack", "tall_bookcase", "wand_case", "tall_bookcase", "mage_hat_stand", "tall_bookcase"], ["wand_case", "mana_crystal_crate", ("glowing_jar", {"variant": "cyan"}), "crystal_ball_pedestal", "wand_case", ("plant_pot", {"variant": "fern"})], start=0.8)
    side_wall(f, "right", [("wall_shelf", {"variant": "crystals"}), "tall_bookcase", "scroll_rack", ("wall_shelf", {"variant": "potions"}), "tall_bookcase", "skeleton_stand"], ["mana_crystal_crate", ("glowing_jar", {"variant": "pink"}), "wand_case", "crystal_ball_pedestal", "mana_crystal_crate"], start=0.8)
    if "left" not in f.room.exposed:
        f.put("rolling_ladder", f.left + 0.8, 1.8, 90.0)
    if "right" not in f.room.exposed:
        f.put("rolling_ladder", f.right - 0.8, 4.8, -90.0)

    f.wall("front", ["wand_case", ("glowing_jar", {"variant": "green"}), "crystal_ball_pedestal", "wand_case", ("glowing_jar", {"variant": "amber"})], start=f.left + 1.2)
    f.wall("front", [("glowing_jar", {"variant": "pink"}), "wand_case", "crystal_ball_pedestal", ("glowing_jar", {"variant": "cyan"}), "wand_case"], start=f.door_u + 2.0)

    f.put("celestial_globe", -5.7, 4.6)
    shelf_island(f, -5.7, 9.7, ("crystals", "potions"))
    f.put("giant_hourglass", -5.7, 12.4)
    f.put("astrolabe", 5.7, 4.6)
    shelf_island(f, 5.7, 9.7, ("scrolls", "books"))
    f.put("mana_crystal_crate", 5.7, 12.4)

    f.grid("wheel_chandelier", (-5.7, 5.7), (5.0, 12.4), 2, 2)
    f.grid("hanging_lantern", (-1.8, 1.8), (2.0, 2.0), 2, 1)


def furnish_alchemy(f) -> None:
    """Alchemist: a big bubbling cauldron in the middle, potion walls and an alembic bench at the back, mortar and
    glowing jars on the right, and the herb wing down the left (drying racks, seed drawers, planters under
    hanging plants, baskets of herbs and mushrooms)."""
    f.put("rug", 0.0, 5.2, variant="green")
    f.put("big_cauldron", 0.0, 9.7)
    f.put("counter_glass", 0.0, 14.2)
    f.put("price_board", 1.9, 14.2)
    f.put("stool_round", 0.9, 16.0)

    f.on_wall("back", "seed_drawers", -7.3)
    f.on_wall("back", "potion_wall", -2.85)
    f.on_wall("back", "potion_wall", 0.0)
    f.on_wall("back", "alembic_table", 3.4)
    f.on_wall("back", "potion_wall", 6.8)
    f.put("mortar_table", -2.6, 17.0)

    side_wall(f, "left", ["drying_rack_herbs", ("wicker_basket", {"variant": "herbs"}), "drying_rack_herbs", ("wicker_basket", {"variant": "mushrooms"}), "seed_drawers", "drying_rack_herbs", ("plant_pot", {"variant": "fern"})], ["planter_box", ("wicker_basket", {"variant": "herbs"}), "planter_box", ("wicker_basket", {"variant": "mushrooms"}), "planter_box", ("plant_pot", {"variant": "flower"})], start=0.8, gap=0.5)
    f.grid("planter_box", (-5.7, -5.7), (4.6, 11.8), 1, 3, 90.0)
    f.grid("hanging_plants", (-5.7, -5.7), (4.6, 11.8), 1, 3)
    f.put("herb_bundles", -5.7, 16.0)
    f.put("wicker_basket", -4.2, 16.4, variant="herbs")

    side_wall(f, "right", [("wall_shelf", {"variant": "potions"}), "potion_wall", ("wall_shelf", {"variant": "jars"}), "recipe_board", ("wall_shelf", {"variant": "bottles"}), "skeleton_stand"], [("crate_open", {"variant": "bottles"}), ("glowing_jar", {"variant": "green"}), ("crate_open", {"variant": "roots"}), "barrel_group", ("wicker_basket", {"variant": "mushrooms"})], start=0.8, gap=0.4)
    f.put("mortar_table", 5.7, 4.6, -90.0)
    f.put("alembic_table", 5.7, 8.6, -90.0)
    f.put("glowing_jar", 4.9, 11.6, variant="green")
    f.put("glowing_jar", 5.7, 11.9, variant="cyan")
    f.put("glowing_jar", 6.5, 11.6, variant="pink")
    f.put("slime_jar", 5.7, 12.7)

    f.wall("front", ["flower_steps", ("wicker_basket", {"variant": "herbs"}), "watering_cans", ("plant_pot", {"variant": "flower"})], start=f.left + 1.2)
    f.wall("front", ["slime_jar", ("glowing_jar", {"variant": "pink"}), ("crate_open", {"variant": "bottles"}), ("glowing_jar", {"variant": "cyan"})], start=f.door_u + 2.0)

    f.grid("wheel_chandelier", (-1.6, 1.6), (6.4, 12.6), 2, 2)
    f.put("hanging_lantern", 5.7, 6.6)


def furnish_tailor(f) -> None:
    """Tailor: dress forms in a ring on a rug in the middle, fabric shelves, clothes rails and hat shelves on the
    walls, a fitting booth and a mirror by the counter, the cutting table, spinning wheel and loom at the back, and
    the jewel wing by the left window (glass cases, necklace busts, the goldsmith's bench and a safe)."""
    f.put("rug", 0.0, 9.7, variant="red")
    f.put("dress_form", -1.3, 8.6, variant="dress")
    f.put("dress_form", 1.3, 8.6, variant="gown")
    f.put("dress_form", -1.3, 10.8, variant="cloak")
    f.put("dress_form", 1.3, 10.8, variant="dress")
    f.put("counter_straight", 0.0, 14.2)
    f.put("stool_round", 0.9, 16.0)
    f.put("fitting_platform", 5.6, 14.6)
    f.put("standing_mirror", 7.5, 14.6, -90.0)

    window_wall(f, "back", [["fabric_shelf"], ["fabric_shelf", 1.0, "wall_banner", 1.0, "fabric_shelf"], ["fitting_booth"]], ["hat_shelf", "hat_shelf"])
    f.put("cutting_table", -4.8, 16.4)
    f.put("chair", -4.8, 17.4)
    f.on_wall("left", "spinning_wheel", 17.6)

    f.on_wall("left", "iron_safe", 0.9)
    f.on_wall("left", "goldsmith_bench", 2.6)
    f.grid("jewel_case", (-5.4, -5.4), (2.6, 5.0), 1, 2, 90.0)
    f.put("jewel_case", -3.9, 1.4)
    f.put("rug", -6.6, 3.8, 90.0, variant="gold")
    side_wall(f, "left", ["fabric_shelf", "clothes_rail", ("wall_shelf", {"variant": "shoes"}), "clothes_rail", "hat_shelf"], ["yarn_basket", ("crate_open", {"variant": "cloth"}), ("dress_form", {"variant": "gown"}), "yarn_basket", ("crate_open", {"variant": "cloth"})], start=6.6)

    window_wall(f, "right", [[("crate_open", {"variant": "cloth"}), ("dress_form", {"variant": "dress"})], [("dress_form", {"variant": "cloak"}), ("plant_pot", {"variant": "flower"})], ["clothes_rail"]], ["yarn_basket", "spinning_wheel", ("crate_open", {"variant": "cloth"}), None])

    f.wall("front", ["necklace_busts", ("plant_pot", {"variant": "flower"}), "necklace_busts"], start=f.left + 1.2)
    f.wall("front", [("dress_form", {"variant": "gown"}), ("crate_open", {"variant": "cloth"}), ("dress_form", {"variant": "dress"}), "yarn_basket"], start=f.door_u + 2.0, gap=0.5)

    f.put("display_table", -5.7, 9.7, variant="cloth")
    f.put("yarn_basket", -5.7, 11.4)
    f.put("clothes_rail", -5.7, 12.8, 90.0)
    shelf_island(f, 5.7, 5.0, ("cloth", "shoes"))
    shelf_island(f, 5.7, 9.7, ("cloth", "cloth"))

    f.grid("wheel_chandelier", (-5.7, 5.7), (5.0, 12.0), 2, 2)
    f.put("hanging_lantern", -5.4, 3.8)


def furnish_general(f) -> None:
    """General store: shelves of everything on every wall, gondolas down both aisles, produce tables in the middle,
    barrels, sacks and crates, a till counter with the pastry case beside it, and the bakery corner at the back
    right (stone oven, dough table, bread racks, flour sacks)."""
    f.put("rug", 0.0, 5.2, variant="gold")
    f.put("display_table", 0.0, 5.6, variant="fruit")
    f.put("display_table", 0.0, 9.7, variant="pottery")
    f.put("counter_till", -1.0, 14.2)
    f.put("pastry_case", 1.5, 14.2)
    f.put("cake_stand", 3.2, 15.2)
    f.put("stool_round", -0.2, 16.0)
    f.put("ceiling_beam_hooks", -1.0, 15.6, variant="sausages")

    window_wall(f, "back", [[("wall_shelf", {"variant": "jars"})], [("wall_shelf", {"variant": "bottles"}), ("wall_shelf", {"variant": "boxes"})]], [("crate_open", {"variant": "apples"})])
    f.on_wall("back", "bread_rack", 3.3)
    f.on_wall("back", "stone_oven", 5.6)
    f.put("dough_table", 5.4, 16.2)
    f.put("chest_gold", -5.6, 16.8)

    side_wall(f, "left", [("wall_shelf", {"variant": "jars"}), "sack_pile", "tool_rack", "crate_stack", "backpack_wall", "barrel_group", ("wall_shelf", {"variant": "boxes"}), "step_ladder"], ["sack_pile", ("crate_open", {"variant": "apples"}), "crate_stack", ("wicker_basket", {"variant": "fruit"}), "barrel_group", ("crate_open", {"variant": "roots"}), ("plant_pot", {"variant": "bush"})], start=0.8)
    side_wall(f, "right", [("wall_shelf", {"variant": "bottles"}), "crate_stack", ("wall_shelf", {"variant": "books"}), "barrel_group", ("wall_shelf", {"variant": "shoes"}), "flour_sacks", "jam_shelf", "bread_rack"], [("crate_open", {"variant": "ingots"}), "barrel_group", ("wicker_basket", {"variant": "wool"}), "crate_stack", ("crate_open", {"variant": "cloth"}), "flour_sacks", "jam_shelf"], start=0.8)

    f.wall("front", [("crate_open", {"variant": "apples"}), ("wicker_basket", {"variant": "fruit"}), ("crate_open", {"variant": "roots"}), ("wicker_basket", {"variant": "bread"}), ("plant_pot", {"variant": "bush"})], start=f.left + 1.2)
    f.wall("front", [("plant_pot", {"variant": "bush"}), "barrel_group", ("crate_open", {"variant": "cloth"}), ("wicker_basket", {"variant": "wool"})], start=f.door_u + 2.0)

    shelf_island(f, -5.7, 5.0, ("jars", "bottles"))
    shelf_island(f, -5.7, 9.7, ("tools", "boxes"))
    f.put("barrel_group", -5.7, 12.6)
    shelf_island(f, 5.7, 5.0, ("bread", "jars"))
    shelf_island(f, 5.7, 9.7, ("cloth", "shoes"))
    f.put("cafe_table_set", 5.7, 12.5)

    f.grid("wheel_chandelier", (-5.7, 5.7), (5.0, 11.4), 3, 2)
    f.grid("hanging_goods", (-5.7, 5.7), (7.35, 7.35), 2, 1)
    f.put("blanket_pile", -3.9, 17.6)
    f.put("cat_sleeping", 1.0, 12.4)
    f.grid("hanging_lantern", (-1.6, 1.6), (2.0, 2.0), 2, 1)


def furnish_library(f) -> None:
    """Public library: bookcases on every wall with rolling ladders, back-to-back stacks forming corridors in the
    side bays, a nave of reading tables, a map table under floating books on the axis, the librarian's counter
    before the back wall, a printing press in the back corner, scroll racks, book carts and a reading nook with
    armchairs by the front windows."""
    stack_rows = (5.4, 8.2, 11.0, 13.8)
    stack_u = 11.3

    f.put("rug", 0.0, 5.4, variant="red")
    f.put("globe_stand", -1.6, 5.0)
    f.put("lectern", 1.6, 5.0)
    f.put("rug", 0.0, 9.7, variant="red")
    f.put("map_table", 0.0, 9.7)
    f.put("floating_books", 0.0, 9.7)
    f.put("counter_straight", 0.0, 14.6)
    f.put("chair", 0.8, 16.4)
    f.put("book_cart", -2.2, 15.4)

    f.wall("back", ["tall_bookcase"] * 5, start=f.left + 0.5, gap=0.25)
    f.on_wall("back", "scroll_rack", -2.2)
    f.on_wall("back", "world_map_wall", 0.0)
    f.on_wall("back", "scroll_rack", 2.2)
    f.wall("back", ["tall_bookcase"] * 5, start=3.1, gap=0.25)
    f.put("rolling_ladder", -7.9, f.back - 0.8)
    f.put("rolling_ladder", 7.9, f.back - 0.8)
    f.put("printing_press", -11.8, 16.8, 90.0)
    f.put("crate_stack", -11.8, 15.0, 90.0)
    f.put("reading_table", 11.6, 16.6)
    f.grid("chair", (10.8, 12.4), (17.4, 17.4), 2, 1)

    side_wall(f, "left", ["tall_bookcase"] * 8, ["book_cart", "bench_long", ("plant_pot", {"variant": "fern"}), "book_cart", "bench_long", ("plant_pot", {"variant": "fern"})], start=0.6, gap=0.25)
    side_wall(f, "right", ["tall_bookcase"] * 8, ["book_cart", "bench_long", ("plant_pot", {"variant": "fern"}), "book_cart", "bench_long", ("plant_pot", {"variant": "fern"})], start=0.6, gap=0.25)
    if "left" not in f.room.exposed:
        f.put("rolling_ladder", f.left + 0.8, 16.2, 90.0)
    if "right" not in f.room.exposed:
        f.put("rolling_ladder", f.right - 0.8, 16.2, -90.0)

    for row_d in stack_rows:
        f.put("tall_bookcase", -stack_u, row_d - 0.2)
        f.put("tall_bookcase", -stack_u, row_d + 0.2, 180.0)
        f.put("tall_bookcase", stack_u, row_d - 0.2)
        f.put("tall_bookcase", stack_u, row_d + 0.2, 180.0)

    f.grid("reading_table", (-5.94, 5.94), (4.6, 11.8), 2, 3)
    for table_u in (-5.94, 5.94):
        f.grid("chair", (table_u - 0.6, table_u + 0.6), (3.85, 11.05), 2, 3, 180.0)
        f.grid("chair", (table_u - 0.6, table_u + 0.6), (5.35, 12.55), 2, 3)

    f.wall("front", [("plant_pot", {"variant": "bush"}), "armchair", ("rug", {"variant": "green"}), "armchair", "lectern"], start=f.left + 0.6, gap=0.4)
    f.wall("front", ["lectern", "armchair", ("rug", {"variant": "green"}), "armchair", ("plant_pot", {"variant": "bush"})], start=f.door_u + 2.6, gap=0.4)
    f.put("book_cart", -5.94, 14.2)
    f.put("book_cart", 5.94, 14.2)

    f.grid("wheel_chandelier", (-5.94, 5.94), (5.4, 12.0), 3, 2)
    f.grid("hanging_lantern", (-stack_u, stack_u), (6.8, 12.4), 2, 2)


PLANS = {
    "school": dict(keeper=(0.0, 16.6), furnish=furnish_school),
    "seminary": dict(keeper=(0.0, 16.8), posts=((-4.4, 6.47), (4.4, 6.47), (-4.4, 12.93), (4.4, 12.93)), furnish=furnish_seminary),
    "guild": dict(keeper=(0.0, 17.3), furnish=furnish_guild),
    "smith": dict(keeper=(-5.0, 15.6), posts=((-8.4, 7.0), (-1.6, 7.0), (-8.4, 13.4), (-1.6, 13.4)), partitions=(("u", 3.1, 8.5, 19.1),), furnish=furnish_smith),
    "armor": dict(keeper=(0.0, 16.2), furnish=furnish_armor),
    "tavern": dict(keeper=(5.0, 17.6), furnish=furnish_tavern),
    "magic": dict(keeper=(0.0, 15.6), furnish=furnish_magic),
    "alchemy": dict(keeper=(0.0, 15.6), furnish=furnish_alchemy),
    "tailor": dict(keeper=(0.0, 15.6), furnish=furnish_tailor),
    "general": dict(keeper=(-1.0, 15.6), furnish=furnish_general),
    "library": dict(keeper=(0.0, 16.0), furnish=furnish_library),
}
FILL = {  # prédio -> ilhas soltas que enchem o chão livre dos dois lados do corredor da porta (fill_floor)
    "smith": [("armor_stand", 0.0, {"variant": "plate"}), ("crate_open", 0.0, {"variant": "ingots"}), ("weapon_barrel", 0.0, {}), ("plate_pile", 0.0, {}), ("gauntlet_basket", 0.0, {}), ("weapon_barrel", 0.0, {"seed": 2}), ("barrel_group", 0.0, {})],
    "armor": [("armor_stand", 0.0, {"variant": "plate"}), ("plate_pile", 0.0, {}), ("chainmail_stand", 0.0, {}), ("gauntlet_basket", 0.0, {}), ("armor_stand", 0.0, {"variant": "leather"}), ("boots_rack", 90.0, {}), ("standing_mirror", 0.0, {})],
    "magic": [("mana_crystal_crate", 0.0, {}), ("rune_pillar", 0.0, {}), ("wand_case", 90.0, {}), ("giant_hourglass", 0.0, {}), ("mage_hat_stand", 0.0, {}), ("celestial_globe", 0.0, {}), ("crystal_ball_pedestal", 0.0, {})],
    "alchemy": [("planter_box", 90.0, {}), ("glowing_jar", 0.0, {}), ("drying_rack_herbs", 90.0, {}), ("mortar_table", 90.0, {}), ("flower_steps", 0.0, {}), ("crate_open", 0.0, {"variant": "roots"}), ("skeleton_stand", 0.0, {}), ("barrel_group", 0.0, {})],
    "tailor": [("dress_form", 0.0, {}), ("clothes_rail", 90.0, {}), ("yarn_basket", 0.0, {}), ("necklace_busts", 90.0, {}), ("display_table", 0.0, {"variant": "cloth"}), ("blanket_pile", 0.0, {}), ("jewel_case", 90.0, {}), ("spinning_wheel", 90.0, {})],
    "general": [("display_table", 0.0, {"variant": "fruit"}), ("crate_open", 0.0, {"variant": "apples"}), ("barrel_group", 0.0, {}), ("sack_pile", 0.0, {}), ("display_table", 0.0, {"variant": "pottery"}), ("wicker_basket", 0.0, {}), ("cake_stand", 0.0, {}), ("crate_stack", 0.0, {})],
}
