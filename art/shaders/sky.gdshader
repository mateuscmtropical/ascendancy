shader_type sky;
// Céu procedural da cidade: gradiente azul saturado de dia (zênite #5C8FD1, horizonte #D7EEF5), pôr do
// sol quente, noite escura sem poluição luminosa com estrelas densas, a faixa da Via Láctea, duas
// galáxias distantes e a lua; nuvens que andam devagar; estrelas cadentes e eclipses vindos de
// features/sky/day_night_cycle.gd. Tudo na direção do olhar (EYEDIR), sem textura.

const int METEOR_SLOTS = 8;
const int CLOUD_OCTAVES = 5;
const int DUST_OCTAVES = 4;

uniform vec3 zenith_day_color : source_color = vec3(0.361, 0.561, 0.82);
uniform vec3 horizon_day_color : source_color = vec3(0.843, 0.933, 0.961);
uniform vec3 zenith_night_color : source_color = vec3(0.008, 0.012, 0.035);
uniform vec3 horizon_night_color : source_color = vec3(0.03, 0.045, 0.09);
uniform vec3 sunset_color : source_color = vec3(1.0, 0.55, 0.3);
uniform vec3 sun_color : source_color = vec3(1.0, 0.886, 0.69);
uniform vec3 ground_color : source_color = vec3(0.35, 0.42, 0.33);
uniform vec3 cloud_color : source_color = vec3(1.0, 1.0, 1.0);
uniform vec3 moon_color : source_color = vec3(0.92, 0.94, 1.0);

// Estado do céu (day_night_cycle.gd escreve a cada quadro).
uniform vec3 sun_direction = vec3(0.0, 0.7, 0.7);
uniform vec3 moon_direction = vec3(0.0, -0.7, -0.7);
uniform float day_amount : hint_range(0.0, 1.0) = 1.0;
uniform float twilight_amount : hint_range(0.0, 1.0) = 0.0;
uniform float cloud_time = 0.0;
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
uniform vec3 galaxy_plane_normal = vec3(0.42, 0.3, 0.86);


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


float milky_way(vec3 direction) {
	vec3 normal = normalize(galaxy_plane_normal);
	float band_offset = dot(direction, normal);
	float band = exp(-band_offset * band_offset * 28.0);
	float core = exp(-pow(length(direction - normalize(cross(normal, vec3(0.0, 1.0, 0.0)) + vec3(0.0, 0.25, 0.0))), 2.0) * 3.0);
	float clouds = fractal_noise(direction * 6.0, DUST_OCTAVES);
	float dust = smoothstep(0.42, 0.62, fractal_noise(direction * 11.0 + vec3(5.0), DUST_OCTAVES)) * exp(-band_offset * band_offset * 120.0);

	return band * (0.35 + 0.9 * clouds) * (1.0 + 1.5 * core) * (1.0 - 0.85 * dust);
}


float star_field(vec3 direction, float twinkle_time) {
	vec3 cell_point = direction * 260.0;
	vec3 cell = floor(cell_point);
	float chance = hash_3d(cell);
	vec3 star_center = cell + vec3(hash_3d(cell + 11.0), hash_3d(cell + 23.0), hash_3d(cell + 37.0)) * 0.6 + 0.2;
	float distance_to_star = length(cell_point - star_center);
	float brightness = pow(hash_3d(cell + 51.0), 6.0) * 3.0 + 0.25;
	float twinkle = 0.75 + 0.25 * sin(twinkle_time * (2.0 + 4.0 * hash_3d(cell + 7.0)) + chance * 40.0);
	float is_star = step(1.0 - 0.09 * star_density, chance);

	return is_star * brightness * twinkle * smoothstep(0.35, 0.0, distance_to_star);
}


float distant_galaxy(vec3 direction, vec3 center, vec3 axis, float size) {
	vec3 offset = direction - normalize(center);
	float along = dot(offset, normalize(axis));
	float across = length(offset - normalize(axis) * along);

	return exp(-(along * along) / (size * size) - (across * across) / (size * size * 0.12));
}


vec3 night_sky(vec3 direction, float night_amount) {
	float stars = star_field(direction, TIME);
	float galaxy_band = milky_way(direction);
	float galaxies = distant_galaxy(direction, vec3(-0.5, 0.62, 0.6), vec3(1.0, 0.3, 0.2), 0.035)
		+ distant_galaxy(direction, vec3(0.7, 0.45, -0.55), vec3(0.2, 1.0, 0.4), 0.025) * 0.7;
	vec3 band_color = mix(vec3(0.55, 0.62, 0.85), vec3(0.95, 0.85, 0.7), galaxy_band * 0.6);
	float horizon_fade = smoothstep(0.0, 0.18, direction.y);

	return (vec3(stars) + band_color * galaxy_band * 0.42 + vec3(0.8, 0.75, 0.95) * galaxies * 0.45)
		* night_amount * horizon_fade;
}


vec4 cloud_layer(vec3 direction, float sun_height) {
	vec2 plane = direction.xz / max(direction.y, 0.06) * cloud_scale + cloud_wind * cloud_time;
	float shape = fractal_noise(vec3(plane, cloud_time * 0.01), CLOUD_OCTAVES);
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
			meteors += meteor_streak(direction, meteor_heads[slot], meteor_tails[slot]);
		}

		color += heavens + moon_disc(direction, max(night_amount, 0.35)) + sun_disc(direction);
		color += vec3(1.0, 0.95, 0.85) * meteors;
		COLOR = mix(color, clouds.rgb, clouds.a * (1.0 - 0.15 * night_amount));
	}
}
