"""Compose the town square's background music loop (original, synthesised, no recordings).

A calm daytime piece for a medieval-fantasy town: G major, 64 BPM, 40 bars of 4/4 = exactly 150 s.
Instruments: soft pad, plucked harp arpeggio, breathy flute melody, glockenspiel chimes, warm bass and a muted frame drum.
Seamless loop: every note and the reverb wrap around the loop end (circular convolution), so the end flows into the start.
Dark by design (low-passed, gentle dynamics) to leave room for the town ambience.

Usage: python tools_src/compose_town_music.py [output.wav]   (default art/audio/town_music_loop.wav)
"""

import subprocess
import sys
import wave
from pathlib import Path

import numpy as np

RATE = 32000
PEAK = 0.89  # -1 dBFS
BPM = 64
BEATS_PER_BAR = 4
BAR_COUNT = 40
BEAT_SECONDS = 60.0 / BPM
BAR_SECONDS = BEAT_SECONDS * BEATS_PER_BAR
LOOP_SECONDS = BAR_SECONDS * BAR_COUNT
LOOP_SAMPLES = round(LOOP_SECONDS * RATE)
OUTPUT_PATH = Path(__file__).resolve().parent.parent / "art" / "audio" / "town_music_loop.ogg"

# Chord name -> (bass note, three upper voices), MIDI numbers.
CHORDS = {
    "G": (43, [55, 59, 62]),
    "D/F#": (42, [57, 62, 66]),
    "Em": (40, [55, 59, 64]),
    "Bm": (47, [54, 59, 62]),
    "C": (48, [55, 60, 64]),
    "G/B": (47, [55, 62, 67]),
    "Am7": (45, [55, 60, 64]),
    "D": (38, [57, 62, 66]),
}

# Melody notes as (start beat in the 8-bar section, MIDI note, length in beats).
MELODY_A = [
    (0, 71, 2.5), (2.5, 74, 1.5), (4, 78, 3), (7, 76, 1), (8, 76, 2), (10, 71, 1), (11, 74, 1), (12, 74, 3),
    (15, 71, 1), (16, 72, 2.5), (18.5, 76, 1.5), (20, 74, 2), (22, 71, 2), (24, 72, 2), (26, 69, 1), (27, 71, 1),
    (28, 69, 4),
]
MELODY_A2 = MELODY_A[:12] + [
    (16, 76, 2), (18, 79, 2), (20, 79, 2), (22, 74, 2), (24, 74, 1.5), (25.5, 78, 0.5), (26, 76, 1), (27, 74, 1),
    (28, 71, 4),
]
MELODY_B = [
    (0, 76, 3), (3, 74, 1), (4, 71, 2), (6, 74, 2), (8, 72, 1.5), (9.5, 76, 0.5), (10, 79, 2), (12, 78, 2),
    (14, 76, 2), (16, 76, 1), (17, 79, 2), (19, 76, 1), (20, 78, 2), (22, 74, 2), (24, 71, 2), (26, 74, 1),
    (27, 79, 1), (28, 78, 3), (31, 74, 1),
]


class Section:
    """Eight bars: chords, melody, which layers play and how dense the harp is (steps per bar)."""

    def __init__(self, chords: str, melody: list, harp_steps: int, has_bells: bool, has_drum: bool, melody_gain: float):
        self.chords = chords.split(" | ")
        self.melody = melody
        self.harp_steps = harp_steps
        self.has_bells = has_bells
        self.has_drum = has_drum
        self.melody_gain = melody_gain


SECTIONS = [
    Section("G | D/F# | Em | Bm | C | G/B | Am7 | D", MELODY_A, 4, False, False, 0.8),
    Section("G | D/F# | Em | Bm | C | G/B | D | G", MELODY_A2, 8, True, False, 1.0),
    Section("C | G/B | Am7 | Em | C | D/F# | G | D", MELODY_B, 8, False, True, 0.9),
    Section("G | D/F# | Em | Bm | C | G/B | D | G", MELODY_A2, 8, True, True, 0.9),
    Section("G | Em | C | D | G | Bm | Am7 | D", [], 4, True, False, 0.0),
]
HARP_PATTERNS = {4: [0, 1, 2, 3], 8: [0, 1, 2, 3, 2, 1, 2, 3]}


def frequency(midi_note: float) -> float:
    return 440.0 * 2 ** ((midi_note - 69) / 12)


def timeline(seconds: float) -> np.ndarray:
    return np.arange(round(seconds * RATE)) / RATE


