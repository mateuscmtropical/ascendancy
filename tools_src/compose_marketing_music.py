"""Score and sound design of the marketing trailer, timed by tools_src/marketing_timeline.py.

Same voice as the promo reel (compose_promo_music.py: warm pad, bell arpeggios, soft kick and hats) carried by a
trailer arc: wind, a tolling bell and hooves in the cold open, a braam and a boom on the fire, the city theme with
a drop at the montage, a riser and a turn to minor at dusk, a heartbeat under the night, taiko drums and a fast
bell ostinato in the fight, silence, then the theme in full under the title. Everything is synthesized.

Usage: python tools_src/compose_marketing_music.py <output.wav>
"""

import sys
import wave
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

from compose_promo_music import RATE, bass, bell, frequency, hat, kick, pad_note, reverb, timeline  # noqa: E402
from marketing_timeline import ACT_CITY, ACT_DUSK, ACT_FIGHT, ACT_NIGHT, ACT_TITLE, BEAT, CUES, DROP, DURATION, FINAL_BOOM  # noqa: E402

D_MAJOR, F_SHARP_MINOR, G_MAJOR, A_MAJOR, B_MINOR = [50, 54, 57, 62], [42, 49, 54, 57], [43, 50, 55, 59], [45, 52, 57, 61], [47, 50, 54, 59]
E_MINOR, D_MINOR, B_FLAT, C_MAJOR = [40, 47, 52, 55], [50, 53, 57, 62], [46, 50, 53, 58], [48, 52, 55, 60]
CITY_CHORDS = [D_MAJOR, B_MINOR, G_MAJOR, A_MAJOR]
DUSK_CHORDS = [B_MINOR, G_MAJOR, E_MINOR, F_SHARP_MINOR]
FIGHT_CHORDS = [D_MINOR, B_FLAT, C_MAJOR, A_MAJOR]
TITLE_CHORDS = [D_MAJOR, G_MAJOR, B_MINOR, A_MAJOR, D_MAJOR]
CHORD_SECONDS = 2.0
ARPEGGIO = [0, 2, 1, 3, 2, 1, 3, 2]
THEME = [(0.0, 74), (1.0, 81), (1.5, 78), (2.0, 76), (3.0, 74), (4.0, 69), (4.5, 71), (5.0, 74)]  # motivo dos sinos no título


# ---------- sound design ----------

def noise(seconds: float, seed: int) -> np.ndarray:
    return np.random.default_rng(seed).standard_normal(int(seconds * RATE))


def lowpass(signal: np.ndarray, cutoff: float) -> np.ndarray:
    spectrum_size = 1 << (len(signal) - 1).bit_length()
    frequencies = np.fft.rfftfreq(spectrum_size, 1.0 / RATE)
    response = 1.0 / np.sqrt(1.0 + (frequencies / cutoff) ** 4)

    return np.fft.irfft(np.fft.rfft(signal, spectrum_size) * response, spectrum_size)[: len(signal)]


def wind(seconds: float) -> np.ndarray:
    time = timeline(seconds)
    gust = 0.6 + 0.4 * np.sin(2 * np.pi * 0.23 * time) * np.sin(2 * np.pi * 0.07 * time + 1.0)

    return lowpass(noise(seconds, 11), 420.0) * gust * np.minimum(1, time / 1.5) * np.minimum(1, (seconds - time) / 1.0).clip(0) * 0.05


def toll(midi_note: int = 38, seconds: float = 6.0) -> np.ndarray:
    """Big church bell: inharmonic partials (hum, prime, tierce, quint, nominal) with long decays."""
    time = timeline(seconds)
    base = frequency(midi_note)
    partials = ((0.5, 1.0, 0.6), (1.0, 0.8, 1.0), (1.2, 0.5, 1.6), (1.5, 0.35, 2.0), (2.0, 0.6, 2.4), (2.6, 0.2, 3.5), (3.2, 0.12, 4.5))
    tone = sum(level * np.sin(2 * np.pi * base * ratio * time) * np.exp(-time * decay / 2.0) for ratio, level, decay in partials)

    return tone * np.minimum(1, time / 0.003) * 0.16


def thud(pitch: float, seconds: float, seed: int, weight: float = 1.0) -> np.ndarray:
    time = timeline(seconds)
    body = np.sin(2 * np.pi * (pitch * time + pitch * 0.8 * (1 - np.exp(-time * 25)) / 25)) * np.exp(-time * 14)
    dirt = lowpass(noise(seconds, seed), 900.0) * np.exp(-time * 40) * 0.6

    return (body + dirt) * weight


def hooves(start: float, end: float) -> list:
    """Gallop (three falls per stride) coming closer: (sound, time) pairs."""
    events = []
    stride = 0.42
    count = int((end - start) / stride)

    for index in range(count):
        closeness = (index + 1) / count
        stride_start = start + index * stride

        for fall, offset in enumerate((0.0, 0.09, 0.2)):
            events.append((thud(70.0 + 10 * fall, 0.25, index * 3 + fall, 0.05 + 0.2 * closeness ** 2), stride_start + offset))

    return events


