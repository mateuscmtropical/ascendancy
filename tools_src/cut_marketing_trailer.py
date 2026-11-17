"""Cut the marketing trailer from the raw capture of tests/promo/marketing.tscn (60 fps) with ffmpeg, following
tools_src/marketing_timeline.py: per-segment trims, slow motion, punch-in zoom, shake and white flashes on hits,
colour grade per act, title cards; then the whole cut gets a 2.39:1 letterbox, vignette and film grain, the score
(compose_marketing_music.py) and a two-pass encode sized to the target.

Usage: python tools_src/cut_marketing_trailer.py <raw.avi> <score.wav> <fonts dir> <work dir> <output.mp4> [MB]
The fonts dir needs Cinzel.ttf and CinzelDecorative-Bold.ttf (SIL OFL; kept outside the repo).
"""

import re
from concurrent.futures import ThreadPoolExecutor
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from marketing_timeline import DURATION, SEGMENTS, check  # noqa: E402

SHOTS_FILE = Path(__file__).resolve().parent.parent / "tests" / "promo" / "marketing_shots.gd"
WIDTH, HEIGHT, FPS = 1920, 1080, 30
LETTERBOX = 138  # 1920 / 2.39 = 803 px de imagem
SHAKE_PIXELS = 22.0
SHAKE_MARGIN = 0.035
FLASH_SECONDS = 0.22
GRADES = {
    "day": "eq=contrast=1.08:saturation=1.2:gamma=0.97,colorbalance=rh=0.03:bh=-0.03",
    "dawn": "eq=contrast=1.06:saturation=1.15,colorbalance=rs=0.04:rh=0.06:bs=-0.03",
    "dusk": "eq=contrast=1.1:saturation=1.12,colorbalance=rm=0.05:bh=-0.05",
    "night": "eq=contrast=1.15:saturation=0.9:brightness=-0.02,colorbalance=bs=0.06:rh=0.05",
    "fire": "eq=contrast=1.2:saturation=1.15,colorbalance=rs=0.06:rh=0.08:bs=0.04",
    "title": "eq=contrast=1.1:saturation=0.75:brightness=-0.12,gblur=sigma=2.5",
}
TEXT_STYLES = {  # estilo -> (fonte, tamanho, cor, y)
    "card": ("Cinzel.ttf", 58, "F2E6D0", "(h-text_h)/2"),
    "word": ("CinzelDecorative-Bold.ttf", 170, "FFFFFF", "(h-text_h)/2"),
    "title": ("CinzelDecorative-Bold.ttf", 176, "E8C46A", "(h-text_h)/2-60"),
    "title_small": ("CinzelDecorative-Bold.ttf", 104, "F2E6D0", "(h-text_h)/2"),
    "sub": ("Cinzel.ttf", 44, "F2E6D0", "h/2+80"),
}
TEXT_FADE = 0.35


def clip_starts() -> list:
    """Start of every clip in the raw capture: the running sum of the "beats" (seconds) of marketing_shots.gd."""
    lengths = [float(value) for value in re.findall(r'"beats":\s*([0-9.]+)', SHOTS_FILE.read_text(encoding="utf-8"))]
    starts = [0.0]

    for length in lengths[:-1]:
        starts.append(starts[-1] + length)

    return starts


def fade_expression(start: float, end: float) -> str:
    return f"if(lt(t,{start}),0,if(lt(t,{start + TEXT_FADE}),(t-{start})/{TEXT_FADE},if(lt(t,{end - TEXT_FADE}),1,if(lt(t,{end}),({end}-t)/{TEXT_FADE},0))))"


def text_filters(entry: dict, work: Path, index: int) -> list:
    filters = []

    for text_index, (text, style, start, end) in enumerate(entry["texts"]):
        font, size, color, y = TEXT_STYLES[style]
        text_file = work / f"text_{index:02d}_{text_index}.txt"
        text_file.write_text(text, encoding="utf-8")
        filters.append(
            f"drawtext=fontfile=fonts/{font}:textfile={text_file.name}:fontsize={size}:fontcolor=0x{color}:x=(w-text_w)/2:y={y}"
            f":shadowcolor=black@0.55:shadowx=0:shadowy=3:alpha='{fade_expression(start, end)}'"
        )

    return filters


