# Ascendancy

Action RPG em terceira pessoa, fantasia estilizada (referências de clima: anime Sword Art Online + Monster Hunter). Personagens no design Quaternius Universal Base Characters, aprovado pelo usuário. Single-player e online no mesmo código. Repositório público (código MIT).

## Regras do usuário (obrigatórias)
- Responda sempre em português do Brasil.
- Nunca feche o jogo do usuário nem mate processos pelo nome; só por PID de processo que você mesmo abriu.
- Testes: sem som, sem pegar/mover mouse, nunca mandar input para janela, só execução roteirizada. Usuário trabalha no monitor 2; janela de teste só no monitor 0 (notebook) ou fora da tela. Ver skill `godot-run`.
- Toda mudança visual validada com prints + recortes ampliados na visão do jogador. Ver skill `style-bible`.
- Código do jogo limpo, sem gambiarra. Scripts geradores de uso único podem ser simples.
- Nunca recriar mapas, personagens ou visual de jogos/animes existentes. Referência é só de clima; tudo original (nada de Aincrad, Kirito, Genshin, Monster Hunter).
- Só assets com licença que permita repo público (CC0, CC-BY, MIT, VRM com redistribuição liberada). Nada de Mixamo no repo. Ver skill `asset-intake`.
- Subagentes: no máximo 3 Haiku em paralelo, reaproveitar os mesmos via SendMessage. Personagem e animação: sessão principal faz.
- Commit local; push só quando pedido. Identidade git: mateuscmtropical (noreply). Nunca usar email pessoal.
- Guardar só resultado final; apagar temporários.
- Imagem para o usuário ver: sempre em `C:\Users\mateu\Downloads\jogo\` com nome descritivo.
- Aviso sonoro no fim de cada turno é automático (hook Stop em `Games/.claude`). Quando precisar do usuário, terminar o turno com uma pergunta clara.

## Qual skill carregar (obrigatório, antes da primeira ação do tipo)
| Tarefa | Skill |
|---|---|
| Escrever/editar GDScript ou shader | `gdscript-code-style` |
| Rodar Godot, testes, prints | `godot-run` |
| Arte, cena, luz, shader, validação visual | `style-bible` |
| Baixar/importar modelo, textura, animação, addon | `asset-intake` |
| Vídeo de divulgação, trailer, teaser (listar os já feitos, não repetir) | `promo-video` |
| Voz, música, modelo 3D ou arte gerados por IA; qualquer vídeo ou áudio (lembrar dos recursos) | `creative-tools` |

Depois de editar código: `gdformat` + `gdlint` (zero aviso) + testes headless.

## Rodar e testar
- Jogar: `jogar.bat` (praça com escolha de personagem; `jogar.bat --character=female` pula a escolha; `--cinematic` roda o tour de câmera).
- Controles: WASD anda (trote), Shift corre, Ctrl caminha, Espaço pula, mouse gira câmera (clique captura, Esc solta), botão esquerdo ou F soca, botão direito ou G chuta (apertar de novo durante o golpe encadeia o combo).
- Testes headless (GUT 9.7.1 em `addons/gut`): `tools/Godot_v4.7.2-stable_win64_console.exe --headless --audio-driver Dummy --path . -s addons/gut/gut_cmdln.gd -gdir=res://tests/unit -gexit`.
- Prints: `bash tools_src/shot.sh res://tests/shots/hub_shots.tscn <saida.png> [Camera] [--character=male|--cinematic] [--shot-delay=s]` (janela 64x64 fora da tela, sem foco).
- Prints de luta e rosto: `bash tools_src/shot.sh res://tests/shots/fight_shots.tscn <saida.png> <FightSide|FightThree|FightFront|FaceClose> [--character=female] [--animation=combat/Kick_Side --seconds=0.4] [--mood=effort] [--blink]` (congela o clipe no instante pedido e o rosto na expressão).
- Vídeo promocional: `bash tools_src/record.sh res://tests/promo/promo_reel.tscn <saida.avi>` (Movie Maker, 1080p30, roteiros em `tests/promo/promo_shots.gd`, diretor em `tests/promo/promo_director.gd`) + `python tools_src/compose_promo_music.py <trilha.wav> 77.5` (calma) ou `python tools_src/compose_epic_music.py <trilha.wav> 77.5` (épica: taikos, cordas, metais, coro); juntar em versão comprimida: `ffmpeg -i saida.avi -i trilha.wav -map 0:v -map 1:a -vf scale=1280:-2 -c:v libx264 -preset slow -crf 28 -pix_fmt yuv420p -c:a aac -b:a 128k -shortest saida.mp4`.
- Trailer de marketing (edição fora do motor): `RECORD_FPS=60 bash tools_src/record.sh res://tests/promo/marketing.tscn <cru.avi>` (clipes crus de `tests/promo/marketing_shots.gd`, espada em `tests/promo/hero_sword.gd`) → `python tools_src/compose_marketing_music.py <trilha.wav>` → `python tools_src/cut_marketing_trailer.py <cru.avi> <trilha.wav> <pasta das fontes Cinzel> <pasta de trabalho> <saida.mp4> [MB]` (cortes, câmera lenta, tremor, clarões, cor, letreiros, letterbox 2.39 e grão; a lista de cortes e os efeitos da trilha ficam juntos em `tools_src/marketing_timeline.py`). Fontes Cinzel (OFL) ficam fora do repo.

