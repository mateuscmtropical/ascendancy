shader_type sky;
// Céu procedural da cidade: gradiente azul saturado de dia (zênite #5C8FD1, horizonte #D7EEF5), pôr do
// sol quente, noite azul-marinho quase preta com milhares de estrelas nítidas (quentes e frias) num
// campo ralo e juntas em dois braços longos de um redemoinho, as mais fortes com halo e raios de
// difração, um astro dourado no fim do braço quente e a lua; nuvens que andam devagar (ralas de
// noite); estrelas cadentes e eclipses vindos de features/sky/day_night_cycle.gd. Tudo na direção
// do olhar (EYEDIR), sem textura.
// Desempenho: o Godot refaz a radiância (luz ambiente e reflexo vindos do céu) sempre que um uniform
// do material muda ou o shader lê TIME. Por isso o tempo que move nuvens e estrelas é o global
// sky_time (não suja o material) e o script só reescreve sol, lua e quantidades quando a mudança
// aparece. Partes invisíveis no pixel (céu noturno de dia, lua longe, nuvem sem cobertura) pulam.

const int METEOR_SLOTS = 8;
const int CLOUD_OCTAVES = 5;

uniform vec3 zenith_day_color : source_color = vec3(0.361, 0.561, 0.82);
uniform vec3 horizon_day_color : source_color = vec3(0.843, 0.933, 0.961);
uniform vec3 zenith_night_color : source_color = vec3(0.004, 0.006, 0.02);
uniform vec3 horizon_night_color : source_color = vec3(0.016, 0.024, 0.05);
uniform vec3 sunset_color : source_color = vec3(1.0, 0.55, 0.3);
uniform vec3 sun_color : source_color = vec3(1.0, 0.886, 0.69);
uniform vec3 ground_color : source_color = vec3(0.35, 0.42, 0.33);
uniform vec3 cloud_color : source_color = vec3(1.0, 1.0, 1.0);
uniform vec3 moon_color : source_color = vec3(0.92, 0.94, 1.0);
uniform vec3 warm_star_color : source_color = vec3(1.0, 0.82, 0.6);
uniform vec3 cool_star_color : source_color = vec3(0.72, 0.84, 1.0);
uniform vec3 orb_color : source_color = vec3(1.0, 0.78, 0.5);

// Tempo de jogo em segundos (global de project.godot, day_night_cycle.gd escreve a cada quadro).
global uniform float sky_time;

// Estado do céu (day_night_cycle.gd escreve quando muda o bastante para aparecer).
uniform vec3 sun_direction = vec3(0.0, 0.7, 0.7);
uniform vec3 moon_direction = vec3(0.0, -0.7, -0.7);
uniform float day_amount : hint_range(0.0, 1.0) = 1.0;
uniform float twilight_amount : hint_range(0.0, 1.0) = 0.0;
uniform float solar_eclipse : hint_range(0.0, 1.0) = 0.0;
uniform float lunar_eclipse : hint_range(0.0, 1.0) = 0.0;
// Estrela cadente: xyz = direção da cabeça / da ponta da cauda, w = brilho (0 = vaga livre).
uniform vec4 meteor_heads[METEOR_SLOTS];
uniform vec4 meteor_tails[METEOR_SLOTS];

uniform float sun_size : hint_range(0.0, 0.2) = 0.035;
uniform float moon_size : hint_range(0.0, 0.2) = 0.03;
uniform float cloud_coverage : hint_range(0.0, 1.0) = 0.42;
uniform float cloud_scale = 1.6;
uniform vec2 cloud_wind = vec2(0.012, 0.004);
uniform float star_density : hint_range(0.0, 1.0) = 0.9;
// Redemoinho de estrelas: centro (ao norte, ~54° de altura, longe do caminho da lua), quanto os
// braços enrolam, achatamento, nitidez dos braços e até onde vão (ângulo em radianos do centro).
uniform vec3 swirl_center = vec3(-0.3, 0.8, -0.5);
uniform float swirl_twist : hint_range(0.0, 6.0) = 3.0;
uniform float swirl_squash : hint_range(0.5, 3.0) = 1.5;
uniform float swirl_arm_sharpness : hint_range(1.0, 30.0) = 5.0;
uniform float swirl_reach : hint_range(0.5, 3.0) = 1.8;
// Astro dourado parado na ponta de dentro do braço quente.
uniform vec3 orb_direction = vec3(-0.548, 0.787, -0.282);
uniform float orb_size : hint_range(0.0, 0.05) = 0.018;
// Além deste ângulo (radianos) do centro da lua o brilho dela é menor que 1e-5: nem calcula.
uniform float moon_reach = 0.3;


