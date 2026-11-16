shader_type spatial;
render_mode cull_back;

// Veia de lava da Mula sem cabeça. UV.x = distância do toco do pescoço (0..1), UV.y = grossura (0 ponta, 1 tronco),
// gravados por tools_src/build_mula_sem_cabeca.py. Brilha mais nos troncos e pulsa como batimento: a onda nasce no
// toco e corre até as pontas.

uniform vec3 trunk_color : source_color = vec3(1.0, 0.6, 0.14);
uniform vec3 tip_color : source_color = vec3(0.95, 0.13, 0.01);
uniform float energy = 5.0;
uniform float beats_per_second = 0.75;
uniform float beat_travel = 2.2;
uniform float beat_strength = 0.9;
// 1 = viva; cai quando a mula morre e a lava esfria (por instância: cada mula tem o seu).
instance uniform float burn = 1.0;


void fragment() {
	float distance_from_stump = UV.x;
	float thickness = UV.y;
	float wave = 0.5 + 0.5 * sin(TAU * (TIME * beats_per_second - distance_from_stump * beat_travel));
	float beat = pow(wave, 5.0);
	float core = pow(clamp(dot(NORMAL, VIEW), 0.0, 1.0), 1.5);
	float strength = mix(0.4, 1.0, thickness) * mix(1.0, 0.55, distance_from_stump) * mix(0.22, 1.0, core * core);
	vec3 lava = mix(tip_color, trunk_color, clamp(thickness * 0.7 + beat * 0.35 + core * 0.2 - 0.2, 0.0, 1.0));

	ALBEDO = vec3(0.03, 0.01, 0.005);
	ROUGHNESS = 0.45;
	EMISSION = lava * energy * strength * (0.65 + beat_strength * beat) * burn;
}
