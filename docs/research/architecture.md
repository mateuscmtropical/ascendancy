# Architecture research: Godot 4 action RPG (listen server + dedicated server)

Date: 2026-11-14. Sources: official Godot docs, GitHub READMEs and licence files, search snippets. **[unverified]** = search snippet only or inference.

## 1. Project structure and conventions

- Official manual: snake_case folders and files (C# excepted), PascalCase node names, third-party code in top-level `addons/` even when not a plugin, assets kept close to the scenes that use them. https://docs.godotengine.org/en/stable/tutorials/best_practices/project_organization.html
- Same page: an empty `.gdignore` stops import of a folder but hides it from the FileSystem dock and blocks `load()`/`preload()`. No pattern support.
- The manual does not choose feature-based vs type-based. Our proposal (opinion):
  ```
  addons/            third-party only
  core/              thin autoloads (Game, Net, Events)
  net/               session, server/client, RPC definitions
  world/             seed + floor generation (pure GDScript, no nodes)
  features/hub/      town plaza, walking NPCs
  features/floor/    floor scene, spawners, boss arenas
  features/combat/   player, enemies, hitboxes, abilities
  data/              Resource scripts + .tres instances (items, monsters, floors)
  tests/
  tools/             generators, export scripts
  ```
- Scene organization: keep scenes self-contained, inject outside dependencies (signals, callables, node refs), and only nest children that are parts of the parent. https://docs.godotengine.org/en/stable/tutorials/best_practices/scene_organization.html
- Same page on autoloads: reserve for systems that own their data, need global access and work in isolation. Systems that modify other systems' data should be regular nodes. (The dedicated autoloads page returned 404 at fetch time.)
- Data: custom `Resource` scripts (`class_name` + `@export`) are editable in the Inspector and saved as `.tres`. Loads are shared by reference, so per-instance mutable state needs `duplicate()` **[inference from that behaviour]**. https://docs.godotengine.org/en/stable/tutorials/scripting/resources.html
- Pin one Godot 4.x version and record it in the repo. Docs exist for 4.4 through 4.7.

## 2. Multiplayer

Built-in API:
- `ENetMultiplayerPeer.create_server(port, max_clients)` / `create_client(address, port)`. Server is peer ID 1. Authority defaults to the server. `@rpc` takes `"authority"` or `"any_peer"`. High-level API is UDP only. https://docs.godotengine.org/en/stable/tutorials/networking/high_level_multiplayer.html
- Same page, server-authoritative guidance: treat client input as untrusted, keep position, combat and inventory on the server, send movement intent rather than positions, validate and rate-limit RPCs.
- `MultiplayerSpawner`: the authority spawns and despawns registered scenes. `spawn_function` lets you send data and build the node on each peer. https://docs.godotengine.org/en/stable/classes/class_multiplayerspawner.html
- `MultiplayerSynchronizer`: replicates listed properties to all peers by default. Visibility via `set_visibility_for` or filters. Object values (Resources) do not sync. Source is the 4.0 class page (snippet): https://docs.godotengine.org/en/4.0/classes/class_multiplayersynchronizer.html

One codebase, two modes:
- Listen server: the host process runs the authoritative server plus a local client.
- Dedicated: export preset "Export as dedicated server" (Resources tab) adds the `dedicated_server` feature tag and forces headless. Detect with `OS.has_feature("dedicated_server")` or `DisplayServer.get_name() == "headless"`. "Strip Visuals" shrinks the PCK. https://docs.godotengine.org/en/stable/tutorials/export/exporting_for_dedicated_servers.html
- Run: `godot --headless --path <project>` (`--headless` = `--display-driver headless --audio-driver Dummy`). https://docs.godotengine.org/en/stable/tutorials/editor/command_line_tutorial.html
- Design: one `Session` layer runs the same way in both modes. The host's own player goes through the same server path, not a shortcut.

Client prediction for action combat:
- Godot has no built-in prediction. Standard pattern: client sends sequence-numbered inputs and predicts locally. Server acknowledges the last processed input. Client rewinds and replays unacknowledged inputs. https://gabrielgambetta.com/client-side-prediction-server-reconciliation.html
- Remote entities: interpolate. https://gabrielgambetta.com/entity-interpolation.html
- Suggested split: predict movement and dodge. Keep hit detection, damage and boss phase changes on the server. Play hit reactions locally and correct on the server result.
- netfox (MIT, Godot 4.x): rollback, prediction with reconciliation, interpolation, client-server support. Start with its core addon. https://github.com/foxssake/netfox

Friends joining (NAT):
- UPnP: built-in `UPNP` class (`discover()`, `add_port_mapping()`, `delete_port_mapping()`, `get_gateway()`). Calls block the thread, so run them on a `Thread`. ENet needs only a UDP mapping. Not all routers support UPnP. https://docs.godotengine.org/en/stable/classes/class_upnp.html
- Noray (MIT, self-hosted with Bun or Docker): coordinates NAT punchthrough and falls back to a UDP relay. TCP control messages (`register-host`, `connect`, `connect-relay`). Godot client side: netfox.noray addon (MIT). https://github.com/foxssake/noray and https://github.com/foxssake/netfox (addons/netfox.noray). A relay means you pay for bandwidth.
- WebRTC: works in HTML5 exports. Desktop needs the webrtc-native GDExtension. Docs still marked work in progress. https://docs.godotengine.org/en/4.4/tutorials/networking/webrtc.html
- GodotSteam (MIT): repo moved to Codeberg and the GitHub copy is archived (per README). Steam networking needs a Steam app ID. Community alternative expressobits/steam-multiplayer-peer lists MIT, but its licence listing conflicts and the author paused development (Dec 2025) **[unverified]**. https://github.com/GodotSteam/GodotSteam
- Suggested order: v1 ENet + UPnP with "forward UDP port X" instructions. v2 self-hosted noray. Steam later, optional.

## 3. Seed-based procedural world

- FastNoiseLite: `noise_type` (Simplex Smooth default, Perlin, Value, Cellular), `seed`, `frequency` (0.01), `fractal_octaves` (5), `fractal_lacunarity` (2.0), `fractal_gain` (0.5). https://docs.godotengine.org/en/stable/classes/class_fastnoiselite.html
- RandomNumberGenerator uses PCG32. Same seed gives the same sequence. `state` can be saved and restored. Docs warn that similar seeds give similar streams, so hash external seeds. The algorithm "should not be depended upon", and no cross-platform or cross-version guarantee is stated. https://docs.godotengine.org/en/stable/classes/class_randomnumbergenerator.html
- Recommendations:
  - Derive every sub-seed by hashing: `hash(floor_seed, cx, cy, layer_id)` using your own 64-bit integer mix in GDScript. Avoid one shared RNG across generation steps, so generation order does not matter. Test integer overflow behaviour **[inference]**.
  - Join packet carries seed + generator version, not geometry. Server and clients run the same code.
  - Clients send a checksum of the generated layout (tile grid and boss spawn points) on join. The server rejects mismatches. This catches build drift and float differences.
  - Floor layout should use integer/grid logic. Cosmetic decoration can stay client-only, since Godot docs promise no cross-platform float determinism.
  - Chunking: a small floor can be generated whole. For paged chunks, godot_voxel (MIT) provides chunk streaming and custom generators, but it is a voxel module and heavy for heightmap floors. https://github.com/Zylann/godot_voxel
  - Generate on a worker thread (WorkerThreadPool) **[not checked in this pass]**.

## 4. Open-source references

Licences verified from the repo or README unless noted.

- godot-tiny-mmo (SlayHorizon), MIT, Godot 4.6. Gateway, master and world servers over WebSocket. `--headless` servers and separate client/server export presets. Learn: server split, headless presets. https://github.com/SlayHorizon/godot-tiny-mmo
- seaciety/GodotMultiplayerDemo, BSD-3-Clause, Godot 4.2. Server, client and host modes. Client prediction, reconciliation, lag compensation. Learn: host-mode listen server layout. https://github.com/seaciety/GodotMultiplayerDemo
- Relintai/broken_seals, MIT. 3D third-person RPG with host/join, server-side authority, chunked terrain, loot and talents. Caveat: built on Pandemonium Engine (Godot 3.x fork), multiplayer described as buggy. Learn: RPG systems. https://github.com/Relintai/broken_seals
- GDQuest/godot-open-rpg, MIT, Godot 4.7.2+. 2D turn-based RPG. Learn: data-driven RPG structure only. https://github.com/GDQuest/godot-open-rpg
- godotengine/godot-demo-projects (networking folder), MIT. Canonical ENet, WebSocket and WebRTC samples. https://github.com/godotengine/godot-demo-projects
- Zylann/godot_voxel, MIT. Chunked infinite voxel terrain, custom generators. No multiplayer. https://github.com/Zylann/godot_voxel
- Veloren, GPL-3.0-or-later, Rust. Multiplayer voxel RPG. Read for ideas only: GPL code cannot go into an MIT project. Official repo is GitLab. https://gitlab.com/veloren/veloren
- Luanti (ex-Minetest), LGPL-2.1-or-later voxel engine. Reference for host-your-own-world UX. Server details not checked. https://docs.luanti.org/for-creators/licensing/
- Not found: a permissive Godot 4 3D co-op monster-hunting or SAO-like project. Souls-like templates exist, but Cat's template licence listings conflict (Unlicense vs AGPL). monster-hunter-pocket is small and "other" licensed.

## 5. Testing and screenshots

Unit tests:
- GUT (bitwes), MIT, GUT 9.x for Godot 4. CLI (bash form): `godot -s addons/gut/gut_cmdln.gd -d --path "$PWD" -gdir=res://tests -gexit`. Also `-gjunit_xml_file`. Headless not covered on the CLI page. https://github.com/bitwes/Gut and https://gut.readthedocs.io/en/latest/Command-Line.html
- gdUnit4 (MikeSchulze), MIT, Godot 4.x (compat table 4.0 to 4.8 dev). `runtest` script in addons/gdunit4 (`runtest.cmd` on Windows), needs `GODOT_BIN`, `-a <dir>`, `-i <suite>`. HTML and JUnit reports. CI action exists. Headless not stated. https://github.com/MikeSchulze/gdUnit4 . CLI page from snippet, fetch 404'd: https://mikeschulze.github.io/gdUnit4/advanced_testing/cmd
- Pick one. Lean gdUnit4 for CI reports; GUT for simpler setup.

Headless limits (official):
- `--headless` "disables all rendering and window management functions. Most functions from DisplayServer will return dummy values." https://docs.godotengine.org/en/stable/classes/class_displayserver.html
- Headless can test netcode, authority, seed determinism and combat math. It cannot capture viewport images. A forum report confirms the rendering server is Dummy and `get_image()` returns nothing: https://forum.godotengine.org/150510/godot-headless-not-same-godot-window-cant-render-the-backend
- `--write-movie` needs rendering **[inference from the rendering statement]**.

Screenshots without a focused window:
- A (Windows, recommended): non-headless run with `--windowed --resolution WxH --position x,y --write-movie shots/out.png --fixed-fps 60 --quit-after N`. Each flag is documented. Off-screen `--position` behaviour not verified. https://docs.godotengine.org/en/stable/tutorials/editor/command_line_tutorial.html
- B: `DisplayServer.WINDOW_FLAG_NO_FOCUS` exists ("window can't be focused"). Runtime toggling not verified. https://straydragon.github.io/godot-csharp-api-doc/4.4-stable/main/Godot.DisplayServer.WindowFlags.html
- C (in-game): wait for a post-draw frame, then `get_viewport().get_texture().get_image().save_png(path)`. Viewport texture docs: https://docs.godotengine.org/en/stable/classes/class_viewport.html
- D (Linux CI): `xvfb-run` gives a real GL context. Community practice, not an official Godot recommendation.
- GDSnap is a Godot 4 snapshot-testing library. Licence not checked.

## 6. Name candidates

Method: one web search per name for exact-title matches on Steam and itch.io. Not exhaustive. No trademark search done.

- Floorbound: no match found. Low.
- Tierfall: no exact match. Timefall, Fatefall, Gravefall exist. Low.
- Stratoria: no exact match. Low (index may miss it).
- Ironhollow: no exact match. A "Hollow" game exists, unconfirmed as related. Low to medium.
- Thornspire: no exact match. Voidspire Tactics, Thornbound, Devil Spire. Medium (spire prefix crowded).
- Veilspire: no exact match. Voidspire Tactics, Veilkeeper, Veil Runners. Medium.
- Nimbus Keep: no exact match. "Nimbus" (floating city, itch.io and Steam), Nimbusfall. Medium (theme overlap).
- Sundered Spire: no exact match. Sundered (Thunder Lotus, Steam 535480), Steam Spire Chronicles. Medium.
- Skyspire: no exact match. "Sky Spire" / SkySpire_Quantum (itch.io, IsDon). Medium.
- Lumenfall: **reject**. Several Steam titles, including a co-op floating-islands game (app 5380660) and a tower roguelite (app 4929120).
- Skyhunt: **reject**. itch.io "Skyhunt" / Sky Hunt (gibibit).
- Gravelight: **reject**. Steam app 4566310 (Early Access roguelike) and app 2371600 (pixel RPG).

First picks: Floorbound, Tierfall, Stratoria, Ironhollow. Confirm on the Steam store search and a trademark register before committing. "Spire" is common in game titles, which hurts discoverability.