// Hash inteiro da célula (exato): o hash de ponto flutuante dava valores diferentes para o mesmo canto
// visto de células vizinhas, e as bordas das células apareciam como riscos retos nas nuvens.
uint hash_cell(uvec3 cell) {
	cell = cell * 1664525u + 1013904223u;
	cell.x += cell.y * cell.z;
	cell.y += cell.z * cell.x;
	cell.z += cell.x * cell.y;
	cell ^= cell >> 16u;
	cell.x += cell.y * cell.z;
	cell.y += cell.z * cell.x;
	cell.z += cell.x * cell.y;

	return cell.x ^ cell.y ^ cell.z;
}


float hash_3d(vec3 point) {
	uvec3 cell = uvec3(ivec3(floor(point)));

	return float(hash_cell(cell) >> 8u) / 16777216.0;
}


float value_noise_3d(vec3 point) {
	vec3 cell = floor(point);
	vec3 blend = fract(point);

	blend = blend * blend * (3.0 - 2.0 * blend);

	return mix(
		mix(
			mix(hash_3d(cell), hash_3d(cell + vec3(1.0, 0.0, 0.0)), blend.x),
			mix(hash_3d(cell + vec3(0.0, 1.0, 0.0)), hash_3d(cell + vec3(1.0, 1.0, 0.0)), blend.x),
			blend.y),
		mix(
			mix(hash_3d(cell + vec3(0.0, 0.0, 1.0)), hash_3d(cell + vec3(1.0, 0.0, 1.0)), blend.x),
			mix(hash_3d(cell + vec3(0.0, 1.0, 1.0)), hash_3d(cell + vec3(1.0, 1.0, 1.0)), blend.x),
			blend.y),
		blend.z);
}


float fractal_noise(vec3 point, int octaves) {
	float total = 0.0;
	float amplitude = 0.5;

	for (int octave = 0; octave < octaves; octave++) {
		total += amplitude * value_noise_3d(point);
		point = point * 2.03 + vec3(1.7, 9.2, 3.1);
		amplitude *= 0.5;
	}

	return total;
}


vec3 sky_gradient(vec3 direction, float sun_height) {
	float height = clamp(direction.y, 0.0, 1.0);
	float horizon_blend = pow(1.0 - height, 3.0);
	vec3 day = mix(zenith_day_color, horizon_day_color, horizon_blend);
	vec3 night = mix(zenith_night_color, horizon_night_color, horizon_blend);
	float toward_sun = max(dot(normalize(direction.xz + 0.0001), normalize(sun_direction.xz + 0.0001)), 0.0);
	float sunset_band = pow(1.0 - height, 7.0);
	float sunset_glow = twilight_amount * sunset_band * (0.25 + 0.75 * toward_sun * toward_sun);
	vec3 color = mix(night, day, day_amount);

	color = mix(color, sunset_color * mix(0.45, 1.0, day_amount), clamp(sunset_glow, 0.0, 1.0));

	return color * (1.0 - 0.8 * solar_eclipse);
}


vec3 sun_disc(vec3 direction) {
	float angle = acos(clamp(dot(direction, sun_direction), -1.0, 1.0));
	float disc = 1.0 - smoothstep(sun_size * 0.9, sun_size, angle);
	float halo = exp(-angle * 16.0) * 0.12 + exp(-angle * 60.0) * 0.45;
	float corona = solar_eclipse * exp(-abs(angle - sun_size) * 60.0) * 2.2;
	float covered = solar_eclipse * (1.0 - smoothstep(sun_size * 0.95, sun_size * 1.0, angle));
	float above_horizon = smoothstep(-0.02, 0.02, sun_direction.y);

	return sun_color * above_horizon * (disc * 4.0 * (1.0 - covered) + halo * (1.0 - solar_eclipse) + corona);
}


