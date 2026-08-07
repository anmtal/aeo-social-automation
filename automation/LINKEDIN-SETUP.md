# The AEO Loop — LinkedIn Company Page Auto-Posting Setup

Posts Mon/Wed/Fri to **The AEO Loop** Company Page (`urn:li:organization:142881365`) via the
official LinkedIn API, cloud-scheduled. No browser bots.

> **Read this first — the honest catch.** Posting to a *Company Page* requires LinkedIn's
> **Community Management API**, which needs an **approval review** (Instagram's token was
> self-serve; this isn't). It's normally granted for a real business page you admin, but it
> can take a few days and isn't guaranteed. If it's slow or denied, use the **fallback**
> at the bottom — a scheduler posts to your page today, no API approval needed.

## Step 1 — Create a LinkedIn developer app
1. **developers.linkedin.com** → **Create app** (log in as the account that admins the page).
2. Associate it with the **The AEO Loop** Company Page (it asks for a page — pick yours).
3. Verify the app (LinkedIn emails a verification link to a page admin — you).

## Step 2 — Request the products you need
On the app's **Products** tab, request:
- **Sign In with LinkedIn using OpenID Connect** (for auth) — usually instant.
- **Community Management API** — this is the one that allows Company Page posting
  (`w_organization_social`). **This triggers the review.** Fill the form describing that you
  post organic updates to your own page. Approval is what unlocks live posting.

## Step 3 — Authorize + get an access token (`w_organization_social`)
Once Community Management API is approved:
1. In the app **Auth** tab, add a redirect URL (e.g. `https://localhost/callback`).
2. Do the OAuth 2.0 authorization-code flow requesting scopes
   `w_organization_social r_organization_social openid profile`. (LinkedIn's Token Generator
   tool under the app can do this in-browser for your own app.)
3. You get an **access token** (~60 days) — this is your `LINKEDIN_ACCESS_TOKEN`.

## Step 4 — GitHub secrets
In the `aeo-social-automation` repo → **Settings → Secrets and variables → Actions**:
**Secrets:** `LINKEDIN_ACCESS_TOKEN`, `LINKEDIN_ORG_URN` = `urn:li:organization:142881365`.
**Variables:** `LINKEDIN_VERSION` = `202405` (bump if LinkedIn deprecates it).

## Step 5 — Test
**Dry-run (posts nothing):**
```
python automation/linkedin_publisher.py --due --dry-run
```
**Real test:** GitHub → **Actions → The AEO Loop LinkedIn scheduler → Run workflow** → slug
`li-no-page-two`. `PUBLISHED post …` in the log = it's on your page. Delete after if it was
just a check. Then the MWF schedule runs itself.

## Caveats / guardrails
- **Token expiry:** LinkedIn tokens last ~60 days. When it expires the job fails and GitHub
  emails you — re-run Step 3 and update the secret. (Refresh tokens exist but LinkedIn keeps
  changing the rules; a 60-day manual refresh is the reliable path for now.)
- **Text escaping:** LinkedIn's "Little Text" format reserves `( ) [ ] { } < > \ | @ * _ ~`.
  The publisher backslash-escapes them automatically (leaving `#` so hashtags stay clickable).
  Eyeball the first real post to confirm it renders clean.
- **Company Page only:** the token authorizes `urn:li:organization:142881365` — it posts only
  to your page, nothing else.
- **Replies stay human** — the machine posts; you engage in the comments yourself.

## Fallback (if Community Management API approval is slow or denied)
The content is already written in `automation/linkedin-manifest.json`. Drop it into a
**scheduler** (Metricool / Publer / Buffer) that has LinkedIn partner access — connect the
Company Page, schedule the MWF posts. No API approval needed; you lose only the fully-hands-off
part (you paste them in weekly). Switch to the API machine once approved.

## Refilling the queue (generate as needed)
Posts are drawn from a topic backlog in `content/linkedin-topics.json` (36 topics,
`priority: 1` = draft first, buyer-intent). When the manifest runs low on future posts:

1. `python tools/linkedin_next.py` — shows how many posts are still scheduled, the next
   topics to draft (priority order), each mapped to a live page to link, and the next
   Mon/Wed/Fri 09:00 ET slots.
2. `python tools/linkedin_next.py --scaffold` — appends empty `draft` slots to
   `linkedin-manifest.json` for the next topics and marks them `drafted` in the backlog.
   (The publisher only ever posts `status: "ready"`, so `draft` slots are inert.)
3. Write each post's `text` in brand voice — short first-person paragraphs, one pointed
   close, 2-3 hashtags, no fabricated stats, never a guaranteed-ranking claim — then change
   that entry's `status` from `"draft"` to `"ready"`.
4. Commit. The MWF scheduler posts the earliest due `ready` one.

`status: "hold"` topics need a real client or consent before they can be written honestly
(e.g. case studies). Leave them until the data is real; use the "our own site" dogfood angle
for proof in the meantime.
