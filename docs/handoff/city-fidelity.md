STATUS: CONCLUIDO

# Handoff: fidelidade da cidade + lojas de RPG

Branch de trabalho: `wip/city-fidelity` (nunca commitar na `main`; push a cada etapa concluída).
Referências (fotos reais + prints "antes"): repositório **privado** `mateuscmtropical/ascendancy-refs`
(`gh repo clone mateuscmtropical/ascendancy-refs`). Nunca copiar essas imagens para este repositório público
(são capturas do Google Maps/Street View). Prints novos de comparação vão para `ascendancy-refs/game_after/`
com o mesmo nome de câmera.

## O que o usuário pediu (2026-11-14, palavras dele)
- "Os personagens estão MUITO melhores do que o design da cidade. O chão não tem profundidade, as barreiras do
  coreto estão todas zoadas e não estão no lugar certo. Não tem os canteiros de gramado, os santos na frente da
  igreja não estão detalhados, o interior também não está [...] Analise frame a frame e compare com as imagens
  da praça de CM."
- "Eu quero que continue o trabalho de fidelização [...] e compararmos depois."
- "Quero que ele faça as casas diferentes ao redor da praça, e cada uma sendo de uma coisa diferente também (se
  der pra ser geração procedural, ia ser top), mas uma casa de ferreiro, outra de armaduras, outra de itens
  mágicos, etc... Todas essas coisas de RPG."
- Depois de tudo: vídeo promocional novo (sem legenda citando Campo Mourão). O vídeo fica para a sessão local
  (precisa de GPU); não gravar na nuvem.

A barra de qualidade são os personagens (Quaternius Universal Base Characters + outfits). Estilizado, não
fotorrealista, mas com cara de feito com cuidado.

## Ordem de trabalho
1. **Chão com profundidade** (`tools_src/build_hub_scene.py`): meio-fio de verdade em todo caminho e canteiro,
   asfalto abaixo da calçada, canteiros de gramado elevados com borda de pedra/concreto e formas curvas como na
   foto aérea (`real/opera/maps_aerial_praca_z19.png`), arbustos/sebes nas bordas, piso com relevo
   (normal/roughness) sem moiré, variação de material.
   - **Estado:** feito na rodada de 2026-11-14 (`tools_src/build_ground.py`); ver a seção "Estado".
2. **Coreto** (`tools_src/build_plaza_props.py` `build_coreto`): guarda-corpo quebrado (placa verde opaca,
   corrimão flutuando). Refazer como o real (`real/opera/praca_getulio_fountain_coreto_1.png`): telhado de
   telha octogonal sobre postes, balaustrada com balaústres ou grade de ferro, abertura certa na escada, base
   de pedra com friso. Colisores `*-colonly` batendo com o visual.
3. **Santos na frente da catedral** (`tools_src/build_cathedral.py` `build_statues`, hoje cone + esfera).
   Real: santo de túnica (estilo São José) em pedestal alto (`real/opera/praca_sao_jose_forecourt_1.png`).
   Sugestão: usar corpo Quaternius + túnica (pipeline de `tools_src/build_characters.py`, CC0) em pose fixa
   com material de mármore, sobre pedestal com base, dado, cornija e placa.
4. **Interior da catedral** (`build_nave`, `build_arcade_wall`, `build_column`, `build_chancel`, `build_apse`):
   real tem colunas caneladas creme com capitel dourado de folhas, arcos com aduelas vermelho/branco com
   ornamento de folha, teto de vigas com painéis grandes, vitrais altos com figuras entre colunas, abside
   pintada com imagem do santo, altares laterais, lambri, muitos bancos escuros, luminárias
   (`real/opera/cathedral_interior_1..3.png`).
5. **Chafariz** do Getúlio Vargas (`features/hub/props/fountain_large.tscn`, `art/town/fountain_large.*`):
   real é chafariz em níveis num tanque redondo grande com estátuas em volta e jatos d'água.
6. **Vegetação/mobiliário**: praça real tem palmeiras e árvores de copa grande; postes, bancos.
7. **Lojas de RPG ao redor da praça (procedural)**: gerador novo (ex.: `tools_src/build_shops.py`, ou estender
   `build_houses.py`) com base modular de casa (largura, andares, janelas, sacadas, telhado por seed) + kit por
   tipo: ferreiro (forja com chaminé e brasa, bigorna, armas na parede), armeiro (armaduras em manequim,
   escudos), itens mágicos (vitrine com cristais/poções, brilho), alquimista, taverna, estalagem, guilda de
   aventureiros, padeiro, alfaiate, joalheiro. Placa pendurada com ícone por tipo, toldo e cores próprias.
   Props CC0 já disponíveis: Quaternius Fantasy Props MegaKit e Medieval Village MegaKit
   (`tools_src/fetch_assets.py` baixa para `tools/vendor/`). Em `build_hub_scene.py`, `add_buildings` escolhe
   o tipo por frente (as casas viradas para as praças viram lojas; o resto continua residencial). Seed fixa
   para o layout ser determinístico.

