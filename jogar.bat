@echo off
rem Abre a praça de Ascendancy. Usa o Godot portátil de tools\ se existir; senão, "godot" do PATH.
rem Argumentos opcionais: --character=male|female (pula a escolha) ou --cinematic (tour de câmera).
cd /d "%~dp0"
set GODOT=tools\Godot_v4.7.2-stable_win64.exe
if not exist "%GODOT%" set GODOT=godot
start "" "%GODOT%" --path . res://features/hub/hub.tscn -- %*
