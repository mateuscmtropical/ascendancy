shader_type spatial;
render_mode blend_mix, unshaded, cull_disabled, depth_draw_never, shadows_disabled;

// Marca de lava no chão da Mula sem cabeça: ferradura (pegada) ou mancha (pingo) de borda roída por ruído. Nasce
// amarela, esfria para vermelho escuro, vira crosta cinza e some. Cada instância do MultiMesh traz em INSTANCE_CUSTOM
// a hora em que nasceu (x), uma semente (y) e a forma (z: 1 ferradura, 0 mancha); features/mobs/lava_marks.gd só
// atualiza `now_seconds`. A ferradura abre para -V (o calcanhar do casco).

uniform sampler2D noise_texture : repeat_enable, filter_linear_mipmap;
uniform float now_seconds = 0.0;
uniform float cooling_seconds = 5.0;
uniform float energy = 3.0;
uniform vec3 hot_color : source_color = vec3(1.0, 0.72, 0.2);
uniform vec3 cooling_color : source_color = vec3(0.5, 0.03, 0.005);
uniform vec3 crust_color : source_color = vec3(0.07, 0.065, 0.062);

varying float heat;
varying float seed;
varying float horseshoe;


void vertex() {
	heat = clamp(1.0 - (now_seconds - INSTANCE_CUSTOM.x) / cooling_seconds, 0.0, 1.0);
	seed = INSTANCE_CUSTOM.y;
	horseshoe = INSTANCE_CUSTOM.z;
}


void fragment() {
	vec2 from_center = (UV - 0.5) * 2.0;
	float radius = length(from_center);
	float ragged = texture(noise_texture, UV * 0.7 + vec2(seed, seed * 1.7)).r - 0.5;
	float heel_gap = (1.0 - smoothstep(0.2, 0.45, abs(from_center.x))) * step(from_center.y, 0.0);
	float stain = 1.0 - radius - ragged * 0.9;
	float shoe = 1.0 - abs(radius - 0.62) * 3.2 - ragged * 0.5 - heel_gap * 2.0;
	float shape = mix(stain, shoe, horseshoe);
	float core = smoothstep(0.15, 0.75, shape);
	float flicker = 0.85 + 0.15 * sin(TIME * 9.0 + seed * 40.0);
	float glow = smoothstep(0.2, 0.6, heat) * (0.4 + 0.6 * core) * flicker;
	vec3 lava = mix(cooling_color, hot_color, smoothstep(0.5, 1.0, heat) * core) * energy;

	ALBEDO = mix(crust_color, lava, glow);
	ALPHA = smoothstep(0.0, 0.2, shape) * smoothstep(0.0, 0.15, heat);
}
