"""Compose the epic fantasy trailer soundtrack: taiko and timpani, string ostinato, brass theme, "ah" choir, crash and reverb.

100% numpy synthesis, original theme in D minor at 137.14 BPM (4/4, one chord per bar; the 7 s cut is exactly 4 bars).
Cues match the PROMO reel of tests/promo/promo_shots.gd (77.5 s): 0 to 7 s drone, timpani roll and choir rising;
7 s the first cut brings everything in (string ostinato, taikos, brass theme); the night shot (51.5 to 57.5 s) drops the
drums for a soft choir, high bells and a falling shooting-star glissando; 57.5 s returns bigger (theme an octave up,
brass stabs, busier taikos); 70.5 s the end title gets a huge D major chord with timpani roll and crash, fading out.
Usage: python tools_src/compose_epic_music.py <output.wav> [duration_seconds]
"""

import itertools
import sys
import wave

import numpy as np

from compose_promo_music import RATE, bell, frequency, timeline

FIRST_CUT = 7.0
NIGHT_START = 51.5
NIGHT_END = 57.5
END_TITLE_START = 70.5
BEAT_SECONDS = 0.4375
STEP_SECONDS = BEAT_SECONDS / 4
BAR_SECONDS = BEAT_SECONDS * 4
STEPS_PER_BAR = 16
PHRASE_BARS = 8
MINOR, MAJOR = (0, 3, 7), (0, 4, 7)
# (fundamental MIDI no oitavo 2, tipo do acorde): Dm Bb F C Dm Bb C A
PROGRESSION = [(38, MINOR), (34, MAJOR), (41, MAJOR), (36, MAJOR), (38, MINOR), (34, MAJOR), (36, MAJOR), (33, MAJOR)]
# tema heroico original: (tempo em colcheias de semínima dentro das 8 barras, nota MIDI, duração em tempos)
THEME = [
    (0, 62, 2), (2, 65, 1), (3, 69, 1), (4, 70, 1.5), (5.5, 69, 0.5), (6, 67, 1), (7, 65, 1),
    (8, 69, 2), (10, 72, 1), (11, 69, 1), (12, 67, 1.5), (13.5, 64, 0.5), (14, 67, 2),
    (16, 74, 2), (18, 72, 1), (19, 69, 1), (20, 70, 1), (21, 74, 1), (22, 77, 2),
    (24, 76, 1.5), (25.5, 74, 0.5), (26, 72, 1), (27, 67, 1), (28, 69, 1), (29, 73, 1), (30, 76, 2),
]
OSTINATO = [0, 1, 2, 3, 2, 1, 2, 3, 0, 1, 2, 3, 2, 1, 2, 1]  # índice no acorde, uma semicolcheia por passo
TAIKO_MAIN = [(0, 1.0), (3, 0.5), (6, 0.6), (8, 0.9), (11, 0.5), (14, 0.6)]
TAIKO_CLIMAX = [(0, 1.0), (2, 0.5), (4, 0.7), (6, 0.5), (8, 1.0), (10, 0.5), (12, 0.8), (13, 0.5), (14, 0.7), (15, 0.6)]
TIMPANI_STEPS = [0, 8]
STAB_STEPS = [0, 10]
SECTIONS = [
    {"start": FIRST_CUT, "end": NIGHT_START, "taiko": TAIKO_MAIN, "theme_shifts": [0], "string_shift": 0,
     "strings": 0.55, "brass": 0.7, "choir": 0.6, "taiko_gain": 0.8, "stabs": False, "crash_bars": 8},
    {"start": NIGHT_END, "end": END_TITLE_START, "taiko": TAIKO_CLIMAX, "theme_shifts": [12, 0], "string_shift": 12,
     "strings": 0.7, "brass": 1.0, "choir": 0.8, "taiko_gain": 1.0, "stabs": True, "crash_bars": 4},
]
NIGHT_BELLS = [(0.0, 86), (1.2, 81), (2.1, 84), (3.3, 77), (4.5, 81)]  # (segundos depois de NIGHT_START, nota MIDI)
NIGHT_CHORDS = [(NIGHT_START, 38, MINOR), (NIGHT_START + 3.0, 34, MAJOR)]
FINAL_BRASS = [38, 50, 57, 62, 66, 69, 74]
FINAL_CHOIR = [50, 62, 66, 69, 74, 78]
FINAL_BELLS = [81, 86, 90, 93]
CHOIR_VOICES = [(-6, 0.0), (6, 1.7)]  # (desafinação em cents, fase do vibrato)
PEAK_LEVEL = 0.88  # -1.1 dBFS


