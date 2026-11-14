# Ascendancy (pasta local: projeto-torre)

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

Depois de editar código: `gdformat` + `gdlint` (zero aviso) + testes headless.

## Rodar e testar
- Jogar: `jogar.bat` (praça com escolha de personagem; `jogar.bat --character=female` pula a escolha; `--cinematic` roda o tour de câmera).
- Controles: WASD anda (trote), Shift corre, Ctrl caminha, Espaço pula, mouse gira câmera (clique captura, Esc solta).
- Testes headless (GUT 9.7.1 em `addons/gut`): `tools/Godot_v4.7.2-stable_win64_console.exe --headless --audio-driver Dummy --path . -s addons/gut/gut_cmdln.gd -gdir=res://tests/unit -gexit`.
- Prints: `bash tools_src/shot.sh res://tests/shots/hub_shots.tscn <saida.png> [Camera] [--character=male|--cinematic] [--shot-delay=s]` (janela 64x64 fora da tela, sem foco).
- Vídeo promocional: `bash tools_src/record.sh res://tests/promo/promo_reel.tscn <saida.avi>` (Movie Maker, 1080p60, roteiro em `tests/promo/promo_director.gd`); depois `ffmpeg -i saida.avi -i trilha.wav -map 0:v -map 1:a -c:v libx264 -crf 24 -pix_fmt yuv420p -c:a aac -shortest saida.mp4`.

## Pipeline de arte da praça (Blender 5.2 em background, depois Godot importa)
Ordem: `fetch_assets.py` (pacotes CC0 em `tools/vendor/`) → `build_characters.py` → `build_houses.py` → `build_cathedral.py` (gera texturas usadas pelos props) → `build_plaza_props.py` → `copy_kit_models.py` (natureza e props prontos) → `python tools_src/build_hub_scene.py` (escreve `features/hub/hub.tscn`; não editar a cena à mão, editar o gerador).
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
features/hub/      praça fixa da cidade inicial, NPCs andando
features/floor/    cena de andar, spawners, arena de chefe
features/player/   personagem, câmera, controle
features/combat/   hitbox, dano, habilidades, monstros
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
- Personagens: base Quaternius Universal Base Characters + Modular Character Outfits (CC0), montados por `tools_src/build_characters.py` no Blender → `art/characters/*.glb`. Mesmo esqueleto de 65 ossos das animações UAL1/UAL2 (CC0), sem retarget. Addon godot-vrm fica só como opção futura.
- Pacotes fonte: `python tools_src/fetch_assets.py` baixa para `tools/vendor/` (fora do git).
- Meta: 60 fps em 1080p num i7-11800H + RTX 3060 Laptop.

## Pesquisa
- `docs/research/architecture.md` — estrutura, rede, seed, projetos OSS de referência, testes.
- `docs/research/assets.md` — licenças (Mixamo, Quaternius, KayKit, VRoid/VRM, ambientes).
- `docs/research/aesthetic.md` — estética, render estilo Genshin, Godot, Blender.
- `docs/research/characters.md` — bases de personagem anime redistribuíveis.