vec3 moon_disc(vec3 direction, float night_amount) {
	if (dot(direction, moon_direction) < cos(moon_reach)) {
		return vec3(0.0);
	}

	float angle = acos(clamp(dot(direction, moon_direction), -1.0, 1.0));
	float disc = 1.0 - smoothstep(moon_size * 0.92, moon_size, angle);
	vec3 surface_point = (direction - moon_direction) / moon_size;
	float maria = smoothstep(0.45, 0.7, fractal_noise(surface_point * 2.5 + vec3(3.0), 3));
	vec3 lit = moon_color * (1.0 - 0.35 * maria);
	vec3 blood = vec3(0.55, 0.16, 0.08) * (0.7 - 0.25 * maria);
	float glow = exp(-angle * 40.0) * 0.18;
	float above_horizon = smoothstep(-0.02, 0.03, moon_direction.y);

	return mix(lit, blood, lunar_eclipse) * above_horizon * (disc * 1.6 + glow * (1.0 - 0.7 * lunar_eclipse)) * night_amount;
}


// Redemoinho de estrelas: dois braços em espiral logarítmica em volta de swirl_center, medidos pelo
// ângulo até o centro (achatado em swirl_squash), por isso os braços passam do zênite e descem do
// outro lado do céu. Devolve (densidade do braço 0..1, quanto é o braço quente 0..1).
vec2 star_swirl(vec3 direction) {
	vec3 center = normalize(swirl_center);
	vec3 side = normalize(cross(center, vec3(0.0, 1.0, 0.0)));
	vec3 rise = cross(side, center);
	vec2 plane = vec2(dot(direction, side), dot(direction, rise));
	vec2 squashed = plane * vec2(1.0, swirl_squash);
	float angle_to_center = atan(length(plane), dot(direction, center));
	float radius = max(angle_to_center * length(squashed) / max(length(plane), 0.0001), 0.001);
	float arm_phase = atan(squashed.y, squashed.x) - swirl_twist * log(radius);
	float arm = pow(0.5 + 0.5 * cos(2.0 * arm_phase), swirl_arm_sharpness);
	float reach = smoothstep(0.18, 0.38, radius) * (1.0 - smoothstep(swirl_reach * 0.6, swirl_reach, radius));
	float clumps = smoothstep(0.25, 0.75, value_noise_3d(direction * 9.0));
	float warmth = smoothstep(-0.35, 0.35, cos(arm_phase));

	return vec2(arm * reach * mix(0.45, 1.0, clumps), warmth);
}


// Raio de difração: forte e fino no eixo, apagando até spike_length (em células) da estrela.
float diffraction_ray(float along, float across, float spike_length, float ray_width) {
	float fade = 1.0 - smoothstep(0.0, spike_length, abs(along));

	return fade * fade * exp(-abs(across) / ray_width);
}


// Face do cubo que a direção atravessa: colunas = eixo da face (com sinal), eixo u, eixo v.
mat3 cube_face_axes(vec3 direction) {
	vec3 magnitude = abs(direction);
	vec3 side = sign(direction);

	if (magnitude.x >= magnitude.y && magnitude.x >= magnitude.z) {
		return mat3(vec3(side.x, 0.0, 0.0), vec3(0.0, 0.0, 1.0), vec3(0.0, 1.0, 0.0));
	}

	if (magnitude.y >= magnitude.z) {
		return mat3(vec3(0.0, side.y, 0.0), vec3(1.0, 0.0, 0.0), vec3(0.0, 0.0, 1.0));
	}

	return mat3(vec3(0.0, 0.0, side.z), vec3(1.0, 0.0, 0.0), vec3(0.0, 1.0, 0.0));
}


