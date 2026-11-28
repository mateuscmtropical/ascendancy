"""Synthesise the game's sound effects and ambience loops (all original, no recordings): footsteps, jump take-offs and
landings on stone, grass, wood and dirt (with a Godot AudioStreamRandomizer .tres per set), the air cut by a punch or a
kick, the fountain's water, the town's breeze and birdsong, the cathedral bell and the menu sounds.

Noise is shaped in the frequency domain (FFT of white noise times a spectral envelope), which makes every loop
periodic: the end flows into the start with no seam. Events (droplets, chirps) are placed modulo the loop length.

Usage: python tools_src/compose_sounds.py [output_dir]   (default art/audio)
"""

import sys
import wave
from pathlib import Path

import numpy as np

RATE = 44100
PEAK = 0.89  # -1 dBFS
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "art" / "audio"


def timeline(seconds: float) -> np.ndarray:
    return np.arange(round(seconds * RATE)) / RATE


def shaped_noise(length: int, envelope, generator: np.random.Generator) -> np.ndarray:
    """White noise filtered by envelope(frequencies) -> gain; periodic over length."""
    spectrum = np.fft.rfft(generator.standard_normal(length))
    frequencies = np.fft.rfftfreq(length, 1.0 / RATE)
    shaped = np.fft.irfft(spectrum * envelope(frequencies), length)

    return shaped / (np.abs(shaped).max() + 1e-9)


def band(low: float, high: float, slope: float = 2.0):
    """Smooth band-pass gain: flat between low and high, falling off as a power law outside."""
    def envelope(frequencies: np.ndarray) -> np.ndarray:
        safe = np.maximum(frequencies, 1.0)
        rise = 1.0 / (1.0 + (low / safe) ** slope)
        fall = 1.0 / (1.0 + (safe / high) ** slope)

        return rise * fall

    return envelope


def slow_swell(length: int, cycles: tuple, depth: float, generator: np.random.Generator) -> np.ndarray:
    """Gentle periodic modulation: a sum of sines with whole cycles per loop, between 1 - depth and 1."""
    phase = np.arange(length) / length * 2.0 * np.pi
    wave_sum = sum(np.sin(cycle * phase + generator.uniform(0.0, 2.0 * np.pi)) / (index + 1) for index, cycle in enumerate(cycles))
    normalized = (wave_sum - wave_sum.min()) / (wave_sum.max() - wave_sum.min() + 1e-9)

    return 1.0 - depth + depth * normalized


def add_wrapped(target: np.ndarray, sound: np.ndarray, start: int) -> None:
    """Mix sound into target at start, wrapping past the end so loops stay seamless."""
    indices = (start + np.arange(len(sound))) % len(target)
    np.add.at(target, indices, sound)


def decay(seconds: float, time_constant: float) -> np.ndarray:
    return np.exp(-timeline(seconds) / time_constant)


def sweep(start_hz: float, end_hz: float, seconds: float) -> np.ndarray:
    """Sine gliding exponentially from start_hz to end_hz."""
    time = timeline(seconds)
    frequency = start_hz * (end_hz / start_hz) ** (time / seconds)

    return np.sin(2.0 * np.pi * np.cumsum(frequency) / RATE)


def fade_edges(sound: np.ndarray, attack: float, release: float) -> np.ndarray:
    count = len(sound)
    ramp_in = np.minimum(1.0, np.arange(count) / max(1, attack * RATE))
    ramp_out = np.minimum(1.0, (count - np.arange(count)) / max(1, release * RATE))

    return sound * ramp_in * ramp_out


def normalized(sound: np.ndarray, peak: float = PEAK) -> np.ndarray:
    return sound / (np.abs(sound).max() + 1e-9) * peak


# ---------- one-shots ----------

def thud(seconds: float, hz: float, time_constant: float) -> np.ndarray:
    """Low body thump of a foot landing: a sine dropping a little in pitch as it dies."""
    return sweep(hz * 1.3, hz, seconds) * decay(seconds, time_constant)


def burst(length: int, low: float, high: float, time_constant: float, generator: np.random.Generator, delay: int = 0) -> np.ndarray:
    """Band of noise starting at delay with an exponential decay."""
    sound = np.zeros(length)
    sound[delay:] = shaped_noise(length - delay, band(low, high, 2.0), generator) * decay((length - delay) / RATE, time_constant)

    return sound