def braam(seconds: float = 3.2) -> np.ndarray:
    """Low distorted brass blast: stacked detuned saw-like tones on D, swelling then decaying."""
    time = timeline(seconds)
    voices = [(frequency(26), 1.0), (frequency(26) * 1.005, 0.8), (frequency(38), 0.7), (frequency(45), 0.35)]
    saw = sum(level * sum(np.sin(2 * np.pi * base * harmonic * time) / harmonic for harmonic in range(1, 14)) for base, level in voices)
    envelope = np.minimum(1, time / 0.06) * np.exp(-time * 0.9)

    return np.tanh(lowpass(saw, 900.0) * 1.6) * envelope * 0.22


def boom(seconds: float = 4.0) -> np.ndarray:
    time = timeline(seconds)
    sub = np.sin(2 * np.pi * (34 * time + 50 * (1 - np.exp(-time * 6)) / 6)) * np.exp(-time * 1.2)
    crack = lowpass(noise(seconds, 5), 2500.0) * np.exp(-time * 9) * 0.5

    return (sub + crack) * 0.42


def taiko(seed: int, weight: float = 1.0) -> np.ndarray:
    return thud(55.0, 0.9, seed + 100, 0.32 * weight)


def hit(seed: int) -> np.ndarray:
    """Short impact for a cut: a taiko with a bright noise snap."""
    time = timeline(0.5)
    snap = np.diff(noise(0.5, seed + 200), prepend=0.0) * np.exp(-time * 35) * 0.08

    return taiko(seed, 0.9)[: len(time)] + snap


def riser(seconds: float, seed: int) -> np.ndarray:
    time = timeline(seconds)
    progress = time / seconds
    sweep = np.sin(2 * np.pi * np.cumsum(200 + 1400 * progress ** 2) / RATE) * 0.3
    hiss = np.diff(noise(seconds, seed), prepend=0.0) * progress ** 2 * 0.35

    return (sweep + hiss) * progress ** 1.5 * 0.12


def whoosh(seed: int) -> np.ndarray:
    time = timeline(0.45)
    shape = np.sin(np.pi * time / 0.45) ** 2

    return lowpass(noise(0.45, seed + 300), 1800.0) * shape * 0.12


def heartbeat(start: float, end: float) -> list:
    beats = int((end - start) / 0.85)

    return [(thud(48.0, 0.35, 400 + index, 0.28 if lub else 0.18), start + index * 0.85 + (0.0 if lub else 0.22)) for index in range(beats) for lub in (True, False)]


