shader_type spatial;
render_mode blend_mix, unshaded, cull_disabled, depth_draw_never, shadows_disabled;

// Marca de lava no chão (pegada ou pingo da Mula sem cabeça): mancha de borda roída por ruído, miolo amarelo que
// esfria para vermelho e depois vira crosta escura e some. Cada instância do MultiMesh traz em INSTANCE_CUSTOM a
// hora em que nasceu (x) e uma semente (y); features/mobs/lava_marks.gd só atualiza `now_seconds`.

uniform sampler2D noise_texture : repeat_enable, filter_linear_mipmap;
uniform float now_seconds = 0.0;
uniform float cooling_seconds = 5.0;
uniform float energy = 3.5;
uniform vec3 hot_color : source_color = vec3(1.0, 0.72, 0.2);
uniform vec3 cooling_color : source_color = vec3(0.85, 0.1, 0.01);
uniform vec3 crust_color : source_color = vec3(0.02, 0.012, 0.01);

varying float heat;
varying float seed;


void vertex() {
	heat = clamp(1.0 - (now_seconds - INSTANCE_CUSTOM.x) / cooling_seconds, 0.0, 1.0);
	seed = INSTANCE_CUSTOM.y;
}


void fragment() {
	float ragged = texture(noise_texture, UV * 0.7 + vec2(seed, seed * 1.7)).r;
	float blob = 1.0 - length((UV - 0.5) * 2.0) - (ragged - 0.5) * 0.9;
	float core = smoothstep(0.15, 0.75, blob);
	float flicker = 0.85 + 0.15 * sin(TIME * 9.0 + seed * 40.0);
	float glow = heat * heat * (0.3 + 0.7 * core) * flicker;
	vec3 lava = mix(cooling_color, hot_color, core * heat) * energy;

	ALBEDO = mix(crust_color, lava, glow);
	ALPHA = smoothstep(0.0, 0.2, blob) * smoothstep(0.0, 0.2, heat);
}
