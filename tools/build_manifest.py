# -*- coding: utf-8 -*-
"""Build posts-manifest.json from carousels.json — one post/day at 19:00 ET.
Start date is passed as arg (YYYY-MM-DD) since the runtime forbids Date.now here.
Run:  python tools/build_manifest.py 2026-07-23"""
import json, os, sys, datetime as dt

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
carousels = json.load(open(os.path.join(HERE, "content", "carousels.json"), encoding="utf-8"))
start = dt.date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else dt.date(2026, 7, 23)

posts = []
for i, c in enumerate(carousels):
    day = start + dt.timedelta(days=i)
    posts.append({
        "slug": c["slug"],
        "type": "carousel",
        "slides": 2 + len(c.get("points", [])),
        "status": "ready",
        "caption": c["caption"],
        "firstComment": c.get("firstComment", ""),
        "publish_at": f"{day.isoformat()}T19:00",   # 7:00 PM, interpreted in manifest timezone (ET)
    })

manifest = {
    "timezone": "America/Toronto",
    "posts_per_day": 1,
    "note": "Daily Instagram carousels at 19:00 ET. Rebuild with tools/build_manifest.py after adding to carousels.json.",
    "posts": posts,
}
json.dump(manifest, open(os.path.join(HERE, "automation", "posts-manifest.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=2)
print(f"wrote posts-manifest.json — {len(posts)} posts, {posts[0]['publish_at']} -> {posts[-1]['publish_at']}")