def crackle(seconds: float, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    pops = np.zeros(int(seconds * RATE))
    positions = rng.integers(0, len(pops), int(seconds * 40))
    pops[positions] = rng.uniform(-1, 1, len(positions))
    roar = lowpass(noise(seconds, seed + 1), 300.0) * 0.4

    return (lowpass(pops, 4000.0) * 0.5 + roar) * 0.06


# ---------- music ----------

def chord_bed(chords: list, start: float, end: float, add, with_bass: bool, seed: int) -> None:
    rng = np.random.default_rng(seed)
    count = int(np.ceil((end - start) / CHORD_SECONDS))

    for index in range(count):
        chord = chords[index % len(chords)]
        chord_start = start + index * CHORD_SECONDS
        seconds = min(CHORD_SECONDS + 1.4, end - chord_start + 1.2)

        for note in chord:
            add(pad_note(note, seconds) * 1.3, chord_start, 0.3 + 0.4 * rng.random())

        if with_bass:
            add(bass(chord[0] - 12, seconds) * 1.2, chord_start, 0.5)


def arpeggio(chords: list, start: float, end: float, step: float, add, octave: int = 12, level: float = 1.0) -> None:
    count = int((end - start) / step)

    for index in range(count):
        chord = chords[int(index * step / CHORD_SECONDS) % len(chords)]
        note = chord[ARPEGGIO[index % len(ARPEGGIO)]] + octave
        add(bell(note, 1.6) * level, start + index * step, 0.3 + 0.4 * (index % 2))


def beat(start: float, end: float, add) -> None:
    for index in range(int((end - start) / BEAT)):
        moment = start + index * BEAT
        add(kick() * (1.2 if index % 2 == 0 else 0.7), moment, 0.5)
        add(hat(index) * 1.4, moment + BEAT / 2, 0.62)


def compose() -> np.ndarray:
    total = int(DURATION * RATE)
    channels = np.zeros((2, total))

    def add(sound: np.ndarray, start: float, pan: float = 0.5) -> None:
        first = int(start * RATE)
        last = min(first + len(sound), total)

        if last <= first:
            return

        channels[0, first:last] += sound[: last - first] * (1 - pan)
        channels[1, first:last] += sound[: last - first] * pan

    # abertura: vento, grave e sinos
    add(wind(ACT_CITY + 1.0), 0.0)
    add(pad_note(26, ACT_CITY - 1.0) * 1.6, 0.0)
    add(pad_note(33, ACT_CITY - 1.0) * 1.1, 0.0)

    # cidade: tema, e na queda o pulso entra
    chord_bed(CITY_CHORDS, ACT_CITY, ACT_DUSK, add, with_bass=False, seed=1)
    arpeggio(CITY_CHORDS, ACT_CITY, DROP, 0.5, add)
    arpeggio(CITY_CHORDS, DROP, ACT_DUSK, 0.25, add, level=0.8)
    beat(DROP, ACT_DUSK, add)

    for index in range(int((ACT_DUSK - DROP) / CHORD_SECONDS)):
        add(bass(CITY_CHORDS[index % 4][0] - 12, CHORD_SECONDS + 0.6) * 1.3, DROP + index * CHORD_SECONDS)

    # crepúsculo: menor, sem pulso
    chord_bed(DUSK_CHORDS, ACT_DUSK, ACT_NIGHT, add, with_bass=True, seed=3)
    arpeggio(DUSK_CHORDS, ACT_DUSK, ACT_NIGHT - 1.0, 0.5, add, level=0.6)

    # noite: grave e sinos esparsos
    add(pad_note(38, ACT_FIGHT - ACT_NIGHT + 1.0) * 1.4, ACT_NIGHT)
    add(pad_note(45, ACT_FIGHT - ACT_NIGHT + 1.0), ACT_NIGHT)

    for offset, note in ((0.6, 86), (2.4, 81), (4.0, 84)):
        add(bell(note, 3.0) * 0.7, ACT_NIGHT + offset, 0.25 + (0.2 * offset) % 0.6)

    # luta: menor, ostinato rápido de sinos e taikos
    chord_bed(FIGHT_CHORDS, ACT_FIGHT, FINAL_BOOM, add, with_bass=True, seed=4)
    arpeggio(FIGHT_CHORDS, ACT_FIGHT + 3.0, FINAL_BOOM, 0.125, add, octave=12, level=0.7)

    for index, moment in enumerate(CUES["taiko"]):
        add(taiko(index, 1.0 if index % 2 == 0 else 0.7), moment, 0.4 + 0.2 * (index % 2))

    for index in range(int((FINAL_BOOM - ACT_FIGHT - 3.0) / BEAT)):
        add(kick() * 1.3, ACT_FIGHT + 3.0 + index * BEAT)

    # título: tema inteiro com o motivo nos sinos
    chord_bed(TITLE_CHORDS, ACT_TITLE + 0.5, DURATION - 0.5, add, with_bass=True, seed=5)
    arpeggio(TITLE_CHORDS, ACT_TITLE + 2.5, DURATION - 3.0, 0.5, add, level=0.55)

    for offset, note in THEME:
        add(bell(note, 2.6) * 1.1, ACT_TITLE + 0.6 + offset, 0.5)

    # efeitos
    for moment in CUES["bell_toll"]:
        add(toll(), moment, 0.45)

    for start, end in CUES["hooves"]:
        for sound, moment in hooves(start, end):
            add(sound, moment, 0.4)

    for moment in CUES["braam"]:
        add(braam(), moment)

    for moment in CUES["boom"]:
        add(boom(), moment)

    for start, end in CUES["riser"]:
        add(riser(end - start, int(start)), start)

    for start, end in (CUES["heartbeat"],):
        for sound, moment in heartbeat(start, end):
            add(sound, moment)

    for index, moment in enumerate(CUES["hit"]):
        add(hit(index), moment)

    for index, moment in enumerate(CUES["whoosh"]):
        add(whoosh(index), moment - 0.3, 0.3 + 0.4 * (index % 2))

    for index, (start, end) in enumerate(CUES["fire"]):
        add(crackle(end - start, 50 + index), start)

    # silêncio depois da última pancada, antes do título
    silence = slice(int((FINAL_BOOM + 0.05) * RATE), int(ACT_TITLE * RATE))
    channels[:, silence] *= np.linspace(1.0, 0.25, silence.stop - silence.start)

    wet = np.stack([reverb(channels[0], 1), reverb(channels[1], 2)])
    fade = np.minimum(1.0, (DURATION - timeline(DURATION)[:total]) / 1.5)

    return wet * fade


def write(path: str, channels: np.ndarray) -> None:
    peak = np.abs(channels).max()
    scaled = np.int16((channels / peak * 0.89).T * 32767)

    with wave.open(path, "wb") as output:
        output.setnchannels(2)
        output.setsampwidth(2)
        output.setframerate(RATE)
        output.writeframes(scaled.tobytes())


if __name__ == "__main__":
    write(sys.argv[1], compose())
    print(f"WROTE {sys.argv[1]} ({DURATION} s)")
