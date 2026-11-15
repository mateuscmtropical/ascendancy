shader_type spatial;
render_mode world_vertex_coords;

// Vidro das janelas da cidade: escuro e brilhante de dia; ao anoitecer parte das janelas acende
// com luz quente fraca de vela (idade média). night_glow vem de features/sky/day_night_cycle.gd;
// quais janelas acendem sai de um hash da posição da vidraça, igual em todas as máquinas.

global uniform float night_glow;

uniform vec3 glass_color : source_color = vec3(0.227, 0.306, 0.4);
uniform vec3 candle_color : source_color = vec3(1.0, 0.72, 0.38);
uniform float candle_energy : hint_range(0.0, 4.0) = 1.4;
uniform float lit_share : hint_range(0.0, 1.0) = 0.55;
uniform float pane_cell = 1.4;

varying vec3 world_position;


float pane_hash(vec3 cell) {
	return fract(sin(dot(cell, vec3(12.9898, 78.233, 37.719))) * 43758.5453);
}


void vertex() {
	world_position = VERTEX;
}


void fragment() {
	vec3 cell = floor(world_position / pane_cell);
	float chance = pane_hash(cell);
	float is_lit = step(chance, lit_share);
	float flicker = 0.85 + 0.15 * sin(TIME * (1.3 + 2.0 * chance) + chance * 30.0);

	ALBEDO = glass_color;
	ROUGHNESS = 0.12;
	METALLIC = 0.4;
	EMISSION = candle_color * candle_energy * night_glow * is_lit * mix(0.6, 1.0, chance / max(lit_share, 0.001)) * flicker;
}
