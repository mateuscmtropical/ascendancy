# Handoff rodada 3 (atualizado 2026-11-15, sessão na nuvem)

Branch de trabalho: `wip/city-fidelity`. Spec de design: `docs/handoff/city_design_v2.md` (seções A–L, prioridade em F).
Regras do projeto em `CLAUDE.md` (obrigatórias). Agentes auxiliares: nunca Fable.

## Feito e integrado em wip/city-fidelity (rodadas anteriores)
- Escadas (catedral, presbitério, coreto) com rampa de colisão; pulo firme; corrida nova; voo de debug; contador de FPS.
- Layout das praças A.4, regra `can_plant()` (J), palmeiras em fileiras (A.5), sebes de 0,5 m (H), rotatória real (K), obelisco do Marco.
- Água fluida do chafariz grande (seção I: jatos, cortinas, superfícies animadas, respingo; estrias descendo).

## Feito nesta sessão (nuvem, SEM Blender/Godot no ambiente)
Nada abaixo foi renderizado nem testado no Godot: só `py_compile`, execução em Python puro do que não depende de bpy
(`build_hub_scene.py` roda inteiro e regenerou `features/hub/hub.tscn`) e um stub de bpy para os construtores de casas
(todos os 47 modelos do plano constroem sem erro, AABB dentro do lote, nenhum prédio atravessando o vizinho).

1. **Branches dos agentes integrados**
   - `wip/agent-trees`: só os arquivos novos (`build_trees.py`, `old_tree_1..6`, `palm_9/11/14`, texturas, materiais, `tests/shots/tree_lineup.tscn`), nada revertido. Não havia lixo de depuração.
   - `wip/agent-cathedral` e `wip/agent-houses-shops`: mesclados.
   - **Não consegui apagar os 3 branches remotos** (`git push --delete` volta HTTP 403 pelo proxy da nuvem). Apagar à mão: `git push origin --delete wip/agent-cathedral wip/agent-trees wip/agent-houses-shops`.
2. **Árvores e palmeiras (B, J)**: `PLANT_MODELS` usa `old_tree_1..6` (variante estável pela posição) e `palm_9/11/14` (20/50/30, nunca igual à vizinha). Ipês floridos `tree_bloom_1/2` (rosa/amarelo) acrescentados a `build_trees.py`; até serem gerados, a cena usa `CommonTree` (fallback automático). Colisão do tronco saiu do glTF (removida também dos .gltf já exportados) e virou `KIT_COLLIDERS` (entra na navmesh). `ROOT_CLEARANCE` 3,0 (raízes medidas: até 3,0 m); pontos da GV que caíam fora dos gramados foram movidos. README de `build_trees.py` preenchido com medidas reais (as árvores têm ~4–5,5 mil triângulos, acima dos 2,5 mil da spec).
3. **Catedral maior (E, G)** em `build_cathedral.py`:
   - Abside: 6 lancetas com vitral de pomba (texturas do agente, espelhadas por lado), óculo do Espírito Santo, lambri, faixa ocre, pilastras, cornija, semicúpula estrelada; por fora meia-cúpula de cobre e contrafortes.
   - Presbitério: 6 degraus, mesa de comunhão, passadeira, supedâneo; altar-mor com frontal de 5 arquinhos, toalha, 6 castiçais, missal.
   - Retábulo: predela, sacrário, edícula com colunas caneladas, nicho azul estrelado, **cruz de madeira com o Cristo** (corpo CC0 posado do agente, escala 1,6, perizônio, coroa, auréola, cravos), INRI, Maria e João nas alas. Peito do Cristo a 5,6 m do piso do presbitério (spec dizia 6,3; baixei para o frontão não bater no óculo).
   - **Bancos em 3 + 3 blocos** (G.2) com corredor transversal em y≈19,5; colisor por bloco contínuo. Altares laterais com Nossa Senhora e São José em vulto, velas votivas, genuflexório.
   - Fachada/torres acompanham a escala (sineira, relógio e coroamento ×1,3; empena, janelas e balaustrada subiram; seteiras das naves laterais saíram de dentro da torre). Paredes laterais: 2 fiadas de vitrais, faixa ocre, lambri de mármore, portas laterais (fechadas, sem rampa externa).
   - `build_hub_scene.py`: `CATHEDRAL_FACADE_X = 13`, adro de 30 m (estátuas no piso), luz no crucifixo, contraluz dourada, spots coloridos das lancetas/óculo, luz nos altares laterais, padre atrás do altar, câmera do tour mira o crucifixo. Teste da escadaria ajustado (início x=6, entrada x=16).
4. **Casas e lojas (C, D)**:
   - Plano de lotes em `build_hub_scene.py` (`town_lots()`): fileiras preenchidas por `lot_widths` (6–12 m, beco com portão quando sobra), lojas nos lotes fixos da D.1 (todas as 10), arquétipo por largura sem repetir em 3 lotes, esquina/rua de trás com preferências, reboco nunca igual ao vizinho, uso equilibrado dos 12 arquétipos. `HOUSE_ROW_DEPTH` 12,5. `check_town_plan()` dá assert em lote sobreposto, lote na rotatória, modelo maior que o lote e prédios que se atravessam (com os sidecars).
   - `build_town_houses.py`: 12 arquétipos (receitas em `ARCHETYPE_SPECS`, telhados e detalhes por dicionário) e 10 lojas entráveis (salão real, paredes com colisor próprio, porta 1,6 × 2,5 sem degrau, vitrines, forro com colisor, interiores com props do Fantasy Props MegaKit, emissivos, luzes e marcador do lojista no sidecar). Guilda com pé-direito duplo e quadro de missões; ferreiro com alpendre da forja; estalagem com portão de carroça e quarto; taverna com terraço coberto.
   - `add_town_lots()` coloca casas, portões de beco, lojas com placa, luzes e lojista. **Enquanto os modelos não existem, a cena usa as casas antigas do kit** (aviso no console) — é o que está no `hub.tscn` commitado.
   - Teste `test_every_shop_type_has_a_dressed_front` agora só exige a placa (vale nas duas montagens).