def delayed(length: int, sound: np.ndarray, delay: int) -> np.ndarray:
    placed = np.zeros(length)
    placed[delay:] = sound[:length - delay]

    return placed


def crackle(length: int, density: float, time_constant: float, generator: np.random.Generator, delay: int = 0) -> np.ndarray:
    """Many tiny bright ticks thinning out over time: blades of grass and twigs bending under the sole."""
    ticks = np.zeros(length)
    count = int(density * time_constant * 4.0)
    positions = delay + (generator.exponential(time_constant, count) * RATE).astype(int)
    positions = positions[positions < length]
    ticks[positions] = generator.uniform(-1.0, 1.0, len(positions))

    return np.convolve(ticks, np.hanning(9), mode="same")


def wood_knock(length: int, generator: np.random.Generator, delay: int = 0) -> np.ndarray:
    """Hollow board: a few resonant modes of a plank over a joist, each with its own short decay."""
    time = timeline(length / RATE)
    base_hz = generator.uniform(105.0, 165.0)
    modes = ((1.0, 1.0, 0.07), (2.32, 0.55, 0.045), (3.9, 0.3, 0.03), (6.1, 0.15, 0.02))
    tone = sum(amplitude * np.sin(2.0 * np.pi * base_hz * ratio * generator.uniform(0.97, 1.03) * time) * np.exp(-time / time_constant) for ratio, amplitude, time_constant in modes)

    return delayed(length, tone, delay)


def creak(length: int, generator: np.random.Generator) -> np.ndarray:
    """Short creak of a loose board: a narrow tone gliding down, rough with fast amplitude flutter."""
    seconds = generator.uniform(0.12, 0.2)
    time = timeline(seconds)
    flutter = 0.6 + 0.4 * np.sin(2.0 * np.pi * generator.uniform(35.0, 60.0) * time)
    tone = sweep(generator.uniform(500.0, 800.0), generator.uniform(380.0, 520.0), seconds) * flutter * np.hanning(len(time))

    return delayed(length, np.pad(tone, (0, length)), int(generator.uniform(0.04, 0.08) * RATE))


def stone_contact(length: int, weight: float, generator: np.random.Generator, delay: int = 0) -> np.ndarray:
    """Leather sole on stone: a soft muffled knock and a short gritty scrape."""
    knock = delayed(length, thud(length / RATE, generator.uniform(80.0, 120.0), 0.02), delay)
    body = burst(length, generator.uniform(250.0, 450.0), generator.uniform(1400.0, 2200.0), generator.uniform(0.012, 0.022), generator, delay)
    grit = burst(length, 2500.0, 7000.0, generator.uniform(0.004, 0.008), generator, delay)

    return weight * (0.8 * knock + 0.9 * body + generator.uniform(0.1, 0.3) * grit)


def grass_contact(length: int, weight: float, generator: np.random.Generator, delay: int = 0) -> np.ndarray:
    """Sole pressing into lawn: a dull soft thump under a swish of leaves and fine crackle."""
    knock = delayed(length, thud(length / RATE, generator.uniform(60.0, 85.0), 0.03), delay)
    swish = burst(length, generator.uniform(900.0, 1500.0), generator.uniform(4500.0, 7000.0), generator.uniform(0.04, 0.07), generator, delay)
    ticks = crackle(length, generator.uniform(2500.0, 4500.0), generator.uniform(0.03, 0.06), generator, delay)

    return weight * (0.35 * knock + 0.55 * swish + 0.45 * normalized(ticks, 1.0))


def wood_contact(length: int, weight: float, generator: np.random.Generator, delay: int = 0) -> np.ndarray:
    """Boot on floorboards: the board's hollow knock plus a dry click of the heel."""
    click = burst(length, 1200.0, 5000.0, generator.uniform(0.003, 0.006), generator, delay)

    return weight * (0.9 * wood_knock(length, generator, delay) + 0.35 * click)


