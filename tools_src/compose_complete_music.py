"""Compose the soundtrack of the complete promo video (tests/promo/full_shots.gd, 120 BPM).

Same voice as the trailer track (ambient pad, bell arpeggio, soft kick and hat, long reverb) from
compose_promo_music.py, in A minor: Am - G - F - Dm, four seconds a chord, a 16 s loop. The bass comes
in at 16 s and the arpeggio doubles at 32 s. Cues are measured in beats of the shot list:
the night sky (bells and a falling chime), the Mula (kick drops out for a low drone and slow bells,
the gallop brings the beat back with a doubled arpeggio, a deep hit lands on the close-up) and the
final chord under the end title.
Usage: python tools_src/compose_complete_music.py <output.wav> [duration_seconds]
"""

import sys
import wave

import numpy as np

from compose_promo_music import RATE, bass, bell, hat, kick, pad_note, reverb, timeline

BEAT_SECONDS = 0.5
CHORD_SECONDS = 4.0
BASS_START = 16.0
DOUBLE_ARPEGGIO_START = 32.0
A_MINOR, G_MAJOR, F_MAJOR, D_MINOR = [57, 60, 64, 69], [55, 59, 62, 67], [53, 57, 60, 65], [50, 57, 62, 65]
PROGRESSION = [A_MINOR, G_MAJOR, F_MAJOR, D_MINOR]
ARPEGGIO_PATTERN = [0, 2, 1, 3, 2, 1, 3, 2]
SKY_BELLS = [(0.0, 86), (1.3, 81), (2.2, 85), (3.4, 78), (4.6, 83)]
FALLING_CHIME = [93, 90, 88, 86, 83, 81]
# Cues in seconds of the video: set from the beats of full_shots.gd.
SKY_START = 0.0
MULA_START = 0.0
MULA_RUN_START = 0.0
MULA_CLOSE_START = 0.0
END_TITLE_START = 0.0


def load_cues() -> None:
    """Cue times come from the shot list (the "cue" key of a shot marks where it starts)."""
    global SKY_START, MULA_START, MULA_RUN_START, MULA_CLOSE_START, END_TITLE_START
    from pathlib import Path

    source = (Path(__file__).resolve().parent.parent / "tests" / "promo" / "full_shots.gd").read_text(encoding="utf-8")
    start, starts = 0.0, {}

    for line in source.splitlines():
        if line.startswith('		"cue": '):
            starts[line.split('"')[3]] = start

        if line.startswith('		"beats": '):
            start += int(line.split(":")[1].strip(" ,")) * BEAT_SECONDS

    SKY_START = starts["sky"]
    MULA_START = starts["mula"]
    MULA_RUN_START = starts["mula_run"]
    MULA_CLOSE_START = starts["mula_close"]
    END_TITLE_START = starts["end"]


def is_mula_calm(moment: float) -> bool:
    return MULA_START <= moment < MULA_RUN_START


def drone(midi_note: int, seconds: float) -> np.ndarray:
    time = timeline(seconds)
    frequency = 440.0 * 2 ** ((midi_note - 69) / 12)
    tone = np.sin(2 * np.pi * frequency * time) + 0.5 * np.sin(2 * np.pi * frequency * 2.002 * time)

    return tone * np.minimum(1, time / 2.5) * np.minimum(1, (seconds - time) / 2.0).clip(0) * 0.16


def deep_hit(seconds: float = 3.0) -> np.ndarray:
    time = timeline(seconds)
    phase = 2 * np.pi * (34 * time + 90 * (1 - np.exp(-time * 14)) / 14)

    return np.sin(phase) * np.exp(-time * 1.6) * 0.7


