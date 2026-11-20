shader_type spatial;

// Vidro colorido da claraboia da escadaria do casarão: a luz do dia entra por cima e acende os
// painéis; de noite sobra só o reflexo fraco do lustre. night_glow vem de
// features/sky/day_night_cycle.gd.

global uniform float night_glow;

uniform vec3 glass_color : source_color = vec3(1.0, 0.85, 0.63);
uniform float day_energy : hint_range(0.0, 4.0) = 1.1;
uniform float night_energy : hint_range(0.0, 4.0) = 0.12;


void fragment() {
	ALBEDO = glass_color;
	ROUGHNESS = 0.4;
	EMISSION = glass_color * mix(day_energy, night_energy, night_glow);
}
