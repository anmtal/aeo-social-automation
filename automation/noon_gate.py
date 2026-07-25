# -*- coding: utf-8 -*-
"""Land the noon carousel at EXACTLY 12:00 America/New_York.

GitHub's scheduled cron only ever starts runs LATE (often 1-2h). So we schedule
the run to START before noon, then this gate sleeps until 12:00 ET and returns,
letting the publish step post right on the hour. DST-aware (zoneinfo).

Exit codes (consumed by daily-post.yml):
  0  -> proceed to publish (either we slept to noon, or it's already >= noon)
  2  -> too early (outside the window); skip this run, a later cron will post
"""
import sys, time
from datetime import datetime
from zoneinfo import ZoneInfo

ET = ZoneInfo("America/New_York")
WINDOW = 2 * 60 * 60  # only wait if we're within 2h before noon (covers GitHub's delay)

now = datetime.now(ET)
target = now.replace(hour=12, minute=0, second=0, microsecond=0)
delta = (target - now).total_seconds()

if delta > WINDOW:
    print(f"[noon_gate] {now:%H:%M} ET — {delta/60:.0f} min before noon (> {WINDOW//60}m window). "
          f"Skipping; a later cron will land it.")
    sys.exit(2)

if delta > 0:
    print(f"[noon_gate] {now:%H:%M} ET — sleeping {delta/60:.1f} min so the post lands at 12:00 ET...")
    time.sleep(delta)

print(f"[noon_gate] posting now ({datetime.now(ET):%H:%M} ET).")
sys.exit(0)