## Pipeline e ambiente
- Ler `CLAUDE.md` e as skills em `.claude/skills/` (style-bible, gdscript-code-style, godot-run, asset-intake).
- `tools/` não está no git. Na nuvem (Linux): baixar Godot 4.7.2 (Linux, `Godot_v4.7.2-stable_linux.x86_64`),
  Blender 5.2 (tarball Linux, rodar `--background --python`), `pip install gdtoolkit==4.5.*`, e rodar
  `python tools_src/fetch_assets.py`. Ajustar caminhos só localmente na sessão; não commitar caminhos de Linux
  nos scripts (os scripts usam `tools/Godot_v4.7.2-stable_win64_console.exe` no Windows do usuário).
- Ordem dos geradores: `build_characters.py` → `build_houses.py` → `build_cathedral.py` →
  `build_plaza_props.py` → `copy_kit_models.py` → `python tools_src/build_hub_scene.py` → rebake da navmesh
  (`godot --headless --path . -s tools_src/bake_hub_navmesh.gd`). Nunca editar `hub.tscn` à mão.
- Eixos: Godot (x, y, z) = Blender (x, z, -y). Catedral em Godot (18, 0, 0) girada -90° (fachada para -X).
- Malha `*-colonly` vira colisor. Props do kit ganham colisor por `KIT_COLLIDERS` em `build_hub_scene.py`.
- Desempenho: 60 fps 1080p numa RTX 3060 laptop; juntar malhas por material (helpers `merge_*`).
- Testes: `godot --headless --audio-driver Dummy --path . -s addons/gut/gut_cmdln.gd -gdir=res://tests/unit -gexit`
  (todos passando). Lint: `gdlint core net world features data tests` zero aviso; `gdformat` nos .gd editados.
- Prints na nuvem: sem GPU. Tentar `xvfb-run` + Mesa lavapipe (Vulkan por software) com
  `bash tools_src/shot.sh res://tests/shots/hub_shots.tscn <saida.png> <Camera>`; se não renderizar, registrar
  e seguir com validação geométrica (contagens, bounds, colisores, testes). A validação visual final é feita
  localmente pelo usuário/sessão local.