def dirt_contact(length: int, weight: float, generator: np.random.Generator, delay: int = 0) -> np.ndarray:
    """Sole on packed farm earth: a muffled low thump, the soft crush of loose soil and a few small pebbles."""
    knock = delayed(length, thud(length / RATE, generator.uniform(55.0, 80.0), 0.035), delay)
    crush = burst(length, generator.uniform(180.0, 320.0), generator.uniform(1100.0, 1800.0), generator.uniform(0.03, 0.05), generator, delay)
    pebbles = crackle(length, generator.uniform(600.0, 1100.0), generator.uniform(0.02, 0.04), generator, delay)

    return weight * (0.6 * knock + 0.7 * crush + 0.3 * normalized(pebbles, 1.0))


CONTACT_BY_SURFACE = {"stone": stone_contact, "grass": grass_contact, "wood": wood_contact, "dirt": dirt_contact}
SEED_BY_SURFACE = {"stone": 100, "grass": 200, "wood": 300, "dirt": 400}


def footstep(surface: str, variant: int) -> np.ndarray:
    """One step: heel strike then the roll onto the toe; gap, weights and tone change from variant to variant."""
    generator = np.random.default_rng(SEED_BY_SURFACE[surface] + variant)
    contact = CONTACT_BY_SURFACE[surface]
    length = int(0.32 * RATE)
    toe_delay = int(generator.uniform(0.045, 0.09) * RATE)
    heel = contact(length, 1.0, generator)
    toe = contact(length, generator.uniform(0.3, 0.6), generator, toe_delay)
    board_creak = creak(length, generator) * 0.25 if surface == "wood" and variant % 3 == 0 else np.zeros(length)

    return normalized(fade_edges(heel + toe + board_creak, 0.001, 0.04), generator.uniform(0.5, 0.75))


def jump_takeoff(surface: str, variant: int) -> np.ndarray:
    """Push-off of a jump: both soles scuff as the weight leaves the ground, lighter than a step."""
    generator = np.random.default_rng(SEED_BY_SURFACE[surface] + 50 + variant)
    contact = CONTACT_BY_SURFACE[surface]
    length = int(0.3 * RATE)
    scuff = burst(length, 900.0, 5000.0, 0.05, generator, int(0.01 * RATE))
    push = contact(length, 0.6, generator) + contact(length, 0.5, generator, int(generator.uniform(0.015, 0.03) * RATE))

    return normalized(fade_edges(push + 0.25 * scuff, 0.002, 0.05), 0.45)


def jump_landing(surface: str, variant: int) -> np.ndarray:
    """Both feet land a few hundredths apart: heavier, with a deep body thump and a longer settle."""
    generator = np.random.default_rng(SEED_BY_SURFACE[surface] + 80 + variant)
    contact = CONTACT_BY_SURFACE[surface]
    length = int(0.5 * RATE)
    second_foot = int(generator.uniform(0.02, 0.045) * RATE)
    body = thud(length / RATE, generator.uniform(50.0, 65.0), 0.06)
    feet = contact(length, 1.0, generator) + contact(length, generator.uniform(0.7, 0.9), generator, second_foot)
    settle = contact(length, 0.25, generator, int(generator.uniform(0.12, 0.18) * RATE))

    return normalized(fade_edges(feet + 0.7 * body + settle, 0.001, 0.08), 0.85)


# Air cut by a limb, per attack: (seconds, when the swing is fastest, how long the rush lasts, low band, high band, peak).
# The game starts the sound SWING_LEAD_SECONDS before the blow lands (features/combat/unarmed_fighter.gd), so the
# fastest instant has to sit that far into the sound.
SWING_BY_ATTACK = {
    "punch": (0.22, 0.09, 0.032, (500.0, 1800.0), (1800.0, 7000.0), 0.5),
    "kick": (0.34, 0.1, 0.05, (220.0, 900.0), (900.0, 4200.0), 0.7),
}
SEED_BY_ATTACK = {"punch": 500, "kick": 600}
SWING_VARIANTS = 4


