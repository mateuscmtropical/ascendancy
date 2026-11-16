#!/usr/bin/env bash
# Benchmark de fps por camera (janela 64x64 fora da tela, render 1920x1080), sem foco nem som.
# Uso: tools_src/fps_bench.sh [argumentos do fps_bench.gd: --cameras=A,B --time-of-day=0.8 --disable=ssao,...]
set -euo pipefail

cd "$(dirname "$0")/.."

GODOT=tools/Godot_v4.7.2-stable_win64_console.exe

cat > override.cfg <<'CFG'
[application]

boot_splash/show_image=false

[display]

window/size/no_focus=true
window/size/borderless=true
window/size/window_width_override=64
window/size/window_height_override=64
window/stretch/mode="viewport"
CFG
trap 'rm -f override.cfg' EXIT

timeout 900 "$GODOT" --path . --screen 0 --audio-driver Dummy res://tests/shots/fps_bench.tscn \
	-- "$@" 2>&1 | grep -E "BENCH|ERROR" || true
