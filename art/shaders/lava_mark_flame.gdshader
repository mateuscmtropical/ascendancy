shader_type spatial;
render_mode blend_add, unshaded, cull_disabled, depth_draw_never, shadows_disabled;

// Chaminha em cima de uma marca de lava: quad em pé virado para a câmera, roído por ruído que sobe, que encolhe e
// apaga conforme a marca esfria. Mesmos dados por instância de lava_mark.gdshader (x = nascimento, y = semente).

uniform sampler2D noise_texture : repeat_enable, filter_linear_mipmap;
uniform float now_seconds = 0.0;
uniform float cooling_seconds = 5.0;
uniform float energy = 0.9;
uniform float scroll_speed = 1.3;
uniform vec3 base_color : source_color = vec3(1.0, 0.38, 0.05);
uniform vec3 tip_color : source_color = vec3(0.7, 0.07, 0.01);

varying float heat;
varying float seed;


void vertex() {
	heat = clamp(1.0 - (now_seconds - INSTANCE_CUSTOM.x) / cooling_seconds, 0.0, 1.0);
	seed = INSTANCE_CUSTOM.y;

	mat4 facing_camera = mat4(
			normalize(INV_VIEW_MATRIX[0]) * length(MODEL_MATRIX[0]),
			vec4(0.0, length(MODEL_MATRIX[1]) * heat, 0.0, 0.0),
			normalize(INV_VIEW_MATRIX[2]) * length(MODEL_MATRIX[2]),
			MODEL_MATRIX[3]);

	MODELVIEW_MATRIX = VIEW_MATRIX * facing_camera;
	MODELVIEW_NORMAL_MATRIX = mat3(MODELVIEW_MATRIX);
}


void fragment() {
	float rise = 1.0 - UV.y;
	float licks = texture(noise_texture, UV * vec2(0.9, 0.5) + vec2(seed, TIME * scroll_speed + seed)).r;
	float flame = 1.0 - abs(UV.x - 0.5) * 2.4 - rise * 0.75 - (licks - 0.5) * (0.5 + rise);

	ALBEDO = mix(tip_color, base_color, clamp(flame * 1.6, 0.0, 1.0)) * energy;
	ALPHA = smoothstep(0.0, 0.25, flame) * smoothstep(0.0, 0.35, heat);
}
