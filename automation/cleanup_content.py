"""Delete already-posted reel videos from the repo to keep it lean.

Once a reel is published, Instagram serves its own copy, so the GitHub-hosted
mp4 (~10MB) is no longer needed. Runs every 2 days.

SAFETY: a video is deleted ONLY if its slug is in content/posted.json (i.e. we
actually published it) AND its scheduled time is past the buffer. Never key this
on publish_at age alone — a post that was skipped/delayed/rescheduled is still
unposted, and deleting its video would make it permanently unpostable and jam
the queue behind it.

Only touches reel videos in content/reels/. Leaves carousel images, specs,
and unscheduled content alone. Files are always re-creatable from the specs.
"""
import datetime as dt
import json
import os

try:
    from zoneinfo import ZoneInfo
except ImportError:
    ZoneInfo = None

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
BUFFER_DAYS = 3   # keep published videos this many days, so you can still grab one to re-post by hand

with open(os.path.join(HERE, "posts-manifest.json"), encoding="utf-8") as f:
    m = json.load(f)

# the permanent record of what actually published — the ONLY safe basis for deletion
try:
    with open(os.path.join(ROOT, "content", "posted.json"), encoding="utf-8") as f:
        POSTED = set(json.load(f))
except Exception:
    POSTED = set()
    print("WARNING: could not read posted.json — refusing to delete anything.")

tz = None
if ZoneInfo is not None:
    try:
        tz = ZoneInfo(m.get("timezone", "UTC"))
    except Exception:
        tz = None
now = dt.datetime.now(tz) if tz else dt.datetime.now(dt.timezone.utc)
cutoff = now - dt.timedelta(days=BUFFER_DAYS)

# Reels live in automation/reel-manifest.json, not in posts-manifest.json. This script
# used to iterate posts-manifest and filter on type == "reel"; every entry there is a
# carousel, so the job ran every 2 days and could never delete anything while the videos
# accumulated in the repo. Read the reel manifest, and fall back to the posts manifest
# for any legacy type=="reel" rows.
_reels = []
_rm = os.path.join(ROOT, "automation", "reel-manifest.json")
if os.path.exists(_rm):
    try:
        _reels = json.load(open(_rm, encoding="utf-8")).get("reels", [])
    except Exception:
        _reels = []
_reels += [p for p in m["posts"] if p.get("type") == "reel"]

# content/reels-mp4/ is deliberately committed for the YouTube CI poster and is never
# touched here; only the render output in content/reels/ is cleaned up.
removed = []
kept_unposted = []
_seen = set()
for post in _reels:
    _k = f'{post["slug"]}@{post.get("publish_at","")[:10]}'
    if _k in _seen:
        continue
    _seen.add(_k)
    if post["slug"] not in POSTED:
        kept_unposted.append(post["slug"])   # never published -> its video is still needed
        continue
    pub = dt.datetime.fromisoformat(post["publish_at"])
    pub = pub.replace(tzinfo=tz) if tz else pub.replace(tzinfo=dt.timezone.utc)
    if pub >= cutoff:
        continue   # too recent — keep the video live a bit longer
    path = os.path.join(ROOT, "content", "reels", f"{post['slug']}.mp4")
    if os.path.exists(path):
        os.remove(path)
        removed.append(f"content/reels/{post['slug']}.mp4")

print(f"cleanup at {now.isoformat()}")
print("removed:", removed if removed else "nothing (no published videos past the buffer)")
print(f"kept {len(kept_unposted)} unpublished reel video(s) — never deleted before publishing")
