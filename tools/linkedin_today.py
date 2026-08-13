# -*- coding: utf-8 -*-
"""The AEO Loop - LinkedIn manual-post helper (no API needed).

Prints the next LinkedIn post to copy-paste, from linkedin-manifest.json, oldest
scheduled first. You post it by hand on your Company Page, then mark it done.

  python tools/linkedin_today.py                 # show the next post to paste
  python tools/linkedin_today.py --done <slug>   # mark that post as posted
  python tools/linkedin_today.py --all           # list every unposted post + date
"""
import argparse, datetime as dt, json, os, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
MANIFEST = os.path.join(ROOT, "automation", "linkedin-manifest.json")
POSTED = os.path.join(ROOT, "content", "linkedin-posted.json")
FMT = "%Y-%m-%dT%H:%M"

if os.name == "nt":
    os.system("")
USE = sys.stdout.isatty() and not os.environ.get("NO_COLOR")
def paint(t, c): return f"\033[{c}m{t}\033[0m" if USE else t
BOLD, DIM, GRN, YEL = "1", "90", "92", "93"

def load(p, d):
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else d

def save_posted(lst):
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(POSTED), suffix=".tmp")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(sorted(set(lst)), f, ensure_ascii=False, indent=2)
    os.replace(tmp, POSTED)

def when(s):
    try: return dt.datetime.strptime(s, FMT)
    except Exception: return dt.datetime.max

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--done", metavar="SLUG")
    ap.add_argument("--all", action="store_true")
    a = ap.parse_args()

    posted = list(load(POSTED, []))
    posts = [p for p in load(MANIFEST, {"posts": []}).get("posts", []) if p.get("status") == "ready"]

    if a.done:
        slugs = {p["slug"] for p in posts}
        if a.done not in slugs:
            sys.exit(f"No ready post with slug '{a.done}'. Run without --done to see the queue.")
        posted.append(a.done); save_posted(posted)
        print(paint(f"\n  Marked posted: {a.done}\n", GRN)); return

    queue = sorted([p for p in posts if p["slug"] not in set(posted)], key=lambda p: when(p.get("publish_at", "")))

    if a.all:
        print(f"\n  {len(queue)} post(s) not yet posted:")
        for p in queue:
            print(f"    {p.get('publish_at','?')[:10]}  {p['slug']}")
        print(); return

    if not queue:
        print(paint("\n  All manifest posts are done.", GRN))
        print("  Run  python tools/linkedin_next.py --scaffold  to draft more from the backlog.\n")
        return

    nxt = queue[0]
    print()
    print(paint("  ===== NEXT LINKEDIN POST (copy everything between the lines) =====", BOLD))
    print()
    print(nxt.get("text", "(no text)"))
    print()
    print(paint("  ================================================================", BOLD))
    print(f"  scheduled {paint(nxt.get('publish_at','?')[:10], DIM)}  |  slug {paint(nxt['slug'], DIM)}  |  {len(queue)-1} more after this")
    print(f"  after you post it:  {paint('python tools/linkedin_today.py --done ' + nxt['slug'], YEL)}")
    print()

if __name__ == "__main__":
    main()
