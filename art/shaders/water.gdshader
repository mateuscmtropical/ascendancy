shader_type spatial;
render_mode blend_mix, depth_draw_opaque, cull_back, specular_schlick_ggx;

// Água estilizada de fonte: cor rasa/funda pela profundidade da tela, ondulação por dois ruídos rolando.

uniform vec3 shallow_color : source_color = vec3(0.45, 0.80, 0.82);
uniform vec3 deep_color : source_color = vec3(0.10, 0.36, 0.52);
uniform float depth_fade_distance : hint_range(0.05, 3.0) = 0.6;
uniform float surface_opacity : hint_range(0.0, 1.0) = 0.82;
uniform sampler2D ripple_normal_a : hint_normal, filter_linear_mipmap, repeat_enable;
uniform sampler2D ripple_normal_b : hint_normal, filter_linear_mipmap, repeat_enable;
uniform float ripple_scale = 0.6;
uniform float ripple_strength : hint_range(0.0, 1.0) = 0.45;
uniform vec2 ripple_speed_a = vec2(0.03, 0.02);
uniform vec2 ripple_speed_b = vec2(-0.025, 0.035);
uniform sampler2D depth_texture : hint_depth_texture, filter_linear_mipmap;

varying vec3 world_position;

void vertex() {
	world_position = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

float water_depth_below_surface(vec2 screen_uv, float fragment_depth, mat4 inverse_projection) {
	float scene_depth = texture(depth_texture, screen_uv).r;
	vec4 scene_view = inverse_projection * vec4(screen_uv * 2.0 - 1.0, scene_depth, 1.0);
	vec4 surface_view = inverse_projection * vec4(screen_uv * 2.0 - 1.0, fragment_depth, 1.0);

	return (surface_view.z / surface_view.w) - (scene_view.z / scene_view.w);
}

void fragment() {
	vec2 ripple_uv = world_position.xz * ripple_scale;
	vec3 normal_a = texture(ripple_normal_a, ripple_uv + TIME * ripple_speed_a).rgb;
	vec3 normal_b = texture(ripple_normal_b, ripple_uv * 1.7 + TIME * ripple_speed_b).rgb;
	float depth_below = water_depth_below_surface(SCREEN_UV, FRAGCOORD.z, INV_PROJECTION_MATRIX);
	float depth_blend = clamp(depth_below / depth_fade_distance, 0.0, 1.0);

	ALBEDO = mix(shallow_color, deep_color, depth_blend);
	ALPHA = mix(surface_opacity * 0.6, surface_opacity, depth_blend);
	NORMAL_MAP = mix(normal_a, normal_b, 0.5);
	NORMAL_MAP_DEPTH = ripple_strength;
	ROUGHNESS = 0.04;
	SPECULAR = 0.7;
}
