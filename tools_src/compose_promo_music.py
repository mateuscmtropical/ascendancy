"""Compose the promo reel soundtrack: original ambient pad in D major + bell arpeggio + reverb.

Cues match tests/promo/promo_director.gd: arpeggio enters at the first cut (7.5 s), final chord under the end title (48.5 s).
Usage: python tools_src/compose_promo_music.py <output.wav> [duration_seconds]
"""

import sys
import wave

import numpy as np

RATE = 48000
ARPEGGIO_START = 7.5
END_TITLE_START = 48.5
CHORD_SECONDS = 4.0
D_MAJOR, A_MAJOR, B_MINOR, G_MAJOR = [50, 54, 57, 62], [45, 52, 57, 61], [47, 50, 54, 59], [43, 50, 55, 59]
PROGRESSION = [D_MAJOR, A_MAJOR, B_MINOR, G_MAJOR, D_MAJOR, A_MAJOR, G_MAJOR, A_MAJOR, D_MAJOR, B_MINOR, G_MAJOR, A_MAJOR]
ARPEGGIO_PATTERN = [0, 1, 2, 3, 2, 3, 1, 2]


def frequency(midi_note: float) -> float:
    return 440.0 * 2 ** ((midi_note - 69) / 12)


def timeline(seconds: float) -> np.ndarray:
    return np.arange(int(seconds * RATE)) / RATE


def pad_note(midi_note: int, seconds: float) -> np.ndarray:
    time = timeline(seconds)
    base = frequency(midi_note)
    tone = sum((1 / harmonic ** 1.6) * (np.sin(2 * np.pi * base * harmonic * time) + np.sin(2 * np.pi * base * harmonic * 1.003 * time + 1.0)) for harmonic in range(1, 7))
    envelope = np.minimum(1, time / 1.4) * np.minimum(1, (seconds - time) / 1.6).clip(0)

    return tone * envelope * 0.05


def bell(midi_note: int, seconds: float = 2.2) -> np.ndarray:
    time = timeline(seconds)
    base = frequency(midi_note)
    tone = np.sin(2 * np.pi * base * time) + 0.35 * np.sin(4 * np.pi * base * time) * np.exp(-time * 3) + 0.15 * np.sin(2 * np.pi * base * 3.01 * time) * np.exp(-time * 5)

    return tone * np.exp(-time * 2.2) * np.minimum(1, time / 0.004) * 0.09


def bass(midi_note: int, seconds: float) -> np.ndarray:
    time = timeline(seconds)
    base = frequency(midi_note)
    tone = np.sin(2 * np.pi * base * time) + 0.3 * np.sin(4 * np.pi * base * time)

    return tone * np.minimum(1, time / 0.3) * np.minimum(1, (seconds - time) / 0.8).clip(0) * 0.11


def reverb(signal: np.ndarray, seed: int) -> np.ndarray:
    time = timeline(2.6)
    impulse = np.random.default_rng(seed).standard_normal(len(time)) * np.exp(-time / 0.55)
    impulse[0] = 0.0
    impulse /= np.sqrt((impulse ** 2).sum())
    size = 1 << (len(signal) + len(impulse) - 1).bit_length()
    wet = np.fft.irfft(np.fft.rfft(signal, size) * np.fft.rfft(impulse, size), size)[: len(signal)]

    return signal * 0.75 + wet * 0.45


def compose(duration: float) -> np.ndarray:
    total = int(duration * RATE)
    channels = np.zeros((2, total))
    rng = np.random.default_rng(7)

    def add(sound: np.ndarray, start: float, pan: float = 0.5) -> None:
        first = int(start * RATE)
        last = min(first + len(sound), total)
        channels[0, first:last] += sound[: last - first] * (1 - pan)
        channels[1, first:last] += sound[: last - first] * pan

    chords = PROGRESSION + [D_MAJOR]

    for index, chord in enumerate(chords):
        start = index * CHORD_SECONDS
        is_final = index == len(PROGRESSION)
        seconds = duration - start if is_final else CHORD_SECONDS + 1.6

        for note in chord:
            add(pad_note(note, seconds), start, pan=0.35 + 0.3 * rng.random())

        if start >= ARPEGGIO_START or is_final:
            add(bass(chord[0] - 12, seconds), start)

        if is_final:
            continue

        for step, tone_index in enumerate(ARPEGGIO_PATTERN):
            note_time = start + step * 0.5

            if note_time >= ARPEGGIO_START:
                add(bell(chord[tone_index] + 12), note_time, pan=0.3 + 0.4 * (step % 2))

    for offset, note in enumerate([74, 78, 81, 86]):
        add(bell(note, 4.0), END_TITLE_START + offset * 0.18, pan=0.3 + 0.13 * offset)

    mixed = np.stack([reverb(channels[0], 1), reverb(channels[1], 2)], axis=1)
    time = timeline(duration)[:total]
    mixed *= (np.minimum(1, time / 2.0) * np.minimum(1, (duration - time) / 3.5).clip(0))[:, None]

    return mixed / (np.abs(mixed).max() / 0.8)


if __name__ == "__main__":
    output_path = sys.argv[1]
    duration_seconds = float(sys.argv[2]) if len(sys.argv) > 2 else 56.0
    pcm = (compose(duration_seconds) * 32767).astype(np.int16)

    with wave.open(output_path, "wb") as wav_file:
        wav_file.setnchannels(2)
        wav_file.setsampwidth(2)
        wav_file.setframerate(RATE)
        wav_file.writeframes(pcm.tobytes())

    print(f"WROTE {output_path} ({duration_seconds:.1f} s)")
