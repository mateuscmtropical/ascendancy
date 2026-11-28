shader_type spatial;
render_mode blend_mix, unshaded, cull_disabled, depth_draw_never, depth_test_disabled, shadows_disabled;
// Risco de luz do corte (CleaveEffect): um quad comprido no X da malha que gira em torno desse
// eixo para ficar sempre de frente para a câmera, com miolo quase branco opaco (aparece contra
// céu claro) e halo colorido em volta. Serve à linha do corte que fica e ao fio da lâmina que voa.

uniform vec3 core_color : source_color = vec3(0.93, 1.0, 1.0);
uniform vec3 halo_color : source_color = vec3(0.2, 0.7, 1.0);
uniform float energy = 3.0;
// 0 = barra de espessura igual; 1 = pontas afinando até sumir.
uniform float taper : hint_range(0.0, 1.0) = 0.0;
// Espessura em metros, halo incluído.
instance uniform float thickness = 0.2;
// Parte do comprimento já riscada, a partir do começo (UV.x = 0).
instance uniform float reveal = 1.0;
instance uniform float fade = 0.0;
instance uniform float glow = 1.0;

varying float along;
varying float across;

void vertex() {
	vec3 axis = normalize(MODEL_MATRIX[0].xyz);
	vec3 center = (MODEL_MATRIX * vec4(VERTEX.x, 0.0, 0.0, 1.0)).xyz;
	vec3 side = normalize(cross(axis, CAMERA_POSITION_WORLD - center));
	vec3 world_position = center + side * VERTEX.y * thickness;

	along = UV.x;
	across = UV.y * 2.0 - 1.0;
	VERTEX = (inverse(MODEL_MATRIX) * vec4(world_position, 1.0)).xyz;
}

void fragment() {
	float width = mix(1.0, sin(along * PI), taper);
	float distance_out = abs(across) / max(width, 0.001);
	float core = 1.0 - smoothstep(0.08, 0.3, distance_out);
	float halo = pow(max(1.0 - distance_out, 0.0), 2.0);
	float shimmer = 0.85 + 0.15 * sin(along * 140.0 - TIME * 34.0);
	float drawn = step(along, reveal);

	ALBEDO = mix(halo_color, core_color, core) * energy * glow;
	ALPHA = clamp(core + halo * 0.7 * shimmer, 0.0, 1.0) * fade * drawn;
}