// Uma camada de estrelas em células de ângulo igual sobre as faces do cubo (cada célula cobre quase o
// mesmo pedaço do céu, a borda da face cai na borda da célula): no máximo uma estrela por célula,
// parada no céu, sem tremer. A chance soma o campo ralo e o braço do redemoinho medido na estrela;
// tamanho, brilho e cor (quente ou fria, puxada pela cor do braço) vêm do hash da célula. Estrelas
// com raios de difração ficam longe da borda da célula para o raio não ser cortado.
vec3 star_layer(vec3 direction, mat3 face, vec2 face_angles, float cells_per_face, float field_chance, float swirl_chance, float star_radius, float spike_length, float brightness) {
	float cells_per_radian = cells_per_face / (0.5 * PI);
	vec2 cell = floor(face_angles * cells_per_radian);
	vec3 cell_key = vec3(cell, dot(face[0], vec3(1.0, 3.0, 9.0)) * 1000.0 + cells_per_face);
	float chance = hash_3d(cell_key);

	if (chance < 1.0 - (field_chance + swirl_chance) * star_density) {
		return vec3(0.0);
	}

	// Célula de ângulo igual mede 0,71 a 1 do ângulo nominal: a folga cobre o pior caso.
	float margin = min(max(star_radius, spike_length) * 1.42, 0.49);
	vec2 jitter = vec2(hash_3d(cell_key + 11.0), hash_3d(cell_key + 23.0));
	vec2 star_angles = (cell + margin + jitter * (1.0 - 2.0 * margin)) / cells_per_radian;
	vec2 star_plane = tan(star_angles);
	vec3 star_direction = normalize(face[0] + face[1] * star_plane.x + face[2] * star_plane.y);
	float plane_stretch = 1.0 + dot(star_plane, star_plane);
	float cell_area = (1.0 + star_plane.x * star_plane.x) * (1.0 + star_plane.y * star_plane.y) / pow(plane_stretch, 1.5);
	vec2 swirl = star_swirl(star_direction);
	float has_star = step(1.0 - (field_chance + swirl_chance * swirl.x) * star_density * cell_area, chance);
	vec3 offset = (direction - star_direction) * cells_per_radian;
	// Raios na vertical e na horizontal do céu; o desvio mínimo só evita divisão por zero no zênite.
	vec3 across = normalize(cross(vec3(0.0, 1.0, 0.0), star_direction) + vec3(0.0, 0.0, 0.0001));
	vec2 flat_offset = vec2(dot(offset, across), dot(offset, cross(star_direction, across)));
	vec2 diagonal_offset = vec2(flat_offset.x + flat_offset.y, flat_offset.x - flat_offset.y) * 0.7071;
	float size_roll = hash_3d(cell_key + 51.0);
	float radius = star_radius * mix(0.55, 1.0, size_roll);
	float distance_to_star = length(flat_offset);
	float core = smoothstep(radius, radius * 0.35, distance_to_star);
	float halo = exp(-3.0 * distance_to_star / radius) * 0.5;
	float ray_width = radius * 0.1;
	float spikes = 0.0;
	float twinkle = 0.8 + 0.2 * sin(sky_time * (1.5 + 3.0 * hash_3d(cell_key + 7.0)) + chance * 40.0);
	float warmth = clamp(swirl.x * (swirl.y - 0.5) * 1.6 + hash_3d(cell_key + 63.0), 0.0, 1.0);
	vec3 tint = mix(cool_star_color, warm_star_color, warmth);
	float shine = brightness * mix(0.3, 1.0, size_roll * size_roll) * (1.0 + 0.5 * swirl.x);

	if (spike_length > 0.0) {
		spikes = diffraction_ray(flat_offset.x, flat_offset.y, spike_length, ray_width)
			+ diffraction_ray(flat_offset.y, flat_offset.x, spike_length, ray_width)
			+ 0.3 * diffraction_ray(diagonal_offset.x, diagonal_offset.y, spike_length * 0.45, ray_width)
			+ 0.3 * diffraction_ray(diagonal_offset.y, diagonal_offset.x, spike_length * 0.45, ray_width);
	}

	return tint * shine * twinkle * has_star * (core + halo + spikes * 0.8);
}


// Astro dourado: disco creme com halo laranja, menor que a lua.
vec3 swirl_orb(vec3 direction) {
	float angle = acos(clamp(dot(direction, normalize(orb_direction)), -1.0, 1.0));
	float disc = smoothstep(orb_size, orb_size * 0.8, angle);
	float glow = exp(-2.0 * angle / orb_size) * 1.4 + exp(-angle * 30.0) * 0.08;

	return orb_color * (disc * 3.0 + glow);
}


