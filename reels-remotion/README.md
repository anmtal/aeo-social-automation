# The AEO Loop — Remotion reel renderer

Data-driven 9:16 Instagram reels for @the_aeo_loop. Reads `../content/reels-content.json`,
renders each reel to an animated MP4, and copies them (with captions + a posting
calendar) to `C:\Users\anmta\Downloads\aeo-reels\` for manual posting. It also writes
a `by-date/` subfolder where each file is named by its post date (e.g.
`2026-07-30 Thu EDU - edu-shortlist.mp4`) — just grab the one dated today.

## Render

```bash
cd reels-remotion
npm install            # first time only (pulls Remotion + a headless Chrome)
node render_all.mjs                 # render ALL reels + rewrite _SCHEDULE.txt
node render_all.mjs edu-shortlist   # render just one (or a list of) slug(s)
```

Live preview while editing: `npm run studio`.

## How a reel is built

Each entry in `reels-content.json` becomes: **cover** (animated ∞ logo + word-by-word
hook) → optional **scene** → **points** → **CTA** (always ends on `Free scan ↓` +
`theaeoloop.com`). Duration is computed per reel (`src/plan.ts`), so no dead air.

### Scene types (`scene.type` in reels-content.json)
- `shortlist` — `{ names[], title?, youLabel? }` — competitors slide in, your slot blinks empty.
- `chat` — `{ prompt, answers[], note }` — mint prompt bubble → AI answer card → red note.
- `versus` — `{ left:{title,sub,tone,mark?}, right:{...} }` — two-column split. tone: mint|coral|mute, mark: check|cross.
- `engines` — `{ lead?, items[] }` — bordered chips light up with ✓.
- (omit `scene` for a clean cover → points → CTA reel.)

## Add / change a reel
Edit `../content/reels-content.json` (slug, kind edu|ad, eyebrow, hook, optional scene,
points[], cta, caption), then `node render_all.mjs <slug>`. Educational reels go out
Tue/Thu, advertising the other days — the calendar in `_SCHEDULE.txt` maps dates to files.

Brand: mint `#1AD6A0` on near-black `#0A0E15`, Inter. Logo sits at center−425 so it
aligns with the 4:5 carousel covers in the Instagram grid.
