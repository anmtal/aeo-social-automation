# -*- coding: utf-8 -*-
"""The AEO Loop - LinkedIn 'generate as needed' helper.

Shows how deep the publish queue is, which backlog topics to draft next
(priority order), and the next daily 09:00 ET slots to assign. With
--scaffold it appends empty 'draft' slots to linkedin-manifest.json for the
next N topics and marks them 'drafted' in linkedin-topics.json, so the
drafting step is just: fill in `text`, flip status 'draft' -> 'ready'.

  python tools/linkedin_next.py                # report: queue depth + next topics + slots
  python tools/linkedin_next.py --count 5      # show the next 5 topics
  python tools/linkedin_next.py --scaffold     # add draft slots to the manifest for the next N

The publisher only ever posts status == 'ready', so 'draft' slots are inert
until you write the copy and promote them. Nothing here calls the LinkedIn API.
"""
import argparse, datetime as dt, json, os, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
AUTO = os.path.join(ROOT, "automation")
CONTENT = os.path.join(ROOT, "content")
MANIFEST = os.path.join(AUTO, "linkedin-manifest.json")
TOPICS = os.path.join(CONTENT, "linkedin-topics.json")
POSTED = os.path.join(CONTENT, "linkedin-posted.json")
FMT = "%Y-%m-%dT%H:%M"
POST_DAYS = {0, 1, 2, 3, 4, 5, 6}  # every day (7-day cadence; trim this set to post on fewer days)
POST_HOUR = 9


def tz():
    try:
        from zoneinfo import ZoneInfo
        return ZoneInfo("America/Toronto")
    except Exception:
        return dt.timezone.utc


def load(path, default):
    if not os.path.exists(path):
        return default
    return json.load(open(path, encoding="utf-8"))


def write_atomic(path, obj):
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(obj, f, ensure_ascii=False, indent=2)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)


def parse_at(s):
    try:
        return dt.datetime.strptime(s, FMT)
    except Exception:
        try:
            return dt.datetime.fromisoformat(s)
        except Exception:
            return None


def next_slots(manifest, now, n):
    """Next n daily 09:00 slots after the later of now and the last scheduled post,
    skipping any date already present in the manifest."""
    used = {p.get("publish_at") for p in manifest.get("posts", [])}
    scheduled = [parse_at(p["publish_at"]) for p in manifest.get("posts", []) if parse_at(p.get("publish_at", ""))]
    start = max([now] + scheduled) if scheduled else now
    day = start.date()
    out = []
    for _ in range(120):
        day += dt.timedelta(days=1)
        if day.weekday() in POST_DAYS:
            slot = dt.datetime(day.year, day.month, day.day, POST_HOUR, 0)
            s = slot.strftime(FMT)
            if s not in used:
                out.append(s)
                if len(out) >= n:
                    break
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--count", type=int, default=3)
    ap.add_argument("--scaffold", action="store_true")
    a = ap.parse_args()

    now = dt.datetime.now(tz()).replace(tzinfo=None)
    manifest = load(MANIFEST, {"posts": []})
    topics_doc = load(TOPICS, {"topics": []})
    topics = topics_doc.get("topics", [])
    posted = set(load(POSTED, []))

    ready_future = [p for p in manifest.get("posts", [])
                    if p.get("status") == "ready" and p["slug"] not in posted
                    and (parse_at(p.get("publish_at", "")) or now) >= now]
    drafts = [p for p in manifest.get("posts", []) if p.get("status") == "draft"]

    print("== LinkedIn queue ==")
    print(f"  ready & scheduled ahead : {len(ready_future)}")
    print(f"  draft slots (need copy) : {len(drafts)}")
    if len(ready_future) + len(drafts) < 2:
        print("  LOW - draft more from the backlog below.")

    queued = [t for t in topics if t.get("status") == "queued"]
    queued.sort(key=lambda t: (t.get("priority", 9), t.get("title", "")))
    take = queued[:a.count]
    slots = next_slots(manifest, now, a.count)

    print(f"\n== Next {len(take)} topics to draft (priority order) ==")
    for i, t in enumerate(take):
        slot = slots[i] if i < len(slots) else "(assign a slot)"
        url = t.get("internal_url") or "(no page yet)"
        print(f"\n  [{t.get('priority')}] {t['title']}   -> {slot}")
        print(f"      slug: {t['slug']}   link: {url}   {' '.join(t.get('tags', []))}")
        print(f"      angle: {t.get('angle','')}")

    holds = [t for t in topics if t.get("status") == "hold"]
    if holds:
        print(f"\n== On hold ({len(holds)}) - need real data/consent, do not draft yet ==")
        for t in holds:
            print(f"  - {t['title']}")

    if a.scaffold:
        if not take:
            sys.exit("\nNothing queued to scaffold.")
        existing = {p["slug"] for p in manifest.get("posts", [])}
        added = 0
        for i, t in enumerate(take):
            if i >= len(slots):
                break
            if t["slug"] in existing:
                continue
            manifest.setdefault("posts", []).append({
                "slug": t["slug"], "status": "draft", "publish_at": slots[i],
                "topic": t["title"], "internal_url": t.get("internal_url", ""), "text": ""})
            t["status"] = "drafted"
            added += 1
        write_atomic(MANIFEST, manifest)
        write_atomic(TOPICS, topics_doc)
        print(f"\nScaffolded {added} draft slot(s) into linkedin-manifest.json "
              f"(status 'draft'). Fill each `text`, then set status to 'ready'.")


if __name__ == "__main__":
    main()
