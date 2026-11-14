# Aesthetic research: anime cel-shaded fantasy town and monster hub (Godot 4, Blender 5.2)

Date: 2026-11-14. Tags: **[src]** = sourced from a URL below. **[unverified]** = search snippet or community claim only. **[proposal]** = my recommendation, not sourced. Note that Genshin internals are community reimplementations; miHoYo's own GDC slides were not accessible.

## 1. Visual analysis of the target look

**Palettes**
- Sky: Shinkai-style "magic hour" skies lean on pushed bloom and diffusion for a soft, humid look [src: colorculture.org/?p=6307]. Overhead blue deepens, lightening to cyan at the horizon, with layered clouds [src: tips.clip-studio.com/en-us/articles/10372].
- Anime palettes reuse a "golden" hue range and a second range for shadows, giving a watercolor feel [src: dtf.ru/howto/2790345-kakie-cveta-primenyayut-v-anime, Russian, secondary].
- Stone, foliage, skin: no sourced hex values found. See section 5 for proposals.

**Lighting**
- miHoYo's art team contrasted "Dirty, noisy, dark" with "Fresh, bright, clean, anime-like" as the target [src: docswell.com/s/UnityJapan/KWRPQ5-210617-unity-dojo20211mihoyozhenzhongyi, slide 12].
- Outline: thin and dark, with some materials tinting it toward their own hue [src: bjayers.artstation.com/blog/category/5].
- Rim light, GGX specular, and hair "angel ring" reflection belong to the base Genshin-style shader; the simplified version drops them [src: github.com/NoiRC256/URPSimpleGenshinShaders].

**Texture style**
- Stylized PBR: material lighting models are altered to fit art direction and are not energy-conserving [src: Dojo deck, slides 9-10].
- Hand-painted vs flat: sources did not settle this. [proposal] Hand-painted albedo with cel bands baked into the ramp, and minimal normal detail.

**Proportions and eyes**
- Stylized figures are about 5-6 heads tall, versus 7-8 for realistic bodies [src: tips.clip-studio.com/en-us/articles/4863; origin-exchange.autodesk.com/chibi-art-style]. Chibi ratios vary across sources, so treat them as approximate.
- Eyes are large and simplified [src: Clip Studio, above].

**Architecture**
- Aincrad Town of Beginnings (fan wiki, not anime canon): round central plaza, circular wall, wide stone-paved streets lined with street lights [unverified: swordartonline.fandom.com/wiki/Town_of_Beginnings; fetch returned 402, snippet only].
- Echoes of Aincrad (game, not anime) gives the town a lavish historic-Europe look [unverified: thegameswiki.com/echoes-of-aincrad/wiki/floor-1-town-of-beginnings].
- Monster Hunter Kokoto: thatched timber houses at the foot of Mount Kokoto, described as practical rather than ornate [src: monsterhunterwiki.org/wiki/Kokoto].
- Medieval European/gothic cathedral, half-timbering, cobble plazas, fountains: not confirmed by any source in this pass. [proposal] Use as art-direction target.

## 2. How Genshin-style rendering works

**Primary sources**
- GDC 2021, "'Genshin Impact': Crafting an Anime Style Open World" (Hugh Cai). Session page only; full talk is members-only [src: gdcvault.com/play/1027538].
- Unity Dojo 2021, miHoYo tech director Zhenzhong Yi, Genshin console rendering. Best primary deck available [src: docswell link above].

**Lighting and shadows (Dojo deck)**
- Cascaded shadow maps with Poisson-disc soft shadows, up to 8 cascades instead of the usual 4 (slide 18).
- CPU caching: first 4 cascades every frame, last 4 interleaved, each updated at least every 8 frames (slide 19).
- GPU penumbra mask: soft filtering runs only on penumbra pixels, cutting the pass from about 2-2.6 ms to 1.3-1.7 ms (slides 20-21).
- About 100 in-view local lights can cast shadows; static shadows are baked (slides 38-39).
- AO split: HBAO for small detail, AO volumes for static props, and Capsule AO for characters that follows the skeleton (slides 26, 31, 34).
- Volumetric fog is light-driven and costs under 1 ms; god rays are a separate half-res ray-march over 5 cascades (slides 47, 50-51).
- ACES was rejected because it did not fit the game's style; a WCG color LUT folds the tone curve and grading in under 0.05 ms (slide 80).