def envelope(time: np.ndarray, seconds: float, attack: float, release: float) -> np.ndarray:
    return np.minimum(1, time / attack) * np.minimum(1, (seconds - time) / release).clip(0)


def decay(sound: np.ndarray, tau: float) -> np.ndarray:
    return sound * np.exp(-np.arange(len(sound)) / RATE / tau)


def brass_note(midi_note: int, seconds: float, attack: float = 0.15, brightness: float = 0.8) -> np.ndarray:
    time = timeline(seconds)
    base = frequency(midi_note)
    swell = np.minimum(1, time / (attack + 0.2))
    tone = np.zeros_like(time)

    for harmonic in range(1, 11):
        rolloff = np.exp(-((harmonic / (2 + 8 * brightness * swell)) ** 2))
        pair = np.sin(2 * np.pi * base * harmonic * time) + np.sin(2 * np.pi * base * harmonic * 1.004 * time + 0.7)
        tone += rolloff / harmonic ** 0.9 * pair

    return tone * envelope(time, seconds, attack, 0.2) * 0.05


def string_note(midi_note: int, seconds: float = 0.22) -> np.ndarray:
    time = timeline(seconds)
    base = frequency(midi_note)
    tone = sum(
        (np.sin(2 * np.pi * base * harmonic * time) + np.sin(2 * np.pi * base * harmonic * 1.005 * time + 0.5)) / harmonic
        for harmonic in range(1, 8)
    )

    return tone * envelope(time, seconds, 0.008, 0.05) * np.exp(-time * 8) * 0.05


def vowel_weight(hertz: float) -> float:
    """Formantes aproximados de um 'ah': picos perto de 750, 1150 e 2700 Hz."""
    return np.exp(-(((hertz - 750) / 220) ** 2)) + 0.6 * np.exp(-(((hertz - 1150) / 200) ** 2)) + 0.2 * np.exp(-(((hertz - 2700) / 450) ** 2)) + 0.04


def choir_note(midi_note: int, seconds: float, attack: float = 0.5) -> np.ndarray:
    time = timeline(seconds)
    tone = np.zeros_like(time)

    for (cents, vibrato_phase), harmonic in itertools.product(CHOIR_VOICES, range(1, 17)):
        pitch = frequency(midi_note) * 2 ** (cents / 1200)
        wobble = -pitch * harmonic * 0.004 / 5.3 * np.cos(2 * np.pi * 5.3 * time + vibrato_phase)
        tone += vowel_weight(pitch * harmonic) / harmonic ** 0.5 * np.sin(2 * np.pi * pitch * harmonic * time + wobble)

    return tone * envelope(time, seconds, attack, 0.5) * 0.02


def bass_note(midi_note: int, seconds: float, attack: float = 0.2) -> np.ndarray:
    time = timeline(seconds)
    base = frequency(midi_note)
    tone = np.sin(2 * np.pi * base * time) + 0.5 * np.sin(4 * np.pi * base * time) + 0.25 * np.sin(6 * np.pi * base * time)

    return tone * envelope(time, seconds, attack, 0.4) * 0.1


def tympani(midi_note: int, seed: int, seconds: float = 1.2) -> np.ndarray:
    time = timeline(seconds)
    base = frequency(midi_note)
    phase = 2 * np.pi * base * (time + 0.25 * (1 - np.exp(-time * 20)) / 20)
    thump = np.random.default_rng(seed).standard_normal(len(time)) * np.exp(-time * 80) * 0.15
    tone = np.sin(phase) + 0.3 * np.sin(1.504 * phase) * np.exp(-time * 9) + thump

    return tone * np.exp(-time * 3.2) * np.minimum(1, time / 0.003) * 0.3


