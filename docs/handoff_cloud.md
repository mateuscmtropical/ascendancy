# Passagem de bastão: praça comercial (lojas grandes mobiliadas)

> Atualização da rodada 4 (nuvem, 2026-11-15): itens 6 (rotas da calçada norte: fregueses que param em cada porta), 7 (fazenda: `tools_src/build_farm.py`, quadra leste e campos além do muro) e 8 (caminho legado removido, `hub.tscn` conferido byte a byte) estão feitos no `wip/city-fidelity`. A quadra leste deixou de ter casas; o plano de lotes usa sub-seed por quadra. Falta o item 9 (revisão de design dos props) e medir fps.

Branch: `worktree-agent-a0d1245143d8ae131` (sai de `wip/city-fidelity`). Nada foi enviado ao remoto.

## Pedido do usuário

Casas de venda pequenas demais. Ele quer prédios de 1/3 a 1/2 de quarteirão, amplos, cheios de coisas por dentro, como um shopping a céu aberto. Zoneamento desenhado por ele:

- fileira norte inteira (ao norte da avenida da rotatória) = comércio e ofícios;
- quadra a oeste da praça oeste, de frente para a catedral = biblioteca, escola e seminário;
- quadra a leste da catedral e o terreno além do muro até x≈150 = casa do fazendeiro, lavouras e curral de vacas e porcos;
- fileira sul = residencial.

## Estado por quarteirão (`BLOCKS` e `FIXED_LOTS` em `tools_src/build_hub_scene.py`)

| Quadra | Conteúdo | Estado |
|---|---|---|
| Norte 0 (x −102..−72) | ferreiro (24 m) | casca e recheio prontos, 59 props |
| Norte 1 (x −64..−4) | armaduras, magia+encantador, alfaiate+joias (18 m cada) | prontos: 48, 69 e 62 props |
| Norte 2 (x 4..64) | taverna+estalagem, alquimia+ervas, armazém+padaria (18 m cada) | prontos: 39, 59 e 71 props |
| Norte 3 (x 72..102) | guilda+banco (24 m) | pronto, 59 props |
| Oeste (x −102..−72, z −48..48) | biblioteca, escola, seminário (30 m cada) | prontos: 112, 61 e 50 props |
| Leste (x 72..102, z −48..48) | ainda casas comuns | FALTA: fazenda (casa, lavouras, curral), nada começado |
| Sul (4 quadras) | casas dos arquétipos | regeneradas para o plano novo |

Os 13 ofícios da pesquisa (`docs/research/shops.md`) viraram 8 prédios com ala, porque a fileira norte só tem 24+54+54+24 m de frente. Alternativas se o usuário quiser os 13 separados: lojas de 12 m, ou uma segunda fileira além do muro.

## O que já foi validado com print

Fachadas das 11 lojas e interior das 11, na altura do olho (1,6 m), depois da correção da tinta de vértice e do recheio extra. Prints em `C:\Users\mateu\Downloads\jogo\` com prefixo `lojas_`.

## O que falta, em ordem

1. Juntar `wip/city-fidelity` neste branch (sons de passo e o que vier depois). Conflitos esperados: `.gltf.import` de lojas que este branch apagou (inn, bakery, jeweler, bank, bookshop, herbalist como prédio): resolver apagando. `features/hub/hub.tscn`, `tests/shots/shop_shots.tscn` e `features/hub/hub_navmesh.tres` são gerados: ficar com qualquer lado e regenerar.
2. Conferir `import_script/path="res://features/audio/tag_ground_surfaces.gd"` em TODOS os `art/town/shops/shop_*.gltf.import` (casca e `_interior`). Os de library, school, seminary e todos os `_interior` nasceram neste branch com o padrão antigo e não têm a linha.
3. `python tools_src/build_hub_scene.py`, reimportar, refazer a navmesh (o arquivo no commit é de ANTES do recheio extra dos salões, está desatualizado).
4. Testes GUT, gdformat e gdlint (único GDScript novo: `features/hub/shop_interior.gd`, já limpo).
5. Medir fps com o jogo do usuário fechado. Última medida limpa: 132 a 152 fps nas câmeras de fachada e interior (antes do recheio extra). As medidas de 12 a 20 fps do fim da sessão foram com a GPU a 98% por outro processo; não valem.
6. Conferir rotas de NPC na calçada norte (z≈−67,5) e os lojistas nos marcadores `keeper`.
7. Fazenda da quadra leste.
8. Remover o caminho legado: `add_kit_rows`, `add_shops`, `house_row`, `SHOP_HOUSES`, `SHOP_TYPES`, `SHOP_FRONTAGES` em `build_hub_scene.py`, `tools_src/build_shop_houses.py`, os construtores de banca e quintal em `build_shops.py` e a arte que só eles usam. Teste de segurança: `hub.tscn` tem de sair idêntico byte a byte antes e depois.
9. Revisão de design dos props no lugar (alguns são simples; nenhum foi redesenhado depois da primeira versão).
10. Avisar a sessão principal quando a cidade estiver pronta: ela vai gravar o vídeo promocional novo.

## Comandos

Blender 5.2 e Godot 4.7.2 só existem na máquina do usuário (Windows). Rodar da raiz do repo.

```
BLENDER="/c/Program Files/Blender Foundation/Blender 5.2/blender.exe"
G=tools/Godot_v4.7.2-stable_win64_console.exe

