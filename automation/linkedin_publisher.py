# -*- coding: utf-8 -*-
"""The AEO Loop — LinkedIn Company Page publisher (official LinkedIn Posts API).

Posts text updates to the Company Page (urn:li:organization:...) on schedule.
ToS-legal, no browser bots. Mon/Wed/Fri cadence comes from publish_at in the manifest
plus a MWF cron in .github/workflows/linkedin-post.yml.

Usage:
    python automation/linkedin_publisher.py --due       # post the earliest due, not-yet-posted
    python automation/linkedin_publisher.py --slug X     # post a specific slug now
    python automation/linkedin_publisher.py --check      # verify token/org (read-only)
    python automation/linkedin_publisher.py --due --dry-run  # show what's due, post nothing

Env: LINKEDIN_ACCESS_TOKEN, LINKEDIN_AUTHOR_URN (urn:li:organization:142881365),
     LINKEDIN_VERSION (optional, default 202405).
Logs: content/linkedin-posted.json (authoritative — slugs already published).
"""
import argparse, datetime as dt, json, os, sys, tempfile
try:
    import requests
except ImportError:
    requests = None

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CONTENT = os.path.join(ROOT, "content")
MANIFEST = os.path.join(HERE, "linkedin-manifest.json")
POSTED_LOG = os.path.join(CONTENT, "linkedin-posted.json")
API = "https://api.linkedin.com/rest/posts"

# LinkedIn "Little Text" reserves these punctuation chars; they must be backslash-escaped
# in commentary or the post is rejected. '#' is left alone so hashtags stay clickable.
_RESERVED = set(r'\|{}@[]()<>*_~')
def li_escape(text):
    return "".join("\\" + c if c in _RESERVED else c for c in text)

def _write_json_atomic(path, obj):
    d = os.path.dirname(path)
    fd, tmp = tempfile.mkstemp(dir=d, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(obj, f, ensure_ascii=False, indent=2)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp): os.remove(tmp)

def load_posted():
    if not os.path.exists(POSTED_LOG): return set()
    try:
        data = json.load(open(POSTED_LOG, encoding="utf-8"))
    except Exception as e:
        sys.exit(f"linkedin-posted.json is corrupt ({e}) — refusing to run to avoid double-posting.")
    if not isinstance(data, list): sys.exit("linkedin-posted.json is not a list — refusing to run.")
    return set(data)

def mark_posted(slug):
    p = load_posted(); p.add(slug); _write_json_atomic(POSTED_LOG, sorted(p))

def env(name, required=True, default=None):
    v = os.environ.get(name, default)
    if required and not v: sys.exit(f"Missing required env var: {name}")
    return v

def load_manifest():
    return json.load(open(MANIFEST, encoding="utf-8"))

def tzinfo(m):
    try:
        from zoneinfo import ZoneInfo
        return ZoneInfo(m.get("timezone", "America/Toronto"))
    except Exception:
        return dt.timezone.utc

def now_local(m): return dt.datetime.now(tzinfo(m))
def due_dt(post, tz): return dt.datetime.fromisoformat(post["publish_at"]).replace(tzinfo=tz)

def headers(token, version):
    return {
        "Authorization": f"Bearer {token}",
        "LinkedIn-Version": version,
        "X-Restli-Protocol-Version": "2.0.0",
        "Content-Type": "application/json",
    }

def build_body(org_urn, text):
    return {
        "author": org_urn,
        "commentary": li_escape(text),
        "visibility": "PUBLIC",
        "distribution": {"feedDistribution": "MAIN_FEED", "targetEntities": [], "thirdPartyDistributionChannels": []},
        "lifecycleState": "PUBLISHED",
        "isReshareDisabledByAuthor": False,
    }

def check(author_urn, token, version):
    # read-only sanity: the author URN is well-formed and the token is present
    if not (author_urn.startswith("urn:li:person:") or author_urn.startswith("urn:li:organization:")):
        sys.exit(f"LINKEDIN_AUTHOR_URN must be urn:li:person:XXXX (your profile) or urn:li:organization:XXXX (got: {author_urn})")
    print(f"OK — token present, author={author_urn}, version={version}. (No post made.)")

def publish(m, post, dry, org_urn, token, version):
    text = post["text"]
    print(f"\n=== {post['slug']}  @ {post['publish_at']} ===")
    print("Text:\n" + text)
    if dry:
        print("\n[dry-run] Validated. Nothing posted.")
        return
    if requests is None: sys.exit("`requests` not installed. Run: pip install requests")
    r = requests.post(API, headers=headers(token, version), json=build_body(org_urn, text), timeout=30)
    if r.status_code not in (200, 201):
        sys.exit(f"LinkedIn API error {r.status_code}: {r.text[:300]}")
    post_id = r.headers.get("x-restli-id") or r.headers.get("x-linkedin-id") or "(id in body)"
    print(f"PUBLISHED post {post_id}")
    mark_posted(post["slug"])

def pick_due(m):
    tz = tzinfo(m); now = now_local(m); posted = load_posted()
    due = []
    for p in m.get("posts", []):
        if p.get("status") != "ready" or p["slug"] in posted: continue
        d = due_dt(p, tz)
        # due if the time has passed but not more than 12h stale (no backlog spam)
        if d <= now and (now - d) <= dt.timedelta(hours=12): due.append(p)
    due.sort(key=lambda p: p["publish_at"])
    return now, due

def resolve_person_urn(token):
    """Derive urn:li:person:<id> from the token via OpenID userinfo, so the user
    only has to set the access token (not hunt down their member id)."""
    if requests is None: return None
    try:
        r = requests.get("https://api.linkedin.com/v2/userinfo",
                         headers={"Authorization": f"Bearer {token}"}, timeout=20)
        if r.status_code == 200:
            sub = r.json().get("sub")
            return f"urn:li:person:{sub}" if sub else None
    except Exception:
        return None
    return None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--due", action="store_true")
    ap.add_argument("--slug")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    m = load_manifest()
    version = os.environ.get("LINKEDIN_VERSION", "202405")
    token = env("LINKEDIN_ACCESS_TOKEN", required=not a.dry_run, default="(dry)")
    org_urn = os.environ.get("LINKEDIN_AUTHOR_URN", "").strip()
    if (not org_urn or org_urn.endswith("REPLACE")) and not a.dry_run:
        org_urn = resolve_person_urn(token)
        if not org_urn:
            sys.exit("Could not resolve your LinkedIn person URN from the token. Generate the "
                     "token with 'openid' + 'profile' + 'w_member_social' scopes, or set the "
                     "LINKEDIN_AUTHOR_URN secret manually (urn:li:person:XXXX).")
    if a.check:
        check(org_urn or "urn:li:person:(dry-run)", token, version); return
    if a.slug:
        post = next((p for p in m["posts"] if p["slug"] == a.slug), None)
        if not post: sys.exit(f"No post with slug {a.slug}")
        if post["slug"] in load_posted(): sys.exit(f"{a.slug} already posted — refusing.")
        publish(m, post, a.dry_run, org_urn, token, version); return
    now, due = pick_due(m)
    print(f"now={now.isoformat()}  due: {[p['slug'] for p in due] or 'none'}")
    if due: publish(m, due[0], a.dry_run, org_urn, token, version)

if __name__ == "__main__":
    main()