def swing(attack: str, variant: int) -> np.ndarray:
    """Whoosh of a punch or a kick: a rush of air that swells and brightens up to the fastest instant and dies after it,
    with the dull flap of the sleeve or the trouser leg right behind."""
    generator = np.random.default_rng(SEED_BY_ATTACK[attack] + variant)
    seconds, fastest, rush_seconds, low_band, high_band, peak = SWING_BY_ATTACK[attack]
    length = int(seconds * RATE)
    time = timeline(seconds)[:length]
    rush = np.exp(-0.5 * ((time - fastest) / (rush_seconds * generator.uniform(0.85, 1.15))) ** 2)
    air = shaped_noise(length, band(*low_band), generator) * rush ** 0.6
    hiss = shaped_noise(length, band(*high_band), generator) * rush ** 1.6
    flap = burst(length, 120.0, 500.0, 0.03, generator, int((fastest + 0.01) * RATE))

    return normalized(fade_edges(air + generator.uniform(0.7, 1.0) * hiss + 0.35 * flap, 0.004, 0.05), peak)


DESTRUCTION_VARIANTS = 4
SEED_BY_DESTRUCTION = {"hit_wood": 700, "hit_stone": 710, "break_wood": 720, "break_stone": 730, "debris_wood": 740, "debris_stone": 750}


def scattered(length: int, count: int, start: float, end: float, make, generator: np.random.Generator) -> np.ndarray:
    """count copies of make(length, generator, delay) at random instants between start and end seconds, quieter later."""
    total = np.zeros(length)

    for index in range(count):
        at = generator.uniform(start, end)
        total += make(length, generator, int(at * RATE)) * generator.uniform(0.3, 1.0) * (1.0 - 0.6 * (at - start) / (end - start + 1e-9))

    return total


def stone_clack(length: int, generator: np.random.Generator, delay: int = 0) -> np.ndarray:
    """A chunk of stone hitting the ground: a short low knock and a dry gritty click."""
    knock = delayed(length, thud(length / RATE, generator.uniform(110.0, 190.0), generator.uniform(0.015, 0.03)), delay)
    click = burst(length, generator.uniform(500.0, 900.0), generator.uniform(2500.0, 4500.0), generator.uniform(0.008, 0.02), generator, delay)

    return 0.8 * knock + 0.9 * click


def destruction(kind: str, variant: int) -> np.ndarray:
    """Sounds of things being hit and broken; the game plays them lower and louder the stronger the blow
    (Destruction.play_sound_at), so each is written at the size of a medium blow."""
    generator = np.random.default_rng(SEED_BY_DESTRUCTION[kind] + variant)
    return normalized(fade_edges(DESTRUCTION_MAKERS[kind](generator), 0.002, 0.08))


def hit_wood(generator: np.random.Generator) -> np.ndarray:
    """Fist or boot on a board that holds: hollow knock of the planks, the dull thump of the blow and a rattle."""
    length = int(0.45 * RATE)
    blow = delayed(length, thud(length / RATE, generator.uniform(70.0, 95.0), 0.04), 0)
    rattle = scattered(length, 3, 0.03, 0.12, wood_knock, generator)

    return 0.9 * wood_knock(length, generator) + 0.7 * blow + 0.3 * rattle + 0.25 * burst(length, 1500.0, 5000.0, 0.005, generator)


def hit_stone(generator: np.random.Generator) -> np.ndarray:
    """Blow on solid stone: a dead heavy thump with almost no ring and a puff of grit."""
    length = int(0.4 * RATE)
    blow = thud(length / RATE, generator.uniform(55.0, 75.0), 0.05)
    grit = burst(length, 1800.0, 6000.0, generator.uniform(0.01, 0.02), generator)

    return blow + 0.35 * burst(length, 200.0, 900.0, 0.03, generator) + 0.2 * grit


def break_wood(generator: np.random.Generator) -> np.ndarray:
    """Planks giving way: a sharp crack, the dry tearing of splinters and the boards clattering down after it."""
    length = int(1.3 * RATE)
    crack = burst(length, 300.0, 6000.0, generator.uniform(0.006, 0.012), generator) + delayed(length, thud(length / RATE, 85.0, 0.06), 0)
    splinters = normalized(crackle(length, generator.uniform(6000.0, 9000.0), 0.09, generator, int(0.01 * RATE)), 1.0)
    clatter = scattered(length, 7, 0.15, 0.9, wood_knock, generator)

    return 1.0 * crack + 0.5 * splinters + 0.6 * clatter


