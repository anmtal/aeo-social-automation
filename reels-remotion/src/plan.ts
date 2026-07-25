// Segment plan for a reel — shared by the component (to lay out scenes) and the
// composition's calculateMetadata (to compute exact duration per reel, no dead air).
export type ReelProps = {
  slug?: string;
  kind?: string;
  eyebrow: string;
  hook: string;
  points?: string[];
  cta: string;
  scene?: any;
  caption?: string;
};

const COVER = 110;
const SCENE = 140;
const CTA = 100;

export function planReel(p: ReelProps) {
  const segs: { kind: string; dur: number; from: number }[] = [];
  let t = 0;
  const add = (kind: string, dur: number) => {
    segs.push({ kind, dur, from: t });
    t += dur;
  };
  add("cover", COVER);
  if (p.scene && p.scene.type) add("scene", SCENE);
  const n = p.points ? p.points.length : 0;
  if (n) add("points", 40 + n * 52);
  add("cta", CTA);
  return { segs, total: t };
}

export const totalFrames = (p: ReelProps) => planReel(p).total;
