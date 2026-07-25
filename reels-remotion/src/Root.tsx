import React from "react";
import { Composition } from "remotion";
import { AeoReel } from "./AeoReel";
import { totalFrames } from "./plan";

export const RemotionRoot: React.FC = () => {
  return (
    <Composition
      id="AeoReel"
      component={AeoReel}
      durationInFrames={480}
      fps={30}
      width={1080}
      height={1920}
      calculateMetadata={({ props }) => ({ durationInFrames: totalFrames(props as any) })}
      defaultProps={{
        eyebrow: "The blind spot",
        hook: "AI already built a shortlist of surgeons in your city",
        scene: {
          type: "shortlist",
          names: ["A Midtown practice", "A downtown competitor", "Another nearby surgeon"],
          youLabel: "you?",
        },
        points: [
          "Most practices aren't on it — and never find out.",
          "It's decided before a patient visits your site.",
        ],
        cta: "Wondering if you made the list?",
      }}
    />
  );
};
