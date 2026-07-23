# -*- coding: utf-8 -*-
"""Turn a carousel's slides into an animated 9:16 Instagram Reel (silent).

Pads each 1080x1350 slide onto a 1080x1920 near-black canvas, then ffmpeg
crossfades them into an MP4 (H.264, yuv420p, 30fps). Silent by design — the
founder adds trending audio in-app when posting (best reach).

Run:  python tools/reel_maker.py <slug>
      python tools/reel_maker.py <slug> --frames-only   # just write padded frames (no ffmpeg)
"""
import os, sys, glob, subprocess, tempfile, shutil
from PIL import Image

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BG = (10, 14, 21)            # #0A0E15
RW, RH = 1080, 1920          # 9:16
DUR = 2.6                    # seconds per slide
XF = 0.5                     # crossfade seconds

def pad_9x16(src, dst):
    im = Image.open(src).convert("RGB")
    canvas = Image.new("RGB", (RW, RH), BG)
    # fit width to 1080, center vertically
    w, h = im.size
    if w != RW:
        im = im.resize((RW, int(h * RW / w)), Image.LANCZOS)
    canvas.paste(im, (0, (RH - im.height) // 2))
    canvas.save(dst, "JPEG", quality=92)

def build(slug, frames_only=False):
    posts = os.path.join(HERE, "content", "posts", slug)
    slides = sorted(glob.glob(os.path.join(posts, "slide-*.jpg")))
    if not slides:
        sys.exit(f"no slides for {slug}")
    tmp = os.path.join(HERE, "content", "reels", "_frames", slug)
    if os.path.exists(tmp): shutil.rmtree(tmp)
    os.makedirs(tmp, exist_ok=True)
    frames = []
    for i, s in enumerate(slides, 1):
        f = os.path.join(tmp, f"f{i:02d}.jpg"); pad_9x16(s, f); frames.append(f)
    print(f"padded {len(frames)} frames -> {tmp}")
    if frames_only:
        return
    if not shutil.which("ffmpeg"):
        sys.exit("ffmpeg not found (expected in CI). Use --frames-only locally.")
    # build the xfade chain: offset_j = j*(DUR-XF)
    n = len(frames)
    inputs = []
    for f in frames:
        inputs += ["-loop", "1", "-t", str(DUR), "-i", f]
    # normalize every input (fps/format/SAR) so xfade never rejects a mismatch
    pre = [f"[{i}:v]fps=30,format=yuv420p,setsar=1[s{i}]" for i in range(n)]
    if n == 1:
        fc = "[0:v]fps=30,format=yuv420p,setsar=1[v]"
    else:
        chain, last = [], "[s0]"
        for j in range(1, n):
            off = round(j * (DUR - XF), 3)
            out = f"[vx{j}]" if j < n - 1 else "[v]"
            chain.append(f"{last}[s{j}]xfade=transition=fade:duration={XF}:offset={off}{out}")
            last = f"[vx{j}]"
        fc = ";".join(pre + chain)
    outdir = os.path.join(HERE, "content", "reels"); os.makedirs(outdir, exist_ok=True)
    out = os.path.join(outdir, f"{slug}.mp4")
    cmd = ["ffmpeg", "-y", *inputs, "-filter_complex", fc, "-map", "[v]", "-an",
           "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "30", "-movflags", "+faststart", out]
    print("running ffmpeg...")
    subprocess.run(cmd, check=True)
    shutil.rmtree(tmp, ignore_errors=True)
    print("wrote", out)

if __name__ == "__main__":
    if len(sys.argv) < 2: sys.exit("usage: reel_maker.py <slug> [--frames-only]")
    build(sys.argv[1], "--frames-only" in sys.argv)
