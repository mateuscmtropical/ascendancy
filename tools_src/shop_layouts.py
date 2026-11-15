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
    f.put("chest_gold", 10.8, 18.2)

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


def furnish_smith(f) -> None:
    """Blacksmith (24 m): sales hall on the left (weapons on every wall, counter at the back), forge yard on the
    right, open to the street: forge and bellows at the back wall, anvil, quench barrel and grindstone around it."""
    f.put("counter_till", -5.0, 14.0)
    f.put("rug", -5.0, 11.4, variant="gold")
    f.wall("back", ["shield_wall", "axe_mace_rack", ("sword_wall", {"seed": 2}), "spear_rack", "helmet_shelf", "giant_sword"], start=-11.3, gap=0.4)
    f.wall("left", [("armor_stand", {"variant": "plate"}), ("armor_stand", {"variant": "mail"}), ("wall_shelf", {"variant": "helmets"}), "sword_wall", "boots_rack", "crate_stack"], start=3.6, gap=0.6)
    f.put("floor_shelf", -8.4, 9.6, 90.0, variant="tools")
    f.put("floor_shelf", -1.6, 9.6, 90.0, variant="helmets")
    f.put("ingot_crates", 0.8, 4.2)
    f.put("blade_shelf", 2.6, 11.4, -90.0)
    f.put("spear_rack", 2.7, 14.4, -90.0)
    f.put("plans_table", 1.6, 17.2, -90.0)
    f.grid("wheel_chandelier", (-8.4, -1.6), (5.0, 12.0), 2, 2)

    f.on_wall("back", "forge", 8.2)
    f.put("bellows", 6.0, 17.5, -20.0)
    f.put("anvil_block", 6.8, 14.0, 30.0)
    f.put("quench_barrel", 9.4, 13.4)
    f.put("grindstone", 5.2, 10.8, 90.0)
    f.on_wall("right", "coal_pile", 16.8)
    f.on_wall("right", "tool_wall_rack", 12.6)
    f.on_wall("right", "ingot_crates", 8.4)
    f.put("plans_table", 3.9, 15.6, 90.0)
    f.put("blade_shelf", 3.6, 12.2, 90.0)
    f.put("barrel_group", 10.4, 4.6)
    f.put("crate_stack", 10.6, 6.6)
    f.put("ceiling_beam_hooks", 7.4, 11.8)
    f.put("hanging_lantern", 7.4, 6.5)


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
    f.wall("left", [("armor_stand", {"variant": "plate"}), ("armor_stand", {"variant": "knight_gold"}), ("armor_stand", {"variant": "mail"}), ("armor_stand", {"variant": "leather"}), "boots_rack", "chainmail_stand"], start=3.4, gap=0.9)
    f.wall("right", [("wall_shelf", {"variant": "helmets"}), ("armor_stand", {"variant": "leather"}), "shield_wall", "gauntlet_basket", ("armor_stand", {"variant": "plate"}), "plate_pile", "crate_stack"], start=3.4, gap=0.6)
    f.grid("armor_stand", (-5.6, 5.6), (5.6, 11.6), 2, 2, variant="knight_gold")
    f.put("floor_shelf", -5.6, 8.6, 90.0, variant="helmets")
    f.put("floor_shelf", 5.6, 8.6, 90.0, variant="shoes")
    f.put("anvil_block", -6.4, 17.2, 20.0)
    f.put("plans_table", -6.8, 14.8, 90.0)
    f.grid("wheel_chandelier", (0.0, 0.0), (5.0, 12.5), 1, 2)


def furnish_tavern(f) -> None:
    """Tavern and inn (18 m): inn reception by the door on the left and the stairs to the rooms at the back, big
    fireplace on the left wall, L bar with kegs and bottles in the back right, a small stage on the right wall,
    long tables down the middle."""
    f.put("bar_counter_l", 4.6, 15.9)
    f.on_wall("back", "bottle_shelf", 5.4)
    f.on_wall("back", "keg_rack", 1.6)
    f.grid("bar_stool", (2.4, 6.6), (14.6, 14.6), 4, 1)
    f.put("mug_rail", 4.6, 15.9)
    f.on_wall("back", "kitchen_stove", -2.0)
    f.put("hanging_pots", -2.0, 18.0)
    f.put("garlic_strings", 0.2, 18.2)

    f.on_wall("left", "reception_desk", 4.4)
    f.put("luggage_pile", -7.6, 6.6)
    f.on_wall("left", "fireplace", 9.7)
    f.put("stew_pot", -7.2, 9.7)
    f.put("armchair", -5.6, 8.0, -50.0)
    f.put("armchair", -5.6, 11.4, -130.0)
    f.put("stairs_straight", -7.75, 15.6)
    f.on_wall("left", "mounted_head", 12.2)

    f.put("stage", 6.9, 9.7, -90.0)
    f.on_wall("right", "dart_board", 4.6)
    f.on_wall("right", "menu_board", 12.6)
    f.put("tavern_table_set", 0.0, 5.6)
    f.put("tavern_table_set", 0.0, 9.7)
    f.put("round_table_set", 5.6, 4.4)
    f.put("round_table_set", -4.6, 13.8)
    f.put("barrel_table", 0.4, 13.2)
    f.grid("wheel_chandelier", (-4.6, 4.6), (5.0, 11.6), 2, 2)


PLANS = {
    "guild": dict(keeper=(0.0, 17.3), furnish=furnish_guild),
    "smith": dict(keeper=(-5.0, 15.6), posts=((-8.4, 7.0), (-1.6, 7.0), (-8.4, 13.4), (-1.6, 13.4)), partitions=(("u", 3.1, 8.5, 19.1),), furnish=furnish_smith),
    "armor": dict(keeper=(0.0, 16.2), furnish=furnish_armor),
    "tavern": dict(keeper=(5.0, 17.6), furnish=furnish_tavern),
}

try:
    from shop_layouts_more import PLANS as MORE_PLANS

    PLANS.update(MORE_PLANS)
except ImportError:
    pass
