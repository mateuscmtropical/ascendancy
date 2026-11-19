"""Compose the soundtrack of the one-take night promo: town at dusk, cathedral, crypt, climb back out, swirl sky.

Same gentle ambient family as the earlier promo track (soft pad, bells, light pulse), but a new piece:
C minor opening that resolves to E-flat major under the night sky, plucked harp and music box instead of the bell
arpeggio, a low drone with a slow heart pulse in the crypt and a high shimmer that follows the star twinkle.
Section times live in CUES so the score can be refitted to the final camera route.
Usage: python tools_src/compose_night_take_music.py <output.wav> [duration_seconds]
"""

import sys
import wave

import numpy as np

RATE = 48000
CUES = {"town": 0.0, "cathedral": 12.6, "crypt": 27.6, "climb": 52.2, "sky": 73.2, "title": 82.0}  # pernas de tests/promo/night_take_route.gd
DEFAULT_SECONDS = 88.4
CHORD_SECONDS = 4.0
C_MINOR, A_FLAT, E_FLAT, B_FLAT = [48, 55, 60, 63], [44, 51, 56, 60], [51, 55, 58, 63], [46, 53, 58, 62]
F_MINOR, G_MAJOR, G_MINOR = [41, 48, 53, 56], [43, 50, 55, 59], [43, 50, 55, 58]
TOWN_CHORDS = [C_MINOR, A_FLAT, E_FLAT, B_FLAT]
CATHEDRAL_CHORDS = [F_MINOR, C_MINOR, A_FLAT, G_MAJOR]
CLIMB_CHORDS = [A_FLAT, B_FLAT, C_MINOR, B_FLAT]
SKY_CHORDS = [E_FLAT, A_FLAT, E_FLAT, B_FLAT]
HARP_PATTERN = [0, 1, 2, 3, 2, 1]
MUSIC_BOX_MELODY = [(0.0, 79), (0.75, 75), (1.5, 72), (2.5, 74), (3.0, 75), (4.0, 79), (4.75, 82), (5.5, 80), (6.5, 79)]
CRYPT_BELLS = [(2.0, 67), (7.5, 63), (13.0, 70), (18.5, 62)]  # (segundos depois da entrada na cripta, nota MIDI)
HEART_SECONDS = 1.6


def frequency(midi_note: float) -> float:
    return 440.0 * 2 ** ((midi_note - 69) / 12)


def timeline(seconds: float) -> np.ndarray:
    return np.arange(int(seconds * RATE)) / RATE


def add_at(track: np.ndarray, sound: np.ndarray, start_seconds: float) -> None:
    start = int(start_seconds * RATE)
    end = min(track.size, start + sound.size)

    if start >= track.size:
        return

    track[start:end] += sound[: end - start]


def pad_note(midi_note: int, seconds: float, brightness: float = 1.6) -> np.ndarray:
    time = timeline(seconds)
    base = frequency(midi_note)
    harmonics = sum((1 / harmonic**brightness) * np.sin(2 * np.pi * base * harmonic * time + harmonic) for harmonic in range(1, 6))
    detuned = np.sin(2 * np.pi * base * 1.004 * time + 0.7)
    envelope = np.minimum(1, time / 1.8) * np.minimum(1, (seconds - time) / 2.0).clip(0)

    return (harmonics + 0.5 * detuned) * envelope * 0.045


def harp_pluck(midi_note: int, seconds: float = 1.8) -> np.ndarray:
    time = timeline(seconds)
    base = frequency(midi_note)
    tone = np.sin(2 * np.pi * base * time) + 0.4 * np.sin(4 * np.pi * base * time) * np.exp(-time * 6)
    envelope = np.exp(-time * 2.6) * np.minimum(1, time / 0.004)

    return tone * envelope * 0.07


def music_box(midi_note: int, seconds: float = 1.4) -> np.ndarray:
    time = timeline(seconds)
    base = frequency(midi_note)
    tone = np.sin(2 * np.pi * base * time) + 0.25 * np.sin(2 * np.pi * base * 4.2 * time) * np.exp(-time * 9)

    return tone * np.exp(-time * 3.5) * 0.06


def low_drone(seconds: float) -> np.ndarray:
    time = timeline(seconds)
    root = frequency(36)
    tone = np.sin(2 * np.pi * root * time) + 0.6 * np.sin(2 * np.pi * root * 1.5 * time) + 0.3 * np.sin(2 * np.pi * root * 2.002 * time)
    breathing = 0.75 + 0.25 * np.sin(2 * np.pi * time / 9.0)
    envelope = np.minimum(1, time / 3.0) * np.minimum(1, (seconds - time) / 3.0).clip(0)

    return tone * breathing * envelope * 0.05


