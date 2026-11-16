shader_type spatial;
render_mode blend_add, unshaded, cull_disabled, depth_draw_never, shadows_disabled;

// Faísca de partícula: ponto redondo virado para a câmera, miolo claro e borda da cor da partícula.

uniform vec3 core_color : source_color = vec3(1.0, 0.9, 0.6);
uniform float energy = 3.0;

varying vec4 tint;


void vertex() {
	mat4 facing_camera = mat4(
			normalize(INV_VIEW_MATRIX[0]) * length(MODEL_MATRIX[0]),
			normalize(INV_VIEW_MATRIX[1]) * length(MODEL_MATRIX[1]),
			normalize(INV_VIEW_MATRIX[2]) * length(MODEL_MATRIX[2]),
			MODEL_MATRIX[3]);

	tint = COLOR;
	MODELVIEW_MATRIX = VIEW_MATRIX * facing_camera;
	MODELVIEW_NORMAL_MATRIX = mat3(MODELVIEW_MATRIX);
}


void fragment() {
	float edge_distance = length((UV - 0.5) * 2.0);
	float dot_shape = smoothstep(1.0, 0.0, edge_distance);

	ALBEDO = mix(tint.rgb, core_color, dot_shape * dot_shape) * energy;
	ALPHA = dot_shape * tint.a;
}
