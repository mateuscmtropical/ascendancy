#!/usr/bin/env bash
# Grava uma cena em vídeo (Movie Maker do Godot, 30 fps fixos) sem roubar foco nem abrir alerta.
# A cena precisa fechar sozinha (ex.: tests/promo/promo_reel.tscn) e mover a janela para fora da tela.
# Uso: tools_src/record.sh <cena.tscn> <saida.avi> [argumentos extras da cena...]
set -euo pipefail

cd "$(dirname "$0")/.."

GODOT=tools/Godot_v4.7.2-stable_win64_console.exe
SCENE="$1"
OUTPUT="$(cygpath -m "$(realpath -m "$2")")"
EXTRA_ARGUMENTS=("${@:3}")
NOISE='Unreferenced static|string_name.cpp|leaked|RID alloc|Pages in use|paged_allocator|instance_notify|ObjectDB|still in use|Thread object|wait_to_finish|thread.cpp|resource.cpp|object.cpp|utilities.cpp|user://'

timeout 300 "$GODOT" --headless --path . --import > /dev/null 2>&1 || true

# Sem sincronia com o relógio (--fixed-fps), o roteiro inteiro roda em segundos no headless.
headless_log="$(timeout 120 "$GODOT" --headless --path . --audio-driver Dummy --fixed-fps 30 "$SCENE" -- "${EXTRA_ARGUMENTS[@]}" 2>&1 || true)"

if echo "$headless_log" | grep -vE "$NOISE" | grep -qE "ERROR|SCRIPT ERROR|Parse Error"; then
	echo "$headless_log" | grep -vE "$NOISE"
	echo "headless check failed; not opening a window" >&2
	exit 1
fi

cat > override.cfg <<'CFG'
[application]

boot_splash/show_image=false

[display]

window/size/no_focus=true
window/size/borderless=true
window/size/window_width_override=64
window/size/window_height_override=64
window/stretch/mode="viewport"

[editor]

movie_writer/fps=30
movie_writer/mjpeg_quality=0.95
CFG
trap 'rm -f override.cfg' EXIT

timeout 600 "$GODOT" --path . --screen 0 --write-movie "$OUTPUT" "$SCENE" -- "${EXTRA_ARGUMENTS[@]}" 2>&1 | grep -E "ERROR|Movie" | grep -vE "$NOISE" || true
ls -la "$OUTPUT"