def break_stone(generator: np.random.Generator) -> np.ndarray:
    """Masonry coming apart: a deep boom, the rumble of the blocks sliding and a long patter of chunks landing."""
    length = int(2.2 * RATE)
    boom = thud(length / RATE, generator.uniform(42.0, 55.0), 0.25)
    rumble = burst(length, 40.0, 400.0, 0.5, generator)
    crumble = normalized(crackle(length, generator.uniform(1500.0, 2500.0), 0.35, generator, int(0.05 * RATE)), 1.0)
    chunks = scattered(length, 14, 0.1, 1.6, stone_clack, generator)

    return 1.0 * boom + 0.7 * rumble + 0.25 * crumble + 0.5 * chunks


def debris_wood(generator: np.random.Generator) -> np.ndarray:
    """A loose plank landing: one hollow knock and a smaller bounce."""
    length = int(0.35 * RATE)

    return wood_knock(length, generator) + 0.4 * wood_knock(length, generator, int(generator.uniform(0.08, 0.14) * RATE))


def debris_stone(generator: np.random.Generator) -> np.ndarray:
    """A stone block landing: a clack and a small second hit as it settles."""
    length = int(0.35 * RATE)

    return stone_clack(length, generator) + 0.35 * stone_clack(length, generator, int(generator.uniform(0.07, 0.12) * RATE))


DESTRUCTION_MAKERS = {"hit_wood": hit_wood, "hit_stone": hit_stone, "break_wood": break_wood, "break_stone": break_stone, "debris_wood": debris_wood, "debris_stone": debris_stone}


BOOM_VARIANTS = 3
SEED_BY_SPELL = {"explosion_charge": 800, "explosion_boom": 810, "fire_loop": 820, "cleave_slash": 830, "cleave_charge": 840}
SLASH_VARIANTS = 3


def explosion_charge() -> np.ndarray:
    """Power gathering for the explosion spell (3 s, stopped by the game at release): a hum rising an octave with
    its fifth, a pulse speeding up and a bright shimmer swelling on top, louder all the way."""
    generator = np.random.default_rng(SEED_BY_SPELL["explosion_charge"])
    seconds = 3.0
    time = timeline(seconds)
    progress = time / seconds
    hum = sweep(110.0, 220.0, seconds) + 0.5 * sweep(165.0, 330.0, seconds) + 0.25 * sweep(55.0, 110.0, seconds)
    pulse_rate = 3.0 + 13.0 * progress ** 1.5
    pulse = 0.65 + 0.35 * np.sin(2.0 * np.pi * np.cumsum(pulse_rate) / RATE)
    shimmer = shaped_noise(len(time), band(3000.0, 9000.0, 3.0), generator) * progress ** 2.0
    swell = 0.15 + 0.85 * progress ** 1.3

    return normalized(fade_edges((hum * pulse + 0.35 * shimmer) * swell, 0.15, 0.01))


def explosion_boom(variant: int) -> np.ndarray:
    """The blast: a sharp crack, a sub-bass punch dropping in pitch, a long rumble and debris raining down; the game
    plays it louder and lower the stronger the spell."""
    generator = np.random.default_rng(SEED_BY_SPELL["explosion_boom"] + variant)
    length = int(4.5 * RATE)
    crack = burst(length, 400.0, 8000.0, 0.025, generator)
    punch = sweep(generator.uniform(55.0, 65.0), 24.0, length / RATE) * decay(length / RATE, 0.7)
    rumble = burst(length, 25.0, 260.0, 1.4, generator, int(0.02 * RATE))
    roar = burst(length, 150.0, 1500.0, 0.5, generator, int(0.01 * RATE))
    rain = scattered(length, 26, 0.5, 3.6, stone_clack, generator)

    return normalized(fade_edges(0.8 * crack + 1.0 * punch + 0.9 * rumble + 0.45 * roar + 0.35 * rain, 0.001, 0.4))


def fire_loop() -> np.ndarray:
    """Grass and timber burning (seamless 6 s loop): a soft roar with slow swells and dry pops and crackles."""
    generator = np.random.default_rng(SEED_BY_SPELL["fire_loop"])
    length = int(6.0 * RATE)
    roar = shaped_noise(length, band(120.0, 900.0, 2.0), generator) * slow_swell(length, (2, 3, 5), 0.5, generator)
    crackles = np.zeros(length)

    for index in range(140):
        pop = burst(int(0.05 * RATE), 1500.0, 7000.0, generator.uniform(0.002, 0.008), generator)
        add_wrapped(crackles, pop * generator.uniform(0.2, 1.0), int(generator.uniform(0, length)))

    return normalized(0.5 * roar + 0.6 * crackles, 0.7)


