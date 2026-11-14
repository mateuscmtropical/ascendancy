# Ready-made anime humanoids that can be committed to a public MIT repo

Scope: male and female rigged humanoids, anime or stylized, with a license that allows redistribution and modification. Verified = license text or license field read on the source page. Unverified = taken from a search snippet or a secondhand mirror; check before use. Pages that returned 403 or 404 are marked as such.

## Bottom line

- Female: Godette (CC-BY 3.0, attribution required). Verified license line in godot-vrm's sample notes.
- Male: no verified male anime humanoid with a clean redistribution grant. Best lead is the OpenGameArt "Base Rigged Stylized Humanoid Character (YW)" by Girush, CC0 per snippet, unverified.
- Safe fallback for both genders: Quaternius Universal Base Characters (CC0, verified), stylized low-poly rather than anime. The anime look would come from our own shaders and hair/face work.
- Do not commit AliciaSolid, Anais, Miyu, Theresa or CGTrader/Booth models. Their terms either forbid redistribution or do not grant it.

## 1. pixiv VRoid sample avatars (AvatarSample_A to Z)

- Official help article: https://vroid.pixiv.help/hc/en-us/articles/4402394424089 (AvatarSample_A, B, C). Returned HTTP 403. Not read.
- Secondhand text, from a gitee mirror (https://gitee.com/melovemingming/vrm-samples), section "Models with particular conditions of use": models "can be used freely, as long as you comply with their conditions of use." Also: "While copyright is not waived, you can alter, distribute, and do many more things with them." Unverified.
- Same mirror lists a separate CC0 group, reportedly AvatarSample_D to G. OpenGameArt "VRoid Studio CC0 models" (https://opengameart.org/content/vroid-studio-cc0-models) says those came from VRoid alpha builds and were released under CC0. OGA returned 403, so this is unverified.
- Newer samples D to Z (23 avatars, 2025) follow "the same Terms of Use" as the earlier ones (VRoid news post, https://vroid.com/en/news/331gGTRqNMtXSucMr0tXc8, returned 403).
- VRoid Studio guidelines (https://vroid.com/en/studio/guidelines, read via search snippet only) say users should also follow each sample's own conditions.
- Verdict: the most promising official source, but the exact conditions are not readable from here. Someone needs to open the pixiv help article and the VRoid Hub license panel for each sample in a browser. Until then, do not commit.

## 2. VRM Consortium / vrm-specification samples

- Seed-san (https://raw.githubusercontent.com/vrm-c/vrm-specification/master/samples/Seed-san/README.md, verified): "## License Information" then "[VRM Public License 1.0](https://vrm.dev/en/licenses/1.0/index)" and "Seed-san model by VirtualCast, Inc." The README gives no redistribution or modification terms. Those depend on the .vrm file's License Settings, which I could not read. Not committable until the file's meta is checked.
- The samples folder README (https://raw.githubusercontent.com/vrm-c/vrm-specification/master/samples/README.md) states no license for any sample.
- VRM Public License 1.0 (https://vrm.dev/en/licenses/1.0/index, verified): redistribution is granted only if the model's License Settings enable it. Posting to a public repo counts as redistribution. A license cannot add terms beyond the license itself.

## 3. VRoid Hub models with redistribution and modification allowed

- Could not reach hub.vroid.com, so I could not enumerate or verify any Hub model's license panel.
- Hub license fields, from VRoid developer documentation (https://developer.vroid.com/en/sdk/docs/0.5.2/Pixiv.VroidSdk.Api.DataModel.CharacterLicense.html, via snippet): Avatar use, Commercial use (profit, nonprofit, disallowed, unset), Redistribution (allow, disallow, unset), Alterations, Attribution. A sample panel showed "Redistribution: Do not allow" and "Alterations: Do not allow".
- VRM 1.0 License Settings (https://vrm.dev/en/vrm/meta/license/, verified): Personation permissions (violent, sexual, commercial, each Allow or Disallow). Redistribution/Modifications License Type: "Redistribution Prohibited", "Copyright wavier (CC0)", CC BY, CC BY NC, CC BY SA, CC BY NC SA, CC BY ND, CC BY NC ND, Other.
- How to find candidates: on hub.vroid.com, filter for free or CC0 models, then open each model's license panel and require Redistribution = Allow, Alterations = Allow, and License Type = CC0 or CC BY. I could not do this from here, so no examples.

## 4. Other permissively licensed anime-style humanoids

Licensed and usable:
- Godette (Godot mascot model; VRM adaptation by Lyuma, 2021). Source: godot-vrm vrm_samples/LICENSE_SAMPLES.txt (https://raw.githubusercontent.com/V-Sekai/godot-vrm/master/vrm_samples/LICENSE_SAMPLES.txt, verified). License line: "Licensed under Creative Commons Attribution 3.0 Unported (CC-BY):". Original model by SirRichard94; VRM adaptation by Lyuma, "licensed under the above terms (CC-BY)". Redistribution, modification and commercial use are allowed with attribution. Polycount and rig not verified.
- Girush "Base Rigged Stylized Humanoid Character (YW)" (https://opengameart.org/content/base-rigged-stylized-humanoid-character-yw): male, anime-inspired proportions, rigged, CC0 per search snippet. Page returned 403, so the license and file format (archive is 7z, VRM not listed) are unverified.
- Quaternius Universal Base Characters (https://quaternius.com/packs/universalbasecharacters.html, verified): CC0. Six models: male and female in superhero, regular and teen proportions. Humanoid rig with retargeting. FBX, OBJ, glTF, Blend. Stylized low-poly, not anime.

Not committable as-is:
- AliciaSolid (DWANGO, VRM spec reference model, https://3d.nicovideo.jp/alicia/rule.html, read in Japanese via fetch): commercial use and derivative works are allowed. Sublicensing is prohibited. The page does not address redistribution of the unmodified model. Not safe for a public repo.
- Unity-chan (https://unity3d.jp/unity-chan/): official readme says the assets, including 3D models and motion data, are "made public under the terms of the Unity-Chan License", and redistribution requires the license notice and logo. Full license text was not readable (the terms page redirected to a page without them, and the PDF could not be rendered). Female only as far as I know; no male model confirmed.
- Fox Jump "Miyu" (https://fox-jump.itch.io/miyu-anime-character): VRoid-made, FBX and VRM, rigged. No license section. "You can use for comercial purposes." Name-your-price. Redistribution and modification not addressed.
- Fox Jump "Theresa" (https://thatnewdevgirl.itch.io/free-3d-anime-girl-theresa): not animated. Commercial use requires a donation of $5 or more. Redistribution not addressed.
- RexMun "Anais magic warrior" (https://sketchfab.com/3d-models/anais-magic-warrior-e14bd44682b546769371122c5ecfc6ad): 55.2k tris, rigged, three VRM files, no license named, NoAI label only. Not safe.
- Vket Store: closed May 9, 2025 (https://store.vket.com/en/items/6837 redirects to a closure notice). Per-item terms moved to Booth. Not verifiable here.
- CGTrader and RenderHub anime VRMs: royalty-free or resale-restricted licenses. Not redistributable.

## 5. Scriptable or procedural character creation

- VRoid SDK (https://developer.vroid.com/en/sdk/): Unity library for Hub OAuth, avatar fetch and VRM loading. Its own page says characters cannot be created with it. Upload SDK requires a separate application. No VRoid Studio CLI or headless mode found.
- MPFB2 (MakeHuman Plugin for Blender, https://github.com/makehumancommunity/mpfb2): code is GPLv3. Bundled assets (base mesh, targets, proxies) are CC0 per the MakeHuman 2020 license clarification (https://static.makehumancommunity.org/about/license.html). Verified by search snippet, page not fetched. Realistic body, not anime. Anime skins and clothing packs: license per pack, not checked.
- CharMorph (https://github.com/Upliner/CharMorph): code GPL-3.0 (verified from license.txt). Base meshes come from MB-Lab, which CharMorph's own doc places under AGPL-3.0. Avoid committing its meshes into an MIT repo.
- Blender add-ons that generate anime bodies procedurally: none found in this pass.

## Recommendation

- Male: Girush YW (CC0 per snippet). Open the OpenGameArt page in a browser, confirm CC0 and the file format, then import. If it fails, use the Quaternius Universal Base Characters male (CC0, verified) and restyle.
- Female: Godette (CC-BY 3.0, verified). Add an attribution line in the repo. If zero attribution is required, use the Quaternius Universal Base Characters female (CC0).
- Open items for a human with a browser: pixiv AvatarSample_A to C help article; VRoid Hub license panel for any candidate; Seed-san .vrm meta; OpenGameArt page for Girush and the CC0 AvatarSample_D to G pack.