def taiko(seed: int, seconds: float = 0.7) -> np.ndarray:
    time = timeline(seconds)
    phase = 2 * np.pi * (42 * time + 60 * (1 - np.exp(-time * 25)) / 25)
    slap = np.random.default_rng(seed).standard_normal(len(time)) * np.exp(-time * 45) * 0.25

    return (np.sin(phase) + slap) * np.exp(-time * 6) * np.minimum(1, time / 0.002) * 0.4


def crash(seed: int, seconds: float = 4.5) -> np.ndarray:
    time = timeline(seconds)
    rng = np.random.default_rng(seed)
    noise = np.diff(rng.standard_normal(len(time) + 2), n=2)
    metal = sum(np.sin(2 * np.pi * rng.uniform(3000, 9000) * time) for _ in range(8)) * 0.25
    body = 0.6 * np.exp(-time * 1.1) + 0.4 * np.exp(-time * 3.0)

    return (noise * 0.4 + metal) * body * (1 - np.exp(-time / 0.01)) * 0.06


def riser(seed: int, seconds: float) -> np.ndarray:
    time = timeline(seconds)
    noise = np.diff(np.random.default_rng(seed).standard_normal(len(time) + 1))

    return noise * (time / seconds) ** 2.2 * 0.08


def boom(seconds: float = 3.0) -> np.ndarray:
    time = timeline(seconds)
    phase = 2 * np.pi * (34 * time + 26 * (1 - np.exp(-time * 6)) / 6)

    return np.sin(phase) * np.exp(-time * 1.2) * np.minimum(1, time / 0.01) * 0.35


def falling_star(seconds: float = 1.8) -> np.ndarray:
    time = timeline(seconds)
    ratio = 700 / 5000
    phase = 2 * np.pi * 5000 * seconds / np.log(ratio) * (ratio ** (time / seconds) - 1)
    tone = np.sin(phase) + 0.5 * np.sin(2 * phase) + 0.6 * np.sin(phase * 1.004 + 0.9)

    return tone * np.exp(-time * 1.6) * np.minimum(1, time / 0.02) * np.minimum(1, (seconds - time) / 0.3).clip(0) * 0.05


def reverb(signal: np.ndarray, seed: int, wet_mix: float, dry_mix: float) -> np.ndarray:
    time = timeline(3.4)
    impulse = np.random.default_rng(seed).standard_normal(len(time)) * np.exp(-time / 0.8)
    impulse[0] = 0.0
    impulse /= np.sqrt((impulse ** 2).sum())
    size = 1 << (len(signal) + len(impulse) - 1).bit_length()
    wet = np.fft.irfft(np.fft.rfft(signal, size) * np.fft.rfft(impulse, size), size)[: len(signal)]

    return signal * dry_mix + wet * wet_mix


def bar_chord(bar_index: int, octave_shift: int) -> list[int]:
    root, intervals = PROGRESSION[bar_index % PHRASE_BARS]

    return [root + octave_shift + interval for interval in intervals]


def add_strings(add, section: dict) -> None:
    step_count = int((section["end"] - section["start"]) / STEP_SECONDS)

    for index in range(step_count):
        bar, step = divmod(index, STEPS_PER_BAR)
        tones = bar_chord(bar, 24 + section["string_shift"])
        tones.append(tones[0] + 12)
        swell = 0.8 + 0.2 * (bar % 4) / 3
        accent = 1.0 if step % 4 == 0 else 0.65
        add(string_note(tones[OSTINATO[step]]), section["start"] + index * STEP_SECONDS, 0.3 + 0.4 * (step % 2), "dry", section["strings"] * swell * accent)


def add_percussion(add, section: dict) -> None:
    start, end = section["start"], section["end"]
    bar_count = int(np.ceil((end - start) / BAR_SECONDS))

    for bar, (step, accent) in itertools.product(range(bar_count), section["taiko"]):
        time = start + bar * BAR_SECONDS + step * STEP_SECONDS
        if time < end:
            add(taiko(bar * 32 + step), time, 0.5, "dry", section["taiko_gain"] * accent)

    for bar, step in itertools.product(range(bar_count), TIMPANI_STEPS):
        time = start + bar * BAR_SECONDS + step * STEP_SECONDS
        if time < end:
            add(tympani(PROGRESSION[bar % PHRASE_BARS][0] + 12, bar * 2 + step), time, 0.5, "dry", section["taiko_gain"] * 0.8)

    for bar in range(0, bar_count, section["crash_bars"]):
        add(crash(bar), start + bar * BAR_SECONDS, 0.5, "wet", 1.0 if bar == 0 else 0.6)


