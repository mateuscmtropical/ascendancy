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
   - **Estado:** o Fable começou aqui e foi parado. Já existem no gerador `RING_RADII`, `PLAZA_RADIUS`,
     `COREO_PLAZA_RADIUS`, `STREET_DROP`, `LAWN_RECTS`, `square_paths()` e `path_distance()` (formas de piso
     recortadas dos gramados, distância com sinal). Ainda **não** estão ligados em `add_ground` /
     `add_getulio_vargas_paths` / `add_sao_jose_paths`, e `features/hub/hub.tscn` não foi regerado com eles.
     Ideia em curso: gramado como malha gerada (grade fina) com altura = canteiro elevado onde
     `path_distance > 0`, e meio-fio na curva de nível zero.
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

## Ao terminar uma rodada
Atualizar a seção "Estado" deste arquivo (o que foi feito, o que falta, problemas), commitar e dar push na
branch; subir prints novos (se houver) para `ascendancy-refs/game_after/`.
