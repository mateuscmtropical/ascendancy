shader_type spatial;
render_mode blend_mix, depth_draw_never, cull_disabled, specular_schlick_ggx;

// Fio de agua da fonte (jatos e cortinas de transbordo).
// UV.x = indice_do_fio * 2 + volta (0..1), UV.y = 0..1 ao longo do fio (do bico ate a queda).
// Estrias rolam ao longo do fio, borda ruidosa, brilho de fresnel e espuma mais clara na largada.

uniform vec3 body_color : source_color = vec3(0.50, 0.80, 0.92);
uniform vec3 foam_color : source_color = vec3(0.97, 1.0, 1.0);
uniform float stream_length_meters : hint_range(0.2, 6.0) = 2.0;
uniform float scroll_speed : hint_range(0.0, 12.0) = 3.0;
uniform float streaks_around : hint_range(1.0, 128.0) = 4.0;
uniform float streak_stretch : hint_range(0.2, 8.0) = 2.0;
uniform float base_opacity : hint_range(0.0, 1.0) = 0.7;
uniform float view_edge_fade : hint_range(0.0, 1.0) = 1.0;
uniform float edge_noise_strength : hint_range(0.0, 1.0) = 0.5;
uniform float fresnel_power : hint_range(0.5, 8.0) = 2.5;
uniform float fresnel_strength : hint_range(0.0, 1.0) = 0.7;
uniform float foam_length : hint_range(0.0, 1.0) = 0.2;
uniform float streak_contrast : hint_range(0.0, 1.0) = 0.3;
uniform float streak_highlight : hint_range(0.0, 1.0) = 0.3;
uniform float tail_breakup : hint_range(0.0, 1.0) = 0.6;
uniform float glow_strength : hint_range(0.0, 2.0) = 0.35;
uniform float wobble_amount : hint_range(0.0, 0.1) = 0.012;
uniform float wobble_speed : hint_range(0.0, 20.0) = 7.0;

varying float stream_seed;
varying float stream_around;

float hash21(vec2 cell) {
	vec2 scrambled = fract(cell * vec2(123.34, 456.21));

	scrambled += dot(scrambled, scrambled + 45.32);

	return fract(scrambled.x * scrambled.y);
}

// Ruido de valor com periodo horizontal inteiro: a volta do tubo fecha sem emenda.
float periodic_noise(vec2 point, float period) {
	vec2 cell = floor(point);
	vec2 local = fract(point);
	vec2 blend = local * local * (3.0 - 2.0 * local);
	float left = mod(cell.x, period);
	float right = mod(cell.x + 1.0, period);
	float bottom_left = hash21(vec2(left, cell.y));
	float bottom_right = hash21(vec2(right, cell.y));
	float top_left = hash21(vec2(left, cell.y + 1.0));
	float top_right = hash21(vec2(right, cell.y + 1.0));

	return mix(mix(bottom_left, bottom_right, blend.x), mix(top_left, top_right, blend.x), blend.y);
}

float layered_streaks(vec2 point, float period) {
	return 0.65 * periodic_noise(point, period) + 0.35 * periodic_noise(vec2(point.x * 2.0, point.y * 1.7 + 3.1), period * 2.0);
}

void vertex() {
	stream_seed = floor(UV.x * 0.5);
	stream_around = UV.x - stream_seed * 2.0;

	float pulse = sin(UV.y * stream_length_meters * 9.0 - TIME * wobble_speed + stream_seed * 2.3);

	VERTEX += NORMAL * pulse * wobble_amount * smoothstep(0.0, 0.25, UV.y);
}

void fragment() {
	float length_meters = UV.y * stream_length_meters;
	vec2 streak_point = vec2(stream_around * streaks_around, length_meters * streak_stretch - TIME * scroll_speed + stream_seed * 13.7);
	float streaks = layered_streaks(streak_point, streaks_around);
	float facing = abs(dot(normalize(NORMAL), normalize(VIEW)));
	float fresnel = pow(1.0 - facing, fresnel_power);
	float edge_fade = smoothstep(0.0, 0.55, facing + (streaks - 0.5) * edge_noise_strength);
	float head_fade = smoothstep(0.0, 0.06, UV.y);
	float breakup_threshold = mix(0.0, 0.7, smoothstep(0.55, 1.0, UV.y)) * tail_breakup;
	float tail_fade = smoothstep(breakup_threshold, breakup_threshold + 0.2, streaks) * (1.0 - smoothstep(0.9, 1.0, UV.y));
	float foam = (1.0 - smoothstep(0.0, foam_length, UV.y)) * mix(0.6, 1.0, streaks);
	float streak_mask = smoothstep(0.35, 0.65, streaks);
	float brightness = clamp(fresnel * fresnel_strength + foam + streak_mask * streak_highlight, 0.0, 1.0);

	ALBEDO = mix(body_color, foam_color, brightness);
	EMISSION = mix(body_color, foam_color, brightness) * glow_strength * (0.6 + 0.8 * brightness);
	ALPHA = base_opacity * mix(1.0, edge_fade, view_edge_fade) * head_fade * tail_fade * mix(1.0 - streak_contrast, 1.0, streak_mask);
	ALPHA = clamp(ALPHA + foam * 0.2 * head_fade, 0.0, 1.0);
	ROUGHNESS = 0.08;
	SPECULAR = 0.8;
}
