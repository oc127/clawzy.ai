import { ImageResponse } from "next/og";

export const runtime = "edge";
export const alt = "Clawzy.ai — Your AI Lobster Assistant";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

export default async function Image() {
  return new ImageResponse(
    (
      <div
        style={{
          background: "linear-gradient(135deg, #0a0a0f 0%, #141420 50%, #1a1a2e 100%)",
          width: "100%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          fontFamily: "system-ui, sans-serif",
        }}
      >
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "16px",
            marginBottom: "32px",
          }}
        >
          <span style={{ fontSize: "72px" }}>🦞</span>
          <span
            style={{
              fontSize: "64px",
              fontWeight: 700,
              color: "#ffffff",
              letterSpacing: "-2px",
            }}
          >
            Clawzy.ai
          </span>
        </div>
        <p
          style={{
            fontSize: "28px",
            color: "#8b8b9e",
            maxWidth: "700px",
            textAlign: "center",
            lineHeight: 1.5,
          }}
        >
          Your personal AI assistant, running in an isolated container — private, powerful, yours.
        </p>
        <div
          style={{
            display: "flex",
            gap: "24px",
            marginTop: "40px",
          }}
        >
          {["Multi-Model", "Tool Store", "Privacy-First"].map((tag) => (
            <span
              key={tag}
              style={{
                padding: "8px 20px",
                borderRadius: "999px",
                border: "1px solid rgba(139, 92, 246, 0.3)",
                color: "#a78bfa",
                fontSize: "16px",
              }}
            >
              {tag}
            </span>
          ))}
        </div>
      </div>
    ),
    { ...size },
  );
}
