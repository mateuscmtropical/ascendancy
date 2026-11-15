"""Synthesise the game's sound effects and ambience loops (all original, no recordings): footsteps on stone, the
fountain's water, the town's wind and birdsong, the cathedral bell and the menu sounds.

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
    return np.arange(int(seconds * RATE)) / RATE


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

def footstep(variant: int) -> np.ndarray:
    """Leather sole on stone: heel thump, a short gritty body and a fine scuff, each variant a little different."""
    generator = np.random.default_rng(100 + variant)
    seconds = 0.24
    length = int(seconds * RATE)
    heel_hz = generator.uniform(70.0, 95.0)
    body_low, body_high = generator.uniform(450.0, 700.0), generator.uniform(1800.0, 2600.0)
    heel = np.sin(2.0 * np.pi * heel_hz * timeline(seconds)) * decay(seconds, 0.018)
    body = shaped_noise(length, band(body_low, body_high, 3.0), generator) * decay(seconds, 0.022)
    grit = shaped_noise(length, band(3500.0, 9000.0, 2.0), generator) * decay(seconds, 0.006)
    scuff_start = int(generator.uniform(0.03, 0.05) * RATE)
    scuff = np.zeros(length)
    scuff_length = length - scuff_start
    scuff[scuff_start:] = shaped_noise(scuff_length, band(1500.0, 6000.0, 2.0), generator) * decay(scuff_length / RATE, 0.025)

    return normalized(fade_edges(0.9 * heel + 0.8 * body + 0.35 * grit + 0.25 * scuff, 0.001, 0.03), 0.7)


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
    splash = shaped_noise(length, band(350.0, 3000.0, 2.0), generator) * slow_swell(length, (3, 7, 13), 0.35, generator)
    churn = shaped_noise(length, band(80.0, 400.0, 2.0), generator) * slow_swell(length, (2, 5), 0.4, generator)
    water = 0.7 * splash + 0.45 * churn

    for _ in range(260):
        droplet_seconds = generator.uniform(0.02, 0.06)
        start_hz = generator.uniform(500.0, 1400.0)
        droplet = sweep(start_hz, start_hz * generator.uniform(1.6, 2.6), droplet_seconds) * decay(droplet_seconds, droplet_seconds / 3.0)
        add_wrapped(water, droplet * generator.uniform(0.08, 0.3), int(generator.uniform(0.0, length)))

    return normalized(water, 0.8)


def chirp_call(generator: np.random.Generator) -> np.ndarray:
    """Quick rising chirps in a short phrase (small songbird)."""
    notes = []

    for _ in range(int(generator.integers(3, 7))):
        note_seconds = generator.uniform(0.05, 0.09)
        low = generator.uniform(2800.0, 3800.0)
        notes.append(sweep(low, low * generator.uniform(1.25, 1.6), note_seconds) * np.hanning(int(note_seconds * RATE)))
        notes.append(np.zeros(int(generator.uniform(0.04, 0.09) * RATE)))

    return np.concatenate(notes)


def whistle_call(generator: np.random.Generator) -> np.ndarray:
    """Two-tone falling whistle, 'fee-bee'."""
    high = generator.uniform(3000.0, 3600.0)
    first = sweep(high, high * 0.98, 0.28) * np.hanning(int(0.28 * RATE))
    second = sweep(high * 0.8, high * 0.76, 0.32) * np.hanning(int(0.32 * RATE))

    return np.concatenate([first, np.zeros(int(0.06 * RATE)), second])


def trill_call(generator: np.random.Generator) -> np.ndarray:
    """Fast trill: a steady tone chopped thirty times a second."""
    seconds = generator.uniform(0.5, 0.9)
    time = timeline(seconds)
    tone = sweep(generator.uniform(4200.0, 4800.0), generator.uniform(3800.0, 4300.0), seconds)
    chopping = 0.5 + 0.5 * np.sin(2.0 * np.pi * generator.uniform(26.0, 34.0) * time)

    return tone * chopping ** 2 * np.hanning(len(time))


def town_ambience_loop() -> np.ndarray:
    """Daytime town square: soft wind with gusts, leaves rustling with the gusts, and distant birds of three kinds."""
    generator = np.random.default_rng(23)
    seconds = 48.0
    length = int(seconds * RATE)
    gusts = slow_swell(length, (2, 5, 9), 0.75, generator)
    wind = shaped_noise(length, band(60.0, 450.0, 2.0), generator) * gusts
    leaves = shaped_noise(length, band(1800.0, 7000.0, 2.0), generator) * gusts ** 2
    ambience = 0.45 * wind + 0.15 * leaves
    calls = (chirp_call, whistle_call, trill_call)

    for index in range(26):
        call = calls[index % len(calls)](generator)
        add_wrapped(ambience, call * generator.uniform(0.05, 0.16), int(generator.uniform(0.0, length)))

    return normalized(ambience, 0.75)


def write_wav(path: Path, sound: np.ndarray) -> None:
    samples = (np.clip(sound, -1.0, 1.0) * 32767.0).astype("<i2")

    with wave.open(str(path), "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(RATE)
        wav_file.writeframes(samples.tobytes())


SOUNDS = {
    **{f"footstep_stone_{variant}": (lambda variant=variant: footstep(variant)) for variant in range(1, 6)},
    "church_bell": church_bell,
    "ui_click": interface_click,
    "ui_open": lambda: interface_tone((660.0, 990.0), 0.07, 0.15),
    "ui_close": lambda: interface_tone((880.0, 587.0), 0.07, 0.15),
    "fountain_loop": fountain_loop,
    "town_ambience_loop": town_ambience_loop,
}


def main() -> None:
    output_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else OUTPUT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    for name, make in SOUNDS.items():
        sound = make()
        write_wav(output_dir / f"{name}.wav", sound)
        print(f"SOUND {name}: {len(sound) / RATE:.2f} s")


if __name__ == "__main__":
    main()