## Regras do usuário (obrigatórias)
- Responder em português do Brasil.
- Nada copiado de jogo existente; assets só CC0/CC-BY/MIT com crédito em `CREDITS.md`.
- Código do jogo limpo (sem gambiarra, estilo do projeto); scripts geradores podem ser mais soltos.
- Identidade git: `mateuscmtropical <88845521+mateuscmtropical@users.noreply.github.com>`; nunca e-mail pessoal.
  Commits terminam com `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
- Push só na branch `wip/city-fidelity`. Nada de merge na `main`.
- Guardar só resultado final; apagar temporários.

## Condição de parada (obrigatória)
A rotina agendada só existe para cumprir a "Ordem de trabalho" acima (itens 1 a 7). Quando todos estiverem feitos
e validados (testes e lint passando), escreva na primeira linha deste arquivo `STATUS: CONCLUIDO`, commite e dê
push. Toda rodada que encontrar `STATUS: CONCLUIDO` aqui encerra imediatamente, sem mudar nada. Se houver
ferramenta para gerenciar rotinas (conector Claude_Code_Remote), desative também a rotina
`trig_01VU2ckA2tjxuEUfaaMP82Zr` (enabled = false). Não invente trabalho extra além do pedido.

## Estado (rodadas na nuvem de 2026-11-14: ~17:40–18:50 e ~21:40–22:50 UTC)

Os sete itens da ordem de trabalho estão feitos, com testes (16) e lint passando. A segunda rodada fechou o
que a primeira tinha deixado em aberto dentro da lista (casas de loja por seed, acabamento do interior da
catedral, jatos do chafariz). **O que resta é só a conferência do usuário no render real (Forward+)** e o vídeo
promocional, ambos da sessão local com GPU.

### Feito
1. **Chão** — `tools_src/build_ground.py` → `art/town/ground.gltf`. Ruas de pedra 12 cm abaixo das calçadas,
   meio-fio de pedra em toda laje (quadras, praças, canteiro central, rotatória), canteiros de gramado elevados
   com meio-fio próprio e leve abaulado, bordas curvas (praça do chafariz, anel, praça do coreto, quatro rondéis
   nas diagonais), sebes aparadas no lado da rua, incrustações de pedra nos largos, normal map no tijolo, grama
   com textura gerada + tufos de capim por seed. O layout (caminhos, campo de distância `bed_field`, alturas
   `ground_height`) fica em `build_hub_scene.py` e é a fonte única: os props usam `grounded()`. Colisão: lajes
   com saia em rampa (`-convcolonly`) e canteiros com borda em rampa (`-colonly`); o personagem sobe o meio-fio
   andando (teste `test_player_walks_up_the_curb_from_the_street`).
2. **Coreto** — refeito em `build_plaza_props.py`: base com plinto e friso, balaustrada torneada entre postes
   de madeira (só o lado da escada fica aberto), telhado em dois níveis com lanternim, escada com muretas.
3. **Santos** — `build_cathedral.py` `build_robed_figure`/`build_saint_figure`: aldeão CC0 do próprio repo em
   pose fixa, túnica e manto canelados, cajado e auréola, mármore; pedestal alto com moldura e placa.
4. **Interior da catedral** — vitrais altos em arco com figura de santo, teto de vigas fundas com painéis
   grandes, três lustres, lambri escuro, altares laterais com nicho pintado, pintura do santo no retábulo.
   Na segunda rodada: a parede entre os arcos foi aberta abaixo da imposta, então a arcada se apoia em
   **colunas caneladas soltas** (antes ficavam embutidas num pilar chato); capitel dourado com duas fileiras
   de folhas e volutas nos cantos (`make_acanthus_leaf`); aduelas vermelho/branco com **folha dourada** em
   cada aduela vermelha; **arandela** com globo aceso em cada coluna, virada para a nave (`build_sconce`);
   bancos em madeira castanha (antes quase pretos); dourado menos metálico (lia esverdeado sem reflexo).
5. **Chafariz** — tanque redondo largo, tambor com painéis, três bacias com gomos, quatro aguadeiras de pedra,
   partículas em `features/hub/props/fountain_large.tscn` (transbordo das três bacias + oito jatos em arco);
   gotas maiores e mais opacas na segunda rodada.
6. **Vegetação** — palmeira-imperial procedural (`art/town/palm.gltf`, 15 na praça), árvores da São José com
   copa 45% maior, tufos de capim, vasos com flores no adro.
7. **Lojas de RPG** — `tools_src/build_shops.py` → `art/town/shops/shop_<tipo>_{sign,stall,yard}.gltf` para
   ferreiro, armaduras, magia, alquimista, taverna, estalagem, guilda, padeiro, alfaiate e joalheiro (placa
   com emblema, toldo listrado com balcão e mercadoria, props grandes do ofício). `add_shops` em
   `build_hub_scene.py` veste as 66 casas viradas para as praças e a avenida (`SHOP_FRONTAGES`), tipo por
   seed fixa (`SHOP_SEED`), vizinhos nunca repetem.
   Na segunda rodada, **casas de loja por seed**: `tools_src/build_shop_houses.py` desmonta as casas de 6 m
   (`house_stone_tall`, `house_narrow_three`) em térreo, andares de cima e telhado (ilhas da malha, pela
   altura) e remonta oito variantes `art/town/shops/house_shop_narrow_1..8.gltf` com seed fixa: qual térreo,
   um ou dois andares de cima e quais, qual telhado, espelhada ou não, cor do reboco e das telhas (cor de
   vértice, que o Godot multiplica sobre a textura do kit). `shop_houses_for` em `build_hub_scene.py` troca a
   casa de cada fachada de loja por uma variante da mesma planta, sem repetir a vizinha.

### Sobra para a sessão local (fora da lista ou dependente de GPU)
- Conferir no Forward+: tom das paredes da catedral (no render por software a luz ambiente azulada deixa o
  creme esverdeado), brilho dos emissivos (arandelas, lustres, cristais, brasa), leitura dos jatos do chafariz,
  cores do reboco das lojas (`PLASTER_TINTS`/`ROOF_TINTS` em `build_shop_houses.py`, hoje bem suaves).
- Com o Medieval Village MegaKit baixado (`fetch_assets.py`), dá para gerar receitas novas direto em
  `build_houses.py` (larguras de 8 m, janelas e sacadas por módulo). Na nuvem o kit não baixa (itch.io
  bloqueado), por isso as variantes são recombinações dos andares das casas já exportadas.
- Lojistas (NPC atrás de cada balcão) e interação com as lojas: não fazem parte desta lista.
- Vídeo promocional novo, sem legenda citando Campo Mourão.

### Problemas do ambiente na nuvem
- `download.blender.org` bloqueado: Blender substituído por `pip install bpy==5.2.4` (Python 3.13) + wrapper
  local que importa `bpy` antes de rodar o script.
- `itch.io` bloqueado: `fetch_assets.py` não roda. As texturas do kit que os geradores leem foram copiadas de
  `art/town/textures/` para um `tools/vendor/` local (fora do git). `build_houses.py`, `build_characters.py`
  e `copy_kit_models.py` **não** foram rodados (saídas antigas mantidas).
- Sem Vulkan por software (pacote `mesa-vulkan-drivers` indisponível): prints feitos com
  `xvfb-run` + `--rendering-driver opengl3` (Mesa llvmpipe, renderer Compatibility). Servem para conferir
  geometria e composição; **não** têm SSAO/SSIL/glow do Forward+, e as cores saem mais lavadas.
- `bpy.ops.object.transform_apply` com escala negativa derruba o `bpy` do pip (falha de segmentação); o
  espelhamento em `build_shop_houses.py` é feito direto na malha (`transform` + `flip_normals`).

### Prints
`ascendancy-refs/game_after/*.png` (mesmos nomes de câmera de `game_before/`, mais `ShopsEye` e `ShopClose`),
atualizados na segunda rodada. Render Compatibility por software, ver ressalva acima.

## Ao terminar uma rodada
Atualizar a seção "Estado" deste arquivo (o que foi feito, o que falta, problemas), commitar e dar push na
branch; subir prints novos (se houver) para `ascendancy-refs/game_after/`.