def cleave_charge() -> np.ndarray:
    """Blade of air gathering for the line cut (2 s, stopped by the game at release): a thin metallic whine rising
    two octaves over a soft wind that tightens, louder all the way."""
    generator = np.random.default_rng(SEED_BY_SPELL["cleave_charge"])
    seconds = 2.0
    time = timeline(seconds)
    progress = time / seconds
    whine = sweep(440.0, 1760.0, seconds) + 0.4 * sweep(660.0, 2640.0, seconds)
    wind = shaped_noise(len(time), band(600.0, 4000.0, 2.0), generator)
    swell = 0.1 + 0.9 * progress ** 1.5

    return normalized(fade_edges((0.5 * whine * progress + 0.6 * wind) * swell, 0.1, 0.01))


def cleave_slash(variant: int) -> np.ndarray:
    """The cut: a ringing metallic shing over a fast tearing whoosh, then earth splitting and a low thud as the cut
    side drops; the game plays it louder and lower the stronger the spell."""
    generator = np.random.default_rng(SEED_BY_SPELL["cleave_slash"] + variant)
    length = int(2.6 * RATE)
    seconds = length / RATE
    ring_hz = generator.uniform(2300.0, 2700.0)
    ring = (sweep(ring_hz, ring_hz * 0.92, seconds) + 0.5 * sweep(ring_hz * 1.51, ring_hz * 1.4, seconds)) * decay(seconds, 0.35)
    whoosh = burst(length, 800.0, 7000.0, 0.12, generator)
    split = burst(length, 120.0, 1800.0, 0.3, generator, int(0.18 * RATE))
    thud = sweep(70.0, 35.0, seconds) * decay(seconds, 0.4)
    rubble = scattered(length, 14, 0.4, 2.0, stone_clack, generator)

    return normalized(fade_edges(0.55 * ring + 0.8 * whoosh + 0.6 * split + 0.7 * delayed(length, thud, int(0.25 * RATE)) + 0.3 * rubble, 0.001, 0.3))


def church_bell() -> np.ndarray:
    """Bronze bell strike in G: hum, prime, minor tierce, quint and nominal partials with their own decays, slightly
    detuned pairs for the slow beating of a real bell, and a clang at the strike."""
    seconds = 9.0
    time = timeline(seconds)
    prime = 196.0
    partials = ((0.5, 1.0, 4.5), (1.0, 0.8, 3.2), (1.183, 0.6, 2.4), (1.506, 0.35, 1.8), (2.0, 0.5, 1.5), (2.51, 0.25, 0.9), (3.01, 0.2, 0.7), (4.16, 0.12, 0.4))
    tone = sum(amplitude * (np.sin(2.0 * np.pi * prime * ratio * time) + 0.6 * np.sin(2.0 * np.pi * prime * ratio * 1.0015 * time + 1.3)) * np.exp(-time / time_constant) for ratio, amplitude, time_constant in partials)
    clang = shaped_noise(len(time), band(1200.0, 5000.0, 2.0), np.random.default_rng(7)) * np.exp(-time / 0.03)

    return normalized(fade_edges(tone + 0.4 * clang, 0.002, 1.0))


def interface_tone(notes: tuple, note_seconds: float, brightness: float) -> np.ndarray:
    """Soft wooden-chime notes in sequence (menu open/close)."""
    pieces = []

    for note_hz in notes:
        time = timeline(note_seconds * 2.5)
        tone = np.sin(2.0 * np.pi * note_hz * time) + brightness * np.sin(2.0 * np.pi * note_hz * 3.0 * time)
        pieces.append((fade_edges(tone * np.exp(-time / (note_seconds * 0.6)), 0.003, 0.04), int(len(pieces) * note_seconds * RATE)))

    total = np.zeros(max(len(piece) + offset for piece, offset in pieces))

    for piece, offset in pieces:
        total[offset:offset + len(piece)] += piece

    return normalized(fade_edges(total, 0.003, 0.05), 0.5)


