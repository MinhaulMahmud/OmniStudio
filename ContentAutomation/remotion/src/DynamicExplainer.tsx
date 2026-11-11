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

  // Ambient background glow pulse
  const ambientPulse = interpolate(
    Math.sin(frame / 20),
    [-1, 1],
    [0.15, 0.35]
  );

  return (
    <div
      style={{
        flex: 1,
        width: "100%",
        height: "100%",
        backgroundColor: "#070714",
        backgroundImage: `radial-gradient(circle at 50% 30%, rgba(99, 102, 241, ${ambientPulse}) 0%, #070714 75%)`,
        display: "flex",
        flexDirection: "column",
        fontFamily: "'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif",
        color: "#ffffff",
        position: "relative",
        overflow: "hidden",
      }}
    >
      {/* Background Narration Audio */}
      {audioFile && <Audio src={staticFile(audioFile)} />}

      {/* Decorative Cybernetic Background Grid */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          backgroundImage: `
            linear-gradient(to right, rgba(255, 255, 255, 0.03) 1px, transparent 1px),
            linear-gradient(to bottom, rgba(255, 255, 255, 0.03) 1px, transparent 1px)
          `,
          backgroundSize: "60px 60px",
          maskImage: "radial-gradient(circle at 50% 50%, black 40%, transparent 80%)",
          WebkitMaskImage: "radial-gradient(circle at 50% 50%, black 40%, transparent 80%)",
          pointerEvents: "none",
        }}
      />

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
          background: "linear-gradient(to bottom, rgba(7, 7, 20, 0.95), transparent)",
          zIndex: 50,
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
          <div
            style={{
              width: "12px",
              height: "12px",
              borderRadius: "50%",
              backgroundColor: "#22c55e",
              boxShadow: "0 0 12px #22c55e",
            }}
          />
          <span style={{ fontSize: "20px", fontWeight: 700, letterSpacing: "1.5px", color: "#a5b4fc" }}>
            VOICESTUDIO AI
          </span>
          <span style={{ color: "rgba(255,255,255,0.3)" }}>|</span>
          <span
            style={{
              fontSize: "14px",
              padding: "4px 12px",
              borderRadius: "20px",
              backgroundColor: "rgba(99, 102, 241, 0.15)",
              border: "1px solid rgba(99, 102, 241, 0.4)",
              color: "#c7d2fe",
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
                  backgroundColor: i % 2 === 0 ? "#818cf8" : "#c084fc",
                  borderRadius: "2px",
                  boxShadow: "0 0 8px rgba(129, 140, 248, 0.6)",
                }}
              />
            );
          })}
          <span style={{ fontSize: "14px", color: "rgba(255,255,255,0.7)", marginLeft: "8px", fontWeight: 600 }}>
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
            background: "linear-gradient(90deg, #6366f1, #a855f7, #38bdf8)",
            boxShadow: "0 0 10px #6366f1",
          }}
        />
      </div>

      {/* Dynamic Content Sections */}
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
        /* Fallback Single Hero Slide when no sections are passed */
        <Sequence from={0} durationInFrames={totalFrames}>
          <HeroSlide title={title} subtitle={subtitle} />
        </Sequence>
      )}

      {/* Bottom Subtitle Caption Overlay Bar */}
      <div
        style={{
          position: "absolute",
          bottom: isPortrait ? "180px" : "35px",
          left: isPortrait ? "40px" : "80px",
          right: isPortrait ? "40px" : "80px",
          minHeight: "75px",
          padding: "16px 28px",
          borderRadius: "16px",
          backgroundColor: "rgba(10, 10, 26, 0.85)",
          border: "1px solid rgba(255, 255, 255, 0.12)",
          backdropFilter: "blur(12px)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          textAlign: "center",
          boxShadow: "0 20px 40px rgba(0,0,0,0.6)",
          zIndex: 40,
        }}
      >
        <span
          style={{
            fontSize: isPortrait ? "22px" : "24px",
            lineHeight: "1.4",
            fontWeight: 500,
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

// ─── Component: Individual Section Slide ────────────────────────────────────

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

  // Entrance spring animation
  const enterScale = spring({
    frame,
    fps,
    config: { damping: 14, mass: 0.6 },
  });

  const cardOpacity = interpolate(frame, [0, 15], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const floatY = interpolate(Math.sin(frame / 25), [-1, 1], [-6, 6]);

  const bullets = section.bullets || splitIntoBullets(section.text);

  return (
    <div
      style={{
        flex: 1,
        display: "flex",
        flexDirection: isPortrait ? "column" : "row",
        alignItems: "center",
        justifyContent: isPortrait ? "center" : "space-between",
        padding: isPortrait ? "130px 40px 260px 40px" : "90px 60px 110px 60px",
        gap: isPortrait ? "24px" : "40px",
        zIndex: 20,
      }}
    >
      {/* Left Column: Heading & Core Takeaways */}
      <div
        style={{
          width: isPortrait ? "100%" : "560px",
          maxWidth: isPortrait ? "960px" : "560px",
          display: "flex",
          flexDirection: "column",
          gap: "12px",
        }}
      >
        {/* Section Step Badge */}
        <div style={{ display: "flex", alignItems: "center", gap: "10px", opacity: cardOpacity }}>
          <div
            style={{
              padding: "6px 16px",
              borderRadius: "30px",
              backgroundColor: "rgba(56, 189, 248, 0.2)",
              border: "1px solid rgba(56, 189, 248, 0.5)",
              fontSize: "13px",
              fontWeight: 800,
              letterSpacing: "1px",
              color: "#38bdf8",
              textTransform: "uppercase",
            }}
          >
            {section.badge || `Section ${sectionIndex + 1} of ${totalSections}`}
          </div>
        </div>

        {/* Main Section Heading */}
        <h1
          style={{
            fontSize: isPortrait ? "36px" : "42px",
            fontWeight: 900,
            lineHeight: "1.2",
            margin: "0 0 6px 0",
            background: "linear-gradient(135deg, #ffffff 40%, #38bdf8 100%)",
            WebkitBackgroundClip: "text",
            WebkitTextFillColor: "transparent",
            transform: `scale(${enterScale}) translateY(${floatY}px)`,
          }}
        >
          {section.heading}
        </h1>

        {/* Structured Insight Bullets */}
        <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
          {bullets.slice(0, isPortrait ? 2 : 3).map((bullet, bIdx) => (
            <div
              key={bIdx}
              style={{
                display: "flex",
                alignItems: "flex-start",
                gap: "14px",
                backgroundColor: "rgba(15, 23, 42, 0.75)",
                border: "1px solid rgba(255, 255, 255, 0.08)",
                borderRadius: "14px",
                padding: "12px 16px",
                boxShadow: "0 4px 15px rgba(0,0,0,0.3)",
              }}
            >
              <div
                style={{
                  width: "26px",
                  height: "26px",
                  borderRadius: "8px",
                  backgroundColor: "rgba(56, 189, 248, 0.2)",
                  color: "#38bdf8",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  fontWeight: 800,
                  fontSize: "13px",
                  flexShrink: 0,
                }}
              >
                {bIdx + 1}
              </div>
              <p style={{ margin: 0, fontSize: "15px", color: "#e2e8f0", lineHeight: "1.4", fontWeight: 400 }}>
                {bullet}
              </p>
            </div>
          ))}
        </div>
      </div>

      {/* Right Column: Live Animated Mechanical/Technical Mechanism Viewport */}
      <div style={{ flex: 1, display: "flex", justifyContent: "center", alignItems: "center", width: "100%" }}>
        <VisualMechanismViewport
          topic={mainTitle}
          sectionIndex={sectionIndex}
          totalSections={totalSections}
          heading={section.heading}
          width={isPortrait ? 960 : 1140}
          height={isPortrait ? 600 : 640}
        />
      </div>
    </div>
  );
};

// ─── Component: Fallback Hero Slide ─────────────────────────────────────────

const HeroSlide: React.FC<{ title: string; subtitle: string }> = ({ title, subtitle }) => {
  const frame = useCurrentFrame();
  const scale = spring({ frame, fps: 30, config: { damping: 12 } });

  return (
    <div
      style={{
        flex: 1,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        padding: "80px",
      }}
    >
      <h1
        style={{
          fontSize: "64px",
          fontWeight: 900,
          textAlign: "center",
          maxWidth: "1300px",
          background: "linear-gradient(135deg, #ffffff 30%, #818cf8 100%)",
          WebkitBackgroundClip: "text",
          WebkitTextFillColor: "transparent",
          transform: `scale(${scale})`,
        }}
      >
        {title}
      </h1>
      <p style={{ fontSize: "28px", color: "#94a3b8", marginTop: "24px", textAlign: "center" }}>
        {subtitle}
      </p>
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

function splitIntoBullets(text: string): string[] {
  if (!text) return [];
  // Split on sentences
  const sentences = text
    .split(/(?<=[.!?])\s+/)
    .map((s) => s.trim())
    .filter((s) => s.length > 10);

  if (sentences.length <= 3) {
    return sentences;
  }
  // Group into max 3 bullets
  return [sentences[0], sentences[1], sentences.slice(2).join(" ")];
}
