# The AEO Loop — YouTube Shorts auto-uploader

Uploads the reels you already render (in `~/Downloads/aeo-reels/`) to the
**The AEO Loop** channel (`UCktLX860_6jJsSCd0utNrNg`) as Shorts, with search-first
titles and the free-scan CTA. Runs **locally** (your machine has the reels, ffmpeg,
and the Google libraries already). Each unique reel uploads once.

> One-time cost: a Google Cloud OAuth setup (same idea as your Meta app for
> Instagram). ~10 minutes, then it runs on a saved refresh token.

## Step 1 — Google Cloud project + enable the API
1. Go to **console.cloud.google.com**, sign in with the account that **owns the
   YouTube channel**, and create a project (e.g. `aeo-youtube`).
2. **APIs & Services → Library → search "YouTube Data API v3" → Enable.**

## Step 2 — Configure the auth platform (new "Google Auth Platform" UI)
Google merged the old "OAuth consent screen" into **APIs & Services → Google Auth
Platform**. Use the left-nav tabs:
1. **Branding** — set the app name (`The AEO Loop uploader`) + your support email, save.
2. **Audience** — this is where the old **User type** moved. On a personal Gmail,
   **External** is the only option (Internal is Workspace-only) and is usually already
   selected. Set **Publishing status = Testing**, then under **Test users** add your
   own Google address. (Test-user refresh tokens for a Desktop app keep working while
   the app stays in Testing with you listed; if one ever stops, just re-run Step 4.)
3. **Data Access** (scopes) — leave as-is; the script requests `youtube.upload` +
   `youtube.readonly` at auth time.

## Step 3 — OAuth client (Desktop app)
1. **Google Auth Platform → Clients → Create client** (this replaced the old
   Credentials → OAuth client ID).
2. Application type: **Desktop app**. Create.
3. **Download JSON** and save it as **`automation/client_secret.json`**
   (already gitignored — it must never be committed; this repo is public).

## Step 4 — Get your refresh token (one command)
```
python automation/youtube_auth.py
```
A browser opens; approve access on your channel's Google account. The script
prints three lines. **Paste them into `automation/.env`** (gitignored):
```
YOUTUBE_CLIENT_ID=...
YOUTUBE_CLIENT_SECRET=...
YOUTUBE_REFRESH_TOKEN=...
```

## Step 5 — Add music (recommended)
Reels render **silent** (you add trending audio on your phone for Instagram).
YouTube Shorts do poorly silent, so drop one royalty-free track anywhere and point
to it in `.env`:
```
YOUTUBE_MUSIC=C:\Users\anmta\Downloads\aeo-reels\bed.mp3
```
Use a track cleared for YouTube (YouTube Audio Library download, or a CC0 source) —
do **not** reuse the Instagram trending audio (licensed for IG only). If you skip
this, it uploads silent with a warning.

## Step 6 — Test, then post
```
python automation/youtube_publisher.py --check          # confirms it sees your channel
python automation/youtube_publisher.py --next --dry-run # shows the next reel + title, uploads nothing
python automation/youtube_publisher.py --next           # uploads the next unposted reel
```
`--next` walks `youtube-manifest.json` in order and uploads the first reel not yet
in `content/youtube-posted.json` (idempotent — never double-uploads). Or target one:
`--slug edu-shortlist`.

## Optional — hands-off scheduling
Ask Claude to add a local scheduled task (like the LinkedIn one) that runs
`youtube_publisher.py --next` on your reel cadence (e.g. Tue/Thu), so new reels post
themselves once rendered. It only needs the Claude app open when it fires.

## Notes
- **Quota:** an upload costs 1,600 of the 10,000 free daily API units, so ~6/day max —
  far more than you need.
- **Titles** come from `youtube-manifest.json` (search-first, <=100 chars). Edit them
  there anytime; keep `#Shorts` in the description so vertical clips register as Shorts.
- **Privacy:** uploads are `public` by default. Set `YOUTUBE_PRIVACY=private` in `.env`
  to stage them first.
