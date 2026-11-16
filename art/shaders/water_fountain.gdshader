shader_type spatial;
render_mode blend_mix, depth_draw_opaque, cull_back, specular_schlick_ggx;

// Superficie das bacias da fonte grande: dois normais rolando, tinta por profundidade, fresnel,
// brilho cintilante e aneis de ondas + espuma onde a cortina e os jatos caem (em coordenadas locais da fonte).

uniform vec3 shallow_color : source_color = vec3(0.45, 0.80, 0.82);
uniform vec3 deep_color : source_color = vec3(0.10, 0.36, 0.52);
uniform vec3 sky_tint : source_color = vec3(0.72, 0.88, 1.0);
uniform vec3 foam_color : source_color = vec3(0.96, 1.0, 1.0);
uniform float depth_fade_distance : hint_range(0.05, 3.0) = 0.6;
uniform float surface_opacity : hint_range(0.0, 1.0) = 0.82;
uniform sampler2D ripple_normal_a : hint_normal, filter_linear_mipmap, repeat_enable;
uniform sampler2D ripple_normal_b : hint_normal, filter_linear_mipmap, repeat_enable;
uniform float ripple_scale = 0.6;
uniform float ripple_strength : hint_range(0.0, 1.0) = 0.45;
uniform vec2 ripple_speed_a = vec2(0.03, 0.02);
uniform vec2 ripple_speed_b = vec2(-0.025, 0.035);
uniform float fresnel_power : hint_range(0.5, 8.0) = 3.0;
uniform float fresnel_strength : hint_range(0.0, 1.0) = 0.55;
uniform float glitter_scale : hint_range(1.0, 60.0) = 14.0;
uniform float glitter_strength : hint_range(0.0, 4.0) = 1.4;
// Pontos de impacto: raio da cortina (0 = sem cortina) e jatos igualmente espacados (0 = sem jatos).
uniform float curtain_ring_radius = 0.0;
uniform float jet_landing_radius = 0.0;
uniform float jet_landing_count : hint_range(1.0, 32.0) = 8.0;
uniform float jet_landing_phase = 0.0;
uniform float ring_frequency : hint_range(2.0, 40.0) = 16.0;
uniform float ring_speed : hint_range(0.0, 8.0) = 2.6;
uniform float ring_reach : hint_range(0.1, 2.0) = 0.7;
uniform float foam_width : hint_range(0.02, 0.6) = 0.16;
uniform sampler2D depth_texture : hint_depth_texture, filter_linear_mipmap;

varying vec3 world_position;
varying vec2 local_plane;

float hash21(vec2 cell) {
	vec2 scrambled = fract(cell * vec2(123.34, 456.21));

	scrambled += dot(scrambled, scrambled + 45.32);

	return fract(scrambled.x * scrambled.y);
}

float value_noise(vec2 point) {
	vec2 cell = floor(point);
	vec2 local = fract(point);
	vec2 blend = local * local * (3.0 - 2.0 * local);

	return mix(mix(hash21(cell), hash21(cell + vec2(1.0, 0.0)), blend.x), mix(hash21(cell + vec2(0.0, 1.0)), hash21(cell + vec2(1.0, 1.0)), blend.x), blend.y);
}

float water_depth_below_surface(vec2 screen_uv, float fragment_depth, mat4 inverse_projection) {
	float scene_depth = texture(depth_texture, screen_uv).r;
	vec4 scene_view = inverse_projection * vec4(screen_uv * 2.0 - 1.0, scene_depth, 1.0);
	vec4 surface_view = inverse_projection * vec4(screen_uv * 2.0 - 1.0, fragment_depth, 1.0);

	return (surface_view.z / surface_view.w) - (scene_view.z / scene_view.w);
}

// Distancia ao ponto de impacto mais proximo entre jatos em volta do eixo (dobra o angulo no setor).
float distance_to_nearest_jet_landing() {
	float sector = 6.28318530718 / jet_landing_count;
	float angle = atan(local_plane.y, local_plane.x) - jet_landing_phase;
	float folded = mod(angle + sector * 0.5, sector) - sector * 0.5;
	float radius = length(local_plane);
	vec2 offset = vec2(radius * cos(folded) - jet_landing_radius, radius * sin(folded));

	return length(offset);
}

// x = anel de onda expandindo, y = espuma no ponto de impacto.
vec2 impact_response(float distance_to_impact, float noise_value) {
	float falloff = 1.0 - smoothstep(0.0, ring_reach, distance_to_impact);
	float wave = pow(0.5 + 0.5 * sin(distance_to_impact * ring_frequency - TIME * ring_speed), 3.0);
	float foam = (1.0 - smoothstep(0.0, foam_width, distance_to_impact)) * mix(0.55, 1.0, noise_value);

	return vec2(wave * falloff, foam);
}

void vertex() {
	world_position = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	local_plane = VERTEX.xz;
}

void fragment() {
	vec2 ripple_uv = world_position.xz * ripple_scale;
	vec3 normal_a = texture(ripple_normal_a, ripple_uv + TIME * ripple_speed_a).rgb;
	vec3 normal_b = texture(ripple_normal_b, ripple_uv * 1.7 + TIME * ripple_speed_b).rgb;
	vec3 blended_normal = mix(normal_a, normal_b, 0.5);
	float depth_below = water_depth_below_surface(SCREEN_UV, FRAGCOORD.z, INV_PROJECTION_MATRIX);
	float depth_blend = clamp(depth_below / depth_fade_distance, 0.0, 1.0);
	float facing = clamp(dot(normalize(NORMAL), normalize(VIEW)), 0.0, 1.0);
	float fresnel = pow(1.0 - facing, fresnel_power) * fresnel_strength;
	float foam_noise = value_noise(local_plane * 9.0 + TIME * 0.6);
	float curtain_distance = abs(length(local_plane) - curtain_ring_radius);
	vec2 curtain_response = impact_response(curtain_distance, foam_noise) * step(0.001, curtain_ring_radius);
	vec2 jet_response = impact_response(distance_to_nearest_jet_landing(), foam_noise) * step(0.001, jet_landing_radius);
	float ring = max(curtain_response.x, jet_response.x);
	float foam = max(curtain_response.y, jet_response.y);
	float glitter_cell = value_noise(world_position.xz * glitter_scale + blended_normal.xy * 4.0 + TIME * vec2(0.35, 0.2));
	float glitter = smoothstep(0.82, 0.95, glitter_cell) * (0.35 + fresnel);
	vec3 water_color = mix(shallow_color, deep_color, depth_blend);

	ALBEDO = mix(mix(water_color, sky_tint, fresnel), foam_color, clamp(foam + ring * 0.35, 0.0, 1.0));
	EMISSION = foam_color * (glitter * glitter_strength + ring * 0.12 + foam * 0.2);
	ALPHA = clamp(mix(surface_opacity * 0.6, surface_opacity, depth_blend) + foam * 0.3 + ring * 0.1, 0.0, 1.0);
	NORMAL_MAP = blended_normal;
	NORMAL_MAP_DEPTH = ripple_strength;
	ROUGHNESS = mix(0.04, 0.35, foam);
	SPECULAR = 0.7;
}
