---
name: godot-run
description: Como rodar o jogo, testes headless e tirar prints sem incomodar o usuário (sem som, sem foco, janela fora da tela). Use antes de qualquer execução do Godot neste projeto.
---

# Rodar Godot com segurança

G=tools/Godot_v4.7.2-stable_win64_console.exe (sempre a versão _console para ver a saída).

## Regras
- Nunca mandar input para janela, nunca mexer no mouse. Sem som (`--audio-driver Dummy`).
- Nunca matar processo pelo nome. Se travar, achar o PID pelo CommandLine (`Get-CimInstance Win32_Process`) e matar só o que você abriu.
- Godot abre ALERTA MODAL (OS.alert) em erro fatal (ex.: projeto sem cena principal, project.godot quebrado). Isso aparece na tela do usuário. Prevenção: antes de qualquer execução com janela, rode a mesma coisa com `--headless` (alerta vira só texto no console) e confira que não há erro.
- Sempre passar a cena explícita na linha de comando.
- Usar `timeout` em toda execução.

## Testes de lógica (sem janela nenhuma)
```
timeout 300 $G --headless --audio-driver Dummy --path . -s addons/gut/gut_cmdln.gd -gdir=res://tests/unit -gexit
```
`--headless` = renderer dummy: não gera imagem. Serve para rede, seed, combate, NPC.

## Prints (precisa de render real)
Sempre por `tools_src/shot.sh <cena.tscn> <saida.png> [NomeDaCamera3D]` (a cena precisa do nó `tests/shots/shot_capture.gd`). O script:
1. `--import` headless (rodar cena não reimporta asset alterado);
2. roda a cena `--headless` e aborta se houver ERROR (evita alerta modal na tela);
3. escreve `override.cfg` temporário: janela 64x64 sem borda, sem foco, sem splash, `stretch/mode=viewport` (render continua 1920x1080);
4. abre com `--screen 0`; no `_ready` a janela vai para (-20000,-20000); salva PNG e fecha; apaga `override.cfg`.
Usuário reclamou de janela grande abrindo na tela (2026-11-14): nunca abrir Godot com janela normal. `--position` negativo é ignorado (vai para 0,0 do monitor principal = monitor do usuário).
Não pôr "ERROR" em print de debug: o passo 2 trata como falha.
Godot no modo autocontido grava `user://` em `./Godot/app_userdata` (gitignored, com `.gdignore`).
Prints de trabalho: scratchpad. Imagem para o usuário ver: sempre em `C:\Users\mateu\Downloads\jogo\` com nome descritivo (nunca caminho do scratchpad).

## Validação visual
Todo print: ver inteiro + recortes ampliados (PIL, 2–3x) das áreas mudadas, na altura dos olhos do jogador (1.6 m). Ver skill `style-bible`.
