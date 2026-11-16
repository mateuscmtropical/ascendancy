shader_type spatial;
render_mode blend_add, unshaded, cull_disabled, depth_draw_never, shadows_disabled, fog_disabled, world_vertex_coords;

// Feixe de luz dos vitrais (god ray falso) que segue o sol da cena (global sun_direction, mantido
// pelo Hub). Malha: um prisma por vitral, boca no vidro (UV.y = 0) e ponta empurrada
// reference_length metros para dentro (UV.y = 1); NORMAL = normal do vitral para dentro da igreja;
// COLOR = cor do vidro. O vértice da ponta é refeito na direção do sol até o chão, e o vitral só
// acende quando está virado para o sol. Some nas bordas, nas faces de raspão, perto da câmera e
// onde encosta na geometria.

global uniform vec3 sun_direction;
global uniform float sunlight; // força do sol (0 de noite e no eclipse), mantida pelo Hub

uniform float intensity : hint_range(0.0, 2.0) = 0.09;
uniform float reference_length = 12.0; // igual a SHAFT_REFERENCE_LENGTH em tools_src/build_cathedral.py
uniform float floor_height = 1.05; // piso da nave, em coordenadas do mundo
uniform float max_length : hint_range(1.0, 40.0) = 22.0;
uniform float min_sun_drop : hint_range(0.01, 1.0) = 0.12;
uniform float facing_sun_fade : hint_range(0.01, 1.0) = 0.35;
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
varying float sun_strength;

float scene_view_depth(vec2 screen_uv, mat4 inverse_projection) {
	float depth = texture(depth_texture, screen_uv).r;
	vec4 view_position = inverse_projection * vec4(screen_uv * 2.0 - 1.0, depth, 1.0);

	return view_position.z / view_position.w;
}

float shaft_length(vec3 mouth, vec3 light_direction) {
	float drop = max(-light_direction.y, min_sun_drop);

	return min((mouth.y - floor_height) / drop, max_length);
}

void vertex() {
	vec3 inward = normalize(NORMAL);
	vec3 light_direction = normalize(sun_direction);
	vec3 mouth = VERTEX - inward * reference_length * UV.y;

	VERTEX = mouth + light_direction * shaft_length(mouth, light_direction) * UV.y;
	shaft_color = COLOR.rgb;
	sun_strength = smoothstep(0.0, facing_sun_fade, dot(inward, light_direction));
}

void fragment() {
	vec3 face_normal = normalize(cross(dFdx(VERTEX), dFdy(VERTEX)));
	float side_fade = smoothstep(0.0, edge_softness, UV.x) * smoothstep(0.0, edge_softness, 1.0 - UV.x);
	float length_fade = smoothstep(0.0, start_fade, UV.y) * (1.0 - smoothstep(end_fade_start, 1.0, UV.y));
	float view_fade = smoothstep(0.0, grazing_fade, abs(dot(face_normal, normalize(VIEW))));
	float camera_fade = smoothstep(0.3, camera_fade_meters, -VERTEX.z);
	float scene_depth = scene_view_depth(SCREEN_UV, INV_PROJECTION_MATRIX);
	float contact_fade = smoothstep(0.0, contact_fade_meters, VERTEX.z - scene_depth);
	float dust = 1.0 - dust_strength + dust_strength * sin(UV.y * 31.0 - TIME * dust_speed * 6.283 + UV.x * 5.0);

	ALBEDO = shaft_color;
	ALPHA = intensity * sunlight * sun_strength * side_fade * length_fade * view_fade * camera_fade * contact_fade * dust;
}
