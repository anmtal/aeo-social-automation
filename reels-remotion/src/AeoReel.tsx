import React from "react";
import { AbsoluteFill, Sequence, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { loadFont } from "@remotion/google-fonts/Inter";
import { planReel, ReelProps } from "./plan";

const { fontFamily } = loadFont("normal", { weights: ["500", "700", "800"], subsets: ["latin"] });

// ---- brand ----
const BG = "#0A0E15";
const MINT = "#1AD6A0";
const WHITE = "#EEF1EE";
const MUTE = "#8A948C";
const CARD = "#121A25";
const CORAL = "#E2564B";
const LINE = "#26323C";
const FOOTER = "theaeoloop.com";
const LOGO_Y = 535; // center(960) - 425, matches the 4:5 carousel logo for grid alignment

const InfinityGlyph: React.FC<{ size: number; progress: number }> = ({ size, progress }) => {
  const d = "M16 16 C12 8 5 8 5 16 C5 24 12 24 16 16 C20 8 27 8 27 16 C27 24 20 24 16 16Z";
  const len = 74;
  return (
    <svg width={size} height={size} viewBox="0 0 32 32">
      <path d={d} fill="none" stroke={MINT} strokeWidth={2.6} strokeLinecap="round"
        strokeDasharray={len} strokeDashoffset={len * (1 - Math.min(1, Math.max(0, progress)))} />
    </svg>
  );
};

const Scene: React.FC<{ children: React.ReactNode; center?: boolean }> = ({ children, center }) => (
  <AbsoluteFill style={{ backgroundColor: BG, fontFamily, ...(center ? { justifyContent: "center", alignItems: "center" } : {}) }}>
    {children}
  </AbsoluteFill>
);

// ---------- COVER ----------
const Cover: React.FC<ReelProps> = ({ eyebrow, hook }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const glyphP = interpolate(frame, [0, 26], [0, 1], { extrapolateRight: "clamp" });
  const eyeO = interpolate(frame, [12, 30], [0, 1], { extrapolateRight: "clamp" });
  const eyeSpread = interpolate(frame, [12, 34], [6, 13], { extrapolateRight: "clamp" });
  const words = hook.split(" ");
  const caretOn = frame > 30 && Math.floor(frame / 8) % 2 === 0;
  return (
    <Scene>
      <div style={{ position: "absolute", top: LOGO_Y - 65, left: 0, right: 0, display: "flex", justifyContent: "center" }}>
        <InfinityGlyph size={130} progress={glyphP} />
      </div>
      <div style={{ position: "absolute", top: 700, left: 0, right: 0, textAlign: "center", color: MINT, fontWeight: 800, fontSize: 30, letterSpacing: eyeSpread, opacity: eyeO }}>
        {eyebrow.toUpperCase()}
      </div>
      <div style={{ position: "absolute", top: 830, left: 80, right: 80 }}>
        <div style={{ display: "flex", flexWrap: "wrap", alignItems: "flex-end", gap: "10px 18px" }}>
          {words.map((w, i) => {
            const p = spring({ frame: Math.max(0, frame - (30 + i * 6)), fps, durationInFrames: 20, config: { damping: 16, stiffness: 120 } });
            return (
              <span key={i} style={{ display: "inline-block", transform: `translateY(${interpolate(p, [0, 1], [26, 0])}px)`, opacity: p, color: WHITE, fontWeight: 800, fontSize: 74, lineHeight: 1.08 }}>{w}</span>
            );
          })}
          <span style={{ display: "inline-block", width: 10, height: 66, background: MINT, opacity: caretOn ? 1 : 0.12, transform: "translateY(-6px)" }} />
        </div>
      </div>
      <Footer />
    </Scene>
  );
};

const Footer: React.FC = () => {
  const frame = useCurrentFrame();
  return (
    <div style={{ position: "absolute", bottom: 90, left: 0, right: 0, textAlign: "center", color: MINT, fontWeight: 700, fontSize: 34, opacity: interpolate(frame, [20, 40], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }) }}>{FOOTER}</div>
  );
};

// ---------- SHORTLIST ----------
const RowIn: React.FC<{ start: number; children: React.ReactNode }> = ({ start, children }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const p = spring({ frame: Math.max(0, frame - start), fps, durationInFrames: 18, config: { damping: 16, stiffness: 120 } });
  return <div style={{ display: "flex", alignItems: "center", gap: 24, marginBottom: 26, transform: `translateX(${interpolate(p, [0, 1], [-40, 0])}px)`, opacity: p }}>{children}</div>;
};

