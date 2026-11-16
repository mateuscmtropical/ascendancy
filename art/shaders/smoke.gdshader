shader_type spatial;
render_mode blend_mix, unshaded, cull_disabled, depth_draw_never, shadows_disabled;

// Fumaça de partícula: quad virado para a câmera, novelo roído por ruído; a base ainda pega o clarão do fogo
// (ember_color some com a idade da partícula).

uniform sampler2D noise_texture : repeat_enable, filter_linear_mipmap;
uniform vec3 smoke_color : source_color = vec3(0.03, 0.028, 0.03);
uniform vec3 ember_color : source_color = vec3(0.5, 0.12, 0.02);
uniform float density = 0.55;

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
	vec2 noise_uv = UV * 0.8 + vec2(seed * 0.61, seed * 0.23 + TIME * 0.12);
	float billow = texture(noise_texture, noise_uv).r * 0.7 + texture(noise_texture, noise_uv * 2.7).r * 0.3;
	float edge_distance = length((UV - 0.5) * 2.0);
	float puff = smoothstep(0.0, 0.45, 1.0 - edge_distance - billow * 0.6);

	ALBEDO = mix(smoke_color, ember_color, pow(1.0 - life, 4.0) * 0.6) * tint.rgb;
	ALPHA = puff * density * tint.a;
}
