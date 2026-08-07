# -*- coding: utf-8 -*-
"""CI daily YouTube poster (GitHub Actions, laptop-free).

Picks the next unposted reel from committed content/reels-mp4, uploads it via
youtube_publisher (ambient music + city hashtags), then stages content/ig-today.*
for the founder to download for the evening Instagram post. Credentials come from
GitHub-secret env vars (no local .env). Set YT_DRY=true to validate without posting.
"""
import datetime as dt, json, os, shutil, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
MANIFEST = os.path.join(HERE, "youtube-manifest.json")
POSTED = os.path.join(ROOT, "content", "youtube-posted.json")
REELS = os.environ.get("REELS_DIR") or os.path.join(ROOT, "content", "reels-mp4")
PUB = os.path.join(HERE, "youtube_publisher.py")
IG_TAGS = "#plasticsurgeon #plasticsurgery #NYC #BeverlyHills #Manhattan #LosAngeles #ChatGPT #AIsearch"
DRY = os.environ.get("YT_DRY", "").lower() == "true"


def main():
    today = dt.date.today().isoformat()
    # Idempotency: GitHub cron AND cron-job.org both trigger this workflow. The
    # concurrency group serializes them; this guard makes the 2nd a no-op so only
    # ONE reel posts per calendar day.
    igj = os.path.join(ROOT, "content", "ig-today.json")
    if not DRY and os.path.exists(igj):
        try:
            if (json.load(open(igj, encoding="utf-8")) or {}).get("date") == today:
                print(f"already posted today ({today}); skipping to avoid a double post.")
                return
        except Exception:
            pass

    man = json.load(open(MANIFEST, encoding="utf-8"))
    reels = {r["slug"]: r for r in man["reels"]}
    order = [r["slug"] for r in man["reels"]]
    posted = set(json.load(open(POSTED, encoding="utf-8"))) if os.path.exists(POSTED) else set()

    nxt = next((s for s in order if s not in posted), None)
    if not nxt:
        print("ALL reels posted — add more to content/reels-mp4 + youtube-manifest.json.")
        return
    print(("[DRY] " if DRY else "") + "next reel: " + nxt)

    if DRY:
        if subprocess.run([sys.executable, PUB, "--check"]).returncode != 0:
            sys.exit("auth check failed")
        mp4 = os.path.join(REELS, nxt + ".mp4")
        music = os.environ.get("YOUTUBE_MUSIC", "")
        print("reel present :", os.path.exists(mp4), mp4)
        print("music present:", os.path.exists(music), music)
        if not os.path.exists(mp4):
            sys.exit("reel file missing")
        print("[DRY] validated (auth OK, reel + music present). Nothing posted.")
        return

    if subprocess.run([sys.executable, PUB, "--slug", nxt]).returncode != 0:
        sys.exit("youtube upload failed")

    # stage today's SILENT reel for manual Instagram (add trending audio in the app)
    shutil.copy(os.path.join(REELS, nxt + ".mp4"), os.path.join(ROOT, "content", "ig-today.mp4"))
    cap = reels[nxt].get("description", "").split("\n\n")[0]
    with open(os.path.join(ROOT, "content", "ig-today.txt"), "w", encoding="utf-8") as f:
        f.write((cap + "\n\n" + IG_TAGS).strip())
    with open(os.path.join(ROOT, "content", "ig-today.json"), "w", encoding="utf-8") as f:
        json.dump({"date": dt.date.today().isoformat(), "slug": nxt}, f, indent=2)
    print("posted to YouTube + staged content/ig-today.mp4 for Instagram.")


if __name__ == "__main__":
    main()
