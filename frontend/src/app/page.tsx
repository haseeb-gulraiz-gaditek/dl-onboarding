"use client";

import { useEffect, useState } from "react";
import { useScrollProgress } from "@/components/Primitives";
import { ToolGraph } from "@/components/ToolGraph";
import {
  Nav,
  Hero,
  HowItWorks,
  TheGraphIsYou,
} from "./(landing)/_sections";
import {
  CommunitiesSection,
  FoundersSection,
  NudgePreview,
  Manifesto,
  FinalCTA,
  Footer,
} from "./(landing)/_sections2";

export default function LandingPage() {
  const scrollP = useScrollProgress();
  const [interactionTags, setInteractionTags] = useState<string[]>([]);
  const [sectionTags, setSectionTags] = useState<string[]>([]);
  const liveTags = interactionTags.length ? interactionTags : sectionTags;

  const [mode, setMode] = useState<"hero" | "flow">("hero");
  useEffect(() => {
    const onScroll = () => {
      const heroH = window.innerHeight * 0.85;
      setMode(window.scrollY > heroH ? "flow" : "hero");
    };
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  useEffect(() => {
    const sections = document.querySelectorAll<HTMLElement>("[data-tags]");
    const io = new IntersectionObserver(
      (entries) => {
        const visible = entries
          .filter((e) => e.isIntersecting)
          .sort((a, b) => b.intersectionRatio - a.intersectionRatio)[0];
        if (visible)
          setSectionTags(
            (visible.target as HTMLElement).dataset.tags
              ?.split(",")
              .filter(Boolean) || [],
          );
      },
      { threshold: [0.3, 0.6] },
    );
    sections.forEach((s) => io.observe(s));
    return () => io.disconnect();
  }, []);

  const nodeScale = mode === "hero" ? 1.4 : 1.0;

  return (
    <>
      <div className="m-bg-graph">
        <ToolGraph
          progress={Math.min(1, 0.3 + scrollP * 1.2)}
          highlightedTags={liveTags}
          mode={mode}
          scale={nodeScale}
        />
      </div>
      <div className="m-vignette" />

      <div className="m-page">
        <Nav />
        <Hero onGraphTags={setInteractionTags} />

        <div data-tags="ai,writing">
          <HowItWorks />
        </div>
        <div data-tags="">
          <TheGraphIsYou
            onAnswer={(tags) => {
              setInteractionTags(tags);
              setTimeout(() => setInteractionTags([]), 2400);
            }}
          />
        </div>
        <div data-tags="pm,dev,design">
          <CommunitiesSection />
        </div>
        <div data-tags="ai">
          <NudgePreview />
        </div>
        <div data-tags="">
          <Manifesto />
        </div>
        <div data-tags="dev,design,pm,writing">
          <FoundersSection />
        </div>
        <div data-tags="">
          <FinalCTA />
        </div>
        <Footer />
      </div>
    </>
  );
}