## Pipeline de arte da praça (Blender 5.2 em background, depois Godot importa)
Ordem: `fetch_assets.py` (pacotes CC0 em `tools/vendor/`) → `build_characters.py` → `build_cathedral.py` (gera texturas usadas pelos props) → `build_plaza_props.py` (chafariz, fonte pequena, coreto, poste, vaso) → `build_trees.py` (árvores velhas `art/town/trees/old_tree_*`, ipês `tree_bloom_*`, palmeiras `art/town/palm_9/11/14`) → `build_ground.py` (chão: ruas rebaixadas, meio-fio, canteiros elevados, sebes, flores; lê o layout de `build_hub_scene.py`) → `build_shops.py` (placas por tipo de loja em `art/town/shops/`) → `build_town_houses.py` (casas dos 12 arquétipos em `art/town/houses/`, com sidecar JSON; lê o plano de lotes `town_lots()` de `build_hub_scene.py`; `-- nome...` gera só os modelos pedidos) → `build_market_shops.py` (prédios grandes do comércio e da quadra cívica: casca `art/town/shops/shop_<tipo>.gltf` e recheio `shop_<tipo>_interior.gltf`; a tabela `SHOPS` define cada casca, `shop_layouts.py` a planta de cada salão e as bibliotecas `shop_props_*.py` os móveis e mercadorias; `-- tipo... [--interiors]` refaz só os pedidos; `build_prop_sheet.py` monta a folha de conferência dos props) → `build_casarao.py` (casarão de azulejo na quadra em frente à catedral, `art/town/casarao.gltf`: sobrado de dois andares andáveis com um só portal para a rua; cinco salões marcados `casarao=True` em `SHOPS`: no térreo biblioteca | vestíbulo | escola, no andar nobre sala de leitura | galeria | seminário, ligados por portas internas junto à fachada (`INNER_DOOR`); o vestíbulo é a casca de dois andares de `casarao_vestibule.py`, com a escadaria imperial, a galeria em volta do vão e a sacada andável; os móveis de solar ficam em `shop_props_manor.py`; `build_casarao.py` veste a fachada dos dois andares, fecha as juntas entre os salões e põe platibanda, frontão, telhado e mirante; rodar depois de mudar esses salões; `-- <salões> --plan=<pasta>` em `build_market_shops.py` grava as pegadas dos móveis para desenhar a planta) → `build_farm.py` (fazenda do quarteirão 5 e campos além do muro leste em `art/town/farm/`: casa, celeiro, terreiro, pasto, chiqueiro, lavouras, carroças, moinho d'água e monjolo no canto leste do pasto; plano em `FARM_*` de `build_hub_scene.py`; a roda `water_wheel.gltf` e o braço `monjolo_beam.gltf` são modelos à parte, postos pela cena nos marcadores do sidecar de `farm_fields` e movidos por `features/hub/water_wheel.gd` e `monjolo.gd`) → `convert_farm_animals.py` (vaca, porco e cavalo do pacote CC0 de animais para `art/town/farm/animals/`; sem eles a cena fica sem bichos e sem carroças) → `copy_kit_models.py` (natureza e props prontos) → `python tools_src/build_hub_scene.py` (escreve `features/hub/hub.tscn`; não editar a cena à mão, editar o gerador; falha com a lista dos modelos que faltam se `build_town_houses.py`/`build_market_shops.py` não rodaram).
  Depois: `tools/Godot_v4.7.2-stable_win64_console.exe --headless --path . -s tools_src/bake_hub_navmesh.gd` (navmesh dos NPCs em `features/hub/hub_navmesh.tres`; rodar de novo sempre que mudar prédio/prop de lugar).
- Sons: `python tools_src/compose_sounds.py` sintetiza tudo (sem gravação de terceiros) em `art/audio/`: passos, pulo e pouso por piso (pedra, grama, madeira; um `AudioStreamRandomizer` .tres por conjunto), chafariz, ambiente da praça, sino, menu. Música calma da praça: `python tools_src/compose_town_music.py` (sintetizada, estéreo, loop ~2:30 em `art/audio/town_music_loop.wav`, canal Music). Piso: o script de import `features/audio/tag_ground_surfaces.gd` marca o corpo estático pelo nome do colisor sem o número (`Bed`/`Hedge` grama, `WoodFloor` madeira, `Yard`/`Path`/`Field` terra, resto pedra) e troca os vidros que acendem à noite (`features/sky/window_glass.gd`: `M_TownGlass` das janelas por `art/materials/window_glass.tres`, `M_TownShopfront` das vitrines das lojas por `art/materials/shopfront_glass.tres`; `M_TownVitrine` dos móveis fica liso; mudou o script de import = reimportar tudo: apagar `.godot/imported/*.gltf-*.md5` e rodar `--import`). Loops com `edit/loop_mode=2` no `.import`. Canais em `default_bus_layout.tres` (Master, Ambient, Effects, Music), volume na aba Audio do Esc.
- Mobs: `tools_src/build_mula_sem_cabeca.py` (Blender em background; `-- --source <Horse.fbx|.glb>` troca a fonte) gera a Mula sem cabeça em `art/mobs/mula_sem_cabeca/` sobre o esqueleto e as animações do cavalo CC0 (`tools/vendor/animals/FBX/Horse.fbx`): corpo vindo do "Equine Model" de Lova Dahn (CC BY 4.0, crédito em CREDITS.md; o .obj exige login no Sketchfab e fica em `tools/vendor/mobs/equine_model/`, fora do git) adaptado por `tools_src/mula_base.py` (forma da base mantida, só pescoço erguido/engrossado e peito um pouco mais cheio; os ossos do cavalo CC0 é que vão para as juntas da malha, pesos automáticos do Blender, relevo e oclusão do .obj inteiro em bake para a malha de jogo de ~40 mil triângulos); o corpo procedural antigo em partes segue sem uso em `tools_src/mula_parts.py` (tabela `PARTS`, pesos por parte) e fundido em `tools_src/mula_body.py` (remesh voxel, relevo, toco cortado com cratera de brasa; `-- --silhouette <json>` grava a silhueta lateral e o sidecar traz as proporções medidas), veias de lava (`MulaVeins`, shader `art/shaders/lava_vein.gdshader`), correntes partidas (`MulaChains`, ossos `Chain<n>`), labaredas em fita do toco, crina, rabo e cascos (`MulaFlames`, shader `art/shaders/flame_ribbon.gdshader`, que abre cada tira de frente para a câmera), marcadores de fogo `Fire*` presos aos ossos (brasas, fumaça e luz) e texturas assadas. O gerador grava o hash do `.bin` no `.gltf` (o Godot só reimporta quando o texto do `.gltf` muda); o glTF inverte o V das UVs, por isso o gerador grava `1 - valor`. Cena `features/mobs/mula_sem_cabeca.tscn` (pendura as partículas de `FireTemplates` nos marcadores; na animação `Death` o fogo apaga; exceção realista à style bible, sem contorno). Prints: `bash tools_src/shot.sh res://tests/shots/mula_shots.tscn <saida.png> <MulaThreeQuarter|MulaSide|MulaBack|MulaNeck|MulaHooves|MulaRun|MulaScale|MulaFootprints|MulaFront|MulaChest> [--animation=Walk|Run|Attack|Death]`.
- NPCs: CharacterBody3D + NavigationAgent3D com avoidance; parados viram NavigationObstacle3D. Camadas de física: 1 mundo, 2 jogador, 3 NPC.
- Malha com nome `*-colonly` vira colisão estática no Godot. Material `M_Water` é trocado por `art/materials/water.tres` via `_subresources` no `.import`.

## Ferramentas
- Godot 4.7.2 portátil em `tools/` (modo autocontido, `tools/._sc_`). Fora do git. Para desinstalar: apagar `tools/`.
  - Editor/jogo: `tools/Godot_v4.7.2-stable_win64.exe`; CLI com console: `tools/Godot_v4.7.2-stable_win64_console.exe`.
- Blender 5.2 instalado no sistema (`C:\Program Files\Blender Foundation\Blender 5.2\blender.exe`); usar em modo `--background --python script.py`.
- GDScript (sem .NET), tipagem estática.
- Linter/formatador: gdtoolkit 4.5 em `tools/pyenv` (`tools/pyenv/Scripts/python.exe -m gdtoolkit.linter` / `gdtoolkit.formatter`; os .exe do venv falham calados), config `gdlintrc`.

## Arquitetura
```
addons/            terceiros (godot-vrm, netfox, gut...) — licença em CREDITS.md
core/              autoloads finos: Game (estado global), Net (sessão), Events (sinais)
net/               Session, servidor, cliente, definições de RPC
world/             geração por seed (GDScript puro, sem nós) — floors, layouts
features/hub/      praça fixa da cidade inicial, NPCs andando, bichos da fazenda, carroças
features/mobs/     visual dos monstros (Mula sem cabeça)
features/sky/      céu: relógio do dia (SkyClock), eventos sorteados por sub-seed (SkyEvents), ciclo dia/noite
features/floor/    cena de andar, spawners, arena de chefe
features/player/   personagem, câmera, controle
features/combat/   luta sem arma (UnarmedFighter); depois hitbox, dano, habilidades, monstros
data/              Resources (.gd class_name + .tres): itens, monstros, andares
art/               modelos .glb, texturas, shaders (art/shaders), fontes .blend em art/src
tests/             testes headless (GUT)
tools_src/         scripts geradores (Blender bpy, Python)
docs/              pesquisa e decisões (docs/research/*.md)
```
- Nomes snake_case em arquivos/pastas, PascalCase em nós. Cena autocontida; dependências injetadas por sinal/export.
- Autoload só para sistema dono dos próprios dados com acesso global.
- Dados em `Resource` (`class_name` + `@export`); `duplicate()` para estado mutável por instância.

### Rede (um código, três modos)
- Single-player = servidor local ENet + cliente local na mesma instância. O jogador do host passa pelo mesmo caminho do servidor (sem atalho).
- "Abrir para amigos": o servidor local passa a aceitar conexões (ENet UDP). UPnP (`UPNP`, em Thread) tenta abrir a porta; senão, instrução de abrir porta. Depois: relay noray (MIT). Steam opcional no futuro.
- Servidor dedicado: mesmo projeto, preset de export "dedicated server" (`OS.has_feature("dedicated_server")`), roda `--headless`.
- Servidor autoritativo: cliente manda intenção de input numerada; servidor valida posição, combate, dano, inventário, chefe. Movimento/esquiva com predição + reconciliação no cliente; entidades remotas interpoladas. Considerar netfox (MIT).
- `MultiplayerSpawner`/`MultiplayerSynchronizer` para spawn e propriedades replicadas.

### Mundo e andares
- Praça/cidade do andar é fixa (cena feita à mão). O exterior de cada andar é gerado por seed.
- Mundo pequeno, dividido em andares; cada andar tem 1–2 chefes. Derrotar o chefe libera subir. No multiplayer, kill do host sobe o grupo inteiro. Voltar a um andar vencido: lutar de novo ou subir direto. Meta futura: ~100 andares.
- Determinismo: sub-seeds por hash próprio (`hash(world_seed, floor, cx, cy, camada)`), sem RNG compartilhado entre etapas. Layout em grade de inteiros. Join manda seed + versão do gerador; cliente devolve checksum do layout; servidor recusa divergência. Decoração cosmética pode ser só do cliente.

## Visual
Resumo em `.claude/skills/style-bible/SKILL.md`; pesquisa completa em `docs/research/aesthetic.md`.
- Forward+, sol único quente, GI assado (LightmapGI) na cidade, SSAO/SSIL meia resolução, tonemap Linear/Filmic leve + LUT, contorno inverted hull, sombras coloridas (nunca cinza).
- Personagens: base Quaternius Universal Base Characters + Modular Character Outfits (CC0), montados por `tools_src/build_characters.py` no Blender → `art/characters/*.gltf`. Mesmo esqueleto de 65 ossos das animações UAL1/UAL2 (CC0), sem retarget. Addon godot-vrm fica só como opção futura. Nenhuma malha pode se chamar como um osso (a da cabeça é `Head_Skin`): o Godot renomeia o osso e as animações param de movê-lo.
- Rosto: o esqueleto não tem ossos de rosto; `tools_src/face_shapes.py` (chamado por `build_characters.py`) esculpe blend shapes na cabeça, nos olhos e nas sobrancelhas medindo a própria malha (`blink_l/r`, `squint`, `eyes_wide`, `brow_up/angry/sad`, `smile`, `frown`, `mouth_open`, `look_left/right/up/down`). `features/player/face_animator.gd` (nó `FaceAnimator` de `character_model.tscn`) pisca sozinho, passeia o olhar e mistura as expressões de `FaceAnimator.Mood`; `CharacterModel.show_expression()` mostra uma passageira e `rest_expression()` troca a de descanso.
- Luta sem arma: `tools_src/build_combat_animations.py` (Blender em background) escreve `art/animations/combat.glb` (biblioteca `combat`: `Fight_Idle`, `Kick_Front`, `Kick_Roundhouse`, `Kick_Side`, `Punch_Uppercut`, `Punch_Hook`) a partir de tabelas de poses-chave por clipe (quadril, mãos, pés, giro do tronco), interpoladas por spline, resolvidas com IK de dois ossos e gravadas a 60 quadros/s; todo clipe começa e termina na guarda do `Punch_Jab` da UAL1, por isso encadeia sem tranco. O esqueleto da UAL descansa em outra postura (pescoço e peito) e o Godot toca as rotações locais da biblioteca como estão: no Blender, a pose de um clipe da UAL tem de ser copiada osso a osso da armadura da própria biblioteca (`copy_library_pose`), nunca aplicando a ação no personagem (sairia torta em até 17°). `features/combat/unarmed_fighter.gd` (nó `UnarmedFighter` do jogador) guarda a sequência dos combos, o pedido feito cedo e os tempos de acerto e de corte de cada golpe (mudou um clipe = conferir as tabelas `*_SECONDS_BY_MOVE`).
- Pacotes fonte: `python tools_src/fetch_assets.py` baixa para `tools/vendor/` (fora do git).
- Céu e hora do dia: `art/shaders/sky.gdshader` (gradiente, nuvens, lua, estrelas cadentes, eclipses; de noite estrelas procedurais em camadas sobre as faces do cubo, juntas num redemoinho de dois braços, um quente e um frio, com halo, raios de difração e um astro dourado; uniforms `swirl_*` e `orb_*` ajustam) movido por `features/sky/day_night_cycle.gd` (nó `DayNight` da praça; ciclo de 24 min, metade dia, metade noite). À noite mudam sol/lua, luz ambiente, névoa e exposição; postes (grupo `night_lights`) e janelas (global `night_glow`) acendem. Câmeras do céu em `tests/shots/hub_shots.tscn`: `SkySwirl`, `SkyZenith`, `SkySouthUp`, `SkyEastUp`, `TownSwirl`; vídeo do céu noturno: `bash tools_src/record.sh res://tests/shots/sky_pan.tscn <saida.avi>`. Prints em outra hora: `--time-of-day=0.75` (0 nascer, 0,25 meio-dia, 0,5 pôr do sol); evento forçado: `--sky-event=shower|solar|lunar`.
- Meta: 60 fps em 1080p num i7-11800H + RTX 3060 Laptop.
- Texturas: mipmap ligado nas opacas (padrão em `[importer_defaults]`; sem mip, textura 2K distante estoura o cache da GPU). Textura de folhagem com alpha scissor fica sem mipmap (o mip afina as folhas): desligar no `.import` dela. `texture_mipmap_bias=-4` mantém a nitidez distante que a cena tinha sem mip.

## Pesquisa
- `docs/research/architecture.md` — estrutura, rede, seed, projetos OSS de referência, testes.
- `docs/research/assets.md` — licenças (Mixamo, Quaternius, KayKit, VRoid/VRM, ambientes).
- `docs/research/aesthetic.md` — estética, render estilo Genshin, Godot, Blender.
- `docs/research/characters.md` — bases de personagem anime redistribuíveis.
- `docs/research/shops.md` — lojas, taverna e guilda: o que tem dentro de cada uma e tamanho dos prédios.
