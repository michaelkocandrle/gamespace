"""Reference video from YouTube -> frames to look at (21. 9. 2026).

    python Tools/Reference/fetch_video.py <url> <name> [--every 2] [--from 0:30 --to 5:00]

1. Downloads the best video stream up to 2160p (plus audio, merged to mp4) with yt-dlp into
   ArtSource/Reference/Video/<name>/ and prints the resolution that actually came down (ffprobe),
   because YouTube serves low resolutions to some clients without saying so.
2. Cuts one frame every --every seconds (full resolution, JPEG quality 2) into frames/.
3. Tiles them into contact sheets (4x3, 640 px per frame) in sheets/, so a whole video can be
   scanned in a few pictures and the interesting timestamps opened at full size.

The video and the frames are someone else's footage: kept locally for reference only, never
committed (ArtSource/Reference/Video/ is in .gitignore). Needs yt-dlp (pip install yt-dlp) and
ffmpeg/ffprobe on PATH. Re-running skips the download when the file is already there.
"""

import argparse
import glob
import json
import os
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ROOT = os.path.join(REPO, "ArtSource", "Reference", "Video")


def run(cmd):
    print(">", " ".join(cmd))
    subprocess.run(cmd, check=True)


def probe(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                          "stream=width,height,r_frame_rate,codec_name:format=duration", "-of", "json", path],
                         check=True, capture_output=True, text=True).stdout
    data = json.loads(out)
    stream = data["streams"][0]
    num, den = stream["r_frame_rate"].split("/")
    return stream["width"], stream["height"], float(num) / float(den), stream["codec_name"], float(data["format"]["duration"])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("url")
    parser.add_argument("name", help="folder name, e.g. sc_quantum_travel")
    parser.add_argument("--every", type=float, default=2.0, help="seconds between frames")
    parser.add_argument("--from", dest="start", default=None, help="start time for frames, e.g. 0:30")
    parser.add_argument("--to", dest="end", default=None, help="end time for frames, e.g. 5:00")
    args = parser.parse_args()

    folder = os.path.join(ROOT, args.name)
    os.makedirs(folder, exist_ok=True)
    video = os.path.join(folder, "video.mp4")
    if not os.path.exists(video):
        run([sys.executable, "-m", "yt_dlp", "-f", "bv*[height<=2160]+ba/b[height<=2160]/bv*+ba/b",
             "--merge-output-format", "mp4", "-o", video, "--no-playlist", args.url])
    width, height, fps, codec, duration = probe(video)
    print("DOWNLOADED %dx%d, %.2f fps, %s, %.0f s, %.0f MB" % (
        width, height, fps, codec, duration, os.path.getsize(video) / 1e6))

    frames = os.path.join(folder, "frames")
    os.makedirs(frames, exist_ok=True)
    for old in glob.glob(os.path.join(frames, "*.jpg")):
        os.remove(old)
    cut = ["ffmpeg", "-v", "error", "-y"]
    if args.start:
        cut += ["-ss", args.start]
    if args.end:
        cut += ["-to", args.end]
    offset = 0.0
    if args.start:
        parts = [float(p) for p in args.start.split(":")]
        offset = sum(p * 60 ** i for i, p in enumerate(reversed(parts)))
    run(cut + ["-i", video, "-vf", "fps=1/%g" % args.every, "-q:v", "2", os.path.join(frames, "f_%05d.jpg")])

    # Name each frame by its time in the video, so a sheet points straight at the file.
    for index, path in enumerate(sorted(glob.glob(os.path.join(frames, "f_*.jpg")))):
        seconds = int(offset + index * args.every)
        os.replace(path, os.path.join(frames, "t%02d_%02d_%02d.jpg" % (seconds // 3600, seconds % 3600 // 60, seconds % 60)))

    # Contact sheets, 4x3 frames each, labelled with the time. With PIL: ffmpeg's drawtext crashes on
    # Windows without a font configured (21. 9. 2026).
    from PIL import Image, ImageDraw, ImageFont
    sheets = os.path.join(folder, "sheets")
    os.makedirs(sheets, exist_ok=True)
    for old in glob.glob(os.path.join(sheets, "*.jpg")):
        os.remove(old)
    names = sorted(glob.glob(os.path.join(frames, "t*.jpg")))
    cell_w, cell_h = 640, int(640 * height / width)
    try:
        font = ImageFont.truetype("arial.ttf", 26)
    except OSError:
        font = ImageFont.load_default()
    for sheet_index in range(0, len(names), 12):
        sheet = Image.new("RGB", (cell_w * 4, cell_h * 3))
        for slot, path in enumerate(names[sheet_index:sheet_index + 12]):
            image = Image.open(path).convert("RGB").resize((cell_w, cell_h))
            stamp = os.path.basename(path)[1:-4].replace("_", ":")
            draw = ImageDraw.Draw(image)
            draw.rectangle((0, 0, 130, 36), fill=(0, 0, 0))
            draw.text((8, 4), stamp, fill=(255, 220, 0), font=font)
            sheet.paste(image, ((slot % 4) * cell_w, (slot // 4) * cell_h))
        sheet.save(os.path.join(sheets, "sheet_%03d.jpg" % (sheet_index // 12 + 1)), quality=88)
    count = len(glob.glob(os.path.join(frames, "*.jpg")))
    print("FRAMES %d in %s" % (count, frames))
    print("SHEETS %d in %s" % (len(glob.glob(os.path.join(sheets, "*.jpg"))), sheets))


if __name__ == "__main__":
    main()