def motion_filters(entry: dict) -> list:
    """Punch-in zoom and decaying shake on hits, as a per-frame scale and a moving crop."""
    zoom_start, zoom_end = entry["zoom"]
    margin = SHAKE_MARGIN if entry["shake"] else 0.0
    zoom = f"({zoom_start + margin}+{zoom_end - zoom_start}*t/{entry['length']})"
    shakes = "+".join(f"gte(t,{moment})*exp(-6*(t-{moment}))" for moment in entry["shake"]) or "0"
    shake_x = f"{SHAKE_PIXELS}*sin(t*71)*({shakes})"
    shake_y = f"{SHAKE_PIXELS * 0.7}*sin(t*53+1)*({shakes})"

    return [
        f"scale=w='trunc({WIDTH}*{zoom}/2)*2':h='trunc({HEIGHT}*{zoom}/2)*2':eval=frame",
        f"crop={WIDTH}:{HEIGHT}:x='(iw-{WIDTH})/2+{shake_x}':y='(ih-{HEIGHT})/2+{shake_y}'",
    ]


def flash_filter(entry: dict) -> list:
    if not entry["flash"]:
        return []

    pulses = "+".join(f"gte(t,{moment})*max(0,1-(t-{moment})/{FLASH_SECONDS})" for moment in entry["flash"])

    return [f"eq=brightness='0.75*({pulses})':eval=frame"]


def render_segment(entry: dict, index: int, raw: Path, starts: list, work: Path) -> Path:
    output = work / f"seg_{index:02d}.mp4"
    length = entry["length"]
    filters = []

    if entry["clip"] is None:
        source = ["-f", "lavfi", "-i", f"color=black:s={WIDTH}x{HEIGHT}:r={FPS}:d={length}"]
    else:
        source_seconds = length * entry["speed"]
        source = ["-ss", f"{starts[entry['clip']] + entry['src']:.4f}", "-t", f"{source_seconds:.4f}", "-i", str(raw)]
        filters += [f"setpts=(PTS-STARTPTS)/{entry['speed']}", f"fps={FPS}", GRADES[entry["grade"]]]
        filters += motion_filters(entry) + flash_filter(entry)

    filters += text_filters(entry, work, index) + ["format=yuv420p"]
    command = ["ffmpeg", "-y", "-v", "error", *source, "-vf", ",".join(filters), "-frames:v", str(round(length * FPS)), "-r", str(FPS), "-an", "-c:v", "libx264", "-preset", "fast", "-crf", "12", output.name]
    subprocess.run(command, cwd=work, check=True)

    return output


def finish(segments: list, score: Path, work: Path, output: Path, megabytes: float) -> None:
    (work / "list.txt").write_text("".join(f"file '{segment.name}'\n" for segment in segments), encoding="utf-8")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", "list.txt", "-c", "copy", "montage.mp4"], cwd=work, check=True)

    audio_kbps = 256
    video_kbps = int(megabytes * 8 * 1024 / DURATION - audio_kbps)
    look = (
        f"vignette=angle=PI/5,noise=alls=5:allf=t,drawbox=x=0:y=0:w={WIDTH}:h={LETTERBOX}:color=black:t=fill,"
        f"drawbox=x=0:y={HEIGHT - LETTERBOX}:w={WIDTH}:h={LETTERBOX}:color=black:t=fill,fade=t=out:st={DURATION - 1.0}:d=1.0,format=yuv420p"
    )
    encode = ["-c:v", "libx264", "-preset", "slow", "-b:v", f"{video_kbps}k", "-maxrate", f"{int(video_kbps * 1.6)}k", "-bufsize", f"{video_kbps * 2}k"]
    first = ["ffmpeg", "-y", "-v", "error", "-i", "montage.mp4", "-vf", look, *encode, "-pass", "1", "-an", "-t", str(DURATION), "-f", "mp4", "NUL"]
    second = ["ffmpeg", "-y", "-v", "error", "-i", "montage.mp4", "-i", str(score), "-vf", look, *encode, "-pass", "2", "-c:a", "aac", "-b:a", f"{audio_kbps}k", "-t", str(DURATION), "-movflags", "+faststart", str(output)]

    subprocess.run(first, cwd=work, check=True)
    subprocess.run(second, cwd=work, check=True)


def main() -> None:
    raw, score, fonts, work, output = (Path(argument).resolve() for argument in sys.argv[1:6])
    megabytes = float(sys.argv[6]) if len(sys.argv) > 6 else 90.0
    starts = clip_starts()

    check()
    work.mkdir(parents=True, exist_ok=True)

    if not (work / "fonts").exists():
        shutil.copytree(fonts, work / "fonts")

    with ThreadPoolExecutor(max_workers=6) as pool:
        segments = list(pool.map(lambda pair: render_segment(pair[1], pair[0], raw, starts, work), enumerate(SEGMENTS)))
    finish(segments, score, work, output, megabytes)
    print(f"CUT {output}")


if __name__ == "__main__":
    main()