**Face shadows (community, unconfirmed by miHoYo)**
- Face shadow textures are authored or generated for several key light angles, each converted to an SDF, slerped between, and averaged. The shader thresholds on FdotL [src: sydianandrewchen.github.io/projects/3-stylized-facial-shadow-workflow].
- The Genshin-style texture stores left-side coverage over 0-180 degrees, flips for right-side light, and compares against head-forward vs light direction. It needs a light-direction offset and automatic 2D hair shadow on the face [src: NoiRC256 README].

**Ramp**
- Shadow ramp, shadow position, and ramp width sliders control the cel bands [src: github.com/Melioli/HoyoToon/wiki/Using-the-Genshin-Shader].

**Outline**
- Inverted hull. Inverted hulls show seams on hard-edged meshes; the fix is smoothed normals, baked or stored separately [unverified: poiyomi.com/outlines, redirected, snippet only].
- Import route: recalculate normals with a high smoothing angle [src: github.com/Delt06/urp-toon-shader/wiki/Outline].
- A Sobel post-process white edge is a separate effect [unverified: adrianmendez.artstation.com/projects/wJZ4Gg].

**Same genre, Japanese sources**
- Blue Protocol (CEDEC 2020): opaque materials for effects, post-processing, vertex animation [src: cgworld.jp/feature/202011-cedec2020-bluep-2.html]. CEDEC 2021 follow-up [src: gamebusiness.jp/article/2021/09/13/19051.html]. Tower of Fantasy: no sources found.

## 3. Reproducing it in Godot 4

**Renderer**
- SDFGI, VoxelGI, SSR, and SSIL all require Forward+ [src: docs.godotengine.org/en/stable/tutorials/3d/global_illumination/using_sdfgi.html; environment_and_post_processing.html]. The RTX 3060 Laptop supports Forward+.

**Tonemap and glow**
- Modes: Linear (fastest), Reinhard, Filmic, ACES, AgX (slowest) [src: environment_and_post_processing.html].
- [proposal] Use Linear or mild Filmic, plus a 3D LUT (33 slices) for stylized control. Skip AgX. This matches the Genshin team's ACES rejection, which is an inference.
- Glow: the stable docs say Softlight is the default and weakest. A commit reportedly changed the default to Screen; check your build [unverified].
- [proposal] Raise HDR threshold to around 1.0 and keep Bloom low, so only highlights bloom.

**Global illumination**
- LightmapGI (baked): the cheapest at runtime, but least responsive. [proposal] Use it for the town and dungeons, since they are static.
- VoxelGI: for small/medium scenes. Light leaks appear with thin walls. Low quality cuts cone taps from 6 to 4 [src: using_voxel_gi docs, search snippet].
- SDFGI: "one of the most demanding global illumination techniques in Godot." Dynamic occluders are unsupported, GI goes stale after geometry changes, and Use Occlusion costs extra. Cascades of 4 or fewer for fast camera moves. About 25 frames to converge [src: using_sdfgi.html].
- [proposal] Skip SDFGI on the open world. Use baked lightmaps plus SSIL/SSAO for dynamics. No benchmark found for this laptop class; profile before committing.

**Fog and AO**
- Volumetric fog has its own docs page; 4.2 defaults were density 0.05, length 64 [unverified mirror].
- Cheaper alternatives: height fog, Sun Scatter, Aerial Perspective. SSAO and SSIL at Half Size cost less but lose small detail [src: environment_and_post_processing.html].

**Toon shading**
- Built-in render modes: diffuse_toon and specular_toon. Custom light() is ignored when vertex lighting is on [src: docs.godotengine.org/en/stable/tutorials/shaders/shader_reference/spatial_shader.html].
- eldskald/godot4-cel-shader: MIT, Godot 4, ramp via a global diffuse_curve texture, outline as a next_pass material with a global width. Best starting point [src: github.com/eldskald/godot4-cel-shader].
- Flexible Toon Shader Godot 4 port with custom ramps (atzuk4451/FlexibleToonShaderGD-4.0) [unverified: godotshaders.com/shader/flexible-toon-shader-godot-4/].
- VRM Importer and MToon for Godot 4.1+, MIT, includes MToon [src: godotengine.org/asset-library/asset/2031].
- Outline: next_pass material with cull_front and a normal-offset vertex. Stencil modes are experimental [src: spatial_shader.html].

