shader_type spatial;
render_mode blend_mix, cull_disabled, depth_draw_opaque;

// Vitrine das lojas grandes: vidro claro e transparente de dia (vê-se o salão por dentro); ao
// anoitecer ganha um véu de luz quente das velas e lustres do salão, mais forte embaixo, onde fica
// a mercadoria. As lojas ficam sempre abertas: toda vitrine acende, sem sorteio como nas casas.
// night_glow vem de features/sky/day_night_cycle.gd.

global uniform float night_glow;

uniform vec3 glass_color : source_color = vec3(0.749, 0.847, 0.91);
uniform vec3 shop_light_color : source_color = vec3(1.0, 0.78, 0.48);
uniform float shop_light_energy : hint_range(0.0, 4.0) = 1.6;
uniform float day_alpha : hint_range(0.0, 1.0) = 0.25;
uniform float night_alpha : hint_range(0.0, 1.0) = 0.5;
uniform float glow_height = 4.0;

varying float height_in_pane;


void vertex() {
	height_in_pane = clamp(VERTEX.y / glow_height, 0.0, 1.0);
}


void fragment() {
	float floor_glow = mix(1.0, 0.55, height_in_pane);
	float view_facing = abs(dot(NORMAL, VIEW));

	ALBEDO = glass_color;
	ROUGHNESS = 0.05;
	METALLIC = 0.0;
	ALPHA = mix(day_alpha, night_alpha, night_glow);
	EMISSION = shop_light_color * shop_light_energy * night_glow * floor_glow * mix(0.7, 1.0, view_facing);
}