vec3 night_sky(vec3 direction, float night_amount) {
	if (night_amount <= 0.0 || direction.y <= 0.0) {
		return vec3(0.0);
	}

	mat3 face = cube_face_axes(direction);
	vec2 face_plane = vec2(dot(direction, face[1]), dot(direction, face[2])) / dot(direction, face[0]);
	vec2 face_angles = atan(face_plane);
	// Camadas (células por face, chance no campo, chance a mais no braço, raio e raio de difração em
	// células, brilho): poeira fina, estrelas médias com halo, brilhantes com raios e raros faróis.
	vec3 dust_stars = star_layer(direction, face, face_angles, 174.0, 0.06, 0.9, 0.15, 0.0, 0.7);
	vec3 medium_stars = star_layer(direction, face, face_angles, 68.0, 0.009, 0.55, 0.11, 0.0, 1.8);
	vec3 bright_stars = star_layer(direction, face, face_angles, 28.0, 0.004, 0.3, 0.07, 0.3, 4.0);
	vec3 beacon_stars = star_layer(direction, face, face_angles, 8.0, 0.0, 0.2, 0.03, 0.33, 8.0);
	float horizon_fade = smoothstep(0.0, 0.18, direction.y);

	return (dust_stars + medium_stars + bright_stars + beacon_stars + swirl_orb(direction))
		* night_amount * horizon_fade;
}


vec4 cloud_layer(vec3 direction, float sun_height) {
	if (cloud_coverage <= 0.0 || direction.y <= 0.02) {
		return vec4(0.0);
	}

	vec2 plane = direction.xz / max(direction.y, 0.06) * cloud_scale + cloud_wind * sky_time;
	float shape = fractal_noise(vec3(plane, sky_time * 0.01), CLOUD_OCTAVES);
	float density = smoothstep(1.0 - cloud_coverage, 1.0 - cloud_coverage + 0.1, shape);
	float thick = smoothstep(0.55, 0.85, shape);
	float toward_sun = max(dot(direction, sun_direction), 0.0);
	vec3 lit = mix(cloud_color, sunset_color * 1.1, twilight_amount * 0.75);
	vec3 shaded = mix(vec3(0.62, 0.68, 0.8), vec3(0.45, 0.35, 0.42), twilight_amount);
	vec3 day_cloud = mix(lit, shaded, thick * 0.6) + sun_color * pow(toward_sun, 12.0) * 0.4;
	vec3 night_cloud = vec3(0.05, 0.06, 0.09) + moon_color * 0.04;
	float horizon_fade = smoothstep(0.02, 0.2, direction.y);

	return vec4(mix(night_cloud, day_cloud, day_amount) * (1.0 - 0.75 * solar_eclipse), density * horizon_fade);
}


float meteor_streak(vec3 direction, vec4 head, vec4 tail) {
	vec3 head_direction = normalize(head.xyz);
	vec3 tail_direction = normalize(tail.xyz);
	vec3 path = head_direction - tail_direction;
	float path_length = max(length(path), 0.0001);
	float along = clamp(dot(direction - tail_direction, path) / (path_length * path_length), 0.0, 1.0);
	vec3 closest = tail_direction + path * along;
	float width = 0.0005 + 0.0011 * along;
	float distance_to_line = length(direction - closest);
	float line = smoothstep(width, 0.0, distance_to_line) + 0.25 * smoothstep(width * 3.0, 0.0, distance_to_line);

	return line * along * along * head.w * 2.0 * step(0.0, direction.y);
}


void sky() {
	vec3 direction = normalize(EYEDIR);
	float sun_height = sun_direction.y;
	float night_amount = clamp(1.0 - day_amount * 1.6, 0.0, 1.0);
	vec3 color = sky_gradient(direction, sun_height);

	if (direction.y < 0.0) {
		vec3 ground = mix(color, ground_color, 0.55) * mix(0.08, 1.0, day_amount);

		COLOR = mix(color, ground, smoothstep(0.0, -0.35, direction.y));
	} else if (AT_CUBEMAP_PASS) {
		vec4 clouds = cloud_layer(direction, sun_height);

		COLOR = mix(color, clouds.rgb, clouds.a);
	} else {
		vec4 clouds = cloud_layer(direction, sun_height);
		vec3 heavens = night_sky(direction, night_amount + solar_eclipse * 0.6);
		float meteors = 0.0;

		for (int slot = 0; slot < METEOR_SLOTS; slot++) {
			if (meteor_heads[slot].w > 0.0) {
				meteors += meteor_streak(direction, meteor_heads[slot], meteor_tails[slot]);
			}
		}

		color += heavens + moon_disc(direction, max(night_amount, 0.35)) + sun_disc(direction);
		color += vec3(1.0, 0.95, 0.85) * meteors;
		COLOR = mix(color, clouds.rgb, clouds.a * (1.0 - 0.9 * night_amount));
	}
}