const Shortlist: React.FC<{ scene: any }> = ({ scene }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const names: string[] = scene.names || [];
  const title = scene.title || "AI'S SHORTLIST — SURGEONS NEAR YOU";
  const youLabel = scene.youLabel || "you?";
  const cardP = spring({ frame, fps, durationInFrames: 16, config: { damping: 200 } });
  const youStart = 20 + names.length * 16 + 8;
  const blink = Math.floor(frame / 8) % 2 === 0;
  return (
    <Scene center>
      <div style={{ width: 880, background: CARD, borderRadius: 34, padding: "56px 56px 48px", transform: `scale(${interpolate(cardP, [0, 1], [0.9, 1])})`, opacity: cardP, boxShadow: "0 30px 90px rgba(0,0,0,.5)" }}>
        <div style={{ color: MUTE, fontWeight: 700, fontSize: 28, marginBottom: 34, letterSpacing: 1 }}>{title}</div>
        {names.map((name, i) => (
          <RowIn key={i} start={20 + i * 16}>
            <span style={{ color: MINT, fontWeight: 800, fontSize: 46, minWidth: 40 }}>{i + 1}.</span>
            <span style={{ color: WHITE, fontWeight: 700, fontSize: 46 }}>{name}</span>
          </RowIn>
        ))}
        <RowIn start={youStart}>
          <span style={{ color: CORAL, fontWeight: 800, fontSize: 46, minWidth: 40 }}>{names.length + 1}.</span>
          <span style={{ display: "inline-block", width: 230, height: 4, background: MUTE }} />
          <span style={{ color: CORAL, fontWeight: 800, fontSize: 42, opacity: blink ? 1 : 0.25, marginLeft: 6 }}>{youLabel}</span>
        </RowIn>
      </div>
      <div style={{ marginTop: 54, color: MINT, fontWeight: 800, fontSize: 46, opacity: interpolate(frame, [youStart + 14, youStart + 34], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }) }}>Are you on the list?</div>
    </Scene>
  );
};

// ---------- CHAT ----------
const Chat: React.FC<{ scene: any }> = ({ scene }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const answers: string[] = scene.answers || [];
  const promptP = spring({ frame, fps, durationInFrames: 16, config: { damping: 200 } });
  const noteStart = 30 + answers.length * 16 + 8;
  const noteP = spring({ frame: Math.max(0, frame - noteStart), fps, durationInFrames: 18, config: { damping: 18 } });
  return (
    <Scene center>
      <div style={{ width: 880 }}>
        <div style={{ maxWidth: 720, marginLeft: "auto", background: MINT, color: BG, fontWeight: 700, fontSize: 40, padding: "26px 34px", borderRadius: "30px 30px 8px 30px", opacity: promptP, transform: `translateY(${interpolate(promptP, [0, 1], [20, 0])}px)`, marginBottom: 30 }}>{scene.prompt}</div>
        <div style={{ background: CARD, borderRadius: "30px 30px 30px 8px", padding: "38px 40px" }}>
          <div style={{ color: MUTE, fontWeight: 700, fontSize: 26, marginBottom: 24, letterSpacing: 1 }}>AI'S ANSWER</div>
          {answers.map((a, i) => {
            const p = spring({ frame: Math.max(0, frame - (30 + i * 16)), fps, durationInFrames: 16, config: { damping: 16 } });
            return <div key={i} style={{ color: WHITE, fontWeight: 700, fontSize: 42, marginBottom: 18, opacity: p, transform: `translateX(${interpolate(p, [0, 1], [-24, 0])}px)` }}>{i + 1}. {a}</div>;
          })}
          <div style={{ color: CORAL, fontWeight: 800, fontSize: 38, marginTop: 16, opacity: noteP, transform: `translateY(${interpolate(noteP, [0, 1], [16, 0])}px)` }}>{scene.note}</div>
        </div>
      </div>
    </Scene>
  );
};

// ---------- VERSUS ----------
const Versus: React.FC<{ scene: any }> = ({ scene }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const tone = (t: string) => (t === "mint" ? MINT : t === "coral" ? CORAL : MUTE);
  const mark = (m: string) => (m === "check" ? "✓" : m === "cross" ? "✕" : "");
  const lp = spring({ frame, fps, durationInFrames: 20, config: { damping: 16 } });
  const rp = spring({ frame: Math.max(0, frame - 14), fps, durationInFrames: 20, config: { damping: 16 } });
  const Col: React.FC<{ d: any; p: number; side: number }> = ({ d, p, side }) => (
    <div style={{ flex: 1, textAlign: "center", opacity: p, transform: `translateX(${interpolate(p, [0, 1], [side * 40, 0])}px)` }}>
      <div style={{ color: tone(d.tone), fontWeight: 800, fontSize: 66, marginBottom: 22 }}>{d.title}</div>
      <div style={{ color: WHITE, fontWeight: 600, fontSize: 40, lineHeight: 1.3 }}>{d.sub} {d.mark ? <span style={{ color: tone(d.tone), fontWeight: 800 }}>{mark(d.mark)}</span> : null}</div>
    </div>
  );
  return (
    <Scene center>
      <div style={{ display: "flex", width: 1000, alignItems: "center" }}>
        <Col d={scene.left} p={lp} side={-1} />
        <div style={{ width: 3, height: 300, background: LINE }} />
        <Col d={scene.right} p={rp} side={1} />
      </div>
    </Scene>
  );
};