# cascas + recheios (todos, ou só os tipos pedidos; --interiors refaz só o recheio)
"$BLENDER" -b --factory-startup -P tools_src/build_market_shops.py -- [tipo...] [--interiors] 2>&1 | grep -E "BUILT|AVISO|Error|Traceback"
# casas que o plano pede e ainda não existem
"$BLENDER" -b --factory-startup -P tools_src/build_town_houses.py -- <nome_do_modelo>...
# cena da praça + tests/shots/shop_shots.tscn
python tools_src/build_hub_scene.py
# reimportar e refazer a navmesh
$G --headless --audio-driver Dummy --path . --import
$G --headless --audio-driver Dummy --path . -s tools_src/bake_hub_navmesh.gd
# testes
timeout 300 $G --headless --audio-driver Dummy --path . -s addons/gut/gut_cmdln.gd -gdir=res://tests/unit -gexit
# print: câmeras <Tipo><Vista>, Tipo = Smith Armor Magic Tailor Tavern Alchemy General Guild Library School Seminary,
# Vista = Front Door Inside Left Right Back Out
bash tools_src/shot.sh res://tests/shots/shop_shots.tscn <saida.png> GuildInside --character=male --hide-ui
```

`AVISO` na saída do Blender = prop sobreposto, fora do salão ou inexistente: corrigir a planta em `tools_src/shop_layouts.py`.

## Onde mexer

- `tools_src/build_market_shops.py`: tabela `SHOPS` (casca de cada prédio), `Room`, paredes, piso, teto, toldos, `Furnisher` (`put`, `on_wall`, `wall`, `grid`, `scatter`), `fill_floor`.
- `tools_src/shop_layouts.py`: `furnish_<tipo>` (planta), `PLANS` (lojista, pilares, paredes internas), `FILL` (ilhas soltas que enchem o chão livre).
- `tools_src/shop_props_common.py`, `_arms.py`, `_food.py`, `_arcane.py`: bibliotecas de props; `tools_src/build_prop_sheet.py` monta a folha de conferência.
- `tools_src/build_hub_scene.py`: `BLOCKS`, `SHOP_LOTS`, `FIXED_LOTS`, `SHOP_SIGNS`, `SHOPKEEPERS`, `add_shop_building`, `build_shop_shots`.
- `features/hub/shop_interior.gd`: recheio sem sombra e escondido além de 60 m.

## Armadilhas

- Tinta de vértice: o import glTF do Godot 4.7.2 deixa `vertex_color_use_as_albedo` DESLIGADO no material da primeira superfície de cada malha, que aparece branco. `untinted_first` em `build_town_houses.py` faz a junção começar por um material que nunca é tingido (brilho, vidro). Se o Blender imprimir `AVISO sem material neutro`, o modelo não tem material assim e o primeiro vai sair sem tinta. Casas geradas antes da correção só mudam ao regerar.
- `FLOOR_TOP = 0.05`: o piso do salão fica 5 cm acima do calçamento da quadra para não brigar com ele; props e soleira partem dessa altura. O colisor `WoodFloor*-colonly` (som de passo de madeira) tem o topo nessa mesma altura, só nas lojas de tábua (tavern, general, magic, alchemy, tailor, library, school).
- `import_script` dos `.gltf.import`: ver item 2 de "O que falta".
- O print reimporta tudo antes (até 5 min na primeira vez); em lote, importar uma vez e chamar o Godot por câmera. Se o script for morto no meio, sobra `override.cfg` na raiz: apagar.
- O Godot varre `tools/vendor` e imprime "Failed loading resource": inofensivo.
- Nunca escrever arquivo do OneDrive com `>>` do bash; usar Python `write_bytes`.
- Worktree: a pasta `tools` é uma junção para a do repo principal. Apagar a junção com `[System.IO.Directory]::Delete(caminho)` ANTES de remover o worktree, senão o git segue a junção e apaga o Godot. Recriar com `cmd /c mklink /J tools <repo>\tools`.
- Não fechar o jogo do usuário nem matar processo pelo nome. Com o jogo aberto a GPU fica ocupada e a medida de fps não vale.
