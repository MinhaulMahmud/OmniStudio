import React from "react";
import {
  Audio,
  interpolate,
  Sequence,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { VisualMechanismViewport } from "./components/VisualMechanismViewport";
import { DynamicBackdrop } from "./scenes/primitives/DynamicBackdrop";
import { CinematicCamera } from "./scenes/primitives/CinematicCamera";
import { KineticText } from "./scenes/primitives/KineticText";

export interface DynamicSection {
  heading: string;
  text: string;
  startFrame: number;
  durationFrames: number;
  badge?: string;
  bullets?: string[];
}

export interface DynamicExplainerProps {
  title: string;
  subtitle?: string;
  category?: string;
  voiceBadge?: string;
  sections: DynamicSection[];
  totalFrames: number;
  audioFile?: string;
}

export const DynamicExplainer: React.FC<DynamicExplainerProps> = ({
  title = "AI Technology Explainer",
  subtitle = "Generated with VoiceStudio & Remotion",
  category = "Artificial Intelligence",
  voiceBadge = "KittenTTS Explainer",
  sections = [],
  totalFrames = 1800,
  audioFile = "narration.mp3",
}) => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();
  const isPortrait = height > width;

  // Overall timeline progress (0 -> 100%)
  const progressPercent = Math.min(100, Math.max(0, (frame / (totalFrames || 1)) * 100));

  return (
    <div
      style={{
        flex: 1,
        width: "100%",
        height: "100%",
        backgroundColor: "#050711",
        display: "flex",
        flexDirection: "column",
        fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
        color: "#ffffff",
        position: "relative",
        overflow: "hidden",
      }}
    >
      {/* Background Narration Audio */}
      {audioFile && <Audio src={staticFile(audioFile)} />}

      {/* Dynamic Multi-Layer Animated Motion Backdrop */}
      <DynamicBackdrop theme="aurora" particleCount={isPortrait ? 28 : 36} showGrid={true} />

      {/* Top Header & Brand Bar */}
      <div
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          right: 0,
          height: isPortrait ? "110px" : "80px",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: isPortrait ? "30px 40px 0 40px" : "0 60px",
          background: "linear-gradient(to bottom, rgba(5, 7, 17, 0.95), transparent)",
          zIndex: 50,
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
          <div
            style={{
              width: "12px",
              height: "12px",
              borderRadius: "50%",
              backgroundColor: "#00e5ff",
              boxShadow: "0 0 14px #00e5ff",
            }}
          />
          <span style={{ fontSize: isPortrait ? "18px" : "20px", fontWeight: 800, letterSpacing: "1.5px", color: "#38bdf8" }}>
            OMNISTUDIO
          </span>
          <span style={{ color: "rgba(255,255,255,0.3)" }}>|</span>
          <span
            style={{
              fontSize: isPortrait ? "12px" : "14px",
              padding: "4px 12px",
              borderRadius: "20px",
              backgroundColor: "rgba(56, 189, 248, 0.15)",
              border: "1px solid rgba(56, 189, 248, 0.4)",
              color: "#bae6fd",
              letterSpacing: "0.5px",
            }}
          >
            {category}
          </span>
        </div>

        {/* Dynamic Voice Cloned Audio Pulse Indicator */}
        <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
          {[...Array(6)].map((_, i) => {
            const h = interpolate(
              Math.sin(frame / 6 + i * 1.2),
              [-1, 1],
              [8, 28]
            );
            return (
              <div
                key={i}
                style={{
                  width: "4px",
                  height: `${h}px`,
                  backgroundColor: i % 2 === 0 ? "#00e5ff" : "#818cf8",
                  borderRadius: "2px",
                  boxShadow: "0 0 8px rgba(0, 229, 255, 0.6)",
                }}
              />
            );
          })}
          <span style={{ fontSize: isPortrait ? "12px" : "14px", color: "rgba(255,255,255,0.7)", marginLeft: "8px", fontWeight: 600 }}>
            {voiceBadge}
          </span>
        </div>
      </div>

      {/* Top Timeline Progress Bar */}
      <div
        style={{
          position: "absolute",
          top: isPortrait ? "110px" : "80px",
          left: 0,
          right: 0,
          height: "4px",
          backgroundColor: "rgba(255, 255, 255, 0.05)",
          zIndex: 51,
        }}
      >
        <div
          style={{
            height: "100%",
            width: `${progressPercent}%`,
            background: "linear-gradient(90deg, #00e5ff, #818cf8, #ec4899)",
            boxShadow: "0 0 10px #00e5ff",
          }}
        />
      </div>

      {/* Dynamic Motion Graphic Content Canvas */}
      <CinematicCamera drift="zoom-in" intensity={0.05}>
        {sections.length > 0 ? (
          sections.map((sec, idx) => (
            <Sequence
              key={idx}
              from={sec.startFrame}
              durationInFrames={sec.durationFrames}
            >
              <SectionSlide
                section={sec}
                sectionIndex={idx}
                totalSections={sections.length}
                mainTitle={title}
              />
            </Sequence>
          ))
        ) : (
          <Sequence from={0} durationInFrames={totalFrames}>
            <HeroSlide title={title} subtitle={subtitle} />
          </Sequence>
        )}
      </CinematicCamera>

      {/* Bottom Subtitle Caption Overlay Bar */}
      <div
        style={{
          position: "absolute",
          bottom: isPortrait ? "180px" : "35px",
          left: isPortrait ? "40px" : "80px",
          right: isPortrait ? "40px" : "80px",
          minHeight: "70px",
          padding: "14px 24px",
          borderRadius: "16px",
          backgroundColor: "rgba(5, 7, 17, 0.82)",
          border: "1px solid rgba(0, 229, 255, 0.25)",
          backdropFilter: "blur(14px)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          textAlign: "center",
          boxShadow: "0 15px 35px rgba(0,0,0,0.7), 0 0 20px rgba(0, 229, 255, 0.15)",
          zIndex: 40,
        }}
      >
        <span
          style={{
            fontSize: isPortrait ? "22px" : "24px",
            lineHeight: "1.35",
            fontWeight: 600,
            color: "#f8fafc",
            textShadow: "0 2px 4px rgba(0,0,0,0.8)",
          }}
        >
          {getCurrentSubtitleText(sections, frame) || subtitle}
        </span>
      </div>
    </div>
  );
};

