# Asset & license research (2026-11-14)

Verified = page fetched directly. Unverified = search snippet only. Re-check license page before importing anything.

## 1. Mixamo — do NOT commit raw files
- Official FAQ (helpx.adobe.com/creative-cloud/faq/mixamo-faq.html) returned 403; quotes below are secondhand from Adobe community post reproducing FAQ (2022): https://community.adobe.com/t5/mixamo-discussions/mixamo-faq-licensing-royalties-ownership-eula-and-tos/td-p/13234775
  - "really the only thing you can't do is distribute the raw character and animation files."
  - NO: "Blueprints, templates, or asset packages for video game engines which redistribute character or animation raw files"; "Any type of free distribution of character or animation raw files".
  - YES: games (paid or free), "DLC or Addon Content for Games".
- Conclusion: shipping inside built game OK; raw .fbx in public GitHub repo = free distribution of raw files → not allowed. Not used.

## 2. Humanoid animations (CC0)
- Quaternius Universal Animation Library 1 — https://quaternius.com/packs/universalanimationlibrary.html — CC0, 120+ anims (8-dir locomotion, jog, sprint, sit, death, combat, emotes), humanoid rig, glTF. Free tier ~60-70%. Reviewer: UpperChest bends too much.
- Quaternius UAL 2 — https://quaternius.com/packs/universalanimationlibrary2.html — CC0, 130+ (melee 3/4-hit combos, armed combat, parkour, fishing).
- KayKit Character Animations — https://kaylousberg.itch.io/kaykit-character-animations — CC0, 150+ free (movement, melee, ranged, tools). glTF.
- Rokoko free packs — commercial use allowed per page; license page not checked.
- CMU mocap — official terms not retrieved; avoid 4TU FBX conversion (CC BY-NC).
- Godot retarget: SkeletonProfileHumanoid + BoneMap (docs.godotengine.org/en/4.7/tutorials/assets_pipeline/retargeting_3d_skeletons.html).
- Gap: no "talk" anim → blend shapes / hand-made loop.

## 3. Anime characters
- VRoid Studio guidelines (https://vroid.com/en/studio/guidelines, via snippets): meshes/textures/presets from VRoid may be used commercially; can't build an app that generates models from VRoid parts.
- VRM Public License 1.0 (https://vrm.dev/en/licenses/1.0/index, verified): redistribution only if model's License Settings allow it. We author our own avatars → set redistribution allowed.
- godot-vrm (https://github.com/V-Sekai/godot-vrm) MIT, Godot 4.1+, VRM 1.0 import + MToon shader. Sample VRMs have separate license — don't copy.
- CC0 fallbacks: Quaternius Universal Base Characters (https://quaternius.com/packs/universalbasecharacters.html), KayKit Adventurers.

## 4. Environment (CC0)
- Quaternius Medieval Village MEGAKIT — https://quaternius.com/packs/medievalvillagemegakit.html — 304 modular models (walls, roofs, doors, windows, stairs). No cathedral/fountain/bench/lamp.
- Quaternius Stylized Nature MegaKit — https://quaternius.com/packs/stylizednaturemegakit.html — 116 (40 trees, 35 plants, 27 rocks), Ghibli-like.
- Kenney Fantasy Town Kit — https://kenney.nl/assets/fantasy-town-kit — 160 files.
- Modular Cathedral Kit — https://sigilsvault.itch.io/modular-cathedral-kit — CC0, 40+ pieces, PS2-era low-poly.
- Poly Haven — https://polyhaven.com/license — CC0 textures + HDRIs. ambientCG (CC0) not checked.
- Unverified: Tiny Treats Pretty Park (fountain), OpenGameArt park props (mixed CC-BY/CC0).

## 5. Toon shading (Godot 4)
- MToon via godot-vrm (MIT) for characters.
- eldskald Complete Cel Shader — https://github.com/eldskald/godot4-cel-shader — MIT, outline next_pass.
- godotshaders.com water/sky/grass: check each license individually.

## 6. Recommendation
- Characters: own VRoid avatars (VRM, redistribution allowed) + godot-vrm/MToon; fallback Quaternius base characters.
- Animations: UAL1 + UAL2 free + KayKit anims (CC0) retargeted to SkeletonProfileHumanoid. No Mixamo.
- Environment: Quaternius/Kenney kits as filler; hero pieces (cathedral, fountain, lamps, benches) modeled in Blender since free packs are low-poly.
- Textures/HDRI: Poly Haven. CREDITS file for any CC-BY.