def interface_click() -> np.ndarray:
    seconds = 0.06
    time = timeline(seconds)
    tick = np.sin(2.0 * np.pi * 1900.0 * time) * np.exp(-time / 0.008)
    noise = shaped_noise(len(time), band(2500.0, 8000.0), np.random.default_rng(3)) * np.exp(-time / 0.003)

    return normalized(fade_edges(tick + 0.5 * noise, 0.0005, 0.01), 0.45)


# ---------- loops ----------

def fountain_loop() -> np.ndarray:
    """Water falling into a basin: a broad splash hiss that breathes, a low churn and many small droplets."""
    generator = np.random.default_rng(11)
    seconds = 12.0
    length = int(seconds * RATE)
    splash = shaped_noise(length, band(300.0, 1800.0, 3.0), generator) * slow_swell(length, (3, 7, 13), 0.35, generator)
    churn = shaped_noise(length, band(80.0, 400.0, 2.0), generator) * slow_swell(length, (2, 5), 0.4, generator)
    water = 0.45 * splash + 0.45 * churn

    for _ in range(420):
        droplet_seconds = generator.uniform(0.02, 0.06)
        start_hz = generator.uniform(500.0, 1400.0)
        droplet = sweep(start_hz, start_hz * generator.uniform(1.6, 2.6), droplet_seconds) * decay(droplet_seconds, droplet_seconds / 3.0)
        add_wrapped(water, droplet * generator.uniform(0.05, 0.22), int(generator.uniform(0.0, length)))

    return normalized(water, 0.8)


def chirp_call(generator: np.random.Generator) -> np.ndarray:
    """Quick rising chirps in a short phrase (small songbird)."""
    notes = []

    for _ in range(int(generator.integers(3, 7))):
        note_seconds = generator.uniform(0.05, 0.09)
        low = generator.uniform(2800.0, 3800.0)
        notes.append(sweep(low, low * generator.uniform(1.25, 1.6), note_seconds) * np.hanning(round(note_seconds * RATE)))
        notes.append(np.zeros(int(generator.uniform(0.04, 0.09) * RATE)))

    return np.concatenate(notes)


def whistle_call(generator: np.random.Generator) -> np.ndarray:
    """Two-tone falling whistle, 'fee-bee'."""
    high = generator.uniform(3000.0, 3600.0)
    first = sweep(high, high * 0.98, 0.28) * np.hanning(round(0.28 * RATE))
    second = sweep(high * 0.8, high * 0.76, 0.32) * np.hanning(round(0.32 * RATE))

    return np.concatenate([first, np.zeros(int(0.06 * RATE)), second])


def trill_call(generator: np.random.Generator) -> np.ndarray:
    """Fast trill: a steady tone chopped thirty times a second."""
    seconds = generator.uniform(0.5, 0.9)
    time = timeline(seconds)
    tone = sweep(generator.uniform(4200.0, 4800.0), generator.uniform(3800.0, 4300.0), seconds)
    chopping = 0.5 + 0.5 * np.sin(2.0 * np.pi * generator.uniform(26.0, 34.0) * time)

    return tone * chopping ** 2 * np.hanning(len(time))


def town_ambience_loop() -> np.ndarray:
    """Daytime town square: a faint breeze, leaves stirring now and then, and distant birds of three kinds."""
    generator = np.random.default_rng(23)
    seconds = 48.0
    length = int(seconds * RATE)
    gusts = slow_swell(length, (2, 5, 9), 0.5, generator)
    breeze = shaped_noise(length, band(250.0, 900.0, 2.0), generator) * gusts
    leaves = shaped_noise(length, band(2500.0, 6000.0, 2.0), generator) * gusts ** 3
    ambience = 0.1 * breeze + 0.05 * leaves
    calls = (chirp_call, whistle_call, trill_call)

    for index in range(26):
        call = calls[index % len(calls)](generator)
        add_wrapped(ambience, call * generator.uniform(0.06, 0.18), int(generator.uniform(0.0, length)))

    return normalized(ambience, 0.75)


