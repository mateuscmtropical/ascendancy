# Credits

| Asset / library | Author | License | Source |
|---|---|---|---|
| GUT (Godot Unit Test) 9.7.1 | Butch Wesley and contributors | MIT | https://github.com/bitwes/Gut |
| Universal Base Characters | Quaternius | CC0 1.0 | https://quaternius.itch.io/universal-base-characters |
| Modular Character Outfits – Fantasy | Quaternius | CC0 1.0 | https://quaternius.itch.io/modular-character-outfits-fantasy |
| Universal Animation Library 1 & 2 | Quaternius | CC0 1.0 | https://quaternius.itch.io/universal-animation-library |
| Stylized Nature MegaKit | Quaternius | CC0 1.0 | https://quaternius.itch.io/stylized-nature-megakit |
| Medieval Village MegaKit | Quaternius | CC0 1.0 | https://quaternius.itch.io/medieval-village-megakit |
| Fantasy Props MegaKit | Quaternius | CC0 1.0 | https://quaternius.itch.io/fantasy-props-megakit |
| KayKit Character Animations | Kay Lousberg | CC0 1.0 | https://kaylousberg.itch.io/kaykit-character-animations |
| Farm Animals Animated (cow, pig, horse) | Quaternius | CC0 1.0 | https://quaternius.itch.io/lowpoly-animated-animals |

CC0 verified from the License.txt inside each downloaded zip (2026-11-14); the Farm Animals pack has no license file, its itch page states CC0 (checked 2026-11-15). The cow, pig and horse in `art/town/farm/animals` are converted from it (scale, heading, animation names) by `tools_src/convert_farm_animals.py`. Characters in `art/characters` are assembled from these packs by `tools_src/build_characters.py`. The stone figures (cathedral saints, fountain water bearers) are those same CC0 characters posed and dressed by `tools_src/build_cathedral.py` / `build_plaza_props.py`. Ground, coreto, fountains, palms, shop dressings and the cathedral are modelled from primitives by the scripts in `tools_src/` (original work, MIT like the rest of the code); their textures are generated or tinted from the Medieval Village MegaKit textures. The farm (farmhouse, barn, yard, fields, crops, wagons in `art/town/farm`) is modelled from primitives by `tools_src/build_farm.py`.

## Reference data

Map data © OpenStreetMap contributors, available under the Open Database License (ODbL 1.0): https://www.openstreetmap.org/copyright. No map data is shipped; the layout is hand-built in `tools_src/build_hub_scene.py`.
