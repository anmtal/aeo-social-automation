# The AEO Loop — Instagram Auto-Posting Setup

Turns **@the_aeo_loop** into a hands-off machine: a free cloud job publishes the due
carousel to Instagram and posts the first comment — your computer stays off.

**Already built (in this folder):**
- Renders the carousels — `tools/carousel_generator.py`
- Hosts the images — GitHub (raw URLs)
- Publishes on schedule — GitHub Actions + Instagram Graph API (`automation/publisher.py`)
- Posts the first comment (the bait)
- Reliability rails — low-buffer alert, delivery watchdog, monthly token refresh

**Your one-time part (~40 min, free):** connect Instagram to a Facebook Page, make a Meta
app + token, push this folder to GitHub, paste the secrets. You never share a password —
you generate the token yourself and paste it into GitHub Secrets.

> LinkedIn (Mon/Wed/Fri) is a **separate** machine on the LinkedIn API — it's being built
> next and has its own short guide. This guide is Instagram only.

---

## Step 1 — @the_aeo_loop must be Professional + linked to a Facebook Page
The Graph API only publishes from a Professional (Business/Creator) account connected to a
Facebook Page.
1. In the Instagram app on @the_aeo_loop: **Settings → Account type and tools → Switch to
   professional account** (choose Business or Creator — free).
2. Create a free Facebook Page: facebook.com → Pages → Create → name it "The AEO Loop."
3. Instagram app → **Settings → Accounts Center → Connected experiences → Add accounts** →
   connect that Page.

> **The Facebook Page is never posted to** — it exists only because the API requires a
> linked Page to authorize publishing. The publisher only calls Instagram endpoints. Leave
> the Page empty; you can even set it **Unpublished** (Page → Settings → Privacy) and API
> publishing still works.

## Step 2 — Create a Meta developer app
1. **developers.facebook.com** → log in with the same Facebook account → **My Apps → Create App**.
2. Use case: **"Other"** → **"Business."**
3. Name it **"aeo-loop-poster."** Create.
4. Dashboard → **Add Product** → **Instagram Graph API** (+ "Facebook Login for Business" if prompted).

## Step 3 — Get a long-lived access token
1. Dashboard → **Tools → Graph API Explorer** → select your app.
2. **Add permissions:** `instagram_basic`, `instagram_content_publish`,
   `instagram_manage_comments`, `pages_show_list`, `pages_read_engagement`,
   `business_management`. (`instagram_manage_comments` is what posts the first comment.)
3. **Generate Access Token** → approve → select your Page + @the_aeo_loop. This is a
   SHORT-lived token (~1 hr).
4. Exchange for a LONG-lived one — paste in your browser, replacing the 3 values (App ID +
   Secret are in App settings → Basic):
   ```
   https://graph.facebook.com/v23.0/oauth/access_token?grant_type=fb_exchange_token&client_id=YOUR_APP_ID&client_secret=YOUR_APP_SECRET&fb_exchange_token=SHORT_LIVED_TOKEN
   ```
5. Get the **non-expiring Page token** (do this — saves redoing Step 3 every 60 days):
   ```
   https://graph.facebook.com/v23.0/me/accounts?access_token=YOUR_LONG_LIVED_USER_TOKEN
   ```
   Copy your Page's `access_token` from the response. **This is your `IG_ACCESS_TOKEN`** and
   it doesn't expire while the app stays active.

## Step 4 — Get your Instagram account ID
Using the Page `id` from Step 5's response above:
```
https://graph.facebook.com/v23.0/PAGE_ID?fields=instagram_business_account&access_token=YOUR_TOKEN
```
The `instagram_business_account.id` (a long number) is your **`IG_USER_ID`**.

## Step 5 — Put this folder on GitHub (also hosts the images)
1. github.com → create a new **public** repo named **`aeo-social-automation`**.
   (Public is required so Instagram can fetch the slide image URLs. This repo holds only
   social content + code — **no secrets, no client data** — so public is fine.)
2. Upload this whole `AEO Social Automation` folder (drag-and-drop works). Include
   `content/posts/...`, `automation/`, `tools/`, `.gitignore`, `.github/workflows/`.

> **Never upload a `.env` file.** The token lives ONLY in GitHub Secrets. GitHub's web
> drag-and-drop ignores `.gitignore`, so make sure no `.env` exists in the folder first.
> (`.env.example` is safe — no real values.)

Your **`IMAGE_BASE_URL`** is then (no trailing slash):
```
https://raw.githubusercontent.com/YOUR_USERNAME/aeo-social-automation/main/content
```
Test it: open `IMAGE_BASE_URL/posts/3-signs-ai-skips-you/slide-1.jpg` in a browser — you
should see the carousel cover. (404 → the folder/filename is wrong; fix before going live.)

## Step 6 — Add secrets + variables
Repo → **Settings → Secrets and variables → Actions**:
**Secrets:** `IG_USER_ID`, `IG_ACCESS_TOKEN` (the Page token), `IMAGE_BASE_URL`.
**Variables:** `GRAPH_VERSION` = `v23.0`.
Posting time lives in each post's `publish_at` in `automation/posts-manifest.json`
(timezone `America/Toronto`). Default cadence: **1/day at 18:00 ET.** The workflow cron just
needs to run often enough to catch it; GitHub cron can be 5–30 min late — that's normal.

## Step 7 — Test before you trust it
**Local dry-run** (validates manifest + image URLs; posts nothing):
```
pip install requests
$env:IMAGE_BASE_URL="https://raw.githubusercontent.com/YOUR_USERNAME/aeo-social-automation/main/content"
python automation/publisher.py --slug 3-signs-ai-skips-you --dry-run
```
Every slide should print `OK`. `NOT REACHABLE` / `not image/jpeg` → fix the repo first.

**The real test (do once):** GitHub → **Actions → the daily post workflow → Run workflow**,
type slug `3-signs-ai-skips-you`, run. `PUBLISHED media …` in the log = it posted to
@the_aeo_loop. Delete the post afterward if it was just a check. Once one manual run works,
the daily schedule needs nothing else.

## Guardrails
- **Only the official API** — no browser bots, auto-follow, or auto-DM (those get accounts banned).
- **The token binds to @the_aeo_loop only** — it cannot post to any other account, ever.
- **No double-posts** — the publisher checks recent posts + `posted.json` and skips duplicates.
- **Comment replies stay human** — the machine posts + drops the first comment; you reply in your own voice in the first hour. That's the growth engine; never automate it.
- **Keep the repo active** — GitHub disables schedules after ~60 days with no commits; the monthly token-refresh workflow makes a heartbeat commit to prevent that.
- **Skip a day** — set that post's `"status"` to anything but `"ready"`.
