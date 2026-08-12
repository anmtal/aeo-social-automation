"""Report how much unposted content is left in the queue (for the buffer alert)."""
import datetime as dt
import json
import os

try:
    from zoneinfo import ZoneInfo
except ImportError:
    ZoneInfo = None

HERE = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(HERE, "posts-manifest.json"), encoding="utf-8") as f:
    m = json.load(f)

tz = None
if ZoneInfo is not None:
    try:
        tz = ZoneInfo(m.get("timezone", "UTC"))
    except Exception:
        tz = None
now = dt.datetime.now(tz) if tz else dt.datetime.now(dt.timezone.utc)


def due(p):
    d = dt.datetime.fromisoformat(p["publish_at"])
    return d.replace(tzinfo=tz) if tz else d.replace(tzinfo=dt.timezone.utc)


# Anything ready and not yet in posted.json still owes a post, including entries whose
# scheduled time has slipped into the past. Counting only future timestamps quietly
# dropped everything the publisher failed to ship and overstated the runway.
try:
    import json as _json, os as _os
    _pp = _os.path.join(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))), "content", "posted.json")
    _posted = set(_json.load(open(_pp, encoding="utf-8"))) if _os.path.exists(_pp) else set()
except Exception:
    _posted = set()
future = [p for p in m["posts"] if p.get("status") == "ready" and p.get("slug") not in _posted]
n = len(future)
per_day = m.get("posts_per_day", 2)
days_left = round(n / per_day, 1)
print(f"unposted={n} days_left={days_left}")

gh_out = os.environ.get("GITHUB_OUTPUT")
if gh_out:
    with open(gh_out, "a", encoding="utf-8") as f:
        f.write(f"days_left={days_left}\nunposted={n}\n")
