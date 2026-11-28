shader_type spatial;
// Bloco e tábua quebráveis (BreakablePiece.make_box sobre BoxMesh): cor do material com mancha
// leve, quina chanfrada mais escura e, na madeira, veio ao longo da tábua. Tudo no espaço do
// objeto, então a textura vai junto quando o pedaço voa.

uniform vec3 base_color : source_color = vec3(0.914, 0.863, 0.776);
uniform vec3 edge_color : source_color = vec3(0.725, 0.667, 0.573);
// Largura da quina, em fração da face.
uniform float edge_width : hint_range(0.0, 0.3) = 0.07;
uniform float blotch_strength : hint_range(0.0, 0.5) = 0.12;
uniform float blotch_scale = 2.2;
// 0 = pedra, 1 = veio de madeira ao longo de grain_axis (o comprimento da tábua, no pedaço).
uniform float grain_strength : hint_range(0.0, 1.0) = 0.0;
uniform float grain_scale = 22.0;
uniform vec3 grain_axis = vec3(1.0, 0.0, 0.0);

varying vec3 object_position;

float hash(vec3 point) {
	return fract(sin(dot(point, vec3(12.9898, 78.233, 37.719))) * 43758.5453);
}

float value_noise(vec3 point) {
	vec3 cell = floor(point);
	vec3 local = fract(point);
	vec3 smooth_local = local * local * (3.0 - 2.0 * local);
	float bottom = mix(
		mix(hash(cell), hash(cell + vec3(1, 0, 0)), smooth_local.x),
		mix(hash(cell + vec3(0, 1, 0)), hash(cell + vec3(1, 1, 0)), smooth_local.x),
		smooth_local.y);
	float top = mix(
		mix(hash(cell + vec3(0, 0, 1)), hash(cell + vec3(1, 0, 1)), smooth_local.x),
		mix(hash(cell + vec3(0, 1, 1)), hash(cell + vec3(1, 1, 1)), smooth_local.x),
		smooth_local.y);
	return mix(bottom, top, smooth_local.z);
}

// A BoxMesh põe cada face numa célula de uma grade 3 x 2 nas UVs: a borda da célula é a quina.
float bevel_shade(vec2 uv) {
	vec2 in_face = fract(uv * vec2(3.0, 2.0));
	float to_edge = min(min(in_face.x, 1.0 - in_face.x), min(in_face.y, 1.0 - in_face.y));
	return 1.0 - smoothstep(0.0, edge_width, to_edge);
}

float wood_grain(vec3 point) {
	vec3 across = point - grain_axis * dot(point, grain_axis);
	float warp = value_noise(point * 3.0 + grain_axis * point * -2.4) * 3.0;
	return 0.5 + 0.5 * sin((across.x + across.y + across.z) * grain_scale + warp);
}

void vertex() {
	object_position = VERTEX;
}

void fragment() {
	float blotch = value_noise(object_position * blotch_scale) - 0.5;
	float grain = wood_grain(object_position);
	vec3 color = base_color * (1.0 + blotch * blotch_strength * 2.0);

	color = mix(color, color * 0.78, grain * grain_strength);
	color = mix(color, edge_color, bevel_shade(UV));
	ALBEDO = color;
	ROUGHNESS = 1.0;
}