// ---------- ENGINES ----------
const Engines: React.FC<{ scene: any }> = ({ scene }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const items: string[] = scene.items || [];
  return (
    <Scene center>
      <div style={{ color: MUTE, fontWeight: 700, fontSize: 34, marginBottom: 40, opacity: interpolate(frame, [0, 16], [0, 1], { extrapolateRight: "clamp" }) }}>{scene.lead || "We make sure they name you on"}</div>
      <div style={{ display: "flex", flexDirection: "column", gap: 30 }}>
        {items.map((it, i) => {
          const p = spring({ frame: Math.max(0, frame - (16 + i * 18)), fps, durationInFrames: 18, config: { damping: 14, stiffness: 120 } });
          return (
            <div key={i} style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 30, width: 620, background: CARD, border: `2px solid ${MINT}`, borderRadius: 20, padding: "22px 42px", opacity: p, transform: `scale(${interpolate(p, [0, 1], [0.8, 1])})` }}>
              <span style={{ color: WHITE, fontWeight: 800, fontSize: 50 }}>{it}</span>
              <span style={{ color: MINT, fontWeight: 800, fontSize: 44 }}>✓</span>
            </div>
          );
        })}
      </div>
    </Scene>
  );
};

// ---------- POINTS ----------
const Points: React.FC<{ points: string[] }> = ({ points }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  return (
    <AbsoluteFill style={{ backgroundColor: BG, fontFamily, justifyContent: "center", padding: "0 90px" }}>
      {points.map((pt, i) => {
        const p = spring({ frame: Math.max(0, frame - (10 + i * 32)), fps, durationInFrames: 22, config: { damping: 16, stiffness: 110 } });
        return (
          <div key={i} style={{ transform: `translateY(${interpolate(p, [0, 1], [40, 0])}px)`, opacity: p, marginBottom: 64, display: "flex", gap: 30, alignItems: "stretch" }}>
            <div style={{ width: 10, background: MINT, borderRadius: 6 }} />
            <div style={{ color: WHITE, fontWeight: 700, fontSize: 60, lineHeight: 1.14 }}>{pt}</div>
          </div>
        );
      })}
    </AbsoluteFill>
  );
};

// ---------- CTA (always last: Free scan + website) ----------
const CTA: React.FC<{ cta: string }> = ({ cta }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const gp = spring({ frame, fps, durationInFrames: 22, config: { damping: 200 } });
  const arrowY = Math.sin(frame / 6) * 8;
  return (
    <Scene center>
      <div style={{ padding: "0 90px", textAlign: "center", display: "flex", flexDirection: "column", alignItems: "center" }}>
        <div style={{ transform: `scale(${interpolate(gp, [0, 1], [0.8, 1])})`, opacity: gp, marginBottom: 46 }}>
          <InfinityGlyph size={140} progress={1} />
        </div>
        <div style={{ color: WHITE, fontWeight: 800, fontSize: 64, lineHeight: 1.14, opacity: interpolate(frame, [12, 30], [0, 1], { extrapolateRight: "clamp" }) }}>{cta}</div>
        <div style={{ color: MINT, fontWeight: 800, fontSize: 52, marginTop: 44, transform: `translateY(${arrowY}px)`, opacity: interpolate(frame, [30, 45], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }) }}>Free scan ↓</div>
        <div style={{ color: MINT, fontWeight: 700, fontSize: 42, marginTop: 22, opacity: interpolate(frame, [40, 55], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }) }}>{FOOTER}</div>
      </div>
    </Scene>
  );
};

// ---------- fade wrapper ----------
const FadeScene: React.FC<{ from: number; dur: number; children: React.ReactNode }> = ({ from, dur, children }) => (
  <Sequence from={from} durationInFrames={dur}>
    <Fade dur={dur}>{children}</Fade>
  </Sequence>
);
const Fade: React.FC<{ dur: number; children: React.ReactNode }> = ({ dur, children }) => {
  const frame = useCurrentFrame();
  const o = interpolate(frame, [0, 8, dur - 8, dur], [0, 1, 1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  return <AbsoluteFill style={{ opacity: o }}>{children}</AbsoluteFill>;
};

const SceneSwitch: React.FC<{ scene: any }> = ({ scene }) => {
  switch (scene?.type) {
    case "shortlist": return <Shortlist scene={scene} />;
    case "chat": return <Chat scene={scene} />;
    case "versus": return <Versus scene={scene} />;
    case "engines": return <Engines scene={scene} />;
    default: return <AbsoluteFill style={{ backgroundColor: BG }} />;
  }
};

export const AeoReel: React.FC<ReelProps> = (props) => {
  const { segs } = planReel(props);
  const renderSeg = (kind: string) => {
    if (kind === "cover") return <Cover {...props} />;
    if (kind === "scene") return <SceneSwitch scene={props.scene} />;
    if (kind === "points") return <Points points={props.points || []} />;
    return <CTA cta={props.cta} />;
  };
  return (
    <AbsoluteFill style={{ backgroundColor: BG }}>
      {segs.map((s, i) => (
        <FadeScene key={i} from={s.from} dur={s.dur}>
          {renderSeg(s.kind)}
        </FadeScene>
      ))}
    </AbsoluteFill>
  );
};