5. **Flores (L.1/L.2)**: `flower_tufts()` em `build_hub_scene.py` (bordadura da esplanada, coroa do chafariz, meias-luas, canteiros redondos, anel do coreto, pé das palmeiras, adro, rotatória, Marco, canteiro central; ~2.300 tufos a 7/m²) e `build_flowers()` em `build_ground.py` (cruz de folhas + 3–5 botões, uma malha por cor, ~37 mil triângulos). Clareiras do bosque (corte permitido) não feitas.
6. **Fonte pequena (I/K)**: `make_jet_mesh`/`make_curtain_mesh` parametrizados; fonte pequena com jato central, 4 arcos do pináculo e véu da taça ao tanque; `.import` já mapeia `M_WaterJet`/`M_WaterCurtain`; `fountain_small.tscn` com respingo em anel e névoa de sprite redondo (sem quadradinhos).
7. CLAUDE.md: ordem do pipeline atualizada (entra `build_trees.py` e `build_town_houses.py`).

## Regenerar localmente (nesta ordem; nada disso foi gerado na nuvem)
1. `blender -b --factory-startup -P tools_src/build_cathedral.py` → `art/town/cathedral.gltf` (precisa de `tools/vendor/ubc` para o Cristo e dos personagens em `art/characters`).
2. `blender ... -P tools_src/build_plaza_props.py` → `fountain_small.gltf` (e os demais props).
3. `blender ... -P tools_src/build_trees.py` → gera `tree_bloom_1/2` e regera árvores/palmeiras sem `Trunk-colonly` (os .gltf atuais já foram limpos à mão).
4. `blender ... -P tools_src/build_ground.py` → `ground.gltf` com flores.
5. `blender ... -P tools_src/build_town_houses.py` → `art/town/houses/*.gltf|json` e `art/town/shops/shop_*.gltf|json` (precisa de `tools/vendor/village` e `tools/vendor/props`; peça de prop ausente só gera AVISO — conferir nomes: Anvil, Anvil_Log, Whetstone, WeaponStand, Peg_Rack, Dummy, Shield_Wooden, Chest_Wood, Workbench(_Drawers), Chandelier, Bookcase_2, BookStand, Scroll_1, Cage_Small, Cauldron, Shelf_Small_Bottles, SmallBottles_1, Potion_1/2/4, Barrel(_Holder), Mug, Table_Large, Stool, Chair_1, Book_Stack, Bed_Twin1, Nightstand_Shelf, Prop_Wagon, Bag, Coin_Pile, Banner_1/2).
6. `python tools_src/build_hub_scene.py` (com os modelos presentes passa a usar casas/lojas novas; o assert de AABB roda com os sidecars) e depois o **rebake da navmesh** `tools/Godot_v4.7.2-stable_win64_console.exe --headless --path . -s tools_src/bake_hub_navmesh.gd` (obrigatório: catedral, lotes, árvores e colisores mudaram).
7. Abrir no editor uma vez para importar; GUT headless; `gdformat` + `gdlint` (só o teste .gd mudou); prints com `tools_src/shot.sh` (inclusive `AerialTop`, interior da catedral mirando o retábulo, uma loja por dentro) + recortes ampliados; comparar com `ascendancy-refs`.

## Pendente (ordem)
1. Regenerar e validar tudo acima; corrigir o que aparecer nos prints (em especial: pose/eixos do Cristo, posição das pombas nas lancetas — o lado espelhado foi escolhido sem ver —, escala dos props nas lojas, empenas escalonada/sino).
2. Depois de validar as casas novas: apagar o caminho legado (`add_kit_rows`, `house_row`, `shop_houses_for`, `add_shops`, `HOUSE_SIZES`/`SHOP_HOUSES`, `build_shop_houses.py`, `shop_*_stall/yard`) e tirar o fallback de `PLANT_FALLBACK_MODELS` quando os ipês existirem.
3. Faltas conhecidas da spec: portas laterais da catedral com rampa externa (hoje fechadas), coro alto/órgão, via-sacra, ambão/púlpito, pia batismal, confessionário, piso em xadrez, ReflectionProbe interno (G.3); exterior G.4 (panos salmão, sinos visíveis, trifório, escadaria com rampas reais); clareiras floridas do bosque; `visibility_range_end` 70 m das flores (hoje parte do `ground.gltf`); orçamento de triângulos das árvores; NPCs sentados na taverna.
4. Atualizar este handoff e commitar no `wip/city-fidelity`.

## Cuidado
- Nunca rodar `git worktree remove` com junction dentro do worktree: ele segue o link e apaga o destino. Remover o junction antes.
- Imagens de referência/Street View nunca entram neste repo público.
- `build_town_houses.py` importa `build_hub_scene.py` (plano de lotes): mudar `FIXED_LOTS`, `HOUSE_ARCHETYPES`, `TOWN_SEED` ou blocos muda o conjunto de modelos a gerar.