// ─── Component: Individual Section Motion Canvas ───────────────────────────

interface SectionSlideProps {
  section: DynamicSection;
  sectionIndex: number;
  totalSections: number;
  mainTitle: string;
}

const SectionSlide: React.FC<SectionSlideProps> = ({
  section,
  sectionIndex,
  totalSections,
  mainTitle,
}) => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();
  const isPortrait = height > width;

  // Extract punchy 3-6 word hero phrase from heading or first sentence
  const heroPhrase = extractHeroPhrase(section.heading, section.text);
  const accentWord = extractAccentWord(heroPhrase);

  const badgeOpacity = interpolate(frame, [0, 10], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <div
      style={{
        flex: 1,
        width: "100%",
        height: "100%",
        display: "flex",
        flexDirection: isPortrait ? "column" : "row",
        alignItems: "center",
        justifyContent: "space-between",
        padding: isPortrait ? "130px 40px 260px 40px" : "90px 60px 110px 60px",
        gap: isPortrait ? "28px" : "50px",
        zIndex: 20,
      }}
    >
      {/* Visual Text Header with Kinetic Typography */}
      <div
        style={{
          width: isPortrait ? "100%" : "520px",
          maxWidth: isPortrait ? "960px" : "520px",
          display: "flex",
          flexDirection: "column",
          alignItems: isPortrait ? "center" : "flex-start",
          textAlign: isPortrait ? "center" : "left",
          gap: "16px",
        }}
      >
        {/* Floating Stage Indicator */}
        <div
          style={{
            opacity: badgeOpacity,
            display: "inline-flex",
            alignItems: "center",
            gap: "8px",
            padding: "6px 14px",
            borderRadius: "30px",
            backgroundColor: "rgba(0, 229, 255, 0.12)",
            border: "1px solid rgba(0, 229, 255, 0.4)",
            fontSize: "12px",
            fontWeight: 800,
            letterSpacing: "1.5px",
            color: "#00e5ff",
            textTransform: "uppercase",
          }}
        >
          <span>●</span>
          <span>{section.badge || `STAGE 0${sectionIndex + 1} / 0${totalSections}`}</span>
        </div>

        {/* Kinetic Hero Phrase */}
        <KineticText
          phrase={heroPhrase}
          accentWords={[accentWord]}
          fontSize={isPortrait ? 44 : 52}
          alignment={isPortrait ? "center" : "left"}
          accentColor="#00e5ff"
        />
      </div>

      {/* Hero Visual Mechanism Viewport */}
      <div
        style={{
          flex: 1,
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          width: "100%",
        }}
      >
        <VisualMechanismViewport
          topic={mainTitle}
          sectionIndex={sectionIndex}
          totalSections={totalSections}
          heading={section.heading}
          width={isPortrait ? 960 : 1140}
          height={isPortrait ? 660 : 640}
        />
      </div>
    </div>
  );
};

// ─── Component: Fallback Hero Motion ────────────────────────────────────────

const HeroSlide: React.FC<{ title: string; subtitle: string }> = ({ title, subtitle }) => {
  const { width, height } = useVideoConfig();
  const isPortrait = height > width;

  return (
    <div
      style={{
        flex: 1,
        width: "100%",
        height: "100%",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        padding: isPortrait ? "130px 40px 240px 40px" : "80px 60px",
        gap: "24px",
      }}
    >
      <KineticText phrase={title} fontSize={isPortrait ? 44 : 56} alignment="center" accentColor="#00e5ff" />
      <div style={{ flex: 1, display: "flex", alignItems: "center", justifyContent: "center", width: "100%" }}>
        <VisualMechanismViewport
          topic={title}
          sectionIndex={0}
          totalSections={1}
          heading={subtitle || title}
          width={isPortrait ? 960 : 1140}
          height={isPortrait ? 660 : 560}
        />
      </div>
    </div>
  );
};

// ─── Helper Functions ───────────────────────────────────────────────────────

function getCurrentSubtitleText(sections: DynamicSection[], currentFrame: number): string {
  for (const s of sections) {
    if (currentFrame >= s.startFrame && currentFrame < s.startFrame + s.durationFrames) {
      return s.text;
    }
  }
  return "";
}

function extractHeroPhrase(heading: string, text: string): string {
  if (heading && heading.split(/\s+/).length <= 7) {
    return heading;
  }
  // Otherwise take the first 4-6 words of the first sentence
  const firstSentence = (text || "").split(/[.!?]/)[0].trim();
  const words = firstSentence.split(/\s+/).filter(Boolean);
  if (words.length <= 6) {
    return words.join(" ") || heading || "Key Principle";
  }
  return words.slice(0, 6).join(" ");
}

function extractAccentWord(phrase: string): string {
  const words = phrase.split(/\s+/).filter(Boolean);
  if (words.length === 0) return "";
  // Pick the longest word as key accent
  return words.reduce((longest, current) =>
    current.length > longest.length ? current : longest, words[0]
  );
}