def add_harmony(add, section: dict) -> None:
    start, end = section["start"], section["end"]
    bar_count = int(np.ceil((end - start) / BAR_SECONDS))

    def bar_seconds(bar: int) -> float:
        return min(BAR_SECONDS + 0.35, end - (start + bar * BAR_SECONDS) + 0.4)

    for bar in range(bar_count):
        bar_start = start + bar * BAR_SECONDS
        add(bass_note(PROGRESSION[bar % PHRASE_BARS][0], bar_seconds(bar)), bar_start, 0.5, "dry", 1.0)
        add(brass_note(PROGRESSION[bar % PHRASE_BARS][0] + 12, bar_seconds(bar)), bar_start, 0.5, "wet", section["brass"] * 0.7)

    for bar, tone_index in itertools.product(range(bar_count), range(3)):
        add(brass_note(bar_chord(bar, 12)[tone_index] + 12, bar_seconds(bar)), start + bar * BAR_SECONDS, 0.35 + 0.15 * tone_index, "wet", section["brass"] * 0.55)

    for bar, tone_index in itertools.product(range(bar_count), range(4)):
        tones = bar_chord(bar, 36) + [PROGRESSION[bar % PHRASE_BARS][0] + 48]
        add(choir_note(tones[tone_index], bar_seconds(bar), 0.35), start + bar * BAR_SECONDS, 0.2 + 0.2 * tone_index, "wet", section["choir"])

    if section["stabs"]:
        for bar, step, tone_index in itertools.product(range(bar_count), STAB_STEPS, range(3)):
            time = start + bar * BAR_SECONDS + step * STEP_SECONDS
            if time < end:
                add(brass_note(bar_chord(bar, 24)[tone_index], 0.4, 0.01, 1.0), time, 0.4 + 0.1 * tone_index, "wet", 0.7)


def add_theme(add, section: dict) -> None:
    start, end = section["start"], section["end"]
    cycles = int(np.ceil((end - start) / (PHRASE_BARS * BAR_SECONDS)))

    for cycle, (beat, midi_note, beats), shift in itertools.product(range(cycles), THEME, section["theme_shifts"]):
        time = start + (cycle * PHRASE_BARS * 4 + beat) * BEAT_SECONDS
        if time < end:
            add(brass_note(midi_note + shift, beats * BEAT_SECONDS + 0.05, 0.04, 1.0), time, 0.45, "wet", section["brass"] * (1.0 if shift else 0.8))


def add_roll(add, start: float, end: float, midi_note: int, peak: float) -> None:
    hit_count = max(8, int((end - start) * 7))
    progress = np.linspace(0, 1, hit_count)
    times = start + (end - start - 0.05) * (1 - (1 - progress) ** 1.8)

    for index, (time, level) in enumerate(zip(times, 0.12 + 0.88 * progress ** 1.5)):
        add(tympani(midi_note, 500 + index), float(time), 0.5, "dry", peak * level)


def add_intro(add) -> None:
    for midi_note, level in [(38, 1.0), (45, 0.6), (50, 0.5)]:
        add(bass_note(midi_note, FIRST_CUT + 1.0, 5.0), 0.0, 0.5, "wet", level)

    for tone_index, midi_note in enumerate(bar_chord(0, 36) + [62 + 12]):
        add(choir_note(midi_note, 5.0, 3.0), 2.5, 0.2 + 0.2 * tone_index, "wet", 0.7)

    add_roll(add, 1.0, FIRST_CUT, 50, 0.5)
    add(riser(1, 3.0), FIRST_CUT - 3.0, 0.5, "wet", 0.35)
    add(boom(), FIRST_CUT, 0.5, "dry", 1.0)
    add(taiko(900, 1.0), FIRST_CUT, 0.5, "dry", 1.6)


