shader_type spatial;
render_mode blend_add, unshaded, cull_disabled, depth_draw_never, shadows_disabled, fog_disabled;

// Feixe de luz dos vitrais (god ray falso): prisma inclinado do vidro até o chão.
// UV.x = 0..1 através de cada face, UV.y = 0..1 do vitral até a ponta; COLOR = cor do vidro.
// Some nas bordas, nas faces vistas de raspão, perto da câmera e onde encosta na geometria.

uniform float intensity : hint_range(0.0, 2.0) = 0.06;
uniform float edge_softness : hint_range(0.01, 0.5) = 0.35;
uniform float start_fade : hint_range(0.0, 0.5) = 0.06;
uniform float end_fade_start : hint_range(0.0, 1.0) = 0.3;
uniform float grazing_fade : hint_range(0.0, 1.0) = 0.55;
uniform float camera_fade_meters : hint_range(0.1, 10.0) = 3.0;
uniform float contact_fade_meters : hint_range(0.01, 4.0) = 0.8;
uniform float dust_strength : hint_range(0.0, 1.0) = 0.2;
uniform float dust_speed : hint_range(0.0, 2.0) = 0.15;
uniform sampler2D depth_texture : hint_depth_texture, filter_linear_mipmap;

varying vec3 shaft_color;

float scene_view_depth(vec2 screen_uv, mat4 inverse_projection) {
	float depth = texture(depth_texture, screen_uv).r;
	vec4 view_position = inverse_projection * vec4(screen_uv * 2.0 - 1.0, depth, 1.0);

	return view_position.z / view_position.w;
}

void vertex() {
	shaft_color = COLOR.rgb;
}

void fragment() {
	float side_fade = smoothstep(0.0, edge_softness, UV.x) * smoothstep(0.0, edge_softness, 1.0 - UV.x);
	float length_fade = smoothstep(0.0, start_fade, UV.y) * (1.0 - smoothstep(end_fade_start, 1.0, UV.y));
	float facing = abs(dot(normalize(NORMAL), normalize(VIEW)));
	float view_fade = smoothstep(0.0, grazing_fade, facing);
	float camera_fade = smoothstep(0.3, camera_fade_meters, -VERTEX.z);
	float scene_depth = scene_view_depth(SCREEN_UV, INV_PROJECTION_MATRIX);
	float contact_fade = smoothstep(0.0, contact_fade_meters, VERTEX.z - scene_depth);
	float dust = 1.0 - dust_strength + dust_strength * sin(UV.y * 31.0 - TIME * dust_speed * 6.283 + UV.x * 5.0);

	ALBEDO = shaft_color;
	ALPHA = intensity * side_fade * length_fade * view_fade * camera_fade * contact_fade * dust;
}