def release_ramp(time: np.ndarray, seconds: float, release: float) -> np.ndarray:
    return np.clip((seconds - time) / release, 0.0, 1.0)


def pad_note(midi_note: int, seconds: float) -> np.ndarray:
    time = timeline(seconds)
    base = frequency(midi_note)
    harmonics = range(1, 5)
    tone = sum(
        (1 / harmonic ** 2) * (np.sin(2 * np.pi * base * harmonic * time) + np.sin(2 * np.pi * base * harmonic * 1.003 * time + 1.0))
        for harmonic in harmonics
    )
    envelope = np.minimum(1, time / 1.6) * release_ramp(time, seconds, 2.0)

    return tone * envelope * 0.05


def harp(midi_note: int, velocity: float) -> np.ndarray:
    time = timeline(3.2)
    base = frequency(midi_note)
    partials = [(1, 1.0, 1.8), (2, 0.35, 1.0), (3, 0.14, 0.6), (4, 0.06, 0.4)]
    tone = sum(level * np.sin(2 * np.pi * base * number * time) * np.exp(-time / life) for number, level, life in partials)

    return tone * np.minimum(1, time / 0.004) * velocity * 0.11


def breath_noise(length: int, generator: np.random.Generator) -> np.ndarray:
    smooth = np.convolve(generator.standard_normal(length), np.ones(24) / 24, mode="same")

    return smooth / (np.abs(smooth).max() + 1e-9)


def flute(midi_note: int, seconds: float, generator: np.random.Generator) -> np.ndarray:
    time = timeline(seconds)
    base = frequency(midi_note)
    vibrato = 0.004 * np.minimum(1, np.maximum(0, time - 0.35) / 0.5) * np.sin(2 * np.pi * 5.0 * time)
    phase = 2 * np.pi * np.cumsum(base * (1 + vibrato)) / RATE
    tone = np.sin(phase) + 0.22 * np.sin(2 * phase) + 0.06 * np.sin(3 * phase)
    breath = breath_noise(len(time), generator) * 0.05
    envelope = np.minimum(1, time / 0.16) * release_ramp(time, seconds, 0.35) * (0.85 + 0.15 * np.sin(2 * np.pi * 0.7 * time))

    return (tone + breath) * envelope * 0.12


def chime(midi_note: int, velocity: float) -> np.ndarray:
    time = timeline(3.0)
    base = frequency(midi_note)
    tone = np.sin(2 * np.pi * base * time) + 0.25 * np.sin(2 * np.pi * base * 2.76 * time) * np.exp(-time * 6)

    return tone * np.exp(-time * 1.8) * np.minimum(1, time / 0.003) * velocity * 0.045


def bass(midi_note: int, seconds: float) -> np.ndarray:
    time = timeline(seconds)
    base = frequency(midi_note)
    tone = np.sin(2 * np.pi * base * time) + 0.25 * np.sin(4 * np.pi * base * time)

    return tone * np.minimum(1, time / 0.35) * release_ramp(time, seconds, 1.0) * 0.09


def frame_drum(velocity: float) -> np.ndarray:
    time = timeline(0.5)
    phase = 2 * np.pi * (62 * time + 55 * (1 - np.exp(-time * 22)) / 22)
    skin = np.sin(phase) * np.exp(-time * 8)

    return skin * np.minimum(1, time / 0.002) * velocity * 0.12


def spectral_filter(signal: np.ndarray, gain) -> np.ndarray:
    """Filter by multiplying the spectrum; circular, so a loop's end and start stay continuous."""
    spectrum = np.fft.rfft(signal)
    frequencies = np.fft.rfftfreq(len(signal), 1.0 / RATE)

    return np.fft.irfft(spectrum * gain(frequencies), len(signal))


def warm_reverb(signal: np.ndarray, seed: int) -> np.ndarray:
    generator = np.random.default_rng(seed)
    impulse = np.zeros(len(signal))
    tail = timeline(3.2)
    impulse[: len(tail)] = generator.standard_normal(len(tail)) * np.exp(-tail / 0.9)
    impulse[0] = 0.0
    impulse = spectral_filter(impulse, lambda frequencies: 1.0 / (1.0 + (frequencies / 3000.0) ** 2))
    impulse /= np.sqrt((impulse ** 2).sum())
    wet = np.fft.irfft(np.fft.rfft(signal) * np.fft.rfft(impulse), len(signal))

    return signal * 0.7 + wet * 0.55


