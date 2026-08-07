# -*- coding: utf-8 -*-
"""Upload The AEO Loop reels to YouTube as Shorts (local, YouTube Data API v3).

Reuses the reels you already render locally. Each unique reel uploads ONCE.
- Reads automation/youtube-manifest.json  (slug -> title / description / tags)
- Finds the rendered MP4 in REELS_DIR       (default: ~/Downloads/aeo-reels)
- Muxes a royalty-free music track via ffmpeg if YOUTUBE_MUSIC is set (reels render silent)
- Uploads a public Short (#Shorts is in the manifest text), logs content/youtube-posted.json

Usage:
    python automation/youtube_publisher.py --check          # verify auth + which channel
    python automation/youtube_publisher.py --next           # upload next unposted (manifest order)
    python automation/youtube_publisher.py --slug edu-shortlist
    python automation/youtube_publisher.py --next --dry-run # show what would happen, upload nothing

Secrets live in automation/.env (gitignored — repo is PUBLIC):
    YOUTUBE_CLIENT_ID, YOUTUBE_CLIENT_SECRET, YOUTUBE_REFRESH_TOKEN
    optional: YOUTUBE_MUSIC (path to an mp3), REELS_DIR, YOUTUBE_PRIVACY (default: public)
Generate the refresh token once with: python automation/youtube_auth.py
"""
import argparse, glob, json, os, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
MANIFEST = os.path.join(HERE, "youtube-manifest.json")
POSTED = os.path.join(ROOT, "content", "youtube-posted.json")
TOKEN_URI = "https://oauth2.googleapis.com/token"
UPLOAD_SCOPE = "https://www.googleapis.com/auth/youtube.upload"
READONLY_SCOPE = "https://www.googleapis.com/auth/youtube.readonly"
# Must match the scopes granted at consent, or a refresh narrows the token and
# channel reads 403. Uploading itself only needs youtube.upload.
SCOPES = [UPLOAD_SCOPE, READONLY_SCOPE]


def load_env():
    p = os.path.join(HERE, ".env")
    if os.path.exists(p):
        for line in open(p, encoding="utf-8"):
            s = line.strip()
            if s and not s.startswith("#") and "=" in s:
                k, v = s.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def env(k, required=True, default=None):
    v = os.environ.get(k, default)
    if required and not v:
        sys.exit(f"Missing env var {k} — put it in automation/.env (run youtube_auth.py first).")
    return v


def _service():
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    creds = Credentials(
        None,
        refresh_token=env("YOUTUBE_REFRESH_TOKEN"),
        client_id=env("YOUTUBE_CLIENT_ID"),
        client_secret=env("YOUTUBE_CLIENT_SECRET"),
        token_uri=TOKEN_URI,
        scopes=SCOPES,
    )
    return build("youtube", "v3", credentials=creds, cache_discovery=False)


def load_posted():
    if not os.path.exists(POSTED):
        return []
    try:
        d = json.load(open(POSTED, encoding="utf-8"))
        return d if isinstance(d, list) else []
    except Exception as e:
        sys.exit(f"youtube-posted.json is corrupt ({e}) — refusing to run to avoid a re-upload.")


def mark_posted(slug):
    p = set(load_posted())
    p.add(slug)
    os.makedirs(os.path.dirname(POSTED), exist_ok=True)
    json.dump(sorted(p), open(POSTED, "w", encoding="utf-8"), ensure_ascii=False, indent=2)


def find_mp4(slug):
    d = os.environ.get("REELS_DIR", os.path.join(os.path.expanduser("~"), "Downloads", "aeo-reels"))
    for pat in (f"{slug}.mp4", f"*{slug}*.mp4"):
        hits = sorted(glob.glob(os.path.join(d, pat)))
        if hits:
            return hits[0]
    return None


def add_music(mp4):
    """Reels render silent; mux one royalty-free track so the Short has audio."""
    music = os.environ.get("YOUTUBE_MUSIC")
    if not music or not os.path.exists(music):
        print("  NOTE: no YOUTUBE_MUSIC set — uploading the SILENT render (Shorts do better with audio).")
        return mp4, None
    out = tempfile.mktemp(suffix="_yt.mp4")
    subprocess.run(
        ["ffmpeg", "-y", "-i", mp4, "-i", music, "-map", "0:v:0", "-map", "1:a:0",
         "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", out],
        check=True, capture_output=True,
    )
    print(f"  muxed music: {os.path.basename(music)}")
    return out, out


def upload(slug, meta, dry=False):
    from googleapiclient.http import MediaFileUpload
    mp4 = find_mp4(slug)
    if not mp4:
        sys.exit(f"No MP4 for '{slug}' in REELS_DIR. Render the reel locally first.")
    title = meta["title"][:100]
    desc = meta["description"]
    tags = meta.get("tags", [])
    print(f"=== {slug} ===\n  file : {mp4}\n  title: {title}")
    if dry:
        print("  [dry-run] validated, nothing uploaded.")
        return
    path, tmp = add_music(mp4)
    body = {
        "snippet": {"title": title, "description": desc, "tags": tags, "categoryId": "22"},
        "status": {"privacyStatus": os.environ.get("YOUTUBE_PRIVACY", "public"),
                   "selfDeclaredMadeForKids": False},
    }
    media = MediaFileUpload(path, chunksize=-1, resumable=True, mimetype="video/mp4")
    req = _service().videos().insert(part="snippet,status", body=body, media_body=media)
    resp = None
    while resp is None:
        _, resp = req.next_chunk()
    print(f"  UPLOADED -> https://youtu.be/{resp['id']}")
    mark_posted(slug)
    if tmp and os.path.exists(tmp):
        os.remove(tmp)


def main():
    load_env()
    ap = argparse.ArgumentParser()
    ap.add_argument("--slug")
    ap.add_argument("--next", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    if a.check:
        ch = _service().channels().list(part="snippet", mine=True).execute()
        items = ch.get("items") or []
        print("OK — authenticated as channel:", items[0]["snippet"]["title"] if items else "(none returned)")
        return

    man = json.load(open(MANIFEST, encoding="utf-8"))
    reels = {r["slug"]: r for r in man["reels"]}
    posted = load_posted()

    if a.slug:
        if a.slug not in reels:
            sys.exit(f"Unknown slug {a.slug}. Known: {', '.join(reels)}")
        if a.slug in posted and not a.dry_run:
            sys.exit(f"{a.slug} already uploaded — refusing.")
        upload(a.slug, reels[a.slug], a.dry_run)
        return

    if a.next:
        for r in man["reels"]:
            if r["slug"] not in posted:
                upload(r["slug"], r, a.dry_run)
                return
        print("Nothing left to upload — every manifest reel is already on YouTube.")
        return

    sys.exit("Pass --check, --slug <slug>, or --next.")


if __name__ == "__main__":
    main()
