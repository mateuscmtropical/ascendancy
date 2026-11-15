# Handoff rodada 3 (2026-11-15)

Branch de trabalho: `wip/city-fidelity`. Spec de design: `docs/handoff/city_design_v2.md` (seções A–L, prioridade em F).
Regras do projeto em `CLAUDE.md` (obrigatórias). Agentes auxiliares: nunca Fable.

## Feito e integrado em wip/city-fidelity
- Escadas (catedral, presbitério, coreto) com rampa de colisão que sobe até o piso; pulo firme; corrida nova; voo de debug (dois toques no Espaço); pés no chão; contador de FPS.
- Layout das praças da spec A.4 (esplanada, largo do chafariz, 2 largos oeste, 2 rondéis leste, coreto em (−46, −13) no gramado, bosque Poisson na São José), regra `can_plant()` (J), palmeiras em fileiras (A.5), sebes de 0,5 m em todo canteiro com vãos e topiaria (H), rotatória real com pista em anel e calçadas recortadas em arco (K), obelisco do Marco.
- Água fluida da fonte grande (seção I parcial: jatos, cortinas, superfícies animadas, respingo). Colisor da fonte grande r 6,0.

## Trabalho parcial de agentes (branches com snapshot WIP, NÃO integrados)
| Branch | Base | Conteúdo | Observação |
|---|---|---|---|
| `wip/agent-cathedral` | 205c2a4 | `build_cathedral.py` + texturas novas (vitrais com pomba, retábulo, óculo) — seções E e G | Não terminado: conferir o que falta de E/G, terminar, regenerar `cathedral.gltf`. Se `CATHEDRAL_FACADE_X` mudar para 13, atualizar `build_hub_scene.py` e testes. |
| `wip/agent-houses-shops` | 205c2a4 | só `tools_src/build_town_houses.py` (557 linhas, inacabado) — seções C e D | Terminar: 12 arquétipos de casa distintos, lotes sem sobreposição (assert de AABB), lojas de RPG entráveis (ferreiro, armeiro, magia, alquimia, taverna...) com interior e porta. |
| `wip/agent-trees` | **b4c7d73 (base velha)** | `build_trees.py`, `art/town/trees/old_tree_1..6`, `art/town/palm_9/11/14`, materiais — seções B e L.1 | Trazer só os arquivos novos para cima de wip/city-fidelity (`git checkout wip/agent-trees -- <arquivos>`), sem reverter nada. Apagar lixo de depuração se houver (ex.: `inspect.py`). Flores (L.1) não feitas. |

## Pendente (ordem)
1. Integrar os três branches acima (resolver conflitos mantendo tudo de wip/city-fidelity), terminar o que falta de cada um.
2. Trocar os modelos em `PLANT_MODELS` de `build_hub_scene.py` pelos novos (tree_old, tree_bloom, palm) e ajustar `TRUNK_RADIUS`/escala aos raios reais.
3. Flores L.1/L.2 (manchas baixas geradas em `build_ground.py`, cores por mancha; tirar tulipas grandes dos gramados — já tiradas).
4. Fonte pequena da rotatória com a receita de água da seção I.
5. Rebake da navmesh (`tools_src/bake_hub_navmesh.gd`) depois de qualquer mudança de prédio/prop.
6. Testes GUT, gdformat + gdlint zero aviso, prints com `tools_src/shot.sh` (câmeras em `tests/shots/hub_shots.tscn`, inclusive `AerialTop`) + recortes ampliados; comparar com as referências do repo privado `ascendancy-refs`.
7. Atualizar este handoff e commitar no `wip/city-fidelity`.

## Cuidado
- Nunca rodar `git worktree remove` com junction dentro do worktree: ele segue o link e apaga o destino. Remover o junction antes.
- Imagens de referência/Street View nunca entram neste repo público.