def mix_master(mixed: np.ndarray) -> np.ndarray:
    """Roll off harsh highs and sub rumble, then normalise to -1 dBFS."""
    def tone_curve(frequencies: np.ndarray) -> np.ndarray:
        highs = 1.0 / (1.0 + (frequencies / 6500.0) ** 4)
        lows = 1.0 / (1.0 + (35.0 / np.maximum(frequencies, 1.0)) ** 2)

        return highs * lows

    filtered = np.stack([spectral_filter(channel, tone_curve) for channel in mixed])

    return filtered / np.abs(filtered).max() * PEAK


def compose() -> np.ndarray:
    channels = np.zeros((2, LOOP_SAMPLES))
    generator = np.random.default_rng(11)

    def add(sound: np.ndarray, start_seconds: float, pan: float = 0.5) -> None:
        indices = (round(start_seconds * RATE) + np.arange(len(sound))) % LOOP_SAMPLES
        channels[0, indices] += sound * np.cos(pan * np.pi / 2)
        channels[1, indices] += sound * np.sin(pan * np.pi / 2)

    def add_chord_layers(chord_name: str, bar_start: float, section: Section) -> None:
        bass_note, tones = CHORDS[chord_name]
        steps = HARP_PATTERNS[section.harp_steps]
        step_seconds = BAR_SECONDS / section.harp_steps
        notes = tones + [tones[0] + 12]

        for tone_index, tone in enumerate(tones + [tones[1] + 12]):
            add(pad_note(tone, BAR_SECONDS + 2.0), bar_start, pan=0.3 + 0.4 * (tone_index % 2) + 0.05 * tone_index)

        add(bass(bass_note, BAR_SECONDS + 0.6), bar_start, pan=0.5)

        for step_index in range(section.harp_steps):
            jitter = generator.uniform(-0.012, 0.012)
            velocity = 0.75 + 0.25 * generator.random()
            pan = 0.3 + 0.4 * ((step_index * 3) % 5) / 4
            add(harp(notes[steps[step_index % len(steps)]], velocity), bar_start + step_index * step_seconds + jitter, pan=pan)

    def add_melody(section: Section, section_start: float) -> None:
        for beat, note, length in section.melody:
            start = section_start + beat * BEAT_SECONDS
            seconds = length * BEAT_SECONDS + 0.3

            add(flute(note, seconds, generator) * section.melody_gain, start, pan=0.55)

            if section.has_bells:
                add(chime(note + 12, 0.7), start + 0.5 * BEAT_SECONDS, pan=0.35 + 0.3 * generator.random())

    def add_drum(section_start: float) -> None:
        for beat_index in range(0, 8 * BEATS_PER_BAR, 2):
            add(frame_drum(1.0 if beat_index % 4 == 0 else 0.55), section_start + beat_index * BEAT_SECONDS, pan=0.5)

    def add_outro_chimes(section_start: float) -> None:
        for bar_index, note in enumerate([83, 81, 79, 78, 79, 83, 81, 78]):
            add(chime(note, 0.8), section_start + (bar_index * 4 + 1.5) * BEAT_SECONDS, pan=0.3 + 0.4 * (bar_index % 2))

    for section_index, section in enumerate(SECTIONS):
        section_start = section_index * 8 * BAR_SECONDS

        for bar_index, chord_name in enumerate(section.chords):
            add_chord_layers(chord_name, section_start + bar_index * BAR_SECONDS, section)

        add_melody(section, section_start)

        if section.has_drum:
            add_drum(section_start)

        if not section.melody and section.has_bells:
            add_outro_chimes(section_start)

    return mix_master(np.stack([warm_reverb(channel, seed) for seed, channel in enumerate(channels, start=1)]))


def write_wav(path: Path, samples: np.ndarray) -> None:
    pcm = (samples.T * 32767).astype(np.int16)

    with wave.open(str(path), "wb") as wav_file:
        wav_file.setnchannels(2)
        wav_file.setsampwidth(2)
        wav_file.setframerate(RATE)
        wav_file.writeframes(pcm.tobytes())


if __name__ == "__main__":
    target_path = Path(sys.argv[1]) if len(sys.argv) > 1 else OUTPUT_PATH
    wav_path = target_path.with_suffix(".wav")

    # The game ships Ogg Vorbis (a tenth of the WAV size); ffmpeg must be on PATH.
    write_wav(wav_path, compose())
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(wav_path), "-c:a", "libvorbis", "-q:a", "6", str(target_path)], check=True)
    wav_path.unlink()
    print(f"WROTE {target_path} ({LOOP_SECONDS:.1f} s)")