def write_wav(path: Path, sound: np.ndarray) -> None:
    samples = (np.clip(sound, -1.0, 1.0) * 32767.0).astype("<i2")

    with wave.open(str(path), "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(RATE)
        wav_file.writeframes(samples.tobytes())


SURFACES = tuple(CONTACT_BY_SURFACE)
STEP_VARIANTS = 10
JUMP_VARIANTS = 3

SOUNDS = {
    **{f"step_{surface}_{variant}": (lambda surface=surface, variant=variant: footstep(surface, variant)) for surface in SURFACES for variant in range(1, STEP_VARIANTS + 1)},
    **{f"jump_{surface}_{variant}": (lambda surface=surface, variant=variant: jump_takeoff(surface, variant)) for surface in SURFACES for variant in range(1, JUMP_VARIANTS + 1)},
    **{f"land_{surface}_{variant}": (lambda surface=surface, variant=variant: jump_landing(surface, variant)) for surface in SURFACES for variant in range(1, JUMP_VARIANTS + 1)},
    **{f"swing_{attack}_{variant}": (lambda attack=attack, variant=variant: swing(attack, variant)) for attack in SWING_BY_ATTACK for variant in range(1, SWING_VARIANTS + 1)},
    **{f"{kind}_{variant}": (lambda kind=kind, variant=variant: destruction(kind, variant)) for kind in SEED_BY_DESTRUCTION for variant in range(1, DESTRUCTION_VARIANTS + 1)},
    **{f"explosion_boom_{variant}": (lambda variant=variant: explosion_boom(variant)) for variant in range(1, BOOM_VARIANTS + 1)},
    "explosion_charge": explosion_charge,
    **{f"cleave_slash_{variant}": (lambda variant=variant: cleave_slash(variant)) for variant in range(1, SLASH_VARIANTS + 1)},
    "cleave_charge": cleave_charge,
    "fire_loop": fire_loop,
    "church_bell": church_bell,
    "ui_click": interface_click,
    "ui_open": lambda: interface_tone((660.0, 990.0), 0.07, 0.15),
    "ui_close": lambda: interface_tone((880.0, 587.0), 0.07, 0.15),
    "fountain_loop": fountain_loop,
    "town_ambience_loop": town_ambience_loop,
}


# Godot AudioStreamRandomizer per sound set: (variants, pitch spread, volume spread in dB)
RANDOMIZERS = {
    **{f"step_{surface}": (STEP_VARIANTS, 1.08, 3.0) for surface in SURFACES},
    **{f"jump_{surface}": (JUMP_VARIANTS, 1.06, 2.0) for surface in SURFACES},
    **{f"land_{surface}": (JUMP_VARIANTS, 1.05, 2.0) for surface in SURFACES},
    **{f"swing_{attack}": (SWING_VARIANTS, 1.1, 2.0) for attack in SWING_BY_ATTACK},
    **{kind: (DESTRUCTION_VARIANTS, 1.08, 2.0) for kind in SEED_BY_DESTRUCTION},
    "explosion_boom": (BOOM_VARIANTS, 1.04, 1.0),
    "cleave_slash": (SLASH_VARIANTS, 1.05, 1.0),
}


def write_randomizer(path: Path, name: str, variants: int, pitch_spread: float, volume_spread: float) -> None:
    """Godot resource that plays one of the set's wavs at random (never the same twice), with pitch and volume jitter."""
    resources = [f'[ext_resource type="AudioStream" path="res://art/audio/{name}_{variant}.wav" id="{variant}"]' for variant in range(1, variants + 1)]
    streams = [f'stream_{variant - 1}/stream = ExtResource("{variant}")' for variant in range(1, variants + 1)]
    header = [f"[gd_resource type=\"AudioStreamRandomizer\" load_steps={variants + 1} format=3]", ""]
    body = ["", "[resource]", f"random_pitch = {pitch_spread}", f"random_volume_offset_db = {volume_spread}", f"streams_count = {variants}"]

    path.write_text("\n".join(header + resources + body + streams) + "\n", encoding="utf-8", newline="\n")


def main() -> None:
    output_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else OUTPUT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    for name, make in SOUNDS.items():
        sound = make()
        write_wav(output_dir / f"{name}.wav", sound)
        print(f"SOUND {name}: {len(sound) / RATE:.2f} s")

    for name, settings in RANDOMIZERS.items():
        write_randomizer(output_dir / f"{name}.tres", name, *settings)


if __name__ == "__main__":
    main()
