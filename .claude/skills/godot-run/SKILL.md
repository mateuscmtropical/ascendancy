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
timeout 120 $G --headless --path . -s addons/gut/gut_cmdln.gd -gdir=res://tests -gexit
```
`--headless` = renderer dummy: não gera imagem. Serve para rede, seed, combate, NPC.

## Prints (precisa de render real)
Testado em 2026-11-14:
- `window/size/initial_position` é forçado para (0,0) pelo Windows → não serve.
- Minimizar a janela para o render (trava) → não serve.
- Funciona: `window/size/no_focus=true` no projeto + no `_ready` do script de captura `DisplayServer.window_set_position(Vector2i(-20000, -20000))`. Janela aparece uma fração de segundo no monitor 0 e sai da tela; não rouba foco.
```
timeout 120 $G --path . --screen 0 --audio-driver Dummy --resolution 1920x1080 res://tests/shots/shot_runner.tscn -- --shot <nome> --eye x,y,z,yaw,pitch
```
Captura: esperar alguns frames + `await RenderingServer.frame_post_draw`, depois `get_viewport().get_texture().get_image().save_png()`.
Prints de trabalho: scratchpad. Imagem para o usuário ver: sempre em `C:\Users\mateu\Downloads\jogo\` com nome descritivo (nunca caminho do scratchpad).

## Validação visual
Todo print: ver inteiro + recortes ampliados (PIL, 2–3x) das áreas mudadas, na altura dos olhos do jogador (1.6 m). Ver skill `style-bible`.
