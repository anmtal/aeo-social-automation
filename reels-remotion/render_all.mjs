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
let CONTENT = path.join(REPO, "content", "reels-content.json");
const DL = "C:/Users/anmta/Downloads/aeo-reels";
const SRC = path.join(DL, "_source"); // master reels (1 per topic); post from by-date/ instead
const OUT = path.join(HERE, "out");
// 5 hashtags: the 5 primary by default; a reel may set its own `hashtags` (5) for a content swap.
const DEFAULT_TAGS = "#plasticsurgeon #plasticsurgery #ChatGPT #medicalmarketing #practicegrowth";
const tagsFor = (r) => (Array.isArray(r.hashtags) && r.hashtags.length ? r.hashtags.join(" ") : DEFAULT_TAGS);

fs.mkdirSync(OUT, { recursive: true });
fs.mkdirSync(DL, { recursive: true });
fs.mkdirSync(SRC, { recursive: true });

let cliArgs = process.argv.slice(2);
const _ci = cliArgs.indexOf("--content");
if (_ci >= 0) { CONTENT = path.resolve(REPO, cliArgs[_ci + 1]); cliArgs.splice(_ci, 2); }
const all = JSON.parse(fs.readFileSync(CONTENT, "utf-8"));
const only = cliArgs;
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
  fs.copyFileSync(outfile, path.join(SRC, fname + ".mp4"));
  fs.writeFileSync(path.join(SRC, fname + ".txt"), ((reel.caption || "") + "\n\n" + tagsFor(reel)).trim());
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
  // by-date/: one file per calendar day, named by its post date (easy manual posting)
  const BD = path.join(DL, "by-date");
  fs.rmSync(BD, { recursive: true, force: true });
  fs.mkdirSync(BD, { recursive: true });
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
    const base = `${iso(d)} ${DOW[wd]} ${reel.kind === "edu" ? "EDU" : "AD"} - ${reel.slug}`;
    fs.copyFileSync(path.join(SRC, fn + ".mp4"), path.join(BD, base + ".mp4"));
    fs.writeFileSync(path.join(BD, base + ".txt"), ((reel.caption || "") + "\n\n" + tagsFor(reel)).trim());
    lines.push(`${iso(d)} ${DOW[wd]}  ${kind}  ->  by-date/${base}.mp4`);
    lines.push(`                              hook: ${reel.hook}`);
  }
  lines.push("", "POST FROM by-date/ (one file per day, named by date). Master reels live in _source/. Each .mp4 has a matching .txt caption.");
  fs.writeFileSync(path.join(DL, "_SCHEDULE.txt"), lines.join("\n"));
  console.log("SCHEDULE written -> " + path.join(DL, "_SCHEDULE.txt"));
}
console.log("done -> " + DL);
