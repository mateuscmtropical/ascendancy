shader_type spatial;
render_mode cull_back, unshaded;

// Vidro de dentro das janelas do casarão: um polígono só, virado para dentro do salão, que o
// vidro aceso por fora (shopfront_glass) não esconde. De dia é invisível; de noite escurece a
// janela vista de dentro, para ela ler como noite lá fora, enquanto a fachada mantém a luz acesa.
// Entra no passe opaco (alpha hash) para não depender da ordem dos vidros transparentes.
// night_glow vem de features/sky/day_night_cycle.gd.

global uniform float night_glow;

uniform vec3 night_color : source_color = vec3(0.03, 0.045, 0.1);


void fragment() {
	ALBEDO = night_color;
	ALPHA = night_glow;
	ALPHA_HASH_SCALE = 1.0;
}
