shader_type spatial;
render_mode blend_mix, unshaded, cull_disabled, depth_draw_never, depth_test_disabled, shadows_disabled;
// Lâmina do corte (CleaveEffect): meia-lua deitada no plano do corte, a frente (UV.y = 0) acesa e
// o rastro sumindo para trás, pontas varridas para trás.

uniform vec3 core_color : source_color = vec3(0.93, 1.0, 1.0);
uniform vec3 halo_color : source_color = vec3(0.2, 0.7, 1.0);
uniform float energy = 2.6;
// Quanto as pontas ficam para trás do meio e a espessura da lâmina no meio (0 a 2, no quad).
uniform float sweep = 0.9;
uniform float middle = 0.9;
instance uniform float fade = 0.0;
instance uniform float glow = 1.0;

void fragment() {
	vec2 point = (UV - 0.5) * 2.0;
	float bend = point.x * point.x;
	float front = -1.0 + sweep * bend;
	float back = front + middle * (1.0 - bend);
	float depth = (point.y - front) / max(back - front, 0.001);
	float inside = step(0.0, depth) * step(depth, 1.0);
	float edge = 1.0 - smoothstep(0.0, 0.22, depth);
	float trail = pow(1.0 - clamp(depth, 0.0, 1.0), 2.0);
	float streaks = 0.75 + 0.25 * sin(point.x * 37.0 + depth * 9.0);

	ALBEDO = mix(halo_color, core_color, edge) * energy * glow;
	ALPHA = clamp(edge + trail * 0.75 * streaks, 0.0, 1.0) * inside * fade;
}
