# -*- coding: utf-8 -*-
"""Print the slug of the next reel that's due and not yet rendered. Empty if none."""
import json, os, sys, datetime as dt
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def tz():
    try:
        from zoneinfo import ZoneInfo; return ZoneInfo("America/Toronto")
    except Exception: return dt.timezone.utc
m = json.load(open(os.path.join(HERE, "automation", "reel-manifest.json"), encoding="utf-8"))
dp = os.path.join(HERE, "content", "reels-done.json")
done = set(json.load(open(dp, encoding="utf-8"))) if os.path.exists(dp) else set()
now = dt.datetime.now(tz())
due = []
for r in m["reels"]:
    # reel-manifest.json repeats slugs on a rotation, so a slug-only key marks every
    # later occurrence as already rendered. Key on slug + scheduled date, and keep
    # honouring bare-slug entries written by older runs.
    key = f'{r["slug"]}@{r["publish_at"][:10]}'
    if key in done or r["slug"] in done: continue
    d = dt.datetime.fromisoformat(r["publish_at"]).replace(tzinfo=tz())
    if d <= now and (now - d) <= dt.timedelta(hours=18):
        due.append((r["publish_at"], r["slug"]))  # renderer marks done as slug@YYYY-MM-DD
due.sort()
print(due[0][1] if due else "")
