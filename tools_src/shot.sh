#!/usr/bin/env bash
# Print de uma cena sem roubar foco nem abrir alerta na tela do usuário.
# Uso: tools_src/shot.sh <cena.tscn> <saida.png> [NomeDaCamera3D] [argumentos extras da cena...]
set -euo pipefail

cd "$(dirname "$0")/.."

GODOT=tools/Godot_v4.7.2-stable_win64_console.exe
SCENE="$1"
OUTPUT="$(cygpath -m "$(realpath -m "$2")")"
CAMERA_ARGUMENT="${3:+--camera=$3}"
EXTRA_ARGUMENTS=("${@:4}")
NOISE='Unreferenced static|string_name.cpp|leaked|RID alloc|Pages in use|paged_allocator|instance_notify|ObjectDB|still in use|Thread object|wait_to_finish|thread.cpp|resource.cpp|object.cpp|utilities.cpp'

timeout 300 "$GODOT" --headless --path . --import > /dev/null 2>&1 || true

headless_log="$(timeout 60 "$GODOT" --headless --path . --audio-driver Dummy "$SCENE" -- $CAMERA_ARGUMENT "${EXTRA_ARGUMENTS[@]}" 2>&1 || true)"

if echo "$headless_log" | grep -vE "$NOISE" | grep -qE "ERROR|SCRIPT ERROR|Parse Error"; then
	echo "$headless_log" | grep -vE "$NOISE"
	echo "headless check failed; not opening a window" >&2
	exit 1
fi

# Janela 64x64 sem borda, sem foco, pedida fora da tela; o render segue 1920x1080 (stretch viewport).
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

timeout 120 "$GODOT" --path . --screen 0 --audio-driver Dummy "$SCENE" \
	-- --shot-out="$OUTPUT" $CAMERA_ARGUMENT "${EXTRA_ARGUMENTS[@]}" 2>&1 | grep -E "SHOT|ERROR" | grep -vE "$NOISE" || true
