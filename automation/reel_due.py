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
    if r["slug"] in done: continue
    d = dt.datetime.fromisoformat(r["publish_at"]).replace(tzinfo=tz())
    if d <= now and (now - d) <= dt.timedelta(hours=18):
        due.append((r["publish_at"], r["slug"]))
due.sort()
print(due[0][1] if due else "")
