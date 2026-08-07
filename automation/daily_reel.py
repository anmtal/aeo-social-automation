# -*- coding: utf-8 -*-
"""Daily just-in-time reel. Run ~15 min before the afternoon slot (Windows Task
Scheduler). Renders the NEXT reel fresh, drops a SILENT copy in the daily folder
for manual Instagram posting (you add trending audio in the evening), then
auto-posts it to YouTube with music + city hashtags.

  python automation/daily_reel.py         # render + IG folder copy + YouTube upload
  python automation/daily_reel.py --dry   # render + IG folder copy, SKIP the upload (test)

"Next" = first reel in youtube-manifest.json not yet in content/youtube-posted.json.
When all are posted it logs and stops (add more reels rather than re-upload dupes).
"""
import argparse, datetime as dt, json, os, shutil, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
REM = os.path.join(ROOT, "reels-remotion")
OUT = os.path.join(REM, "out")
MANIFEST = os.path.join(HERE, "youtube-manifest.json")
POSTED = os.path.join(ROOT, "content", "youtube-posted.json")
DAILY = os.path.join(os.path.expanduser("~"), "Downloads", "aeo-reels", "daily")
LOG = os.path.join(ROOT, "content", "daily-reel.log")
IG_TAGS = "#plasticsurgeon #plasticsurgery #NYC #BeverlyHills #Manhattan #LosAngeles #ChatGPT #AIsearch"


def log(msg):
    line = f"[{dt.datetime.now().isoformat(timespec='seconds')}] {msg}"
    print(line)
    try:
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


def load_json(p, default):
    if not os.path.exists(p):
        return default
    try:
        return json.load(open(p, encoding="utf-8"))
    except Exception as e:
        log(f"WARN: could not read {p}: {e}")
        return default


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true")
    a = ap.parse_args()

    man = load_json(MANIFEST, {"reels": []})
    reels = {r["slug"]: r for r in man.get("reels", [])}
    order = [r["slug"] for r in man.get("reels", [])]
    posted = set(load_json(POSTED, []))

    nxt = next((s for s in order if s not in posted), None)
    if not nxt:
        log("ALL reels posted — nothing left. Add more reels to reels-content.json + youtube-manifest.json, then re-run.")
        return
    log(f"next reel = {nxt}")

    node = shutil.which("node") or "node"
    log("rendering (just-in-time)...")
    r = subprocess.run([node, "render_all.mjs", nxt], cwd=REM)
    if r.returncode != 0:
        log(f"ERROR: render failed (exit {r.returncode})"); sys.exit(1)
    mp4 = os.path.join(OUT, nxt + ".mp4")
    if not os.path.exists(mp4):
        log(f"ERROR: no rendered file at {mp4}"); sys.exit(1)

    # SILENT copy for manual Instagram (add trending audio when you post in the evening)
    os.makedirs(DAILY, exist_ok=True)
    today = dt.date.today()
    base = f"{today.isoformat()} {today.strftime('%a')} - {nxt}"
    shutil.copy(mp4, os.path.join(DAILY, base + ".mp4"))
    cap = reels.get(nxt, {}).get("description", "").split("\n\n")[0]
    with open(os.path.join(DAILY, base + ".txt"), "w", encoding="utf-8") as f:
        f.write((cap + "\n\n" + IG_TAGS).strip())
    log(f"IG copy -> Downloads/aeo-reels/daily/{base}.mp4  (silent; add trending audio)")

    if a.dry:
        log("[--dry] skipped YouTube upload."); return

    log("uploading to YouTube (music + city hashtags)...")
    up = subprocess.run([sys.executable, os.path.join(HERE, "youtube_publisher.py"), "--slug", nxt])
    if up.returncode != 0:
        log(f"ERROR: YouTube upload failed (exit {up.returncode}); the IG copy is still in the daily folder."); sys.exit(1)
    log("done — posted to YouTube + IG copy ready.")


if __name__ == "__main__":
    main()