def heart_pulse(seconds: float = 0.5) -> np.ndarray:
    time = timeline(seconds)
    thump = np.sin(2 * np.pi * 52 * time * (1 - time)) * np.exp(-time * 14)

    return thump * 0.22


def shimmer(seconds: float) -> np.ndarray:
    time = timeline(seconds)
    voices = sum(np.sin(2 * np.pi * frequency(note) * time) * (0.5 + 0.5 * np.sin(2 * np.pi * rate * time + note)) for note, rate in ((87, 0.31), (91, 0.47), (94, 0.23), (98, 0.39)))
    envelope = np.minimum(1, time / 4.0) * np.minimum(1, (seconds - time) / 3.0).clip(0)

    return voices * envelope * 0.012


def chord_bed(track: np.ndarray, chords: list, start: float, end: float, brightness: float = 1.6) -> None:
    chord_count = int(np.ceil((end - start) / CHORD_SECONDS))

    for index in range(chord_count):
        chord = chords[index % len(chords)]
        chord_start = start + index * CHORD_SECONDS
        notes = sum(pad_note(note, CHORD_SECONDS + 1.5, brightness) for note in chord)

        add_at(track, notes, chord_start)


def harp_line(track: np.ndarray, chords: list, start: float, end: float, step: float) -> None:
    step_count = int((end - start) / step)

    for index in range(step_count):
        chord = chords[int(index * step / CHORD_SECONDS) % len(chords)]
        note = chord[HARP_PATTERN[index % len(HARP_PATTERN)]] + 12

        add_at(track, harp_pluck(note), start + index * step)


def compose(seconds: float) -> np.ndarray:
    track = np.zeros(int(seconds * RATE))

    chord_bed(track, TOWN_CHORDS, CUES["town"], CUES["cathedral"])
    harp_line(track, TOWN_CHORDS, CUES["town"] + 4.0, CUES["cathedral"], 0.5)

    chord_bed(track, CATHEDRAL_CHORDS, CUES["cathedral"], CUES["crypt"], brightness=1.2)

    for offset, note in MUSIC_BOX_MELODY:
        add_at(track, music_box(note), CUES["cathedral"] + 2.0 + offset)

    add_at(track, low_drone(CUES["climb"] - CUES["crypt"] + 2.0), CUES["crypt"])

    for beat_index in range(int((CUES["climb"] - CUES["crypt"]) / HEART_SECONDS)):
        add_at(track, heart_pulse(), CUES["crypt"] + 4.0 + beat_index * HEART_SECONDS)

    for offset, note in CRYPT_BELLS:
        add_at(track, harp_pluck(note, 3.0) * 1.2, CUES["crypt"] + offset)

    chord_bed(track, CLIMB_CHORDS, CUES["climb"], CUES["sky"])
    harp_line(track, CLIMB_CHORDS, CUES["climb"], CUES["sky"], 0.25)

    chord_bed(track, SKY_CHORDS, CUES["sky"], CUES["title"], brightness=1.3)
    add_at(track, shimmer(seconds - CUES["sky"]), CUES["sky"])

    for offset, note in MUSIC_BOX_MELODY:
        add_at(track, music_box(note + 3) * 0.8, CUES["sky"] + 2.0 + offset)

    add_at(track, sum(pad_note(note, seconds - CUES["title"]) for note in E_FLAT + [70]), CUES["title"])

    return track


def reverb(track: np.ndarray) -> np.ndarray:
    wet = track.copy()

    for delay_seconds, gain in ((0.031, 0.5), (0.047, 0.42), (0.071, 0.35), (0.113, 0.27), (0.173, 0.2), (0.257, 0.14)):
        shift = int(delay_seconds * RATE)

        wet[shift:] += track[:-shift] * gain

    return wet


def write_stereo(path: str, track: np.ndarray) -> None:
    left = track
    right = np.roll(track, int(0.011 * RATE))
    peak = max(np.abs(left).max(), np.abs(right).max(), 1e-9)
    samples = (np.stack([left, right], axis=1) / peak * 0.85 * 32767).astype(np.int16)

    with wave.open(path, "wb") as output:
        output.setnchannels(2)
        output.setsampwidth(2)
        output.setframerate(RATE)
        output.writeframes(samples.tobytes())


def main() -> None:
    output_path = sys.argv[1]
    seconds = float(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_SECONDS
    track = reverb(compose(seconds))

    write_stereo(output_path, track)
    print(f"MUSIC {output_path} {seconds:.1f}s")


if __name__ == "__main__":
    main()
