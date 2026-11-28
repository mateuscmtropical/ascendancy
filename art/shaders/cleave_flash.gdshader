shader_type spatial;
render_mode blend_mix, unshaded, cull_disabled, depth_draw_never, depth_test_disabled, shadows_disabled;
// Clarão do começo do corte (CleaveEffect): disco branco virado para a câmera com um risco
// horizontal comprido, por cima de tudo.

uniform vec3 halo_color : source_color = vec3(0.55, 0.88, 1.0);
instance uniform float strength = 0.0;

void vertex() {
	mat4 facing_camera = mat4(
			normalize(INV_VIEW_MATRIX[0]) * length(MODEL_MATRIX[0]),
			normalize(INV_VIEW_MATRIX[1]) * length(MODEL_MATRIX[1]),
			normalize(INV_VIEW_MATRIX[2]) * length(MODEL_MATRIX[2]),
			MODEL_MATRIX[3]);

	MODELVIEW_MATRIX = VIEW_MATRIX * facing_camera;
	MODELVIEW_NORMAL_MATRIX = mat3(MODELVIEW_MATRIX);
}

void fragment() {
	vec2 point = (UV - 0.5) * 2.0;
	float core = 1.0 - smoothstep(0.0, 0.45, length(point));
	float streak = (1.0 - smoothstep(0.0, 0.06, abs(point.y))) * (1.0 - smoothstep(0.2, 1.0, abs(point.x)));

	ALBEDO = mix(halo_color, vec3(1.0), core) * 1.8;
	ALPHA = clamp(core * 1.4 + streak, 0.0, 1.0) * strength;
}
