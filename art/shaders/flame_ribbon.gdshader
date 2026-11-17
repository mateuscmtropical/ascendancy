shader_type spatial;
render_mode blend_add, unshaded, cull_disabled, depth_draw_never, shadows_disabled;

// Língua de fogo em fita da Mula sem cabeça (malha MulaFlames de tools_src/build_mula_sem_cabeca.py): cada tira vem
// quase sem largura ao longo de uma curva presa aos ossos. NORMAL = direção da curva, UV.x = lado, UV.y = raiz (0)
// à ponta (1), UV2 = (semente, largura na unidade do modelo). Aqui a tira abre de frente para a câmera, a ponta
// chicoteia e a forma é roída por ruído que corre da raiz para a ponta.

uniform sampler2D noise_texture : repeat_enable, filter_linear_mipmap;
uniform sampler2D heat_ramp : repeat_disable, source_color;
uniform float energy = 1.0;
uniform float scroll_speed = 0.8;
uniform float erosion = 1.0;
uniform float lick_speed = 2.6;
uniform float lick_reach = 0.3;
uniform float root_dimming_floor = 0.4;
uniform float root_dimming_reach = 0.45;
// 1 = acesa; cai até 0 quando a mula morre e o fogo apaga (por instância: cada mula tem o seu).
instance uniform float burn = 1.0;

varying float seed;


float lick_wave(float ribbon_seed, float tip_share) {
	float slow = sin(TIME * lick_speed + ribbon_seed * TAU + tip_share * 4.0);
	float fast = sin(TIME * lick_speed * 2.3 + ribbon_seed * 40.0 + tip_share * 9.0);

	return slow + fast * 0.5;
}


void vertex() {
	vec3 camera_position = (inverse(MODEL_MATRIX) * vec4(CAMERA_POSITION_WORLD, 1.0)).xyz;
	vec3 curve_direction = normalize(NORMAL);
	vec3 toward_camera = normalize(camera_position - VERTEX);
	vec3 side = normalize(cross(curve_direction, toward_camera));
	float width = UV2.y;
	float tip_share = UV.y;
	float lick = lick_wave(UV2.x, tip_share) * lick_reach * tip_share * tip_share;

	seed = UV2.x;
	VERTEX += side * width * (UV.x - 0.5 + lick);
	NORMAL = toward_camera;
}


void fragment() {
	float tip_share = UV.y;
	vec2 noise_uv = vec2(UV.x * 0.4 + seed * 3.7, tip_share * 0.8 - TIME * scroll_speed + seed);
	float coarse = texture(noise_texture, noise_uv).r;
	float fine = texture(noise_texture, noise_uv * vec2(2.1, 2.6) + vec2(0.37, -TIME * scroll_speed * 0.7)).r;
	float wander = (coarse - 0.5) * 0.9 * tip_share;
	float half_width = mix(1.0, 0.3, tip_share);
	float core = 1.0 - abs((UV.x - 0.5) * 2.0 + wander) / half_width;
	float heat = core * (1.0 - tip_share * 0.55) - (coarse * 0.9 + fine * 0.6 - 0.5) * (0.25 + tip_share * 1.1) * erosion;

	heat *= smoothstep(0.0, 0.1, tip_share) * smoothstep(1.0, 0.85, tip_share);
	heat -= 1.0 - burn;

	// muitas línguas nascem do mesmo ponto: a raiz de cada uma brilha menos para a soma não estourar
	float root_dimming = mix(root_dimming_floor, 1.0, smoothstep(0.0, root_dimming_reach, tip_share));

	ALBEDO = texture(heat_ramp, vec2(clamp(heat, 0.0, 1.0), 0.5)).rgb * energy * root_dimming;
	ALPHA = smoothstep(0.02, 0.28, heat);
}