## 4. Blender 5.2 pipeline

- Blender 5.2 LTS released July 2026 [src: digitalproduction.com/2026/07/21/blender-5-2-lts-lands-with-node-physics/]. Python API: Geometry Nodes modifier property access changed, and paint.eraser_brush was removed [src: developer.blender.org/docs/release_notes/5.2/python_api/, partial page].
- Character pipeline: VRoid Studio -> VRM -> Blender VRM add-on -> cleanup -> GLB -> Godot [src: gamefromscratch.com/easy-anime-character-creation-with-vroid-studio-and-blender/]. VRoid Studio exports VRM 1.0 [unverified]. Animation retargeting in Godot needs extra tools [unverified: godot-vrm README].
- Normal editing for faces and hulls (Data Transfer modifier, smoothed custom normals) is standard practice, not sourced here.
- Freestyle: edge-based NPR, with a cartoon preset. It has no Z-depth output and supports only faced meshes [src: docs.blender.org/manual/en/render/freestyle/view_layer/line_style/thickness.html]. [proposal] Use it for key art and concept renders only, not runtime outlines.
- Procedural buildings: Procedural Building Generator 2 has half-timbered styles but is broken on Blender 5.2.0, so use 5.2.2 [src: blendermarket.com/products/pbg-2]. Medieval House Generator is a paid Geometry Nodes asset [src: superhivemarket.com/products/medieval-house-generator]. No free bpy half-timber script was found. [proposal] Write a small bpy generator: posts and beams placed along a footprint, instanced, then realized.
- Environment process: Capcom's Rise Sunbreak team defined each territory's setting first, then form, then gameplay gimmicks, and hit memory limits in dense areas [src: news.capcomusa.com/2023/01/31/building-the-environments-ofmonster-hunter-rise-sunbreak].

## 5. Proposed style bible

**Palette (proposal, all hex)**
- Sky: zenith #5C8FD1, horizon #D7EEF5, sun warm #FFE2B0.
- Stone: lit #E9DCC6, mid #B9AA92, cool hued shadow #7C7E98.
- Wood #8B5A3C, roof #B65A40.
- Foliage: #7FC46A, #3F8A50, #245A3A.
- Skin: lit #F7D6C4, ramp shadow #E2A7A3 (warm pink, not grey), deep shadow #A97A8F.
- Outline base #2B2236, tinted per material at about 35% of albedo hue.

**Lighting**
- One key sun, warm #FFE6C4, 35-45 degree elevation, 2-3 shadow cascades, about 60 m max shadow distance.
- Sky fill cool #A9C8F0 at about 30% of key.
- Character rim light cool #BFE6FF, 1.5-2 px, opposite the key.
- Tonemap Linear + 3D LUT. Bloom threshold ~1.0, Screen blend, low intensity.
- Height fog light, Sun Scatter on, Aerial Perspective about 0.3-0.4.
- Baked LightmapGI for static areas; SSAO and SSIL at Half Size.

**Outline**
- 1.5 px at 1080p, depth-scaled and clamped 0.8-2.5 px. Smoothed normals for hard edges. Fade out beyond about 40 m.

**Proportions**
- Hero 6.5 heads, NPC adult 6, child 5. Large eyes; simplified hands and feet.

**Materials**
- Max 3 ramp bands plus specular toon. No roughness maps on stone; no normal maps on faces.
- Hand-painted albedo: 2048 atlas per character, 1024 per district.

**Do**
- Hued shadows, one key light, baked GI for the town, quality set in Project Settings.
- Use references for mood only.
- Verify each visual change with zoomed screenshots (project rule).

**Don't**
- ACES or AgX as defaults. SDFGI on the open world. Runtime Freestyle. Pure black outlines. Grey desaturated shadows. Photoreal normal maps on faces. Copying Aincrad, Genshin, Monster Hunter, or Warface assets or maps.

**Budget on RTX 3060 Laptop (1080p60, proposal)**
- Forward+ with baked GI and 2-3 shadow splits is plausible. Nothing here is benchmarked, so profile in the Godot debugger before locking settings.