def compose(duration: float) -> np.ndarray:
    total = int(duration * RATE)
    channels = np.zeros((2, total))
    rng = np.random.default_rng(11)

    def add(sound: np.ndarray, start: float, pan: float = 0.5) -> None:
        first = int(start * RATE)
        last = min(first + len(sound), total)

        if last > first:
            channels[0, first:last] += sound[: last - first] * (1 - pan)
            channels[1, first:last] += sound[: last - first] * pan

    chord_count = int(np.ceil(END_TITLE_START / CHORD_SECONDS))
    chords = [PROGRESSION[index % len(PROGRESSION)] for index in range(chord_count)] + [A_MINOR]
    beat_count = int(END_TITLE_START / BEAT_SECONDS)

    for beat_index in range(beat_count):
        beat_time = beat_index * BEAT_SECONDS

        if is_mula_calm(beat_time):
            continue

        softness = 0.55 if beat_time < BASS_START else 1.0
        add(kick() * (1.0 if beat_index % 2 == 0 else 0.6) * softness * 0.8, beat_time)
        add(hat(beat_index) * 2.0, beat_time + BEAT_SECONDS / 2, pan=0.6)

    for index, chord in enumerate(chords):
        is_final = index == chord_count
        start = END_TITLE_START if is_final else index * CHORD_SECONDS
        seconds = duration - start if is_final else CHORD_SECONDS + 1.6

        for note in chord:
            add(pad_note(note, seconds) * 1.5, start, pan=0.35 + 0.3 * rng.random())

        if is_mula_calm(start):
            add(drone(chord[0] - 24, seconds), start)

        if (start >= BASS_START and not is_mula_calm(start)) or is_final:
            add(bass(chord[0] - 24, seconds) * 0.6, start)

        if is_final:
            continue

        for step, tone_index in enumerate(ARPEGGIO_PATTERN):
            note_time = start + step * BEAT_SECONDS

            if is_mula_calm(note_time) or note_time >= END_TITLE_START:
                continue

            add(bell(chord[tone_index] + 12) * 2.4, note_time, pan=0.3 + 0.4 * (step % 2))

            if note_time >= DOUBLE_ARPEGGIO_START:
                add(bell(chord[tone_index] + 24) * 2.2, note_time + BEAT_SECONDS / 2, pan=0.7 - 0.4 * (step % 2))

    for offset, note in SKY_BELLS:
        add(bell(note, 3.5) * 0.8, SKY_START + offset, pan=0.2 + 0.6 * rng.random())

    for step, note in enumerate(FALLING_CHIME):
        add(bell(note, 1.6) * 0.5, SKY_START + 2.6 + step * 0.07, pan=0.8 - 0.1 * step)

    for step, note in enumerate([69, 72, 76, 81, 84]):
        add(bell(note, 4.0) * 0.7, MULA_START + 1.0 + step * 1.6, pan=0.25 + 0.12 * step)

    add(deep_hit(), MULA_RUN_START, pan=0.5)
    add(deep_hit(4.0) * 1.2, MULA_CLOSE_START, pan=0.5)

    for offset, note in enumerate([69, 72, 76, 81]):
        add(bell(note, 5.0), END_TITLE_START + offset * 0.18, pan=0.3 + 0.13 * offset)

    mixed = np.stack([reverb(channels[0], 1), reverb(channels[1], 2)], axis=1)
    time = timeline(duration)[:total]
    mixed *= (np.minimum(1, time / 1.5) * np.minimum(1, (duration - time) / 3.5).clip(0))[:, None]

    # Soft limiter: keeps the average level near the trailer's while the kick and hits stay under full scale.
    return np.tanh(mixed / np.abs(mixed).mean() * 0.2) * 0.9


if __name__ == "__main__":
    output_path = sys.argv[1]
    load_cues()
    duration_seconds = float(sys.argv[2]) if len(sys.argv) > 2 else END_TITLE_START + 4.0
    pcm = (compose(duration_seconds) * 32767).astype(np.int16)

    with wave.open(output_path, "wb") as wav_file:
        wav_file.setnchannels(2)
        wav_file.setsampwidth(2)
        wav_file.setframerate(RATE)
        wav_file.writeframes(pcm.tobytes())

    print(f"WROTE {output_path} ({duration_seconds:.1f} s)")
