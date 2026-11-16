shader_type spatial;
render_mode blend_add, unshaded, cull_disabled, depth_draw_never, shadows_disabled;

// Chama de partícula: quad virado para a câmera, forma roída por ruído que sobe, cor pela temperatura
// (heat_ramp: frio à esquerda, quente à direita). O ângulo sorteado da partícula serve de semente.

uniform sampler2D noise_texture : repeat_enable, filter_linear_mipmap;
uniform sampler2D heat_ramp : repeat_disable, source_color;
uniform float energy = 1.6;
uniform float scroll_speed = 1.2;
uniform float erosion = 1.0;

varying float life;
varying float seed;
varying vec4 tint;


void vertex() {
	mat4 facing_camera = mat4(
			normalize(INV_VIEW_MATRIX[0]) * length(MODEL_MATRIX[0]),
			normalize(INV_VIEW_MATRIX[1]) * length(MODEL_MATRIX[1]),
			normalize(INV_VIEW_MATRIX[2]) * length(MODEL_MATRIX[2]),
			MODEL_MATRIX[3]);

	life = INSTANCE_CUSTOM.y;
	seed = INSTANCE_CUSTOM.x;
	tint = COLOR;
	MODELVIEW_MATRIX = VIEW_MATRIX * facing_camera;
	MODELVIEW_NORMAL_MATRIX = mat3(MODELVIEW_MATRIX);
}


void fragment() {
	float rise = 1.0 - UV.y;
	vec2 noise_uv = UV * 0.55 + vec2(seed * 0.37, TIME * scroll_speed + seed * 1.3);
	float coarse = texture(noise_texture, noise_uv).r;
	float fine = texture(noise_texture, noise_uv * 2.3 + vec2(0.4, TIME * scroll_speed * 0.6)).r;
	vec2 centered = UV - 0.5;

	centered.x += (coarse - 0.5) * 0.25 * (0.3 + rise);

	float edge_distance = length(centered * vec2(2.6, 2.0));
	float heat = 1.0 - edge_distance - (coarse * 0.9 + fine * 0.5 - 0.45) * (0.35 + rise * 0.9) * erosion;

	heat *= 1.0 - life * 0.55;

	ALBEDO = texture(heat_ramp, vec2(clamp(heat * 1.25, 0.0, 1.0), 0.5)).rgb * tint.rgb * energy;
	ALPHA = smoothstep(0.03, 0.3, heat) * tint.a;
}
