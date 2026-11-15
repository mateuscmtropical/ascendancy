"""Floor plans of the market shops: what stands where in each hall (docs/research/shops.md).

Each plan is a function of a Furnisher (build_market_shops.py): f.put(prop, u, d, degrees), f.on_wall(side, prop,
along), f.wall(side, [props]), f.grid(prop, u range, d range, columns, rows). Coordinates in metres: u across the
facade (0 = middle of the lot, the hall goes from f.left to f.right), d into the lot (f.front at the door wall,
f.back at the far wall). Props turn their front to the street at 0 degrees; the wall helpers turn their backs to
the wall. PLANS also says where the shopkeeper stands and, when the default grid does not fit, the posts and the
inner walls ("u" | "d", fixed coordinate, from, to).
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
    """Adventurers' guild: nave from the portal to the three-wicket counter under the world map, quest board on the
    right wall, fireplace lounge and a small bar on the left, party tables between the columns, a dragon skull overhead."""
    f.put("rug", 0.0, 6.2, variant="red_large")
    f.put("registry_crystal", 0.0, 11.4)
    f.put("dragon_skull_hanging", 0.0, 8.0)
    f.put("guild_counter", 0.0, 15.7)
    f.on_wall("back", "world_map_wall", 0.0)
    f.on_wall("back", "guild_banner", -3.4)
    f.on_wall("back", "guild_banner", 3.4)
    f.on_wall("back", "rank_board", 6.4)
    f.on_wall("back", "monster_trophy", -6.4, variant="horns")
    f.on_wall("back", "trophy_case", 10.6)
    f.on_wall("back", "weapon_rental_rack", 13.2)

    f.on_wall("right", "notice_board", 4.2)
    f.on_wall("right", "quest_board", 8.2)
    f.on_wall("right", "wanted_posters", 11.6)
    f.on_wall("right", "monster_trophy", 14.6, variant="skull")
    f.put("bench_long", 11.2, 6.5, 90.0)
    f.put("bench_long", 11.2, 10.0, 90.0)
    f.on_wall("right", "plant_pot", 16.6, variant="fern")

    f.on_wall("left", "fireplace", 9.7)
    f.on_wall("left", "monster_trophy", 5.6, variant="claw")
    f.put("armchair", -11.4, 7.9, -60.0)
    f.put("armchair", -11.4, 11.5, -120.0)
    f.put("rug", -11.8, 9.7, 90.0, variant="fur")
    f.put("bar_counter_l", -11.0, 16.0)
    f.on_wall("back", "bottle_shelf", -11.6)
    f.on_wall("back", "keg_rack", -8.4)
    f.grid("bar_stool", (-12.6, -9.8), (14.6, 14.6), 3, 1)

    f.grid("group_table", (-5.9, 5.9), (3.9, 9.7), 2, 2)
    f.put("group_table", 5.9, 13.6)
    f.put("group_table", -5.9, 13.2)
    f.on_wall("front", "armor_stand", -3.4, variant="knight_gold")
    f.on_wall("front", "armor_stand", 3.4, variant="plate")
    f.on_wall("front", "plant_pot", -13.6, variant="bush")
    f.on_wall("front", "plant_pot", 13.6, variant="bush")
    f.grid("wheel_chandelier", (-8.9, 8.9), (4.5, 14.5), 2, 2)


def furnish_smith(f) -> None:
    """Blacksmith: sales hall on the left (weapons on every wall, counter at the back), forge yard on the right, open
    to the street: forge and bellows at the back wall, anvil, quench barrel and grindstone around it."""
    f.put("counter_till", -6.0, 14.0)
    f.put("rug", -6.0, 11.6, variant="fur")
    f.wall("back", ["shield_wall", "axe_mace_rack", ("sword_wall", {"seed": 2}), "spear_rack", "helmet_shelf", "giant_sword", "tool_wall_rack", "spear_rack"], start=-14.2, gap=0.45)
    f.wall("left", [("armor_stand", {"variant": "plate"}), ("armor_stand", {"variant": "mail"}), ("wall_shelf", {"variant": "helmets"}), "sword_wall", "boots_rack", "crate_stack"], start=3.6, gap=0.6)
    f.put("display_table", -10.6, 5.2, variant="tools")
    f.put("display_table", -1.4, 5.2, variant="helmets")
    f.put("floor_shelf", -6.0, 8.2, variant="tools")
    f.put("ingot_crates", 3.6, 3.0, -90.0)
    f.put("blade_shelf", 5.0, 11.5, -90.0)
    f.put("spear_rack", 5.2, 14.5, -90.0)
    f.put("plans_table", 2.6, 16.6, -90.0)
    f.put("barrel_group", 1.6, 9.0)
    f.grid("wheel_chandelier", (-10.5, -1.5), (5.5, 12.0), 2, 2)

    f.on_wall("back", "forge", 11.8)
    f.put("bellows", 9.6, 17.6, -20.0)
    f.put("anvil_block", 10.4, 14.2, 30.0)
    f.put("quench_barrel", 12.6, 13.6)
    f.put("grindstone", 7.8, 11.8, 90.0)
    f.on_wall("right", "coal_pile", 16.6)
    f.on_wall("right", "tool_wall_rack", 12.6)
    f.on_wall("right", "ingot_crates", 8.6)
    f.put("plans_table", 6.6, 15.6, 90.0)
    f.put("blade_shelf", 6.0, 10.0, 90.0)
    f.put("barrel_group", 13.6, 4.2)
    f.put("crate_stack", 6.8, 5.6)
    f.put("ceiling_beam_hooks", 10.2, 12.0)
    f.put("hanging_lantern", 10.2, 7.0)


def furnish_armor(f) -> None:
    """Armourer: showroom of mannequins along both walls and on the floor, a fitting platform with a mirror in the
    middle, shields and helmets behind the counter, a small plate workshop in the back corner."""
    f.put("counter_straight", 0.0, 14.7)
    f.put("rug", 0.0, 5.6, variant="red_large")
    f.put("fitting_platform", 0.0, 9.6)
    f.put("standing_mirror", 1.7, 11.2, 30.0)
    f.on_wall("back", "shield_wall", 0.0)
    f.on_wall("back", "helmet_shelf", -3.6)
    f.on_wall("back", "helmet_shelf", 3.6)
    f.on_wall("back", "guild_banner", 6.6, tint="7A2F3A")
    f.wall("left", [("armor_stand", {"variant": "plate"}), ("armor_stand", {"variant": "knight_gold"}), ("armor_stand", {"variant": "mail"}), ("armor_stand", {"variant": "leather"}), "boots_rack", "chainmail_stand"], start=3.4, gap=0.9)
    f.wall("right", [("wall_shelf", {"variant": "helmets"}), ("armor_stand", {"variant": "leather"}), "shield_wall", "gauntlet_basket", ("armor_stand", {"variant": "plate"}), "plate_pile", "crate_stack"], start=3.4, gap=0.6)
    f.grid("armor_stand", (-5.6, 5.6), (5.6, 11.6), 2, 2, variant="knight_gold")
    f.put("display_table", -5.6, 8.6, variant="helmets")
    f.put("display_table", 5.6, 8.6, variant="boxes")
    f.put("anvil_block", -6.4, 17.2, 20.0)
    f.put("plans_table", -6.8, 14.8, 90.0)
    f.grid("wheel_chandelier", (0.0, 0.0), (5.0, 12.5), 1, 2)


def furnish_tavern(f) -> None:
    """Tavern: L bar with kegs and bottles in the back right corner, big fireplace on the left wall, a stage in the
    back left corner, long tables between the posts and round tables along the windows."""
    f.put("bar_counter_l", 9.6, 15.9)
    f.on_wall("back", "bottle_shelf", 10.6)
    f.on_wall("back", "keg_rack", 6.6)
    f.on_wall("back", "keg_rack", 13.3)
    f.grid("bar_stool", (7.2, 12.0), (14.5, 14.5), 5, 1)
    f.put("mug_rail", 9.6, 15.9)
    f.on_wall("back", "kitchen_stove", 1.6)
    f.on_wall("back", "plate_rack", -1.2)
    f.put("stew_pot", -12.6, 9.7)

    f.on_wall("left", "fireplace", 9.7)
    f.on_wall("left", "mounted_head", 5.4)
    f.on_wall("left", "mounted_head", 14.0)
    f.put("rug", -11.6, 9.7, 90.0, variant="fur")
    f.put("armchair", -11.2, 7.6, -50.0)
    f.put("armchair", -11.2, 11.8, -130.0)
    f.put("stage", -11.6, 17.4)
    f.put("bench_long", -11.6, 14.9)

    f.grid("tavern_table_set", (-5.9, 5.9), (4.4, 9.7), 3, 2)
    f.put("round_table_set", -11.8, 4.2)
    f.put("round_table_set", 11.8, 4.2)
    f.put("round_table_set", 11.8, 9.2)
    f.put("round_table_set", -5.6, 14.6)
    f.put("barrel_table", 0.0, 13.6)
    f.put("barrel_table", 4.4, 12.2)
    f.on_wall("right", "dart_board", 6.6)
    f.on_wall("right", "menu_board", 12.0)
    f.on_wall("right", "notice_board", 15.2)
    f.put("barrel_group", 13.6, 18.0)
    f.grid("wheel_chandelier", (-8.9, 8.9), (4.6, 11.4), 3, 2)
    f.put("hanging_pots", 1.6, 17.6)
    f.put("garlic_strings", -1.4, 17.8)


PLANS = {
    "guild": dict(keeper=(0.0, 17.3), furnish=furnish_guild),
    "smith": dict(keeper=(-6.0, 15.6), posts=((-9.5, 7.0), (-2.5, 7.0), (-9.5, 13.4), (-2.5, 13.4)), partitions=(("u", 5.6, 8.5, 19.1),), furnish=furnish_smith),
    "armor": dict(keeper=(0.0, 16.2), furnish=furnish_armor),
    "tavern": dict(keeper=(10.0, 17.6), furnish=furnish_tavern),
}

try:
    from shop_layouts_more import PLANS as MORE_PLANS

    PLANS.update(MORE_PLANS)
except ImportError:
    pass
