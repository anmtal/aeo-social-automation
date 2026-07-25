// Render every reel in content/reels-content.json to a 9:16 MP4 via Remotion,
// copy to the founder's Downloads with captions, and write the posting calendar.
//   node render_all.mjs            -> renders all
//   node render_all.mjs edu-shortlist ad-free-scan   -> renders only those slugs
import { bundle } from "@remotion/bundler";
import { selectComposition, renderMedia } from "@remotion/renderer";
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const REPO = path.resolve(HERE, "..");
const CONTENT = path.join(REPO, "content", "reels-content.json");
const DL = "C:/Users/anmta/Downloads/aeo-reels";
const OUT = path.join(HERE, "out");
const TAGS =
  "#plasticsurgeon #plasticsurgery #cosmeticsurgery #medspa #AIsearch #ChatGPT #medicalmarketing #practicegrowth #AEO #AIvisibility";

fs.mkdirSync(OUT, { recursive: true });
fs.mkdirSync(DL, { recursive: true });

const all = JSON.parse(fs.readFileSync(CONTENT, "utf-8"));
const only = process.argv.slice(2);
const reels = only.length ? all.filter((r) => only.includes(r.slug)) : all;

console.log("Bundling Remotion project...");
const serveUrl = await bundle({ entryPoint: path.join(HERE, "src", "index.ts") });

const built = {};
for (const reel of reels) {
  const comp = await selectComposition({ serveUrl, id: "AeoReel", inputProps: reel });
  const outfile = path.join(OUT, reel.slug + ".mp4");
  await renderMedia({ serveUrl, composition: comp, codec: "h264", outputLocation: outfile, inputProps: reel });
  const tag = reel.kind === "edu" ? "EDU" : "AD";
  const fname = `${tag}_${reel.slug}`;
  fs.copyFileSync(outfile, path.join(DL, fname + ".mp4"));
  fs.writeFileSync(path.join(DL, fname + ".txt"), ((reel.caption || "") + "\n\n" + TAGS).trim());
  built[reel.slug] = fname;
  console.log(`  built ${fname}  (${comp.durationInFrames} frames)`);
}

// ---- posting calendar (only when rendering the full set) ----
if (!only.length) {
  const edu = all.filter((r) => r.kind === "edu");
  const ads = all.filter((r) => r.kind === "ad");
  const DOW = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
  const today = new Date();
  const iso = (d) => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
  const lines = [
    "THE AEO LOOP — REEL POSTING CALENDAR (Remotion, animated)",
    `(rebuilt ${iso(today)})`,
    "",
    "Educational reels (toned down) go out TUESDAY & THURSDAY.",
    "Advertising reels go out every other day.",
    "Every reel ends on the Free-scan + theaeoloop.com CTA.",
    "Each day: upload the listed .mp4, paste the matching .txt caption, add trending audio on your phone, post.",
    "",
  ];
  let ei = 0, ai = 0;
  for (let i = 0; i < 21; i++) {
    const d = new Date(today);
    d.setDate(d.getDate() + i);
    const wd = d.getDay();
    let reel, kind;
    if (wd === 2 || wd === 4) { reel = edu[ei % edu.length]; ei++; kind = "EDUCATIONAL"; }
    else { reel = ads[ai % ads.length]; ai++; kind = "ADVERTISING "; }
    const fn = built[reel.slug] || `${reel.kind === "edu" ? "EDU" : "AD"}_${reel.slug}`;
    lines.push(`${iso(d)} ${DOW[wd]}  ${kind}  ->  ${fn}.mp4`);
    lines.push(`                              hook: ${reel.hook}`);
  }
  lines.push("", "FILES: EDU_*.mp4 (6, rotate Tue/Thu) · AD_*.mp4 (6, rotate other days). Each has a matching .txt caption.");
  fs.writeFileSync(path.join(DL, "_SCHEDULE.txt"), lines.join("\n"));
  console.log("SCHEDULE written -> " + path.join(DL, "_SCHEDULE.txt"));
}
console.log("done -> " + DL);
