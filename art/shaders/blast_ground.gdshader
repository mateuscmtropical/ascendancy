shader_type spatial;
// Chão que a explosão deforma (BlastGround): a altura de cada vértice vem de height_texture e a
// cor mistura grama -> grama seca -> terra revolvida -> carvão pela máscara (R = queimado,
// G = brasa acesa). Intocado, é o gramado da cidade (T_Lawn a 7 m por ladrilho).

uniform sampler2D height_texture : repeat_disable, filter_linear;
uniform sampler2D mask_texture : repeat_disable, filter_linear;
uniform sampler2D grass_texture : source_color, repeat_enable, filter_linear_mipmap_anisotropic;
uniform sampler2D soil_texture : source_color, repeat_enable, filter_linear_mipmap_anisotropic;
// Amostras por lado das duas texturas (uma por vértice) e metros entre duas amostras.
uniform float sample_count = 193.0;
uniform float meters_per_sample = 0.25;
uniform float grass_meters_per_tile = 7.0;
uniform float soil_meters_per_tile = 3.0;
uniform vec3 dry_grass_color : source_color = vec3(0.62, 0.52, 0.2);
uniform vec3 soil_color : source_color = vec3(0.5, 0.33, 0.2);
uniform vec3 charcoal_color : source_color = vec3(0.05, 0.045, 0.05);
uniform vec3 ash_color : source_color = vec3(0.3, 0.29, 0.3);
uniform vec3 ember_color : source_color = vec3(1.0, 0.32, 0.04);
uniform float ember_energy = 1.2;

varying vec2 ground_position;
varying vec2 sample_uv;

float hash(vec2 point) {
	return fract(sin(dot(point, vec2(12.9898, 78.233))) * 43758.5453);
}

float value_noise(vec2 point) {
	vec2 cell = floor(point);
	vec2 local = fract(point);
	vec2 smooth_local = local * local * (3.0 - 2.0 * local);
	float bottom = mix(hash(cell), hash(cell + vec2(1.0, 0.0)), smooth_local.x);
	float top = mix(hash(cell + vec2(0.0, 1.0)), hash(cell + vec2(1.0, 1.0)), smooth_local.x);
	return mix(bottom, top, smooth_local.y);
}

float height_at(vec2 uv) {
	return textureLod(height_texture, uv, 0.0).r;
}

// A borda da mancha sai roída por ruído em vez de seguir o círculo do pincel.
float ragged_burn(float burn, vec2 position) {
	vec2 turned = vec2(position.x * 0.8 - position.y * 0.6, position.x * 0.6 + position.y * 0.8);
	float ragged = value_noise(turned * 0.9) * 0.6 + value_noise(position * 2.3 + 7.0) * 0.4 - 0.5;
	return clamp(burn + ragged * 0.42 * smoothstep(0.0, 0.12, burn), 0.0, 1.0);
}

void vertex() {
	float texel = 1.0 / sample_count;
	float slope_x;
	float slope_z;

	// Um texel por vértice: a amostra cai no centro do texel dele.
	sample_uv = UV * (sample_count - 1.0) * texel + vec2(0.5 * texel);
	slope_x = height_at(sample_uv - vec2(texel, 0.0)) - height_at(sample_uv + vec2(texel, 0.0));
	slope_z = height_at(sample_uv - vec2(0.0, texel)) - height_at(sample_uv + vec2(0.0, texel));
	VERTEX.y = height_at(sample_uv);
	NORMAL = normalize(vec3(slope_x, 2.0 * meters_per_sample, slope_z));
	ground_position = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xz;
}

void fragment() {
	vec2 mask = texture(mask_texture, sample_uv).rg;
	float burn = ragged_burn(mask.r, ground_position);
	vec3 grass = texture(grass_texture, ground_position / grass_meters_per_tile).rgb;
	float soil_grain = texture(soil_texture, ground_position / soil_meters_per_tile).r;
	float clods = value_noise(ground_position * 2.6);
	vec3 soil = soil_color * (0.55 + soil_grain * 0.5 + step(0.62, clods) * 0.12);
	float ash = step(0.7, value_noise(ground_position * 7.0)) * 0.35;
	vec3 charcoal = mix(charcoal_color, ash_color, ash) * (0.7 + soil_grain * 0.5);
	float flicker = 0.6 + 0.4 * value_noise(ground_position * 3.0 + vec2(TIME * 1.7, -TIME * 1.1));
	float ember = mask.g * flicker * smoothstep(0.68, 0.84, value_noise(ground_position * 9.0));
	vec3 color = mix(grass, dry_grass_color * (0.7 + grass.g * 0.8), smoothstep(0.04, 0.2, burn));

	color = mix(color, soil, smoothstep(0.24, 0.42, burn));
	color = mix(color, charcoal, max(smoothstep(0.62, 0.84, burn), mask.g * 0.7));
	ALBEDO = color;
	ROUGHNESS = 0.9;
	EMISSION = ember_color * ember * ember_energy;
}