def add_night(add) -> None:
    for start, root, intervals in NIGHT_CHORDS:
        add(bass_note(root, 4.0, 1.5), start, 0.5, "wet", 0.5)

        for tone_index, interval in enumerate(intervals):
            add(choir_note(root + 36 + interval, 4.0, 1.4), start, 0.25 + 0.25 * tone_index, "wet", 0.7)

    for offset, midi_note in NIGHT_BELLS:
        add(bell(midi_note, 3.5) * 0.8, NIGHT_START + offset, 0.2 + 0.6 * (offset % 2 / 1.5), "wet", 1.0)

    add(falling_star(), NIGHT_START + 2.6, 0.75, "wet", 1.0)
    add(riser(2, 2.0), NIGHT_END - 2.0, 0.5, "wet", 0.7)
    add_roll(add, NIGHT_END - 1.0, NIGHT_END, 50, 0.5)
    add(boom(), NIGHT_END, 0.5, "dry", 1.0)
    add(taiko(901, 1.0), NIGHT_END, 0.5, "dry", 1.4)


def add_final(add, duration: float) -> None:
    seconds = duration - END_TITLE_START
    add_roll(add, END_TITLE_START - 1.8, END_TITLE_START, 50, 1.0)
    add(riser(3, 2.0), END_TITLE_START - 2.0, 0.5, "wet", 1.0)
    add(crash(77, 6.0), END_TITLE_START, 0.5, "wet", 1.6)
    add(boom(4.0), END_TITLE_START, 0.5, "dry", 1.4)
    add(taiko(902, 1.0), END_TITLE_START, 0.5, "dry", 1.8)
    add(tympani(38, 903, 3.0), END_TITLE_START, 0.5, "dry", 2.0)
    add(decay(bass_note(26, seconds, 0.05), 5.0), END_TITLE_START, 0.5, "dry", 1.6)

    for tone_index, midi_note in enumerate(FINAL_BRASS):
        add(decay(brass_note(midi_note, seconds, 0.06, 1.0), 4.5), END_TITLE_START, 0.2 + 0.1 * tone_index, "wet", 0.9)

    for tone_index, midi_note in enumerate(FINAL_CHOIR):
        add(decay(choir_note(midi_note, seconds, 0.7), 5.0), END_TITLE_START, 0.15 + 0.14 * tone_index, "wet", 1.0)

    for index, midi_note in enumerate(FINAL_BELLS):
        add(bell(midi_note, 4.0), END_TITLE_START + 0.4 + index * 0.18, 0.3 + 0.13 * index, "wet", 1.0)


def compose(duration: float) -> np.ndarray:
    total = int(duration * RATE)
    stems = {"dry": np.zeros((2, total)), "wet": np.zeros((2, total))}

    def add(sound: np.ndarray, start: float, pan: float, stem: str, gain: float) -> None:
        first = int(start * RATE)
        last = min(first + len(sound), total)
        if first >= total:
            return

        angle = pan * np.pi / 2
        stems[stem][0, first:last] += sound[: last - first] * np.cos(angle) * gain
        stems[stem][1, first:last] += sound[: last - first] * np.sin(angle) * gain

    add_intro(add)
    add_night(add)
    add_final(add, duration)

    for section in SECTIONS:
        add_strings(add, section)
        add_percussion(add, section)
        add_harmony(add, section)
        add_theme(add, section)

    mixed = np.stack(
        [reverb(stems["dry"][side], side + 1, 0.15, 1.0) + reverb(stems["wet"][side], side + 3, 0.6, 0.6) for side in range(2)],
        axis=1,
    )
    time = timeline(duration)[:total]
    mixed *= (np.minimum(1, time / 1.5) * np.minimum(1, (duration - time) / 3.5).clip(0))[:, None]
    reference = np.percentile(np.abs(mixed), 99.5)
    limited = np.tanh(mixed / reference * 1.2)

    return limited / np.abs(limited).max() * PEAK_LEVEL


if __name__ == "__main__":
    output_path = sys.argv[1]
    duration_seconds = float(sys.argv[2]) if len(sys.argv) > 2 else 77.5
    pcm = (compose(duration_seconds) * 32767).astype(np.int16)

    with wave.open(output_path, "wb") as wav_file:
        wav_file.setnchannels(2)
        wav_file.setsampwidth(2)
        wav_file.setframerate(RATE)
        wav_file.writeframes(pcm.tobytes())

    print(f"WROTE {output_path} ({duration_seconds:.1f} s)")
